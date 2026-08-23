"""Continuous drifted-weight path with post-return-equity cost."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
import math
from numbers import Real
from types import MappingProxyType

from campaign.returns import SimpleReturn


_REASON_HELD_RETURN_MISSING = "HELD_RETURN_MISSING"
_REASON_HELD_RETURN_BOOLEAN = "HELD_RETURN_BOOLEAN"
_REASON_HELD_RETURN_NON_FINITE = "HELD_RETURN_NON_FINITE"
_REASON_HELD_RETURN_INVALID = "HELD_RETURN_INVALID"
_REASON_PORTFOLIO_INSOLVENT = "PORTFOLIO_INSOLVENT"
_BPS_PER_UNIT = 10000.0


@dataclass(frozen=True)
class HoldingInterval:
    """One adjacent holding interval and an optional end-of-interval reset."""

    session_date: str
    held_returns: MappingProxyType[bytes, SimpleReturn]
    reset_weights: MappingProxyType[bytes, float] | None


@dataclass(frozen=True)
class IntervalPoint:
    """One retained interval of the continuous holdings path."""

    session_date: str
    gross_return: float | None
    net_return: float | None
    turnover: float | None
    cost_impact: float | None
    equity: float | None
    gross_multiplier: float | None
    pre_return_weights: MappingProxyType[bytes, float]
    drifted_weights: MappingProxyType[bytes, float]
    post_trade_weights: MappingProxyType[bytes, float]
    gross_contributions: MappingProxyType[bytes, float]
    cost_contributions: MappingProxyType[bytes, float]
    valid: bool
    reason: str | None


@dataclass(frozen=True)
class ContinuousHoldings:
    """Connected holdings path starting from supplied initial weights."""

    initial_equity: float
    initial_weights: MappingProxyType[bytes, float]
    points: tuple[IntervalPoint, ...]
    valid: bool
    reason: str | None
    reason_counts: MappingProxyType[str, int]


def post_return_equity_cost(
    turnover: object,
    transaction_cost_bps: object,
    gross_multiplier: object,
) -> float:
    """Return turnover * (bps / 10000) * incoming gross multiplier."""

    traded = _finite_real(turnover, "turnover")
    bps = _finite_real(transaction_cost_bps, "transaction_cost_bps")
    multiplier = _finite_real(gross_multiplier, "gross_multiplier")
    if traded < 0.0:
        raise ValueError("turnover must be nonnegative")
    if bps < 0.0:
        raise ValueError("transaction_cost_bps must be nonnegative")
    return traded * (bps / _BPS_PER_UNIT) * multiplier


def holding_interval(
    session_date: str,
    held_returns: Mapping[bytes, object],
    reset_weights: Mapping[bytes, object] | None,
) -> HoldingInterval:
    """Build one validated interval. None reset_weights means no reset."""

    if not isinstance(held_returns, Mapping):
        raise TypeError("held_returns must be a mapping")
    parsed_returns: dict[bytes, SimpleReturn] = {}
    for listing_key, raw in held_returns.items():
        _validate_listing_key(listing_key)
        parsed_returns[listing_key] = _coerce_simple_return(raw)
    parsed_reset = None
    if reset_weights is not None:
        parsed_reset = _validated_weights(reset_weights, "reset_weights")
    return HoldingInterval(
        session_date=_strict_date(session_date).isoformat(),
        held_returns=MappingProxyType(parsed_returns),
        reset_weights=(
            None if parsed_reset is None else MappingProxyType(parsed_reset)
        ),
    )


def advance_holdings(
    initial_weights: Mapping[bytes, object],
    intervals: Sequence[HoldingInterval],
    transaction_cost_bps: object,
    initial_equity: object,
) -> ContinuousHoldings:
    """Advance drifted weights, undivided turnover, and post-return cost."""

    if (
        isinstance(intervals, (str, bytes, bytearray))
        or not isinstance(intervals, Sequence)
    ):
        raise TypeError("intervals must be a sequence")
    current_weights = _validated_weights(initial_weights, "initial_weights")
    equity = _positive_real(initial_equity, "initial_equity")
    bps = _finite_real(transaction_cost_bps, "transaction_cost_bps")
    if bps < 0.0:
        raise ValueError("transaction_cost_bps must be nonnegative")

    points: list[IntervalPoint] = []
    reason_counts: dict[str, int] = {}
    blocked_reason: str | None = None
    for interval in intervals:
        if not isinstance(interval, HoldingInterval):
            raise TypeError("intervals must contain HoldingInterval values")
        if blocked_reason is not None:
            point = _blocked_point(interval, current_weights, blocked_reason)
        else:
            point = _advance_one(
                interval,
                current_weights,
                bps,
                equity,
            )
            if point.valid:
                current_weights = dict(point.post_trade_weights)
                if point.equity is None:
                    raise RuntimeError("valid interval must carry equity")
                equity = point.equity
            else:
                blocked_reason = point.reason
        if point.reason is not None:
            reason_counts[point.reason] = (
                reason_counts.get(point.reason, 0) + 1
            )
        points.append(point)

    overall_reason = None
    for point in points:
        if not point.valid:
            overall_reason = point.reason
            break
    return ContinuousHoldings(
        initial_equity=_positive_real(initial_equity, "initial_equity"),
        initial_weights=MappingProxyType(
            _validated_weights(initial_weights, "initial_weights")
        ),
        points=tuple(points),
        valid=overall_reason is None,
        reason=overall_reason,
        reason_counts=MappingProxyType(reason_counts),
    )


def _advance_one(
    interval: HoldingInterval,
    pre_weights: Mapping[bytes, float],
    transaction_cost_bps: float,
    previous_equity: float,
) -> IntervalPoint:
    pre = {key: weight for key, weight in pre_weights.items() if weight != 0.0}
    for listing_key, weight in pre.items():
        observed = interval.held_returns.get(listing_key)
        if observed is None:
            return _invalid_point(
                interval,
                pre,
                _REASON_HELD_RETURN_MISSING,
            )
        if not isinstance(observed, SimpleReturn):
            return _invalid_point(
                interval,
                pre,
                _REASON_HELD_RETURN_INVALID,
            )
        if not observed.valid or observed.value is None:
            return _invalid_point(
                interval,
                pre,
                observed.reason or _REASON_HELD_RETURN_INVALID,
            )
        if not math.isfinite(observed.value):
            return _invalid_point(
                interval,
                pre,
                _REASON_HELD_RETURN_NON_FINITE,
            )

    gross = 0.0
    grown: dict[bytes, float] = {}
    gross_contributions: dict[bytes, float] = {}
    for listing_key, weight in pre.items():
        held_return = interval.held_returns[listing_key].value
        if held_return is None:
            return _invalid_point(
                interval,
                pre,
                _REASON_HELD_RETURN_INVALID,
            )
        contribution = weight * held_return
        gross += contribution
        grown[listing_key] = weight * (1.0 + held_return)
        gross_contributions[listing_key] = contribution

    multiplier = 1.0 + gross
    if (
        not math.isfinite(gross)
        or not math.isfinite(multiplier)
        or multiplier <= 0.0
    ):
        return _invalid_point(interval, pre, _REASON_PORTFOLIO_INSOLVENT)

    if grown:
        drifted = {
            listing_key: value / multiplier
            for listing_key, value in grown.items()
        }
    else:
        drifted = {}

    if interval.reset_weights is None:
        turnover = 0.0
        cost = 0.0
        post = drifted
        cost_contributions: dict[bytes, float] = {}
    else:
        target = {
            key: weight
            for key, weight in interval.reset_weights.items()
            if weight != 0.0
        }
        turnover = _undivided_turnover(drifted, target)
        cost = post_return_equity_cost(
            turnover,
            transaction_cost_bps,
            multiplier,
        )
        post = target
        rate = (transaction_cost_bps / _BPS_PER_UNIT) * multiplier
        cost_contributions = {
            listing_key: -rate * abs(
                target.get(listing_key, 0.0) - drifted.get(listing_key, 0.0)
            )
            for listing_key in set(target) | set(drifted)
        }

    net = gross - cost
    equity = previous_equity * (1.0 + net)
    if (
        not math.isfinite(net)
        or not math.isfinite(cost)
        or not math.isfinite(equity)
        or equity <= 0.0
    ):
        return _invalid_point(interval, pre, _REASON_PORTFOLIO_INSOLVENT)

    return IntervalPoint(
        session_date=interval.session_date,
        gross_return=gross,
        net_return=net,
        turnover=turnover,
        cost_impact=cost,
        equity=equity,
        gross_multiplier=multiplier,
        pre_return_weights=MappingProxyType(pre),
        drifted_weights=MappingProxyType(drifted),
        post_trade_weights=MappingProxyType(post),
        gross_contributions=MappingProxyType(gross_contributions),
        cost_contributions=MappingProxyType(cost_contributions),
        valid=True,
        reason=None,
    )


def _undivided_turnover(
    drifted: Mapping[bytes, float],
    target: Mapping[bytes, float],
) -> float:
    listing_keys = set(drifted) | set(target)
    return sum(
        abs(target.get(listing_key, 0.0) - drifted.get(listing_key, 0.0))
        for listing_key in listing_keys
    )


def _blocked_point(
    interval: HoldingInterval,
    pre_weights: Mapping[bytes, float],
    reason: str,
) -> IntervalPoint:
    pre = {key: weight for key, weight in pre_weights.items() if weight != 0.0}
    return _invalid_point(interval, pre, reason)


def _invalid_point(
    interval: HoldingInterval,
    pre_weights: Mapping[bytes, float],
    reason: str,
) -> IntervalPoint:
    return IntervalPoint(
        session_date=interval.session_date,
        gross_return=None,
        net_return=None,
        turnover=None,
        cost_impact=None,
        equity=None,
        gross_multiplier=None,
        pre_return_weights=MappingProxyType(dict(pre_weights)),
        drifted_weights=MappingProxyType({}),
        post_trade_weights=MappingProxyType(dict(pre_weights)),
        gross_contributions=MappingProxyType({}),
        cost_contributions=MappingProxyType({}),
        valid=False,
        reason=reason,
    )


def _coerce_simple_return(raw: object) -> SimpleReturn:
    if isinstance(raw, SimpleReturn):
        return raw
    if raw is None:
        return SimpleReturn(None, False, _REASON_HELD_RETURN_MISSING)
    if isinstance(raw, bool):
        return SimpleReturn(None, False, _REASON_HELD_RETURN_BOOLEAN)
    if isinstance(raw, Real):
        numeric = float(raw)
        if not math.isfinite(numeric):
            return SimpleReturn(None, False, _REASON_HELD_RETURN_NON_FINITE)
        return SimpleReturn(numeric, True, None)
    raise TypeError("held returns must be SimpleReturn, None, or real scalars")


def _validated_weights(
    weights: Mapping[bytes, object],
    name: str,
) -> dict[bytes, float]:
    if not isinstance(weights, Mapping):
        raise TypeError(f"{name} must be a mapping")
    validated: dict[bytes, float] = {}
    for listing_key, weight in weights.items():
        _validate_listing_key(listing_key)
        numeric = _finite_real(weight, name)
        if numeric < 0.0:
            raise ValueError(f"{name} weights must be nonnegative")
        if numeric != 0.0:
            validated[listing_key] = numeric
    return validated


def _validate_listing_key(listing_key: object) -> bytes:
    if not isinstance(listing_key, bytes) or not listing_key:
        raise TypeError("listing keys must be nonempty bytes")
    return listing_key


def _strict_date(value: object) -> date:
    if not isinstance(value, str):
        raise ValueError("date must be strict YYYY-MM-DD")
    parsed = date.fromisoformat(value)
    if len(value) != 10 or parsed.isoformat() != value:
        raise ValueError("date must be strict YYYY-MM-DD")
    return parsed


def _finite_real(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real non-Boolean scalar")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError(f"{name} must be finite")
    return numeric


def _positive_real(value: object, name: str) -> float:
    numeric = _finite_real(value, name)
    if numeric <= 0.0:
        raise ValueError(f"{name} must be positive")
    return numeric


__all__ = [
    "ContinuousHoldings",
    "HoldingInterval",
    "IntervalPoint",
    "advance_holdings",
    "holding_interval",
    "post_return_equity_cost",
]

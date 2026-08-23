"""Factor-matched primary comparison and SPY secondary routing."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType

from campaign.eligibility import FrozenDecisionTime
from campaign.paths import (
    ContinuousHoldings,
    advance_holdings,
    holding_interval,
)
from campaign.returns import SimpleReturn


_REASON_UNFORMABLE = "BENCHMARK_UNFORMABLE"
_REASON_SPY_MISSING = "SPY_DATE_MISSING"
_REASON_SPY_BOOLEAN = "SPY_RETURN_BOOLEAN"
_REASON_SPY_NON_FINITE = "SPY_RETURN_NON_FINITE"
_ROLE_SPY = "spy_secondary"
_COST_FREE_BPS = 0.0


@dataclass(frozen=True)
class BenchmarkComparison:
    """One retained benchmark comparison and its validity route."""

    role: str
    valid: bool
    reason: str | None
    hard_validity_failure: bool
    active_returns: tuple[float | None, ...]
    benchmark_gross_returns: tuple[float | None, ...]
    holdings: ContinuousHoldings | None
    reason_counts: MappingProxyType[str, int]


def factor_matched_cost_free_comparison(
    frozen_decisions: Sequence[FrozenDecisionTime],
    strategy: ContinuousHoldings,
    held_returns_by_interval: Sequence[Mapping[bytes, object]],
    initial_equity: object,
    role: str,
) -> BenchmarkComparison:
    """Compare strategy net to the frozen equal-weight membership path.

    Membership is read from each FrozenDecisionTime and is never recomputed
    from later returns. The comparison is structurally cost-free.
    """

    if not isinstance(role, str) or not role:
        raise ValueError("role must be a nonempty string")
    if not isinstance(strategy, ContinuousHoldings):
        raise TypeError("strategy must be ContinuousHoldings")
    if (
        isinstance(frozen_decisions, (str, bytes, bytearray))
        or not isinstance(frozen_decisions, Sequence)
    ):
        raise TypeError("frozen_decisions must be a sequence")
    if (
        isinstance(held_returns_by_interval, (str, bytes, bytearray))
        or not isinstance(held_returns_by_interval, Sequence)
    ):
        raise TypeError("held_returns_by_interval must be a sequence")
    frozen = tuple(frozen_decisions)
    observed = tuple(held_returns_by_interval)
    if len(frozen) != len(observed):
        raise ValueError(
            "frozen_decisions and held_returns_by_interval must align"
        )
    if len(strategy.points) != len(frozen):
        raise ValueError("strategy interval count must match frozen_decisions")
    if any(not isinstance(item, FrozenDecisionTime) for item in frozen):
        raise TypeError("frozen_decisions must contain FrozenDecisionTime")
    if not frozen:
        return BenchmarkComparison(
            role=role,
            valid=True,
            reason=None,
            hard_validity_failure=False,
            active_returns=(),
            benchmark_gross_returns=(),
            holdings=None,
            reason_counts=MappingProxyType({}),
        )

    unformable = sum(1 for item in frozen if not item.benchmark_formable)
    if unformable:
        return BenchmarkComparison(
            role=role,
            valid=False,
            reason=_REASON_UNFORMABLE,
            hard_validity_failure=True,
            active_returns=tuple(None for _ in frozen),
            benchmark_gross_returns=tuple(None for _ in frozen),
            holdings=None,
            reason_counts=MappingProxyType({_REASON_UNFORMABLE: unformable}),
        )

    intervals = []
    for index, item in enumerate(frozen):
        reset = (
            frozen[index + 1].matched_benchmark_target
            if index + 1 < len(frozen)
            else None
        )
        intervals.append(
            holding_interval(
                strategy.points[index].session_date,
                observed[index],
                reset,
            )
        )
    holdings = advance_holdings(
        frozen[0].matched_benchmark_target,
        intervals,
        _COST_FREE_BPS,
        initial_equity,
    )
    active = tuple(
        _active_return(strategy_point.net_return, bench_point.gross_return)
        for strategy_point, bench_point in zip(
            strategy.points,
            holdings.points,
            strict=True,
        )
    )
    return BenchmarkComparison(
        role=role,
        valid=holdings.valid,
        reason=holdings.reason,
        hard_validity_failure=not holdings.valid,
        active_returns=active,
        benchmark_gross_returns=tuple(
            point.gross_return for point in holdings.points
        ),
        holdings=holdings,
        reason_counts=holdings.reason_counts,
    )


def spy_secondary_comparison(
    spy_returns: Sequence[object],
    strategy: ContinuousHoldings,
) -> BenchmarkComparison:
    """Retain a missing SPY date as a secondary-only invalid comparison."""

    if not isinstance(strategy, ContinuousHoldings):
        raise TypeError("strategy must be ContinuousHoldings")
    if (
        isinstance(spy_returns, (str, bytes, bytearray))
        or not isinstance(spy_returns, Sequence)
    ):
        raise TypeError("spy_returns must be a sequence")
    if len(spy_returns) != len(strategy.points):
        raise ValueError("spy_returns length must match strategy intervals")

    parsed: list[SimpleReturn] = []
    counts: dict[str, int] = {}
    valid = True
    reason: str | None = None
    for raw in spy_returns:
        item = _coerce_spy_return(raw)
        parsed.append(item)
        if not item.valid:
            valid = False
            reason = item.reason
            if item.reason is not None:
                counts[item.reason] = counts.get(item.reason, 0) + 1
    active = tuple(
        _active_return(point.net_return, item.value)
        if point.valid and item.valid
        else None
        for point, item in zip(strategy.points, parsed, strict=True)
    )
    return BenchmarkComparison(
        role=_ROLE_SPY,
        valid=valid,
        reason=reason,
        hard_validity_failure=False,
        active_returns=active,
        benchmark_gross_returns=tuple(
            item.value if item.valid else None for item in parsed
        ),
        holdings=None,
        reason_counts=MappingProxyType(counts),
    )


def _active_return(
    strategy_net: float | None,
    benchmark_gross: float | None,
) -> float | None:
    if strategy_net is None or benchmark_gross is None:
        return None
    return strategy_net - benchmark_gross


def _coerce_spy_return(raw: object) -> SimpleReturn:
    if raw is None:
        return SimpleReturn(None, False, _REASON_SPY_MISSING)
    if isinstance(raw, bool):
        return SimpleReturn(None, False, _REASON_SPY_BOOLEAN)
    if isinstance(raw, SimpleReturn):
        if raw.valid:
            return raw
        return SimpleReturn(
            None,
            False,
            raw.reason or _REASON_SPY_MISSING,
        )
    try:
        numeric = float(raw)  # type: ignore[arg-type]
    except (OverflowError, TypeError, ValueError):
        return SimpleReturn(None, False, _REASON_SPY_MISSING)
    if numeric != numeric or numeric in {float("inf"), float("-inf")}:
        return SimpleReturn(None, False, _REASON_SPY_NON_FINITE)
    return SimpleReturn(numeric, True, None)


__all__ = [
    "BenchmarkComparison",
    "factor_matched_cost_free_comparison",
    "spy_secondary_comparison",
]

"""Factor-matched primary comparison and SPY secondary routing."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from types import MappingProxyType

from campaign.eligibility import FrozenDecisionTime
from campaign.paths import (
    ContinuousHoldings,
    HoldingInterval,
    IntervalPoint,
    advance_holdings,
    holding_interval,
)
from campaign.returns import SimpleReturn
from campaign.schedule import CampaignSchedule, SignalRow


_REASON_UNFORMABLE = "BENCHMARK_UNFORMABLE"
_REASON_SPY_MISSING = "SPY_DATE_MISSING"
_REASON_SPY_BOOLEAN = "SPY_RETURN_BOOLEAN"
_REASON_SPY_NON_FINITE = "SPY_RETURN_NON_FINITE"
_ROLE_SPY = "spy_secondary"
_COST_FREE_BPS = 0.0


@dataclass(frozen=True)
class DatedHeldReturns:
    """One held-return map bound to a single schedule session."""

    session_date: str
    held_returns: MappingProxyType[bytes, object]


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


def dated_held_returns(
    session_date: str,
    held_returns: Mapping[bytes, object],
) -> DatedHeldReturns:
    """Bind one held-return map to a strict schedule session."""

    if not isinstance(held_returns, Mapping):
        raise TypeError("held_returns must be a mapping")
    return DatedHeldReturns(
        session_date=_strict_date(session_date).isoformat(),
        held_returns=MappingProxyType(dict(held_returns)),
    )


def factor_matched_cost_free_comparison(
    frozen_decisions: Sequence[FrozenDecisionTime],
    strategy: ContinuousHoldings,
    held_returns_by_interval: Sequence[DatedHeldReturns],
    initial_equity: object,
    role: str,
    schedule: CampaignSchedule,
) -> BenchmarkComparison:
    """Compare strategy net to the frozen equal-weight membership path.

    Membership is read from each FrozenDecisionTime and is never recomputed
    from later returns. Daily strategy points must be the accepted
    CampaignSchedule's exact execution-bounded span, from the first included
    execution through the execution following the last target, and map onto
    the governing monthly frozen decision. Every nonempty frozen set uses
    that span; a one-point path dated at signal close is not a substitute.
    Each frozen decision must belong to a continuously included schedule
    row, and the bounded endpoint must not exceed accepted_cutoff. Old
    holdings earn the return into execution close; the new equal-weight
    target resets at execution close. The comparison is structurally
    cost-free.
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
    if len(observed) != len(strategy.points):
        raise ValueError(
            "held_returns_by_interval must align with strategy intervals"
        )
    if any(not isinstance(item, FrozenDecisionTime) for item in frozen):
        raise TypeError("frozen_decisions must contain FrozenDecisionTime")
    if any(not isinstance(item, DatedHeldReturns) for item in observed):
        raise TypeError("held_returns_by_interval must contain DatedHeldReturns")
    _require_one_factor_identity(frozen)
    if not isinstance(schedule, CampaignSchedule):
        raise TypeError("schedule must be CampaignSchedule")
    if strategy.points:
        _require_bound_calendar(
            tuple(point.session_date for point in strategy.points),
            frozen,
            schedule,
        )
    if not frozen:
        if strategy.points:
            raise ValueError(
                "strategy interval count must match frozen_decisions"
            )
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
            active_returns=tuple(None for _ in strategy.points),
            benchmark_gross_returns=tuple(None for _ in strategy.points),
            holdings=None,
            reason_counts=MappingProxyType({_REASON_UNFORMABLE: unformable}),
        )

    intervals, initial_weights = _benchmark_intervals(
        frozen,
        observed,
        strategy.points,
    )
    holdings = advance_holdings(
        initial_weights,
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


def _benchmark_intervals(
    frozen: tuple[FrozenDecisionTime, ...],
    observed: tuple[DatedHeldReturns, ...],
    strategy_points: tuple[IntervalPoint, ...],
) -> tuple[tuple[HoldingInterval, ...], MappingProxyType[bytes, float]]:
    if len(strategy_points) == len(frozen):
        intervals = tuple(
            holding_interval(
                _aligned_session(item, observed[index], strategy_points[index]),
                observed[index].held_returns,
                (
                    frozen[index + 1].matched_benchmark_target
                    if index + 1 < len(frozen)
                    else None
                ),
            )
            for index, item in enumerate(frozen)
        )
        return intervals, frozen[0].matched_benchmark_target
    if len(strategy_points) < len(frozen):
        raise ValueError("strategy interval count must match frozen_decisions")
    for item, point in zip(observed, strategy_points, strict=True):
        if item.session_date != point.session_date:
            raise ValueError(
                "frozen decision, held returns, and strategy point must share "
                "one session identity"
            )
    governors = _governing_indices(
        frozen,
        tuple(point.session_date for point in strategy_points),
    )
    intervals = []
    for index, point in enumerate(strategy_points):
        previous = governors[index - 1] if index > 0 else None
        reset = (
            frozen[governors[index]].matched_benchmark_target
            if previous is not None and previous != governors[index]
            else None
        )
        intervals.append(
            holding_interval(
                point.session_date,
                observed[index].held_returns,
                reset,
            )
        )
    return tuple(intervals), frozen[governors[0]].matched_benchmark_target


def _governing_indices(
    frozen: tuple[FrozenDecisionTime, ...],
    session_dates: tuple[str, ...],
) -> tuple[int, ...]:
    signals = tuple(_strict_date(item.signal_date) for item in frozen)
    if len(set(signals)) != len(signals):
        raise ValueError("frozen decisions must have unique signal dates")
    governors: list[int] = []
    for session_date in session_dates:
        session = _strict_date(session_date)
        best_index = None
        best_signal = None
        for index, signal in enumerate(signals):
            if signal < session and (
                best_signal is None or signal > best_signal
            ):
                best_index = index
                best_signal = signal
        if best_index is None:
            raise ValueError(
                "frozen decision, held returns, and strategy point must share "
                "one session identity"
            )
        governors.append(best_index)
    if set(governors) != set(range(len(frozen))):
        raise ValueError("strategy interval count must match frozen_decisions")
    return tuple(governors)


def _require_one_factor_identity(frozen: tuple[FrozenDecisionTime, ...]) -> None:
    if not frozen:
        return
    factor_id = frozen[0].factor_id
    if any(item.factor_id != factor_id for item in frozen):
        raise ValueError("frozen decisions must share one factor identity")


def _require_bound_calendar(
    session_dates: tuple[str, ...],
    frozen: tuple[FrozenDecisionTime, ...],
    schedule: CampaignSchedule,
) -> None:
    sessions = _accepted_schedule_sessions(schedule)
    path = _ordered_unique_dates(session_dates, "session dates")
    _require_contiguous_slice(path, sessions)
    if not frozen:
        return
    for item in frozen:
        row = _validated_signal_row(schedule, item.signal_date)
        if not row.continuous_included:
            raise ValueError(
                "frozen decision must belong to a continuously included "
                "schedule row"
            )
    required = _execution_bounded_span(frozen, schedule)
    if path != required:
        raise ValueError(
            "session dates must match the campaign schedule's exact "
            "execution-bounded session span"
        )


def _accepted_schedule_sessions(schedule: CampaignSchedule) -> tuple[str, ...]:
    if not schedule.session_dates:
        raise ValueError("schedule session dates must be a nonempty sequence")
    return _ordered_unique_dates(
        tuple(schedule.session_dates),
        "schedule session dates",
    )


def _ordered_unique_dates(
    values: tuple[str, ...],
    label: str,
) -> tuple[str, ...]:
    parsed = tuple(_strict_date(item).isoformat() for item in values)
    if len(set(parsed)) != len(parsed):
        raise ValueError(f"{label} must be unique")
    if parsed != tuple(sorted(parsed)):
        raise ValueError(f"{label} must be strictly increasing")
    return parsed


def _require_contiguous_slice(
    path: tuple[str, ...],
    sessions: tuple[str, ...],
) -> None:
    start = None
    for index, session in enumerate(sessions):
        if session == path[0]:
            start = index
            break
    if start is None or sessions[start : start + len(path)] != path:
        raise ValueError(
            "session dates must match the campaign schedule's exact ordered "
            "session slice"
        )


def _validated_signal_row(
    schedule: CampaignSchedule,
    signal_date: str,
) -> SignalRow:
    wanted = _strict_date(signal_date).isoformat()
    matches = [row for row in schedule.signals if row.signal_date == wanted]
    if len(matches) != 1:
        raise ValueError(
            "frozen decision signal must exist on the campaign schedule"
        )
    row = matches[0]
    sessions = _accepted_schedule_sessions(schedule)
    if row.signal_date not in sessions:
        raise ValueError(
            "frozen decision signal must exist on the campaign schedule"
        )
    signal_index = sessions.index(row.signal_date)
    expected_execution = (
        sessions[signal_index + 1]
        if signal_index + 1 < len(sessions)
        else None
    )
    if row.execution_date != expected_execution:
        raise ValueError(
            "campaign schedule execution must be the session after its signal"
        )
    return row


def _execution_bounded_span(
    frozen: tuple[FrozenDecisionTime, ...],
    schedule: CampaignSchedule,
) -> tuple[str, ...]:
    first = min(frozen, key=lambda item: item.signal_date)
    last = max(frozen, key=lambda item: item.signal_date)
    start = _validated_signal_row(schedule, first.signal_date).execution_date
    if start is None:
        raise ValueError(
            "campaign schedule is missing the first included execution"
        )
    end = _following_execution(schedule, last.signal_date)
    if _strict_date(end) > _strict_date(schedule.accepted_cutoff):
        raise ValueError(
            "execution-bounded session span must not exceed accepted_cutoff"
        )
    sessions = _accepted_schedule_sessions(schedule)
    try:
        start_index = sessions.index(start)
        end_index = sessions.index(end)
    except ValueError as exc:
        raise ValueError(
            "campaign schedule is missing the execution-bounded session span"
        ) from exc
    if end_index < start_index:
        raise ValueError(
            "campaign schedule is missing the execution-bounded session span"
        )
    return sessions[start_index : end_index + 1]


def _following_execution(schedule: CampaignSchedule, signal_date: str) -> str:
    wanted = _strict_date(signal_date).isoformat()
    found = False
    for row in schedule.signals:
        if found:
            if row.execution_date is None:
                raise ValueError(
                    "campaign schedule is missing the execution following "
                    "the last target"
                )
            _validated_signal_row(schedule, row.signal_date)
            return row.execution_date
        if row.signal_date == wanted:
            found = True
    raise ValueError(
        "campaign schedule is missing the execution following the last target"
    )


def _aligned_session(
    frozen: FrozenDecisionTime,
    observed: DatedHeldReturns,
    strategy_point: IntervalPoint,
) -> str:
    session_date = strategy_point.session_date
    if (
        frozen.signal_date != session_date
        or observed.session_date != session_date
    ):
        raise ValueError(
            "frozen decision, held returns, and strategy point must share "
            "one session identity"
        )
    return session_date


def _strict_date(value: object) -> date:
    if not isinstance(value, str):
        raise ValueError("date must be strict YYYY-MM-DD")
    parsed = date.fromisoformat(value)
    if len(value) != 10 or parsed.isoformat() != value:
        raise ValueError("date must be strict YYYY-MM-DD")
    return parsed


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
    "DatedHeldReturns",
    "dated_held_returns",
    "factor_matched_cost_free_comparison",
    "spy_secondary_comparison",
]

"""Common-session schedule, labels, folds, and continuous-cutoff inclusion."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from numbers import Integral


@dataclass(frozen=True)
class SignalRow:
    """One month-end signal and its execution, label, and inclusion flags."""

    signal_date: str
    execution_date: str | None
    label_start_date: str | None
    label_end_date: str | None
    signal_index: int
    execution_index: int | None
    label_end_index: int | None
    factor_label_complete: bool
    continuous_included: bool


@dataclass(frozen=True)
class EvaluationFold:
    """One calendar-year evaluation fold, possibly a final partial year."""

    fold_year: int
    bound_end: str
    partial: bool
    signal_dates: tuple[str, ...]


@dataclass(frozen=True)
class CampaignSchedule:
    """Ordered signals, folds, and the cutoff-exclusion disposition."""

    session_dates: tuple[str, ...]
    accepted_cutoff: str
    horizon_return_rows: int
    horizon_purge_signal_axis_rows: int
    embargo_rows: int
    first_fold_year: int
    signals: tuple[SignalRow, ...]
    folds: tuple[EvaluationFold, ...]
    campaign_invalid: bool


def build_campaign_schedule(
    session_dates: Sequence[str],
    accepted_cutoff: str,
    horizon_return_rows: int,
    horizon_purge_signal_axis_rows: int,
    embargo_rows: int,
    first_fold_year: int,
) -> CampaignSchedule:
    """Build the common-session signal schedule from supplied session dates."""

    sessions = _parse_session_dates(session_dates)
    cutoff = _strict_date(accepted_cutoff)
    horizon = _nonneg_int(horizon_return_rows, "horizon_return_rows")
    purge = _nonneg_int(
        horizon_purge_signal_axis_rows, "horizon_purge_signal_axis_rows"
    )
    embargo = _nonneg_int(embargo_rows, "embargo_rows")
    fold_floor = _year_int(first_fold_year, "first_fold_year")
    if purge != horizon + 1:
        raise ValueError(
            "horizon_purge_signal_axis_rows must equal "
            "horizon_return_rows + 1"
        )

    last_index_by_month: dict[tuple[int, int], int] = {}
    for index, session in enumerate(sessions):
        last_index_by_month[(session.year, session.month)] = index
    signal_indices = tuple(last_index_by_month.values())

    iso_sessions = tuple(session.isoformat() for session in sessions)
    last_usable_index = len(sessions) - 1 - embargo

    rows: list[SignalRow] = []
    for position, signal_index in enumerate(signal_indices):
        execution_index = signal_index + 1
        label_end_index = signal_index + purge
        execution_date = (
            sessions[execution_index].isoformat()
            if execution_index < len(sessions)
            else None
        )
        label_end_date = (
            sessions[label_end_index].isoformat()
            if label_end_index < len(sessions)
            else None
        )
        label_complete = (
            execution_date is not None
            and label_end_date is not None
            and label_end_index <= last_usable_index
            and sessions[label_end_index] <= cutoff
        )
        next_execution_date = None
        if position + 1 < len(signal_indices):
            next_execution_index = signal_indices[position + 1] + 1
            if next_execution_index < len(sessions):
                next_execution_date = sessions[next_execution_index]
        continuous_included = (
            next_execution_date is not None
            and next_execution_date <= cutoff
        )
        rows.append(
            SignalRow(
                signal_date=sessions[signal_index].isoformat(),
                execution_date=execution_date,
                label_start_date=execution_date,
                label_end_date=label_end_date,
                signal_index=signal_index,
                execution_index=(
                    execution_index if execution_date is not None else None
                ),
                label_end_index=(
                    label_end_index if label_end_date is not None else None
                ),
                factor_label_complete=label_complete,
                continuous_included=continuous_included,
            )
        )

    first_year = max(fold_floor, sessions[0].year)
    last_year = cutoff.year
    folds: list[EvaluationFold] = []
    for year in range(first_year, last_year + 1):
        year_end = date(year, 12, 31)
        partial = year == cutoff.year and cutoff != year_end
        bound_end = cutoff if year == cutoff.year else year_end
        fold_signals = tuple(
            row.signal_date
            for row in rows
            if _strict_date(row.signal_date).year == year
            and row.factor_label_complete
            and row.label_end_date is not None
            and _strict_date(row.label_end_date) <= bound_end
        )
        folds.append(
            EvaluationFold(
                fold_year=year,
                bound_end=bound_end.isoformat(),
                partial=partial,
                signal_dates=fold_signals,
            )
        )

    return CampaignSchedule(
        session_dates=iso_sessions,
        accepted_cutoff=cutoff.isoformat(),
        horizon_return_rows=horizon,
        horizon_purge_signal_axis_rows=purge,
        embargo_rows=embargo,
        first_fold_year=fold_floor,
        signals=tuple(rows),
        folds=tuple(folds),
        campaign_invalid=False,
    )


def _parse_session_dates(session_dates: Sequence[str]) -> tuple[date, ...]:
    if (
        isinstance(session_dates, (str, bytes, bytearray))
        or not isinstance(session_dates, Sequence)
        or not session_dates
    ):
        raise ValueError("session_dates must be a nonempty sequence")
    parsed = tuple(_strict_date(value) for value in session_dates)
    if len(set(parsed)) != len(parsed):
        raise ValueError("session_dates must be unique")
    if parsed != tuple(sorted(parsed)):
        raise ValueError("session_dates must be strictly increasing")
    return parsed


def _strict_date(value: object) -> date:
    if not isinstance(value, str):
        raise ValueError("date must be strict YYYY-MM-DD")
    parsed = date.fromisoformat(value)
    if len(value) != 10 or parsed.isoformat() != value:
        raise ValueError("date must be strict YYYY-MM-DD")
    return parsed


def _nonneg_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer")
    integer = int(value)
    if integer < 0:
        raise ValueError(f"{name} must be nonnegative")
    return integer


def _year_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer")
    return int(value)


__all__ = [
    "CampaignSchedule",
    "EvaluationFold",
    "SignalRow",
    "build_campaign_schedule",
]

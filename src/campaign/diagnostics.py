"""Rank IC, decile-curve, coverage, yearly/LOYO, and turnover diagnostics."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import math
from numbers import Integral, Real
from types import MappingProxyType

from campaign.deciles import DecileBucket
from campaign.inference import (
    CommonCompleteCaseRankICRecord,
    FactorRobustness,
    FactorVector,
    rank_ic_robustness,
)
from campaign.turnover import factor_target_turnover


_REASON_DISTINCT_FACTORS = "DISTINCT_FACTOR_VALUE_COUNT_BELOW_FLOOR"
_REASON_DISTINCT_RETURNS = "DISTINCT_FORWARD_RETURN_COUNT_BELOW_FLOOR"
_REASON_EMPTY_DECILE = "EMPTY_DECILE"
_REASON_MISSING_FORWARD_RETURN = "FORWARD_RETURN_MISSING"
_REASON_INVALID_FORWARD_RETURN = "FORWARD_RETURN_INVALID"
_REASON_INSUFFICIENT_VALUES = "INSUFFICIENT_VALUES"
_LOW_DECILE = "D1"


@dataclass(frozen=True)
class RankICResult:
    """One retained cross-sectional Spearman Rank IC or invalid reason."""

    value: float | None
    valid: bool
    reason: str | None
    distinct_factor_values: int
    distinct_forward_returns: int


@dataclass(frozen=True)
class DecileCurve:
    """Decile means, spread, and adjacent monotonicity, or an invalid reason."""

    means: MappingProxyType[str, float]
    spread: float | None
    adjacent_differences: tuple[float, ...]
    monotonicity_share: float | None
    fully_monotone: bool | None
    valid: bool
    reason: str | None


@dataclass(frozen=True)
class LabelCoverage:
    """Eligible-label completeness for one factor-month."""

    eligible_count: int
    valid_label_count: int
    missing_label_count: int
    all_eligible_labels_valid: bool


@dataclass(frozen=True)
class DescriptiveRankIC:
    """All-valid-month descriptive Rank IC summaries."""

    count: int
    mean: float | None
    median: float | None
    sample_std: float | None
    monthly_icir: float | None
    valid: bool
    reason: str | None


@dataclass(frozen=True)
class YearlyRankIC:
    """One calendar-year Rank IC mean and its contribution to the full mean."""

    year: int
    count: int
    mean: float
    contribution: float


@dataclass(frozen=True)
class CommonCaseMonth:
    """One already-computed common-complete-case Rank IC month."""

    signal_year: int
    label_intersection_years: tuple[int, ...]
    rank_ics: tuple[float, float, float]


def spearman_rank_ic(
    pairs: Sequence[object],
    min_distinct_factor_values: int,
    min_distinct_forward_returns: int,
) -> RankICResult:
    """Spearman Rank IC: average tie ranks, then Pearson of the rank vectors."""

    if (
        isinstance(pairs, (str, bytes, bytearray))
        or not isinstance(pairs, Sequence)
    ):
        raise TypeError("pairs must be a sequence")
    floor_factors = _nonneg_int(
        min_distinct_factor_values,
        "min_distinct_factor_values",
    )
    floor_returns = _nonneg_int(
        min_distinct_forward_returns,
        "min_distinct_forward_returns",
    )

    factors: list[float] = []
    returns: list[float] = []
    for item in pairs:
        try:
            factor_value, forward_return = item  # type: ignore[misc]
        except (TypeError, ValueError) as exc:
            raise TypeError(
                "pairs must be (factor_value, forward_return) pairs"
            ) from exc
        if factor_value is None or forward_return is None:
            return _invalid_rank_ic(
                _REASON_MISSING_FORWARD_RETURN,
                factors,
                returns,
            )
        if not _is_finite_real(factor_value) or not _is_finite_real(
            forward_return
        ):
            return _invalid_rank_ic(
                _REASON_INVALID_FORWARD_RETURN,
                factors,
                returns,
            )
        factors.append(float(factor_value))
        returns.append(float(forward_return))

    distinct_factors = len(set(factors))
    distinct_returns = len(set(returns))
    if distinct_factors < floor_factors:
        return RankICResult(
            None,
            False,
            _REASON_DISTINCT_FACTORS,
            distinct_factors,
            distinct_returns,
        )
    if distinct_returns < floor_returns:
        return RankICResult(
            None,
            False,
            _REASON_DISTINCT_RETURNS,
            distinct_factors,
            distinct_returns,
        )
    return RankICResult(
        _pearson(_average_ranks(factors), _average_ranks(returns)),
        True,
        None,
        distinct_factors,
        distinct_returns,
    )


def decile_return_curve(
    deciles: Sequence[DecileBucket],
    forward_returns: Mapping[bytes, object],
    quantile_count: int,
) -> DecileCurve:
    """Mean forward return by D1..D{quantile_count}, plus spread and gaps."""

    if (
        isinstance(deciles, (str, bytes, bytearray))
        or not isinstance(deciles, Sequence)
    ):
        raise TypeError("deciles must be a sequence")
    if not isinstance(forward_returns, Mapping):
        raise TypeError("forward_returns must be a mapping")
    count = _positive_int(quantile_count, "quantile_count")
    buckets = tuple(deciles)
    if len(buckets) != count:
        raise ValueError("deciles must contain quantile_count buckets")

    means: dict[str, float] = {}
    for index, bucket in enumerate(buckets):
        expected = f"D{index + 1}"
        if not isinstance(bucket, DecileBucket) or bucket.label != expected:
            raise ValueError("deciles must be labelled D1 through D{n}")
        if not bucket.members:
            return _invalid_curve(_REASON_EMPTY_DECILE)
        values: list[float] = []
        for member in bucket.members:
            if member.listing_key not in forward_returns:
                return _invalid_curve(_REASON_MISSING_FORWARD_RETURN)
            raw = forward_returns[member.listing_key]
            if not _is_finite_real(raw):
                return _invalid_curve(_REASON_INVALID_FORWARD_RETURN)
            values.append(float(raw))
        means[bucket.label] = sum(values) / len(values)

    adjacent = tuple(
        means[f"D{index + 1}"] - means[f"D{index}"]
        for index in range(1, count)
    )
    gaps = count - 1
    nonnegative = sum(1 for difference in adjacent if difference >= 0.0)
    high_label = f"D{count}"
    return DecileCurve(
        means=MappingProxyType(means),
        spread=means[high_label] - means[_LOW_DECILE],
        adjacent_differences=adjacent,
        monotonicity_share=nonnegative / gaps,
        fully_monotone=nonnegative == gaps,
        valid=True,
        reason=None,
    )


def label_coverage(
    eligible_keys: Sequence[bytes],
    forward_returns: Mapping[bytes, object],
) -> LabelCoverage:
    """Count valid and missing execution-to-endpoint labels for eligible keys."""

    if (
        isinstance(eligible_keys, (str, bytes, bytearray))
        or not isinstance(eligible_keys, Sequence)
    ):
        raise TypeError("eligible_keys must be a sequence")
    if not isinstance(forward_returns, Mapping):
        raise TypeError("forward_returns must be a mapping")
    valid = 0
    missing = 0
    for listing_key in eligible_keys:
        if not isinstance(listing_key, bytes) or not listing_key:
            raise TypeError("eligible_keys must contain nonempty bytes")
        if _is_finite_real(forward_returns.get(listing_key)):
            valid += 1
        else:
            missing += 1
    return LabelCoverage(
        eligible_count=len(eligible_keys),
        valid_label_count=valid,
        missing_label_count=missing,
        all_eligible_labels_valid=missing == 0,
    )


def descriptive_rank_ic(
    values: Sequence[object],
    sample_std_ddof: int,
) -> DescriptiveRankIC:
    """Mean, median, sample standard deviation, and monthly ICIR."""

    if (
        isinstance(values, (str, bytes, bytearray))
        or not isinstance(values, Sequence)
    ):
        raise TypeError("values must be a sequence")
    ddof = _nonneg_int(sample_std_ddof, "sample_std_ddof")
    numeric = tuple(_finite_real(value, "rank_ic") for value in values)
    count = len(numeric)
    if count == 0:
        return DescriptiveRankIC(
            0,
            None,
            None,
            None,
            None,
            False,
            _REASON_INSUFFICIENT_VALUES,
        )
    mean = sum(numeric) / count
    ordered = sorted(numeric)
    if count % 2:
        median = ordered[count // 2]
    else:
        median = (ordered[count // 2 - 1] + ordered[count // 2]) / 2.0
    if count <= ddof:
        return DescriptiveRankIC(
            count,
            mean,
            median,
            None,
            None,
            True,
            None,
        )
    variance = sum((value - mean) ** 2 for value in numeric) / (count - ddof)
    sample_std = math.sqrt(variance)
    monthly_icir = None if sample_std == 0.0 else mean / sample_std
    return DescriptiveRankIC(
        count,
        mean,
        median,
        sample_std,
        monthly_icir,
        True,
        None,
    )


def yearly_rank_ic_contributions(
    months: Sequence[object],
) -> tuple[YearlyRankIC, ...]:
    """Group valid months by signal year and report mean contributions."""

    if (
        isinstance(months, (str, bytes, bytearray))
        or not isinstance(months, Sequence)
    ):
        raise TypeError("months must be a sequence")
    grouped: dict[int, list[float]] = {}
    for item in months:
        try:
            year, value = item  # type: ignore[misc]
        except (TypeError, ValueError) as exc:
            raise TypeError("months must be (year, rank_ic) pairs") from exc
        grouped.setdefault(_year_int(year, "year"), []).append(
            _finite_real(value, "rank_ic")
        )
    total = sum(len(values) for values in grouped.values())
    if total == 0:
        return ()
    rows: list[YearlyRankIC] = []
    for year in sorted(grouped):
        values = grouped[year]
        mean = sum(values) / len(values)
        rows.append(
            YearlyRankIC(
                year=year,
                count=len(values),
                mean=mean,
                contribution=len(values) * mean / total,
            )
        )
    return tuple(rows)


def common_case_robustness(
    records: Sequence[CommonCaseMonth],
    required_years: Sequence[int],
) -> FactorVector[FactorRobustness]:
    """Assemble owner-ordered common-case records and evaluate robustness."""

    if (
        isinstance(records, (str, bytes, bytearray))
        or not isinstance(records, Sequence)
    ):
        raise TypeError("records must be a sequence")
    prepared: list[CommonCompleteCaseRankICRecord] = []
    for record in records:
        if not isinstance(record, CommonCaseMonth):
            raise TypeError("records must contain CommonCaseMonth values")
        if len(record.rank_ics) != 3:
            raise ValueError("rank_ics must contain three owner-ordered values")
        prepared.append(
            CommonCompleteCaseRankICRecord(
                signal_year=record.signal_year,
                label_intersection_years=record.label_intersection_years,
                rank_ics=FactorVector(*record.rank_ics),
            )
        )
    return rank_ic_robustness(prepared, required_years=required_years)


def scheduled_target_turnovers(
    scheduled_targets: Sequence[Mapping[bytes, object]],
) -> tuple[float | None, ...]:
    """Target-to-target turnover over the scheduled frozen-target chain."""

    if (
        isinstance(scheduled_targets, (str, bytes, bytearray))
        or not isinstance(scheduled_targets, Sequence)
    ):
        raise TypeError("scheduled_targets must be a sequence")
    if not scheduled_targets:
        return ()
    turnovers: list[float | None] = [None]
    for previous, current in zip(
        scheduled_targets,
        scheduled_targets[1:],
        strict=False,
    ):
        turnovers.append(factor_target_turnover(previous, current))
    return tuple(turnovers)


def _average_ranks(values: Sequence[float]) -> tuple[float, ...]:
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(values)
    index = 0
    while index < len(values):
        end = index + 1
        while (
            end < len(values)
            and values[order[end]] == values[order[index]]
        ):
            end += 1
        average = (index + 1 + end) / 2.0
        for position in range(index, end):
            ranks[order[position]] = average
        index = end
    return tuple(ranks)


def _pearson(left: Sequence[float], right: Sequence[float]) -> float:
    count = len(left)
    left_mean = sum(left) / count
    right_mean = sum(right) / count
    numerator = sum(
        (left_value - left_mean) * (right_value - right_mean)
        for left_value, right_value in zip(left, right, strict=True)
    )
    left_ss = sum((value - left_mean) ** 2 for value in left)
    right_ss = sum((value - right_mean) ** 2 for value in right)
    return numerator / math.sqrt(left_ss * right_ss)


def _invalid_rank_ic(
    reason: str,
    factors: Sequence[float],
    returns: Sequence[float],
) -> RankICResult:
    return RankICResult(
        None,
        False,
        reason,
        len(set(factors)),
        len(set(returns)),
    )


def _invalid_curve(reason: str) -> DecileCurve:
    return DecileCurve(
        means=MappingProxyType({}),
        spread=None,
        adjacent_differences=(),
        monotonicity_share=None,
        fully_monotone=None,
        valid=False,
        reason=reason,
    )


def _is_finite_real(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, Real):
        return False
    numeric = float(value)
    return math.isfinite(numeric)


def _finite_real(value: object, name: str) -> float:
    if not _is_finite_real(value):
        raise TypeError(f"{name} must be a finite real non-Boolean scalar")
    return float(value)  # type: ignore[arg-type]


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


def _positive_int(value: object, name: str) -> int:
    integer = _nonneg_int(value, name)
    if integer < 1:
        raise ValueError(f"{name} must be positive")
    return integer


__all__ = [
    "CommonCaseMonth",
    "DecileCurve",
    "DescriptiveRankIC",
    "LabelCoverage",
    "RankICResult",
    "YearlyRankIC",
    "common_case_robustness",
    "decile_return_curve",
    "descriptive_rank_ic",
    "label_coverage",
    "scheduled_target_turnovers",
    "spearman_rank_ic",
    "yearly_rank_ic_contributions",
]

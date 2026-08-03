"""Frozen dataset-independent inference computations for prepared inputs."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math
from numbers import Integral, Real
from typing import Generic, TypeVar

import numpy as np


FACTOR_ORDER = ("MOM_12_1", "REV_1M", "LOW_VOL_3M")
HOLM_ALPHA = 0.05
LONG_SEGMENT_BLOCK_LENGTH = 6

_T = TypeVar("_T")


@dataclass(frozen=True)
class FactorVector(Generic[_T]):
    """Values explicitly bound to the frozen three-factor order."""

    MOM_12_1: _T
    REV_1M: _T
    LOW_VOL_3M: _T


@dataclass(frozen=True)
class HolmResult:
    """Frozen Holm decisions and their named factor binding."""

    factor_order: tuple[str, str, str]
    sorted_factor_ids: tuple[str, str, str]
    multiplied_sorted: tuple[float, float, float]
    adjusted_sorted: tuple[float, float, float]
    adjusted_p_values: FactorVector[float]
    rejections: FactorVector[bool]
    rejected_factor_ids: tuple[str, ...]


@dataclass(frozen=True)
class BootstrapResult:
    """Bootstrap distributions and summaries bound to ``factor_order``."""

    factor_order: tuple[str, str, str]
    observed_means: FactorVector[float]
    uncentered_bootstrap_means: np.ndarray
    null_centered_bootstrap_means: np.ndarray
    percentile_interval_95: FactorVector[tuple[float, float]]
    one_sided_p_values: FactorVector[float]
    support_by_factor: FactorVector[bool]
    bootstrap_support_all_three_factors: bool


@dataclass(frozen=True)
class CommonCompleteCaseRankICRecord:
    """One already-prepared common-complete-case monthly Rank IC record."""

    signal_year: int
    label_intersection_years: tuple[int, ...]
    rank_ics: FactorVector[float]


@dataclass(frozen=True)
class FactorRobustness:
    """Final-state robustness summaries for one named factor."""

    positive_year_fraction: float
    all_leave_one_year_out_means_positive: bool


def holm_adjust(raw_p_values: FactorVector[object]) -> HolmResult:
    """Apply the frozen three-test Holm procedure at familywise alpha 0.05."""

    if not isinstance(raw_p_values, FactorVector):
        raise TypeError("raw_p_values must be a FactorVector")
    raw = tuple(
        _coerce_probability(value, name=f"raw_p_values.{factor_id}")
        for factor_id, value in zip(
            FACTOR_ORDER,
            _factor_values(raw_p_values),
            strict=True,
        )
    )
    sorted_indices = tuple(
        sorted(range(3), key=lambda index: (raw[index], index))
    )
    sorted_p_values = tuple(raw[index] for index in sorted_indices)
    multiplied_sorted = tuple(
        (3 - sorted_index) * raw_p_value
        for sorted_index, raw_p_value in enumerate(sorted_p_values)
    )

    adjusted_values: list[float] = []
    running_maximum = 0.0
    for multiplied in multiplied_sorted:
        running_maximum = max(running_maximum, multiplied)
        adjusted_values.append(min(1.0, running_maximum))
    adjusted_sorted = tuple(adjusted_values)

    adjusted_original = [0.0, 0.0, 0.0]
    rejected_original = [False, False, False]
    for sorted_position, original_index in enumerate(sorted_indices):
        adjusted_original[original_index] = adjusted_sorted[sorted_position]
    for sorted_position, raw_p_value in enumerate(sorted_p_values):
        if raw_p_value > HOLM_ALPHA / (3 - sorted_position):
            break
        rejected_original[sorted_indices[sorted_position]] = True

    rejections = _factor_vector(rejected_original)
    return HolmResult(
        factor_order=FACTOR_ORDER,
        sorted_factor_ids=tuple(FACTOR_ORDER[index] for index in sorted_indices),
        multiplied_sorted=multiplied_sorted,
        adjusted_sorted=adjusted_sorted,
        adjusted_p_values=_factor_vector(adjusted_original),
        rejections=rejections,
        rejected_factor_ids=tuple(
            factor_id
            for factor_id, rejected in zip(
                FACTOR_ORDER,
                _factor_values(rejections),
                strict=True,
            )
            if rejected
        ),
    )


def draw_segment_indices(
    segment_length: int,
    *,
    rng: np.random.Generator,
) -> tuple[int, ...]:
    """Draw one circular moving-block index vector for a prepared segment."""

    if isinstance(segment_length, bool) or not isinstance(segment_length, Integral):
        raise TypeError("segment_length must be an integer")
    length = int(segment_length)
    if length < 1:
        raise ValueError("segment_length must be positive")

    block_length = LONG_SEGMENT_BLOCK_LENGTH if length > 6 else 1
    block_count = math.ceil(length / block_length)
    starts = rng.integers(
        low=0,
        high=length,
        size=block_count,
        endpoint=False,
    )
    flattened_starts = np.asarray(starts).reshape(-1)
    if len(flattened_starts) != block_count:
        raise ValueError("rng returned the wrong number of block starts")

    indices: list[int] = []
    for raw_start in flattened_starts:
        start = int(raw_start)
        if start < 0 or start >= length:
            raise ValueError("rng returned an out-of-range block start")
        indices.extend(
            (start + offset) % length
            for offset in range(block_length)
        )
    return tuple(indices[:length])


def bootstrap_mean_rank_ic(
    segments: Sequence[Sequence[tuple[float, float, float]]],
    *,
    bootstrap_seed: int,
    replicates: int,
) -> BootstrapResult:
    """Bootstrap already-prepared numeric Rank IC segments jointly by row."""

    prepared = _prepare_numeric_segments(segments)
    seed = _coerce_nonnegative_integer(bootstrap_seed, name="bootstrap_seed")
    replicate_count = _coerce_positive_integer(replicates, name="replicates")
    retained_rows = tuple(row for segment in prepared for row in segment)
    observed = tuple(
        sum(row[factor_index] for row in retained_rows) / len(retained_rows)
        for factor_index in range(3)
    )
    centered = tuple(
        tuple(row[index] - observed[index] for index in range(3))
        for row in retained_rows
    )

    segment_offsets: list[int] = []
    offset = 0
    for segment in prepared:
        segment_offsets.append(offset)
        offset += len(segment)

    uncentered_means = np.empty((replicate_count, 3), dtype=float)
    null_centered_means = np.empty((replicate_count, 3), dtype=float)
    rng = np.random.Generator(np.random.PCG64DXSM(seed))
    total_count = len(retained_rows)

    for replicate_index in range(replicate_count):
        uncentered_sums = [0.0, 0.0, 0.0]
        centered_sums = [0.0, 0.0, 0.0]
        for segment, segment_offset in zip(
            prepared,
            segment_offsets,
            strict=True,
        ):
            local_indices = draw_segment_indices(len(segment), rng=rng)
            for local_index in local_indices:
                row = segment[local_index]
                centered_row = centered[segment_offset + local_index]
                for factor_index in range(3):
                    uncentered_sums[factor_index] += row[factor_index]
                    centered_sums[factor_index] += centered_row[factor_index]
        for factor_index in range(3):
            uncentered_means[replicate_index, factor_index] = (
                uncentered_sums[factor_index] / total_count
            )
            null_centered_means[replicate_index, factor_index] = (
                centered_sums[factor_index] / total_count
            )

    interval = np.quantile(
        uncentered_means,
        [0.025, 0.975],
        axis=0,
        method="linear",
    )
    p_values = tuple(
        (
            1
            + int(
                np.count_nonzero(
                    null_centered_means[:, factor_index]
                    >= observed[factor_index]
                )
            )
        )
        / (replicate_count + 1)
        for factor_index in range(3)
    )
    has_resampling_segment = any(len(segment) >= 2 for segment in prepared)
    support = tuple(
        has_resampling_segment
        and len(np.unique(null_centered_means[:, factor_index])) >= 2
        for factor_index in range(3)
    )

    uncentered_means.setflags(write=False)
    null_centered_means.setflags(write=False)
    support_vector = _factor_vector(support)
    return BootstrapResult(
        factor_order=FACTOR_ORDER,
        observed_means=_factor_vector(observed),
        uncentered_bootstrap_means=uncentered_means,
        null_centered_bootstrap_means=null_centered_means,
        percentile_interval_95=_factor_vector(
            tuple(
                (float(interval[0, index]), float(interval[1, index]))
                for index in range(3)
            )
        ),
        one_sided_p_values=_factor_vector(p_values),
        support_by_factor=support_vector,
        bootstrap_support_all_three_factors=all(
            _factor_values(support_vector)
        ),
    )


def rank_ic_robustness(
    records: Sequence[CommonCompleteCaseRankICRecord],
    *,
    required_years: Sequence[int],
) -> FactorVector[FactorRobustness]:
    """Evaluate robustness using common-complete-case records exclusively."""

    validated_years = _validate_required_years(required_years)
    validated_records = tuple(_validate_common_record(record) for record in records)
    results: list[FactorRobustness] = []

    for factor_index in range(3):
        positive_year_count = 0
        all_required_years_present = True
        for year in validated_years:
            year_values = [
                _factor_values(record.rank_ics)[factor_index]
                for record in validated_records
                if record.signal_year == year
            ]
            if not year_values:
                all_required_years_present = False
                continue
            if sum(year_values) / len(year_values) > 0.0:
                positive_year_count += 1

        all_omission_means_positive = all_required_years_present
        if all_omission_means_positive:
            for omitted_year in validated_years:
                remaining_values = [
                    _factor_values(record.rank_ics)[factor_index]
                    for record in validated_records
                    if omitted_year not in record.label_intersection_years
                ]
                if (
                    not remaining_values
                    or sum(remaining_values) / len(remaining_values) <= 0.0
                ):
                    all_omission_means_positive = False
                    break

        results.append(
            FactorRobustness(
                positive_year_fraction=(
                    positive_year_count / len(validated_years)
                ),
                all_leave_one_year_out_means_positive=(
                    all_omission_means_positive
                ),
            )
        )

    return _factor_vector(results)


def _prepare_numeric_segments(
    segments: Sequence[Sequence[tuple[float, float, float]]],
) -> tuple[tuple[tuple[float, float, float], ...], ...]:
    if isinstance(segments, (str, bytes, bytearray)) or not isinstance(
        segments, Sequence
    ):
        raise TypeError("segments must be a sequence of numeric segments")
    if not segments:
        raise ValueError("segments must not be empty")

    prepared_segments: list[tuple[tuple[float, float, float], ...]] = []
    for segment in segments:
        if isinstance(segment, (str, bytes, bytearray)) or not isinstance(
            segment, Sequence
        ):
            raise TypeError("each segment must be a sequence")
        if not segment:
            raise ValueError("segments must not contain empty segments")
        prepared_rows: list[tuple[float, float, float]] = []
        for row in segment:
            if isinstance(row, (str, bytes, bytearray)) or not isinstance(
                row, Sequence
            ):
                raise TypeError("each Rank IC row must be a numeric sequence")
            if len(row) != 3:
                raise ValueError("each Rank IC row must contain three factors")
            prepared_rows.append(
                tuple(
                    _coerce_finite_real(value, name="Rank IC value")
                    for value in row
                )
            )
        prepared_segments.append(tuple(prepared_rows))
    return tuple(prepared_segments)


def _validate_required_years(required_years: Sequence[int]) -> tuple[int, ...]:
    if isinstance(required_years, (str, bytes, bytearray)) or not isinstance(
        required_years, Sequence
    ):
        raise TypeError("required_years must be a sequence of integers")
    years = tuple(
        _coerce_integer(year, name="required year") for year in required_years
    )
    if not years:
        raise ValueError("required_years must not be empty")
    if len(set(years)) != len(years):
        raise ValueError("required_years must be unique")
    if years != tuple(sorted(years)):
        raise ValueError("required_years must be sorted")
    return years


def _validate_common_record(
    record: CommonCompleteCaseRankICRecord,
) -> CommonCompleteCaseRankICRecord:
    if not isinstance(record, CommonCompleteCaseRankICRecord):
        raise TypeError(
            "records must contain CommonCompleteCaseRankICRecord values"
        )
    signal_year = _coerce_integer(record.signal_year, name="signal_year")
    intersection_years = tuple(
        _coerce_integer(year, name="label intersection year")
        for year in record.label_intersection_years
    )
    if len(set(intersection_years)) != len(intersection_years):
        raise ValueError("label_intersection_years must be unique")
    if not isinstance(record.rank_ics, FactorVector):
        raise TypeError("rank_ics must be a FactorVector")
    rank_ics = _factor_vector(
        tuple(
            _coerce_finite_real(value, name=f"rank_ics.{factor_id}")
            for factor_id, value in zip(
                FACTOR_ORDER,
                _factor_values(record.rank_ics),
                strict=True,
            )
        )
    )
    return CommonCompleteCaseRankICRecord(
        signal_year=signal_year,
        label_intersection_years=intersection_years,
        rank_ics=rank_ics,
    )


def _factor_values(vector: FactorVector[_T]) -> tuple[_T, _T, _T]:
    return (vector.MOM_12_1, vector.REV_1M, vector.LOW_VOL_3M)


def _factor_vector(values: Sequence[_T]) -> FactorVector[_T]:
    if len(values) != 3:
        raise ValueError("factor vector must contain exactly three values")
    return FactorVector(values[0], values[1], values[2])


def _coerce_probability(value: object, *, name: str) -> float:
    numeric = _coerce_finite_real(value, name=name)
    if numeric < 0.0 or numeric > 1.0:
        raise ValueError(f"{name} must be between zero and one")
    return numeric


def _coerce_finite_real(value: object, *, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real non-Boolean scalar")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError(f"{name} must be finite")
    return numeric


def _coerce_integer(value: object, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer")
    return int(value)


def _coerce_nonnegative_integer(value: object, *, name: str) -> int:
    integer = _coerce_integer(value, name=name)
    if integer < 0:
        raise ValueError(f"{name} must be nonnegative")
    return integer


def _coerce_positive_integer(value: object, *, name: str) -> int:
    integer = _coerce_integer(value, name=name)
    if integer < 1:
        raise ValueError(f"{name} must be positive")
    return integer


__all__ = [
    "FACTOR_ORDER",
    "BootstrapResult",
    "CommonCompleteCaseRankICRecord",
    "FactorRobustness",
    "FactorVector",
    "HolmResult",
    "bootstrap_mean_rank_ic",
    "draw_segment_indices",
    "holm_adjust",
    "rank_ic_robustness",
]

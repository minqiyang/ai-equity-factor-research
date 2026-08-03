"""Golden tests for frozen Holm and prepared-segment bootstrap inference."""

from __future__ import annotations

import hashlib
import itertools
import json

import numpy as np
import pytest

from campaign.inference import (
    FACTOR_ORDER,
    FactorVector,
    bootstrap_mean_rank_ic,
    draw_segment_indices,
    holm_adjust,
)


def _values(vector: FactorVector[object]) -> tuple[object, object, object]:
    return (vector.MOM_12_1, vector.REV_1M, vector.LOW_VOL_3M)


def _prepared_segments(
    table: np.ndarray,
    lengths: tuple[int, ...],
) -> tuple[tuple[tuple[float, float, float], ...], ...]:
    segments = []
    start = 0
    for length in lengths:
        segments.append(
            tuple(
                tuple(float(value) for value in row)
                for row in table[start : start + length]
            )
        )
        start += length
    return tuple(segments)


def test_holm_one_based_running_max_and_factor_mapping_golden_fixture() -> None:
    result = holm_adjust(FactorVector(0.04, 0.01, 0.03))

    assert result.factor_order == FACTOR_ORDER == (
        "MOM_12_1",
        "REV_1M",
        "LOW_VOL_3M",
    )
    assert result.sorted_factor_ids == (
        "REV_1M",
        "LOW_VOL_3M",
        "MOM_12_1",
    )
    assert result.multiplied_sorted == (0.03, 0.06, 0.04)
    assert result.adjusted_sorted == (0.03, 0.06, 0.06)
    assert _values(result.adjusted_p_values) == (0.06, 0.03, 0.06)
    assert result.rejected_factor_ids == ("REV_1M",)


def test_holm_ties_follow_the_frozen_factor_order() -> None:
    result = holm_adjust(FactorVector(0.01, 0.01, 0.01))
    assert result.sorted_factor_ids == FACTOR_ORDER
    assert _values(result.rejections) == (True, True, True)


def test_bootstrap_reuses_segment_draws_for_both_distributions() -> None:
    row_index = np.arange(15, dtype=float)
    factor_table = np.column_stack(
        (
            row_index / 100.0,
            (14.0 - row_index) / 200.0,
            ((row_index % 4.0) - 1.5) / 100.0,
        )
    )
    rng = np.random.Generator(np.random.PCG64DXSM(20260730))

    replicate_indices = []
    for _ in range(3):
        first = draw_segment_indices(8, rng=rng)
        second = draw_segment_indices(7, rng=rng)
        replicate_indices.append(first + tuple(8 + index for index in second))
    replicate_indices = tuple(replicate_indices)
    expected_replicate_indices = (
        (2, 3, 4, 5, 6, 7, 2, 3, 11, 12, 13, 14, 8, 9, 12),
        (2, 3, 4, 5, 6, 7, 7, 0, 14, 8, 9, 10, 11, 12, 8),
        (0, 1, 2, 3, 4, 5, 3, 4, 12, 13, 14, 8, 9, 10, 14),
    )
    result = bootstrap_mean_rank_ic(
        _prepared_segments(factor_table, (8, 7)),
        bootstrap_seed=20260730,
        replicates=3,
    )
    expected_uncentered_means = np.asarray(
        [
            [0.074, 0.033, 0.0003333333333333334],
            [0.07066666666666667, 0.034666666666666665, -0.00033333333333333294],
            [0.068, 0.036000000000000004, -0.0030000000000000005],
        ]
    )
    expected_null_centered_means = np.asarray(
        [
            [0.0039999999999999975, -0.0020000000000000035, 0.0013333333333333335],
            [0.0006666666666666636, -0.0003333333333333359, 0.0006666666666666673],
            [-0.0020000000000000057, 0.000999999999999998, -0.002],
        ]
    )

    assert replicate_indices == expected_replicate_indices
    assert result.factor_order == FACTOR_ORDER
    np.testing.assert_allclose(
        _values(result.observed_means),
        [0.07, 0.035, -0.001],
    )
    np.testing.assert_allclose(
        result.uncentered_bootstrap_means,
        expected_uncentered_means,
        rtol=0.0,
        atol=1e-15,
    )
    np.testing.assert_allclose(
        result.null_centered_bootstrap_means,
        expected_null_centered_means,
        rtol=0.0,
        atol=1e-15,
    )
    np.testing.assert_allclose(
        result.null_centered_bootstrap_means,
        result.uncentered_bootstrap_means
        - np.asarray(_values(result.observed_means)),
        rtol=0.0,
        atol=1e-15,
    )

    forbidden_second_pass_indices = []
    for _ in range(3):
        first = draw_segment_indices(8, rng=rng)
        second = draw_segment_indices(7, rng=rng)
        forbidden_second_pass_indices.append(
            first + tuple(8 + index for index in second)
        )
    assert tuple(forbidden_second_pass_indices) != replicate_indices


class _StartsRng:
    def __init__(self, starts: tuple[int, int]) -> None:
        self.starts = np.asarray(starts)
        self.call_count = 0

    def integers(self, **kwargs: object) -> np.ndarray:
        assert kwargs == {
            "low": 0,
            "high": 7,
            "size": 2,
            "endpoint": False,
        }
        self.call_count += 1
        return self.starts


def test_circular_bootstrap_nonmultiple_segments_center_null_mean() -> None:
    segment_length = 7
    segment_count = 9
    record_count = segment_length * segment_count
    row_index = np.arange(record_count, dtype=float)
    factor_table = np.column_stack(
        (
            row_index / 100.0,
            ((row_index % 5.0) - 2.0) / 100.0,
            ((row_index * row_index) % 11.0) / 100.0,
        )
    )
    null_centered_table = factor_table - factor_table.mean(axis=0)

    inclusion_counts = np.zeros(segment_length)
    for starts in itertools.product(range(segment_length), repeat=2):
        rng = _StartsRng(starts)
        sampled = draw_segment_indices(segment_length, rng=rng)  # type: ignore[arg-type]
        assert rng.call_count == 1
        np.add.at(inclusion_counts, list(sampled), 1)
    circular_weights = inclusion_counts / (segment_length**2)

    expected_sum = np.zeros(3)
    for segment_start in range(0, record_count, segment_length):
        segment = null_centered_table[
            segment_start : segment_start + segment_length
        ]
        expected_sum += (circular_weights[:, None] * segment).sum(axis=0)
    circular_null_mean = expected_sum / record_count
    forbidden_noncircular_weights = np.asarray(
        [1.0, 1.5, 1.0, 1.0, 1.0, 1.0, 0.5]
    )
    forbidden_sum = np.zeros(3)
    for segment_start in range(0, record_count, segment_length):
        segment = null_centered_table[
            segment_start : segment_start + segment_length
        ]
        forbidden_sum += (
            forbidden_noncircular_weights[:, None] * segment
        ).sum(axis=0)
    forbidden_noncircular_null_mean = forbidden_sum / record_count

    assert record_count == 63
    np.testing.assert_array_equal(circular_weights, np.ones(segment_length))
    np.testing.assert_allclose(circular_null_mean, np.zeros(3), atol=1e-15)
    np.testing.assert_allclose(
        circular_null_mean,
        [
            7.401486830834377e-17,
            4.2679704567683347e-19,
            9.141717365465079e-18,
        ],
        rtol=0.0,
        atol=1e-30,
    )
    np.testing.assert_array_equal(
        forbidden_noncircular_weights,
        [1.0, 1.5, 1.0, 1.0, 1.0, 1.0, 0.5],
    )
    np.testing.assert_allclose(
        forbidden_noncircular_null_mean,
        [
            -0.0035714285714285128,
            3.441911658684141e-19,
            0.00023809523809524734,
        ],
        rtol=0.0,
        atol=1e-18,
    )
    assert abs(forbidden_noncircular_null_mean[0]) > 1e-3
    assert abs(forbidden_noncircular_null_mean[2]) > 1e-4


def test_short_bootstrap_segments_resample_60_records_nondegenerately() -> None:
    rng = np.random.Generator(np.random.PCG64DXSM(20260730))
    replicate_indices = []
    for _ in range(3):
        indices = []
        for segment_start in range(0, 60, 6):
            indices.extend(
                segment_start + index
                for index in draw_segment_indices(6, rng=rng)
            )
        replicate_indices.append(tuple(indices))
    replicate_indices = tuple(replicate_indices)
    identity_copy = tuple(range(60))
    serialized_replicates = json.dumps(
        replicate_indices,
        separators=(",", ":"),
    ).encode("ascii")

    row_index = np.arange(60, dtype=float)
    factor_table = np.column_stack(
        (
            row_index / 100.0,
            ((row_index % 7.0) - 3.0) / 100.0,
            ((row_index * row_index) % 17.0) / 100.0,
        )
    )
    result = bootstrap_mean_rank_ic(
        _prepared_segments(factor_table, (6,) * 10),
        bootstrap_seed=20260730,
        replicates=3,
    )

    assert hashlib.sha256(serialized_replicates).hexdigest() == (
        "1af6fb42e42646a709d038138e5f0d35"
        "88ac003022ab7950fe1e83cb6811826b"
    )
    assert len(set(replicate_indices)) == 3
    assert all(indices != identity_copy for indices in replicate_indices)
    for indices in replicate_indices:
        assert len(indices) == 60
        for segment_start in range(0, 60, 6):
            sampled_segment = indices[segment_start : segment_start + 6]
            assert all(
                segment_start <= index < segment_start + 6
                for index in sampled_segment
            )
    for factor_index in range(3):
        assert len(
            set(
                np.round(
                    result.null_centered_bootstrap_means[:, factor_index],
                    15,
                )
            )
        ) >= 2
    assert result.bootstrap_support_all_three_factors

    forbidden_full_segment_copies = (identity_copy,) * 3
    assert len(set(forbidden_full_segment_copies)) == 1
    assert forbidden_full_segment_copies != replicate_indices
    singleton_result = bootstrap_mean_rank_ic(
        _prepared_segments(factor_table, (1,) * 60),
        bootstrap_seed=20260730,
        replicates=3,
    )
    assert not singleton_result.bootstrap_support_all_three_factors


@pytest.mark.parametrize(
    "segments",
    [(), ((),), (((1.0, 2.0),),), (((1.0, 2.0, object()),),)],
)
def test_bootstrap_accepts_only_prepared_three_column_numeric_segments(
    segments: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        bootstrap_mean_rank_ic(
            segments,  # type: ignore[arg-type]
            bootstrap_seed=20260730,
            replicates=3,
        )

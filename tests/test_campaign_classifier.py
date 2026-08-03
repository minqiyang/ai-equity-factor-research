"""Tests for named common-case robustness and ordered final-state routing."""

from __future__ import annotations

from dataclasses import replace
import inspect

import pytest

from campaign.classifier import DiagnosticInputs, classify_diagnostic
from campaign.inference import (
    FACTOR_ORDER,
    CommonCompleteCaseRankICRecord,
    FactorVector,
    rank_ic_robustness,
)


def _base_inputs() -> DiagnosticInputs:
    return DiagnosticInputs(
        hard_valid=True,
        prefrozen_coverage_met=True,
        common_months=60,
        bootstrap_support_all_three_factors=True,
        primary_matched_benchmark_comparisons_valid=True,
        secondary_spy_comparisons_valid=True,
        mean_rank_ics=FactorVector(0.02, -0.01, -0.02),
        holm_rejections=FactorVector(True, False, False),
        active_return_10bps=FactorVector(0.01, -0.01, -0.01),
        active_return_25bps=FactorVector(0.005, -0.01, -0.01),
        common_case_positive_year_fractions=FactorVector(0.6, 0.4, 0.4),
        common_case_all_loyo_means_positive=FactorVector(True, False, False),
    )


def test_diagnostic_final_state_assignment_is_exhaustive_at_boundaries() -> None:
    base = _base_inputs()
    cases = [
        ({"hard_valid": False}, "INVALID_DIAGNOSTIC"),
        (
            {
                "mean_rank_ics": FactorVector(0.0, -0.01, -0.02),
                "holm_rejections": FactorVector(True, False, False),
            },
            "INVALID_DIAGNOSTIC",
        ),
        ({"prefrozen_coverage_met": False}, "INCONCLUSIVE_DIAGNOSTIC"),
        ({"common_months": 59}, "INCONCLUSIVE_DIAGNOSTIC"),
        (
            {"bootstrap_support_all_three_factors": False},
            "INCONCLUSIVE_DIAGNOSTIC",
        ),
        (
            {
                "hard_valid": False,
                "bootstrap_support_all_three_factors": False,
            },
            "INVALID_DIAGNOSTIC",
        ),
        (
            {"active_return_10bps": FactorVector(0.0, -0.01, -0.01)},
            "MIXED_DIAGNOSTIC",
        ),
        (
            {"active_return_25bps": FactorVector(0.0, -0.01, -0.01)},
            "MIXED_DIAGNOSTIC",
        ),
        (
            {
                "common_case_positive_year_fractions": FactorVector(
                    0.5, 0.4, 0.4
                )
            },
            "MIXED_DIAGNOSTIC",
        ),
        (
            {
                "common_case_all_loyo_means_positive": FactorVector(
                    False, False, False
                )
            },
            "MIXED_DIAGNOSTIC",
        ),
        ({}, "POSITIVE_DIAGNOSTIC"),
        (
            {
                "mean_rank_ics": FactorVector(-0.01, -0.02, -0.03),
                "holm_rejections": FactorVector(False, False, False),
            },
            "NEGATIVE_DIAGNOSTIC",
        ),
        (
            {
                "mean_rank_ics": FactorVector(0.0, -0.02, -0.03),
                "holm_rejections": FactorVector(False, False, False),
            },
            "INCONCLUSIVE_DIAGNOSTIC",
        ),
        (
            {"holm_rejections": FactorVector(False, False, False)},
            "INCONCLUSIVE_DIAGNOSTIC",
        ),
    ]

    observed_states = set()
    for overrides, expected in cases:
        observed = classify_diagnostic(replace(base, **overrides))
        observed_states.add(observed)
        assert observed == expected

    assert observed_states == {
        "INVALID_DIAGNOSTIC",
        "INCONCLUSIVE_DIAGNOSTIC",
        "NEGATIVE_DIAGNOSTIC",
        "MIXED_DIAGNOSTIC",
        "POSITIVE_DIAGNOSTIC",
    }


def test_benchmark_comparison_gaps_have_frozen_final_state_routing() -> None:
    base = _base_inputs()
    matched_universe_gap = classify_diagnostic(
        replace(base, primary_matched_benchmark_comparisons_valid=False)
    )
    secondary_spy_gap = classify_diagnostic(
        replace(base, secondary_spy_comparisons_valid=False)
    )

    assert matched_universe_gap == "INVALID_DIAGNOSTIC"
    assert secondary_spy_gap == "POSITIVE_DIAGNOSTIC"


def _factor_all_valid_oracle(
    records: list[dict[str, object]],
    *,
    factor_index: int,
    required_years: tuple[int, ...],
) -> tuple[float, bool]:
    def value(record: dict[str, object]) -> float | None:
        rank_ics = record["rank_ics"]
        assert isinstance(rank_ics, tuple)
        item = rank_ics[factor_index]
        return None if item is None else float(item)

    source = [record for record in records if value(record) is not None]
    positive_year_count = 0
    for year in required_years:
        year_values = [
            value(record)
            for record in source
            if int(record["signal_year"]) == year
        ]
        if not year_values:
            return 0.0, False
        if sum(year_values) / len(year_values) > 0:  # type: ignore[arg-type]
            positive_year_count += 1
    for omitted_year in required_years:
        remaining = [
            value(record)
            for record in source
            if omitted_year not in record["label_intersection_years"]
        ]
        if not remaining or sum(remaining) / len(remaining) <= 0:  # type: ignore[arg-type]
            return positive_year_count / len(required_years), False
    return positive_year_count / len(required_years), True


def test_final_state_robustness_uses_common_case_not_factor_all_valid() -> None:
    raw_records: list[dict[str, object]] = []
    common_records = []
    required_years = (2018, 2019, 2020)
    for year in required_years:
        raw_records.extend(
            [
                {
                    "signal_year": year,
                    "label_intersection_years": (year,),
                    "rank_ics": (0.1, -0.01, -0.02),
                },
                {
                    "signal_year": year,
                    "label_intersection_years": (year,),
                    "rank_ics": (-1.0, None, None),
                },
            ]
        )
        common_records.append(
            CommonCompleteCaseRankICRecord(
                signal_year=year,
                label_intersection_years=(year,),
                rank_ics=FactorVector(0.1, -0.01, -0.02),
            )
        )

    common = rank_ic_robustness(
        common_records,
        required_years=required_years,
    )
    all_valid_fraction, all_valid_loyo_positive = _factor_all_valid_oracle(
        raw_records,
        factor_index=0,
        required_years=required_years,
    )
    common_factor = common.MOM_12_1
    base = _base_inputs()
    common_case_state = classify_diagnostic(
        replace(
            base,
            mean_rank_ics=FactorVector(0.1, -0.01, -0.02),
            common_case_positive_year_fractions=FactorVector(
                common_factor.positive_year_fraction,
                0.0,
                0.0,
            ),
            common_case_all_loyo_means_positive=FactorVector(
                common_factor.all_leave_one_year_out_means_positive,
                False,
                False,
            ),
        )
    )
    forbidden_all_valid_state = classify_diagnostic(
        replace(
            base,
            mean_rank_ics=FactorVector(0.1, -0.01, -0.02),
            common_case_positive_year_fractions=FactorVector(
                all_valid_fraction,
                0.0,
                0.0,
            ),
            common_case_all_loyo_means_positive=FactorVector(
                all_valid_loyo_positive,
                False,
                False,
            ),
        )
    )

    assert (
        common_factor.positive_year_fraction,
        common_factor.all_leave_one_year_out_means_positive,
    ) == (1.0, True)
    assert (all_valid_fraction, all_valid_loyo_positive) == (0.0, False)
    assert common_case_state == "POSITIVE_DIAGNOSTIC"
    assert forbidden_all_valid_state == "MIXED_DIAGNOSTIC"


def test_rank_ic_robustness_keeps_missing_required_year_in_denominator() -> None:
    records = [
        CommonCompleteCaseRankICRecord(
            signal_year=year,
            label_intersection_years=(year,),
            rank_ics=FactorVector(0.1, -0.1, -0.2),
        )
        for year in (2018, 2019)
    ]

    result = rank_ic_robustness(
        records,
        required_years=(2018, 2019, 2020),
    )

    assert result.MOM_12_1.positive_year_fraction == 2 / 3
    assert not result.MOM_12_1.all_leave_one_year_out_means_positive


def test_rank_ic_robustness_rejects_noncomplete_factor_rows() -> None:
    incomplete = CommonCompleteCaseRankICRecord(
        signal_year=2018,
        label_intersection_years=(2018,),
        rank_ics=FactorVector(0.1, None, -0.2),
    )

    with pytest.raises(TypeError):
        rank_ic_robustness([incomplete], required_years=(2018,))


def test_rank_ic_robustness_public_api_has_no_sample_basis_switch() -> None:
    assert tuple(inspect.signature(rank_ic_robustness).parameters) == (
        "records",
        "required_years",
    )
    with pytest.raises(TypeError):
        rank_ic_robustness(
            [],
            required_years=(2018,),
            sample_basis="FACTOR_ALL_VALID",  # type: ignore[call-arg]
        )
    assert FACTOR_ORDER == ("MOM_12_1", "REV_1M", "LOW_VOL_3M")

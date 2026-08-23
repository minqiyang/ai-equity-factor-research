"""Rank IC, decile curve, coverage, yearly/LOYO, and turnover diagnostics."""

from __future__ import annotations

import math

from campaign.diagnostics import (
    CommonCaseMonth,
    common_case_robustness,
    decile_return_curve,
    descriptive_rank_ic,
    label_coverage,
    scheduled_target_turnovers,
    spearman_rank_ic,
    yearly_rank_ic_contributions,
)
from campaign.inference import FACTOR_ORDER
from campaign_runner_v1_support import (
    encode_runner_listing_key,
    freeze_numeric_universe,
    load_runner_fixture,
)


def test_spearman_rank_ic_is_average_tie_ranks_then_pearson() -> None:
    fixture = load_runner_fixture("spearman_rank_ic.json")
    inputs = fixture["inputs"]
    expected = fixture["expected"]
    monotone = spearman_rank_ic(
        inputs["monotone_pairs"],
        inputs["min_distinct_factor_values"],
        inputs["min_distinct_forward_returns"],
    )
    reversed_ic = spearman_rank_ic(
        inputs["reversed_pairs"],
        inputs["min_distinct_factor_values"],
        inputs["min_distinct_forward_returns"],
    )
    descriptive = descriptive_rank_ic(
        inputs["descriptive_values"],
        inputs["sample_std_ddof"],
    )
    assert monotone.valid is expected["monotone"]["valid"]
    assert monotone.reason is expected["monotone"]["reason"]
    assert monotone.value is not None
    assert math.isclose(
        monotone.value,
        expected["monotone"]["value"],
        rel_tol=expected["rel_tol"],
        abs_tol=expected["abs_tol"],
    )
    assert reversed_ic.valid is expected["reversed"]["valid"]
    assert reversed_ic.value is not None
    assert math.isclose(
        reversed_ic.value,
        expected["reversed"]["value"],
        rel_tol=expected["rel_tol"],
        abs_tol=expected["abs_tol"],
    )
    assert reversed_ic.value != fixture["forbidden"]["sign_reversal_of_reversed"]
    assert monotone.value != fixture["forbidden"]["winsorized_monotone"]
    assert descriptive.count == expected["descriptive"]["count"]
    assert descriptive.mean is not None
    assert descriptive.median is not None
    assert descriptive.sample_std is not None
    assert descriptive.monthly_icir is not None
    assert math.isclose(
        descriptive.mean,
        expected["descriptive"]["mean"],
        rel_tol=expected["rel_tol"],
        abs_tol=expected["abs_tol"],
    )
    assert math.isclose(
        descriptive.median,
        expected["descriptive"]["median"],
        rel_tol=expected["rel_tol"],
        abs_tol=expected["abs_tol"],
    )
    assert math.isclose(
        descriptive.sample_std,
        expected["descriptive"]["sample_std"],
        rel_tol=expected["rel_tol"],
        abs_tol=expected["abs_tol"],
    )
    assert math.isclose(
        descriptive.monthly_icir,
        expected["descriptive"]["monthly_icir"],
        rel_tol=expected["rel_tol"],
        abs_tol=expected["abs_tol"],
    )
    assert descriptive.valid is expected["descriptive"]["valid"]


def _materialize_rank_ic_pair_member(value: object) -> object:
    if isinstance(value, dict) and "ieee" in value:
        return float(value["ieee"])
    return value


def test_rank_ic_missing_or_invalid_pair_is_retained_invalid() -> None:
    fixture = load_runner_fixture("rank_ic_missing_label.json")
    inputs = fixture["inputs"]
    expected_cases = fixture["expected"]
    for case in inputs["cases"]:
        pairs = [
            (
                _materialize_rank_ic_pair_member(left),
                _materialize_rank_ic_pair_member(right),
            )
            for left, right in case["pairs"]
        ]
        result = spearman_rank_ic(
            pairs,
            inputs["min_distinct_factor_values"],
            inputs["min_distinct_forward_returns"],
        )
        expected = expected_cases[case["name"]]
        assert result.valid is expected["valid"], case["name"]
        assert result.value is expected["value"], case["name"]
        assert result.reason == expected["reason"], case["name"]
        assert result.value != fixture["forbidden"]["silent_drop_value"]


def test_rank_ic_validity_gates_and_label_coverage() -> None:
    fixture = load_runner_fixture("rank_ic_validity_gates.json")
    inputs = fixture["inputs"]
    nine = spearman_rank_ic(
        inputs["nine_distinct_pairs"],
        inputs["min_distinct_factor_values"],
        inputs["min_distinct_forward_returns"],
    )
    one_return = spearman_rank_ic(
        inputs["one_return_pairs"],
        inputs["min_distinct_factor_values"],
        inputs["min_distinct_forward_returns"],
    )
    expected_nine = fixture["expected"]["nine_distinct"]
    expected_one = fixture["expected"]["one_return"]
    assert nine.valid is expected_nine["valid"]
    assert nine.value is expected_nine["value"]
    assert nine.reason == expected_nine["reason"]
    assert nine.distinct_factor_values == expected_nine["distinct_factor_values"]
    assert one_return.valid is expected_one["valid"]
    assert one_return.value is expected_one["value"]
    assert one_return.reason == expected_one["reason"]
    assert one_return.distinct_forward_returns == expected_one[
        "distinct_forward_returns"
    ]

    keys = tuple(
        encode_runner_listing_key(
            inputs["exchange"],
            ticker,
            inputs["effective_from"],
            inputs["effective_to"],
        )
        for ticker in inputs["coverage_keys"]
    )
    returns = {
        encode_runner_listing_key(
            inputs["exchange"],
            ticker,
            inputs["effective_from"],
            inputs["effective_to"],
        ): value
        for ticker, value in inputs["coverage_returns"].items()
    }
    coverage = label_coverage(keys, returns)
    expected_coverage = fixture["expected"]["coverage"]
    assert coverage.eligible_count == expected_coverage["eligible_count"]
    assert coverage.valid_label_count == expected_coverage["valid_label_count"]
    assert coverage.missing_label_count == expected_coverage["missing_label_count"]
    assert (
        coverage.all_eligible_labels_valid
        is expected_coverage["all_eligible_labels_valid"]
    )


def test_decile_curve_spread_and_monotonicity() -> None:
    fixture = load_runner_fixture("decile_curve_monotonicity.json")
    inputs = fixture["inputs"]
    frozen = freeze_numeric_universe(
        inputs,
        inputs["min_eligible_count"],
        inputs["min_distinct_values"],
        FACTOR_ORDER[0],
        inputs["signal_date"],
    )
    forward_returns = {
        decision.listing_key: decision.factor_value * inputs["return_scale"]
        for decision in frozen.retained_decisions
    }
    curve = decile_return_curve(
        frozen.deciles,
        forward_returns,
        inputs["quantile_count"],
    )
    expected = fixture["expected"]
    assert curve.valid is expected["valid"]
    assert curve.reason is expected["reason"]
    assert curve.fully_monotone is expected["fully_monotone"]
    assert curve.monotonicity_share == expected["monotonicity_share"]
    assert math.isclose(
        curve.spread,
        expected["spread"],
        rel_tol=expected["rel_tol"],
        abs_tol=expected["abs_tol"],
    )
    assert curve.spread != fixture["forbidden"]["reversed_spread"]
    for difference, expected_difference in zip(
        curve.adjacent_differences,
        expected["adjacent_differences"],
        strict=True,
    ):
        assert math.isclose(
            difference,
            expected_difference,
            rel_tol=expected["rel_tol"],
            abs_tol=expected["abs_tol"],
        )
    for label, mean in expected["means"].items():
        assert math.isclose(
            curve.means[label],
            mean,
            rel_tol=expected["rel_tol"],
            abs_tol=expected["abs_tol"],
        )
    missing = dict(forward_returns)
    del missing[next(iter(missing))]
    invalid = decile_return_curve(
        frozen.deciles,
        missing,
        inputs["quantile_count"],
    )
    assert invalid.valid is False
    assert invalid.reason == expected["missing_return_reason"]
    assert invalid.fully_monotone is not fixture["forbidden"][
        "fully_monotone_if_reversed"
    ]


def test_yearly_contributions_and_common_case_loyo() -> None:
    fixture = load_runner_fixture("yearly_loyo_rank_ic.json")
    inputs = fixture["inputs"]
    yearly = yearly_rank_ic_contributions(inputs["months"])
    expected_years = fixture["expected"]["yearly"]
    assert len(yearly) == len(expected_years)
    for row, expected in zip(yearly, expected_years, strict=True):
        assert row.year == expected["year"]
        assert row.count == expected["count"]
        assert math.isclose(
            row.mean,
            expected["mean"],
            rel_tol=fixture["expected"]["rel_tol"],
            abs_tol=fixture["expected"]["abs_tol"],
        )
        assert math.isclose(
            row.contribution,
            expected["contribution"],
            rel_tol=fixture["expected"]["rel_tol"],
            abs_tol=fixture["expected"]["abs_tol"],
        )
    robustness = common_case_robustness(
        tuple(
            CommonCaseMonth(
                row["signal_year"],
                tuple(row["label_intersection_years"]),
                tuple(row["rank_ics"]),
            )
            for row in inputs["common_case"]
        ),
        inputs["required_years"],
    )
    observed = (
        robustness.MOM_12_1,
        robustness.REV_1M,
        robustness.LOW_VOL_3M,
    )
    for item, expected in zip(
        observed,
        fixture["expected"]["robustness"],
        strict=True,
    ):
        assert math.isclose(
            item.positive_year_fraction,
            expected["positive_year_fraction"],
            rel_tol=fixture["expected"]["rel_tol"],
            abs_tol=fixture["expected"]["abs_tol"],
        )
        assert (
            item.all_leave_one_year_out_means_positive
            is expected["all_leave_one_year_out_means_positive"]
        )
        if expected["positive_year_fraction"] != fixture["forbidden"][
            "drop_required_year_from_denominator"
        ]:
            assert item.positive_year_fraction != fixture["forbidden"][
                "drop_required_year_from_denominator"
            ]


def test_scheduled_turnover_keeps_outcome_invalid_predecessor() -> None:
    fixture = load_runner_fixture("turnover_predecessor_chain.json")
    inputs = fixture["inputs"]
    targets = []
    for month in inputs["months"]:
        weights = {}
        for ticker, weight in zip(
            month["tickers"],
            month["weights"],
            strict=True,
        ):
            weights[
                encode_runner_listing_key(
                    inputs["exchange"],
                    ticker,
                    inputs["effective_from"],
                    inputs["effective_to"],
                )
            ] = weight
        targets.append(weights)
    before = scheduled_target_turnovers(targets)
    mutated_flags = inputs["outcome_invalid_mutations"]
    original_flags = [month["outcome_valid"] for month in inputs["months"]]
    assert mutated_flags != original_flags
    after = scheduled_target_turnovers(targets)
    assert before == after
    assert before == tuple(fixture["expected"]["turnovers"])
    assert before != tuple(fixture["forbidden"]["skip_invalid_middle_turnovers"])

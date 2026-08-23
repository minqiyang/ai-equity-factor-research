"""Factor-matched primary and SPY secondary comparison goldens."""

from __future__ import annotations

import inspect
import math

import pytest

from campaign.benchmarks import (
    dated_held_returns,
    factor_matched_cost_free_comparison,
    spy_secondary_comparison,
)
from campaign.inference import FACTOR_ORDER
from campaign.paths import advance_holdings
from campaign_runner_v1_support import (
    dated_uniform_returns,
    freeze_numeric_universe,
    load_runner_fixture,
    runner_holding_interval,
    runner_weight_map,
)


def test_integrated_tied_month_keeps_invested_benchmark() -> None:
    fixture = load_runner_fixture("integrated_tied_month.json")
    inputs = fixture["inputs"]
    expected = fixture["expected"]
    frozen = freeze_numeric_universe(
        inputs["tied_universe"],
        inputs["min_eligible_count"],
        inputs["min_distinct_values"],
        FACTOR_ORDER[0],
        inputs["session_date"],
    )
    assert frozen.invalid_factor_month is expected["invalid_factor_month"]
    assert frozen.benchmark_formable is expected["benchmark_formable"]
    assert (not frozen.long_only_target) is expected["factor_target_empty"]
    assert len(frozen.matched_benchmark_target) == expected["benchmark_count"]
    assert set(frozen.matched_benchmark_target.values()) == {
        expected["benchmark_weight"]
    }
    prior = runner_weight_map(
        inputs["exchange"],
        inputs["effective_from"],
        inputs["effective_to"],
        {inputs["prior_factor_ticker"]: inputs["prior_factor_weight"]},
    )
    for bps, wanted in expected["by_bps"].items():
        strategy = advance_holdings(
            prior,
            (
                runner_holding_interval(
                    inputs["session_date"],
                    inputs["exchange"],
                    inputs["effective_from"],
                    inputs["effective_to"],
                    {inputs["prior_factor_ticker"]: inputs["factor_held_return"]},
                    {},
                ),
            ),
            int(bps),
            inputs["initial_equity"],
        )
        comparison = factor_matched_cost_free_comparison(
            (frozen,),
            strategy,
            (
                dated_uniform_returns(
                    inputs["session_date"],
                    dict(frozen.matched_benchmark_target),
                    inputs["benchmark_held_return"],
                ),
            ),
            inputs["initial_equity"],
            inputs["role"],
        )
        point = strategy.points[0]
        assert strategy.valid
        assert comparison.valid is expected["comparison_valid"]
        assert (
            comparison.hard_validity_failure
            is expected["hard_validity_failure"]
        )
        assert point.turnover == expected["turnover"]
        assert point.gross_return == expected["strategy_gross"]
        assert comparison.benchmark_gross_returns[0] is not None
        assert math.isclose(
            comparison.benchmark_gross_returns[0],
            expected["benchmark_gross"],
            rel_tol=expected["rel_tol"],
            abs_tol=expected["abs_tol"],
        )
        assert point.cost_impact is not None
        assert point.net_return is not None
        assert comparison.active_returns[0] is not None
        assert math.isclose(
            point.cost_impact,
            wanted["cost"],
            rel_tol=expected["rel_tol"],
            abs_tol=expected["abs_tol"],
        )
        assert math.isclose(
            point.net_return,
            wanted["net"],
            rel_tol=expected["rel_tol"],
            abs_tol=expected["abs_tol"],
        )
        assert math.isclose(
            comparison.active_returns[0],
            wanted["active"],
            rel_tol=expected["rel_tol"],
            abs_tol=expected["abs_tol"],
        )
        assert (
            comparison.active_returns[0]
            != fixture["forbidden"]["cash_benchmark_active"][bps]
        )
        assert dict(frozen.long_only_target) != dict(
            frozen.matched_benchmark_target
        )


def test_valid_tied_valid_three_month_stays_connected() -> None:
    fixture = load_runner_fixture("valid_tied_valid_three_month.json")
    inputs = fixture["inputs"]
    expected = fixture["expected"]
    spec = inputs["strategy"]
    frozen_by_session = tuple(
        freeze_numeric_universe(
            inputs["benchmark_universe"],
            inputs["min_eligible_count"],
            inputs["min_distinct_values"],
            FACTOR_ORDER[0],
            session_date,
        )
        for session_date in spec["session_dates"]
    )
    frozen = frozen_by_session[0]
    for bps, wanted in expected["by_bps"].items():
        strategy = advance_holdings(
            runner_weight_map(
                inputs["exchange"],
                inputs["effective_from"],
                inputs["effective_to"],
                spec["initial_weights"],
            ),
            tuple(
                runner_holding_interval(
                    session_date,
                    inputs["exchange"],
                    inputs["effective_from"],
                    inputs["effective_to"],
                    interval["held_returns"],
                    interval["reset_weights"],
                )
                for session_date, interval in zip(
                    spec["session_dates"],
                    spec["intervals"],
                    strict=True,
                )
            ),
            int(bps),
            inputs["initial_equity"],
        )
        comparison = factor_matched_cost_free_comparison(
            frozen_by_session,
            strategy,
            tuple(
                dated_uniform_returns(
                    session_date,
                    dict(frozen.matched_benchmark_target),
                    value,
                )
                for session_date, value in zip(
                    spec["session_dates"],
                    inputs["benchmark_held_returns"],
                    strict=True,
                )
            ),
            inputs["initial_equity"],
            inputs["role"],
        )
        assert strategy.valid
        assert comparison.valid
        assert tuple(point.turnover for point in strategy.points) == tuple(
            expected["connected_turnovers"]
        )
        assert tuple(point.gross_return for point in strategy.points) == tuple(
            expected["strategy_gross"]
        )
        assert comparison.benchmark_gross_returns == tuple(
            expected["benchmark_gross"]
        )
        for observed, net in zip(strategy.points, wanted["net"], strict=True):
            assert observed.net_return is not None
            assert math.isclose(
                observed.net_return,
                net,
                rel_tol=expected["rel_tol"],
                abs_tol=expected["abs_tol"],
            )
        assert wanted["annualized_active_negative"]
        assert wanted["annualized_active"] < expected["bridge"]["by_bps"][bps][
            "annualized_active"
        ]


def test_benchmark_comparison_gap_is_hard_validity() -> None:
    fixture = load_runner_fixture("benchmark_comparison_gap.json")
    inputs = fixture["inputs"]
    expected = fixture["expected"]
    frozen = freeze_numeric_universe(
        inputs["universe"],
        inputs["min_eligible_count"],
        inputs["min_distinct_values"],
        FACTOR_ORDER[0],
        inputs["session_date"],
    )
    assert frozen.benchmark_formable is expected["benchmark_formable"]
    assert len(frozen.matched_benchmark_target) == expected["benchmark_count"]
    strategy = advance_holdings(
        runner_weight_map(
            inputs["exchange"],
            inputs["effective_from"],
            inputs["effective_to"],
            inputs["strategy"]["initial_weights"],
        ),
        (
            runner_holding_interval(
                inputs["session_date"],
                inputs["exchange"],
                inputs["effective_from"],
                inputs["effective_to"],
                inputs["strategy"]["held_returns"],
                inputs["strategy"]["reset_weights"],
            ),
        ),
        inputs["transaction_cost_bps"],
        inputs["initial_equity"],
    )
    present = next(iter(frozen.matched_benchmark_target))
    missing = runner_weight_map(
        inputs["exchange"],
        inputs["effective_from"],
        inputs["effective_to"],
        {inputs["missing_ticker"]: expected["benchmark_count"]},
    )
    observed = {present: inputs["valid_constituent_return"]}
    assert next(iter(missing)) not in observed
    comparison = factor_matched_cost_free_comparison(
        (frozen,),
        strategy,
        (dated_held_returns(inputs["session_date"], observed),),
        inputs["initial_equity"],
        inputs["role"],
    )
    assert comparison.valid is expected["comparison_valid"]
    assert comparison.hard_validity_failure is expected["hard_validity_failure"]
    assert comparison.reason == expected["reason"]
    assert comparison.active_returns == (expected["active_return"],)
    assert (
        comparison.benchmark_gross_returns[0]
        != fixture["forbidden"]["survivor_renormalized_return"]
    )
    assert (
        comparison.benchmark_gross_returns[0]
        != fixture["forbidden"]["half_filled_return"]
    )


def test_spy_secondary_gap_does_not_change_primary() -> None:
    fixture = load_runner_fixture("spy_secondary_gap.json")
    inputs = fixture["inputs"]
    expected = fixture["expected"]
    spec = inputs["strategy"]
    frozen_by_session = tuple(
        freeze_numeric_universe(
            inputs["universe"],
            inputs["min_eligible_count"],
            inputs["min_distinct_values"],
            FACTOR_ORDER[0],
            session_date,
        )
        for session_date in inputs["session_dates"]
    )
    frozen = frozen_by_session[0]
    strategy = advance_holdings(
        runner_weight_map(
            inputs["exchange"],
            inputs["effective_from"],
            inputs["effective_to"],
            spec["initial_weights"],
        ),
        tuple(
            runner_holding_interval(
                session_date,
                inputs["exchange"],
                inputs["effective_from"],
                inputs["effective_to"],
                interval["held_returns"],
                interval["reset_weights"],
            )
            for session_date, interval in zip(
                inputs["session_dates"],
                spec["intervals"],
                strict=True,
            )
        ),
        inputs["transaction_cost_bps"],
        inputs["initial_equity"],
    )
    primary = factor_matched_cost_free_comparison(
        frozen_by_session,
        strategy,
        tuple(
            dated_uniform_returns(
                session_date,
                dict(frozen.matched_benchmark_target),
                value,
            )
            for session_date, value in zip(
                inputs["session_dates"],
                inputs["primary_held_returns"],
                strict=True,
            )
        ),
        inputs["initial_equity"],
        inputs["primary_role"],
    )
    secondary = spy_secondary_comparison(inputs["spy_returns"], strategy)
    assert primary.valid is expected["primary_valid"]
    assert (
        primary.hard_validity_failure
        is expected["primary_hard_validity_failure"]
    )
    assert secondary.valid is expected["secondary_valid"]
    assert (
        secondary.hard_validity_failure
        is expected["secondary_hard_validity_failure"]
    )
    assert secondary.reason == expected["secondary_reason"]
    assert secondary.role == expected["secondary_role"]
    assert (
        secondary.reason_counts[expected["secondary_reason"]]
        == expected["secondary_missing_count"]
    )
    assert None in secondary.benchmark_gross_returns
    assert fixture["forbidden"]["fill_missing_spy_with_zero"] not in (
        secondary.benchmark_gross_returns
    )


def test_empty_or_duplicate_universe_is_unformable_not_cash() -> None:
    fixture = load_runner_fixture("empty_or_duplicate_key_universe.json")
    inputs = fixture["inputs"]
    strategy = advance_holdings(
        runner_weight_map(
            inputs["exchange"],
            inputs["effective_from"],
            inputs["effective_to"],
            inputs["strategy"]["initial_weights"],
        ),
        (
            runner_holding_interval(
                inputs["session_date"],
                inputs["exchange"],
                inputs["effective_from"],
                inputs["effective_to"],
                inputs["strategy"]["held_returns"],
                inputs["strategy"]["reset_weights"],
            ),
        ),
        inputs["transaction_cost_bps"],
        inputs["initial_equity"],
    )
    for name in ("empty", "duplicate"):
        frozen = freeze_numeric_universe(
            inputs[f"{name}_universe"],
            inputs["min_eligible_count"],
            inputs["min_distinct_values"],
            FACTOR_ORDER[0],
            inputs["session_date"],
        )
        wanted = fixture["expected"][name]
        assert frozen.benchmark_formable is wanted["benchmark_formable"]
        comparison = factor_matched_cost_free_comparison(
            (frozen,),
            strategy,
            (dated_held_returns(inputs["session_date"], {}),),
            inputs["initial_equity"],
            inputs["role"],
        )
        assert comparison.valid is wanted["comparison_valid"]
        assert comparison.hard_validity_failure is wanted["hard_validity_failure"]
        assert comparison.reason == wanted["reason"]
        assert (comparison.holdings is None) is wanted["holdings_is_none"]
        assert comparison.active_returns == (wanted["active_return"],)
        assert (
            comparison.active_returns[0]
            != fixture["forbidden"]["cash_substitute_active"]
        )


def test_permuted_decision_return_pairs_cannot_reuse_strategy_order() -> None:
    fixture = load_runner_fixture("benchmark_schedule_permutation.json")
    inputs = fixture["inputs"]
    first = freeze_numeric_universe(
        inputs["first_universe"],
        inputs["min_eligible_count"],
        inputs["min_distinct_values"],
        FACTOR_ORDER[0],
        inputs["session_dates"][0],
    )
    second = freeze_numeric_universe(
        inputs["second_universe"],
        inputs["min_eligible_count"],
        inputs["min_distinct_values"],
        FACTOR_ORDER[0],
        inputs["session_dates"][1],
    )
    spec = inputs["strategy"]
    strategy = advance_holdings(
        runner_weight_map(
            inputs["exchange"],
            inputs["effective_from"],
            inputs["effective_to"],
            spec["initial_weights"],
        ),
        tuple(
            runner_holding_interval(
                session_date,
                inputs["exchange"],
                inputs["effective_from"],
                inputs["effective_to"],
                interval["held_returns"],
                interval["reset_weights"],
            )
            for session_date, interval in zip(
                inputs["session_dates"],
                spec["intervals"],
                strict=True,
            )
        ),
        inputs["transaction_cost_bps"],
        inputs["initial_equity"],
    )
    aligned_returns = tuple(
        dated_uniform_returns(
            session_date,
            dict(frozen.matched_benchmark_target),
            value,
        )
        for frozen, session_date, value in zip(
            (first, second),
            inputs["session_dates"],
            inputs["benchmark_held_returns"],
            strict=True,
        )
    )
    aligned = factor_matched_cost_free_comparison(
        (first, second),
        strategy,
        aligned_returns,
        inputs["initial_equity"],
        inputs["role"],
    )
    assert aligned.valid is fixture["expected"]["aligned_valid"]
    assert aligned.benchmark_gross_returns == tuple(
        fixture["expected"]["aligned_benchmark_gross"]
    )
    with pytest.raises(ValueError, match="session identity"):
        factor_matched_cost_free_comparison(
            (second, first),
            strategy,
            (aligned_returns[1], aligned_returns[0]),
            inputs["initial_equity"],
            inputs["role"],
        )
    assert fixture["forbidden"]["align_only_by_sequence_position"]


def test_benchmark_functions_have_no_fill_or_defaults() -> None:
    for function in (
        dated_held_returns,
        factor_matched_cost_free_comparison,
        spy_secondary_comparison,
    ):
        names = inspect.signature(function).parameters
        assert "fill" not in names
        assert "membership" not in names
        for parameter in names.values():
            assert parameter.default is inspect.Parameter.empty

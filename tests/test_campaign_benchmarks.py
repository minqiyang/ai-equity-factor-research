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
    fixture_campaign_schedule,
    freeze_numeric_universe,
    load_runner_fixture,
    runner_holding_interval,
    runner_return_map,
    runner_weight_map,
    strategy_campaign_schedule,
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
            strategy_campaign_schedule(strategy),
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
            strategy_campaign_schedule(strategy),
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
        strategy_campaign_schedule(strategy),
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
        strategy_campaign_schedule(strategy),
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
            strategy_campaign_schedule(strategy),
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
        strategy_campaign_schedule(strategy),
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
            strategy_campaign_schedule(strategy),
        )
    assert fixture["forbidden"]["align_only_by_sequence_position"]


def _uniform_strategy(inputs: dict, session_dates: list) -> object:
    spec = inputs["strategy"]
    return advance_holdings(
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
                spec["held_returns"],
                spec["reset_weights"],
            )
            for session_date in session_dates
        ),
        inputs["transaction_cost_bps"],
        inputs["initial_equity"],
    )


def test_daily_execution_path_refuses_sparse_calendar_jump() -> None:
    fixture = load_runner_fixture("benchmark_daily_execution_path.json")
    inputs = fixture["inputs"]
    frozen = tuple(
        freeze_numeric_universe(
            inputs["benchmark_universe"],
            inputs["min_eligible_count"],
            inputs["min_distinct_values"],
            FACTOR_ORDER[0],
            signal_date,
        )
        for signal_date in inputs["signal_dates"]
    )
    strategy = _uniform_strategy(inputs, inputs["session_dates"])
    observed = tuple(
        dated_held_returns(
            session_date,
            runner_return_map(
                inputs["exchange"],
                inputs["effective_from"],
                inputs["effective_to"],
                held_returns,
            ),
        )
        for session_date, held_returns in zip(
            inputs["session_dates"],
            inputs["benchmark_held_returns"],
            strict=True,
        )
    )
    with pytest.raises(ValueError, match=fixture["expected"]["match"]):
        factor_matched_cost_free_comparison(
            frozen,
            strategy,
            observed,
            inputs["initial_equity"],
            inputs["role"],
            fixture_campaign_schedule(inputs["campaign_schedule"]),
        )
    assert fixture["forbidden"]["valid_continuous_daily_path"]
    assert fixture["forbidden"]["jump_2024_02_07_to_2024_03_01"]


def _membership_pair(inputs: dict) -> tuple[object, object]:
    first = freeze_numeric_universe(
        inputs["first_universe"],
        inputs["min_eligible_count"],
        inputs["min_distinct_values"],
        FACTOR_ORDER[inputs["first_factor_index"]],
        inputs["signal_dates"][0],
    )
    second = freeze_numeric_universe(
        inputs["second_universe"],
        inputs["min_eligible_count"],
        inputs["min_distinct_values"],
        FACTOR_ORDER[inputs["second_factor_index"]],
        inputs["signal_dates"][1],
    )
    return first, second


def _dated_return_path(inputs: dict, session_dates: list) -> tuple:
    return tuple(
        dated_held_returns(
            session_date,
            runner_return_map(
                inputs["exchange"],
                inputs["effective_from"],
                inputs["effective_to"],
                held_returns,
            ),
        )
        for session_date, held_returns in zip(
            session_dates,
            inputs["benchmark_held_returns"],
            strict=True,
        )
    )


def test_membership_boundary_refuses_truncated_calendar() -> None:
    fixture = load_runner_fixture("benchmark_membership_boundary.json")
    inputs = fixture["inputs"]
    first, second = _membership_pair(inputs)
    strategy = _uniform_strategy(inputs, inputs["session_dates"])
    observed = _dated_return_path(inputs, inputs["session_dates"])
    assert inputs["session_dates"][0] == fixture["expected"]["starts_on"]
    assert (
        fixture["expected"]["omits_first_execution"]
        not in inputs["session_dates"]
    )
    with pytest.raises(ValueError, match=fixture["expected"]["match"]):
        factor_matched_cost_free_comparison(
            (first, second),
            strategy,
            observed,
            inputs["initial_equity"],
            inputs["role"],
            fixture_campaign_schedule(inputs["campaign_schedule"]),
        )
    assert fixture["forbidden"]["valid_truncated_membership_path"]
    assert fixture["forbidden"]["accept_contiguous_sub_slice"]


def test_changed_membership_resets_at_execution_close() -> None:
    fixture = load_runner_fixture("benchmark_membership_complete_span.json")
    inputs = fixture["inputs"]
    expected = fixture["expected"]
    first, second = _membership_pair(inputs)
    assert dict(first.matched_benchmark_target) != dict(
        second.matched_benchmark_target
    )
    strategy = _uniform_strategy(inputs, inputs["session_dates"])
    observed = _dated_return_path(inputs, inputs["session_dates"])
    schedule = fixture_campaign_schedule(inputs["campaign_schedule"])
    comparison = factor_matched_cost_free_comparison(
        (first, second),
        strategy,
        observed,
        inputs["initial_equity"],
        inputs["role"],
        schedule,
    )
    assert len(strategy.points) == expected["daily_count"]
    assert len((first, second)) == expected["frozen_count"]
    assert len(strategy.points) != expected["frozen_count"]
    assert comparison.valid is expected["valid"]
    for observed_gross, wanted in zip(
        comparison.benchmark_gross_returns,
        expected["benchmark_gross"],
        strict=True,
    ):
        assert observed_gross is not None
        assert math.isclose(
            observed_gross,
            wanted,
            rel_tol=expected["rel_tol"],
            abs_tol=expected["abs_tol"],
        )
    execution_gross = comparison.benchmark_gross_returns[
        inputs["execution_index"]
    ]
    assert execution_gross != fixture["forbidden"][
        "new_membership_execution_close"
    ]
    assert comparison.benchmark_gross_returns[
        inputs["pre_execution_index"]
    ] != fixture["forbidden"]["daily_rebalanced_second_interval"]
    assert comparison.benchmark_gross_returns[-1] != fixture["forbidden"][
        "no_reset_after_execution"
    ]
    assert fixture["forbidden"]["same_universe_on_both_decisions"]
    permuted = factor_matched_cost_free_comparison(
        (second, first),
        strategy,
        observed,
        inputs["initial_equity"],
        inputs["role"],
        schedule,
    )
    assert permuted.benchmark_gross_returns == comparison.benchmark_gross_returns


def test_prefix_and_suffix_truncation_are_refused() -> None:
    fixture = load_runner_fixture("benchmark_span_truncation.json")
    inputs = fixture["inputs"]
    frozen = tuple(
        freeze_numeric_universe(
            inputs["benchmark_universe"],
            inputs["min_eligible_count"],
            inputs["min_distinct_values"],
            FACTOR_ORDER[0],
            signal_date,
        )
        for signal_date in inputs["signal_dates"]
    )
    schedule = fixture_campaign_schedule(inputs["campaign_schedule"])
    assert inputs["required_span"][0] == fixture["expected"][
        "first_included_execution"
    ]
    assert inputs["required_span"][-1] == fixture["expected"][
        "execution_following_last_target"
    ]
    for name in fixture["expected"]["case_names"]:
        case = inputs["cases"][name]
        strategy = _uniform_strategy(inputs, case["session_dates"])
        observed = tuple(
            dated_held_returns(session_date, {})
            for session_date in case["session_dates"]
        )
        assert case["session_dates"] != inputs["required_span"]
        with pytest.raises(ValueError, match=case["match"]):
            factor_matched_cost_free_comparison(
                frozen,
                strategy,
                observed,
                inputs["initial_equity"],
                inputs["role"],
                schedule,
            )
    assert fixture["forbidden"]["accept_contiguous_sub_slice"]


def test_raw_session_list_is_not_an_accepted_schedule() -> None:
    fixture = load_runner_fixture("benchmark_membership_complete_span.json")
    inputs = fixture["inputs"]
    first, second = _membership_pair(inputs)
    strategy = _uniform_strategy(inputs, inputs["session_dates"])
    observed = _dated_return_path(inputs, inputs["session_dates"])
    with pytest.raises(TypeError, match="CampaignSchedule"):
        factor_matched_cost_free_comparison(
            (first, second),
            strategy,
            observed,
            inputs["initial_equity"],
            inputs["role"],
            inputs["session_dates"],
        )


def test_daily_path_refuses_sparse_duplicate_and_reversed_calendars() -> None:
    fixture = load_runner_fixture("benchmark_calendar_refusals.json")
    inputs = fixture["inputs"]
    frozen = tuple(
        freeze_numeric_universe(
            inputs["benchmark_universe"],
            inputs["min_eligible_count"],
            inputs["min_distinct_values"],
            FACTOR_ORDER[0],
            signal_date,
        )
        for signal_date in inputs["signal_dates"]
    )
    for name in fixture["expected"]["case_names"]:
        case = inputs["cases"][name]
        strategy = _uniform_strategy(inputs, case["session_dates"])
        observed = tuple(
            dated_held_returns(session_date, {})
            for session_date in case["session_dates"]
        )
        with pytest.raises(ValueError, match=case["match"]):
            factor_matched_cost_free_comparison(
                frozen,
                strategy,
                observed,
                inputs["initial_equity"],
                inputs["role"],
                fixture_campaign_schedule(inputs["campaign_schedule"]),
            )
    assert fixture["forbidden"]["accept_sparse_or_reordered_path"]


def test_mixed_factor_frozen_decisions_are_rejected() -> None:
    fixture = load_runner_fixture("benchmark_mixed_factor.json")
    inputs = fixture["inputs"]
    first = freeze_numeric_universe(
        inputs["first_universe"],
        inputs["min_eligible_count"],
        inputs["min_distinct_values"],
        FACTOR_ORDER[inputs["first_factor_index"]],
        inputs["session_dates"][0],
    )
    second = freeze_numeric_universe(
        inputs["second_universe"],
        inputs["min_eligible_count"],
        inputs["min_distinct_values"],
        FACTOR_ORDER[inputs["second_factor_index"]],
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
    observed = tuple(
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
    with pytest.raises(ValueError, match=fixture["expected"]["match"]):
        factor_matched_cost_free_comparison(
            (first, second),
            strategy,
            observed,
            inputs["initial_equity"],
            inputs["role"],
            strategy_campaign_schedule(strategy),
        )
    assert first.factor_id != second.factor_id
    assert fixture["forbidden"]["compound_mixed_factor_benchmark"]


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

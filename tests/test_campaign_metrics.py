"""Annualized active, cost drag, drawdown, and contribution goldens."""

from __future__ import annotations

import inspect
import math

from campaign.benchmarks import factor_matched_cost_free_comparison
from campaign.inference import FACTOR_ORDER
from campaign.metrics import (
    aggregate_contributions,
    annualized_active_return,
    annualized_geometric_return,
    annualized_volatility,
    cost_drag,
    max_drawdown,
    zero_cash_rate_sharpe_style,
)
from campaign.paths import advance_holdings
from campaign_runner_v1_support import (
    dated_uniform_returns,
    freeze_numeric_universe,
    load_runner_fixture,
    runner_holding_interval,
    runner_weight_map,
    strategy_campaign_schedule,
)


def test_three_month_metrics_and_forbidden_alternatives() -> None:
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
    bps = inputs["transaction_cost_bps"][0]
    wanted = expected["by_bps"][str(bps)]
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
        bps,
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
    net = tuple(point.net_return for point in strategy.points)
    gross = tuple(point.gross_return for point in strategy.points)
    active = annualized_active_return(
        net,
        comparison.benchmark_gross_returns,
        inputs["periods_per_year"],
    )
    drag = cost_drag(gross, net, inputs["periods_per_year"])
    equity = (strategy.initial_equity,) + tuple(
        point.equity for point in strategy.points
    )
    drawdown = max_drawdown(equity)
    volatility = annualized_volatility(
        net,
        inputs["periods_per_year"],
        inputs["sample_std_ddof"],
    )
    sharpe = zero_cash_rate_sharpe_style(
        net,
        inputs["periods_per_year"],
        inputs["sample_std_ddof"],
    )
    assert active.valid
    assert drag.valid
    assert drawdown.valid
    assert volatility.valid
    assert sharpe.valid
    assert active.value is not None
    assert drag.value is not None
    assert drawdown.value is not None
    assert volatility.value is not None
    assert sharpe.value is not None
    assert math.isclose(
        active.value,
        wanted["annualized_active"],
        rel_tol=expected["rel_tol"],
        abs_tol=expected["abs_tol"],
    )
    assert (active.value < 0.0) is wanted["annualized_active_negative"]
    assert math.isclose(
        drag.value,
        wanted["cost_drag"],
        rel_tol=expected["rel_tol"],
        abs_tol=expected["abs_tol"],
    )
    assert math.isclose(
        drawdown.value,
        wanted["max_drawdown"],
        rel_tol=expected["rel_tol"],
        abs_tol=expected["abs_tol"],
    )
    assert math.isclose(
        volatility.value,
        wanted["annualized_volatility"],
        rel_tol=expected["rel_tol"],
        abs_tol=expected["abs_tol"],
    )
    assert math.isclose(
        sharpe.value,
        wanted["zero_cash_rate_sharpe_style"],
        rel_tol=expected["rel_tol"],
        abs_tol=expected["abs_tol"],
    )
    for name in ("bridge", "restart"):
        alt = inputs[name]
        alt_expected = expected[name]
        for alt_bps, alt_wanted in alt_expected["by_bps"].items():
            alt_holdings = advance_holdings(
                runner_weight_map(
                    inputs["exchange"],
                    inputs["effective_from"],
                    inputs["effective_to"],
                    alt["initial_weights"],
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
                        alt["session_dates"],
                        alt["intervals"],
                        strict=True,
                    )
                ),
                int(alt_bps),
                inputs["initial_equity"],
            )
            assert tuple(
                point.turnover for point in alt_holdings.points
            ) == tuple(alt_expected["turnovers"])
            alt_active = annualized_active_return(
                tuple(point.net_return for point in alt_holdings.points),
                tuple(alt["benchmark_held_returns"]),
                inputs["periods_per_year"],
            )
            assert alt_active.valid
            assert alt_active.value is not None
            assert math.isclose(
                alt_active.value,
                alt_wanted["annualized_active"],
                rel_tol=expected["rel_tol"],
                abs_tol=expected["abs_tol"],
            )
            assert (
                alt_active.value > 0.0
            ) is alt_wanted["annualized_active_positive"]
            assert alt_active.value != active.value
    assert (
        expected["bridge"]["by_bps"]["10"]["annualized_active"]
        != expected["restart"]["by_bps"]["10"]["annualized_active"]
    )
    assert fixture["forbidden"]["positive_diagnostic_from_deleted_tied_month"]
    assert not fixture["forbidden"]["bridge_and_restart_costs_indistinguishable"]


def test_incomplete_series_does_not_annualize() -> None:
    fixture = load_runner_fixture("benchmark_comparison_gap.json")
    expected = fixture["expected"]
    active = annualized_active_return(
        (fixture["inputs"]["strategy"]["held_returns"]["T000"], None),
        (expected["active_return"], expected["active_return"]),
        fixture["inputs"]["periods_per_year"],
    )
    assert active.valid is False
    assert active.value is None


def test_contribution_aggregate_matches_accounting_order() -> None:
    fixture = load_runner_fixture("accounting_order_golden.json")
    inputs = fixture["inputs"]
    expected = fixture["expected"]
    holdings = advance_holdings(
        runner_weight_map(
            inputs["exchange"],
            inputs["effective_from"],
            inputs["effective_to"],
            inputs["initial_weights"],
        ),
        (
            runner_holding_interval(
                inputs["session_date"],
                inputs["exchange"],
                inputs["effective_from"],
                inputs["effective_to"],
                inputs["held_returns"],
                inputs["reset_weights"],
            ),
        ),
        inputs["transaction_cost_bps"],
        inputs["initial_equity"],
    )
    totals = aggregate_contributions(holdings.points)
    assert totals.valid
    assert totals.gross_sum is not None
    assert totals.cost_sum is not None
    assert math.isclose(
        totals.gross_sum,
        expected["gross_return"],
        rel_tol=expected["rel_tol"],
        abs_tol=expected["abs_tol"],
    )
    assert math.isclose(
        totals.cost_sum,
        expected["contribution_cost_sum"],
        rel_tol=expected["rel_tol"],
        abs_tol=expected["abs_tol"],
    )


def test_metric_functions_have_no_defaults() -> None:
    for function in (
        annualized_geometric_return,
        annualized_volatility,
        zero_cash_rate_sharpe_style,
        max_drawdown,
        cost_drag,
        annualized_active_return,
        aggregate_contributions,
    ):
        for parameter in inspect.signature(function).parameters.values():
            assert parameter.default is inspect.Parameter.empty

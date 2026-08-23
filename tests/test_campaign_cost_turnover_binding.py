"""D-1: cost and turnover goldens bind campaign.paths, not backtest."""

from __future__ import annotations

import math

from campaign.metrics import aggregate_contributions
from campaign.paths import advance_holdings, post_return_equity_cost
from campaign_runner_v1_support import (
    load_runner_fixture,
    runner_holding_interval,
    runner_weight_map,
)


def test_unit_multiplier_cost_table_binds_campaign_paths() -> None:
    fixture = load_runner_fixture("unit_multiplier_cost_table.json")
    inputs = fixture["inputs"]
    expected = fixture["expected"]
    for turnover, row in zip(
        inputs["turnovers"],
        expected["table"],
        strict=True,
    ):
        for bps, cost in zip(inputs["transaction_cost_bps"], row, strict=True):
            observed = post_return_equity_cost(
                turnover,
                bps,
                inputs["gross_multiplier"],
            )
            assert math.isclose(
                observed,
                cost,
                rel_tol=expected["rel_tol"],
                abs_tol=expected["abs_tol"],
            )


def test_unit_multiplier_sequence_turnovers_and_costs() -> None:
    fixture = load_runner_fixture("unit_multiplier_cost_table.json")
    inputs = fixture["inputs"]
    expected = fixture["expected"]
    sequence = inputs["sequence"]
    for bps in inputs["transaction_cost_bps"]:
        holdings = advance_holdings(
            runner_weight_map(
                inputs["exchange"],
                inputs["effective_from"],
                inputs["effective_to"],
                sequence["initial_weights"],
            ),
            tuple(
                runner_holding_interval(
                    session_date,
                    inputs["exchange"],
                    inputs["effective_from"],
                    inputs["effective_to"],
                    sequence["held_returns"],
                    reset,
                )
                for session_date, reset in zip(
                    sequence["session_dates"],
                    sequence["resets"],
                    strict=True,
                )
            ),
            bps,
            inputs["initial_equity"],
        )
        assert holdings.valid
        turnovers = tuple(point.turnover for point in holdings.points)
        costs = tuple(point.cost_impact for point in holdings.points)
        for observed, wanted in zip(
            turnovers,
            expected["sequence_turnovers"],
            strict=True,
        ):
            assert observed is not None
            assert math.isclose(
                observed,
                wanted,
                rel_tol=expected["rel_tol"],
                abs_tol=expected["abs_tol"],
            )
        for observed, wanted in zip(
            costs,
            expected["sequence_costs"][str(bps)],
            strict=True,
        ):
            assert observed is not None
            assert math.isclose(
                observed,
                wanted,
                rel_tol=expected["rel_tol"],
                abs_tol=expected["abs_tol"],
            )


def test_accounting_order_uses_post_return_equity() -> None:
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
    point = holdings.points[0]
    assert holdings.valid
    assert point.gross_return is not None
    assert point.gross_multiplier is not None
    assert point.turnover is not None
    assert point.cost_impact is not None
    assert point.net_return is not None
    assert math.isclose(
        point.gross_return,
        expected["gross_return"],
        rel_tol=expected["rel_tol"],
        abs_tol=expected["abs_tol"],
    )
    assert math.isclose(
        point.gross_multiplier,
        expected["gross_multiplier"],
        rel_tol=expected["rel_tol"],
        abs_tol=expected["abs_tol"],
    )
    assert math.isclose(
        point.turnover,
        expected["turnover"],
        rel_tol=expected["rel_tol"],
        abs_tol=expected["abs_tol"],
    )
    assert math.isclose(
        point.cost_impact,
        expected["cost_impact"],
        rel_tol=expected["rel_tol"],
        abs_tol=expected["abs_tol"],
    )
    assert math.isclose(
        point.net_return,
        expected["net_return"],
        rel_tol=expected["rel_tol"],
        abs_tol=expected["abs_tol"],
    )
    assert point.cost_impact != fixture["forbidden"]["pre_return_equity_cost"]
    totals = aggregate_contributions(holdings.points)
    assert totals.valid
    assert totals.cost_sum is not None
    assert math.isclose(
        totals.cost_sum,
        expected["contribution_cost_sum"],
        rel_tol=expected["rel_tol"],
        abs_tol=expected["abs_tol"],
    )


def test_random_rank_primary_basis_is_ten_bps_only() -> None:
    fixture = load_runner_fixture("random_rank_primary_basis.json")
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
    point = holdings.points[0]
    assert holdings.valid
    assert point.cost_impact is not None
    assert point.net_return is not None
    assert math.isclose(
        point.cost_impact,
        expected["cost_impact"],
        rel_tol=expected["rel_tol"],
        abs_tol=expected["abs_tol"],
    )
    assert math.isclose(
        point.net_return,
        expected["net_return"],
        rel_tol=expected["rel_tol"],
        abs_tol=expected["abs_tol"],
    )
    assert point.cost_impact != fixture["forbidden"]["zero_bps_cost"]
    assert point.net_return != fixture["forbidden"]["zero_bps_net"]
    assert point.cost_impact != fixture["forbidden"]["twenty_five_bps_cost"]
    assert point.net_return != fixture["forbidden"]["twenty_five_bps_net"]
    for bps in inputs["forbidden_bps"]:
        other = advance_holdings(
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
            bps,
            inputs["initial_equity"],
        )
        assert other.points[0].cost_impact != expected["cost_impact"]
        assert other.points[0].net_return != expected["net_return"]

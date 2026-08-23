"""Continuous path goldens: split, no-fill, and no terminal liquidation."""

from __future__ import annotations

import inspect
import math

from campaign.paths import (
    advance_holdings,
    holding_interval,
    post_return_equity_cost,
)
from campaign.returns import simple_adjusted_close_return
from campaign_runner_v1_support import (
    load_runner_fixture,
    runner_holding_interval,
    runner_return_map,
    runner_weight_map,
)


def test_split_corporate_action_uses_adjusted_not_raw() -> None:
    fixture = load_runner_fixture("split_corporate_action.json")
    inputs = fixture["inputs"]
    expected = fixture["expected"]
    adjusted_returns = {}
    for ticker, row in inputs["adjusted"].items():
        result = simple_adjusted_close_return(
            row["start_anchor"],
            row["end_anchor"],
            row["anchors"],
            row["target_identity"],
            row["alias_chain"],
        )
        assert result.valid
        assert result.value is not None
        assert math.isclose(
            result.value,
            expected["adjusted_held_returns"][ticker],
            rel_tol=expected["rel_tol"],
            abs_tol=expected["abs_tol"],
        )
        adjusted_returns[ticker] = result
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
                adjusted_returns,
                inputs["reset_weights"],
            ),
        ),
        inputs["transaction_cost_bps"],
        inputs["initial_equity"],
    )
    point = holdings.points[0]
    assert holdings.valid is expected["valid"]
    assert point.gross_return is not None
    assert point.turnover is not None
    assert point.cost_impact is not None
    assert math.isclose(
        point.gross_return,
        expected["gross_return"],
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
    drifted = {
        ticker: point.drifted_weights[
            runner_weight_map(
                inputs["exchange"],
                inputs["effective_from"],
                inputs["effective_to"],
                {ticker: expected["drifted_weights"][ticker]},
            ).popitem()[0]
        ]
        for ticker in expected["drifted_weights"]
    }
    for ticker, weight in expected["drifted_weights"].items():
        assert math.isclose(
            drifted[ticker],
            weight,
            rel_tol=expected["rel_tol"],
            abs_tol=expected["abs_tol"],
        )
    raw = advance_holdings(
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
                fixture["forbidden"]["raw_held_returns"],
                inputs["reset_weights"],
            ),
        ),
        inputs["transaction_cost_bps"],
        inputs["initial_equity"],
    )
    raw_point = raw.points[0]
    assert raw_point.gross_return == fixture["forbidden"]["raw_gross_return"]
    assert raw_point.turnover == fixture["forbidden"]["raw_turnover"]
    assert raw_point.cost_impact == fixture["forbidden"]["raw_cost_impact"]
    assert point.gross_return != fixture["forbidden"]["raw_gross_return"]
    assert point.turnover != fixture["forbidden"]["raw_turnover"]
    assert point.cost_impact != fixture["forbidden"]["raw_cost_impact"]


def test_no_terminal_liquidation_when_reset_is_absent() -> None:
    fixture = load_runner_fixture("valid_tied_valid_three_month.json")
    inputs = fixture["inputs"]
    expected = fixture["expected"]
    spec = inputs["strategy"]
    holdings = advance_holdings(
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
        inputs["transaction_cost_bps"][0],
        inputs["initial_equity"],
    )
    turnovers = tuple(point.turnover for point in holdings.points)
    for observed, wanted in zip(
        turnovers,
        expected["connected_turnovers"],
        strict=True,
    ):
        assert observed is not None
        assert math.isclose(
            observed,
            wanted,
            rel_tol=expected["rel_tol"],
            abs_tol=expected["abs_tol"],
        )
    deploy = advance_holdings(
        runner_weight_map(
            inputs["exchange"],
            inputs["effective_from"],
            inputs["effective_to"],
            {},
        ),
        (
            runner_holding_interval(
                inputs["deployment"]["session_date"],
                inputs["exchange"],
                inputs["effective_from"],
                inputs["effective_to"],
                inputs["deployment"]["held_returns"],
                inputs["deployment"]["reset_weights"],
            ),
        ),
        inputs["transaction_cost_bps"][0],
        inputs["initial_equity"],
    )
    assert deploy.points[0].turnover == expected["deployment_turnover"]


def test_path_entry_points_have_no_fill_or_defaults() -> None:
    for function in (advance_holdings, holding_interval, post_return_equity_cost):
        names = inspect.signature(function).parameters
        assert "fill" not in names
        assert "interpolate" not in names
        for parameter in names.values():
            assert parameter.default is inspect.Parameter.empty


def test_runner_return_map_encodes_fixture_tickers() -> None:
    fixture = load_runner_fixture("accounting_order_golden.json")
    inputs = fixture["inputs"]
    encoded = runner_return_map(
        inputs["exchange"],
        inputs["effective_from"],
        inputs["effective_to"],
        inputs["held_returns"],
    )
    assert len(encoded) == len(inputs["held_returns"])

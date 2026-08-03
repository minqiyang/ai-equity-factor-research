"""Conformance bindings to existing strategy turnover and cost accounting."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from backtest.portfolio import (
    capture_backtest_source_provenance,
    run_long_only_backtest,
)


def _run(
    prices: pd.DataFrame,
    signals: pd.DataFrame,
    *,
    transaction_cost_bps: float,
    top_n: int,
):
    return run_long_only_backtest(
        prices,
        signals,
        source_provenance=capture_backtest_source_provenance(prices, signals),
        evaluation_start=prices.index[0],
        evaluation_end=prices.index[-1],
        rebalance_frequency="D",
        top_n=top_n,
        transaction_cost_bps=transaction_cost_bps,
    )


@pytest.mark.parametrize(
    ("bps", "expected_costs"),
    [
        (0, (0.0, 0.0, 0.0)),
        (10, (0.0010, 0.0004, 0.0020)),
        (25, (0.0025, 0.0010, 0.0050)),
    ],
)
def test_fixed_bps_cost_table_binds_strategy_turnover_and_costs(
    bps: int,
    expected_costs: tuple[float, float, float],
) -> None:
    dates = pd.date_range("2026-01-01", periods=5, freq="D")
    columns = list("ABCDEFGHIJK")
    prices = pd.DataFrame(100.0, index=dates, columns=columns)
    signals = pd.DataFrame(0.0, index=dates, columns=columns)
    signals.loc[dates[0], list("ABCDE")] = 1.0
    signals.loc[dates[1], list("BCDEF")] = 1.0
    signals.loc[dates[2], list("GHIJK")] = 1.0
    signals.loc[dates[3], list("GHIJK")] = 1.0

    result = _run(
        prices,
        signals,
        transaction_cost_bps=float(bps),
        top_n=5,
    )

    observed_turnovers = tuple(
        float(result.turnover.loc[date]) for date in dates[1:4]
    )
    observed_costs = tuple(
        float(result.transaction_costs.loc[date]) for date in dates[1:4]
    )
    assert observed_turnovers == pytest.approx((1.0, 0.4, 2.0), abs=1e-15)
    assert observed_costs == pytest.approx(expected_costs, abs=1e-15)


@pytest.mark.parametrize(
    ("bps", "expected_cost", "expected_net"),
    [(25, 0.0055, 0.0945), (10, 0.0022, 0.0978)],
)
def test_post_return_execution_cost_goldens_bind_existing_accounting(
    bps: int,
    expected_cost: float,
    expected_net: float,
) -> None:
    dates = pd.date_range("2026-02-01", periods=4, freq="D")
    prices = pd.DataFrame(
        {
            "AAA": [100.0, 100.0, 110.0, 110.0],
            "BBB": [100.0, 100.0, 100.0, 100.0],
        },
        index=dates,
    )
    signals = pd.DataFrame(
        {
            "AAA": [2.0, 1.0, 1.0, 1.0],
            "BBB": [1.0, 2.0, 2.0, 2.0],
        },
        index=dates,
    )
    result = _run(
        prices,
        signals,
        transaction_cost_bps=float(bps),
        top_n=1,
    )
    rebalance = dates[2]

    assert result.gross_returns.loc[rebalance] == pytest.approx(0.10)
    assert result.turnover.loc[rebalance] == pytest.approx(2.0)
    assert math.isclose(
        float(result.transaction_costs.loc[rebalance]),
        expected_cost,
        abs_tol=1e-15,
    )
    assert math.isclose(
        float(result.returns.loc[rebalance]),
        expected_net,
        abs_tol=1e-15,
    )

    forbidden_pre_return_equity_cost = 2.0 * bps / 10000
    assert not math.isclose(
        forbidden_pre_return_equity_cost,
        expected_cost,
        abs_tol=1e-15,
    )

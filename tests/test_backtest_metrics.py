import math
from fractions import Fraction

import numpy as np
import pandas as pd
import pytest

from backtest.metrics import (
    calculate_basic_metrics,
    calculate_holding_episode_metrics,
    calculate_holdings_state_metrics,
    calculate_max_drawdown,
    calculate_tracking_error,
)


def test_holding_episode_metrics_include_entry_exit_returns_and_costs() -> None:
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    holdings = pd.DataFrame({"AAA": [0.5, 0.5, 0.5, 0.0]}, index=dates)
    asset_returns = pd.DataFrame({"AAA": [0.0, 0.1, -0.05, 0.2]}, index=dates)
    signed_trades = pd.DataFrame({"AAA": [0.5, 0.0, 0.0, -0.5]}, index=dates)
    trades = signed_trades.abs()
    turnover = trades.sum(axis=1)
    costs = pd.Series([0.005, 0.0, 0.0, 0.005], index=dates)

    metrics, closed_count, open_count = calculate_holding_episode_metrics(
        holdings,
        asset_returns,
        signed_trades,
        trades,
        turnover,
        costs,
    )

    assert metrics["episode_hit_rate"] == pytest.approx(1.0)
    assert metrics["average_holding_period_return"] == pytest.approx(0.23)
    assert closed_count == 1
    assert open_count == 0


def test_holding_episode_metrics_keep_resizes_and_split_reentry() -> None:
    dates = pd.date_range("2024-01-01", periods=6, freq="D")
    holdings = pd.DataFrame({"AAA": [0.4, 0.6, 0.2, 0.0, 0.5, 0.0]}, index=dates)
    asset_returns = pd.DataFrame({"AAA": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}, index=dates)
    signed_trades = pd.DataFrame(
        {"AAA": [0.4, 0.2, -0.4, -0.2, 0.5, -0.5]},
        index=dates,
    )
    trades = signed_trades.abs()
    turnover = trades.sum(axis=1)
    costs = pd.Series(0.0, index=dates)

    metrics, closed_count, open_count = calculate_holding_episode_metrics(
        holdings,
        asset_returns,
        signed_trades,
        trades,
        turnover,
        costs,
    )

    assert metrics["episode_hit_rate"] == pytest.approx(0.0)
    assert metrics["average_holding_period_return"] == pytest.approx(0.0)
    assert closed_count == 2
    assert open_count == 0


def test_holding_episode_metrics_exclude_terminal_open_episode() -> None:
    dates = pd.date_range("2024-01-01", periods=2, freq="D")
    holdings = pd.DataFrame({"AAA": [0.5, 0.5]}, index=dates)
    asset_returns = pd.DataFrame({"AAA": [0.0, 0.1]}, index=dates)
    signed_trades = pd.DataFrame({"AAA": [0.5, 0.0]}, index=dates)
    trades = signed_trades.abs()

    metrics, closed_count, open_count = calculate_holding_episode_metrics(
        holdings,
        asset_returns,
        signed_trades,
        trades,
        trades.sum(axis=1),
        pd.Series(0.0, index=dates),
    )

    assert math.isnan(metrics["episode_hit_rate"])
    assert math.isnan(metrics["average_holding_period_return"])
    assert closed_count == 0
    assert open_count == 1


def test_holding_episode_metrics_reject_accounting_mismatch() -> None:
    dates = pd.date_range("2024-01-01", periods=2, freq="D")
    holdings = pd.DataFrame({"AAA": [0.5, 0.0]}, index=dates)
    returns = pd.DataFrame({"AAA": [0.0, 0.0]}, index=dates)
    signed = pd.DataFrame({"AAA": [0.5, -0.5]}, index=dates)
    trades = signed.abs()

    with pytest.raises(ValueError, match="absolute signed trades"):
        calculate_holding_episode_metrics(
            holdings,
            returns,
            signed,
            trades * 0.5,
            trades.sum(axis=1),
            pd.Series(0.0, index=dates),
        )

    with pytest.raises(ValueError, match="zero when turnover is zero"):
        calculate_holding_episode_metrics(
            holdings * 0.0,
            returns,
            signed * 0.0,
            trades * 0.0,
            pd.Series(0.0, index=dates),
            pd.Series([0.01, 0.0], index=dates),
        )


def test_holding_episode_metrics_equal_weight_completed_episodes_and_costs() -> None:
    dates = pd.date_range("2024-01-01", periods=2, freq="D")
    holdings = pd.DataFrame(
        {"AAA": [0.5, 0.0], "BBB": [0.5, 0.0]},
        index=dates,
    )
    returns = pd.DataFrame(
        {"AAA": [0.0, 0.1], "BBB": [0.0, -0.1]},
        index=dates,
    )
    signed = pd.DataFrame(
        {"AAA": [0.5, -0.5], "BBB": [0.5, -0.5]},
        index=dates,
    )
    trades = signed.abs()

    metrics, closed_count, _ = calculate_holding_episode_metrics(
        holdings,
        returns,
        signed,
        trades,
        trades.sum(axis=1),
        pd.Series([0.01, 0.01], index=dates),
    )

    assert metrics["episode_hit_rate"] == pytest.approx(0.5)
    assert metrics["average_holding_period_return"] == pytest.approx(-0.02)
    assert closed_count == 2


def test_holding_episode_metrics_total_loss_closes_without_exit_trade() -> None:
    dates = pd.date_range("2024-01-01", periods=2, freq="D")
    holdings = pd.DataFrame({"AAA": [0.5, 0.0]}, index=dates)
    returns = pd.DataFrame({"AAA": [0.0, -1.0]}, index=dates)
    signed = pd.DataFrame({"AAA": [0.5, 0.0]}, index=dates)
    trades = signed.abs()

    metrics, closed_count, open_count = calculate_holding_episode_metrics(
        holdings,
        returns,
        signed,
        trades,
        trades.sum(axis=1),
        pd.Series(0.0, index=dates),
    )

    assert metrics["episode_hit_rate"] == pytest.approx(0.0)
    assert metrics["average_holding_period_return"] == pytest.approx(-1.0)
    assert closed_count == 1
    assert open_count == 0


def test_holding_episode_metrics_reject_axis_and_return_contract_violations() -> None:
    dates = pd.date_range("2024-01-01", periods=2, freq="D")
    holdings = pd.DataFrame({"AAA": [0.5, 0.0]}, index=dates)
    signed = pd.DataFrame({"AAA": [0.5, -0.5]}, index=dates)
    trades = signed.abs()

    with pytest.raises(ValueError, match="axes must exactly match holdings"):
        calculate_holding_episode_metrics(
            holdings,
            pd.DataFrame({"BBB": [0.0, 0.0]}, index=dates),
            signed,
            trades,
            trades.sum(axis=1),
            pd.Series(0.0, index=dates),
        )

    with pytest.raises(ValueError, match="must not be below -1"):
        calculate_holding_episode_metrics(
            holdings,
            pd.DataFrame({"AAA": [0.0, -1.1]}, index=dates),
            signed,
            trades,
            trades.sum(axis=1),
            pd.Series(0.0, index=dates),
        )


def _holdings(values: dict[str, list[object]]) -> pd.DataFrame:
    first_column = next(iter(values.values()))
    index = pd.date_range("2024-01-01", periods=len(first_column), freq="D")
    return pd.DataFrame(values, index=index)


def test_holdings_state_metrics_are_hand_calculated_and_gross_normalized() -> None:
    holdings = _holdings(
        {
            "AAA": [0.0, 0.5, 0.25, 0.8, 1.0],
            "BBB": [0.0, 0.5, 0.25, 0.2, 0.0],
            "CCC": [0.0, 0.0, 0.0, 0.0, 0.0],
        }
    )

    metrics = calculate_holdings_state_metrics(holdings)

    assert metrics["average_holding_count"] == pytest.approx(1.75)
    assert metrics["average_position_concentration_hhi"] == pytest.approx(0.67)
    assert metrics["max_position_concentration_hhi"] == pytest.approx(1.0)

    partial_cash = calculate_holdings_state_metrics(
        holdings.loc[[holdings.index[2]]]
    )
    assert partial_cash["average_position_concentration_hhi"] == pytest.approx(0.5)
    assert partial_cash["average_position_concentration_hhi"] != pytest.approx(0.125)


def test_holdings_state_hhi_is_rounded_for_stable_serialization() -> None:
    holdings = pd.DataFrame(
        [[0.1, 0.2, 0.3]],
        index=pd.date_range("2024-01-01", periods=1),
        columns=["A", "B", "C"],
    )

    metrics = calculate_holdings_state_metrics(holdings)

    assert metrics["average_position_concentration_hhi"] == 0.388888888888889
    assert metrics["max_position_concentration_hhi"] == 0.388888888888889


def test_holdings_state_metrics_include_terminal_closing_snapshot() -> None:
    holdings = _holdings(
        {
            "AAA": [0.5, 0.5, 1.0],
            "BBB": [0.5, 0.5, 0.0],
        }
    )

    metrics = calculate_holdings_state_metrics(holdings)

    assert metrics["average_holding_count"] == pytest.approx(5.0 / 3.0)
    assert metrics["average_position_concentration_hhi"] == pytest.approx(2.0 / 3.0)
    assert metrics["max_position_concentration_hhi"] == pytest.approx(1.0)


def test_holdings_state_metrics_return_nan_without_active_dates() -> None:
    metrics = calculate_holdings_state_metrics(
        _holdings({"AAA": [0.0, 0.0], "BBB": [0.0, 0.0]})
    )

    assert all(math.isnan(value) for value in metrics.values())


@pytest.mark.parametrize(
    ("holdings", "error_type", "match"),
    [
        (pd.DataFrame({"AAA": [0.5]}), TypeError, "DatetimeIndex"),
        (_holdings({"AAA": [np.nan]}), ValueError, "missing"),
        (_holdings({"AAA": [np.inf]}), ValueError, "finite"),
        (_holdings({"AAA": [-0.1]}), ValueError, "non-negative"),
        (_holdings({"AAA": [0.6], "BBB": [0.5]}), ValueError, "gross exposure"),
        (_holdings({"AAA": ["0.5"]}), TypeError, "numeric, non-boolean"),
        (_holdings({"AAA": [True]}), TypeError, "numeric, non-boolean"),
        (_holdings({"AAA": [0.5 + 99j]}), TypeError, "numeric, non-boolean"),
    ],
)
def test_holdings_state_metrics_reject_invalid_values(
    holdings: pd.DataFrame,
    error_type: type[Exception],
    match: str,
) -> None:
    with pytest.raises(error_type, match=match):
        calculate_holdings_state_metrics(holdings)


def test_holdings_state_metrics_reject_duplicate_and_unsorted_axes() -> None:
    duplicate_dates = _holdings({"AAA": [0.5, 0.5]})
    duplicate_dates.index = pd.DatetimeIndex(
        [duplicate_dates.index[0], duplicate_dates.index[0]]
    )
    with pytest.raises(ValueError, match="duplicate dates"):
        calculate_holdings_state_metrics(duplicate_dates)

    unsorted = _holdings({"AAA": [0.5, 0.5]}).sort_index(ascending=False)
    with pytest.raises(ValueError, match="sorted"):
        calculate_holdings_state_metrics(unsorted)

    duplicate_assets = _holdings({"AAA": [0.5]})
    duplicate_assets["BBB"] = 0.5
    duplicate_assets.columns = ["AAA", "AAA"]
    with pytest.raises(ValueError, match="duplicate assets"):
        calculate_holdings_state_metrics(duplicate_assets)


def test_max_drawdown_uses_keyword_capital_anchor() -> None:
    index = pd.date_range("2024-01-01", periods=3, freq="D")
    equity = pd.Series([0.90, 0.95, 0.80], index=index)

    assert calculate_max_drawdown(
        equity,
        initial_capital=1.0,
    ) == pytest.approx(-0.20)
    with pytest.raises(TypeError):
        calculate_max_drawdown(equity, 1.0)  # type: ignore[misc]


def test_basic_metrics_match_four_row_timing_reference() -> None:
    index = pd.date_range("2024-01-01", periods=4, freq="D")
    returns = pd.Series([0.0, -0.01, 0.078, 0.0], index=index)
    equity = pd.Series([1.0, 0.99, 1.06722, 1.06722], index=index)
    turnover = pd.Series([0.0, 1.0, 2.0, 0.0], index=index)
    transaction_costs = pd.Series([0.0, 0.01, 0.022, 0.0], index=index)
    benchmark_returns = pd.Series([0.0, 0.01, -0.02, 0.03], index=index)
    benchmark_equity = (1.0 + benchmark_returns).cumprod()

    metrics = calculate_basic_metrics(
        equity,
        returns,
        turnover=turnover,
        transaction_costs=transaction_costs,
        benchmark_equity_curve=benchmark_equity,
        benchmark_returns=benchmark_returns,
        initial_capital=1.0,
        periods_per_year=252,
    )

    measured_returns = returns.loc[index[1:]]
    measured_benchmark = benchmark_returns.loc[index[1:]]
    expected_benchmark_total = float((1.0 + measured_benchmark).prod() - 1.0)
    expected_active = measured_returns - measured_benchmark

    assert metrics["total_return"] == pytest.approx(0.06722)
    assert metrics["annualized_return"] == pytest.approx(
        1.06722 ** (252 / 3) - 1.0
    )
    assert metrics["annualized_volatility"] == pytest.approx(
        measured_returns.std(ddof=0) * np.sqrt(252)
    )
    assert metrics["sharpe_ratio"] == pytest.approx(
        measured_returns.mean()
        / measured_returns.std(ddof=0)
        * np.sqrt(252)
    )
    assert metrics["max_drawdown"] == pytest.approx(-0.01)
    assert metrics["average_turnover"] == pytest.approx(1.0)
    assert metrics["total_turnover"] == pytest.approx(3.0)
    assert metrics["total_transaction_cost_impact"] == pytest.approx(0.032)
    assert metrics["total_trading_cost_impact"] == pytest.approx(0.032)
    assert metrics["benchmark_total_return"] == pytest.approx(
        expected_benchmark_total
    )
    assert metrics["excess_total_return"] == pytest.approx(
        0.06722 - expected_benchmark_total
    )
    assert metrics["tracking_error"] == pytest.approx(
        expected_active.std(ddof=0) * np.sqrt(252)
    )


def test_basic_metrics_use_measured_rows_for_averages_and_all_rows_for_totals() -> None:
    index = pd.date_range("2024-01-01", periods=4, freq="D")
    returns = pd.Series([0.0, 0.01, -0.02, 0.03], index=index)
    equity = (1.0 + returns).cumprod()
    turnover = pd.Series([10.0, 1.0, 2.0, 3.0], index=index)
    transaction_costs = pd.Series([0.4, 0.1, 0.2, 0.3], index=index)
    slippage_costs = pd.Series([0.04, 0.01, 0.02, 0.03], index=index)
    volume_costs = pd.Series([0.004, 0.001, 0.002, 0.003], index=index)

    metrics = calculate_basic_metrics(
        equity,
        returns,
        turnover=turnover,
        transaction_costs=transaction_costs,
        slippage_costs=slippage_costs,
        volume_aware_slippage_costs=volume_costs,
    )

    assert metrics["total_return"] == pytest.approx(equity.iloc[-1] - 1.0)
    assert metrics["average_turnover"] == pytest.approx(2.0)
    assert metrics["total_turnover"] == pytest.approx(16.0)
    assert metrics["total_transaction_cost_impact"] == pytest.approx(1.0)
    assert metrics["total_slippage_cost_impact"] == pytest.approx(0.1)
    assert metrics["total_volume_aware_slippage_cost_impact"] == pytest.approx(
        0.01
    )
    assert metrics["total_trading_cost_impact"] == pytest.approx(1.11)


@pytest.mark.parametrize(
    "initial_capital",
    [
        True,
        False,
        np.bool_(True),
        1.0 + 0.0j,
        "1.0",
        None,
        pd.NA,
        0.0,
        -1.0,
        np.nan,
        np.inf,
        -np.inf,
        Fraction(10**400, 1),
    ],
)
def test_metric_helpers_reject_invalid_initial_capital(
    initial_capital: object,
) -> None:
    index = pd.date_range("2024-01-01", periods=2, freq="D")
    equity = pd.Series([1.0, 1.01], index=index)
    returns = pd.Series([0.0, 0.01], index=index)

    with pytest.raises(ValueError, match="initial_capital_invalid"):
        calculate_max_drawdown(
            equity,
            initial_capital=initial_capital,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="initial_capital_invalid"):
        calculate_basic_metrics(
            equity,
            returns,
            initial_capital=initial_capital,  # type: ignore[arg-type]
        )


def test_metric_helpers_reject_stateful_initial_capital_without_conversion() -> None:
    class StatefulFloat(float):
        def __new__(cls, value: float):
            instance = super().__new__(cls, value)
            instance.float_calls = 0
            return instance

        def __float__(self) -> float:
            self.float_calls += 1
            return 1.0 if self.float_calls == 1 else 2.0

    index = pd.date_range("2024-01-01", periods=2, freq="D")
    equity = pd.Series([1.0, 1.01], index=index)
    returns = pd.Series([0.0, 0.01], index=index)
    capital = StatefulFloat(1.0)

    with pytest.raises(ValueError, match="initial_capital_invalid"):
        calculate_max_drawdown(equity, initial_capital=capital)
    with pytest.raises(ValueError, match="initial_capital_invalid"):
        calculate_basic_metrics(equity, returns, initial_capital=capital)

    assert capital.float_calls == 0


def test_max_drawdown_rejects_invalid_equity_matrix() -> None:
    index = pd.date_range("2024-01-01", periods=3, freq="D")
    duplicate_index = pd.DatetimeIndex([index[0], index[0], index[2]])
    invalid_equity_curves: list[object] = [
        [1.0, 1.1, 1.2],
        pd.Series(dtype=float, index=pd.DatetimeIndex([])),
        pd.Series([1.0, 1.1, 1.2]),
        pd.Series([1.0, 1.1, 1.2], index=duplicate_index),
        pd.Series([1.0, 1.1, 1.2], index=index[::-1]),
        pd.Series([1.0, 0.0, 1.2], index=index),
        pd.Series([1.0, -0.1, 1.2], index=index),
        pd.Series([1.0, np.nan, 1.2], index=index),
        pd.Series([1.0, np.inf, 1.2], index=index),
        pd.Series([1.0, -np.inf, 1.2], index=index),
        pd.Series([True, True, True], index=index),
        pd.Series([1.0 + 0.0j, 1.1 + 1.0j, 1.2 + 0.0j], index=index),
        pd.Series(["1.0", "1.1", "1.2"], index=index),
    ]

    for equity_curve in invalid_equity_curves:
        with pytest.raises(ValueError, match="equity_curve_invalid"):
            calculate_max_drawdown(
                equity_curve,  # type: ignore[arg-type]
                initial_capital=1.0,
            )


def test_basic_metrics_reject_invalid_returns_matrix() -> None:
    index = pd.date_range("2024-01-01", periods=3, freq="D")
    equity = pd.Series([1.0, 1.01, 1.02], index=index)
    duplicate_index = pd.DatetimeIndex([index[0], index[0], index[2]])
    invalid_returns: list[object] = [
        [0.0, 0.01, 0.02],
        pd.Series(dtype=float, index=pd.DatetimeIndex([])),
        pd.Series([0.0, 0.01, 0.02]),
        pd.Series([0.0, 0.01, 0.02], index=duplicate_index),
        pd.Series([0.0, 0.01, 0.02], index=index[::-1]),
        pd.Series([False, False, False], index=index),
        pd.Series([0.0 + 0.0j, 0.01 + 1.0j, 0.02 + 0.0j], index=index),
        pd.Series(["0.0", "0.01", "0.02"], index=index),
        pd.Series([0.0, np.nan, 0.02], index=index),
        pd.Series([0.0, np.inf, 0.02], index=index),
        pd.Series([0.0, -np.inf, 0.02], index=index),
        pd.Series([0.01, 0.01, 0.02], index=index),
        pd.Series([0.0], index=index[:1]),
    ]

    for invalid in invalid_returns:
        with pytest.raises(ValueError, match="returns_invalid"):
            calculate_basic_metrics(
                equity,
                invalid,  # type: ignore[arg-type]
            )


def test_basic_metrics_require_exact_equity_return_axes() -> None:
    index = pd.date_range("2024-01-01", periods=3, freq="D")
    returns = pd.Series([0.0, 0.01, 0.02], index=index)
    exact_equity = pd.Series([1.0, 1.01, 1.0302], index=index)
    extra_index = index.append(pd.DatetimeIndex([index[-1] + pd.Timedelta(days=1)]))
    invalid_equity_curves = [
        exact_equity.iloc[:-1],
        pd.Series([1.0, 1.01, 1.0302, 1.04], index=extra_index),
        exact_equity.shift(freq="D"),
        exact_equity.tz_localize("UTC"),
    ]

    for invalid_equity in invalid_equity_curves:
        with pytest.raises(ValueError, match="equity_curve_invalid"):
            calculate_basic_metrics(invalid_equity, returns)


@pytest.mark.parametrize(
    ("final_equity", "initial_capital"),
    [
        (1e308, 1e-308),
        (1e308, 1.0),
    ],
)
def test_basic_metrics_reject_non_finite_geometric_results(
    final_equity: float,
    initial_capital: float,
) -> None:
    index = pd.date_range("2024-01-01", periods=2, freq="D")
    equity = pd.Series([1.0, final_equity], index=index)
    returns = pd.Series([0.0, 0.0], index=index)

    with pytest.raises(ValueError, match="equity_curve_invalid"):
        calculate_basic_metrics(
            equity,
            returns,
            initial_capital=initial_capital,
        )


@pytest.mark.parametrize(
    "periods_per_year",
    [False, True, np.bool_(False), 251, 365, 252.0, "252", None],
)
def test_basic_metrics_require_exact_daily_annualizer(
    periods_per_year: object,
) -> None:
    index = pd.date_range("2024-01-01", periods=2, freq="D")
    returns = pd.Series([0.0, 0.01], index=index)
    equity = (1.0 + returns).cumprod()

    with pytest.raises(ValueError, match="periods_per_year_invalid"):
        calculate_basic_metrics(
            equity,
            returns,
            periods_per_year=periods_per_year,  # type: ignore[arg-type]
        )

    metrics = calculate_basic_metrics(
        equity,
        returns,
        periods_per_year=np.int64(252),
    )
    assert metrics["annualized_return"] == pytest.approx(1.01**252 - 1.0)


def test_basic_metrics_reject_stateful_integer_annualizer_without_conversion() -> None:
    class StatefulInt(int):
        def __new__(cls, value: int):
            instance = super().__new__(cls, value)
            instance.int_calls = 0
            return instance

        def __int__(self) -> int:
            self.int_calls += 1
            return 365

    index = pd.date_range("2024-01-01", periods=2, freq="D")
    returns = pd.Series([0.0, 0.01], index=index)
    equity = (1.0 + returns).cumprod()
    annualizer = StatefulInt(252)

    with pytest.raises(ValueError, match="periods_per_year_invalid"):
        calculate_basic_metrics(
            equity,
            returns,
            periods_per_year=annualizer,
        )

    assert annualizer.int_calls == 0


@pytest.mark.parametrize(
    "parameter_name",
    [
        "turnover",
        "transaction_costs",
        "slippage_costs",
        "volume_aware_slippage_costs",
    ],
)
def test_basic_metrics_reject_invalid_optional_accounting_series(
    parameter_name: str,
) -> None:
    index = pd.date_range("2024-01-01", periods=4, freq="D")
    returns = pd.Series([0.0, 0.01, 0.02, 0.03], index=index)
    equity = (1.0 + returns).cumprod()
    valid = pd.Series([0.0, 0.1, 0.2, 0.3], index=index)
    duplicate_index = pd.DatetimeIndex([index[0], index[0], index[2], index[3]])
    extra_index = index.append(pd.DatetimeIndex([index[-1] + pd.Timedelta(days=1)]))
    invalid_series: list[object] = [
        valid.tolist(),
        pd.Series(valid.to_numpy()),
        pd.Series(valid.to_numpy(), index=duplicate_index),
        valid.sort_index(ascending=False),
        valid.iloc[:-1],
        pd.Series([0.0, 0.1, 0.2, 0.3, 0.4], index=extra_index),
        valid.shift(freq="D"),
        valid.tz_localize("UTC"),
        pd.Series([False, False, False, False], index=index),
        pd.Series([0.0 + 0.0j, 0.1 + 1.0j, 0.2, 0.3], index=index),
        pd.Series(["0.0", "0.1", "0.2", "0.3"], index=index),
        pd.Series([0.0, np.nan, 0.2, 0.3], index=index),
        pd.Series([0.0, np.inf, 0.2, 0.3], index=index),
        pd.Series([0.0, -np.inf, 0.2, 0.3], index=index),
        pd.Series([0.0, -0.1, 0.2, 0.3], index=index),
    ]

    for invalid in invalid_series:
        with pytest.raises(ValueError, match=f"{parameter_name}_invalid"):
            calculate_basic_metrics(
                equity,
                returns,
                **{parameter_name: invalid},
            )


def test_basic_metrics_reject_invalid_benchmark_metric_series() -> None:
    index = pd.date_range("2024-01-01", periods=4, freq="D")
    returns = pd.Series([0.0, 0.01, 0.02, 0.03], index=index)
    equity = (1.0 + returns).cumprod()
    benchmark_returns = pd.Series([0.0, 0.0, 0.01, 0.01], index=index)
    benchmark_equity = (1.0 + benchmark_returns).cumprod()

    invalid_benchmark_equity = [
        benchmark_equity.iloc[:-1],
        benchmark_equity.shift(freq="D"),
        benchmark_equity.tz_localize("UTC"),
        pd.Series([1.0, np.nan, 1.01, 1.02], index=index),
        pd.Series([1.0, 0.0, 1.01, 1.02], index=index),
        pd.Series([True, True, True, True], index=index),
    ]
    for invalid in invalid_benchmark_equity:
        with pytest.raises(ValueError, match="benchmark_equity_curve_invalid"):
            calculate_basic_metrics(
                equity,
                returns,
                benchmark_equity_curve=invalid,
            )

    invalid_benchmark_returns = [
        benchmark_returns.iloc[:-1],
        benchmark_returns.shift(freq="D"),
        benchmark_returns.tz_localize("UTC"),
        pd.Series([0.0, np.nan, 0.01, 0.01], index=index),
        pd.Series([False, False, False, False], index=index),
        pd.Series([0.01, 0.0, 0.01, 0.01], index=index),
    ]
    for invalid in invalid_benchmark_returns:
        with pytest.raises(ValueError, match="benchmark_returns_invalid"):
            calculate_basic_metrics(
                equity,
                returns,
                benchmark_returns=invalid,
            )


def test_basic_metrics_require_returns_for_benchmark_equity() -> None:
    index = pd.date_range("2024-01-01", periods=3, freq="D")
    returns = pd.Series([0.0, 0.01, 0.02], index=index)
    equity = (1.0 + returns).cumprod()
    flat_benchmark_equity = pd.Series([2.0, 2.0, 2.0], index=index)

    with pytest.raises(ValueError, match="benchmark_returns_invalid"):
        calculate_basic_metrics(
            equity,
            returns,
            benchmark_equity_curve=flat_benchmark_equity,
        )


def test_basic_metrics_compound_benchmark_returns_from_shared_anchor() -> None:
    index = pd.date_range("2024-01-01", periods=3, freq="D")
    returns = pd.Series([0.0, 0.01, 0.02], index=index)
    equity = (1.0 + returns).cumprod()
    benchmark_returns = pd.Series([0.0, 0.00, 0.01], index=index)

    metrics = calculate_basic_metrics(
        equity,
        returns,
        benchmark_returns=benchmark_returns,
    )

    assert metrics["benchmark_total_return"] == pytest.approx(0.01)
    assert metrics["excess_total_return"] == pytest.approx(
        float(equity.iloc[-1] - 1.0) - 0.01
    )


def test_basic_metrics_reject_nonpositive_benchmark_period_multipliers() -> None:
    index = pd.date_range("2024-01-01", periods=3, freq="D")
    returns = pd.Series([0.0, 0.01, 0.02], index=index)
    equity = (1.0 + returns).cumprod()
    benchmark_returns = pd.Series([0.0, -2.0, -2.0], index=index)

    with pytest.raises(ValueError, match="benchmark_returns_invalid"):
        calculate_basic_metrics(
            equity,
            returns,
            benchmark_returns=benchmark_returns,
        )


def test_basic_metrics_require_benchmark_equity_to_match_return_path() -> None:
    index = pd.date_range("2024-01-01", periods=3, freq="D")
    returns = pd.Series([0.0, 0.01, 0.02], index=index)
    equity = (1.0 + returns).cumprod()
    benchmark_returns = pd.Series([0.0, 0.00, 0.01], index=index)
    mismatched_benchmark_equity = pd.Series([2.0, 2.0, 2.02], index=index)

    with pytest.raises(ValueError, match="benchmark_equity_curve_invalid"):
        calculate_basic_metrics(
            equity,
            returns,
            benchmark_equity_curve=mismatched_benchmark_equity,
            benchmark_returns=benchmark_returns,
        )


def test_basic_metrics_benchmark_path_check_scales_with_initial_capital() -> None:
    index = pd.date_range("2024-01-01", periods=3, freq="D")
    initial_capital = 1e-20
    returns = pd.Series([0.0, 0.01, 0.02], index=index)
    equity = initial_capital * (1.0 + returns).cumprod()
    benchmark_returns = pd.Series([0.0, 0.0, 0.0], index=index)
    mismatched_benchmark_equity = pd.Series([5e-13, 5e-13, 5e-13], index=index)

    with pytest.raises(ValueError, match="benchmark_equity_curve_invalid"):
        calculate_basic_metrics(
            equity,
            returns,
            benchmark_equity_curve=mismatched_benchmark_equity,
            benchmark_returns=benchmark_returns,
            initial_capital=initial_capital,
        )


def test_basic_metrics_remain_backward_compatible_without_holdings() -> None:
    index = pd.date_range("2024-01-01", periods=2, freq="D")
    returns = pd.Series([0.0, 0.01], index=index)
    equity = (1.0 + returns).cumprod()

    metrics = calculate_basic_metrics(equity, returns)

    assert "average_holding_count" not in metrics
    assert "average_position_concentration_hhi" not in metrics
    assert "max_position_concentration_hhi" not in metrics


def test_basic_metrics_require_holdings_to_match_return_dates() -> None:
    index = pd.date_range("2024-01-01", periods=2, freq="D")
    returns = pd.Series([0.0, 0.01], index=index)
    equity = (1.0 + returns).cumprod()
    holdings = _holdings({"AAA": [0.0, 1.0]}).shift(freq="D")

    with pytest.raises(ValueError, match="holdings index must exactly match"):
        calculate_basic_metrics(equity, returns, holdings=holdings)


def test_tracking_error_is_hand_calculated_and_excludes_only_anchor() -> None:
    index = pd.date_range("2024-01-01", periods=4, freq="D")
    strategy_returns = pd.Series([99.0, 0.01, 0.03, -0.02], index=index)
    benchmark_returns = pd.Series([0.0, 0.0, 0.01, 0.0], index=index)

    result = calculate_tracking_error(
        strategy_returns,
        benchmark_returns,
        return_frequency="daily_close_to_close",
    )

    assert result == pytest.approx(np.std([0.01, 0.02, -0.02], ddof=0) * np.sqrt(252))
    changed_terminal = strategy_returns.copy()
    changed_terminal.iloc[-1] = 0.02
    assert calculate_tracking_error(
        changed_terminal,
        benchmark_returns,
        return_frequency="daily_close_to_close",
    ) != pytest.approx(result)


def test_tracking_error_rejects_invalid_return_values() -> None:
    index = pd.date_range("2024-01-01", periods=3, freq="D")
    valid = pd.Series([0.0, 0.01, 0.02], index=index)

    for invalid in [
        pd.Series([0.0, np.nan, 0.02], index=index),
        pd.Series([0.0, np.inf, 0.02], index=index),
        pd.Series([False, True, False], index=index),
        pd.Series([0.0 + 0.0j, 0.01 + 1.0j, 0.02 + 0.0j], index=index),
        pd.Series(["0.0", "0.01", "0.02"], index=index),
    ]:
        with pytest.raises((TypeError, ValueError)):
            calculate_tracking_error(
                invalid,
                valid,
                return_frequency="daily_close_to_close",
            )


def test_tracking_error_requires_exact_index_timezone_and_frequency() -> None:
    index = pd.date_range("2024-01-01", periods=3, freq="D")
    strategy_returns = pd.Series([0.0, 0.01, 0.02], index=index)
    benchmark_returns = pd.Series([0.0, 0.00, 0.01], index=index)

    with pytest.raises(ValueError, match="identical indexes"):
        calculate_tracking_error(
            strategy_returns,
            benchmark_returns.shift(freq="D"),
            return_frequency="daily_close_to_close",
        )
    with pytest.raises(ValueError, match="matching timezones"):
        calculate_tracking_error(
            strategy_returns,
            benchmark_returns.tz_localize("UTC"),
            return_frequency="daily_close_to_close",
        )
    with pytest.raises(ValueError, match="matching timezones"):
        calculate_tracking_error(
            strategy_returns.tz_localize("UTC"),
            benchmark_returns.tz_localize("America/New_York"),
            return_frequency="daily_close_to_close",
        )
    with pytest.raises(ValueError, match="daily_close_to_close only"):
        calculate_tracking_error(
            strategy_returns,
            benchmark_returns,
            return_frequency="weekly_close_to_close",
        )


def test_tracking_error_rejects_bad_axes_anchor_and_short_sample() -> None:
    index = pd.date_range("2024-01-01", periods=3, freq="D")
    valid = pd.Series([0.0, 0.01, 0.02], index=index)

    duplicate = valid.copy()
    duplicate.index = pd.DatetimeIndex([index[0], index[0], index[2]])
    with pytest.raises(ValueError, match="duplicate dates"):
        calculate_tracking_error(
            duplicate,
            valid,
            return_frequency="daily_close_to_close",
        )

    with pytest.raises(ValueError, match="sorted"):
        calculate_tracking_error(
            valid.sort_index(ascending=False),
            valid.sort_index(ascending=False),
            return_frequency="daily_close_to_close",
        )

    nonzero_anchor = valid.copy()
    nonzero_anchor.iloc[0] = 0.01
    with pytest.raises(ValueError, match="synthetic zero-return anchor"):
        calculate_tracking_error(
            valid,
            nonzero_anchor,
            return_frequency="daily_close_to_close",
        )

    short_index = index[:2]
    with pytest.raises(ValueError, match="at least 2 measured return periods"):
        calculate_tracking_error(
            pd.Series([0.0, 0.01], index=short_index),
            pd.Series([0.0, 0.00], index=short_index),
            return_frequency="daily_close_to_close",
        )


def test_tracking_error_rejects_wrong_types_empty_and_non_datetime_indexes() -> None:
    index = pd.date_range("2024-01-01", periods=3, freq="D")
    valid = pd.Series([0.0, 0.01, 0.02], index=index)

    with pytest.raises(TypeError, match="strategy_returns must be a pandas Series"):
        calculate_tracking_error(
            [0.0, 0.01, 0.02],
            valid,
            return_frequency="daily_close_to_close",
        )
    with pytest.raises(TypeError, match="DatetimeIndex"):
        calculate_tracking_error(
            pd.Series([0.0, 0.01, 0.02]),
            valid,
            return_frequency="daily_close_to_close",
        )
    with pytest.raises(ValueError, match="must not be empty"):
        calculate_tracking_error(
            pd.Series(dtype=float, index=pd.DatetimeIndex([])),
            pd.Series(dtype=float, index=pd.DatetimeIndex([])),
            return_frequency="daily_close_to_close",
        )


def test_basic_metrics_add_tracking_error_only_with_explicit_benchmark_returns() -> None:
    index = pd.date_range("2024-01-01", periods=3, freq="D")
    returns = pd.Series([0.0, 0.01, 0.02], index=index)
    benchmark_returns = pd.Series([0.0, 0.00, 0.01], index=index)
    equity = (1.0 + returns).cumprod()

    without_benchmark_returns = calculate_basic_metrics(equity, returns)
    with_benchmark_returns = calculate_basic_metrics(
        equity,
        returns,
        benchmark_returns=benchmark_returns,
    )

    assert "tracking_error" not in without_benchmark_returns
    assert with_benchmark_returns["tracking_error"] == pytest.approx(
        np.std([0.01, 0.01], ddof=0) * np.sqrt(252)
    )

    with pytest.raises(ValueError, match="daily_close_to_close only"):
        calculate_basic_metrics(
            equity,
            returns,
            benchmark_returns=benchmark_returns,
            periods_per_year=12,
        )

from pathlib import Path

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal, assert_series_equal

import research.eodhd_factor_diagnostics_dry_run as demo
from research.eodhd_factor_diagnostics_dry_run import (
    EODHDFactorDiagnosticsConfig,
    run_eodhd_factor_diagnostics_dry_run,
)


def _write_ohlcv(
    path: Path,
    symbols: list[str],
    dates: pd.DatetimeIndex,
    *,
    value_multiplier_by_date: dict[pd.Timestamp, float] | None = None,
) -> Path:
    rows = ["date,symbol,open,high,low,close,adjusted_close,volume"]
    for date_index, date in enumerate(dates):
        for symbol_index, symbol in enumerate(symbols):
            multiplier = (
                1.0
                if value_multiplier_by_date is None
                else value_multiplier_by_date.get(date, 1.0)
            )
            base = (
                100 + symbol_index * 7 + date_index * (symbol_index + 1)
            ) * multiplier
            rows.append(
                ",".join(
                    [
                        date.date().isoformat(),
                        symbol,
                        f"{base:.2f}",
                        f"{base + 1:.2f}",
                        f"{base - 1:.2f}",
                        f"{base + 0.5:.2f}",
                        f"{base + 0.5:.2f}",
                        str(1000 + 100 * symbol_index + 10 * date_index),
                    ]
                )
            )
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


def _bounded_config(
    *,
    asset_path: Path,
    benchmark_path: Path,
    output_path: Path,
) -> EODHDFactorDiagnosticsConfig:
    return EODHDFactorDiagnosticsConfig(
        ohlcv_path=asset_path,
        benchmark_path=benchmark_path,
        output_path=output_path,
        alpha_window=1,
        quantiles=2,
        train_start="2024-01-03",
        train_end="2024-01-05",
        validation_start="2024-01-06",
        validation_end="2024-01-08",
        test_start="2024-01-09",
        test_end="2024-01-10",
        feature_warm_up_rows=1,
    )


def test_eodhd_factor_diagnostics_dry_run_writes_private_summary(tmp_path: Path) -> None:
    dates = pd.date_range("2024-01-02", periods=9, freq="D")
    asset_path = _write_ohlcv(tmp_path / "asset_ohlcv.csv", ["AAA", "BBB", "CCC", "DDD"], dates)
    benchmark_path = _write_ohlcv(tmp_path / "benchmark_ohlcv.csv", ["SPY"], dates)
    output_path = tmp_path / "factor_diagnostics.md"

    result = run_eodhd_factor_diagnostics_dry_run(
        EODHDFactorDiagnosticsConfig(
            ohlcv_path=asset_path,
            benchmark_path=benchmark_path,
            output_path=output_path,
            alpha_window=1,
            quantiles=2,
            train_start="2024-01-03",
            train_end="2024-01-05",
            validation_start="2024-01-06",
            validation_end="2024-01-08",
            test_start="2024-01-09",
            test_end="2024-01-10",
            feature_warm_up_rows=1,
        )
    )

    assert output_path.is_file()
    assert result.asset_row_count == 36
    assert result.benchmark_row_count == 9
    assert result.symbol_count == 5
    assert set(result.factor_summary.index) == {"alpha_009", "alpha_012"}
    assert result.factor_summary["valid_observations"].gt(0).all()
    assert set(result.split_summary["split"]) == {"train", "validation", "test"}
    assert result.split_summary["ic_valid_dates"].ge(0).all()
    assert result.split.label_kind == "price_forward_return"
    assert result.split.label_horizon_rows == 1
    assert result.split.label_derivation == (
        "adjusted_close_row_forward_return_v1"
    )
    assert result.forward_returns_by_split["test"].iloc[-1].isna().all()
    assert result.benchmark_forward_returns_by_split["test"].iloc[-1:].isna().all()

    text = output_path.read_text(encoding="utf-8")
    assert "No strategy, backtest, portfolio construction, PnL, Sharpe, drawdown" in text
    assert "alpha_009" in text
    assert "alpha_012" in text
    assert "## Label Contract" in text


def test_eodhd_consumer_is_invariant_to_post_test_asset_and_benchmark_values(
    tmp_path: Path,
) -> None:
    dates = pd.date_range("2024-01-02", periods=12, freq="D")
    symbols = ["AAA", "BBB", "CCC", "DDD"]
    post_test = {
        date: 50.0
        for date in dates
        if date > pd.Timestamp("2024-01-10")
    }
    baseline_assets = _write_ohlcv(tmp_path / "assets_base.csv", symbols, dates)
    changed_assets = _write_ohlcv(
        tmp_path / "assets_changed.csv",
        symbols,
        dates,
        value_multiplier_by_date=post_test,
    )
    baseline_benchmark = _write_ohlcv(
        tmp_path / "benchmark_base.csv",
        ["SPY"],
        dates,
    )
    changed_benchmark = _write_ohlcv(
        tmp_path / "benchmark_changed.csv",
        ["SPY"],
        dates,
        value_multiplier_by_date=post_test,
    )

    baseline = demo.run_eodhd_factor_diagnostics_dry_run(
        _bounded_config(
            asset_path=baseline_assets,
            benchmark_path=baseline_benchmark,
            output_path=tmp_path / "baseline.md",
        )
    )
    asset_changed = demo.run_eodhd_factor_diagnostics_dry_run(
        _bounded_config(
            asset_path=changed_assets,
            benchmark_path=baseline_benchmark,
            output_path=tmp_path / "asset_changed.md",
        )
    )
    benchmark_changed = demo.run_eodhd_factor_diagnostics_dry_run(
        _bounded_config(
            asset_path=baseline_assets,
            benchmark_path=changed_benchmark,
            output_path=tmp_path / "benchmark_changed.md",
        )
    )

    assert_frame_equal(baseline.forward_returns, asset_changed.forward_returns)
    assert_frame_equal(baseline.split_summary, asset_changed.split_summary)
    assert_frame_equal(
        baseline.label_availability,
        asset_changed.label_availability,
    )
    assert_series_equal(
        baseline.benchmark_forward_returns,
        benchmark_changed.benchmark_forward_returns,
    )
    assert_frame_equal(
        baseline.benchmark_label_availability,
        benchmark_changed.benchmark_label_availability,
    )
    assert baseline.split.metadata_as_dict() == (
        asset_changed.split.metadata_as_dict()
    )


def test_eodhd_consumer_is_invariant_across_split_edges(tmp_path: Path) -> None:
    dates = pd.date_range("2024-01-02", periods=12, freq="D")
    symbols = ["AAA", "BBB", "CCC", "DDD"]
    benchmark = _write_ohlcv(tmp_path / "benchmark.csv", ["SPY"], dates)
    baseline_path = _write_ohlcv(tmp_path / "baseline.csv", symbols, dates)
    validation_changed_path = _write_ohlcv(
        tmp_path / "validation_changed.csv",
        symbols,
        dates,
        value_multiplier_by_date={
            date: 20.0
            for date in dates
            if pd.Timestamp("2024-01-06")
            <= date
            <= pd.Timestamp("2024-01-08")
        },
    )
    test_changed_path = _write_ohlcv(
        tmp_path / "test_changed.csv",
        symbols,
        dates,
        value_multiplier_by_date={
            date: 20.0 for date in dates if date >= pd.Timestamp("2024-01-09")
        },
    )
    baseline = demo.run_eodhd_factor_diagnostics_dry_run(
        _bounded_config(
            asset_path=baseline_path,
            benchmark_path=benchmark,
            output_path=tmp_path / "baseline.md",
        )
    )
    validation_changed = demo.run_eodhd_factor_diagnostics_dry_run(
        _bounded_config(
            asset_path=validation_changed_path,
            benchmark_path=benchmark,
            output_path=tmp_path / "validation_changed.md",
        )
    )
    test_changed = demo.run_eodhd_factor_diagnostics_dry_run(
        _bounded_config(
            asset_path=test_changed_path,
            benchmark_path=benchmark,
            output_path=tmp_path / "test_changed.md",
        )
    )

    train_dates = baseline.split.window_metadata["train"].eligible_dates
    validation_dates = baseline.split.window_metadata[
        "validation"
    ].eligible_dates
    assert_frame_equal(
        baseline.forward_returns.loc[train_dates],
        validation_changed.forward_returns.loc[train_dates],
    )
    assert_frame_equal(
        baseline.forward_returns.loc[validation_dates],
        test_changed.forward_returns.loc[validation_dates],
    )
    assert_frame_equal(
        baseline.split_summary.loc[
            baseline.split_summary["split"].eq("train")
        ].reset_index(drop=True),
        validation_changed.split_summary.loc[
            validation_changed.split_summary["split"].eq("train")
        ].reset_index(drop=True),
    )
    assert_frame_equal(
        baseline.split_summary.loc[
            baseline.split_summary["split"].eq("validation")
        ].reset_index(drop=True),
        test_changed.split_summary.loc[
            test_changed.split_summary["split"].eq("validation")
        ].reset_index(drop=True),
    )


def test_eodhd_consumer_retains_zero_eligible_windows_as_invalid(
    tmp_path: Path,
) -> None:
    dates = pd.date_range("2024-01-02", periods=9, freq="D")
    assets = _write_ohlcv(
        tmp_path / "assets.csv",
        ["AAA", "BBB", "CCC", "DDD"],
        dates,
    )
    benchmark = _write_ohlcv(tmp_path / "benchmark.csv", ["SPY"], dates)
    config = EODHDFactorDiagnosticsConfig(
        ohlcv_path=assets,
        benchmark_path=benchmark,
        output_path=tmp_path / "zero_eligible.md",
        alpha_window=1,
        quantiles=2,
        train_start="2024-01-03",
        train_end="2024-01-03",
        validation_start="2024-01-04",
        validation_end="2024-01-04",
        test_start="2024-01-05",
        test_end="2024-01-05",
        feature_warm_up_rows=1,
    )

    result = demo.run_eodhd_factor_diagnostics_dry_run(config)

    assert result.forward_returns.loc[result.split.all_dates].isna().all().all()
    assert set(result.split_summary["invalid_reason"]) == {
        "no_eligible_labels"
    }
    assert set(result.split_summary["status"]) == {"INVALID"}
    assert result.split_summary["ic_valid_dates"].eq(0).all()


def test_eodhd_consumer_audits_partial_and_all_missing_targets(
    tmp_path: Path,
    monkeypatch,
) -> None:
    dates = pd.date_range("2024-01-02", periods=12, freq="D")
    assets = _write_ohlcv(
        tmp_path / "assets.csv",
        ["AAA", "BBB", "CCC", "DDD"],
        dates,
    )
    benchmark = _write_ohlcv(tmp_path / "benchmark.csv", ["SPY"], dates)
    config = _bounded_config(
        asset_path=assets,
        benchmark_path=benchmark,
        output_path=tmp_path / "missing.md",
    )
    original = demo.make_price_forward_return_labels

    def partial_labels(values, split, **kwargs):
        labels = original(values, split, **kwargs)
        if isinstance(labels, pd.DataFrame):
            date = split.window_metadata["train"].eligible_dates[0]
            labels.loc[date, labels.columns[0]] = np.nan
        return labels

    monkeypatch.setattr(
        demo,
        "make_price_forward_return_labels",
        partial_labels,
    )
    partial = demo.run_eodhd_factor_diagnostics_dry_run(config)
    assert partial.split_summary.loc[
        partial.split_summary["split"].eq("train"),
        "missing_eligible_target_cells",
    ].eq(1).all()

    def all_missing_labels(values, split, **kwargs):
        labels = original(values, split, **kwargs)
        if isinstance(labels, pd.DataFrame):
            for metadata in split.window_metadata.values():
                labels.loc[metadata.eligible_dates] = np.nan
        return labels

    monkeypatch.setattr(
        demo,
        "make_price_forward_return_labels",
        all_missing_labels,
    )
    missing = demo.run_eodhd_factor_diagnostics_dry_run(config)
    assert set(missing.split_summary["invalid_reason"]) == {
        "no_usable_label_pairs"
    }
    assert set(missing.split_summary["status"]) == {"INVALID"}

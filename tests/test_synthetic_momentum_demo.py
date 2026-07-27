import json
from pathlib import Path

import pandas as pd

from research.synthetic_momentum_demo import (
    SyntheticDemoConfig,
    generate_synthetic_prices,
    run_synthetic_momentum_demo,
)


def test_synthetic_price_generation_is_reproducible() -> None:
    config = SyntheticDemoConfig(seed=123, asset_count=20, periods=30)

    first = generate_synthetic_prices(config)
    second = generate_synthetic_prices(config)

    pd.testing.assert_frame_equal(first, second)
    assert first.shape == (30, 20)
    assert list(first.columns[:3]) == ["ASSET_01", "ASSET_02", "ASSET_03"]


def test_synthetic_demo_writes_report_with_profitability_warning(tmp_path: Path) -> None:
    report_path = tmp_path / "synthetic_momentum_demo.md"
    config = SyntheticDemoConfig(seed=123, asset_count=20, periods=320, top_n=5)

    result = run_synthetic_momentum_demo(config=config, report_path=report_path)

    report_text = report_path.read_text(encoding="utf-8")
    assert report_path.is_file()
    assert "synthetic data only" in report_text
    assert "not evidence of real-world strategy profitability" in report_text
    assert "| Total return |" in report_text
    assert "| Tracking error vs synthetic benchmark |" in report_text
    assert "exclude_synthetic_anchor" in report_text
    assert "cost_free_price_return" in report_text
    assert "Episode hit rate" in report_text
    assert "continuous_positive_weight_v1" in report_text
    assert result.holdings.shape[1] == 20


def test_synthetic_demo_writes_experiment_log(tmp_path: Path) -> None:
    report_path = tmp_path / "synthetic_momentum_demo.md"
    log_path = tmp_path / "synthetic_momentum_demo.json"
    config = SyntheticDemoConfig(seed=123, asset_count=20, periods=320, top_n=5)

    result = run_synthetic_momentum_demo(
        config=config,
        report_path=report_path,
        experiment_log_path=log_path,
    )

    payload = json.loads(log_path.read_text(encoding="utf-8"))
    assert payload["experiment_id"] == "synthetic-momentum-demo"
    assert payload["experiment_type"] == "synthetic_backtest_smoke_test"
    assert payload["assumptions"]["data_scope"] == "synthetic only"
    assert payload["assumptions"]["data_source"] == "local deterministic generator; no external data fetch"
    assert payload["assumptions"]["benchmark"] == "synthetic equal-weight universe benchmark"
    assert payload["assumptions"]["transaction_cost_model"].startswith(
        "fixed_bps_on_target_weight_turnover"
    )
    assert payload["assumptions"]["transaction_cost_bps"] == 10.0
    assert payload["assumptions"]["slippage_model"].startswith(
        "fixed_bps_on_target_weight_turnover"
    )
    assert payload["assumptions"]["slippage_bps"] == 0.0
    assert payload["assumptions"]["zero_cost_or_slippage_is_diagnostic"] is True
    assert payload["assumptions"]["tracking_error_contract"] == (
        "daily_close_to_close_v1"
    )
    assert payload["assumptions"]["benchmark_cost_basis"] == (
        "cost_free_price_return"
    )
    assert payload["assumptions"]["live_trading"] is False
    assert payload["assumptions"]["brokerage_integration"] is False
    assert payload["metrics"]["total_return"] == result.metrics["total_return"]
    assert payload["metrics"]["tracking_error"] == result.metrics["tracking_error"]
    assert payload["metrics"]["episode_hit_rate"] == result.metrics["episode_hit_rate"]
    assert payload["assumptions"]["holding_episode_contract"] == (
        "continuous_positive_weight_v1"
    )
    assert payload["metrics"]["total_slippage_cost_impact"] == 0.0
    assert payload["metrics"]["total_trading_cost_impact"] == result.metrics[
        "total_trading_cost_impact"
    ]
    assert payload["assumptions"]["timing_metadata"]["timing_contract"] == (
        "after_close_signal_next_observed_close_v1"
    )
    assert payload["assumptions"]["timing_metadata"][
        "backtest_source_provenance_policy"
    ] == "tracked_pre_mutation_source_snapshot_v1"
    assert payload["assumptions"]["timing_metadata"][
        "backtest_source_provenance_status"
    ] == "validated_without_recovery"
    assert payload["assumptions"]["sharpe_risk_free_policy"] == "zero"
    assert payload["assumptions"]["sharpe_measured_row_policy"] == (
        "exclude_initialization_anchor"
    )
    assert payload["assumptions"]["date_range"]["start"] == (
        result.timing_metadata["evaluation_start"].date().isoformat()
    )
    assert len(payload["diagnostics"]["timing_ledger"]) == len(result.timing_ledger)
    assert payload["diagnostics"]["timing_ledger"][0]["event_status"] == (
        "initialization_anchor_no_execution"
    )
    assert "not a profitability claim" in payload["caveats"]
    assert "not evidence of real-world strategy performance" in payload["caveats"]
    serialized = json.dumps(payload, sort_keys=True)
    for private_field in [
        "axis_fingerprint",
        "original_cells",
        "original_dtype_names",
        "original_state_digest",
        "current_state_digest",
        "mutations",
        "record_digest",
        "_source_identity",
        "_lineage_token",
    ]:
        assert f'"{private_field}"' not in serialized

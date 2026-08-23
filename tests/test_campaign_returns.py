"""Execution-anchored simple-return golden and invalid-anchor matrix."""

from __future__ import annotations

import inspect
import math

from campaign.returns import simple_adjusted_close_return
from campaign.schedule import build_campaign_schedule
from campaign_runner_v1_support import decode_fixture_anchor, load_runner_fixture


def test_execution_anchored_label_is_simple_not_log() -> None:
    fixture = load_runner_fixture("execution_anchored_label.json")
    inputs = fixture["inputs"]
    built = build_campaign_schedule(
        inputs["session_dates"],
        inputs["accepted_cutoff"],
        inputs["horizon_return_rows"],
        inputs["horizon_purge_signal_axis_rows"],
        inputs["embargo_rows"],
        inputs["first_fold_year"],
    )
    signal = next(
        row
        for row in built.signals
        if row.signal_date == inputs["signal_date"]
    )
    result = simple_adjusted_close_return(
        inputs["start_anchor"],
        inputs["end_anchor"],
        inputs["anchors"],
        inputs["target_identity"],
        inputs["alias_chain"],
    )
    expected = fixture["expected"]
    assert result.valid is expected["valid"]
    assert result.reason is expected["reason"]
    assert result.value is not None
    assert math.isclose(
        result.value,
        expected["value"],
        rel_tol=expected["rel_tol"],
        abs_tol=expected["abs_tol"],
    )
    assert signal.label_start_date == expected["label_start_date"]
    assert signal.label_end_date == expected["label_end_date"]
    assert (
        signal.execution_index - signal.signal_index
        == expected["label_start_offset"]
    )
    assert (
        signal.label_end_index - signal.signal_index
        == expected["label_end_offset"]
    )
    assert result.value != fixture["forbidden"]["log_return"]
    assert not math.isclose(
        result.value,
        fixture["forbidden"]["log_return"],
        rel_tol=expected["rel_tol"],
        abs_tol=expected["abs_tol"],
    )


def test_execution_anchored_anchors_fail_closed() -> None:
    fixture = load_runner_fixture("execution_anchored_label.json")
    inputs = fixture["inputs"]
    for kind in inputs["invalid_kinds"]:
        mutated = decode_fixture_anchor(kind)
        start_invalid = simple_adjusted_close_return(
            mutated,
            inputs["end_anchor"],
            inputs["anchors"],
            inputs["target_identity"],
            inputs["alias_chain"],
        )
        end_invalid = simple_adjusted_close_return(
            inputs["start_anchor"],
            mutated,
            inputs["anchors"],
            inputs["target_identity"],
            inputs["alias_chain"],
        )
        assert start_invalid.valid is False
        assert start_invalid.value is None
        assert start_invalid.reason == kind["reason"]
        assert end_invalid.valid is False
        assert end_invalid.value is None
        assert end_invalid.reason == kind["reason"]


def test_mismatched_anchor_prices_are_invalid() -> None:
    fixture = load_runner_fixture("anchor_price_mismatch.json")
    inputs = fixture["inputs"]
    expected = fixture["expected"]
    matched = simple_adjusted_close_return(
        inputs["start_anchor"],
        inputs["end_anchor"],
        inputs["anchors"],
        inputs["target_identity"],
        inputs["alias_chain"],
    )
    assert matched.valid is expected["matched_valid"]
    assert matched.value is not None
    assert math.isclose(
        matched.value,
        expected["matched_value"],
        rel_tol=expected["rel_tol"],
        abs_tol=expected["abs_tol"],
    )
    start_mismatch = simple_adjusted_close_return(
        inputs["mismatched_start_anchor"],
        inputs["end_anchor"],
        inputs["anchors"],
        inputs["target_identity"],
        inputs["alias_chain"],
    )
    end_mismatch = simple_adjusted_close_return(
        inputs["start_anchor"],
        inputs["mismatched_end_anchor"],
        inputs["anchors"],
        inputs["target_identity"],
        inputs["alias_chain"],
    )
    assert start_mismatch.valid is expected["valid"]
    assert start_mismatch.value is expected["value"]
    assert start_mismatch.reason == expected["reason"]
    assert end_mismatch.valid is expected["valid"]
    assert end_mismatch.value is expected["value"]
    assert end_mismatch.reason == expected["reason"]
    assert fixture["forbidden"]["compute_from_independent_scalars"]


def test_simple_return_gate_has_no_fill_parameter() -> None:
    names = inspect.signature(simple_adjusted_close_return).parameters
    assert "fill" not in names

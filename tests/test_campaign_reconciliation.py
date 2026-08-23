"""Fourteen-trial completeness, invalid retention, and diagnostic routing."""

from __future__ import annotations

import inspect
import json

from campaign.reconciliation import (
    parse_trial_inventory,
    reconcile_semantic_trials,
    required_output_names,
)
from campaign_runner_v1_support import fixture_file, load_runner_fixture


def _inventory(name: str):
    return parse_trial_inventory(fixture_file(name).read_bytes())


def _prepared(name: str) -> dict[str, object]:
    return json.loads(fixture_file(name).read_text(encoding="utf-8"))


def test_complete_inventory_reconciles_fourteen_trials() -> None:
    fixture = load_runner_fixture("reconciliation_complete.json")
    prepared = _prepared(fixture["inputs"]["prepared_file"])
    result = reconcile_semantic_trials(
        _inventory(fixture["inputs"]["inventory_file"]),
        prepared["trial_outputs"],
        prepared["diagnostic_payload"],
    )
    expected = fixture["expected"]
    assert result.complete is expected["complete"]
    assert result.trial_count == expected["trial_count"]
    assert result.invalid_and_missing["missing_required_outputs"] == expected[
        "missing_required_outputs"
    ]
    assert result.invalid_and_missing["invalid_required_outputs"] == expected[
        "invalid_required_outputs"
    ]
    assert result.final_state == expected["final_state"]
    assert len(result.trials) == expected["trial_count"]


def test_missing_required_output_is_incomplete() -> None:
    fixture = load_runner_fixture("reconciliation_missing_output.json")
    prepared = _prepared(fixture["inputs"]["prepared_file"])
    outputs = prepared["trial_outputs"]
    del outputs[fixture["inputs"]["missing_trial_id"]][fixture["inputs"]["missing_name"]]
    result = reconcile_semantic_trials(
        _inventory(fixture["inputs"]["inventory_file"]),
        outputs,
        prepared["diagnostic_payload"],
    )
    expected = fixture["expected"]
    assert result.complete is expected["complete"]
    assert result.reason == expected["reason"]
    assert result.invalid_and_missing["missing_required_outputs"] == expected[
        "missing_required_outputs"
    ]
    assert result.final_state is expected["final_state"]


def test_invalid_required_output_is_retained_not_missing() -> None:
    fixture = load_runner_fixture("reconciliation_invalid_output.json")
    prepared = _prepared(fixture["inputs"]["prepared_file"])
    outputs = prepared["trial_outputs"]
    outputs[fixture["inputs"]["invalid_trial_id"]][fixture["inputs"]["invalid_name"]] = {
        "present": True,
        "valid": False,
        "reason": fixture["inputs"]["invalid_reason"],
    }
    result = reconcile_semantic_trials(
        _inventory(fixture["inputs"]["inventory_file"]),
        outputs,
        prepared["diagnostic_payload"],
    )
    expected = fixture["expected"]
    assert result.complete is expected["complete"]
    assert result.invalid_and_missing["missing_required_outputs"] == expected[
        "missing_required_outputs"
    ]
    assert result.invalid_and_missing["invalid_required_outputs"] == expected[
        "invalid_required_outputs"
    ]
    assert result.final_state == expected["final_state"]
    trial = next(
        item
        for item in result.trials
        if item.trial_id == fixture["inputs"]["invalid_trial_id"]
    )
    assert fixture["inputs"]["invalid_name"] in trial.invalid_names
    assert trial.outputs[fixture["inputs"]["invalid_name"]].present
    assert not trial.outputs[fixture["inputs"]["invalid_name"]].valid


def test_invalid_primary_comparison_routes_hard_validity() -> None:
    fixture = load_runner_fixture("reconciliation_invalid_primary.json")
    prepared = _prepared(fixture["inputs"]["prepared_file"])
    payload = prepared["diagnostic_payload"]
    payload["invalid_primary_comparison_count"] = fixture["inputs"][
        "invalid_primary_comparison_count"
    ]
    payload["primary_matched_benchmark_comparisons_valid"] = fixture["inputs"][
        "primary_matched_benchmark_comparisons_valid"
    ]
    result = reconcile_semantic_trials(
        _inventory(fixture["inputs"]["inventory_file"]),
        prepared["trial_outputs"],
        payload,
    )
    expected = fixture["expected"]
    assert result.complete is expected["complete"]
    assert result.final_state == expected["final_state"]
    assert result.diagnostic_inputs is not None
    assert result.diagnostic_inputs.hard_valid is expected["hard_valid"]
    assert result.diagnostic_inputs.prefrozen_coverage_met


def test_required_output_names_follow_inventory() -> None:
    fixture = load_runner_fixture("reconciliation_complete.json")
    inventory = _inventory(fixture["inputs"]["inventory_file"])
    prepared = _prepared(fixture["inputs"]["prepared_file"])
    for trial in inventory:
        names = required_output_names(trial)
        assert set(names) == set(prepared["trial_outputs"][trial["trial_id"]])


def test_reconciliation_functions_have_no_defaults() -> None:
    for function in (
        parse_trial_inventory,
        required_output_names,
        reconcile_semantic_trials,
    ):
        for parameter in inspect.signature(function).parameters.values():
            assert parameter.default is inspect.Parameter.empty

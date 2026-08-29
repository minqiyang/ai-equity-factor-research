"""Authorized runner orchestration and byte-identical repeat runs."""

from __future__ import annotations

import dataclasses
import inspect
import json
from pathlib import Path

from campaign.precondition import authorize, result_bearing_refusal_reason
from campaign.runner import (
    CampaignRun,
    RunConfig,
    configuration_projection,
    run_campaign,
)
from pit_manifest_validator_v1.canonical import sha256_hex
from campaign_runner_v1_support import (
    fixture_file,
    load_runner_fixture,
    make_run_config,
)


def _authorized_config(**overrides: object) -> RunConfig:
    golden = load_runner_fixture("acceptance_record_identity_golden.json")
    protocol = load_runner_fixture("run_config_protocol.json")["inputs"]
    expected = golden["expected"]
    inputs = golden["inputs"]
    locators = {
        "acceptance_record_file": str(fixture_file(inputs["record_file"])),
        "stage2_grant_file": str(fixture_file(inputs["grant_file"])),
        "protocol_file": str(fixture_file(inputs["protocol_file"])),
        "trial_inventory_file": str(fixture_file(inputs["inventory_file"])),
        "detached_binding_file": str(fixture_file(inputs["binding_file"])),
        "prepared_campaign_file": str(fixture_file(inputs["prepared_file"])),
    }
    digests = {
        "acceptance_record_file_sha256": expected["file_bytes"],
        "acceptance_identity_sha256": expected["canonical_identity"],
        "decision_file_sha256": expected["decision_file_sha256"],
        "decision_identity_sha256": expected["decision_identity_sha256"],
        "stage2_grant_file_sha256": expected["grant_file_bytes"],
        "protocol_file_sha256": expected["protocol_file_bytes"],
        "trial_inventory_file_sha256": expected["inventory_file_bytes"],
        "prepared_campaign_file_sha256": expected["prepared_file_bytes"],
    }
    return make_run_config(locators, digests, protocol, **overrides)


def test_run_campaign_refuses_without_bundle_when_unauthorized() -> None:
    fixture = load_runner_fixture("acceptance_record_role_swap.json")
    result = run_campaign(
        _authorized_config(
            acceptance_identity_sha256=fixture["expected"]["file_bytes"]
        )
    )
    assert isinstance(result, CampaignRun)
    assert result.status == "REFUSED"
    assert result.reason == fixture["expected"]["reason"]
    assert result.bundle is None
    assert result.reconciliation is None
    assert result.run_record is None


def test_run_campaign_planning_grant_refuses_result_bearing() -> None:
    fixture = load_runner_fixture("grant_result_bearing_refusal.json")
    expected = fixture["expected"]
    result = run_campaign(_authorized_config())
    assert isinstance(result, CampaignRun)
    assert result.status == expected["status"]
    assert result.reason == expected["reason"]
    assert result.authorization.status == expected["authorization_status"]
    assert result.bundle is None
    assert result.reconciliation is None
    assert result.run_record is None
    assert fixture["forbidden"]["emit_result_bearing_bundle"]


def test_two_runs_over_same_inputs_are_identical() -> None:
    fixture = load_runner_fixture("grant_result_bearing_refusal.json")
    first = run_campaign(_authorized_config())
    second = run_campaign(_authorized_config())
    assert first.status == fixture["expected"]["status"]
    assert second.status == fixture["expected"]["status"]
    assert first.reason == second.reason
    assert first.bundle is None
    assert second.bundle is None
    assert first.authorization.status == second.authorization.status
    assert first.run_record == second.run_record


def test_run_campaign_ignores_unbound_prepared_file(tmp_path: Path) -> None:
    fixture = load_runner_fixture("prepared_file_unbound_mutation.json")
    prepared = json.loads(
        fixture_file(fixture["inputs"]["prepared_file"]).read_text(encoding="utf-8")
    )
    cursor = prepared
    path = fixture["inputs"]["mutation"]["path"]
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = fixture["inputs"]["mutation"]["value"]
    target = tmp_path / "mutated_prepared.json"
    target.write_text(json.dumps(prepared), encoding="utf-8")
    original = run_campaign(_authorized_config())
    mutated = run_campaign(_authorized_config(prepared_campaign_file=str(target)))
    expected = fixture["expected"]
    assert original.status == expected["status"]
    assert mutated.status == expected["status"]
    assert original.reason == expected["reason"]
    assert mutated.reason == expected["reason"]
    assert original.bundle is None
    assert mutated.bundle is None
    assert fixture["forbidden"]["trust_unbound_prepared_file"]


def test_run_campaign_missing_output_does_not_emit_valid_null_bundle(
    tmp_path: Path,
) -> None:
    fixture = load_runner_fixture("reconciliation_missing_output.json")
    prepared = json.loads(
        fixture_file(fixture["inputs"]["prepared_file"]).read_text(encoding="utf-8")
    )
    del prepared["trial_outputs"][fixture["inputs"]["missing_trial_id"]][
        fixture["inputs"]["missing_name"]
    ]
    target = tmp_path / "missing_output.json"
    target.write_text(json.dumps(prepared), encoding="utf-8")
    result = run_campaign(_authorized_config(prepared_campaign_file=str(target)))
    expected = fixture["expected"]
    assert result.status == expected["run_campaign_status"]
    assert result.reason == expected["run_campaign_reason"]
    assert result.bundle is None
    assert result.run_record is None
    assert result.reconciliation is None


def test_configuration_projection_labels_digest_roles() -> None:
    config = _authorized_config()
    projection = configuration_projection(config)
    roles = projection["roles"]
    assert roles["acceptance_record_file_sha256"] == "FILE_BYTES"
    assert roles["acceptance_identity_sha256"] == "CANONICAL_IDENTITY"
    assert roles["prepared_campaign_file_sha256"] == "FILE_BYTES"
    assert (
        projection["acceptance_record_file_sha256"]
        == config.acceptance_record_file_sha256
    )
    assert projection["acceptance_identity_sha256"] == config.acceptance_identity_sha256
    assert (
        projection["prepared_campaign_file_sha256"]
        == config.prepared_campaign_file_sha256
    )


def test_run_config_fields_have_no_defaults() -> None:
    for field in dataclasses.fields(RunConfig):
        assert field.default is dataclasses.MISSING
        assert field.default_factory is dataclasses.MISSING


def test_runner_functions_have_no_defaults() -> None:
    for function in (configuration_projection, run_campaign):
        for parameter in inspect.signature(function).parameters.values():
            assert parameter.default is inspect.Parameter.empty


def _config_with_grant(grant_file: str, **overrides: object) -> RunConfig:
    grant_path = fixture_file(grant_file)
    return _authorized_config(
        stage2_grant_file=str(grant_path),
        stage2_grant_file_sha256=sha256_hex(grant_path.read_bytes()),
        **overrides,
    )


def test_exact_grant_v2_lists_reach_diagnostic_execution() -> None:
    fixture = load_runner_fixture("grant_run_execution.json")
    expected = fixture["expected"]
    inputs = fixture["inputs"]
    locators = (
        fixture_file(inputs["grant_file"]),
        fixture_file(inputs["prepared_file"]),
        fixture_file("precondition/acceptance_valid.json"),
        fixture_file("precondition/binding_valid.json"),
        fixture_file("precondition/protocol.yaml"),
        fixture_file("precondition/trial_inventory.json"),
    )
    before = {path: sha256_hex(path.read_bytes()) for path in locators}
    config = _config_with_grant(inputs["grant_file"])
    grant = json.loads(fixture_file(inputs["grant_file"]).read_text(encoding="utf-8"))
    assert grant["now_eligible"] == expected["now_eligible"]
    assert grant["does_not_authorize"] == expected["does_not_authorize"]
    assert result_bearing_refusal_reason(grant) == expected["refusal_reason"]
    authorization = authorize(config)
    assert authorization.status == expected["authorization_status"]
    assert authorization.reason == expected["authorization_reason"]
    result = run_campaign(config)
    assert isinstance(result, CampaignRun)
    assert result.status == expected["status"]
    assert result.reason is None
    assert result.reconciliation is not None
    assert result.bundle is not None
    assert result.run_record is not None
    assert list(result.run_record) == expected["run_record_keys"]
    assert result.run_record["evidence_ceiling"] == expected["evidence_ceiling"]
    assert result.run_record["trials_executed"] == expected["trials_executed"]
    assert result.run_record["trial_ids"] == expected["trial_ids"]
    after = {path: sha256_hex(path.read_bytes()) for path in locators}
    assert before == after
    assert fixture["forbidden"]["filesystem_write"]
    assert fixture["forbidden"]["result_access_executable"]
    assert fixture["forbidden"]["performance_access_executable"]


def test_run_campaign_refuses_sentinel_and_prepared_byte_mismatch(
    tmp_path: Path,
) -> None:
    fixture = load_runner_fixture("grant_run_execution.json")
    expected = fixture["expected"]
    inputs = fixture["inputs"]
    sentinel = fixture_file(inputs["sentinel_file"])
    binding = json.loads(
        fixture_file("precondition/binding_valid.json").read_text(encoding="utf-8")
    )
    binding["prepared_campaign_file_sha256"] = sha256_hex(sentinel.read_bytes())
    binding_path = tmp_path / "sentinel_binding.json"
    binding_path.write_text(json.dumps(binding), encoding="utf-8")
    sentinel_run = run_campaign(
        _config_with_grant(
            inputs["grant_file"],
            prepared_campaign_file=str(sentinel),
            prepared_campaign_file_sha256=sha256_hex(sentinel.read_bytes()),
            detached_binding_file=str(binding_path),
        )
    )
    assert sentinel_run.status == "REFUSED"
    assert sentinel_run.reason == expected["sentinel_reason"]
    mutated = json.loads(
        fixture_file(inputs["prepared_file"]).read_text(encoding="utf-8")
    )
    mutated["attempt_count"] = expected["trials_executed"]
    mutated_path = tmp_path / "mutated_prepared.json"
    mutated_path.write_text(json.dumps(mutated), encoding="utf-8")
    mismatched = run_campaign(
        _config_with_grant(
            inputs["grant_file"],
            prepared_campaign_file=str(mutated_path),
        )
    )
    assert mismatched.status == "REFUSED"
    assert mismatched.reason == expected["prepared_bytes_reason"]

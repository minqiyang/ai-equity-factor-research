"""Authorized runner orchestration and byte-identical repeat runs."""

from __future__ import annotations

import dataclasses
from datetime import date, timedelta
import inspect
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from campaign.bundle import invalid_and_missing_bytes, required_bundle_children
from campaign.precondition import authorize, result_bearing_refusal_reason
from campaign.runner import (
    CampaignRun,
    RunConfig,
    attempt_ledger_path,
    campaign_identity,
    configuration_projection,
    run_campaign,
)
from pit_manifest_validator_v1.canonical import sha256_hex
from campaign_runner_v1_support import (
    encode_runner_listing_key,
    fixture_file,
    fixture_ticker,
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
        "attempt_state_file": str(fixture_file(inputs["attempt_state_file"])),
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
        "owner_authorization_file_sha256": expected[
            "owner_authorization_file_sha256"
        ],
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
        fixture_file("precondition/prepared_campaign.json").read_text(encoding="utf-8")
    )
    prepared["prices"] = {}
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
    assert roles["owner_authorization_file_sha256"] == "FILE_BYTES"
    assert (
        projection["acceptance_record_file_sha256"]
        == config.acceptance_record_file_sha256
    )
    assert projection["acceptance_identity_sha256"] == config.acceptance_identity_sha256
    assert (
        projection["prepared_campaign_file_sha256"]
        == config.prepared_campaign_file_sha256
    )
    assert (
        projection["owner_authorization_file_sha256"]
        == config.owner_authorization_file_sha256
    )


def test_run_config_fields_have_no_defaults() -> None:
    for field in dataclasses.fields(RunConfig):
        assert field.default is dataclasses.MISSING
        assert field.default_factory is dataclasses.MISSING


def test_runner_functions_have_no_defaults() -> None:
    for function in (configuration_projection, run_campaign):
        for parameter in inspect.signature(function).parameters.values():
            assert parameter.default is inspect.Parameter.empty


def _write_binding(
    tmp_path: Path,
    name: str,
    prepared_digest: str | None = None,
) -> str:
    binding = json.loads(
        fixture_file("precondition/binding_valid.json").read_text(encoding="utf-8")
    )
    if prepared_digest is not None:
        binding["prepared_campaign_file_sha256"] = prepared_digest
    path = tmp_path / name
    path.write_text(json.dumps(binding), encoding="utf-8")
    return str(path)


def _config_with_grant(
    grant_file: str,
    tmp_path: Path,
    **overrides: object,
) -> RunConfig:
    del tmp_path
    grant_path = fixture_file(grant_file)
    payload = {
        "stage2_grant_file": str(grant_path),
        "stage2_grant_file_sha256": sha256_hex(grant_path.read_bytes()),
    }
    payload.update(overrides)
    return _authorized_config(**payload)


def _copy_attempt_state(
    tmp_path: Path,
    identity: str,
    name: str,
) -> str:
    payload = json.loads(
        fixture_file("precondition/attempt_state.json").read_text(encoding="utf-8")
    )
    payload["campaign_identity_sha256"] = identity
    target = tmp_path / name
    target.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return str(target)


def _seed_identity_ledger(identity: str) -> str:
    payload = json.loads(
        fixture_file("precondition/attempt_state.json").read_text(encoding="utf-8")
    )
    payload["campaign_identity_sha256"] = identity
    target = attempt_ledger_path(identity)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return str(target)


def _run_config_payload(config: RunConfig) -> dict[str, object]:
    payload = dataclasses.asdict(config)
    payload["cost_bps"] = list(config.cost_bps)
    return payload


def _binding_identity(path: str) -> str:
    return campaign_identity(
        json.loads(Path(path).read_text(encoding="utf-8"))
    )


def test_exact_grant_v2_lists_reach_diagnostic_execution(
    tmp_path: Path,
) -> None:
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
    prepared = json.loads(
        fixture_file(inputs["prepared_file"]).read_text(encoding="utf-8")
    )
    prepared_path = tmp_path / "conflicting_prepared.json"
    prepared_path.write_text(json.dumps(prepared), encoding="utf-8")
    prepared_digest = sha256_hex(prepared_path.read_bytes())
    binding_path = _write_binding(
        tmp_path, "authorized_binding.json", prepared_digest
    )
    identity = _binding_identity(binding_path)
    _seed_identity_ledger(identity)
    config = _config_with_grant(
        inputs["grant_file"],
        tmp_path,
        prepared_campaign_file=str(prepared_path),
        prepared_campaign_file_sha256=prepared_digest,
        detached_binding_file=binding_path,
        attempt_state_file=_copy_attempt_state(
            tmp_path, identity, "attempt_state.json"
        ),
    )
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
    assert expected["reconciled_claim_key"] not in result.run_record
    assert result.run_record["evidence_ceiling"] == expected["evidence_ceiling"]
    assert result.run_record["trials_executed"] == expected["trials_executed"]
    assert result.run_record["trial_ids"] == expected["trial_ids"]
    assert result.reconciliation.trial_count == expected["trials_executed"]
    assert result.bundle.detached_root is not None
    assert (
        result.bundle.detached_root["attempt_count"]
        == expected["ledger_attempt_count"]
    )
    for name in expected["runner_owned_children"]:
        assert name in result.bundle.child_digests
    invalid_name = expected["invalid_child"]
    assert result.bundle.child_digests[invalid_name] == sha256_hex(
        invalid_and_missing_bytes(result.reconciliation)
    )
    replay = run_campaign(config)
    assert replay.status == "REFUSED"
    assert replay.reason == expected["attempt_consumed_reason"]
    alternate = run_campaign(
        _config_with_grant(
            inputs["grant_file"],
            tmp_path,
            prepared_campaign_file=str(prepared_path),
            prepared_campaign_file_sha256=prepared_digest,
            detached_binding_file=binding_path,
            attempt_state_file=_copy_attempt_state(
                tmp_path, identity, "attempt_alt.json"
            ),
        )
    )
    assert alternate.status == "REFUSED"
    assert alternate.reason == expected["alternate_locator_reason"]
    mutated_grant = json.loads(
        fixture_file(inputs["grant_file"]).read_text(encoding="utf-8")
    )
    mutated_grant["artifact_id"] = inputs["mutated_artifact_id"]
    mutated_path = tmp_path / "mutated_grant.json"
    mutated_path.write_text(json.dumps(mutated_grant), encoding="utf-8")
    mutated_run = run_campaign(
        _config_with_grant(
            inputs["grant_file"],
            tmp_path,
            stage2_grant_file=str(mutated_path),
            stage2_grant_file_sha256=sha256_hex(mutated_path.read_bytes()),
            prepared_campaign_file=str(prepared_path),
            prepared_campaign_file_sha256=prepared_digest,
            detached_binding_file=binding_path,
            attempt_state_file=_copy_attempt_state(
                tmp_path, identity, "attempt_mutated.json"
            ),
        )
    )
    assert mutated_run.status == "REFUSED"
    assert mutated_run.reason == expected["mutated_grant_reason"]
    after = {path: sha256_hex(path.read_bytes()) for path in locators}
    assert before == after
    assert fixture["forbidden"]["campaign_artifact_write"]
    assert fixture["forbidden"]["result_access_executable"]
    assert fixture["forbidden"]["performance_access_executable"]
    assert fixture["forbidden"]["reconcile_precomputed_payload"]


def test_run_campaign_refuses_sentinel_and_prepared_byte_mismatch(
    tmp_path: Path,
) -> None:
    fixture = load_runner_fixture("grant_run_execution.json")
    expected = fixture["expected"]
    inputs = fixture["inputs"]
    sentinel = fixture_file(inputs["sentinel_file"])
    sentinel_digest = sha256_hex(sentinel.read_bytes())
    sentinel_run = run_campaign(
        _config_with_grant(
            inputs["grant_file"],
            tmp_path,
            prepared_campaign_file=str(sentinel),
            prepared_campaign_file_sha256=sentinel_digest,
            detached_binding_file=_write_binding(
                tmp_path,
                "sentinel_binding.json",
                sentinel_digest,
            ),
        )
    )
    assert sentinel_run.status == "REFUSED"
    assert sentinel_run.reason == expected["sentinel_reason"]
    mutated = json.loads(
        fixture_file(inputs["prepared_file"]).read_text(encoding="utf-8")
    )
    mutated["prices"] = {}
    mutated_path = tmp_path / "mutated_prepared.json"
    mutated_path.write_text(json.dumps(mutated), encoding="utf-8")
    mismatched = run_campaign(
        _config_with_grant(
            inputs["grant_file"],
            tmp_path,
            prepared_campaign_file=str(mutated_path),
        )
    )
    assert mismatched.status == "REFUSED"
    assert mismatched.reason == expected["prepared_bytes_reason"]


def test_forged_owner_authorization_digest_is_refused(tmp_path: Path) -> None:
    fixture = load_runner_fixture("grant_run_execution.json")
    expected = fixture["expected"]
    grant = json.loads(
        fixture_file(fixture["inputs"]["grant_file"]).read_text(encoding="utf-8")
    )
    grant["fourteen_trial_run_authorization"]["owner_authorization_file_sha256"] = (
        expected["wrong_owner_digest"]
    )
    grant_path = tmp_path / "forged_grant.json"
    grant_path.write_text(json.dumps(grant), encoding="utf-8")
    result = authorize(
        _authorized_config(
            stage2_grant_file=str(grant_path),
            stage2_grant_file_sha256=sha256_hex(grant_path.read_bytes()),
        )
    )
    assert result.status == "REFUSED"
    assert result.reason == expected["owner_mismatch_reason"]


def test_malformed_prepared_campaign_is_named_refusal(tmp_path: Path) -> None:
    fixture = load_runner_fixture("grant_run_execution.json")
    expected = fixture["expected"]
    inputs = fixture["inputs"]
    malformed_path = tmp_path / "malformed.json"
    malformed_path.write_bytes(inputs["malformed_prepared"].encode("utf-8"))
    malformed_digest = sha256_hex(malformed_path.read_bytes())
    malformed_binding = _write_binding(
        tmp_path, "binding_malformed.json", malformed_digest
    )
    malformed = run_campaign(
        _config_with_grant(
            inputs["grant_file"],
            tmp_path,
            prepared_campaign_file=str(malformed_path),
            prepared_campaign_file_sha256=malformed_digest,
            detached_binding_file=malformed_binding,
            attempt_state_file=_copy_attempt_state(
                tmp_path,
                _binding_identity(malformed_binding),
                "attempt_malformed.json",
            ),
        )
    )
    assert malformed.status == "REFUSED"
    assert malformed.reason == expected["malformed_reason"]
    missing_path = tmp_path / "missing.json"
    missing_path.write_text(json.dumps(inputs["missing_key_prepared"]), encoding="utf-8")
    missing_digest = sha256_hex(missing_path.read_bytes())
    missing_binding = _write_binding(
        tmp_path, "binding_missing.json", missing_digest
    )
    missing = run_campaign(
        _config_with_grant(
            inputs["grant_file"],
            tmp_path,
            prepared_campaign_file=str(missing_path),
            prepared_campaign_file_sha256=missing_digest,
            detached_binding_file=missing_binding,
            attempt_state_file=_copy_attempt_state(
                tmp_path,
                _binding_identity(missing_binding),
                "attempt_missing.json",
            ),
        )
    )
    assert missing.status == "REFUSED"
    assert missing.reason == expected["schema_reason"]
    wrong_path = tmp_path / "wrong_type.json"
    wrong_path.write_text(json.dumps(inputs["wrong_type_prepared"]), encoding="utf-8")
    wrong_digest = sha256_hex(wrong_path.read_bytes())
    wrong_binding = _write_binding(tmp_path, "binding_wrong.json", wrong_digest)
    wrong = run_campaign(
        _config_with_grant(
            inputs["grant_file"],
            tmp_path,
            prepared_campaign_file=str(wrong_path),
            prepared_campaign_file_sha256=wrong_digest,
            detached_binding_file=wrong_binding,
            attempt_state_file=_copy_attempt_state(
                tmp_path,
                _binding_identity(wrong_binding),
                "attempt_wrong.json",
            ),
        )
    )
    assert wrong.status == "REFUSED"
    assert wrong.reason == expected["schema_reason"]
    nested = json.loads(
        fixture_file(inputs["prepared_file"]).read_text(encoding="utf-8")
    )
    nested["listings"][inputs["nested_wrong_signal_date"]] = ["not-a-listing"]
    nested_path = tmp_path / "nested.json"
    nested_path.write_text(json.dumps(nested), encoding="utf-8")
    nested_digest = sha256_hex(nested_path.read_bytes())
    nested_binding = _write_binding(tmp_path, "binding_nested.json", nested_digest)
    nested_identity = _binding_identity(nested_binding)
    nested_state = _copy_attempt_state(
        tmp_path, nested_identity, "attempt_nested.json"
    )
    nested_ledger = _seed_identity_ledger(nested_identity)
    nested_run = run_campaign(
        _config_with_grant(
            inputs["grant_file"],
            tmp_path,
            prepared_campaign_file=str(nested_path),
            prepared_campaign_file_sha256=nested_digest,
            detached_binding_file=nested_binding,
            attempt_state_file=nested_state,
        )
    )
    assert nested_run.status == "REFUSED"
    assert nested_run.reason == expected["schema_reason"]
    leftover = json.loads(Path(nested_ledger).read_text(encoding="utf-8"))
    assert leftover["consumed"] is False


def test_negative_ledger_execution_count_is_refused(tmp_path: Path) -> None:
    fixture = load_runner_fixture("grant_run_execution.json")
    expected = fixture["expected"]
    inputs = fixture["inputs"]
    binding_path = str(fixture_file("precondition/binding_valid.json"))
    identity = _binding_identity(binding_path)
    state = _copy_attempt_state(tmp_path, identity, "attempt_negative.json")
    ledger = _seed_identity_ledger(identity)
    payload = json.loads(Path(ledger).read_text(encoding="utf-8"))
    payload["execution_count"] = inputs["negative_execution_count"]
    Path(ledger).write_text(json.dumps(payload), encoding="utf-8")
    result = run_campaign(
        _config_with_grant(
            inputs["grant_file"],
            tmp_path,
            attempt_state_file=state,
        )
    )
    assert result.status == "REFUSED"
    assert result.reason == expected["negative_count_reason"]
    leftover = json.loads(Path(ledger).read_text(encoding="utf-8"))
    assert leftover["consumed"] is False
    assert leftover["execution_count"] == inputs["negative_execution_count"]


def test_two_process_replay_consumes_the_identity_ledger(
    tmp_path: Path,
) -> None:
    fixture = load_runner_fixture("grant_run_execution.json")
    expected = fixture["expected"]
    inputs = fixture["inputs"]
    prepared = json.loads(
        fixture_file(inputs["prepared_file"]).read_text(encoding="utf-8")
    )
    prepared_path = tmp_path / "two_process_prepared.json"
    prepared_path.write_text(json.dumps(prepared), encoding="utf-8")
    prepared_digest = sha256_hex(prepared_path.read_bytes())
    binding_path = _write_binding(
        tmp_path, "two_process_binding.json", prepared_digest
    )
    identity = _binding_identity(binding_path)
    _seed_identity_ledger(identity)
    first_config = _config_with_grant(
        inputs["grant_file"],
        tmp_path,
        prepared_campaign_file=str(prepared_path),
        prepared_campaign_file_sha256=prepared_digest,
        detached_binding_file=binding_path,
        attempt_state_file=_copy_attempt_state(
            tmp_path, identity, "attempt_process_one.json"
        ),
    )
    first_payload = tmp_path / "first_config.json"
    first_payload.write_text(
        json.dumps(_run_config_payload(first_config)), encoding="utf-8"
    )
    worker = Path(__file__).resolve().parent / expected["two_process_worker"]
    first = subprocess.run(
        [sys.executable, str(worker), str(first_payload)],
        check=True,
        capture_output=True,
        text=True,
    )
    first_result = json.loads(first.stdout)
    assert first_result["status"] == expected["status"]
    assert first_result["reason"] is None
    second_config = _config_with_grant(
        inputs["grant_file"],
        tmp_path,
        prepared_campaign_file=str(prepared_path),
        prepared_campaign_file_sha256=prepared_digest,
        detached_binding_file=binding_path,
        attempt_state_file=_copy_attempt_state(
            tmp_path, identity, "attempt_process_two.json"
        ),
    )
    second_payload = tmp_path / "second_config.json"
    second_payload.write_text(
        json.dumps(_run_config_payload(second_config)), encoding="utf-8"
    )
    second = subprocess.run(
        [sys.executable, str(worker), str(second_payload)],
        check=True,
        capture_output=True,
        text=True,
    )
    second_result = json.loads(second.stdout)
    assert second_result["status"] == "REFUSED"
    assert second_result["reason"] == expected["attempt_consumed_reason"]


def test_result_bearing_prepared_campaign_is_refused(
    tmp_path: Path,
) -> None:
    fixture = load_runner_fixture("grant_run_execution.json")
    expected = fixture["expected"]
    inputs = fixture["inputs"]
    prepared_path = tmp_path / "result_bearing.json"
    prepared_path.write_text(
        json.dumps(inputs["result_bearing_prepared"]), encoding="utf-8"
    )
    prepared_digest = sha256_hex(prepared_path.read_bytes())
    binding_path = _write_binding(
        tmp_path, "result_bearing_binding.json", prepared_digest
    )
    identity = _binding_identity(binding_path)
    ledger = _seed_identity_ledger(identity)
    result = run_campaign(
        _config_with_grant(
            inputs["grant_file"],
            tmp_path,
            prepared_campaign_file=str(prepared_path),
            prepared_campaign_file_sha256=prepared_digest,
            detached_binding_file=binding_path,
            attempt_state_file=_copy_attempt_state(
                tmp_path, identity, "attempt_result_bearing.json"
            ),
        )
    )
    assert result.status == "REFUSED"
    assert result.reason == expected["result_bearing_reason"]
    leftover = json.loads(Path(ledger).read_text(encoding="utf-8"))
    assert leftover["consumed"] is False


def _reconcile_ready_config(
    tmp_path: Path,
    prepared: dict[str, object],
    name: str,
) -> tuple[RunConfig, str]:
    fixture = load_runner_fixture("grant_run_execution.json")
    inputs = fixture["inputs"]
    prepared_path = tmp_path / f"{name}_prepared.json"
    prepared_path.write_text(json.dumps(prepared), encoding="utf-8")
    prepared_digest = sha256_hex(prepared_path.read_bytes())
    binding_path = _write_binding(
        tmp_path, f"{name}_binding.json", prepared_digest
    )
    identity = _binding_identity(binding_path)
    ledger = _seed_identity_ledger(identity)
    config = _config_with_grant(
        inputs["grant_file"],
        tmp_path,
        prepared_campaign_file=str(prepared_path),
        prepared_campaign_file_sha256=prepared_digest,
        detached_binding_file=binding_path,
        attempt_state_file=_copy_attempt_state(
            tmp_path, identity, f"{name}_attempt.json"
        ),
    )
    return config, ledger


def test_tmp_environment_wipe_cannot_replay(tmp_path: Path) -> None:
    fixture = load_runner_fixture("grant_run_execution.json")
    expected = fixture["expected"]
    inputs = fixture["inputs"]
    prepared = json.loads(
        fixture_file(inputs["prepared_file"]).read_text(encoding="utf-8")
    )
    config, ledger = _reconcile_ready_config(tmp_path, prepared, "tmp_wipe")
    first = run_campaign(config)
    assert first.status == expected["status"]
    identity = json.loads(Path(ledger).read_text(encoding="utf-8"))[
        "campaign_identity_sha256"
    ]
    ephemeral = Path(tempfile.gettempdir()) / expected["tmp_ledger_dirname"]
    if ephemeral.exists():
        shutil.rmtree(ephemeral)
    ephemeral.mkdir(parents=True)
    fake = json.loads(
        fixture_file("precondition/attempt_state.json").read_text(encoding="utf-8")
    )
    fake["campaign_identity_sha256"] = identity
    (ephemeral / f"{identity}.json").write_text(
        json.dumps(fake, sort_keys=True), encoding="utf-8"
    )
    second = run_campaign(config)
    assert second.status == "REFUSED"
    assert second.reason == expected["attempt_consumed_reason"]
    leftover = json.loads(Path(ledger).read_text(encoding="utf-8"))
    assert leftover["consumed"] is True


def test_executed_bundle_contains_required_children(tmp_path: Path) -> None:
    fixture = load_runner_fixture("grant_run_execution.json")
    expected = fixture["expected"]
    prepared = json.loads(
        fixture_file(fixture["inputs"]["prepared_file"]).read_text(encoding="utf-8")
    )
    config, ledger = _reconcile_ready_config(tmp_path, prepared, "required_children")
    result = run_campaign(config)
    assert result.status == expected["status"]
    assert result.bundle is not None
    for name in expected["runner_owned_children"]:
        assert name in result.bundle.child_digests
    leftover = json.loads(Path(ledger).read_text(encoding="utf-8"))
    assert leftover["consumed"] is True


def test_protocol_and_inventory_file_swap_is_refused(tmp_path: Path) -> None:
    fixture = load_runner_fixture("grant_run_execution.json")
    expected = fixture["expected"]
    inputs = fixture["inputs"]
    prepared = json.loads(
        fixture_file(inputs["prepared_file"]).read_text(encoding="utf-8")
    )
    for case in expected["file_swap_cases"]:
        config, ledger = _reconcile_ready_config(
            tmp_path, prepared, str(case["config_field"])
        )
        source = fixture_file(case["source"])
        swapped = tmp_path / source.name
        swapped.write_bytes(source.read_bytes() + b"\n")
        result = run_campaign(
            _config_with_grant(
                inputs["grant_file"],
                tmp_path,
                prepared_campaign_file=config.prepared_campaign_file,
                prepared_campaign_file_sha256=config.prepared_campaign_file_sha256,
                detached_binding_file=config.detached_binding_file,
                attempt_state_file=config.attempt_state_file,
                **{case["config_field"]: str(swapped)},
            )
        )
        assert result.status == "REFUSED", case
        assert result.reason == case["reason"], case
        leftover = json.loads(Path(ledger).read_text(encoding="utf-8"))
        assert leftover["consumed"] is False, case


def _p1_cases() -> dict[str, object]:
    return load_runner_fixture("execution_p1_cases.json")


def _session_range(start: date, count: int) -> tuple[str, ...]:
    return tuple((start + timedelta(days=index)).isoformat() for index in range(count))


def _listing_index(spec: dict[str, object]) -> int:
    identity = spec["identity"]
    assert isinstance(identity, dict)
    return int(str(identity["resolved_listing_id"]).split("-")[-1])


def _synthetic_listing(index: int, cases: dict[str, object]) -> dict[str, object]:
    inputs = cases["inputs"]
    ticker = fixture_ticker(
        str(inputs["ticker_prefix"]),
        int(inputs["ticker_width"]),
        index,
    )
    listing_key = encode_runner_listing_key(
        str(inputs["exchange"]),
        ticker,
        str(inputs["alias_effective_from"]),
        None,
    )
    identity = {
        "resolved_listing_episode_id": f"EP-{index}",
        "resolved_listing_id": f"LST-{index}",
        "resolved_permanent_security_id": f"SEC-{index}",
    }
    alias = {
        **identity,
        "alias_effective_from": inputs["alias_effective_from"],
        "alias_effective_to": None,
        "lineage_resolution_evidence_id": f"EV-{index}",
        "source_exchange": inputs["exchange"],
        "source_ticker": ticker,
        "transition_to_next": "TARGET_ALIAS",
    }
    return {
        "alias": alias,
        "hex_key": listing_key.hex(),
        "identity": identity,
        "listing_key": listing_key,
    }


def _price_for_case(
    case_name: str,
    cases: dict[str, object],
    spec: dict[str, object],
    session: str,
    sessions: tuple[str, ...],
) -> float:
    inputs = cases["inputs"]
    if case_name == "execution_anchor":
        cfg = inputs["execution_anchor"]
        if session == sessions[0]:
            return float(cfg["start_price"])
        if session == sessions[-1]:
            return float(cfg["end_price"])
        return float(cfg["execution_price"])
    index = _listing_index(spec)
    day = sessions.index(session)
    if case_name == "monthly_ic":
        cfg = inputs["monthly_ic"]
        one = int(inputs["one"])
        price = float(cfg["start_price"]) + index + float(cfg["slope"]) * (index + one) * day
        if session >= str(cfg["first_signal"]) and session < str(cfg["second_signal"]):
            if index >= int(cfg["split_index"]):
                return price * float(cfg["early_high_mult"])
            return price * float(cfg["early_low_mult"])
        if session >= str(cfg["second_signal"]):
            if index >= int(cfg["split_index"]):
                return price * float(cfg["late_high_mult"])
            return price * float(cfg["late_low_mult"])
        return price
    if case_name == "rebalance":
        cfg = inputs["rebalance"]
        return float(cfg["start_price"]) + index + day * float(cfg["day_weight"])
    cfg = inputs["derived_large"]
    remainder = index % int(cfg["parity_mod"])
    parity = float(cfg["parity_boost"]) if remainder else float(cfg["zero"])
    return float(cfg["start_price"]) + index + float(cfg["day_weight"]) * day + parity


def _synthetic_panel(
    sessions: tuple[str, ...],
    listing_count: int,
    signal_flags: dict[str, bool],
    case_name: str,
    cases: dict[str, object],
) -> dict[str, object]:
    listings_out: dict[str, list[dict[str, object]]] = {}
    prices: dict[str, dict[str, float]] = {}
    anchors: dict[str, list[dict[str, object]]] = {}
    specs = [_synthetic_listing(index, cases) for index in range(listing_count)]
    for spec in specs:
        hex_key = str(spec["hex_key"])
        alias = spec["alias"]
        assert isinstance(alias, dict)
        prices[hex_key] = {
            session: _price_for_case(case_name, cases, spec, session, sessions)
            for session in sessions
        }
        anchors[hex_key] = [
            {
                **alias,
                "adjusted_close": prices[hex_key][session],
                "session_date": session,
            }
            for session in sessions
        ]
    for signal_date, in_universe in signal_flags.items():
        rows = []
        for spec in specs:
            rows.append(
                {
                    "alias_chain": [spec["alias"]],
                    "in_universe_at_t": in_universe,
                    "listing_key": spec["hex_key"],
                    "lookback_addressable_at_t": True,
                    "target_identity": spec["identity"],
                    "terminal_blocked_at_t": False,
                }
            )
        listings_out[signal_date] = rows
    return {"anchors": anchors, "listings": listings_out, "prices": prices}


def _run_prepared(tmp_path: Path, prepared: dict[str, object], name: str):
    config, _ledger = _reconcile_ready_config(tmp_path, prepared, name)
    return run_campaign(config)


def _parse_child(result: CampaignRun, name: str) -> dict[str, object]:
    assert result.artifacts is not None
    payload = json.loads(result.artifacts[name].decode("utf-8"))
    assert isinstance(payload, dict)
    return payload


def _month_end_flags(sessions: tuple[str, ...], one: int) -> dict[str, bool]:
    flags: dict[str, bool] = {}
    for index, session in enumerate(sessions):
        nxt_index = index + one
        if nxt_index >= len(sessions):
            continue
        if session[5:7] != sessions[nxt_index][5:7]:
            flags[session] = True
    return flags


def test_executed_children_parse_with_required_schemas(tmp_path: Path) -> None:
    cases = _p1_cases()
    inputs = cases["inputs"]
    prepared = json.loads(
        fixture_file("precondition/prepared_campaign.json").read_text(encoding="utf-8")
    )
    result = _run_prepared(tmp_path, prepared, "artifact_schema")
    assert result.status == inputs["executed_status"]
    assert result.artifacts is not None
    placeholder = json.dumps(
        {
            "name": inputs["placeholder_child"],
            "schema_version": inputs["placeholder_schema"],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    assert result.artifacts[str(inputs["placeholder_child"])] != placeholder
    schema = inputs["artifact_schema"]
    diagnostics = _parse_child(result, "factor_diagnostics.parquet")
    assert diagnostics["schema_version"] == schema["diagnostics"]
    assert "monthly_rank_ics" in diagnostics
    strategy = _parse_child(result, "strategy_returns.parquet")
    assert strategy["schema_version"] == schema["strategy"]
    assert "trials" in strategy
    review = _parse_child(result, "review_record.json")
    assert review["schema_version"] == schema["review"]
    assert review["evidence_ceiling"] == cases["expected"]["evidence_ceiling"]
    for name in required_bundle_children():
        assert name in result.artifacts


def test_forward_returns_anchor_at_execution_close(tmp_path: Path) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["execution_anchor"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    prepared = _synthetic_panel(
        sessions,
        int(cfg["listing_count"]),
        {str(cfg["signal_date"]): True},
        "execution_anchor",
        cases,
    )
    result = _run_prepared(tmp_path, prepared, "execution_anchor")
    assert result.status == cases["inputs"]["executed_status"]
    diagnostics = _parse_child(result, "factor_diagnostics.parquet")
    months = diagnostics["monthly_rank_ics"]
    assert months
    forwards = months[0]["forward_returns"]
    assert months[0]["execution_date"] == sessions[1]
    assert months[0]["label_end_date"] == sessions[-1]
    values = [row["value"] for row in forwards if row["valid"]]
    assert values
    expected = float(cfg["expected_return"])
    rel_tol = float(cfg["rel_tol"])
    for value in values:
        assert abs(float(value) - expected) < rel_tol


def test_rank_ic_is_computed_per_signal_month(tmp_path: Path) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["monthly_ic"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    first = str(cfg["first_signal"])
    second = str(cfg["second_signal"])
    prepared = _synthetic_panel(
        sessions,
        int(cfg["listing_count"]),
        {first: True, second: True},
        "monthly_ic",
        cases,
    )
    result = _run_prepared(tmp_path, prepared, "monthly_ic")
    assert result.status == cases["inputs"]["executed_status"]
    diagnostics = _parse_child(result, "factor_diagnostics.parquet")
    by_signal: dict[str, list[object]] = {}
    for month in diagnostics["monthly_rank_ics"]:
        by_signal.setdefault(month["signal_date"], []).append(month["value"])
    assert first in by_signal
    assert second in by_signal
    assert by_signal[first] != by_signal[second]


def test_continuous_paths_charge_initial_turnover_and_keep_factor_benchmarks(
    tmp_path: Path,
) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["rebalance"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    flags = {
        str(row["signal_date"]): bool(row["in_universe"])
        for row in cfg["signals"]
    }
    result = _run_prepared(
        tmp_path,
        _synthetic_panel(
            sessions,
            int(cfg["listing_count"]),
            flags,
            "rebalance",
            cases,
        ),
        "rebalance",
    )
    assert result.status == cases["inputs"]["executed_status"]
    costs = _parse_child(result, "cost_sensitivity.json")
    rev = str(cases["inputs"]["rev_factor_id"])
    zero = next(
        row["cost_impact_sum"]
        for row in costs["trials"]
        if row["trial_id"] == cases["inputs"]["rev_zero_trial_id"]
        and row["factor_id"] == rev
    )
    ten = next(
        row["cost_impact_sum"]
        for row in costs["trials"]
        if row["trial_id"] == cases["inputs"]["rev_ten_trial_id"]
        and row["factor_id"] == rev
    )
    assert zero == 0.0
    assert ten > zero
    strategy = _parse_child(result, "strategy_returns.parquet")
    baseline = [
        row
        for row in strategy["trials"]
        if row["trial_id"] == cases["inputs"]["equal_weight_trial_id"]
    ]
    factor_ids = {row["factor_id"] for row in baseline}
    assert factor_ids == set(cases["inputs"]["universe_factor_ids"])
    by_factor = {row["factor_id"]: row["valid"] for row in baseline}
    assert by_factor[rev] is True
    ten_path = next(
        row
        for row in strategy["trials"]
        if row["trial_id"] == cases["inputs"]["rev_ten_trial_id"]
        and row["factor_id"] == rev
    )
    first = ten_path["points"][0]
    expected = float(cases["inputs"]["initial_turnover"])
    rel_tol = float(cases["inputs"]["execution_anchor"]["rel_tol"])
    assert abs(float(first["turnover"]) - expected) < rel_tol
    assert first["cost_impact"] > 0.0


def test_diagnostic_payload_is_derived_from_execution(tmp_path: Path) -> None:
    cases = _p1_cases()
    prepared = json.loads(
        fixture_file("precondition/prepared_campaign.json").read_text(encoding="utf-8")
    )
    small = _run_prepared(tmp_path, prepared, "derived_small")
    assert small.status == cases["inputs"]["executed_status"]
    assert small.reconciliation is not None
    assert small.reconciliation.diagnostic_inputs is not None
    small_inputs = small.reconciliation.diagnostic_inputs
    cfg = cases["inputs"]["derived_large"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    large = _run_prepared(
        tmp_path,
        _synthetic_panel(
            sessions,
            int(cfg["listing_count"]),
            _month_end_flags(sessions, int(cases["inputs"]["one"])),
            "derived_large",
            cases,
        ),
        "derived_large",
    )
    assert large.status == cases["inputs"]["executed_status"]
    assert large.reconciliation is not None
    assert large.reconciliation.diagnostic_inputs is not None
    large_inputs = large.reconciliation.diagnostic_inputs
    assert large_inputs.common_months != small_inputs.common_months or (
        large_inputs.mean_rank_ics != small_inputs.mean_rank_ics
    )
    assert large.reconciliation.final_state != cases["expected"]["invalid_state"]


def test_attempt_is_reserved_before_execution(tmp_path: Path) -> None:
    cases = _p1_cases()
    prepared = json.loads(
        fixture_file("precondition/prepared_campaign.json").read_text(encoding="utf-8")
    )
    config, _ledger = _reconcile_ready_config(tmp_path, prepared, "reserve_once")
    first = run_campaign(config)
    assert first.status == cases["inputs"]["executed_status"]
    second = run_campaign(config)
    assert second.status == "REFUSED"
    assert second.reason == "CAMPAIGN_ATTEMPT_ALREADY_CONSUMED"
    assert second.reconciliation is None


def test_boundary_signals_are_excluded_from_continuous_paths(
    tmp_path: Path,
) -> None:
    cases = _p1_cases()
    cutoff = load_runner_fixture("session_month_cutoff.json")
    bound = str(cutoff["inputs"]["accepted_cutoff"])
    sessions = tuple(
        session
        for session in cutoff["inputs"]["session_dates"]
        if session <= bound
    )
    flags = {
        cutoff["expected"]["june_signal"]["signal_date"]: True,
        cutoff["expected"]["july_signal"]["signal_date"]: True,
    }
    result = _run_prepared(
        tmp_path,
        _synthetic_panel(sessions, int(cases["inputs"]["one"]), flags, "rebalance", cases),
        "cutoff_boundary",
    )
    assert result.status == cases["inputs"]["executed_status"]
    strategy = _parse_child(result, "strategy_returns.parquet")
    sessions_seen = {
        point["session_date"]
        for row in strategy["trials"]
        for point in row["points"]
    }
    assert cutoff["expected"]["july_signal"]["execution_date"] not in sessions_seen


def test_held_returns_require_exact_boundary_anchors(tmp_path: Path) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["execution_anchor"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    missing_sessions = (sessions[1], sessions[-1])
    for missing in missing_sessions:
        prepared = _synthetic_panel(
            sessions,
            int(cfg["listing_count"]),
            {str(cfg["signal_date"]): True},
            "execution_anchor",
            cases,
        )
        hex_key = next(iter(prepared["prices"]))
        del prepared["prices"][hex_key][missing]
        prepared["anchors"][hex_key] = [
            record
            for record in prepared["anchors"][hex_key]
            if record["session_date"] != missing
        ]
        result = _run_prepared(
            tmp_path, prepared, f"missing-{missing}"
        )
        assert result.status == cases["inputs"]["executed_status"]
        diagnostics = _parse_child(result, "factor_diagnostics.parquet")
        forwards = diagnostics["monthly_rank_ics"][0]["forward_returns"]
        dropped = [row for row in forwards if row["listing_key"] == hex_key]
        assert dropped
        assert dropped[0]["valid"] is False


def test_invalid_stress_paths_fail_hard_validity(tmp_path: Path) -> None:
    cases = _p1_cases()
    prepared = json.loads(
        fixture_file("precondition/prepared_campaign.json").read_text(encoding="utf-8")
    )
    result = _run_prepared(tmp_path, prepared, "stress_hard")
    assert result.status == cases["inputs"]["executed_status"]
    assert result.reconciliation is not None
    assert result.reconciliation.diagnostic_inputs is not None
    assert result.reconciliation.diagnostic_inputs.hard_valid is False
    assert result.reconciliation.final_state == cases["expected"]["invalid_state"]


def test_robustness_keeps_missing_scheduled_years(tmp_path: Path) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["robustness_years"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    flags = _month_end_flags(sessions, int(cases["inputs"]["one"]))
    for signal_date in list(flags):
        if signal_date.startswith(str(cases["inputs"]["gap_year_prefix"])):
            flags[signal_date] = False
    result = _run_prepared(
        tmp_path,
        _synthetic_panel(
            sessions,
            int(cfg["listing_count"]),
            flags,
            "monthly_ic",
            cases,
        ),
        "missing_year",
    )
    assert result.status == cases["inputs"]["executed_status"]
    yearly = _parse_child(result, "yearly_robustness.json")
    assert cases["inputs"]["missing_year"] in yearly["required_years"]


def test_decile_artifact_contains_executed_fields(tmp_path: Path) -> None:
    cases = _p1_cases()
    prepared = json.loads(
        fixture_file("precondition/prepared_campaign.json").read_text(encoding="utf-8")
    )
    result = _run_prepared(tmp_path, prepared, "decile_rows")
    assert result.status == cases["inputs"]["executed_status"]
    deciles = _parse_child(result, "decile_returns.parquet")
    assert deciles["schema_version"] == cases["inputs"]["artifact_schema"]["decile"]
    assert deciles["rows"]
    required = cases["inputs"]["decile_fields"]
    for row in deciles["rows"]:
        for field in required:
            assert field in row


def test_accepted_cutoff_is_last_session_not_latest_signal(
    tmp_path: Path,
) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["mid_month_cutoff"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    result = _run_prepared(
        tmp_path,
        _synthetic_panel(
            sessions,
            int(cfg["listing_count"]),
            {str(cfg["signal_date"]): True},
            "execution_anchor",
            cases,
        ),
        "mid_month_cutoff",
    )
    assert result.status == cases["inputs"]["executed_status"]
    manifest = _parse_child(result, "dataset_full_manifest.json")
    assert manifest["accepted_cutoff"] == sessions[-1]
    assert manifest["accepted_cutoff"] != cfg["signal_date"]


def test_primary_folds_start_in_evaluation_year(tmp_path: Path) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["warmup_folds"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    result = _run_prepared(
        tmp_path,
        _synthetic_panel(
            sessions,
            int(cfg["listing_count"]),
            _month_end_flags(sessions, int(cases["inputs"]["one"])),
            "monthly_ic",
            cases,
        ),
        "warmup_folds",
    )
    assert result.status == cases["inputs"]["executed_status"]
    manifest = _parse_child(result, "dataset_full_manifest.json")
    yearly = _parse_child(result, "yearly_robustness.json")
    assert manifest["first_fold_year"] == cases["expected"]["first_fold_year"]
    assert cfg["warmup_year"] not in yearly["required_years"]


def test_rank_ic_omits_ineligible_listings(tmp_path: Path) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["mixed_eligible"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    flags = _month_end_flags(sessions, int(cases["inputs"]["one"]))
    listing_count = int(cfg["eligible_count"]) + int(cfg["ineligible_count"])
    mixed = _synthetic_panel(
        sessions,
        listing_count,
        flags,
        "derived_large",
        cases,
    )
    ineligible_hex = None
    for rows in mixed["listings"].values():
        rows[-1]["in_universe_at_t"] = False
        ineligible_hex = rows[-1]["listing_key"]
    eligible = _synthetic_panel(
        sessions,
        int(cfg["eligible_count"]),
        flags,
        "derived_large",
        cases,
    )
    mixed_result = _run_prepared(tmp_path, mixed, "mixed_eligible")
    eligible_result = _run_prepared(tmp_path, eligible, "eligible_cross_section")
    assert mixed_result.status == cases["inputs"]["executed_status"]
    assert eligible_result.status == cases["inputs"]["executed_status"]
    mixed_diagnostics = _parse_child(mixed_result, "factor_diagnostics.parquet")
    eligible_diagnostics = _parse_child(
        eligible_result, "factor_diagnostics.parquet"
    )
    valid_months = [
        month
        for month in mixed_diagnostics["monthly_rank_ics"]
        if month["valid"] is True
    ]
    assert valid_months
    assert ineligible_hex is not None
    mixed_listing_keys = {
        row["listing_key"]
        for rows in mixed["listings"].values()
        for row in rows
    }
    eligible_listing_keys = {
        row["listing_key"]
        for rows in eligible["listings"].values()
        for row in rows
    }
    assert ineligible_hex in mixed_listing_keys
    assert ineligible_hex not in eligible_listing_keys
    mixed_ics = [
        (month["factor_id"], month["signal_date"], month["value"], month["valid"])
        for month in mixed_diagnostics["monthly_rank_ics"]
    ]
    eligible_ics = [
        (month["factor_id"], month["signal_date"], month["value"], month["valid"])
        for month in eligible_diagnostics["monthly_rank_ics"]
    ]
    assert mixed_ics == eligible_ics
    for month in valid_months:
        assert month["value"] is not None
        assert month["reason"] is None


def test_below_floor_rank_ic_months_remain_invalid(tmp_path: Path) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["below_floor_eligible"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    listing_count = int(cfg["eligible_count"]) + int(cfg["ineligible_count"])
    prepared = _synthetic_panel(
        sessions,
        listing_count,
        _month_end_flags(sessions, int(cases["inputs"]["one"])),
        "derived_large",
        cases,
    )
    ineligible = int(cfg["ineligible_count"])
    for rows in prepared["listings"].values():
        for row in rows[-ineligible:]:
            row["in_universe_at_t"] = False
    result = _run_prepared(tmp_path, prepared, "below_floor_eligible")
    assert result.status == cases["inputs"]["executed_status"]
    diagnostics = _parse_child(result, "factor_diagnostics.parquet")
    scored = [
        month
        for month in diagnostics["monthly_rank_ics"]
        if month["reason"] != "EVALUATION_FOLD_LABEL_PURGED"
    ]
    assert scored
    assert all(month["valid"] is False for month in scored)
    assert any(
        month["reason"] == cfg["invalid_reason"] for month in scored
    )


def test_unscheduled_listing_dates_do_not_enter_resets_outputs_or_lineage(
    tmp_path: Path,
) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["mid_month_injection"]
    rebalance = cases["inputs"]["rebalance"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    flags = {
        str(row["signal_date"]): bool(row["in_universe"])
        for row in rebalance["signals"]
    }
    control = _synthetic_panel(
        sessions,
        int(cfg["listing_count"]),
        flags,
        "rebalance",
        cases,
    )
    template = next(iter(control["listings"].values()))
    injected_date = str(cfg["injected_date"])
    ineligible = json.loads(json.dumps(control))
    ineligible["listings"][injected_date] = [
        {**row, "in_universe_at_t": False} for row in template
    ]
    eligible = json.loads(json.dumps(control))
    eligible["listings"][injected_date] = [
        {**row, "in_universe_at_t": True} for row in template
    ]
    lineage = json.loads(json.dumps(control))
    mutated = []
    for row in template:
        identity = dict(row["target_identity"])
        identity["resolved_permanent_security_id"] = (
            f"OTHER-{identity['resolved_permanent_security_id']}"
        )
        alias = dict(row["alias_chain"][0])
        alias["resolved_permanent_security_id"] = identity[
            "resolved_permanent_security_id"
        ]
        mutated.append(
            {
                **row,
                "alias_chain": [alias],
                "in_universe_at_t": True,
                "target_identity": identity,
            }
        )
    lineage["listings"][injected_date] = mutated
    control_result = _run_prepared(tmp_path, control, "mid_month_control")
    ineligible_result = _run_prepared(tmp_path, ineligible, "mid_month_injected")
    eligible_result = _run_prepared(tmp_path, eligible, "eligible_mid_injected")
    lineage_result = _run_prepared(tmp_path, lineage, "lineage_mid_injected")
    executed = cases["inputs"]["executed_status"]
    assert control_result.status == executed
    assert ineligible_result.status == executed
    assert eligible_result.status == executed
    assert lineage_result.status == executed
    session = str(cfg["injected_execution"])
    assert _turnover_on(cases, control_result, session) == _turnover_on(
        cases, ineligible_result, session
    )
    assert control_result.reconciliation is not None
    assert eligible_result.reconciliation is not None
    assert lineage_result.reconciliation is not None
    assert (
        control_result.reconciliation.invalid_and_missing["invalid_required_outputs"]
        == eligible_result.reconciliation.invalid_and_missing["invalid_required_outputs"]
    )
    assert _parse_child(control_result, "factor_diagnostics.parquet") == _parse_child(
        eligible_result, "factor_diagnostics.parquet"
    )
    assert _parse_child(control_result, "decile_returns.parquet")["rows"] == _parse_child(
        eligible_result, "decile_returns.parquet"
    )["rows"]
    assert control_result.reconciliation.final_state == cases["expected"][
        "inconclusive_state"
    ]
    assert (
        lineage_result.reconciliation.final_state
        == control_result.reconciliation.final_state
    )
    assert lineage_result.reconciliation.final_state != cases["expected"][
        "invalid_state"
    ]


def test_warmup_missing_labels_do_not_invalidate_primary(
    tmp_path: Path,
) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["warmup_missing_label"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    flags = _month_end_flags(sessions, int(cases["inputs"]["one"]))
    control = _synthetic_panel(
        sessions,
        int(cfg["listing_count"]),
        flags,
        "derived_large",
        cases,
    )
    prepared = json.loads(json.dumps(control))
    warmup = next(
        signal_date
        for signal_date in flags
        if signal_date.startswith(str(cfg["warmup_prefix"]))
    )
    label_end = sessions[
        sessions.index(warmup) + int(cases["inputs"]["one"]) + int(cfg["horizon_rows"])
    ]
    hex_key = next(iter(prepared["prices"]))
    del prepared["prices"][hex_key][label_end]
    prepared["anchors"][hex_key] = [
        record
        for record in prepared["anchors"][hex_key]
        if record["session_date"] != label_end
    ]
    control_result = _run_prepared(tmp_path, control, "warmup_control")
    result = _run_prepared(tmp_path, prepared, "warmup_missing_label")
    assert result.status == cases["inputs"]["executed_status"]
    assert control_result.status == cases["inputs"]["executed_status"]
    assert result.reconciliation is not None
    assert control_result.reconciliation is not None
    assert result.reconciliation.diagnostic_inputs is not None
    assert result.reconciliation.diagnostic_inputs.prefrozen_coverage_met is True
    assert result.reconciliation.final_state != cases["expected"]["invalid_state"]
    assert (
        result.reconciliation.invalid_and_missing["invalid_required_outputs"]
        == control_result.reconciliation.invalid_and_missing["invalid_required_outputs"]
    )


def test_empty_primary_calendar_does_not_use_warmup_coverage(
    tmp_path: Path,
) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["empty_primary_calendar"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    flags = _month_end_flags(sessions, int(cases["inputs"]["one"]))
    prepared = _synthetic_panel(
        sessions,
        int(cfg["listing_count"]),
        flags,
        "derived_large",
        cases,
    )
    warmup = max(
        signal_date
        for signal_date in flags
        if signal_date.startswith(str(cfg["warmup_prefix"]))
    )
    for signal_date, rows in prepared["listings"].items():
        if signal_date != warmup:
            rows[0]["in_universe_at_t"] = False
    label_end = sessions[
        sessions.index(warmup) + int(cases["inputs"]["one"]) + int(cfg["horizon_rows"])
    ]
    hex_key = next(iter(prepared["prices"]))
    del prepared["prices"][hex_key][label_end]
    prepared["anchors"][hex_key] = [
        record
        for record in prepared["anchors"][hex_key]
        if record["session_date"] != label_end
    ]
    result = _run_prepared(tmp_path, prepared, "empty_primary_calendar")
    assert result.status == cases["inputs"]["executed_status"]
    assert result.reconciliation is not None
    assert result.reconciliation.diagnostic_inputs is not None
    assert result.reconciliation.diagnostic_inputs.prefrozen_coverage_met is True
    yearly = _parse_child(result, "yearly_robustness.json")
    assert cases["expected"]["first_fold_year"] not in yearly["required_years"]
    assert result.reconciliation.invalid_and_missing["invalid_required_outputs"] > 0
    assert result.reconciliation.final_state == cases["expected"]["invalid_state"]


def test_continuous_resets_across_year_boundary(tmp_path: Path) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["year_boundary"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    result = _run_prepared(
        tmp_path,
        _synthetic_panel(
            sessions,
            int(cfg["listing_count"]),
            _month_end_flags(sessions, int(cases["inputs"]["one"])),
            "rebalance",
            cases,
        ),
        "year_boundary",
    )
    assert result.status == cases["inputs"]["executed_status"]
    execution = str(cfg["january_execution"])
    turnover = _turnover_on(cases, result, execution)
    expected = float(cases["inputs"]["initial_turnover"])
    rel_tol = float(cases["inputs"]["execution_anchor"]["rel_tol"])
    assert abs(turnover - expected) < rel_tol
    diagnostics = _parse_child(result, "factor_diagnostics.parquet")
    december = str(cfg["december_signal"])
    purged = [
        month
        for month in diagnostics["monthly_rank_ics"]
        if month["signal_date"] == december
    ]
    assert purged
    assert all(month["valid"] is False for month in purged)
    assert all(month["reason"] == cfg["purged_reason"] for month in purged)
    assert len(purged) == int(cfg["december_purged_factor_month_count"])
    summary = _parse_child(result, "invalid_and_missing_summary.json")
    assert summary["summary"]["purged_factor_month_count"] == int(
        cfg["purged_factor_month_count"]
    )


def test_omitted_scheduled_month_is_still_purged_and_counted(
    tmp_path: Path,
) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["year_boundary"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    prepared = _synthetic_panel(
        sessions,
        int(cfg["listing_count"]),
        _month_end_flags(sessions, int(cases["inputs"]["one"])),
        "rebalance",
        cases,
    )
    del prepared["listings"][str(cfg["december_signal"])]
    result = _run_prepared(tmp_path, prepared, "omitted_december")
    assert result.status == cases["inputs"]["executed_status"]
    summary = _parse_child(result, "invalid_and_missing_summary.json")
    assert summary["summary"]["purged_factor_month_count"] == int(
        cfg["purged_factor_month_count"]
    )
    diagnostics = _parse_child(result, "factor_diagnostics.parquet")
    december = str(cfg["december_signal"])
    purged = [
        month
        for month in diagnostics["monthly_rank_ics"]
        if month["signal_date"] == december
    ]
    assert purged
    assert all(month["valid"] is False for month in purged)
    assert all(month["reason"] == cfg["purged_reason"] for month in purged)
    execution = str(cfg["january_execution"])
    strategy = _parse_child(result, "strategy_returns.parquet")
    rev = str(cases["inputs"]["rev_factor_id"])
    ten = next(
        row
        for row in strategy["trials"]
        if row["trial_id"] == cases["inputs"]["rev_ten_trial_id"]
        and row["factor_id"] == rev
    )
    sessions_seen = {point["session_date"] for point in ten["points"]}
    assert execution in sessions_seen


def test_omitted_incomplete_cutoff_month_is_still_purged_and_counted(
    tmp_path: Path,
) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["year_boundary"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    prepared = _synthetic_panel(
        sessions,
        int(cfg["listing_count"]),
        _month_end_flags(sessions, int(cases["inputs"]["one"])),
        "rebalance",
        cases,
    )
    cutoff = str(cfg["final_cutoff_signal"])
    prepared["listings"].pop(cutoff, None)
    result = _run_prepared(tmp_path, prepared, "omitted_incomplete_cutoff")
    assert result.status == cases["inputs"]["executed_status"]
    summary = _parse_child(result, "invalid_and_missing_summary.json")
    assert summary["summary"]["purged_factor_month_count"] == int(
        cfg["purged_factor_month_count"]
    )
    diagnostics = _parse_child(result, "factor_diagnostics.parquet")
    purged = [
        month
        for month in diagnostics["monthly_rank_ics"]
        if month["signal_date"] == cutoff
    ]
    assert purged
    assert all(month["valid"] is False for month in purged)
    assert all(month["reason"] == cfg["purged_reason"] for month in purged)
    assert len(purged) == int(cfg["december_purged_factor_month_count"])


def _turnover_on(
    cases: dict[str, object],
    result: CampaignRun,
    session: str,
) -> float:
    strategy = _parse_child(result, "strategy_returns.parquet")
    rev = str(cases["inputs"]["rev_factor_id"])
    ten = next(
        row
        for row in strategy["trials"]
        if row["trial_id"] == cases["inputs"]["rev_ten_trial_id"]
        and row["factor_id"] == rev
    )
    point = next(row for row in ten["points"] if row["session_date"] == session)
    return float(point["turnover"])

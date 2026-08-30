"""Authorized runner orchestration and byte-identical repeat runs."""

from __future__ import annotations

import dataclasses
import inspect
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from campaign.bundle import invalid_and_missing_bytes
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

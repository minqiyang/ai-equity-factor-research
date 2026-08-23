"""P-1 through P-5 same-role authorization goldens."""

from __future__ import annotations

import inspect
import json
from pathlib import Path

from campaign.precondition import (
    IDENTITY_EXCLUDE,
    authorize,
    project_acceptance_identity,
    result_bearing_refusal_reason,
)
from campaign.runner import RunConfig
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
    }
    return make_run_config(locators, digests, protocol, **overrides)


def _write_json(path: Path, payload: object) -> bytes:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    path.write_bytes(raw)
    return raw


def test_identity_golden_verifies_each_role_independently() -> None:
    fixture = load_runner_fixture("acceptance_record_identity_golden.json")
    raw = fixture_file(fixture["inputs"]["record_file"]).read_bytes()
    expected = fixture["expected"]
    assert sha256_hex(raw) == expected["file_bytes"]
    record = json.loads(raw.decode("utf-8"))
    assert project_acceptance_identity(record) == expected["canonical_identity"]
    assert record["acceptance_record_sha256"] == expected["canonical_identity"]
    result = authorize(_authorized_config())
    assert result.status == expected["status"]
    assert result.reason == expected["reason"]
    assert result.record is not None
    assert fixture["forbidden"]["use_file_bytes_as_identity_expected"]
    assert fixture["forbidden"]["assert_roles_equal"]
    assert fixture["forbidden"]["assert_roles_unequal"]


def test_self_inconsistent_record_is_refused_without_repair(
    tmp_path: Path,
) -> None:
    fixture = load_runner_fixture("acceptance_record_self_inconsistent.json")
    golden = load_runner_fixture("acceptance_record_identity_golden.json")
    record = json.loads(
        fixture_file(fixture["inputs"]["record_file"]).read_text(encoding="utf-8")
    )
    record["acceptance_record_sha256"] = fixture["inputs"]["wrong_identity"]
    target = tmp_path / "self_inconsistent.json"
    raw = _write_json(target, record)
    result = authorize(
        _authorized_config(
            acceptance_record_file=str(target),
            acceptance_record_file_sha256=sha256_hex(raw),
            acceptance_identity_sha256=golden["expected"]["canonical_identity"],
        )
    )
    assert result.status == "REFUSED"
    assert result.reason == fixture["expected"]["reason"]
    assert result.record is None
    assert project_acceptance_identity(record) == fixture["expected"]["canonical_identity"]
    assert record["acceptance_record_sha256"] != fixture["expected"]["canonical_identity"]


def test_role_swap_refuses_at_p15_without_comparing_config_fields() -> None:
    fixture = load_runner_fixture("acceptance_record_role_swap.json")
    expected = fixture["expected"]
    result = authorize(
        _authorized_config(acceptance_identity_sha256=expected["file_bytes"])
    )
    assert result.status == "REFUSED"
    assert result.reason == expected["reason"]
    assert result.record is None
    assert fixture["forbidden"]["compare_config_digest_fields"]


def test_byte_tamper_refuses_before_parse(tmp_path: Path) -> None:
    fixture = load_runner_fixture("acceptance_record_byte_tamper.json")
    raw = bytearray(fixture_file(fixture["inputs"]["record_file"]).read_bytes())
    offset = fixture["inputs"]["flip_offset"]
    raw[offset] = raw[offset] ^ 0x01
    target = tmp_path / "tampered.json"
    target.write_bytes(raw)
    result = authorize(_authorized_config(acceptance_record_file=str(target)))
    assert result.status == "REFUSED"
    assert result.reason == fixture["expected"]["reason"]
    assert result.record is None


def test_whitespace_reserialize_refuses_file_bytes_and_keeps_identity(
    tmp_path: Path,
) -> None:
    fixture = load_runner_fixture("acceptance_record_whitespace.json")
    record = json.loads(
        fixture_file(fixture["inputs"]["record_file"]).read_text(encoding="utf-8")
    )
    pretty = json.dumps(record, indent=4).encode("utf-8")
    assert sha256_hex(pretty) != fixture["expected"]["file_bytes"]
    assert project_acceptance_identity(record) == fixture["expected"]["canonical_identity"]
    target = tmp_path / "whitespace.json"
    target.write_bytes(pretty)
    result = authorize(
        _authorized_config(
            acceptance_record_file=str(target),
            acceptance_identity_sha256=fixture["expected"]["canonical_identity"],
        )
    )
    assert result.status == "REFUSED"
    assert result.reason == fixture["expected"]["reason"]
    assert result.record is None


def test_authorization_field_matrix_names_each_refusal(tmp_path: Path) -> None:
    fixture = load_runner_fixture("authorization_field_matrix.json")
    golden = load_runner_fixture("acceptance_record_identity_golden.json")
    base_record = json.loads(
        fixture_file(fixture["inputs"]["record_file"]).read_text(encoding="utf-8")
    )
    base_grant = json.loads(
        fixture_file(fixture["inputs"]["grant_file"]).read_text(encoding="utf-8")
    )
    for case in fixture["expected"]["cases"]:
        record = json.loads(json.dumps(base_record))
        grant = json.loads(json.dumps(base_grant))
        if case["target"] == "record":
            record[case["field"]] = case["value"]
            record["acceptance_record_sha256"] = project_acceptance_identity(record)
        elif case["target"] == "grant":
            grant[case["field"]] = case["value"]
        else:
            grant["gate"][case["field"]] = case["value"]
        record_path = tmp_path / "matrix_record.json"
        grant_path = tmp_path / "matrix_grant.json"
        record_raw = _write_json(record_path, record)
        grant["acceptance_record_file_sha256"] = sha256_hex(record_raw)
        grant["acceptance_record_sha256"] = record["acceptance_record_sha256"]
        grant_raw = _write_json(grant_path, grant)
        result = authorize(
            _authorized_config(
                acceptance_record_file=str(record_path),
                acceptance_record_file_sha256=sha256_hex(record_raw),
                acceptance_identity_sha256=record["acceptance_record_sha256"],
                stage2_grant_file=str(grant_path),
                stage2_grant_file_sha256=sha256_hex(grant_raw),
            )
        )
        assert result.status == "REFUSED", case
        assert result.reason == case["reason"], case
    assert fixture["forbidden"]["single_field_authorizes"]
    assert golden["expected"]["status"] == "AUTHORIZED"


def test_stage2_status_does_not_authorize_or_deny() -> None:
    fixture = load_runner_fixture("stage2_status_non_authorizer.json")
    result = authorize(_authorized_config())
    assert result.status == fixture["expected"]["status"]
    assert result.record is not None
    assert result.record["stage2_status"] == fixture["expected"]["stage2_status"]


def test_timestamp_normalization_and_naive_refusal(tmp_path: Path) -> None:
    fixture = load_runner_fixture("timestamp_normalization.json")
    base = json.loads(
        fixture_file("precondition/acceptance_valid.json").read_text(encoding="utf-8")
    )
    field = fixture["inputs"]["timestamp_field"]
    for value in fixture["inputs"]["aware_values"]:
        record = json.loads(json.dumps(base))
        record[field] = value
        record["acceptance_record_sha256"] = project_acceptance_identity(record)
        path = tmp_path / "ts_record.json"
        raw = _write_json(path, record)
        grant = json.loads(
            fixture_file("precondition/grant_valid.json").read_text(encoding="utf-8")
        )
        grant["acceptance_record_file_sha256"] = sha256_hex(raw)
        grant["acceptance_record_sha256"] = record["acceptance_record_sha256"]
        grant_path = tmp_path / "ts_grant.json"
        grant_raw = _write_json(grant_path, grant)
        binding = json.loads(
            fixture_file("precondition/binding_valid.json").read_text(
                encoding="utf-8"
            )
        )
        binding["acceptance_record_file_sha256"] = sha256_hex(raw)
        binding["acceptance_identity_sha256"] = record["acceptance_record_sha256"]
        binding_path = tmp_path / "ts_binding.json"
        _write_json(binding_path, binding)
        result = authorize(
            _authorized_config(
                acceptance_record_file=str(path),
                acceptance_record_file_sha256=sha256_hex(raw),
                acceptance_identity_sha256=record["acceptance_record_sha256"],
                stage2_grant_file=str(grant_path),
                stage2_grant_file_sha256=sha256_hex(grant_raw),
                detached_binding_file=str(binding_path),
            )
        )
        assert result.status == "AUTHORIZED"
        assert result.record is not None
        assert result.record[field] == fixture["expected"]["utc"]
    for value in (
        *fixture["inputs"]["naive_values"],
        *fixture["inputs"]["date_only_values"],
    ):
        record = json.loads(json.dumps(base))
        record[field] = value
        path = tmp_path / "ts_bad.json"
        raw = _write_json(path, record)
        result = authorize(
            _authorized_config(
                acceptance_record_file=str(path),
                acceptance_record_file_sha256=sha256_hex(raw),
                acceptance_identity_sha256=project_acceptance_identity(record),
            )
        )
        assert result.status == "REFUSED"
        assert result.reason == fixture["expected"]["reason"]


def test_protocol_and_binding_refusals(tmp_path: Path) -> None:
    fixture = load_runner_fixture("precondition_p3_p4.json")
    expected = fixture["expected"]
    protocol = authorize(
        _authorized_config(
            protocol_file_sha256=fixture["inputs"]["wrong_protocol_bytes"]
        )
    )
    assert protocol.reason == expected["protocol_reason"]
    inventory = authorize(
        _authorized_config(
            trial_inventory_file_sha256=fixture["inputs"]["wrong_inventory_bytes"]
        )
    )
    assert inventory.reason == expected["inventory_reason"]
    absent = authorize(
        _authorized_config(
            detached_binding_file=fixture["inputs"]["missing_binding_file"]
        )
    )
    assert absent.reason == expected["absent_reason"]
    binding = json.loads(
        fixture_file("precondition/binding_valid.json").read_text(encoding="utf-8")
    )
    binding[fixture["inputs"]["wrong_binding_field"]] = fixture["inputs"][
        "wrong_binding_value"
    ]
    path = tmp_path / "bad_binding.json"
    _write_json(path, binding)
    mismatched = authorize(_authorized_config(detached_binding_file=str(path)))
    assert mismatched.reason == expected["field_reason"]


def test_run_config_has_no_cross_role_construction_guard() -> None:
    fixture = load_runner_fixture("run_config_protocol.json")
    golden = load_runner_fixture("acceptance_record_identity_golden.json")
    same = golden["expected"]["file_bytes"]
    config = _authorized_config(
        acceptance_record_file_sha256=same,
        acceptance_identity_sha256=same,
    )
    assert isinstance(config, RunConfig)
    assert fixture["forbidden"]["cross_role_construction_guard"]
    result = authorize(config)
    assert result.status == "REFUSED"
    assert result.reason == "ACCEPTANCE_IDENTITY_NOT_THE_BOUND_IDENTITY"


def test_run_config_rejects_unfrozen_protocol_value() -> None:
    fixture = load_runner_fixture("run_config_protocol.json")
    try:
        _authorized_config(
            horizon_return_rows=fixture["expected"]["wrong_horizon_return_rows"]
        )
    except ValueError:
        return
    raise AssertionError("unfrozen protocol value must fail construction")


def test_authorize_has_no_defaults() -> None:
    for function in (authorize, result_bearing_refusal_reason):
        for parameter in inspect.signature(function).parameters.values():
            assert parameter.default is inspect.Parameter.empty
    assert "acceptance_record_sha256" in IDENTITY_EXCLUDE


def test_planning_grant_authorizes_code_path_not_result_bearing() -> None:
    fixture = load_runner_fixture("grant_result_bearing_refusal.json")
    expected = fixture["expected"]
    result = authorize(_authorized_config())
    assert result.status == expected["authorization_status"]
    assert result.grant is not None
    assert result.grant["now_eligible"] == expected["now_eligible"]
    assert expected["reason"] == result_bearing_refusal_reason(result.grant)
    assert fixture["forbidden"]["authorize_result_bearing_run"]


def test_calendar_mutation_refuses_before_authorized(tmp_path: Path) -> None:
    fixture = load_runner_fixture("calendar_binding_mutation.json")
    expected = fixture["expected"]
    inputs = fixture["inputs"]
    calendar_id = authorize(
        _authorized_config(calendar_id=inputs["wrong_calendar_id"])
    )
    assert calendar_id.status == expected["status"]
    assert calendar_id.reason == expected["calendar_id_reason"]
    calendar_version = authorize(
        _authorized_config(calendar_version=inputs["wrong_calendar_version"])
    )
    assert calendar_version.status == expected["status"]
    assert calendar_version.reason == expected["calendar_version_reason"]
    binding = json.loads(
        fixture_file("precondition/binding_valid.json").read_text(encoding="utf-8")
    )
    binding["calendar_id"] = inputs["wrong_calendar_id"]
    id_path = tmp_path / "binding_calendar_id.json"
    _write_json(id_path, binding)
    binding_id = authorize(_authorized_config(detached_binding_file=str(id_path)))
    assert binding_id.status == expected["status"]
    assert binding_id.reason == expected["binding_field_reason"]
    binding["calendar_id"] = _authorized_config().calendar_id
    binding["calendar_version"] = inputs["wrong_calendar_version"]
    version_path = tmp_path / "binding_calendar_version.json"
    _write_json(version_path, binding)
    binding_version = authorize(
        _authorized_config(detached_binding_file=str(version_path))
    )
    assert binding_version.status == expected["status"]
    assert binding_version.reason == expected["binding_field_reason"]
    assert fixture["forbidden"]["authorize_altered_calendar"]


def test_missing_or_unreadable_authorization_inputs_refuse(
    tmp_path: Path,
) -> None:
    fixture = load_runner_fixture("authorization_unreadable_inputs.json")
    expected = fixture["expected"]
    missing = tmp_path / fixture["inputs"]["missing_name"]
    unreadable = tmp_path / fixture["inputs"]["unreadable_name"]
    unreadable.mkdir()
    for case in fixture["inputs"]["cases"]:
        absent = authorize(
            _authorized_config(**{case["config_field"]: str(missing)})
        )
        assert absent.status == expected["status"], case
        assert absent.reason == case["reason"], case
        blocked = authorize(
            _authorized_config(**{case["config_field"]: str(unreadable)})
        )
        assert blocked.status == expected["status"], case
        assert blocked.reason == case["reason"], case
    assert fixture["forbidden"]["raise_oserror"]

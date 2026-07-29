from copy import deepcopy
import hashlib
from importlib import resources
import json
from pathlib import Path

import pytest

from ledger.schema_registry import (
    LedgerSchemaError,
    load_default_registry,
    load_registry_release,
    registry_digest,
    run_conformance_vectors,
    validate_event,
    validate_raw_event_bytes,
    validate_registry,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = PROJECT_ROOT / "src/ledger/schemas"
R0_REGISTRY_PATH = (
    SCHEMA_ROOT / "experiment_trial_ledger_payload_schema_registry_v1.json"
)
R1_REGISTRY_PATH = (
    SCHEMA_ROOT / "experiment_trial_ledger_payload_schema_registry_v2.json"
)
R2_REGISTRY_PATH = (
    SCHEMA_ROOT / "experiment_trial_ledger_payload_schema_registry_v3.json"
)
R0_DIGEST_PATH = R0_REGISTRY_PATH.with_suffix(".sha256")
R1_DIGEST_PATH = R1_REGISTRY_PATH.with_suffix(".sha256")
R2_DIGEST_PATH = R2_REGISTRY_PATH.with_suffix(".sha256")
FAMILY_FIXTURE_PATH = (
    PROJECT_ROOT
    / "tests/fixtures/"
    "experiment_trial_ledger_trial_family_registration_v1_golden.json"
)

EXPECTED_R0_RAW_SHA256 = (
    "4b78c36647621deaec15114558d827c17dae2bfa29918f4cbf2ceb2aa6b6e6d9"
)
EXPECTED_R0_SIDECAR_RAW_SHA256 = (
    "dc870da2958a107998d3939350edb20d3a9185e13a4edb48664befcb89e79d51"
)
EXPECTED_R1_RAW_SHA256 = (
    "d31b7a812a79618f097a50db0177e63f5246522b3b63590968172e31b71cd499"
)
EXPECTED_R1_SIDECAR_RAW_SHA256 = (
    "ba6b1682d1a22004618c274b362359123ce7abbcb7b211335dcd4c74b1159ac8"
)
EXPECTED_R2_RAW_SHA256 = (
    "1d36c3cc5d608209cb431a9a768a1f95e24cb73f64745199670b175ffa6758dd"
)
EXPECTED_R2_SIDECAR_RAW_SHA256 = (
    "d9491f211a4e7d84777c82cdb6af716f4e4422ed57624a0cbff1f713bc8f8fce"
)
EXPECTED_R1_CANONICAL_SHA256 = (
    "6c1044a1a5d770b8d841164d0232134e975c8c372e7d62333eac3a8ae2eacab4"
)
EXPECTED_R2_CANONICAL_SHA256 = (
    "d0e3c08ed5699c8fd6078afb6d7c0a513bbc20b306bad630b175abd09e695f85"
)
EXPECTED_SUPPORTED_R2_EVENTS = (
    "LEDGER_EPOCH_CREATED",
    "CAMPAIGN_ALLOCATED",
    "EXPERIMENT_ALLOCATED",
    "TRIAL_FAMILY_REGISTERED",
)
EXPECTED_FAMILY_FIELDS = (
    "actor_id",
    "canonicalization_id",
    "event_id",
    "event_schema_version",
    "event_type",
    "identity_projection_id",
    "ledger_id",
    "ledger_schema_version",
    "occurred_at",
    "operation_id",
    "operation_request_projection_id",
    "operation_request_sha256",
    "payload",
    "previous_event_sha256",
    "recorded_at",
    "sequence",
    "subject_id",
    "subject_type",
)
EXPECTED_FAMILY_PAYLOAD_FIELDS = (
    "campaign_scope_ids",
    "family_acceptance_decision_id",
    "family_acceptance_generation",
    "family_acceptance_record_sha256",
    "family_acceptance_schema_version",
    "family_authority_id",
    "family_authority_registry_sha256",
    "family_authority_version",
    "family_definition_canonicalization_id",
    "family_definition_record_id",
    "family_definition_record_sha256",
    "family_definition_record_version",
    "family_definition_schema_version",
)


def _assert_code(code: str, callback) -> None:
    with pytest.raises(LedgerSchemaError) as raised:
        callback()
    assert raised.value.code == code


def _registry() -> dict[str, object]:
    return load_registry_release("0.3.0")


def _fixture() -> dict[str, object]:
    return json.loads(FAMILY_FIXTURE_PATH.read_text(encoding="ascii"))


def _global_event() -> dict[str, object]:
    return deepcopy(_fixture()["global_trial_family_registered"])


def _direct_event() -> dict[str, object]:
    return deepcopy(_fixture()["direct_trial_family_registered"])


def _family_schema(registry: dict[str, object]) -> dict[str, object]:
    return next(
        entry
        for entry in registry["event_schemas"]
        if entry["event_type"] == "TRIAL_FAMILY_REGISTERED"
    )


def test_r1c_release_is_explicit_and_preserves_r0_r1_bytes_and_behavior() -> None:
    r0_registry = load_default_registry()
    r1_registry = load_registry_release("0.2.0")
    r2_registry = _registry()

    assert r0_registry["registry_version"] == "0.1.0"
    assert r1_registry["registry_version"] == "0.2.0"
    assert r2_registry["registry_version"] == "0.3.0"
    assert r2_registry["registry_status"] == "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY"
    assert r2_registry["schema_language_version"] == "0.2.0"
    assert r2_registry["closed_event_vocabulary"] == (
        r1_registry["closed_event_vocabulary"]
    )
    assert tuple(
        entry["event_type"] for entry in r2_registry["event_schemas"]
    ) == EXPECTED_SUPPORTED_R2_EVENTS
    assert r2_registry["event_schemas"][:3] == r1_registry["event_schemas"]
    assert len(r2_registry["incomplete_event_types"]) == 33
    assert set(r2_registry["incomplete_event_types"]).isdisjoint(
        EXPECTED_SUPPORTED_R2_EVENTS
    )
    assert r2_registry["type_definitions"]["trial_family_id"] == {
        "kind": "typed_id",
        "prefix": "fam",
    }
    r2_old_type_definitions = dict(r2_registry["type_definitions"])
    r2_old_type_definitions.pop("trial_family_id")
    assert r2_old_type_definitions == r1_registry["type_definitions"]
    assert registry_digest(r1_registry) == EXPECTED_R1_CANONICAL_SHA256
    assert registry_digest(r2_registry) == EXPECTED_R2_CANONICAL_SHA256
    assert R2_DIGEST_PATH.read_text(encoding="ascii").strip() == (
        EXPECTED_R2_CANONICAL_SHA256
    )

    assert hashlib.sha256(R0_REGISTRY_PATH.read_bytes()).hexdigest() == (
        EXPECTED_R0_RAW_SHA256
    )
    assert hashlib.sha256(R0_DIGEST_PATH.read_bytes()).hexdigest() == (
        EXPECTED_R0_SIDECAR_RAW_SHA256
    )
    assert hashlib.sha256(R1_REGISTRY_PATH.read_bytes()).hexdigest() == (
        EXPECTED_R1_RAW_SHA256
    )
    assert hashlib.sha256(R1_DIGEST_PATH.read_bytes()).hexdigest() == (
        EXPECTED_R1_SIDECAR_RAW_SHA256
    )
    assert hashlib.sha256(R2_REGISTRY_PATH.read_bytes()).hexdigest() == (
        EXPECTED_R2_RAW_SHA256
    )
    assert hashlib.sha256(R2_DIGEST_PATH.read_bytes()).hexdigest() == (
        EXPECTED_R2_SIDECAR_RAW_SHA256
    )

    for old_registry in (r0_registry, r1_registry):
        _assert_code(
            "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY",
            lambda old_registry=old_registry: validate_event(
                _global_event(), registry=old_registry
            ),
        )


def test_r1c_package_resources_match_all_three_source_releases() -> None:
    packaged = resources.files("ledger").joinpath("schemas")
    for path in (
        R0_REGISTRY_PATH,
        R0_DIGEST_PATH,
        R1_REGISTRY_PATH,
        R1_DIGEST_PATH,
        R2_REGISTRY_PATH,
        R2_DIGEST_PATH,
    ):
        assert packaged.joinpath(path.name).read_bytes() == path.read_bytes()


def test_r1c_conformance_vectors_have_literal_expected_outcomes() -> None:
    assert run_conformance_vectors(_registry()) == {
        "epoch_valid": "ACCEPT",
        "campaign_allocated_valid": "ACCEPT",
        "experiment_allocated_valid": "ACCEPT",
        "trial_family_registered_valid": "ACCEPT",
        "trial_family_wrong_namespace": "INVALID_EVENT",
        "epoch_wrong_subject": "INVALID_EVENT",
        "epoch_nonempty_scope": "INVALID_EVENT",
        "known_incomplete_trial": "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY",
        "unknown_event_type": "UNKNOWN_EVENT_TYPE",
        "raw_duplicate_event_type": "DUPLICATE_PROPERTY",
    }


def test_r1c_validates_independent_global_and_direct_fixtures() -> None:
    registry = _registry()
    fixture = _fixture()

    assert fixture["fixture_id"] == (
        "experiment_trial_ledger_trial_family_registration_v1_golden"
    )
    for key in (
        "global_trial_family_registered",
        "direct_trial_family_registered",
    ):
        event = fixture[key]
        assert validate_event(event, registry=registry) == event


def test_r1c_schema_has_literal_subject_scope_and_authority_contract() -> None:
    event_schema = _family_schema(_registry())["event_schema"]
    payload = event_schema["properties"]["payload"]

    assert tuple(event_schema["required"]) == EXPECTED_FAMILY_FIELDS
    assert tuple(event_schema["properties"]) == EXPECTED_FAMILY_FIELDS
    assert tuple(payload["required"]) == EXPECTED_FAMILY_PAYLOAD_FIELDS
    assert tuple(payload["properties"]) == EXPECTED_FAMILY_PAYLOAD_FIELDS
    assert event_schema["properties"]["subject_type"] == {
        "kind": "literal",
        "value": "trial_family",
    }
    assert event_schema["properties"]["subject_id"] == {
        "kind": "named",
        "name": "trial_family_id",
    }
    assert payload["properties"]["campaign_scope_ids"] == {
        "kind": "array",
        "collection_semantics": "sorted_unique",
        "items": {"kind": "named", "name": "campaign_id"},
        "min_items": 0,
        "max_items": 32,
    }
    assert payload["properties"]["family_definition_canonicalization_id"] == {
        "kind": "literal",
        "value": "pit_canonical_json_v1",
    }
    assert payload["properties"]["family_definition_schema_version"] == {
        "kind": "literal",
        "value": "trial_family_definition_v1",
    }
    assert payload["properties"]["family_acceptance_schema_version"] == {
        "kind": "literal",
        "value": "trial_family_definition_acceptance_v1",
    }


@pytest.mark.parametrize(
    "event_field",
    EXPECTED_FAMILY_FIELDS,
)
def test_r1c_rejects_every_missing_envelope_field(event_field: str) -> None:
    event = _global_event()
    event.pop(event_field)

    _assert_code(
        "INVALID_EVENT",
        lambda: validate_event(event, registry=_registry()),
    )


@pytest.mark.parametrize(
    "payload_field",
    EXPECTED_FAMILY_PAYLOAD_FIELDS,
)
def test_r1c_rejects_every_missing_payload_field(payload_field: str) -> None:
    event = _global_event()
    event["payload"].pop(payload_field)

    _assert_code(
        "INVALID_EVENT",
        lambda: validate_event(event, registry=_registry()),
    )


def test_r1c_rejects_unknown_fields_at_each_closed_level() -> None:
    top = _global_event()
    top["unexpected"] = "x"
    payload = _global_event()
    payload["payload"]["unexpected"] = "x"

    for event in (top, payload):
        _assert_code(
            "INVALID_EVENT",
            lambda event=event: validate_event(event, registry=_registry()),
        )


@pytest.mark.parametrize(
    "payload_field",
    EXPECTED_FAMILY_PAYLOAD_FIELDS,
)
def test_r1c_raw_parser_rejects_every_duplicate_payload_property(
    payload_field: str,
) -> None:
    event = _global_event()
    raw = json.dumps(event, separators=(",", ":"), ensure_ascii=True)
    encoded_key = json.dumps(payload_field)
    encoded_value = json.dumps(
        event["payload"][payload_field],
        separators=(",", ":"),
        ensure_ascii=True,
    )
    needle = f"{encoded_key}:{encoded_value}"
    raw = raw.replace(needle, f"{needle},{needle}", 1).encode("ascii")

    _assert_code(
        "DUPLICATE_PROPERTY",
        lambda: validate_raw_event_bytes(raw, registry=_registry()),
    )


def test_r1c_raw_parser_rejects_duplicate_envelope_property() -> None:
    event = _global_event()
    raw = json.dumps(event, separators=(",", ":"), ensure_ascii=True)
    needle = '"subject_type":"trial_family"'
    raw = raw.replace(needle, f"{needle},{needle}", 1).encode("ascii")

    _assert_code(
        "DUPLICATE_PROPERTY",
        lambda: validate_raw_event_bytes(raw, registry=_registry()),
    )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("subject_type", "family"),
        ("subject_type", None),
        ("subject_id", "tfm_00000000000000000000000000000024"),
        ("subject_id", "FAM_00000000000000000000000000000024"),
        ("subject_id", "fam_0000000000000000000000000000024"),
        ("subject_id", "fam_0000000000000000000000000000002g"),
        ("subject_id", None),
    ],
)
def test_r1c_rejects_subject_and_namespace_killers(
    field: str, bad_value: object
) -> None:
    event = _global_event()
    event[field] = bad_value

    _assert_code(
        "INVALID_EVENT",
        lambda: validate_event(event, registry=_registry()),
    )


def test_r1c_rejects_redundant_subject_identity_in_payload() -> None:
    event = _global_event()
    event["payload"]["trial_family_id"] = event["subject_id"]

    _assert_code(
        "INVALID_EVENT",
        lambda: validate_event(event, registry=_registry()),
    )


def test_r1c_scope_accepts_zero_and_32_but_rejects_33_items() -> None:
    global_event = _global_event()
    direct_32 = _direct_event()
    direct_32["payload"]["campaign_scope_ids"] = [
        f"cmp_{index:032x}" for index in range(1, 33)
    ]
    direct_33 = deepcopy(direct_32)
    direct_33["payload"]["campaign_scope_ids"].append(
        "cmp_00000000000000000000000000000021"
    )

    assert validate_event(global_event, registry=_registry()) == global_event
    assert validate_event(direct_32, registry=_registry()) == direct_32
    _assert_code(
        "INVALID_EVENT",
        lambda: validate_event(direct_33, registry=_registry()),
    )


@pytest.mark.parametrize(
    "scope",
    [
        [
            "cmp_00000000000000000000000000000029",
            "cmp_00000000000000000000000000000028",
        ],
        [
            "cmp_00000000000000000000000000000028",
            "cmp_00000000000000000000000000000028",
        ],
        ["exp_00000000000000000000000000000028"],
        ["CMP_00000000000000000000000000000028"],
        None,
        True,
        "cmp_00000000000000000000000000000028",
        {},
    ],
)
def test_r1c_rejects_scope_order_uniqueness_namespace_and_type(
    scope: object,
) -> None:
    event = _direct_event()
    event["payload"]["campaign_scope_ids"] = scope

    _assert_code(
        "INVALID_EVENT",
        lambda: validate_event(event, registry=_registry()),
    )


@pytest.mark.parametrize(
    "field",
    [
        "family_authority_id",
        "family_definition_record_id",
        "family_acceptance_decision_id",
    ],
)
@pytest.mark.parametrize(
    "bad_value",
    [
        "",
        "Uppercase",
        "has space",
        "has/slash",
        "has\\backslash",
        "has:colon",
        "has?query",
        "has#fragment",
        "has%escape",
        "has@sign",
        "nonascii-\u00e9",
        "a" * 129,
        None,
        True,
    ],
)
def test_r1c_rejects_unsafe_authority_record_and_decision_ids(
    field: str, bad_value: object
) -> None:
    event = _global_event()
    event["payload"][field] = bad_value

    _assert_code(
        "INVALID_EVENT",
        lambda: validate_event(event, registry=_registry()),
    )


@pytest.mark.parametrize(
    "field",
    [
        "family_authority_version",
        "family_definition_record_version",
        "family_acceptance_generation",
    ],
)
@pytest.mark.parametrize(
    "bad_value",
    [0, -1, True, False, 1.0, "1", None, 2**53],
)
def test_r1c_rejects_invalid_versions_and_generations(
    field: str, bad_value: object
) -> None:
    event = _global_event()
    event["payload"][field] = bad_value

    _assert_code(
        "INVALID_EVENT",
        lambda: validate_event(event, registry=_registry()),
    )


@pytest.mark.parametrize(
    "field",
    [
        "family_authority_version",
        "family_definition_record_version",
        "family_acceptance_generation",
    ],
)
def test_r1c_accepts_safe_integer_maximum_for_version_fields(field: str) -> None:
    event = _global_event()
    event["payload"][field] = 2**53 - 1

    assert validate_event(event, registry=_registry()) == event


@pytest.mark.parametrize(
    "field",
    [
        "family_authority_registry_sha256",
        "family_definition_record_sha256",
        "family_acceptance_record_sha256",
    ],
)
@pytest.mark.parametrize(
    "bad_value",
    ["A" * 64, "a" * 63, "a" * 65, "g" * 64, "", None, True],
)
def test_r1c_rejects_invalid_authority_record_and_acceptance_digests(
    field: str, bad_value: object
) -> None:
    event = _global_event()
    event["payload"][field] = bad_value

    _assert_code(
        "INVALID_EVENT",
        lambda: validate_event(event, registry=_registry()),
    )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("family_definition_canonicalization_id", "jcs_v1"),
        ("family_definition_canonicalization_id", None),
        ("family_definition_schema_version", "trial_family_definition_v2"),
        ("family_definition_schema_version", None),
        (
            "family_acceptance_schema_version",
            "trial_family_definition_acceptance_v2",
        ),
        ("family_acceptance_schema_version", None),
    ],
)
def test_r1c_rejects_wrong_authority_literal_versions(
    field: str, bad_value: object
) -> None:
    event = _global_event()
    event["payload"][field] = bad_value

    _assert_code(
        "INVALID_EVENT",
        lambda: validate_event(event, registry=_registry()),
    )


def test_r1c_rejects_every_nonpromoted_and_unknown_event_before_action() -> None:
    registry = _registry()
    for event_type in registry["incomplete_event_types"]:
        _assert_code(
            "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY",
            lambda event_type=event_type: validate_event(
                {"event_type": event_type},
                registry=registry,
            ),
        )
    _assert_code(
        "UNKNOWN_EVENT_TYPE",
        lambda: validate_event(
            {"event_type": "NOT_A_LEDGER_EVENT"},
            registry=registry,
        ),
    )


def test_r1c_rejects_self_consistent_unpublished_promotion() -> None:
    promoted = _registry()
    sample_schema = deepcopy(_family_schema(promoted))
    sample_schema["event_type"] = "SAMPLE_REGISTERED"
    sample_schema["event_schema"]["properties"]["event_type"]["value"] = (
        "SAMPLE_REGISTERED"
    )
    promoted["event_schemas"].append(sample_schema)
    promoted["incomplete_event_types"].remove("SAMPLE_REGISTERED")
    forged_vector = deepcopy(promoted["conformance_vectors"][3])
    forged_vector["vector_id"] = "forged_sample_valid"
    forged_vector["value"]["event_type"] = "SAMPLE_REGISTERED"
    promoted["conformance_vectors"].append(forged_vector)

    validate_registry(promoted)
    _assert_code(
        "REGISTRY_DIGEST_MISMATCH",
        lambda: validate_event(forged_vector["value"], registry=promoted),
    )
    _assert_code(
        "REGISTRY_DIGEST_MISMATCH",
        lambda: run_conformance_vectors(promoted),
    )


def test_r1c_digest_is_literal_reordered_and_mutation_sensitive() -> None:
    registry = _registry()
    assert registry_digest(dict(reversed(registry.items()))) == (
        EXPECTED_R2_CANONICAL_SHA256
    )

    mutated = deepcopy(registry)
    mutated["conformance_vectors"][3]["value"]["actor_id"] = (
        "act_00000000000000000000000000000019"
    )
    validate_registry(mutated)
    assert registry_digest(mutated) != EXPECTED_R2_CANONICAL_SHA256

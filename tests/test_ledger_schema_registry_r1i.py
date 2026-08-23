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
from ledger_cross_product import first_full_rest_smoke


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = PROJECT_ROOT / "src/ledger/schemas"
REGISTRY_PATHS = tuple(
    SCHEMA_ROOT
    / f"experiment_trial_ledger_payload_schema_registry_v{version}.json"
    for version in range(1, 10)
)
DIGEST_PATHS = tuple(path.with_suffix(".sha256") for path in REGISTRY_PATHS)
FIXTURE_PATH = (
    PROJECT_ROOT
    / "tests/fixtures/"
    "experiment_trial_ledger_attempt_start_v1_golden.json"
)
CONTRACT_PATH = (
    PROJECT_ROOT
    / "docs/experiment_trial_ledger_attempt_start_schema_contract.md"
)

EXPECTED_RAW_HASHES = (
    "4b78c36647621deaec15114558d827c17dae2bfa29918f4cbf2ceb2aa6b6e6d9",
    "d31b7a812a79618f097a50db0177e63f5246522b3b63590968172e31b71cd499",
    "1d36c3cc5d608209cb431a9a768a1f95e24cb73f64745199670b175ffa6758dd",
    "1562852a4b95f867f7843818f31a0672949afb187ef84291ccac030e105ef46d",
    "223a2b7e2ff8ffdb4977c878186236cd747428838bade571e43e513e71ee52b2",
    "162e20df0b7cfb4e07abb818ccf87160d007eced7f90faeefe0d20831fd7229c",
    "3b90c79f13caa85812d1e42a6964f4d4216632d54cc8c481102945e0127f63c9",
    "455782c8c18f187f0209f2e20af92f10648180dabc422cc0e975d270877bfeff",
    "865b882a4b905158adae8165ca1d4fa66299e2b2d9f889a1ed9f181a8a662525",
)
EXPECTED_SIDECAR_RAW_HASHES = (
    "dc870da2958a107998d3939350edb20d3a9185e13a4edb48664befcb89e79d51",
    "ba6b1682d1a22004618c274b362359123ce7abbcb7b211335dcd4c74b1159ac8",
    "d9491f211a4e7d84777c82cdb6af716f4e4422ed57624a0cbff1f713bc8f8fce",
    "fc34bc6d5183fc977e863fda183b40fd4252bed073cfa04e567cb784aa0b7845",
    "dceb0f334fe2056ae0d3a673e499caa899d69d67b60a21b2380d0ea947427483",
    "8322d6c509797710e5f8d7c85d5406202535b878c88ddf05f83525bbaa83db46",
    "111730a1739e91b2a72efef0e7616b4aee6bafbbf15fe77628f268c19d7f4317",
    "eafd6a98b82ae248c89d94667d278507d43045f8eaf8854cc351d81a95a16c6a",
    "da84c385bd60ef91cf051cc03a53860a3190d23630040fa97d6763d1c03576c9",
)
EXPECTED_CANONICAL_HASHES = (
    "92ab88b0bac4c683c25aab25dd31f6a48f44250afbef7d4995de26b68451e2cf",
    "6c1044a1a5d770b8d841164d0232134e975c8c372e7d62333eac3a8ae2eacab4",
    "d0e3c08ed5699c8fd6078afb6d7c0a513bbc20b306bad630b175abd09e695f85",
    "3a1c17be6dc6d20f512429b4ff2457be4f28472050a99a5f97eee16a9dd57ab4",
    "c6fed9409f596cae5cdba1bce3ad8c5b088d2931361aeda7c06dfd2453805a52",
    "acada613202d7ab3a96380ea70ba9bbfeffe7c401bf998828a39528db3ad8691",
    "1d85424d1ee60dcc9523a52c56b22080b47aebb4275551a7ea9ee38e8e28d710",
    "3c71399f9ee8de51b6bd401dc409865c672d12a97cc00057c6de26445c0c538f",
    "1a58c069098921a8446fd2e0452fe544e7c56e8f9e5ff392ff201cb5c177503a",
)
EXPECTED_SUPPORTED_EVENTS = (
    "LEDGER_EPOCH_CREATED",
    "CAMPAIGN_ALLOCATED",
    "EXPERIMENT_ALLOCATED",
    "TRIAL_FAMILY_REGISTERED",
    "SAMPLE_REGISTERED",
    "CAMPAIGN_ENTITY_BOUND",
    "STAGE3_SAMPLE_REFERENCE_BOUND",
    "TRIAL_ALLOCATED",
    "CAMPAIGN_INVENTORY_SEALED",
    "ATTEMPT_ALLOCATED",
    "ATTEMPT_STARTED",
)
EXPECTED_EVENT_FIELDS = (
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
EXPECTED_PAYLOAD_FIELDS = (
    "attempt_allocation_event_id",
    "attempt_allocation_event_sha256",
    "campaign_scope_ids",
    "execution_capability_id",
    "execution_capability_record_canonicalization_id",
    "execution_capability_record_schema_version",
    "execution_capability_record_sha256",
    "execution_capability_record_version",
    "readiness_authority_id",
    "readiness_authority_registry_sha256",
    "readiness_authority_version",
    "readiness_record_canonicalization_id",
    "readiness_record_id",
    "readiness_record_schema_version",
    "readiness_record_sha256",
    "readiness_record_version",
    "start_authority_generation",
    "start_authority_id",
    "start_authority_record_sha256",
    "start_authority_schema_version",
    "trial_id",
)
SAFE_PUBLIC_FIELDS = (
    "readiness_authority_id",
    "readiness_record_id",
    "start_authority_id",
)
INTEGER_FIELDS = (
    "execution_capability_record_version",
    "readiness_authority_version",
    "readiness_record_version",
    "start_authority_generation",
)
DIGEST_FIELDS = (
    "attempt_allocation_event_sha256",
    "execution_capability_record_sha256",
    "readiness_authority_registry_sha256",
    "readiness_record_sha256",
    "start_authority_record_sha256",
)


def _assert_code(code: str, callback) -> None:
    with pytest.raises(LedgerSchemaError) as raised:
        callback()
    assert raised.value.code == code


def _registry() -> dict[str, object]:
    return load_registry_release("0.9.0")


def _fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="ascii"))


def _event() -> dict[str, object]:
    return deepcopy(_fixture()["attempt_started"])


def _event_schema(
    registry: dict[str, object], event_type: str
) -> dict[str, object]:
    return next(
        entry
        for entry in registry["event_schemas"]
        if entry["event_type"] == event_type
    )


def _start_schema(registry: dict[str, object]) -> dict[str, object]:
    return _event_schema(registry, "ATTEMPT_STARTED")


def test_r1i_release_is_explicit_and_preserves_all_prior_releases() -> None:
    versions = tuple(f"0.{minor}.0" for minor in range(1, 10))
    releases = tuple(load_registry_release(version) for version in versions)
    prior = releases[-2]
    current = releases[-1]

    assert load_default_registry() == releases[0]
    assert tuple(item["registry_version"] for item in releases) == versions
    assert current["registry_status"] == "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY"
    assert current["schema_language_version"] == "0.2.0"
    assert current["closed_event_vocabulary"] == prior["closed_event_vocabulary"]
    assert tuple(
        entry["event_type"] for entry in current["event_schemas"]
    ) == EXPECTED_SUPPORTED_EVENTS
    assert current["event_schemas"][:10] == prior["event_schemas"]
    assert {
        name: schema
        for name, schema in current["type_definitions"].items()
        if name != "execution_capability_id"
    } == prior["type_definitions"]
    assert current["type_definitions"]["execution_capability_id"] == {
        "kind": "typed_id",
        "prefix": "cap",
    }
    assert len(current["incomplete_event_types"]) == 26
    assert set(current["incomplete_event_types"]).isdisjoint(
        EXPECTED_SUPPORTED_EVENTS
    )

    prior_vectors = {
        vector["vector_id"]: vector
        for vector in prior["conformance_vectors"]
    }
    current_vectors = {
        vector["vector_id"]: vector
        for vector in current["conformance_vectors"]
    }
    assert set(current_vectors) - set(prior_vectors) == {
        "attempt_started_valid",
        "attempt_started_wrong_capability_namespace",
        "attempt_started_wrong_readiness_schema",
    }
    assert not (set(prior_vectors) - set(current_vectors))
    for vector_id in prior_vectors:
        assert current_vectors[vector_id] == prior_vectors[vector_id]

    for release, expected in zip(
        releases, EXPECTED_CANONICAL_HASHES, strict=True
    ):
        assert registry_digest(release) == expected
    for path, expected in zip(
        DIGEST_PATHS, EXPECTED_CANONICAL_HASHES, strict=True
    ):
        assert path.read_text(encoding="ascii").strip() == expected
    for path, expected in zip(
        REGISTRY_PATHS, EXPECTED_RAW_HASHES, strict=True
    ):
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
    for path, expected in zip(
        DIGEST_PATHS, EXPECTED_SIDECAR_RAW_HASHES, strict=True
    ):
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected

    for prior_registry in releases[:-1]:
        _assert_code(
            "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY",
            lambda prior_registry=prior_registry: validate_event(
                _event(), registry=prior_registry
            ),
        )


def test_r1i_package_resources_match_all_nine_source_releases() -> None:
    packaged = resources.files("ledger").joinpath("schemas")
    for path in (*REGISTRY_PATHS, *DIGEST_PATHS):
        assert packaged.joinpath(path.name).read_bytes() == path.read_bytes()


def test_r1i_conformance_vectors_have_literal_expected_outcomes() -> None:
    assert run_conformance_vectors(_registry()) == {
        "epoch_valid": "ACCEPT",
        "campaign_allocated_valid": "ACCEPT",
        "experiment_allocated_valid": "ACCEPT",
        "trial_family_registered_valid": "ACCEPT",
        "trial_family_wrong_namespace": "INVALID_EVENT",
        "sample_registered_valid": "ACCEPT",
        "sample_wrong_namespace": "INVALID_EVENT",
        "campaign_entity_bound_trial_family_valid": "ACCEPT",
        "campaign_entity_bound_sample_local_valid": "ACCEPT",
        "stage3_sample_reference_bound_valid": "ACCEPT",
        "campaign_entity_bound_sample_external_valid": "ACCEPT",
        "stage3_sample_reference_wrong_namespace": "INVALID_EVENT",
        "trial_allocated_original_clean_valid": "ACCEPT",
        "trial_allocated_rerun_dirty_valid": "ACCEPT",
        "trial_allocated_wrong_namespace": "INVALID_EVENT",
        "trial_allocated_unknown_relation": "INVALID_EVENT",
        "epoch_wrong_subject": "INVALID_EVENT",
        "epoch_nonempty_scope": "INVALID_EVENT",
        "campaign_inventory_sealed_standard_valid": "ACCEPT",
        "campaign_inventory_sealed_maximum_valid": "ACCEPT",
        "campaign_inventory_sealed_count_too_large": "INVALID_EVENT",
        "attempt_allocated_first_valid": "ACCEPT",
        "attempt_allocated_retry_valid": "ACCEPT",
        "attempt_allocated_wrong_namespace": "INVALID_EVENT",
        "attempt_allocated_unknown_relation": "INVALID_EVENT",
        "attempt_allocated_first_wrong_ordinal": "INVALID_EVENT",
        "attempt_allocated_retry_wrong_ordinal": "INVALID_EVENT",
        "attempt_started_valid": "ACCEPT",
        "attempt_started_wrong_capability_namespace": "INVALID_EVENT",
        "attempt_started_wrong_readiness_schema": "INVALID_EVENT",
        "known_incomplete_amendment_proposed": (
            "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY"
        ),
        "unknown_event_type": "UNKNOWN_EVENT_TYPE",
        "raw_duplicate_event_type": "DUPLICATE_PROPERTY",
    }


def test_r1i_validates_independent_positive_fixture() -> None:
    fixture = _fixture()
    assert fixture["fixture_id"] == (
        "experiment_trial_ledger_attempt_start_v1_golden"
    )
    assert set(fixture) == {"fixture_id", "attempt_started"}
    event = fixture["attempt_started"]
    assert validate_event(event, registry=_registry()) == event


def test_r1i_schema_has_exact_subject_payload_scope_and_namespaces() -> None:
    registry = _registry()
    entry = _start_schema(registry)
    schema = entry["event_schema"]
    payload = schema["properties"]["payload"]
    assert registry["type_definitions"]["attempt_id"] == {
        "kind": "typed_id",
        "prefix": "att",
    }
    assert registry["type_definitions"]["execution_capability_id"] == {
        "kind": "typed_id",
        "prefix": "cap",
    }
    assert schema["kind"] == "closed_object"
    assert tuple(schema["required"]) == EXPECTED_EVENT_FIELDS
    assert tuple(schema["properties"]) == EXPECTED_EVENT_FIELDS
    assert schema["properties"]["event_type"] == {
        "kind": "literal",
        "value": "ATTEMPT_STARTED",
    }
    assert schema["properties"]["subject_type"] == {
        "kind": "literal",
        "value": "attempt",
    }
    assert schema["properties"]["subject_id"] == {
        "kind": "named",
        "name": "attempt_id",
    }
    assert tuple(payload["required"]) == EXPECTED_PAYLOAD_FIELDS
    assert tuple(payload["properties"]) == EXPECTED_PAYLOAD_FIELDS
    assert payload["properties"]["execution_capability_id"] == {
        "kind": "named",
        "name": "execution_capability_id",
    }
    assert payload["properties"]["campaign_scope_ids"] == {
        "kind": "array",
        "collection_semantics": "sorted_unique",
        "items": {"kind": "named", "name": "campaign_id"},
        "min_items": 1,
        "max_items": 1,
    }
    assert entry["local_constraints"] == []


@pytest.mark.parametrize("field", EXPECTED_EVENT_FIELDS)
def test_r1i_rejects_every_missing_envelope_field(field: str) -> None:
    event = _event()
    event.pop(field)
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize("field", EXPECTED_PAYLOAD_FIELDS)
def test_r1i_rejects_every_missing_payload_field(field: str) -> None:
    event = _event()
    event["payload"].pop(field)
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize("path", [(), ("payload",)])
def test_r1i_rejects_unknown_fields_at_every_closed_level(
    path: tuple[str, ...],
) -> None:
    event = _event()
    target = event
    for component in path:
        target = target[component]
    target["unexpected"] = "x"
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize("field", EXPECTED_EVENT_FIELDS)
def test_r1i_raw_parser_rejects_every_duplicate_envelope_property(
    field: str,
) -> None:
    event = _event()
    raw = json.dumps(event, separators=(",", ":"), ensure_ascii=True)
    key = json.dumps(field)
    value = json.dumps(
        event[field], separators=(",", ":"), ensure_ascii=True
    )
    needle = f"{key}:{value}"
    raw = raw.replace(needle, f"{needle},{needle}", 1).encode("ascii")
    _assert_code(
        "DUPLICATE_PROPERTY",
        lambda: validate_raw_event_bytes(raw, registry=_registry()),
    )


@pytest.mark.parametrize("field", EXPECTED_PAYLOAD_FIELDS)
def test_r1i_raw_parser_rejects_every_duplicate_payload_property(
    field: str,
) -> None:
    event = _event()
    raw = json.dumps(event, separators=(",", ":"), ensure_ascii=True)
    key = json.dumps(field)
    value = json.dumps(
        event["payload"][field], separators=(",", ":"), ensure_ascii=True
    )
    needle = f"{key}:{value}"
    raw = raw.replace(needle, f"{needle},{needle}", 1).encode("ascii")
    _assert_code(
        "DUPLICATE_PROPERTY",
        lambda: validate_raw_event_bytes(raw, registry=_registry()),
    )


@pytest.mark.parametrize(
    "bad_scope",
    [
        [],
        [
            "cmp_00000000000000000000000000000001",
            "cmp_00000000000000000000000000000002",
        ],
        ["exp_00000000000000000000000000000001"],
        ["CMP_00000000000000000000000000000001"],
        None,
        True,
        "cmp_00000000000000000000000000000001",
        {},
    ],
)
def test_r1i_rejects_non_singleton_or_wrong_campaign_scope(
    bad_scope: object,
) -> None:
    event = _event()
    event["payload"]["campaign_scope_ids"] = bad_scope
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("subject_id", "trl_000000000000000000000000000000a4"),
        ("subject_id", "ATT_000000000000000000000000000000a4"),
        ("subject_id", "att_00000000000000000000000000000a4"),
        (
            "trial_id",
            "att_000000000000000000000000000000a8",
        ),
        (
            "attempt_allocation_event_id",
            "att_000000000000000000000000000000a5",
        ),
        (
            "execution_capability_id",
            "att_000000000000000000000000000000a7",
        ),
        (
            "execution_capability_id",
            "CAP_000000000000000000000000000000a7",
        ),
    ],
)
def test_r1i_rejects_literal_identity_namespace_killers(
    field: str, bad_value: object
) -> None:
    event = _event()
    if field == "subject_id":
        event[field] = bad_value
    else:
        event["payload"][field] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    first_full_rest_smoke(
        DIGEST_FIELDS,
        ("A" * 64, "a" * 63, "a" * 65, "g" * 64, "", None, True),
    ),
)
def test_r1i_rejects_invalid_payload_digests(
    field: str, bad_value: object
) -> None:
    event = _event()
    event["payload"][field] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    first_full_rest_smoke(
        SAFE_PUBLIC_FIELDS,
        (
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
        ),
    ),
)
def test_r1i_rejects_unsafe_public_reference_ids(
    field: str, bad_value: object
) -> None:
    event = _event()
    event["payload"][field] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    first_full_rest_smoke(
        INTEGER_FIELDS,
        (0, -1, True, False, 1.0, "1", None, 2**53),
    ),
)
def test_r1i_rejects_invalid_versions_and_generations(
    field: str, bad_value: object
) -> None:
    event = _event()
    event["payload"][field] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        (
            "execution_capability_record_canonicalization_id",
            "jcs_v1",
        ),
        (
            "execution_capability_record_schema_version",
            "attempt_execution_capability_record_v2",
        ),
        ("readiness_record_canonicalization_id", "jcs_v1"),
        (
            "readiness_record_schema_version",
            "attempt_start_readiness_record_v2",
        ),
        ("start_authority_schema_version", "attempt_start_authority_v2"),
    ],
)
def test_r1i_rejects_wrong_payload_literals(
    field: str, bad_value: object
) -> None:
    event = _event()
    event["payload"][field] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize(
    "private_field",
    [
        "capability_secret",
        "redemption_handle",
        "private_path",
        "validation_output",
        "performance_value",
    ],
)
def test_r1i_rejects_private_or_result_payload_fields(
    private_field: str,
) -> None:
    event = _event()
    event["payload"][private_field] = "secret"
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


def test_r1i_rejects_redundant_attempt_identity() -> None:
    event = _event()
    event["payload"]["attempt_id"] = event["subject_id"]
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


def test_r1i_shape_valid_stateful_killers_remain_fail_closed() -> None:
    wrong_source = _event()
    wrong_source["payload"]["attempt_allocation_event_id"] = (
        "evt_000000000000000000000000000000ff"
    )
    stale_readiness = _event()
    stale_readiness["payload"]["readiness_record_id"] = (
        "attempt-readiness-record-stale"
    )
    reused_capability = _event()
    reused_capability["payload"]["execution_capability_id"] = (
        "cap_00000000000000000000000000000001"
    )
    for event in (wrong_source, stale_readiness, reused_capability):
        assert validate_event(event, registry=_registry()) == event

    contract = " ".join(CONTRACT_PATH.read_text(encoding="utf-8").split())
    required = (
        "The append and capability-record creation are one atomic transaction.",
        "Exact lost-ack replay of the same `operation_id` and exact "
        "operation-request hash returns the existing start event and the same "
        "capability identity",
        "Exactly one start is permitted per attempt.",
        "These are mandatory stateful authority checks.",
        "Shape-valid events are not evidence that any of them occurred.",
    )
    for text in required:
        assert text in contract


def test_r1i_role_currentness_and_execution_barrier_are_explicit() -> None:
    contract = " ".join(CONTRACT_PATH.read_text(encoding="utf-8").split())
    required = (
        "The reviewer must be distinct from:",
        "The readiness issuer must also be distinct from the executor",
        "It must be current immediately before append.",
        "Execution may begin only after the durable append and one successful "
        "atomic consumption",
        "Only that successful consumer may begin execution.",
        "Private redemption secret/material is prohibited from the event.",
        "Actual allocated-attempt count, started-attempt count, capability "
        "count, execution count, artifact production, and protected-sample "
        "access remain zero.",
    )
    for text in required:
        assert text in contract


def test_r1i_rejects_every_nonpromoted_and_unknown_event_before_action() -> None:
    registry = _registry()
    assert "ATTEMPT_COMPLETED" in registry["incomplete_event_types"]
    assert len(registry["incomplete_event_types"]) == 26
    for event_type in registry["incomplete_event_types"]:
        _assert_code(
            "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY",
            lambda event_type=event_type: validate_event(
                {"event_type": event_type}, registry=registry
            ),
        )
    _assert_code(
        "UNKNOWN_EVENT_TYPE",
        lambda: validate_event(
            {"event_type": "NOT_A_LEDGER_EVENT"}, registry=registry
        ),
    )


def test_r1i_rejects_self_consistent_unpublished_promotion() -> None:
    promoted = _registry()
    terminal = deepcopy(_start_schema(promoted))
    terminal["event_type"] = "ATTEMPT_COMPLETED"
    terminal["event_schema"]["properties"]["event_type"]["value"] = (
        "ATTEMPT_COMPLETED"
    )
    promoted["event_schemas"].append(terminal)
    promoted["incomplete_event_types"].remove("ATTEMPT_COMPLETED")
    forged_vector = {
        "vector_id": "forged_attempt_completed_valid",
        "input_kind": "event_object",
        "expected_code": "ACCEPT",
        "value": _event(),
    }
    forged_vector["value"]["event_type"] = "ATTEMPT_COMPLETED"
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


def test_r1i_digest_is_literal_reordered_and_mutation_sensitive() -> None:
    registry = _registry()
    assert registry_digest(dict(reversed(registry.items()))) == (
        EXPECTED_CANONICAL_HASHES[8]
    )
    mutated = deepcopy(registry)
    mutated["conformance_vectors"][-4]["value"]["actor_id"] = (
        "act_000000000000000000000000000000bc"
    )
    validate_registry(mutated)
    assert registry_digest(mutated) != EXPECTED_CANONICAL_HASHES[8]

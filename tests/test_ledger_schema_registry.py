from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from ledger.schema_registry import (
    LedgerSchemaError,
    canonical_registry_bytes,
    load_default_registry,
    load_registry_bytes,
    parse_json_bytes,
    registry_digest,
    run_conformance_vectors,
    validate_event,
    validate_registry,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = (
    PROJECT_ROOT
    / "src/ledger/schemas/experiment_trial_ledger_payload_schema_registry_v1.json"
)
DIGEST_PATH = REGISTRY_PATH.with_suffix(".sha256")
EXPECTED_REGISTRY_SHA256 = (
    "92ab88b0bac4c683c25aab25dd31f6a48f44250afbef7d4995de26b68451e2cf"
)
EXPECTED_EVENT_TYPES = (
    "LEDGER_EPOCH_CREATED",
    "CAMPAIGN_ALLOCATED",
    "EXPERIMENT_ALLOCATED",
    "TRIAL_FAMILY_REGISTERED",
    "SAMPLE_REGISTERED",
    "CAMPAIGN_ENTITY_BOUND",
    "STAGE3_SAMPLE_REFERENCE_BOUND",
    "TRIAL_ALLOCATED",
    "CAMPAIGN_INVENTORY_SEALED",
    "CAMPAIGN_AMENDMENT_PROPOSED",
    "CAMPAIGN_INVENTORY_AMENDED",
    "ATTEMPT_ALLOCATED",
    "ATTEMPT_STARTED",
    "ATTEMPT_COMPLETED",
    "ATTEMPT_FAILED",
    "ATTEMPT_INVALID",
    "ATTEMPT_ABORTED",
    "TRIAL_COMPLETED",
    "TRIAL_FAILED",
    "TRIAL_INVALID",
    "TRIAL_ABORTED",
    "TRIAL_EXCLUDED",
    "ARTIFACT_DISPOSITION_RECORDED",
    "ACCESS_INTENT",
    "ACCESS_STARTED",
    "ACCESS_COMPLETED",
    "ACCESS_FAILED",
    "ACCESS_ABORTED",
    "ACCESS_CANCELLED",
    "EXPOSURE_DECISION",
    "CAMPAIGN_EVIDENCE_FROZEN",
    "CHECKPOINT_REFERENCE_RECORDED",
    "CAMPAIGN_ACCOUNTING_CLOSED",
    "REVIEW_DECIDED",
    "PROMOTION_DECIDED",
    "CAMPAIGN_ADJUDICATED",
    "EVENT_SUPERSEDED",
)
EPOCH_REQUIRED_FIELDS = (
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


def _valid_epoch(registry: dict[str, object]) -> dict[str, object]:
    vector = next(
        vector
        for vector in registry["conformance_vectors"]
        if vector["vector_id"] == "epoch_valid"
    )
    return deepcopy(vector["value"])


def _assert_code(code: str, callback) -> None:
    with pytest.raises(LedgerSchemaError) as raised:
        callback()
    assert raised.value.code == code


def test_default_registry_is_incomplete_and_covers_vocabulary_once() -> None:
    registry = load_default_registry()

    assert tuple(registry["closed_event_vocabulary"]) == EXPECTED_EVENT_TYPES
    assert registry["registry_status"] == "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY"
    assert [entry["event_type"] for entry in registry["event_schemas"]] == [
        "LEDGER_EPOCH_CREATED"
    ]
    assert tuple(registry["incomplete_event_types"]) == EXPECTED_EVENT_TYPES[1:]
    assert set(registry["incomplete_event_types"]).isdisjoint(
        entry["event_type"] for entry in registry["event_schemas"]
    )

    source = REGISTRY_PATH.read_text(encoding="ascii")
    assert "PAYLOAD_SCHEMA_REGISTRY_ACCEPTED" not in source
    assert "TODO" not in source
    assert "wildcard" not in source.lower()


def test_registry_digest_is_literal_reordered_and_mutation_sensitive() -> None:
    registry = load_default_registry()
    canonical = canonical_registry_bytes(registry)

    assert hashlib.sha256(canonical).hexdigest() == EXPECTED_REGISTRY_SHA256
    assert DIGEST_PATH.read_text(encoding="ascii").strip() == (
        EXPECTED_REGISTRY_SHA256
    )
    assert registry_digest(dict(reversed(registry.items()))) == (
        EXPECTED_REGISTRY_SHA256
    )

    mutated = deepcopy(registry)
    valid_vector = next(
        vector
        for vector in mutated["conformance_vectors"]
        if vector["vector_id"] == "epoch_valid"
    )
    valid_vector["value"]["actor_id"] = (
        "act_00000000000000000000000000000005"
    )
    validate_registry(mutated)
    assert registry_digest(mutated) != EXPECTED_REGISTRY_SHA256


@pytest.mark.parametrize(
    "raw",
    [
        b'{"registry_schema_id":"a","registry_schema_id":"b"}',
        b'{"outer":{"event_type":"A","event_type":"B"}}',
        b'{"items":[{"kind":"literal","kind":"named"}]}',
    ],
)
def test_parser_rejects_duplicate_properties_before_mapping(raw: bytes) -> None:
    _assert_code("DUPLICATE_PROPERTY", lambda: parse_json_bytes(raw))


@pytest.mark.parametrize(
    "mutator",
    [
        lambda value: value.pop("schema_language_id"),
        lambda value: value.update(unexpected=True),
        lambda value: value["closed_event_vocabulary"].append(
            "LEDGER_EPOCH_CREATED"
        ),
        lambda value: value["incomplete_event_types"].append(
            "LEDGER_EPOCH_CREATED"
        ),
        lambda value: value["event_schemas"].append(
            deepcopy(value["event_schemas"][0])
        ),
        lambda value: value["local_constraint_predicates"].append(
            "path_always_true"
        ),
        lambda value: value["event_schemas"][0].update(
            event_schema_version="ledger_event_v2"
        ),
        lambda value: value["event_schemas"][0]["event_schema"].update(
            unexpected={}
        ),
        lambda value: value["type_definitions"].update({1: {"kind": "sha256"}}),
        lambda value: value["type_definitions"].update(
            ledger_id={"kind": "named", "name": "ledger_id"}
        ),
        lambda value: value["type_definitions"]["campaign_id"].update(
            prefix=True
        ),
        lambda value: value["event_schemas"][0]["event_schema"]["properties"][
            "payload"
        ]["properties"]["campaign_scope_ids"].update(min_items=True),
    ],
)
def test_registry_meta_contract_rejects_ambiguous_mutations(mutator) -> None:
    registry = load_default_registry()
    mutator(registry)
    _assert_code("INVALID_REGISTRY", lambda: validate_registry(registry))


@pytest.mark.parametrize(
    "raw",
    [
        b'{"value":1.0}',
        b'{"value":9007199254740992}',
        b'{"value":NaN}',
        b'{"value":' + (b"1" * 5000) + b"}",
        b'{"value":-' + (b"1" * 5000) + b"}",
    ],
)
def test_parser_rejects_non_ijson_numbers(raw: bytes) -> None:
    _assert_code("NON_IJSON_NUMBER", lambda: parse_json_bytes(raw))


def test_registry_bound_conformance_vectors_pass() -> None:
    outcomes = run_conformance_vectors(load_default_registry())

    assert outcomes == {
        "epoch_valid": "ACCEPT",
        "epoch_wrong_subject": "INVALID_EVENT",
        "epoch_nonempty_scope": "INVALID_EVENT",
        "known_incomplete_trial": "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY",
        "unknown_event_type": "UNKNOWN_EVENT_TYPE",
        "raw_duplicate_event_type": "DUPLICATE_PROPERTY",
    }


def test_registry_digest_mismatch_fails_closed() -> None:
    _assert_code(
        "REGISTRY_DIGEST_MISMATCH",
        lambda: load_registry_bytes(
            REGISTRY_PATH.read_bytes(),
            expected_digest="0" * 64,
        ),
    )


def test_event_validation_rejects_self_consistent_unpublished_promotion() -> None:
    promoted = load_default_registry()
    promoted_schema = deepcopy(promoted["event_schemas"][0])
    promoted_schema["event_type"] = "TRIAL_ALLOCATED"
    promoted_schema["event_schema"]["properties"]["event_type"]["value"] = (
        "TRIAL_ALLOCATED"
    )
    promoted["event_schemas"].append(promoted_schema)
    promoted["incomplete_event_types"].remove("TRIAL_ALLOCATED")

    promoted_vector = deepcopy(promoted["conformance_vectors"][0])
    promoted_vector["vector_id"] = "forged_trial_accept"
    promoted_vector["value"]["event_type"] = "TRIAL_ALLOCATED"
    promoted["conformance_vectors"].append(promoted_vector)

    validate_registry(promoted)
    forged_trial = promoted_vector["value"]
    _assert_code(
        "REGISTRY_DIGEST_MISMATCH",
        lambda: validate_event(forged_trial, registry=promoted),
    )
    _assert_code(
        "REGISTRY_DIGEST_MISMATCH",
        lambda: run_conformance_vectors(promoted),
    )


def test_registry_object_keys_cannot_alias_in_canonical_digest() -> None:
    string_key_registry = load_default_registry()
    string_key_registry["type_definitions"]["actor_id"] = {
        "kind": "enum",
        "values": [{"1": "x"}],
    }
    validate_registry(string_key_registry)

    integer_key_registry = deepcopy(string_key_registry)
    integer_key_registry["type_definitions"]["actor_id"]["values"] = [
        {1: "x"}
    ]
    _assert_code(
        "INVALID_REGISTRY",
        lambda: canonical_registry_bytes(integer_key_registry),
    )


def test_event_dispatch_rejects_incomplete_and_unknown_before_action() -> None:
    registry = load_default_registry()

    for event_type in EXPECTED_EVENT_TYPES[1:]:
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
            {"event_type": "UNREGISTERED_EVENT"},
            registry=registry,
        ),
    )


def test_epoch_schema_accepts_stage_four_a_golden_and_rejects_trial_stub() -> None:
    registry = load_default_registry()
    fixture = json.loads(
        (
            PROJECT_ROOT
            / "tests/fixtures/experiment_trial_ledger_event_v1_golden.json"
        ).read_text(encoding="ascii")
    )

    assert validate_event(
        fixture["semantic_input"],
        registry=registry,
    ) == fixture["semantic_input"]
    _assert_code(
        "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY",
        lambda: validate_event(
            fixture["incomplete_trial_allocation_stub"],
            registry=registry,
        ),
    )


@pytest.mark.parametrize(
    "field",
    EPOCH_REQUIRED_FIELDS + ("payload.campaign_scope_ids",),
)
def test_epoch_schema_rejects_each_missing_required_field(field: str) -> None:
    registry = load_default_registry()
    invalid = _valid_epoch(registry)
    if field == "payload.campaign_scope_ids":
        invalid["payload"].pop("campaign_scope_ids")
    else:
        invalid.pop(field)

    _assert_code(
        "INVALID_EVENT",
        lambda: validate_event(invalid, registry=registry),
    )


def test_epoch_schema_rejects_missing_unknown_null_type_and_timing_changes() -> None:
    registry = load_default_registry()
    valid = _valid_epoch(registry)
    assert validate_event(valid, registry=registry) == valid

    invalid_events: list[dict[str, object]] = []

    null_scope = deepcopy(valid)
    null_scope["payload"]["campaign_scope_ids"] = None
    invalid_events.append(null_scope)

    unknown_payload = deepcopy(valid)
    unknown_payload["payload"]["details"] = "not allowed"
    invalid_events.append(unknown_payload)

    bool_sequence = deepcopy(valid)
    bool_sequence["sequence"] = False
    invalid_events.append(bool_sequence)

    nonzero_sequence = deepcopy(valid)
    nonzero_sequence["sequence"] = 1
    invalid_events.append(nonzero_sequence)

    nonnull_previous = deepcopy(valid)
    nonnull_previous["previous_event_sha256"] = "2" * 64
    invalid_events.append(nonnull_previous)

    uppercase_hash = deepcopy(valid)
    uppercase_hash["operation_request_sha256"] = "A" * 64
    invalid_events.append(uppercase_hash)

    invalid_date = deepcopy(valid)
    invalid_date["occurred_at"] = "2026-02-29T00:00:00Z"
    invalid_events.append(invalid_date)

    wrong_subject = deepcopy(valid)
    wrong_subject["subject_id"] = "ldg_00000000000000000000000000000005"
    invalid_events.append(wrong_subject)

    wrong_subject_type = deepcopy(valid)
    wrong_subject_type["subject_type"] = "campaign"
    invalid_events.append(wrong_subject_type)

    for id_field in ("ledger_id", "event_id", "operation_id", "actor_id"):
        wrong_id_prefix = deepcopy(valid)
        bad_id = "bad_00000000000000000000000000000005"
        wrong_id_prefix[id_field] = bad_id
        if id_field == "ledger_id":
            wrong_id_prefix["subject_id"] = bad_id
        invalid_events.append(wrong_id_prefix)

    nonempty_scope = deepcopy(valid)
    nonempty_scope["payload"]["campaign_scope_ids"] = [
        "cmp_00000000000000000000000000000006"
    ]
    invalid_events.append(nonempty_scope)

    unknown_envelope = deepcopy(valid)
    unknown_envelope["metadata"] = {}
    invalid_events.append(unknown_envelope)

    nonstring_envelope_key = deepcopy(valid)
    nonstring_envelope_key[1] = "not allowed"
    invalid_events.append(nonstring_envelope_key)

    for invalid in invalid_events:
        _assert_code(
            "INVALID_EVENT",
            lambda invalid=invalid: validate_event(
                invalid,
                registry=registry,
            ),
        )


def test_registry_artifact_is_ascii_json_and_not_self_digesting() -> None:
    raw = REGISTRY_PATH.read_bytes()
    assert raw.decode("ascii").endswith("\n")
    parsed = json.loads(raw)
    assert "registry_sha256" not in parsed
    assert registry_digest(parsed) == EXPECTED_REGISTRY_SHA256

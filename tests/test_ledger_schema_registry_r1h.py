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
from ledger_cross_product import (
    first_full_rest_smoke,
    registry_field_constraint_kind,
    registry_requiredness_kind,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = PROJECT_ROOT / "src/ledger/schemas"
REGISTRY_PATHS = tuple(
    SCHEMA_ROOT
    / f"experiment_trial_ledger_payload_schema_registry_v{version}.json"
    for version in range(1, 9)
)
DIGEST_PATHS = tuple(path.with_suffix(".sha256") for path in REGISTRY_PATHS)
FIXTURE_PATH = (
    PROJECT_ROOT
    / "tests/fixtures/"
    "experiment_trial_ledger_attempt_allocation_v1_golden.json"
)
CONTRACT_PATH = (
    PROJECT_ROOT
    / "docs/experiment_trial_ledger_attempt_allocation_schema_contract.md"
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
    "allocation_authority_generation",
    "allocation_authority_id",
    "allocation_authority_record_sha256",
    "allocation_authority_schema_version",
    "attempt_plan_acceptance_decision_id",
    "attempt_plan_acceptance_generation",
    "attempt_plan_acceptance_record_sha256",
    "attempt_plan_acceptance_schema_version",
    "attempt_plan_authority_id",
    "attempt_plan_authority_registry_sha256",
    "attempt_plan_authority_version",
    "attempt_plan_record_canonicalization_id",
    "attempt_plan_record_id",
    "attempt_plan_record_schema_version",
    "attempt_plan_record_sha256",
    "attempt_plan_record_version",
    "campaign_inventory_seal_event_id",
    "campaign_inventory_seal_event_sha256",
    "campaign_scope_ids",
    "expected_output_inventory_sha256",
    "relation",
    "trial_allocation_event_id",
    "trial_allocation_event_sha256",
    "trial_id",
)
EXPECTED_FIRST_RELATION_FIELDS = (
    "attempt_kind",
    "attempt_ordinal",
)
EXPECTED_RETRY_RELATION_FIELDS = (
    "attempt_kind",
    "attempt_ordinal",
    "prior_attempt_id",
    "prior_terminal_event_id",
    "prior_terminal_event_sha256",
)
FIXTURE_EVENT_KEYS = (
    "first_attempt_allocated",
    "retry_attempt_allocated",
)
SAFE_PUBLIC_FIELDS = (
    "allocation_authority_id",
    "attempt_plan_acceptance_decision_id",
    "attempt_plan_authority_id",
    "attempt_plan_record_id",
)
INTEGER_FIELDS = (
    "allocation_authority_generation",
    "attempt_plan_acceptance_generation",
    "attempt_plan_authority_version",
    "attempt_plan_record_version",
)
DIGEST_FIELDS = (
    "allocation_authority_record_sha256",
    "attempt_plan_acceptance_record_sha256",
    "attempt_plan_authority_registry_sha256",
    "attempt_plan_record_sha256",
    "campaign_inventory_seal_event_sha256",
    "expected_output_inventory_sha256",
    "trial_allocation_event_sha256",
)


def _assert_code(code: str, callback) -> None:
    with pytest.raises(LedgerSchemaError) as raised:
        callback()
    assert raised.value.code == code


def _registry() -> dict[str, object]:
    return load_registry_release("0.8.0")


def _fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="ascii"))


def _event(key: str = "first_attempt_allocated") -> dict[str, object]:
    return deepcopy(_fixture()[key])


def _event_schema(
    registry: dict[str, object], event_type: str
) -> dict[str, object]:
    return next(
        entry
        for entry in registry["event_schemas"]
        if entry["event_type"] == event_type
    )


def _attempt_schema(registry: dict[str, object]) -> dict[str, object]:
    return _event_schema(registry, "ATTEMPT_ALLOCATED")


def _envelope_requiredness_kind(fixture_key: str) -> object:
    return registry_requiredness_kind(
        _registry(),
        _event(fixture_key),
        tuple((field,) for field in EXPECTED_EVENT_FIELDS),
    )


def _payload_requiredness_kind(fixture_key: str) -> object:
    return registry_requiredness_kind(
        _registry(),
        _event(fixture_key),
        tuple(("payload", field) for field in EXPECTED_PAYLOAD_FIELDS),
    )


def _payload_constraint_kind(field: str) -> object:
    return registry_field_constraint_kind(
        _registry(),
        "ATTEMPT_ALLOCATED",
        ("payload", field),
    )


def test_r1h_release_is_explicit_and_preserves_all_prior_releases() -> None:
    versions = tuple(f"0.{minor}.0" for minor in range(1, 9))
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
    assert current["event_schemas"][:9] == prior["event_schemas"]
    assert {
        name: schema
        for name, schema in current["type_definitions"].items()
        if name != "attempt_id"
    } == prior["type_definitions"]
    assert current["type_definitions"]["attempt_id"] == {
        "kind": "typed_id",
        "prefix": "att",
    }
    assert len(current["incomplete_event_types"]) == 27
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
        "attempt_allocated_first_valid",
        "attempt_allocated_retry_valid",
        "attempt_allocated_wrong_namespace",
        "attempt_allocated_unknown_relation",
        "attempt_allocated_first_wrong_ordinal",
        "attempt_allocated_retry_wrong_ordinal",
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
        for key in FIXTURE_EVENT_KEYS:
            _assert_code(
                "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY",
                lambda prior_registry=prior_registry, key=key: validate_event(
                    _event(key), registry=prior_registry
                ),
            )


def test_r1h_package_resources_match_all_eight_source_releases() -> None:
    packaged = resources.files("ledger").joinpath("schemas")
    for path in (*REGISTRY_PATHS, *DIGEST_PATHS):
        assert packaged.joinpath(path.name).read_bytes() == path.read_bytes()


def test_r1h_conformance_vectors_have_literal_expected_outcomes() -> None:
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
        "known_incomplete_amendment_proposed": (
            "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY"
        ),
        "unknown_event_type": "UNKNOWN_EVENT_TYPE",
        "raw_duplicate_event_type": "DUPLICATE_PROPERTY",
    }


def test_r1h_validates_independent_first_and_retry_fixtures() -> None:
    fixture = _fixture()
    assert fixture["fixture_id"] == (
        "experiment_trial_ledger_attempt_allocation_v1_golden"
    )
    assert set(fixture) == {"fixture_id", *FIXTURE_EVENT_KEYS}
    for key in FIXTURE_EVENT_KEYS:
        event = fixture[key]
        assert validate_event(event, registry=_registry()) == event


def test_r1h_schema_has_exact_subject_payload_scope_and_namespace() -> None:
    registry = _registry()
    entry = _attempt_schema(registry)
    schema = entry["event_schema"]
    payload = schema["properties"]["payload"]
    assert registry["type_definitions"]["attempt_id"] == {
        "kind": "typed_id",
        "prefix": "att",
    }
    assert schema["kind"] == "closed_object"
    assert tuple(schema["required"]) == EXPECTED_EVENT_FIELDS
    assert tuple(schema["properties"]) == EXPECTED_EVENT_FIELDS
    assert schema["properties"]["event_type"] == {
        "kind": "literal",
        "value": "ATTEMPT_ALLOCATED",
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
    assert payload["properties"]["campaign_scope_ids"] == {
        "kind": "array",
        "collection_semantics": "sorted_unique",
        "items": {"kind": "named", "name": "campaign_id"},
        "min_items": 1,
        "max_items": 1,
    }
    assert entry["local_constraints"] == []


def test_r1h_schema_has_exact_closed_first_and_retry_relations() -> None:
    relation = _attempt_schema(_registry())["event_schema"]["properties"][
        "payload"
    ]["properties"]["relation"]
    assert relation["kind"] == "tagged_union"
    assert relation["discriminator"] == "attempt_kind"
    assert tuple(relation["variants"]) == ("first_attempt", "retry")

    first = relation["variants"]["first_attempt"]
    assert tuple(first["required"]) == EXPECTED_FIRST_RELATION_FIELDS
    assert tuple(first["properties"]) == EXPECTED_FIRST_RELATION_FIELDS
    assert first["properties"]["attempt_kind"] == {
        "kind": "literal",
        "value": "first_attempt",
    }
    assert first["properties"]["attempt_ordinal"] == {
        "kind": "literal",
        "value": 1,
    }

    retry = relation["variants"]["retry"]
    assert tuple(retry["required"]) == EXPECTED_RETRY_RELATION_FIELDS
    assert tuple(retry["properties"]) == EXPECTED_RETRY_RELATION_FIELDS
    assert retry["properties"]["attempt_kind"] == {
        "kind": "literal",
        "value": "retry",
    }
    assert retry["properties"]["attempt_ordinal"] == {
        "kind": "safe_integer",
        "minimum": 2,
    }
    assert retry["properties"]["prior_attempt_id"] == {
        "kind": "named",
        "name": "attempt_id",
    }


@pytest.mark.parametrize(
    ("fixture_key", "field"),
    first_full_rest_smoke(
        FIXTURE_EVENT_KEYS,
        EXPECTED_EVENT_FIELDS,
        constraint_kind=_envelope_requiredness_kind,
    ),
)
def test_r1h_rejects_every_missing_envelope_field(
    fixture_key: str, field: str
) -> None:
    event = _event(fixture_key)
    event.pop(field)
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize(
    ("fixture_key", "field"),
    first_full_rest_smoke(
        FIXTURE_EVENT_KEYS,
        EXPECTED_PAYLOAD_FIELDS,
        constraint_kind=_payload_requiredness_kind,
    ),
)
def test_r1h_rejects_every_missing_payload_field(
    fixture_key: str, field: str
) -> None:
    event = _event(fixture_key)
    event["payload"].pop(field)
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize("field", EXPECTED_FIRST_RELATION_FIELDS)
def test_r1h_rejects_every_missing_first_relation_field(field: str) -> None:
    event = _event("first_attempt_allocated")
    event["payload"]["relation"].pop(field)
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize("field", EXPECTED_RETRY_RELATION_FIELDS)
def test_r1h_rejects_every_missing_retry_relation_field(field: str) -> None:
    event = _event("retry_attempt_allocated")
    event["payload"]["relation"].pop(field)
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize("fixture_key", FIXTURE_EVENT_KEYS)
def test_r1h_rejects_unknown_fields_at_every_closed_level(
    fixture_key: str,
) -> None:
    for path in ((), ("payload",), ("payload", "relation")):
        event = _event(fixture_key)
        target = event
        for component in path:
            target = target[component]
        target["unexpected"] = "x"
        _assert_code(
            "INVALID_EVENT",
            lambda event=event: validate_event(event, registry=_registry()),
        )


@pytest.mark.parametrize("field", EXPECTED_EVENT_FIELDS)
def test_r1h_raw_parser_rejects_every_duplicate_envelope_property(
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
def test_r1h_raw_parser_rejects_every_duplicate_payload_property(
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
    ("fixture_key", "relation_fields"),
    (
        ("first_attempt_allocated", EXPECTED_FIRST_RELATION_FIELDS),
        ("retry_attempt_allocated", EXPECTED_RETRY_RELATION_FIELDS),
    ),
)
def test_r1h_raw_parser_rejects_every_duplicate_relation_property(
    fixture_key: str, relation_fields: tuple[str, ...]
) -> None:
    for field in relation_fields:
        event = _event(fixture_key)
        raw = json.dumps(event, separators=(",", ":"), ensure_ascii=True)
        key = json.dumps(field)
        value = json.dumps(
            event["payload"]["relation"][field],
            separators=(",", ":"),
            ensure_ascii=True,
        )
        needle = f"{key}:{value}"
        raw = raw.replace(needle, f"{needle},{needle}", 1).encode("ascii")
        _assert_code(
            "DUPLICATE_PROPERTY",
            lambda raw=raw: validate_raw_event_bytes(
                raw, registry=_registry()
            ),
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
def test_r1h_rejects_non_singleton_or_wrong_campaign_scope(
    bad_scope: object,
) -> None:
    event = _event()
    event["payload"]["campaign_scope_ids"] = bad_scope
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize(
    "bad_value",
    [
        "attempt-1",
        "ATT_00000000000000000000000000000084",
        "atm_00000000000000000000000000000084",
        "att_0000000000000000000000000000084",
        "att_0000000000000000000000000000008g",
        None,
        True,
    ],
)
def test_r1h_rejects_attempt_subject_namespace_killers(
    bad_value: object,
) -> None:
    event = _event()
    event["subject_id"] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize(
    "bad_value",
    [
        "trial-1",
        "TRL_00000000000000000000000000000086",
        "att_00000000000000000000000000000086",
        "trl_0000000000000000000000000000086",
        "trl_0000000000000000000000000000008g",
        None,
        True,
    ],
)
def test_r1h_rejects_trial_reference_namespace_killers(
    bad_value: object,
) -> None:
    event = _event()
    event["payload"]["trial_id"] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        (
            "campaign_inventory_seal_event_id",
            "trl_00000000000000000000000000000087",
        ),
        (
            "trial_allocation_event_id",
            "cmp_00000000000000000000000000000085",
        ),
    ],
)
def test_r1h_rejects_wrong_source_event_namespaces(
    field: str, bad_value: str
) -> None:
    event = _event()
    event["payload"][field] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    first_full_rest_smoke(
        DIGEST_FIELDS,
        ("A" * 64, "a" * 63, "a" * 65, "g" * 64, "", None, True),
        constraint_kind=_payload_constraint_kind,
    ),
)
def test_r1h_rejects_invalid_payload_digests(
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
        constraint_kind=_payload_constraint_kind,
    ),
)
def test_r1h_rejects_unsafe_public_reference_ids(
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
        constraint_kind=_payload_constraint_kind,
    ),
)
def test_r1h_rejects_invalid_versions_and_generations(
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
            "allocation_authority_schema_version",
            "attempt_allocation_authority_v2",
        ),
        (
            "attempt_plan_acceptance_schema_version",
            "attempt_plan_acceptance_v2",
        ),
        (
            "attempt_plan_record_canonicalization_id",
            "jcs_v1",
        ),
        (
            "attempt_plan_record_schema_version",
            "attempt_plan_record_v2",
        ),
    ],
)
def test_r1h_rejects_wrong_payload_literals(
    field: str, bad_value: object
) -> None:
    event = _event()
    event["payload"][field] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize(
    "bad_ordinal", [0, 2, -1, True, False, 1.0, "1", None, 2**53]
)
def test_r1h_rejects_wrong_first_attempt_ordinals(
    bad_ordinal: object,
) -> None:
    event = _event("first_attempt_allocated")
    event["payload"]["relation"]["attempt_ordinal"] = bad_ordinal
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize(
    "bad_ordinal", [0, 1, -1, True, False, 1.0, "2", None, 2**53]
)
def test_r1h_rejects_wrong_retry_ordinals(bad_ordinal: object) -> None:
    event = _event("retry_attempt_allocated")
    event["payload"]["relation"]["attempt_ordinal"] = bad_ordinal
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize("bad_kind", ["first", "rerun", "", None, True])
def test_r1h_rejects_unknown_or_wrong_relation_kinds(
    bad_kind: object,
) -> None:
    event = _event()
    event["payload"]["relation"]["attempt_kind"] = bad_kind
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


def test_r1h_rejects_cross_branch_relation_fields() -> None:
    first = _event("first_attempt_allocated")
    first["payload"]["relation"]["prior_attempt_id"] = (
        "att_00000000000000000000000000000001"
    )
    retry = _event("retry_attempt_allocated")
    retry["payload"]["relation"].pop("prior_attempt_id")
    for event in (first, retry):
        _assert_code(
            "INVALID_EVENT",
            lambda event=event: validate_event(event, registry=_registry()),
        )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        (
            "prior_attempt_id",
            "trl_0000000000000000000000000000008f",
        ),
        (
            "prior_terminal_event_id",
            "att_00000000000000000000000000000090",
        ),
        ("prior_terminal_event_sha256", "A" * 64),
    ],
)
def test_r1h_rejects_invalid_retry_predecessor_syntax(
    field: str, bad_value: object
) -> None:
    event = _event("retry_attempt_allocated")
    event["payload"]["relation"][field] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


def test_r1h_rejects_redundant_attempt_identity() -> None:
    event = _event()
    event["payload"]["attempt_id"] = event["subject_id"]
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


def test_r1h_shape_valid_stateful_retry_killers_remain_fail_closed() -> None:
    duplicate_predecessor = _event("retry_attempt_allocated")
    duplicate_predecessor["payload"]["relation"]["prior_attempt_id"] = (
        duplicate_predecessor["subject_id"]
    )
    skipped_ordinal = _event("retry_attempt_allocated")
    skipped_ordinal["payload"]["relation"]["attempt_ordinal"] = 5
    assert validate_event(
        duplicate_predecessor, registry=_registry()
    ) == duplicate_predecessor
    assert validate_event(skipped_ordinal, registry=_registry()) == (
        skipped_ordinal
    )

    contract = " ".join(CONTRACT_PATH.read_text(encoding="utf-8").split())
    required = (
        "The first branch is legal only when no attempt has previously been "
        "allocated.",
        "A retry ordinal must equal the exact prior count plus one",
        "Missing predecessors, nonterminal predecessors, later references, "
        "wrong-trial references, duplicate/skipped ordinals",
        "stateful checks rather than local `ACCEPT` evidence",
    )
    for text in required:
        assert text in contract


def test_r1h_role_currentness_and_pre_action_barrier_are_explicit() -> None:
    contract = " ".join(CONTRACT_PATH.read_text(encoding="utf-8").split())
    required = (
        "Its reviewer must be distinct from:",
        "The repository-external authority record binds the exact `actor_id`",
        "the trial allocation exists earlier",
        "the exact initial inventory seal exists earlier",
        "the allocation append durably commits before any validator, "
        "executor, artifact writer, protected accessor",
        "`ATTEMPT_ALLOCATED` is allocation only.",
        "Actual allocated-attempt count, trial execution count, artifact "
        "production, and protected-sample access remain zero.",
    )
    for text in required:
        assert text in contract


def test_r1h_rejects_every_nonpromoted_and_unknown_event_before_action() -> None:
    registry = _registry()
    assert "ATTEMPT_STARTED" in registry["incomplete_event_types"]
    assert len(registry["incomplete_event_types"]) == 27
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


def test_r1h_rejects_self_consistent_unpublished_promotion() -> None:
    promoted = _registry()
    started = deepcopy(_attempt_schema(promoted))
    started["event_type"] = "ATTEMPT_STARTED"
    started["event_schema"]["properties"]["event_type"]["value"] = (
        "ATTEMPT_STARTED"
    )
    promoted["event_schemas"].append(started)
    promoted["incomplete_event_types"].remove("ATTEMPT_STARTED")
    forged_vector = {
        "vector_id": "forged_attempt_started_valid",
        "input_kind": "event_object",
        "expected_code": "ACCEPT",
        "value": _event(),
    }
    forged_vector["value"]["event_type"] = "ATTEMPT_STARTED"
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


def test_r1h_digest_is_literal_reordered_and_mutation_sensitive() -> None:
    registry = _registry()
    assert registry_digest(dict(reversed(registry.items()))) == (
        EXPECTED_CANONICAL_HASHES[7]
    )
    mutated = deepcopy(registry)
    mutated["conformance_vectors"][21]["value"]["actor_id"] = (
        "act_0000000000000000000000000000007c"
    )
    validate_registry(mutated)
    assert registry_digest(mutated) != EXPECTED_CANONICAL_HASHES[7]

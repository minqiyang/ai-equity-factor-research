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
    for version in range(1, 5)
)
DIGEST_PATHS = tuple(path.with_suffix(".sha256") for path in REGISTRY_PATHS)
SAMPLE_FIXTURE_PATH = (
    PROJECT_ROOT
    / "tests/fixtures/experiment_trial_ledger_sample_registration_v1_golden.json"
)

EXPECTED_RAW_HASHES = (
    "4b78c36647621deaec15114558d827c17dae2bfa29918f4cbf2ceb2aa6b6e6d9",
    "d31b7a812a79618f097a50db0177e63f5246522b3b63590968172e31b71cd499",
    "1d36c3cc5d608209cb431a9a768a1f95e24cb73f64745199670b175ffa6758dd",
    "1562852a4b95f867f7843818f31a0672949afb187ef84291ccac030e105ef46d",
)
EXPECTED_SIDECAR_RAW_HASHES = (
    "dc870da2958a107998d3939350edb20d3a9185e13a4edb48664befcb89e79d51",
    "ba6b1682d1a22004618c274b362359123ce7abbcb7b211335dcd4c74b1159ac8",
    "d9491f211a4e7d84777c82cdb6af716f4e4422ed57624a0cbff1f713bc8f8fce",
    "fc34bc6d5183fc977e863fda183b40fd4252bed073cfa04e567cb784aa0b7845",
)
EXPECTED_CANONICAL_HASHES = (
    "92ab88b0bac4c683c25aab25dd31f6a48f44250afbef7d4995de26b68451e2cf",
    "6c1044a1a5d770b8d841164d0232134e975c8c372e7d62333eac3a8ae2eacab4",
    "d0e3c08ed5699c8fd6078afb6d7c0a513bbc20b306bad630b175abd09e695f85",
    "3a1c17be6dc6d20f512429b4ff2457be4f28472050a99a5f97eee16a9dd57ab4",
)
EXPECTED_SUPPORTED_R3_EVENTS = (
    "LEDGER_EPOCH_CREATED",
    "CAMPAIGN_ALLOCATED",
    "EXPERIMENT_ALLOCATED",
    "TRIAL_FAMILY_REGISTERED",
    "SAMPLE_REGISTERED",
)
EXPECTED_SAMPLE_FIELDS = (
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
EXPECTED_SAMPLE_PAYLOAD_FIELDS = (
    "campaign_scope_ids",
    "sample_acceptance_decision_id",
    "sample_acceptance_generation",
    "sample_acceptance_record_sha256",
    "sample_acceptance_schema_version",
    "sample_authority_id",
    "sample_authority_registry_sha256",
    "sample_authority_version",
    "sample_public_projection_id",
    "sample_public_projection_schema_version",
    "sample_public_projection_sha256",
    "sample_publication_approval_generation",
    "sample_publication_approval_id",
    "sample_publication_approval_record_sha256",
    "sample_publication_approval_schema_version",
    "sample_record_canonicalization_id",
    "sample_record_id",
    "sample_record_schema_version",
    "sample_record_sha256",
    "sample_record_version",
)


def _assert_code(code: str, callback) -> None:
    with pytest.raises(LedgerSchemaError) as raised:
        callback()
    assert raised.value.code == code


def _registry() -> dict[str, object]:
    return load_registry_release("0.4.0")


def _fixture() -> dict[str, object]:
    return json.loads(SAMPLE_FIXTURE_PATH.read_text(encoding="ascii"))


def _global_event() -> dict[str, object]:
    return deepcopy(_fixture()["global_sample_registered"])


def _direct_event() -> dict[str, object]:
    return deepcopy(_fixture()["direct_sample_registered"])


def _sample_schema(registry: dict[str, object]) -> dict[str, object]:
    return next(
        entry
        for entry in registry["event_schemas"]
        if entry["event_type"] == "SAMPLE_REGISTERED"
    )


def test_r1d_release_is_explicit_and_preserves_all_prior_releases() -> None:
    releases = tuple(
        load_registry_release(version)
        for version in ("0.1.0", "0.2.0", "0.3.0", "0.4.0")
    )
    r0_registry, r1_registry, r2_registry, r3_registry = releases

    assert load_default_registry() == r0_registry
    assert tuple(release["registry_version"] for release in releases) == (
        "0.1.0",
        "0.2.0",
        "0.3.0",
        "0.4.0",
    )
    assert r3_registry["registry_status"] == "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY"
    assert r3_registry["schema_language_version"] == "0.2.0"
    assert r3_registry["closed_event_vocabulary"] == (
        r2_registry["closed_event_vocabulary"]
    )
    assert tuple(
        entry["event_type"] for entry in r3_registry["event_schemas"]
    ) == EXPECTED_SUPPORTED_R3_EVENTS
    assert r3_registry["event_schemas"][:4] == r2_registry["event_schemas"]
    assert len(r3_registry["incomplete_event_types"]) == 32
    assert set(r3_registry["incomplete_event_types"]).isdisjoint(
        EXPECTED_SUPPORTED_R3_EVENTS
    )
    assert r3_registry["type_definitions"]["sample_id"] == {
        "kind": "typed_id",
        "prefix": "smp",
    }
    prior_types = dict(r3_registry["type_definitions"])
    prior_types.pop("sample_id")
    assert prior_types == r2_registry["type_definitions"]

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

    for prior_registry in (r0_registry, r1_registry, r2_registry):
        _assert_code(
            "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY",
            lambda prior_registry=prior_registry: validate_event(
                _global_event(), registry=prior_registry
            ),
        )


def test_r1d_package_resources_match_all_four_source_releases() -> None:
    packaged = resources.files("ledger").joinpath("schemas")
    for path in (*REGISTRY_PATHS, *DIGEST_PATHS):
        assert packaged.joinpath(path.name).read_bytes() == path.read_bytes()


def test_r1d_conformance_vectors_have_literal_expected_outcomes() -> None:
    assert run_conformance_vectors(_registry()) == {
        "epoch_valid": "ACCEPT",
        "campaign_allocated_valid": "ACCEPT",
        "experiment_allocated_valid": "ACCEPT",
        "trial_family_registered_valid": "ACCEPT",
        "trial_family_wrong_namespace": "INVALID_EVENT",
        "sample_registered_valid": "ACCEPT",
        "sample_wrong_namespace": "INVALID_EVENT",
        "epoch_wrong_subject": "INVALID_EVENT",
        "epoch_nonempty_scope": "INVALID_EVENT",
        "known_incomplete_trial": "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY",
        "unknown_event_type": "UNKNOWN_EVENT_TYPE",
        "raw_duplicate_event_type": "DUPLICATE_PROPERTY",
    }


def test_r1d_validates_independent_global_and_direct_fixtures() -> None:
    fixture = _fixture()
    assert fixture["fixture_id"] == (
        "experiment_trial_ledger_sample_registration_v1_golden"
    )
    for key in ("global_sample_registered", "direct_sample_registered"):
        event = fixture[key]
        assert validate_event(event, registry=_registry()) == event


def test_r1d_schema_has_literal_subject_scope_authority_and_privacy() -> None:
    event_schema = _sample_schema(_registry())["event_schema"]
    payload = event_schema["properties"]["payload"]

    assert tuple(event_schema["required"]) == EXPECTED_SAMPLE_FIELDS
    assert tuple(event_schema["properties"]) == EXPECTED_SAMPLE_FIELDS
    assert tuple(payload["required"]) == EXPECTED_SAMPLE_PAYLOAD_FIELDS
    assert tuple(payload["properties"]) == EXPECTED_SAMPLE_PAYLOAD_FIELDS
    assert event_schema["properties"]["subject_type"] == {
        "kind": "literal",
        "value": "sample",
    }
    assert event_schema["properties"]["subject_id"] == {
        "kind": "named",
        "name": "sample_id",
    }
    assert payload["properties"]["campaign_scope_ids"] == {
        "kind": "array",
        "collection_semantics": "sorted_unique",
        "items": {"kind": "named", "name": "campaign_id"},
        "min_items": 0,
        "max_items": 32,
    }
    literal_fields = {
        "sample_acceptance_schema_version": "stage3_sample_acceptance_v1",
        "sample_public_projection_schema_version": (
            "public_redacted_projection_v1"
        ),
        "sample_publication_approval_schema_version": (
            "sample_public_projection_approval_v1"
        ),
        "sample_record_canonicalization_id": "pit_canonical_json_v1",
        "sample_record_schema_version": "stage3_sample_record_v1",
    }
    for field, expected in literal_fields.items():
        assert payload["properties"][field] == {
            "kind": "literal",
            "value": expected,
        }


@pytest.mark.parametrize("event_field", EXPECTED_SAMPLE_FIELDS)
def test_r1d_rejects_every_missing_envelope_field(event_field: str) -> None:
    event = _global_event()
    event.pop(event_field)
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize("payload_field", EXPECTED_SAMPLE_PAYLOAD_FIELDS)
def test_r1d_rejects_every_missing_payload_field(payload_field: str) -> None:
    event = _global_event()
    event["payload"].pop(payload_field)
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


def test_r1d_rejects_unknown_fields_at_each_closed_level() -> None:
    top = _global_event()
    top["unexpected"] = "x"
    payload = _global_event()
    payload["payload"]["unexpected"] = "x"
    for event in (top, payload):
        _assert_code(
            "INVALID_EVENT",
            lambda event=event: validate_event(event, registry=_registry()),
        )


@pytest.mark.parametrize("payload_field", EXPECTED_SAMPLE_PAYLOAD_FIELDS)
def test_r1d_raw_parser_rejects_every_duplicate_payload_property(
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


def test_r1d_raw_parser_rejects_duplicate_envelope_property() -> None:
    event = _global_event()
    raw = json.dumps(event, separators=(",", ":"), ensure_ascii=True)
    needle = '"subject_type":"sample"'
    raw = raw.replace(needle, f"{needle},{needle}", 1).encode("ascii")
    _assert_code(
        "DUPLICATE_PROPERTY",
        lambda: validate_raw_event_bytes(raw, registry=_registry()),
    )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("subject_type", "dataset_sample"),
        ("subject_type", None),
        ("subject_id", "sam_00000000000000000000000000000034"),
        ("subject_id", "SMP_00000000000000000000000000000034"),
        ("subject_id", "smp_0000000000000000000000000000034"),
        ("subject_id", "smp_0000000000000000000000000000003g"),
        ("subject_id", None),
    ],
)
def test_r1d_rejects_subject_and_namespace_killers(
    field: str, bad_value: object
) -> None:
    event = _global_event()
    event[field] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


def test_r1d_rejects_redundant_subject_identity_in_payload() -> None:
    event = _global_event()
    event["payload"]["sample_id"] = event["subject_id"]
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


def test_r1d_scope_accepts_zero_and_32_but_rejects_33_items() -> None:
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
            "cmp_00000000000000000000000000000039",
            "cmp_00000000000000000000000000000038",
        ],
        [
            "cmp_00000000000000000000000000000038",
            "cmp_00000000000000000000000000000038",
        ],
        ["exp_00000000000000000000000000000038"],
        ["CMP_00000000000000000000000000000038"],
        None,
        True,
        "cmp_00000000000000000000000000000038",
        {},
    ],
)
def test_r1d_rejects_scope_order_uniqueness_namespace_and_type(
    scope: object,
) -> None:
    event = _direct_event()
    event["payload"]["campaign_scope_ids"] = scope
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    first_full_rest_smoke(
        (
            "sample_acceptance_decision_id",
            "sample_authority_id",
            "sample_public_projection_id",
            "sample_publication_approval_id",
            "sample_record_id",
        ),
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
def test_r1d_rejects_unsafe_public_reference_ids(
    field: str, bad_value: object
) -> None:
    event = _global_event()
    event["payload"][field] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    first_full_rest_smoke(
        (
            "sample_acceptance_generation",
            "sample_authority_version",
            "sample_publication_approval_generation",
            "sample_record_version",
        ),
        (0, -1, True, False, 1.0, "1", None, 2**53),
    ),
)
def test_r1d_rejects_invalid_versions_and_generations(
    field: str, bad_value: object
) -> None:
    event = _global_event()
    event["payload"][field] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize(
    "field",
    [
        "sample_acceptance_generation",
        "sample_authority_version",
        "sample_publication_approval_generation",
        "sample_record_version",
    ],
)
def test_r1d_accepts_safe_integer_maximum(field: str) -> None:
    event = _global_event()
    event["payload"][field] = 2**53 - 1
    assert validate_event(event, registry=_registry()) == event


@pytest.mark.parametrize(
    ("field", "bad_value"),
    first_full_rest_smoke(
        (
            "sample_acceptance_record_sha256",
            "sample_authority_registry_sha256",
            "sample_public_projection_sha256",
            "sample_publication_approval_record_sha256",
            "sample_record_sha256",
        ),
        ("A" * 64, "a" * 63, "a" * 65, "g" * 64, "", None, True),
    ),
)
def test_r1d_rejects_invalid_digests(
    field: str, bad_value: object
) -> None:
    event = _global_event()
    event["payload"][field] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("sample_acceptance_schema_version", "stage3_sample_acceptance_v2"),
        (
            "sample_public_projection_schema_version",
            "public_redacted_projection_v2",
        ),
        (
            "sample_publication_approval_schema_version",
            "sample_public_projection_approval_v2",
        ),
        ("sample_record_canonicalization_id", "jcs_v1"),
        ("sample_record_schema_version", "stage3_sample_record_v2"),
        ("sample_record_schema_version", None),
    ],
)
def test_r1d_rejects_wrong_literal_versions(
    field: str, bad_value: object
) -> None:
    event = _global_event()
    event["payload"][field] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


def test_r1d_rejects_every_nonpromoted_and_unknown_event_before_action() -> None:
    registry = _registry()
    assert "CAMPAIGN_ENTITY_BOUND" in registry["incomplete_event_types"]
    assert "STAGE3_SAMPLE_REFERENCE_BOUND" in registry["incomplete_event_types"]
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


def test_r1d_rejects_self_consistent_unpublished_promotion() -> None:
    promoted = _registry()
    binding_schema = deepcopy(_sample_schema(promoted))
    binding_schema["event_type"] = "CAMPAIGN_ENTITY_BOUND"
    binding_schema["event_schema"]["properties"]["event_type"]["value"] = (
        "CAMPAIGN_ENTITY_BOUND"
    )
    promoted["event_schemas"].append(binding_schema)
    promoted["incomplete_event_types"].remove("CAMPAIGN_ENTITY_BOUND")
    forged_vector = deepcopy(promoted["conformance_vectors"][5])
    forged_vector["vector_id"] = "forged_binding_valid"
    forged_vector["value"]["event_type"] = "CAMPAIGN_ENTITY_BOUND"
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


def test_r1d_digest_is_literal_reordered_and_mutation_sensitive() -> None:
    registry = _registry()
    assert registry_digest(dict(reversed(registry.items()))) == (
        EXPECTED_CANONICAL_HASHES[3]
    )
    mutated = deepcopy(registry)
    mutated["conformance_vectors"][5]["value"]["actor_id"] = (
        "act_00000000000000000000000000000019"
    )
    validate_registry(mutated)
    assert registry_digest(mutated) != EXPECTED_CANONICAL_HASHES[3]

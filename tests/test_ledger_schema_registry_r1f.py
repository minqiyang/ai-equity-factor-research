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
REGISTRY_PATHS = tuple(
    SCHEMA_ROOT
    / f"experiment_trial_ledger_payload_schema_registry_v{version}.json"
    for version in range(1, 7)
)
DIGEST_PATHS = tuple(path.with_suffix(".sha256") for path in REGISTRY_PATHS)
FIXTURE_PATH = (
    PROJECT_ROOT
    / "tests/fixtures/"
    "experiment_trial_ledger_trial_allocation_events_v1_golden.json"
)

EXPECTED_RAW_HASHES = (
    "4b78c36647621deaec15114558d827c17dae2bfa29918f4cbf2ceb2aa6b6e6d9",
    "d31b7a812a79618f097a50db0177e63f5246522b3b63590968172e31b71cd499",
    "1d36c3cc5d608209cb431a9a768a1f95e24cb73f64745199670b175ffa6758dd",
    "1562852a4b95f867f7843818f31a0672949afb187ef84291ccac030e105ef46d",
    "223a2b7e2ff8ffdb4977c878186236cd747428838bade571e43e513e71ee52b2",
    "162e20df0b7cfb4e07abb818ccf87160d007eced7f90faeefe0d20831fd7229c",
)
EXPECTED_SIDECAR_RAW_HASHES = (
    "dc870da2958a107998d3939350edb20d3a9185e13a4edb48664befcb89e79d51",
    "ba6b1682d1a22004618c274b362359123ce7abbcb7b211335dcd4c74b1159ac8",
    "d9491f211a4e7d84777c82cdb6af716f4e4422ed57624a0cbff1f713bc8f8fce",
    "fc34bc6d5183fc977e863fda183b40fd4252bed073cfa04e567cb784aa0b7845",
    "dceb0f334fe2056ae0d3a673e499caa899d69d67b60a21b2380d0ea947427483",
    "8322d6c509797710e5f8d7c85d5406202535b878c88ddf05f83525bbaa83db46",
)
EXPECTED_CANONICAL_HASHES = (
    "92ab88b0bac4c683c25aab25dd31f6a48f44250afbef7d4995de26b68451e2cf",
    "6c1044a1a5d770b8d841164d0232134e975c8c372e7d62333eac3a8ae2eacab4",
    "d0e3c08ed5699c8fd6078afb6d7c0a513bbc20b306bad630b175abd09e695f85",
    "3a1c17be6dc6d20f512429b4ff2457be4f28472050a99a5f97eee16a9dd57ab4",
    "c6fed9409f596cae5cdba1bce3ad8c5b088d2931361aeda7c06dfd2453805a52",
    "acada613202d7ab3a96380ea70ba9bbfeffe7c401bf998828a39528db3ad8691",
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
    "campaign_allocation_event_id",
    "campaign_allocation_event_sha256",
    "campaign_scope_ids",
    "code_identity",
    "experiment_allocation_event_id",
    "experiment_allocation_event_sha256",
    "experiment_id",
    "initial_disposition",
    "relation",
    "trial_definition_acceptance_decision_id",
    "trial_definition_acceptance_generation",
    "trial_definition_acceptance_record_sha256",
    "trial_definition_acceptance_schema_version",
    "trial_definition_authority_id",
    "trial_definition_authority_registry_sha256",
    "trial_definition_authority_version",
    "trial_definition_public_projection_id",
    "trial_definition_public_projection_schema_version",
    "trial_definition_public_projection_sha256",
    "trial_definition_publication_approval_generation",
    "trial_definition_publication_approval_id",
    "trial_definition_publication_approval_record_sha256",
    "trial_definition_publication_approval_schema_version",
    "trial_definition_record_canonicalization_id",
    "trial_definition_record_id",
    "trial_definition_record_schema_version",
    "trial_definition_record_sha256",
    "trial_definition_record_version",
    "trial_family_id",
    "trial_family_source_event_id",
    "trial_family_source_event_sha256",
)
FIXTURE_EVENT_KEYS = (
    "original_clean_trial_allocated",
    "rerun_dirty_trial_allocated",
)
SAFE_PUBLIC_PAYLOAD_FIELDS = (
    "allocation_authority_id",
    "trial_definition_acceptance_decision_id",
    "trial_definition_authority_id",
    "trial_definition_public_projection_id",
    "trial_definition_publication_approval_id",
    "trial_definition_record_id",
)
INTEGER_PAYLOAD_FIELDS = (
    "allocation_authority_generation",
    "trial_definition_acceptance_generation",
    "trial_definition_authority_version",
    "trial_definition_publication_approval_generation",
    "trial_definition_record_version",
)
DIGEST_PAYLOAD_FIELDS = (
    "allocation_authority_record_sha256",
    "campaign_allocation_event_sha256",
    "experiment_allocation_event_sha256",
    "trial_definition_acceptance_record_sha256",
    "trial_definition_authority_registry_sha256",
    "trial_definition_public_projection_sha256",
    "trial_definition_publication_approval_record_sha256",
    "trial_definition_record_sha256",
    "trial_family_source_event_sha256",
)
EVENT_ID_PAYLOAD_FIELDS = (
    "campaign_allocation_event_id",
    "experiment_allocation_event_id",
    "trial_family_source_event_id",
)


def _assert_code(code: str, callback) -> None:
    with pytest.raises(LedgerSchemaError) as raised:
        callback()
    assert raised.value.code == code


def _registry() -> dict[str, object]:
    return load_registry_release("0.6.0")


def _fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="ascii"))


def _event(key: str) -> dict[str, object]:
    return deepcopy(_fixture()[key])


def _event_schema(
    registry: dict[str, object], event_type: str
) -> dict[str, object]:
    return next(
        entry
        for entry in registry["event_schemas"]
        if entry["event_type"] == event_type
    )


def _trial_schema(registry: dict[str, object]) -> dict[str, object]:
    return _event_schema(registry, "TRIAL_ALLOCATED")


def _relation_source(kind: str) -> dict[str, object]:
    return {
        "relation_kind": kind,
        "source_trial_allocation_event_id": (
            "evt_00000000000000000000000000000070"
        ),
        "source_trial_allocation_event_sha256": "18" * 32,
        "source_trial_id": "trl_00000000000000000000000000000071",
    }


def test_r1f_release_is_explicit_and_preserves_all_prior_releases() -> None:
    versions = ("0.1.0", "0.2.0", "0.3.0", "0.4.0", "0.5.0", "0.6.0")
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
    assert current["event_schemas"][:7] == prior["event_schemas"]
    assert current["type_definitions"] | {} == {
        **prior["type_definitions"],
        "trial_id": {"kind": "typed_id", "prefix": "trl"},
    }
    assert len(current["incomplete_event_types"]) == 29
    assert set(current["incomplete_event_types"]).isdisjoint(
        EXPECTED_SUPPORTED_EVENTS
    )

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


def test_r1f_package_resources_match_all_six_source_releases() -> None:
    packaged = resources.files("ledger").joinpath("schemas")
    for path in (*REGISTRY_PATHS, *DIGEST_PATHS):
        assert packaged.joinpath(path.name).read_bytes() == path.read_bytes()


def test_r1f_conformance_vectors_have_literal_expected_outcomes() -> None:
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
        "known_incomplete_inventory_seal": (
            "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY"
        ),
        "unknown_event_type": "UNKNOWN_EVENT_TYPE",
        "raw_duplicate_event_type": "DUPLICATE_PROPERTY",
    }


def test_r1f_validates_independent_clean_and_dirty_fixture_paths() -> None:
    fixture = _fixture()
    assert fixture["fixture_id"] == (
        "experiment_trial_ledger_trial_allocation_events_v1_golden"
    )
    assert set(fixture) == {"fixture_id", *FIXTURE_EVENT_KEYS}
    for key in FIXTURE_EVENT_KEYS:
        event = fixture[key]
        assert validate_event(event, registry=_registry()) == event


def test_r1f_schema_has_exact_subject_payload_and_singleton_scope() -> None:
    schema = _trial_schema(_registry())["event_schema"]
    payload = schema["properties"]["payload"]
    assert schema["kind"] == "closed_object"
    assert tuple(schema["required"]) == EXPECTED_EVENT_FIELDS
    assert tuple(schema["properties"]) == EXPECTED_EVENT_FIELDS
    assert schema["properties"]["event_type"] == {
        "kind": "literal",
        "value": "TRIAL_ALLOCATED",
    }
    assert schema["properties"]["subject_type"] == {
        "kind": "literal",
        "value": "trial",
    }
    assert schema["properties"]["subject_id"] == {
        "kind": "named",
        "name": "trial_id",
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
    assert payload["properties"]["initial_disposition"] == {
        "kind": "literal",
        "value": "PLANNED",
    }


def test_r1f_envelope_is_an_exact_r1e_successor() -> None:
    prior = _event_schema(
        load_registry_release("0.5.0"), "STAGE3_SAMPLE_REFERENCE_BOUND"
    )["event_schema"]
    current = _trial_schema(_registry())["event_schema"]
    common = set(EXPECTED_EVENT_FIELDS) - {
        "event_type",
        "payload",
        "subject_id",
        "subject_type",
    }
    for field in common:
        assert current["properties"][field] == prior["properties"][field]


def test_r1f_relation_union_is_literal_and_closed() -> None:
    relation = _trial_schema(_registry())["event_schema"]["properties"][
        "payload"
    ]["properties"]["relation"]
    assert relation["kind"] == "tagged_union"
    assert relation["discriminator"] == "relation_kind"
    assert tuple(relation["variants"]) == (
        "original",
        "child",
        "clone",
        "rerun",
    )
    original = relation["variants"]["original"]
    assert tuple(original["properties"]) == ("relation_kind",)
    assert original["properties"]["relation_kind"] == {
        "kind": "literal",
        "value": "original",
    }
    expected = (
        "relation_kind",
        "source_trial_allocation_event_id",
        "source_trial_allocation_event_sha256",
        "source_trial_id",
    )
    for kind in ("child", "clone", "rerun"):
        branch = relation["variants"][kind]
        assert tuple(branch["required"]) == expected
        assert tuple(branch["properties"]) == expected
        assert branch["properties"]["relation_kind"] == {
            "kind": "literal",
            "value": kind,
        }
        assert branch["properties"]["source_trial_id"] == {
            "kind": "named",
            "name": "trial_id",
        }


def test_r1f_code_identity_union_is_literal_and_closed() -> None:
    code = _trial_schema(_registry())["event_schema"]["properties"]["payload"][
        "properties"
    ]["code_identity"]
    assert code["kind"] == "tagged_union"
    assert code["discriminator"] == "code_identity_kind"
    assert tuple(code["variants"]) == ("clean_commit", "dirty_tree")
    clean = code["variants"]["clean_commit"]
    dirty = code["variants"]["dirty_tree"]
    assert tuple(clean["properties"]) == (
        "code_commit_id",
        "code_identity_kind",
        "code_repository_id",
        "code_tree_sha256",
    )
    assert tuple(dirty["properties"]) == (
        "code_base_commit_id",
        "code_base_tree_sha256",
        "code_identity_kind",
        "code_patch_sha256",
        "code_repository_id",
        "code_resulting_tree_sha256",
    )
    assert clean["properties"]["code_identity_kind"] == {
        "kind": "literal",
        "value": "clean_commit",
    }
    assert dirty["properties"]["code_identity_kind"] == {
        "kind": "literal",
        "value": "dirty_tree",
    }


def test_r1f_accepts_literal_child_and_clone_relation_variants() -> None:
    for kind in ("child", "clone"):
        event = _event("original_clean_trial_allocated")
        event["payload"]["relation"] = _relation_source(kind)
        assert validate_event(event, registry=_registry()) == event


@pytest.mark.parametrize("fixture_key", FIXTURE_EVENT_KEYS)
@pytest.mark.parametrize("event_field", EXPECTED_EVENT_FIELDS)
def test_r1f_rejects_every_missing_envelope_field(
    fixture_key: str, event_field: str
) -> None:
    event = _event(fixture_key)
    event.pop(event_field)
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize("fixture_key", FIXTURE_EVENT_KEYS)
@pytest.mark.parametrize("payload_field", EXPECTED_PAYLOAD_FIELDS)
def test_r1f_rejects_every_missing_payload_field(
    fixture_key: str, payload_field: str
) -> None:
    event = _event(fixture_key)
    event["payload"].pop(payload_field)
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize("fixture_key", FIXTURE_EVENT_KEYS)
def test_r1f_rejects_unknown_fields_at_every_closed_level(
    fixture_key: str,
) -> None:
    paths = (
        (),
        ("payload",),
        ("payload", "relation"),
        ("payload", "code_identity"),
    )
    for path in paths:
        event = _event(fixture_key)
        target = event
        for component in path:
            target = target[component]
        target["unexpected"] = "x"
        _assert_code(
            "INVALID_EVENT",
            lambda event=event: validate_event(event, registry=_registry()),
        )


@pytest.mark.parametrize("event_field", EXPECTED_EVENT_FIELDS)
def test_r1f_raw_parser_rejects_every_duplicate_envelope_property(
    event_field: str,
) -> None:
    event = _event("original_clean_trial_allocated")
    raw = json.dumps(event, separators=(",", ":"), ensure_ascii=True)
    key = json.dumps(event_field)
    value = json.dumps(
        event[event_field], separators=(",", ":"), ensure_ascii=True
    )
    needle = f"{key}:{value}"
    raw = raw.replace(needle, f"{needle},{needle}", 1).encode("ascii")
    _assert_code(
        "DUPLICATE_PROPERTY",
        lambda: validate_raw_event_bytes(raw, registry=_registry()),
    )


@pytest.mark.parametrize("payload_field", EXPECTED_PAYLOAD_FIELDS)
def test_r1f_raw_parser_rejects_every_duplicate_payload_property(
    payload_field: str,
) -> None:
    event = _event("original_clean_trial_allocated")
    raw = json.dumps(event, separators=(",", ":"), ensure_ascii=True)
    key = json.dumps(payload_field)
    value = json.dumps(
        event["payload"][payload_field],
        separators=(",", ":"),
        ensure_ascii=True,
    )
    needle = f"{key}:{value}"
    raw = raw.replace(needle, f"{needle},{needle}", 1).encode("ascii")
    _assert_code(
        "DUPLICATE_PROPERTY",
        lambda: validate_raw_event_bytes(raw, registry=_registry()),
    )


@pytest.mark.parametrize(
    ("fixture_key", "nested_field"),
    [
        ("original_clean_trial_allocated", "relation_kind"),
        ("original_clean_trial_allocated", "code_identity_kind"),
        ("rerun_dirty_trial_allocated", "source_trial_id"),
        ("rerun_dirty_trial_allocated", "code_patch_sha256"),
    ],
)
def test_r1f_raw_parser_rejects_nested_duplicate_properties(
    fixture_key: str, nested_field: str
) -> None:
    event = _event(fixture_key)
    raw = json.dumps(event, separators=(",", ":"), ensure_ascii=True)
    target = (
        event["payload"]["relation"]
        if nested_field in {"relation_kind", "source_trial_id"}
        else event["payload"]["code_identity"]
    )
    key = json.dumps(nested_field)
    value = json.dumps(
        target[nested_field], separators=(",", ":"), ensure_ascii=True
    )
    needle = f"{key}:{value}"
    raw = raw.replace(needle, f"{needle},{needle}", 1).encode("ascii")
    _assert_code(
        "DUPLICATE_PROPERTY",
        lambda: validate_raw_event_bytes(raw, registry=_registry()),
    )


@pytest.mark.parametrize(
    "bad_value",
    [
        "tri_0000000000000000000000000000006a",
        "TRL_0000000000000000000000000000006a",
        "trl_000000000000000000000000000006a",
        "trl_0000000000000000000000000000006g",
        None,
        True,
    ],
)
def test_r1f_rejects_trial_namespace_killers(bad_value: object) -> None:
    event = _event("original_clean_trial_allocated")
    event["subject_id"] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
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
def test_r1f_rejects_non_singleton_or_wrong_campaign_scope(
    bad_scope: object,
) -> None:
    event = _event("original_clean_trial_allocated")
    event["payload"]["campaign_scope_ids"] = bad_scope
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize("field", EVENT_ID_PAYLOAD_FIELDS)
@pytest.mark.parametrize(
    "bad_value",
    [
        "event-1",
        "EVT_00000000000000000000000000000001",
        "evt_0000000000000000000000000000001",
        "evt_0000000000000000000000000000000g",
        None,
        True,
    ],
)
def test_r1f_rejects_invalid_parent_event_ids(
    field: str, bad_value: object
) -> None:
    event = _event("original_clean_trial_allocated")
    event["payload"][field] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("experiment_id", "exm_00000000000000000000000000000001"),
        ("experiment_id", "EXP_00000000000000000000000000000001"),
        ("trial_family_id", "tfm_00000000000000000000000000000001"),
        ("trial_family_id", "FAM_00000000000000000000000000000001"),
        ("experiment_id", None),
        ("trial_family_id", True),
    ],
)
def test_r1f_rejects_wrong_parent_typed_ids(
    field: str, bad_value: object
) -> None:
    event = _event("original_clean_trial_allocated")
    event["payload"][field] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize("field", DIGEST_PAYLOAD_FIELDS)
@pytest.mark.parametrize(
    "bad_value", ["A" * 64, "a" * 63, "a" * 65, "g" * 64, "", None, True]
)
def test_r1f_rejects_invalid_payload_digests(
    field: str, bad_value: object
) -> None:
    event = _event("original_clean_trial_allocated")
    event["payload"][field] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize("field", SAFE_PUBLIC_PAYLOAD_FIELDS)
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
def test_r1f_rejects_unsafe_public_reference_ids(
    field: str, bad_value: object
) -> None:
    event = _event("original_clean_trial_allocated")
    event["payload"][field] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize("field", INTEGER_PAYLOAD_FIELDS)
@pytest.mark.parametrize(
    "bad_value", [0, -1, True, False, 1.0, "1", None, 2**53]
)
def test_r1f_rejects_invalid_versions_and_generations(
    field: str, bad_value: object
) -> None:
    event = _event("original_clean_trial_allocated")
    event["payload"][field] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("initial_disposition", "RUNNING"),
        (
            "allocation_authority_schema_version",
            "trial_allocation_authority_v2",
        ),
        (
            "trial_definition_acceptance_schema_version",
            "trial_definition_acceptance_v2",
        ),
        (
            "trial_definition_public_projection_schema_version",
            "public_redacted_projection_v2",
        ),
        (
            "trial_definition_publication_approval_schema_version",
            "trial_definition_public_projection_approval_v2",
        ),
        ("trial_definition_record_canonicalization_id", "jcs_v1"),
        (
            "trial_definition_record_schema_version",
            "trial_definition_record_v2",
        ),
        ("trial_definition_record_schema_version", None),
    ],
)
def test_r1f_rejects_wrong_literal_versions_and_disposition(
    field: str, bad_value: object
) -> None:
    event = _event("original_clean_trial_allocated")
    event["payload"][field] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize(
    "bad_kind", ["derived", "parent", "", None, True, 1]
)
def test_r1f_rejects_unknown_or_wrong_relation_discriminators(
    bad_kind: object,
) -> None:
    event = _event("original_clean_trial_allocated")
    event["payload"]["relation"]["relation_kind"] = bad_kind
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


def test_r1f_rejects_relation_branch_bleed_and_missing_sources() -> None:
    original = _event("original_clean_trial_allocated")
    original["payload"]["relation"]["source_trial_id"] = (
        "trl_00000000000000000000000000000001"
    )
    rerun = _event("rerun_dirty_trial_allocated")
    rerun["payload"]["relation"].pop("source_trial_id")
    for event in (original, rerun):
        _assert_code(
            "INVALID_EVENT",
            lambda event=event: validate_event(
                event, registry=_registry()
            ),
        )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        (
            "source_trial_id",
            "tri_00000000000000000000000000000001",
        ),
        (
            "source_trial_allocation_event_id",
            "event-1",
        ),
        ("source_trial_allocation_event_sha256", "A" * 64),
        ("source_trial_allocation_event_sha256", None),
    ],
)
def test_r1f_rejects_invalid_relation_source_syntax(
    field: str, bad_value: object
) -> None:
    event = _event("rerun_dirty_trial_allocated")
    event["payload"]["relation"][field] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


def test_r1f_self_source_is_shape_valid_but_statefully_fail_closed() -> None:
    event = _event("rerun_dirty_trial_allocated")
    event["payload"]["relation"]["source_trial_id"] = event["subject_id"]
    assert validate_event(event, registry=_registry()) == event
    contract = (
        PROJECT_ROOT
        / "docs/experiment_trial_ledger_trial_allocation_schema_contract.md"
    ).read_text(encoding="utf-8")
    normalized_contract = " ".join(contract.split())
    assert "Aliases, self-reference, cycles, later sources" in (
        normalized_contract
    )
    assert (
        "shape-valid self-source, cycle, later-source, and changed-source cases"
        in normalized_contract
    )
    assert (
        "local schema `ACCEPT` must not be represented as proof"
        in normalized_contract
    )


@pytest.mark.parametrize(
    "bad_kind", ["clean", "dirty", "", None, True, 1]
)
def test_r1f_rejects_unknown_or_wrong_code_identity_discriminators(
    bad_kind: object,
) -> None:
    event = _event("original_clean_trial_allocated")
    event["payload"]["code_identity"]["code_identity_kind"] = bad_kind
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


def test_r1f_rejects_code_identity_branch_bleed_and_missing_fields() -> None:
    clean = _event("original_clean_trial_allocated")
    clean["payload"]["code_identity"]["code_patch_sha256"] = "a" * 64
    dirty = _event("rerun_dirty_trial_allocated")
    dirty["payload"]["code_identity"].pop("code_patch_sha256")
    for event in (clean, dirty):
        _assert_code(
            "INVALID_EVENT",
            lambda event=event: validate_event(
                event, registry=_registry()
            ),
        )


@pytest.mark.parametrize(
    ("fixture_key", "field", "bad_value"),
    [
        ("original_clean_trial_allocated", "code_repository_id", "Has Space"),
        ("original_clean_trial_allocated", "code_commit_id", "bad/ref"),
        ("original_clean_trial_allocated", "code_tree_sha256", "A" * 64),
        ("rerun_dirty_trial_allocated", "code_base_commit_id", "bad/ref"),
        ("rerun_dirty_trial_allocated", "code_base_tree_sha256", "a" * 63),
        ("rerun_dirty_trial_allocated", "code_patch_sha256", "g" * 64),
        ("rerun_dirty_trial_allocated", "code_resulting_tree_sha256", None),
    ],
)
def test_r1f_rejects_invalid_code_identity_fields(
    fixture_key: str, field: str, bad_value: object
) -> None:
    event = _event(fixture_key)
    event["payload"]["code_identity"][field] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


def test_r1f_rejects_redundant_trial_and_campaign_identity_fields() -> None:
    trial = _event("original_clean_trial_allocated")
    trial["payload"]["trial_id"] = trial["subject_id"]
    campaign = _event("original_clean_trial_allocated")
    campaign["payload"]["campaign_id"] = (
        campaign["payload"]["campaign_scope_ids"][0]
    )
    for event in (trial, campaign):
        _assert_code(
            "INVALID_EVENT",
            lambda event=event: validate_event(
                event, registry=_registry()
            ),
        )


def test_r1f_rejects_every_nonpromoted_and_unknown_event_before_action() -> None:
    registry = _registry()
    assert "CAMPAIGN_INVENTORY_SEALED" in registry["incomplete_event_types"]
    assert len(registry["incomplete_event_types"]) == 29
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


def test_r1f_rejects_self_consistent_unpublished_promotion() -> None:
    promoted = _registry()
    inventory_schema = deepcopy(_trial_schema(promoted))
    inventory_schema["event_type"] = "CAMPAIGN_INVENTORY_SEALED"
    inventory_schema["event_schema"]["properties"]["event_type"]["value"] = (
        "CAMPAIGN_INVENTORY_SEALED"
    )
    promoted["event_schemas"].append(inventory_schema)
    promoted["incomplete_event_types"].remove("CAMPAIGN_INVENTORY_SEALED")
    forged_vector = deepcopy(promoted["conformance_vectors"][12])
    forged_vector["vector_id"] = "forged_inventory_valid"
    forged_vector["value"]["event_type"] = "CAMPAIGN_INVENTORY_SEALED"
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


def test_r1f_digest_is_literal_reordered_and_mutation_sensitive() -> None:
    registry = _registry()
    assert registry_digest(dict(reversed(registry.items()))) == (
        EXPECTED_CANONICAL_HASHES[5]
    )
    mutated = deepcopy(registry)
    mutated["conformance_vectors"][12]["value"]["actor_id"] = (
        "act_00000000000000000000000000000072"
    )
    validate_registry(mutated)
    assert registry_digest(mutated) != EXPECTED_CANONICAL_HASHES[5]

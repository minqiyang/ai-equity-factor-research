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
    for version in range(1, 6)
)
DIGEST_PATHS = tuple(path.with_suffix(".sha256") for path in REGISTRY_PATHS)
BINDING_FIXTURE_PATH = (
    PROJECT_ROOT
    / "tests/fixtures/experiment_trial_ledger_binding_events_v1_golden.json"
)

EXPECTED_RAW_HASHES = (
    "4b78c36647621deaec15114558d827c17dae2bfa29918f4cbf2ceb2aa6b6e6d9",
    "d31b7a812a79618f097a50db0177e63f5246522b3b63590968172e31b71cd499",
    "1d36c3cc5d608209cb431a9a768a1f95e24cb73f64745199670b175ffa6758dd",
    "1562852a4b95f867f7843818f31a0672949afb187ef84291ccac030e105ef46d",
    "223a2b7e2ff8ffdb4977c878186236cd747428838bade571e43e513e71ee52b2",
)
EXPECTED_SIDECAR_RAW_HASHES = (
    "dc870da2958a107998d3939350edb20d3a9185e13a4edb48664befcb89e79d51",
    "ba6b1682d1a22004618c274b362359123ce7abbcb7b211335dcd4c74b1159ac8",
    "d9491f211a4e7d84777c82cdb6af716f4e4422ed57624a0cbff1f713bc8f8fce",
    "fc34bc6d5183fc977e863fda183b40fd4252bed073cfa04e567cb784aa0b7845",
    "dceb0f334fe2056ae0d3a673e499caa899d69d67b60a21b2380d0ea947427483",
)
EXPECTED_CANONICAL_HASHES = (
    "92ab88b0bac4c683c25aab25dd31f6a48f44250afbef7d4995de26b68451e2cf",
    "6c1044a1a5d770b8d841164d0232134e975c8c372e7d62333eac3a8ae2eacab4",
    "d0e3c08ed5699c8fd6078afb6d7c0a513bbc20b306bad630b175abd09e695f85",
    "3a1c17be6dc6d20f512429b4ff2457be4f28472050a99a5f97eee16a9dd57ab4",
    "c6fed9409f596cae5cdba1bce3ad8c5b088d2931361aeda7c06dfd2453805a52",
)
EXPECTED_SUPPORTED_R4_EVENTS = (
    "LEDGER_EPOCH_CREATED",
    "CAMPAIGN_ALLOCATED",
    "EXPERIMENT_ALLOCATED",
    "TRIAL_FAMILY_REGISTERED",
    "SAMPLE_REGISTERED",
    "CAMPAIGN_ENTITY_BOUND",
    "STAGE3_SAMPLE_REFERENCE_BOUND",
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
EXPECTED_FAMILY_BINDING_PAYLOAD_FIELDS = (
    "campaign_scope_ids",
    "source_registration_event_id",
    "source_registration_event_sha256",
)
EXPECTED_LOCAL_SAMPLE_BINDING_PAYLOAD_FIELDS = (
    "campaign_scope_ids",
    "source_kind",
    "source_registration_event_id",
    "source_registration_event_sha256",
)
EXPECTED_EXTERNAL_SAMPLE_BINDING_PAYLOAD_FIELDS = (
    "campaign_scope_ids",
    "source_kind",
    "source_reference_event_id",
    "source_reference_event_sha256",
)
EXPECTED_STAGE3_PAYLOAD_FIELDS = (
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
FIXTURE_EVENT_KEYS = (
    "trial_family_global_bound",
    "sample_global_local_bound",
    "stage3_sample_reference_bound",
    "sample_external_origin_reused",
)


def _assert_code(code: str, callback) -> None:
    with pytest.raises(LedgerSchemaError) as raised:
        callback()
    assert raised.value.code == code


def _registry() -> dict[str, object]:
    return load_registry_release("0.5.0")


def _fixture() -> dict[str, object]:
    return json.loads(BINDING_FIXTURE_PATH.read_text(encoding="ascii"))


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


def _binding_schema(registry: dict[str, object]) -> dict[str, object]:
    return _event_schema(registry, "CAMPAIGN_ENTITY_BOUND")


def _stage3_schema(registry: dict[str, object]) -> dict[str, object]:
    return _event_schema(registry, "STAGE3_SAMPLE_REFERENCE_BOUND")


def test_r1e_release_is_explicit_and_preserves_all_prior_releases() -> None:
    releases = tuple(
        load_registry_release(version)
        for version in ("0.1.0", "0.2.0", "0.3.0", "0.4.0", "0.5.0")
    )
    r0_registry, r1_registry, r2_registry, r3_registry, r4_registry = releases

    assert load_default_registry() == r0_registry
    assert tuple(release["registry_version"] for release in releases) == (
        "0.1.0",
        "0.2.0",
        "0.3.0",
        "0.4.0",
        "0.5.0",
    )
    assert r4_registry["registry_status"] == "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY"
    assert r4_registry["schema_language_version"] == "0.2.0"
    assert r4_registry["closed_event_vocabulary"] == (
        r3_registry["closed_event_vocabulary"]
    )
    assert tuple(
        entry["event_type"] for entry in r4_registry["event_schemas"]
    ) == EXPECTED_SUPPORTED_R4_EVENTS
    assert r4_registry["event_schemas"][:5] == r3_registry["event_schemas"]
    assert r4_registry["type_definitions"] == r3_registry["type_definitions"]
    assert len(r4_registry["incomplete_event_types"]) == 30
    assert set(r4_registry["incomplete_event_types"]).isdisjoint(
        EXPECTED_SUPPORTED_R4_EVENTS
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

    for prior_registry in (
        r0_registry,
        r1_registry,
        r2_registry,
        r3_registry,
    ):
        for key in FIXTURE_EVENT_KEYS:
            _assert_code(
                "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY",
                lambda prior_registry=prior_registry, key=key: validate_event(
                    _event(key), registry=prior_registry
                ),
            )


def test_r1e_package_resources_match_all_five_source_releases() -> None:
    packaged = resources.files("ledger").joinpath("schemas")
    for path in (*REGISTRY_PATHS, *DIGEST_PATHS):
        assert packaged.joinpath(path.name).read_bytes() == path.read_bytes()


def test_r1e_conformance_vectors_have_literal_expected_outcomes() -> None:
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
        "epoch_wrong_subject": "INVALID_EVENT",
        "epoch_nonempty_scope": "INVALID_EVENT",
        "known_incomplete_trial": "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY",
        "unknown_event_type": "UNKNOWN_EVENT_TYPE",
        "raw_duplicate_event_type": "DUPLICATE_PROPERTY",
    }


def test_r1e_validates_four_independent_positive_fixture_paths() -> None:
    fixture = _fixture()
    assert fixture["fixture_id"] == (
        "experiment_trial_ledger_binding_events_v1_golden"
    )
    assert set(fixture) == {"fixture_id", *FIXTURE_EVENT_KEYS}
    for key in FIXTURE_EVENT_KEYS:
        event = fixture[key]
        assert validate_event(event, registry=_registry()) == event


def test_r1e_binding_schema_has_literal_outer_and_nested_unions() -> None:
    event_schema = _binding_schema(_registry())["event_schema"]
    assert event_schema["kind"] == "tagged_union"
    assert event_schema["discriminator"] == "subject_type"
    assert tuple(event_schema["variants"]) == ("trial_family", "sample")

    family = event_schema["variants"]["trial_family"]
    sample = event_schema["variants"]["sample"]
    for branch in (family, sample):
        assert tuple(branch["required"]) == EXPECTED_EVENT_FIELDS
        assert tuple(branch["properties"]) == EXPECTED_EVENT_FIELDS
        assert branch["properties"]["event_type"] == {
            "kind": "literal",
            "value": "CAMPAIGN_ENTITY_BOUND",
        }
    assert family["properties"]["subject_type"] == {
        "kind": "literal",
        "value": "trial_family",
    }
    assert family["properties"]["subject_id"] == {
        "kind": "named",
        "name": "trial_family_id",
    }
    assert sample["properties"]["subject_type"] == {
        "kind": "literal",
        "value": "sample",
    }
    assert sample["properties"]["subject_id"] == {
        "kind": "named",
        "name": "sample_id",
    }

    family_payload = family["properties"]["payload"]
    assert tuple(family_payload["required"]) == (
        EXPECTED_FAMILY_BINDING_PAYLOAD_FIELDS
    )
    assert tuple(family_payload["properties"]) == (
        EXPECTED_FAMILY_BINDING_PAYLOAD_FIELDS
    )

    sample_payload = sample["properties"]["payload"]
    assert sample_payload["kind"] == "tagged_union"
    assert sample_payload["discriminator"] == "source_kind"
    assert tuple(sample_payload["variants"]) == (
        "local_registration",
        "external_reference",
    )
    local = sample_payload["variants"]["local_registration"]
    external = sample_payload["variants"]["external_reference"]
    assert tuple(local["required"]) == (
        EXPECTED_LOCAL_SAMPLE_BINDING_PAYLOAD_FIELDS
    )
    assert tuple(local["properties"]) == (
        EXPECTED_LOCAL_SAMPLE_BINDING_PAYLOAD_FIELDS
    )
    assert tuple(external["required"]) == (
        EXPECTED_EXTERNAL_SAMPLE_BINDING_PAYLOAD_FIELDS
    )
    assert tuple(external["properties"]) == (
        EXPECTED_EXTERNAL_SAMPLE_BINDING_PAYLOAD_FIELDS
    )
    assert local["properties"]["source_kind"] == {
        "kind": "literal",
        "value": "local_registration",
    }
    assert external["properties"]["source_kind"] == {
        "kind": "literal",
        "value": "external_reference",
    }


def test_r1e_binding_branches_have_singleton_scope_and_typed_sources() -> None:
    event_schema = _binding_schema(_registry())["event_schema"]
    family = event_schema["variants"]["trial_family"]
    local = event_schema["variants"]["sample"]["properties"]["payload"][
        "variants"
    ]["local_registration"]
    external = event_schema["variants"]["sample"]["properties"]["payload"][
        "variants"
    ]["external_reference"]
    expected_scope = {
        "kind": "array",
        "collection_semantics": "sorted_unique",
        "items": {"kind": "named", "name": "campaign_id"},
        "min_items": 1,
        "max_items": 1,
    }
    for payload in (family["properties"]["payload"], local, external):
        assert payload["properties"]["campaign_scope_ids"] == expected_scope
    for payload in (family["properties"]["payload"], local):
        assert payload["properties"]["source_registration_event_id"] == {
            "kind": "named",
            "name": "event_id",
        }
        assert payload["properties"]["source_registration_event_sha256"] == {
            "kind": "named",
            "name": "sha256",
        }
    assert external["properties"]["source_reference_event_id"] == {
        "kind": "named",
        "name": "event_id",
    }
    assert external["properties"]["source_reference_event_sha256"] == {
        "kind": "named",
        "name": "sha256",
    }


def test_r1e_stage3_schema_reuses_r1d_tuple_with_singleton_scope() -> None:
    schema = _stage3_schema(_registry())["event_schema"]
    payload = schema["properties"]["payload"]
    assert tuple(schema["required"]) == EXPECTED_EVENT_FIELDS
    assert tuple(schema["properties"]) == EXPECTED_EVENT_FIELDS
    assert tuple(payload["required"]) == EXPECTED_STAGE3_PAYLOAD_FIELDS
    assert tuple(payload["properties"]) == EXPECTED_STAGE3_PAYLOAD_FIELDS
    assert schema["properties"]["subject_type"] == {
        "kind": "literal",
        "value": "sample",
    }
    assert schema["properties"]["subject_id"] == {
        "kind": "named",
        "name": "sample_id",
    }
    assert payload["properties"]["campaign_scope_ids"] == {
        "kind": "array",
        "collection_semantics": "sorted_unique",
        "items": {"kind": "named", "name": "campaign_id"},
        "min_items": 1,
        "max_items": 1,
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


def test_r1e_binding_envelopes_and_stage3_tuple_are_exact_r1d_successors() -> None:
    r1d = load_registry_release("0.4.0")
    r1e = _registry()
    r1d_sample = _event_schema(r1d, "SAMPLE_REGISTERED")["event_schema"]
    binding = _binding_schema(r1e)["event_schema"]
    stage3 = _stage3_schema(r1e)["event_schema"]

    common_fields = set(EXPECTED_EVENT_FIELDS) - {
        "event_type",
        "payload",
        "subject_id",
        "subject_type",
    }
    for branch in binding["variants"].values():
        for field in common_fields:
            assert branch["properties"][field] == (
                r1d_sample["properties"][field]
            )

    expected_stage3 = deepcopy(r1d_sample)
    expected_stage3["properties"]["event_type"]["value"] = (
        "STAGE3_SAMPLE_REFERENCE_BOUND"
    )
    expected_scope = expected_stage3["properties"]["payload"]["properties"][
        "campaign_scope_ids"
    ]
    expected_scope["min_items"] = 1
    expected_scope["max_items"] = 1
    assert stage3 == expected_stage3


@pytest.mark.parametrize(
    ("fixture_key", "event_field"),
    first_full_rest_smoke(FIXTURE_EVENT_KEYS, EXPECTED_EVENT_FIELDS),
)
def test_r1e_rejects_every_missing_envelope_field(
    fixture_key: str, event_field: str
) -> None:
    event = _event(fixture_key)
    event.pop(event_field)
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize(
    ("fixture_key", "payload_fields"),
    [
        (
            "trial_family_global_bound",
            EXPECTED_FAMILY_BINDING_PAYLOAD_FIELDS,
        ),
        (
            "sample_global_local_bound",
            EXPECTED_LOCAL_SAMPLE_BINDING_PAYLOAD_FIELDS,
        ),
        (
            "stage3_sample_reference_bound",
            EXPECTED_STAGE3_PAYLOAD_FIELDS,
        ),
        (
            "sample_external_origin_reused",
            EXPECTED_EXTERNAL_SAMPLE_BINDING_PAYLOAD_FIELDS,
        ),
    ],
)
def test_r1e_rejects_every_missing_payload_field(
    fixture_key: str, payload_fields: tuple[str, ...]
) -> None:
    for payload_field in payload_fields:
        event = _event(fixture_key)
        event["payload"].pop(payload_field)
        _assert_code(
            "INVALID_EVENT",
            lambda event=event: validate_event(event, registry=_registry()),
        )


@pytest.mark.parametrize("fixture_key", FIXTURE_EVENT_KEYS)
def test_r1e_rejects_unknown_fields_at_each_closed_level(
    fixture_key: str,
) -> None:
    top = _event(fixture_key)
    top["unexpected"] = "x"
    payload = _event(fixture_key)
    payload["payload"]["unexpected"] = "x"
    for event in (top, payload):
        _assert_code(
            "INVALID_EVENT",
            lambda event=event: validate_event(event, registry=_registry()),
        )


@pytest.mark.parametrize(
    ("fixture_key", "payload_fields"),
    [
        (
            "trial_family_global_bound",
            EXPECTED_FAMILY_BINDING_PAYLOAD_FIELDS,
        ),
        (
            "sample_global_local_bound",
            EXPECTED_LOCAL_SAMPLE_BINDING_PAYLOAD_FIELDS,
        ),
        (
            "stage3_sample_reference_bound",
            EXPECTED_STAGE3_PAYLOAD_FIELDS,
        ),
        (
            "sample_external_origin_reused",
            EXPECTED_EXTERNAL_SAMPLE_BINDING_PAYLOAD_FIELDS,
        ),
    ],
)
def test_r1e_raw_parser_rejects_every_duplicate_payload_property(
    fixture_key: str, payload_fields: tuple[str, ...]
) -> None:
    for payload_field in payload_fields:
        event = _event(fixture_key)
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
            lambda raw=raw: validate_raw_event_bytes(
                raw, registry=_registry()
            ),
        )


@pytest.mark.parametrize("event_field", EXPECTED_EVENT_FIELDS)
def test_r1e_raw_parser_rejects_every_duplicate_envelope_property(
    event_field: str,
) -> None:
    event = _event("trial_family_global_bound")
    raw = json.dumps(event, separators=(",", ":"), ensure_ascii=True)
    encoded_key = json.dumps(event_field)
    encoded_value = json.dumps(
        event[event_field],
        separators=(",", ":"),
        ensure_ascii=True,
    )
    needle = f"{encoded_key}:{encoded_value}"
    raw = raw.replace(needle, f"{needle},{needle}", 1).encode("ascii")
    _assert_code(
        "DUPLICATE_PROPERTY",
        lambda: validate_raw_event_bytes(raw, registry=_registry()),
    )


@pytest.mark.parametrize(
    ("fixture_key", "field", "bad_value"),
    [
        ("trial_family_global_bound", "subject_type", "sample"),
        ("trial_family_global_bound", "subject_type", "entity"),
        ("trial_family_global_bound", "subject_type", None),
        ("sample_global_local_bound", "subject_type", "trial_family"),
        ("sample_global_local_bound", "subject_type", "entity"),
        ("sample_global_local_bound", "subject_type", None),
        (
            "stage3_sample_reference_bound",
            "subject_type",
            "dataset_sample",
        ),
        ("stage3_sample_reference_bound", "subject_type", None),
    ],
)
def test_r1e_rejects_outer_discriminator_killers(
    fixture_key: str, field: str, bad_value: object
) -> None:
    event = _event(fixture_key)
    event[field] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize(
    ("fixture_key", "bad_value"),
    [
        ("sample_global_local_bound", "external_reference"),
        ("sample_global_local_bound", "unknown"),
        ("sample_global_local_bound", None),
        ("sample_external_origin_reused", "local_registration"),
        ("sample_external_origin_reused", "unknown"),
        ("sample_external_origin_reused", None),
    ],
)
def test_r1e_rejects_nested_source_discriminator_killers(
    fixture_key: str, bad_value: object
) -> None:
    event = _event(fixture_key)
    event["payload"]["source_kind"] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize(
    ("fixture_key", "bad_subject"),
    [
        (
            "trial_family_global_bound",
            "tfm_00000000000000000000000000000043",
        ),
        (
            "trial_family_global_bound",
            "FAM_00000000000000000000000000000043",
        ),
        (
            "trial_family_global_bound",
            "fam_0000000000000000000000000000043",
        ),
        (
            "sample_global_local_bound",
            "sam_00000000000000000000000000000049",
        ),
        (
            "sample_global_local_bound",
            "SMP_00000000000000000000000000000049",
        ),
        (
            "stage3_sample_reference_bound",
            "smp_000000000000000000000000000004e",
        ),
        (
            "stage3_sample_reference_bound",
            "smp_0000000000000000000000000000004g",
        ),
    ],
)
def test_r1e_rejects_subject_namespace_killers(
    fixture_key: str, bad_subject: str
) -> None:
    event = _event(fixture_key)
    event["subject_id"] = bad_subject
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize(
    ("fixture_key", "bad_scope"),
    first_full_rest_smoke(
        FIXTURE_EVENT_KEYS,
        (
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
        ),
    ),
)
def test_r1e_rejects_non_singleton_wrong_namespace_and_wrong_type_scope(
    fixture_key: str, bad_scope: object
) -> None:
    event = _event(fixture_key)
    event["payload"]["campaign_scope_ids"] = bad_scope
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize(
    ("fixture_key", "field", "bad_value"),
    tuple(
        (fixture_key, field, bad_value)
        for (fixture_key, field), bad_value in first_full_rest_smoke(
            (
                ("trial_family_global_bound", "source_registration_event_id"),
                ("sample_global_local_bound", "source_registration_event_id"),
                ("sample_external_origin_reused", "source_reference_event_id"),
            ),
            (
                "event-1",
                "EVT_00000000000000000000000000000001",
                "evt_0000000000000000000000000000001",
                "evt_0000000000000000000000000000000g",
                None,
                True,
            ),
        )
    ),
)
def test_r1e_rejects_invalid_source_event_ids(
    fixture_key: str, field: str, bad_value: object
) -> None:
    event = _event(fixture_key)
    event["payload"][field] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize(
    ("fixture_key", "field", "bad_value"),
    tuple(
        (fixture_key, field, bad_value)
        for (fixture_key, field), bad_value in first_full_rest_smoke(
            (
                (
                    "trial_family_global_bound",
                    "source_registration_event_sha256",
                ),
                (
                    "sample_global_local_bound",
                    "source_registration_event_sha256",
                ),
                (
                    "sample_external_origin_reused",
                    "source_reference_event_sha256",
                ),
            ),
            ("A" * 64, "a" * 63, "a" * 65, "g" * 64, "", None, True),
        )
    ),
)
def test_r1e_rejects_invalid_source_event_digests(
    fixture_key: str, field: str, bad_value: object
) -> None:
    event = _event(fixture_key)
    event["payload"][field] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


@pytest.mark.parametrize(
    ("fixture_key", "extra_field", "extra_value"),
    [
        (
            "trial_family_global_bound",
            "source_kind",
            "local_registration",
        ),
        (
            "trial_family_global_bound",
            "source_reference_event_id",
            "evt_00000000000000000000000000000001",
        ),
        (
            "sample_global_local_bound",
            "source_reference_event_id",
            "evt_00000000000000000000000000000001",
        ),
        (
            "sample_global_local_bound",
            "source_reference_event_sha256",
            "a" * 64,
        ),
        (
            "sample_external_origin_reused",
            "source_registration_event_id",
            "evt_00000000000000000000000000000001",
        ),
        (
            "sample_external_origin_reused",
            "source_registration_event_sha256",
            "a" * 64,
        ),
    ],
)
def test_r1e_rejects_outer_and_nested_branch_field_bleed(
    fixture_key: str, extra_field: str, extra_value: object
) -> None:
    event = _event(fixture_key)
    event["payload"][extra_field] = extra_value
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
def test_r1e_rejects_unsafe_stage3_public_reference_ids(
    field: str, bad_value: object
) -> None:
    event = _event("stage3_sample_reference_bound")
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
def test_r1e_rejects_invalid_stage3_versions_and_generations(
    field: str, bad_value: object
) -> None:
    event = _event("stage3_sample_reference_bound")
    event["payload"][field] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


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
def test_r1e_rejects_invalid_stage3_digests(
    field: str, bad_value: object
) -> None:
    event = _event("stage3_sample_reference_bound")
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
def test_r1e_rejects_wrong_stage3_literal_versions(
    field: str, bad_value: object
) -> None:
    event = _event("stage3_sample_reference_bound")
    event["payload"][field] = bad_value
    _assert_code(
        "INVALID_EVENT", lambda: validate_event(event, registry=_registry())
    )


def test_r1e_rejects_redundant_subject_and_campaign_identity_fields() -> None:
    for key in FIXTURE_EVENT_KEYS:
        subject = _event(key)
        subject["payload"]["sample_id"] = subject["subject_id"]
        campaign = _event(key)
        campaign["payload"]["campaign_id"] = (
            campaign["payload"]["campaign_scope_ids"][0]
        )
        for event in (subject, campaign):
            _assert_code(
                "INVALID_EVENT",
                lambda event=event: validate_event(
                    event, registry=_registry()
                ),
            )


def test_r1e_rejects_every_nonpromoted_and_unknown_event_before_action() -> None:
    registry = _registry()
    assert "TRIAL_ALLOCATED" in registry["incomplete_event_types"]
    assert len(registry["incomplete_event_types"]) == 30
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


def test_r1e_rejects_self_consistent_unpublished_promotion() -> None:
    promoted = _registry()
    binding_schema = deepcopy(_stage3_schema(promoted))
    binding_schema["event_type"] = "TRIAL_ALLOCATED"
    binding_schema["event_schema"]["properties"]["event_type"]["value"] = (
        "TRIAL_ALLOCATED"
    )
    promoted["event_schemas"].append(binding_schema)
    promoted["incomplete_event_types"].remove("TRIAL_ALLOCATED")
    forged_vector = deepcopy(promoted["conformance_vectors"][9])
    forged_vector["vector_id"] = "forged_trial_valid"
    forged_vector["value"]["event_type"] = "TRIAL_ALLOCATED"
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


def test_r1e_digest_is_literal_reordered_and_mutation_sensitive() -> None:
    registry = _registry()
    assert registry_digest(dict(reversed(registry.items()))) == (
        EXPECTED_CANONICAL_HASHES[4]
    )
    mutated = deepcopy(registry)
    mutated["conformance_vectors"][8]["value"]["actor_id"] = (
        "act_00000000000000000000000000000019"
    )
    validate_registry(mutated)
    assert registry_digest(mutated) != EXPECTED_CANONICAL_HASHES[4]

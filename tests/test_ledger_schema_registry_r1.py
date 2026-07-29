from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from ledger.schema_registry import (
    LedgerSchemaError,
    _validate_constraint,
    _validate_schema_node,
    _validate_value,
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
R0_DIGEST_PATH = R0_REGISTRY_PATH.with_suffix(".sha256")
R1_REGISTRY_PATH = (
    SCHEMA_ROOT / "experiment_trial_ledger_payload_schema_registry_v2.json"
)
R1_DIGEST_PATH = R1_REGISTRY_PATH.with_suffix(".sha256")
ALLOCATION_FIXTURE_PATH = (
    PROJECT_ROOT
    / "tests/fixtures/experiment_trial_ledger_allocation_events_v1_golden.json"
)
EXPECTED_R0_CANONICAL_SHA256 = (
    "92ab88b0bac4c683c25aab25dd31f6a48f44250afbef7d4995de26b68451e2cf"
)
EXPECTED_R0_RAW_SHA256 = (
    "4b78c36647621deaec15114558d827c17dae2bfa29918f4cbf2ceb2aa6b6e6d9"
)
EXPECTED_R0_SIDECAR_RAW_SHA256 = (
    "dc870da2958a107998d3939350edb20d3a9185e13a4edb48664befcb89e79d51"
)
EXPECTED_R1_CANONICAL_SHA256 = (
    "6c1044a1a5d770b8d841164d0232134e975c8c372e7d62333eac3a8ae2eacab4"
)
EXPECTED_SUPPORTED_R1_EVENTS = (
    "LEDGER_EPOCH_CREATED",
    "CAMPAIGN_ALLOCATED",
    "EXPERIMENT_ALLOCATED",
)
EXPECTED_ALLOCATION_FIELDS = (
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


def _assert_code(code: str, callback) -> None:
    with pytest.raises(LedgerSchemaError) as raised:
        callback()
    assert raised.value.code == code


def _allocation_fixture() -> dict[str, object]:
    return json.loads(ALLOCATION_FIXTURE_PATH.read_text(encoding="ascii"))


def _r1_registry() -> dict[str, object]:
    return load_registry_release("0.2.0")


def _validate_dsl_schema(schema: object, *, version: str = "0.2.0") -> None:
    referenced_types: set[str] = set()
    _validate_schema_node(
        schema,
        context="test_schema",
        referenced_types=referenced_types,
        schema_language_version=version,
    )
    assert referenced_types == set()


def _validate_dsl_value(schema: object, value: object) -> None:
    _validate_value(
        schema,
        value,
        definitions={},
        context="test_value",
    )


def _tagged_union_schema() -> dict[str, object]:
    return {
        "kind": "tagged_union",
        "discriminator": "entity_kind",
        "variants": {
            "sample": {
                "kind": "closed_object",
                "properties": {
                    "entity_kind": {"kind": "literal", "value": "sample"},
                    "sample_ref": {"kind": "safe_public_id"},
                },
                "required": ["entity_kind", "sample_ref"],
            },
            "trial_family": {
                "kind": "closed_object",
                "properties": {
                    "entity_kind": {
                        "kind": "literal",
                        "value": "trial_family",
                    },
                    "family_ref": {"kind": "safe_public_id"},
                },
                "required": ["entity_kind", "family_ref"],
            },
        },
    }


def _array_constraint_schema(
    *,
    array_item_prefix: str = "cmp",
    scalar_prefix: str = "cmp",
) -> dict[str, object]:
    return {
        "kind": "closed_object",
        "properties": {
            "payload": {
                "kind": "closed_object",
                "properties": {
                    "campaign_scope_ids": {
                        "kind": "array",
                        "collection_semantics": "sorted_unique",
                        "items": {
                            "kind": "typed_id",
                            "prefix": array_item_prefix,
                        },
                        "min_items": 1,
                        "max_items": 1,
                    }
                },
                "required": ["campaign_scope_ids"],
            },
            "subject_id": {"kind": "typed_id", "prefix": scalar_prefix},
        },
        "required": ["payload", "subject_id"],
    }


def _array_contains_constraint() -> dict[str, object]:
    return {
        "constraint_id": "subject_in_scope",
        "predicate": "array_contains_path",
        "left_path": ["payload", "campaign_scope_ids"],
        "right_path": ["subject_id"],
    }


def test_r1_release_is_explicit_and_r0_artifacts_remain_byte_exact() -> None:
    r0_registry = load_default_registry()
    r1_registry = _r1_registry()

    assert r0_registry["registry_version"] == "0.1.0"
    assert r1_registry["registry_version"] == "0.2.0"
    assert r1_registry["schema_language_version"] == "0.2.0"
    assert (
        r1_registry["closed_event_vocabulary"]
        == r0_registry["closed_event_vocabulary"]
    )
    assert tuple(
        entry["event_type"] for entry in r1_registry["event_schemas"]
    ) == EXPECTED_SUPPORTED_R1_EVENTS
    assert r1_registry["event_schemas"][0] == r0_registry["event_schemas"][0]
    assert len(r1_registry["incomplete_event_types"]) == 34
    assert set(r1_registry["incomplete_event_types"]).isdisjoint(
        EXPECTED_SUPPORTED_R1_EVENTS
    )
    assert r1_registry["type_definitions"]["experiment_id"] == {
        "kind": "typed_id",
        "prefix": "exp",
    }

    assert hashlib.sha256(R0_REGISTRY_PATH.read_bytes()).hexdigest() == (
        EXPECTED_R0_RAW_SHA256
    )
    assert hashlib.sha256(R0_DIGEST_PATH.read_bytes()).hexdigest() == (
        EXPECTED_R0_SIDECAR_RAW_SHA256
    )
    assert R0_DIGEST_PATH.read_text(encoding="ascii").strip() == (
        EXPECTED_R0_CANONICAL_SHA256
    )
    assert registry_digest(r0_registry) == EXPECTED_R0_CANONICAL_SHA256
    assert registry_digest(r1_registry) == EXPECTED_R1_CANONICAL_SHA256
    assert R1_DIGEST_PATH.read_text(encoding="ascii").strip() == (
        EXPECTED_R1_CANONICAL_SHA256
    )


def test_r1_conformance_vectors_have_literal_expected_outcomes() -> None:
    assert run_conformance_vectors(_r1_registry()) == {
        "epoch_valid": "ACCEPT",
        "campaign_allocated_valid": "ACCEPT",
        "experiment_allocated_valid": "ACCEPT",
        "epoch_wrong_subject": "INVALID_EVENT",
        "epoch_nonempty_scope": "INVALID_EVENT",
        "known_incomplete_trial": "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY",
        "unknown_event_type": "UNKNOWN_EVENT_TYPE",
        "raw_duplicate_event_type": "DUPLICATE_PROPERTY",
    }


def test_r1_digest_is_literal_reordered_and_mutation_sensitive() -> None:
    registry = _r1_registry()

    assert registry_digest(dict(reversed(registry.items()))) == (
        EXPECTED_R1_CANONICAL_SHA256
    )
    mutated = deepcopy(registry)
    mutated["conformance_vectors"][1]["value"]["actor_id"] = (
        "act_00000000000000000000000000000019"
    )
    validate_registry(mutated)
    assert registry_digest(mutated) != EXPECTED_R1_CANONICAL_SHA256


def test_r1_validates_independent_campaign_and_experiment_fixtures() -> None:
    registry = _r1_registry()
    fixture = _allocation_fixture()

    campaign = fixture["campaign_allocated"]
    experiment = fixture["experiment_allocated"]
    assert validate_event(campaign, registry=registry) == campaign
    assert validate_event(experiment, registry=registry) == experiment


def test_r0_compatibility_entry_point_does_not_silently_upgrade() -> None:
    fixture = _allocation_fixture()

    for event_key in ("campaign_allocated", "experiment_allocated"):
        _assert_code(
            "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY",
            lambda event_key=event_key: validate_event(fixture[event_key]),
        )
    assert load_registry_release("0.7.0")["registry_version"] == "0.7.0"
    assert load_registry_release("0.8.0")["registry_version"] == "0.8.0"
    assert load_registry_release("0.9.0")["registry_version"] == "0.9.0"
    _assert_code("INVALID_REGISTRY", lambda: load_registry_release("0.10.0"))


def test_r1_rejects_every_nonpromoted_and_unknown_event_before_action() -> None:
    registry = _r1_registry()

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


def test_r1_rejects_self_consistent_unpublished_promotion() -> None:
    promoted = _r1_registry()
    trial_schema = deepcopy(promoted["event_schemas"][1])
    trial_schema["event_type"] = "TRIAL_ALLOCATED"
    trial_schema["event_schema"]["properties"]["event_type"]["value"] = (
        "TRIAL_ALLOCATED"
    )
    promoted["event_schemas"].append(trial_schema)
    promoted["incomplete_event_types"].remove("TRIAL_ALLOCATED")
    forged_vector = deepcopy(promoted["conformance_vectors"][1])
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


@pytest.mark.parametrize("event_key", ["campaign_allocated", "experiment_allocated"])
@pytest.mark.parametrize(
    "field",
    EXPECTED_ALLOCATION_FIELDS + ("payload.campaign_scope_ids",),
)
def test_r1_allocations_reject_every_missing_required_field(
    event_key: str,
    field: str,
) -> None:
    event = deepcopy(_allocation_fixture()[event_key])
    if field == "payload.campaign_scope_ids":
        event["payload"].pop("campaign_scope_ids")
    else:
        event.pop(field)

    _assert_code(
        "INVALID_EVENT",
        lambda: validate_event(event, registry=_r1_registry()),
    )


def test_campaign_allocation_kills_subject_scope_and_shape_mutations() -> None:
    valid = _allocation_fixture()["campaign_allocated"]
    invalid_events: list[dict[str, object]] = []

    wrong_scope = deepcopy(valid)
    wrong_scope["payload"]["campaign_scope_ids"] = [
        "cmp_00000000000000000000000000000018"
    ]
    invalid_events.append(wrong_scope)

    for scope in (
        [],
        [
            "cmp_00000000000000000000000000000011",
            "cmp_00000000000000000000000000000018",
        ],
        ["exp_00000000000000000000000000000014"],
        None,
    ):
        invalid = deepcopy(valid)
        invalid["payload"]["campaign_scope_ids"] = scope
        invalid_events.append(invalid)

    wrong_subject = deepcopy(valid)
    wrong_subject["subject_id"] = "exp_00000000000000000000000000000014"
    invalid_events.append(wrong_subject)

    wrong_subject_type = deepcopy(valid)
    wrong_subject_type["subject_type"] = "experiment"
    invalid_events.append(wrong_subject_type)

    unknown_payload = deepcopy(valid)
    unknown_payload["payload"]["objective"] = "forbidden"
    invalid_events.append(unknown_payload)

    unknown_envelope = deepcopy(valid)
    unknown_envelope["metadata"] = {}
    invalid_events.append(unknown_envelope)

    zero_sequence = deepcopy(valid)
    zero_sequence["sequence"] = 0
    invalid_events.append(zero_sequence)

    bool_sequence = deepcopy(valid)
    bool_sequence["sequence"] = True
    invalid_events.append(bool_sequence)

    null_previous = deepcopy(valid)
    null_previous["previous_event_sha256"] = None
    invalid_events.append(null_previous)

    for invalid in invalid_events:
        _assert_code(
            "INVALID_EVENT",
            lambda invalid=invalid: validate_event(
                invalid,
                registry=_r1_registry(),
            ),
        )


@pytest.mark.parametrize("event_key", ["campaign_allocated", "experiment_allocated"])
def test_r1_allocation_common_envelope_types_fail_closed(
    event_key: str,
) -> None:
    valid = _allocation_fixture()[event_key]
    invalid_events: list[dict[str, object]] = []

    invalid_date = deepcopy(valid)
    invalid_date["occurred_at"] = "2026-02-29T00:00:00Z"
    invalid_events.append(invalid_date)

    uppercase_request_digest = deepcopy(valid)
    uppercase_request_digest["operation_request_sha256"] = "A" * 64
    invalid_events.append(uppercase_request_digest)

    uppercase_previous_digest = deepcopy(valid)
    uppercase_previous_digest["previous_event_sha256"] = "B" * 64
    invalid_events.append(uppercase_previous_digest)

    wrong_ledger_prefix = deepcopy(valid)
    wrong_ledger_prefix["ledger_id"] = (
        "bad_00000000000000000000000000000010"
    )
    invalid_events.append(wrong_ledger_prefix)

    wrong_actor_prefix = deepcopy(valid)
    wrong_actor_prefix["actor_id"] = (
        "bad_00000000000000000000000000000017"
    )
    invalid_events.append(wrong_actor_prefix)

    string_sequence = deepcopy(valid)
    string_sequence["sequence"] = "1"
    invalid_events.append(string_sequence)

    unknown_envelope = deepcopy(valid)
    unknown_envelope["free_text"] = "forbidden"
    invalid_events.append(unknown_envelope)

    for invalid in invalid_events:
        _assert_code(
            "INVALID_EVENT",
            lambda invalid=invalid: validate_event(
                invalid,
                registry=_r1_registry(),
            ),
        )


@pytest.mark.parametrize(
    "bad_experiment_id",
    [
        "cmp_00000000000000000000000000000014",
        "EXP_00000000000000000000000000000014",
        "exp_0000000000000000000000000000001g",
        "exp_0000000000000000000000000000014",
        "exp-00000000000000000000000000000014",
    ],
)
def test_experiment_allocation_kills_nonratified_namespaces(
    bad_experiment_id: str,
) -> None:
    invalid = deepcopy(_allocation_fixture()["experiment_allocated"])
    invalid["subject_id"] = bad_experiment_id

    _assert_code(
        "INVALID_EVENT",
        lambda: validate_event(invalid, registry=_r1_registry()),
    )


def test_experiment_allocation_has_only_single_parent_campaign_scope() -> None:
    valid = _allocation_fixture()["experiment_allocated"]
    assert valid["subject_id"] not in valid["payload"]["campaign_scope_ids"]

    invalid_events: list[dict[str, object]] = []
    for scope in (
        [],
        [
            "cmp_00000000000000000000000000000011",
            "cmp_00000000000000000000000000000018",
        ],
        ["exp_00000000000000000000000000000014"],
        None,
    ):
        invalid = deepcopy(valid)
        invalid["payload"]["campaign_scope_ids"] = scope
        invalid_events.append(invalid)

    redundant_parent = deepcopy(valid)
    redundant_parent["payload"]["campaign_id"] = (
        "cmp_00000000000000000000000000000011"
    )
    invalid_events.append(redundant_parent)

    for invalid in invalid_events:
        _assert_code(
            "INVALID_EVENT",
            lambda invalid=invalid: validate_event(
                invalid,
                registry=_r1_registry(),
            ),
        )


def test_r1_raw_event_parser_rejects_duplicate_nested_properties() -> None:
    raw = (
        b'{"event_type":"CAMPAIGN_ALLOCATED","payload":'
        b'{"campaign_scope_ids":[],"campaign_scope_ids":[]}}'
    )
    _assert_code(
        "DUPLICATE_PROPERTY",
        lambda: validate_raw_event_bytes(raw, registry=_r1_registry()),
    )


@pytest.mark.parametrize(
    "value",
    [
        "a",
        "0",
        "a.b-c_d",
        "a" + ("b" * 126) + "c",
    ],
)
def test_safe_public_id_accepts_exact_boundaries(value: str) -> None:
    schema = {"kind": "safe_public_id"}
    _validate_dsl_schema(schema)
    _validate_dsl_value(schema, value)


@pytest.mark.parametrize(
    "value",
    [
        "",
        "a" * 129,
        "Upper",
        "white space",
        "a/b",
        "a\\b",
        "a:b",
        "a?b",
        "a#b",
        "a%2fb",
        "a@b",
        "nonascii-é",
        ".leading",
        "trailing.",
        "..",
        "https://example",
    ],
)
def test_safe_public_id_rejects_every_forbidden_class(value: str) -> None:
    schema = {"kind": "safe_public_id"}
    _validate_dsl_schema(schema)
    _assert_code(
        "INVALID_EVENT",
        lambda: _validate_dsl_value(schema, value),
    )


def test_safe_public_id_is_parameter_free_and_unavailable_in_r0() -> None:
    _assert_code(
        "INVALID_REGISTRY",
        lambda: _validate_dsl_schema(
            {"kind": "safe_public_id", "pattern": ".*"}
        ),
    )
    _assert_code(
        "INVALID_REGISTRY",
        lambda: _validate_dsl_schema(
            {"kind": "safe_public_id"},
            version="0.1.0",
        ),
    )


def test_tagged_union_accepts_each_exact_closed_branch() -> None:
    schema = _tagged_union_schema()
    _validate_dsl_schema(schema)

    _validate_dsl_value(
        schema,
        {"entity_kind": "sample", "sample_ref": "sample.reference-1"},
    )
    _validate_dsl_value(
        schema,
        {
            "entity_kind": "trial_family",
            "family_ref": "family.reference-1",
        },
    )


@pytest.mark.parametrize(
    "value",
    [
        {"entity_kind": "unknown", "sample_ref": "sample-1"},
        {"sample_ref": "sample-1"},
        {"entity_kind": None, "sample_ref": "sample-1"},
        {"entity_kind": "sample"},
        {
            "entity_kind": "sample",
            "sample_ref": "sample-1",
            "family_ref": "family-1",
        },
        {"entity_kind": "trial_family"},
        {
            "entity_kind": "trial_family",
            "family_ref": "family-1",
            "sample_ref": "sample-1",
        },
    ],
)
def test_tagged_union_rejects_unknown_mixed_both_and_neither(
    value: object,
) -> None:
    schema = _tagged_union_schema()
    _validate_dsl_schema(schema)
    _assert_code(
        "INVALID_EVENT",
        lambda: _validate_dsl_value(schema, value),
    )


def test_tagged_union_meta_contract_kills_ambiguous_shapes() -> None:
    base = _tagged_union_schema()
    invalid_schemas: list[dict[str, object]] = []

    one_branch = deepcopy(base)
    one_branch["variants"].pop("trial_family")
    invalid_schemas.append(one_branch)

    mismatched_literal = deepcopy(base)
    mismatched_literal["variants"]["sample"]["properties"]["entity_kind"][
        "value"
    ] = "trial_family"
    invalid_schemas.append(mismatched_literal)

    optional_discriminator = deepcopy(base)
    optional_discriminator["variants"]["sample"]["required"].remove(
        "entity_kind"
    )
    invalid_schemas.append(optional_discriminator)

    open_branch = deepcopy(base)
    open_branch["variants"]["sample"] = {"kind": "safe_public_id"}
    invalid_schemas.append(open_branch)

    invalid_tag = deepcopy(base)
    invalid_tag["variants"]["sample-kind"] = invalid_tag["variants"].pop(
        "sample"
    )
    invalid_schemas.append(invalid_tag)

    for invalid in invalid_schemas:
        _assert_code(
            "INVALID_REGISTRY",
            lambda invalid=invalid: _validate_dsl_schema(invalid),
        )

    _assert_code(
        "INVALID_REGISTRY",
        lambda: _validate_dsl_schema(base, version="0.1.0"),
    )


def test_array_contains_path_meta_contract_requires_array_and_compatible_scalar() -> None:
    constraint = _array_contains_constraint()
    assert (
        _validate_constraint(
            constraint,
            context="test_constraint",
            allowed_predicates={"array_contains_path", "path_equals_path"},
            event_schema=_array_constraint_schema(),
            definitions={},
            schema_language_version="0.2.0",
        )
        == "subject_in_scope"
    )

    wrong_left = _array_constraint_schema()
    wrong_left["properties"]["payload"]["properties"][
        "campaign_scope_ids"
    ] = {"kind": "typed_id", "prefix": "cmp"}
    _assert_code(
        "INVALID_REGISTRY",
        lambda: _validate_constraint(
            constraint,
            context="test_constraint",
            allowed_predicates={"array_contains_path", "path_equals_path"},
            event_schema=wrong_left,
            definitions={},
            schema_language_version="0.2.0",
        ),
    )

    wrong_right = _array_constraint_schema()
    wrong_right["properties"]["subject_id"] = {
        "kind": "array",
        "collection_semantics": "ordered",
        "items": {"kind": "typed_id", "prefix": "cmp"},
        "min_items": 1,
        "max_items": 1,
    }
    _assert_code(
        "INVALID_REGISTRY",
        lambda: _validate_constraint(
            constraint,
            context="test_constraint",
            allowed_predicates={"array_contains_path", "path_equals_path"},
            event_schema=wrong_right,
            definitions={},
            schema_language_version="0.2.0",
        ),
    )

    _assert_code(
        "INVALID_REGISTRY",
        lambda: _validate_constraint(
            constraint,
            context="test_constraint",
            allowed_predicates={"array_contains_path", "path_equals_path"},
            event_schema=_array_constraint_schema(scalar_prefix="exp"),
            definitions={},
            schema_language_version="0.2.0",
        ),
    )


def test_constraint_path_nullable_named_cycle_fails_as_invalid_registry() -> None:
    registry = _r1_registry()
    registry["type_definitions"]["nullable_cycle"] = {
        "kind": "nullable",
        "schema": {"kind": "named", "name": "nullable_cycle"},
    }
    campaign_schema = registry["event_schemas"][1]
    campaign_schema["event_schema"]["properties"]["subject_id"] = {
        "kind": "closed_object",
        "properties": {
            "nested": {"kind": "named", "name": "nullable_cycle"},
        },
        "required": ["nested"],
    }
    campaign_schema["local_constraints"][0]["right_path"] = [
        "subject_id",
        "nested",
        "leaf",
    ]

    _assert_code(
        "INVALID_REGISTRY",
        lambda: validate_registry(registry),
    )


def test_array_constraint_paths_must_exist_in_every_tagged_union_branch() -> None:
    schema = {
        "kind": "tagged_union",
        "discriminator": "entity_kind",
        "variants": {
            "sample": {
                "kind": "closed_object",
                "properties": {
                    "entity_kind": {"kind": "literal", "value": "sample"},
                    "scope": {
                        "kind": "array",
                        "collection_semantics": "ordered",
                        "items": {"kind": "typed_id", "prefix": "cmp"},
                        "min_items": 1,
                        "max_items": 1,
                    },
                    "subject": {"kind": "typed_id", "prefix": "cmp"},
                },
                "required": ["entity_kind", "scope", "subject"],
            },
            "trial_family": {
                "kind": "closed_object",
                "properties": {
                    "entity_kind": {
                        "kind": "literal",
                        "value": "trial_family",
                    },
                    "subject": {"kind": "typed_id", "prefix": "cmp"},
                },
                "required": ["entity_kind", "subject"],
            },
        },
    }
    _validate_dsl_schema(schema)
    constraint = {
        "constraint_id": "scope_contains_subject",
        "predicate": "array_contains_path",
        "left_path": ["scope"],
        "right_path": ["subject"],
    }

    _assert_code(
        "INVALID_REGISTRY",
        lambda: _validate_constraint(
            constraint,
            context="test_constraint",
            allowed_predicates={"array_contains_path", "path_equals_path"},
            event_schema=schema,
            definitions={},
            schema_language_version="0.2.0",
        ),
    )


def test_r1_constraint_paths_allow_repeated_property_names_without_r0_drift() -> None:
    repeated_path_schema = {
        "kind": "closed_object",
        "properties": {
            "node": {
                "kind": "closed_object",
                "properties": {
                    "node": {"kind": "typed_id", "prefix": "cmp"}
                },
                "required": ["node"],
            },
            "subject_id": {"kind": "typed_id", "prefix": "cmp"},
        },
        "required": ["node", "subject_id"],
    }
    constraint = {
        "constraint_id": "repeated_path",
        "predicate": "path_equals_path",
        "left_path": ["node", "node"],
        "right_path": ["subject_id"],
    }

    assert (
        _validate_constraint(
            constraint,
            context="test_constraint",
            allowed_predicates={"array_contains_path", "path_equals_path"},
            event_schema=repeated_path_schema,
            definitions={},
            schema_language_version="0.2.0",
        )
        == "repeated_path"
    )
    _assert_code(
        "INVALID_REGISTRY",
        lambda: _validate_constraint(
            constraint,
            context="test_constraint",
            allowed_predicates={"path_equals_path"},
            event_schema=repeated_path_schema,
            definitions={},
            schema_language_version="0.1.0",
        ),
    )

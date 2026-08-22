"""Executable validators for Track A PR 2 PIT manifest artifacts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pit_manifest_validator_v1.canonical import (
    CANONICALIZATION_ID,
    ValidationError,
    canonical_sha256,
    canonical_utf8,
    fail,
    is_safe_public_id,
    is_sha256,
    normalize_timestamp,
    parse_json_bytes,
    require_code_sha,
    require_date,
    require_decimal_string,
    require_enum,
    require_exact_keys,
    require_list,
    require_literal,
    require_mapping,
    require_nonempty_nfc,
    require_nonnegative_int,
    require_safe_public_id,
    require_sha256,
    require_string,
    utf16_sort_key,
)


DECISION_STATES = frozenset({"accepted", "diagnostic_only", "blocked"})
PRIVATE_FULL_MANIFEST_SCHEMA = "private_full_manifest_v1"
ORDERED_INVENTORY_SCHEMA = "ordered_component_inventory_v1"
PUBLIC_PROJECTION_SCHEMA = "public_redacted_projection_v1"
DECISION_RECORD_SCHEMA = "dataset_review_decision_v1"
FREEZE_RECORD_SCHEMA = "track_a_pr2_freeze_record_v1"
CONTRACT_ID = "point_in_time_data_methodology_contract_v1"
CONTRACT_VERSION = "1.0.0"
CONTRACT_CONTENT_SHA256 = (
    "febb08c62d954f738503dcd215967370dbccfda3460481b755fb6607c0182574"
)
REQUIRED_FREEZE_ROLES = (
    "historical_membership",
    "member_eod",
    "delisted_symbols",
    "symbol_change_history",
    "splits",
    "dividends",
    "benchmark_spy",
)
COVERAGE_LABELS = (
    "coverage_all_available",
    "coverage_primary_quality_window",
    "coverage_pre_2018_limited",
)
ZERO_TARGET_TRIGGERS = (
    "ELIGIBLE_SECURITY_COUNT_BELOW_100_AT_T",
    "DISTINCT_FINITE_FACTOR_VALUE_COUNT_BELOW_10_AT_T",
    "DUPLICATE_CANONICAL_LISTING_KEY_BYTES_AT_T",
)
EXCLUSION_CLASSES = (
    "conflicting_snapshot_undefined_interval",
    "pre_baseline_date",
    "null_startdate_never_in_valid_snapshot",
    "d7_adjudicated_identity_ineligible",
    "quarantined_payload",
)
COMMON_IDENTITY_EXCLUDE = frozenset({"signatures", "presentation_notes"})
KIND_IDENTITY_EXCLUDE = {
    "private_full_manifest": frozenset({"canonical_manifest_sha256"}),
    "dataset_review_decision": frozenset({"decision_record_sha256"}),
    "track_a_pr2_freeze_record_v1": frozenset({"freeze_record_sha256"}),
}
CONTENT_STATUSES = frozenset(
    {"raw", "vendor_cleaned", "hand_cleaned", "normalized", "derived"}
)
PRIVACY_CLASSES = frozenset({"public", "private", "restricted"})
HASH_PUBLICATION_CLASSES = frozenset({"private", "publication_approved"})
FINDING_SEVERITIES = frozenset({"info", "low", "medium", "high", "critical"})

MANIFEST_TOP_LEVEL_KEYS = {
    "schema_version",
    "manifest_id",
    "created_at_utc",
    "dataset_role",
    "provider_label",
    "provider_product_release",
    "retrieved_at_utc",
    "as_of_cutoff",
    "extraction_identity",
    "privacy_classification",
    "code_sha",
    "config_sha256",
    "environment_id",
    "environment_lock_sha256",
    "canonicalization_id",
    "ordered_manifest_sha256",
    "canonical_manifest_sha256",
    "inputs",
}
EXTRACTION_IDENTITY_KEYS = {
    "extraction_id",
    "coverage_start_inclusive",
    "coverage_end_inclusive",
    "filter_ids",
    "requested_field_ids",
}
INPUT_KEYS = {
    "input_id",
    "role",
    "schema_name",
    "schema_version",
    "physical_components",
    "row_count",
    "coverage_start_inclusive",
    "coverage_end_inclusive",
    "hash_publication_classification",
    "content_status",
    "parent_input_ids",
    "parent_input_hashes",
    "transformation_id",
    "code_sha",
    "config_sha256",
    "environment_id",
    "environment_lock_sha256",
    "identifier_namespace",
    "currency",
    "units",
    "calendar_id",
    "timezone",
    "timestamp_semantics",
    "adjustment_policy_id",
    "revision_policy_id",
    "missingness_policy_id",
    "publication_policy_id",
    "manual_transformations",
    "quality_exceptions",
}
COMPONENT_KEYS = {"input_id", "component_ordinal", "raw_byte_sha256", "byte_size"}
MANUAL_TRANSFORMATION_KEYS = {"transformation_id", "code_sha", "config_sha256"}
QUALITY_EXCEPTION_KEYS = {"exception_id", "disposition", "reviewer_id"}
INVENTORY_KEYS = {"schema_version", "canonicalization_id", "components"}
PROJECTION_KEYS = {
    "schema_version",
    "public_projection_id",
    "canonicalization_id",
    "manifest_id",
    "dataset_roles",
    "policy_states",
    "redacted_evidence_refs",
    "published_hashes",
}
POLICY_STATE_KEYS = {"policy_id", "state"}
EVIDENCE_REF_KEYS = {"evidence_ref_id"}
PUBLISHED_HASH_KEYS = {"hash_id", "sha256", "publication_approval_ref_id"}
DECISION_KEYS = {
    "schema_version",
    "review_decision_id",
    "reviewed_at",
    "reviewer_id",
    "reviewer_authority_reference",
    "contract_id",
    "contract_version",
    "contract_content_sha256",
    "contract_protected_merge_sha",
    "manifest_id",
    "canonical_manifest_sha256",
    "canonicalization_id",
    "public_projection_id",
    "public_projection_schema_version",
    "public_projection_sha256",
    "declared_dataset_roles",
    "declared_use",
    "date_universe_scope",
    "privacy_publication_scope",
    "applicable_contract_version",
    "decision",
    "findings",
    "predecessor_decision_id",
    "decision_canonicalization_id",
    "decision_record_sha256",
    "public_decision_reference",
}
FINDING_KEYS = {
    "finding_id",
    "severity",
    "evidence_refs",
    "disposition",
    "unresolved_limitation",
}
FREEZE_KEYS = {
    "schema_version",
    "freeze_record_id",
    "canonicalization_id",
    "as_of_cutoff",
    "role_coverage",
    "coverage_labels",
    "calendar",
    "lineage_and_terminal",
    "exclusions",
    "coverage_thresholds",
    "materiality_thresholds",
    "contract_binding",
    "identity_fail_closed",
    "freeze_record_sha256",
}
ROLE_COVERAGE_KEYS = {
    "role",
    "coverage_start_inclusive",
    "coverage_end_inclusive",
    "row_count",
    "limitation_state",
    "limitation_id",
}
CALENDAR_KEYS = {
    "calendar_id",
    "calendar_version",
    "calendar_evidence_ref",
    "source_timezone",
    "utc_conversion_rule",
    "environment_id",
    "environment_lock_sha256",
}
LINEAGE_KEYS = {
    "membership_policy_id",
    "membership_policy_sha256",
    "snapshot_authority",
    "as_of_rule",
    "carry_forward",
    "baseline_date",
    "pre_baseline_claims",
    "invented_start_date",
    "start_date_boundary",
    "end_date_boundary",
    "interval_notation",
    "factor_anchor_lineage_id",
    "terminal_event_policy_state",
    "terminal_event_policy_sha256",
}
EXCLUSION_KEYS = {
    "exclusion_id",
    "exclusion_class",
    "count",
    "evidence_sha256",
}
COVERAGE_THRESHOLD_KEYS = {
    "factor_month_eligible_listing_floor",
    "distinct_finite_factor_value_floor",
    "common_complete_case_month_floor",
    "zero_target_triggers",
}
MATERIALITY_KEYS = {
    "state",
    "performance_informed_selection",
    "thresholds",
}
MATERIALITY_THRESHOLD_KEYS = {"threshold_id", "value", "evidence_sha256"}
CONTRACT_BINDING_KEYS = {
    "contract_id",
    "contract_version",
    "contract_content_sha256",
    "contract_protected_merge_sha",
}
IDENTITY_FAIL_CLOSED_KEYS = {
    "identities_adjudicated",
    "accepted_identities",
    "disposition",
    "effect",
    "scope",
}


def _join_locator(prefix: str | None, suffix: str) -> str:
    if not prefix:
        return suffix
    return f"{prefix}.{suffix}"


def _require_optional_string(
    value: object,
    field: str,
    *,
    input_id: str | None = None,
    locator: str | None = None,
) -> str | None:
    if value is None:
        return None
    return require_nonempty_nfc(value, field, input_id=input_id, locator=locator)


def _require_optional_code_sha(
    value: object,
    field: str,
    *,
    input_id: str | None = None,
    locator: str | None = None,
) -> str | None:
    if value is None:
        return None
    return require_code_sha(value, field, input_id=input_id, locator=locator)


def _require_optional_sha256(
    value: object,
    field: str,
    *,
    input_id: str | None = None,
    locator: str | None = None,
) -> str | None:
    if value is None:
        return None
    return require_sha256(value, field, input_id=input_id, locator=locator)


def _require_id_list(
    value: object,
    field: str,
    *,
    input_id: str | None = None,
    locator: str | None = None,
    public: bool = False,
) -> list[str]:
    items = require_list(value, field, input_id=input_id, locator=locator)
    normalized: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(items):
        item_locator = f"{locator}[{index}]" if locator else f"{field}[{index}]"
        if public:
            text = require_safe_public_id(
                item, field, input_id=input_id, locator=item_locator
            )
        else:
            text = require_nonempty_nfc(
                item, field, input_id=input_id, locator=item_locator
            )
        if text in seen:
            fail("DUPLICATE_ID", field, input_id=input_id, locator=item_locator)
        seen.add(text)
        normalized.append(text)
    normalized.sort(key=utf16_sort_key)
    return normalized


def _require_inclusive_coverage(
    start: str,
    end: str,
    *,
    field: str = "coverage_end_inclusive",
    input_id: str | None = None,
    locator: str | None = None,
) -> None:
    if start > end:
        fail("COVERAGE_ORDER", field, input_id=input_id, locator=locator)


def _as_of_cutoff_date(as_of_cutoff: str) -> str:
    return as_of_cutoff[:10]


def _require_as_of_inside_coverage(
    cutoff_date: str,
    start: str,
    end: str,
    *,
    field: str = "as_of_cutoff",
    locator: str | None = None,
) -> None:
    if cutoff_date < start or cutoff_date > end:
        fail("AS_OF_OUTSIDE_COVERAGE", field, locator=locator)


def _require_parent_pairs(
    raw_ids: object,
    raw_hashes: object,
    *,
    input_id: str,
    ids_locator: str,
    hashes_locator: str,
) -> tuple[list[str], list[str]]:
    items = require_list(
        raw_ids, "parent_input_ids", input_id=input_id, locator=ids_locator
    )
    hashes_raw = require_list(
        raw_hashes, "parent_input_hashes", input_id=input_id, locator=hashes_locator
    )
    if len(hashes_raw) != len(items):
        fail(
            "PARENT_HASH_COUNT",
            "parent_input_hashes",
            input_id=input_id,
            locator=hashes_locator,
        )
    pairs: list[tuple[str, str]] = []
    seen: set[str] = set()
    for index, item in enumerate(items):
        item_locator = f"{ids_locator}[{index}]"
        text = require_nonempty_nfc(
            item, "parent_input_ids", input_id=input_id, locator=item_locator
        )
        if text in seen:
            fail(
                "DUPLICATE_ID",
                "parent_input_ids",
                input_id=input_id,
                locator=item_locator,
            )
        seen.add(text)
        digest = require_sha256(
            hashes_raw[index],
            "parent_input_hashes",
            input_id=input_id,
            locator=f"{hashes_locator}[{index}]",
        )
        pairs.append((text, digest))
    pairs.sort(key=lambda pair: utf16_sort_key(pair[0]))
    return [pair[0] for pair in pairs], [pair[1] for pair in pairs]


def _identity_projection(
    source: Mapping[str, object],
    kind: str | None = None,
) -> dict[str, object]:
    excluded = COMMON_IDENTITY_EXCLUDE | KIND_IDENTITY_EXCLUDE.get(kind, frozenset())
    return {key: value for key, value in source.items() if key not in excluded}


def _sorted_objects(
    records: list[dict[str, object]],
    key_field: str,
) -> list[dict[str, object]]:
    return sorted(records, key=lambda item: utf16_sort_key(str(item[key_field])))


def validate_physical_component(
    source: object,
    *,
    expected_input_id: str | None = None,
    locator: str,
) -> dict[str, object]:
    component = require_exact_keys(
        source, COMPONENT_KEYS, "physical_component", locator=locator
    )
    input_id = require_nonempty_nfc(
        component["input_id"], "input_id", locator=_join_locator(locator, "input_id")
    )
    if expected_input_id is not None and input_id != expected_input_id:
        fail("INPUT_ID_MISMATCH", "input_id", input_id=expected_input_id, locator=locator)
    ordinal = require_nonnegative_int(
        component["component_ordinal"],
        "component_ordinal",
        input_id=input_id,
        locator=_join_locator(locator, "component_ordinal"),
    )
    digest = require_sha256(
        component["raw_byte_sha256"],
        "raw_byte_sha256",
        input_id=input_id,
        locator=_join_locator(locator, "raw_byte_sha256"),
    )
    byte_size = require_nonnegative_int(
        component["byte_size"],
        "byte_size",
        input_id=input_id,
        locator=_join_locator(locator, "byte_size"),
    )
    return {
        "input_id": input_id,
        "component_ordinal": ordinal,
        "raw_byte_sha256": digest,
        "byte_size": byte_size,
    }


def _validate_component_collection(
    source: object,
    *,
    expected_input_id: str | None,
    field: str,
    locator: str,
) -> list[dict[str, object]]:
    raw_components = require_list(source, field, locator=locator)
    if not raw_components:
        fail("EMPTY_COMPONENTS", field, input_id=expected_input_id, locator=locator)
    components = [
        validate_physical_component(
            item,
            expected_input_id=expected_input_id,
            locator=f"{locator}[{index}]",
        )
        for index, item in enumerate(raw_components)
    ]
    seen: set[tuple[str, int]] = set()
    ordinals_by_input: dict[str, set[int]] = {}
    for component in components:
        key = (str(component["input_id"]), int(component["component_ordinal"]))
        if key in seen:
            fail(
                "DUPLICATE_COMPONENT",
                "component_ordinal",
                input_id=str(component["input_id"]),
                locator=locator,
            )
        seen.add(key)
        ordinals_by_input.setdefault(str(component["input_id"]), set()).add(
            int(component["component_ordinal"])
        )
    for input_id, ordinals in ordinals_by_input.items():
        if ordinals != set(range(len(ordinals))):
            fail(
                "NONCONTIGUOUS_ORDINAL",
                "component_ordinal",
                input_id=input_id,
                locator=locator,
            )
    components.sort(
        key=lambda item: (
            utf16_sort_key(str(item["input_id"])),
            int(item["component_ordinal"]),
        )
    )
    return components


def project_ordered_component_inventory(source: object) -> dict[str, object]:
    inventory = require_exact_keys(source, INVENTORY_KEYS, "ordered_component_inventory")
    require_literal(inventory["schema_version"], ORDERED_INVENTORY_SCHEMA, "schema_version")
    require_literal(
        inventory["canonicalization_id"], CANONICALIZATION_ID, "canonicalization_id"
    )
    components = _validate_component_collection(
        inventory["components"],
        expected_input_id=None,
        field="components",
        locator="components",
    )
    return {
        "schema_version": ORDERED_INVENTORY_SCHEMA,
        "canonicalization_id": CANONICALIZATION_ID,
        "components": components,
    }


def build_ordered_component_inventory(
    components: list[dict[str, object]],
) -> dict[str, object]:
    return project_ordered_component_inventory(
        {
            "schema_version": ORDERED_INVENTORY_SCHEMA,
            "canonicalization_id": CANONICALIZATION_ID,
            "components": components,
        }
    )


def ordered_manifest_sha256(components: list[dict[str, object]]) -> str:
    return canonical_sha256(build_ordered_component_inventory(components))


def project_public_redacted_projection(source: object) -> dict[str, object]:
    projection = require_exact_keys(source, PROJECTION_KEYS, "public_redacted_projection")
    require_literal(
        projection["schema_version"], PUBLIC_PROJECTION_SCHEMA, "schema_version"
    )
    require_literal(
        projection["canonicalization_id"], CANONICALIZATION_ID, "canonicalization_id"
    )
    public_projection_id = require_safe_public_id(
        projection["public_projection_id"], "public_projection_id"
    )
    manifest_id = require_safe_public_id(projection["manifest_id"], "manifest_id")
    dataset_roles = _require_id_list(
        projection["dataset_roles"],
        "dataset_roles",
        locator="dataset_roles",
        public=True,
    )

    raw_policies = require_list(projection["policy_states"], "policy_states")
    policy_states: list[dict[str, object]] = []
    policy_ids: set[str] = set()
    for index, raw_policy in enumerate(raw_policies):
        locator = f"policy_states[{index}]"
        policy = require_exact_keys(
            raw_policy, POLICY_STATE_KEYS, "policy_state", locator=locator
        )
        policy_id = require_safe_public_id(
            policy["policy_id"], "policy_id", locator=_join_locator(locator, "policy_id")
        )
        if policy_id in policy_ids:
            fail("DUPLICATE_ID", "policy_id", locator=locator)
        policy_ids.add(policy_id)
        state = require_enum(
            policy["state"],
            DECISION_STATES,
            "state",
            locator=_join_locator(locator, "state"),
        )
        policy_states.append({"policy_id": policy_id, "state": state})
    policy_states = _sorted_objects(policy_states, "policy_id")

    raw_refs = require_list(projection["redacted_evidence_refs"], "redacted_evidence_refs")
    evidence_refs: list[dict[str, object]] = []
    evidence_ids: set[str] = set()
    for index, raw_ref in enumerate(raw_refs):
        locator = f"redacted_evidence_refs[{index}]"
        ref = require_exact_keys(
            raw_ref, EVIDENCE_REF_KEYS, "redacted_evidence_ref", locator=locator
        )
        evidence_id = require_safe_public_id(
            ref["evidence_ref_id"],
            "evidence_ref_id",
            locator=_join_locator(locator, "evidence_ref_id"),
        )
        if evidence_id in evidence_ids:
            fail("DUPLICATE_ID", "evidence_ref_id", locator=locator)
        evidence_ids.add(evidence_id)
        evidence_refs.append({"evidence_ref_id": evidence_id})
    evidence_refs = _sorted_objects(evidence_refs, "evidence_ref_id")

    raw_hashes = require_list(projection["published_hashes"], "published_hashes")
    published_hashes: list[dict[str, object]] = []
    hash_ids: set[str] = set()
    for index, raw_hash in enumerate(raw_hashes):
        locator = f"published_hashes[{index}]"
        published = require_exact_keys(
            raw_hash, PUBLISHED_HASH_KEYS, "published_hash", locator=locator
        )
        hash_id = require_safe_public_id(
            published["hash_id"], "hash_id", locator=_join_locator(locator, "hash_id")
        )
        if hash_id in hash_ids:
            fail("DUPLICATE_ID", "hash_id", locator=locator)
        hash_ids.add(hash_id)
        digest = require_sha256(
            published["sha256"], "sha256", locator=_join_locator(locator, "sha256")
        )
        approval = require_safe_public_id(
            published["publication_approval_ref_id"],
            "publication_approval_ref_id",
            locator=_join_locator(locator, "publication_approval_ref_id"),
        )
        published_hashes.append(
            {
                "hash_id": hash_id,
                "sha256": digest,
                "publication_approval_ref_id": approval,
            }
        )
    published_hashes = _sorted_objects(published_hashes, "hash_id")
    return {
        "schema_version": PUBLIC_PROJECTION_SCHEMA,
        "public_projection_id": public_projection_id,
        "canonicalization_id": CANONICALIZATION_ID,
        "manifest_id": manifest_id,
        "dataset_roles": dataset_roles,
        "policy_states": policy_states,
        "redacted_evidence_refs": evidence_refs,
        "published_hashes": published_hashes,
    }


def public_projection_sha256(source: object) -> str:
    return canonical_sha256(project_public_redacted_projection(source))


def _validate_manual_transformations(
    source: object,
    *,
    input_id: str,
    locator: str,
) -> list[dict[str, object]]:
    raw_items = require_list(source, "manual_transformations", input_id=input_id, locator=locator)
    records: list[dict[str, object]] = []
    seen: set[str] = set()
    for index, raw_item in enumerate(raw_items):
        item_locator = f"{locator}[{index}]"
        item = require_exact_keys(
            raw_item,
            MANUAL_TRANSFORMATION_KEYS,
            "manual_transformation",
            input_id=input_id,
            locator=item_locator,
        )
        transformation_id = require_nonempty_nfc(
            item["transformation_id"],
            "transformation_id",
            input_id=input_id,
            locator=_join_locator(item_locator, "transformation_id"),
        )
        if transformation_id in seen:
            fail(
                "DUPLICATE_ID",
                "transformation_id",
                input_id=input_id,
                locator=item_locator,
            )
        seen.add(transformation_id)
        records.append(
            {
                "transformation_id": transformation_id,
                "code_sha": require_code_sha(
                    item["code_sha"],
                    "code_sha",
                    input_id=input_id,
                    locator=_join_locator(item_locator, "code_sha"),
                ),
                "config_sha256": require_sha256(
                    item["config_sha256"],
                    "config_sha256",
                    input_id=input_id,
                    locator=_join_locator(item_locator, "config_sha256"),
                ),
            }
        )
    return _sorted_objects(records, "transformation_id")


def _validate_quality_exceptions(
    source: object,
    *,
    input_id: str,
    locator: str,
) -> list[dict[str, object]]:
    raw_items = require_list(source, "quality_exceptions", input_id=input_id, locator=locator)
    records: list[dict[str, object]] = []
    seen: set[str] = set()
    for index, raw_item in enumerate(raw_items):
        item_locator = f"{locator}[{index}]"
        item = require_exact_keys(
            raw_item,
            QUALITY_EXCEPTION_KEYS,
            "quality_exception",
            input_id=input_id,
            locator=item_locator,
        )
        exception_id = require_nonempty_nfc(
            item["exception_id"],
            "exception_id",
            input_id=input_id,
            locator=_join_locator(item_locator, "exception_id"),
        )
        if exception_id in seen:
            fail("DUPLICATE_ID", "exception_id", input_id=input_id, locator=item_locator)
        seen.add(exception_id)
        records.append(
            {
                "exception_id": exception_id,
                "disposition": require_enum(
                    item["disposition"],
                    DECISION_STATES,
                    "disposition",
                    input_id=input_id,
                    locator=_join_locator(item_locator, "disposition"),
                ),
                "reviewer_id": require_nonempty_nfc(
                    item["reviewer_id"],
                    "reviewer_id",
                    input_id=input_id,
                    locator=_join_locator(item_locator, "reviewer_id"),
                ),
            }
        )
    return _sorted_objects(records, "exception_id")


def _validate_manifest_input(source: object, *, locator: str) -> dict[str, object]:
    raw = require_exact_keys(source, INPUT_KEYS, "input", locator=locator)
    input_id = require_nonempty_nfc(
        raw["input_id"], "input_id", locator=_join_locator(locator, "input_id")
    )
    components = _validate_component_collection(
        raw["physical_components"],
        expected_input_id=input_id,
        field="physical_components",
        locator=_join_locator(locator, "physical_components"),
    )
    content_status = require_enum(
        raw["content_status"],
        CONTENT_STATUSES,
        "content_status",
        input_id=input_id,
        locator=_join_locator(locator, "content_status"),
    )
    parent_input_ids, parent_input_hashes = _require_parent_pairs(
        raw["parent_input_ids"],
        raw["parent_input_hashes"],
        input_id=input_id,
        ids_locator=_join_locator(locator, "parent_input_ids"),
        hashes_locator=_join_locator(locator, "parent_input_hashes"),
    )
    transformation_id = _require_optional_string(
        raw["transformation_id"],
        "transformation_id",
        input_id=input_id,
        locator=_join_locator(locator, "transformation_id"),
    )
    code_sha = _require_optional_code_sha(
        raw["code_sha"],
        "code_sha",
        input_id=input_id,
        locator=_join_locator(locator, "code_sha"),
    )
    config_sha256 = _require_optional_sha256(
        raw["config_sha256"],
        "config_sha256",
        input_id=input_id,
        locator=_join_locator(locator, "config_sha256"),
    )
    if content_status == "raw":
        if parent_input_ids or transformation_id is not None:
            fail("RAW_LINEAGE", "content_status", input_id=input_id, locator=locator)
    elif not parent_input_ids or transformation_id is None or code_sha is None or config_sha256 is None:
        fail("DERIVED_LINEAGE", "content_status", input_id=input_id, locator=locator)
    coverage_start = require_date(
        raw["coverage_start_inclusive"],
        "coverage_start_inclusive",
        input_id=input_id,
        locator=_join_locator(locator, "coverage_start_inclusive"),
    )
    coverage_end = require_date(
        raw["coverage_end_inclusive"],
        "coverage_end_inclusive",
        input_id=input_id,
        locator=_join_locator(locator, "coverage_end_inclusive"),
    )
    _require_inclusive_coverage(
        coverage_start,
        coverage_end,
        input_id=input_id,
        locator=_join_locator(locator, "coverage_end_inclusive"),
    )
    return {
        "input_id": input_id,
        "role": require_nonempty_nfc(
            raw["role"], "role", input_id=input_id, locator=_join_locator(locator, "role")
        ),
        "schema_name": require_nonempty_nfc(
            raw["schema_name"],
            "schema_name",
            input_id=input_id,
            locator=_join_locator(locator, "schema_name"),
        ),
        "schema_version": require_nonempty_nfc(
            raw["schema_version"],
            "schema_version",
            input_id=input_id,
            locator=_join_locator(locator, "schema_version"),
        ),
        "physical_components": components,
        "row_count": require_nonnegative_int(
            raw["row_count"],
            "row_count",
            input_id=input_id,
            locator=_join_locator(locator, "row_count"),
        ),
        "coverage_start_inclusive": coverage_start,
        "coverage_end_inclusive": coverage_end,
        "hash_publication_classification": require_enum(
            raw["hash_publication_classification"],
            HASH_PUBLICATION_CLASSES,
            "hash_publication_classification",
            input_id=input_id,
            locator=_join_locator(locator, "hash_publication_classification"),
        ),
        "content_status": content_status,
        "parent_input_ids": parent_input_ids,
        "parent_input_hashes": parent_input_hashes,
        "transformation_id": transformation_id,
        "code_sha": code_sha,
        "config_sha256": config_sha256,
        "environment_id": require_nonempty_nfc(
            raw["environment_id"],
            "environment_id",
            input_id=input_id,
            locator=_join_locator(locator, "environment_id"),
        ),
        "environment_lock_sha256": require_sha256(
            raw["environment_lock_sha256"],
            "environment_lock_sha256",
            input_id=input_id,
            locator=_join_locator(locator, "environment_lock_sha256"),
        ),
        "identifier_namespace": require_nonempty_nfc(
            raw["identifier_namespace"],
            "identifier_namespace",
            input_id=input_id,
            locator=_join_locator(locator, "identifier_namespace"),
        ),
        "currency": require_nonempty_nfc(
            raw["currency"],
            "currency",
            input_id=input_id,
            locator=_join_locator(locator, "currency"),
        ),
        "units": require_nonempty_nfc(
            raw["units"],
            "units",
            input_id=input_id,
            locator=_join_locator(locator, "units"),
        ),
        "calendar_id": require_nonempty_nfc(
            raw["calendar_id"],
            "calendar_id",
            input_id=input_id,
            locator=_join_locator(locator, "calendar_id"),
        ),
        "timezone": require_nonempty_nfc(
            raw["timezone"],
            "timezone",
            input_id=input_id,
            locator=_join_locator(locator, "timezone"),
        ),
        "timestamp_semantics": require_nonempty_nfc(
            raw["timestamp_semantics"],
            "timestamp_semantics",
            input_id=input_id,
            locator=_join_locator(locator, "timestamp_semantics"),
        ),
        "adjustment_policy_id": require_nonempty_nfc(
            raw["adjustment_policy_id"],
            "adjustment_policy_id",
            input_id=input_id,
            locator=_join_locator(locator, "adjustment_policy_id"),
        ),
        "revision_policy_id": require_nonempty_nfc(
            raw["revision_policy_id"],
            "revision_policy_id",
            input_id=input_id,
            locator=_join_locator(locator, "revision_policy_id"),
        ),
        "missingness_policy_id": require_nonempty_nfc(
            raw["missingness_policy_id"],
            "missingness_policy_id",
            input_id=input_id,
            locator=_join_locator(locator, "missingness_policy_id"),
        ),
        "publication_policy_id": require_nonempty_nfc(
            raw["publication_policy_id"],
            "publication_policy_id",
            input_id=input_id,
            locator=_join_locator(locator, "publication_policy_id"),
        ),
        "manual_transformations": _validate_manual_transformations(
            raw["manual_transformations"],
            input_id=input_id,
            locator=_join_locator(locator, "manual_transformations"),
        ),
        "quality_exceptions": _validate_quality_exceptions(
            raw["quality_exceptions"],
            input_id=input_id,
            locator=_join_locator(locator, "quality_exceptions"),
        ),
    }


def _reject_cycles(inputs: list[dict[str, object]]) -> None:
    children: dict[str, list[str]] = {
        str(item["input_id"]): [str(parent) for parent in item["parent_input_ids"]]
        for item in inputs
    }
    known = set(children)
    for item in inputs:
        input_id = str(item["input_id"])
        for parent in item["parent_input_ids"]:
            if parent not in known:
                fail("UNKNOWN_PARENT", "parent_input_ids", input_id=input_id)
    visiting: set[str] = set()
    visited: set[str] = set()

    def walk(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            fail("CYCLIC_LINEAGE", "parent_input_ids", input_id=node)
        visiting.add(node)
        for parent in children[node]:
            walk(parent)
        visiting.remove(node)
        visited.add(node)

    for node in children:
        walk(node)


def _validate_extraction_identity(source: object) -> dict[str, object]:
    raw = require_exact_keys(source, EXTRACTION_IDENTITY_KEYS, "extraction_identity")
    coverage_start = require_date(
        raw["coverage_start_inclusive"], "coverage_start_inclusive"
    )
    coverage_end = require_date(
        raw["coverage_end_inclusive"], "coverage_end_inclusive"
    )
    _require_inclusive_coverage(coverage_start, coverage_end)
    return {
        "extraction_id": require_nonempty_nfc(raw["extraction_id"], "extraction_id"),
        "coverage_start_inclusive": coverage_start,
        "coverage_end_inclusive": coverage_end,
        "filter_ids": _require_id_list(raw["filter_ids"], "filter_ids", locator="filter_ids"),
        "requested_field_ids": _require_id_list(
            raw["requested_field_ids"],
            "requested_field_ids",
            locator="requested_field_ids",
        ),
    }


def project_private_full_manifest(
    source: object,
    *,
    verify_digest: bool = True,
) -> dict[str, object]:
    raw = require_exact_keys(source, MANIFEST_TOP_LEVEL_KEYS, "private_full_manifest")
    require_literal(raw["schema_version"], PRIVATE_FULL_MANIFEST_SCHEMA, "schema_version")
    require_literal(raw["canonicalization_id"], CANONICALIZATION_ID, "canonicalization_id")
    raw_inputs = require_list(raw["inputs"], "inputs", locator="inputs")
    if not raw_inputs:
        fail("EMPTY_INPUTS", "inputs", locator="inputs")
    inputs = [
        _validate_manifest_input(item, locator=f"inputs[{index}]")
        for index, item in enumerate(raw_inputs)
    ]
    seen_ids: set[str] = set()
    for item in inputs:
        input_id = str(item["input_id"])
        if input_id in seen_ids:
            fail("DUPLICATE_ID", "input_id", input_id=input_id)
        seen_ids.add(input_id)
    _reject_cycles(inputs)
    inputs = _sorted_objects(inputs, "input_id")
    flattened = [
        dict(component)
        for item in inputs
        for component in item["physical_components"]
    ]
    computed_ordered = ordered_manifest_sha256(flattened)
    stored_ordered = require_sha256(raw["ordered_manifest_sha256"], "ordered_manifest_sha256")
    if stored_ordered != computed_ordered:
        fail("ORDERED_DIGEST_MISMATCH", "ordered_manifest_sha256")
    projection = {
        "schema_version": PRIVATE_FULL_MANIFEST_SCHEMA,
        "manifest_id": require_nonempty_nfc(raw["manifest_id"], "manifest_id"),
        "created_at_utc": normalize_timestamp(raw["created_at_utc"], "created_at_utc"),
        "dataset_role": require_nonempty_nfc(raw["dataset_role"], "dataset_role"),
        "provider_label": require_nonempty_nfc(raw["provider_label"], "provider_label"),
        "provider_product_release": require_nonempty_nfc(
            raw["provider_product_release"], "provider_product_release"
        ),
        "retrieved_at_utc": normalize_timestamp(raw["retrieved_at_utc"], "retrieved_at_utc"),
        "as_of_cutoff": normalize_timestamp(raw["as_of_cutoff"], "as_of_cutoff"),
        "extraction_identity": _validate_extraction_identity(raw["extraction_identity"]),
        "privacy_classification": require_enum(
            raw["privacy_classification"], PRIVACY_CLASSES, "privacy_classification"
        ),
        "code_sha": require_code_sha(raw["code_sha"], "code_sha"),
        "config_sha256": require_sha256(raw["config_sha256"], "config_sha256"),
        "environment_id": require_nonempty_nfc(raw["environment_id"], "environment_id"),
        "environment_lock_sha256": require_sha256(
            raw["environment_lock_sha256"], "environment_lock_sha256"
        ),
        "canonicalization_id": CANONICALIZATION_ID,
        "ordered_manifest_sha256": stored_ordered,
        "inputs": inputs,
    }
    computed_canonical = canonical_sha256(projection)
    if verify_digest:
        stored_canonical = require_sha256(
            raw["canonical_manifest_sha256"], "canonical_manifest_sha256"
        )
        if stored_canonical != computed_canonical:
            fail("CANONICAL_DIGEST_MISMATCH", "canonical_manifest_sha256")
    return {**projection, "canonical_manifest_sha256": computed_canonical}


def _require_evidence_ref_id(
    value: object,
    field: str,
    *,
    locator: str,
) -> str:
    text = require_string(value, field, locator=locator)
    if is_sha256(text) or is_safe_public_id(text):
        return text
    fail("EVIDENCE_REF_ID", field, locator=locator)
    raise AssertionError("unreachable")


def _validate_findings(source: object) -> list[dict[str, object]]:
    raw_findings = require_list(source, "findings", locator="findings")
    findings: list[dict[str, object]] = []
    seen: set[str] = set()
    for index, raw_finding in enumerate(raw_findings):
        locator = f"findings[{index}]"
        finding = require_exact_keys(
            raw_finding, FINDING_KEYS, "finding", locator=locator
        )
        finding_id = require_nonempty_nfc(
            finding["finding_id"],
            "finding_id",
            locator=_join_locator(locator, "finding_id"),
        )
        if finding_id in seen:
            fail("DUPLICATE_ID", "finding_id", locator=locator)
        seen.add(finding_id)
        raw_refs = require_list(
            finding["evidence_refs"],
            "evidence_refs",
            locator=_join_locator(locator, "evidence_refs"),
        )
        refs: list[dict[str, object]] = []
        ref_ids: set[str] = set()
        for ref_index, raw_ref in enumerate(raw_refs):
            ref_locator = f"{locator}.evidence_refs[{ref_index}]"
            ref = require_exact_keys(
                raw_ref, EVIDENCE_REF_KEYS, "evidence_ref", locator=ref_locator
            )
            evidence_id = _require_evidence_ref_id(
                ref["evidence_ref_id"],
                "evidence_ref_id",
                locator=_join_locator(ref_locator, "evidence_ref_id"),
            )
            if evidence_id in ref_ids:
                fail("DUPLICATE_ID", "evidence_ref_id", locator=ref_locator)
            ref_ids.add(evidence_id)
            refs.append({"evidence_ref_id": evidence_id})
        refs = _sorted_objects(refs, "evidence_ref_id")
        limitation = finding["unresolved_limitation"]
        if limitation is not None:
            limitation = require_nonempty_nfc(
                limitation,
                "unresolved_limitation",
                locator=_join_locator(locator, "unresolved_limitation"),
            )
        findings.append(
            {
                "finding_id": finding_id,
                "severity": require_enum(
                    finding["severity"],
                    FINDING_SEVERITIES,
                    "severity",
                    locator=_join_locator(locator, "severity"),
                ),
                "evidence_refs": refs,
                "disposition": require_enum(
                    finding["disposition"],
                    DECISION_STATES,
                    "disposition",
                    locator=_join_locator(locator, "disposition"),
                ),
                "unresolved_limitation": limitation,
            }
        )
    return _sorted_objects(findings, "finding_id")


def project_dataset_review_decision(
    source: object,
    *,
    expected_binding: Mapping[str, str] | None = None,
    verify_digest: bool = True,
) -> dict[str, object]:
    raw = require_exact_keys(source, DECISION_KEYS, "dataset_review_decision")
    require_literal(raw["schema_version"], DECISION_RECORD_SCHEMA, "schema_version")
    require_literal(raw["canonicalization_id"], CANONICALIZATION_ID, "canonicalization_id")
    require_literal(
        raw["decision_canonicalization_id"],
        CANONICALIZATION_ID,
        "decision_canonicalization_id",
    )
    require_literal(raw["contract_id"], CONTRACT_ID, "contract_id")
    require_literal(raw["contract_version"], CONTRACT_VERSION, "contract_version")
    require_literal(
        raw["contract_content_sha256"],
        CONTRACT_CONTENT_SHA256,
        "contract_content_sha256",
    )
    require_literal(
        raw["public_projection_schema_version"],
        PUBLIC_PROJECTION_SCHEMA,
        "public_projection_schema_version",
    )
    require_literal(
        raw["applicable_contract_version"],
        CONTRACT_VERSION,
        "applicable_contract_version",
    )
    predecessor = raw["predecessor_decision_id"]
    if predecessor is not None:
        predecessor = require_nonempty_nfc(predecessor, "predecessor_decision_id")
    projection = {
        "schema_version": DECISION_RECORD_SCHEMA,
        "review_decision_id": require_nonempty_nfc(
            raw["review_decision_id"], "review_decision_id"
        ),
        "reviewed_at": normalize_timestamp(raw["reviewed_at"], "reviewed_at"),
        "reviewer_id": require_nonempty_nfc(raw["reviewer_id"], "reviewer_id"),
        "reviewer_authority_reference": require_nonempty_nfc(
            raw["reviewer_authority_reference"], "reviewer_authority_reference"
        ),
        "contract_id": CONTRACT_ID,
        "contract_version": CONTRACT_VERSION,
        "contract_content_sha256": CONTRACT_CONTENT_SHA256,
        "contract_protected_merge_sha": require_code_sha(
            raw["contract_protected_merge_sha"], "contract_protected_merge_sha"
        ),
        "manifest_id": require_nonempty_nfc(raw["manifest_id"], "manifest_id"),
        "canonical_manifest_sha256": require_sha256(
            raw["canonical_manifest_sha256"], "canonical_manifest_sha256"
        ),
        "canonicalization_id": CANONICALIZATION_ID,
        "public_projection_id": require_safe_public_id(
            raw["public_projection_id"], "public_projection_id"
        ),
        "public_projection_schema_version": PUBLIC_PROJECTION_SCHEMA,
        "public_projection_sha256": require_sha256(
            raw["public_projection_sha256"], "public_projection_sha256"
        ),
        "declared_dataset_roles": _require_id_list(
            raw["declared_dataset_roles"],
            "declared_dataset_roles",
            locator="declared_dataset_roles",
            public=True,
        ),
        "declared_use": require_nonempty_nfc(raw["declared_use"], "declared_use"),
        "date_universe_scope": require_nonempty_nfc(
            raw["date_universe_scope"], "date_universe_scope"
        ),
        "privacy_publication_scope": require_nonempty_nfc(
            raw["privacy_publication_scope"], "privacy_publication_scope"
        ),
        "applicable_contract_version": CONTRACT_VERSION,
        "decision": require_enum(raw["decision"], DECISION_STATES, "decision"),
        "findings": _validate_findings(raw["findings"]),
        "predecessor_decision_id": predecessor,
        "decision_canonicalization_id": CANONICALIZATION_ID,
        "public_decision_reference": require_safe_public_id(
            raw["public_decision_reference"], "public_decision_reference"
        ),
    }
    if expected_binding:
        for field, expected in expected_binding.items():
            if field not in projection:
                fail("UNEXPECTED_VALUE", field)
            if projection[field] != expected:
                fail("BINDING_MISMATCH", field)
    computed = canonical_sha256(projection)
    if verify_digest:
        stored = require_sha256(raw["decision_record_sha256"], "decision_record_sha256")
        if stored != computed:
            fail("DECISION_DIGEST_MISMATCH", "decision_record_sha256")
    return {**projection, "decision_record_sha256": computed}


def _validate_role_coverage(source: object, *, as_of_cutoff: str) -> list[dict[str, object]]:
    raw_roles = require_list(source, "role_coverage", locator="role_coverage")
    records: list[dict[str, object]] = []
    seen: set[str] = set()
    for index, raw_role in enumerate(raw_roles):
        locator = f"role_coverage[{index}]"
        item = require_exact_keys(
            raw_role, ROLE_COVERAGE_KEYS, "role_coverage", locator=locator
        )
        role = require_enum(
            item["role"],
            set(REQUIRED_FREEZE_ROLES),
            "role",
            locator=_join_locator(locator, "role"),
        )
        if role in seen:
            fail("DUPLICATE_ID", "role", locator=locator)
        seen.add(role)
        limitation_state = require_enum(
            item["limitation_state"],
            {"none", "counted_evidence_limitation"},
            "limitation_state",
            locator=_join_locator(locator, "limitation_state"),
        )
        limitation_id = item["limitation_id"]
        if limitation_state == "none":
            if limitation_id is not None:
                fail("TYPED_NULL", "limitation_id", locator=locator)
            limitation_id = None
        else:
            limitation_id = require_nonempty_nfc(
                limitation_id,
                "limitation_id",
                locator=_join_locator(locator, "limitation_id"),
            )
        coverage_start = require_date(
            item["coverage_start_inclusive"],
            "coverage_start_inclusive",
            locator=_join_locator(locator, "coverage_start_inclusive"),
        )
        coverage_end = require_date(
            item["coverage_end_inclusive"],
            "coverage_end_inclusive",
            locator=_join_locator(locator, "coverage_end_inclusive"),
        )
        _require_inclusive_coverage(
            coverage_start,
            coverage_end,
            locator=_join_locator(locator, "coverage_end_inclusive"),
        )
        _require_as_of_inside_coverage(
            _as_of_cutoff_date(as_of_cutoff),
            coverage_start,
            coverage_end,
            locator=locator,
        )
        records.append(
            {
                "role": role,
                "coverage_start_inclusive": coverage_start,
                "coverage_end_inclusive": coverage_end,
                "row_count": require_nonnegative_int(
                    item["row_count"],
                    "row_count",
                    locator=_join_locator(locator, "row_count"),
                ),
                "limitation_state": limitation_state,
                "limitation_id": limitation_id,
            }
        )
    if set(seen) != set(REQUIRED_FREEZE_ROLES):
        fail("MISSING_KEY", "role_coverage", locator="missing.required_role")
    return _sorted_objects(records, "role")


def _validate_coverage_labels(source: object) -> list[str]:
    labels = _require_id_list(source, "coverage_labels", locator="coverage_labels")
    if set(labels) != set(COVERAGE_LABELS):
        fail("UNEXPECTED_VALUE", "coverage_labels")
    return labels


def _validate_calendar(source: object) -> dict[str, object]:
    raw = require_exact_keys(source, CALENDAR_KEYS, "calendar")
    return {
        "calendar_id": require_literal(raw["calendar_id"], "XNYS", "calendar_id"),
        "calendar_version": require_nonempty_nfc(
            raw["calendar_version"], "calendar_version"
        ),
        "calendar_evidence_ref": _require_evidence_ref_id(
            raw["calendar_evidence_ref"],
            "calendar_evidence_ref",
            locator="calendar.calendar_evidence_ref",
        ),
        "source_timezone": require_nonempty_nfc(raw["source_timezone"], "source_timezone"),
        "utc_conversion_rule": require_nonempty_nfc(
            raw["utc_conversion_rule"], "utc_conversion_rule"
        ),
        "environment_id": require_nonempty_nfc(raw["environment_id"], "environment_id"),
        "environment_lock_sha256": require_sha256(
            raw["environment_lock_sha256"], "environment_lock_sha256"
        ),
    }


def _validate_lineage_and_terminal(source: object) -> dict[str, object]:
    raw = require_exact_keys(source, LINEAGE_KEYS, "lineage_and_terminal")
    terminal_state = require_enum(
        raw["terminal_event_policy_state"],
        {"owner_accepted", "candidate_not_accepted"},
        "terminal_event_policy_state",
    )
    terminal_hash = raw["terminal_event_policy_sha256"]
    if terminal_state == "owner_accepted":
        terminal_hash = require_sha256(
            terminal_hash, "terminal_event_policy_sha256"
        )
    else:
        if terminal_hash is not None:
            fail("TYPED_NULL", "terminal_event_policy_sha256")
        terminal_hash = None
    return {
        "membership_policy_id": require_nonempty_nfc(
            raw["membership_policy_id"], "membership_policy_id"
        ),
        "membership_policy_sha256": require_sha256(
            raw["membership_policy_sha256"], "membership_policy_sha256"
        ),
        "snapshot_authority": require_literal(
            raw["snapshot_authority"], "snapshot_primary", "snapshot_authority"
        ),
        "as_of_rule": require_literal(
            raw["as_of_rule"], "s_eq_max_snapshot_date_le_t", "as_of_rule"
        ),
        "carry_forward": require_literal(
            raw["carry_forward"],
            "event_driven_no_fixed_age_limit",
            "carry_forward",
        ),
        "baseline_date": require_literal(
            raw["baseline_date"], "2014-01-24", "baseline_date"
        ),
        "pre_baseline_claims": require_literal(
            raw["pre_baseline_claims"], "forbidden", "pre_baseline_claims"
        ),
        "invented_start_date": require_literal(
            raw["invented_start_date"], "forbidden", "invented_start_date"
        ),
        "start_date_boundary": require_literal(
            raw["start_date_boundary"], "inclusive", "start_date_boundary"
        ),
        "end_date_boundary": require_literal(
            raw["end_date_boundary"], "exclusive", "end_date_boundary"
        ),
        "interval_notation": require_literal(
            raw["interval_notation"], "[StartDate, EndDate)", "interval_notation"
        ),
        "factor_anchor_lineage_id": require_literal(
            raw["factor_anchor_lineage_id"],
            "factor_anchor_lineage_v1",
            "factor_anchor_lineage_id",
        ),
        "terminal_event_policy_state": terminal_state,
        "terminal_event_policy_sha256": terminal_hash,
    }


def _validate_exclusions(source: object) -> list[dict[str, object]]:
    raw_items = require_list(source, "exclusions", locator="exclusions")
    records: list[dict[str, object]] = []
    seen_classes: set[str] = set()
    seen_ids: set[str] = set()
    for index, raw_item in enumerate(raw_items):
        locator = f"exclusions[{index}]"
        item = require_exact_keys(
            raw_item, EXCLUSION_KEYS, "exclusion", locator=locator
        )
        exclusion_id = require_nonempty_nfc(
            item["exclusion_id"],
            "exclusion_id",
            locator=_join_locator(locator, "exclusion_id"),
        )
        if exclusion_id in seen_ids:
            fail("DUPLICATE_ID", "exclusion_id", locator=locator)
        seen_ids.add(exclusion_id)
        exclusion_class = require_enum(
            item["exclusion_class"],
            set(EXCLUSION_CLASSES),
            "exclusion_class",
            locator=_join_locator(locator, "exclusion_class"),
        )
        if exclusion_class in seen_classes:
            fail("DUPLICATE_ID", "exclusion_class", locator=locator)
        seen_classes.add(exclusion_class)
        records.append(
            {
                "exclusion_id": exclusion_id,
                "exclusion_class": exclusion_class,
                "count": require_nonnegative_int(
                    item["count"], "count", locator=_join_locator(locator, "count")
                ),
                "evidence_sha256": require_sha256(
                    item["evidence_sha256"],
                    "evidence_sha256",
                    locator=_join_locator(locator, "evidence_sha256"),
                ),
            }
        )
    if set(seen_classes) != set(EXCLUSION_CLASSES):
        fail("MISSING_KEY", "exclusions", locator="missing.exclusion_class")
    return _sorted_objects(records, "exclusion_id")


def _validate_coverage_thresholds(source: object) -> dict[str, object]:
    raw = require_exact_keys(source, COVERAGE_THRESHOLD_KEYS, "coverage_thresholds")
    triggers = require_list(raw["zero_target_triggers"], "zero_target_triggers")
    normalized = [
        require_nonempty_nfc(
            item,
            "zero_target_triggers",
            locator=f"zero_target_triggers[{index}]",
        )
        for index, item in enumerate(triggers)
    ]
    if normalized != list(ZERO_TARGET_TRIGGERS):
        fail("UNEXPECTED_VALUE", "zero_target_triggers")
    floor_100 = require_nonnegative_int(
        raw["factor_month_eligible_listing_floor"],
        "factor_month_eligible_listing_floor",
    )
    floor_10 = require_nonnegative_int(
        raw["distinct_finite_factor_value_floor"],
        "distinct_finite_factor_value_floor",
    )
    floor_60 = require_nonnegative_int(
        raw["common_complete_case_month_floor"],
        "common_complete_case_month_floor",
    )
    if floor_100 != 100 or floor_10 != 10 or floor_60 != 60:
        fail("UNEXPECTED_VALUE", "coverage_thresholds")
    return {
        "factor_month_eligible_listing_floor": 100,
        "distinct_finite_factor_value_floor": 10,
        "common_complete_case_month_floor": 60,
        "zero_target_triggers": list(ZERO_TARGET_TRIGGERS),
    }


def _validate_materiality_thresholds(source: object) -> dict[str, object]:
    raw = require_exact_keys(source, MATERIALITY_KEYS, "materiality_thresholds")
    state = require_enum(
        raw["state"], {"proposed", "owner_approved"}, "state"
    )
    require_literal(
        raw["performance_informed_selection"],
        "FORBIDDEN",
        "performance_informed_selection",
    )
    raw_thresholds = require_list(raw["thresholds"], "thresholds", locator="thresholds")
    thresholds: list[dict[str, object]] = []
    seen: set[str] = set()
    for index, raw_item in enumerate(raw_thresholds):
        locator = f"thresholds[{index}]"
        item = require_exact_keys(
            raw_item,
            MATERIALITY_THRESHOLD_KEYS,
            "materiality_threshold",
            locator=locator,
        )
        threshold_id = require_nonempty_nfc(
            item["threshold_id"],
            "threshold_id",
            locator=_join_locator(locator, "threshold_id"),
        )
        if threshold_id in seen:
            fail("DUPLICATE_ID", "threshold_id", locator=locator)
        seen.add(threshold_id)
        thresholds.append(
            {
                "threshold_id": threshold_id,
                "value": require_decimal_string(
                    item["value"], "value", locator=_join_locator(locator, "value")
                ),
                "evidence_sha256": require_sha256(
                    item["evidence_sha256"],
                    "evidence_sha256",
                    locator=_join_locator(locator, "evidence_sha256"),
                ),
            }
        )
    return {
        "state": state,
        "performance_informed_selection": "FORBIDDEN",
        "thresholds": _sorted_objects(thresholds, "threshold_id"),
    }


def _validate_contract_binding(source: object) -> dict[str, object]:
    raw = require_exact_keys(source, CONTRACT_BINDING_KEYS, "contract_binding")
    require_literal(raw["contract_id"], CONTRACT_ID, "contract_id")
    require_literal(raw["contract_version"], CONTRACT_VERSION, "contract_version")
    require_literal(
        raw["contract_content_sha256"],
        CONTRACT_CONTENT_SHA256,
        "contract_content_sha256",
    )
    return {
        "contract_id": CONTRACT_ID,
        "contract_version": CONTRACT_VERSION,
        "contract_content_sha256": CONTRACT_CONTENT_SHA256,
        "contract_protected_merge_sha": require_code_sha(
            raw["contract_protected_merge_sha"], "contract_protected_merge_sha"
        ),
    }


def _validate_identity_fail_closed(source: object) -> dict[str, object]:
    raw = require_exact_keys(source, IDENTITY_FAIL_CLOSED_KEYS, "identity_fail_closed")
    adjudicated = require_nonnegative_int(
        raw["identities_adjudicated"], "identities_adjudicated"
    )
    accepted = require_nonnegative_int(raw["accepted_identities"], "accepted_identities")
    if accepted > adjudicated:
        fail("UNEXPECTED_VALUE", "accepted_identities")
    return {
        "identities_adjudicated": adjudicated,
        "accepted_identities": accepted,
        "disposition": require_literal(
            raw["disposition"],
            "A_ACCEPT_TERMINAL_FAIL_CLOSED",
            "disposition",
        ),
        "effect": require_literal(
            raw["effect"],
            "UNRESOLVED_IDENTITIES_ROUTE_THROUGH_FROZEN_DECISION_TIME_ELIGIBILITY_AS_COUNTED_INELIGIBILITY",
            "effect",
        ),
        "scope": require_literal(
            raw["scope"],
            "only_adjudicated_unresolved_identities_and_affected_episodes",
            "scope",
        ),
    }


def project_freeze_record(
    source: object,
    *,
    verify_digest: bool = True,
) -> dict[str, object]:
    raw = require_exact_keys(source, FREEZE_KEYS, "track_a_pr2_freeze_record")
    require_literal(raw["schema_version"], FREEZE_RECORD_SCHEMA, "schema_version")
    require_literal(raw["canonicalization_id"], CANONICALIZATION_ID, "canonicalization_id")
    as_of_cutoff = normalize_timestamp(raw["as_of_cutoff"], "as_of_cutoff")
    projection = {
        "schema_version": FREEZE_RECORD_SCHEMA,
        "freeze_record_id": require_nonempty_nfc(
            raw["freeze_record_id"], "freeze_record_id"
        ),
        "canonicalization_id": CANONICALIZATION_ID,
        "as_of_cutoff": as_of_cutoff,
        "role_coverage": _validate_role_coverage(
            raw["role_coverage"], as_of_cutoff=as_of_cutoff
        ),
        "coverage_labels": _validate_coverage_labels(raw["coverage_labels"]),
        "calendar": _validate_calendar(raw["calendar"]),
        "lineage_and_terminal": _validate_lineage_and_terminal(raw["lineage_and_terminal"]),
        "exclusions": _validate_exclusions(raw["exclusions"]),
        "coverage_thresholds": _validate_coverage_thresholds(raw["coverage_thresholds"]),
        "materiality_thresholds": _validate_materiality_thresholds(
            raw["materiality_thresholds"]
        ),
        "contract_binding": _validate_contract_binding(raw["contract_binding"]),
        "identity_fail_closed": _validate_identity_fail_closed(
            raw["identity_fail_closed"]
        ),
    }
    computed = canonical_sha256(projection)
    if verify_digest:
        stored = require_sha256(raw["freeze_record_sha256"], "freeze_record_sha256")
        if stored != computed:
            fail("FREEZE_DIGEST_MISMATCH", "freeze_record_sha256")
    return {**projection, "freeze_record_sha256": computed}


KIND_PROJECTORS = {
    "pit_canonical_json_v1": lambda source: source,
    "ordered_component_inventory_v1": project_ordered_component_inventory,
    "public_redacted_projection_v1": project_public_redacted_projection,
    "private_full_manifest": project_private_full_manifest,
    "dataset_review_decision": project_dataset_review_decision,
    "track_a_pr2_freeze_record_v1": project_freeze_record,
}


SCHEMA_VERSION_TO_KIND = {
    ORDERED_INVENTORY_SCHEMA: "ordered_component_inventory_v1",
    PUBLIC_PROJECTION_SCHEMA: "public_redacted_projection_v1",
    PRIVATE_FULL_MANIFEST_SCHEMA: "private_full_manifest",
    DECISION_RECORD_SCHEMA: "dataset_review_decision",
    FREEZE_RECORD_SCHEMA: "track_a_pr2_freeze_record_v1",
}


def infer_kind(source: object) -> str:
    mapping = require_mapping(source, "document")
    if "schema_version" not in mapping:
        return "pit_canonical_json_v1"
    schema_version = mapping["schema_version"]
    if not isinstance(schema_version, str):
        fail("NOT_STRING", "schema_version")
    kind = SCHEMA_VERSION_TO_KIND.get(schema_version)
    if kind is None:
        fail("UNKNOWN_SCHEMA_VERSION", "schema_version")
    return kind


def project_kind(source: object, kind: str) -> dict[str, Any] | object:
    if kind not in KIND_PROJECTORS:
        fail("UNEXPECTED_VALUE", "kind")
    return KIND_PROJECTORS[kind](source)


def validate_document(
    source: object,
    kind: str | None = None,
    *,
    expected_binding: Mapping[str, str] | None = None,
) -> dict[str, object]:
    resolved_kind = kind or infer_kind(source)
    if resolved_kind == "dataset_review_decision":
        projection = project_dataset_review_decision(
            source, expected_binding=expected_binding
        )
    else:
        projection = project_kind(source, resolved_kind)
    identity = (
        _identity_projection(projection, resolved_kind)
        if isinstance(projection, dict)
        else projection
    )
    payload = canonical_utf8(identity)
    return {
        "kind": resolved_kind,
        "projection": projection,
        "canonical_utf8": payload,
        "sha256": canonical_sha256(identity),
    }


def validate_bytes(
    raw: bytes,
    kind: str | None = None,
    *,
    expected_binding: Mapping[str, str] | None = None,
) -> dict[str, object]:
    return validate_document(
        parse_json_bytes(raw),
        kind,
        expected_binding=expected_binding,
    )


# Re-export NFC helper used by tests that construct IDs.
__all__ = [
    "CONTRACT_CONTENT_SHA256",
    "CONTRACT_ID",
    "CONTRACT_VERSION",
    "DECISION_STATES",
    "ValidationError",
    "build_ordered_component_inventory",
    "infer_kind",
    "ordered_manifest_sha256",
    "project_dataset_review_decision",
    "project_freeze_record",
    "project_ordered_component_inventory",
    "project_private_full_manifest",
    "project_public_redacted_projection",
    "public_projection_sha256",
    "validate_bytes",
    "validate_document",
    "validate_physical_component",
]

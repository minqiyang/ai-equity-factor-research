"""Fail-closed acceptance, grant, protocol, and detached-binding gates."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
import re
from types import MappingProxyType

from pit_manifest_validator_v1.canonical import (
    CANONICALIZATION_ID,
    ValidationError,
    canonical_sha256,
    normalize_timestamp,
    parse_json_bytes,
    sha256_hex,
)


IDENTITY_EXCLUDE = frozenset(
    {
        "signatures",
        "presentation_notes",
        "acceptance_record_sha256",
    }
)

_STATUS_AUTHORIZED = "AUTHORIZED"
_STATUS_REFUSED = "REFUSED"

_REASON_FILE_BYTES = "ACCEPTANCE_RECORD_FILE_BYTES_MISMATCH"
_REASON_UNPARSEABLE = "ACCEPTANCE_RECORD_UNPARSEABLE"
_REASON_SCHEMA = "ACCEPTANCE_RECORD_SCHEMA_INVALID"
_REASON_SELF_IDENTITY = "ACCEPTANCE_RECORD_IDENTITY_SELF_INCONSISTENT"
_REASON_BOUND_IDENTITY = "ACCEPTANCE_IDENTITY_NOT_THE_BOUND_IDENTITY"
_REASON_PROTOCOL = "PROTOCOL_FREEZE_BYTES_MISMATCH"
_REASON_INVENTORY = "TRIAL_INVENTORY_BYTES_MISMATCH"
_REASON_BINDING_ABSENT = "DETACHED_BINDING_ABSENT"
_REASON_BINDING_FIELD = "DETACHED_BINDING_FIELD_MISMATCH"
_REASON_TIMESTAMP = "TIMESTAMP_NOT_TZ_AWARE"
_REASON_GRANT_BYTES = "STAGE2_GRANT_FILE_BYTES_MISMATCH"
_REASON_GRANT_UNPARSEABLE = "STAGE2_GRANT_UNPARSEABLE"
_REASON_GRANT_SCHEMA = "STAGE2_GRANT_SCHEMA_INVALID"
_REASON_BINDING_UNPARSEABLE = "DETACHED_BINDING_UNPARSEABLE"
_REASON_BINDING_SCHEMA = "DETACHED_BINDING_SCHEMA_INVALID"
_REASON_ACCEPTANCE_ABSENT = "ACCEPTANCE_RECORD_ABSENT"
_REASON_GRANT_ABSENT = "STAGE2_GRANT_ABSENT"
_REASON_PROTOCOL_ABSENT = "PROTOCOL_FREEZE_ABSENT"
_REASON_INVENTORY_ABSENT = "TRIAL_INVENTORY_ABSENT"
_REASON_CALENDAR_ID = "CALENDAR_ID_MISMATCH"
_REASON_CALENDAR_VERSION = "CALENDAR_VERSION_MISMATCH"
_REASON_ENVIRONMENT_ID = "ENVIRONMENT_ID_MISMATCH"
_REASON_ENVIRONMENT_LOCK = "ENVIRONMENT_LOCK_SHA256_MISMATCH"
_REASON_ELIGIBLE_FORBIDDEN_STAGE = "GRANT_NOW_ELIGIBLE_AUTHORIZES_FORBIDDEN_STAGE"
_REASON_INTENDED_STAGE_FORBIDDEN = "GRANT_DOES_NOT_AUTHORIZE_TRACK_A_PR3_PLANNING"
_REASON_FOURTEEN_TRIAL_FORBIDDEN = "GRANT_DOES_NOT_AUTHORIZE_FOURTEEN_TRIAL_RUN"
_REASON_RESULT_ACCESS_FORBIDDEN = "GRANT_DOES_NOT_AUTHORIZE_RESULT_ACCESS"
_REASON_PERFORMANCE_ACCESS_FORBIDDEN = "GRANT_DOES_NOT_AUTHORIZE_PERFORMANCE_ACCESS"
_REASON_ELIGIBLE_NOT_CAMPAIGN_RUN = (
    "GRANT_NOW_ELIGIBLE_DOES_NOT_AUTHORIZE_CAMPAIGN_RUN"
)
_STAGE_PR3_PLANNING = "TRACK_A_PR3_PLANNING"
_STAGE_FOURTEEN_TRIAL = "FOURTEEN_TRIAL_RUN"
_STAGE_RESULT_ACCESS = "RESULT_ACCESS"
_STAGE_PERFORMANCE_ACCESS = "PERFORMANCE_ACCESS"
_RESULT_BEARING_STAGES = frozenset(
    {
        _STAGE_FOURTEEN_TRIAL,
        _STAGE_RESULT_ACCESS,
        _STAGE_PERFORMANCE_ACCESS,
    }
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_DATE_ONLY_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_NAIVE_TIMESTAMP_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?$"
)

_ACCEPTANCE_TOP = frozenset(
    {
        "schema_version",
        "acceptance_record_id",
        "canonicalization_id",
        "accepted_at_utc",
        "dataset_acceptance",
        "declared_use",
        "evidence_ceiling",
        "as_of_cutoff",
        "canonical_manifest_sha256",
        "public_projection_id",
        "public_projection_sha256",
        "freeze_record_sha256",
        "review_decision_id",
        "review_decision",
        "decision_record_sha256",
        "decision_file_sha256",
        "reviewer_id",
        "reviewer_authority_reference",
        "reviewer_appointment_sha256",
        "calendar",
        "lineage_and_terminal",
        "exclusions",
        "coverage_thresholds",
        "identity_fail_closed",
        "materiality_thresholds",
        "contract_binding",
        "stage2_status",
        "stage2_decision_sha256",
        "terminal_event_policy",
        "materialization",
        "performance_access",
        "result_access",
        "does_not_authorize",
        "acceptance_record_sha256",
    }
)
_CALENDAR_KEYS = frozenset(
    {
        "calendar_id",
        "calendar_version",
        "calendar_evidence_ref",
        "source_timezone",
        "utc_conversion_rule",
        "environment_id",
        "environment_lock_sha256",
    }
)
_LINEAGE_KEYS = frozenset(
    {
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
)
_COVERAGE_KEYS = frozenset(
    {
        "factor_month_eligible_listing_floor",
        "distinct_finite_factor_value_floor",
        "common_complete_case_month_floor",
        "zero_target_triggers",
    }
)
_IDENTITY_FAIL_CLOSED_KEYS = frozenset(
    {
        "identities_adjudicated",
        "accepted_identities",
        "disposition",
        "effect",
        "scope",
    }
)
_MATERIALITY_KEYS = frozenset(
    {
        "state",
        "performance_informed_selection",
        "proposal_sha256",
        "approval_sha256",
        "thresholds",
    }
)
_THRESHOLD_KEYS = frozenset(
    {
        "threshold_id",
        "class",
        "metric",
        "comparator",
        "value",
        "reviewed_value",
    }
)
_EXCLUSION_KEYS = frozenset(
    {
        "exclusion_id",
        "exclusion_class",
        "count",
        "evidence_sha256",
    }
)
_CONTRACT_KEYS = frozenset(
    {
        "contract_id",
        "contract_version",
        "contract_content_sha256",
        "contract_protected_merge_sha",
    }
)
_TERMINAL_POLICY_KEYS = frozenset(
    {
        "state",
        "owner_defer_sha256",
        "policy_sha256",
    }
)
_GRANT_TOP = frozenset(
    {
        "artifact_id",
        "decision_id",
        "status",
        "owner_authorization",
        "operating_standard",
        "operating_standard_sha256",
        "granted_at_utc",
        "choice",
        "roadmap_stage2",
        "dataset_acceptance",
        "review_decision",
        "acceptance_record_file_sha256",
        "acceptance_record_sha256",
        "materiality_proposal_sha256",
        "gate",
        "review_file_sha256",
        "now_eligible",
        "does_not_authorize",
    }
)
_GRANT_GATE_KEYS = frozenset({"qa", "grok", "sol", "fable", "result"})
_GRANT_REVIEW_FILE_KEYS = frozenset({"grok", "sol"})
_BINDING_TOP = frozenset(
    {
        "schema_version",
        "runner_code_sha",
        "environment_id",
        "environment_lock_sha256",
        "calendar_id",
        "calendar_version",
        "protocol_file_sha256",
        "trial_inventory_file_sha256",
        "acceptance_record_file_sha256",
        "acceptance_identity_sha256",
        "bound_at_utc",
    }
)

_ACCEPTANCE_SCHEMA = "blinded_dataset_acceptance_record_v1"
_DATASET_ACCEPTANCE = "DIAGNOSTIC_READY"
_DECLARED_USE = "diagnostic-campaign"
_EVIDENCE_CEILING = "DIAGNOSTIC_ONLY"
_REVIEW_DECISION = "diagnostic_only"
_PERFORMANCE_ACCESS = "FORBIDDEN"
_RESULT_ACCESS = "FORBIDDEN"
_MATERIALIZATION = "NOT_ENTERED"
_GRANT_STATUS = "ANSWERED_BOUND"
_GRANT_CHOICE = "GRANT_STAGE2_DIAGNOSTIC_READY"
_ROADMAP_STAGE2 = "COMPLETE"
_GATE_RESULT = "UNANIMOUS_3_OF_3"

_P2_RECORD_CHECKS = (
    ("schema_version", _ACCEPTANCE_SCHEMA, "SCHEMA_VERSION_NOT_BOUND"),
    ("canonicalization_id", CANONICALIZATION_ID, "CANONICALIZATION_ID_NOT_BOUND"),
    ("dataset_acceptance", _DATASET_ACCEPTANCE, "DATASET_ACCEPTANCE_NOT_DIAGNOSTIC_READY"),
    ("declared_use", _DECLARED_USE, "DECLARED_USE_NOT_DIAGNOSTIC_CAMPAIGN"),
    ("evidence_ceiling", _EVIDENCE_CEILING, "EVIDENCE_CEILING_NOT_DIAGNOSTIC_ONLY"),
    ("review_decision", _REVIEW_DECISION, "REVIEW_DECISION_NOT_DIAGNOSTIC_ONLY"),
    ("performance_access", _PERFORMANCE_ACCESS, "PERFORMANCE_ACCESS_NOT_FORBIDDEN"),
    ("result_access", _RESULT_ACCESS, "RESULT_ACCESS_NOT_FORBIDDEN"),
    ("materialization", _MATERIALIZATION, "MATERIALIZATION_NOT_THE_BOUND_VALUE"),
)
_P2_GRANT_CHECKS = (
    ("status", _GRANT_STATUS, "GRANT_STATUS_NOT_ANSWERED_BOUND"),
    ("choice", _GRANT_CHOICE, "GRANT_CHOICE_NOT_GRANT_STAGE2_DIAGNOSTIC_READY"),
    ("roadmap_stage2", _ROADMAP_STAGE2, "GRANT_ROADMAP_STAGE2_NOT_COMPLETE"),
)


@dataclass(frozen=True)
class Authorization:
    """Named fail-closed result of the P-1 through P-5 chain."""

    status: str
    reason: str | None
    counter: int
    record: MappingProxyType[str, object] | None
    grant: MappingProxyType[str, object] | None
    binding: MappingProxyType[str, object] | None


def authorize(config: object) -> Authorization:
    """Return AUTHORIZED only after P-1 through P-5 succeed in order."""

    raw = _read_octets(
        getattr(config, "acceptance_record_file"),
        _REASON_ACCEPTANCE_ABSENT,
    )
    if isinstance(raw, Authorization):
        return raw
    expected_file = _hex64(
        getattr(config, "acceptance_record_file_sha256"),
        "acceptance_record_file_sha256",
    )
    if sha256_hex(raw) != expected_file:
        return _refuse(_REASON_FILE_BYTES)

    try:
        parsed = parse_json_bytes(raw)
    except ValidationError:
        return _refuse(_REASON_UNPARSEABLE)
    if not isinstance(parsed, dict):
        return _refuse(_REASON_SCHEMA)

    schema_error = _validate_acceptance_schema(parsed)
    if schema_error is not None:
        return _refuse(schema_error)

    expected_identity = _hex64(
        getattr(config, "acceptance_identity_sha256"),
        "acceptance_identity_sha256",
    )
    computed_identity = project_acceptance_identity(parsed)
    stored_identity = parsed["acceptance_record_sha256"]
    if not _is_sha256(stored_identity) or computed_identity != stored_identity:
        return _refuse(_REASON_SELF_IDENTITY)
    if computed_identity != expected_identity:
        return _refuse(_REASON_BOUND_IDENTITY)

    grant_loaded = _load_grant(config)
    if isinstance(grant_loaded, Authorization):
        return grant_loaded
    grant = grant_loaded

    record_auth = _authorize_record_fields(config, parsed)
    if record_auth is not None:
        return record_auth
    grant_auth = _authorize_grant_fields(config, parsed, grant)
    if grant_auth is not None:
        return grant_auth

    protocol_raw = _read_octets(
        getattr(config, "protocol_file"),
        _REASON_PROTOCOL_ABSENT,
    )
    if isinstance(protocol_raw, Authorization):
        return protocol_raw
    if sha256_hex(protocol_raw) != _hex64(
        getattr(config, "protocol_file_sha256"),
        "protocol_file_sha256",
    ):
        return _refuse(_REASON_PROTOCOL)
    inventory_raw = _read_octets(
        getattr(config, "trial_inventory_file"),
        _REASON_INVENTORY_ABSENT,
    )
    if isinstance(inventory_raw, Authorization):
        return inventory_raw
    if sha256_hex(inventory_raw) != _hex64(
        getattr(config, "trial_inventory_file_sha256"),
        "trial_inventory_file_sha256",
    ):
        return _refuse(_REASON_INVENTORY)

    binding_result = _authorize_binding(config)
    if isinstance(binding_result, Authorization):
        return binding_result
    return Authorization(
        _STATUS_AUTHORIZED,
        None,
        0,
        MappingProxyType(parsed),
        MappingProxyType(grant),
        MappingProxyType(binding_result),
    )


def result_bearing_refusal_reason(grant: object) -> str | None:
    """Return the named refusal if the grant does not authorize a campaign run."""

    if not isinstance(grant, Mapping):
        raise TypeError("grant must be a mapping")
    eligible = grant.get("now_eligible")
    forbidden = grant.get("does_not_authorize")
    if not _string_list(eligible) or not _string_list(forbidden):
        raise TypeError("grant eligibility lists must be string lists")
    assert isinstance(eligible, list)
    assert isinstance(forbidden, list)
    if _STAGE_FOURTEEN_TRIAL in forbidden:
        return _REASON_FOURTEEN_TRIAL_FORBIDDEN
    if _STAGE_RESULT_ACCESS in forbidden:
        return _REASON_RESULT_ACCESS_FORBIDDEN
    if _STAGE_PERFORMANCE_ACCESS in forbidden:
        return _REASON_PERFORMANCE_ACCESS_FORBIDDEN
    if _STAGE_FOURTEEN_TRIAL not in eligible:
        return _REASON_ELIGIBLE_NOT_CAMPAIGN_RUN
    return None


def project_acceptance_identity(record: object) -> str:
    """Return the CANONICAL_IDENTITY digest of one acceptance record."""

    if not isinstance(record, dict):
        raise TypeError("record must be an object")
    projection = {
        key: value
        for key, value in record.items()
        if key not in IDENTITY_EXCLUDE
    }
    return canonical_sha256(projection)


def _authorize_record_fields(
    config: object,
    record: dict[str, object],
) -> Authorization | None:
    timestamp_error = _normalize_record_timestamps(record)
    if timestamp_error is not None:
        return _refuse(timestamp_error)
    for field, required, reason in _P2_RECORD_CHECKS:
        if record[field] != required:
            return _refuse(reason)
    authority_error = _review_authority_error(record)
    if authority_error is not None:
        return _refuse(authority_error)
    if record["decision_file_sha256"] != _hex64(
        getattr(config, "decision_file_sha256"),
        "decision_file_sha256",
    ):
        return _refuse("DECISION_FILE_BYTES_MISMATCH")
    if record["decision_record_sha256"] != _hex64(
        getattr(config, "decision_identity_sha256"),
        "decision_identity_sha256",
    ):
        return _refuse("DECISION_IDENTITY_NOT_THE_BOUND_IDENTITY")
    calendar = record["calendar"]
    assert isinstance(calendar, dict)
    if calendar["calendar_id"] != getattr(config, "calendar_id"):
        return _refuse(_REASON_CALENDAR_ID)
    if calendar["calendar_version"] != getattr(config, "calendar_version"):
        return _refuse(_REASON_CALENDAR_VERSION)
    if calendar["environment_id"] != getattr(config, "environment_id"):
        return _refuse(_REASON_ENVIRONMENT_ID)
    if calendar["environment_lock_sha256"] != getattr(
        config, "environment_lock_sha256"
    ):
        return _refuse(_REASON_ENVIRONMENT_LOCK)
    return None


def _load_grant(config: object) -> Authorization | dict[str, object]:
    raw = _read_octets(
        getattr(config, "stage2_grant_file"),
        _REASON_GRANT_ABSENT,
    )
    if isinstance(raw, Authorization):
        return raw
    if sha256_hex(raw) != _hex64(
        getattr(config, "stage2_grant_file_sha256"),
        "stage2_grant_file_sha256",
    ):
        return _refuse(_REASON_GRANT_BYTES)
    try:
        parsed = parse_json_bytes(raw)
    except ValidationError:
        return _refuse(_REASON_GRANT_UNPARSEABLE)
    if not _grant_schema_valid(parsed):
        return _refuse(_REASON_GRANT_SCHEMA)
    assert isinstance(parsed, dict)
    granted_at = _as_utc_timestamp(parsed["granted_at_utc"])
    if granted_at is None:
        return _refuse(_REASON_TIMESTAMP)
    parsed["granted_at_utc"] = granted_at
    return parsed


def _authorize_grant_fields(
    config: object,
    record: dict[str, object],
    grant: dict[str, object],
) -> Authorization | None:
    for field, required, reason in _P2_GRANT_CHECKS:
        if grant[field] != required:
            return _refuse(reason)
    gate = grant["gate"]
    assert isinstance(gate, dict)
    if gate["result"] != _GATE_RESULT:
        return _refuse("GRANT_GATE_RESULT_NOT_UNANIMOUS")
    if grant["dataset_acceptance"] != record["dataset_acceptance"]:
        return _refuse("GRANT_DATASET_ACCEPTANCE_MISMATCH")
    if grant["review_decision"] != record["review_decision"]:
        return _refuse("GRANT_REVIEW_DECISION_MISMATCH")
    if grant["acceptance_record_file_sha256"] != _hex64(
        getattr(config, "acceptance_record_file_sha256"),
        "acceptance_record_file_sha256",
    ):
        return _refuse("GRANT_ACCEPTANCE_FILE_BYTES_MISMATCH")
    if grant["acceptance_record_sha256"] != _hex64(
        getattr(config, "acceptance_identity_sha256"),
        "acceptance_identity_sha256",
    ):
        return _refuse("GRANT_ACCEPTANCE_IDENTITY_MISMATCH")
    eligible = grant["now_eligible"]
    forbidden = grant["does_not_authorize"]
    assert isinstance(eligible, list)
    assert isinstance(forbidden, list)
    if any(stage in eligible for stage in _RESULT_BEARING_STAGES):
        return _refuse(_REASON_ELIGIBLE_FORBIDDEN_STAGE)
    if _STAGE_PR3_PLANNING in forbidden:
        return _refuse(_REASON_INTENDED_STAGE_FORBIDDEN)
    if _STAGE_PR3_PLANNING not in eligible:
        return _refuse(_REASON_INTENDED_STAGE_FORBIDDEN)
    return None


def _authorize_binding(config: object) -> Authorization | dict[str, object]:
    raw = _read_octets(
        getattr(config, "detached_binding_file"),
        _REASON_BINDING_ABSENT,
    )
    if isinstance(raw, Authorization):
        return raw
    try:
        parsed = parse_json_bytes(raw)
    except ValidationError:
        return _refuse(_REASON_BINDING_UNPARSEABLE)
    if not _binding_schema_valid(parsed):
        return _refuse(_REASON_BINDING_SCHEMA)
    assert isinstance(parsed, dict)
    bound_at = _as_utc_timestamp(parsed["bound_at_utc"])
    if bound_at is None:
        return _refuse(_REASON_TIMESTAMP)
    parsed["bound_at_utc"] = bound_at
    expected = {
        "runner_code_sha": getattr(config, "runner_code_sha"),
        "environment_id": getattr(config, "environment_id"),
        "environment_lock_sha256": getattr(config, "environment_lock_sha256"),
        "calendar_id": getattr(config, "calendar_id"),
        "calendar_version": getattr(config, "calendar_version"),
        "protocol_file_sha256": getattr(config, "protocol_file_sha256"),
        "trial_inventory_file_sha256": getattr(
            config, "trial_inventory_file_sha256"
        ),
        "acceptance_record_file_sha256": getattr(
            config, "acceptance_record_file_sha256"
        ),
        "acceptance_identity_sha256": getattr(
            config, "acceptance_identity_sha256"
        ),
    }
    for field, wanted in expected.items():
        if parsed[field] != wanted:
            return _refuse(_REASON_BINDING_FIELD)
    return parsed


def _validate_acceptance_schema(record: dict[str, object]) -> str | None:
    if set(record) != _ACCEPTANCE_TOP:
        return _REASON_SCHEMA
    string_fields = (
        "schema_version",
        "acceptance_record_id",
        "canonicalization_id",
        "dataset_acceptance",
        "declared_use",
        "evidence_ceiling",
        "public_projection_id",
        "review_decision_id",
        "review_decision",
        "reviewer_id",
        "reviewer_authority_reference",
        "stage2_status",
        "materialization",
        "performance_access",
        "result_access",
    )
    for field in string_fields:
        if not _nonempty_string(record[field]):
            return _REASON_SCHEMA
    sha_fields = (
        "canonical_manifest_sha256",
        "public_projection_sha256",
        "freeze_record_sha256",
        "decision_record_sha256",
        "decision_file_sha256",
        "reviewer_appointment_sha256",
        "stage2_decision_sha256",
        "acceptance_record_sha256",
    )
    for field in sha_fields:
        if not _is_sha256(record[field]):
            return _REASON_SCHEMA
    if _as_utc_timestamp(record["accepted_at_utc"]) is None:
        return _REASON_TIMESTAMP
    if _as_utc_timestamp(record["as_of_cutoff"]) is None:
        return _REASON_TIMESTAMP
    if not _calendar_valid(record["calendar"]):
        return _REASON_SCHEMA
    if not _lineage_valid(record["lineage_and_terminal"]):
        return _REASON_SCHEMA
    if not _exclusions_valid(record["exclusions"]):
        return _REASON_SCHEMA
    if not _coverage_valid(record["coverage_thresholds"]):
        return _REASON_SCHEMA
    if not _mapping_strings(
        record["identity_fail_closed"],
        _IDENTITY_FAIL_CLOSED_KEYS,
        ints=("identities_adjudicated", "accepted_identities"),
    ):
        return _REASON_SCHEMA
    if not _materiality_valid(record["materiality_thresholds"]):
        return _REASON_SCHEMA
    if not _mapping_strings(
        record["contract_binding"],
        _CONTRACT_KEYS,
        shas=("contract_content_sha256",),
        git=("contract_protected_merge_sha",),
    ):
        return _REASON_SCHEMA
    if not _terminal_policy_valid(record["terminal_event_policy"]):
        return _REASON_SCHEMA
    if not _string_list(record["does_not_authorize"]):
        return _REASON_SCHEMA
    return None


def _calendar_valid(value: object) -> bool:
    return _mapping_strings(
        value,
        _CALENDAR_KEYS,
        shas=("environment_lock_sha256",),
    )


def _lineage_valid(value: object) -> bool:
    if not _exact_keys(value, _LINEAGE_KEYS):
        return False
    assert isinstance(value, dict)
    nullable = {"terminal_event_policy_sha256"}
    sha_fields = {"membership_policy_sha256"}
    for key, item in value.items():
        if key in nullable:
            if item is None:
                continue
            if not _is_sha256(item):
                return False
            continue
        if key in sha_fields and not _is_sha256(item):
            return False
        if key not in sha_fields and not _nonempty_string(item):
            return False
    return True


def _exclusions_valid(value: object) -> bool:
    if not isinstance(value, list):
        return False
    for item in value:
        if not _exact_keys(item, _EXCLUSION_KEYS):
            return False
        assert isinstance(item, dict)
        if not _nonempty_string(item["exclusion_id"]):
            return False
        if not _nonempty_string(item["exclusion_class"]):
            return False
        if not _is_sha256(item["evidence_sha256"]):
            return False
        if isinstance(item["count"], bool) or not isinstance(item["count"], int):
            return False
        if item["count"] < 0:
            return False
    return True


def _coverage_valid(value: object) -> bool:
    if not _exact_keys(value, _COVERAGE_KEYS):
        return False
    assert isinstance(value, dict)
    for key in (
        "factor_month_eligible_listing_floor",
        "distinct_finite_factor_value_floor",
        "common_complete_case_month_floor",
    ):
        item = value[key]
        if isinstance(item, bool) or not isinstance(item, int) or item < 0:
            return False
    return _string_list(value["zero_target_triggers"])


def _materiality_valid(value: object) -> bool:
    if not _exact_keys(value, _MATERIALITY_KEYS):
        return False
    assert isinstance(value, dict)
    if not _nonempty_string(value["state"]):
        return False
    if not _nonempty_string(value["performance_informed_selection"]):
        return False
    if not _is_sha256(value["proposal_sha256"]):
        return False
    if not _is_sha256(value["approval_sha256"]):
        return False
    thresholds = value["thresholds"]
    if not isinstance(thresholds, list):
        return False
    for item in thresholds:
        if not _exact_keys(item, _THRESHOLD_KEYS):
            return False
        assert isinstance(item, dict)
        for key in ("threshold_id", "class", "metric", "comparator"):
            if not _nonempty_string(item[key]):
                return False
        for key in ("value", "reviewed_value"):
            field = item[key]
            if isinstance(field, bool) or not isinstance(field, int):
                return False
    return True


def _terminal_policy_valid(value: object) -> bool:
    if not _exact_keys(value, _TERMINAL_POLICY_KEYS):
        return False
    assert isinstance(value, dict)
    if not _nonempty_string(value["state"]):
        return False
    if not _is_sha256(value["owner_defer_sha256"]):
        return False
    policy = value["policy_sha256"]
    return policy is None or _is_sha256(policy)


def _grant_schema_valid(value: object) -> bool:
    if not _exact_keys(value, _GRANT_TOP):
        return False
    assert isinstance(value, dict)
    for key in (
        "artifact_id",
        "decision_id",
        "status",
        "owner_authorization",
        "operating_standard",
        "choice",
        "roadmap_stage2",
        "dataset_acceptance",
        "review_decision",
    ):
        if not _nonempty_string(value[key]):
            return False
    for key in (
        "operating_standard_sha256",
        "acceptance_record_file_sha256",
        "acceptance_record_sha256",
        "materiality_proposal_sha256",
    ):
        if not _is_sha256(value[key]):
            return False
    if not _mapping_strings(value["gate"], _GRANT_GATE_KEYS):
        return False
    if not _mapping_strings(
        value["review_file_sha256"],
        _GRANT_REVIEW_FILE_KEYS,
        shas=tuple(_GRANT_REVIEW_FILE_KEYS),
    ):
        return False
    return _string_list(value["now_eligible"]) and _string_list(
        value["does_not_authorize"]
    )


def _binding_schema_valid(value: object) -> bool:
    if not _exact_keys(value, _BINDING_TOP):
        return False
    assert isinstance(value, dict)
    if not _nonempty_string(value["schema_version"]):
        return False
    if not _nonempty_string(value["environment_id"]):
        return False
    if not _nonempty_string(value["calendar_id"]):
        return False
    if not _nonempty_string(value["calendar_version"]):
        return False
    if not _is_git_sha(value["runner_code_sha"]):
        return False
    for key in (
        "environment_lock_sha256",
        "protocol_file_sha256",
        "trial_inventory_file_sha256",
        "acceptance_record_file_sha256",
        "acceptance_identity_sha256",
    ):
        if not _is_sha256(value[key]):
            return False
    return True


def _review_authority_error(record: dict[str, object]) -> str | None:
    reviewer = record["reviewer_id"]
    decision_id = record["review_decision_id"]
    reference = record["reviewer_authority_reference"]
    appointment = record["reviewer_appointment_sha256"]
    if not (
        _nonempty_string(reviewer)
        and _nonempty_string(decision_id)
        and _nonempty_string(reference)
        and _is_sha256(appointment)
    ):
        return "REVIEW_AUTHORITY_MALFORMED"
    if reviewer in {record["acceptance_record_id"], decision_id}:
        return "REVIEWER_SELF_ISSUING"
    return None


def _normalize_record_timestamps(record: dict[str, object]) -> str | None:
    for field in ("accepted_at_utc", "as_of_cutoff"):
        normalized = _as_utc_timestamp(record[field])
        if normalized is None:
            return _REASON_TIMESTAMP
        record[field] = normalized
    calendar = record["calendar"]
    assert isinstance(calendar, dict)
    return None


def _as_utc_timestamp(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    if _DATE_ONLY_RE.fullmatch(value) or _NAIVE_TIMESTAMP_RE.fullmatch(value):
        return None
    try:
        return normalize_timestamp(value, "timestamp")
    except ValidationError:
        return None


def _read_octets(locator: object, absent_reason: str) -> bytes | Authorization:
    if not isinstance(locator, str) or not locator:
        return _refuse(absent_reason)
    path = Path(locator)
    try:
        if not path.is_file():
            return _refuse(absent_reason)
        return path.read_bytes()
    except OSError:
        return _refuse(absent_reason)


def _hex64(value: object, name: str) -> str:
    if not _is_sha256(value):
        raise ValueError(f"{name} must be a 64-hex digest")
    return str(value)


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and _SHA256_RE.fullmatch(value) is not None


def _is_git_sha(value: object) -> bool:
    return isinstance(value, str) and _GIT_SHA_RE.fullmatch(value) is not None


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _string_list(value: object) -> bool:
    if not isinstance(value, list):
        return False
    return all(_nonempty_string(item) for item in value)


def _exact_keys(value: object, keys: frozenset[str]) -> bool:
    return isinstance(value, dict) and set(value) == keys


def _mapping_strings(
    value: object,
    keys: frozenset[str],
    *,
    ints: tuple[str, ...] = (),
    shas: tuple[str, ...] = (),
    git: tuple[str, ...] = (),
) -> bool:
    if not _exact_keys(value, keys):
        return False
    assert isinstance(value, dict)
    int_fields = set(ints)
    sha_fields = set(shas)
    git_fields = set(git)
    for key, item in value.items():
        if key in int_fields:
            if isinstance(item, bool) or not isinstance(item, int) or item < 0:
                return False
            continue
        if key in sha_fields and not _is_sha256(item):
            return False
        if key in git_fields and not (
            _is_git_sha(item) or _is_sha256(item)
        ):
            return False
        if key not in int_fields | sha_fields | git_fields and not _nonempty_string(
            item
        ):
            return False
    return True


def _refuse(reason: str) -> Authorization:
    return Authorization(_STATUS_REFUSED, reason, 1, None, None, None)


__all__ = [
    "IDENTITY_EXCLUDE",
    "Authorization",
    "authorize",
    "project_acceptance_identity",
    "result_bearing_refusal_reason",
]

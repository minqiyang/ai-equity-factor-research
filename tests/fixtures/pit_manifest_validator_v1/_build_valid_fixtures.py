"""One-shot builder for committed synthetic validator fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from pit_manifest_validator_v1.validator import (
    CONTRACT_CONTENT_SHA256,
    CONTRACT_ID,
    CONTRACT_VERSION,
    ordered_manifest_sha256,
    project_dataset_review_decision,
    project_freeze_record,
    project_private_full_manifest,
)


ROOT = Path(__file__).resolve().parent


def digest(char: str) -> str:
    return char * 64


def component(input_id: str, ordinal: int, digest_char: str, size: int) -> dict[str, object]:
    return {
        "input_id": input_id,
        "component_ordinal": ordinal,
        "raw_byte_sha256": digest(digest_char),
        "byte_size": size,
    }


def write_json(name: str, payload: object) -> None:
    path = ROOT / name
    path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def raw_input(
    input_id: str,
    role: str,
    component_row: dict[str, object],
    *,
    row_count: int,
    coverage_start: str,
    content_status: str = "raw",
    parent_input_ids: list[str] | None = None,
    parent_input_hashes: list[str] | None = None,
    transformation_id: str | None = None,
    code_sha: str | None = None,
    config_sha256: str | None = None,
    hash_publication_classification: str = "private",
    currency: str = "USD",
    units: str = "price",
    schema_name: str = "synthetic-schema",
    manual_transformations: list[dict[str, object]] | None = None,
    quality_exceptions: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "input_id": input_id,
        "role": role,
        "schema_name": schema_name,
        "schema_version": "v1",
        "physical_components": [component_row],
        "row_count": row_count,
        "coverage_start_inclusive": coverage_start,
        "coverage_end_inclusive": "2026-05-29",
        "hash_publication_classification": hash_publication_classification,
        "content_status": content_status,
        "parent_input_ids": parent_input_ids or [],
        "parent_input_hashes": parent_input_hashes or [],
        "transformation_id": transformation_id,
        "code_sha": code_sha,
        "config_sha256": config_sha256,
        "environment_id": "synthetic-environment-001",
        "environment_lock_sha256": digest("e"),
        "identifier_namespace": "synthetic-listing",
        "currency": currency,
        "units": units,
        "calendar_id": "XNYS",
        "timezone": "America/New_York",
        "timestamp_semantics": "session-close-utc",
        "adjustment_policy_id": "synthetic-adjustment-001",
        "revision_policy_id": "synthetic-revision-001",
        "missingness_policy_id": "synthetic-missingness-001",
        "publication_policy_id": "synthetic-publication-001",
        "manual_transformations": manual_transformations or [],
        "quality_exceptions": quality_exceptions or [],
    }


def build_manifest() -> dict[str, object]:
    prices = component("synthetic-prices", 0, "a", 11)
    membership = component("synthetic-membership", 0, "b", 17)
    derived = component("synthetic-derived", 0, "c", 19)
    raw = {
        "schema_version": "private_full_manifest_v1",
        "manifest_id": "synthetic-private-full-manifest-001",
        "created_at_utc": "2026-08-22T00:00:00Z",
        "dataset_role": "campaign-bundle",
        "provider_label": "synthetic-provider",
        "provider_product_release": "synthetic-release-001",
        "retrieved_at_utc": "2026-08-21T21:00:00Z",
        "as_of_cutoff": "2026-05-29T20:00:00Z",
        "extraction_identity": {
            "extraction_id": "synthetic-extraction-001",
            "coverage_start_inclusive": "2018-01-01",
            "coverage_end_inclusive": "2026-05-29",
            "filter_ids": ["filter-synthetic-001"],
            "requested_field_ids": ["adjusted-close"],
        },
        "privacy_classification": "private",
        "code_sha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "config_sha256": digest("d"),
        "environment_id": "synthetic-environment-001",
        "environment_lock_sha256": digest("e"),
        "canonicalization_id": "pit_canonical_json_v1",
        "ordered_manifest_sha256": ordered_manifest_sha256([prices, membership, derived]),
        "canonical_manifest_sha256": digest("0"),
        "inputs": [
            raw_input(
                "synthetic-prices",
                "member_eod",
                prices,
                row_count=12,
                coverage_start="2018-01-01",
                schema_name="synthetic-eod-schema",
            ),
            raw_input(
                "synthetic-membership",
                "historical_membership",
                membership,
                row_count=8,
                coverage_start="2014-01-24",
                currency="NA",
                units="membership",
                schema_name="synthetic-membership-schema",
            ),
            raw_input(
                "synthetic-derived",
                "security_master",
                derived,
                row_count=8,
                coverage_start="2014-01-24",
                content_status="derived",
                parent_input_ids=["synthetic-membership", "synthetic-prices"],
                parent_input_hashes=[digest("b"), digest("a")],
                transformation_id="synthetic-transform-001",
                code_sha="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                config_sha256=digest("f"),
                hash_publication_classification="publication_approved",
                units="identity",
                schema_name="synthetic-derived-schema",
                manual_transformations=[
                    {
                        "transformation_id": "synthetic-manual-001",
                        "code_sha": "cccccccccccccccccccccccccccccccccccccccc",
                        "config_sha256": digest("1"),
                    }
                ],
                quality_exceptions=[
                    {
                        "exception_id": "synthetic-exception-001",
                        "disposition": "diagnostic_only",
                        "reviewer_id": "synthetic-reviewer-001",
                    }
                ],
            ),
        ],
    }
    projected = project_private_full_manifest(raw, verify_digest=False)
    raw["canonical_manifest_sha256"] = projected["canonical_manifest_sha256"]
    return raw


def build_decision() -> dict[str, object]:
    raw = {
        "schema_version": "dataset_review_decision_v1",
        "review_decision_id": "synthetic-decision-001",
        "reviewed_at": "2026-08-22T12:00:00Z",
        "reviewer_id": "synthetic-reviewer-001",
        "reviewer_authority_reference": "synthetic-authority-001",
        "contract_id": CONTRACT_ID,
        "contract_version": CONTRACT_VERSION,
        "contract_content_sha256": CONTRACT_CONTENT_SHA256,
        "contract_protected_merge_sha": "dddddddddddddddddddddddddddddddddddddddd",
        "manifest_id": "synthetic-private-full-manifest-001",
        "canonical_manifest_sha256": digest("2"),
        "canonicalization_id": "pit_canonical_json_v1",
        "public_projection_id": "projection-001",
        "public_projection_schema_version": "public_redacted_projection_v1",
        "public_projection_sha256": digest("3"),
        "declared_dataset_roles": ["member-eod", "historical-membership"],
        "declared_use": "diagnostic-campaign",
        "date_universe_scope": "synthetic-2018-2026",
        "privacy_publication_scope": "public-hashes-and-counts-only",
        "applicable_contract_version": CONTRACT_VERSION,
        "decision": "diagnostic_only",
        "findings": [
            {
                "finding_id": "identity-terminal-fail-closed-d7a",
                "severity": "high",
                "evidence_refs": [
                    {"evidence_ref_id": "evidence-identity-001"},
                    {"evidence_ref_id": digest("4")},
                ],
                "disposition": "diagnostic_only",
                "unresolved_limitation": "counted-ineligibility-retained",
            }
        ],
        "predecessor_decision_id": None,
        "decision_canonicalization_id": "pit_canonical_json_v1",
        "decision_record_sha256": digest("0"),
        "public_decision_reference": "decision-ref-001",
    }
    projected = project_dataset_review_decision(raw, verify_digest=False)
    raw["decision_record_sha256"] = projected["decision_record_sha256"]
    return raw


def build_freeze() -> dict[str, object]:
    roles = []
    for role in (
        "historical_membership",
        "member_eod",
        "delisted_symbols",
        "symbol_change_history",
        "splits",
        "dividends",
        "benchmark_spy",
    ):
        limited = role == "symbol_change_history"
        roles.append(
            {
                "role": role,
                "coverage_start_inclusive": "2022-07-22" if limited else "2018-01-01",
                "coverage_end_inclusive": "2026-05-29",
                "row_count": 4 if limited else 12,
                "limitation_state": (
                    "counted_evidence_limitation" if limited else "none"
                ),
                "limitation_id": "synthetic-symbol-change-gap" if limited else None,
            }
        )
    raw = {
        "schema_version": "track_a_pr2_freeze_record_v1",
        "freeze_record_id": "synthetic-freeze-001",
        "canonicalization_id": "pit_canonical_json_v1",
        "as_of_cutoff": "2026-05-29T20:00:00Z",
        "role_coverage": roles,
        "coverage_labels": [
            "coverage_all_available",
            "coverage_primary_quality_window",
            "coverage_pre_2018_limited",
        ],
        "calendar": {
            "calendar_id": "XNYS",
            "calendar_version": "synthetic-calendar-v1",
            "calendar_evidence_ref": digest("5"),
            "source_timezone": "America/New_York",
            "utc_conversion_rule": "session-close-to-utc",
            "environment_id": "synthetic-environment-001",
            "environment_lock_sha256": digest("e"),
        },
        "lineage_and_terminal": {
            "membership_policy_id": "membership-reconstruction-policy-v2",
            "membership_policy_sha256": digest("6"),
            "snapshot_authority": "snapshot_primary",
            "as_of_rule": "s_eq_max_snapshot_date_le_t",
            "carry_forward": "event_driven_no_fixed_age_limit",
            "baseline_date": "2014-01-24",
            "pre_baseline_claims": "forbidden",
            "invented_start_date": "forbidden",
            "start_date_boundary": "inclusive",
            "end_date_boundary": "exclusive",
            "interval_notation": "[StartDate, EndDate)",
            "factor_anchor_lineage_id": "factor_anchor_lineage_v1",
            "terminal_event_policy_state": "candidate_not_accepted",
            "terminal_event_policy_sha256": None,
        },
        "exclusions": [
            {
                "exclusion_id": "conflicting-snapshot-interval",
                "exclusion_class": "conflicting_snapshot_undefined_interval",
                "count": 1,
                "evidence_sha256": digest("7"),
            },
            {
                "exclusion_id": "pre-baseline-dates",
                "exclusion_class": "pre_baseline_date",
                "count": 0,
                "evidence_sha256": digest("8"),
            },
            {
                "exclusion_id": "null-startdate-unobserved",
                "exclusion_class": "null_startdate_never_in_valid_snapshot",
                "count": 2,
                "evidence_sha256": digest("9"),
            },
            {
                "exclusion_id": "d7-identity-ineligible",
                "exclusion_class": "d7_adjudicated_identity_ineligible",
                "count": 2,
                "evidence_sha256": digest("a"),
            },
            {
                "exclusion_id": "quarantined-payloads",
                "exclusion_class": "quarantined_payload",
                "count": 0,
                "evidence_sha256": digest("b"),
            },
        ],
        "coverage_thresholds": {
            "factor_month_eligible_listing_floor": 100,
            "distinct_finite_factor_value_floor": 10,
            "common_complete_case_month_floor": 60,
            "zero_target_triggers": [
                "ELIGIBLE_SECURITY_COUNT_BELOW_100_AT_T",
                "DISTINCT_FINITE_FACTOR_VALUE_COUNT_BELOW_10_AT_T",
                "DUPLICATE_CANONICAL_LISTING_KEY_BYTES_AT_T",
            ],
        },
        "materiality_thresholds": {
            "state": "proposed",
            "performance_informed_selection": "FORBIDDEN",
            "thresholds": [
                {
                    "threshold_id": "synthetic-invalidation-001",
                    "value": "0.25",
                    "evidence_sha256": digest("c"),
                }
            ],
        },
        "contract_binding": {
            "contract_id": CONTRACT_ID,
            "contract_version": CONTRACT_VERSION,
            "contract_content_sha256": CONTRACT_CONTENT_SHA256,
            "contract_protected_merge_sha": "dddddddddddddddddddddddddddddddddddddddd",
        },
        "identity_fail_closed": {
            "identities_adjudicated": 2,
            "accepted_identities": 0,
            "disposition": "A_ACCEPT_TERMINAL_FAIL_CLOSED",
            "effect": "UNRESOLVED_IDENTITIES_ROUTE_THROUGH_FROZEN_DECISION_TIME_ELIGIBILITY_AS_COUNTED_INELIGIBILITY",
            "scope": "only_adjudicated_unresolved_identities_and_affected_episodes",
        },
        "freeze_record_sha256": digest("0"),
    }
    projected = project_freeze_record(raw, verify_digest=False)
    raw["freeze_record_sha256"] = projected["freeze_record_sha256"]
    return raw


def main() -> None:
    manifest = build_manifest()
    project_private_full_manifest(manifest)
    write_json("private_full_manifest_valid.json", manifest)

    decision = build_decision()
    project_dataset_review_decision(decision)
    write_json("dataset_review_decision_valid.json", decision)

    freeze = build_freeze()
    project_freeze_record(freeze)
    write_json("track_a_pr2_freeze_record_valid.json", freeze)


if __name__ == "__main__":
    main()

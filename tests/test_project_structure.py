from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import runpy
import tomllib
import unicodedata


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_required_directories_exist() -> None:
    required_directories = [
        "src/data",
        "src/features",
        "src/strategies",
        "src/backtest",
        "src/risk",
        "src/reporting",
        "src/utils",
        "tests",
        "research",
        "reports",
    ]

    for directory in required_directories:
        assert (PROJECT_ROOT / directory).is_dir(), f"Missing directory: {directory}"


def test_required_governance_files_exist() -> None:
    required_files = [
        "README.md",
        "PROJECT_SPEC.md",
        "AGENTS.md",
        "EXPERIMENT_LOG.md",
        "pyproject.toml",
        "docs/research_program_charter.md",
        "docs/purged_bounded_split_contract.md",
        "docs/signal_execution_timing_contract.md",
        "docs/point_in_time_data_methodology_contract.md",
        "docs/experiment_trial_ledger_contract.md",
        "docs/current_roadmap.md",
        "docs/current_handoff.md",
    ]

    for file_name in required_files:
        assert (PROJECT_ROOT / file_name).is_file(), f"Missing file: {file_name}"


def test_current_roadmap_and_handoff_define_one_active_status_source() -> None:
    roadmap = (PROJECT_ROOT / "docs/current_roadmap.md").read_text(
        encoding="utf-8"
    )
    handoff = (PROJECT_ROOT / "docs/current_handoff.md").read_text(encoding="utf-8")
    historical_roadmap = (
        PROJECT_ROOT / "docs/current_roadmap_gap_refresh.md"
    ).read_text(encoding="utf-8")

    for phrase in [
        "This is the canonical roadmap",
        "## Implemented Baseline",
        "## Current Research-Validity Findings",
        "## Delivery Sequence",
        "0. Research Charter Reset",
        "1a. Purged/bounded split contract",
        "1b. Purged/bounded split implementation",
        "2a. Signal/execution timing contract",
        "2b. Signal/execution timing implementation",
        "3. Point-in-time data methodology",
        "`docs/point_in_time_data_methodology_contract.md`",
        "Target construction currently lives in `src/backtest/portfolio.py`",
        "`historical_evaluation`, not a pristine holdout",
        "request `@codex review` once on the",
        "`docs/purged_bounded_split_contract.md`",
        "`docs/signal_execution_timing_contract.md`",
    ]:
        assert phrase in roadmap

    for phrase in [
        "Long-term evidence policy: `docs/research_program_charter.md`",
        "Active roadmap: `docs/current_roadmap.md`",
        "## Research Charter Decision",
        "## Stage 1 Split Decision",
        "## Stage 2 Timing Decision",
        "## Stage 3 Data Methodology Decision",
        "## Proposed Stage 4a Experiment and Trial Ledger Decision",
        "## Audited Findings",
        "## PR #148 Interaction",
        "## Next Safe Stage",
        "Stage 4b - Experiment/trial ledger implementation",
    ]:
        assert phrase in handoff

    assert "## Status: Historical" in historical_roadmap
    assert "must not be used as the current task queue" in historical_roadmap
    assert "854 passing tests" in roadmap
    assert "Starting validation: 854 tests passed" in handoff
    assert "completed holding-episode metrics" in roadmap
    assert "no actionable P1/P2 findings" not in roadmap
    design = (
        PROJECT_ROOT / "docs/risk_evaluation_metrics_design.md"
    ).read_text(encoding="utf-8")
    for phrase in [
        "## Stage 1: Holdings-State Metrics",
        "average_holding_count",
        "average_position_concentration_hhi",
        "max_position_concentration_hhi",
        "## Stage 2: Tracking Error",
        "## Formerly Deferred Metrics",
        "## PR Sequence",
    ]:
        assert phrase in design


def test_research_program_charter_defines_evidence_and_authorization_gates() -> None:
    charter = (PROJECT_ROOT / "docs/research_program_charter.md").read_text(
        encoding="utf-8"
    )
    specification = " ".join(
        (PROJECT_ROOT / "PROJECT_SPEC.md").read_text(encoding="utf-8").split()
    )

    for phrase in [
        "## Current Authorization",
        "## Evidence Layers",
        "Factor | A date-by-asset score",
        "Strategy | A frozen signal policy",
        "Portfolio | One or more strategies",
        "Execution | The translation from frozen targets",
        "### Complete trial accounting",
        "## Sample Classification and Holdout Access",
        "historical evaluation or pseudo-holdout",
        "## Candidate States",
        "`PAPER_CANDIDATE`",
        "Controlled live execution is not a stage authorized by this charter",
    ]:
        assert phrase in charter

    for phrase in [
        "The current phase is research-only",
        "Passing deterministic tests proves implementation behavior",
        "not historical validity",
        "Every protected-sample access",
        "holdout exposure ledger",
        "A candidate label is not",
        "authorization to paper trade or trade live",
    ]:
        assert phrase in specification


def test_purged_bounded_split_contract_freezes_stage_one_design() -> None:
    contract = (
        PROJECT_ROOT / "docs/purged_bounded_split_contract.md"
    ).read_text(encoding="utf-8")
    roadmap = (PROJECT_ROOT / "docs/current_roadmap.md").read_text(
        encoding="utf-8"
    )
    handoff = (PROJECT_ROOT / "docs/current_handoff.md").read_text(
        encoding="utf-8"
    )
    repo_map = (PROJECT_ROOT / "docs/repo_map.md").read_text(encoding="utf-8")

    for phrase in [
        "train_start",
        "validation_start",
        "test_start",
        "`test_end` is always explicit",
        "label_start = source_index[i]",
        "label_end = source_index[i + h]",
        "`price_forward_return` requires `label_horizon_rows >= 1`",
        "`synthetic_same_row_response` requires",
        "`label_derivation`",
        "`label_crosses_window_end`",
        "masks every purged or embargoed target value to `NaN`",
        "`embargo_rows`",
        "An explicit gap can therefore satisfy all or part of an embargo",
        "`feature_warm_up_rows`",
        "The purged tail is the label warm-down set",
        "`no_eligible_labels`",
        "`SPLIT-005`",
        "`SPLIT-006`",
        "`SPLIT-017`",
        "`SPLIT-021`",
        "`SPLIT-022`",
        "`no_usable_label_pairs`",
        "gap_dates_consuming_embargo",
        "No post-test value may complete a test label",
        "supersede that earlier wording for Stage 1b",
        "Stage 2",
    ]:
        assert phrase in contract

    for canonical_doc in [roadmap, handoff, repo_map]:
        assert "docs/purged_bounded_split_contract.md" in canonical_doc

    for case_number in range(1, 23):
        assert contract.count(f"`SPLIT-{case_number:03d}`") == 1

    assert roadmap.count("| 1b. Purged/bounded split implementation |") == 1
    assert "| 1b. Purged/bounded split implementation | Complete" in roadmap
    assert "| 2a. Signal/execution timing contract | Complete" in roadmap
    assert (
        "| 2b. Signal/execution timing implementation | "
        "Complete on protected main via PR #162"
    ) in roadmap
    assert "Stage 4b - Experiment/trial ledger implementation" in handoff


def test_signal_execution_timing_contract_freezes_stage_two_design() -> None:
    contract = (
        PROJECT_ROOT / "docs/signal_execution_timing_contract.md"
    ).read_text(encoding="utf-8")
    roadmap = (PROJECT_ROOT / "docs/current_roadmap.md").read_text(
        encoding="utf-8"
    )
    handoff = (PROJECT_ROOT / "docs/current_handoff.md").read_text(
        encoding="utf-8"
    )
    specification = (PROJECT_ROOT / "PROJECT_SPEC.md").read_text(
        encoding="utf-8"
    )
    repo_map = (PROJECT_ROOT / "docs/repo_map.md").read_text(encoding="utf-8")

    for phrase in [
        "Status: accepted Stage 2 design; Stage 2b runtime implementation complete on",
        "This is the normative documentation and methodology target for the current",
        "after_close_signal_next_observed_close_v1",
        "A close-derived signal stamped at row `t` becomes available only after",
        "The earliest supported execution is `close[t+1]`, the next observed source",
        "It does not constrain source rows after execution",
        "execution_time < holding_effective_start",
        "first_return_end    = missing",
        "It must not construct or infer `a[N+1]`",
        "`signal_lag_periods=0` is invalid for close-derived signals.",
        "Row lag counts observed source rows within the exact bounded accounting slice",
        "Rows in the full source index before `a[0]` never satisfy lag",
        "A target executed at close `t` does not earn the return stamped `t`",
        "Both bounds must be exact scalar timestamp labels in the validated price index",
        "price_index.get_loc(evaluation_start)",
        "partial-date strings such as `2024-01`",
        "measured_return_dates = accounting_dates[1:]",
        "timing_ledger_dates =",
        "`is_scheduled_rebalance` is false",
        "`incoming_return_start = a[j-1]`",
        "`first_holding_return_start = a[N]`",
        "net_return.loc[measured_return_dates]",
        "`initial_capital_invalid`",
        "`signal_value_invalid`",
        "`source_provenance_invalid`",
        "`source_provenance` with no default or",
        "`tracked_pre_mutation_source_snapshot_v1`",
        "pre-start `1+0j` write",
        "controlled API",
        "enforcement begins at capture",
        "cannot infer or",
        "latest tracked assignment",
        "latest controlled bounded assignment determines recovery",
        "changes the promoted column",
        "container from complex to object",
        "wider NumPy scalar such as x86 `longdouble`",
        "raises `source_provenance_invalid` at capture before any Python",
        "Direct and nested provenance objects are rejected",
        "extracted primitives",
        "bounded_final_signals = final_signals.iloc",
        "Only after that exact bounded slice exists",
        "Signal values strictly before `evaluation_start` or after `evaluation_end`",
        "`incoming_price_invalid`",
        "`execution_price_invalid`",
        "`returns_invalid`",
        "`portfolio_insolvent_or_non_finite_before_trade`",
        "`portfolio_insolvent_or_non_finite_after_costs`",
        "`equity_curve_invalid`",
        "calculate_max_drawdown(equity_curve, *, initial_capital)",
        "It has no external index-equality requirement",
        "`DatetimeIndex` values, timezone, and order",
        "raise_before_successful_result_on_invalid_or_insolvent_capital",
        "validate_bounded_scores_after_exact_slice_raise_on_invalid_available_score",
        "decision_information_only_no_execution_close_rerank",
        "execution_price_failure_policy",
        "include_return_trade_cost_open_holdings_no_future_return",
        "Same-row synthetic response diagnostics are not executable strategy returns",
        "The model is an idealized full target reset at an observed close.",
        "## Required Metadata",
        "## Hand-Calculated Reference Case",
        "## Deterministic Stage 2b Test Matrix",
        "## Stage 2b Implementation Boundary",
        "## Accepted Decisions and Deferred Choices",
    ]:
        assert phrase in contract

    for field in [
        "`timing_contract`",
        "`feature_time`",
        "`signal_availability_time`",
        "`decision_time`",
        "`execution_time`",
        "`signal_lag_rows`",
        "`return_frequency`",
        "`periods_per_year`",
        "`return_interval`",
        "`holding_effective_interval`",
        "`cost_application_time`",
        "`metric_anchor_policy`",
        "`terminal_row_policy`",
        "`signal_value_failure_policy`",
        "`incoming_price_failure_policy`",
        "`returns_failure_policy`",
        "`gross_insolvency_failure_policy`",
        "`insolvency_failure_policy`",
        "`equity_curve_failure_policy`",
        "`benchmark_return_window`",
        "`backtest_source_provenance_policy`",
        "`backtest_source_provenance_status`",
    ]:
        assert field in contract

    for case_number in range(1, 15):
        assert contract.count(f"`TIMING-{case_number:03d}`") == 1

    for canonical_doc in [roadmap, handoff, specification, repo_map]:
        assert "docs/signal_execution_timing_contract.md" in canonical_doc

    assert (
        "Stage 2b now requires explicit exact evaluation bounds and exact "
        "full-source price/signal axes plus exact source provenance whose "
        "caller-declared baseline is captured before later mutation."
    ) in " ".join(handoff.split())
    assert "rejects zero and invalid lag types" in " ".join(
        specification.split()
    )
    assert "| 2a. Signal/execution timing contract | Complete" in roadmap
    assert (
        "| 2b. Signal/execution timing implementation | "
        "Complete on protected main via PR #162"
    ) in roadmap
    assert (
        "| 3. Point-in-time data methodology | "
        "Complete on protected main via PR #163"
    ) in roadmap
    assert (
        "| 4a. Experiment/trial ledger contract | "
        "Local P1/P2-remediation gates passed"
    ) in roadmap
    assert (
        "| 4b. Experiment/trial ledger implementation | "
        "Blocked by Stage 4a protected merge and exact merge-head CI"
    ) in roadmap


def test_point_in_time_data_methodology_contract_freezes_stage_three_design() -> None:
    contract = (
        PROJECT_ROOT / "docs/point_in_time_data_methodology_contract.md"
    ).read_text(encoding="utf-8")
    roadmap = (PROJECT_ROOT / "docs/current_roadmap.md").read_text(
        encoding="utf-8"
    )
    handoff = (PROJECT_ROOT / "docs/current_handoff.md").read_text(
        encoding="utf-8"
    )
    specification = (PROJECT_ROOT / "PROJECT_SPEC.md").read_text(
        encoding="utf-8"
    )
    readiness_audit = (
        PROJECT_ROOT / "docs/real_data_readiness_audit.md"
    ).read_text(encoding="utf-8")
    readiness_skill = (
        PROJECT_ROOT / ".agents/skills/real-data-readiness-audit/SKILL.md"
    ).read_text(encoding="utf-8")
    study_checklist = (
        PROJECT_ROOT / "docs/local_csv_study_checklist.md"
    ).read_text(encoding="utf-8")
    audit_template = (
        PROJECT_ROOT / "docs/local_csv_readiness_audit_report_template.md"
    ).read_text(encoding="utf-8")
    experiment_log = (PROJECT_ROOT / "EXPERIMENT_LOG.md").read_text(
        encoding="utf-8"
    )
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    repo_map = (PROJECT_ROOT / "docs/repo_map.md").read_text(encoding="utf-8")

    for phrase in [
        "Status: accepted Stage 3 methodology contract",
        "Contract ID: `point_in_time_data_methodology_contract_v1`",
        "Contract version: `1.0.0`",
        "`methodology_contract_accepted`",
        "`dataset_manifest_reviewed`",
        "`formal_interpretation_eligible`",
        "Contract acceptance does not verify any dataset",
        "`UNKNOWN`",
        "`NOT_APPLICABLE`",
        "`asserted`",
        "`owner_accepted`",
        "`canonical_manifest_sha256`",
        "`raw_byte_sha256`",
        "`ordered_manifest_sha256`",
        "`ordered_component_inventory_v1`",
        "`physical_components`",
        "all-and-only, one-to-one flattening",
        "`canonicalization_id`",
        "`environment_id`",
        "`environment_lock_sha256`",
        "`review_decision_id`",
        "`public_projection_sha256`",
        "`public_redacted_projection_v1`",
        "`safe_public_id`",
        "`contract_content_sha256`",
        "`contract_protected_merge_sha`",
        "`decision_canonicalization_id`",
        "`decision_record_sha256`",
        "`pit_canonical_json_v1`",
        "RFC 8785 JCS",
        "an absent required property is rejected and is never synthesized",
        "The public projection cannot contain its dataset-review decision",
        "tests/fixtures/pit_canonical_json_v1_golden.json",
        "`permanent_security_id`",
        "`listing_id`",
        "`ticker_alias`",
        "`effective_from`",
        "`effective_to`",
        "`effective_to_state`",
        "`FINITE`",
        "`OPEN_IN_VINTAGE`",
        "`known_at`",
        "`public_available_at`",
        "`provider_available_at`",
        "`revision_published_at`",
        "`supersedes`",
        "`delisting_terminal_value_policy`",
        "`adjustment_set_id`",
        "`volume_basis`",
        "`NOT_YET_LISTED`",
        "`PROVIDER_GAP`",
        "`calendar_id`",
        "`calendar_version`",
        "`source_timezone`",
        "`session_date`",
        "`available_at`",
        "`benchmark_purpose`",
        "`risk_free_policy`",
        "`private_full_manifest`",
        "`public_redacted_projection`",
        "`sealed_at`",
        "`accessed_at`",
        "`recorded_at`",
        "`backfilled`",
        "`classification_before`",
        "`classification_after`",
        "`design_impact`",
        "`historical_evaluation`",
        "2025-05-01 through 2026-05-31",
        "Stage 4 owns append-only enforcement",
        "and known_at <= t",
        "and t <= as_of_cutoff",
        "inside every required role/input coverage range",
        "A later-known closure never",
        "Neither a manifest author nor a checklist can self-certify",
        "No provider selection, download, credentials, or remote data access",
        "## Deterministic Stage 3 Test Matrix",
        "## Accepted Decisions and Deferred Implementation",
    ]:
        assert phrase in contract

    for case_number in range(1, 16):
        assert contract.count(f"`PIT-{case_number:03d}`") == 1

    for case_id, decision_fragment in {
        "PIT-003": "requires digest recomputation",
        "PIT-004": "It is unavailable to that signal",
        "PIT-011": "Serialization fails closed through the allowlist",
        "PIT-012": "cannot retain or establish holdout status and is downgraded",
        "PIT-013": "uncertain overlap downgrades the nominal window",
        "PIT-014": "dataset verification and formal interpretation blocked",
        "PIT-015": "`t_after` is unsupported",
    }.items():
        case_row = next(
            line for line in contract.splitlines() if f"`{case_id}`" in line
        )
        assert decision_fragment in case_row

    pit_015_row = next(
        line for line in contract.splitlines() if "`PIT-015`" in line
    )
    for boundary_token in [
        "`effective_to_state = OPEN_IN_VINTAGE`",
        "`effective_to = null`",
        "`C = 2024-06-28T21:00:00Z`",
        "`t_in = 2024-06-28T20:00:00Z`",
        "`t_after = 2024-07-01T14:30:00Z`",
    ]:
        assert boundary_token in pit_015_row

    for canonical_doc in [
        roadmap,
        handoff,
        specification,
        readiness_audit,
        readiness_skill,
        study_checklist,
        audit_template,
        experiment_log,
        readme,
        repo_map,
    ]:
        assert "docs/point_in_time_data_methodology_contract.md" in canonical_doc

    normalized_contract = " ".join(contract.split())
    assert "no envelope, delimiter, byte-order mark, or trailing newline" in (
        normalized_contract
    )
    assert "Classification moves only toward greater exposure" in normalized_contract
    assert "An existing window is never upgraded" in normalized_contract
    assert (
        "methodology_contract_accepted does not imply "
        "dataset_manifest_reviewed"
    ) in normalized_contract
    assert (
        "dataset_manifest_reviewed does not imply "
        "formal_interpretation_eligible"
    ) in normalized_contract
    assert (
        "does not establish `formal_ready`, point-in-time status, license "
        "entitlement, or historical validity"
    ) in normalized_contract
    assert (
        "Tracked records must not contain private absolute paths"
        in normalized_contract
    )
    assert "Static or survivor-selected cohorts remain `DIAGNOSTIC_ONLY`" in contract

    for intake_doc in [study_checklist, audit_template]:
        normalized_intake = " ".join(intake_doc.split())
        assert "dataset-manifest review candidate (not formal evidence)" in normalized_intake
        assert "methodology_contract_accepted" in normalized_intake
        assert "dataset_manifest_reviewed" in normalized_intake
        assert "formal_interpretation_eligible" in normalized_intake
        assert "private absolute paths" in normalized_intake
        assert "hash plan is not evidence" in normalized_intake
        assert "this form cannot grant any gate" in normalized_intake
        assert "Dataset review decision ID:" in normalized_intake
        assert "Reviewer authority reference:" in normalized_intake
        assert "Finding IDs and dispositions:" in normalized_intake
        assert "cannot self-certify" in normalized_intake
        assert "outcome-reconstructible" in normalized_intake
        assert "2025-05-01 through 2026-05-31" in normalized_intake
        assert "`historical_evaluation`, never a pristine holdout" in normalized_intake
        assert "must not be upgraded" in normalized_intake
        assert "canonicalization_id" in normalized_intake
        assert "environment_id" in normalized_intake
        assert "environment_lock_sha256" in normalized_intake
        assert "known_at <= decision_time" in normalized_intake
        assert "non-self-issued exact-version dataset-review decision" in normalized_intake
        assert (
            "methodology_contract_accepted` does not imply "
            "`dataset_manifest_reviewed"
        ) in normalized_intake
        assert (
            "dataset_manifest_reviewed` does not imply "
            "`formal_interpretation_eligible"
        ) in normalized_intake


def test_experiment_trial_ledger_contract_freezes_stage_four_a_design() -> None:
    contract = (
        PROJECT_ROOT / "docs/experiment_trial_ledger_contract.md"
    ).read_text(encoding="utf-8")
    roadmap = (PROJECT_ROOT / "docs/current_roadmap.md").read_text(
        encoding="utf-8"
    )
    handoff = (PROJECT_ROOT / "docs/current_handoff.md").read_text(
        encoding="utf-8"
    )
    specification = (PROJECT_ROOT / "PROJECT_SPEC.md").read_text(
        encoding="utf-8"
    )
    point_in_time_contract = (
        PROJECT_ROOT / "docs/point_in_time_data_methodology_contract.md"
    ).read_text(encoding="utf-8")
    repo_map = (PROJECT_ROOT / "docs/repo_map.md").read_text(encoding="utf-8")
    normalized_contract = " ".join(contract.split())

    for phrase in [
        "Status: proposed Stage 4a design contract",
        "acceptance requires final current-head review, protected merge, and successful exact merge-head CI",
        "Contract ID: `experiment_trial_ledger_contract_v1`",
        "Contract version: `1.0.0`",
        "Stage 4b runtime enforcement is not implemented",
        "diagnostic/legacy sidecars",
        "`trial_id` identifies exactly one semantic configuration",
        "`attempt_id` identifies one invocation",
        "Each ledger-owned logical entity ID is allocated exactly once across the ledger",
        "`actor_id` is an externally assigned, opaque claimed-attribution reference",
        "does not prove the actor's authenticity, control, authorization",
        "grants no append, access, review, promotion",
        "must fail closed until Stage 4b accepts an owner-approved external authority mechanism",
        "Stage 4a does not choose that mechanism",
        "reuse that already allocated ID as a typed subject or reference",
        "Entity-ID conflict therefore means a second allocation attempt",
        "Campaign reports disclose both semantic trial count and execution-attempt count",
        "No validator, executor, protected-data accessor, or result-producing process",
        "LEDGER_EPOCH_CREATED",
        "Parent precedence is an exact partial order",
        "Direct campaign-scoped registration",
        "Ledger-global registration plus campaign binding",
        "Accepted external Stage 3 registration",
        "may list multiple affected campaigns",
        "registration and `CAMPAIGN_ALLOCATED` are independent siblings",
        "`STAGE3_SAMPLE_REFERENCE_BOUND` allocates the ledger-local typed `sample_id`",
        "exact external registry authority, external sample-record ID, schema/contract version",
        "A direct registration cannot also have `CAMPAIGN_ENTITY_BOUND`",
        "`CAMPAIGN_INVENTORY_SEALED`",
        "included and bound inside the inventory-seal request/event preimage",
        "referenced predecessor event bytes are external to and excluded from that seal preimage",
        "sequence/event hash are never named by the anchor, so the anchor is nonrecursive",
        "stored `event_sha256` remains outside its event preimage",
        "same serialized atomic commit boundary",
        "assigns the seal sequence/envelope `previous_event_sha256`",
        "seal fails/conflicts; it must not silently rebase",
        "epoch-empty `(null, null)` is not legal",
        "`ledger_operation_request_v1`",
        "result-informed amendment",
        "cannot support `RESEARCH_PASS` or higher",
        "Trial disposition and attempt execution state are separate",
        "It never means `RESEARCH_PASS`",
        "`ACCESS_INTENT` must be durable before the accessor",
        "validates and consumes that exact capability",
        "`protected_material_observed = NONE | SOME | UNKNOWN`",
        "No canonical access event, including the private full ledger",
        "a complete `SOME` observation with frozen `purpose = design` is `development`",
        "even without separately confirmed downstream design/tuning influence",
        "complete design-purpose `SOME` classification",
        "The explicit allowed-transition graph",
        "validation -> validation | historical_evaluation | pseudo_holdout | development",
        "irrevocable floor of `historical_evaluation`",
        "`ledger_event_identity_v1`",
        "`pit_canonical_json_v1`",
        "The stored `event_sha256`",
        "The common identity-envelope schema rejects missing or unknown envelope fields",
        "`ledger_v1_utc_timestamp` subset",
        "including year `0000`",
        "A fractional second may have arbitrary precision but must be nonzero",
        "Ledger event schema v1 rejects every `second = 60`",
        "this contract pins no leap-second table",
        "deliberate application-level subset of RFC 3339 timestamp syntax",
        "It does not change `pit_canonical_json_v1`",
        "The v1 event-type vocabulary is closed at exactly these 37 values",
        "Stage 4a freezes an exact unknown-field-rejecting payload schema only for one golden event type",
        "`TRIAL_ALLOCATED` bindings are normative semantic requirements",
        "must reject `TRIAL_ALLOCATED` as `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`",
        "`incomplete_trial_allocation_stub` is rejection evidence only",
        "separately reviewed machine-readable per-event payload schema registry",
        "`SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`",
        "must not claim a contract-wide fail-closed ledger, Stage 4b conformance",
        "tamper-evident, not WORM",
        "`CAMPAIGN_EVIDENCE_FROZEN`",
        "`campaign_evidence_prefix_v1`",
        "The freeze event is necessarily excluded",
        "`campaign_evidence_checkpoint_v1`",
        "`freeze_event_sequence = evidence_sequence + 1`",
        "entire target-campaign projection is all-and-only exactly one",
        "`sealed_semantic_trial_count` is the cardinality",
        "equal counts never substitute for exact set equality",
        "A same-cardinality ID substitution fails",
        "one fixed all-excluded trial set and zero allocated/terminal",
        "depends on the complete Stage 4b per-event payload schema registry",
        "runtime remains fail closed until that registry is accepted and enforced",
        "`freeze_event_sequence`",
        "independently retained immutable checkpoint",
        "A producer cannot self-certify",
        "does not self-stale the decision",
        "`CAMPAIGN_ADJUDICATED`",
        "`campaign_adjudication_checkpoint_v1` anchors the complete verified chain",
        "checkpoint_generation",
        "Generation 1 has both",
        "Every successor is exactly the preceding generation plus one",
        "every retained generation, not only the head",
        "correspond one-to-one in that order",
        "The provider-neutral currentness authority key is exactly",
        "exactly `current_checkpoint_generation + 1` becomes pending",
        "Before any post-adjudication action scoped to that campaign",
        "A pending generation is not fully adjudicated",
        "No campaign-scoped `CHECKPOINT_REFERENCE_RECORDED` is appended",
        "General machine proof of which payloads are genuinely global remains deferred",
        "A local old ledger plus its old checkpoint cannot detect",
        "the full runtime must remain fail closed",
        "independent append-only and anti-rollback latestness",
        "Stage 4a chooses no provider, physical backend, signature scheme",
        "externally unverified adjudication checkpoint",
        "The full canonical ledger is private, repository-external evidence",
        "No runtime may create a default ledger database or event stream inside the repository",
        "`ledger_public_projection_v1` has all-and-only these top-level keys",
        "`schema_version` is exactly `ledger_public_projection_v1`",
        "`canonicalization_id` is exactly `pit_canonical_json_v1`",
        "Unknown-field, path, file-URI, query, username, raw-value",
        "`backfilled = true`, `DIAGNOSTIC_ONLY`",
        "Documentation-token tests for this matrix are not runtime append-only evidence",
        "physical storage backend",
        "The next implementation PR must not retrofit the legacy reporter in place",
    ]:
        assert phrase in normalized_contract

    for rejected_identity_architecture in [
        "genesis_principal_binding",
        "trusted_authority_manifest_v1",
        "owner_pinned_manifest_sha256",
        "authenticated_producer_context_v1",
    ]:
        assert rejected_identity_architecture not in contract

    vocabulary_block = (
        contract.split(
            "The v1 event-type vocabulary is closed at exactly these 37 values:", 1
        )[1]
        .split("```text", 1)[1]
        .split("```", 1)[0]
        .split()
    )
    assert len(vocabulary_block) == len(set(vocabulary_block))
    assert len(vocabulary_block) == 37
    assert set(vocabulary_block) == _LEDGER_EVENT_TYPES
    assert {
        "LEDGER_EPOCH_CREATED", "CAMPAIGN_ENTITY_BOUND",
        "STAGE3_SAMPLE_REFERENCE_BOUND", "TRIAL_ALLOCATED",
        "CAMPAIGN_ACCOUNTING_CLOSED", "EVENT_SUPERSEDED",
    } <= set(vocabulary_block)

    for case_number in range(1, 16):
        assert contract.count(f"`LEDGER-{case_number:03d}`") == 1

    for canonical_doc in [roadmap, handoff, specification, repo_map]:
        assert "docs/experiment_trial_ledger_contract.md" in canonical_doc

    assert "accepted Stage 3 methodology contract" in point_in_time_contract
    assert "acceptance pending protected merge" not in point_in_time_contract
    assert "| 3. Point-in-time data methodology | Complete" in roadmap
    assert (
        "| 4a. Experiment/trial ledger contract | "
        "Local P1/P2-remediation gates passed"
    ) in roadmap
    assert (
        "| 4b. Experiment/trial ledger implementation | "
        "Blocked by Stage 4a protected merge and exact merge-head CI"
    ) in roadmap
    assert "Finish Stage 4a contract PR gates" in handoff
    assert "Proposed Stage 4a design authority" in handoff
    assert "proposed Stage 4a design authority" in " ".join(
        specification.split()
    )
    assert "Proposed Stage 4a experiment/trial" in repo_map
    assert "proposed Stage 3" not in roadmap
    assert "proposed Stage 3" not in handoff
    assert "new-head GitHub gates pending" not in roadmap
    assert "required current-head review remain pending" not in handoff


def _ascii_jcs_golden_bytes(value: object) -> bytes:
    """Serialize a preprocessed ASCII-only golden vector under the JCS subset."""

    def validate(item: object) -> None:
        if item is None or isinstance(item, bool):
            return
        if isinstance(item, int):
            if not (-(2**53) + 1 <= item <= (2**53) - 1):
                raise ValueError("integer is outside the I-JSON safe range")
            return
        if isinstance(item, float):
            raise ValueError("raw floats are outside the frozen preprocessing profile")
        if isinstance(item, str):
            item.encode("ascii")
            if unicodedata.normalize("NFC", item) != item:
                raise ValueError("golden string is not NFC-normalized")
            return
        if isinstance(item, list):
            for member in item:
                validate(member)
            return
        if isinstance(item, dict):
            for key, member in item.items():
                if not isinstance(key, str):
                    raise ValueError("JSON object keys must be strings")
                validate(key)
                validate(member)
            return
        raise ValueError(f"unsupported golden value type: {type(item).__name__}")

    validate(value)
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _require_exact_keys(
    value: object,
    expected_keys: set[str],
    *,
    context: str,
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != expected_keys:
        raise ValueError(f"{context} must contain exactly {sorted(expected_keys)}")
    return value


def _require_stable_id(value: object, *, context: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or unicodedata.normalize("NFC", value) != value
    ):
        raise ValueError(f"{context} must be a nonempty NFC-normalized string")
    return value


def _require_safe_public_id(value: object, *, context: str) -> str:
    if (
        not isinstance(value, str)
        or re.fullmatch(
            r"[a-z0-9](?:[a-z0-9._-]{0,126}[a-z0-9])?",
            value,
        )
        is None
    ):
        raise ValueError(f"{context} must be an opaque safe_public_id")
    return value


def _require_ledger_typed_id(
    value: object,
    *,
    prefix: str,
    context: str,
) -> str:
    if (
        not isinstance(value, str)
        or re.fullmatch(rf"{re.escape(prefix)}_[0-9a-f]{{32}}", value) is None
    ):
        raise ValueError(f"{context} must be a typed opaque ledger ID")
    return value


def _require_actor_attribution_reference(value: object, *, context: str) -> str:
    if (
        not isinstance(value, str)
        or re.fullmatch(r"act_[0-9a-f]{32}", value) is None
    ):
        raise ValueError(f"{context} must be an opaque actor attribution reference")
    return value


def _require_normalized_utc_timestamp(value: object, *, context: str) -> str:
    """Validate the ledger v1 UTC subset without a mutable leap-second table."""
    if not isinstance(value, str):
        raise ValueError(f"{context} must be a normalized UTC timestamp")
    match = re.fullmatch(
        r"([0-9]{4})-([0-9]{2})-([0-9]{2})"
        r"T([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.([0-9]+))?Z",
        value,
    )
    if match is None:
        raise ValueError(f"{context} must be a normalized UTC timestamp")
    year, month, day, hour, minute, second = map(int, match.groups()[:6])
    leap_year = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    days_in_month = (
        31,
        29 if leap_year else 28,
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    )
    if not (1 <= month <= 12 and 1 <= day <= days_in_month[month - 1]):
        raise ValueError(f"{context} must be a valid Gregorian date")
    if not (
        0 <= hour <= 23
        and 0 <= minute <= 59
        and 0 <= second <= 59
    ):
        raise ValueError(f"{context} must be a valid ledger v1 UTC time")
    fraction = match.group(7)
    if fraction is not None and fraction.endswith("0"):
        raise ValueError(f"{context} has a noncanonical fractional second")
    return value


def _ledger_event_identity_projection(source: object) -> dict[str, object]:
    """Validate the exact envelope and sole Stage 4a golden epoch payload."""
    projection = _require_exact_keys(
        source,
        {
            "ledger_schema_version",
            "event_schema_version",
            "canonicalization_id",
            "identity_projection_id",
            "ledger_id",
            "sequence",
            "event_id",
            "operation_id",
            "operation_request_projection_id",
            "operation_request_sha256",
            "event_type",
            "subject_type",
            "subject_id",
            "occurred_at",
            "recorded_at",
            "actor_id",
            "previous_event_sha256",
            "payload",
        },
        context="ledger event identity projection",
    )
    if projection["ledger_schema_version"] != "experiment_trial_ledger_v1":
        raise ValueError("unexpected ledger schema version")
    if projection["event_schema_version"] != "ledger_event_v1":
        raise ValueError("unexpected event schema version")
    if projection["canonicalization_id"] != "pit_canonical_json_v1":
        raise ValueError("unexpected canonicalization ID")
    if projection["identity_projection_id"] != "ledger_event_identity_v1":
        raise ValueError("unexpected identity projection ID")
    _require_ledger_typed_id(
        projection["ledger_id"],
        prefix="ldg",
        context="ledger_id",
    )
    _require_ledger_typed_id(
        projection["event_id"],
        prefix="evt",
        context="event_id",
    )
    _require_ledger_typed_id(
        projection["operation_id"],
        prefix="opn",
        context="operation_id",
    )
    if (
        projection["operation_request_projection_id"]
        != "ledger_operation_request_v1"
    ):
        raise ValueError("unexpected operation request projection ID")
    _require_actor_attribution_reference(
        projection["actor_id"],
        context="actor_id",
    )
    sequence = projection["sequence"]
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
        raise ValueError("sequence must be a nonnegative non-Boolean integer")
    if (
        not isinstance(projection["operation_request_sha256"], str)
        or re.fullmatch(
            r"[0-9a-f]{64}",
            projection["operation_request_sha256"],
        )
        is None
    ):
        raise ValueError("operation request hash must be lowercase SHA-256")
    if projection["event_type"] != "LEDGER_EPOCH_CREATED":
        raise ValueError("event type has no exact Stage 4a payload schema")
    for field in ["occurred_at", "recorded_at"]:
        _require_normalized_utc_timestamp(projection[field], context=field)
    previous_hash = projection["previous_event_sha256"]
    if previous_hash is not None and (
        not isinstance(previous_hash, str)
        or re.fullmatch(r"[0-9a-f]{64}", previous_hash) is None
    ):
        raise ValueError("previous event hash must be null or lowercase SHA-256")

    if sequence != 0 or previous_hash is not None:
        raise ValueError("LEDGER_EPOCH_CREATED must reserve sequence zero")
    if projection["subject_type"] != "ledger":
        raise ValueError("golden epoch subject must be ledger")
    if projection["subject_id"] != projection["ledger_id"]:
        raise ValueError("golden epoch subject must equal its ledger")
    _require_exact_keys(
        projection["payload"],
        {"campaign_scope_ids"},
        context="LEDGER_EPOCH_CREATED payload",
    )
    if projection["payload"]["campaign_scope_ids"] != []:
        raise ValueError("golden epoch must be ledger-global")
    return projection


def _ledger_operation_request_projection(source: object) -> dict[str, object]:
    event = _ledger_event_identity_projection(source)
    request_keys = [
        "operation_request_projection_id",
        "ledger_schema_version",
        "event_schema_version",
        "canonicalization_id",
        "identity_projection_id",
        "ledger_id",
        "event_id",
        "operation_id",
        "event_type",
        "subject_type",
        "subject_id",
        "occurred_at",
        "actor_id",
        "payload",
    ]
    return {key: event[key] for key in request_keys}


def _require_trial_parent_semantic_order_facts(
    parent_facts: object,
) -> None:
    """Check non-append semantic trial-parent ordering facts."""
    facts = _require_exact_keys(
        parent_facts,
        {
            "epoch_sequence",
            "campaign_sequence",
            "experiment_sequence",
            "trial_sequence",
            "campaign_id",
            "experiment_id",
            "family_id",
            "trial_id",
            "sample_ids",
            "family_path",
            "sample_paths",
        },
        context="trial parent facts",
    )
    epoch_sequence = facts["epoch_sequence"]
    campaign_sequence = facts["campaign_sequence"]
    experiment_sequence = facts["experiment_sequence"]
    trial_sequence = facts["trial_sequence"]
    for field, prefix in {
        "campaign_id": "cmp",
        "experiment_id": "exp",
        "family_id": "tfm",
        "trial_id": "trl",
    }.items():
        _require_ledger_typed_id(facts[field], prefix=prefix, context=field)
    sample_ids = facts["sample_ids"]
    if (
        any(
            isinstance(sequence, bool) or not isinstance(sequence, int)
            for sequence in [
                epoch_sequence,
                campaign_sequence,
                experiment_sequence,
                trial_sequence,
            ]
        )
        or not (epoch_sequence == 0 < campaign_sequence < experiment_sequence)
        or experiment_sequence >= trial_sequence
        or not isinstance(sample_ids, list)
        or sample_ids != sorted(set(sample_ids))
        or set(facts["sample_paths"]) != set(sample_ids)
    ):
        raise ValueError("base semantic parent bindings or order are invalid")
    for sample_id in sample_ids:
        _require_ledger_typed_id(sample_id, prefix="smp", context="sample_id")

    def require_path(
        path: object,
        *,
        expected_entity_id: object,
        allow_external: bool,
    ) -> None:
        if not isinstance(path, dict):
            raise ValueError("parent path must be an object")
        kind = path.get("kind")
        if kind == "direct":
            direct_path = _require_exact_keys(
                path,
                {
                    "kind",
                    "entity_id",
                    "campaign_scope_ids",
                    "registration_sequence",
                },
                context="direct parent path facts",
            )
            campaign_scope_ids = direct_path["campaign_scope_ids"]
            if not (
                direct_path["entity_id"] == expected_entity_id
                and isinstance(campaign_scope_ids, list)
                and campaign_scope_ids == sorted(set(campaign_scope_ids))
                and facts["campaign_id"] in campaign_scope_ids
                and campaign_sequence
                < direct_path["registration_sequence"]
                < trial_sequence
            ):
                raise ValueError("direct parent path is invalid")
        elif kind == "ledger_global":
            global_path = _require_exact_keys(
                path,
                {
                    "kind",
                    "entity_id",
                    "registration_scope_ids",
                    "registration_sequence",
                    "registration_event_id",
                    "registration_event_sha256",
                    "binding_entity_id",
                    "binding_campaign_id",
                    "binding_sequence",
                    "binding_source_event_id",
                    "binding_source_event_sha256",
                },
                context="ledger-global parent path facts",
            )
            if not (
                global_path["entity_id"] == expected_entity_id
                and global_path["binding_entity_id"] == expected_entity_id
                and global_path["registration_scope_ids"] == []
                and global_path["registration_event_id"]
                == global_path["binding_source_event_id"]
                and global_path["registration_event_sha256"]
                == global_path["binding_source_event_sha256"]
                and re.fullmatch(
                    r"evt_[0-9a-f]{32}",
                    global_path["registration_event_id"],
                )
                is not None
                and re.fullmatch(
                    r"[0-9a-f]{64}",
                    global_path["registration_event_sha256"],
                )
                is not None
                and global_path["binding_campaign_id"] == facts["campaign_id"]
                and epoch_sequence < global_path["registration_sequence"]
                < global_path["binding_sequence"]
                < trial_sequence
                and epoch_sequence < campaign_sequence
                < global_path["binding_sequence"]
                < trial_sequence
            ):
                raise ValueError("ledger-global parent path is invalid")
        elif kind == "stage3_external" and allow_external:
            external_path = _require_exact_keys(
                path,
                {
                    "kind",
                    "entity_id",
                    "binding_entity_id",
                    "binding_campaign_id",
                    "binding_sequence",
                    "external_reference",
                },
                context="external Stage 3 sample path facts",
            )
            external_reference = _require_exact_keys(
                external_path["external_reference"],
                {
                    "registry_authority_id",
                    "external_sample_record_id",
                    "schema_contract_version",
                    "record_sha256",
                    "review_decision_ref_id",
                },
                context="external Stage 3 sample reference",
            )
            if not (
                all(
                    isinstance(value, str) and value
                    for value in external_reference.values()
                )
                and re.fullmatch(
                    r"[0-9a-f]{64}",
                    external_reference["record_sha256"],
                )
                is not None
                and external_path["entity_id"] == expected_entity_id
                and external_path["binding_entity_id"] == expected_entity_id
                and external_path["binding_campaign_id"] == facts["campaign_id"]
                and campaign_sequence
                < external_path["binding_sequence"]
                < trial_sequence
            ):
                raise ValueError("external Stage 3 sample path is invalid")
        else:
            raise ValueError("ambiguous or illegal parent path")

    require_path(
        facts["family_path"],
        expected_entity_id=facts["family_id"],
        allow_external=False,
    )
    for sample_id, sample_path in facts["sample_paths"].items():
        require_path(
            sample_path,
            expected_entity_id=sample_id,
            allow_external=True,
        )


def _count_entity_identity_fact_appends(source: object) -> int:
    """Evaluate allocation/reference/idempotency documentation facts."""
    if not isinstance(source, list):
        raise ValueError("entity identity facts must be a list")
    allocations: dict[str, tuple[str, int]] = {}
    committed_operations: dict[str, tuple[object, ...]] = {}
    event_ids: set[str] = set()
    sequences: set[int] = set()
    append_count = 0
    entity_prefixes = {"trial": "trl", "attempt": "att"}

    for raw_fact in source:
        fact = _require_exact_keys(
            raw_fact,
            {
                "kind",
                "entity_type",
                "entity_id",
                "event_id",
                "operation_id",
                "sequence",
                "operation_request_sha256",
            },
            context="entity identity fact",
        )
        entity_type = fact["entity_type"]
        if entity_type not in entity_prefixes:
            raise ValueError("unknown entity type")
        entity_id = _require_ledger_typed_id(
            fact["entity_id"],
            prefix=entity_prefixes[entity_type],
            context="entity identity fact",
        )
        event_id = _require_ledger_typed_id(
            fact["event_id"],
            prefix="evt",
            context="entity fact event_id",
        )
        operation_id = _require_ledger_typed_id(
            fact["operation_id"],
            prefix="opn",
            context="entity fact operation_id",
        )
        sequence = fact["sequence"]
        request_sha256 = fact["operation_request_sha256"]
        if (
            isinstance(sequence, bool)
            or not isinstance(sequence, int)
            or sequence < 0
            or not isinstance(request_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", request_sha256) is None
        ):
            raise ValueError("invalid entity identity commit fact")
        request_identity = (
            event_id,
            operation_id,
            sequence,
            request_sha256,
            entity_type,
            entity_id,
        )

        if fact["kind"] == "exact_replay":
            if committed_operations.get(operation_id) != request_identity:
                raise ValueError("replay does not match the committed request")
            continue
        if (
            operation_id in committed_operations
            or event_id in event_ids
            or sequence in sequences
        ):
            raise ValueError("conflicting operation, event, or sequence reuse")
        if fact["kind"] == "allocate":
            if entity_id in allocations:
                raise ValueError("logical entity has already been allocated")
            allocations[entity_id] = (entity_type, sequence)
        elif fact["kind"] == "reference":
            allocation = allocations.get(entity_id)
            if (
                allocation is None
                or allocation[0] != entity_type
                or sequence <= allocation[1]
            ):
                raise ValueError("reference precedes allocation or has wrong type")
        else:
            raise ValueError("unknown entity identity fact kind")

        committed_operations[operation_id] = request_identity
        event_ids.add(event_id)
        sequences.add(sequence)
        append_count += 1

    return append_count


def _utf16_sort_key(value: str) -> bytes:
    return value.encode("utf-16-be")


def _require_inventory_preseal_head_facts(
    source: object,
    *,
    retained_ledger_id: object,
    retained_predecessor_sequence: object,
    retained_predecessor_event_sha256: object,
) -> None:
    """Conformance-only facts for the nonrecursive pre-attempt seal anchor."""
    facts = _require_exact_keys(
        source,
        {
            "anchor_schema_version",
            "ledger_id",
            "predecessor_sequence",
            "predecessor_event_sha256",
            "inventory_seal_previous_event_sha256",
            "inventory_seal_sequence",
            "first_attempt_or_access_sequence",
            "anchor_fields_in_seal_preimage",
            "predecessor_event_bytes_excluded_from_seal_preimage",
            "atomic_head_compare_and_assign",
        },
        context="inventory preseal head facts",
    )
    if facts["anchor_schema_version"] != "campaign_inventory_preseal_head_v1":
        raise ValueError("unexpected inventory preseal anchor schema")
    _require_ledger_typed_id(facts["ledger_id"], prefix="ldg", context="ledger_id")
    _require_ledger_typed_id(
        retained_ledger_id, prefix="ldg", context="retained ledger_id"
    )
    if retained_ledger_id != facts["ledger_id"]:
        raise ValueError("retained ledger does not match inventory anchor")
    for field in ["predecessor_sequence", "inventory_seal_sequence", "first_attempt_or_access_sequence"]:
        value = facts[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{field} must be a nonnegative integer")
    predecessor_hash = facts["predecessor_event_sha256"]
    if not isinstance(predecessor_hash, str) or re.fullmatch(r"[0-9a-f]{64}", predecessor_hash) is None:
        raise ValueError("predecessor event hash must be lowercase SHA-256")
    if (
        isinstance(retained_predecessor_sequence, bool)
        or not isinstance(retained_predecessor_sequence, int)
        or retained_predecessor_sequence < 0
    ):
        raise ValueError("retained predecessor sequence must be a nonnegative integer")
    if (
        not isinstance(retained_predecessor_event_sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", retained_predecessor_event_sha256) is None
    ):
        raise ValueError("retained predecessor hash must be lowercase SHA-256")
    if (
        retained_predecessor_sequence != facts["predecessor_sequence"]
        or retained_predecessor_event_sha256 != predecessor_hash
    ):
        raise ValueError("retained predecessor mutation invalidates inventory seal")
    if not (
        facts["predecessor_sequence"] + 1 == facts["inventory_seal_sequence"]
        and facts["inventory_seal_sequence"] < facts["first_attempt_or_access_sequence"]
        and facts["inventory_seal_previous_event_sha256"] == predecessor_hash
        and facts["anchor_fields_in_seal_preimage"] is True
        and facts["predecessor_event_bytes_excluded_from_seal_preimage"] is True
        and facts["atomic_head_compare_and_assign"] is True
    ):
        raise ValueError("inventory seal must anchor its immediate predecessor before action")


def _ordered_component_inventory_projection(source: object) -> dict[str, object]:
    projection = _require_exact_keys(
        source,
        {"schema_version", "canonicalization_id", "components"},
        context="ordered component inventory",
    )
    if projection["schema_version"] != "ordered_component_inventory_v1":
        raise ValueError("unexpected ordered inventory schema")
    if projection["canonicalization_id"] != "pit_canonical_json_v1":
        raise ValueError("unexpected ordered inventory canonicalization")
    if not isinstance(projection["components"], list):
        raise ValueError("ordered inventory components must be a list")

    normalized_components: list[dict[str, object]] = []
    seen_keys: set[tuple[str, int]] = set()
    ordinals_by_input: dict[str, set[int]] = {}
    for raw_component in projection["components"]:
        component = _require_exact_keys(
            raw_component,
            {"input_id", "component_ordinal", "raw_byte_sha256", "byte_size"},
            context="ordered component",
        )
        input_id = _require_stable_id(
            component["input_id"],
            context="component input_id",
        )
        component_ordinal = component["component_ordinal"]
        byte_size = component["byte_size"]
        if (
            not isinstance(component_ordinal, int)
            or isinstance(component_ordinal, bool)
            or not 0 <= component_ordinal <= (2**53) - 1
        ):
            raise ValueError("component ordinal must be a nonnegative safe integer")
        if (
            not isinstance(byte_size, int)
            or isinstance(byte_size, bool)
            or not 0 <= byte_size <= (2**53) - 1
        ):
            raise ValueError("byte size must be a nonnegative safe integer")
        raw_digest = component["raw_byte_sha256"]
        if (
            not isinstance(raw_digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", raw_digest) is None
        ):
            raise ValueError("raw component digest must be lowercase SHA-256")
        component_key = (input_id, component_ordinal)
        if component_key in seen_keys:
            raise ValueError("duplicate component identity")
        seen_keys.add(component_key)
        ordinals_by_input.setdefault(input_id, set()).add(component_ordinal)
        normalized_components.append(dict(component))

    for input_id, ordinals in ordinals_by_input.items():
        if ordinals != set(range(len(ordinals))):
            raise ValueError(f"noncontiguous component ordinals for {input_id}")

    normalized_components.sort(
        key=lambda component: (
            _utf16_sort_key(str(component["input_id"])),
            int(component["component_ordinal"]),
        )
    )
    return {
        "schema_version": projection["schema_version"],
        "canonicalization_id": projection["canonicalization_id"],
        "components": normalized_components,
    }


def _public_redacted_projection(source: object) -> dict[str, object]:
    projection = _require_exact_keys(
        source,
        {
            "schema_version",
            "public_projection_id",
            "canonicalization_id",
            "manifest_id",
            "dataset_roles",
            "policy_states",
            "redacted_evidence_refs",
            "published_hashes",
        },
        context="public redacted projection",
    )
    if projection["schema_version"] != "public_redacted_projection_v1":
        raise ValueError("unexpected public projection schema")
    if projection["canonicalization_id"] != "pit_canonical_json_v1":
        raise ValueError("unexpected public projection canonicalization")
    public_projection_id = _require_safe_public_id(
        projection["public_projection_id"],
        context="public projection ID",
    )
    manifest_id = _require_safe_public_id(
        projection["manifest_id"],
        context="public manifest ID",
    )

    raw_roles = projection["dataset_roles"]
    if not isinstance(raw_roles, list):
        raise ValueError("dataset roles must be a list")
    roles = [
        _require_safe_public_id(role, context="dataset role")
        for role in raw_roles
    ]
    if len(roles) != len(set(roles)):
        raise ValueError("duplicate dataset role")
    roles.sort(key=_utf16_sort_key)

    raw_policy_states = projection["policy_states"]
    if not isinstance(raw_policy_states, list):
        raise ValueError("policy states must be a list")
    policy_states: list[dict[str, object]] = []
    policy_ids: set[str] = set()
    for raw_policy in raw_policy_states:
        policy = _require_exact_keys(
            raw_policy,
            {"policy_id", "state"},
            context="public policy state",
        )
        policy_id = _require_safe_public_id(
            policy["policy_id"],
            context="public policy ID",
        )
        if policy_id in policy_ids:
            raise ValueError("duplicate public policy ID")
        policy_ids.add(policy_id)
        if policy["state"] not in {"accepted", "diagnostic_only", "blocked"}:
            raise ValueError("invalid public policy state")
        policy_states.append(dict(policy))
    policy_states.sort(key=lambda item: _utf16_sort_key(str(item["policy_id"])))

    raw_evidence_refs = projection["redacted_evidence_refs"]
    if not isinstance(raw_evidence_refs, list):
        raise ValueError("redacted evidence references must be a list")
    evidence_refs: list[dict[str, object]] = []
    evidence_ids: set[str] = set()
    for raw_evidence in raw_evidence_refs:
        evidence = _require_exact_keys(
            raw_evidence,
            {"evidence_ref_id"},
            context="redacted evidence reference",
        )
        evidence_id = _require_safe_public_id(
            evidence["evidence_ref_id"],
            context="redacted evidence ID",
        )
        if evidence_id in evidence_ids:
            raise ValueError("duplicate redacted evidence ID")
        evidence_ids.add(evidence_id)
        evidence_refs.append(dict(evidence))
    evidence_refs.sort(
        key=lambda item: _utf16_sort_key(str(item["evidence_ref_id"]))
    )

    raw_hashes = projection["published_hashes"]
    if not isinstance(raw_hashes, list):
        raise ValueError("published hashes must be a list")
    published_hashes: list[dict[str, object]] = []
    hash_ids: set[str] = set()
    for raw_hash in raw_hashes:
        published_hash = _require_exact_keys(
            raw_hash,
            {"hash_id", "sha256", "publication_approval_ref_id"},
            context="publication-approved hash",
        )
        hash_id = _require_safe_public_id(
            published_hash["hash_id"],
            context="published hash ID",
        )
        if hash_id in hash_ids:
            raise ValueError("duplicate published hash ID")
        hash_ids.add(hash_id)
        digest = published_hash["sha256"]
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ValueError("published digest must be lowercase SHA-256")
        _require_safe_public_id(
            published_hash["publication_approval_ref_id"],
            context="hash publication approval reference",
        )
        published_hashes.append(dict(published_hash))
    published_hashes.sort(
        key=lambda item: _utf16_sort_key(str(item["hash_id"]))
    )

    return {
        "schema_version": projection["schema_version"],
        "public_projection_id": public_projection_id,
        "canonicalization_id": projection["canonicalization_id"],
        "manifest_id": manifest_id,
        "dataset_roles": roles,
        "policy_states": policy_states,
        "redacted_evidence_refs": evidence_refs,
        "published_hashes": published_hashes,
    }


def _assert_value_error(operation: object) -> str:
    if not callable(operation):
        raise AssertionError("operation must be callable")
    try:
        operation()
    except ValueError as error:
        return str(error)
    raise AssertionError("operation did not fail closed")


_LEDGER_EVENT_TYPES = frozenset(
    """
    LEDGER_EPOCH_CREATED CAMPAIGN_ALLOCATED EXPERIMENT_ALLOCATED
    TRIAL_FAMILY_REGISTERED SAMPLE_REGISTERED CAMPAIGN_ENTITY_BOUND
    STAGE3_SAMPLE_REFERENCE_BOUND TRIAL_ALLOCATED CAMPAIGN_INVENTORY_SEALED
    CAMPAIGN_AMENDMENT_PROPOSED CAMPAIGN_INVENTORY_AMENDED ATTEMPT_ALLOCATED
    ATTEMPT_STARTED ATTEMPT_COMPLETED ATTEMPT_FAILED ATTEMPT_INVALID
    ATTEMPT_ABORTED TRIAL_COMPLETED TRIAL_FAILED TRIAL_INVALID TRIAL_ABORTED
    TRIAL_EXCLUDED ARTIFACT_DISPOSITION_RECORDED ACCESS_INTENT ACCESS_STARTED
    ACCESS_COMPLETED ACCESS_FAILED ACCESS_ABORTED ACCESS_CANCELLED
    EXPOSURE_DECISION CAMPAIGN_EVIDENCE_FROZEN CHECKPOINT_REFERENCE_RECORDED
    CAMPAIGN_ACCOUNTING_CLOSED REVIEW_DECIDED PROMOTION_DECIDED
    CAMPAIGN_ADJUDICATED EVENT_SUPERSEDED
    """.split()
)
_EVENT_KEYS = set("ledger_id sequence event_id event_type campaign_scope_ids previous_event_sha256 facts event_sha256".split())
_CHECKPOINT_KEYS = set(
    "schema_version canonicalization_id checkpoint_id ledger_id campaign_id checkpoint_generation "
    "previous_checkpoint_id previous_checkpoint_sha256 campaign_evidence_version_id "
    "campaign_evidence_sha256 campaign_evidence_checkpoint_id campaign_evidence_checkpoint_sha256 "
    "adjudication_event_sequence adjudication_event_id adjudication_event_sha256 created_at "
    "issuer_authority_reference".split()
)
_EVIDENCE_KEYS = set("schema_version canonicalization_id checkpoint_id ledger_id campaign_id evidence_sequence evidence_event_sha256 freeze_event_sequence freeze_event_id freeze_event_sha256 campaign_evidence_version_id campaign_evidence_sha256 sealed_trial_inventory_sha256 sealed_semantic_trial_count terminal_semantic_trial_count allocated_attempt_count terminal_attempt_count created_at issuer_authority_reference".split())
_FREEZE_KEYS = set("evidence_sequence evidence_event_sha256 campaign_evidence_version_id campaign_evidence_sha256 sealed_trial_inventory_sha256 sealed_trial_ids terminal_trial_ids terminal_trial_disposition_event_type allocated_attempt_bindings terminal_attempt_ids".split())
_REFERENCE_KEYS = {"checkpoint_id", "checkpoint_sha256"}
_SYNTHETIC_UNSUPPORTED = set("TRIAL_COMPLETED TRIAL_FAILED TRIAL_INVALID TRIAL_ABORTED ATTEMPT_ALLOCATED ATTEMPT_STARTED ATTEMPT_COMPLETED ATTEMPT_FAILED ATTEMPT_INVALID ATTEMPT_ABORTED".split())
_ADJUDICATION_KEYS = set(
    "checkpoint_id campaign_evidence_version_id campaign_evidence_sha256 campaign_evidence_checkpoint_id "
    "campaign_evidence_checkpoint_sha256 sealed_trial_inventory_sha256 closure_event_sequence "
    "closure_event_id closure_event_sha256 review_event_sequence review_event_id review_event_sha256 "
    "decision_event_sequence decision_event_id decision_event_sha256 decision_outcome".split()
)
_CLOSURE_KEYS = set(
    "freeze_event_id freeze_event_sha256 campaign_evidence_version_id campaign_evidence_sha256 "
    "campaign_evidence_checkpoint_id campaign_evidence_checkpoint_sha256 sealed_trial_inventory_sha256".split()
)
_REVIEW_KEYS = set(
    "closure_event_id closure_event_sha256 campaign_evidence_checkpoint_id "
    "campaign_evidence_checkpoint_sha256 review_outcome".split()
)
_DECISION_KEYS = set(
    "review_event_id review_event_sha256 campaign_evidence_checkpoint_id "
    "campaign_evidence_checkpoint_sha256 decision_outcome".split()
)
_CURRENTNESS_KEYS = set(
    "ledger_id campaign_id current_checkpoint_generation current_checkpoint_id current_checkpoint_sha256 "
    "pending_checkpoint_generation external_currentness_proof_verified".split()
)
_LEDGER_ID = "ldg_00000000000000000000000000000001"
_CAMPAIGN_ID = "cmp_00000000000000000000000000000002"
_OTHER_CAMPAIGN_ID = "cmp_00000000000000000000000000000003"


def _safe_int(value: object, minimum: int, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= (2**53) - 1:
        raise ValueError(f"{context} must be an I-JSON-safe integer")
    return value


def _lower_sha(value: object, context: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError(f"{context} must be lowercase SHA-256")
    return value


def _campaign_tail_test_event_projection(source: object) -> dict[str, object]:
    event = _require_exact_keys(source, _EVENT_KEYS, context="test event")
    _require_ledger_typed_id(event["ledger_id"], prefix="ldg", context="ledger_id")
    _safe_int(event["sequence"], 0, "sequence")
    _require_ledger_typed_id(event["event_id"], prefix="evt", context="event_id")
    event_type = _require_stable_id(event["event_type"], context="event type")
    if event_type not in _LEDGER_EVENT_TYPES:
        raise ValueError("unknown ledger event type")
    scopes = event["campaign_scope_ids"]
    if not isinstance(scopes, list):
        raise ValueError("campaign scopes must be a list")
    for scope in scopes:
        _require_ledger_typed_id(scope, prefix="cmp", context="campaign scope")
    if scopes != sorted(set(scopes)) or not isinstance(event["facts"], dict):
        raise ValueError("campaign scopes or facts are invalid")
    if event["previous_event_sha256"] is not None:
        _lower_sha(event["previous_event_sha256"], "previous digest")
    _lower_sha(event["event_sha256"], "event digest")
    return {key: event[key] for key in _EVENT_KEYS - {"event_sha256"}}


def _verified_campaign_chain(source: object) -> list[dict[str, object]]:
    if not isinstance(source, list) or not source:
        raise ValueError("retained ledger must be nonempty")
    verified: list[dict[str, object]] = []
    seen, previous, ledger_id = set(), None, None
    for sequence, raw in enumerate(source):
        event = _campaign_tail_test_event_projection(raw)
        digest = hashlib.sha256(_ascii_jcs_golden_bytes(event)).hexdigest()
        if (event["sequence"], event["previous_event_sha256"], raw["event_sha256"]) != (sequence, previous, digest):
            raise ValueError("event sequence, chain, or digest mismatch")
        ledger_id = event["ledger_id"] if ledger_id is None else ledger_id
        if event["ledger_id"] != ledger_id or event["event_id"] in seen:
            raise ValueError("ledger ID changed or event ID duplicated")
        seen.add(event["event_id"])
        verified.append({**event, "event_sha256": digest})
        previous = digest
    return verified


def _campaign_adjudication_checkpoint_projection(source: object) -> dict[str, object]:
    item = _require_exact_keys(source, _CHECKPOINT_KEYS, context="checkpoint")
    if (item["schema_version"], item["canonicalization_id"]) != (
        "campaign_adjudication_checkpoint_v1", "pit_canonical_json_v1"
    ):
        raise ValueError("checkpoint schema/canonicalization mismatch")
    for field in ("checkpoint_id", "campaign_evidence_version_id", "campaign_evidence_checkpoint_id", "issuer_authority_reference"):
        _require_stable_id(item[field], context=field)
    _require_ledger_typed_id(item["ledger_id"], prefix="ldg", context="ledger_id")
    _require_ledger_typed_id(item["campaign_id"], prefix="cmp", context="campaign_id")
    _require_ledger_typed_id(item["adjudication_event_id"], prefix="evt", context="adjudication ID")
    generation = _safe_int(item["checkpoint_generation"], 1, "generation")
    _safe_int(item["adjudication_event_sequence"], 0, "adjudication sequence")
    for field in ("campaign_evidence_sha256", "campaign_evidence_checkpoint_sha256", "adjudication_event_sha256"):
        _lower_sha(item[field], field)
    prior = item["previous_checkpoint_id"], item["previous_checkpoint_sha256"]
    if (prior[0] is None) != (prior[1] is None) or (generation == 1) != (prior == (None, None)):
        raise ValueError("checkpoint predecessor nullability mismatch")
    if prior[0] is not None:
        _require_stable_id(prior[0], context="previous checkpoint ID")
        _lower_sha(prior[1], "previous checkpoint digest")
    _require_normalized_utc_timestamp(item["created_at"], context="created_at")
    return dict(item)


def _evidence_projection(source: object) -> dict[str, object]:
    item = _require_exact_keys(source, _EVIDENCE_KEYS, context="evidence checkpoint")
    if (item["schema_version"], item["canonicalization_id"]) != ("campaign_evidence_checkpoint_v1", "pit_canonical_json_v1"):
        raise ValueError("evidence checkpoint schema/canonicalization mismatch")
    for field in ("checkpoint_id", "campaign_evidence_version_id", "issuer_authority_reference"):
        _require_stable_id(item[field], context=field)
    for field, prefix in (("ledger_id", "ldg"), ("campaign_id", "cmp"), ("freeze_event_id", "evt")):
        _require_ledger_typed_id(item[field], prefix=prefix, context=field)
    for field in ("evidence_event_sha256", "freeze_event_sha256", "campaign_evidence_sha256", "sealed_trial_inventory_sha256"):
        _lower_sha(item[field], field)
    for field in "evidence_sequence freeze_event_sequence sealed_semantic_trial_count terminal_semantic_trial_count allocated_attempt_count terminal_attempt_count".split():
        _safe_int(item[field], 0, field)
    if item["freeze_event_sequence"] != item["evidence_sequence"] + 1:
        raise ValueError("freeze sequence must equal evidence sequence plus one")
    _require_normalized_utc_timestamp(item["created_at"], context="evidence created_at")
    return dict(item)


def _evidence_record(source: object) -> dict:
    record = _require_exact_keys(source, {"checkpoint", "checkpoint_sha256"}, context="evidence record")
    item = _evidence_projection(record["checkpoint"])
    digest = _lower_sha(record["checkpoint_sha256"], "evidence checkpoint digest")
    if digest != hashlib.sha256(_ascii_jcs_golden_bytes(item)).hexdigest():
        raise ValueError("evidence checkpoint digest mismatch")
    return {**item, "checkpoint_sha256": digest}


def _campaign_prefix_object(events: list[dict], evidence: dict) -> dict:
    sequence = evidence["evidence_sequence"]
    if sequence >= len(events):
        raise ValueError("ledger is truncated below evidence cutoff")
    cutoff = events[sequence]
    if cutoff["event_sha256"] != evidence["evidence_event_sha256"]:
        raise ValueError("evidence cutoff event digest mismatch")
    campaign_id = evidence["campaign_id"]
    return {
        "schema_version": "campaign_evidence_prefix_v1",
        "canonicalization_id": "pit_canonical_json_v1",
        "ledger_id": evidence["ledger_id"], "campaign_id": campaign_id,
        "evidence_sequence": sequence, "evidence_event_sha256": evidence["evidence_event_sha256"],
        "campaign_events": [
            {"sequence": event["sequence"], "event_id": event["event_id"], "event_sha256": event["event_sha256"]}
            for event in events[: sequence + 1] if campaign_id in event["campaign_scope_ids"]
        ],
    }


def _campaign_evidence_prefix(events: list[dict], evidence: dict, candidate: object | None = None) -> dict:
    expected = _campaign_prefix_object(events, evidence)
    if candidate is not None and (not isinstance(candidate, dict) or candidate != expected):
        raise ValueError("campaign evidence prefix is not all-and-only")
    digest = hashlib.sha256(_ascii_jcs_golden_bytes(expected)).hexdigest()
    if digest != evidence["campaign_evidence_sha256"]:
        raise ValueError("campaign evidence prefix digest mismatch")
    return expected


def _typed_id_set(source: object, prefix: str, context: str) -> set[str]:
    if not isinstance(source, list):
        raise ValueError(f"{context} must be a list")
    values = {_require_ledger_typed_id(item, prefix=prefix, context=context) for item in source}
    if len(values) != len(source):
        raise ValueError(f"{context} must be unique")
    return values


def _synthetic_count_semantics(events: list[dict], facts: dict, evidence: dict) -> None:
    sealed = _typed_id_set(facts["sealed_trial_ids"], "trl", "sealed trial ID")
    terminal = _typed_id_set(facts["terminal_trial_ids"], "trl", "terminal trial ID")
    if facts["terminal_trial_disposition_event_type"] != "TRIAL_EXCLUDED":
        raise ValueError("synthetic terminal trial disposition is not fixed")
    campaign_events = [event for event in events[: evidence["evidence_sequence"] + 1] if evidence["campaign_id"] in event["campaign_scope_ids"]]
    inventories = [event for event in campaign_events if event["event_type"] == "CAMPAIGN_INVENTORY_SEALED"]
    if len(inventories) != 1:
        raise ValueError("synthetic inventory is not unique")
    inventory = _require_exact_keys(inventories[0]["facts"], {"sealed_trial_inventory_sha256", "sealed_trial_ids"}, context="synthetic inventory facts")
    inventory_trials = _typed_id_set(inventory["sealed_trial_ids"], "trl", "inventory trial ID")
    excluded_trials = _typed_id_set(
        [_require_exact_keys(event["facts"], {"trial_id"}, context="synthetic exclusion facts")["trial_id"]
         for event in campaign_events if event["event_type"] == "TRIAL_EXCLUDED"],
        "trl", "excluded trial ID",
    )
    if any(event["event_type"] in _SYNTHETIC_UNSUPPORTED for event in campaign_events):
        raise ValueError("event is outside the fixed all-excluded synthetic vector")
    attempts = facts["allocated_attempt_bindings"], facts["terminal_attempt_ids"]
    if attempts != ([], []):
        raise ValueError("synthetic vector requires exact empty attempt sets")
    counts = len(sealed), len(terminal), 0, 0
    recorded = tuple(evidence[field] for field in "sealed_semantic_trial_count terminal_semantic_trial_count allocated_attempt_count terminal_attempt_count".split())
    if (
        inventory["sealed_trial_inventory_sha256"] != evidence["sealed_trial_inventory_sha256"]
        or sealed != inventory_trials or terminal != excluded_trials or sealed != terminal or counts != recorded
    ):
        raise ValueError("synthetic trial/attempt set or count mismatch")


def _evidence_checkpoint_semantics(events: list[dict], evidence: dict, closure_sequence: int) -> None:
    _campaign_evidence_prefix(events, evidence)
    freeze_sequence = evidence["freeze_event_sequence"]
    if freeze_sequence >= len(events):
        raise ValueError("ledger is truncated below evidence freeze")
    freeze = events[freeze_sequence]
    if (
        (freeze["event_id"], freeze["event_sha256"], freeze["event_type"]) !=
        (evidence["freeze_event_id"], evidence["freeze_event_sha256"], "CAMPAIGN_EVIDENCE_FROZEN")
        or freeze["campaign_scope_ids"] != [evidence["campaign_id"]]
        or freeze["previous_event_sha256"] != evidence["evidence_event_sha256"]
    ):
        raise ValueError("evidence freeze identity/scope/predecessor mismatch")
    facts = _require_exact_keys(freeze["facts"], _FREEZE_KEYS, context="freeze facts")
    for field in "evidence_sequence evidence_event_sha256 campaign_evidence_version_id campaign_evidence_sha256 sealed_trial_inventory_sha256".split():
        if facts[field] != evidence[field]:
            raise ValueError("freeze evidence facts mismatch")
    _synthetic_count_semantics(events, facts, evidence)
    target_interval = [event for event in events[freeze_sequence + 1 : closure_sequence]
                       if evidence["campaign_id"] in event["campaign_scope_ids"]]
    if len(target_interval) != 1 or target_interval[0]["event_type"] != "CHECKPOINT_REFERENCE_RECORDED":
        raise ValueError("target campaign interval must contain only its checkpoint reference")
    reference = _require_exact_keys(target_interval[0]["facts"], _REFERENCE_KEYS, context="checkpoint reference")
    if (reference["checkpoint_id"], reference["checkpoint_sha256"]) != (evidence["checkpoint_id"], evidence["checkpoint_sha256"]):
        raise ValueError("evidence checkpoint reference mismatch")


def _checkpoint_lineage(source: object, ledger_id: str) -> tuple[str, list[tuple[dict[str, object], str]]]:
    if not isinstance(source, list) or not source:
        raise ValueError("checkpoint history must be nonempty")
    lineage: list[tuple[dict[str, object], str]] = []
    seen, campaign_id = set(), None
    for generation, raw in enumerate(source, start=1):
        record = _require_exact_keys(raw, {"checkpoint", "checkpoint_sha256"}, context="checkpoint record")
        item = _campaign_adjudication_checkpoint_projection(record["checkpoint"])
        digest = _lower_sha(record["checkpoint_sha256"], "checkpoint digest")
        prior = (None, None) if not lineage else (lineage[-1][0]["checkpoint_id"], lineage[-1][1])
        if digest != hashlib.sha256(_ascii_jcs_golden_bytes(item)).hexdigest():
            raise ValueError("checkpoint digest mismatch")
        if (item["checkpoint_generation"], item["previous_checkpoint_id"], item["previous_checkpoint_sha256"]) != (generation, *prior):
            raise ValueError("checkpoint generation/predecessor mismatch")
        campaign_id = item["campaign_id"] if campaign_id is None else campaign_id
        if item["ledger_id"] != ledger_id or item["campaign_id"] != campaign_id or item["checkpoint_id"] in seen:
            raise ValueError("checkpoint authority changed or ID duplicated")
        seen.add(item["checkpoint_id"])
        lineage.append((item, digest))
    assert isinstance(campaign_id, str)
    return campaign_id, lineage


def _evidence_binding(left: dict, right: dict, pairs: tuple[tuple[str, str], ...], context: str) -> None:
    if any(left[a] != right[b] for a, b in pairs):
        raise ValueError(f"{context} evidence binding mismatch")


def _event_ref(events: list[dict], facts: dict, prefix: str, event_type: str, campaign_id: str, anchor: int) -> dict:
    sequence = _safe_int(facts[f"{prefix}_event_sequence"], 0, f"{prefix} sequence")
    if sequence >= anchor:
        raise ValueError(f"{prefix} must precede adjudication")
    event = events[sequence]
    if (
        (event["event_id"], event["event_sha256"], event["event_type"])
        != (facts[f"{prefix}_event_id"], facts[f"{prefix}_event_sha256"], event_type)
        or campaign_id not in event["campaign_scope_ids"]
    ):
        raise ValueError(f"{prefix} reference mismatch")
    matching = [item for item in events[:anchor] if item["event_type"] == event_type and campaign_id in item["campaign_scope_ids"]]
    if not matching or matching[-1]["sequence"] != sequence:
        raise ValueError(f"{prefix} is not current")
    return event


_CHECKPOINT_EVIDENCE_BINDING = (
    ("ledger_id", "ledger_id"), ("campaign_id", "campaign_id"),
    ("campaign_evidence_version_id", "campaign_evidence_version_id"),
    ("campaign_evidence_sha256", "campaign_evidence_sha256"),
    ("campaign_evidence_checkpoint_id", "checkpoint_id"),
    ("campaign_evidence_checkpoint_sha256", "checkpoint_sha256"),
)
_ADJUDICATION_EVIDENCE_BINDING = _CHECKPOINT_EVIDENCE_BINDING[2:] + (
    ("sealed_trial_inventory_sha256", "sealed_trial_inventory_sha256"),
)
_EVIDENCE_CHECKPOINT_BINDING = (
    ("campaign_evidence_checkpoint_id", "checkpoint_id"),
    ("campaign_evidence_checkpoint_sha256", "checkpoint_sha256"),
)


def _generation_terminal_binding(events: list[dict], checkpoint: dict, evidence: dict) -> int:
    campaign_id = checkpoint["campaign_id"]
    _evidence_binding(checkpoint, evidence, _CHECKPOINT_EVIDENCE_BINDING, "checkpoint")
    anchor = checkpoint["adjudication_event_sequence"]
    if anchor >= len(events):
        raise ValueError("ledger is truncated below adjudication")
    event = events[anchor]
    if (
        (event["event_id"], event["event_sha256"], event["event_type"])
        != (checkpoint["adjudication_event_id"], checkpoint["adjudication_event_sha256"], "CAMPAIGN_ADJUDICATED")
        or campaign_id not in event["campaign_scope_ids"]
    ):
        raise ValueError("checkpoint anchor mismatch")
    facts = _require_exact_keys(event["facts"], _ADJUDICATION_KEYS, context="adjudication facts")
    if facts["checkpoint_id"] != checkpoint["checkpoint_id"]:
        raise ValueError("checkpoint preallocation mismatch")
    _evidence_binding(facts, evidence, _ADJUDICATION_EVIDENCE_BINDING, "adjudication")
    closure = _event_ref(events, facts, "closure", "CAMPAIGN_ACCOUNTING_CLOSED", campaign_id, anchor)
    review = _event_ref(events, facts, "review", "REVIEW_DECIDED", campaign_id, anchor)
    decision = _event_ref(events, facts, "decision", "PROMOTION_DECIDED", campaign_id, anchor)
    if not closure["sequence"] < review["sequence"] < decision["sequence"] < anchor:
        raise ValueError("terminal event order mismatch")
    allowed = {"CAMPAIGN_ACCOUNTING_CLOSED", "REVIEW_DECIDED", "PROMOTION_DECIDED", "CAMPAIGN_ADJUDICATED"}
    if any(campaign_id in item["campaign_scope_ids"] and item["event_type"] not in allowed for item in events[closure["sequence"] : anchor + 1]):
        raise ValueError("campaign evidence changed after closure")
    closure_facts = _require_exact_keys(closure["facts"], _CLOSURE_KEYS, context="closure facts")
    review_facts = _require_exact_keys(review["facts"], _REVIEW_KEYS, context="review facts")
    decision_facts = _require_exact_keys(decision["facts"], _DECISION_KEYS, context="decision facts")
    _evidence_checkpoint_semantics(events, evidence, closure["sequence"])
    _evidence_binding(
        closure_facts, evidence,
        (("freeze_event_id", "freeze_event_id"), ("freeze_event_sha256", "freeze_event_sha256"))
        + _ADJUDICATION_EVIDENCE_BINDING,
        "closure",
    )
    if (
        (review_facts["closure_event_id"], review_facts["closure_event_sha256"], review_facts["review_outcome"])
        != (closure["event_id"], closure["event_sha256"], "ACCEPTED")
        or (decision_facts["review_event_id"], decision_facts["review_event_sha256"])
        != (review["event_id"], review["event_sha256"])
    ):
        raise ValueError("review or decision predecessor mismatch")
    for item in (review_facts, decision_facts):
        _evidence_binding(item, evidence, _EVIDENCE_CHECKPOINT_BINDING, "review/decision")
    outcome = facts["decision_outcome"]
    if not isinstance(outcome, str) or outcome not in {"PROMOTED", "REJECTED", "INCONCLUSIVE", "INVALIDATED"} or decision_facts["decision_outcome"] != outcome:
        raise ValueError("terminal outcome mismatch")
    return anchor


def _current_checkpoint(source: object, ledger_id: str, campaign_id: str, lineage: list[tuple[dict, str]]) -> None:
    item = _require_exact_keys(source, _CURRENTNESS_KEYS, context="currentness")
    _require_ledger_typed_id(item["ledger_id"], prefix="ldg", context="current ledger")
    _require_ledger_typed_id(item["campaign_id"], prefix="cmp", context="current campaign")
    generation = _safe_int(item["current_checkpoint_generation"], 1, "current generation")
    _require_stable_id(item["current_checkpoint_id"], context="current checkpoint ID")
    _lower_sha(item["current_checkpoint_sha256"], "current checkpoint digest")
    pending = item["pending_checkpoint_generation"]
    if pending is not None and _safe_int(pending, 1, "pending generation") != generation + 1:
        raise ValueError("pending generation must equal current plus one")
    head, digest = lineage[-1]
    if (
        (item["ledger_id"], item["campaign_id"]) != (ledger_id, campaign_id)
        or item["external_currentness_proof_verified"] is not True or pending is not None
        or (generation, item["current_checkpoint_id"], item["current_checkpoint_sha256"])
        != (head["checkpoint_generation"], head["checkpoint_id"], digest)
    ):
        raise ValueError("checkpoint is pending, old, or externally unverified")


def _require_campaign_adjudication_checkpoint_facts(
    *, retained_events: object, retained_checkpoints: object,
    retained_evidence_checkpoints: object, currentness: object,
) -> str:
    events = _verified_campaign_chain(retained_events)
    ledger_id = events[0]["ledger_id"]
    campaign_id, lineage = _checkpoint_lineage(retained_checkpoints, ledger_id)
    if not isinstance(retained_evidence_checkpoints, list) or len(retained_evidence_checkpoints) != len(lineage):
        raise ValueError("every generation needs one evidence checkpoint")
    evidences = [_evidence_record(item) for item in retained_evidence_checkpoints]
    if len({item["checkpoint_id"] for item in evidences}) != len(evidences):
        raise ValueError("duplicate evidence checkpoint")
    anchors = []
    for (checkpoint, _), evidence in zip(lineage, evidences, strict=True):
        if (
            (evidence["ledger_id"], evidence["campaign_id"]) != (ledger_id, campaign_id)
            or checkpoint["campaign_evidence_checkpoint_id"] != evidence["checkpoint_id"]
        ):
            raise ValueError("generation/evidence correspondence mismatch")
        anchors.append(_generation_terminal_binding(events, checkpoint, evidence))
    adjudications = [
        event["sequence"] for event in events
        if event["event_type"] == "CAMPAIGN_ADJUDICATED" and campaign_id in event["campaign_scope_ids"]
    ]
    if anchors != sorted(set(anchors)) or anchors != adjudications:
        raise ValueError("generation/adjudication correspondence mismatch")
    if any(campaign_id in event["campaign_scope_ids"] for event in events[anchors[-1] + 1 :]):
        raise ValueError("post-adjudication campaign suffix is stale")
    _current_checkpoint(currentness, ledger_id, campaign_id, lineage)
    return lineage[-1][1]


def _append_tail_event(events: list[dict], event_type: str, scopes: list[str], facts: dict, nonce: int | None = None) -> dict:
    sequence = len(events)
    event = {
        "ledger_id": _LEDGER_ID, "sequence": sequence,
        "event_id": f"evt_{(nonce or sequence + 1):032x}", "event_type": event_type,
        "campaign_scope_ids": scopes,
        "previous_event_sha256": events[-1]["event_sha256"] if events else None,
        "facts": facts, "event_sha256": "0" * 64,
    }
    projection = _campaign_tail_test_event_projection(event)
    event["event_sha256"] = hashlib.sha256(_ascii_jcs_golden_bytes(projection)).hexdigest()
    events.append(event)
    return event


def _rechain_tail(
    source: list[dict], *, refresh_terminal_refs: bool = False
) -> list[dict]:
    events, previous = deepcopy(source), None
    latest = {}
    for sequence, event in enumerate(events):
        if refresh_terminal_refs:
            references = {
                "REVIEW_DECIDED": (("closure", "CAMPAIGN_ACCOUNTING_CLOSED"),),
                "PROMOTION_DECIDED": (("review", "REVIEW_DECIDED"),),
                "CAMPAIGN_ADJUDICATED": (
                    ("closure", "CAMPAIGN_ACCOUNTING_CLOSED"),
                    ("review", "REVIEW_DECIDED"),
                    ("decision", "PROMOTION_DECIDED"),
                ),
            }
            for prefix, event_type in references.get(event["event_type"], ()):
                reference = _event_reference(prefix, latest[event_type])
                if event["event_type"] != "CAMPAIGN_ADJUDICATED":
                    del reference[f"{prefix}_event_sequence"]
                event["facts"].update(reference)
        event.update(sequence=sequence, previous_event_sha256=previous, event_sha256="0" * 64)
        projection = _campaign_tail_test_event_projection(event)
        event["event_sha256"] = hashlib.sha256(_ascii_jcs_golden_bytes(projection)).hexdigest()
        previous = event["event_sha256"]
        latest[event["event_type"]] = event
    return events


def _pack_checkpoint(item: dict) -> dict:
    projection = _campaign_adjudication_checkpoint_projection(item)
    return {"checkpoint": item, "checkpoint_sha256": hashlib.sha256(_ascii_jcs_golden_bytes(projection)).hexdigest()}


def _pack_evidence_checkpoint(item: dict) -> dict:
    projection = _evidence_projection(item)
    return {
        "checkpoint": item,
        "checkpoint_sha256": hashlib.sha256(
            _ascii_jcs_golden_bytes(projection)
        ).hexdigest(),
    }


def _currentness(record: dict, pending: int | None = None) -> dict:
    item = record["checkpoint"]
    return {
        "ledger_id": item["ledger_id"], "campaign_id": item["campaign_id"],
        "current_checkpoint_generation": item["checkpoint_generation"],
        "current_checkpoint_id": item["checkpoint_id"],
        "current_checkpoint_sha256": record["checkpoint_sha256"],
        "pending_checkpoint_generation": pending,
        "external_currentness_proof_verified": True,
    }


def _event_reference(prefix: str, event: dict) -> dict:
    return {
        f"{prefix}_event_sequence": event["sequence"],
        f"{prefix}_event_id": event["event_id"],
        f"{prefix}_event_sha256": event["event_sha256"],
    }


def _build_generation(generation: int, outcome: str, events: list[dict] | None = None, previous: dict | None = None) -> tuple[list, dict, dict]:
    events = deepcopy(events) if events is not None else []
    inventory = hashlib.sha256(b"sealed-inventory").hexdigest()
    trial_id = "trl_00000000000000000000000000000001"
    if not events:
        _append_tail_event(events, "LEDGER_EPOCH_CREATED", [], {"epoch": 1})
        _append_tail_event(events, "CAMPAIGN_INVENTORY_SEALED", [_CAMPAIGN_ID], {"sealed_trial_inventory_sha256": inventory, "sealed_trial_ids": [trial_id]})
        _append_tail_event(events, "TRIAL_EXCLUDED", [_CAMPAIGN_ID], {"trial_id": trial_id})
        _append_tail_event(events, "CAMPAIGN_ACCOUNTING_CLOSED", [_OTHER_CAMPAIGN_ID], {"other_campaign_interleave": True})
        _append_tail_event(events, "TRIAL_FAMILY_REGISTERED", [], {"unbound_global_family_interleave": True})
    version, evidence_id = f"campaign-evidence-version-{generation}", f"campaign-evidence-checkpoint-{generation}"
    cutoff = events[-1]
    evidence_basis = {"ledger_id": _LEDGER_ID, "campaign_id": _CAMPAIGN_ID, "evidence_sequence": cutoff["sequence"], "evidence_event_sha256": cutoff["event_sha256"]}
    evidence_sha = hashlib.sha256(_ascii_jcs_golden_bytes(_campaign_prefix_object(events, evidence_basis))).hexdigest()
    freeze_facts = {
        "evidence_sequence": evidence_basis["evidence_sequence"], "evidence_event_sha256": evidence_basis["evidence_event_sha256"],
        "campaign_evidence_version_id": version, "campaign_evidence_sha256": evidence_sha, "sealed_trial_inventory_sha256": inventory,
        "sealed_trial_ids": [trial_id], "terminal_trial_ids": [trial_id], "terminal_trial_disposition_event_type": "TRIAL_EXCLUDED",
        "allocated_attempt_bindings": [], "terminal_attempt_ids": []}
    freeze = _append_tail_event(events, "CAMPAIGN_EVIDENCE_FROZEN", [_CAMPAIGN_ID], freeze_facts)
    evidence_item = {
        "schema_version": "campaign_evidence_checkpoint_v1", "canonicalization_id": "pit_canonical_json_v1",
        "checkpoint_id": evidence_id, "ledger_id": _LEDGER_ID, "campaign_id": _CAMPAIGN_ID, **evidence_basis,
        "freeze_event_sequence": freeze["sequence"], "freeze_event_id": freeze["event_id"], "freeze_event_sha256": freeze["event_sha256"],
        "campaign_evidence_version_id": version, "campaign_evidence_sha256": evidence_sha, "sealed_trial_inventory_sha256": inventory,
        "sealed_semantic_trial_count": 1, "terminal_semantic_trial_count": 1,
        "allocated_attempt_count": 0, "terminal_attempt_count": 0,
        "created_at": f"2026-07-27T00:00:0{generation}Z", "issuer_authority_reference": "owner-approved-authority-reference",
    }
    evidence = _pack_evidence_checkpoint(evidence_item)
    evidence_checkpoint_sha = evidence["checkpoint_sha256"]
    common = {"campaign_evidence_version_id": version, "campaign_evidence_sha256": evidence_sha, "campaign_evidence_checkpoint_id": evidence_id, "campaign_evidence_checkpoint_sha256": evidence_checkpoint_sha}
    _append_tail_event(events, "CHECKPOINT_REFERENCE_RECORDED", [_CAMPAIGN_ID], {"checkpoint_id": evidence_id, "checkpoint_sha256": evidence_checkpoint_sha})
    _append_tail_event(events, "EVENT_SUPERSEDED", [_OTHER_CAMPAIGN_ID], {"other_campaign_interval": True})
    _append_tail_event(events, "TRIAL_FAMILY_REGISTERED", [], {"global_interval": True})
    closure = _append_tail_event(events, "CAMPAIGN_ACCOUNTING_CLOSED", [_CAMPAIGN_ID], {
        **common, "freeze_event_id": freeze["event_id"], "freeze_event_sha256": freeze["event_sha256"], "sealed_trial_inventory_sha256": inventory,
    })
    review = _append_tail_event(
        events, "REVIEW_DECIDED", [_CAMPAIGN_ID], {"closure_event_id": closure["event_id"], "closure_event_sha256": closure["event_sha256"],
        "campaign_evidence_checkpoint_id": evidence_id, "campaign_evidence_checkpoint_sha256": evidence_checkpoint_sha, "review_outcome": "ACCEPTED"},
    )
    decision = _append_tail_event(events, "PROMOTION_DECIDED", [_CAMPAIGN_ID], {
        "review_event_id": review["event_id"], "review_event_sha256": review["event_sha256"], "campaign_evidence_checkpoint_id": evidence_id,
        "campaign_evidence_checkpoint_sha256": evidence_checkpoint_sha, "decision_outcome": outcome,
    })
    checkpoint_id = f"campaign-adjudication-checkpoint-{generation}"
    adjudication = _append_tail_event(events, "CAMPAIGN_ADJUDICATED", [_CAMPAIGN_ID], {
        **common, "checkpoint_id": checkpoint_id, "sealed_trial_inventory_sha256": inventory,
        **_event_reference("closure", closure), **_event_reference("review", review), **_event_reference("decision", decision), "decision_outcome": outcome,
    })
    prior = previous["checkpoint"] if previous else None
    item = {
        "schema_version": "campaign_adjudication_checkpoint_v1", "canonicalization_id": "pit_canonical_json_v1",
        "checkpoint_id": checkpoint_id, "ledger_id": _LEDGER_ID, "campaign_id": _CAMPAIGN_ID,
        "checkpoint_generation": generation, "previous_checkpoint_id": prior["checkpoint_id"] if prior else None,
        "previous_checkpoint_sha256": previous["checkpoint_sha256"] if previous else None,
        **common, "adjudication_event_sequence": adjudication["sequence"], "adjudication_event_id": adjudication["event_id"],
        "adjudication_event_sha256": adjudication["event_sha256"], "created_at": f"2026-07-27T00:00:0{generation}Z",
        "issuer_authority_reference": "owner-approved-authority-reference",
    }
    return events, evidence, _pack_checkpoint(item)


def _campaign_case(outcome: str = "PROMOTED", renewed: bool = False) -> dict:
    events, evidence, record = _build_generation(1, outcome)
    evidences, records = [evidence], [record]
    if renewed:
        _append_tail_event(events, "EVENT_SUPERSEDED", [_CAMPAIGN_ID], {"correction": True})
        events, evidence, record = _build_generation(2, outcome, events, record)
        evidences.append(evidence)
        records.append(record)
    return {"events": events, "evidences": evidences, "records": records, "currentness": _currentness(records[-1])}


def _verify_case(case: dict) -> str:
    return _require_campaign_adjudication_checkpoint_facts(
        retained_events=case["events"], retained_checkpoints=case["records"],
        retained_evidence_checkpoints=case["evidences"], currentness=case["currentness"],
    )


def _refresh_records(case: dict) -> None:
    refreshed = []
    for generation, record in enumerate(case["records"], start=1):
        item = deepcopy(record["checkpoint"])
        anchor = next(event for event in case["events"] if event["event_id"] == item["adjudication_event_id"])
        item.update(
            checkpoint_generation=generation, adjudication_event_sequence=anchor["sequence"],
            adjudication_event_sha256=anchor["event_sha256"],
            previous_checkpoint_id=refreshed[-1]["checkpoint"]["checkpoint_id"] if refreshed else None,
            previous_checkpoint_sha256=refreshed[-1]["checkpoint_sha256"] if refreshed else None,
        )
        refreshed.append(_pack_checkpoint(item))
    case["records"], case["currentness"] = refreshed, _currentness(refreshed[-1])


def _coherent_fact_mutation(case: dict, event_type: str, field: str, value: object) -> dict:
    case = deepcopy(case)
    next(
        item for item in reversed(case["events"])
        if item["event_type"] == event_type and _CAMPAIGN_ID in item["campaign_scope_ids"]
    )["facts"][field] = value
    case["events"] = _rechain_tail(case["events"], refresh_terminal_refs=True)
    _refresh_records(case)
    return case


def _propagated_evidence_case(*, campaign_evidence_sha256: str | None = None, forced_checkpoint_sha256: str | None = None) -> dict:
    case = _campaign_case()
    item = deepcopy(case["evidences"][0]["checkpoint"])
    if campaign_evidence_sha256 is not None:
        item["campaign_evidence_sha256"] = campaign_evidence_sha256
    evidence = _pack_evidence_checkpoint(item)
    if forced_checkpoint_sha256 is not None:
        evidence["checkpoint_sha256"] = forced_checkpoint_sha256
    case["evidences"][0] = evidence
    digest = evidence["checkpoint_sha256"]
    for event in case["events"]:
        if _CAMPAIGN_ID in event["campaign_scope_ids"]:
            facts = event["facts"]
            if event["event_type"] == "CHECKPOINT_REFERENCE_RECORDED":
                facts["checkpoint_sha256"] = digest
            if "campaign_evidence_checkpoint_sha256" in facts:
                facts["campaign_evidence_checkpoint_sha256"] = digest
            if campaign_evidence_sha256 is not None and "campaign_evidence_sha256" in facts:
                facts["campaign_evidence_sha256"] = campaign_evidence_sha256
    checkpoint = case["records"][0]["checkpoint"]
    checkpoint["campaign_evidence_checkpoint_sha256"] = digest
    if campaign_evidence_sha256 is not None:
        checkpoint["campaign_evidence_sha256"] = campaign_evidence_sha256
    case["events"] = _rechain_tail(case["events"], refresh_terminal_refs=True)
    _refresh_records(case)
    return case


def test_campaign_adjudication_checkpoint_golden_bytes_and_vocabulary() -> None:
    assert len(_LEDGER_EVENT_TYPES) == 37
    checkpoint = {
        "issuer_authority_reference": "authority-ref", "created_at": "2026-07-27T00:00:01Z",
        "adjudication_event_sha256": "d" * 64, "adjudication_event_id": "evt_00000000000000000000000000000004",
        "adjudication_event_sequence": 7, "campaign_evidence_checkpoint_sha256": "c" * 64,
        "campaign_evidence_checkpoint_id": "evidence-checkpoint-1", "campaign_evidence_sha256": "b" * 64,
        "campaign_evidence_version_id": "evidence-version-1", "previous_checkpoint_sha256": None,
        "previous_checkpoint_id": None, "checkpoint_generation": 1, "campaign_id": _CAMPAIGN_ID,
        "ledger_id": _LEDGER_ID, "checkpoint_id": "adjudication-checkpoint-1",
        "canonicalization_id": "pit_canonical_json_v1", "schema_version": "campaign_adjudication_checkpoint_v1",
    }
    expected_bytes = (
        b'{"adjudication_event_id":"evt_00000000000000000000000000000004","adjudication_event_sequence":7,'
        b'"adjudication_event_sha256":"dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",'
        b'"campaign_evidence_checkpoint_id":"evidence-checkpoint-1","campaign_evidence_checkpoint_sha256":'
        b'"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc","campaign_evidence_sha256":'
        b'"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","campaign_evidence_version_id":'
        b'"evidence-version-1","campaign_id":"cmp_00000000000000000000000000000002","canonicalization_id":'
        b'"pit_canonical_json_v1","checkpoint_generation":1,"checkpoint_id":"adjudication-checkpoint-1",'
        b'"created_at":"2026-07-27T00:00:01Z","issuer_authority_reference":"authority-ref","ledger_id":'
        b'"ldg_00000000000000000000000000000001","previous_checkpoint_id":null,'
        b'"previous_checkpoint_sha256":null,"schema_version":"campaign_adjudication_checkpoint_v1"}'
    )
    expected_sha256 = "b5931c6c4379f2ce4dd46c69d9ecc24906a6ed2b420e1d0ae4c479cf7f83d71e"
    assert _ascii_jcs_golden_bytes(checkpoint) == expected_bytes
    assert hashlib.sha256(expected_bytes).hexdigest() == expected_sha256
    assert _pack_checkpoint(checkpoint)["checkpoint_sha256"] == expected_sha256
    assert _ascii_jcs_golden_bytes(dict(reversed(checkpoint.items()))) == expected_bytes
    assert _pack_checkpoint(dict(reversed(checkpoint.items())))["checkpoint_sha256"] == expected_sha256
    evidence_checkpoint = {
        "schema_version": "campaign_evidence_checkpoint_v1", "canonicalization_id": "pit_canonical_json_v1",
        "checkpoint_id": "evidence-checkpoint-1", "ledger_id": _LEDGER_ID, "campaign_id": _CAMPAIGN_ID,
        "evidence_sequence": 4, "evidence_event_sha256": "a" * 64, "freeze_event_sequence": 5,
        "freeze_event_id": "evt_00000000000000000000000000000006", "freeze_event_sha256": "b" * 64,
        "campaign_evidence_version_id": "evidence-version-1", "campaign_evidence_sha256": "c" * 64,
        "sealed_trial_inventory_sha256": "d" * 64, "sealed_semantic_trial_count": 1,
        "terminal_semantic_trial_count": 1, "allocated_attempt_count": 0, "terminal_attempt_count": 0,
        "created_at": "2026-07-27T00:00:01Z", "issuer_authority_reference": "authority-ref",
    }
    evidence_bytes = (
        b'{"allocated_attempt_count":0,"campaign_evidence_sha256":"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",'
        b'"campaign_evidence_version_id":"evidence-version-1","campaign_id":"cmp_00000000000000000000000000000002",'
        b'"canonicalization_id":"pit_canonical_json_v1","checkpoint_id":"evidence-checkpoint-1","created_at":"2026-07-27T00:00:01Z",'
        b'"evidence_event_sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","evidence_sequence":4,'
        b'"freeze_event_id":"evt_00000000000000000000000000000006","freeze_event_sequence":5,'
        b'"freeze_event_sha256":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",'
        b'"issuer_authority_reference":"authority-ref","ledger_id":"ldg_00000000000000000000000000000001",'
        b'"schema_version":"campaign_evidence_checkpoint_v1","sealed_semantic_trial_count":1,'
        b'"sealed_trial_inventory_sha256":"dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",'
        b'"terminal_attempt_count":0,"terminal_semantic_trial_count":1}'
    )
    evidence_sha256 = "047f025978c986d0515a16e3bc9c3a659796eed0bcf3990cd88007ea7bdc0df7"
    assert _ascii_jcs_golden_bytes(evidence_checkpoint) == evidence_bytes
    assert hashlib.sha256(evidence_bytes).hexdigest() == evidence_sha256
    assert _pack_evidence_checkpoint(evidence_checkpoint)["checkpoint_sha256"] == evidence_sha256
    assert _pack_evidence_checkpoint(dict(reversed(evidence_checkpoint.items())))["checkpoint_sha256"] == evidence_sha256
    unknown = {
        "ledger_id": _LEDGER_ID, "sequence": 0, "event_id": "evt_00000000000000000000000000000001",
        "event_type": "LEDGER_MAINTENANCE_RECORDED", "campaign_scope_ids": [],
        "previous_event_sha256": None, "facts": {}, "event_sha256": "0" * 64,
    }
    _assert_value_error(lambda: _campaign_tail_test_event_projection(unknown))


def test_campaign_adjudication_outcomes_and_suffix_scope() -> None:
    for outcome in ("PROMOTED", "REJECTED", "INCONCLUSIVE", "INVALIDATED"):
        case = _campaign_case(outcome)
        assert _verify_case(case) == case["records"][-1]["checkpoint_sha256"]
    prefix_case = _campaign_case()
    verified = _verified_campaign_chain(prefix_case["events"])
    evidence = _evidence_record(prefix_case["evidences"][0])
    prefix = _campaign_evidence_prefix(verified, evidence)
    assert tuple(evidence[field] for field in (
        "sealed_semantic_trial_count", "terminal_semantic_trial_count", "allocated_attempt_count", "terminal_attempt_count"
    )) == (1, 1, 0, 0)
    prefix_ids = {event["event_id"] for event in prefix["campaign_events"]}
    excluded_ids = {
        event["event_id"] for event in verified[: evidence["evidence_sequence"] + 1]
        if _CAMPAIGN_ID not in event["campaign_scope_ids"]
    }
    assert prefix_ids.isdisjoint(excluded_ids)
    other = [
        {key: verified[index][key] for key in ("sequence", "event_id", "event_sha256")}
        for index in (3, 4)
    ]
    for campaign_events in (
        prefix["campaign_events"][:-1],
        prefix["campaign_events"] + [deepcopy(prefix["campaign_events"][-1])],
        list(reversed(prefix["campaign_events"])),
        [prefix["campaign_events"][0], other[0]],
        prefix["campaign_events"] + [other[1]],
    ):
        candidate = {**prefix, "campaign_events": campaign_events}
        _assert_value_error(lambda candidate=candidate: _campaign_evidence_prefix(verified, evidence, candidate))
    unrelated = _campaign_case()
    _append_tail_event(unrelated["events"], "CAMPAIGN_ACCOUNTING_CLOSED", [_OTHER_CAMPAIGN_ID], {"other_campaign": True}, 900)
    _append_tail_event(unrelated["events"], "TRIAL_FAMILY_REGISTERED", [], {"unbound_global_family": True}, 901)
    assert _verify_case(unrelated)
    for event_type in ("EVENT_SUPERSEDED", "CHECKPOINT_REFERENCE_RECORDED"):
        stale = _campaign_case()
        _append_tail_event(stale["events"], event_type, [_CAMPAIGN_ID], {"post_adjudication": True})
        _assert_value_error(lambda stale=stale: _verify_case(stale))


def test_campaign_evidence_checkpoint_semantics_fail_closed() -> None:
    case = _campaign_case()
    events = _verified_campaign_chain(case["events"])
    evidence = _evidence_record(case["evidences"][0])
    closure_sequence = next(event["sequence"] for event in events if event["event_type"] == "CAMPAIGN_ACCOUNTING_CLOSED" and event["campaign_scope_ids"] == [_CAMPAIGN_ID])
    freeze_sequence = evidence["freeze_event_sequence"]
    reference_sequence = next(event["sequence"] for event in events if event["event_type"] == "CHECKPOINT_REFERENCE_RECORDED" and _CAMPAIGN_ID in event["campaign_scope_ids"])

    def repacked(**changes: object) -> dict:
        item = deepcopy(case["evidences"][0]["checkpoint"])
        item.update(changes)
        return _evidence_record(_pack_evidence_checkpoint(item))

    def changed(sequence: int, field: str, value: object, *, facts: bool = False) -> list[dict]:
        mutated = deepcopy(events)
        target = mutated[sequence]["facts"] if facts else mutated[sequence]
        target[field] = value
        return mutated

    def rejects(mutated_events: list[dict] = events, mutated_evidence: dict = evidence, boundary: int = closure_sequence, expected: str | None = None) -> None:
        error = _assert_value_error(lambda: _evidence_checkpoint_semantics(mutated_events, mutated_evidence, boundary))
        if expected is not None:
            assert error == expected

    _evidence_checkpoint_semantics(events, evidence, closure_sequence)
    interval = events[freeze_sequence + 1 : closure_sequence]
    assert [event["event_type"] for event in interval if _CAMPAIGN_ID in event["campaign_scope_ids"]] == ["CHECKPOINT_REFERENCE_RECORDED"]
    assert any(_OTHER_CAMPAIGN_ID in event["campaign_scope_ids"] for event in interval)
    assert any(not event["campaign_scope_ids"] for event in interval)
    for mutated_events, mutated_evidence in (
        (events, repacked(evidence_sequence=3, freeze_event_sequence=4)),
        (events, repacked(evidence_event_sha256="f" * 64)),
        (events, repacked(evidence_sequence=len(events), freeze_event_sequence=len(events) + 1)),
        (events[: evidence["evidence_sequence"]], evidence),
    ):
        rejects(mutated_events, mutated_evidence)
    for field, value in (
        ("freeze_event_id", "evt_ffffffffffffffffffffffffffffffff"),
        ("freeze_event_sha256", "f" * 64),
    ):
        rejects(mutated_evidence=repacked(**{field: value}))
    for field, value in (
        ("event_type", "EVENT_SUPERSEDED"),
        ("campaign_scope_ids", [_CAMPAIGN_ID, _OTHER_CAMPAIGN_ID]),
        ("previous_event_sha256", "f" * 64),
    ):
        rejects(changed(freeze_sequence, field, value))
    rejects(changed(freeze_sequence, "unexpected", True, facts=True))
    count_error = "synthetic trial/attempt set or count mismatch"
    rejects(mutated_evidence=repacked(terminal_semantic_trial_count=0), expected=count_error)
    same_count_different_set = deepcopy(events)
    alternate_trial = "trl_ffffffffffffffffffffffffffffffff"
    same_count_different_set[freeze_sequence]["facts"].update(sealed_trial_ids=[alternate_trial], terminal_trial_ids=[alternate_trial])
    rejects(same_count_different_set, expected=count_error)
    rejects(changed(2, "event_type", "ATTEMPT_ALLOCATED"), expected="event is outside the fixed all-excluded synthetic vector")

    reference_mutations = [
        (changed(reference_sequence, "event_type", "EVENT_SUPERSEDED"), closure_sequence),
        (changed(reference_sequence, "campaign_scope_ids", [_OTHER_CAMPAIGN_ID]), closure_sequence),
        (changed(reference_sequence, "checkpoint_id", "wrong-evidence-checkpoint", facts=True), closure_sequence),
        (changed(reference_sequence, "checkpoint_sha256", "f" * 64, facts=True), closure_sequence),
    ]
    duplicate = deepcopy(events)
    duplicate.insert(closure_sequence, deepcopy(duplicate[reference_sequence]))
    reference_mutations.extend(((duplicate, closure_sequence + 1), (events, reference_sequence)))
    for mutated, boundary in reference_mutations:
        rejects(mutated, boundary=boundary)
    for nonce, (offset, event_type) in enumerate((
        (0, "EVENT_SUPERSEDED"), (1, "EVENT_SUPERSEDED"),
        (0, "CAMPAIGN_INVENTORY_AMENDED"), (0, "ACCESS_COMPLETED"), (0, "TRIAL_EXCLUDED"),
    ), start=1000):
        invalid = deepcopy(case)
        intruder = deepcopy(invalid["events"][reference_sequence])
        intruder.update(event_id=f"evt_{nonce:032x}", event_type=event_type, facts={"interval_intrusion": True})
        invalid["events"].insert(reference_sequence + offset, intruder)
        invalid["events"] = _rechain_tail(invalid["events"], refresh_terminal_refs=True)
        _refresh_records(invalid)
        assert _assert_value_error(lambda invalid=invalid: _verify_case(invalid)) == "target campaign interval must contain only its checkpoint reference"

    for invalid, expected in (
        (_propagated_evidence_case(forced_checkpoint_sha256="f" * 64), "evidence checkpoint digest mismatch"),
        (_propagated_evidence_case(campaign_evidence_sha256="f" * 64), "campaign evidence prefix digest mismatch"),
        (_coherent_fact_mutation(case, "CAMPAIGN_EVIDENCE_FROZEN", "sealed_trial_inventory_sha256", "f" * 64), "evidence freeze identity/scope/predecessor mismatch"),
    ):
        assert _assert_value_error(lambda invalid=invalid: _verify_case(invalid)) == expected


def test_campaign_adjudication_tail_mutations_fail_closed() -> None:
    base = _campaign_case()
    positions = {
        event["event_type"]: event["sequence"] for event in base["events"]
        if event["event_type"] in {"CAMPAIGN_ACCOUNTING_CLOSED", "REVIEW_DECIDED", "PROMOTION_DECIDED", "CAMPAIGN_ADJUDICATED"}
    }
    review, decision = positions["REVIEW_DECIDED"], positions["PROMOTION_DECIDED"]
    mutations = {
        "delete": [event for event in deepcopy(base["events"]) if event["sequence"] != positions["CAMPAIGN_ACCOUNTING_CLOSED"]],
        "modify": deepcopy(base["events"]), "insert": deepcopy(base["events"]),
        "duplicate": deepcopy(base["events"]), "reorder": deepcopy(base["events"]),
        "replace": deepcopy(base["events"]),
        "truncate": deepcopy(base["events"])[: positions["CAMPAIGN_ADJUDICATED"]],
    }
    mutations["modify"][review]["facts"]["review_outcome"] = "REJECTED"
    mutations["insert"].insert(review, {
        "ledger_id": _LEDGER_ID, "sequence": 0, "event_id": "evt_00000000000000000000000000000384",
        "event_type": "EVENT_SUPERSEDED", "campaign_scope_ids": [_CAMPAIGN_ID],
        "previous_event_sha256": None, "facts": {"inserted": True}, "event_sha256": "0" * 64,
    })
    mutations["duplicate"].insert(review, deepcopy(mutations["duplicate"][review]))
    mutations["reorder"][review], mutations["reorder"][decision] = mutations["reorder"][decision], mutations["reorder"][review]
    mutations["replace"][decision]["event_type"] = "EVENT_SUPERSEDED"
    for events in mutations.values():
        invalid = deepcopy(base)
        invalid["events"] = _rechain_tail(events)
        _assert_value_error(lambda invalid=invalid: _verify_case(invalid))
    coherent = {
        "closure": ("CAMPAIGN_ACCOUNTING_CLOSED", "campaign_evidence_sha256", "f" * 64, "closure evidence binding mismatch"),
        "review": ("REVIEW_DECIDED", "review_outcome", "REJECTED", "review or decision predecessor mismatch"),
        "decision": ("PROMOTION_DECIDED", "decision_outcome", "REJECTED", "terminal outcome mismatch"),
        "adjudication": ("CAMPAIGN_ADJUDICATED", "checkpoint_id", "wrong-preallocation", "checkpoint preallocation mismatch"),
    }
    for event_type, field, value, expected_error in coherent.values():
        invalid = _coherent_fact_mutation(base, event_type, field, value)
        assert _assert_value_error(
            lambda invalid=invalid: _verify_case(invalid)
        ) == expected_error


def test_campaign_adjudication_lineage_and_currentness_fail_closed() -> None:
    renewed = _campaign_case(renewed=True)
    assert _verify_case(renewed)
    rehashed = deepcopy(renewed)
    first = deepcopy(rehashed["records"][0]["checkpoint"])
    first["campaign_evidence_sha256"] = "f" * 64
    rehashed["records"][0] = _pack_checkpoint(first)
    second = deepcopy(rehashed["records"][1]["checkpoint"])
    second["previous_checkpoint_sha256"] = rehashed["records"][0]["checkpoint_sha256"]
    rehashed["records"][1] = _pack_checkpoint(second)
    rehashed["currentness"] = _currentness(rehashed["records"][1])
    assert _assert_value_error(
        lambda: _verify_case(rehashed)
    ) == "checkpoint evidence binding mismatch"
    lineage_mutations = {}
    for name, generation, prior_id, prior_sha in (
        ("reset", 1, None, None),
        ("skip", 3, renewed["records"][0]["checkpoint"]["checkpoint_id"], renewed["records"][0]["checkpoint_sha256"]),
        ("fork", 2, "wrong-predecessor", "f" * 64),
    ):
        invalid = deepcopy(renewed)
        item = invalid["records"][1]["checkpoint"]
        item.update(checkpoint_generation=generation, previous_checkpoint_id=prior_id, previous_checkpoint_sha256=prior_sha)
        invalid["records"][1] = _pack_checkpoint(item)
        invalid["currentness"] = _currentness(invalid["records"][1])
        lineage_mutations[name] = invalid
    missing = deepcopy(renewed)
    missing["records"], missing["evidences"] = missing["records"][:1], missing["evidences"][:1]
    missing["currentness"] = _currentness(missing["records"][0])
    lineage_mutations["missing"] = missing
    sibling = deepcopy(renewed)
    sibling_item = deepcopy(sibling["records"][1]["checkpoint"])
    sibling_item["checkpoint_id"] = "campaign-adjudication-sibling-2"
    sibling["records"].append(_pack_checkpoint(sibling_item))
    sibling["evidences"].append(deepcopy(sibling["evidences"][1]))
    sibling["currentness"] = _currentness(sibling["records"][-1])
    lineage_mutations["sibling"] = sibling
    for invalid in lineage_mutations.values():
        _assert_value_error(lambda invalid=invalid: _verify_case(invalid))
    for pending in (2, 3, 1):
        invalid = _campaign_case()
        invalid["currentness"] = _currentness(invalid["records"][0], pending)
        _assert_value_error(lambda invalid=invalid: _verify_case(invalid))
    old = deepcopy(renewed)
    old["currentness"] = _currentness(old["records"][0])
    _assert_value_error(lambda: _verify_case(old))
    unverified = _campaign_case()
    unverified["currentness"]["external_currentness_proof_verified"] = False
    _assert_value_error(lambda: _verify_case(unverified))


def test_campaign_adjudication_exact_correspondence_and_schema() -> None:
    base = _campaign_case()
    original = next(event for event in base["events"] if event["event_type"] == "CAMPAIGN_ADJUDICATED")
    for nonce, checkpoint_id in ((901, "unaccounted-checkpoint"), (902, original["facts"]["checkpoint_id"])):
        invalid, extra = deepcopy(base), deepcopy(original)
        extra["event_id"], extra["facts"]["checkpoint_id"] = f"evt_{nonce:032x}", checkpoint_id
        invalid["events"].insert(original["sequence"], extra)
        invalid["events"] = _rechain_tail(invalid["events"])
        _refresh_records(invalid)
        assert _assert_value_error(
            lambda invalid=invalid: _verify_case(invalid)
        ) == "generation/adjudication correspondence mismatch"
    checkpoint_mutations = {
        "missing": ("delete", "created_at", None), "unknown": ("set", "unknown_field", "rejected"),
        "type": ("set", "checkpoint_generation", True), "ledger": ("set", "ledger_id", "ldg_" + "f" * 32),
        "evidence": ("set", "campaign_evidence_sha256", "f" * 64),
        "anchor sequence": ("set", "adjudication_event_sequence", 0),
        "anchor ID": ("set", "adjudication_event_id", "evt_ffffffffffffffffffffffffffffffff"),
        "anchor digest": ("set", "adjudication_event_sha256", "f" * 64),
    }
    for operation, field, value in checkpoint_mutations.values():
        invalid = deepcopy(base)
        item = invalid["records"][0]["checkpoint"]
        if operation == "delete" or field in {"unknown_field", "checkpoint_generation"}:
            if operation == "delete":
                del item[field]
            else:
                item[field] = value
            invalid["records"][0]["checkpoint_sha256"] = "f" * 64
        else:
            item[field] = value
            invalid["records"][0] = _pack_checkpoint(item)
            invalid["currentness"] = _currentness(invalid["records"][0])
        _assert_value_error(lambda invalid=invalid: _verify_case(invalid))
    bad_digest = deepcopy(base)
    bad_digest["records"][0]["checkpoint_sha256"] = "f" * 64
    _assert_value_error(lambda: _verify_case(bad_digest))
    evidence_mutations = {
        "missing": ("delete", "checkpoint_id", None), "unknown": ("set", "unknown_field", "rejected"),
        "schema": ("set", "schema_version", "campaign_evidence_checkpoint_v2"),
        "type": ("set", "checkpoint_id", 1),
        "Boolean": ("set", "evidence_sequence", True),
        "negative": ("set", "freeze_event_sequence", -1),
        "unsafe": ("set", "terminal_attempt_count", 2**53),
        "uppercase hash": ("set", "evidence_event_sha256", "A" * 64),
        "ID": ("set", "checkpoint_id", "wrong-evidence-checkpoint"),
        "freeze": ("set", "freeze_event_sha256", "f" * 64),
    }
    for operation, field, value in evidence_mutations.values():
        invalid = deepcopy(base)
        evidence = invalid["evidences"][0]["checkpoint"]
        if operation == "delete":
            del evidence[field]
        else:
            evidence[field] = value
        _assert_value_error(lambda invalid=invalid: _verify_case(invalid))
    for operation in ("missing digest", "unknown outer field"):
        invalid = deepcopy(base)
        if operation == "missing digest":
            del invalid["evidences"][0]["checkpoint_sha256"]
        else:
            invalid["evidences"][0]["unknown"] = True
        _assert_value_error(lambda invalid=invalid: _verify_case(invalid))
    missing_fact = deepcopy(base)
    adjudication = next(event for event in missing_fact["events"] if event["event_type"] == "CAMPAIGN_ADJUDICATED")
    del adjudication["facts"]["decision_event_sha256"]
    missing_fact["events"] = _rechain_tail(missing_fact["events"])
    _refresh_records(missing_fact)
    _assert_value_error(lambda: _verify_case(missing_fact))


def test_inventory_preseal_head_anchor_precedes_attempt_and_detects_mutation() -> None:
    facts = {
        "anchor_schema_version": "campaign_inventory_preseal_head_v1",
        "ledger_id": "ldg_00000000000000000000000000000001",
        "predecessor_sequence": 5,
        "predecessor_event_sha256": "a" * 64,
        "inventory_seal_previous_event_sha256": "a" * 64,
        "inventory_seal_sequence": 6,
        "first_attempt_or_access_sequence": 7,
        "anchor_fields_in_seal_preimage": True,
        "predecessor_event_bytes_excluded_from_seal_preimage": True,
        "atomic_head_compare_and_assign": True,
    }
    _require_inventory_preseal_head_facts(
        facts,
        retained_ledger_id="ldg_00000000000000000000000000000001",
        retained_predecessor_sequence=5,
        retained_predecessor_event_sha256="a" * 64,
    )

    mutated_predecessor = dict(facts)
    mutated_predecessor["predecessor_event_sha256"] = "b" * 64
    assert mutated_predecessor["predecessor_event_sha256"] != facts[
        "predecessor_event_sha256"
    ]
    _assert_value_error(
        lambda: _require_inventory_preseal_head_facts(
            mutated_predecessor,
            retained_ledger_id="ldg_00000000000000000000000000000001",
            retained_predecessor_sequence=5,
            retained_predecessor_event_sha256="a" * 64,
        )
    )
    _assert_value_error(
        lambda: _require_inventory_preseal_head_facts(
            facts,
            retained_ledger_id="ldg_00000000000000000000000000000001",
            retained_predecessor_sequence=4,
            retained_predecessor_event_sha256="a" * 64,
        )
    )
    _assert_value_error(
        lambda: _require_inventory_preseal_head_facts(
            {**facts, "inventory_seal_sequence": 7},
            retained_ledger_id="ldg_00000000000000000000000000000001",
            retained_predecessor_sequence=5,
            retained_predecessor_event_sha256="a" * 64,
        )
    )
    _assert_value_error(
        lambda: _require_inventory_preseal_head_facts(
            {**facts, "first_attempt_or_access_sequence": 6},
            retained_ledger_id="ldg_00000000000000000000000000000001",
            retained_predecessor_sequence=5,
            retained_predecessor_event_sha256="a" * 64,
        )
    )
    _assert_value_error(
        lambda: _require_inventory_preseal_head_facts(
            {**facts, "atomic_head_compare_and_assign": False},
            retained_ledger_id="ldg_00000000000000000000000000000001",
            retained_predecessor_sequence=5,
            retained_predecessor_event_sha256="a" * 64,
        )
    )
    _assert_value_error(
        lambda: _require_inventory_preseal_head_facts(
            facts,
            retained_ledger_id="ldg_00000000000000000000000000000001",
            retained_predecessor_sequence=6,
            retained_predecessor_event_sha256="c" * 64,
        )
    )
    _assert_value_error(
        lambda: _require_inventory_preseal_head_facts(
            {**facts, "inventory_seal_previous_event_sha256": "b" * 64},
            retained_ledger_id="ldg_00000000000000000000000000000001",
            retained_predecessor_sequence=5,
            retained_predecessor_event_sha256="a" * 64,
        )
    )
    _assert_value_error(
        lambda: _require_inventory_preseal_head_facts(
            facts,
            retained_ledger_id="ldg_00000000000000000000000000000002",
            retained_predecessor_sequence=5,
            retained_predecessor_event_sha256="a" * 64,
        )
    )
    _assert_value_error(
        lambda: _require_inventory_preseal_head_facts(
            {
                **facts,
                "predecessor_sequence": None,
                "predecessor_event_sha256": None,
            },
            retained_ledger_id="ldg_00000000000000000000000000000001",
            retained_predecessor_sequence=0,
            retained_predecessor_event_sha256="a" * 64,
        )
    )


def test_pit_canonical_json_v1_golden_bytes_and_digest() -> None:
    fixture = json.loads(
        (
            PROJECT_ROOT
            / "tests/fixtures/pit_canonical_json_v1_golden.json"
        ).read_text(encoding="utf-8")
    )
    canonical_text = _ascii_jcs_golden_bytes(fixture["semantic_input"]).decode()

    assert fixture["schema_version"] == "pit_canonical_json_v1_golden_v2"
    assert canonical_text == fixture["canonical_utf8"]
    assert " " not in canonical_text
    assert (
        hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()
        == fixture["sha256"]
    )


def test_ordered_manifest_sha256_golden_reorder_and_mutation_vectors() -> None:
    fixture = json.loads(
        (
            PROJECT_ROOT
            / "tests/fixtures/pit_canonical_json_v1_golden.json"
        ).read_text(encoding="utf-8")
    )["ordered_manifest_sha256_vectors"]

    base_bytes = _ascii_jcs_golden_bytes(
        _ordered_component_inventory_projection(fixture["semantic_input"])
    )
    reordered_bytes = _ascii_jcs_golden_bytes(
        _ordered_component_inventory_projection(
            fixture["reordered_semantic_input"]
        )
    )
    mutated_bytes = _ascii_jcs_golden_bytes(
        _ordered_component_inventory_projection(
            fixture["mutated_semantic_input"]
        )
    )

    assert base_bytes.decode() == fixture["canonical_utf8"]
    assert reordered_bytes == base_bytes
    assert hashlib.sha256(base_bytes).hexdigest() == fixture["sha256"]
    assert hashlib.sha256(reordered_bytes).hexdigest() == fixture["sha256"]
    assert mutated_bytes.decode() == fixture["mutated_canonical_utf8"]
    assert hashlib.sha256(mutated_bytes).hexdigest() == fixture["mutated_sha256"]
    assert fixture["mutated_sha256"] != fixture["sha256"]

    duplicate_component = json.loads(json.dumps(fixture["semantic_input"]))
    duplicate_component["components"].append(
        dict(duplicate_component["components"][0])
    )
    _assert_value_error(
        lambda: _ordered_component_inventory_projection(duplicate_component)
    )
    unknown_component_key = json.loads(json.dumps(fixture["semantic_input"]))
    unknown_component_key["components"][0]["path"] = "private.csv"
    _assert_value_error(
        lambda: _ordered_component_inventory_projection(unknown_component_key)
    )


def test_public_projection_sha256_golden_reorder_and_mutation_vectors() -> None:
    fixture = json.loads(
        (
            PROJECT_ROOT
            / "tests/fixtures/pit_canonical_json_v1_golden.json"
        ).read_text(encoding="utf-8")
    )["public_projection_sha256_vectors"]

    base_bytes = _ascii_jcs_golden_bytes(
        _public_redacted_projection(fixture["semantic_input"])
    )
    reordered_bytes = _ascii_jcs_golden_bytes(
        _public_redacted_projection(fixture["reordered_semantic_input"])
    )
    mutated_bytes = _ascii_jcs_golden_bytes(
        _public_redacted_projection(fixture["mutated_semantic_input"])
    )

    assert base_bytes.decode() == fixture["canonical_utf8"]
    assert reordered_bytes == base_bytes
    assert hashlib.sha256(base_bytes).hexdigest() == fixture["sha256"]
    assert hashlib.sha256(reordered_bytes).hexdigest() == fixture["sha256"]
    assert mutated_bytes.decode() == fixture["mutated_canonical_utf8"]
    assert hashlib.sha256(mutated_bytes).hexdigest() == fixture["mutated_sha256"]
    assert fixture["mutated_sha256"] != fixture["sha256"]

    duplicate_policy = json.loads(json.dumps(fixture["semantic_input"]))
    duplicate_policy["policy_states"].append(
        dict(duplicate_policy["policy_states"][0])
    )
    _assert_value_error(lambda: _public_redacted_projection(duplicate_policy))
    unknown_public_key = dict(fixture["semantic_input"])
    unknown_public_key["private_path"] = "/private/data.csv"
    _assert_value_error(lambda: _public_redacted_projection(unknown_public_key))
    private_manifest_locator = json.loads(json.dumps(fixture["semantic_input"]))
    private_manifest_locator["manifest_id"] = "/private/data.csv"
    _assert_value_error(
        lambda: _public_redacted_projection(private_manifest_locator)
    )
    private_evidence_uri = json.loads(json.dumps(fixture["semantic_input"]))
    private_evidence_uri["redacted_evidence_refs"][0]["evidence_ref_id"] = (
        "file://private/data.csv"
    )
    _assert_value_error(lambda: _public_redacted_projection(private_evidence_uri))
    private_approval_identity = json.loads(json.dumps(fixture["semantic_input"]))
    private_approval_identity["published_hashes"][0][
        "publication_approval_ref_id"
    ] = "owner@example.com"
    _assert_value_error(
        lambda: _public_redacted_projection(private_approval_identity)
    )


def test_ledger_epoch_golden_semantic_facts_and_fail_closed_vectors() -> None:
    fixture = json.loads(
        (
            PROJECT_ROOT
            / "tests/fixtures/experiment_trial_ledger_event_v1_golden.json"
        ).read_text(encoding="utf-8")
    )
    base_bytes = _ascii_jcs_golden_bytes(
        _ledger_event_identity_projection(fixture["semantic_input"])
    )
    reordered_bytes = _ascii_jcs_golden_bytes(
        _ledger_event_identity_projection(fixture["reordered_semantic_input"])
    )
    mutated_bytes = _ascii_jcs_golden_bytes(
        _ledger_event_identity_projection(fixture["mutated_semantic_input"])
    )
    base_request_bytes = _ascii_jcs_golden_bytes(
        _ledger_operation_request_projection(fixture["semantic_input"])
    )
    reordered_request_bytes = _ascii_jcs_golden_bytes(
        _ledger_operation_request_projection(fixture["reordered_semantic_input"])
    )
    mutated_request_bytes = _ascii_jcs_golden_bytes(
        _ledger_operation_request_projection(fixture["mutated_semantic_input"])
    )

    assert (
        fixture["schema_version"]
        == "experiment_trial_ledger_event_v1_golden_v2"
    )
    assert fixture["semantic_input"]["event_type"] == "LEDGER_EPOCH_CREATED"
    assert fixture["semantic_input"]["sequence"] == 0
    assert fixture["semantic_input"]["previous_event_sha256"] is None
    fractional_timestamp_event = json.loads(json.dumps(fixture["semantic_input"]))
    fractional_timestamp_event["occurred_at"] = "2024-02-29T23:59:59.123456789Z"
    fractional_timestamp_event["recorded_at"] = "2024-03-01T00:00:00.000001Z"
    assert _ledger_event_identity_projection(fractional_timestamp_event)[
        "occurred_at"
    ].endswith(".123456789Z")
    arbitrary_precision_timestamp_event = json.loads(
        json.dumps(fixture["semantic_input"])
    )
    arbitrary_precision_timestamp_event["occurred_at"] = (
        "2024-02-29T23:59:59.1234567890123456789Z"
    )
    arbitrary_precision_timestamp_event["recorded_at"] = (
        "2024-03-01T00:00:00.0000000000000000001Z"
    )
    arbitrary_precision_projection = _ledger_event_identity_projection(
        arbitrary_precision_timestamp_event
    )
    assert arbitrary_precision_projection["occurred_at"] == (
        "2024-02-29T23:59:59.1234567890123456789Z"
    )
    assert arbitrary_precision_projection["recorded_at"] == (
        "2024-03-01T00:00:00.0000000000000000001Z"
    )
    year_zero_event = json.loads(json.dumps(fixture["semantic_input"]))
    year_zero_event["occurred_at"] = "0000-02-29T00:00:00Z"
    assert (
        _ledger_event_identity_projection(year_zero_event)["occurred_at"]
        == "0000-02-29T00:00:00Z"
    )
    for invalid_timestamp in [
        "2026-02-29T00:00:00Z",
        "0001-02-29T00:00:00Z",
        "0001-00-01T00:00:00Z",
        "2026-13-01T00:00:00Z",
        "0001-04-31T00:00:00Z",
        "0001-01-00T00:00:00Z",
        "2026-01-01T24:00:00Z",
        "2026-01-01T23:60:00Z",
        "2026-01-01T23:59:60Z",
        "2026-01-01T23:59:61Z",
        "1990-12-31T23:59:60Z",
        "1990-12-31T23:59:60.1234567890123456789Z",
        "1990-12-31T23:59:60.120Z",
        "2015-06-30T23:59:60Z",
        "2015-06-30T23:59:60.1Z",
        "2016-12-31T23:59:60Z",
        "2016-12-31T23:59:60.1Z",
        "2024-06-30T23:59:60Z",
        "2024-06-30T23:59:60.1Z",
        "2026-12-31T23:59:60Z",
        "2026-12-31T23:59:60.1Z",
        "2024-06-30T22:59:60Z",
        "2024-06-29T23:59:60Z",
        "2026-01-01T00:00:00.000Z",
        "2026-01-01T00:00:00.120Z",
        "2026-01-01T00:00:00.Z",
        "2026-01-01T00:00:00+00:00",
    ]:
        for timestamp_field in ["occurred_at", "recorded_at"]:
            invalid_timestamp_event = json.loads(
                json.dumps(fixture["semantic_input"])
            )
            invalid_timestamp_event[timestamp_field] = invalid_timestamp
            _assert_value_error(
                lambda event=invalid_timestamp_event: (
                    _ledger_event_identity_projection(event)
                )
            )

    assert (
        base_request_bytes.decode()
        == fixture["operation_request_canonical_utf8"]
    )
    assert reordered_request_bytes == base_request_bytes
    assert (
        hashlib.sha256(base_request_bytes).hexdigest()
        == fixture["operation_request_sha256"]
        == fixture["semantic_input"]["operation_request_sha256"]
    )
    assert (
        hashlib.sha256(reordered_request_bytes).hexdigest()
        == fixture["operation_request_sha256"]
        == fixture["reordered_semantic_input"]["operation_request_sha256"]
    )
    assert (
        mutated_request_bytes.decode()
        == fixture["mutated_operation_request_canonical_utf8"]
    )
    assert (
        hashlib.sha256(mutated_request_bytes).hexdigest()
        == fixture["mutated_operation_request_sha256"]
        == fixture["mutated_semantic_input"]["operation_request_sha256"]
    )
    assert (
        fixture["mutated_operation_request_sha256"]
        != fixture["operation_request_sha256"]
    )
    assert (
        fixture["mutated_semantic_input"]["operation_id"]
        == fixture["semantic_input"]["operation_id"]
    )
    assert base_bytes.decode() == fixture["canonical_utf8"]
    assert reordered_bytes == base_bytes
    assert hashlib.sha256(base_bytes).hexdigest() == fixture["sha256"]
    assert hashlib.sha256(reordered_bytes).hexdigest() == fixture["sha256"]
    assert mutated_bytes.decode() == fixture["mutated_canonical_utf8"]
    assert hashlib.sha256(mutated_bytes).hexdigest() == fixture["mutated_sha256"]
    assert fixture["mutated_sha256"] != fixture["sha256"]

    unknown_event_key = dict(fixture["semantic_input"])
    unknown_event_key["event_sha256"] = fixture["sha256"]
    _assert_value_error(
        lambda: _ledger_event_identity_projection(unknown_event_key)
    )
    unauthorized_actor_binding = json.loads(json.dumps(fixture["semantic_input"]))
    unauthorized_actor_binding["payload"]["genesis_principal_binding"] = {}
    _assert_value_error(
        lambda: _ledger_event_identity_projection(unauthorized_actor_binding)
    )
    missing_event_key = dict(fixture["semantic_input"])
    del missing_event_key["operation_request_sha256"]
    _assert_value_error(
        lambda: _ledger_event_identity_projection(missing_event_key)
    )
    invalid_typed_id = json.loads(json.dumps(fixture["semantic_input"]))
    invalid_typed_id["subject_id"] = "ledger-readable-name"
    _assert_value_error(
        lambda: _ledger_event_identity_projection(invalid_typed_id)
    )
    for invalid_actor_id in [
        "usr_00000000000000000000000000000004",
        "act_0000000000000000000000000000004",
        "act_0000000000000000000000000000000A",
        "act_0000000000000000000000000000000é",
    ]:
        invalid_actor = json.loads(json.dumps(fixture["semantic_input"]))
        invalid_actor["actor_id"] = invalid_actor_id
        _assert_value_error(
            lambda event=invalid_actor: _ledger_event_identity_projection(event)
        )
    incomplete_trial_stub = fixture["incomplete_trial_allocation_stub"]
    _assert_value_error(
        lambda: _ledger_event_identity_projection(incomplete_trial_stub)
    )
    sequence_repaired_stub = json.loads(json.dumps(incomplete_trial_stub))
    sequence_repaired_stub["sequence"] = 1
    sequence_repaired_stub["previous_event_sha256"] = fixture["sha256"]
    _assert_value_error(
        lambda: _ledger_event_identity_projection(sequence_repaired_stub)
    )

    # Independent semantic facts; these do not project the rejected stub payload.
    campaign_id = "cmp_00000000000000000000000000000005"
    experiment_id = "exp_00000000000000000000000000000006"
    family_id = "tfm_00000000000000000000000000000007"
    trial_id = "trl_00000000000000000000000000000008"
    sample_id = "smp_0000000000000000000000000000000b"

    def facts(
        campaign_sequence: int,
        experiment_sequence: int,
        trial_sequence: int,
        family_path: dict[str, object],
        sample_path: dict[str, object],
    ) -> dict[str, object]:
        return {
            "epoch_sequence": 0,
            "campaign_sequence": campaign_sequence,
            "experiment_sequence": experiment_sequence,
            "trial_sequence": trial_sequence,
            "campaign_id": campaign_id,
            "experiment_id": experiment_id,
            "family_id": family_id,
            "trial_id": trial_id,
            "sample_ids": [sample_id],
            "family_path": family_path,
            "sample_paths": {sample_id: sample_path},
        }

    def direct(
        sequence: int,
        entity_id: str,
        campaign_scope_ids: list[str] | None = None,
    ) -> dict[str, object]:
        return {
            "kind": "direct",
            "entity_id": entity_id,
            "campaign_scope_ids": campaign_scope_ids or [campaign_id],
            "registration_sequence": sequence,
        }

    def ledger_global(
        registration_sequence: int,
        binding_sequence: int,
        entity_id: str,
    ) -> dict[str, object]:
        registration_event_id = f"evt_{registration_sequence:032x}"
        registration_event_sha256 = f"{registration_sequence:064x}"
        return {
            "kind": "ledger_global",
            "entity_id": entity_id,
            "registration_scope_ids": [],
            "registration_sequence": registration_sequence,
            "registration_event_id": registration_event_id,
            "registration_event_sha256": registration_event_sha256,
            "binding_entity_id": entity_id,
            "binding_campaign_id": campaign_id,
            "binding_sequence": binding_sequence,
            "binding_source_event_id": registration_event_id,
            "binding_source_event_sha256": registration_event_sha256,
        }

    def stage3_external(
        binding_sequence: int,
        entity_id: str,
    ) -> dict[str, object]:
        return {
            "kind": "stage3_external",
            "entity_id": entity_id,
            "binding_entity_id": entity_id,
            "binding_campaign_id": campaign_id,
            "binding_sequence": binding_sequence,
            "external_reference": {
                "registry_authority_id": "registry-authority",
                "external_sample_record_id": "sample-record",
                "schema_contract_version": "schema-version",
                "record_sha256": "b" * 64,
                "review_decision_ref_id": "review-reference",
            },
        }

    direct_facts = facts(1, 4, 5, direct(3, family_id), direct(2, sample_id))
    other_campaign_id = "cmp_00000000000000000000000000000004"
    shared_direct_facts = facts(
        1,
        4,
        5,
        direct(3, family_id, [other_campaign_id, campaign_id]),
        direct(2, sample_id),
    )
    global_facts = facts(
        3,
        4,
        7,
        ledger_global(1, 5, family_id),
        ledger_global(2, 6, sample_id),
    )
    late_global_facts = facts(
        1,
        2,
        7,
        ledger_global(3, 5, family_id),
        ledger_global(4, 6, sample_id),
    )
    external_facts = facts(
        1,
        3,
        5,
        direct(4, family_id),
        stage3_external(2, sample_id),
    )
    for valid_facts in [
        direct_facts,
        shared_direct_facts,
        global_facts,
        late_global_facts,
        external_facts,
    ]:
        _require_trial_parent_semantic_order_facts(valid_facts)

    invalid_cases: list[dict[str, object]] = []

    def invalid_path(
        base: dict[str, object],
        *,
        sample: bool = False,
    ) -> dict[str, object]:
        invalid = json.loads(json.dumps(base))
        invalid_cases.append(invalid)
        return (
            invalid["sample_paths"][sample_id]
            if sample
            else invalid["family_path"]
        )

    invalid_path(direct_facts)["registration_sequence"] = 0
    invalid_path(direct_facts)["binding_source_event_id"] = "extra-global-field"
    invalid_path(direct_facts)["external_reference"] = {"extra": "external-field"}
    invalid_path(global_facts, sample=True)["binding_entity_id"] = family_id
    invalid_path(global_facts)["binding_campaign_id"] = other_campaign_id
    invalid_path(global_facts)["binding_source_event_id"] = f"evt_{99:032x}"
    invalid_path(global_facts)["binding_source_event_sha256"] = "f" * 64
    invalid_path(direct_facts)["campaign_scope_ids"] = [other_campaign_id]
    invalid_path(direct_facts)["campaign_scope_ids"] = [campaign_id, campaign_id]
    invalid_path(direct_facts)["campaign_scope_ids"] = [
        campaign_id,
        other_campaign_id,
    ]
    missing_external = invalid_path(external_facts, sample=True)
    del missing_external["external_reference"]["record_sha256"]
    unknown_external = invalid_path(external_facts, sample=True)
    unknown_external["external_reference"]["unknown_field"] = "rejected"

    for invalid_facts in invalid_cases:
        _assert_value_error(
            lambda invalid_facts=invalid_facts: _require_trial_parent_semantic_order_facts(
                invalid_facts,
            )
        )

    def entity_fact(
        kind: str,
        sequence: int,
        *,
        event_suffix: int,
        operation_suffix: int,
        request_digit: str,
    ) -> dict[str, object]:
        return {
            "kind": kind,
            "entity_type": "trial",
            "entity_id": trial_id,
            "event_id": f"evt_{event_suffix:032x}",
            "operation_id": f"opn_{operation_suffix:032x}",
            "sequence": sequence,
            "operation_request_sha256": request_digit * 64,
        }

    allocation_fact = entity_fact(
        "allocate",
        1,
        event_suffix=21,
        operation_suffix=31,
        request_digit="1",
    )
    lifecycle_reference_fact = entity_fact(
        "reference",
        2,
        event_suffix=22,
        operation_suffix=32,
        request_digit="2",
    )
    assert (
        _count_entity_identity_fact_appends(
            [allocation_fact, lifecycle_reference_fact]
        )
        == 2
    )
    exact_replay_fact = dict(allocation_fact)
    exact_replay_fact["kind"] = "exact_replay"
    assert (
        _count_entity_identity_fact_appends([allocation_fact, exact_replay_fact])
        == 1
    )

    duplicate_allocation = entity_fact(
        "allocate",
        3,
        event_suffix=23,
        operation_suffix=33,
        request_digit="3",
    )
    _assert_value_error(
        lambda: _count_entity_identity_fact_appends(
            [allocation_fact, duplicate_allocation]
        )
    )
    _assert_value_error(
        lambda: _count_entity_identity_fact_appends([lifecycle_reference_fact])
    )
    allocation_at_two = dict(allocation_fact)
    allocation_at_two["sequence"] = 2
    reference_at_one = dict(lifecycle_reference_fact)
    reference_at_one["sequence"] = 1
    _assert_value_error(
        lambda: _count_entity_identity_fact_appends(
            [allocation_at_two, reference_at_one]
        )
    )
    wrong_type_reference = dict(lifecycle_reference_fact)
    wrong_type_reference["entity_type"] = "attempt"
    _assert_value_error(
        lambda: _count_entity_identity_fact_appends(
            [allocation_fact, wrong_type_reference]
        )
    )
    conflicting_replay = dict(exact_replay_fact)
    conflicting_replay["operation_request_sha256"] = "f" * 64
    _assert_value_error(
        lambda: _count_entity_identity_fact_appends(
            [allocation_fact, conflicting_replay]
        )
    )
    duplicate_event_reference = dict(lifecycle_reference_fact)
    duplicate_event_reference["event_id"] = allocation_fact["event_id"]
    _assert_value_error(
        lambda: _count_entity_identity_fact_appends(
            [allocation_fact, duplicate_event_reference]
        )
    )
    duplicate_sequence_reference = dict(lifecycle_reference_fact)
    duplicate_sequence_reference["sequence"] = allocation_fact["sequence"]
    _assert_value_error(
        lambda: _count_entity_identity_fact_appends(
            [allocation_fact, duplicate_sequence_reference]
        )
    )

    _assert_value_error(
        lambda: _ascii_jcs_golden_bytes({"allowed_key": 1.5})
    )


def test_stage_three_tracked_policy_files_fail_closed_on_private_identifiers() -> None:
    tracked_policy_paths = [
        ".agents/skills/real-data-readiness-audit/SKILL.md",
        "EXPERIMENT_LOG.md",
        "docs/local_csv_study_checklist.md",
        "docs/local_csv_readiness_audit_report_template.md",
        "docs/point_in_time_data_methodology_contract.md",
        "docs/experiment_trial_ledger_contract.md",
        "docs/real_data_readiness_audit.md",
    ]

    for relative_path in tracked_policy_paths:
        text = (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")
        assert "/Users/" not in text
        assert "/home/" not in text
        assert "/private/tmp/" not in text
        assert "file://" not in text
        assert re.search(r"(?i)\b[a-z]:[\\/]", text) is None
        assert re.search(r"\b[0-9a-fA-F]{64}\b", text) is None

    for relative_path in tracked_policy_paths[:4] + [tracked_policy_paths[-1]]:
        normalized_text = " ".join(
            (PROJECT_ROOT / relative_path)
            .read_text(encoding="utf-8")
            .split()
        )
        assert (
            "publication-approved hash or redacted private-evidence reference"
            in normalized_text
        )

    checklist = (
        PROJECT_ROOT / "docs/local_csv_study_checklist.md"
    ).read_text(encoding="utf-8")
    audit_template = (
        PROJECT_ROOT / "docs/local_csv_readiness_audit_report_template.md"
    ).read_text(encoding="utf-8")
    experiment_log = (PROJECT_ROOT / "EXPERIMENT_LOG.md").read_text(
        encoding="utf-8"
    )
    assert "| Actual hash |" not in checklist
    assert "| Actual hash |" not in audit_template
    assert "License documents, contract/account IDs" in experiment_log
    assert (
        "Private performance values remain outside tracked records"
        in " ".join(experiment_log.split())
    )


def test_readiness_and_experiment_records_do_not_bypass_program_gates() -> None:
    readiness_skill = (
        PROJECT_ROOT / ".agents/skills/real-data-readiness-audit/SKILL.md"
    ).read_text(encoding="utf-8")
    readiness_audit = (
        PROJECT_ROOT / "docs/real_data_readiness_audit.md"
    ).read_text(encoding="utf-8")
    experiment_log = (PROJECT_ROOT / "EXPERIMENT_LOG.md").read_text(
        encoding="utf-8"
    )
    study_checklist = (
        PROJECT_ROOT / "docs/local_csv_study_checklist.md"
    ).read_text(encoding="utf-8")
    audit_template = (
        PROJECT_ROOT / "docs/local_csv_readiness_audit_report_template.md"
    ).read_text(encoding="utf-8")
    controller = (
        PROJECT_ROOT / "docs/codex_long_running_controller.md"
    ).read_text(encoding="utf-8")
    methodology_contract = (
        PROJECT_ROOT / "docs/point_in_time_data_methodology_contract.md"
    ).read_text(encoding="utf-8")
    roadmap = (PROJECT_ROOT / "docs/current_roadmap.md").read_text(
        encoding="utf-8"
    )
    handoff = (PROJECT_ROOT / "docs/current_handoff.md").read_text(
        encoding="utf-8"
    )
    specification = (PROJECT_ROOT / "PROJECT_SPEC.md").read_text(
        encoding="utf-8"
    )

    for text in [readiness_skill, readiness_audit, methodology_contract]:
        normalized_text = " ".join(text.split())
        assert "docs/research_program_charter.md" in normalized_text
        assert "docs/current_roadmap.md" in normalized_text
        assert "`diagnostic_ready`" in normalized_text
        assert "`formal_ready`" in normalized_text
        assert "static current" in normalized_text
        assert "blocks formal interpretation" in normalized_text
        assert "immutable all-trial ledger" in normalized_text

    for text in [readiness_skill, readiness_audit, experiment_log]:
        normalized_text = " ".join(text.split())
        assert "canonicalization_id" in normalized_text
        assert "environment_id" in normalized_text
        assert "environment_lock_sha256" in normalized_text
        assert "known_at <= decision_time" in normalized_text
        assert "non-self-issued exact-version dataset-review decision" in normalized_text

    for text in [readiness_skill, readiness_audit]:
        normalized_text = " ".join(text.split())
        assert "unlocked/incomplete environment" in normalized_text
        assert (
            "A diagnostic-scope audit may return `diagnostic_ready` without a "
            "dataset-review decision"
        ) in normalized_text
        assert "`dataset_manifest_reviewed = false`" in normalized_text
        assert "`formal_interpretation_eligible = false`" in normalized_text
        assert "formal readiness remains blocked" in normalized_text
        assert "the outcome is not `formal_ready`" in normalized_text
        assert (
            "when formal interpretation is proposed, the dataset-review "
            "decision is absent"
        ) in normalized_text.lower()
        assert (
            "when formal interpretation is proposed, the immutable "
            "dataset-review decision id"
        ) in normalized_text.lower()
        assert (
            "for diagnostic scope without a dataset-review decision, do not "
            "fabricate a decision id"
        ) in normalized_text.lower()
        assert (
            "access-record and exposure-decision ids"
        ) in normalized_text.lower()
        assert "remain scope-applicable for diagnostics" in normalized_text.lower()

    normalized_readiness_skill = " ".join(readiness_skill.split()).lower()
    assert (
        "when formal interpretation is proposed, `dataset_manifest_reviewed` "
        "or `formal_interpretation_eligible` is absent"
    ) in normalized_readiness_skill
    assert (
        "- `dataset_manifest_reviewed` or "
        "`formal_interpretation_eligible` is absent"
    ) not in readiness_skill
    assert "- the dataset-review decision is absent" not in readiness_skill.lower()
    assert "- the dataset-review decision is absent" not in readiness_audit.lower()
    assert "finding dispositions, and exposure-decision id" not in (
        normalized_readiness_skill
    )

    for text in [experiment_log, study_checklist, audit_template]:
        normalized_text = " ".join(text.split()).lower()
        assert (
            "when formal interpretation is proposed, the immutable "
            "dataset-review decision"
        ) in normalized_text
        assert (
            "for diagnostic scope without a dataset-review decision, do not "
            "fabricate a decision id"
        ) in normalized_text
        assert "`dataset_manifest_reviewed = false`" in normalized_text
        assert "`formal_interpretation_eligible = false`" in normalized_text
        assert "protected-sample access-record" in normalized_text
        assert "exposure-decision id" in normalized_text
        assert "stop if the immutable decision is absent" not in normalized_text
        assert (
            "- immutable dataset-review decision id and exposure-decision id"
            not in normalized_text
        )

    for text in [study_checklist, audit_template]:
        normalized_text = " ".join(text.split()).lower()
        assert "every scope-applicable statement" in normalized_text
        assert "[formal interpretation only] dataset review" in normalized_text
        assert "the formal-only dataset-review box is outside scope" in normalized_text

    for phrase in [
        "diagnostic/legacy experiment record",
        "not the immutable all-trial ledger",
        "must not support formal historical interpretation",
        "Every configured case",
        "Tracked records must not contain private absolute paths",
    ]:
        assert phrase in " ".join(experiment_log.split())

    for text in [
        methodology_contract,
        roadmap,
        handoff,
        specification,
        readiness_skill,
        readiness_audit,
        experiment_log,
    ]:
        normalized_text = " ".join(text.split())
        assert "2025-05-01 through 2026-05-31" in normalized_text
        assert "`historical_evaluation`" in normalized_text

    assert "the required predecessor or current-stage PR" in controller
    assert "the current-stage PR has been opened" in controller
    assert "- an open PR requires human review" not in controller
    assert "- a previous PR is not verified merged" not in controller
    assert "- a PR has been opened but is not eligible" not in controller


def test_review_required_prs_complete_current_head_review_before_merge() -> None:
    controller = " ".join(
        (PROJECT_ROOT / "docs/codex_long_running_controller.md")
        .read_text(encoding="utf-8")
        .split()
    )
    workflow_skill = " ".join(
        (PROJECT_ROOT / ".agents/skills/staged-quant-workflow/SKILL.md")
        .read_text(encoding="utf-8")
        .split()
    )
    roadmap = " ".join(
        (PROJECT_ROOT / "docs/current_roadmap.md")
        .read_text(encoding="utf-8")
        .split()
    )

    for text in [controller, workflow_skill]:
        assert (
            "Do not enable auto-merge or attempt a merge while required checks "
            "or an applicable current-head Codex review is pending."
        ) in text
        assert (
            "completed on the current head with no unresolved actionable "
            "findings"
        ) in text
        assert text.index("post `@codex review` once") < text.index(
            "Do not enable auto-merge or attempt a merge"
        )
        assert "required checks pass, or auto-merge" not in text
        assert "required checks pass or auto-merge" not in text

    assert (
        "Do not enable auto-merge or merge a review-required PR until Codex "
        "review has completed on the current head with no unresolved actionable "
        "findings."
    ) in roadmap


def test_tracking_error_design_freezes_stage_two_contract() -> None:
    design = (
        PROJECT_ROOT / "docs/risk_evaluation_metrics_design.md"
    ).read_text(encoding="utf-8")
    stage_two = design.split("## Stage 2: Tracking Error", maxsplit=1)[1]
    stage_two = stage_two.split("## Deferred Metrics", maxsplit=1)[0]

    for phrase in [
        "tracking_error = std(measured_active_return, ddof=0) * sqrt(252)",
        "strategy_net_after_applied_costs_vs_cost_free_benchmark",
        "cost-free close-to-close price return",
        "daily_close_to_close",
        "exclude_synthetic_anchor",
        "tracking_error_missing_policy = \"raise\"",
        "tracking error requires at least 2 measured return periods",
        "It is never the difference between strategy and",
        "benchmark annualized returns",
        "refreshes affected reports, JSON experiment logs, and the",
        "experiment registry",
        "Generated evidence",
        "remains explicitly synthetic",
    ]:
        assert phrase in stage_two


def test_placeholder_modules_are_importable() -> None:
    import backtest.metrics
    import backtest.portfolio
    import data.csv_loader
    import features.momentum
    import features.reversal
    import features.volatility
    import reporting.plots
    import risk.constraints

    assert features.momentum.__doc__
    assert features.reversal.__doc__
    assert features.volatility.__doc__
    assert backtest.portfolio.__doc__
    assert backtest.metrics.__doc__
    assert data.csv_loader.__doc__
    assert risk.constraints.__doc__
    assert reporting.plots.__doc__


def test_position_constraint_design_matches_implementation_scope() -> None:
    design = (PROJECT_ROOT / "docs/risk_evaluation_metrics_design.md").read_text(
        encoding="utf-8"
    )
    constraints = (PROJECT_ROOT / "src/risk/constraints.py").read_text(
        encoding="utf-8"
    )

    for phrase in [
        "after signal lag, ranking, eligibility, and equal-weight target",
        "constrained_weight[i, t] = min(target_weight[i, t], max_position_weight)",
        "not redistributed or renormalized",
        "non-interest-bearing cash",
        "clip_and_hold_cash",
        "after_selection_before_trade_calculation",
        "calculated from constrained targets versus drifted pre-trade holdings",
    ]:
        assert phrase in design
    assert "apply_long_only_position_cap" in constraints


def test_holding_episode_design_matches_implementation_contract() -> None:
    design = (PROJECT_ROOT / "docs/risk_evaluation_metrics_design.md").read_text(
        encoding="utf-8"
    )

    for phrase in [
        "continuous_positive_weight_v1",
        "net_contribution_over_cumulative_deployed_weight",
        "pro_rata_absolute_signed_trade_weight",
        "abs(signed_trade_weights) == trade_weights",
        "terminal-open episode",
        "Zero-return episodes are not hits",
        "episode_hit_rate = mean(episode_return > 0)",
        "average_holding_period_return = mean(episode_return)",
    ]:
        assert phrase in design


def test_public_metadata_and_readme_match_implemented_scope() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    configuration = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    metadata = configuration["project"]

    assert "docs/current_roadmap.md" in readme
    assert "docs/research_program_charter.md" in readme
    assert "docs/point_in_time_data_methodology_contract.md" in readme
    assert "plotting remains unimplemented" in readme
    assert "No market-data downloader" in readme
    assert "POINT-IN-TIME FEATURES" not in readme
    assert "private_data" not in readme
    assert metadata["license"] == "Apache-2.0"
    assert metadata["urls"]["Repository"].endswith("equity-factor-research")
    assert metadata["dependencies"] == [
        "numpy>=1.26",
        "pandas>=2.1",
        "scipy>=1.11",
    ]
    assert configuration["tool"]["ruff"]["lint"]["select"] == [
        "E4",
        "E7",
        "E9",
        "F",
    ]


def test_ci_and_generated_repo_map_share_core_validation_commands() -> None:
    workflow = (PROJECT_ROOT / ".github/workflows/ci.yml").read_text(
        encoding="utf-8"
    )
    repo_map = (PROJECT_ROOT / "docs/repo_map.md").read_text(encoding="utf-8")
    commands = [
        "python -m pytest -q",
        "python -m ruff check .",
        "python -m compileall src tests research",
        "python -m compileall lean",
        "python -m build",
    ]

    for command in commands:
        assert command in workflow
        assert command in repo_map

    repo_map_module = runpy.run_path(str(PROJECT_ROOT / "scripts/repo_map.py"))
    assert repo_map_module["build_repo_map"]() == repo_map

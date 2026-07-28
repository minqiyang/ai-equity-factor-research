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
        "| 4a. Experiment/trial ledger contract | Local gates passed"
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
        "The v1 event-type vocabulary is closed at this minimum set",
        "Stage 4a freezes exact unknown-field-rejecting payload schemas only for the two golden event types",
        "separately reviewed machine-readable per-event payload schema registry",
        "`SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`",
        "must not claim a contract-wide fail-closed ledger, Stage 4b conformance",
        "tamper-evident, not WORM",
        "`CAMPAIGN_EVIDENCE_FROZEN`",
        "`campaign_evidence_prefix_v1`",
        "The freeze event is necessarily excluded",
        "`freeze_event_sequence`",
        "independently retained immutable checkpoint",
        "A producer cannot self-certify",
        "does not self-stale the decision",
        "`CAMPAIGN_ADJUDICATED`",
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

    vocabulary_block = (
        contract.split("The v1 event-type vocabulary is closed at this minimum set:", 1)[
            1
        ]
        .split("```text", 1)[1]
        .split("```", 1)[0]
        .split()
    )
    assert len(vocabulary_block) == len(set(vocabulary_block))
    assert len(vocabulary_block) == 37
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
    assert "| 4a. Experiment/trial ledger contract | Local gates passed" in roadmap
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


def _require_normalized_utc_timestamp(value: object, *, context: str) -> str:
    """Validate the frozen RFC 3339 UTC syntax without a mutable leap table."""
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
    ordinary_time = 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59
    # RFC 3339 permits an inserted leap second at these structural UTC sites.
    leap_second = (
        hour == 23
        and minute == 59
        and second == 60
        and (month, day) in {(6, 30), (12, 31)}
    )
    if not (ordinary_time or leap_second):
        raise ValueError(f"{context} must be a valid RFC 3339 UTC time")
    fraction = match.group(7)
    if fraction is not None and fraction.endswith("0"):
        raise ValueError(f"{context} has a noncanonical fractional second")
    return value


def _ledger_event_identity_projection(source: object) -> dict[str, object]:
    """Validate the exact envelope and the two Stage 4a golden payload schemas."""
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
    _require_ledger_typed_id(
        projection["actor_id"],
        prefix="act",
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
    if projection["event_type"] not in {
        "LEDGER_EPOCH_CREATED",
        "TRIAL_ALLOCATED",
    }:
        raise ValueError("event type has no frozen Stage 4a golden payload schema")
    for field in ["occurred_at", "recorded_at"]:
        _require_normalized_utc_timestamp(projection[field], context=field)
    previous_hash = projection["previous_event_sha256"]
    if previous_hash is not None and (
        not isinstance(previous_hash, str)
        or re.fullmatch(r"[0-9a-f]{64}", previous_hash) is None
    ):
        raise ValueError("previous event hash must be null or lowercase SHA-256")

    if projection["event_type"] == "LEDGER_EPOCH_CREATED":
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

    if sequence == 0 or previous_hash is None:
        raise ValueError("TRIAL_ALLOCATED requires earlier parent allocations")
    if projection["subject_type"] != "trial":
        raise ValueError("golden subject must be trial")
    subject_id = _require_ledger_typed_id(
        projection["subject_id"],
        prefix="trl",
        context="subject_id",
    )

    payload = _require_exact_keys(
        projection["payload"],
        {
            "campaign_id",
            "campaign_scope_ids",
            "experiment_id",
            "trial_family_id",
            "trial_id",
            "configuration_sha256",
            "code_identity_sha256",
            "data_manifest_ids",
            "environment_id",
            "environment_lock_sha256",
            "sample_ids",
            "selection_role",
            "expected_artifact_roles",
            "trial_state",
        },
        context="TRIAL_ALLOCATED payload",
    )
    for field, prefix in {
        "campaign_id": "cmp",
        "experiment_id": "exp",
        "trial_family_id": "tfm",
        "trial_id": "trl",
        "environment_id": "env",
    }.items():
        _require_ledger_typed_id(payload[field], prefix=prefix, context=field)
    campaign_scope_ids = payload["campaign_scope_ids"]
    if (
        not isinstance(campaign_scope_ids, list)
        or campaign_scope_ids != sorted(set(campaign_scope_ids))
        or payload["campaign_id"] not in campaign_scope_ids
    ):
        raise ValueError("campaign scope IDs must be sorted and include campaign")
    for index, campaign_scope_id in enumerate(campaign_scope_ids):
        _require_ledger_typed_id(
            campaign_scope_id,
            prefix="cmp",
            context=f"campaign_scope_ids[{index}]",
        )
    if payload["trial_id"] != subject_id:
        raise ValueError("payload trial ID must equal the event subject")
    for field in [
        "configuration_sha256",
        "code_identity_sha256",
        "environment_lock_sha256",
    ]:
        value = payload[field]
        if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
            raise ValueError(f"{field} must be lowercase SHA-256")
    for field, prefix in {
        "data_manifest_ids": "dsm",
        "sample_ids": "smp",
    }.items():
        values = payload[field]
        if not isinstance(values, list) or values != sorted(set(values)):
            raise ValueError(f"{field} must be a sorted unique array")
        for index, value in enumerate(values):
            _require_ledger_typed_id(
                value,
                prefix=prefix,
                context=f"{field}[{index}]",
            )
    artifact_roles = payload["expected_artifact_roles"]
    if (
        not isinstance(artifact_roles, list)
        or artifact_roles != sorted(set(artifact_roles))
        or not all(isinstance(role, str) and role for role in artifact_roles)
    ):
        raise ValueError("expected artifact roles must be sorted unique strings")
    if payload["selection_role"] != "diagnostic":
        raise ValueError("unexpected golden selection role")
    if payload["trial_state"] != "PLANNED":
        raise ValueError("unexpected golden trial state")
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


def _require_trial_allocation_parent_order(
    parent_facts: object,
    trial_event: object,
) -> None:
    """Check the contract's three parent paths from documentation-only facts."""
    trial = _ledger_event_identity_projection(trial_event)
    if trial["event_type"] != "TRIAL_ALLOCATED":
        raise ValueError("trial parent order requires TRIAL_ALLOCATED")
    facts = _require_exact_keys(
        parent_facts,
        {
            "epoch_sequence",
            "campaign_sequence",
            "experiment_sequence",
            "campaign_id",
            "experiment_id",
            "family_id",
            "family_path",
            "sample_paths",
        },
        context="trial parent facts",
    )
    payload = trial["payload"]
    assert isinstance(payload, dict)
    epoch_sequence = facts["epoch_sequence"]
    campaign_sequence = facts["campaign_sequence"]
    experiment_sequence = facts["experiment_sequence"]
    trial_sequence = trial["sequence"]
    if (
        facts["campaign_id"] != payload["campaign_id"]
        or facts["experiment_id"] != payload["experiment_id"]
        or facts["family_id"] != payload["trial_family_id"]
        or not (epoch_sequence == 0 < campaign_sequence < experiment_sequence)
        or experiment_sequence >= trial_sequence
        or set(facts["sample_paths"]) != set(payload["sample_ids"])
    ):
        raise ValueError("base parent bindings or order are invalid")

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


def _utf16_sort_key(value: str) -> bytes:
    return value.encode("utf-16-be")


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


def _assert_value_error(operation: object) -> None:
    if not callable(operation):
        raise AssertionError("operation must be callable")
    try:
        operation()
    except ValueError:
        return
    raise AssertionError("operation did not fail closed")


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


def test_ledger_event_golden_parent_paths_and_fail_closed_vectors() -> None:
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
        == "experiment_trial_ledger_event_v1_golden_v1"
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
    year_zero_event = json.loads(json.dumps(fixture["semantic_input"]))
    year_zero_event["occurred_at"] = "0000-02-29T00:00:00Z"
    assert (
        _ledger_event_identity_projection(year_zero_event)["occurred_at"]
        == "0000-02-29T00:00:00Z"
    )
    leap_second_event = json.loads(json.dumps(fixture["semantic_input"]))
    leap_second_event["occurred_at"] = "1990-12-31T23:59:60Z"
    assert (
        _ledger_event_identity_projection(leap_second_event)["occurred_at"]
        == "1990-12-31T23:59:60Z"
    )
    fractional_leap_second_event = json.loads(
        json.dumps(fixture["semantic_input"])
    )
    fractional_leap_second_event["occurred_at"] = (
        "1990-12-31T23:59:60.1234567890123456789Z"
    )
    assert _ledger_event_identity_projection(fractional_leap_second_event)[
        "occurred_at"
    ].endswith(".1234567890123456789Z")

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
        "1990-12-31T23:59:60.120Z",
        "2024-06-30T22:59:60Z",
        "2024-06-29T23:59:60Z",
        "2026-01-01T00:00:00.000Z",
        "2026-01-01T00:00:00.120Z",
        "2026-01-01T00:00:00.Z",
        "2026-01-01T00:00:00+00:00",
    ]:
        invalid_timestamp_event = json.loads(json.dumps(fixture["semantic_input"]))
        invalid_timestamp_event["occurred_at"] = invalid_timestamp
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
    _assert_value_error(
        lambda: _ledger_event_identity_projection(
            fixture["orphan_trial_semantic_input"]
        )
    )
    epoch_chained_trial = json.loads(
        json.dumps(fixture["orphan_trial_semantic_input"])
    )
    epoch_chained_trial["sequence"] = 1
    epoch_chained_trial["previous_event_sha256"] = fixture["sha256"]
    assert _ledger_event_identity_projection(epoch_chained_trial)[
        "previous_event_sha256"
    ] == fixture["sha256"]

    payload = epoch_chained_trial["payload"]
    campaign_id = payload["campaign_id"]
    experiment_id = payload["experiment_id"]
    family_id = payload["trial_family_id"]
    sample_id = payload["sample_ids"][0]

    def facts(
        campaign_sequence: int,
        experiment_sequence: int,
        family_path: dict[str, object],
        sample_path: dict[str, object],
    ) -> dict[str, object]:
        return {
            "epoch_sequence": 0,
            "campaign_sequence": campaign_sequence,
            "experiment_sequence": experiment_sequence,
            "campaign_id": campaign_id,
            "experiment_id": experiment_id,
            "family_id": family_id,
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

    def trial_at(sequence: int) -> dict[str, object]:
        trial = json.loads(json.dumps(epoch_chained_trial))
        trial["sequence"] = sequence
        trial["previous_event_sha256"] = "a" * 64
        return trial

    direct_facts = facts(1, 4, direct(3, family_id), direct(2, sample_id))
    other_campaign_id = "cmp_00000000000000000000000000000004"
    shared_direct_facts = facts(
        1,
        4,
        direct(3, family_id, [other_campaign_id, campaign_id]),
        direct(2, sample_id),
    )
    global_facts = facts(
        3,
        4,
        ledger_global(1, 5, family_id),
        ledger_global(2, 6, sample_id),
    )
    late_global_facts = facts(
        1,
        2,
        ledger_global(3, 5, family_id),
        ledger_global(4, 6, sample_id),
    )
    external_facts = facts(
        1,
        3,
        direct(4, family_id),
        stage3_external(2, sample_id),
    )
    for valid_facts, trial_sequence in [
        (direct_facts, 5),
        (shared_direct_facts, 5),
        (global_facts, 7),
        (late_global_facts, 7),
        (external_facts, 5),
    ]:
        _require_trial_allocation_parent_order(
            valid_facts,
            trial_at(trial_sequence),
        )

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
            lambda invalid_facts=invalid_facts: _require_trial_allocation_parent_order(
                invalid_facts,
                trial_at(7),
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

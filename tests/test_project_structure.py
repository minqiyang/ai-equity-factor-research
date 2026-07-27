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
        "## Audited Findings",
        "## PR #148 Interaction",
        "## Next Safe Stage",
        "Stage 4 - Experiment and trial ledger",
    ]:
        assert phrase in handoff

    assert "## Status: Historical" in historical_roadmap
    assert "must not be used as the current task queue" in historical_roadmap
    assert "849 passing tests" in roadmap
    assert "Starting validation: 849 tests passed" in handoff
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
    assert (
        "Stage 4 - Experiment and trial ledger"
        in handoff
    )


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
        "Readiness-scope re-review fix validated; new-head GitHub gates pending"
    ) in roadmap
    assert (
        "| 4. Experiment/trial ledger | Next after Stage 3 protected merge "
        "and successful exact merge-head CI"
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
        "Status: proposed Stage 3 methodology contract",
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


def test_stage_three_tracked_policy_files_fail_closed_on_private_identifiers() -> None:
    tracked_policy_paths = [
        ".agents/skills/real-data-readiness-audit/SKILL.md",
        "EXPERIMENT_LOG.md",
        "docs/local_csv_study_checklist.md",
        "docs/local_csv_readiness_audit_report_template.md",
        "docs/point_in_time_data_methodology_contract.md",
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

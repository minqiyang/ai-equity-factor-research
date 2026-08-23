"""Behavioral tests for pit_manifest_validator_v1."""

from __future__ import annotations

from copy import deepcopy
import ast
import hashlib
import json
from pathlib import Path
import socket
import unicodedata

import pytest

from pit_manifest_validator_v1.canonical import (
    ValidationError,
    canonical_sha256,
    canonical_utf8,
    nfc_text,
    parse_json_bytes,
)
from pit_manifest_validator_v1.cli import main as cli_main
from pit_manifest_validator_v1.validator import (
    DECISION_STATES,
    infer_kind,
    project_dataset_review_decision,
    project_freeze_record,
    project_ordered_component_inventory,
    project_private_full_manifest,
    project_public_redacted_projection,
    validate_bytes,
    validate_document,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_PATH = PROJECT_ROOT / "tests/fixtures/pit_canonical_json_v1_golden.json"
FIXTURE_DIR = PROJECT_ROOT / "tests/fixtures/pit_manifest_validator_v1"
MANIFEST_PATH = FIXTURE_DIR / "private_full_manifest_valid.json"
DECISION_PATH = FIXTURE_DIR / "dataset_review_decision_valid.json"
FREEZE_PATH = FIXTURE_DIR / "track_a_pr2_freeze_record_valid.json"


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_error(operation, code: str) -> ValidationError:
    with pytest.raises(ValidationError) as captured:
        operation()
    assert captured.value.code == code
    message = str(captured.value)
    assert "/private" not in message
    assert "file://" not in message
    assert "@example.com" not in message
    return captured.value


def test_golden_canonical_bytes_and_digest() -> None:
    fixture = _load_json(GOLDEN_PATH)
    result = validate_document(fixture["semantic_input"], "pit_canonical_json_v1")
    assert result["canonical_utf8"].decode("utf-8") == fixture["canonical_utf8"]
    assert result["sha256"] == fixture["sha256"]
    assert canonical_utf8(fixture["semantic_input"]) == result["canonical_utf8"]
    assert canonical_sha256(fixture["semantic_input"]) == fixture["sha256"]


def test_ordered_inventory_reorder_stable_and_mutation_changes_digest() -> None:
    fixture = _load_json(GOLDEN_PATH)["ordered_manifest_sha256_vectors"]
    base = validate_document(fixture["semantic_input"], "ordered_component_inventory_v1")
    reordered = validate_document(
        fixture["reordered_semantic_input"],
        "ordered_component_inventory_v1",
    )
    mutated = validate_document(
        fixture["mutated_semantic_input"],
        "ordered_component_inventory_v1",
    )
    assert base["canonical_utf8"].decode("utf-8") == fixture["canonical_utf8"]
    assert reordered["canonical_utf8"] == base["canonical_utf8"]
    assert base["sha256"] == fixture["sha256"]
    assert reordered["sha256"] == fixture["sha256"]
    assert mutated["canonical_utf8"].decode("utf-8") == fixture["mutated_canonical_utf8"]
    assert mutated["sha256"] == fixture["mutated_sha256"]
    assert mutated["sha256"] != base["sha256"]


def test_public_projection_reorder_stable_and_mutation_changes_digest() -> None:
    fixture = _load_json(GOLDEN_PATH)["public_projection_sha256_vectors"]
    base = validate_document(fixture["semantic_input"], "public_redacted_projection_v1")
    reordered = validate_document(
        fixture["reordered_semantic_input"],
        "public_redacted_projection_v1",
    )
    mutated = validate_document(
        fixture["mutated_semantic_input"],
        "public_redacted_projection_v1",
    )
    assert base["canonical_utf8"].decode("utf-8") == fixture["canonical_utf8"]
    assert reordered["canonical_utf8"] == base["canonical_utf8"]
    assert base["sha256"] == fixture["sha256"]
    assert mutated["canonical_utf8"].decode("utf-8") == fixture["mutated_canonical_utf8"]
    assert mutated["sha256"] == fixture["mutated_sha256"]
    assert mutated["sha256"] != base["sha256"]
    assert {
        item["state"] for item in base["projection"]["policy_states"]
    } <= DECISION_STATES


def test_byte_identical_rerun() -> None:
    fixture = _load_json(GOLDEN_PATH)
    first = canonical_utf8(fixture["semantic_input"])
    second = canonical_utf8(fixture["semantic_input"])
    assert first == second
    inventory = _load_json(GOLDEN_PATH)["ordered_manifest_sha256_vectors"]["semantic_input"]
    assert canonical_utf8(
        project_ordered_component_inventory(inventory)
    ) == canonical_utf8(project_ordered_component_inventory(deepcopy(inventory)))


def test_duplicate_keys_fail_closed() -> None:
    raw = b'{"a":1,"a":2}'
    error = _assert_error(lambda: parse_json_bytes(raw), "DUPLICATE_KEY")
    assert error.field == "object"


def test_lone_surrogate_fail_closed() -> None:
    raw = '{"x":"\\ud800"}'.encode("utf-8")
    _assert_error(lambda: parse_json_bytes(raw), "LONE_SURROGATE")


def test_non_ijson_integer_and_raw_float_fail_closed() -> None:
    too_large = str(2**53).encode("utf-8")
    _assert_error(lambda: parse_json_bytes(too_large), "NON_IJSON_INTEGER")
    _assert_error(lambda: parse_json_bytes(b"1.25"), "RAW_FLOAT")
    _assert_error(lambda: parse_json_bytes(b"NaN"), "NON_FINITE_NUMBER")


def test_unknown_key_and_grammar_violations_fail_closed() -> None:
    fixture = deepcopy(
        _load_json(GOLDEN_PATH)["public_projection_sha256_vectors"]["semantic_input"]
    )
    leaked = deepcopy(fixture)
    leaked["private_path"] = "/private/data.csv"
    error = _assert_error(
        lambda: project_public_redacted_projection(leaked),
        "UNKNOWN_KEY",
    )
    assert "/private/data.csv" not in str(error)

    path_id = deepcopy(fixture)
    path_id["manifest_id"] = "/private/data.csv"
    error = _assert_error(
        lambda: project_public_redacted_projection(path_id),
        "SAFE_PUBLIC_ID",
    )
    assert "/private/data.csv" not in str(error)

    uri = deepcopy(fixture)
    uri["redacted_evidence_refs"][0]["evidence_ref_id"] = "file://private/data.csv"
    error = _assert_error(
        lambda: project_public_redacted_projection(uri),
        "SAFE_PUBLIC_ID",
    )
    assert "file://" not in str(error)

    email = deepcopy(fixture)
    email["published_hashes"][0]["publication_approval_ref_id"] = "owner@example.com"
    error = _assert_error(
        lambda: project_public_redacted_projection(email),
        "SAFE_PUBLIC_ID",
    )
    assert "@example.com" not in str(error)


def test_decision_enum_is_exactly_accepted_diagnostic_only_blocked() -> None:
    assert DECISION_STATES == {"accepted", "diagnostic_only", "blocked"}
    fixture = deepcopy(
        _load_json(GOLDEN_PATH)["public_projection_sha256_vectors"]["semantic_input"]
    )
    fixture["policy_states"][0]["state"] = "diagnostic_ready"
    _assert_error(
        lambda: project_public_redacted_projection(fixture),
        "UNEXPECTED_VALUE",
    )
    decision = deepcopy(_load_json(DECISION_PATH))
    decision["decision"] = "formal_ready"
    _assert_error(lambda: project_dataset_review_decision(decision), "UNEXPECTED_VALUE")


def test_sentinel_timestamp_and_typed_null_fail_closed() -> None:
    freeze = deepcopy(_load_json(FREEZE_PATH))
    freeze["as_of_cutoff"] = "9999-12-31T00:00:00Z"
    _assert_error(lambda: project_freeze_record(freeze), "SENTINEL_TIMESTAMP")

    limited = deepcopy(freeze)
    limited["as_of_cutoff"] = "2026-05-29T20:00:00Z"
    symbol_change = next(
        item
        for item in limited["role_coverage"]
        if item["role"] == "symbol_change_history"
    )
    symbol_change["limitation_state"] = "none"
    symbol_change["limitation_id"] = "still-present"
    _assert_error(lambda: project_freeze_record(limited), "TYPED_NULL")

    terminal = deepcopy(_load_json(FREEZE_PATH))
    terminal["lineage_and_terminal"]["terminal_event_policy_state"] = (
        "candidate_not_accepted"
    )
    terminal["lineage_and_terminal"]["terminal_event_policy_sha256"] = "a" * 64
    _assert_error(lambda: project_freeze_record(terminal), "TYPED_NULL")


def test_unknown_token_is_blocked() -> None:
    freeze = deepcopy(_load_json(FREEZE_PATH))
    freeze["calendar"]["calendar_version"] = "UNKNOWN"
    _assert_error(lambda: project_freeze_record(freeze), "UNKNOWN_BLOCKED")


def _derived_input(payload: dict[str, object]) -> dict[str, object]:
    return next(
        item
        for item in payload["inputs"]
        if item["input_id"] == "synthetic-derived"
    )


def test_parent_pairs_reorder_stable_and_count_mispair_fail_closed() -> None:
    manifest = deepcopy(_load_json(MANIFEST_PATH))
    base = project_private_full_manifest(manifest)
    base_derived = _derived_input(base)

    reordered = deepcopy(manifest)
    target = _derived_input(reordered)
    target["parent_input_ids"] = list(reversed(target["parent_input_ids"]))
    target["parent_input_hashes"] = list(reversed(target["parent_input_hashes"]))
    reordered_proj = project_private_full_manifest(reordered, verify_digest=False)
    reordered_derived = _derived_input(reordered_proj)
    assert reordered_proj["canonical_manifest_sha256"] == base["canonical_manifest_sha256"]
    assert reordered_derived["parent_input_ids"] == base_derived["parent_input_ids"]
    assert reordered_derived["parent_input_hashes"] == base_derived["parent_input_hashes"]

    mispaired = deepcopy(manifest)
    mis_target = _derived_input(mispaired)
    mis_target["parent_input_ids"] = list(reversed(mis_target["parent_input_ids"]))
    mis_proj = project_private_full_manifest(mispaired, verify_digest=False)
    assert mis_proj["canonical_manifest_sha256"] != base["canonical_manifest_sha256"]
    assert _derived_input(mis_proj)["parent_input_hashes"] != base_derived[
        "parent_input_hashes"
    ]

    short = deepcopy(manifest)
    _derived_input(short)["parent_input_hashes"] = _derived_input(short)[
        "parent_input_hashes"
    ][:1]
    _assert_error(lambda: project_private_full_manifest(short), "PARENT_HASH_COUNT")

    extra = deepcopy(manifest)
    _derived_input(extra)["parent_input_hashes"] = list(
        _derived_input(extra)["parent_input_hashes"]
    ) + ["f" * 64]
    _assert_error(lambda: project_private_full_manifest(extra), "PARENT_HASH_COUNT")


def test_coverage_bounds_and_as_of_cutoff_fail_closed() -> None:
    inverted_role = deepcopy(_load_json(FREEZE_PATH))
    inverted_role["role_coverage"][0]["coverage_start_inclusive"] = "2026-05-30"
    inverted_role["role_coverage"][0]["coverage_end_inclusive"] = "2026-05-29"
    _assert_error(lambda: project_freeze_record(inverted_role), "COVERAGE_ORDER")

    cutoff_after_end = deepcopy(_load_json(FREEZE_PATH))
    cutoff_after_end["role_coverage"][0]["coverage_end_inclusive"] = "2026-05-28"
    _assert_error(
        lambda: project_freeze_record(cutoff_after_end), "AS_OF_OUTSIDE_COVERAGE"
    )

    cutoff_before_start = deepcopy(_load_json(FREEZE_PATH))
    for item in cutoff_before_start["role_coverage"]:
        item["coverage_start_inclusive"] = "2026-05-30"
        item["coverage_end_inclusive"] = "2026-06-30"
    _assert_error(
        lambda: project_freeze_record(cutoff_before_start), "AS_OF_OUTSIDE_COVERAGE"
    )

    inverted_input = deepcopy(_load_json(MANIFEST_PATH))
    inverted_input["inputs"][0]["coverage_start_inclusive"] = "2026-05-30"
    inverted_input["inputs"][0]["coverage_end_inclusive"] = "2026-05-29"
    _assert_error(
        lambda: project_private_full_manifest(inverted_input), "COVERAGE_ORDER"
    )

    inverted_extraction = deepcopy(_load_json(MANIFEST_PATH))
    inverted_extraction["extraction_identity"]["coverage_start_inclusive"] = (
        "2026-05-30"
    )
    inverted_extraction["extraction_identity"]["coverage_end_inclusive"] = "2026-05-29"
    _assert_error(
        lambda: project_private_full_manifest(inverted_extraction), "COVERAGE_ORDER"
    )


def test_infer_kind_unknown_schema_fails_closed() -> None:
    leaked = {
        "schema_version": "public_redacted_projection_v2",
        "private_path": "/private/data.csv",
    }
    error = _assert_error(lambda: validate_document(leaked), "UNKNOWN_SCHEMA_VERSION")
    assert "/private/data.csv" not in str(error)
    error = _assert_error(lambda: infer_kind(leaked), "UNKNOWN_SCHEMA_VERSION")
    assert "/private/data.csv" not in str(error)
    raw = json.dumps(leaked, ensure_ascii=True).encode("utf-8")
    _assert_error(lambda: validate_bytes(raw), "UNKNOWN_SCHEMA_VERSION")

    generic = {"alpha": 1, "z": None}
    result = validate_document(generic)
    assert result["kind"] == "pit_canonical_json_v1"
    assert infer_kind(generic) == "pit_canonical_json_v1"

    known = deepcopy(
        _load_json(GOLDEN_PATH)["public_projection_sha256_vectors"]["semantic_input"]
    )
    assert infer_kind(known) == "public_redacted_projection_v1"


def test_valid_private_manifest_and_acyclic_lineage() -> None:
    manifest = _load_json(MANIFEST_PATH)
    result = validate_document(manifest, "private_full_manifest")
    assert result["kind"] == "private_full_manifest"
    assert result["sha256"] == manifest["canonical_manifest_sha256"]
    assert hashlib.sha256(result["canonical_utf8"]).hexdigest() == result["sha256"]
    input_ids = [item["input_id"] for item in result["projection"]["inputs"]]
    assert input_ids == sorted(input_ids)


def test_cyclic_lineage_and_empty_components_fail_closed() -> None:
    manifest = deepcopy(_load_json(MANIFEST_PATH))
    first, second = manifest["inputs"][0], manifest["inputs"][1]
    first["content_status"] = "derived"
    first["parent_input_ids"] = [second["input_id"]]
    first["parent_input_hashes"] = [second["physical_components"][0]["raw_byte_sha256"]]
    first["transformation_id"] = "cycle-transform"
    first["code_sha"] = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    first["config_sha256"] = "d" * 64
    second["content_status"] = "derived"
    second["parent_input_ids"] = [first["input_id"]]
    second["parent_input_hashes"] = [first["physical_components"][0]["raw_byte_sha256"]]
    second["transformation_id"] = "cycle-transform-2"
    second["code_sha"] = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    second["config_sha256"] = "e" * 64
    _assert_error(lambda: project_private_full_manifest(manifest), "CYCLIC_LINEAGE")

    empty = deepcopy(_load_json(MANIFEST_PATH))
    empty["inputs"][0]["physical_components"] = []
    _assert_error(lambda: project_private_full_manifest(empty), "EMPTY_COMPONENTS")


def test_valid_decision_record_and_binding_tuple() -> None:
    decision = _load_json(DECISION_PATH)
    result = validate_document(
        decision,
        "dataset_review_decision",
        expected_binding={
            "manifest_id": decision["manifest_id"],
            "canonical_manifest_sha256": decision["canonical_manifest_sha256"],
            "public_projection_id": decision["public_projection_id"],
            "public_projection_sha256": decision["public_projection_sha256"],
            "contract_id": decision["contract_id"],
            "contract_version": decision["contract_version"],
            "contract_content_sha256": decision["contract_content_sha256"],
            "contract_protected_merge_sha": decision["contract_protected_merge_sha"],
        },
    )
    assert result["projection"]["decision"] in DECISION_STATES
    assert result["sha256"] == decision["decision_record_sha256"]
    mismatched = deepcopy(decision)
    _assert_error(
        lambda: validate_document(
            mismatched,
            "dataset_review_decision",
            expected_binding={"manifest_id": "other-manifest"},
        ),
        "BINDING_MISMATCH",
    )


def test_valid_freeze_record() -> None:
    freeze = _load_json(FREEZE_PATH)
    result = validate_document(freeze, "track_a_pr2_freeze_record_v1")
    assert result["sha256"] == freeze["freeze_record_sha256"]
    roles = [item["role"] for item in result["projection"]["role_coverage"]]
    assert "symbol_change_history" in roles
    assert result["projection"]["coverage_thresholds"][
        "factor_month_eligible_listing_floor"
    ] == 100


def test_validate_bytes_round_trip_for_committed_fixtures() -> None:
    for path, kind in [
        (MANIFEST_PATH, "private_full_manifest"),
        (DECISION_PATH, "dataset_review_decision"),
        (FREEZE_PATH, "track_a_pr2_freeze_record_v1"),
    ]:
        first = validate_bytes(path.read_bytes(), kind)
        second = validate_bytes(path.read_bytes(), kind)
        assert first["canonical_utf8"] == second["canonical_utf8"]
        assert first["sha256"] == second["sha256"]


def test_no_network_during_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket.socket, "__init__", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    validate_bytes(MANIFEST_PATH.read_bytes(), "private_full_manifest")
    validate_bytes(DECISION_PATH.read_bytes(), "dataset_review_decision")
    validate_bytes(FREEZE_PATH.read_bytes(), "track_a_pr2_freeze_record_v1")


def test_cli_validate_and_canonicalize(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    golden = _load_json(GOLDEN_PATH)
    semantic_path = tmp_path / "semantic.json"
    semantic_path.write_text(
        json.dumps(golden["semantic_input"], ensure_ascii=True),
        encoding="utf-8",
    )
    assert cli_main(["canonicalize", "--kind", "pit_canonical_json_v1", str(semantic_path)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["canonical_utf8"] == golden["canonical_utf8"]
    assert payload["sha256"] == golden["sha256"]

    assert cli_main(["validate", "--kind", "private_full_manifest", str(MANIFEST_PATH)]) == 0
    validated = json.loads(capsys.readouterr().out)
    assert validated["ok"] is True
    assert validated["kind"] == "private_full_manifest"
    assert "errors" in validated


def test_package_source_has_no_network_imports() -> None:
    forbidden_roots = {
        "http",
        "http.client",
        "httplib",
        "requests",
        "urllib",
        "urllib.request",
        "socket",
    }
    package_root = PROJECT_ROOT / "src/pit_manifest_validator_v1"
    for module_path in sorted(package_root.glob("*.py")):
        tree = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = {alias.name for alias in node.names}
            elif isinstance(node, ast.ImportFrom):
                names = {node.module or ""}
            else:
                continue
            assert not (names & forbidden_roots), module_path.name


def _package_tree_sha256() -> str:
    digest = hashlib.sha256()
    package_root = PROJECT_ROOT / "src/pit_manifest_validator_v1"
    for module_path in sorted(package_root.glob("*.py")):
        digest.update(module_path.name.encode("utf-8"))
        digest.update(hashlib.sha256(module_path.read_bytes()).digest())
    return digest.hexdigest()


def test_published_validator_package_tree_digest_matches() -> None:
    status = json.loads(
        (PROJECT_ROOT / "docs/track_a_pr2_public_status_v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert status["validator"]["package_tree_sha256"] == _package_tree_sha256()


def test_nfc_composed_and_decomposed_text_hash_equal() -> None:
    composed = "caf\u00e9"
    decomposed = unicodedata.normalize("NFD", composed)
    assert composed != decomposed
    assert nfc_text(decomposed, "label") == composed
    assert canonical_sha256({"label": nfc_text(decomposed, "label")}) == canonical_sha256(
        {"label": composed}
    )


def test_offset_timestamp_overflow_and_sentinel_fail_closed() -> None:
    freeze = deepcopy(_load_json(FREEZE_PATH))
    freeze["as_of_cutoff"] = "0001-01-01T00:00:00+23:59"
    _assert_error(lambda: project_freeze_record(freeze), "INVALID_TIMESTAMP")
    freeze["as_of_cutoff"] = "9998-12-31T23:59:59-23:59"
    _assert_error(lambda: project_freeze_record(freeze), "SENTINEL_TIMESTAMP")


def test_accepted_decision_cannot_outrank_diagnostic_findings() -> None:
    decision = deepcopy(_load_json(DECISION_PATH))
    decision["decision"] = "accepted"
    _assert_error(
        lambda: project_dataset_review_decision(decision, verify_digest=False),
        "DECISION_MORE_PERMISSIVE",
    )

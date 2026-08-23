"""Bundle child hashing and non-self-hashing manifest goldens."""

from __future__ import annotations

import inspect

from campaign.bundle import (
    assemble_evidence_bundle,
    invalid_and_missing_bytes,
    required_bundle_children,
)
from campaign_runner_v1_support import load_runner_fixture


def test_bundle_hashes_every_required_child_and_omits_self_hash() -> None:
    fixture = load_runner_fixture("bundle_assembly.json")
    children = {
        name: value.encode("utf-8")
        for name, value in fixture["inputs"]["children"].items()
    }
    assembly = assemble_evidence_bundle(children, fixture["inputs"]["root_fields"])
    expected = fixture["expected"]
    assert assembly.valid is expected["valid"]
    assert len(assembly.child_digests) == expected["child_count"]
    assert set(assembly.child_digests) == set(required_bundle_children())
    assert "bundle_manifest_sha256" not in assembly.bundle_manifest
    assert "self_sha256" not in assembly.bundle_manifest
    assert assembly.bundle_manifest_digest is not None
    assert assembly.detached_root is not None
    assert (
        assembly.detached_root["bundle_manifest_digest"]
        == assembly.bundle_manifest_digest
    )
    assert fixture["forbidden"]["bundle_manifest_self_hash"]


def test_missing_child_is_retained_as_invalid() -> None:
    fixture = load_runner_fixture("bundle_assembly.json")
    children = {
        name: value.encode("utf-8")
        for name, value in fixture["inputs"]["children"].items()
        if name != fixture["inputs"]["omit_child"]
    }
    assembly = assemble_evidence_bundle(children, fixture["inputs"]["root_fields"])
    assert assembly.valid is False
    assert assembly.reason == fixture["expected"]["missing_reason"]
    assert assembly.detached_root is None


def test_substituted_child_bytes_with_frozen_digests_are_invalid() -> None:
    fixture = load_runner_fixture("bundle_assembly.json")
    mutation = load_runner_fixture("bundle_child_digest_mismatch.json")
    children = {
        name: value.encode("utf-8")
        for name, value in fixture["inputs"]["children"].items()
    }
    matched = assemble_evidence_bundle(children, fixture["inputs"]["root_fields"])
    assert matched.valid is True
    for case in mutation["inputs"]["mutations"]:
        mutated = dict(children)
        mutated[case["child"]] = case["bytes"].encode("utf-8")
        assembly = assemble_evidence_bundle(
            mutated,
            fixture["inputs"]["root_fields"],
        )
        assert assembly.valid is mutation["expected"]["valid"], case
        assert assembly.reason == mutation["expected"]["reason"], case
        assert assembly.detached_root is None, case
    assert mutation["forbidden"]["accept_substituted_child_with_frozen_digest"]


def test_omitted_or_malformed_frozen_digest_fields_are_invalid() -> None:
    fixture = load_runner_fixture("bundle_assembly.json")
    mutation = load_runner_fixture("bundle_child_digest_mismatch.json")
    children = {
        name: value.encode("utf-8")
        for name, value in fixture["inputs"]["children"].items()
    }
    for case in mutation["inputs"]["omit_field_cases"]:
        root_fields = dict(fixture["inputs"]["root_fields"])
        for field in case["fields"]:
            del root_fields[field]
        assembly = assemble_evidence_bundle(children, root_fields)
        assert assembly.valid is mutation["expected"]["omit_valid"], case
        assert assembly.reason == mutation["expected"]["omit_reason"], case
        assert assembly.detached_root is None, case
    for case in mutation["inputs"]["malformed_digest_cases"]:
        root_fields = dict(fixture["inputs"]["root_fields"])
        root_fields[case["field"]] = case["value"]
        assembly = assemble_evidence_bundle(children, root_fields)
        assert assembly.valid is mutation["expected"]["malformed_valid"], case
        assert assembly.reason == mutation["expected"]["malformed_reason"], case
        assert assembly.detached_root is None, case
    assert mutation["forbidden"]["accept_bundle_when_frozen_digest_omitted"]


def test_missing_or_malformed_root_bindings_are_invalid() -> None:
    fixture = load_runner_fixture("bundle_assembly.json")
    mutation = load_runner_fixture("bundle_root_binding_missing.json")
    children = {
        name: value.encode("utf-8")
        for name, value in fixture["inputs"]["children"].items()
    }
    for field in mutation["inputs"]["required_fields"]:
        root_fields = dict(fixture["inputs"]["root_fields"])
        del root_fields[field]
        assembly = assemble_evidence_bundle(children, root_fields)
        assert assembly.valid is mutation["expected"]["valid"], field
        assert assembly.reason == mutation["expected"]["reason"], field
        assert assembly.detached_root is None, field
    for field in mutation["inputs"]["null_fields"]:
        root_fields = dict(fixture["inputs"]["root_fields"])
        root_fields[field] = None
        assembly = assemble_evidence_bundle(children, root_fields)
        assert assembly.valid is mutation["expected"]["valid"], field
        assert assembly.reason == mutation["expected"]["reason"], field
        assert assembly.detached_root is None, field
    for case in mutation["inputs"]["malformed_cases"]:
        root_fields = dict(fixture["inputs"]["root_fields"])
        root_fields[case["field"]] = case["value"]
        assembly = assemble_evidence_bundle(children, root_fields)
        assert assembly.valid is mutation["expected"]["valid"], case
        assert assembly.reason == mutation["expected"]["reason"], case
        assert assembly.detached_root is None, case
    assert mutation["forbidden"]["accept_bundle_with_none_root_bindings"]


def test_per_trial_status_must_cover_every_inventory_trial() -> None:
    fixture = load_runner_fixture("bundle_assembly.json")
    mutation = load_runner_fixture("bundle_per_trial_status.json")
    children = {
        name: value.encode("utf-8")
        for name, value in fixture["inputs"]["children"].items()
    }
    valid = assemble_evidence_bundle(children, fixture["inputs"]["root_fields"])
    assert valid.valid is True
    assert valid.detached_root is not None
    assert (
        len(valid.detached_root["per_trial_status"])
        == fixture["inputs"]["root_fields"]["semantic_trial_count"]
    )
    for name in ("empty", "short", "duplicate", "unknown"):
        root_fields = dict(fixture["inputs"]["root_fields"])
        root_fields["per_trial_status"] = mutation["inputs"][name]
        assembly = assemble_evidence_bundle(children, root_fields)
        assert assembly.valid is mutation["expected"]["valid"], name
        assert assembly.reason == mutation["expected"]["reason"], name
        assert assembly.detached_root is None, name
    assert mutation["forbidden"]["accept_empty_per_trial_status"]


def test_bundle_functions_have_no_defaults() -> None:
    for function in (
        assemble_evidence_bundle,
        invalid_and_missing_bytes,
        required_bundle_children,
    ):
        for parameter in inspect.signature(function).parameters.values():
            assert parameter.default is inspect.Parameter.empty

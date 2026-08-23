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


def test_bundle_without_carried_child_digests_still_assembles() -> None:
    fixture = load_runner_fixture("bundle_assembly.json")
    mutation = load_runner_fixture("bundle_child_digest_mismatch.json")
    children = {
        name: value.encode("utf-8")
        for name, value in fixture["inputs"]["children"].items()
    }
    root_fields = dict(fixture["inputs"]["root_fields"])
    for field in mutation["inputs"]["omit_fields"]:
        del root_fields[field]
    assembly = assemble_evidence_bundle(children, root_fields)
    assert assembly.valid is mutation["expected"]["omit_valid"]
    assert assembly.reason is None
    assert assembly.detached_root is not None


def test_bundle_functions_have_no_defaults() -> None:
    for function in (
        assemble_evidence_bundle,
        invalid_and_missing_bytes,
        required_bundle_children,
    ):
        for parameter in inspect.signature(function).parameters.values():
            assert parameter.default is inspect.Parameter.empty

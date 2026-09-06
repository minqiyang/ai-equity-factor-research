"""Registry 0.10.0 ACCESS promotion for Path A. Prior releases stay immutable."""

from copy import deepcopy
import hashlib
from importlib import resources
import json
from pathlib import Path

import pytest

from ledger.schema_registry import (
    LedgerSchemaError,
    load_default_registry,
    load_registry_release,
    registry_digest,
    run_conformance_vectors,
    validate_event,
    validate_raw_event_bytes,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = PROJECT_ROOT / "src/ledger/schemas"
REGISTRY_PATHS = tuple(
    SCHEMA_ROOT
    / f"experiment_trial_ledger_payload_schema_registry_v{version}.json"
    for version in range(1, 11)
)
DIGEST_PATHS = tuple(path.with_suffix(".sha256") for path in REGISTRY_PATHS)
FIXTURE_PATH = (
    PROJECT_ROOT
    / "tests/fixtures/experiment_trial_ledger_access_events_v1_golden.json"
)
EXPECTED_RAW_HASHES = (
    "4b78c36647621deaec15114558d827c17dae2bfa29918f4cbf2ceb2aa6b6e6d9",
    "d31b7a812a79618f097a50db0177e63f5246522b3b63590968172e31b71cd499",
    "1d36c3cc5d608209cb431a9a768a1f95e24cb73f64745199670b175ffa6758dd",
    "1562852a4b95f867f7843818f31a0672949afb187ef84291ccac030e105ef46d",
    "223a2b7e2ff8ffdb4977c878186236cd747428838bade571e43e513e71ee52b2",
    "162e20df0b7cfb4e07abb818ccf87160d007eced7f90faeefe0d20831fd7229c",
    "3b90c79f13caa85812d1e42a6964f4d4216632d54cc8c481102945e0127f63c9",
    "455782c8c18f187f0209f2e20af92f10648180dabc422cc0e975d270877bfeff",
    "865b882a4b905158adae8165ca1d4fa66299e2b2d9f889a1ed9f181a8a662525",
    "a81c061bfdd7a27d0922fc6449b1c6634ecb65f03a2dfa309f740b519806ee6d",
)
EXPECTED_SIDECAR_RAW_HASHES = (
    "dc870da2958a107998d3939350edb20d3a9185e13a4edb48664befcb89e79d51",
    "ba6b1682d1a22004618c274b362359123ce7abbcb7b211335dcd4c74b1159ac8",
    "d9491f211a4e7d84777c82cdb6af716f4e4422ed57624a0cbff1f713bc8f8fce",
    "fc34bc6d5183fc977e863fda183b40fd4252bed073cfa04e567cb784aa0b7845",
    "dceb0f334fe2056ae0d3a673e499caa899d69d67b60a21b2380d0ea947427483",
    "8322d6c509797710e5f8d7c85d5406202535b878c88ddf05f83525bbaa83db46",
    "111730a1739e91b2a72efef0e7616b4aee6bafbbf15fe77628f268c19d7f4317",
    "eafd6a98b82ae248c89d94667d278507d43045f8eaf8854cc351d81a95a16c6a",
    "da84c385bd60ef91cf051cc03a53860a3190d23630040fa97d6763d1c03576c9",
    "b845aab06077c53d0fcc86fef45c48e0463b3384abfb50378538764e9db87d12",
)
EXPECTED_CANONICAL_HASHES = (
    "92ab88b0bac4c683c25aab25dd31f6a48f44250afbef7d4995de26b68451e2cf",
    "6c1044a1a5d770b8d841164d0232134e975c8c372e7d62333eac3a8ae2eacab4",
    "d0e3c08ed5699c8fd6078afb6d7c0a513bbc20b306bad630b175abd09e695f85",
    "3a1c17be6dc6d20f512429b4ff2457be4f28472050a99a5f97eee16a9dd57ab4",
    "c6fed9409f596cae5cdba1bce3ad8c5b088d2931361aeda7c06dfd2453805a52",
    "acada613202d7ab3a96380ea70ba9bbfeffe7c401bf998828a39528db3ad8691",
    "1d85424d1ee60dcc9523a52c56b22080b47aebb4275551a7ea9ee38e8e28d710",
    "3c71399f9ee8de51b6bd401dc409865c672d12a97cc00057c6de26445c0c538f",
    "1a58c069098921a8446fd2e0452fe544e7c56e8f9e5ff392ff201cb5c177503a",
    "0e0e1ab44976db3882ce9dfd1aa656b50bd92afe22b6d645b9b38c519e0e1bfd",
)
EXPECTED_SUPPORTED_EVENTS = (
    "LEDGER_EPOCH_CREATED",
    "CAMPAIGN_ALLOCATED",
    "EXPERIMENT_ALLOCATED",
    "TRIAL_FAMILY_REGISTERED",
    "SAMPLE_REGISTERED",
    "CAMPAIGN_ENTITY_BOUND",
    "STAGE3_SAMPLE_REFERENCE_BOUND",
    "TRIAL_ALLOCATED",
    "CAMPAIGN_INVENTORY_SEALED",
    "ATTEMPT_ALLOCATED",
    "ATTEMPT_STARTED",
    "ACCESS_INTENT",
    "ACCESS_STARTED",
    "ACCESS_COMPLETED",
)


def _assert_code(code: str, callback) -> None:
    with pytest.raises(LedgerSchemaError) as raised:
        callback()
    assert raised.value.code == code


def test_v10_release_preserves_prior_releases_and_promotes_access() -> None:
    versions = tuple(
        "0.10.0" if minor == 10 else f"0.{minor}.0" for minor in range(1, 11)
    )
    releases = tuple(load_registry_release(version) for version in versions)
    prior = releases[-2]
    current = releases[-1]

    assert load_default_registry() == releases[0]
    assert tuple(item["registry_version"] for item in releases) == versions
    assert current["registry_status"] == "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY"
    assert current["schema_language_version"] == "0.2.0"
    assert current["closed_event_vocabulary"] == prior["closed_event_vocabulary"]
    assert tuple(entry["event_type"] for entry in current["event_schemas"]) == (
        EXPECTED_SUPPORTED_EVENTS
    )
    assert current["event_schemas"][:11] == prior["event_schemas"]
    assert current["type_definitions"]["access_capability_id"] == {
        "kind": "typed_id",
        "prefix": "cap",
    }
    assert len(current["incomplete_event_types"]) == 23
    assert set(current["incomplete_event_types"]).isdisjoint(EXPECTED_SUPPORTED_EVENTS)

    prior_vectors = {vector["vector_id"]: vector for vector in prior["conformance_vectors"]}
    current_vectors = {
        vector["vector_id"]: vector for vector in current["conformance_vectors"]
    }
    assert set(current_vectors) - set(prior_vectors) == {
        "access_intent_valid",
        "access_intent_subject_mismatch",
        "access_started_valid",
        "access_started_subject_mismatch",
        "access_completed_valid",
        "access_completed_subject_mismatch",
    }
    for vector_id in prior_vectors:
        assert current_vectors[vector_id] == prior_vectors[vector_id]

    for release, expected in zip(releases, EXPECTED_CANONICAL_HASHES, strict=True):
        assert registry_digest(release) == expected
    for path, expected in zip(DIGEST_PATHS, EXPECTED_CANONICAL_HASHES, strict=True):
        assert path.read_text(encoding="ascii").strip() == expected
    for path, expected in zip(REGISTRY_PATHS, EXPECTED_RAW_HASHES, strict=True):
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
    for path, expected in zip(DIGEST_PATHS, EXPECTED_SIDECAR_RAW_HASHES, strict=True):
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected

    fixture = json.loads(FIXTURE_PATH.read_text(encoding="ascii"))
    for event_type in ("ACCESS_INTENT", "ACCESS_STARTED", "ACCESS_COMPLETED"):
        event = fixture[event_type.lower()]
        assert validate_event(event, registry=current) == event
        _assert_code(
            "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY",
            lambda event=event, prior=prior: validate_event(event, registry=prior),
        )


def test_v10_package_resources_match_source_releases() -> None:
    packaged = resources.files("ledger").joinpath("schemas")
    for path in (*REGISTRY_PATHS, *DIGEST_PATHS):
        assert packaged.joinpath(path.name).read_bytes() == path.read_bytes()


def test_v10_conformance_vectors_include_access_outcomes() -> None:
    outcomes = run_conformance_vectors(load_registry_release("0.10.0"))
    assert outcomes["access_intent_valid"] == "ACCEPT"
    assert outcomes["access_intent_subject_mismatch"] == "INVALID_EVENT"
    assert outcomes["access_started_valid"] == "ACCEPT"
    assert outcomes["access_completed_valid"] == "ACCEPT"
    assert outcomes["known_incomplete_amendment_proposed"] == (
        "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY"
    )


def test_v10_access_payloads_are_closed_and_subject_bound() -> None:
    registry = load_registry_release("0.10.0")
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="ascii"))
    intent = deepcopy(fixture["access_intent"])
    intent["payload"]["purpose"] = "design"
    _assert_code(
        "INVALID_EVENT",
        lambda: validate_event(intent, registry=registry),
    )
    started = deepcopy(fixture["access_started"])
    started["payload"]["evidence_ref_ids"] = []
    _assert_code(
        "INVALID_EVENT",
        lambda: validate_event(started, registry=registry),
    )
    raw = json.dumps(fixture["access_intent"], separators=(",", ":")).encode("ascii")
    assert validate_raw_event_bytes(raw, registry=registry)["event_type"] == (
        "ACCESS_INTENT"
    )

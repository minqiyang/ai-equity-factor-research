"""T-1 through T-8 and registry-bound factor goldens."""

from __future__ import annotations

import dataclasses
import hashlib
from pathlib import Path
from types import MappingProxyType

import math
import pytest

from campaign.inference import FACTOR_ORDER, FactorVector
from campaign.registry import (
    FACTOR_REGISTRY,
    FactorSpec,
    compute_registered_factor,
    factor_spec,
)
from campaign_runner_v1_support import (
    CAMPAIGN_ROOT,
    collect_disallowed_factor_id_literals,
    decode_fixture_anchor,
    load_runner_fixture,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_t1_registry_keys_equal_owner_tuple() -> None:
    assert tuple(FACTOR_REGISTRY) == FACTOR_ORDER


def test_t2_factor_vector_fields_equal_owner_tuple() -> None:
    assert (
        tuple(field.name for field in dataclasses.fields(FactorVector))
        == FACTOR_ORDER
    )


def test_t3_compute_callables_are_unique() -> None:
    computes = tuple(spec.compute for spec in FACTOR_REGISTRY.values())
    assert len(computes) == len(FACTOR_ORDER)
    assert len(set(computes)) == len(computes)


def test_t4_lookup_is_exact_key_and_raises_on_unknown() -> None:
    fixture = load_runner_fixture("unknown_factor_lookup.json")
    for factor_id in FACTOR_ORDER:
        assert factor_spec(factor_id).factor_id == factor_id
    with pytest.raises(KeyError):
        factor_spec(fixture["inputs"]["factor_id"])


def test_t5_registry_and_spec_are_immutable() -> None:
    assert isinstance(FACTOR_REGISTRY, MappingProxyType)
    spec = next(iter(FACTOR_REGISTRY.values()))
    assert isinstance(spec, FactorSpec)
    with pytest.raises(TypeError):
        FACTOR_REGISTRY[FACTOR_ORDER[0]] = spec
    with pytest.raises(dataclasses.FrozenInstanceError):
        spec.direction = spec.direction


def test_t6_registry_binding_golden() -> None:
    fixture = load_runner_fixture("registry_binding_golden.json")
    for row in fixture["expected"]["rows"]:
        spec = factor_spec(FACTOR_ORDER[row["owner_index"]])
        assert spec.factor_id == FACTOR_ORDER[row["owner_index"]]
        assert spec.factor_id == row["factor_id"]
        assert spec.compute_qualname() == row["compute"]
        assert (
            spec.lookback_common_calendar_positions
            == row["lookback_common_calendar_positions"]
        )
        assert spec.referenced_anchor_offsets == (
            None
            if row["referenced_anchor_offsets"] is None
            else tuple(row["referenced_anchor_offsets"])
        )
        assert spec.required_history_price_anchor_span == (
            None
            if row["required_history_price_anchor_span"] is None
            else tuple(row["required_history_price_anchor_span"])
        )
        assert spec.required_anchor_count == row["required_anchor_count"]
        assert spec.direction == row["direction"]
        assert spec.anchor_lineage_policy == row["anchor_lineage_policy"]
    for pairing in fixture["forbidden"]["pairings"]:
        spec = factor_spec(FACTOR_ORDER[pairing["owner_index"]])
        assert spec.compute_qualname() != pairing["compute"]


def test_t7_owner_uniqueness_conformance_scan() -> None:
    assert collect_disallowed_factor_id_literals(FACTOR_ORDER) == ()
    assert (CAMPAIGN_ROOT / "inference.py").is_file()


def test_t8_owner_file_bytes_unchanged() -> None:
    fixture = load_runner_fixture("reuse_as_is_file_bytes.json")
    for relative_path, expected in fixture["expected"]["file_bytes"].items():
        digest = hashlib.sha256(
            (PROJECT_ROOT / relative_path).read_bytes()
        ).hexdigest()
        assert digest == expected


def test_momentum_golden_through_registry() -> None:
    fixture = load_runner_fixture("momentum_golden.json")
    result = compute_registered_factor(
        FACTOR_ORDER[fixture["inputs"]["owner_index"]],
        fixture["inputs"]["anchors"],
    )
    assert result.valid is fixture["expected"]["valid"]
    assert result.reason is fixture["expected"]["reason"]
    assert result.value is not None
    assert math.isclose(
        result.value,
        fixture["expected"]["value"],
        rel_tol=fixture["expected"]["rel_tol"],
        abs_tol=fixture["expected"]["abs_tol"],
    )


def test_reversal_golden_through_registry() -> None:
    fixture = load_runner_fixture("reversal_golden.json")
    result = compute_registered_factor(
        FACTOR_ORDER[fixture["inputs"]["owner_index"]],
        fixture["inputs"]["anchors"],
    )
    assert result.valid is fixture["expected"]["valid"]
    assert result.reason is fixture["expected"]["reason"]
    assert result.value is not None
    assert math.isclose(
        result.value,
        fixture["expected"]["value"],
        rel_tol=fixture["expected"]["rel_tol"],
        abs_tol=fixture["expected"]["abs_tol"],
    )


def test_low_vol_golden_through_registry() -> None:
    fixture = load_runner_fixture("low_vol_golden.json")
    result = compute_registered_factor(
        FACTOR_ORDER[fixture["inputs"]["owner_index"]],
        fixture["inputs"]["anchors"],
    )
    expected = fixture["expected"]
    assert result.valid is expected["valid"]
    assert result.reason is expected["reason"]
    assert result.value is not None
    assert math.isclose(
        result.value,
        expected["value"],
        rel_tol=expected["rel_tol"],
        abs_tol=expected["abs_tol"],
    )
    assert result.value != fixture["forbidden"]["log_return_value"]


def test_anchor_mutation_matrix_is_invalid_missing() -> None:
    fixture = load_runner_fixture("anchor_mutation_matrix.json")
    for case in fixture["inputs"]["cases"]:
        for position in case["positions"]:
            for kind in fixture["inputs"]["kinds"]:
                anchors = list(case["valid_anchors"])
                anchors[position] = decode_fixture_anchor(kind)
                result = compute_registered_factor(
                    FACTOR_ORDER[case["owner_index"]],
                    anchors,
                )
                assert result.valid is fixture["expected"]["valid"]
                assert result.value is fixture["expected"]["value"]
                assert result.reason == kind["reason"]


def test_low_vol_anchor_count_matrix_is_invalid_missing() -> None:
    fixture = load_runner_fixture("low_vol_anchor_count_matrix.json")
    valid = fixture["inputs"]["valid_anchors"]
    for count in fixture["inputs"]["counts"]:
        result = compute_registered_factor(
            FACTOR_ORDER[fixture["inputs"]["owner_index"]],
            valid[:count] if count < len(valid) else valid + [valid[-1]],
        )
        assert result.valid is fixture["expected"]["valid"]
        assert result.value is fixture["expected"]["value"]
        assert result.reason == fixture["expected"]["reason"]


def test_interior_missing_momentum_remains_valid() -> None:
    fixture = load_runner_fixture("interior_missing_momentum.json")
    result = compute_registered_factor(
        FACTOR_ORDER[fixture["inputs"]["owner_index"]],
        fixture["inputs"]["referenced_anchors"],
    )
    assert result.valid is fixture["expected"]["valid"]
    assert result.value is not None
    assert math.isclose(
        result.value,
        fixture["expected"]["value"],
        rel_tol=fixture["expected"]["rel_tol"],
        abs_tol=fixture["expected"]["abs_tol"],
    )
    assert fixture["inputs"]["interior_missing"]
    assert fixture["forbidden"]["full_window_contiguity_rejection"]


def test_interior_missing_reversal_remains_valid() -> None:
    fixture = load_runner_fixture("interior_missing_reversal.json")
    result = compute_registered_factor(
        FACTOR_ORDER[fixture["inputs"]["owner_index"]],
        fixture["inputs"]["referenced_anchors"],
    )
    assert result.valid is fixture["expected"]["valid"]
    assert result.value is not None
    assert math.isclose(
        result.value,
        fixture["expected"]["value"],
        rel_tol=fixture["expected"]["rel_tol"],
        abs_tol=fixture["expected"]["abs_tol"],
    )
    assert fixture["inputs"]["interior_missing"]
    assert fixture["forbidden"]["full_window_contiguity_rejection"]

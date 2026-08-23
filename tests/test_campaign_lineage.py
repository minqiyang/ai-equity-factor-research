"""Accepted-rename, reused-ticker, and staggered key-freeze fixtures."""

from __future__ import annotations

from copy import deepcopy

import math

from campaign.inference import FACTOR_ORDER
from campaign.lineage import (
    evaluate_factor_anchor_lineage_v1,
    freeze_listing_lineage_key,
)
from campaign.listing_key import encode_listing_lineage_key_v1
from campaign.registry import compute_registered_factor
from campaign_runner_v1_support import load_runner_fixture


def test_accepted_rename_retains_momentum_and_rejects_gap() -> None:
    fixture = load_runner_fixture("accepted_rename.json")
    inputs = fixture["inputs"]
    verdict = evaluate_factor_anchor_lineage_v1(
        inputs["anchors"],
        inputs["target_identity"],
        inputs["alias_chain"],
    )
    result = compute_registered_factor(
        FACTOR_ORDER[inputs["owner_index"]],
        inputs["referenced_anchors"],
    )
    assert verdict.valid is fixture["expected"]["lineage_valid"]
    assert verdict.reason is fixture["expected"]["reason"]
    assert result.value is not None
    assert math.isclose(
        result.value,
        fixture["expected"]["value"],
        rel_tol=fixture["expected"]["rel_tol"],
        abs_tol=fixture["expected"]["abs_tol"],
    )

    gapped_chain = deepcopy(inputs["alias_chain"])
    gapped_chain[1]["alias_effective_from"] = inputs["gapped_next_from"]
    gapped = evaluate_factor_anchor_lineage_v1(
        inputs["anchors"],
        inputs["target_identity"],
        gapped_chain,
    )
    assert gapped.valid is not fixture["forbidden"]["gapped_lineage_valid"]


def test_reused_ticker_rejects_ticker_only_join() -> None:
    fixture = load_runner_fixture("reused_ticker.json")
    inputs = fixture["inputs"]
    verdict = evaluate_factor_anchor_lineage_v1(
        inputs["anchors"],
        inputs["target_identity"],
        inputs["alias_chain"],
    )
    ticker_only = (
        float(inputs["anchors"][1]["adjusted_close"])
        / float(inputs["anchors"][0]["adjusted_close"])
        - 1.0
    )
    assert ticker_only == fixture["forbidden"]["ticker_only_join_value"]
    assert verdict.valid is fixture["expected"]["lineage_valid"]
    assert verdict.reason == fixture["expected"]["reason"]


def test_staggered_key_freeze_keeps_null_endpoint() -> None:
    fixture = load_runner_fixture("staggered_key_freeze.json")
    inputs = fixture["inputs"]
    frozen = freeze_listing_lineage_key(
        inputs["exchange"],
        inputs["ticker"],
        inputs["effective_from"],
        inputs["first_eligibility_dates"],
        inputs["endpoint_known_date"],
        inputs["endpoint_date"],
    )
    expected = encode_listing_lineage_key_v1(
        inputs["exchange"],
        inputs["ticker"],
        inputs["effective_from"],
        fixture["expected"]["effective_to"],
    )
    forbidden = encode_listing_lineage_key_v1(
        inputs["exchange"],
        inputs["ticker"],
        inputs["effective_from"],
        fixture["forbidden"]["effective_to"],
    )
    assert frozen == expected
    assert frozen != forbidden

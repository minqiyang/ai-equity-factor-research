"""Decision-time eligibility reasons, triggers, and frozen targets."""

from __future__ import annotations

import inspect
import math

from campaign.eligibility import (
    evaluate_decision_time_listings,
    freeze_decision_time,
)
from campaign.inference import FACTOR_ORDER
from campaign_runner_v1_support import (
    encode_runner_listing_key,
    expand_decision_time_listings,
    listing_decisions_from_numeric_spec,
    load_runner_fixture,
)


def test_decision_time_listing_reasons_are_counted_and_retained() -> None:
    fixture = load_runner_fixture("decision_time_listing_reasons.json")
    inputs = fixture["inputs"]
    listings = expand_decision_time_listings(inputs)
    decisions = evaluate_decision_time_listings(
        listings,
        FACTOR_ORDER[inputs["owner_index"]],
    )
    expected_cases = fixture["expected"]["cases"]
    for row, decision in zip(inputs["rows"], decisions, strict=True):
        expected = expected_cases[row["name"]]
        assert decision.eligible is expected["eligible"]
        assert decision.reason == expected["reason"]
        if expected["value"] is None:
            assert decision.factor_value is None
        else:
            assert decision.factor_value is not None
            assert math.isclose(
                decision.factor_value,
                expected["value"],
                rel_tol=fixture["expected"]["rel_tol"],
                abs_tol=fixture["expected"]["abs_tol"],
            )
    reused = expected_cases["reused_ticker"]
    assert reused["value"] != fixture["forbidden"]["reused_ticker_ticker_only_join_value"]
    assert expected_cases["interior_missing_still_eligible"]["eligible"]
    assert fixture["forbidden"]["interior_missing_full_window_rejection"]
    mismatched = expected_cases["mismatched_referenced_prices"]
    assert mismatched["eligible"] is False
    assert mismatched["value"] != fixture["forbidden"]["unbound_referenced_price_value"]


def test_zero_target_trigger_matrix() -> None:
    fixture = load_runner_fixture("zero_target_trigger_matrix.json")
    inputs = fixture["inputs"]
    for case in inputs["cases"]:
        spec = {
            "key_spec": inputs["key_spec"],
            "count": case["count"],
            "value_mode": case["value_mode"],
            "constant_value": case.get("constant_value"),
            "duplicate_last": case["duplicate_last"],
        }
        frozen = freeze_decision_time(
            listing_decisions_from_numeric_spec(spec),
            inputs["min_eligible_count"],
            inputs["min_distinct_values"],
        )
        expected = fixture["expected"]["cases"][case["name"]]
        assert frozen.zero_target_triggers == tuple(expected["triggers"])
        assert frozen.invalid_factor_month is expected["invalid_factor_month"]
        assert (not frozen.long_only_target) is expected["long_only_empty"]
        assert frozen.benchmark_formable is expected["benchmark_formable"]
        assert len(frozen.matched_benchmark_target) == expected["benchmark_count"]
        if "benchmark_weight" in expected:
            assert set(frozen.matched_benchmark_target.values()) == {
                expected["benchmark_weight"]
            }


def test_valid_top_decile_target_uses_remainder_first_high_chunk() -> None:
    fixture = load_runner_fixture("valid_top_decile_target.json")
    inputs = fixture["inputs"]
    frozen = freeze_decision_time(
        listing_decisions_from_numeric_spec(inputs),
        inputs["min_eligible_count"],
        inputs["min_distinct_values"],
    )
    expected = fixture["expected"]
    key_spec = inputs["key_spec"]
    selected = tuple(
        encode_runner_listing_key(
            key_spec["exchange"],
            ticker,
            key_spec["effective_from"],
            key_spec["effective_to"],
        )
        for ticker in expected["top_decile_tickers"]
    )
    forbidden = tuple(
        encode_runner_listing_key(
            key_spec["exchange"],
            ticker,
            key_spec["effective_from"],
            key_spec["effective_to"],
        )
        for ticker in fixture["forbidden"]["last_chunk_tickers"]
    )
    assert frozen.zero_target_triggers == tuple(expected["triggers"])
    assert frozen.invalid_factor_month is expected["invalid_factor_month"]
    assert len(frozen.ordered_eligible) == expected["eligible_count"]
    assert tuple(frozen.long_only_target) == tuple(sorted(selected))
    assert set(frozen.long_only_target.values()) == {expected["long_only_weight"]}
    assert tuple(frozen.long_only_target) != forbidden
    assert frozen.factor_ranks[0][0] == encode_runner_listing_key(
        key_spec["exchange"],
        expected["first_rank_ticker"],
        key_spec["effective_from"],
        key_spec["effective_to"],
    )
    assert frozen.factor_ranks[-1][0] == encode_runner_listing_key(
        key_spec["exchange"],
        expected["last_rank_ticker"],
        key_spec["effective_from"],
        key_spec["effective_to"],
    )
    assert len(frozen.matched_benchmark_target) == expected["benchmark_count"]
    assert set(frozen.matched_benchmark_target.values()) == {
        expected["benchmark_weight"]
    }


def test_mismatched_factor_prices_are_invalid() -> None:
    fixture = load_runner_fixture("factor_anchor_price_mismatch.json")
    inputs = fixture["inputs"]
    listings = expand_decision_time_listings(inputs)
    decisions = evaluate_decision_time_listings(
        listings,
        FACTOR_ORDER[inputs["owner_index"]],
    )
    expected_cases = fixture["expected"]["cases"]
    for row, decision in zip(inputs["rows"], decisions, strict=True):
        expected = expected_cases[row["name"]]
        assert decision.eligible is expected["eligible"]
        assert decision.reason == expected["reason"]
        if expected["value"] is None:
            assert decision.factor_value is None
        else:
            assert decision.factor_value is not None
            assert math.isclose(
                decision.factor_value,
                expected["value"],
                rel_tol=fixture["expected"]["rel_tol"],
                abs_tol=fixture["expected"]["abs_tol"],
            )
    assert fixture["forbidden"]["compute_from_unbound_referenced_prices"]
    first = expected_cases["mismatched_first"]
    last = expected_cases["mismatched_last"]
    assert first["value"] != fixture["forbidden"]["unbound_first_value"]
    assert last["value"] != fixture["forbidden"]["unbound_last_value"]


def test_freeze_decision_time_has_no_semantic_defaults() -> None:
    for parameter in inspect.signature(freeze_decision_time).parameters.values():
        assert parameter.default is inspect.Parameter.empty

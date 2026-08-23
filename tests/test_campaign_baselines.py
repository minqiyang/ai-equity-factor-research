"""Equal-weight reuse, random-rank permutation, and episode return goldens."""

from __future__ import annotations

import math

import pytest

from campaign.baselines import (
    episode_gross_return,
    equal_weight_universe_target,
    random_rank_target,
)
from campaign.inference import FACTOR_ORDER
from campaign.returns import simple_adjusted_close_return
from campaign_runner_v1_support import (
    encode_runner_listing_key,
    freeze_numeric_universe,
    load_runner_fixture,
)


def test_random_rank_non_divisible_permutation_and_no_rng_on_invalid() -> None:
    fixture = load_runner_fixture("random_rank_non_divisible.json")
    inputs = fixture["inputs"]
    expected = fixture["expected"]
    factor_id = FACTOR_ORDER[inputs["owner_index"]]
    frozen = freeze_numeric_universe(
        inputs["valid_universe"],
        inputs["min_eligible_count"],
        inputs["min_distinct_values"],
        factor_id,
        inputs["signal_date"],
    )
    result = random_rank_target(
        frozen,
        factor_id,
        inputs["signal_date"],
        inputs["scheme_id"],
        inputs["seed_version"],
        inputs["generator_name"],
    )
    key_spec = inputs["valid_universe"]["key_spec"]
    selected = tuple(
        encode_runner_listing_key(
            key_spec["exchange"],
            ticker,
            key_spec["effective_from"],
            key_spec["effective_to"],
        )
        for ticker in expected["selected_tickers_in_permutation_order"]
    )
    last_chunk = tuple(
        encode_runner_listing_key(
            key_spec["exchange"],
            ticker,
            key_spec["effective_from"],
            key_spec["effective_to"],
        )
        for ticker in fixture["forbidden"]["last_chunk_tickers"]
    )
    assert result.preimage == expected["preimage"]
    assert result.preimage_sha256 == expected["preimage_sha256"]
    assert result.seed == expected["seed"]
    assert result.permutation == tuple(expected["permutation"])
    assert result.selected_keys == selected
    assert result.selected_keys != last_chunk
    assert len(result.selected_keys) != fixture["forbidden"]["floor_only_size"]
    assert result.consumed_rng is expected["consumed_rng"]
    assert result.formable is expected["formable"]
    assert set(result.weights.values()) == {expected["weight"]}
    assert tuple(result.weights) == tuple(sorted(selected))

    with pytest.raises(ValueError, match="signal_date"):
        random_rank_target(
            frozen,
            factor_id,
            inputs["forbidden_execution_date"],
            inputs["scheme_id"],
            inputs["seed_version"],
            inputs["generator_name"],
        )
    with pytest.raises(ValueError, match="factor_id"):
        random_rank_target(
            frozen,
            FACTOR_ORDER[1],
            inputs["signal_date"],
            inputs["scheme_id"],
            inputs["seed_version"],
            inputs["generator_name"],
        )
    assert result.preimage == (
        f"{inputs['scheme_id']}|{inputs['seed_version']}|"
        f"{frozen.factor_id}|{frozen.signal_date}"
    )
    assert inputs["forbidden_execution_date"] not in result.preimage

    invalid = random_rank_target(
        freeze_numeric_universe(
            inputs["invalid_universe"],
            inputs["min_eligible_count"],
            inputs["min_distinct_values"],
            factor_id,
            inputs["signal_date"],
        ),
        factor_id,
        inputs["signal_date"],
        inputs["scheme_id"],
        inputs["seed_version"],
        inputs["generator_name"],
    )
    assert invalid.consumed_rng is expected["invalid_consumed_rng"]
    assert invalid.formable is expected["invalid_formable"]
    assert invalid.permutation is None
    assert invalid.seed is None
    assert dict(invalid.weights) == {}


def test_equal_weight_reuses_frozen_benchmark_not_zero_target() -> None:
    fixture = load_runner_fixture("equal_weight_reuses_benchmark.json")
    inputs = fixture["inputs"]
    tied = freeze_numeric_universe(
        inputs["tied_universe"],
        inputs["min_eligible_count"],
        inputs["min_distinct_values"],
        FACTOR_ORDER[0],
        inputs["signal_date"],
    )
    equal_weight = equal_weight_universe_target(tied, inputs["role"])
    expected = fixture["expected"]["tied"]
    assert equal_weight.role == inputs["role"]
    assert equal_weight.weights is tied.matched_benchmark_target
    assert equal_weight.formable is expected["formable"]
    assert len(equal_weight.weights) == expected["count"]
    assert set(equal_weight.weights.values()) == {expected["weight"]}
    assert (not tied.long_only_target) is expected["factor_target_empty"]
    assert dict(equal_weight.weights) != dict(tied.long_only_target)
    assert fixture["forbidden"]["reuse_factor_zero_target_when_invested"]

    empty = freeze_numeric_universe(
        inputs["empty_universe"],
        inputs["min_eligible_count"],
        inputs["min_distinct_values"],
        FACTOR_ORDER[0],
        inputs["signal_date"],
    )
    empty_target = equal_weight_universe_target(empty, inputs["role"])
    assert empty_target.formable is fixture["expected"]["empty"]["formable"]
    assert len(empty_target.weights) == fixture["expected"]["empty"]["count"]
    assert empty_target.weights is empty.matched_benchmark_target


def test_episode_short_month_is_static_not_continuous_slice() -> None:
    fixture = load_runner_fixture("episode_short_month.json")
    inputs = fixture["inputs"]
    expected = fixture["expected"]
    weights = {}
    constituent_returns = {}
    observed = []
    for row, weight in zip(
        inputs["constituents"],
        inputs["weights"],
        strict=True,
    ):
        listing_key = encode_runner_listing_key(
            inputs["exchange"],
            row["ticker"],
            inputs["effective_from"],
            inputs["effective_to"],
        )
        result = simple_adjusted_close_return(
            row["start_anchor"],
            row["end_anchor"],
            row["anchors"],
            row["target_identity"],
            row["alias_chain"],
        )
        assert result.valid
        assert result.value is not None
        observed.append(result.value)
        weights[listing_key] = weight
        constituent_returns[listing_key] = result.value
    episode = episode_gross_return(weights, constituent_returns)
    for observed_return, expected_return in zip(
        observed,
        expected["constituent_returns"],
        strict=True,
    ):
        assert math.isclose(
            observed_return,
            expected_return,
            rel_tol=expected["rel_tol"],
            abs_tol=expected["abs_tol"],
        )
    assert episode.valid is expected["valid"]
    assert episode.reason is expected["reason"]
    assert episode.value is not None
    assert math.isclose(
        episode.value,
        expected["value"],
        rel_tol=expected["rel_tol"],
        abs_tol=expected["abs_tol"],
    )
    assert episode.value != fixture["forbidden"]["continuous_path_slice_return"]


def test_invalid_constituent_retains_whole_episode() -> None:
    fixture = load_runner_fixture("baseline_invalid_constituent.json")
    inputs = fixture["inputs"]
    valid = inputs["valid_constituent"]
    valid_key = encode_runner_listing_key(
        inputs["exchange"],
        valid["ticker"],
        inputs["effective_from"],
        inputs["effective_to"],
    )
    invalid_key = encode_runner_listing_key(
        inputs["exchange"],
        inputs["invalid_ticker"],
        inputs["effective_from"],
        inputs["effective_to"],
    )
    valid_return = simple_adjusted_close_return(
        valid["start_anchor"],
        valid["end_anchor"],
        valid["anchors"],
        valid["target_identity"],
        valid["alias_chain"],
    )
    assert valid_return.valid
    episode = episode_gross_return(
        {
            valid_key: inputs["weights"][0],
            invalid_key: inputs["weights"][1],
        },
        {valid_key: valid_return.value},
    )
    assert episode.valid is fixture["expected"]["valid"]
    assert episode.value is fixture["expected"]["value"]
    assert episode.reason == fixture["expected"]["reason"]
    assert episode.value != fixture["forbidden"]["survivor_renormalized_return"]
    assert episode.value != fixture["forbidden"]["half_survivor_return"]
    zero = episode_gross_return({}, {})
    assert zero.valid is False
    assert zero.value is None
    assert zero.reason == fixture["expected"]["zero_target_reason"]

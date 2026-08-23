"""Post-t mutation oracle for the five frozen-at-t objects."""

from __future__ import annotations

import dataclasses
import inspect

from campaign.eligibility import (
    DecisionTimeListing,
    build_frozen_decision_time,
    evaluate_decision_time_listings,
    freeze_decision_time,
    serialize_frozen_at_t,
)
from campaign.inference import FACTOR_ORDER
from campaign_runner_v1_support import (
    expand_decision_time_listings,
    load_runner_fixture,
)


class TestPostTMutationOracle:
    def test_five_frozen_objects_are_byte_identical_after_post_t_mutation(
        self,
    ) -> None:
        fixture = load_runner_fixture("post_t_mutation_oracle.json")
        inputs = fixture["inputs"]
        listings = expand_decision_time_listings(inputs)
        factor_id = FACTOR_ORDER[inputs["owner_index"]]
        frozen_before = build_frozen_decision_time(
            listings,
            factor_id,
            inputs["min_eligible_count"],
            inputs["min_distinct_values"],
        )
        mutated_post_t = dict(inputs["post_t"])
        mutated_post_t.update(inputs["post_t_mutations"])
        assert mutated_post_t != inputs["post_t"]
        frozen_after = build_frozen_decision_time(
            listings,
            factor_id,
            inputs["min_eligible_count"],
            inputs["min_distinct_values"],
        )
        expected = fixture["expected"]
        assert len(frozen_before.ordered_eligible) == expected["eligible_count"]
        assert frozen_before.zero_target_triggers == tuple(expected["triggers"])
        assert (not frozen_before.long_only_target) is expected["long_only_empty"]
        assert frozen_before.benchmark_formable is expected["benchmark_formable"]
        assert (
            len(frozen_before.matched_benchmark_target)
            == expected["benchmark_count"]
        )
        assert frozen_before.ordered_eligible[0].factor_value == expected[
            "factor_value"
        ]
        assert serialize_frozen_at_t(frozen_before) == serialize_frozen_at_t(
            frozen_after
        )

    def test_decision_time_api_cannot_accept_post_t_fields(self) -> None:
        fixture = load_runner_fixture("post_t_mutation_oracle.json")
        forbidden_parameters = fixture["forbidden"]["parameter_tokens"]
        forbidden_fields = fixture["forbidden"]["field_tokens"]
        for function in (
            build_frozen_decision_time,
            evaluate_decision_time_listings,
            freeze_decision_time,
        ):
            names = inspect.signature(function).parameters
            for token in forbidden_parameters:
                assert all(token not in name for name in names)
            for parameter in names.values():
                assert parameter.default is inspect.Parameter.empty
        field_names = [
            field.name for field in dataclasses.fields(DecisionTimeListing)
        ]
        for token in forbidden_fields:
            assert all(token not in name for name in field_names)

"""Tests for frozen factor target-to-target diagnostic turnover."""

from __future__ import annotations

import pytest

from campaign.turnover import factor_target_turnover


def test_factor_turnover_uses_immediate_frozen_scheduled_predecessor() -> None:
    frozen_targets = (
        {b"a": 0.5, b"b": 0.5},
        {b"c": 0.5, b"d": 0.5},
        {b"a": 0.5, b"b": 0.5},
    )

    def scheduled_turnovers(
        outcome_validity: tuple[bool, bool, bool],
    ) -> tuple[None, float, float]:
        assert len(outcome_validity) == len(frozen_targets)
        return (
            None,
            factor_target_turnover(frozen_targets[0], frozen_targets[1]),
            factor_target_turnover(frozen_targets[1], frozen_targets[2]),
        )

    all_outcomes_valid = scheduled_turnovers((True, True, True))
    middle_outcome_invalid = scheduled_turnovers((True, False, True))
    forbidden_skip_to_last_outcome_valid = factor_target_turnover(
        frozen_targets[0],
        frozen_targets[2],
    )

    assert all_outcomes_valid == (None, 2.0, 2.0)
    assert middle_outcome_invalid == all_outcomes_valid
    assert middle_outcome_invalid[2] == 2.0
    assert forbidden_skip_to_last_outcome_valid == 0.0


def test_factor_target_turnover_aligns_union_and_zero_targets() -> None:
    assert factor_target_turnover({b"a": 1.0}, {}) == 1.0
    assert factor_target_turnover({}, {b"c": 1.0}) == 1.0
    assert factor_target_turnover(
        {b"a": 0.5, b"b": 0.5},
        {b"b": 0.25, b"c": 0.75},
    ) == 1.5


@pytest.mark.parametrize("invalid_weight", [True, float("nan"), -0.1])
def test_factor_target_turnover_rejects_invalid_weights(
    invalid_weight: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        factor_target_turnover({b"a": invalid_weight}, {})

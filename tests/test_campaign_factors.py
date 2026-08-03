"""Frozen golden and mutation tests for campaign factor anchors."""

from __future__ import annotations

import math

from campaign.factors import (
    is_valid_price_anchor,
    low_vol_3m_from_anchors,
    mom_12_1_from_anchors,
    rev_1m_from_anchors,
)


INVALID_ANCHORS: tuple[object, ...] = (
    None,
    True,
    float("nan"),
    float("inf"),
    float("-inf"),
    0.0,
    -1.0,
)


def test_momentum_and_reversal_price_anchors_fail_closed() -> None:
    assert math.isclose(
        mom_12_1_from_anchors(80.0, 100.0),
        0.25,
        abs_tol=1e-15,
    )
    assert math.isclose(
        rev_1m_from_anchors(100.0, 90.0),
        0.10,
        abs_tol=1e-15,
    )

    for invalid_anchor in INVALID_ANCHORS:
        assert mom_12_1_from_anchors(invalid_anchor, 100.0) is None
        assert mom_12_1_from_anchors(80.0, invalid_anchor) is None
        assert rev_1m_from_anchors(invalid_anchor, 90.0) is None
        assert rev_1m_from_anchors(100.0, invalid_anchor) is None


def test_endpoint_factor_adapters_ignore_unreferenced_interior_missing() -> None:
    momentum_window: list[object] = [95.0] * 253
    momentum_window[0] = 80.0
    momentum_window[-22] = 100.0
    momentum_window[100] = None
    reversal_window: list[object] = [95.0] * 22
    reversal_window[0] = 100.0
    reversal_window[-1] = 90.0
    reversal_window[10] = None

    assert not all(is_valid_price_anchor(value) for value in momentum_window)
    assert not all(is_valid_price_anchor(value) for value in reversal_window)
    assert math.isclose(
        mom_12_1_from_anchors(momentum_window[0], momentum_window[-22]),
        0.25,
        abs_tol=1e-15,
    )
    assert math.isclose(
        rev_1m_from_anchors(reversal_window[0], reversal_window[-1]),
        0.10,
        abs_tol=1e-15,
    )


def test_low_vol_3m_uses_exactly_63_returns_from_64_price_anchors() -> None:
    source_returns = tuple(index / 1000 for index in range(1, 64))
    price_anchors = [100.0]
    for one_day_return in source_returns:
        price_anchors.append(price_anchors[-1] * (1.0 + one_day_return))

    recovered_returns = tuple(
        price_anchors[index] / price_anchors[index - 1] - 1.0
        for index in range(1, len(price_anchors))
    )
    inclusive_t_window = recovered_returns[-63:]
    mean_return = sum(inclusive_t_window) / len(inclusive_t_window)
    sample_std = math.sqrt(
        sum(
            (one_day_return - mean_return) ** 2
            for one_day_return in inclusive_t_window
        )
        / (len(inclusive_t_window) - 1)
    )
    log_returns = tuple(
        math.log(price_anchors[index] / price_anchors[index - 1])
        for index in range(1, len(price_anchors))
    )
    mean_log_return = sum(log_returns) / len(log_returns)
    forbidden_log_sample_std = math.sqrt(
        sum(
            (one_day_return - mean_log_return) ** 2
            for one_day_return in log_returns
        )
        / (len(log_returns) - 1)
    )

    assert len(price_anchors) == 64
    assert len(inclusive_t_window) == 63
    assert math.isclose(
        low_vol_3m_from_anchors(price_anchors),
        -math.sqrt(336) / 1000,
        rel_tol=1e-12,
        abs_tol=1e-15,
    )
    assert math.isclose(
        -sample_std,
        -0.01833030277982336,
        rel_tol=1e-15,
        abs_tol=1e-15,
    )
    assert math.isclose(
        -forbidden_log_sample_std,
        -0.017765781758667692,
        rel_tol=1e-15,
        abs_tol=1e-15,
    )
    assert not math.isclose(
        sample_std,
        forbidden_log_sample_std,
        rel_tol=1e-12,
        abs_tol=1e-15,
    )

    for invalid_anchor in INVALID_ANCHORS:
        mutated_anchors: list[object] = list(price_anchors)
        mutated_anchors[31] = invalid_anchor
        assert low_vol_3m_from_anchors(mutated_anchors) is None
    assert low_vol_3m_from_anchors(price_anchors[:-1]) is None
    assert low_vol_3m_from_anchors(price_anchors + [100.0]) is None

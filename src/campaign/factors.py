"""Frozen scalar factor-anchor computations for the campaign protocol."""

from __future__ import annotations

from collections.abc import Sequence
import math
from numbers import Real


def is_valid_price_anchor(anchor: object) -> bool:
    """Return whether an anchor is real, non-Boolean, finite, and positive."""

    if isinstance(anchor, bool) or not isinstance(anchor, Real):
        return False
    try:
        numeric = float(anchor)
    except (OverflowError, TypeError, ValueError):
        return False
    return math.isfinite(numeric) and numeric > 0.0


def mom_12_1_from_anchors(
    adjusted_close_t_minus_252: object,
    adjusted_close_t_minus_21: object,
) -> float | None:
    """Compute frozen MOM_12_1 from its two referenced price anchors."""

    if not (
        is_valid_price_anchor(adjusted_close_t_minus_252)
        and is_valid_price_anchor(adjusted_close_t_minus_21)
    ):
        return None
    return (
        float(adjusted_close_t_minus_21)
        / float(adjusted_close_t_minus_252)
        - 1.0
    )


def rev_1m_from_anchors(
    adjusted_close_t_minus_21: object,
    adjusted_close_t: object,
) -> float | None:
    """Compute frozen REV_1M from its two referenced price anchors."""

    if not (
        is_valid_price_anchor(adjusted_close_t_minus_21)
        and is_valid_price_anchor(adjusted_close_t)
    ):
        return None
    return -(
        float(adjusted_close_t)
        / float(adjusted_close_t_minus_21)
        - 1.0
    )


def low_vol_3m_from_anchors(
    adjusted_close_anchors: Sequence[object],
) -> float | None:
    """Compute frozen LOW_VOL_3M from exactly 64 adjusted-close anchors."""

    if (
        isinstance(adjusted_close_anchors, (str, bytes, bytearray))
        or not isinstance(adjusted_close_anchors, Sequence)
        or len(adjusted_close_anchors) != 64
        or any(
            not is_valid_price_anchor(anchor)
            for anchor in adjusted_close_anchors
        )
    ):
        return None

    anchors = tuple(float(anchor) for anchor in adjusted_close_anchors)
    simple_returns = tuple(
        anchors[index] / anchors[index - 1] - 1.0
        for index in range(1, len(anchors))
    )
    mean_simple_return = sum(simple_returns) / len(simple_returns)
    sample_variance = sum(
        (one_day_return - mean_simple_return) ** 2
        for one_day_return in simple_returns
    ) / (len(simple_returns) - 1)
    return -math.sqrt(sample_variance)


__all__ = [
    "is_valid_price_anchor",
    "low_vol_3m_from_anchors",
    "mom_12_1_from_anchors",
    "rev_1m_from_anchors",
]

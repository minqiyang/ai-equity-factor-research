"""Frozen factor target-to-target diagnostic turnover.

This module does not implement strategy turnover. Drift-aware strategy
pretrade-to-target turnover and cost accounting remain in
``backtest.portfolio`` and are bound only through conformance tests.
"""

from __future__ import annotations

from collections.abc import Mapping
import math
from numbers import Real


def factor_target_turnover(
    previous_target: Mapping[bytes, object],
    current_target: Mapping[bytes, object],
) -> float:
    """Compute undivided target-to-target turnover over the key union."""

    previous = _validated_target(previous_target, name="previous_target")
    current = _validated_target(current_target, name="current_target")
    listing_keys = sorted(previous.keys() | current.keys())
    return sum(
        abs(current.get(key, 0.0) - previous.get(key, 0.0))
        for key in listing_keys
    )


def _validated_target(
    target: Mapping[bytes, object],
    *,
    name: str,
) -> dict[bytes, float]:
    if not isinstance(target, Mapping):
        raise TypeError(f"{name} must be a mapping")
    validated: dict[bytes, float] = {}
    for listing_key, weight in target.items():
        if not isinstance(listing_key, bytes) or not listing_key:
            raise TypeError(f"{name} keys must be nonempty bytes")
        if isinstance(weight, bool) or not isinstance(weight, Real):
            raise TypeError(f"{name} weights must be real non-Boolean scalars")
        numeric_weight = float(weight)
        if not math.isfinite(numeric_weight) or numeric_weight < 0.0:
            raise ValueError(f"{name} weights must be finite and nonnegative")
        validated[listing_key] = numeric_weight
    return validated


__all__ = ["factor_target_turnover"]

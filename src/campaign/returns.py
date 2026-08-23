"""One strict simple adjusted-close return gate."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import math
from numbers import Real

from campaign.factors import is_valid_price_anchor
from campaign.lineage import evaluate_factor_anchor_lineage_v1


_REASON_ANCHOR_MISSING = "ANCHOR_MISSING"
_REASON_ANCHOR_BOOLEAN = "ANCHOR_BOOLEAN"
_REASON_ANCHOR_NON_FINITE = "ANCHOR_NON_FINITE"
_REASON_ANCHOR_NON_POSITIVE = "ANCHOR_NON_POSITIVE"
_REASON_ANCHOR_PRICE_MISMATCH = "ANCHOR_PRICE_MISMATCH"


@dataclass(frozen=True)
class SimpleReturn:
    """One retained simple return or an invalid/missing reason."""

    value: float | None
    valid: bool
    reason: str | None


def simple_adjusted_close_return(
    start_anchor: object,
    end_anchor: object,
    anchors: Sequence[Mapping[str, object]],
    target_identity: Mapping[str, str],
    alias_chain: Sequence[Mapping[str, object]],
) -> SimpleReturn:
    """Return end/start - 1 after lineage and positive-anchor gates.

    The same gate serves execution_anchored_forward_return_v1,
    adjusted_close_simple_held_return_v1, and the baseline episode return.
    """

    lineage = evaluate_factor_anchor_lineage_v1(
        anchors,
        target_identity,
        alias_chain,
    )
    if not lineage.valid:
        return SimpleReturn(None, False, lineage.reason)
    for anchor in (start_anchor, end_anchor):
        reason = _anchor_invalid_reason(anchor)
        if reason is not None:
            return SimpleReturn(None, False, reason)
    start_price = _bound_record_price(start_anchor, anchors[0])
    end_price = _bound_record_price(end_anchor, anchors[-1])
    if start_price is None or end_price is None:
        return SimpleReturn(None, False, _REASON_ANCHOR_PRICE_MISMATCH)
    return SimpleReturn(end_price / start_price - 1.0, True, None)


def _bound_record_price(
    scalar: object,
    record: Mapping[str, object],
) -> float | None:
    try:
        scalar_value = _finite_real(scalar, "start_or_end_anchor")
        record_value = _finite_real(record.get("adjusted_close"), "adjusted_close")
    except (TypeError, ValueError):
        return None
    if scalar_value != record_value:
        return None
    return record_value


def _finite_real(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real non-Boolean scalar")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError(f"{name} must be finite")
    return numeric


def _anchor_invalid_reason(anchor: object) -> str | None:
    if anchor is None:
        return _REASON_ANCHOR_MISSING
    if isinstance(anchor, bool):
        return _REASON_ANCHOR_BOOLEAN
    if not is_valid_price_anchor(anchor):
        try:
            numeric = float(anchor)  # type: ignore[arg-type]
        except (OverflowError, TypeError, ValueError):
            return _REASON_ANCHOR_MISSING
        if numeric != numeric or numeric in {float("inf"), float("-inf")}:
            return _REASON_ANCHOR_NON_FINITE
        return _REASON_ANCHOR_NON_POSITIVE
    return None


__all__ = [
    "SimpleReturn",
    "simple_adjusted_close_return",
]

"""Derived factor-ID registry bound to the frozen owner tuple."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from types import MappingProxyType

from campaign import factors
from campaign.inference import FACTOR_ORDER


_HIGHER_IS_BETTER = "HIGHER_IS_BETTER"
_ANCHOR_LINEAGE_POLICY = "factor_anchor_lineage_v1"
_REASON_ANCHOR_MISSING = "ANCHOR_MISSING"
_REASON_ANCHOR_BOOLEAN = "ANCHOR_BOOLEAN"
_REASON_ANCHOR_NON_FINITE = "ANCHOR_NON_FINITE"
_REASON_ANCHOR_NON_POSITIVE = "ANCHOR_NON_POSITIVE"
_REASON_ANCHOR_COUNT_INVALID = "ANCHOR_COUNT_INVALID"
_REASON_ANCHOR_INVALID = "ANCHOR_INVALID"


@dataclass(frozen=True)
class FactorSpec:
    """One frozen factor implementation and its required anchor spec."""

    factor_id: str
    direction: str
    lookback_common_calendar_positions: int
    referenced_anchor_offsets: tuple[int, ...] | None
    required_history_price_anchor_span: tuple[int, int] | None
    required_anchor_count: int | None
    anchor_lineage_policy: str
    compute: Callable[..., float | None]

    def compute_qualname(self) -> str:
        """Return the bound implementation's module-qualified name."""

        return f"{self.compute.__module__}.{self.compute.__qualname__}"


@dataclass(frozen=True)
class ComputedFactor:
    """One retained factor value or an invalid/missing reason."""

    value: float | None
    valid: bool
    reason: str | None


@dataclass(frozen=True)
class _Row:
    compute: Callable[..., float | None]
    lookback_common_calendar_positions: int
    referenced_anchor_offsets: tuple[int, ...] | None
    required_history_price_anchor_span: tuple[int, int] | None
    required_anchor_count: int | None


# Positionally aligned to FACTOR_ORDER. Contains no factor-ID literal.
_SPEC_ROWS = (
    _Row(
        compute=factors.mom_12_1_from_anchors,
        lookback_common_calendar_positions=253,
        referenced_anchor_offsets=(-252, -21),
        required_history_price_anchor_span=None,
        required_anchor_count=None,
    ),
    _Row(
        compute=factors.rev_1m_from_anchors,
        lookback_common_calendar_positions=22,
        referenced_anchor_offsets=(-21, 0),
        required_history_price_anchor_span=None,
        required_anchor_count=None,
    ),
    _Row(
        compute=factors.low_vol_3m_from_anchors,
        lookback_common_calendar_positions=64,
        referenced_anchor_offsets=None,
        required_history_price_anchor_span=(-63, 0),
        required_anchor_count=64,
    ),
)


FACTOR_REGISTRY = MappingProxyType(
    {
        factor_id: FactorSpec(
            factor_id=factor_id,
            direction=_HIGHER_IS_BETTER,
            lookback_common_calendar_positions=(
                row.lookback_common_calendar_positions
            ),
            referenced_anchor_offsets=row.referenced_anchor_offsets,
            required_history_price_anchor_span=(
                row.required_history_price_anchor_span
            ),
            required_anchor_count=row.required_anchor_count,
            anchor_lineage_policy=_ANCHOR_LINEAGE_POLICY,
            compute=row.compute,
        )
        for factor_id, row in zip(FACTOR_ORDER, _SPEC_ROWS, strict=True)
    }
)


def factor_spec(factor_id: str) -> FactorSpec:
    """Return the unique spec for an exact frozen factor ID."""

    if not isinstance(factor_id, str):
        raise TypeError("factor_id must be a string")
    try:
        return FACTOR_REGISTRY[factor_id]
    except KeyError:
        raise KeyError(factor_id) from None


def compute_registered_factor(
    factor_id: str,
    anchors: Sequence[object],
) -> ComputedFactor:
    """Compute one registered factor from already-selected anchors."""

    spec = factor_spec(factor_id)
    if (
        isinstance(anchors, (str, bytes, bytearray))
        or not isinstance(anchors, Sequence)
    ):
        return ComputedFactor(None, False, _REASON_ANCHOR_COUNT_INVALID)

    expected_count = (
        len(spec.referenced_anchor_offsets)
        if spec.referenced_anchor_offsets is not None
        else spec.required_anchor_count
    )
    if expected_count is None or len(anchors) != expected_count:
        return ComputedFactor(None, False, _REASON_ANCHOR_COUNT_INVALID)

    for anchor in anchors:
        reason = _anchor_invalid_reason(anchor)
        if reason is not None:
            return ComputedFactor(None, False, reason)

    if spec.referenced_anchor_offsets is not None:
        value = spec.compute(*anchors)
    else:
        value = spec.compute(anchors)
    if value is None:
        return ComputedFactor(None, False, _REASON_ANCHOR_INVALID)
    return ComputedFactor(float(value), True, None)


def _anchor_invalid_reason(anchor: object) -> str | None:
    if anchor is None:
        return _REASON_ANCHOR_MISSING
    if isinstance(anchor, bool):
        return _REASON_ANCHOR_BOOLEAN
    if not factors.is_valid_price_anchor(anchor):
        try:
            numeric = float(anchor)  # type: ignore[arg-type]
        except (OverflowError, TypeError, ValueError):
            return _REASON_ANCHOR_MISSING
        if numeric != numeric or numeric in {float("inf"), float("-inf")}:
            return _REASON_ANCHOR_NON_FINITE
        return _REASON_ANCHOR_NON_POSITIVE
    return None


__all__ = [
    "ComputedFactor",
    "FACTOR_REGISTRY",
    "FactorSpec",
    "compute_registered_factor",
    "factor_spec",
]

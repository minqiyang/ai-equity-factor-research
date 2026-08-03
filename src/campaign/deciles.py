"""Frozen factor-ranking and decile-assignment computations."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
import math
from numbers import Real


@dataclass(frozen=True)
class RankedListing:
    """One validated listing and factor value in canonical rank order."""

    listing_key: bytes
    factor_value: float


@dataclass(frozen=True)
class DecileBucket:
    """One explicitly labelled decile and its high-to-low ordered members."""

    label: str
    members: tuple[RankedListing, ...]


def order_eligible(
    eligible: Iterable[tuple[bytes, object]],
) -> tuple[RankedListing, ...]:
    """Order prepared eligible listings by value, then canonical key bytes."""

    ranked: list[RankedListing] = []
    seen_keys: set[bytes] = set()
    for item in eligible:
        try:
            listing_key, factor_value = item
        except (TypeError, ValueError) as exc:
            raise TypeError(
                "eligible entries must be (listing_key, factor_value) pairs"
            ) from exc
        if not isinstance(listing_key, bytes) or not listing_key:
            raise TypeError("listing keys must be nonempty bytes")
        if listing_key in seen_keys:
            raise ValueError("eligible listing keys must be unique")
        if isinstance(factor_value, bool) or not isinstance(factor_value, Real):
            raise TypeError("factor values must be real non-Boolean scalars")
        numeric_value = float(factor_value)
        if not math.isfinite(numeric_value):
            raise ValueError("factor values must be finite")
        seen_keys.add(listing_key)
        ranked.append(RankedListing(listing_key, numeric_value))

    return tuple(
        sorted(
            ranked,
            key=lambda item: (-item.factor_value, item.listing_key),
        )
    )


def top_decile_count(eligible_count: int) -> int:
    """Return the frozen remainder-first count of the highest decile."""

    if isinstance(eligible_count, bool) or not isinstance(eligible_count, int):
        raise TypeError("eligible_count must be an integer")
    if eligible_count < 0:
        raise ValueError("eligible_count must be nonnegative")
    base, remainder = divmod(eligible_count, 10)
    return base + (1 if remainder else 0)


def assign_deciles(
    ordered_eligible: Sequence[RankedListing],
) -> tuple[DecileBucket, ...]:
    """Assign canonical ordered listings and return buckets in D1..D10 order."""

    if isinstance(ordered_eligible, (str, bytes, bytearray)) or not isinstance(
        ordered_eligible, Sequence
    ):
        raise TypeError("ordered_eligible must be a sequence of RankedListing")
    ordered = tuple(ordered_eligible)
    if any(not isinstance(item, RankedListing) for item in ordered):
        raise TypeError("ordered_eligible must contain RankedListing values")
    canonical = order_eligible(
        (item.listing_key, item.factor_value) for item in ordered
    )
    if ordered != canonical:
        raise ValueError("ordered_eligible is not in canonical rank order")

    base, remainder = divmod(len(ordered), 10)
    high_to_low: dict[str, tuple[RankedListing, ...]] = {}
    cursor = 0
    for high_rank_index in range(10):
        size = base + (1 if high_rank_index < remainder else 0)
        label = f"D{10 - high_rank_index}"
        high_to_low[label] = ordered[cursor : cursor + size]
        cursor += size

    return tuple(
        DecileBucket(f"D{decile}", high_to_low[f"D{decile}"])
        for decile in range(1, 11)
    )


__all__ = [
    "DecileBucket",
    "RankedListing",
    "assign_deciles",
    "order_eligible",
    "top_decile_count",
]

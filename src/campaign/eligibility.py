"""Decision-time eligibility, zero-target triggers, and frozen-at-t objects."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json
import math
from numbers import Integral, Real
from types import MappingProxyType

from campaign.deciles import (
    DecileBucket,
    RankedListing,
    assign_deciles,
    order_eligible,
)
from campaign.lineage import evaluate_factor_anchor_lineage_v1
from campaign.registry import compute_registered_factor, factor_spec


_REASON_MEMBERSHIP_NOT_KNOWN_AT_T = "MEMBERSHIP_NOT_KNOWN_AT_T"
_REASON_TERMINAL_EVENT_BLOCKED_AT_T = "TERMINAL_EVENT_BLOCKED_AT_T"
_REASON_LOOKBACK_NOT_ADDRESSABLE_AT_T = "LOOKBACK_NOT_ADDRESSABLE_AT_T"
_TRIGGER_DUPLICATE = "DUPLICATE_CANONICAL_LISTING_KEY_BYTES_AT_T"
_TRIGGER_COUNT = "ELIGIBLE_SECURITY_COUNT_BELOW_100_AT_T"
_TRIGGER_DISTINCT = "DISTINCT_FINITE_FACTOR_VALUE_COUNT_BELOW_10_AT_T"
_HIGH_DECILE = "D10"


@dataclass(frozen=True)
class DecisionTimeListing:
    """One listing's at-t fields. Post-t availability is not representable."""

    listing_key: bytes
    in_universe_at_t: bool
    terminal_blocked_at_t: bool
    lookback_addressable_at_t: bool
    referenced_anchors: tuple[object, ...]
    lineage_anchors: tuple[Mapping[str, object], ...]
    target_identity: Mapping[str, str]
    alias_chain: tuple[Mapping[str, object], ...]


@dataclass(frozen=True)
class ListingDecision:
    """Retained listing-level eligibility decision and counted reason."""

    listing_key: bytes
    eligible: bool
    reason: str | None
    factor_value: float | None


@dataclass(frozen=True)
class FrozenDecisionTime:
    """The five frozen-at-t objects plus retained reasons and triggers."""

    ordered_eligible: tuple[RankedListing, ...]
    factor_ranks: tuple[tuple[bytes, int], ...]
    deciles: tuple[DecileBucket, ...]
    long_only_target: MappingProxyType[bytes, float]
    matched_benchmark_target: MappingProxyType[bytes, float]
    benchmark_formable: bool
    zero_target_triggers: tuple[str, ...]
    invalid_factor_month: bool
    reason_counts: MappingProxyType[str, int]
    retained_decisions: tuple[ListingDecision, ...]


def evaluate_decision_time_listings(
    listings: Sequence[DecisionTimeListing],
    factor_id: str,
) -> tuple[ListingDecision, ...]:
    """Evaluate factor-specific eligibility using only at-t inputs."""

    if (
        isinstance(listings, (str, bytes, bytearray))
        or not isinstance(listings, Sequence)
    ):
        raise TypeError("listings must be a sequence")
    factor_spec(factor_id)
    return tuple(_evaluate_one(listing, factor_id) for listing in listings)


def freeze_decision_time(
    decisions: Sequence[ListingDecision],
    min_eligible_count: int,
    min_distinct_values: int,
) -> FrozenDecisionTime:
    """Freeze ranks, deciles, targets, and the three zero-target triggers."""

    if (
        isinstance(decisions, (str, bytes, bytearray))
        or not isinstance(decisions, Sequence)
    ):
        raise TypeError("decisions must be a sequence")
    floor_count = _nonneg_int(min_eligible_count, "min_eligible_count")
    floor_distinct = _nonneg_int(min_distinct_values, "min_distinct_values")

    retained: list[ListingDecision] = []
    eligible_pairs: list[tuple[bytes, float]] = []
    seen_keys: set[bytes] = set()
    duplicate_keys = False
    reason_counts: dict[str, int] = {}
    for decision in decisions:
        if not isinstance(decision, ListingDecision):
            raise TypeError("decisions must contain ListingDecision values")
        _validate_listing_key(decision.listing_key)
        if not isinstance(decision.eligible, bool):
            raise TypeError("eligible must be a bool")
        retained.append(decision)
        if decision.reason is not None:
            if not isinstance(decision.reason, str) or not decision.reason:
                raise ValueError("reason must be a nonempty string")
            reason_counts[decision.reason] = (
                reason_counts.get(decision.reason, 0) + 1
            )
        if not decision.eligible:
            continue
        value = _finite_real(decision.factor_value, "factor_value")
        if decision.listing_key in seen_keys:
            duplicate_keys = True
        seen_keys.add(decision.listing_key)
        eligible_pairs.append((decision.listing_key, value))

    triggers = _zero_target_triggers(
        len(eligible_pairs),
        len({value for _key, value in eligible_pairs}),
        duplicate_keys,
        floor_count,
        floor_distinct,
    )
    if duplicate_keys:
        ordered: tuple[RankedListing, ...] = ()
        benchmark = MappingProxyType({})
        benchmark_formable = False
    else:
        ordered = order_eligible(eligible_pairs)
        if ordered:
            universe_weight = 1.0 / len(ordered)
            benchmark = MappingProxyType(
                {
                    item.listing_key: universe_weight
                    for item in sorted(
                        ordered,
                        key=_listing_key_of,
                    )
                }
            )
            benchmark_formable = True
        else:
            benchmark = MappingProxyType({})
            benchmark_formable = False

    deciles = assign_deciles(ordered)
    ranks = tuple(
        (item.listing_key, index + 1) for index, item in enumerate(ordered)
    )
    if triggers or not ordered:
        long_only: MappingProxyType[bytes, float] = MappingProxyType({})
    else:
        selected = _high_decile(deciles).members
        selected_weight = 1.0 / len(selected)
        long_only = MappingProxyType(
            {
                item.listing_key: selected_weight
                for item in sorted(selected, key=_listing_key_of)
            }
        )
    return FrozenDecisionTime(
        ordered_eligible=ordered,
        factor_ranks=ranks,
        deciles=deciles,
        long_only_target=long_only,
        matched_benchmark_target=benchmark,
        benchmark_formable=benchmark_formable,
        zero_target_triggers=triggers,
        invalid_factor_month=bool(triggers),
        reason_counts=MappingProxyType(reason_counts),
        retained_decisions=tuple(retained),
    )


def build_frozen_decision_time(
    listings: Sequence[DecisionTimeListing],
    factor_id: str,
    min_eligible_count: int,
    min_distinct_values: int,
) -> FrozenDecisionTime:
    """Evaluate at-t listings and freeze the five decision-time objects."""

    return freeze_decision_time(
        evaluate_decision_time_listings(listings, factor_id),
        min_eligible_count,
        min_distinct_values,
    )


def serialize_frozen_at_t(frozen: FrozenDecisionTime) -> bytes:
    """Serialize the five frozen-at-t objects to stable bytes."""

    if not isinstance(frozen, FrozenDecisionTime):
        raise TypeError("frozen must be FrozenDecisionTime")
    payload = {
        "deciles": [
            {
                "label": bucket.label,
                "members": [
                    {
                        "factor_value": member.factor_value,
                        "listing_key": member.listing_key.hex(),
                    }
                    for member in bucket.members
                ],
            }
            for bucket in frozen.deciles
        ],
        "factor_ranks": [
            {"listing_key": key.hex(), "rank": rank}
            for key, rank in frozen.factor_ranks
        ],
        "long_only_target": {
            key.hex(): weight
            for key, weight in sorted(frozen.long_only_target.items())
        },
        "matched_benchmark_target": {
            key.hex(): weight
            for key, weight in sorted(frozen.matched_benchmark_target.items())
        },
        "ordered_eligible": [
            {
                "factor_value": item.factor_value,
                "listing_key": item.listing_key.hex(),
            }
            for item in frozen.ordered_eligible
        ],
    }
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def _evaluate_one(
    listing: DecisionTimeListing,
    factor_id: str,
) -> ListingDecision:
    if not isinstance(listing, DecisionTimeListing):
        raise TypeError("listings must contain DecisionTimeListing values")
    _validate_listing_key(listing.listing_key)
    if not isinstance(listing.in_universe_at_t, bool):
        raise TypeError("in_universe_at_t must be a bool")
    if not listing.in_universe_at_t:
        return ListingDecision(
            listing.listing_key,
            False,
            _REASON_MEMBERSHIP_NOT_KNOWN_AT_T,
            None,
        )
    if not isinstance(listing.terminal_blocked_at_t, bool):
        raise TypeError("terminal_blocked_at_t must be a bool")
    if listing.terminal_blocked_at_t:
        return ListingDecision(
            listing.listing_key,
            False,
            _REASON_TERMINAL_EVENT_BLOCKED_AT_T,
            None,
        )
    if not isinstance(listing.lookback_addressable_at_t, bool):
        raise TypeError("lookback_addressable_at_t must be a bool")
    if not listing.lookback_addressable_at_t:
        return ListingDecision(
            listing.listing_key,
            False,
            _REASON_LOOKBACK_NOT_ADDRESSABLE_AT_T,
            None,
        )
    lineage = evaluate_factor_anchor_lineage_v1(
        listing.lineage_anchors,
        listing.target_identity,
        listing.alias_chain,
    )
    if not lineage.valid:
        return ListingDecision(
            listing.listing_key,
            False,
            lineage.reason,
            None,
        )
    computed = compute_registered_factor(factor_id, listing.referenced_anchors)
    if not computed.valid:
        return ListingDecision(
            listing.listing_key,
            False,
            computed.reason,
            None,
        )
    return ListingDecision(
        listing.listing_key,
        True,
        None,
        computed.value,
    )


def _zero_target_triggers(
    eligible_count: int,
    distinct_value_count: int,
    duplicate_keys: bool,
    min_eligible_count: int,
    min_distinct_values: int,
) -> tuple[str, ...]:
    triggers: list[str] = []
    if duplicate_keys:
        triggers.append(_TRIGGER_DUPLICATE)
    if eligible_count < min_eligible_count:
        triggers.append(_TRIGGER_COUNT)
    if distinct_value_count < min_distinct_values:
        triggers.append(_TRIGGER_DISTINCT)
    return tuple(triggers)


def _high_decile(deciles: tuple[DecileBucket, ...]) -> DecileBucket:
    for bucket in deciles:
        if bucket.label == _HIGH_DECILE:
            return bucket
    raise ValueError("decile assignments must include the high decile")


def _listing_key_of(item: RankedListing) -> bytes:
    return item.listing_key


def _validate_listing_key(listing_key: object) -> bytes:
    if not isinstance(listing_key, bytes) or not listing_key:
        raise TypeError("listing keys must be nonempty bytes")
    return listing_key


def _finite_real(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real non-Boolean scalar")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError(f"{name} must be finite")
    return numeric


def _nonneg_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer")
    integer = int(value)
    if integer < 0:
        raise ValueError(f"{name} must be nonnegative")
    return integer


__all__ = [
    "DecisionTimeListing",
    "FrozenDecisionTime",
    "ListingDecision",
    "build_frozen_decision_time",
    "evaluate_decision_time_listings",
    "freeze_decision_time",
    "serialize_frozen_at_t",
]

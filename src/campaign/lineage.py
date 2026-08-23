"""factor_anchor_lineage_v1 identity gate and campaign-wide key freeze."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from campaign.listing_key import encode_listing_lineage_key_v1


_IDENTITY_FIELDS = (
    "resolved_permanent_security_id",
    "resolved_listing_id",
    "resolved_listing_episode_id",
)
_ALIAS_TEXT_FIELDS = (
    "source_exchange",
    "source_ticker",
    "lineage_resolution_evidence_id",
)
_ACCEPTED_RENAME = (
    "ACCEPTED_SYMBOL_RENAME_SAME_PERMANENT_SECURITY_"
    "SAME_LISTING_AND_LISTING_EPISODE"
)
_TARGET_ALIAS = "TARGET_ALIAS"
_REASON_TARGET_IDENTITY_INCOMPLETE = "TARGET_IDENTITY_INCOMPLETE"
_REASON_ALIAS_CHAIN_EMPTY = "ALIAS_CHAIN_EMPTY"
_REASON_ANCHORS_EMPTY = "ANCHORS_EMPTY"
_REASON_ALIAS_INTERVAL_INVALID = "ALIAS_INTERVAL_INVALID"
_REASON_ALIAS_IDENTITY_MISMATCH = "ALIAS_IDENTITY_MISMATCH"
_REASON_ALIAS_EVIDENCE_MISSING = "ALIAS_EVIDENCE_MISSING"
_REASON_ALIAS_CHAIN_NOT_CONTIGUOUS = "ALIAS_CHAIN_NOT_CONTIGUOUS"
_REASON_ALIAS_TRANSITION_FORBIDDEN = "ALIAS_TRANSITION_FORBIDDEN"
_REASON_ANCHOR_IDENTITY_MISMATCH = "ANCHOR_IDENTITY_MISMATCH"
_REASON_ANCHOR_SESSION_INVALID = "ANCHOR_SESSION_INVALID"
_REASON_ANCHOR_ALIAS_UNRESOLVED = "ANCHOR_ALIAS_UNRESOLVED"
_REASON_ANCHOR_ALIAS_AMBIGUOUS = "ANCHOR_ALIAS_AMBIGUOUS"


@dataclass(frozen=True)
class LineageVerdict:
    """Retained lineage decision and the exact counted reason."""

    valid: bool
    reason: str | None


def evaluate_factor_anchor_lineage_v1(
    anchors: Sequence[Mapping[str, object]],
    target_identity: Mapping[str, str],
    alias_chain: Sequence[Mapping[str, object]],
) -> LineageVerdict:
    """Validate identity match and accepted rename traversal."""

    if not isinstance(anchors, Sequence) or isinstance(
        anchors, (str, bytes, bytearray)
    ):
        return LineageVerdict(False, _REASON_ANCHORS_EMPTY)
    if not isinstance(alias_chain, Sequence) or isinstance(
        alias_chain, (str, bytes, bytearray)
    ):
        return LineageVerdict(False, _REASON_ALIAS_CHAIN_EMPTY)
    if not isinstance(target_identity, Mapping):
        return LineageVerdict(False, _REASON_TARGET_IDENTITY_INCOMPLETE)
    if not anchors:
        return LineageVerdict(False, _REASON_ANCHORS_EMPTY)
    if not alias_chain:
        return LineageVerdict(False, _REASON_ALIAS_CHAIN_EMPTY)
    if any(
        not isinstance(target_identity.get(field), str)
        or not target_identity[field]
        for field in _IDENTITY_FIELDS
    ):
        return LineageVerdict(False, _REASON_TARGET_IDENTITY_INCOMPLETE)

    parsed_chain: list[tuple[date, date | None, Mapping[str, object]]] = []
    for alias in alias_chain:
        if not isinstance(alias, Mapping):
            return LineageVerdict(False, _REASON_ALIAS_INTERVAL_INVALID)
        try:
            effective_from = _strict_date(alias["alias_effective_from"])
            effective_to_raw = alias.get("alias_effective_to")
            effective_to = (
                None
                if effective_to_raw is None
                else _strict_date(effective_to_raw)
            )
        except (KeyError, TypeError, ValueError):
            return LineageVerdict(False, _REASON_ALIAS_INTERVAL_INVALID)
        if effective_to is not None and effective_to <= effective_from:
            return LineageVerdict(False, _REASON_ALIAS_INTERVAL_INVALID)
        if any(
            alias.get(field) != target_identity[field]
            for field in _IDENTITY_FIELDS
        ):
            return LineageVerdict(False, _REASON_ALIAS_IDENTITY_MISMATCH)
        for required_text in _ALIAS_TEXT_FIELDS:
            if (
                not isinstance(alias.get(required_text), str)
                or not alias[required_text]
            ):
                return LineageVerdict(False, _REASON_ALIAS_EVIDENCE_MISSING)
        parsed_chain.append((effective_from, effective_to, alias))

    for index, (effective_from, effective_to, alias) in enumerate(parsed_chain):
        if index == len(parsed_chain) - 1:
            if alias.get("transition_to_next") != _TARGET_ALIAS:
                return LineageVerdict(False, _REASON_ALIAS_TRANSITION_FORBIDDEN)
            continue
        next_effective_from = parsed_chain[index + 1][0]
        if (
            effective_to != next_effective_from
            or alias.get("transition_to_next") != _ACCEPTED_RENAME
            or next_effective_from <= effective_from
        ):
            if alias.get("transition_to_next") != _ACCEPTED_RENAME:
                return LineageVerdict(
                    False, _REASON_ALIAS_TRANSITION_FORBIDDEN
                )
            return LineageVerdict(False, _REASON_ALIAS_CHAIN_NOT_CONTIGUOUS)

    for anchor in anchors:
        if not isinstance(anchor, Mapping):
            return LineageVerdict(False, _REASON_ANCHOR_IDENTITY_MISMATCH)
        if any(
            anchor.get(field) != target_identity[field]
            for field in _IDENTITY_FIELDS
        ):
            return LineageVerdict(False, _REASON_ANCHOR_IDENTITY_MISMATCH)
        try:
            session = _strict_date(anchor["session_date"])
        except (KeyError, TypeError, ValueError):
            return LineageVerdict(False, _REASON_ANCHOR_SESSION_INVALID)
        matching_aliases = [
            alias
            for effective_from, effective_to, alias in parsed_chain
            if anchor.get("source_exchange") == alias["source_exchange"]
            and anchor.get("source_ticker") == alias["source_ticker"]
            and anchor.get("alias_effective_from")
            == alias["alias_effective_from"]
            and anchor.get("alias_effective_to") == alias["alias_effective_to"]
            and anchor.get("lineage_resolution_evidence_id")
            == alias["lineage_resolution_evidence_id"]
            and session >= effective_from
            and (effective_to is None or session < effective_to)
        ]
        if len(matching_aliases) == 0:
            return LineageVerdict(False, _REASON_ANCHOR_ALIAS_UNRESOLVED)
        if len(matching_aliases) != 1:
            return LineageVerdict(False, _REASON_ANCHOR_ALIAS_AMBIGUOUS)
    return LineageVerdict(True, None)


def freeze_listing_lineage_key(
    exchange: str,
    ticker: str,
    effective_from: str,
    first_eligibility_dates: Sequence[str],
    endpoint_known_date: str | None,
    endpoint_date: str | None,
) -> bytes:
    """Freeze one listing key at the earliest any-factor eligibility date."""

    if (
        isinstance(first_eligibility_dates, (str, bytes, bytearray))
        or not isinstance(first_eligibility_dates, Sequence)
        or not first_eligibility_dates
    ):
        raise ValueError("first_eligibility_dates must be a nonempty sequence")
    earliest = min(
        _strict_date(value) for value in first_eligibility_dates
    )
    known_at_freeze = (
        endpoint_known_date is not None
        and endpoint_date is not None
        and _strict_date(endpoint_known_date) <= earliest
    )
    frozen_endpoint = endpoint_date if known_at_freeze else None
    return encode_listing_lineage_key_v1(
        exchange,
        ticker,
        effective_from,
        frozen_endpoint,
    )


def _strict_date(value: object) -> date:
    if not isinstance(value, str):
        raise ValueError("date must be strict YYYY-MM-DD")
    parsed = date.fromisoformat(value)
    if len(value) != 10 or parsed.isoformat() != value:
        raise ValueError("date must be strict YYYY-MM-DD")
    return parsed


__all__ = [
    "LineageVerdict",
    "evaluate_factor_anchor_lineage_v1",
    "freeze_listing_lineage_key",
]

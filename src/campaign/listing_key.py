"""Canonical listing-lineage key encoding for the frozen campaign protocol."""

from __future__ import annotations

from datetime import date
import unicodedata


_MAGIC = b"listing_lineage_key_v1\x00"
_MAX_UINT32 = (1 << 32) - 1


def encode_listing_lineage_key_v1(
    exchange: str,
    ticker: str,
    effective_from: str,
    effective_to: str | None,
) -> bytes:
    """Encode one canonical diagnostic listing-lineage key.

    The encoding is length-prefixed and delimiter-free. It performs no
    trimming, case folding, or locale-sensitive transformation.
    """

    encoded_end = (
        b"\x00"
        if effective_to is None
        else b"\x01" + _encode_strict_date(effective_to)
    )
    return (
        _MAGIC
        + _encode_text(exchange)
        + _encode_text(ticker)
        + _encode_strict_date(effective_from)
        + encoded_end
    )


def _encode_text(value: str) -> bytes:
    if not isinstance(value, str) or not value:
        raise ValueError("listing-key text must be a nonempty string")
    normalized = unicodedata.normalize("NFC", value)
    if any(
        unicodedata.category(character).startswith("C")
        for character in normalized
    ):
        raise ValueError("listing-key text must not contain control characters")
    encoded = normalized.encode("utf-8")
    if len(encoded) > _MAX_UINT32:
        raise ValueError("listing-key text exceeds the uint32 byte-length bound")
    return len(encoded).to_bytes(4, byteorder="big", signed=False) + encoded


def _encode_strict_date(value: str) -> bytes:
    if not isinstance(value, str):
        raise ValueError("listing-key date must be strict YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            "listing-key date must be strict YYYY-MM-DD"
        ) from exc
    if len(value) != 10 or parsed.isoformat() != value:
        raise ValueError("listing-key date must be strict YYYY-MM-DD")
    return value.encode("ascii")


__all__ = ["encode_listing_lineage_key_v1"]

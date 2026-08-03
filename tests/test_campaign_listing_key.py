"""Golden and fail-closed tests for canonical listing-lineage key bytes."""

from __future__ import annotations

import pytest

from campaign.listing_key import encode_listing_lineage_key_v1


def test_listing_lineage_key_bytes_v1_golden_fixtures() -> None:
    assert encode_listing_lineage_key_v1(
        "XNYS", "BRK.B", "2014-01-01", None
    ).hex() == (
        "6c697374696e675f6c696e656167655f6b65795f763100"
        "00000004584e59530000000542524b2e42323031342d30312d303100"
    )
    decomposed = encode_listing_lineage_key_v1(
        "XNAS", "A\u030a", "2026-07-29", "2026-07-30"
    )
    assert decomposed.hex() == (
        "6c697374696e675f6c696e656167655f6b65795f763100"
        "00000004584e415300000002c385323032362d30372d3239"
        "01323032362d30372d3330"
    )
    assert decomposed == encode_listing_lineage_key_v1(
        "XNAS", "\u00c5", "2026-07-29", "2026-07-30"
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("exchange", ""),
        ("ticker", ""),
        ("exchange", "XN\x00YS"),
        ("ticker", "ABC\u200e"),
        ("effective_from", "2026-7-29"),
        ("effective_from", "2026-02-29"),
        ("effective_to", "2026-07-30T00:00:00"),
    ],
)
def test_listing_lineage_key_rejects_invalid_field_mutations(
    field: str,
    value: str,
) -> None:
    values: dict[str, object] = {
        "exchange": "XNYS",
        "ticker": "ABC",
        "effective_from": "2026-07-29",
        "effective_to": None,
    }
    values[field] = value
    with pytest.raises(ValueError):
        encode_listing_lineage_key_v1(**values)  # type: ignore[arg-type]


def test_listing_lineage_key_does_not_trim_or_case_fold() -> None:
    canonical = encode_listing_lineage_key_v1(
        "XNYS", "ABC", "2026-07-29", None
    )
    assert canonical != encode_listing_lineage_key_v1(
        "xnys", "ABC", "2026-07-29", None
    )
    assert canonical != encode_listing_lineage_key_v1(
        "XNYS", " ABC ", "2026-07-29", None
    )

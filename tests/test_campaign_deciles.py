"""Tests for the frozen high-to-low remainder-first decile procedure."""

from __future__ import annotations

import pytest

from campaign.deciles import (
    RankedListing,
    assign_deciles,
    order_eligible,
    top_decile_count,
)


def test_order_eligible_breaks_factor_ties_by_ascending_key_bytes() -> None:
    ordered = order_eligible(
        ((b"b", 1.0), (b"a", 1.0), (b"c", 2.0))
    )
    assert ordered == (
        RankedListing(b"c", 2.0),
        RankedListing(b"a", 1.0),
        RankedListing(b"b", 1.0),
    )


def test_assign_deciles_is_remainder_first_and_reports_d1_through_d10() -> None:
    ordered = order_eligible(
        (f"k{index:02d}".encode("ascii"), 100.0 - index)
        for index in range(23)
    )
    buckets = assign_deciles(ordered)

    assert tuple(bucket.label for bucket in buckets) == tuple(
        f"D{index}" for index in range(1, 11)
    )
    assert tuple(len(bucket.members) for bucket in buckets) == (
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        3,
        3,
        3,
    )
    assert tuple(item.listing_key for item in buckets[-1].members) == (
        b"k00",
        b"k01",
        b"k02",
    )
    assert tuple(item.listing_key for item in buckets[0].members) == (
        b"k21",
        b"k22",
    )


@pytest.mark.parametrize(
    ("eligible_count", "expected"),
    [(0, 0), (1, 1), (10, 1), (11, 2), (100, 10), (103, 11)],
)
def test_top_decile_count_uses_frozen_remainder_rule(
    eligible_count: int,
    expected: int,
) -> None:
    assert top_decile_count(eligible_count) == expected


def test_decile_inputs_fail_closed_on_duplicate_or_noncanonical_keys() -> None:
    with pytest.raises(ValueError, match="unique"):
        order_eligible(((b"a", 2.0), (b"a", 1.0)))
    with pytest.raises(ValueError, match="canonical"):
        assign_deciles(
            (RankedListing(b"a", 1.0), RankedListing(b"b", 2.0))
        )

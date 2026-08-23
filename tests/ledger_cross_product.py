"""Collapse independent ledger fail-closed axes without dropping either axis.

The case axis is a property of one validator kind. The representative axis is
the field or fixture that uses that kind. Full case coverage belongs on the
first representative; later representatives only need a smoke case.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar


T = TypeVar("T")
U = TypeVar("U")


def first_full_rest_smoke(
    representatives: Sequence[T],
    cases: Sequence[U],
) -> tuple[tuple[T, U], ...]:
    """Cover every case on the first representative; smoke the rest."""
    if not representatives:
        raise ValueError("representatives must not be empty")
    if not cases:
        raise ValueError("cases must not be empty")
    pairs = [(representatives[0], case) for case in cases]
    first_case = cases[0]
    pairs.extend(
        (representative, first_case)
        for representative in representatives[1:]
    )
    return tuple(pairs)

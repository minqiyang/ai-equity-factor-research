import pytest

from ledger_cross_product import first_full_rest_smoke


def test_first_representative_keeps_every_case() -> None:
    pairs = first_full_rest_smoke(("field_a", "field_b", "field_c"), (1, 2, 3))
    assert pairs == (
        ("field_a", 1),
        ("field_a", 2),
        ("field_a", 3),
        ("field_b", 1),
        ("field_c", 1),
    )
    assert len(pairs) == 3 + 3 - 1


def test_single_representative_keeps_full_case_axis() -> None:
    assert first_full_rest_smoke(("only",), ("x", "y")) == (
        ("only", "x"),
        ("only", "y"),
    )


@pytest.mark.parametrize(
    ("representatives", "cases"),
    [
        ((), ("x",)),
        (("field",), ()),
    ],
)
def test_empty_axes_fail_closed(
    representatives: tuple[str, ...], cases: tuple[str, ...]
) -> None:
    with pytest.raises(ValueError):
        first_full_rest_smoke(representatives, cases)

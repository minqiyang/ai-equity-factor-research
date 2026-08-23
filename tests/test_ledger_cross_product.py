import pytest

from ledger.schema_registry import load_registry_release
from ledger_cross_product import (
    first_full_rest_smoke,
    registry_field_constraint_kind,
    registry_requiredness_kind,
    require_equivalent_constraint_kinds,
)


def test_first_representative_keeps_every_case() -> None:
    pairs = first_full_rest_smoke(
        ("field_a", "field_b", "field_c"),
        (1, 2, 3),
        constraint_kind=lambda _: "same",
    )
    assert pairs == (
        ("field_a", 1),
        ("field_a", 2),
        ("field_a", 3),
        ("field_b", 1),
        ("field_c", 1),
    )
    assert len(pairs) == 3 + 3 - 1


def test_single_representative_keeps_full_case_axis() -> None:
    assert first_full_rest_smoke(
        ("only",),
        ("x", "y"),
        constraint_kind=lambda _: "same",
    ) == (
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
        first_full_rest_smoke(
            representatives,
            cases,
            constraint_kind=lambda _: "same",
        )


def test_mismatched_constraint_kinds_fail_closed_before_collapse() -> None:
    with pytest.raises(ValueError, match="one constraint kind"):
        first_full_rest_smoke(
            ("field_a", "field_b"),
            (1, 2, 3),
            constraint_kind=lambda field: field,
        )


def test_unknown_constraint_kind_fails_closed() -> None:
    with pytest.raises(ValueError, match="must be known"):
        first_full_rest_smoke(
            ("field_a", "field_b"),
            (1, 2),
            constraint_kind=lambda _: None,
        )


def test_require_equivalent_constraint_kinds_returns_shared_kind() -> None:
    assert (
        require_equivalent_constraint_kinds(
            ("a", "b"),
            lambda _: ("sha256",),
        )
        == ("sha256",)
    )


def test_registry_field_constraint_kind_matches_equivalent_event_ids() -> None:
    registry = load_registry_release("0.6.0")
    kinds = {
        registry_field_constraint_kind(
            registry,
            "TRIAL_ALLOCATED",
            ("payload", field),
        )
        for field in (
            "campaign_allocation_event_id",
            "experiment_allocation_event_id",
            "trial_family_source_event_id",
        )
    }
    assert len(kinds) == 1
    required, type_identity = next(iter(kinds))
    assert required is True
    assert ("kind", "typed_id") in type_identity
    assert ("prefix", "evt") in type_identity


def test_registry_field_constraint_kind_distinguishes_unrelated_kinds() -> None:
    registry = load_registry_release("0.6.0")
    event_id_kind = registry_field_constraint_kind(
        registry,
        "TRIAL_ALLOCATED",
        ("payload", "campaign_allocation_event_id"),
    )
    digest_kind = registry_field_constraint_kind(
        registry,
        "TRIAL_ALLOCATED",
        ("payload", "campaign_allocation_event_sha256"),
    )
    integer_kind = registry_field_constraint_kind(
        registry,
        "TRIAL_ALLOCATED",
        ("payload", "allocation_authority_generation"),
    )
    public_id_kind = registry_field_constraint_kind(
        registry,
        "TRIAL_ALLOCATED",
        ("payload", "allocation_authority_id"),
    )
    experiment_id_kind = registry_field_constraint_kind(
        registry,
        "TRIAL_ALLOCATED",
        ("payload", "experiment_id"),
    )
    assert len({
        event_id_kind,
        digest_kind,
        integer_kind,
        public_id_kind,
        experiment_id_kind,
    }) == 5
    with pytest.raises(ValueError, match="one constraint kind"):
        first_full_rest_smoke(
            (
                "campaign_allocation_event_id",
                "campaign_allocation_event_sha256",
            ),
            (None, True),
            constraint_kind=lambda field: registry_field_constraint_kind(
                registry,
                "TRIAL_ALLOCATED",
                ("payload", field),
            ),
        )


def test_registry_requiredness_kind_allows_same_required_envelope() -> None:
    registry = load_registry_release("0.2.0")
    paths = (("actor_id",), ("payload", "campaign_scope_ids"))
    campaign = registry_requiredness_kind(registry, "CAMPAIGN_ALLOCATED", paths)
    experiment = registry_requiredness_kind(
        registry, "EXPERIMENT_ALLOCATED", paths
    )
    assert campaign == experiment == (True, True)


def test_tagged_union_event_type_requires_branch_agreement() -> None:
    registry = load_registry_release("0.5.0")
    with pytest.raises(ValueError, match="not equivalent across union branches"):
        registry_field_constraint_kind(
            registry,
            "CAMPAIGN_ENTITY_BOUND",
            ("payload", "source_registration_event_id"),
        )


def test_tagged_union_concrete_event_selects_branch() -> None:
    registry = load_registry_release("0.5.0")
    event = {
        "event_type": "CAMPAIGN_ENTITY_BOUND",
        "subject_type": "trial_family",
        "payload": {},
    }
    required, type_identity = registry_field_constraint_kind(
        registry,
        event,
        ("payload", "source_registration_event_id"),
    )
    assert required is True
    assert ("prefix", "evt") in type_identity

"""Collapse independent ledger fail-closed axes without dropping either axis.

The case axis is a property of one validator kind. The representative axis is
the field or fixture that uses that kind. Full case coverage belongs on the
first representative; later representatives only need a smoke case.

Collapse is allowed only after every representative is proven to delegate to
the same non-null constraint kind. Unequivalent groups must use a full
Cartesian product instead of this helper.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import TypeVar


T = TypeVar("T")
U = TypeVar("U")


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        return tuple((key, _freeze(value[key])) for key in sorted(value))
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(_freeze(item) for item in value)
    return value


def _require_mapping(value: object, *, context: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{context} must be an object")
    return value


def _resolve_named(
    node: Mapping[str, object],
    definitions: Mapping[str, object],
) -> Mapping[str, object]:
    seen: set[str] = set()
    current = node
    while current.get("kind") == "named":
        name = current.get("name")
        if not isinstance(name, str) or name in seen or name not in definitions:
            raise ValueError(f"cannot resolve named type {name!r}")
        seen.add(name)
        current = _require_mapping(definitions[name], context=f"type {name}")
    return current


def _event_schema_source(
    registry: Mapping[str, object],
    source: Mapping[str, object] | str,
) -> tuple[Mapping[str, object], Mapping[str, object] | None, Mapping[str, object]]:
    if isinstance(source, str):
        event_type = source
        event_value: Mapping[str, object] | None = None
    else:
        event_type_value = source.get("event_type")
        if not isinstance(event_type_value, str):
            raise ValueError("event source must include event_type")
        event_type = event_type_value
        event_value = source
    definitions = _require_mapping(
        registry.get("type_definitions"),
        context="type_definitions",
    )
    for entry in registry.get("event_schemas", ()):
        mapping = _require_mapping(entry, context="event schema")
        if mapping.get("event_type") == event_type:
            return (
                _require_mapping(
                    mapping.get("event_schema"),
                    context=f"{event_type} event_schema",
                ),
                event_value,
                definitions,
            )
    raise ValueError(f"unknown event type {event_type!r}")


def _constraint_at(
    node: Mapping[str, object],
    path: Sequence[str],
    *,
    definitions: Mapping[str, object],
    event_value: object | None,
    required: bool,
) -> tuple[bool, object]:
    resolved = _resolve_named(node, definitions)
    if not path:
        return required, _freeze(resolved)

    kind = resolved.get("kind")
    if kind == "nullable":
        return _constraint_at(
            _require_mapping(resolved.get("schema"), context="nullable schema"),
            path,
            definitions=definitions,
            event_value=event_value,
            required=False,
        )

    if kind == "tagged_union":
        variants = _require_mapping(
            resolved.get("variants"),
            context="tagged_union variants",
        )
        discriminator = resolved.get("discriminator")
        if (
            isinstance(event_value, Mapping)
            and isinstance(discriminator, str)
            and discriminator in event_value
        ):
            tag = event_value[discriminator]
            if tag not in variants:
                raise ValueError(
                    f"unknown tagged-union branch {tag!r} for {path!r}"
                )
            return _constraint_at(
                _require_mapping(
                    variants[tag],
                    context=f"tagged_union branch {tag}",
                ),
                path,
                definitions=definitions,
                event_value=event_value,
                required=required,
            )
        kinds: list[tuple[bool, object]] = []
        for branch in variants.values():
            try:
                kinds.append(
                    _constraint_at(
                        _require_mapping(branch, context="tagged_union branch"),
                        path,
                        definitions=definitions,
                        event_value=None,
                        required=required,
                    )
                )
            except ValueError as exc:
                raise ValueError(
                    f"path {tuple(path)!r} is not equivalent across union branches"
                ) from exc
        if not kinds or any(kind_item != kinds[0] for kind_item in kinds[1:]):
            raise ValueError(
                f"path {tuple(path)!r} is not equivalent across union branches"
            )
        return kinds[0]

    if kind != "closed_object":
        raise ValueError(f"cannot walk path {tuple(path)!r} through {kind!r}")

    properties = _require_mapping(
        resolved.get("properties"),
        context="closed_object properties",
    )
    part = path[0]
    if part not in properties:
        raise ValueError(f"path {tuple(path)!r} is absent from schema")
    required_names = resolved.get("required")
    child_required = required and isinstance(required_names, Sequence) and (
        part in required_names
    )
    child_value = event_value.get(part) if isinstance(event_value, Mapping) else None
    return _constraint_at(
        _require_mapping(properties[part], context=f"property {part}"),
        path[1:],
        definitions=definitions,
        event_value=child_value,
        required=child_required,
    )


def registry_field_constraint_kind(
    registry: Mapping[str, object],
    source: Mapping[str, object] | str,
    path: Sequence[str],
) -> tuple[bool, object]:
    """Return ``(required, frozen resolved schema)`` for one registry path.

    ``source`` is either an event type or a concrete event. A concrete event
    selects tagged-union branches. An event type requires every reachable
    branch to agree.
    """
    if not path:
        raise ValueError("constraint path must not be empty")
    schema, event_value, definitions = _event_schema_source(registry, source)
    return _constraint_at(
        schema,
        path,
        definitions=definitions,
        event_value=event_value,
        required=True,
    )


def registry_requiredness_kind(
    registry: Mapping[str, object],
    source: Mapping[str, object] | str,
    paths: Sequence[Sequence[str]],
) -> tuple[bool, ...]:
    """Return requiredness for each path so missing-field groups can collapse."""
    if not paths:
        raise ValueError("requiredness paths must not be empty")
    return tuple(
        registry_field_constraint_kind(registry, source, path)[0] for path in paths
    )


def require_equivalent_constraint_kinds(
    representatives: Sequence[T],
    constraint_kind: Callable[[T], object],
) -> object:
    """Fail closed unless every representative delegates to one known kind."""
    if not representatives:
        raise ValueError("representatives must not be empty")
    kinds = [constraint_kind(representative) for representative in representatives]
    first_kind = kinds[0]
    if first_kind is None:
        raise ValueError("constraint kind must be known before collapse")
    mismatched = [
        (representative, kind)
        for representative, kind in zip(
            representatives[1:], kinds[1:], strict=True
        )
        if kind != first_kind
    ]
    if mismatched:
        raise ValueError(
            "representatives must delegate to one constraint kind before "
            f"collapse; first={first_kind!r} mismatched={mismatched!r}"
        )
    return first_kind


def first_full_rest_smoke(
    representatives: Sequence[T],
    cases: Sequence[U],
    *,
    constraint_kind: Callable[[T], object],
) -> tuple[tuple[T, U], ...]:
    """Cover every case on the first representative; smoke the rest."""
    if not representatives:
        raise ValueError("representatives must not be empty")
    if not cases:
        raise ValueError("cases must not be empty")
    require_equivalent_constraint_kinds(representatives, constraint_kind)
    pairs = [(representatives[0], case) for case in cases]
    first_case = cases[0]
    pairs.extend(
        (representative, first_case)
        for representative in representatives[1:]
    )
    return tuple(pairs)

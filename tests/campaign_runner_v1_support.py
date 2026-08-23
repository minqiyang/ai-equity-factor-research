"""Fixture loading and T-7 scan helpers for campaign runner v1 tests."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


FIXTURE_ROOT = (
    Path(__file__).resolve().parent / "fixtures" / "campaign_runner_v1"
)
CAMPAIGN_ROOT = Path(__file__).resolve().parents[1] / "src" / "campaign"


def load_runner_fixture(name: str) -> dict[str, Any]:
    """Load one committed campaign_runner_v1 JSON fixture."""

    return json_object((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def json_object(text: str) -> dict[str, Any]:
    """Parse a JSON object from committed fixture text."""

    import json

    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise TypeError("fixture root must be an object")
    return payload


def decode_fixture_anchor(item: dict[str, Any]) -> object:
    """Materialize a fixture anchor, including IEEE non-finite sentinels."""

    if "ieee" in item:
        return float(item["ieee"])
    return item["value"]


def collect_disallowed_factor_id_literals(
    factor_ids: tuple[str, ...],
) -> tuple[tuple[str, int, str], ...]:
    """Collect factor-ID string literals outside the sole allowed owner site."""

    hits: list[tuple[str, int, str]] = []
    for module_path in sorted(CAMPAIGN_ROOT.glob("*.py")):
        tree = ast.parse(
            module_path.read_text(encoding="utf-8"),
            filename=str(module_path),
        )
        docstring_nodes = _docstring_constant_ids(tree)
        allowed_nodes = _allowed_owner_constant_ids(tree, module_path.name)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant):
                continue
            if not isinstance(node.value, str) or node.value not in factor_ids:
                continue
            if id(node) in docstring_nodes or id(node) in allowed_nodes:
                continue
            hits.append((module_path.name, node.lineno, node.value))
    return tuple(hits)


def _docstring_constant_ids(tree: ast.AST) -> set[int]:
    node_ids: set[int] = set()

    def consider(body: list[ast.stmt]) -> None:
        if not body:
            return
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            node_ids.add(id(first.value))

    if isinstance(tree, ast.Module):
        consider(tree.body)
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            consider(node.body)
    return node_ids


def _allowed_owner_constant_ids(
    tree: ast.AST,
    module_name: str,
) -> set[int]:
    if module_name != "inference.py" or not isinstance(tree, ast.Module):
        return set()
    allowed: set[int] = set()
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id != "FACTOR_ORDER":
            continue
        for child in ast.walk(node):
            if isinstance(child, ast.Constant):
                allowed.add(id(child))
    return allowed

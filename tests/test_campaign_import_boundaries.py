"""AST-based package boundary checks for dataset-independent campaign code."""

from __future__ import annotations

import ast
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_ROOT = PROJECT_ROOT / "src" / "campaign"
TEST_ROOT = PROJECT_ROOT / "tests"

# Literal reviewable allowance. Widening this list is a reviewable diff.
ALLOWED_CANONICAL_NAMES = (
    "parse_json_bytes",
    "canonical_utf8",
    "canonical_sha256",
    "sha256_hex",
    "normalize_timestamp",
    "CANONICALIZATION_ID",
    "ValidationError",
)
FORBIDDEN_IMPORT_ROOTS = (
    "backtest",
    "features",
    "strategies",
    "risk",
    "data",
)
ALLOWED_CAMPAIGN_ROOTS = frozenset(sys.stdlib_module_names) | {
    "__future__",
    "campaign",
    "numpy",
}


def _import_specs(tree: ast.AST) -> tuple[tuple[ast.AST, str, frozenset[str]], ...]:
    specs: list[tuple[ast.AST, str, frozenset[str]]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                specs.append((node, alias.name, frozenset()))
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                continue
            module = "" if node.module is None else node.module
            specs.append(
                (node, module, frozenset(alias.name for alias in node.names)),
            )
    return tuple(specs)


def test_campaign_imports_only_stdlib_numpy_and_named_canonical_allowance() -> None:
    observed_modules = tuple(sorted(CAMPAIGN_ROOT.glob("*.py")))
    assert observed_modules
    allowed_canonical = frozenset(ALLOWED_CANONICAL_NAMES)

    for module_path in observed_modules:
        tree = ast.parse(
            module_path.read_text(encoding="utf-8"),
            filename=str(module_path),
        )
        for node, module, imported_names in _import_specs(tree):
            root = module.split(".", 1)[0]
            assert root not in FORBIDDEN_IMPORT_ROOTS, (
                f"{module_path.relative_to(PROJECT_ROOT)} imports forbidden "
                f"root {root}"
            )
            if module == "pit_manifest_validator_v1.canonical":
                assert isinstance(node, ast.ImportFrom), (
                    f"{module_path.name} must import canonical names"
                )
                assert module_path.name == "precondition.py", (
                    f"{module_path.name} may not import {module}"
                )
                assert imported_names <= allowed_canonical, (
                    f"{module_path.name} widens the canonical allowance "
                    f"{sorted(imported_names - allowed_canonical)}"
                )
                continue
            assert root != "pit_manifest_validator_v1", (
                f"{module_path.relative_to(PROJECT_ROOT)} imports "
                f"forbidden module {module}"
            )
            assert module != "features.validation", (
                f"{module_path.relative_to(PROJECT_ROOT)} imports "
                "forbidden features.validation"
            )
            assert root in ALLOWED_CAMPAIGN_ROOTS, (
                f"{module_path.relative_to(PROJECT_ROOT)} imports forbidden "
                f"root {root}"
            )


def test_campaign_never_imports_generic_engines_or_pr2_validator() -> None:
    forbidden_modules = (
        "backtest.portfolio",
        "backtest.metrics",
        "backtest.slippage",
        "features.validation",
        "pit_manifest_validator_v1.validator",
    )
    for module_path in sorted(CAMPAIGN_ROOT.glob("*.py")):
        tree = ast.parse(
            module_path.read_text(encoding="utf-8"),
            filename=str(module_path),
        )
        imported = {module for _, module, _ in _import_specs(tree)}
        assert imported.isdisjoint(forbidden_modules), (
            f"{module_path.name} imports {sorted(imported & set(forbidden_modules))}"
        )


def test_campaign_tests_route_assertions_through_public_campaign_entry_points() -> None:
    for path in sorted(TEST_ROOT.glob("test_campaign_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for _, module, imported_names in _import_specs(tree):
            root = module.split(".", 1)[0]
            assert root not in FORBIDDEN_IMPORT_ROOTS, (
                f"{path.name} imports forbidden root {root}"
            )
            assert module != "pit_manifest_validator_v1.validator"
            if root != "campaign":
                continue
            private_names = sorted(
                name for name in imported_names if name.startswith("_")
            )
            assert not private_names, (
                f"{path.name} imports private campaign names {private_names}"
            )


def test_campaign_public_function_parameters_are_dataset_independent() -> None:
    forbidden_parameter_tokens = {
        "calendar",
        "dataset",
        "loader",
        "manifest",
        "membership",
        "path",
    }
    for module_path in sorted(CAMPAIGN_ROOT.glob("*.py")):
        tree = ast.parse(
            module_path.read_text(encoding="utf-8"),
            filename=str(module_path),
        )
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name.startswith("_"):
                continue
            parameter_names = {
                argument.arg
                for argument in (
                    *node.args.posonlyargs,
                    *node.args.args,
                    *node.args.kwonlyargs,
                )
            }
            assert not {
                token
                for token in forbidden_parameter_tokens
                if any(token in name.lower() for name in parameter_names)
            }, f"{module_path.name}:{node.name} has a dataset-shaped parameter"

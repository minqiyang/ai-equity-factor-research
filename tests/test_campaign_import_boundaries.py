"""AST-based package boundary checks for dataset-independent campaign code."""

from __future__ import annotations

import ast
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_ROOT = PROJECT_ROOT / "src" / "campaign"


def test_campaign_imports_only_stdlib_numpy_and_local_campaign_modules() -> None:
    allowed_roots = set(sys.stdlib_module_names) | {
        "__future__",
        "campaign",
        "numpy",
    }
    allowed_canonical = {
        "parse_json_bytes",
        "canonical_utf8",
        "canonical_sha256",
        "sha256_hex",
        "normalize_timestamp",
        "CANONICALIZATION_ID",
        "ValidationError",
    }
    observed_modules = tuple(sorted(CAMPAIGN_ROOT.glob("*.py")))
    assert observed_modules

    for module_path in observed_modules:
        tree = ast.parse(
            module_path.read_text(encoding="utf-8"),
            filename=str(module_path),
        )
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules = tuple(alias.name for alias in node.names)
                imported_names: set[str] = set()
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    continue
                imported_modules = (
                    "" if node.module is None else node.module,
                )
                imported_names = {alias.name for alias in node.names}
            else:
                continue
            for module in imported_modules:
                root = module.split(".", 1)[0]
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
                assert root in allowed_roots, (
                    f"{module_path.relative_to(PROJECT_ROOT)} imports forbidden "
                    f"root {root}"
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

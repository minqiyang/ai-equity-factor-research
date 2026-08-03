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
    observed_modules = tuple(sorted(CAMPAIGN_ROOT.glob("*.py")))
    assert observed_modules

    for module_path in observed_modules:
        tree = ast.parse(
            module_path.read_text(encoding="utf-8"),
            filename=str(module_path),
        )
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {alias.name.split(".", 1)[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    continue
                roots = {
                    "" if node.module is None else node.module.split(".", 1)[0]
                }
            else:
                continue
            assert roots <= allowed_roots, (
                f"{module_path.relative_to(PROJECT_ROOT)} imports forbidden "
                f"roots {sorted(roots - allowed_roots)}"
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

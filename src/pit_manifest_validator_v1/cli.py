"""Local CLI for pit_manifest_validator_v1. No network access."""

from __future__ import annotations

import argparse
import json
import locale
import platform
import sys
from pathlib import Path
from typing import Sequence
from zoneinfo import ZoneInfoNotFoundError
from datetime import datetime, timezone

from pit_manifest_validator_v1.canonical import ValidationError, parse_json_bytes
from pit_manifest_validator_v1.validator import infer_kind, validate_bytes, validate_document


def _environment_facts() -> dict[str, str]:
    process_timezone = "UTC"
    try:
        local_tz = datetime.now().astimezone().tzinfo
        if local_tz is not None:
            process_timezone = str(local_tz)
    except (OSError, ZoneInfoNotFoundError):
        process_timezone = "UTC"
    return {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "locale": locale.getlocale()[0] or "C",
        "process_timezone": process_timezone,
        "validation_clock_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def _issue_payload(error: ValidationError) -> dict[str, str | None]:
    return {
        "code": error.code,
        "field": error.field,
        "input_id": error.input_id,
        "locator": error.locator,
    }


def _read_local_bytes(path_text: str) -> bytes:
    path = Path(path_text)
    try:
        return path.read_bytes()
    except OSError:
        raise ValidationError("INPUT_UNREADABLE", "document", locator="input_file") from None


def _emit(payload: dict[str, object], *, ok: bool) -> int:
    json.dump(payload, sys.stdout, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    sys.stdout.write("\n")
    return 0 if ok else 1


def _run_validate(kind: str | None, path_text: str) -> int:
    try:
        raw = _read_local_bytes(path_text)
        result = validate_bytes(raw, None if kind == "auto" else kind)
    except ValidationError as error:
        return _emit(
            {
                "ok": False,
                "kind": kind,
                "sha256": None,
                "errors": [_issue_payload(error)],
                "environment": _environment_facts(),
            },
            ok=False,
        )
    return _emit(
        {
            "ok": True,
            "kind": result["kind"],
            "sha256": result["sha256"],
            "errors": [],
            "environment": _environment_facts(),
        },
        ok=True,
    )


def _run_canonicalize(kind: str | None, path_text: str) -> int:
    try:
        raw = _read_local_bytes(path_text)
        parsed = parse_json_bytes(raw)
        resolved = None if kind == "auto" else kind
        if resolved is None:
            resolved = infer_kind(parsed)
        result = validate_document(parsed, resolved)
    except ValidationError as error:
        return _emit(
            {
                "ok": False,
                "kind": kind,
                "sha256": None,
                "canonical_utf8": None,
                "errors": [_issue_payload(error)],
                "environment": _environment_facts(),
            },
            ok=False,
        )
    canonical_text = result["canonical_utf8"].decode("utf-8")
    return _emit(
        {
            "ok": True,
            "kind": result["kind"],
            "sha256": result["sha256"],
            "canonical_utf8": canonical_text,
            "errors": [],
            "environment": _environment_facts(),
        },
        ok=True,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pit_manifest_validator_v1",
        description="Validate or canonicalize PIT manifest artifacts locally.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    kinds = [
        "auto",
        "pit_canonical_json_v1",
        "ordered_component_inventory_v1",
        "public_redacted_projection_v1",
        "private_full_manifest",
        "dataset_review_decision",
        "track_a_pr2_freeze_record_v1",
    ]
    validate = subparsers.add_parser("validate", help="Validate one local JSON document.")
    validate.add_argument("--kind", choices=kinds, default="auto")
    validate.add_argument("path")
    canonicalize = subparsers.add_parser(
        "canonicalize",
        help="Emit canonical UTF-8 text and SHA-256 for one local JSON document.",
    )
    canonicalize.add_argument("--kind", choices=kinds, default="auto")
    canonicalize.add_argument("path")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "validate":
        return _run_validate(args.kind, args.path)
    if args.command == "canonicalize":
        return _run_canonicalize(args.kind, args.path)
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Evidence-bundle child assembly, verification, and detached root record."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
import re
from types import MappingProxyType

from campaign.reconciliation import ReconciliationResult


_REQUIRED_CHILDREN = (
    "dataset_full_manifest.json",
    "dataset_public_projection.json",
    "eodhd_sp500_three_factor_diagnostic_v1.yaml",
    "trial_inventory.json",
    "run_manifest.json",
    "factor_diagnostics.parquet",
    "decile_returns.parquet",
    "strategy_returns.parquet",
    "baseline_comparison.json",
    "cost_sensitivity.json",
    "yearly_robustness.json",
    "invalid_and_missing_summary.json",
    "review_record.json",
)
_SELF_HASH_FIELDS = frozenset(
    {
        "bundle_manifest_sha256",
        "self_sha256",
        "manifest_sha256",
    }
)
_REASON_MISSING = "BUNDLE_CHILD_MISSING"
_REASON_SELF_HASH = "BUNDLE_MANIFEST_SELF_HASH_FORBIDDEN"
_REASON_DIGEST_MISMATCH = "BUNDLE_CHILD_DIGEST_MISMATCH"
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_FROZEN_CHILD_DIGEST_FIELDS = (
    ("eodhd_sp500_three_factor_diagnostic_v1.yaml", "protocol_file_sha256"),
    ("trial_inventory.json", "trial_inventory_file_sha256"),
)


@dataclass(frozen=True)
class BundleAssembly:
    """Verified child hashes, bundle manifest bytes, and detached root."""

    valid: bool
    reason: str | None
    child_digests: MappingProxyType[str, str]
    bundle_manifest: MappingProxyType[str, object]
    bundle_manifest_bytes: bytes
    bundle_manifest_digest: str | None
    detached_root: MappingProxyType[str, object] | None


def required_bundle_children() -> tuple[str, ...]:
    """Return the frozen required child artifact names."""

    return _REQUIRED_CHILDREN


def assemble_evidence_bundle(
    children: Mapping[str, bytes],
    root_fields: Mapping[str, object],
) -> BundleAssembly:
    """Hash every required child and emit a non-self-hashing bundle manifest."""

    if not isinstance(children, Mapping):
        raise TypeError("children must be a mapping")
    if not isinstance(root_fields, Mapping):
        raise TypeError("root_fields must be a mapping")
    digests: dict[str, str] = {}
    missing: list[str] = []
    for name in _REQUIRED_CHILDREN:
        payload = children.get(name)
        if not isinstance(payload, (bytes, bytearray)):
            missing.append(name)
            continue
        digests[name] = hashlib.sha256(bytes(payload)).hexdigest()
    if missing:
        return BundleAssembly(
            False,
            _REASON_MISSING,
            MappingProxyType(digests),
            MappingProxyType({}),
            b"",
            None,
            None,
        )
    digest_error = _frozen_child_digest_error(digests, root_fields)
    if digest_error is not None:
        return BundleAssembly(
            False,
            digest_error,
            MappingProxyType(digests),
            MappingProxyType({}),
            b"",
            None,
            None,
        )
    manifest = {
        "schema_version": "campaign_bundle_manifest_v1",
        "children": dict(digests),
        "child_order": list(_REQUIRED_CHILDREN),
        "semantic_trial_count": root_fields.get("semantic_trial_count"),
        "attempt_count": root_fields.get("attempt_count"),
        "final_state": root_fields.get("final_state"),
    }
    if _SELF_HASH_FIELDS & set(manifest):
        return BundleAssembly(
            False,
            _REASON_SELF_HASH,
            MappingProxyType(digests),
            MappingProxyType({}),
            b"",
            None,
            None,
        )
    manifest_bytes = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    manifest_digest = hashlib.sha256(manifest_bytes).hexdigest()
    detached_root = {
        "schema_version": "campaign_detached_root_v1",
        "bundle_manifest_digest": manifest_digest,
        "runner_code_sha": root_fields.get("runner_code_sha"),
        "environment_id": root_fields.get("environment_id"),
        "environment_lock_sha256": root_fields.get("environment_lock_sha256"),
        "protocol_file_sha256": root_fields.get("protocol_file_sha256"),
        "trial_inventory_file_sha256": root_fields.get("trial_inventory_file_sha256"),
        "acceptance_record_file_sha256": root_fields.get(
            "acceptance_record_file_sha256"
        ),
        "acceptance_identity_sha256": root_fields.get("acceptance_identity_sha256"),
        "semantic_trial_count": root_fields.get("semantic_trial_count"),
        "attempt_count": root_fields.get("attempt_count"),
        "per_trial_status": root_fields.get("per_trial_status"),
        "final_state": root_fields.get("final_state"),
    }
    return BundleAssembly(
        True,
        None,
        MappingProxyType(digests),
        MappingProxyType(manifest),
        manifest_bytes,
        manifest_digest,
        MappingProxyType(detached_root),
    )


def _frozen_child_digest_error(
    digests: Mapping[str, str],
    root_fields: Mapping[str, object],
) -> str | None:
    for child_name, field in _FROZEN_CHILD_DIGEST_FIELDS:
        expected = root_fields[field] if field in root_fields else None
        if not _is_sha256_digest(expected) or expected != digests[child_name]:
            return _REASON_DIGEST_MISMATCH
    return None


def _is_sha256_digest(value: object) -> bool:
    return isinstance(value, str) and _SHA256_HEX.fullmatch(value) is not None


def invalid_and_missing_bytes(result: ReconciliationResult) -> bytes:
    """Serialize the retained invalid/missing summary as JSON octets."""

    if not isinstance(result, ReconciliationResult):
        raise TypeError("result must be ReconciliationResult")
    payload = {
        "complete": result.complete,
        "reason": result.reason,
        "summary": dict(result.invalid_and_missing),
        "trials": [
            {
                "trial_id": trial.trial_id,
                "trial_type": trial.trial_type,
                "complete": trial.complete,
                "missing_names": list(trial.missing_names),
                "invalid_names": list(trial.invalid_names),
            }
            for trial in result.trials
        ],
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


__all__ = [
    "BundleAssembly",
    "assemble_evidence_bundle",
    "invalid_and_missing_bytes",
    "required_bundle_children",
]

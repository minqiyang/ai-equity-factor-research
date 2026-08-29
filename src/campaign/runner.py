"""Frozen RunConfig and authorized campaign orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from types import MappingProxyType

from campaign.bundle import (
    BundleAssembly,
    assemble_evidence_bundle,
    invalid_and_missing_bytes,
)
from campaign.inference import HOLM_ALPHA, LONG_SEGMENT_BLOCK_LENGTH
from campaign.precondition import (
    Authorization,
    authorize,
    result_bearing_refusal_reason,
)
from campaign.reconciliation import (
    ReconciliationResult,
    parse_trial_inventory,
    reconcile_semantic_trials,
)


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_FAMILYWISE_ALPHA = "0.05"
_COST_BPS = (0, 10, 25)
_BIT_GENERATOR = "PCG64DXSM"
_QUANTILE_METHOD = "linear"
_HORIZON_RETURN_ROWS = 21
_HORIZON_PURGE_ROWS = 22
_EMBARGO_ROWS = 0
_DECILE_COUNT = 10
_MIN_ELIGIBLE = 100
_MIN_DISTINCT = 10
_COMMON_MONTHS = 60
_BOOTSTRAP_REPLICATES = 20000
_RANDOM_RANK_SEED = 20260729
_BOOTSTRAP_SEED = 20260730
_STATUS_REFUSED = "REFUSED"
_STATUS_AUTHORIZED = "AUTHORIZED"
_STATUS_EXECUTED = "EXECUTED_DIAGNOSTIC_ONLY"
_EVIDENCE_CEILING = "DIAGNOSTIC_ONLY"
_RUN_RECORD_SCHEMA = "campaign_run_record_v1"
_PROTOCOL_CHILD = "eodhd_sp500_three_factor_diagnostic_v1.yaml"
_INVENTORY_CHILD = "trial_inventory.json"
_RUN_MANIFEST_CHILD = "run_manifest.json"
_INVALID_CHILD = "invalid_and_missing_summary.json"
_SENTINEL_BODY = b"STAGE4_G2_PREPARED_CAMPAIGN_NOT_BOUND_NO_PANEL_ACCESS"
_REASON_PREPARED_BYTES = "PREPARED_CAMPAIGN_BYTES_MISMATCH"
_REASON_PREPARED_SENTINEL = "PREPARED_CAMPAIGN_IS_SENTINEL"
_BOUND_FIELDS = (
    "runner_code_sha",
    "environment_id",
    "environment_lock_sha256",
    "calendar_id",
    "calendar_version",
    "protocol_file_sha256",
    "trial_inventory_file_sha256",
    "acceptance_record_file_sha256",
    "acceptance_identity_sha256",
    "prepared_campaign_file_sha256",
)


@dataclass(frozen=True)
class RunConfig:
    """Explicit frozen protocol and same-role digest bindings."""

    acceptance_record_file: str
    acceptance_record_file_sha256: str
    acceptance_identity_sha256: str
    decision_file_sha256: str
    decision_identity_sha256: str
    stage2_grant_file: str
    stage2_grant_file_sha256: str
    protocol_file: str
    protocol_file_sha256: str
    trial_inventory_file: str
    trial_inventory_file_sha256: str
    detached_binding_file: str
    runner_code_sha: str
    environment_id: str
    environment_lock_sha256: str
    calendar_id: str
    calendar_version: str
    prepared_campaign_file: str
    prepared_campaign_file_sha256: str
    horizon_return_rows: int
    horizon_purge_signal_axis_rows: int
    embargo_rows: int
    decile_count: int
    min_eligible_count: int
    min_distinct_values: int
    common_complete_case_month_floor: int
    long_segment_block_length: int
    bootstrap_replicates: int
    random_rank_seed: int
    bootstrap_seed: int
    familywise_alpha: str
    cost_bps: tuple[int, int, int]
    bit_generator: str
    quantile_method: str

    def __post_init__(self) -> None:
        for name in (
            "acceptance_record_file",
            "stage2_grant_file",
            "protocol_file",
            "trial_inventory_file",
            "runner_code_sha",
            "environment_id",
            "calendar_id",
            "calendar_version",
            "prepared_campaign_file",
            "familywise_alpha",
            "bit_generator",
            "quantile_method",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ValueError(f"{name} must be a nonempty string")
        if not isinstance(self.detached_binding_file, str):
            raise TypeError("detached_binding_file must be a string")
        for name in (
            "acceptance_record_file_sha256",
            "acceptance_identity_sha256",
            "decision_file_sha256",
            "decision_identity_sha256",
            "stage2_grant_file_sha256",
            "protocol_file_sha256",
            "trial_inventory_file_sha256",
            "environment_lock_sha256",
            "prepared_campaign_file_sha256",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
                raise ValueError(f"{name} must be a 64-hex digest")
        if _GIT_SHA_RE.fullmatch(self.runner_code_sha) is None:
            raise ValueError("runner_code_sha must be a 40-hex git object name")
        _require_int(self.horizon_return_rows, "horizon_return_rows", _HORIZON_RETURN_ROWS)
        _require_int(
            self.horizon_purge_signal_axis_rows,
            "horizon_purge_signal_axis_rows",
            _HORIZON_PURGE_ROWS,
        )
        _require_int(self.embargo_rows, "embargo_rows", _EMBARGO_ROWS)
        _require_int(self.decile_count, "decile_count", _DECILE_COUNT)
        _require_int(self.min_eligible_count, "min_eligible_count", _MIN_ELIGIBLE)
        _require_int(self.min_distinct_values, "min_distinct_values", _MIN_DISTINCT)
        _require_int(
            self.common_complete_case_month_floor,
            "common_complete_case_month_floor",
            _COMMON_MONTHS,
        )
        _require_int(
            self.long_segment_block_length,
            "long_segment_block_length",
            LONG_SEGMENT_BLOCK_LENGTH,
        )
        _require_int(
            self.bootstrap_replicates,
            "bootstrap_replicates",
            _BOOTSTRAP_REPLICATES,
        )
        _require_int(self.random_rank_seed, "random_rank_seed", _RANDOM_RANK_SEED)
        _require_int(self.bootstrap_seed, "bootstrap_seed", _BOOTSTRAP_SEED)
        if self.familywise_alpha != _FAMILYWISE_ALPHA:
            raise ValueError("familywise_alpha must equal the frozen protocol value")
        if abs(float(self.familywise_alpha) - HOLM_ALPHA) > 0.0:
            raise ValueError("familywise_alpha must equal HOLM_ALPHA")
        if tuple(self.cost_bps) != _COST_BPS:
            raise ValueError("cost_bps must equal the frozen protocol tuple")
        object.__setattr__(self, "cost_bps", tuple(self.cost_bps))
        if self.bit_generator != _BIT_GENERATOR:
            raise ValueError("bit_generator must equal the frozen protocol value")
        if self.quantile_method != _QUANTILE_METHOD:
            raise ValueError("quantile_method must equal the frozen protocol value")


@dataclass(frozen=True)
class CampaignRun:
    """Authorized diagnostic execution, or a named refusal with no outputs."""

    status: str
    reason: str | None
    authorization: Authorization
    reconciliation: ReconciliationResult | None
    bundle: BundleAssembly | None
    run_record: MappingProxyType[str, object] | None


def configuration_projection(config: RunConfig) -> dict[str, object]:
    """Return the I-JSON configuration projection with digest roles labelled."""

    if not isinstance(config, RunConfig):
        raise TypeError("config must be RunConfig")
    return {
        "horizon_return_rows": config.horizon_return_rows,
        "horizon_purge_signal_axis_rows": config.horizon_purge_signal_axis_rows,
        "embargo_rows": config.embargo_rows,
        "decile_count": config.decile_count,
        "min_eligible_count": config.min_eligible_count,
        "min_distinct_values": config.min_distinct_values,
        "common_complete_case_month_floor": config.common_complete_case_month_floor,
        "long_segment_block_length": config.long_segment_block_length,
        "bootstrap_replicates": config.bootstrap_replicates,
        "random_rank_seed": config.random_rank_seed,
        "bootstrap_seed": config.bootstrap_seed,
        "familywise_alpha": config.familywise_alpha,
        "cost_bps": list(config.cost_bps),
        "bit_generator": config.bit_generator,
        "quantile_method": config.quantile_method,
        "calendar_id": config.calendar_id,
        "calendar_version": config.calendar_version,
        "acceptance_record_file_sha256": config.acceptance_record_file_sha256,
        "acceptance_identity_sha256": config.acceptance_identity_sha256,
        "decision_file_sha256": config.decision_file_sha256,
        "decision_identity_sha256": config.decision_identity_sha256,
        "roles": {
            "acceptance_record_file_sha256": "FILE_BYTES",
            "acceptance_identity_sha256": "CANONICAL_IDENTITY",
            "decision_file_sha256": "FILE_BYTES",
            "decision_identity_sha256": "CANONICAL_IDENTITY",
            "protocol_file_sha256": "FILE_BYTES",
            "trial_inventory_file_sha256": "FILE_BYTES",
            "environment_lock_sha256": "ENV_LOCK",
            "runner_code_sha": "GIT_COMMIT",
            "prepared_campaign_file_sha256": "FILE_BYTES",
        },
        "protocol_file_sha256": config.protocol_file_sha256,
        "trial_inventory_file_sha256": config.trial_inventory_file_sha256,
        "environment_lock_sha256": config.environment_lock_sha256,
        "runner_code_sha": config.runner_code_sha,
        "environment_id": config.environment_id,
        "prepared_campaign_file_sha256": config.prepared_campaign_file_sha256,
    }


def run_campaign(config: RunConfig) -> CampaignRun:
    """Authorize the code path, then execute the diagnostic campaign once."""

    if not isinstance(config, RunConfig):
        raise TypeError("config must be RunConfig")
    authorization = authorize(config)
    if authorization.status != _STATUS_AUTHORIZED:
        return _refused(authorization, authorization.reason)
    grant = authorization.grant
    if grant is None:
        return _refused(authorization, "STAGE2_GRANT_ABSENT")
    reason = result_bearing_refusal_reason(grant)
    if reason is not None:
        return _refused(authorization, reason)
    prepared_raw = _read_prepared_octets(config.prepared_campaign_file)
    if prepared_raw is None:
        return _refused(authorization, _REASON_PREPARED_BYTES)
    if hashlib.sha256(prepared_raw).hexdigest() != config.prepared_campaign_file_sha256:
        return _refused(authorization, _REASON_PREPARED_BYTES)
    if _is_sentinel(prepared_raw):
        return _refused(authorization, _REASON_PREPARED_SENTINEL)
    started_at = _utc_now()
    inventory_raw = Path(config.trial_inventory_file).read_bytes()
    protocol_raw = Path(config.protocol_file).read_bytes()
    inventory = parse_trial_inventory(inventory_raw)
    prepared = json.loads(prepared_raw.decode("utf-8"))
    reconciliation = reconcile_semantic_trials(
        inventory,
        prepared["trial_outputs"],
        prepared["diagnostic_payload"],
    )
    trial_ids = tuple(str(trial["trial_id"]) for trial in inventory)
    binding = authorization.binding
    if binding is None:
        return _refused(authorization, "DETACHED_BINDING_ABSENT")
    bound_fields = {name: binding[name] for name in _BOUND_FIELDS}
    projection_digest = hashlib.sha256(
        json.dumps(
            configuration_projection(config),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    finished_at = _utc_now()
    run_record = {
        "schema_version": _RUN_RECORD_SCHEMA,
        "evidence_ceiling": _EVIDENCE_CEILING,
        "trials_executed": len(trial_ids),
        "trial_ids": list(trial_ids),
        "bound_fields": bound_fields,
        "configuration_projection_sha256": projection_digest,
        "started_at_utc": started_at,
        "finished_at_utc": finished_at,
    }
    children = _bundle_children(prepared, protocol_raw, inventory_raw, reconciliation)
    children[_RUN_MANIFEST_CHILD] = json.dumps(
        dict(run_record),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    bundle = assemble_evidence_bundle(
        children,
        _root_fields(config, prepared, inventory, reconciliation),
    )
    return CampaignRun(
        _STATUS_EXECUTED,
        None,
        authorization,
        reconciliation,
        bundle,
        MappingProxyType(run_record),
    )


def _refused(authorization: Authorization, reason: str | None) -> CampaignRun:
    return CampaignRun(
        _STATUS_REFUSED,
        reason,
        authorization,
        None,
        None,
        None,
    )


def _read_prepared_octets(locator: str) -> bytes | None:
    path = Path(locator)
    try:
        if not path.is_file():
            return None
        return path.read_bytes()
    except OSError:
        return None


def _is_sentinel(raw: bytes) -> bool:
    return raw == _SENTINEL_BODY or raw == _SENTINEL_BODY + b"\n"


def _utc_now() -> str:
    stamp = datetime.now(timezone.utc).replace(microsecond=0)
    return stamp.strftime("%Y-%m-%dT%H:%M:%SZ")


def _child_bytes(value: object) -> bytes:
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    if isinstance(value, str):
        return value.encode("utf-8")
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _bundle_children(
    prepared: object,
    protocol_raw: bytes,
    inventory_raw: bytes,
    reconciliation: ReconciliationResult,
) -> dict[str, bytes]:
    children: dict[str, bytes] = {
        _PROTOCOL_CHILD: protocol_raw,
        _INVENTORY_CHILD: inventory_raw,
        _INVALID_CHILD: invalid_and_missing_bytes(reconciliation),
    }
    if isinstance(prepared, dict):
        bundle_children = prepared.get("bundle_children")
        if isinstance(bundle_children, dict):
            for name, value in bundle_children.items():
                children[str(name)] = _child_bytes(value)
    return children


def _root_fields(
    config: RunConfig,
    prepared: object,
    inventory: tuple[object, ...],
    reconciliation: ReconciliationResult,
) -> dict[str, object]:
    attempt_count = 0
    if isinstance(prepared, dict):
        raw_attempt = prepared.get("attempt_count")
        if not isinstance(raw_attempt, bool) and isinstance(raw_attempt, int):
            attempt_count = raw_attempt
    if reconciliation.trials:
        statuses: list[dict[str, str]] = [
            {
                "trial_id": trial.trial_id,
                "status": "RECONCILED" if trial.complete else "INCOMPLETE",
            }
            for trial in reconciliation.trials
        ]
    else:
        statuses = [
            {
                "trial_id": str(trial["trial_id"]),
                "status": "UNRECONCILED",
            }
            for trial in inventory
            if isinstance(trial, dict)
        ]
    final_state = reconciliation.final_state
    return {
        "runner_code_sha": config.runner_code_sha,
        "environment_id": config.environment_id,
        "environment_lock_sha256": config.environment_lock_sha256,
        "protocol_file_sha256": config.protocol_file_sha256,
        "trial_inventory_file_sha256": config.trial_inventory_file_sha256,
        "acceptance_record_file_sha256": config.acceptance_record_file_sha256,
        "acceptance_identity_sha256": config.acceptance_identity_sha256,
        "semantic_trial_count": len(inventory),
        "attempt_count": attempt_count,
        "per_trial_status": statuses,
        "final_state": "" if final_state is None else str(final_state),
    }


def _require_int(value: object, name: str, expected: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value != expected:
        raise ValueError(f"{name} must equal the frozen protocol value")


__all__ = [
    "CampaignRun",
    "RunConfig",
    "configuration_projection",
    "run_campaign",
]

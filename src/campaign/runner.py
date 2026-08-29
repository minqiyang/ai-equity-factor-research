"""Frozen RunConfig and authorized campaign orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
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
_STATUS_RECONCILED = "RECONCILED_DIAGNOSTIC_ONLY"
_EVIDENCE_CEILING = "DIAGNOSTIC_ONLY"
_RUN_RECORD_SCHEMA = "campaign_run_record_v1"
_PROTOCOL_CHILD = "eodhd_sp500_three_factor_diagnostic_v1.yaml"
_INVENTORY_CHILD = "trial_inventory.json"
_RUN_MANIFEST_CHILD = "run_manifest.json"
_INVALID_CHILD = "invalid_and_missing_summary.json"
_SENTINEL_BODY = b"STAGE4_G2_PREPARED_CAMPAIGN_NOT_BOUND_NO_PANEL_ACCESS"
_REASON_PREPARED_BYTES = "PREPARED_CAMPAIGN_BYTES_MISMATCH"
_REASON_PREPARED_SENTINEL = "PREPARED_CAMPAIGN_IS_SENTINEL"
_REASON_PREPARED_UNPARSEABLE = "PREPARED_CAMPAIGN_UNPARSEABLE"
_REASON_PREPARED_SCHEMA = "PREPARED_CAMPAIGN_SCHEMA_INVALID"
_REASON_ATTEMPT_ABSENT = "CAMPAIGN_ATTEMPT_STATE_ABSENT"
_REASON_ATTEMPT_INVALID = "CAMPAIGN_ATTEMPT_STATE_INVALID"
_REASON_ATTEMPT_CONSUMED = "CAMPAIGN_ATTEMPT_ALREADY_CONSUMED"
_REASON_ATTEMPT_LEDGER = "CAMPAIGN_ATTEMPT_LEDGER_MISMATCH"
_ATTEMPT_SCHEMA = "campaign_attempt_state_v1"
_ATTEMPT_KEYS = frozenset(
    {"schema_version", "consumed", "execution_count", "grant_file_sha256"}
)
_PREPARED_REQUIRED = ("trial_outputs", "diagnostic_payload")
_CONSUMED_GRANT_DIGESTS: set[str] = set()
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
    "owner_authorization_file_sha256",
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
    owner_authorization_file_sha256: str
    attempt_state_file: str
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
            "attempt_state_file",
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
            "owner_authorization_file_sha256",
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
    """Authorized diagnostic reconciliation, or a named refusal with no outputs."""

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
            "owner_authorization_file_sha256": "FILE_BYTES",
        },
        "protocol_file_sha256": config.protocol_file_sha256,
        "trial_inventory_file_sha256": config.trial_inventory_file_sha256,
        "environment_lock_sha256": config.environment_lock_sha256,
        "runner_code_sha": config.runner_code_sha,
        "environment_id": config.environment_id,
        "prepared_campaign_file_sha256": config.prepared_campaign_file_sha256,
        "owner_authorization_file_sha256": config.owner_authorization_file_sha256,
    }


def run_campaign(config: RunConfig) -> CampaignRun:
    """Authorize, then reconcile a prepared diagnostic payload at most once."""

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
    prepared = _parse_prepared_campaign(prepared_raw)
    if isinstance(prepared, str):
        return _refused(authorization, prepared)
    inventory_raw = Path(config.trial_inventory_file).read_bytes()
    protocol_raw = Path(config.protocol_file).read_bytes()
    reconciled = _reconcile_prepared(inventory_raw, prepared)
    if isinstance(reconciled, str):
        return _refused(authorization, reconciled)
    inventory, reconciliation = reconciled
    block = grant["fourteen_trial_run_authorization"]
    assert isinstance(block, dict)
    limit = block["execution_count_limit"]
    assert isinstance(limit, int)
    consumed = _consume_attempt(
        config.attempt_state_file,
        limit,
        config.stage2_grant_file_sha256,
    )
    if isinstance(consumed, str):
        return _refused(authorization, consumed)
    started_at = _utc_now()
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
        "trials_reconciled": len(trial_ids),
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
        _root_fields(config, inventory, reconciliation, consumed),
    )
    return CampaignRun(
        _STATUS_RECONCILED,
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


def _parse_prepared_campaign(raw: bytes) -> dict[str, object] | str:
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _REASON_PREPARED_UNPARSEABLE
    if not isinstance(parsed, dict):
        return _REASON_PREPARED_SCHEMA
    for key in _PREPARED_REQUIRED:
        value = parsed.get(key)
        if not isinstance(value, dict):
            return _REASON_PREPARED_SCHEMA
    trial_outputs = parsed["trial_outputs"]
    assert isinstance(trial_outputs, dict)
    for value in trial_outputs.values():
        if not isinstance(value, dict):
            return _REASON_PREPARED_SCHEMA
        for record in value.values():
            if record is not None and not isinstance(record, dict):
                return _REASON_PREPARED_SCHEMA
    return parsed


def _reconcile_prepared(
    inventory_raw: bytes,
    prepared: dict[str, object],
) -> tuple[tuple[object, ...], ReconciliationResult] | str:
    try:
        inventory = parse_trial_inventory(inventory_raw)
        reconciliation = reconcile_semantic_trials(
            inventory,
            prepared["trial_outputs"],
            prepared["diagnostic_payload"],
        )
    except (TypeError, ValueError):
        return _REASON_PREPARED_SCHEMA
    return inventory, reconciliation


def _consume_attempt(
    locator: str,
    limit: int,
    grant_digest: str,
) -> str | int:
    if grant_digest in _CONSUMED_GRANT_DIGESTS:
        return _REASON_ATTEMPT_CONSUMED
    path = Path(locator)
    try:
        if not path.is_file():
            return _REASON_ATTEMPT_ABSENT
        fd = os.open(path, os.O_RDWR)
    except OSError:
        return _REASON_ATTEMPT_ABSENT
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        size = os.fstat(fd).st_size
        raw = os.read(fd, size) if size else b""
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return _REASON_ATTEMPT_INVALID
        if not isinstance(parsed, dict) or set(parsed) != _ATTEMPT_KEYS:
            return _REASON_ATTEMPT_INVALID
        if parsed.get("schema_version") != _ATTEMPT_SCHEMA:
            return _REASON_ATTEMPT_INVALID
        ledger_grant = parsed.get("grant_file_sha256")
        if not isinstance(ledger_grant, str) or ledger_grant != grant_digest:
            return _REASON_ATTEMPT_LEDGER
        consumed = parsed.get("consumed")
        execution_count = parsed.get("execution_count")
        if not isinstance(consumed, bool):
            return _REASON_ATTEMPT_INVALID
        if isinstance(execution_count, bool) or not isinstance(execution_count, int):
            return _REASON_ATTEMPT_INVALID
        if consumed or execution_count >= limit:
            _CONSUMED_GRANT_DIGESTS.add(grant_digest)
            return _REASON_ATTEMPT_CONSUMED
        new_count = execution_count + 1
        payload = json.dumps(
            {
                "schema_version": _ATTEMPT_SCHEMA,
                "consumed": True,
                "execution_count": new_count,
                "grant_file_sha256": grant_digest,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        os.lseek(fd, 0, os.SEEK_SET)
        os.write(fd, payload)
        os.ftruncate(fd, len(payload))
        os.fsync(fd)
        _CONSUMED_GRANT_DIGESTS.add(grant_digest)
    finally:
        os.close(fd)
    return new_count


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
    inventory: tuple[object, ...],
    reconciliation: ReconciliationResult,
    attempt_count: int,
) -> dict[str, object]:
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

"""Frozen RunConfig and authorized campaign orchestration."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json
from pathlib import Path
import re
from types import MappingProxyType

from campaign.bundle import (
    BundleAssembly,
    assemble_evidence_bundle,
    invalid_and_missing_bytes,
    required_bundle_children,
)
from campaign.inference import HOLM_ALPHA, LONG_SEGMENT_BLOCK_LENGTH
from campaign.precondition import Authorization, authorize
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
    """Authorized bundle assembly, or a named refusal with no outputs."""

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
        },
        "protocol_file_sha256": config.protocol_file_sha256,
        "trial_inventory_file_sha256": config.trial_inventory_file_sha256,
        "environment_lock_sha256": config.environment_lock_sha256,
        "runner_code_sha": config.runner_code_sha,
        "environment_id": config.environment_id,
    }


def run_campaign(config: RunConfig) -> CampaignRun:
    """Refuse unless authorize returns AUTHORIZED, then assemble the bundle."""

    if not isinstance(config, RunConfig):
        raise TypeError("config must be RunConfig")
    authorization = authorize(config)
    if authorization.status != _STATUS_AUTHORIZED:
        return CampaignRun(
            _STATUS_REFUSED,
            authorization.reason,
            authorization,
            None,
            None,
            None,
        )
    prepared = _load_prepared(config.prepared_campaign_file)
    inventory = parse_trial_inventory(Path(config.trial_inventory_file).read_bytes())
    trial_outputs = prepared["trial_outputs"]
    if not isinstance(trial_outputs, Mapping):
        raise TypeError("trial_outputs must be a mapping")
    diagnostic_payload = prepared["diagnostic_payload"]
    if not isinstance(diagnostic_payload, Mapping):
        raise TypeError("diagnostic_payload must be a mapping")
    reconciliation = reconcile_semantic_trials(
        inventory,
        trial_outputs,
        diagnostic_payload,
    )
    run_record = {
        "schema_version": "campaign_run_manifest_v1",
        "authorization_status": authorization.status,
        "configuration": configuration_projection(config),
        "semantic_trial_count": reconciliation.trial_count,
        "reconciliation_complete": reconciliation.complete,
        "final_state": reconciliation.final_state,
        "invalid_and_missing": dict(reconciliation.invalid_and_missing),
    }
    child_payloads = prepared.get("bundle_children", {})
    if not isinstance(child_payloads, Mapping):
        raise TypeError("bundle_children must be a mapping")
    children = {
        name: _child_bytes(child_payloads.get(name))
        for name in required_bundle_children()
        if name != "invalid_and_missing_summary.json"
        and name != "run_manifest.json"
        and name != "trial_inventory.json"
        and name
        != "eodhd_sp500_three_factor_diagnostic_v1.yaml"
    }
    children["trial_inventory.json"] = Path(config.trial_inventory_file).read_bytes()
    children["eodhd_sp500_three_factor_diagnostic_v1.yaml"] = Path(
        config.protocol_file
    ).read_bytes()
    children["run_manifest.json"] = json.dumps(
        run_record,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    children["invalid_and_missing_summary.json"] = invalid_and_missing_bytes(
        reconciliation
    )
    bundle = assemble_evidence_bundle(
        children,
        {
            "semantic_trial_count": reconciliation.trial_count,
            "attempt_count": prepared.get("attempt_count"),
            "final_state": reconciliation.final_state,
            "runner_code_sha": config.runner_code_sha,
            "environment_id": config.environment_id,
            "environment_lock_sha256": config.environment_lock_sha256,
            "protocol_file_sha256": config.protocol_file_sha256,
            "trial_inventory_file_sha256": config.trial_inventory_file_sha256,
            "acceptance_record_file_sha256": config.acceptance_record_file_sha256,
            "acceptance_identity_sha256": config.acceptance_identity_sha256,
            "per_trial_status": [
                {
                    "trial_id": trial.trial_id,
                    "complete": trial.complete,
                    "invalid": list(trial.invalid_names),
                }
                for trial in reconciliation.trials
            ],
        },
    )
    return CampaignRun(
        _STATUS_AUTHORIZED,
        None,
        authorization,
        reconciliation,
        bundle,
        MappingProxyType(run_record),
    )


def _load_prepared(locator: str) -> dict[str, object]:
    payload = json.loads(Path(locator).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("prepared campaign file must be an object")
    return payload


def _child_bytes(value: object) -> bytes:
    if isinstance(value, str):
        return value.encode("utf-8")
    if isinstance(value, Mapping):
        return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return json.dumps(list(value), sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    raise TypeError("bundle child must be text or a JSON value")


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

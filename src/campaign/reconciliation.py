"""Frozen 14-trial required-output reconciliation and diagnostic assembly."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json
from types import MappingProxyType

from campaign.classifier import DiagnosticInputs, DiagnosticState, classify_diagnostic
from campaign.inference import FACTOR_ORDER, FactorVector
from campaign.registry import factor_spec


_FACTOR_TYPE = "FACTOR_DIAGNOSTIC"
_STRATEGY_PREFIX = "STRATEGY_"
_CONTINUOUS = "continuous_daily_return"
_MONTHLY_RANK_IC = "monthly_rank_ic"
_REASON_COUNT = "SEMANTIC_TRIAL_COUNT_INVALID"
_REASON_ORDER = "SEMANTIC_TRIAL_INVENTORY_MISMATCH"
_REASON_MISSING = "REQUIRED_OUTPUT_MISSING"
_REASON_UNKNOWN_TYPE = "TRIAL_TYPE_UNKNOWN"


@dataclass(frozen=True)
class OutputRecord:
    """One retained trial output, present even when invalid."""

    present: bool
    valid: bool
    reason: str | None


@dataclass(frozen=True)
class TrialReconciliation:
    """One inventory trial and its retained required outputs."""

    trial_id: str
    trial_type: str
    complete: bool
    outputs: MappingProxyType[str, OutputRecord]
    missing_names: tuple[str, ...]
    invalid_names: tuple[str, ...]


@dataclass(frozen=True)
class ReconciliationResult:
    """Terminally reconciled inventory plus assembled diagnostic inputs."""

    complete: bool
    reason: str | None
    trial_count: int
    trials: tuple[TrialReconciliation, ...]
    invalid_and_missing: MappingProxyType[str, object]
    diagnostic_inputs: DiagnosticInputs | None
    final_state: DiagnosticState | None


def parse_trial_inventory(raw: bytes) -> tuple[Mapping[str, object], ...]:
    """Parse a frozen trial-inventory document into ordered trial records."""

    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("trial inventory is unparseable") from exc
    if not isinstance(parsed, dict):
        raise ValueError("trial inventory must be an object")
    trials = parsed.get("trials")
    if not isinstance(trials, list) or not trials:
        raise ValueError("trial inventory must contain trials")
    records: list[Mapping[str, object]] = []
    for item in trials:
        if not isinstance(item, dict):
            raise ValueError("each trial must be an object")
        records.append(item)
    return tuple(records)


def required_output_names(trial: Mapping[str, object]) -> tuple[str, ...]:
    """Return the frozen required output names for one inventory trial."""

    if not isinstance(trial, Mapping):
        raise TypeError("trial must be a mapping")
    declared = trial.get("output_series_per_factor")
    factor_ids = _trial_factor_ids(trial)
    if declared is not None:
        if not isinstance(declared, Sequence) or isinstance(declared, (str, bytes)):
            raise ValueError("output_series_per_factor must be a sequence")
        series = tuple(str(name) for name in declared)
        return tuple(
            f"{factor_id}:{name}" for factor_id in factor_ids for name in series
        )
    trial_type = trial.get("type")
    if trial_type == _FACTOR_TYPE:
        return tuple(f"{factor_id}:{_MONTHLY_RANK_IC}" for factor_id in factor_ids)
    if isinstance(trial_type, str) and trial_type.startswith(_STRATEGY_PREFIX):
        return tuple(f"{factor_id}:{_CONTINUOUS}" for factor_id in factor_ids)
    raise ValueError(_REASON_UNKNOWN_TYPE)


def reconcile_semantic_trials(
    inventory: Sequence[Mapping[str, object]],
    trial_outputs: Mapping[str, Mapping[str, object]],
    diagnostic_payload: Mapping[str, object],
) -> ReconciliationResult:
    """Retain every required output and assemble DiagnosticInputs."""

    if (
        isinstance(inventory, (str, bytes, bytearray))
        or not isinstance(inventory, Sequence)
    ):
        raise TypeError("inventory must be a sequence")
    if not isinstance(trial_outputs, Mapping):
        raise TypeError("trial_outputs must be a mapping")
    if not isinstance(diagnostic_payload, Mapping):
        raise TypeError("diagnostic_payload must be a mapping")

    trials = tuple(inventory)
    if len(trials) != 14:
        return _incomplete(_REASON_COUNT, trials, trial_outputs, diagnostic_payload)
    seen: set[str] = set()
    reconciled: list[TrialReconciliation] = []
    missing_total = 0
    invalid_total = 0
    for trial in trials:
        if not isinstance(trial, Mapping):
            raise TypeError("inventory trials must be mappings")
        trial_id = trial.get("trial_id")
        trial_type = trial.get("type")
        if not isinstance(trial_id, str) or not trial_id:
            raise ValueError("trial_id must be a nonempty string")
        if not isinstance(trial_type, str) or not trial_type:
            raise ValueError("type must be a nonempty string")
        if trial_id in seen:
            return _incomplete(
                _REASON_ORDER, trials, trial_outputs, diagnostic_payload
            )
        seen.add(trial_id)
        required = required_output_names(trial)
        supplied = trial_outputs.get(trial_id, {})
        if not isinstance(supplied, Mapping):
            raise TypeError("each trial output map must be a mapping")
        outputs: dict[str, OutputRecord] = {}
        missing: list[str] = []
        invalid: list[str] = []
        for name in required:
            record = _as_output(supplied.get(name))
            outputs[name] = record
            if not record.present:
                missing.append(name)
            elif not record.valid:
                invalid.append(name)
        missing_total += len(missing)
        invalid_total += len(invalid)
        reconciled.append(
            TrialReconciliation(
                trial_id=trial_id,
                trial_type=trial_type,
                complete=not missing,
                outputs=MappingProxyType(outputs),
                missing_names=tuple(missing),
                invalid_names=tuple(invalid),
            )
        )

    complete = missing_total == 0
    reason = None if complete else _REASON_MISSING
    summary = MappingProxyType(
        {
            "trial_count": len(reconciled),
            "missing_required_outputs": missing_total,
            "invalid_required_outputs": invalid_total,
            "invalid_primary_comparisons": _as_nonneg_int(
                diagnostic_payload.get("invalid_primary_comparison_count"),
                "invalid_primary_comparison_count",
            ),
            "invalid_secondary_comparisons": _as_nonneg_int(
                diagnostic_payload.get("invalid_secondary_comparison_count"),
                "invalid_secondary_comparison_count",
            ),
        }
    )
    inputs = assemble_diagnostic_inputs(diagnostic_payload, complete)
    state = classify_diagnostic(inputs)
    return ReconciliationResult(
        complete=complete,
        reason=reason,
        trial_count=len(reconciled),
        trials=tuple(reconciled),
        invalid_and_missing=summary,
        diagnostic_inputs=inputs,
        final_state=state,
    )


def assemble_diagnostic_inputs(
    payload: Mapping[str, object],
    trials_complete: bool,
) -> DiagnosticInputs:
    """Assemble classifier inputs from retained diagnostic payload fields."""

    if not isinstance(payload, Mapping):
        raise TypeError("payload must be a mapping")
    if not isinstance(trials_complete, bool):
        raise TypeError("trials_complete must be a bool")
    invalid_primary = _as_nonneg_int(
        payload.get("invalid_primary_comparison_count"),
        "invalid_primary_comparison_count",
    )
    hard_valid = (
        _as_bool(payload.get("hard_valid"), "hard_valid")
        and trials_complete
        and invalid_primary == 0
    )
    return DiagnosticInputs(
        hard_valid=hard_valid,
        prefrozen_coverage_met=_as_bool(
            payload.get("prefrozen_coverage_met"),
            "prefrozen_coverage_met",
        ),
        common_months=_as_nonneg_int(payload.get("common_months"), "common_months"),
        bootstrap_support_all_three_factors=_as_bool(
            payload.get("bootstrap_support_all_three_factors"),
            "bootstrap_support_all_three_factors",
        ),
        primary_matched_benchmark_comparisons_valid=(
            _as_bool(
                payload.get("primary_matched_benchmark_comparisons_valid"),
                "primary_matched_benchmark_comparisons_valid",
            )
            and invalid_primary == 0
        ),
        secondary_spy_comparisons_valid=_as_bool(
            payload.get("secondary_spy_comparisons_valid"),
            "secondary_spy_comparisons_valid",
        ),
        mean_rank_ics=_real_vector(payload.get("mean_rank_ics"), "mean_rank_ics"),
        holm_rejections=_bool_vector(
            payload.get("holm_rejections"),
            "holm_rejections",
        ),
        active_return_10bps=_real_vector(
            payload.get("active_return_10bps"),
            "active_return_10bps",
        ),
        active_return_25bps=_real_vector(
            payload.get("active_return_25bps"),
            "active_return_25bps",
        ),
        common_case_positive_year_fractions=_real_vector(
            payload.get("common_case_positive_year_fractions"),
            "common_case_positive_year_fractions",
        ),
        common_case_all_loyo_means_positive=_bool_vector(
            payload.get("common_case_all_loyo_means_positive"),
            "common_case_all_loyo_means_positive",
        ),
    )


def _trial_factor_ids(trial: Mapping[str, object]) -> tuple[str, ...]:
    declared = trial.get("output_factor_ids")
    if declared is not None:
        if not isinstance(declared, Sequence) or isinstance(declared, (str, bytes)):
            raise ValueError("output_factor_ids must be a sequence")
        factor_ids = tuple(str(item) for item in declared)
        if factor_ids != FACTOR_ORDER:
            raise ValueError("output_factor_ids must equal FACTOR_ORDER")
        return factor_ids
    factor_id = trial.get("factor_id")
    if not isinstance(factor_id, str):
        raise ValueError("factor_id must be a string")
    factor_spec(factor_id)
    return (factor_id,)


def _as_output(value: object) -> OutputRecord:
    if value is None:
        return OutputRecord(False, False, _REASON_MISSING)
    if not isinstance(value, Mapping):
        raise TypeError("output record must be a mapping")
    present = _as_bool(value.get("present"), "present")
    valid = _as_bool(value.get("valid"), "valid")
    reason = value.get("reason")
    if reason is not None and not isinstance(reason, str):
        raise TypeError("reason must be a string or null")
    if not present:
        return OutputRecord(False, False, reason or _REASON_MISSING)
    if not valid:
        return OutputRecord(True, False, reason)
    return OutputRecord(True, True, None)


def _incomplete(
    reason: str,
    trials: Sequence[Mapping[str, object]],
    trial_outputs: Mapping[str, Mapping[str, object]],
    diagnostic_payload: Mapping[str, object],
) -> ReconciliationResult:
    del trial_outputs, diagnostic_payload
    return ReconciliationResult(
        complete=False,
        reason=reason,
        trial_count=len(trials),
        trials=(),
        invalid_and_missing=MappingProxyType(
            {
                "trial_count": len(trials),
                "missing_required_outputs": 0,
                "invalid_required_outputs": 0,
                "invalid_primary_comparisons": 0,
                "invalid_secondary_comparisons": 0,
            }
        ),
        diagnostic_inputs=None,
        final_state="INVALID_DIAGNOSTIC",
    )


def _as_bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be a bool")
    return value


def _as_nonneg_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 0:
        raise ValueError(f"{name} must be nonnegative")
    return value


def _real_vector(value: object, name: str) -> FactorVector[float]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise TypeError(f"{name} must be a sequence")
    if len(value) != len(FACTOR_ORDER):
        raise ValueError(f"{name} must have one value per frozen factor")
    return FactorVector(
        **{
            factor_id: float(item)
            for factor_id, item in zip(FACTOR_ORDER, value, strict=True)
        }
    )


def _bool_vector(value: object, name: str) -> FactorVector[bool]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise TypeError(f"{name} must be a sequence")
    if len(value) != len(FACTOR_ORDER):
        raise ValueError(f"{name} must have one value per frozen factor")
    return FactorVector(
        **{
            factor_id: _as_bool(item, f"{name}.{factor_id}")
            for factor_id, item in zip(FACTOR_ORDER, value, strict=True)
        }
    )


__all__ = [
    "OutputRecord",
    "ReconciliationResult",
    "TrialReconciliation",
    "assemble_diagnostic_inputs",
    "parse_trial_inventory",
    "reconcile_semantic_trials",
    "required_output_names",
]

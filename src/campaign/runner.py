"""Frozen RunConfig and authorized campaign orchestration."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
from types import MappingProxyType

from campaign.baselines import (
    episode_gross_return,
    equal_weight_universe_target,
    random_rank_target,
)
from campaign.bundle import (
    BundleAssembly,
    assemble_evidence_bundle,
    invalid_and_missing_bytes,
    required_bundle_children,
)
from campaign.diagnostics import spearman_rank_ic
from campaign.eligibility import (
    DecisionTimeListing,
    FrozenDecisionTime,
    build_frozen_decision_time,
)
from campaign.inference import FACTOR_ORDER, HOLM_ALPHA, LONG_SEGMENT_BLOCK_LENGTH
from campaign.paths import advance_holdings, holding_interval
from campaign.precondition import (
    Authorization,
    authorize,
    result_bearing_refusal_reason,
)
from campaign.reconciliation import (
    ReconciliationResult,
    parse_trial_inventory,
    reconcile_semantic_trials,
    required_output_names,
)
from campaign.registry import factor_spec
from campaign.returns import simple_adjusted_close_return


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
_REASON_PREPARED_UNPARSEABLE = "PREPARED_CAMPAIGN_UNPARSEABLE"
_REASON_PREPARED_SCHEMA = "PREPARED_CAMPAIGN_SCHEMA_INVALID"
_REASON_ATTEMPT_ABSENT = "CAMPAIGN_ATTEMPT_STATE_ABSENT"
_REASON_ATTEMPT_INVALID = "CAMPAIGN_ATTEMPT_STATE_INVALID"
_REASON_ATTEMPT_CONSUMED = "CAMPAIGN_ATTEMPT_ALREADY_CONSUMED"
_REASON_ATTEMPT_LEDGER = "CAMPAIGN_ATTEMPT_LEDGER_MISMATCH"
_REASON_BUNDLE_MISSING = "BUNDLE_CHILD_MISSING"
_REASON_PROTOCOL = "PROTOCOL_FREEZE_BYTES_MISMATCH"
_REASON_INVENTORY = "TRIAL_INVENTORY_BYTES_MISMATCH"
_REASON_ZERO_TARGET = "ZERO_TARGET"
_REASON_HELD_MISSING = "HELD_RETURN_MISSING"
_REASON_OUTPUT_INVALID = "TRIAL_OUTPUT_INVALID"
_CONTINUOUS = "continuous_daily_return"
_MONTHLY_RANK_IC = "monthly_rank_ic"
_EPISODE = "episode_21_row_return"
_BASELINE_TYPE = "BASELINE"
_EQUAL_WEIGHT_TRIAL = "BASELINE_EQUAL_WEIGHT_UNIVERSE"
_RANDOM_RANK_TRIAL = "BASELINE_RANDOM_RANK_TOP_DECILE"
_EQUAL_WEIGHT_ROLE = "equal_weight_universe"
_RANDOM_RANK_SCHEME = "random_rank_v1"
_INITIAL_EQUITY = 1.0
_ATTEMPT_SCHEMA = "campaign_attempt_state_v1"
_ATTEMPT_LEDGER_DIRNAME = "campaign_attempt_ledger_v1"
_ATTEMPT_LEDGER_ROOT = (".local", "share", "equity-factor-research")
_ATTEMPT_KEYS = frozenset(
    {
        "schema_version",
        "consumed",
        "execution_count",
        "campaign_identity_sha256",
    }
)
_PREPARED_REQUIRED = frozenset({"prices", "anchors", "listings"})
_PREPARED_FORBIDDEN = frozenset(
    {
        "trial_outputs",
        "diagnostic_payload",
        "returns",
        "factors",
        "factor",
        "portfolio",
        "cumulative",
        "bundle_children",
    }
)
_RUNNER_OWNED_CHILDREN = frozenset(
    {
        _PROTOCOL_CHILD,
        _INVENTORY_CHILD,
        _INVALID_CHILD,
        _RUN_MANIFEST_CHILD,
    }
)
_LISTING_ROW_KEYS = frozenset(
    {
        "listing_key",
        "in_universe_at_t",
        "terminal_blocked_at_t",
        "lookback_addressable_at_t",
        "target_identity",
        "alias_chain",
    }
)
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
    """Authorized diagnostic execution, or a named refusal with no outputs."""

    status: str
    reason: str | None
    authorization: Authorization
    reconciliation: ReconciliationResult | None
    bundle: BundleAssembly | None
    run_record: MappingProxyType[str, object] | None


@dataclass(frozen=True)
class _ListingRow:
    listing_key: bytes
    in_universe_at_t: bool
    terminal_blocked_at_t: bool
    lookback_addressable_at_t: bool
    target_identity: MappingProxyType[str, str]
    alias_chain: tuple[MappingProxyType[str, object], ...]


@dataclass(frozen=True)
class _PreparedPanel:
    prices: MappingProxyType[bytes, MappingProxyType[str, float]]
    anchors: MappingProxyType[bytes, tuple[MappingProxyType[str, object], ...]]
    listings: MappingProxyType[str, tuple[_ListingRow, ...]]
    session_dates: tuple[str, ...]


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
    """Authorize, then execute 14 inventory trials from an input-bearing panel."""

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
    panel = _parse_prepared_campaign(prepared_raw)
    if isinstance(panel, str):
        return _refused(authorization, panel)
    protocol_raw = _bound_file_bytes(
        config.protocol_file,
        config.protocol_file_sha256,
        _REASON_PROTOCOL,
    )
    if isinstance(protocol_raw, str):
        return _refused(authorization, protocol_raw)
    inventory_raw = _bound_file_bytes(
        config.trial_inventory_file,
        config.trial_inventory_file_sha256,
        _REASON_INVENTORY,
    )
    if isinstance(inventory_raw, str):
        return _refused(authorization, inventory_raw)
    executed = _execute_prepared(config, inventory_raw, panel)
    if isinstance(executed, str):
        return _refused(authorization, executed)
    inventory, reconciliation = executed
    binding = authorization.binding
    if binding is None:
        return _refused(authorization, "DETACHED_BINDING_ABSENT")
    block = grant["fourteen_trial_run_authorization"]
    assert isinstance(block, dict)
    limit = block["execution_count_limit"]
    assert isinstance(limit, int)
    started_at = _utc_now()
    trial_ids = tuple(str(trial["trial_id"]) for trial in inventory)
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
    children = _bundle_children(protocol_raw, inventory_raw, reconciliation)
    children[_RUN_MANIFEST_CHILD] = json.dumps(
        dict(run_record),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    missing = _missing_required_children(children)
    if missing is not None:
        return _refused(authorization, missing)
    bundle = assemble_evidence_bundle(
        children,
        _root_fields(config, inventory, reconciliation, limit),
    )
    if not bundle.valid:
        reason = bundle.reason
        if reason is None:
            reason = _REASON_BUNDLE_MISSING
        return _refused(authorization, reason)
    consumed = _consume_attempt(limit, campaign_identity(binding))
    if isinstance(consumed, str):
        return _refused(authorization, consumed)
    if consumed != limit:
        bundle = assemble_evidence_bundle(
            children,
            _root_fields(config, inventory, reconciliation, consumed),
        )
        if not bundle.valid:
            reason = bundle.reason
            if reason is None:
                reason = _REASON_BUNDLE_MISSING
            return _refused(authorization, reason)
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


def _parse_prepared_campaign(raw: bytes) -> _PreparedPanel | str:
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _REASON_PREPARED_UNPARSEABLE
    if not isinstance(parsed, dict):
        return _REASON_PREPARED_SCHEMA
    if any(key in parsed for key in _PREPARED_FORBIDDEN):
        return _REASON_PREPARED_SCHEMA
    if set(parsed) != _PREPARED_REQUIRED:
        return _REASON_PREPARED_SCHEMA
    prices = _parse_prices(parsed["prices"])
    if isinstance(prices, str):
        return prices
    anchors = _parse_anchors(parsed["anchors"], set(prices))
    if isinstance(anchors, str):
        return anchors
    listings = _parse_listings(parsed["listings"], set(prices))
    if isinstance(listings, str):
        return listings
    sessions = _session_dates(prices)
    if isinstance(sessions, str):
        return sessions
    return _PreparedPanel(prices, anchors, listings, sessions)


def _execute_prepared(
    config: RunConfig,
    inventory_raw: bytes,
    panel: _PreparedPanel,
) -> tuple[tuple[object, ...], ReconciliationResult] | str:
    try:
        inventory = parse_trial_inventory(inventory_raw)
        frozen = _freeze_panel(config, panel)
        trial_outputs: dict[str, dict[str, dict[str, object]]] = {}
        for trial in inventory:
            trial_id = trial.get("trial_id")
            if not isinstance(trial_id, str) or not trial_id:
                return _REASON_PREPARED_SCHEMA
            trial_outputs[trial_id] = _execute_trial(
                config,
                trial,
                panel,
                frozen,
            )
        reconciliation = reconcile_semantic_trials(
            inventory,
            trial_outputs,
            _fail_closed_diagnostic_payload(),
        )
    except (TypeError, ValueError, KeyError):
        return _REASON_PREPARED_SCHEMA
    return inventory, reconciliation


def _parse_prices(
    raw: object,
) -> MappingProxyType[bytes, MappingProxyType[str, float]] | str:
    if not isinstance(raw, dict):
        return _REASON_PREPARED_SCHEMA
    prices: dict[bytes, MappingProxyType[str, float]] = {}
    for key, series in raw.items():
        listing_key = _parse_listing_key(key)
        if listing_key is None or not isinstance(series, dict):
            return _REASON_PREPARED_SCHEMA
        parsed_series: dict[str, float] = {}
        for session, price in series.items():
            if _invalid_session(session) or not _finite_price(price):
                return _REASON_PREPARED_SCHEMA
            parsed_series[str(session)] = float(price)
        prices[listing_key] = MappingProxyType(parsed_series)
    return MappingProxyType(prices)


def _parse_anchors(
    raw: object,
    known_keys: set[bytes],
) -> MappingProxyType[bytes, tuple[MappingProxyType[str, object], ...]] | str:
    if not isinstance(raw, dict):
        return _REASON_PREPARED_SCHEMA
    anchors: dict[bytes, tuple[MappingProxyType[str, object], ...]] = {}
    for key, records in raw.items():
        listing_key = _parse_listing_key(key)
        if listing_key is None or listing_key not in known_keys:
            return _REASON_PREPARED_SCHEMA
        if not isinstance(records, list):
            return _REASON_PREPARED_SCHEMA
        parsed_records: list[MappingProxyType[str, object]] = []
        for record in records:
            if not isinstance(record, dict):
                return _REASON_PREPARED_SCHEMA
            session = record.get("session_date")
            if _invalid_session(session):
                return _REASON_PREPARED_SCHEMA
            parsed_records.append(MappingProxyType(dict(record)))
        anchors[listing_key] = tuple(parsed_records)
    if set(anchors) != known_keys:
        return _REASON_PREPARED_SCHEMA
    return MappingProxyType(anchors)


def _parse_listings(
    raw: object,
    known_keys: set[bytes],
) -> MappingProxyType[str, tuple[_ListingRow, ...]] | str:
    if not isinstance(raw, dict):
        return _REASON_PREPARED_SCHEMA
    listings: dict[str, tuple[_ListingRow, ...]] = {}
    for signal_date, rows in raw.items():
        if _invalid_session(signal_date) or not isinstance(rows, list):
            return _REASON_PREPARED_SCHEMA
        parsed_rows: list[_ListingRow] = []
        seen: set[bytes] = set()
        for row in rows:
            parsed = _parse_listing_row(row, known_keys)
            if isinstance(parsed, str):
                return parsed
            if parsed.listing_key in seen:
                return _REASON_PREPARED_SCHEMA
            seen.add(parsed.listing_key)
            parsed_rows.append(parsed)
        listings[str(signal_date)] = tuple(parsed_rows)
    return MappingProxyType(listings)


def _parse_listing_row(raw: object, known_keys: set[bytes]) -> _ListingRow | str:
    if not isinstance(raw, dict) or set(raw) != _LISTING_ROW_KEYS:
        return _REASON_PREPARED_SCHEMA
    listing_key = _parse_listing_key(raw.get("listing_key"))
    if listing_key is None or listing_key not in known_keys:
        return _REASON_PREPARED_SCHEMA
    identity = raw.get("target_identity")
    alias_chain = raw.get("alias_chain")
    if not isinstance(identity, dict) or not isinstance(alias_chain, list):
        return _REASON_PREPARED_SCHEMA
    if any(not isinstance(item, dict) for item in alias_chain):
        return _REASON_PREPARED_SCHEMA
    in_universe = raw.get("in_universe_at_t")
    terminal = raw.get("terminal_blocked_at_t")
    lookback = raw.get("lookback_addressable_at_t")
    if not isinstance(in_universe, bool):
        return _REASON_PREPARED_SCHEMA
    if not isinstance(terminal, bool) or not isinstance(lookback, bool):
        return _REASON_PREPARED_SCHEMA
    parsed_identity = {
        str(key): str(value) for key, value in identity.items() if isinstance(value, str)
    }
    if len(parsed_identity) != len(identity):
        return _REASON_PREPARED_SCHEMA
    return _ListingRow(
        listing_key=listing_key,
        in_universe_at_t=in_universe,
        terminal_blocked_at_t=terminal,
        lookback_addressable_at_t=lookback,
        target_identity=MappingProxyType(parsed_identity),
        alias_chain=tuple(MappingProxyType(dict(item)) for item in alias_chain),
    )


def _session_dates(
    prices: Mapping[bytes, Mapping[str, float]],
) -> tuple[str, ...] | str:
    sessions: set[str] = set()
    for series in prices.values():
        sessions.update(series)
    if not sessions:
        return _REASON_PREPARED_SCHEMA
    ordered = tuple(sorted(sessions))
    if any(_invalid_session(session) for session in ordered):
        return _REASON_PREPARED_SCHEMA
    return ordered


def _freeze_panel(
    config: RunConfig,
    panel: _PreparedPanel,
) -> dict[tuple[str, str], object]:
    frozen: dict[tuple[str, str], object] = {}
    for signal_date, rows in panel.listings.items():
        for factor_id in FACTOR_ORDER:
            listings = tuple(
                _decision_listing(panel, row, signal_date, factor_id) for row in rows
            )
            frozen[(factor_id, signal_date)] = build_frozen_decision_time(
                listings,
                factor_id,
                signal_date,
                config.min_eligible_count,
                config.min_distinct_values,
            )
    return frozen


def _decision_listing(
    panel: _PreparedPanel,
    row: _ListingRow,
    signal_date: str,
    factor_id: str,
) -> DecisionTimeListing:
    selected = _select_factor_anchors(panel, row.listing_key, signal_date, factor_id)
    referenced, lineage = ((), ()) if selected is None else selected
    return DecisionTimeListing(
        listing_key=row.listing_key,
        in_universe_at_t=row.in_universe_at_t,
        terminal_blocked_at_t=row.terminal_blocked_at_t,
        lookback_addressable_at_t=row.lookback_addressable_at_t,
        referenced_anchors=referenced,
        lineage_anchors=lineage,
        target_identity=row.target_identity,
        alias_chain=row.alias_chain,
    )


def _select_factor_anchors(
    panel: _PreparedPanel,
    listing_key: bytes,
    signal_date: str,
    factor_id: str,
) -> tuple[tuple[float, ...], tuple[MappingProxyType[str, object], ...]] | None:
    spec = factor_spec(factor_id)
    try:
        signal_index = panel.session_dates.index(signal_date)
    except ValueError:
        return None
    if spec.referenced_anchor_offsets is not None:
        indexes = tuple(signal_index + offset for offset in spec.referenced_anchor_offsets)
    elif spec.required_history_price_anchor_span is not None:
        start, end = spec.required_history_price_anchor_span
        indexes = tuple(range(signal_index + start, signal_index + end + 1))
    else:
        return None
    if any(index < 0 or index >= len(panel.session_dates) for index in indexes):
        return None
    dates = tuple(panel.session_dates[index] for index in indexes)
    series = panel.prices.get(listing_key)
    records = panel.anchors.get(listing_key)
    if series is None or records is None:
        return None
    by_date = {
        str(record.get("session_date")): record
        for record in records
        if isinstance(record.get("session_date"), str)
    }
    scalars: list[float] = []
    lineage: list[MappingProxyType[str, object]] = []
    for session in dates:
        if session not in series or session not in by_date:
            return None
        scalars.append(float(series[session]))
        lineage.append(by_date[session])
    return tuple(scalars), tuple(lineage)


def _execute_trial(
    config: RunConfig,
    trial: Mapping[str, object],
    panel: _PreparedPanel,
    frozen: Mapping[tuple[str, str], object],
) -> dict[str, dict[str, object]]:
    outputs: dict[str, dict[str, object]] = {}
    for name in required_output_names(trial):
        outputs[name] = _execute_named_output(config, trial, name, panel, frozen)
    return outputs


def _execute_named_output(
    config: RunConfig,
    trial: Mapping[str, object],
    name: str,
    panel: _PreparedPanel,
    frozen: Mapping[tuple[str, str], object],
) -> dict[str, object]:
    factor_id, _, series = name.partition(":")
    if not factor_id or not series:
        return _invalid_output(_REASON_OUTPUT_INVALID)
    try:
        if series == _MONTHLY_RANK_IC:
            return _rank_ic_output(config, factor_id, panel, frozen)
        if series == _EPISODE:
            return _episode_output(config, trial, factor_id, panel, frozen)
        if series == _CONTINUOUS:
            return _continuous_output(config, trial, factor_id, panel, frozen)
    except (TypeError, ValueError, KeyError):
        return _invalid_output(_REASON_OUTPUT_INVALID)
    return _invalid_output(_REASON_OUTPUT_INVALID)


def _rank_ic_output(
    config: RunConfig,
    factor_id: str,
    panel: _PreparedPanel,
    frozen: Mapping[tuple[str, str], object],
) -> dict[str, object]:
    pairs: list[tuple[object, object]] = []
    for signal_date, rows in panel.listings.items():
        frozen_dt = frozen.get((factor_id, signal_date))
        values = _eligible_values(frozen_dt)
        horizon = _horizon_date(
            panel.session_dates,
            signal_date,
            config.horizon_return_rows,
        )
        for row in rows:
            factor_value = values.get(row.listing_key)
            if factor_value is None or horizon is None:
                pairs.append((None, None))
                continue
            held = _held_return(panel, row, signal_date, horizon)
            pairs.append(
                (
                    factor_value,
                    None if held is None or not held.valid else held.value,
                )
            )
    result = spearman_rank_ic(
        pairs,
        config.min_distinct_values,
        config.min_distinct_values,
    )
    return _from_valid(result.valid, result.reason)


def _episode_output(
    config: RunConfig,
    trial: Mapping[str, object],
    factor_id: str,
    panel: _PreparedPanel,
    frozen: Mapping[tuple[str, str], object],
) -> dict[str, object]:
    frozen_dt, signal_date = _first_frozen(factor_id, panel, frozen)
    weights = _trial_weights(config, trial, factor_id, frozen_dt, signal_date)
    horizon = None if signal_date is None else _horizon_date(
        panel.session_dates,
        signal_date,
        config.horizon_return_rows,
    )
    constituent: dict[bytes, object] = {}
    if frozen_dt is not None and signal_date is not None and horizon is not None:
        for row in panel.listings[signal_date]:
            held = _held_return(panel, row, signal_date, horizon)
            constituent[row.listing_key] = (
                None if held is None or not held.valid else held.value
            )
    result = episode_gross_return(weights, constituent)
    return _from_valid(result.valid, result.reason)


def _continuous_output(
    config: RunConfig,
    trial: Mapping[str, object],
    factor_id: str,
    panel: _PreparedPanel,
    frozen: Mapping[tuple[str, str], object],
) -> dict[str, object]:
    frozen_dt, signal_date = _first_frozen(factor_id, panel, frozen)
    weights = _trial_weights(config, trial, factor_id, frozen_dt, signal_date)
    if not weights:
        return _invalid_output(_REASON_ZERO_TARGET)
    cost = trial.get("cost_bps", 0)
    if isinstance(cost, bool) or not isinstance(cost, int):
        cost = 0
    intervals = _holding_intervals(panel, signal_date)
    if not intervals:
        return _invalid_output(_REASON_HELD_MISSING)
    holdings = advance_holdings(weights, intervals, float(cost), _INITIAL_EQUITY)
    return _from_valid(holdings.valid, holdings.reason)


def _trial_weights(
    config: RunConfig,
    trial: Mapping[str, object],
    factor_id: str,
    frozen_dt: object,
    signal_date: str | None,
) -> Mapping[bytes, float]:
    if not isinstance(frozen_dt, FrozenDecisionTime) or signal_date is None:
        return {}
    trial_type = trial.get("type")
    trial_id = trial.get("trial_id")
    if trial_type == _BASELINE_TYPE and trial_id == _EQUAL_WEIGHT_TRIAL:
        return equal_weight_universe_target(frozen_dt, _EQUAL_WEIGHT_ROLE).weights
    if trial_type == _BASELINE_TYPE and trial_id == _RANDOM_RANK_TRIAL:
        return random_rank_target(
            frozen_dt,
            factor_id,
            signal_date,
            _RANDOM_RANK_SCHEME,
            str(config.random_rank_seed),
            config.bit_generator,
        ).weights
    return frozen_dt.long_only_target


def _holding_intervals(
    panel: _PreparedPanel,
    signal_date: str | None,
) -> tuple[object, ...]:
    if signal_date is None:
        return ()
    try:
        start = panel.session_dates.index(signal_date)
    except ValueError:
        return ()
    intervals = []
    for index in range(start, len(panel.session_dates) - 1):
        begin = panel.session_dates[index]
        end = panel.session_dates[index + 1]
        held: dict[bytes, object] = {}
        rows = panel.listings.get(signal_date, ())
        for row in rows:
            result = _held_return(panel, row, begin, end)
            held[row.listing_key] = (
                None if result is None or not result.valid else result.value
            )
        intervals.append(holding_interval(end, held, None))
    return tuple(intervals)


def _held_return(
    panel: _PreparedPanel,
    row: _ListingRow,
    start_date: str,
    end_date: str,
):
    records = [
        record
        for record in panel.anchors.get(row.listing_key, ())
        if isinstance(record.get("session_date"), str)
        and start_date <= str(record["session_date"]) <= end_date
    ]
    if len(records) < 2:
        return None
    start = records[0]
    end = records[-1]
    return simple_adjusted_close_return(
        start.get("adjusted_close"),
        end.get("adjusted_close"),
        records,
        row.target_identity,
        row.alias_chain,
    )


def _first_frozen(
    factor_id: str,
    panel: _PreparedPanel,
    frozen: Mapping[tuple[str, str], object],
) -> tuple[object | None, str | None]:
    for signal_date in panel.listings:
        item = frozen.get((factor_id, signal_date))
        if item is not None:
            return item, signal_date
    return None, None


def _eligible_values(frozen_dt: object) -> dict[bytes, float]:
    if not isinstance(frozen_dt, FrozenDecisionTime):
        return {}
    values: dict[bytes, float] = {}
    for decision in frozen_dt.retained_decisions:
        if decision.eligible and decision.factor_value is not None:
            values[decision.listing_key] = float(decision.factor_value)
    return values


def _horizon_date(
    session_dates: tuple[str, ...],
    signal_date: str,
    rows: int,
) -> str | None:
    try:
        index = session_dates.index(signal_date)
    except ValueError:
        return None
    end = index + rows
    if end >= len(session_dates):
        return None
    return session_dates[end]


def _fail_closed_diagnostic_payload() -> dict[str, object]:
    zeros = [0.0, 0.0, 0.0]
    falses = [False, False, False]
    return {
        "hard_valid": False,
        "prefrozen_coverage_met": False,
        "common_months": 0,
        "bootstrap_support_all_three_factors": False,
        "primary_matched_benchmark_comparisons_valid": False,
        "secondary_spy_comparisons_valid": False,
        "mean_rank_ics": zeros,
        "holm_rejections": falses,
        "active_return_10bps": zeros,
        "active_return_25bps": zeros,
        "common_case_positive_year_fractions": zeros,
        "common_case_all_loyo_means_positive": falses,
        "invalid_primary_comparison_count": 1,
        "invalid_secondary_comparison_count": 1,
    }


def _from_valid(valid: bool, reason: str | None) -> dict[str, object]:
    if valid:
        return {"present": True, "valid": True, "reason": None}
    return {
        "present": True,
        "valid": False,
        "reason": reason or _REASON_OUTPUT_INVALID,
    }


def _invalid_output(reason: str) -> dict[str, object]:
    return {"present": True, "valid": False, "reason": reason}


def _parse_listing_key(value: object) -> bytes | None:
    if not isinstance(value, str) or len(value) < 2 or len(value) % 2:
        return None
    try:
        listing_key = bytes.fromhex(value)
    except ValueError:
        return None
    if not listing_key:
        return None
    return listing_key


def _invalid_session(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 10:
        return True
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return True
    return parsed.isoformat() != value


def _finite_price(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    numeric = float(value)
    return numeric == numeric and numeric not in {float("inf"), float("-inf")}


def campaign_identity(binding: object) -> str:
    """Return the FILE_BYTES digest of the trusted detached bound fields."""

    if not isinstance(binding, Mapping):
        raise TypeError("binding must be a mapping")
    payload = {name: binding[name] for name in _BOUND_FIELDS}
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def attempt_ledger_path(identity: str) -> Path:
    """Return the durable ledger path uniquely keyed by campaign identity."""

    if not isinstance(identity, str) or _SHA256_RE.fullmatch(identity) is None:
        raise ValueError("identity must be a 64-hex digest")
    return Path.home().joinpath(
        *_ATTEMPT_LEDGER_ROOT,
        _ATTEMPT_LEDGER_DIRNAME,
        f"{identity}.json",
    )


def _bound_file_bytes(locator: str, expected: str, reason: str) -> bytes | str:
    try:
        raw = Path(locator).read_bytes()
    except OSError:
        return reason
    if hashlib.sha256(raw).hexdigest() != expected:
        return reason
    return raw


def _missing_required_children(children: Mapping[str, bytes]) -> str | None:
    names = set(children)
    for name in required_bundle_children():
        if name not in names:
            return _REASON_BUNDLE_MISSING
    return None


def _consume_attempt(limit: int, identity: str) -> str | int:
    path = attempt_ledger_path(identity)
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
            loaded = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return _REASON_ATTEMPT_INVALID
        if not isinstance(loaded, dict):
            return _REASON_ATTEMPT_INVALID
        parsed = loaded
        if set(parsed) != _ATTEMPT_KEYS:
            return _REASON_ATTEMPT_INVALID
        if parsed.get("schema_version") != _ATTEMPT_SCHEMA:
            return _REASON_ATTEMPT_INVALID
        ledger_identity = parsed.get("campaign_identity_sha256")
        if not isinstance(ledger_identity, str) or ledger_identity != identity:
            return _REASON_ATTEMPT_LEDGER
        consumed = parsed.get("consumed")
        execution_count = parsed.get("execution_count")
        if not isinstance(consumed, bool):
            return _REASON_ATTEMPT_INVALID
        if isinstance(execution_count, bool) or not isinstance(execution_count, int):
            return _REASON_ATTEMPT_INVALID
        if execution_count < 0:
            return _REASON_ATTEMPT_INVALID
        if consumed == (execution_count == 0):
            return _REASON_ATTEMPT_INVALID
        if consumed or execution_count >= limit:
            return _REASON_ATTEMPT_CONSUMED
        new_count = execution_count + 1
        payload = json.dumps(
            {
                "schema_version": _ATTEMPT_SCHEMA,
                "consumed": True,
                "execution_count": new_count,
                "campaign_identity_sha256": identity,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        os.lseek(fd, 0, os.SEEK_SET)
        os.write(fd, payload)
        os.ftruncate(fd, len(payload))
        os.fsync(fd)
    finally:
        os.close(fd)
    return new_count


def _utc_now() -> str:
    stamp = datetime.now(timezone.utc).replace(microsecond=0)
    return stamp.strftime("%Y-%m-%dT%H:%M:%SZ")


def _bundle_children(
    protocol_raw: bytes,
    inventory_raw: bytes,
    reconciliation: ReconciliationResult,
) -> dict[str, bytes]:
    children: dict[str, bytes] = {}
    for name in required_bundle_children():
        if name in _RUNNER_OWNED_CHILDREN:
            continue
        children[name] = json.dumps(
            {"name": name, "schema_version": "campaign_execution_child_v1"},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    children[_PROTOCOL_CHILD] = protocol_raw
    children[_INVENTORY_CHILD] = inventory_raw
    children[_INVALID_CHILD] = invalid_and_missing_bytes(reconciliation)
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
                "status": "EXECUTED" if trial.complete else "FAIL_CLOSED",
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
    "attempt_ledger_path",
    "campaign_identity",
    "configuration_projection",
    "run_campaign",
]

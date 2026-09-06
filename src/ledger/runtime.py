"""Track B v7 Path A/B sqlite3 ledger runtime.

Caller-supplied database path, stdlib sqlite3, and synthetic catalogs only.
Evidence ceiling is DIAGNOSTIC_ONLY. Path A stops before ACCESS_COMPLETED.
Path B first checkpoint appends ATTEMPT_ALLOCATED then ATTEMPT_STARTED after
inventory/seal. It does not append retry, terminal attempt, ACCESS_COMPLETED,
or EXPOSURE_DECISION.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import re
import sqlite3
from pathlib import Path
import threading
from typing import Any, Callable

from ledger.schema_registry import (
    LedgerSchemaError,
    _same_json_value,
    load_registry_release,
    validate_raw_event_bytes,
)


SELECTED_14 = (
    "LEDGER_EPOCH_CREATED",
    "CAMPAIGN_ALLOCATED",
    "EXPERIMENT_ALLOCATED",
    "TRIAL_FAMILY_REGISTERED",
    "SAMPLE_REGISTERED",
    "CAMPAIGN_ENTITY_BOUND",
    "STAGE3_SAMPLE_REFERENCE_BOUND",
    "TRIAL_ALLOCATED",
    "CAMPAIGN_INVENTORY_SEALED",
    "ATTEMPT_ALLOCATED",
    "ATTEMPT_STARTED",
    "ACCESS_INTENT",
    "ACCESS_STARTED",
    "ACCESS_COMPLETED",
)
PATH_A_EVENT_TYPES = frozenset(
    {
        "LEDGER_EPOCH_CREATED",
        "CAMPAIGN_ALLOCATED",
        "EXPERIMENT_ALLOCATED",
        "TRIAL_FAMILY_REGISTERED",
        "SAMPLE_REGISTERED",
        "TRIAL_ALLOCATED",
        "CAMPAIGN_INVENTORY_SEALED",
        "ACCESS_INTENT",
        "ACCESS_STARTED",
    }
)
PATH_B_EVENT_TYPES = PATH_A_EVENT_TYPES | frozenset(
    {
        "ATTEMPT_ALLOCATED",
        "ATTEMPT_STARTED",
    }
)
OPERATIONAL_VALUE_FIELDS = (
    "code_identity",
    "environment_id",
    "environment_lock_sha256",
    "input_manifest_sha256",
    "retry_policy_sha256",
    "expected_output_inventory_sha256",
)
COMMIT_OWNED_FIELDS = frozenset(
    {
        "sequence",
        "recorded_at",
        "previous_event_sha256",
        "operation_request_sha256",
    }
)
OPERATION_REQUEST_KEYS = (
    "operation_request_projection_id",
    "ledger_schema_version",
    "event_schema_version",
    "canonicalization_id",
    "identity_projection_id",
    "ledger_id",
    "event_id",
    "operation_id",
    "event_type",
    "subject_type",
    "subject_id",
    "occurred_at",
    "actor_id",
    "payload",
)
REGISTRY_VERSION = "0.10.0"
DEFAULT_CAPABILITY_EXPIRY = "2099-01-01T00:00:00Z"
_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS events (
    sequence INTEGER PRIMARY KEY,
    event_id TEXT NOT NULL UNIQUE,
    operation_id TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL,
    subject_type TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    event_sha256 TEXT NOT NULL UNIQUE,
    operation_request_sha256 TEXT NOT NULL,
    event_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS stream_head (
    ledger_id TEXT PRIMARY KEY,
    sequence INTEGER NOT NULL,
    event_id TEXT NOT NULL,
    event_sha256 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS entities (
    entity_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    allocated_sequence INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS origins (
    sample_id TEXT PRIMARY KEY,
    origin_event_type TEXT NOT NULL,
    canonical_lineage_id TEXT NOT NULL,
    record_identity_sha256 TEXT NOT NULL,
    origin_event_id TEXT NOT NULL,
    origin_event_sha256 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS capabilities (
    capability_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    record_json TEXT NOT NULL,
    record_sha256 TEXT NOT NULL,
    consumed INTEGER NOT NULL DEFAULT 0,
    minted_event_id TEXT,
    consumed_event_id TEXT
);
CREATE TABLE IF NOT EXISTS campaign_seal_head (
    campaign_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    event_sha256 TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    sealed_trial_ids_json TEXT NOT NULL
);
"""


class LedgerRuntimeError(ValueError):
    """Fail-closed Path A/B runtime refusal."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class Clock:
    """UTC clock used to fix transaction as_of after BEGIN IMMEDIATE."""

    def now_utc(self) -> str:
        stamp = datetime.now(timezone.utc).replace(microsecond=0)
        return stamp.strftime("%Y-%m-%dT%H:%M:%SZ")


class FixedClock(Clock):
    """Deterministic clock for synthetic Path A/B tests."""

    def __init__(self, stamp: str) -> None:
        self.stamp = stamp

    def now_utc(self) -> str:
        return self.stamp


def canonical_json_bytes(value: object) -> bytes:
    """Return pit_canonical_json_v1 ASCII bytes for a JSON-compatible value."""
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def digest_json(value: object) -> str:
    """Return the lowercase SHA-256 of canonical JSON bytes."""
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


_CANONICAL_UTC = "%Y-%m-%dT%H:%M:%SZ"
_ACTOR_ID_PATTERN = re.compile(r"act_[0-9a-f]{32}\Z")


def _parse_canonical_utc(value: object, *, code: str) -> datetime:
    """Parse a canonical UTC instant YYYY-MM-DDTHH:MM:SSZ. Offset/malformed fail."""
    if not isinstance(value, str):
        _fail(code, "timestamp must be a canonical UTC string")
    try:
        parsed = datetime.strptime(value, _CANONICAL_UTC)
    except ValueError:
        _fail(code, "timestamp is not canonical UTC")
        raise
    return parsed.replace(tzinfo=timezone.utc)


def _canonical_interval_active(
    record: "CatalogRecord", as_of_dt: datetime, *, code: str
) -> bool:
    """True when as_of is inside a canonical [valid_from, valid_until) interval."""
    from_dt = _parse_canonical_utc(record.valid_from, code=code)
    until_dt = None
    if record.valid_until is not None:
        until_dt = _parse_canonical_utc(record.valid_until, code=code)
    return as_of_dt >= from_dt and (until_dt is None or as_of_dt < until_dt)


def _fail(code: str, message: str) -> None:
    raise LedgerRuntimeError(code, message)


def _require_mapping(value: object, *, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail("INVALID_OPERATION_REQUEST", f"{context} must be an object")
    return value


def _campaign_id(payload: dict[str, Any]) -> str:
    scope = payload.get("campaign_scope_ids")
    if not isinstance(scope, list) or len(scope) != 1 or not isinstance(scope[0], str):
        _fail("RECORD_CONTENT_MISMATCH", "campaign_scope_ids must be a singleton")
    return scope[0]


@dataclass
class CatalogRecord:
    """One synthetic catalog record with owner-stream currentness."""

    kind: str
    record_id: str
    schema_version: str
    sha256: str
    body: dict[str, Any]
    generation: int | None = None
    version: int | None = None
    status: str = "accepted"
    valid_from: str = "1970-01-01T00:00:00Z"
    valid_until: str | None = None
    stream_key: str = ""
    authority_id: str = ""
    registry_sha256: str = ""
    authority_version: int = 1
    canonicalization_id: str = "pit_canonical_json_v1"

    def active_at(self, as_of: str) -> bool:
        if as_of < self.valid_from:
            return False
        if self.valid_until is not None and as_of >= self.valid_until:
            return False
        return True


@dataclass
class SyntheticCatalog:
    """In-memory synthetic catalog. Not a production authority source."""

    records: list[CatalogRecord] = field(default_factory=list)
    evidence_refs: set[str] = field(default_factory=set)
    proven_digests: set[str] = field(default_factory=set)
    capability_activation: str | None = None
    capability_expiry: str | None = None
    _lock: threading.RLock = field(default_factory=threading.RLock)

    def add(self, record: CatalogRecord) -> CatalogRecord:
        with self._lock:
            if not record.sha256:
                record.sha256 = digest_json(record.body)
            if not record.stream_key:
                record.stream_key = f"{record.kind}:{record.record_id}"
            self.records.append(record)
            return record

    def snapshot(self) -> SyntheticCatalog:
        """Return a stable copy of catalog bytes for one append transaction."""
        frozen = SyntheticCatalog()
        frozen.records = deepcopy(self.records)
        frozen.evidence_refs = set(self.evidence_refs)
        frozen.proven_digests = set(self.proven_digests)
        frozen.capability_activation = self.capability_activation
        frozen.capability_expiry = self.capability_expiry
        return frozen

    def get(
        self,
        kind: str,
        record_id: str,
        sha256: str,
        *,
        generation: int | None = None,
        version: int | None = None,
    ) -> CatalogRecord | None:
        matches = [
            item
            for item in self.records
            if item.kind == kind
            and item.record_id == record_id
            and (generation is None or _same_json_value(item.generation, generation))
            and (version is None or _same_json_value(item.version, version))
        ]
        if len(matches) != 1:
            return None
        item = matches[0]
        body_digest = digest_json(item.body)
        if item.sha256 != body_digest or body_digest != sha256:
            _fail(
                "RECORD_CONTENT_MISMATCH",
                "catalog digest does not match record bytes",
            )
        return item

    def stream(self, stream_key: str) -> list[CatalogRecord]:
        return [item for item in self.records if item.stream_key == stream_key]


class LedgerStore:
    """Path A/B append-only sqlite3 ledger with synthetic catalog currentness."""

    def __init__(
        self,
        database_path: str | Path,
        catalog: SyntheticCatalog,
        *,
        clock: Clock | None = None,
        checkpoint: str = "path_a",
        inject_access_started_failure: bool = False,
        inject_catalog_mutation: Callable[[], None] | None = None,
    ) -> None:
        if checkpoint not in {"path_a", "path_b"}:
            _fail("INVALID_OPERATION_REQUEST", f"unknown checkpoint {checkpoint}")
        self.database_path = Path(database_path).expanduser()
        self.catalog = catalog
        self._tx_catalog: SyntheticCatalog | None = None
        self.clock = clock or Clock()
        self.checkpoint = checkpoint
        self.inject_access_started_failure = inject_access_started_failure
        self.inject_catalog_mutation = inject_catalog_mutation
        self.registry = load_registry_release(REGISTRY_VERSION)
        self._assert_path_outside_repository(self.database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(
            str(self.database_path),
            isolation_level=None,
            check_same_thread=False,
            timeout=30.0,
        )
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(_SCHEMA_SQL)

    def close(self) -> None:
        self._conn.close()

    def events(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT event_json FROM events ORDER BY sequence"
        ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def event_by_id(self, event_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT event_json FROM events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def capability(self, capability_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT record_json, consumed FROM capabilities WHERE capability_id = ?",
            (capability_id,),
        ).fetchone()
        if row is None:
            return None
        record = json.loads(row[0])
        record["consumed"] = bool(row[1])
        return record

    def consume_execute(
        self,
        *,
        capability_id: str,
        consumer_actor_id: str,
        trial_id: str,
        attempt_id: str,
        code_tree_sha256: str,
        environment_id: str,
        environment_lock_sha256: str,
    ) -> dict[str, Any]:
        """Consume the one-shot EXECUTE capability minted with ATTEMPT_STARTED."""
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            row = self._conn.execute(
                "SELECT record_json, consumed, kind FROM capabilities "
                "WHERE capability_id = ?",
                (capability_id,),
            ).fetchone()
            if row is None:
                _fail("PARENT_EVENT_MISSING", "EXECUTE capability was not minted")
            record = json.loads(row[0])
            if row[2] != "EXECUTE":
                _fail("RECORD_CONTENT_MISMATCH", "capability is not an EXECUTE capability")
            if row[1]:
                _fail(
                    "EXECUTE_CAPABILITY_ALREADY_CONSUMED",
                    "EXECUTE capability already consumed",
                )
            if record.get("executor_actor_id") != consumer_actor_id:
                _fail(
                    "CAPABILITY_CONSUMER_MISMATCH",
                    "EXECUTE consumer is not the readiness executor",
                )
            if (
                record.get("trial_id") != trial_id
                or record.get("attempt_id") != attempt_id
                or record.get("code_tree_sha256") != code_tree_sha256
                or record.get("environment_id") != environment_id
                or record.get("environment_lock_sha256") != environment_lock_sha256
            ):
                _fail(
                    "RECORD_CONTENT_MISMATCH",
                    "EXECUTE consume does not bind trial, attempt, code, and environment",
                )
            as_of = self.clock.now_utc()
            activation = record.get("activation")
            expiry = record.get("expiry")
            as_of_dt = _parse_canonical_utc(
                as_of, code="EXECUTE_CAPABILITY_TIMESTAMP_INVALID"
            )
            activation_dt = _parse_canonical_utc(
                activation, code="EXECUTE_CAPABILITY_TIMESTAMP_INVALID"
            )
            expiry_dt = _parse_canonical_utc(
                expiry, code="EXECUTE_CAPABILITY_TIMESTAMP_INVALID"
            )
            if as_of_dt < activation_dt:
                _fail(
                    "EXECUTE_CAPABILITY_NOT_ACTIVE",
                    "EXECUTE capability is not yet active",
                )
            if as_of_dt >= expiry_dt:
                _fail(
                    "EXECUTE_CAPABILITY_EXPIRED",
                    "EXECUTE capability has expired",
                )
            updated = self._conn.execute(
                "UPDATE capabilities SET consumed = 1 WHERE capability_id = ? "
                "AND consumed = 0",
                (capability_id,),
            ).rowcount
            if updated != 1:
                _fail(
                    "EXECUTE_CAPABILITY_ALREADY_CONSUMED",
                    "EXECUTE consume did not land",
                )
            self._conn.execute("COMMIT")
            record["consumed"] = True
            return record
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def append(self, request: object) -> dict[str, Any]:
        raw_request = _require_mapping(request, context="operation request")
        for forbidden in COMMIT_OWNED_FIELDS:
            if forbidden in raw_request:
                _fail(
                    "OPERATION_REQUEST_COMMIT_FIELD_FORBIDDEN",
                    f"caller supplied store-owned field {forbidden}",
                )
        event_type = raw_request.get("event_type")
        if not isinstance(event_type, str):
            _fail("INVALID_OPERATION_REQUEST", "event_type must be a string")
        if event_type not in SELECTED_14:
            vocabulary = set(self.registry["closed_event_vocabulary"])
            if event_type not in vocabulary:
                _fail("UNKNOWN_EVENT_TYPE", f"unknown ledger event type: {event_type}")
            _fail(
                "WIRE_TYPE_NOT_SELECTED",
                f"event type is outside the selected 14-wire budget: {event_type}",
            )
        allowed = (
            PATH_A_EVENT_TYPES if self.checkpoint == "path_a" else PATH_B_EVENT_TYPES
        )
        if event_type not in allowed:
            if event_type == "ACCESS_COMPLETED" and self.checkpoint == "path_a":
                _fail(
                    "PATH_A_STOPS_BEFORE_ACCESS_COMPLETED",
                    "Path A first checkpoint does not append ACCESS_COMPLETED",
                )
            code = (
                "PATH_A_CHECKPOINT_EXCLUDES_EVENT"
                if self.checkpoint == "path_a"
                else "PATH_B_CHECKPOINT_EXCLUDES_EVENT"
            )
            label = "Path A" if self.checkpoint == "path_a" else "Path B"
            _fail(code, f"{label} first checkpoint does not append {event_type}")
        payload = _require_mapping(raw_request.get("payload"), context="payload")
        if event_type in {"ACCESS_INTENT", "ACCESS_STARTED"}:
            refs = payload.get("evidence_ref_ids")
            if refs == []:
                _fail(
                    f"{event_type}_EVIDENCE_REF_SET_EMPTY",
                    "evidence_ref_ids must be nonempty",
                )
        if event_type == "ACCESS_INTENT" and payload.get("affected_trial_ids") == []:
            _fail(
                "ACCESS_INTENT_AFFECTED_TRIAL_SET_EMPTY",
                "affected_trial_ids must be a nonempty sealed subset",
            )

        self._conn.execute("BEGIN IMMEDIATE")
        self.catalog._lock.acquire()
        try:
            as_of = self.clock.now_utc()
            self._tx_catalog = self.catalog.snapshot()
            result = self._append_locked(raw_request, event_type, as_of)
            self._conn.execute("COMMIT")
            return result
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        finally:
            self._tx_catalog = None
            self.catalog._lock.release()

    def _append_locked(
        self,
        request: dict[str, Any],
        event_type: str,
        as_of: str,
    ) -> dict[str, Any]:
        existing = self._replay_if_duplicate(request)
        if existing is not None:
            return existing
        handlers: dict[str, Callable[[dict[str, Any], str], None]] = {
            "LEDGER_EPOCH_CREATED": self._check_epoch,
            "CAMPAIGN_ALLOCATED": self._check_campaign,
            "EXPERIMENT_ALLOCATED": self._check_experiment,
            "TRIAL_FAMILY_REGISTERED": self._check_family,
            "SAMPLE_REGISTERED": self._check_sample,
            "TRIAL_ALLOCATED": self._check_trial,
            "CAMPAIGN_INVENTORY_SEALED": self._check_seal,
            "ATTEMPT_ALLOCATED": self._check_attempt_allocated,
            "ATTEMPT_STARTED": self._check_attempt_started,
            "ACCESS_INTENT": self._check_access_intent,
            "ACCESS_STARTED": self._check_access_started,
        }
        handlers[event_type](request, as_of)
        extra_insert: Callable[[dict[str, Any], str], None] | None = None
        if event_type == "ACCESS_INTENT":
            extra_insert = self._mint_access_capability
        elif event_type == "ACCESS_STARTED":
            extra_insert = self._consume_access_capability
        elif event_type == "ATTEMPT_STARTED":
            extra_insert = self._mint_execute_capability
        return self._commit_event(request, as_of, extra_insert=extra_insert)

    @property
    def _active_catalog(self) -> SyntheticCatalog:
        if self._tx_catalog is not None:
            return self._tx_catalog
        return self.catalog

    def _replay_if_duplicate(self, request: dict[str, Any]) -> dict[str, Any] | None:
        operation_id = request.get("operation_id")
        event_id = request.get("event_id")
        if not isinstance(operation_id, str) or not isinstance(event_id, str):
            _fail("INVALID_OPERATION_REQUEST", "operation_id and event_id are required")
        request_digest = digest_json(self._operation_request_object(request))
        row = self._conn.execute(
            "SELECT event_json, operation_request_sha256, event_id, event_sha256 "
            "FROM events WHERE operation_id = ? OR event_id = ?",
            (operation_id, event_id),
        ).fetchone()
        if row is None:
            return None
        event_json, stored_digest, stored_event_id, event_sha256 = row
        if stored_digest != request_digest or stored_event_id != event_id:
            _fail(
                "OPERATION_REQUEST_CONFLICT",
                "operation or event identity reused with different request bytes",
            )
        event = json.loads(event_json)
        event["event_sha256"] = event_sha256
        return event

    def _operation_request_object(self, request: dict[str, Any]) -> dict[str, Any]:
        missing = [key for key in OPERATION_REQUEST_KEYS if key not in request]
        if missing:
            _fail(
                "INVALID_OPERATION_REQUEST",
                f"missing operation request fields: {missing}",
            )
        extra = [
            key
            for key in request
            if key not in OPERATION_REQUEST_KEYS and key not in COMMIT_OWNED_FIELDS
        ]
        if extra:
            _fail(
                "INVALID_OPERATION_REQUEST",
                f"unknown operation request fields: {extra}",
            )
        return {key: request[key] for key in OPERATION_REQUEST_KEYS}

    def _commit_event(
        self,
        request: dict[str, Any],
        as_of: str,
        *,
        extra_insert: Callable[[dict[str, Any], str], None] | None = None,
    ) -> dict[str, Any]:
        if self.inject_catalog_mutation is not None:
            self.inject_catalog_mutation()
        ledger_id = request["ledger_id"]
        head = self._stream_head(ledger_id)
        if request["event_type"] == "LEDGER_EPOCH_CREATED":
            sequence = 0
            previous = None
        else:
            if head is None:
                _fail("PARENT_EVENT_MISSING", "ledger epoch has not been created")
            sequence = head["sequence"] + 1
            previous = head["event_sha256"]
        event = {
            "actor_id": request["actor_id"],
            "canonicalization_id": "pit_canonical_json_v1",
            "event_id": request["event_id"],
            "event_schema_version": "ledger_event_v1",
            "event_type": request["event_type"],
            "identity_projection_id": "ledger_event_identity_v1",
            "ledger_id": ledger_id,
            "ledger_schema_version": "experiment_trial_ledger_v1",
            "occurred_at": request["occurred_at"],
            "operation_id": request["operation_id"],
            "operation_request_projection_id": "ledger_operation_request_v1",
            "operation_request_sha256": digest_json(
                self._operation_request_object(request)
            ),
            "payload": request["payload"],
            "previous_event_sha256": previous,
            "recorded_at": as_of,
            "sequence": sequence,
            "subject_id": request["subject_id"],
            "subject_type": request["subject_type"],
        }
        if extra_insert is not None and request["event_type"] == "ACCESS_STARTED":
            extra_insert(event, digest_json(event))
            if self.inject_access_started_failure:
                _fail("INJECTED_APPEND_REFUSAL", "test-injected ACCESS_STARTED failure")
        try:
            validate_raw_event_bytes(
                canonical_json_bytes(event),
                registry=self.registry,
            )
        except LedgerSchemaError as exc:
            _fail(exc.code, exc.message)
        event_sha256 = digest_json(event)
        if extra_insert is not None and request["event_type"] in {
            "ACCESS_INTENT",
            "ATTEMPT_STARTED",
        }:
            extra_insert(event, event_sha256)
        self._conn.execute(
            "INSERT INTO events ("
            "sequence, event_id, operation_id, event_type, subject_type, "
            "subject_id, recorded_at, event_sha256, operation_request_sha256, "
            "event_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                sequence,
                event["event_id"],
                event["operation_id"],
                event["event_type"],
                event["subject_type"],
                event["subject_id"],
                as_of,
                event_sha256,
                event["operation_request_sha256"],
                json.dumps(event, sort_keys=True, separators=(",", ":")),
            ),
        )
        self._conn.execute(
            "INSERT INTO stream_head (ledger_id, sequence, event_id, event_sha256) "
            "VALUES (?, ?, ?, ?) ON CONFLICT(ledger_id) DO UPDATE SET "
            "sequence = excluded.sequence, event_id = excluded.event_id, "
            "event_sha256 = excluded.event_sha256",
            (ledger_id, sequence, event["event_id"], event_sha256),
        )
        if event["event_type"] in {
            "LEDGER_EPOCH_CREATED",
            "CAMPAIGN_ALLOCATED",
            "EXPERIMENT_ALLOCATED",
            "TRIAL_FAMILY_REGISTERED",
            "SAMPLE_REGISTERED",
            "TRIAL_ALLOCATED",
            "ATTEMPT_ALLOCATED",
        }:
            try:
                self._conn.execute(
                    "INSERT INTO entities (entity_id, entity_type, allocated_sequence) "
                    "VALUES (?, ?, ?)",
                    (event["subject_id"], event["subject_type"], sequence),
                )
            except sqlite3.IntegrityError:
                _fail(
                    f"{event['subject_type'].upper()}_ID_ALREADY_ALLOCATED"
                    if event["subject_type"] != "sample"
                    else "SAMPLE_ID_ALREADY_ALLOCATED",
                    f"{event['subject_id']} is already allocated",
                )
        if event["event_type"] == "SAMPLE_REGISTERED":
            self._insert_origin(event, event_sha256)
        if event["event_type"] == "CAMPAIGN_INVENTORY_SEALED":
            campaign_id = _campaign_id(event["payload"])
            sealed_ids = self._sealed_trial_ids_from_inventory(event["payload"])
            self._conn.execute(
                "INSERT INTO campaign_seal_head ("
                "campaign_id, event_id, event_sha256, sequence, sealed_trial_ids_json) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    campaign_id,
                    event["event_id"],
                    event_sha256,
                    sequence,
                    json.dumps(sealed_ids),
                ),
            )
        committed = dict(event)
        committed["event_sha256"] = event_sha256
        return committed

    def _stream_head(self, ledger_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT sequence, event_id, event_sha256 FROM stream_head WHERE ledger_id = ?",
            (ledger_id,),
        ).fetchone()
        if row is None:
            return None
        return {"sequence": row[0], "event_id": row[1], "event_sha256": row[2]}

    def _require_event(
        self,
        event_id: str,
        event_sha256: str,
        *,
        event_type: str | None = None,
        subject_id: str | None = None,
    ) -> dict[str, Any]:
        row = self._conn.execute(
            "SELECT event_json, event_sha256 FROM events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        if row is None:
            _fail("PARENT_EVENT_MISSING", f"missing parent event {event_id}")
        event = json.loads(row[0])
        if row[1] != event_sha256 or digest_json(event) != event_sha256:
            _fail("RECORD_CONTENT_MISMATCH", "retained source event digest mismatch")
        if event_type is not None and event["event_type"] != event_type:
            _fail("RECORD_CONTENT_MISMATCH", "retained source event type mismatch")
        if subject_id is not None and event["subject_id"] != subject_id:
            _fail("RECORD_CONTENT_MISMATCH", "retained source subject mismatch")
        return event

    def _entity(self, entity_id: str, entity_type: str) -> None:
        row = self._conn.execute(
            "SELECT entity_type FROM entities WHERE entity_id = ?",
            (entity_id,),
        ).fetchone()
        if row is None:
            _fail("PARENT_EVENT_MISSING", f"unallocated {entity_type} {entity_id}")
        if row[0] != entity_type:
            _fail("RECORD_CONTENT_MISMATCH", "allocated entity type mismatch")

    def _unused_entity(self, entity_id: str, *, sample: bool = False) -> None:
        row = self._conn.execute(
            "SELECT entity_id FROM entities WHERE entity_id = ?",
            (entity_id,),
        ).fetchone()
        if row is not None:
            code = "SAMPLE_ID_ALREADY_ALLOCATED" if sample else "ENTITY_ID_ALREADY_ALLOCATED"
            _fail(code, f"{entity_id} is already allocated")

    def _check_epoch(self, request: dict[str, Any], as_of: str) -> None:
        del as_of
        ledger_id = request["ledger_id"]
        if self._stream_head(ledger_id) is not None:
            _fail("LEDGER_EPOCH_ALREADY_CREATED", "ledger epoch already exists")
        if request["payload"].get("campaign_scope_ids") != []:
            _fail("RECORD_CONTENT_MISMATCH", "epoch campaign_scope_ids must be empty")
        if request["subject_type"] != "ledger" or request["subject_id"] != ledger_id:
            _fail("RECORD_CONTENT_MISMATCH", "epoch subject must equal ledger_id")

    def _check_campaign(self, request: dict[str, Any], as_of: str) -> None:
        del as_of
        self._require_epoch(request)
        campaign_id = request["subject_id"]
        self._unused_entity(campaign_id)
        if request["subject_type"] != "campaign":
            _fail("RECORD_CONTENT_MISMATCH", "campaign subject_type mismatch")
        if request["payload"] != {"campaign_scope_ids": [campaign_id]}:
            _fail("RECORD_CONTENT_MISMATCH", "campaign allocation is reservation-only")

    def _check_experiment(self, request: dict[str, Any], as_of: str) -> None:
        del as_of
        self._require_epoch(request)
        campaign_id = _campaign_id(request["payload"])
        self._entity(campaign_id, "campaign")
        self._unused_entity(request["subject_id"])
        if request["subject_type"] != "experiment":
            _fail("RECORD_CONTENT_MISMATCH", "experiment subject_type mismatch")
        extra = set(request["payload"]) - {"campaign_scope_ids"}
        if extra:
            _fail("RECORD_CONTENT_MISMATCH", "experiment allocation is reservation-only")

    def _check_family(self, request: dict[str, Any], as_of: str) -> None:
        self._require_epoch(request)
        payload = request["payload"]
        self._unused_entity(request["subject_id"])
        definition = self._resolve_family_definition(payload)
        acceptance = self._resolve_family_acceptance(payload)
        self._require_current(
            acceptance, as_of, event_type="TRIAL_FAMILY_REGISTERED", kind="acceptance"
        )
        self._assert_content_scope(
            definition.body,
            request["subject_id"],
            payload.get("campaign_scope_ids"),
            family_id_key="trial_family_id",
        )
        issuer = definition.body["issuer_actor_id"]
        reviewer = acceptance.body["reviewer_actor_id"]
        if acceptance.body.get("issuer_actor_id") != issuer:
            _fail("RECORD_CONTENT_MISMATCH", "family acceptance issuer mismatch")
        self._require_distinct(
            {
                "issuer": issuer,
                "reviewer": reviewer,
                "actor": request["actor_id"],
            },
            "TRIAL_FAMILY_REGISTERED_ROLE_COLLISION",
        )
        self._exclude_private_producers(
            reviewer,
            definition.body.get("private_input_producer_actor_ids") or [],
            "TRIAL_FAMILY_REGISTERED_PRIVATE_INPUT_PRODUCER_ROLE_COLLISION",
        )
        for campaign_id in payload.get("campaign_scope_ids") or []:
            self._entity(campaign_id, "campaign")

    def _check_sample(self, request: dict[str, Any], as_of: str) -> None:
        self._require_epoch(request)
        payload = request["payload"]
        sample_id = request["subject_id"]
        self._unused_entity(sample_id, sample=True)
        record = self._resolve_sample_record(payload)
        acceptance = self._resolve_sample_acceptance(payload)
        projection = self._resolve_sample_projection(payload)
        approval = self._resolve_sample_publication_approval(payload)
        if "canonical_sample_lineage_id" not in record.body:
            _fail(
                "SAMPLE_REGISTERED_LINEAGE_REQUIRED",
                "resolved local record lacks canonical_sample_lineage_id",
            )
        self._require_current(
            acceptance, as_of, event_type="SAMPLE_REGISTERED", kind="acceptance"
        )
        self._require_current(
            projection,
            as_of,
            event_type="SAMPLE_REGISTERED",
            kind="projection",
        )
        self._require_current(
            approval,
            as_of,
            event_type="SAMPLE_REGISTERED",
            kind="publication_approval",
        )
        self._check_origin_uniqueness(
            "SAMPLE_REGISTERED",
            sample_id,
            record,
            payload,
        )
        if projection.body.get("sample_id") != sample_id:
            _fail("RECORD_CONTENT_MISMATCH", "sample projection sample_id mismatch")
        if (
            projection.body.get("sample_record_id") != payload["sample_record_id"]
            or projection.body.get("sample_record_sha256") != payload["sample_record_sha256"]
        ):
            _fail("RECORD_CONTENT_MISMATCH", "sample projection record binding mismatch")
        if (
            approval.body.get("sample_id") != sample_id
            or approval.body.get("sample_public_projection_id")
            != payload["sample_public_projection_id"]
            or approval.body.get("sample_public_projection_schema_version")
            != payload["sample_public_projection_schema_version"]
            or approval.body.get("sample_public_projection_sha256")
            != payload["sample_public_projection_sha256"]
            or approval.body.get("outcome") != "approved"
        ):
            _fail(
                "RECORD_CONTENT_MISMATCH",
                "publication approval does not bind this sample projection",
            )
        self._assert_content_scope(
            record.body,
            sample_id,
            payload.get("campaign_scope_ids"),
            sample_id_key="sample_id",
        )
        producer = record.body["producer_actor_id"]
        reviewer = acceptance.body["reviewer_actor_id"]
        if acceptance.body.get("producer_actor_id") != producer:
            _fail("RECORD_CONTENT_MISMATCH", "sample acceptance producer mismatch")
        self._require_distinct(
            {
                "producer": producer,
                "reviewer": reviewer,
                "actor": request["actor_id"],
            },
            "SAMPLE_REGISTERED_ROLE_COLLISION",
        )
        self._exclude_private_producers(
            reviewer,
            record.body.get("private_input_producer_actor_ids") or [],
            "SAMPLE_REGISTERED_PRIVATE_INPUT_PRODUCER_ROLE_COLLISION",
        )
        for campaign_id in payload.get("campaign_scope_ids") or []:
            self._entity(campaign_id, "campaign")

    def _check_trial(self, request: dict[str, Any], as_of: str) -> None:
        self._require_epoch(request)
        payload = request["payload"]
        trial_id = request["subject_id"]
        self._unused_entity(trial_id)
        campaign_id = _campaign_id(payload)
        campaign_event = self._require_event(
            payload["campaign_allocation_event_id"],
            payload["campaign_allocation_event_sha256"],
            event_type="CAMPAIGN_ALLOCATED",
            subject_id=campaign_id,
        )
        experiment_event = self._require_event(
            payload["experiment_allocation_event_id"],
            payload["experiment_allocation_event_sha256"],
            event_type="EXPERIMENT_ALLOCATED",
            subject_id=payload["experiment_id"],
        )
        if _campaign_id(experiment_event["payload"]) != campaign_id:
            _fail("RECORD_CONTENT_MISMATCH", "experiment campaign scope mismatch")
        family_event = self._require_event(
            payload["trial_family_source_event_id"],
            payload["trial_family_source_event_sha256"],
            event_type="TRIAL_FAMILY_REGISTERED",
            subject_id=payload["trial_family_id"],
        )
        del campaign_event
        self._revalidate_family(family_event, as_of, "TRIAL_ALLOCATED")
        definition = self._revalidate_trial_definition(payload, trial_id, campaign_id, as_of)
        for binding in definition.body.get("sample_bindings") or []:
            sample_event = self._require_event(
                binding["source_event_id"],
                binding["source_event_sha256"],
                event_type="SAMPLE_REGISTERED",
                subject_id=binding["sample_id"],
            )
            self._revalidate_sample(sample_event, as_of, "TRIAL_ALLOCATED")
        relation = payload.get("relation") or {}
        if relation.get("relation_kind") != "original":
            _fail("RECORD_CONTENT_MISMATCH", "Path A allocates original trials only")
        if payload["code_identity"] != definition.body.get("code_identity"):
            _fail(
                "RECORD_CONTENT_MISMATCH",
                "payload code_identity does not match trial definition",
            )
        self._prove_code_digest(payload["code_identity"])
        issuer = definition.body["issuer_actor_id"]
        acceptance = self._resolve_trial_acceptance(payload)
        reviewer = acceptance.body["reviewer_actor_id"]
        allocator = request["actor_id"]
        self._require_distinct(
            {"issuer": issuer, "reviewer": reviewer, "actor": allocator},
            "TRIAL_ALLOCATED_ROLE_COLLISION",
        )
        producers = definition.body.get("private_input_producer_actor_ids") or []
        self._exclude_private_producers(
            reviewer,
            producers,
            "TRIAL_ALLOCATED_PRIVATE_INPUT_PRODUCER_ROLE_COLLISION",
        )
        self._exclude_private_producers(
            allocator,
            producers,
            "TRIAL_ALLOCATED_PRIVATE_INPUT_PRODUCER_ROLE_COLLISION",
        )
        authority = self._resolve_trial_allocation_authority(payload)
        self._require_current(
            authority, as_of, event_type="TRIAL_ALLOCATED", kind="authority"
        )
        if authority.body.get("authorized_actor_id") != allocator:
            _fail(
                "TRIAL_ALLOCATED_AUTHORITY_ACTOR_MISMATCH",
                "allocation actor is not the authorized actor",
            )
        if (
            authority.body.get("operation") != "TRIAL_ALLOCATED"
            or authority.body.get("campaign_id") != campaign_id
            or authority.body.get("trial_id") != trial_id
            or authority.body.get("trial_definition_record_id")
            != payload["trial_definition_record_id"]
            or authority.body.get("trial_definition_record_sha256")
            != payload["trial_definition_record_sha256"]
        ):
            _fail(
                "RECORD_CONTENT_MISMATCH",
                "allocation authority does not bind this trial allocation",
            )

    def _check_seal(self, request: dict[str, Any], as_of: str) -> None:
        self._require_epoch(request)
        payload = request["payload"]
        campaign_id = _campaign_id(payload)
        campaign_event = self._require_event(
            payload["campaign_allocation_event_id"],
            payload["campaign_allocation_event_sha256"],
            event_type="CAMPAIGN_ALLOCATED",
            subject_id=campaign_id,
        )
        del campaign_event
        existing = self._conn.execute(
            "SELECT campaign_id FROM campaign_seal_head WHERE campaign_id = ?",
            (campaign_id,),
        ).fetchone()
        if existing is not None:
            _fail("CAMPAIGN_INVENTORY_SEALED_DUPLICATE", "campaign already sealed")
        inventory = self._resolve_inventory_record(payload)
        acceptance = self._resolve_inventory_acceptance(payload)
        authority = self._resolve_seal_authority(payload)
        self._require_current(
            acceptance, as_of, event_type="CAMPAIGN_INVENTORY_SEALED", kind="acceptance"
        )
        self._require_current(
            authority, as_of, event_type="CAMPAIGN_INVENTORY_SEALED", kind="authority"
        )
        if digest_json(inventory.body) != payload["sealed_trial_inventory_sha256"]:
            _fail("RECORD_CONTENT_MISMATCH", "inventory digest mismatch")
        trials = inventory.body.get("trials") or []
        trial_ids = [entry["trial_id"] for entry in trials]
        if sorted(trial_ids) != sorted(set(trial_ids)):
            _fail("RECORD_CONTENT_MISMATCH", "inventory trial ids must be unique")
        if len(trial_ids) != payload["sealed_semantic_trial_count"]:
            _fail("RECORD_CONTENT_MISMATCH", "sealed trial count is not set equality")
        if inventory.body.get("campaign_id") != campaign_id:
            _fail("RECORD_CONTENT_MISMATCH", "inventory campaign mismatch")
        head = self._stream_head(request["ledger_id"])
        assert head is not None
        preseal = payload["preseal_head"]
        if (
            preseal["ledger_id"] != request["ledger_id"]
            or preseal["predecessor_sequence"] != head["sequence"]
            or preseal["predecessor_event_sha256"] != head["event_sha256"]
        ):
            _fail(
                "CAMPAIGN_INVENTORY_SEALED_PRESEAL_HEAD_MISMATCH",
                "claimed pre-seal head is not the current stream head",
            )
        included_issuers: list[str] = []
        for entry in trials:
            trial_event = self._require_event(
                entry["trial_allocation_event_id"],
                entry["trial_allocation_event_sha256"],
                event_type="TRIAL_ALLOCATED",
                subject_id=entry["trial_id"],
            )
            if _campaign_id(trial_event["payload"]) != campaign_id:
                _fail("RECORD_CONTENT_MISMATCH", "sealed trial campaign mismatch")
            self._revalidate_trial_event(trial_event, as_of, "CAMPAIGN_INVENTORY_SEALED")
            definition = self._resolve_trial_definition(trial_event["payload"])
            included_issuers.append(definition.body["issuer_actor_id"])
        inventory_issuer = inventory.body["issuer_actor_id"]
        inventory_reviewer = acceptance.body["reviewer_actor_id"]
        seal_authority_issuer = authority.body["issuer_actor_id"]
        seal_actor = request["actor_id"]
        authorized = authority.body["authorized_actor_id"]
        if seal_actor != authorized:
            _fail(
                "CAMPAIGN_INVENTORY_SEALED_AUTHORITY_ACTOR_MISMATCH",
                "seal actor is not the authorized seal actor",
            )
        prohibited = [
            (inventory_reviewer, inventory_issuer),
            (inventory_reviewer, seal_authority_issuer),
            (inventory_reviewer, seal_actor),
            (inventory_issuer, seal_actor),
        ]
        for left, right in prohibited:
            if left == right:
                _fail(
                    "CAMPAIGN_INVENTORY_SEALED_ROLE_COLLISION",
                    "inventory seal roles are not independent",
                )
        if inventory_reviewer in included_issuers:
            _fail(
                "CAMPAIGN_INVENTORY_SEALED_ROLE_COLLISION",
                "inventory reviewer equals an included trial-definition issuer",
            )
        self._exclude_private_producers(
            inventory_reviewer,
            inventory.body.get("private_input_producer_actor_ids") or [],
            "CAMPAIGN_INVENTORY_SEALED_PRIVATE_INPUT_PRODUCER_ROLE_COLLISION",
        )

    def _check_attempt_allocated(self, request: dict[str, Any], as_of: str) -> None:
        self._require_epoch(request)
        payload = request["payload"]
        attempt_id = request["subject_id"]
        if request["subject_type"] != "attempt":
            _fail("RECORD_CONTENT_MISMATCH", "attempt subject_type mismatch")
        self._unused_entity(attempt_id)
        campaign_id = _campaign_id(payload)
        trial_id = payload["trial_id"]
        relation = payload.get("relation") or {}
        if (
            relation.get("attempt_kind") != "first_attempt"
            or not _same_json_value(relation.get("attempt_ordinal"), 1)
        ):
            _fail(
                "ATTEMPT_ALLOCATED_RETRY_NOT_SELECTED",
                "Path B first checkpoint does not append retry attempts",
            )
        seal = self._current_seal(campaign_id)
        if (
            payload["campaign_inventory_seal_event_id"] != seal["event_id"]
            or payload["campaign_inventory_seal_event_sha256"] != seal["event_sha256"]
        ):
            _fail(
                "ATTEMPT_ALLOCATED_SEAL_NOT_CURRENT",
                "referenced seal is not the current seal head",
            )
        if trial_id not in seal["sealed_trial_ids"]:
            _fail(
                "ATTEMPT_ALLOCATED_TRIAL_NOT_IN_SEAL",
                "requested trial is absent from sealed_trial_ids",
            )
        if self._attempts_for_trial(trial_id):
            _fail(
                "ATTEMPT_ALLOCATED_NOT_FIRST",
                "Path B allocates the first attempt only",
            )
        trial_event = self._require_event(
            payload["trial_allocation_event_id"],
            payload["trial_allocation_event_sha256"],
            event_type="TRIAL_ALLOCATED",
            subject_id=trial_id,
        )
        if _campaign_id(trial_event["payload"]) != campaign_id:
            _fail("RECORD_CONTENT_MISMATCH", "trial campaign scope mismatch")
        self._revalidate_trial_event(trial_event, as_of, "ATTEMPT_ALLOCATED")
        definition = self._revalidate_trial_definition(
            trial_event["payload"],
            trial_id,
            campaign_id,
            as_of,
            event_type="ATTEMPT_ALLOCATED",
        )
        plan = self._resolve_attempt_plan(payload)
        plan_acceptance = self._resolve_attempt_plan_acceptance(payload)
        authority = self._resolve_attempt_allocation_authority(payload)
        self._require_current(
            plan, as_of, event_type="ATTEMPT_ALLOCATED", kind="plan"
        )
        self._require_current(
            plan_acceptance, as_of, event_type="ATTEMPT_ALLOCATED", kind="acceptance"
        )
        self._require_current(
            authority, as_of, event_type="ATTEMPT_ALLOCATED", kind="authority"
        )
        if (
            plan.body.get("trial_id") != trial_id
            or plan.body.get("attempt_id") != attempt_id
            or plan.body.get("campaign_id") != campaign_id
            or plan.body.get("ledger_id") != request["ledger_id"]
            or plan.body.get("trial_allocation_event_id")
            != payload["trial_allocation_event_id"]
            or plan.body.get("trial_allocation_event_sha256")
            != payload["trial_allocation_event_sha256"]
            or plan.body.get("campaign_inventory_seal_event_id")
            != payload["campaign_inventory_seal_event_id"]
            or plan.body.get("campaign_inventory_seal_event_sha256")
            != payload["campaign_inventory_seal_event_sha256"]
            or not _same_json_value(plan.body.get("relation"), payload.get("relation"))
        ):
            _fail("RECORD_CONTENT_MISMATCH", "attempt plan does not bind this attempt")
        if self._operational_values(plan.body) != self._operational_values(
            definition.body
        ):
            _fail(
                "RECORD_CONTENT_MISMATCH",
                "attempt plan operational values do not match trial definition",
            )
        if payload["expected_output_inventory_sha256"] != plan.body.get(
            "expected_output_inventory_sha256"
        ):
            _fail(
                "RECORD_CONTENT_MISMATCH",
                "expected_output_inventory_sha256 does not match attempt plan",
            )
        self._prove_code_digest(plan.body["code_identity"])
        if authority.body.get("authorized_actor_id") != request["actor_id"]:
            _fail(
                "ATTEMPT_ALLOCATED_AUTHORITY_ACTOR_MISMATCH",
                "allocation actor is not the authorized actor",
            )
        if (
            authority.body.get("operation") != "ATTEMPT_ALLOCATED"
            or authority.body.get("campaign_id") != campaign_id
            or authority.body.get("trial_id") != trial_id
            or authority.body.get("attempt_id") != attempt_id
            or authority.body.get("attempt_plan_authority_id")
            != payload["attempt_plan_authority_id"]
            or authority.body.get("attempt_plan_authority_registry_sha256")
            != payload["attempt_plan_authority_registry_sha256"]
            or not _same_json_value(
                authority.body.get("attempt_plan_authority_version"),
                payload["attempt_plan_authority_version"],
            )
            or authority.body.get("attempt_plan_record_id")
            != payload["attempt_plan_record_id"]
            or authority.body.get("attempt_plan_record_schema_version")
            != payload["attempt_plan_record_schema_version"]
            or not _same_json_value(
                authority.body.get("attempt_plan_record_version"),
                payload["attempt_plan_record_version"],
            )
            or authority.body.get("attempt_plan_record_canonicalization_id")
            != payload["attempt_plan_record_canonicalization_id"]
            or authority.body.get("attempt_plan_record_sha256")
            != payload["attempt_plan_record_sha256"]
            or authority.body.get("ledger_id") != request["ledger_id"]
        ):
            _fail(
                "RECORD_CONTENT_MISMATCH",
                "attempt allocation authority does not bind this allocation",
            )
        if plan_acceptance.body.get("reviewer_actor_id") is None:
            _fail("RECORD_CONTENT_MISMATCH", "attempt plan acceptance reviewer missing")
        if (
            plan_acceptance.body.get("attempt_id") != attempt_id
            or plan_acceptance.body.get("trial_id") != trial_id
            or plan_acceptance.body.get("campaign_id") != campaign_id
            or plan_acceptance.body.get("campaign_scope_ids") != [campaign_id]
            or plan_acceptance.body.get("attempt_plan_record_id")
            != payload["attempt_plan_record_id"]
            or plan_acceptance.body.get("attempt_plan_record_sha256")
            != payload["attempt_plan_record_sha256"]
            or plan_acceptance.body.get("attempt_plan_authority_id")
            != payload["attempt_plan_authority_id"]
            or plan_acceptance.body.get("attempt_plan_authority_registry_sha256")
            != payload["attempt_plan_authority_registry_sha256"]
            or not _same_json_value(
                plan_acceptance.body.get("attempt_plan_authority_version"),
                payload["attempt_plan_authority_version"],
            )
            or plan_acceptance.body.get("attempt_plan_record_schema_version")
            != payload["attempt_plan_record_schema_version"]
            or not _same_json_value(
                plan_acceptance.body.get("attempt_plan_record_version"),
                payload["attempt_plan_record_version"],
            )
            or plan_acceptance.body.get("attempt_plan_record_canonicalization_id")
            != payload["attempt_plan_record_canonicalization_id"]
            or not _same_json_value(
                plan_acceptance.body.get("relation"), payload.get("relation")
            )
            or plan_acceptance.body.get("campaign_inventory_seal_event_id")
            != payload["campaign_inventory_seal_event_id"]
            or plan_acceptance.body.get("campaign_inventory_seal_event_sha256")
            != payload["campaign_inventory_seal_event_sha256"]
            or plan_acceptance.body.get("trial_allocation_event_id")
            != payload["trial_allocation_event_id"]
            or plan_acceptance.body.get("trial_allocation_event_sha256")
            != payload["trial_allocation_event_sha256"]
            or plan_acceptance.body.get("ledger_id") != request["ledger_id"]
        ):
            _fail(
                "RECORD_CONTENT_MISMATCH",
                "attempt plan acceptance does not bind this plan, attempt, trial, seal, and scope",
            )
        issuer = plan.body["issuer_actor_id"]
        reviewer = plan_acceptance.body["reviewer_actor_id"]
        trial_issuer = definition.body["issuer_actor_id"]
        allocator = request["actor_id"]
        self._require_distinct(
            {
                "plan_issuer": issuer,
                "plan_reviewer": reviewer,
                "trial_issuer": trial_issuer,
                "actor": allocator,
            },
            "ATTEMPT_ALLOCATED_ROLE_COLLISION",
        )
        producers = self._require_private_input_producer_ids(
            plan.body, "ATTEMPT_ALLOCATED"
        )
        self._exclude_private_producers(
            reviewer,
            producers,
            "ATTEMPT_ALLOCATED_PRIVATE_INPUT_PRODUCER_ROLE_COLLISION",
        )
        self._exclude_private_producers(
            allocator,
            producers,
            "ATTEMPT_ALLOCATED_PRIVATE_INPUT_PRODUCER_ROLE_COLLISION",
        )

    def _check_attempt_started(self, request: dict[str, Any], as_of: str) -> None:
        self._require_epoch(request)
        payload = request["payload"]
        attempt_id = request["subject_id"]
        if request["subject_type"] != "attempt":
            _fail("RECORD_CONTENT_MISMATCH", "attempt subject_type mismatch")
        campaign_id = _campaign_id(payload)
        trial_id = payload["trial_id"]
        allocation = self._require_event(
            payload["attempt_allocation_event_id"],
            payload["attempt_allocation_event_sha256"],
            event_type="ATTEMPT_ALLOCATED",
            subject_id=attempt_id,
        )
        if allocation["payload"]["trial_id"] != trial_id:
            _fail("RECORD_CONTENT_MISMATCH", "start trial does not match allocation")
        if _campaign_id(allocation["payload"]) != campaign_id:
            _fail("RECORD_CONTENT_MISMATCH", "start campaign does not match allocation")
        if self._has_attempt_start(attempt_id):
            _fail("ATTEMPT_STARTED_ALREADY_STARTED", "attempt already started")
        seal = self._current_seal(campaign_id)
        if (
            allocation["payload"]["campaign_inventory_seal_event_id"] != seal["event_id"]
            or allocation["payload"]["campaign_inventory_seal_event_sha256"]
            != seal["event_sha256"]
        ):
            _fail(
                "ATTEMPT_STARTED_SEAL_NOT_CURRENT",
                "seal head is no longer current",
            )
        if trial_id not in seal["sealed_trial_ids"]:
            _fail(
                "ATTEMPT_STARTED_TRIAL_NOT_IN_SEAL",
                "trial is absent from the current sealed set",
            )
        seal_event = self._require_event(seal["event_id"], seal["event_sha256"])
        inventory = self._resolve_inventory_record(seal_event["payload"])
        inventory_acceptance = self._resolve_inventory_acceptance(seal_event["payload"])
        self._require_current(
            inventory_acceptance,
            as_of,
            event_type="ATTEMPT_STARTED",
            kind="acceptance",
        )
        trial_event = self._require_event(
            allocation["payload"]["trial_allocation_event_id"],
            allocation["payload"]["trial_allocation_event_sha256"],
            event_type="TRIAL_ALLOCATED",
            subject_id=trial_id,
        )
        self._revalidate_trial_event(trial_event, as_of, "ATTEMPT_STARTED")
        definition = self._revalidate_trial_definition(
            trial_event["payload"],
            trial_id,
            campaign_id,
            as_of,
            event_type="ATTEMPT_STARTED",
        )
        family_event = self._require_event(
            trial_event["payload"]["trial_family_source_event_id"],
            trial_event["payload"]["trial_family_source_event_sha256"],
            event_type="TRIAL_FAMILY_REGISTERED",
        )
        sample_events = []
        for binding in definition.body.get("sample_bindings") or []:
            sample_events.append(
                self._require_event(
                    binding["source_event_id"],
                    binding["source_event_sha256"],
                    event_type="SAMPLE_REGISTERED",
                    subject_id=binding["sample_id"],
                )
            )
        plan = self._resolve_attempt_plan(allocation["payload"])
        plan_acceptance = self._resolve_attempt_plan_acceptance(allocation["payload"])
        allocation_authority = self._resolve_attempt_allocation_authority(
            allocation["payload"]
        )
        self._require_current(
            plan, as_of, event_type="ATTEMPT_STARTED", kind="plan"
        )
        alloc_payload = allocation["payload"]
        if (
            plan.body.get("trial_id") != trial_id
            or plan.body.get("attempt_id") != attempt_id
            or plan.body.get("campaign_id") != campaign_id
            or plan.body.get("ledger_id") != request["ledger_id"]
            or plan.body.get("trial_allocation_event_id")
            != alloc_payload["trial_allocation_event_id"]
            or plan.body.get("trial_allocation_event_sha256")
            != alloc_payload["trial_allocation_event_sha256"]
            or plan.body.get("campaign_inventory_seal_event_id")
            != alloc_payload["campaign_inventory_seal_event_id"]
            or plan.body.get("campaign_inventory_seal_event_sha256")
            != alloc_payload["campaign_inventory_seal_event_sha256"]
            or not _same_json_value(
                plan.body.get("relation"), alloc_payload.get("relation")
            )
        ):
            _fail(
                "RECORD_CONTENT_MISMATCH",
                "attempt plan does not bind retained trial, seal, and relation",
            )
        self._require_current(
            plan_acceptance, as_of, event_type="ATTEMPT_STARTED", kind="acceptance"
        )
        self._require_current(
            allocation_authority,
            as_of,
            event_type="ATTEMPT_STARTED",
            kind="allocation_authority",
        )
        readiness = self._resolve_attempt_readiness(payload)
        self._require_current(
            readiness, as_of, event_type="ATTEMPT_STARTED", kind="readiness"
        )
        if readiness.body.get("outcome") != "READY":
            _fail(
                "ATTEMPT_STARTED_READINESS_NOT_CURRENT",
                "readiness outcome is not READY",
            )
        if (
            readiness.body.get("trial_id") != trial_id
            or readiness.body.get("attempt_id") != attempt_id
            or readiness.body.get("campaign_id") != campaign_id
            or readiness.body.get("ledger_id") != request["ledger_id"]
            or readiness.body.get("ledger_id") != allocation["ledger_id"]
        ):
            _fail("RECORD_CONTENT_MISMATCH", "readiness does not bind this attempt")
        issuer = self._require_actor_id(
            readiness.body, "issuer_actor_id", "ATTEMPT_STARTED"
        )
        reviewer = self._require_actor_id(
            readiness.body, "reviewer_actor_id", "ATTEMPT_STARTED"
        )
        executor = self._require_actor_id(
            readiness.body, "executor_actor_id", "ATTEMPT_STARTED"
        )
        trial_acceptance = self._resolve_trial_acceptance(trial_event["payload"])
        if reviewer in {
            issuer,
            executor,
            allocation["actor_id"],
            plan.body["issuer_actor_id"],
            plan_acceptance.body["reviewer_actor_id"],
            definition.body["issuer_actor_id"],
            trial_acceptance.body["reviewer_actor_id"],
        } or issuer in {executor, allocation["actor_id"]}:
            _fail(
                "ATTEMPT_STARTED_ROLE_COLLISION",
                "readiness issuer, reviewer, and executor are not independent",
            )
        producers = self._require_private_input_producer_ids(
            readiness.body, "ATTEMPT_STARTED"
        )
        self._exclude_private_producers(
            reviewer,
            producers,
            "ATTEMPT_STARTED_PRIVATE_INPUT_PRODUCER_ROLE_COLLISION",
        )
        start_authority = self._resolve_attempt_start_authority(payload)
        self._require_current(
            start_authority,
            as_of,
            event_type="ATTEMPT_STARTED",
            kind="start_authority",
        )
        if start_authority.body.get("executor_actor_id") != executor:
            _fail(
                "ATTEMPT_STARTED_EXECUTOR_MISMATCH",
                "start-authority executor does not match readiness executor",
            )
        if start_authority.body.get("authorized_actor_id") != request["actor_id"]:
            _fail(
                "ATTEMPT_STARTED_AUTHORITY_ACTOR_MISMATCH",
                "start actor is not the authorized actor",
            )
        if (
            start_authority.body.get("operation") != "ATTEMPT_STARTED"
            or start_authority.body.get("attempt_id") != attempt_id
            or start_authority.body.get("trial_id") != trial_id
            or start_authority.body.get("campaign_id") != campaign_id
            or start_authority.body.get("ledger_id") != request["ledger_id"]
            or start_authority.body.get("attempt_allocation_event_id")
            != allocation["event_id"]
            or start_authority.body.get("attempt_allocation_event_sha256")
            != digest_json(allocation)
            or start_authority.body.get("readiness_authority_id")
            != payload["readiness_authority_id"]
            or start_authority.body.get("readiness_authority_registry_sha256")
            != payload["readiness_authority_registry_sha256"]
            or start_authority.body.get("readiness_authority_version")
            != payload["readiness_authority_version"]
            or start_authority.body.get("readiness_record_id")
            != payload["readiness_record_id"]
            or start_authority.body.get("readiness_record_schema_version")
            != payload["readiness_record_schema_version"]
            or start_authority.body.get("readiness_record_version")
            != payload["readiness_record_version"]
            or start_authority.body.get("readiness_record_canonicalization_id")
            != payload["readiness_record_canonicalization_id"]
            or start_authority.body.get("readiness_record_sha256")
            != payload["readiness_record_sha256"]
        ):
            _fail(
                "RECORD_CONTENT_MISMATCH",
                "start authority does not bind this start",
            )
        if self._operational_values(readiness.body) != self._operational_values(
            plan.body
        ) or self._operational_values(readiness.body) != self._operational_values(
            definition.body
        ):
            _fail(
                "ATTEMPT_STARTED_INHERITED_VALUE_MISMATCH",
                "readiness operational values do not match plan and trial definition",
            )
        expected = {
            "inventory_catalog_key": self._inventory_catalog_key(seal_event["payload"]),
            "inventory_acceptance": self._inventory_acceptance_tuple(
                seal_event["payload"]
            ),
            "seal_event_id_sha256": {
                "event_id": seal["event_id"],
                "event_sha256": seal["event_sha256"],
            },
            "family_definition_and_acceptance": [self._family_tuple(family_event)],
            "sample_record_acceptance_projection_publication_approval": [
                self._sample_tuple(sample_event) for sample_event in sample_events
            ],
            "trial_definition_acceptance_projection_allocation_authority": (
                self._trial_tuple(trial_event)
            ),
            "attempt_plan_catalog_key": self._plan_catalog_key(allocation["payload"]),
            "attempt_plan_acceptance": self._plan_acceptance_tuple(
                allocation["payload"]
            ),
            "attempt_allocation_authority": self._attempt_allocation_authority_tuple(
                allocation["payload"]
            ),
            "attempt_allocation_event": {
                "event_id": allocation["event_id"],
                "event_sha256": digest_json(allocation),
            },
            "retained_source_event_id_hash": self._retained_sources(
                family_event=family_event,
                sample_events=sample_events,
                trial_event=trial_event,
                seal_event=seal_event,
                allocation_event=allocation,
            ),
        }
        actual = {
            key: readiness.body.get(key) for key in expected
        }
        actual["family_definition_and_acceptance"] = sorted(
            actual.get("family_definition_and_acceptance") or [],
            key=lambda item: item.get("trial_family_id") or "",
        )
        actual["sample_record_acceptance_projection_publication_approval"] = sorted(
            actual.get("sample_record_acceptance_projection_publication_approval")
            or [],
            key=lambda item: item.get("sample_id") or "",
        )
        actual["retained_source_event_id_hash"] = sorted(
            actual.get("retained_source_event_id_hash") or [],
            key=lambda item: (item.get("source") or {}).get("event_id") or "",
        )
        expected["family_definition_and_acceptance"] = sorted(
            expected["family_definition_and_acceptance"],
            key=lambda item: item.get("trial_family_id") or "",
        )
        expected["sample_record_acceptance_projection_publication_approval"] = sorted(
            expected["sample_record_acceptance_projection_publication_approval"],
            key=lambda item: item.get("sample_id") or "",
        )
        expected["retained_source_event_id_hash"] = sorted(
            expected["retained_source_event_id_hash"],
            key=lambda item: (item.get("source") or {}).get("event_id") or "",
        )
        if digest_json(actual) != digest_json(expected):
            _fail(
                "ATTEMPT_STARTED_INHERITED_TUPLE_MISMATCH",
                "readiness tuples do not equal same-transaction revalidated tuples",
            )
        del inventory

    def _check_access_intent(self, request: dict[str, Any], as_of: str) -> None:
        self._require_epoch(request)
        payload = request["payload"]
        campaign_id = _campaign_id(payload)
        sample_id = payload["sample_id"]
        if request["subject_id"] != sample_id:
            _fail("RECORD_CONTENT_MISMATCH", "ACCESS_INTENT subject must be sample_id")
        seal = self._current_seal(campaign_id)
        if (
            payload["inventory_seal_event_id"] != seal["event_id"]
            or payload["inventory_seal_event_sha256"] != seal["event_sha256"]
        ):
            _fail(
                "ACCESS_INTENT_SEAL_NOT_CURRENT",
                "referenced seal is not the current seal head",
            )
        sealed_ids = list(seal["sealed_trial_ids"])
        affected = payload.get("affected_trial_ids") or []
        if not affected:
            _fail(
                "ACCESS_INTENT_AFFECTED_TRIAL_SET_EMPTY",
                "affected_trial_ids must be nonempty",
            )
        if not set(affected) <= set(sealed_ids):
            _fail(
                "ACCESS_INTENT_AFFECTED_TRIAL_SET_EMPTY"
                if not affected
                else "RECORD_CONTENT_MISMATCH",
                "affected trials must be a nonempty subset of the sealed set",
            )
        if payload.get("purpose") == "design":
            _fail("RECORD_CONTENT_MISMATCH", "ACCESS_INTENT purpose cannot be design")
        self._require_evidence_refs(payload.get("evidence_ref_ids") or [], "ACCESS_INTENT")
        sample_event = self._latest_sample(sample_id)
        self._revalidate_sample(sample_event, as_of, "ACCESS_INTENT")
        for trial_id in affected:
            trial_event = self._latest_trial(trial_id)
            family_event = self._require_event(
                trial_event["payload"]["trial_family_source_event_id"],
                trial_event["payload"]["trial_family_source_event_sha256"],
                event_type="TRIAL_FAMILY_REGISTERED",
            )
            self._revalidate_family(family_event, as_of, "ACCESS_INTENT")
        authorization = self._resolve_access_authorization(payload)
        intent_authority = self._resolve_intent_authority(payload)
        self._require_current(
            authorization, as_of, event_type="ACCESS_INTENT", kind="authorization"
        )
        self._require_current(
            intent_authority, as_of, event_type="ACCESS_INTENT", kind="authority"
        )
        auth_body = authorization.body
        if (
            auth_body.get("sample_id") != sample_id
            or auth_body.get("campaign_id") != campaign_id
            or auth_body.get("affected_trial_ids") != affected
            or auth_body.get("purpose") != payload["purpose"]
            or auth_body.get("intended_window_id") != payload["intended_window_id"]
            or auth_body.get("intended_field_class_ids")
            != payload["intended_field_class_ids"]
            or auth_body.get("accessor_code_tree_sha256")
            != payload["accessor_code_tree_sha256"]
            or auth_body.get("accessor_environment_id")
            != payload["accessor_environment_id"]
            or auth_body.get("accessor_environment_lock_sha256")
            != payload["accessor_environment_lock_sha256"]
        ):
            _fail("RECORD_CONTENT_MISMATCH", "authorization does not bind this intent")
        intent_body = intent_authority.body
        if intent_body.get("authorized_actor_id") != request["actor_id"]:
            _fail(
                "ACCESS_INTENT_AUTHORITY_ACTOR_MISMATCH",
                "intent actor is not the authorized actor",
            )
        if (
            intent_body.get("operation") != "ACCESS_INTENT"
            or intent_body.get("sample_id") != sample_id
            or intent_body.get("campaign_id") != campaign_id
        ):
            _fail(
                "RECORD_CONTENT_MISMATCH",
                "intent authority does not bind operation, sample, and campaign",
            )
        seal_event = self._require_event(seal["event_id"], seal["event_sha256"])
        inventory = self._resolve_inventory_record(seal_event["payload"])
        principals = {
            "authorization_issuer": auth_body["issuer_actor_id"],
            "intent_authority_issuer": intent_authority.body["issuer_actor_id"],
            "accessor": auth_body["accessor_actor_id"],
            "inventory_issuer": inventory.body["issuer_actor_id"],
            "seal_actor": seal_event["actor_id"],
        }
        self._require_distinct(principals, "ACCESS_INTENT_ROLE_COLLISION")

    def _check_access_started(self, request: dict[str, Any], as_of: str) -> None:
        self._require_epoch(request)
        payload = request["payload"]
        campaign_id = _campaign_id(payload)
        sample_id = payload["sample_id"]
        if request["subject_id"] != sample_id:
            _fail("RECORD_CONTENT_MISMATCH", "ACCESS_STARTED subject must be sample_id")
        intent = self._require_event(
            payload["access_intent_event_id"],
            payload["access_intent_event_sha256"],
            event_type="ACCESS_INTENT",
            subject_id=sample_id,
        )
        if _campaign_id(intent["payload"]) != campaign_id:
            _fail("RECORD_CONTENT_MISMATCH", "start campaign does not match intent")
        if payload["access_capability_id"] != intent["payload"]["access_capability_id"]:
            _fail("RECORD_CONTENT_MISMATCH", "start capability does not match intent")
        self._require_evidence_refs(payload.get("evidence_ref_ids") or [], "ACCESS_STARTED")
        seal = self._current_seal(campaign_id)
        if (
            intent["payload"]["inventory_seal_event_id"] != seal["event_id"]
            or intent["payload"]["inventory_seal_event_sha256"] != seal["event_sha256"]
        ):
            _fail(
                "ACCESS_STARTED_SEAL_NOT_CURRENT",
                "seal head is no longer current",
            )
        sample_event = self._latest_sample(sample_id)
        self._revalidate_sample(sample_event, as_of, "ACCESS_STARTED")
        for trial_id in intent["payload"]["affected_trial_ids"]:
            trial_event = self._latest_trial(trial_id)
            family_event = self._require_event(
                trial_event["payload"]["trial_family_source_event_id"],
                trial_event["payload"]["trial_family_source_event_sha256"],
                event_type="TRIAL_FAMILY_REGISTERED",
            )
            self._revalidate_family(family_event, as_of, "ACCESS_STARTED")
        start_authority = self._resolve_start_authority(payload)
        self._require_current(
            start_authority, as_of, event_type="ACCESS_STARTED", kind="authority"
        )
        body = start_authority.body
        if (
            body.get("authorized_actor_id") != request["actor_id"]
            or body.get("access_intent_event_id") != intent["event_id"]
            or body.get("access_intent_event_sha256") != digest_json(intent)
            or body.get("sample_id") != sample_id
            or body.get("campaign_id") != campaign_id
            or body.get("reader_code_tree_sha256") != payload["reader_code_tree_sha256"]
            or body.get("reader_environment_id") != payload["reader_environment_id"]
            or body.get("reader_environment_lock_sha256")
            != payload["reader_environment_lock_sha256"]
        ):
            _fail("RECORD_CONTENT_MISMATCH", "start authority does not bind this start")
        cap_row = self._conn.execute(
            "SELECT record_json, record_sha256, consumed FROM capabilities "
            "WHERE capability_id = ?",
            (payload["access_capability_id"],),
        ).fetchone()
        if cap_row is None:
            _fail("PARENT_EVENT_MISSING", "ACCESS capability was not minted")
        record = json.loads(cap_row[0])
        if cap_row[2]:
            _fail("ACCESS_CAPABILITY_ALREADY_CONSUMED", "ACCESS capability already consumed")
        if (
            record.get("accessor_code_tree_sha256") != payload["reader_code_tree_sha256"]
            or record.get("accessor_environment_id") != payload["reader_environment_id"]
            or record.get("accessor_environment_lock_sha256")
            != payload["reader_environment_lock_sha256"]
        ):
            _fail("RECORD_CONTENT_MISMATCH", "reader does not match ACCESS capability")
        if body.get("accessor_actor_id") != record.get("accessor_actor_id"):
            _fail(
                "RECORD_CONTENT_MISMATCH",
                "start authority accessor does not match ACCESS capability accessor",
            )
        activation = record.get("activation")
        expiry = record.get("expiry")
        if not isinstance(activation, str) or not isinstance(expiry, str):
            _fail(
                "RECORD_CONTENT_MISMATCH",
                "ACCESS capability is missing activation or expiry",
            )
        if as_of < activation:
            _fail(
                "ACCESS_STARTED_CAPABILITY_NOT_ACTIVE",
                "ACCESS capability is not yet active",
            )
        if as_of >= expiry:
            _fail(
                "ACCESS_STARTED_CAPABILITY_EXPIRED",
                "ACCESS capability has expired",
            )

    def _mint_access_capability(self, event: dict[str, Any], event_sha256: str) -> None:
        payload = event["payload"]
        record = {
            "schema_version": "sample_access_capability_record_v1",
            "canonicalization_id": "pit_canonical_json_v1",
            "access_capability_id": payload["access_capability_id"],
            "access_capability_record_version": payload["access_capability_record_version"],
            "ledger_id": event["ledger_id"],
            "sample_id": payload["sample_id"],
            "campaign_id": _campaign_id(payload),
            "intent_operation_id": event["operation_id"],
            "intent_event_id": event["event_id"],
            "accessor_actor_id": self._resolve_access_authorization(payload).body[
                "accessor_actor_id"
            ],
            "accessor_code_tree_sha256": payload["accessor_code_tree_sha256"],
            "accessor_environment_id": payload["accessor_environment_id"],
            "accessor_environment_lock_sha256": payload["accessor_environment_lock_sha256"],
            "intended_window_id": payload["intended_window_id"],
            "intended_field_class_ids": payload["intended_field_class_ids"],
            "activation": (
                self._active_catalog.capability_activation or event["recorded_at"]
            ),
            "expiry": (
                self._active_catalog.capability_expiry or DEFAULT_CAPABILITY_EXPIRY
            ),
            "one_use": True,
        }
        record_sha256 = digest_json(record)
        if record_sha256 != payload["access_capability_record_sha256"]:
            _fail("RECORD_CONTENT_MISMATCH", "ACCESS capability digest mismatch")
        self._conn.execute(
            "INSERT INTO capabilities ("
            "capability_id, kind, record_json, record_sha256, consumed, minted_event_id) "
            "VALUES (?, 'ACCESS', ?, ?, 0, ?)",
            (
                payload["access_capability_id"],
                json.dumps(record, sort_keys=True, separators=(",", ":")),
                record_sha256,
                event["event_id"],
            ),
        )
        del event_sha256

    def _consume_access_capability(self, event: dict[str, Any], event_sha256: str) -> None:
        capability_id = event["payload"]["access_capability_id"]
        updated = self._conn.execute(
            "UPDATE capabilities SET consumed = 1, consumed_event_id = ? "
            "WHERE capability_id = ? AND consumed = 0",
            (event["event_id"], capability_id),
        ).rowcount
        if updated != 1:
            _fail("ACCESS_CAPABILITY_ALREADY_CONSUMED", "ACCESS consume did not land")
        del event_sha256

    def _mint_execute_capability(self, event: dict[str, Any], event_sha256: str) -> None:
        payload = event["payload"]
        readiness = self._resolve_attempt_readiness(payload)
        allocation = self._require_event(
            payload["attempt_allocation_event_id"],
            payload["attempt_allocation_event_sha256"],
        )
        record = self._execution_capability_record(
            event,
            readiness=readiness,
            allocation=allocation,
        )
        record_sha256 = digest_json(record)
        if record_sha256 != payload["execution_capability_record_sha256"]:
            _fail("RECORD_CONTENT_MISMATCH", "EXECUTE capability digest mismatch")
        self._conn.execute(
            "INSERT INTO capabilities ("
            "capability_id, kind, record_json, record_sha256, consumed, minted_event_id) "
            "VALUES (?, 'EXECUTE', ?, ?, 0, ?)",
            (
                payload["execution_capability_id"],
                json.dumps(record, sort_keys=True, separators=(",", ":")),
                record_sha256,
                event["event_id"],
            ),
        )
        del event_sha256

    def _execution_capability_record(
        self,
        event: dict[str, Any],
        *,
        readiness: CatalogRecord,
        allocation: dict[str, Any],
    ) -> dict[str, Any]:
        payload = event["payload"]
        code = readiness.body["code_identity"]
        return {
            "schema_version": "attempt_execution_capability_record_v1",
            "canonicalization_id": "pit_canonical_json_v1",
            "execution_capability_id": payload["execution_capability_id"],
            "execution_capability_record_version": payload[
                "execution_capability_record_version"
            ],
            "ledger_id": event["ledger_id"],
            "campaign_id": _campaign_id(payload),
            "trial_id": payload["trial_id"],
            "attempt_id": event["subject_id"],
            "start_event_id": event["event_id"],
            "attempt_allocation_event_id": allocation["event_id"],
            "attempt_allocation_event_sha256": digest_json(allocation),
            "readiness_record_id": payload["readiness_record_id"],
            "readiness_record_sha256": payload["readiness_record_sha256"],
            "start_authority_id": payload["start_authority_id"],
            "start_authority_record_sha256": payload["start_authority_record_sha256"],
            "executor_actor_id": readiness.body["executor_actor_id"],
            "code_tree_sha256": code["code_tree_sha256"],
            "environment_id": readiness.body["environment_id"],
            "environment_lock_sha256": readiness.body["environment_lock_sha256"],
            "activation": (
                self._active_catalog.capability_activation or event["recorded_at"]
            ),
            "expiry": (
                self._active_catalog.capability_expiry or DEFAULT_CAPABILITY_EXPIRY
            ),
            "one_use": True,
            "state": "CREATED",
        }

    def _insert_origin(self, event: dict[str, Any], event_sha256: str) -> None:
        record = self._resolve_sample_record(event["payload"])
        lineage = record.body["canonical_sample_lineage_id"]
        identity = digest_json(self._sample_identity_tuple(event["payload"], record))
        try:
            self._conn.execute(
                "INSERT INTO origins ("
                "sample_id, origin_event_type, canonical_lineage_id, "
                "record_identity_sha256, origin_event_id, origin_event_sha256) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    event["subject_id"],
                    event["event_type"],
                    lineage,
                    identity,
                    event["event_id"],
                    event_sha256,
                ),
            )
        except sqlite3.IntegrityError:
            _fail("SAMPLE_ID_ALREADY_ALLOCATED", "sample origin already committed")

    def _check_origin_uniqueness(
        self,
        event_type: str,
        sample_id: str,
        record: CatalogRecord,
        payload: dict[str, Any],
    ) -> None:
        lineage = record.body["canonical_sample_lineage_id"]
        identity = digest_json(self._sample_identity_tuple(payload, record))
        by_id = self._conn.execute(
            "SELECT sample_id FROM origins WHERE sample_id = ?",
            (sample_id,),
        ).fetchone()
        if by_id is not None:
            _fail("SAMPLE_ID_ALREADY_ALLOCATED", "sample_id already has an origin")
        same_tuple = self._conn.execute(
            "SELECT origin_event_type FROM origins WHERE record_identity_sha256 = ?",
            (identity,),
        ).fetchone()
        if same_tuple is not None:
            _fail(f"{event_type}_RECORD_DUP", "authority/record identity already originated")
        same_lineage = self._conn.execute(
            "SELECT origin_event_type FROM origins WHERE canonical_lineage_id = ?",
            (lineage,),
        ).fetchone()
        if same_lineage is not None:
            other_type = same_lineage[0]
            if other_type != event_type:
                _fail(
                    f"{event_type}_ORIGIN_PATH_CONFLICT",
                    "lineage already originated on the other path",
                )
            _fail(f"{event_type}_LINEAGE_DUP", "lineage already originated on this path")

    def _sample_identity_tuple(
        self, payload: dict[str, Any], record: CatalogRecord
    ) -> dict[str, Any]:
        return {
            "sample_authority_id": payload["sample_authority_id"],
            "sample_authority_version": payload["sample_authority_version"],
            "sample_authority_registry_sha256": payload["sample_authority_registry_sha256"],
            "sample_record_id": payload["sample_record_id"],
            "sample_record_version": payload["sample_record_version"],
            "sample_record_schema_version": payload["sample_record_schema_version"],
            "sample_record_canonicalization_id": payload["sample_record_canonicalization_id"],
            "sample_record_sha256": payload["sample_record_sha256"],
            "resolved_sha256": record.sha256,
        }

    def _current_seal(self, campaign_id: str) -> dict[str, Any]:
        row = self._conn.execute(
            "SELECT event_id, event_sha256, sealed_trial_ids_json FROM campaign_seal_head "
            "WHERE campaign_id = ?",
            (campaign_id,),
        ).fetchone()
        if row is None:
            _fail("PARENT_EVENT_MISSING", "campaign inventory is not sealed")
        return {
            "event_id": row[0],
            "event_sha256": row[1],
            "sealed_trial_ids": json.loads(row[2]),
        }

    def _sealed_trial_ids_from_inventory(self, payload: dict[str, Any]) -> list[str]:
        inventory = self._resolve_inventory_record(payload)
        return [entry["trial_id"] for entry in inventory.body["trials"]]

    def _latest_sample(self, sample_id: str) -> dict[str, Any]:
        row = self._conn.execute(
            "SELECT event_json FROM events WHERE subject_id = ? "
            "AND event_type = 'SAMPLE_REGISTERED' ORDER BY sequence DESC LIMIT 1",
            (sample_id,),
        ).fetchone()
        if row is None:
            _fail("PARENT_EVENT_MISSING", f"sample {sample_id} is not registered")
        return json.loads(row[0])

    def _latest_trial(self, trial_id: str) -> dict[str, Any]:
        row = self._conn.execute(
            "SELECT event_json FROM events WHERE subject_id = ? "
            "AND event_type = 'TRIAL_ALLOCATED' ORDER BY sequence DESC LIMIT 1",
            (trial_id,),
        ).fetchone()
        if row is None:
            _fail("PARENT_EVENT_MISSING", f"trial {trial_id} is not allocated")
        return json.loads(row[0])

    def _require_epoch(self, request: dict[str, Any]) -> None:
        if self._stream_head(request["ledger_id"]) is None:
            _fail("PARENT_EVENT_MISSING", "ledger epoch has not been created")

    def _revalidate_family(
        self, family_event: dict[str, Any], as_of: str, event_type: str
    ) -> CatalogRecord:
        payload = family_event["payload"]
        definition = self._resolve_family_definition(payload)
        acceptance = self._resolve_family_acceptance(payload)
        self._require_current(acceptance, as_of, event_type=event_type, kind="acceptance")
        self._assert_content_scope(
            definition.body,
            family_event["subject_id"],
            payload.get("campaign_scope_ids"),
            family_id_key="trial_family_id",
        )
        return definition

    def _revalidate_sample(
        self, sample_event: dict[str, Any], as_of: str, event_type: str
    ) -> CatalogRecord:
        payload = sample_event["payload"]
        record = self._resolve_sample_record(payload)
        acceptance = self._resolve_sample_acceptance(payload)
        projection = self._resolve_sample_projection(payload)
        approval = self._resolve_sample_publication_approval(payload)
        self._require_current(acceptance, as_of, event_type=event_type, kind="acceptance")
        self._require_current(
            projection, as_of, event_type=event_type, kind="projection"
        )
        self._require_current(
            approval, as_of, event_type=event_type, kind="publication_approval"
        )
        if projection.body.get("sample_id") != sample_event["subject_id"]:
            _fail("RECORD_CONTENT_MISMATCH", "sample projection sample_id mismatch")
        if (
            projection.body.get("sample_record_id") != payload["sample_record_id"]
            or projection.body.get("sample_record_sha256") != payload["sample_record_sha256"]
        ):
            _fail("RECORD_CONTENT_MISMATCH", "sample projection record binding mismatch")
        if (
            approval.body.get("sample_id") != sample_event["subject_id"]
            or approval.body.get("sample_public_projection_id")
            != payload["sample_public_projection_id"]
            or approval.body.get("sample_public_projection_schema_version")
            != payload["sample_public_projection_schema_version"]
            or approval.body.get("sample_public_projection_sha256")
            != payload["sample_public_projection_sha256"]
            or approval.body.get("outcome") != "approved"
        ):
            _fail(
                "RECORD_CONTENT_MISMATCH",
                "publication approval does not bind this sample projection",
            )
        self._assert_content_scope(
            record.body,
            sample_event["subject_id"],
            payload.get("campaign_scope_ids"),
            sample_id_key="sample_id",
        )
        return record

    def _revalidate_trial_definition(
        self,
        payload: dict[str, Any],
        trial_id: str,
        campaign_id: str,
        as_of: str,
        *,
        event_type: str = "TRIAL_ALLOCATED",
    ) -> CatalogRecord:
        definition = self._resolve_trial_definition(payload)
        acceptance = self._resolve_trial_acceptance(payload)
        projection = self._resolve_trial_projection(payload)
        approval = self._resolve_trial_publication_approval(payload)
        self._require_current(
            acceptance, as_of, event_type=event_type, kind="acceptance"
        )
        self._require_current(
            projection, as_of, event_type=event_type, kind="projection"
        )
        self._require_current(
            approval, as_of, event_type=event_type, kind="publication_approval"
        )
        body = definition.body
        if body.get("trial_id") != trial_id:
            _fail("RECORD_CONTENT_MISMATCH", "trial definition trial_id mismatch")
        if body.get("trial_family_id") != payload.get("trial_family_id"):
            _fail("RECORD_CONTENT_MISMATCH", "trial definition trial_family_id mismatch")
        if body.get("experiment_id") != payload.get("experiment_id"):
            _fail("RECORD_CONTENT_MISMATCH", "trial definition experiment_id mismatch")
        if projection.body.get("trial_id") != trial_id:
            _fail("RECORD_CONTENT_MISMATCH", "trial projection trial_id mismatch")
        scope = body.get("campaign_scope_ids")
        if scope != [campaign_id] and scope != payload.get("campaign_scope_ids"):
            _fail("RECORD_CONTENT_MISMATCH", "resolved definition binds another campaign")
        return definition

    def _revalidate_trial_event(
        self, trial_event: dict[str, Any], as_of: str, event_type: str
    ) -> None:
        payload = trial_event["payload"]
        family_event = self._require_event(
            payload["trial_family_source_event_id"],
            payload["trial_family_source_event_sha256"],
            event_type="TRIAL_FAMILY_REGISTERED",
        )
        self._revalidate_family(family_event, as_of, event_type)
        definition = self._resolve_trial_definition(payload)
        acceptance = self._resolve_trial_acceptance(payload)
        projection = self._resolve_trial_projection(payload)
        approval = self._resolve_trial_publication_approval(payload)
        self._require_current(acceptance, as_of, event_type=event_type, kind="acceptance")
        self._require_current(
            projection, as_of, event_type=event_type, kind="projection"
        )
        self._require_current(
            approval, as_of, event_type=event_type, kind="publication_approval"
        )
        authority = self._resolve_trial_allocation_authority(payload)
        self._require_current(authority, as_of, event_type=event_type, kind="authority")
        del projection
        for binding in definition.body.get("sample_bindings") or []:
            sample_event = self._require_event(
                binding["source_event_id"],
                binding["source_event_sha256"],
                event_type="SAMPLE_REGISTERED",
                subject_id=binding["sample_id"],
            )
            self._revalidate_sample(sample_event, as_of, event_type)

    def _prove_code_digest(self, code_identity: dict[str, Any]) -> None:
        kind = code_identity.get("code_identity_kind")
        if kind == "clean_commit":
            digest = code_identity["code_tree_sha256"]
        elif kind == "dirty_tree":
            digest = code_identity["code_patch_sha256"]
        else:
            _fail("RECORD_CONTENT_MISMATCH", "unknown code identity kind")
            return
        if digest not in self._active_catalog.proven_digests:
            _fail("RECORD_CONTENT_MISMATCH", "code content digest is not proven")

    def _require_evidence_refs(self, refs: list[Any], event_type: str) -> None:
        if not refs:
            _fail(f"{event_type}_EVIDENCE_REF_SET_EMPTY", "evidence_ref_ids is empty")
        for ref in refs:
            if ref not in self._active_catalog.evidence_refs:
                _fail("RECORD_CONTENT_MISMATCH", f"unknown evidence_ref_id {ref}")

    def _require_current(
        self,
        record: CatalogRecord,
        as_of: str,
        *,
        event_type: str,
        kind: str,
    ) -> None:
        if kind == "readiness":
            prefix = f"{event_type}_READINESS"
        elif kind == "acceptance":
            prefix = f"{event_type}_ACCEPTANCE"
        elif kind == "publication_approval":
            prefix = f"{event_type}_PUBLICATION_APPROVAL"
        elif kind == "projection":
            prefix = f"{event_type}_PROJECTION"
        elif kind == "authorization":
            prefix = f"{event_type}_AUTHORIZATION"
        elif kind == "start_authority":
            prefix = f"{event_type}_START_AUTHORITY"
        elif kind == "allocation_authority":
            prefix = f"{event_type}_ALLOCATION_AUTHORITY"
        elif kind == "plan":
            prefix = f"{event_type}_PLAN"
        else:
            prefix = f"{event_type}_AUTHORITY"
        ts_code = f"{prefix}_TIMESTAMP_INVALID"
        as_of_dt = _parse_canonical_utc(as_of, code=ts_code)
        inactive = not _canonical_interval_active(record, as_of_dt, code=ts_code)
        accepted_current = []
        for item in self._active_catalog.stream(record.stream_key):
            item_active = _canonical_interval_active(item, as_of_dt, code=ts_code)
            if item.status == "accepted" and item_active:
                accepted_current.append(item)
        if kind == "readiness":
            if (
                record.status in {"revoked", "superseded"}
                or record.status != "accepted"
                or inactive
            ):
                _fail(
                    "ATTEMPT_STARTED_READINESS_NOT_CURRENT",
                    "readiness is not current",
                )
            if len(accepted_current) != 1 or accepted_current[0].sha256 != record.sha256:
                _fail(
                    "ATTEMPT_STARTED_READINESS_NOT_CURRENT",
                    "readiness is not sole-current",
                )
            return
        if record.status == "revoked":
            _fail(f"{prefix}_REVOKED", f"{kind} is revoked")
        if record.status == "superseded":
            _fail(f"{prefix}_SUPERSEDED", f"{kind} is superseded")
        if inactive:
            _fail(f"{prefix}_STALE", f"{kind} is stale at as_of")
        if record.status != "accepted":
            _fail(f"{prefix}_NOT_CURRENT", f"{kind} is not current")
        if len(accepted_current) != 1 or accepted_current[0].sha256 != record.sha256:
            if record.status == "accepted" and not inactive:
                if len(accepted_current) != 1:
                    _fail(f"{prefix}_NOT_CURRENT", f"{kind} is not sole-current")
            else:
                _fail(f"{prefix}_NOT_CURRENT", f"{kind} is not sole-current")

    def _assert_content_scope(
        self,
        body: dict[str, Any],
        subject_id: str,
        campaign_scope_ids: object,
        *,
        family_id_key: str | None = None,
        sample_id_key: str | None = None,
    ) -> None:
        if family_id_key and body.get(family_id_key) != subject_id:
            _fail("RECORD_CONTENT_MISMATCH", "resolved family id mismatch")
        if sample_id_key and body.get(sample_id_key) != subject_id:
            _fail("RECORD_CONTENT_MISMATCH", "resolved sample id mismatch")
        if body.get("campaign_scope_ids") != campaign_scope_ids:
            _fail("RECORD_CONTENT_MISMATCH", "resolved campaign scope mismatch")

    def _require_distinct(self, principals: dict[str, str], code: str) -> None:
        values = list(principals.values())
        if len(values) != len(set(values)):
            _fail(code, "required principals are not pairwise distinct")

    @staticmethod
    def _require_actor_id(body: dict[str, Any], field: str, event_type: str) -> str:
        value = body.get(field)
        if not isinstance(value, str) or value == "":
            _fail("RECORD_CONTENT_MISMATCH", f"{event_type} missing {field}")
        return value

    @staticmethod
    def _require_private_input_producer_ids(
        body: dict[str, Any], event_type: str
    ) -> list[Any]:
        if "private_input_producer_actor_ids" not in body:
            _fail(
                "RECORD_CONTENT_MISMATCH",
                f"{event_type} missing private_input_producer_actor_ids",
            )
        producers = body["private_input_producer_actor_ids"]
        if not isinstance(producers, list):
            _fail(
                "RECORD_CONTENT_MISMATCH",
                f"{event_type} private_input_producer_actor_ids is malformed",
            )
        if len(producers) > 4096:
            _fail(
                "RECORD_CONTENT_MISMATCH",
                f"{event_type} private_input_producer_actor_ids exceeds 4096",
            )
        if any(
            not isinstance(item, str) or _ACTOR_ID_PATTERN.fullmatch(item) is None
            for item in producers
        ):
            _fail(
                "RECORD_CONTENT_MISMATCH",
                f"{event_type} private_input_producer_actor_ids is malformed",
            )
        if producers != sorted(set(producers)):
            _fail(
                "RECORD_CONTENT_MISMATCH",
                f"{event_type} private_input_producer_actor_ids must be sorted-unique",
            )
        return producers

    def _exclude_private_producers(
        self, actor_id: str, producers: list[Any], code: str
    ) -> None:
        if actor_id in producers:
            _fail(code, "reviewer or actor is a private-input producer")

    def _resolve_or_fail(
        self,
        kind: str,
        record_id: str,
        sha256: str,
        *,
        generation: int | None = None,
        version: int | None = None,
        event_type: str,
        incomplete_kind: str,
        expected: dict[str, object] | None = None,
    ) -> CatalogRecord:
        record = self._active_catalog.get(
            kind, record_id, sha256, generation=generation, version=version
        )
        if record is None:
            _fail(f"{event_type}_RECORD_INCOMPLETE", f"missing {incomplete_kind}")
        for attr, value in (expected or {}).items():
            if getattr(record, attr) != value:
                _fail(
                    "RECORD_CONTENT_MISMATCH",
                    f"{incomplete_kind} resolver tuple mismatch on {attr}",
                )
        return record

    def _resolve_family_definition(self, payload: dict[str, Any]) -> CatalogRecord:
        return self._resolve_or_fail(
            "family_definition",
            payload["family_definition_record_id"],
            payload["family_definition_record_sha256"],
            version=payload["family_definition_record_version"],
            event_type="TRIAL_FAMILY_REGISTERED",
            incomplete_kind="family_definition",
            expected={
                "schema_version": payload["family_definition_schema_version"],
                "canonicalization_id": payload["family_definition_canonicalization_id"],
                "authority_id": payload["family_authority_id"],
                "authority_version": payload["family_authority_version"],
                "registry_sha256": payload["family_authority_registry_sha256"],
            },
        )

    def _resolve_family_acceptance(self, payload: dict[str, Any]) -> CatalogRecord:
        return self._resolve_or_fail(
            "family_acceptance",
            payload["family_acceptance_decision_id"],
            payload["family_acceptance_record_sha256"],
            generation=payload["family_acceptance_generation"],
            event_type="TRIAL_FAMILY_REGISTERED",
            incomplete_kind="family_acceptance",
            expected={
                "schema_version": payload["family_acceptance_schema_version"],
            },
        )

    def _sample_resolver_key(self, payload: dict[str, Any]) -> tuple[object, ...]:
        return (
            payload["sample_authority_id"],
            payload["sample_authority_version"],
            payload["sample_authority_registry_sha256"],
            payload["sample_record_id"],
            payload["sample_record_version"],
            payload["sample_record_schema_version"],
            payload["sample_record_canonicalization_id"],
            payload["sample_record_sha256"],
        )

    def _record_resolver_key(self, record: CatalogRecord) -> tuple[object, ...]:
        return (
            record.authority_id,
            record.authority_version,
            record.registry_sha256,
            record.record_id,
            record.version,
            record.schema_version,
            record.canonicalization_id,
            record.sha256,
        )

    def _resolve_sample_record(self, payload: dict[str, Any]) -> CatalogRecord:
        record = self._resolve_or_fail(
            "sample_record",
            payload["sample_record_id"],
            payload["sample_record_sha256"],
            version=payload["sample_record_version"],
            event_type="SAMPLE_REGISTERED",
            incomplete_kind="sample_record",
        )
        if self._record_resolver_key(record) != self._sample_resolver_key(payload):
            _fail(
                "RECORD_CONTENT_MISMATCH",
                "sample authority resolver key does not match catalog record",
            )
        return record

    def _resolve_sample_acceptance(self, payload: dict[str, Any]) -> CatalogRecord:
        return self._resolve_or_fail(
            "sample_acceptance",
            payload["sample_acceptance_decision_id"],
            payload["sample_acceptance_record_sha256"],
            generation=payload["sample_acceptance_generation"],
            event_type="SAMPLE_REGISTERED",
            incomplete_kind="sample_acceptance",
            expected={
                "schema_version": payload["sample_acceptance_schema_version"],
            },
        )

    def _resolve_sample_projection(self, payload: dict[str, Any]) -> CatalogRecord:
        return self._resolve_or_fail(
            "sample_projection",
            payload["sample_public_projection_id"],
            payload["sample_public_projection_sha256"],
            event_type="SAMPLE_REGISTERED",
            incomplete_kind="sample_projection",
            expected={
                "schema_version": payload["sample_public_projection_schema_version"],
                "canonicalization_id": "pit_canonical_json_v1",
            },
        )

    def _resolve_sample_publication_approval(
        self, payload: dict[str, Any]
    ) -> CatalogRecord:
        return self._resolve_or_fail(
            "sample_publication_approval",
            payload["sample_publication_approval_id"],
            payload["sample_publication_approval_record_sha256"],
            generation=payload["sample_publication_approval_generation"],
            event_type="SAMPLE_REGISTERED",
            incomplete_kind="sample_publication_approval",
            expected={
                "schema_version": payload["sample_publication_approval_schema_version"],
            },
        )

    def _resolve_trial_definition(self, payload: dict[str, Any]) -> CatalogRecord:
        return self._resolve_or_fail(
            "trial_definition",
            payload["trial_definition_record_id"],
            payload["trial_definition_record_sha256"],
            version=payload["trial_definition_record_version"],
            event_type="TRIAL_ALLOCATED",
            incomplete_kind="trial_definition",
            expected={
                "schema_version": payload["trial_definition_record_schema_version"],
                "canonicalization_id": payload[
                    "trial_definition_record_canonicalization_id"
                ],
                "authority_id": payload["trial_definition_authority_id"],
                "authority_version": payload["trial_definition_authority_version"],
                "registry_sha256": payload["trial_definition_authority_registry_sha256"],
            },
        )

    def _resolve_trial_acceptance(self, payload: dict[str, Any]) -> CatalogRecord:
        return self._resolve_or_fail(
            "trial_acceptance",
            payload["trial_definition_acceptance_decision_id"],
            payload["trial_definition_acceptance_record_sha256"],
            generation=payload["trial_definition_acceptance_generation"],
            event_type="TRIAL_ALLOCATED",
            incomplete_kind="trial_acceptance",
            expected={
                "schema_version": payload["trial_definition_acceptance_schema_version"],
            },
        )

    def _resolve_trial_projection(self, payload: dict[str, Any]) -> CatalogRecord:
        return self._resolve_or_fail(
            "trial_projection",
            payload["trial_definition_public_projection_id"],
            payload["trial_definition_public_projection_sha256"],
            event_type="TRIAL_ALLOCATED",
            incomplete_kind="trial_projection",
            expected={
                "schema_version": payload[
                    "trial_definition_public_projection_schema_version"
                ],
                "canonicalization_id": "pit_canonical_json_v1",
            },
        )

    def _resolve_trial_publication_approval(
        self, payload: dict[str, Any]
    ) -> CatalogRecord:
        return self._resolve_or_fail(
            "trial_publication_approval",
            payload["trial_definition_publication_approval_id"],
            payload["trial_definition_publication_approval_record_sha256"],
            generation=payload["trial_definition_publication_approval_generation"],
            event_type="TRIAL_ALLOCATED",
            incomplete_kind="trial_publication_approval",
            expected={
                "schema_version": payload[
                    "trial_definition_publication_approval_schema_version"
                ],
            },
        )

    def _resolve_trial_allocation_authority(
        self, payload: dict[str, Any]
    ) -> CatalogRecord:
        return self._resolve_or_fail(
            "trial_allocation_authority",
            payload["allocation_authority_id"],
            payload["allocation_authority_record_sha256"],
            generation=payload["allocation_authority_generation"],
            event_type="TRIAL_ALLOCATED",
            incomplete_kind="trial_allocation_authority",
            expected={
                "schema_version": payload["allocation_authority_schema_version"],
            },
        )

    def _resolve_inventory_record(self, payload: dict[str, Any]) -> CatalogRecord:
        return self._resolve_or_fail(
            "inventory_record",
            payload["inventory_record_id"],
            payload["sealed_trial_inventory_sha256"],
            version=payload["inventory_record_version"],
            event_type="CAMPAIGN_INVENTORY_SEALED",
            incomplete_kind="inventory_record",
            expected={
                "schema_version": payload["inventory_record_schema_version"],
                "canonicalization_id": payload["inventory_record_canonicalization_id"],
                "authority_id": payload["inventory_authority_id"],
                "authority_version": payload["inventory_authority_version"],
                "registry_sha256": payload["inventory_authority_registry_sha256"],
            },
        )

    def _resolve_inventory_acceptance(self, payload: dict[str, Any]) -> CatalogRecord:
        return self._resolve_or_fail(
            "inventory_acceptance",
            payload["inventory_acceptance_decision_id"],
            payload["inventory_acceptance_record_sha256"],
            generation=payload["inventory_acceptance_generation"],
            event_type="CAMPAIGN_INVENTORY_SEALED",
            incomplete_kind="inventory_acceptance",
            expected={
                "schema_version": payload["inventory_acceptance_schema_version"],
            },
        )

    def _resolve_seal_authority(self, payload: dict[str, Any]) -> CatalogRecord:
        return self._resolve_or_fail(
            "seal_authority",
            payload["seal_authority_id"],
            payload["seal_authority_record_sha256"],
            generation=payload["seal_authority_generation"],
            event_type="CAMPAIGN_INVENTORY_SEALED",
            incomplete_kind="seal_authority",
            expected={
                "schema_version": payload["seal_authority_schema_version"],
            },
        )

    def _resolve_access_authorization(self, payload: dict[str, Any]) -> CatalogRecord:
        return self._resolve_or_fail(
            "access_authorization",
            payload["authorization_record_id"],
            payload["authorization_record_sha256"],
            event_type="ACCESS_INTENT",
            incomplete_kind="access_authorization",
            expected={
                "schema_version": payload["authorization_record_schema_version"],
            },
        )

    def _resolve_intent_authority(self, payload: dict[str, Any]) -> CatalogRecord:
        return self._resolve_or_fail(
            "intent_authority",
            payload["intent_authority_id"],
            payload["intent_authority_record_sha256"],
            generation=payload["intent_authority_generation"],
            event_type="ACCESS_INTENT",
            incomplete_kind="intent_authority",
            expected={
                "schema_version": payload["intent_authority_schema_version"],
            },
        )

    def _resolve_start_authority(self, payload: dict[str, Any]) -> CatalogRecord:
        return self._resolve_or_fail(
            "start_authority",
            payload["start_authority_id"],
            payload["start_authority_record_sha256"],
            generation=payload["start_authority_generation"],
            event_type="ACCESS_STARTED",
            incomplete_kind="start_authority",
            expected={
                "schema_version": payload["start_authority_schema_version"],
            },
        )

    def _resolve_attempt_plan(self, payload: dict[str, Any]) -> CatalogRecord:
        return self._resolve_or_fail(
            "attempt_plan",
            payload["attempt_plan_record_id"],
            payload["attempt_plan_record_sha256"],
            version=payload["attempt_plan_record_version"],
            event_type="ATTEMPT_ALLOCATED",
            incomplete_kind="attempt_plan",
            expected={
                "schema_version": payload["attempt_plan_record_schema_version"],
                "canonicalization_id": payload["attempt_plan_record_canonicalization_id"],
                "authority_id": payload["attempt_plan_authority_id"],
                "authority_version": payload["attempt_plan_authority_version"],
                "registry_sha256": payload["attempt_plan_authority_registry_sha256"],
            },
        )

    def _resolve_attempt_plan_acceptance(self, payload: dict[str, Any]) -> CatalogRecord:
        return self._resolve_or_fail(
            "attempt_plan_acceptance",
            payload["attempt_plan_acceptance_decision_id"],
            payload["attempt_plan_acceptance_record_sha256"],
            generation=payload["attempt_plan_acceptance_generation"],
            event_type="ATTEMPT_ALLOCATED",
            incomplete_kind="attempt_plan_acceptance",
            expected={
                "schema_version": payload["attempt_plan_acceptance_schema_version"],
            },
        )

    def _resolve_attempt_allocation_authority(
        self, payload: dict[str, Any]
    ) -> CatalogRecord:
        return self._resolve_or_fail(
            "attempt_allocation_authority",
            payload["allocation_authority_id"],
            payload["allocation_authority_record_sha256"],
            generation=payload["allocation_authority_generation"],
            event_type="ATTEMPT_ALLOCATED",
            incomplete_kind="attempt_allocation_authority",
            expected={
                "schema_version": payload["allocation_authority_schema_version"],
            },
        )

    def _resolve_attempt_readiness(self, payload: dict[str, Any]) -> CatalogRecord:
        return self._resolve_or_fail(
            "attempt_readiness",
            payload["readiness_record_id"],
            payload["readiness_record_sha256"],
            version=payload["readiness_record_version"],
            event_type="ATTEMPT_STARTED",
            incomplete_kind="attempt_readiness",
            expected={
                "schema_version": payload["readiness_record_schema_version"],
                "canonicalization_id": payload["readiness_record_canonicalization_id"],
                "authority_id": payload["readiness_authority_id"],
                "authority_version": payload["readiness_authority_version"],
                "registry_sha256": payload["readiness_authority_registry_sha256"],
            },
        )

    def _resolve_attempt_start_authority(self, payload: dict[str, Any]) -> CatalogRecord:
        return self._resolve_or_fail(
            "attempt_start_authority",
            payload["start_authority_id"],
            payload["start_authority_record_sha256"],
            generation=payload["start_authority_generation"],
            event_type="ATTEMPT_STARTED",
            incomplete_kind="attempt_start_authority",
            expected={
                "schema_version": payload["start_authority_schema_version"],
            },
        )

    def _attempts_for_trial(self, trial_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT event_json FROM events WHERE event_type = 'ATTEMPT_ALLOCATED' "
            "ORDER BY sequence"
        ).fetchall()
        found = []
        for row in rows:
            event = json.loads(row[0])
            if event["payload"].get("trial_id") == trial_id:
                found.append(event)
        return found

    def _has_attempt_start(self, attempt_id: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM events WHERE event_type = 'ATTEMPT_STARTED' "
            "AND subject_id = ? LIMIT 1",
            (attempt_id,),
        ).fetchone()
        return row is not None

    @staticmethod
    def _operational_values(body: dict[str, Any]) -> dict[str, Any]:
        return {field: body.get(field) for field in OPERATIONAL_VALUE_FIELDS}

    @staticmethod
    def _inventory_catalog_key(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "inventory_authority_id": payload["inventory_authority_id"],
            "inventory_authority_registry_sha256": payload[
                "inventory_authority_registry_sha256"
            ],
            "inventory_authority_version": payload["inventory_authority_version"],
            "inventory_record_id": payload["inventory_record_id"],
            "inventory_record_schema_version": payload["inventory_record_schema_version"],
            "inventory_record_version": payload["inventory_record_version"],
            "inventory_record_canonicalization_id": payload[
                "inventory_record_canonicalization_id"
            ],
            "sealed_trial_inventory_sha256": payload["sealed_trial_inventory_sha256"],
        }

    @staticmethod
    def _inventory_acceptance_tuple(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "inventory_acceptance_decision_id": payload[
                "inventory_acceptance_decision_id"
            ],
            "inventory_acceptance_generation": payload["inventory_acceptance_generation"],
            "inventory_acceptance_schema_version": payload[
                "inventory_acceptance_schema_version"
            ],
            "inventory_acceptance_record_sha256": payload[
                "inventory_acceptance_record_sha256"
            ],
        }

    @staticmethod
    def _plan_catalog_key(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "attempt_plan_authority_id": payload["attempt_plan_authority_id"],
            "attempt_plan_authority_registry_sha256": payload[
                "attempt_plan_authority_registry_sha256"
            ],
            "attempt_plan_authority_version": payload["attempt_plan_authority_version"],
            "attempt_plan_record_id": payload["attempt_plan_record_id"],
            "attempt_plan_record_schema_version": payload[
                "attempt_plan_record_schema_version"
            ],
            "attempt_plan_record_version": payload["attempt_plan_record_version"],
            "attempt_plan_record_canonicalization_id": payload[
                "attempt_plan_record_canonicalization_id"
            ],
            "attempt_plan_record_sha256": payload["attempt_plan_record_sha256"],
        }

    @staticmethod
    def _plan_acceptance_tuple(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "attempt_plan_acceptance_decision_id": payload[
                "attempt_plan_acceptance_decision_id"
            ],
            "attempt_plan_acceptance_generation": payload[
                "attempt_plan_acceptance_generation"
            ],
            "attempt_plan_acceptance_schema_version": payload[
                "attempt_plan_acceptance_schema_version"
            ],
            "attempt_plan_acceptance_record_sha256": payload[
                "attempt_plan_acceptance_record_sha256"
            ],
        }

    @staticmethod
    def _attempt_allocation_authority_tuple(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "allocation_authority_id": payload["allocation_authority_id"],
            "allocation_authority_generation": payload["allocation_authority_generation"],
            "allocation_authority_schema_version": payload[
                "allocation_authority_schema_version"
            ],
            "allocation_authority_record_sha256": payload[
                "allocation_authority_record_sha256"
            ],
        }

    @staticmethod
    def _family_tuple(family_event: dict[str, Any]) -> dict[str, Any]:
        payload = family_event["payload"]
        return {
            "trial_family_id": family_event["subject_id"],
            "definition": {
                "family_authority_id": payload["family_authority_id"],
                "family_authority_version": payload["family_authority_version"],
                "family_authority_registry_sha256": payload[
                    "family_authority_registry_sha256"
                ],
                "family_definition_record_id": payload["family_definition_record_id"],
                "family_definition_record_version": payload[
                    "family_definition_record_version"
                ],
                "family_definition_schema_version": payload[
                    "family_definition_schema_version"
                ],
                "family_definition_canonicalization_id": payload[
                    "family_definition_canonicalization_id"
                ],
                "family_definition_record_sha256": payload[
                    "family_definition_record_sha256"
                ],
            },
            "acceptance": {
                "family_acceptance_decision_id": payload[
                    "family_acceptance_decision_id"
                ],
                "family_acceptance_generation": payload["family_acceptance_generation"],
                "family_acceptance_schema_version": payload[
                    "family_acceptance_schema_version"
                ],
                "family_acceptance_record_sha256": payload[
                    "family_acceptance_record_sha256"
                ],
            },
        }

    @staticmethod
    def _sample_tuple(sample_event: dict[str, Any]) -> dict[str, Any]:
        payload = sample_event["payload"]
        return {
            "sample_id": sample_event["subject_id"],
            "record": {
                "sample_authority_id": payload["sample_authority_id"],
                "sample_authority_version": payload["sample_authority_version"],
                "sample_authority_registry_sha256": payload[
                    "sample_authority_registry_sha256"
                ],
                "sample_record_id": payload["sample_record_id"],
                "sample_record_version": payload["sample_record_version"],
                "sample_record_schema_version": payload["sample_record_schema_version"],
                "sample_record_canonicalization_id": payload[
                    "sample_record_canonicalization_id"
                ],
                "sample_record_sha256": payload["sample_record_sha256"],
            },
            "acceptance": {
                "sample_acceptance_decision_id": payload[
                    "sample_acceptance_decision_id"
                ],
                "sample_acceptance_generation": payload["sample_acceptance_generation"],
                "sample_acceptance_schema_version": payload[
                    "sample_acceptance_schema_version"
                ],
                "sample_acceptance_record_sha256": payload[
                    "sample_acceptance_record_sha256"
                ],
            },
            "projection": {
                "sample_public_projection_id": payload["sample_public_projection_id"],
                "sample_public_projection_schema_version": payload[
                    "sample_public_projection_schema_version"
                ],
                "sample_public_projection_sha256": payload[
                    "sample_public_projection_sha256"
                ],
            },
            "publication_approval": {
                "sample_publication_approval_id": payload[
                    "sample_publication_approval_id"
                ],
                "sample_publication_approval_generation": payload[
                    "sample_publication_approval_generation"
                ],
                "sample_publication_approval_schema_version": payload[
                    "sample_publication_approval_schema_version"
                ],
                "sample_publication_approval_record_sha256": payload[
                    "sample_publication_approval_record_sha256"
                ],
            },
        }

    @staticmethod
    def _trial_tuple(trial_event: dict[str, Any]) -> dict[str, Any]:
        payload = trial_event["payload"]
        return {
            "trial_id": trial_event["subject_id"],
            "definition": {
                "trial_definition_authority_id": payload["trial_definition_authority_id"],
                "trial_definition_authority_registry_sha256": payload[
                    "trial_definition_authority_registry_sha256"
                ],
                "trial_definition_authority_version": payload[
                    "trial_definition_authority_version"
                ],
                "trial_definition_record_id": payload["trial_definition_record_id"],
                "trial_definition_record_schema_version": payload[
                    "trial_definition_record_schema_version"
                ],
                "trial_definition_record_version": payload[
                    "trial_definition_record_version"
                ],
                "trial_definition_record_canonicalization_id": payload[
                    "trial_definition_record_canonicalization_id"
                ],
                "trial_definition_record_sha256": payload[
                    "trial_definition_record_sha256"
                ],
            },
            "acceptance": {
                "trial_definition_acceptance_decision_id": payload[
                    "trial_definition_acceptance_decision_id"
                ],
                "trial_definition_acceptance_generation": payload[
                    "trial_definition_acceptance_generation"
                ],
                "trial_definition_acceptance_schema_version": payload[
                    "trial_definition_acceptance_schema_version"
                ],
                "trial_definition_acceptance_record_sha256": payload[
                    "trial_definition_acceptance_record_sha256"
                ],
            },
            "projection": {
                "trial_definition_public_projection_id": payload[
                    "trial_definition_public_projection_id"
                ],
                "trial_definition_public_projection_schema_version": payload[
                    "trial_definition_public_projection_schema_version"
                ],
                "trial_definition_public_projection_sha256": payload[
                    "trial_definition_public_projection_sha256"
                ],
            },
            "publication_approval": {
                "trial_definition_publication_approval_id": payload[
                    "trial_definition_publication_approval_id"
                ],
                "trial_definition_publication_approval_generation": payload[
                    "trial_definition_publication_approval_generation"
                ],
                "trial_definition_publication_approval_schema_version": payload[
                    "trial_definition_publication_approval_schema_version"
                ],
                "trial_definition_publication_approval_record_sha256": payload[
                    "trial_definition_publication_approval_record_sha256"
                ],
            },
            "allocation_authority": {
                "allocation_authority_id": payload["allocation_authority_id"],
                "allocation_authority_generation": payload[
                    "allocation_authority_generation"
                ],
                "allocation_authority_schema_version": payload[
                    "allocation_authority_schema_version"
                ],
                "allocation_authority_record_sha256": payload[
                    "allocation_authority_record_sha256"
                ],
            },
        }

    @staticmethod
    def _source_entry(
        subject_type: str,
        subject_id: str,
        event_type: str,
        event: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "subject_type": subject_type,
            "subject_id": subject_id,
            "event_type": event_type,
            "source": {
                "event_id": event["event_id"],
                "event_sha256": digest_json(event)
                if "event_sha256" not in event
                else event["event_sha256"],
            },
        }

    def _retained_sources(
        self,
        *,
        family_event: dict[str, Any],
        sample_events: list[dict[str, Any]],
        trial_event: dict[str, Any],
        seal_event: dict[str, Any],
        allocation_event: dict[str, Any],
    ) -> list[dict[str, Any]]:
        sources = [
            self._source_entry(
                "trial_family",
                family_event["subject_id"],
                "TRIAL_FAMILY_REGISTERED",
                family_event,
            )
        ]
        for sample_event in sample_events:
            sources.append(
                self._source_entry(
                    "sample",
                    sample_event["subject_id"],
                    "SAMPLE_REGISTERED",
                    sample_event,
                )
            )
        sources.extend(
            [
                self._source_entry(
                    "trial",
                    trial_event["subject_id"],
                    "TRIAL_ALLOCATED",
                    trial_event,
                ),
                self._source_entry(
                    "campaign",
                    seal_event["subject_id"],
                    "CAMPAIGN_INVENTORY_SEALED",
                    seal_event,
                ),
                self._source_entry(
                    "attempt",
                    allocation_event["subject_id"],
                    "ATTEMPT_ALLOCATED",
                    allocation_event,
                ),
            ]
        )
        return sources

    @staticmethod
    def _assert_path_outside_repository(database_path: Path) -> None:
        resolved = database_path.resolve()
        for parent in resolved.parents:
            if (parent / "AGENTS.md").is_file() and (parent / "src" / "ledger").is_dir():
                _fail(
                    "LEDGER_DATABASE_PATH_IN_REPOSITORY",
                    "caller-supplied database path must be outside the canonical repository",
                )


def open_path_a_store(
    database_path: str | Path,
    catalog: SyntheticCatalog,
    *,
    clock: Clock | None = None,
    inject_access_started_failure: bool = False,
    inject_catalog_mutation: Callable[[], None] | None = None,
) -> LedgerStore:
    """Open a Path A ledger at a caller-supplied path outside the repository."""
    return LedgerStore(
        database_path,
        catalog,
        clock=clock,
        checkpoint="path_a",
        inject_access_started_failure=inject_access_started_failure,
        inject_catalog_mutation=inject_catalog_mutation,
    )


def open_path_b_store(
    database_path: str | Path,
    catalog: SyntheticCatalog,
    *,
    clock: Clock | None = None,
    inject_catalog_mutation: Callable[[], None] | None = None,
) -> LedgerStore:
    """Open a Path B ledger at a caller-supplied path outside the repository."""
    return LedgerStore(
        database_path,
        catalog,
        clock=clock,
        checkpoint="path_b",
        inject_catalog_mutation=inject_catalog_mutation,
    )

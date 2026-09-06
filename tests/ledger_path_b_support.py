"""Synthetic Path B fixture helpers. DIAGNOSTIC_ONLY; no market data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ledger.runtime import CatalogRecord, LedgerStore, SyntheticCatalog, digest_json
from ledger_path_a_support import (
    DEFAULT_CAPABILITY_EXPIRY,
    ENV_LOCK,
    ENVIRONMENT,
    EXPECTED_OUTPUT,
    INPUT_MANIFEST,
    RETRY_POLICY,
    STAMP,
    PathAIds,
    add_record,
    bind_inventory_trial,
    bind_parent_digests,
    bind_sample_source,
    build_path_a_catalog,
    campaign_request,
    default_ids,
    epoch_request,
    experiment_request,
    family_request,
    request,
    sample_request,
    seal_request,
    trial_request,
    typed_id,
)


PLAN_REGISTRY = "77" * 32
READINESS_REGISTRY = "aa" * 32


@dataclass(frozen=True)
class PathBIds:
    a: PathAIds
    attempt: str
    attempt_event: str
    attempt_op: str
    started_event: str
    started_op: str
    execute_capability: str
    plan_issuer: str
    plan_reviewer: str
    attempt_actor: str
    attempt_start_actor: str
    executor: str
    readiness_issuer: str
    readiness_reviewer: str
    attempt_authority_issuer: str
    attempt_start_authority_issuer: str


def default_path_b_ids() -> PathBIds:
    return PathBIds(
        a=default_ids(),
        attempt=typed_id("att", 1),
        attempt_event=typed_id("evt", 19),
        attempt_op=typed_id("opn", 19),
        started_event=typed_id("evt", 20),
        started_op=typed_id("opn", 20),
        execute_capability=typed_id("cap", 8),
        plan_issuer=typed_id("act", 60),
        plan_reviewer=typed_id("act", 61),
        attempt_actor=typed_id("act", 62),
        attempt_start_actor=typed_id("act", 63),
        executor=typed_id("act", 64),
        readiness_issuer=typed_id("act", 65),
        readiness_reviewer=typed_id("act", 66),
        attempt_authority_issuer=typed_id("act", 68),
        attempt_start_authority_issuer=typed_id("act", 67),
    )


def _stored(event: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in event.items() if key != "event_sha256"}


def build_path_b_catalog(
    ids: PathBIds | None = None,
    *,
    plan_producers: list[str] | None = None,
    plan_reviewer: str | None = None,
    **path_a_kwargs: Any,
) -> tuple[PathBIds, SyntheticCatalog, dict[str, CatalogRecord]]:
    ids = ids or default_path_b_ids()
    _path_a_ids, catalog, records = build_path_a_catalog(ids.a, **path_a_kwargs)
    del _path_a_ids
    definition = records["trial_definition"]
    plan_reviewer = plan_reviewer or ids.plan_reviewer
    records["attempt_plan"] = add_record(
        catalog,
        kind="attempt_plan",
        record_id="attempt-plan-1",
        schema_version="attempt_plan_record_v1",
        sha256="",
        body={
            "issuer_actor_id": ids.plan_issuer,
            "private_input_producer_actor_ids": plan_producers or [],
            "trial_id": ids.a.trial,
            "attempt_id": ids.attempt,
            "campaign_id": ids.a.campaign,
            "ledger_id": ids.a.ledger,
            "code_identity": definition.body["code_identity"],
            "environment_id": ENVIRONMENT,
            "environment_lock_sha256": ENV_LOCK,
            "input_manifest_sha256": INPUT_MANIFEST,
            "retry_policy_sha256": RETRY_POLICY,
            "expected_output_inventory_sha256": EXPECTED_OUTPUT,
        },
        version=1,
        authority_id="attempt-plan-authority-1",
        registry_sha256=PLAN_REGISTRY,
        authority_version=1,
        stream_key="attempt_plan:attempt-plan-1",
    )
    records["attempt_plan_acceptance"] = add_record(
        catalog,
        kind="attempt_plan_acceptance",
        record_id="attempt-plan-acceptance-1",
        schema_version="attempt_plan_acceptance_v1",
        sha256="",
        body={
            "reviewer_actor_id": plan_reviewer,
            "issuer_actor_id": ids.plan_issuer,
            "trial_id": ids.a.trial,
            "attempt_id": ids.attempt,
            "campaign_id": ids.a.campaign,
            "campaign_scope_ids": [ids.a.campaign],
            "attempt_plan_authority_id": records["attempt_plan"].authority_id,
            "attempt_plan_authority_registry_sha256": records[
                "attempt_plan"
            ].registry_sha256,
            "attempt_plan_authority_version": records["attempt_plan"].authority_version,
            "attempt_plan_record_id": records["attempt_plan"].record_id,
            "attempt_plan_record_sha256": records["attempt_plan"].sha256,
            "campaign_inventory_seal_event_id": ids.a.seal_event,
            "campaign_inventory_seal_event_sha256": "pending-seal-event",
            "trial_allocation_event_id": ids.a.trial_event,
            "trial_allocation_event_sha256": "pending-trial-event",
        },
        generation=1,
        stream_key="attempt_plan_acceptance:attempt-1",
    )
    records["attempt_allocation_authority"] = add_record(
        catalog,
        kind="attempt_allocation_authority",
        record_id="attempt-allocation-authority-1",
        schema_version="attempt_allocation_authority_v1",
        sha256="",
        body={
            "issuer_actor_id": ids.attempt_authority_issuer,
            "authorized_actor_id": ids.attempt_actor,
            "operation": "ATTEMPT_ALLOCATED",
            "campaign_id": ids.a.campaign,
            "trial_id": ids.a.trial,
            "attempt_id": ids.attempt,
            "attempt_plan_record_id": "attempt-plan-1",
            "attempt_plan_record_sha256": records["attempt_plan"].sha256,
        },
        generation=1,
        stream_key="attempt_allocation_authority:attempt-1",
    )
    records["attempt_readiness"] = add_record(
        catalog,
        kind="attempt_readiness",
        record_id="attempt-readiness-1",
        schema_version="attempt_start_readiness_record_v1",
        sha256="",
        body={
            "outcome": "READY",
            "issuer_actor_id": ids.readiness_issuer,
            "reviewer_actor_id": ids.readiness_reviewer,
            "executor_actor_id": ids.executor,
            "private_input_producer_actor_ids": [],
            "trial_id": ids.a.trial,
            "attempt_id": ids.attempt,
            "campaign_id": ids.a.campaign,
            "code_identity": definition.body["code_identity"],
            "environment_id": ENVIRONMENT,
            "environment_lock_sha256": ENV_LOCK,
            "input_manifest_sha256": INPUT_MANIFEST,
            "retry_policy_sha256": RETRY_POLICY,
            "expected_output_inventory_sha256": EXPECTED_OUTPUT,
        },
        version=1,
        authority_id="attempt-readiness-authority-1",
        registry_sha256=READINESS_REGISTRY,
        authority_version=1,
        stream_key="attempt_readiness:attempt-readiness-1",
    )
    records["attempt_start_authority"] = add_record(
        catalog,
        kind="attempt_start_authority",
        record_id="attempt-start-authority-1",
        schema_version="attempt_start_authority_v1",
        sha256="",
        body={
            "issuer_actor_id": ids.attempt_start_authority_issuer,
            "authorized_actor_id": ids.attempt_start_actor,
            "executor_actor_id": ids.executor,
            "operation": "ATTEMPT_STARTED",
            "campaign_id": ids.a.campaign,
            "trial_id": ids.a.trial,
            "attempt_id": ids.attempt,
            "attempt_allocation_event_id": ids.attempt_event,
            "attempt_allocation_event_sha256": "pending-attempt-event",
            "readiness_record_id": "attempt-readiness-1",
            "readiness_record_sha256": records["attempt_readiness"].sha256,
        },
        generation=1,
        stream_key="attempt_start_authority:attempt-1",
    )
    return ids, catalog, records


def append_through_seal(store, ids: PathAIds, records: dict[str, CatalogRecord]):
    epoch = store.append(epoch_request(ids))
    campaign = store.append(campaign_request(ids))
    experiment = store.append(experiment_request(ids))
    family = store.append(family_request(ids, records))
    sample = store.append(sample_request(ids, records))
    bind_sample_source(records, sample["event_sha256"])
    trial_req = trial_request(ids, records)
    bind_parent_digests(
        trial_req,
        campaign_sha256=campaign["event_sha256"],
        experiment_sha256=experiment["event_sha256"],
        family_sha256=family["event_sha256"],
    )
    trial = store.append(trial_req)
    bind_inventory_trial(records, trial["event_sha256"])
    seal_req = seal_request(
        ids,
        records,
        predecessor_sequence=trial["sequence"],
        predecessor_sha256=trial["event_sha256"],
    )
    seal_req["payload"]["campaign_allocation_event_sha256"] = campaign["event_sha256"]
    seal = store.append(seal_req)
    return {
        "epoch": epoch,
        "campaign": campaign,
        "experiment": experiment,
        "family": family,
        "sample": sample,
        "trial": trial,
        "seal": seal,
    }


def refresh_plan_and_authority(records: dict[str, CatalogRecord]) -> None:
    records["attempt_plan"].sha256 = digest_json(records["attempt_plan"].body)
    authority = records["attempt_allocation_authority"]
    authority.body["attempt_plan_record_sha256"] = records["attempt_plan"].sha256
    authority.sha256 = digest_json(authority.body)
    acceptance = records["attempt_plan_acceptance"]
    acceptance.body["attempt_plan_record_id"] = records["attempt_plan"].record_id
    acceptance.body["attempt_plan_record_sha256"] = records["attempt_plan"].sha256
    acceptance.body["attempt_plan_authority_id"] = records["attempt_plan"].authority_id
    acceptance.body["attempt_plan_authority_registry_sha256"] = records[
        "attempt_plan"
    ].registry_sha256
    acceptance.body["attempt_plan_authority_version"] = records[
        "attempt_plan"
    ].authority_version
    acceptance.sha256 = digest_json(acceptance.body)


def bind_readiness_after_seal(
    records: dict[str, CatalogRecord],
    committed: dict[str, dict[str, Any]],
) -> None:
    readiness = records["attempt_readiness"]
    family = _stored(committed["family"])
    sample = _stored(committed["sample"])
    trial = _stored(committed["trial"])
    seal = _stored(committed["seal"])
    readiness.body["inventory_catalog_key"] = LedgerStore._inventory_catalog_key(
        seal["payload"]
    )
    readiness.body["inventory_acceptance"] = LedgerStore._inventory_acceptance_tuple(
        seal["payload"]
    )
    readiness.body["seal_event_id_sha256"] = {
        "event_id": committed["seal"]["event_id"],
        "event_sha256": committed["seal"]["event_sha256"],
    }
    readiness.body["family_definition_and_acceptance"] = [
        LedgerStore._family_tuple(family)
    ]
    readiness.body["sample_record_acceptance_projection_publication_approval"] = [
        LedgerStore._sample_tuple(sample)
    ]
    readiness.body["trial_definition_acceptance_projection_allocation_authority"] = (
        LedgerStore._trial_tuple(trial)
    )
    readiness.body["attempt_plan_catalog_key"] = {
        "attempt_plan_authority_id": records["attempt_plan"].authority_id,
        "attempt_plan_authority_registry_sha256": records["attempt_plan"].registry_sha256,
        "attempt_plan_authority_version": records["attempt_plan"].authority_version,
        "attempt_plan_record_id": records["attempt_plan"].record_id,
        "attempt_plan_record_schema_version": records["attempt_plan"].schema_version,
        "attempt_plan_record_version": records["attempt_plan"].version,
        "attempt_plan_record_canonicalization_id": records[
            "attempt_plan"
        ].canonicalization_id,
        "attempt_plan_record_sha256": records["attempt_plan"].sha256,
    }
    acceptance = records["attempt_plan_acceptance"]
    acceptance.body["campaign_inventory_seal_event_id"] = committed["seal"]["event_id"]
    acceptance.body["campaign_inventory_seal_event_sha256"] = committed["seal"][
        "event_sha256"
    ]
    acceptance.body["trial_allocation_event_id"] = committed["trial"]["event_id"]
    acceptance.body["trial_allocation_event_sha256"] = committed["trial"][
        "event_sha256"
    ]
    acceptance.sha256 = digest_json(acceptance.body)
    readiness.body["attempt_plan_acceptance"] = {
        "attempt_plan_acceptance_decision_id": acceptance.record_id,
        "attempt_plan_acceptance_generation": acceptance.generation,
        "attempt_plan_acceptance_schema_version": acceptance.schema_version,
        "attempt_plan_acceptance_record_sha256": acceptance.sha256,
    }
    readiness.body["attempt_allocation_authority"] = {
        "allocation_authority_id": records["attempt_allocation_authority"].record_id,
        "allocation_authority_generation": records[
            "attempt_allocation_authority"
        ].generation,
        "allocation_authority_schema_version": records[
            "attempt_allocation_authority"
        ].schema_version,
        "allocation_authority_record_sha256": records[
            "attempt_allocation_authority"
        ].sha256,
    }
    readiness.sha256 = digest_json(readiness.body)


def bind_readiness_after_allocation(
    records: dict[str, CatalogRecord],
    committed: dict[str, dict[str, Any]],
) -> None:
    readiness = records["attempt_readiness"]
    family = _stored(committed["family"])
    sample = _stored(committed["sample"])
    trial = _stored(committed["trial"])
    seal = _stored(committed["seal"])
    allocation = _stored(committed["attempt"])
    readiness.body["attempt_allocation_event"] = {
        "event_id": committed["attempt"]["event_id"],
        "event_sha256": committed["attempt"]["event_sha256"],
    }
    readiness.body["retained_source_event_id_hash"] = [
        LedgerStore._source_entry(
            "trial_family", family["subject_id"], "TRIAL_FAMILY_REGISTERED", family
        ),
        LedgerStore._source_entry(
            "sample", sample["subject_id"], "SAMPLE_REGISTERED", sample
        ),
        LedgerStore._source_entry(
            "trial", trial["subject_id"], "TRIAL_ALLOCATED", trial
        ),
        LedgerStore._source_entry(
            "campaign", seal["subject_id"], "CAMPAIGN_INVENTORY_SEALED", seal
        ),
        LedgerStore._source_entry(
            "attempt", allocation["subject_id"], "ATTEMPT_ALLOCATED", allocation
        ),
    ]
    readiness.sha256 = digest_json(readiness.body)
    authority = records["attempt_start_authority"]
    authority.body["attempt_allocation_event_id"] = committed["attempt"]["event_id"]
    authority.body["attempt_allocation_event_sha256"] = committed["attempt"][
        "event_sha256"
    ]
    authority.body["readiness_record_sha256"] = readiness.sha256
    authority.sha256 = digest_json(authority.body)


def refresh_readiness(records: dict[str, CatalogRecord]) -> None:
    records["attempt_readiness"].sha256 = digest_json(
        records["attempt_readiness"].body
    )
    authority = records["attempt_start_authority"]
    authority.body["readiness_record_sha256"] = records["attempt_readiness"].sha256
    authority.sha256 = digest_json(authority.body)


def attempt_request(ids: PathBIds, records: dict[str, CatalogRecord]) -> dict[str, Any]:
    plan = records["attempt_plan"]
    acceptance = records["attempt_plan_acceptance"]
    authority = records["attempt_allocation_authority"]
    return request(
        event_type="ATTEMPT_ALLOCATED",
        event_id=ids.attempt_event,
        operation_id=ids.attempt_op,
        subject_type="attempt",
        subject_id=ids.attempt,
        actor_id=ids.attempt_actor,
        ledger_id=ids.a.ledger,
        payload={
            "allocation_authority_generation": 1,
            "allocation_authority_id": authority.record_id,
            "allocation_authority_record_sha256": authority.sha256,
            "allocation_authority_schema_version": "attempt_allocation_authority_v1",
            "attempt_plan_acceptance_decision_id": acceptance.record_id,
            "attempt_plan_acceptance_generation": 1,
            "attempt_plan_acceptance_record_sha256": acceptance.sha256,
            "attempt_plan_acceptance_schema_version": "attempt_plan_acceptance_v1",
            "attempt_plan_authority_id": plan.authority_id,
            "attempt_plan_authority_registry_sha256": plan.registry_sha256,
            "attempt_plan_authority_version": plan.authority_version,
            "attempt_plan_record_canonicalization_id": plan.canonicalization_id,
            "attempt_plan_record_id": plan.record_id,
            "attempt_plan_record_schema_version": plan.schema_version,
            "attempt_plan_record_sha256": plan.sha256,
            "attempt_plan_record_version": plan.version,
            "campaign_inventory_seal_event_id": ids.a.seal_event,
            "campaign_inventory_seal_event_sha256": "pending-seal-event",
            "campaign_scope_ids": [ids.a.campaign],
            "expected_output_inventory_sha256": EXPECTED_OUTPUT,
            "relation": {"attempt_kind": "first_attempt", "attempt_ordinal": 1},
            "trial_allocation_event_id": ids.a.trial_event,
            "trial_allocation_event_sha256": "pending-trial-event",
            "trial_id": ids.a.trial,
        },
    )


def execution_capability_record(
    ids: PathBIds,
    records: dict[str, CatalogRecord],
    allocation: dict[str, Any],
    *,
    recorded_at: str = STAMP,
    activation: str | None = None,
    expiry: str | None = None,
) -> dict[str, Any]:
    readiness = records["attempt_readiness"]
    authority = records["attempt_start_authority"]
    code = readiness.body["code_identity"]
    return {
        "schema_version": "attempt_execution_capability_record_v1",
        "canonicalization_id": "pit_canonical_json_v1",
        "execution_capability_id": ids.execute_capability,
        "execution_capability_record_version": 1,
        "ledger_id": ids.a.ledger,
        "campaign_id": ids.a.campaign,
        "trial_id": ids.a.trial,
        "attempt_id": ids.attempt,
        "start_event_id": ids.started_event,
        "attempt_allocation_event_id": allocation["event_id"],
        "attempt_allocation_event_sha256": allocation["event_sha256"],
        "readiness_record_id": readiness.record_id,
        "readiness_record_sha256": readiness.sha256,
        "start_authority_id": authority.record_id,
        "start_authority_record_sha256": authority.sha256,
        "executor_actor_id": readiness.body.get("executor_actor_id"),
        "code_tree_sha256": code["code_tree_sha256"],
        "environment_id": readiness.body["environment_id"],
        "environment_lock_sha256": readiness.body["environment_lock_sha256"],
        "activation": activation or recorded_at,
        "expiry": expiry or DEFAULT_CAPABILITY_EXPIRY,
        "one_use": True,
        "state": "CREATED",
    }


def started_request(
    ids: PathBIds,
    records: dict[str, CatalogRecord],
    allocation: dict[str, Any],
    *,
    activation: str | None = None,
    expiry: str | None = None,
) -> dict[str, Any]:
    readiness = records["attempt_readiness"]
    authority = records["attempt_start_authority"]
    capability_sha256 = digest_json(
        execution_capability_record(
            ids,
            records,
            allocation,
            activation=activation,
            expiry=expiry,
        )
    )
    return request(
        event_type="ATTEMPT_STARTED",
        event_id=ids.started_event,
        operation_id=ids.started_op,
        subject_type="attempt",
        subject_id=ids.attempt,
        actor_id=ids.attempt_start_actor,
        ledger_id=ids.a.ledger,
        payload={
            "attempt_allocation_event_id": allocation["event_id"],
            "attempt_allocation_event_sha256": allocation["event_sha256"],
            "campaign_scope_ids": [ids.a.campaign],
            "execution_capability_id": ids.execute_capability,
            "execution_capability_record_canonicalization_id": "pit_canonical_json_v1",
            "execution_capability_record_schema_version": (
                "attempt_execution_capability_record_v1"
            ),
            "execution_capability_record_sha256": capability_sha256,
            "execution_capability_record_version": 1,
            "readiness_authority_id": readiness.authority_id,
            "readiness_authority_registry_sha256": readiness.registry_sha256,
            "readiness_authority_version": readiness.authority_version,
            "readiness_record_canonicalization_id": readiness.canonicalization_id,
            "readiness_record_id": readiness.record_id,
            "readiness_record_schema_version": readiness.schema_version,
            "readiness_record_sha256": readiness.sha256,
            "readiness_record_version": readiness.version,
            "start_authority_generation": 1,
            "start_authority_id": authority.record_id,
            "start_authority_record_sha256": authority.sha256,
            "start_authority_schema_version": "attempt_start_authority_v1",
            "trial_id": ids.a.trial,
        },
    )

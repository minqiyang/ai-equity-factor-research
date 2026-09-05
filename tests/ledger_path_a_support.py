"""Synthetic Path A fixture helpers. DIAGNOSTIC_ONLY; no market data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ledger.runtime import (
    CatalogRecord,
    SyntheticCatalog,
    digest_json,
)


def typed_id(prefix: str, n: int) -> str:
    return f"{prefix}_{n:032x}"


DIGEST_A = "11" * 32
DIGEST_B = "22" * 32
DIGEST_C = "33" * 32
DIGEST_D = "44" * 32
DIGEST_E = "55" * 32
STAMP = "2026-09-05T12:00:00Z"
WINDOW = "synthetic-window"
FIELD_CLASS = "synthetic-field-class"
ENVIRONMENT = "synthetic-accessor-environment"
LINEAGE = "synthetic-canonical-lineage"
OVERLAP = "synthetic-canonical-overlap"
CODE_TREE = DIGEST_A
ENV_LOCK = DIGEST_B
INPUT_MANIFEST = DIGEST_C
RETRY_POLICY = DIGEST_D
EXPECTED_OUTPUT = DIGEST_E
AUTHORITY_REGISTRY = "66" * 32


@dataclass(frozen=True)
class PathAIds:
    ledger: str
    campaign: str
    experiment: str
    family: str
    sample: str
    trial: str
    capability: str
    epoch_event: str
    campaign_event: str
    experiment_event: str
    family_event: str
    sample_event: str
    trial_event: str
    seal_event: str
    intent_event: str
    started_event: str
    epoch_op: str
    campaign_op: str
    experiment_op: str
    family_op: str
    sample_op: str
    trial_op: str
    seal_op: str
    intent_op: str
    started_op: str
    epoch_actor: str
    campaign_actor: str
    experiment_actor: str
    family_issuer: str
    family_reviewer: str
    family_actor: str
    sample_producer: str
    sample_reviewer: str
    sample_actor: str
    trial_issuer: str
    trial_reviewer: str
    trial_actor: str
    inventory_issuer: str
    inventory_reviewer: str
    seal_authority_issuer: str
    seal_actor: str
    authorization_issuer: str
    intent_authority_issuer: str
    accessor: str
    intent_actor: str
    start_actor: str


def default_ids() -> PathAIds:
    return PathAIds(
        ledger=typed_id("ldg", 1),
        campaign=typed_id("cmp", 2),
        experiment=typed_id("exp", 3),
        family=typed_id("fam", 4),
        sample=typed_id("smp", 5),
        trial=typed_id("trl", 6),
        capability=typed_id("cap", 7),
        epoch_event=typed_id("evt", 10),
        campaign_event=typed_id("evt", 11),
        experiment_event=typed_id("evt", 12),
        family_event=typed_id("evt", 13),
        sample_event=typed_id("evt", 14),
        trial_event=typed_id("evt", 15),
        seal_event=typed_id("evt", 16),
        intent_event=typed_id("evt", 17),
        started_event=typed_id("evt", 18),
        epoch_op=typed_id("opn", 10),
        campaign_op=typed_id("opn", 11),
        experiment_op=typed_id("opn", 12),
        family_op=typed_id("opn", 13),
        sample_op=typed_id("opn", 14),
        trial_op=typed_id("opn", 15),
        seal_op=typed_id("opn", 16),
        intent_op=typed_id("opn", 17),
        started_op=typed_id("opn", 18),
        epoch_actor=typed_id("act", 1),
        campaign_actor=typed_id("act", 2),
        experiment_actor=typed_id("act", 3),
        family_issuer=typed_id("act", 10),
        family_reviewer=typed_id("act", 11),
        family_actor=typed_id("act", 12),
        sample_producer=typed_id("act", 20),
        sample_reviewer=typed_id("act", 21),
        sample_actor=typed_id("act", 22),
        trial_issuer=typed_id("act", 30),
        trial_reviewer=typed_id("act", 31),
        trial_actor=typed_id("act", 32),
        inventory_issuer=typed_id("act", 40),
        inventory_reviewer=typed_id("act", 41),
        seal_authority_issuer=typed_id("act", 42),
        seal_actor=typed_id("act", 43),
        authorization_issuer=typed_id("act", 50),
        intent_authority_issuer=typed_id("act", 51),
        accessor=typed_id("act", 52),
        intent_actor=typed_id("act", 53),
        start_actor=typed_id("act", 54),
    )


def add_record(catalog: SyntheticCatalog, **kwargs: Any) -> CatalogRecord:
    return catalog.add(CatalogRecord(**kwargs))


def build_path_a_catalog(
    ids: PathAIds | None = None,
    *,
    family_reviewer: str | None = None,
    sample_reviewer: str | None = None,
    trial_reviewer: str | None = None,
    inventory_reviewer: str | None = None,
    inventory_issuer: str | None = None,
    seal_authorized_actor: str | None = None,
    authorization_issuer: str | None = None,
    intent_authority_issuer: str | None = None,
    accessor: str | None = None,
    definition_campaign_scope: list[str] | None = None,
    sample_lineage: str | None = None,
    family_producers: list[str] | None = None,
    sample_producers: list[str] | None = None,
    trial_producers: list[str] | None = None,
    inventory_producers: list[str] | None = None,
    extra_sample_id: str | None = None,
) -> tuple[PathAIds, SyntheticCatalog, dict[str, CatalogRecord]]:
    ids = ids or default_ids()
    catalog = SyntheticCatalog()
    catalog.proven_digests.add(CODE_TREE)
    catalog.evidence_refs.update(
        {
            "synthetic_intent_evidence_ref",
            "synthetic_start_evidence_ref",
        }
    )
    family_reviewer = family_reviewer or ids.family_reviewer
    sample_reviewer = sample_reviewer or ids.sample_reviewer
    trial_reviewer = trial_reviewer or ids.trial_reviewer
    inventory_reviewer = inventory_reviewer or ids.inventory_reviewer
    inventory_issuer = inventory_issuer or ids.inventory_issuer
    seal_authorized_actor = seal_authorized_actor or ids.seal_actor
    authorization_issuer = authorization_issuer or ids.authorization_issuer
    intent_authority_issuer = intent_authority_issuer or ids.intent_authority_issuer
    accessor = accessor or ids.accessor
    campaign_scope = [ids.campaign]
    definition_scope = definition_campaign_scope or campaign_scope
    lineage = LINEAGE if sample_lineage is None else sample_lineage

    records: dict[str, CatalogRecord] = {}
    records["family_definition"] = add_record(
        catalog,
        kind="family_definition",
        record_id="family-definition-1",
        schema_version="trial_family_definition_v1",
        sha256="",
        body={
            "issuer_actor_id": ids.family_issuer,
            "private_input_producer_actor_ids": family_producers or [],
            "trial_family_id": ids.family,
            "campaign_scope_ids": campaign_scope,
        },
        version=1,
        stream_key="family_definition:family-definition-1",
    )
    records["family_acceptance"] = add_record(
        catalog,
        kind="family_acceptance",
        record_id="family-acceptance-1",
        schema_version="trial_family_definition_acceptance_v1",
        sha256="",
        body={
            "issuer_actor_id": ids.family_issuer,
            "reviewer_actor_id": family_reviewer,
            "trial_family_id": ids.family,
        },
        generation=1,
        stream_key="family_acceptance:family-1",
    )
    sample_body: dict[str, Any] = {
        "producer_actor_id": ids.sample_producer,
        "private_input_producer_actor_ids": sample_producers or [],
        "sample_id": ids.sample,
        "campaign_scope_ids": campaign_scope,
        "canonical_overlap_id": OVERLAP,
    }
    if lineage is not None:
        sample_body["canonical_sample_lineage_id"] = lineage
    records["sample_record"] = add_record(
        catalog,
        kind="sample_record",
        record_id="sample-record-1",
        schema_version="stage3_sample_record_v1",
        sha256="",
        body=sample_body,
        version=1,
        authority_id="sample-authority-1",
        registry_sha256=AUTHORITY_REGISTRY,
        authority_version=1,
        stream_key="sample_record:sample-record-1",
    )
    records["sample_acceptance"] = add_record(
        catalog,
        kind="sample_acceptance",
        record_id="sample-acceptance-1",
        schema_version="stage3_sample_acceptance_v1",
        sha256="",
        body={
            "producer_actor_id": ids.sample_producer,
            "reviewer_actor_id": sample_reviewer,
        },
        generation=1,
        stream_key="sample_acceptance:sample-1",
    )
    records["sample_projection"] = add_record(
        catalog,
        kind="sample_projection",
        record_id="sample-projection-1",
        schema_version="public_redacted_projection_v1",
        sha256="",
        body={"sample_id": ids.sample},
        stream_key="sample_projection:sample-1",
    )
    records["sample_publication_approval"] = add_record(
        catalog,
        kind="sample_publication_approval",
        record_id="sample-publication-approval-1",
        schema_version="sample_public_projection_approval_v1",
        sha256="",
        body={"sample_id": ids.sample},
        generation=1,
        stream_key="sample_publication_approval:sample-1",
    )
    sample_bindings = [
        {
            "sample_id": ids.sample,
            "source_event_id": ids.sample_event,
            "source_event_sha256": "pending-sample-event",
        }
    ]
    if extra_sample_id is not None:
        sample_bindings.append(
            {
                "sample_id": extra_sample_id,
                "source_event_id": ids.sample_event,
                "source_event_sha256": "pending-sample-event",
            }
        )
    records["trial_definition"] = add_record(
        catalog,
        kind="trial_definition",
        record_id="trial-definition-1",
        schema_version="trial_definition_record_v1",
        sha256="",
        body={
            "issuer_actor_id": ids.trial_issuer,
            "private_input_producer_actor_ids": trial_producers or [],
            "trial_id": ids.trial,
            "trial_family_id": ids.family,
            "campaign_scope_ids": definition_scope,
            "sample_bindings": sample_bindings,
            "code_identity": {
                "code_commit_id": "abc123def456",
                "code_identity_kind": "clean_commit",
                "code_repository_id": "equity-factor-research",
                "code_tree_sha256": CODE_TREE,
            },
            "environment_id": ENVIRONMENT,
            "environment_lock_sha256": ENV_LOCK,
            "input_manifest_sha256": INPUT_MANIFEST,
            "retry_policy_sha256": RETRY_POLICY,
            "expected_output_inventory_sha256": EXPECTED_OUTPUT,
        },
        version=1,
        stream_key="trial_definition:trial-definition-1",
    )
    records["trial_acceptance"] = add_record(
        catalog,
        kind="trial_acceptance",
        record_id="trial-acceptance-1",
        schema_version="trial_definition_acceptance_v1",
        sha256="",
        body={"reviewer_actor_id": trial_reviewer, "trial_id": ids.trial},
        generation=1,
        stream_key="trial_acceptance:trial-1",
    )
    records["trial_projection"] = add_record(
        catalog,
        kind="trial_projection",
        record_id="trial-projection-1",
        schema_version="public_redacted_projection_v1",
        sha256="",
        body={"trial_id": ids.trial},
        stream_key="trial_projection:trial-1",
    )
    records["trial_publication_approval"] = add_record(
        catalog,
        kind="trial_publication_approval",
        record_id="trial-publication-approval-1",
        schema_version="trial_definition_public_projection_approval_v1",
        sha256="",
        body={"trial_id": ids.trial},
        generation=1,
        stream_key="trial_publication_approval:trial-1",
    )
    records["trial_allocation_authority"] = add_record(
        catalog,
        kind="trial_allocation_authority",
        record_id="trial-allocation-authority-1",
        schema_version="trial_allocation_authority_v1",
        sha256="",
        body={
            "issuer_actor_id": ids.trial_issuer,
            "authorized_actor_id": ids.trial_actor,
        },
        generation=1,
        stream_key="trial_allocation_authority:trial-1",
    )
    inventory_body = {
        "issuer_actor_id": inventory_issuer,
        "private_input_producer_actor_ids": inventory_producers or [],
        "campaign_id": ids.campaign,
        "campaign_scope_ids": campaign_scope,
        "trials": [
            {
                "trial_id": ids.trial,
                "trial_allocation_event_id": ids.trial_event,
                "trial_allocation_event_sha256": "pending-trial-event",
            }
        ],
    }
    records["inventory_record"] = add_record(
        catalog,
        kind="inventory_record",
        record_id="inventory-record-1",
        schema_version="campaign_inventory_record_v1",
        sha256="",
        body=inventory_body,
        version=1,
        stream_key="inventory_record:inventory-record-1",
    )
    records["inventory_acceptance"] = add_record(
        catalog,
        kind="inventory_acceptance",
        record_id="inventory-acceptance-1",
        schema_version="campaign_inventory_acceptance_v1",
        sha256="",
        body={"reviewer_actor_id": inventory_reviewer},
        generation=1,
        stream_key="inventory_acceptance:campaign-1",
    )
    records["seal_authority"] = add_record(
        catalog,
        kind="seal_authority",
        record_id="seal-authority-1",
        schema_version="campaign_inventory_seal_authority_v1",
        sha256="",
        body={
            "issuer_actor_id": ids.seal_authority_issuer,
            "authorized_actor_id": seal_authorized_actor,
        },
        generation=1,
        stream_key="seal_authority:campaign-1",
    )
    auth_body = {
        "issuer_actor_id": authorization_issuer,
        "accessor_actor_id": accessor,
        "sample_id": ids.sample,
        "campaign_id": ids.campaign,
        "affected_trial_ids": [ids.trial],
        "purpose": "validation",
        "intended_window_id": WINDOW,
        "intended_field_class_ids": [FIELD_CLASS],
        "accessor_code_tree_sha256": CODE_TREE,
        "accessor_environment_id": ENVIRONMENT,
        "accessor_environment_lock_sha256": ENV_LOCK,
    }
    records["access_authorization"] = add_record(
        catalog,
        kind="access_authorization",
        record_id="access-authorization-1",
        schema_version="sample_access_authorization_v1",
        sha256="",
        body=auth_body,
        stream_key="access_authorization:sample-1",
    )
    records["intent_authority"] = add_record(
        catalog,
        kind="intent_authority",
        record_id="intent-authority-1",
        schema_version="sample_access_intent_authority_v1",
        sha256="",
        body={
            "issuer_actor_id": intent_authority_issuer,
            "authorized_actor_id": ids.intent_actor,
            "operation": "ACCESS_INTENT",
            "sample_id": ids.sample,
            "campaign_id": ids.campaign,
        },
        generation=1,
        stream_key="intent_authority:sample-1",
    )
    records["start_authority"] = add_record(
        catalog,
        kind="start_authority",
        record_id="start-authority-1",
        schema_version="sample_access_start_authority_v1",
        sha256="",
        body={
            "issuer_actor_id": intent_authority_issuer,
            "authorized_actor_id": ids.start_actor,
            "access_intent_event_id": ids.intent_event,
            "access_intent_event_sha256": "pending-intent-event",
            "accessor_actor_id": accessor,
            "sample_id": ids.sample,
            "campaign_id": ids.campaign,
            "reader_code_tree_sha256": CODE_TREE,
            "reader_environment_id": ENVIRONMENT,
            "reader_environment_lock_sha256": ENV_LOCK,
        },
        generation=1,
        stream_key="start_authority:sample-1",
    )
    return ids, catalog, records


def request(
    *,
    event_type: str,
    event_id: str,
    operation_id: str,
    subject_type: str,
    subject_id: str,
    actor_id: str,
    ledger_id: str,
    payload: dict[str, Any],
    occurred_at: str = STAMP,
) -> dict[str, Any]:
    return {
        "operation_request_projection_id": "ledger_operation_request_v1",
        "ledger_schema_version": "experiment_trial_ledger_v1",
        "event_schema_version": "ledger_event_v1",
        "canonicalization_id": "pit_canonical_json_v1",
        "identity_projection_id": "ledger_event_identity_v1",
        "ledger_id": ledger_id,
        "event_id": event_id,
        "operation_id": operation_id,
        "event_type": event_type,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "occurred_at": occurred_at,
        "actor_id": actor_id,
        "payload": payload,
    }


def epoch_request(ids: PathAIds) -> dict[str, Any]:
    return request(
        event_type="LEDGER_EPOCH_CREATED",
        event_id=ids.epoch_event,
        operation_id=ids.epoch_op,
        subject_type="ledger",
        subject_id=ids.ledger,
        actor_id=ids.epoch_actor,
        ledger_id=ids.ledger,
        payload={"campaign_scope_ids": []},
    )


def campaign_request(ids: PathAIds) -> dict[str, Any]:
    return request(
        event_type="CAMPAIGN_ALLOCATED",
        event_id=ids.campaign_event,
        operation_id=ids.campaign_op,
        subject_type="campaign",
        subject_id=ids.campaign,
        actor_id=ids.campaign_actor,
        ledger_id=ids.ledger,
        payload={"campaign_scope_ids": [ids.campaign]},
    )


def experiment_request(ids: PathAIds) -> dict[str, Any]:
    return request(
        event_type="EXPERIMENT_ALLOCATED",
        event_id=ids.experiment_event,
        operation_id=ids.experiment_op,
        subject_type="experiment",
        subject_id=ids.experiment,
        actor_id=ids.experiment_actor,
        ledger_id=ids.ledger,
        payload={"campaign_scope_ids": [ids.campaign]},
    )


def family_request(ids: PathAIds, records: dict[str, CatalogRecord]) -> dict[str, Any]:
    definition = records["family_definition"]
    acceptance = records["family_acceptance"]
    return request(
        event_type="TRIAL_FAMILY_REGISTERED",
        event_id=ids.family_event,
        operation_id=ids.family_op,
        subject_type="trial_family",
        subject_id=ids.family,
        actor_id=ids.family_actor,
        ledger_id=ids.ledger,
        payload={
            "campaign_scope_ids": [ids.campaign],
            "family_acceptance_decision_id": acceptance.record_id,
            "family_acceptance_generation": 1,
            "family_acceptance_record_sha256": acceptance.sha256,
            "family_acceptance_schema_version": "trial_family_definition_acceptance_v1",
            "family_authority_id": "family-authority-1",
            "family_authority_registry_sha256": AUTHORITY_REGISTRY,
            "family_authority_version": 1,
            "family_definition_canonicalization_id": "pit_canonical_json_v1",
            "family_definition_record_id": definition.record_id,
            "family_definition_record_sha256": definition.sha256,
            "family_definition_record_version": 1,
            "family_definition_schema_version": "trial_family_definition_v1",
        },
    )


def sample_request(ids: PathAIds, records: dict[str, CatalogRecord]) -> dict[str, Any]:
    record = records["sample_record"]
    acceptance = records["sample_acceptance"]
    projection = records["sample_projection"]
    approval = records["sample_publication_approval"]
    return request(
        event_type="SAMPLE_REGISTERED",
        event_id=ids.sample_event,
        operation_id=ids.sample_op,
        subject_type="sample",
        subject_id=ids.sample,
        actor_id=ids.sample_actor,
        ledger_id=ids.ledger,
        payload={
            "campaign_scope_ids": [ids.campaign],
            "sample_acceptance_decision_id": acceptance.record_id,
            "sample_acceptance_generation": 1,
            "sample_acceptance_record_sha256": acceptance.sha256,
            "sample_acceptance_schema_version": "stage3_sample_acceptance_v1",
            "sample_authority_id": "sample-authority-1",
            "sample_authority_registry_sha256": AUTHORITY_REGISTRY,
            "sample_authority_version": 1,
            "sample_public_projection_id": projection.record_id,
            "sample_public_projection_schema_version": "public_redacted_projection_v1",
            "sample_public_projection_sha256": projection.sha256,
            "sample_publication_approval_generation": 1,
            "sample_publication_approval_id": approval.record_id,
            "sample_publication_approval_record_sha256": approval.sha256,
            "sample_publication_approval_schema_version": (
                "sample_public_projection_approval_v1"
            ),
            "sample_record_canonicalization_id": "pit_canonical_json_v1",
            "sample_record_id": record.record_id,
            "sample_record_schema_version": "stage3_sample_record_v1",
            "sample_record_sha256": record.sha256,
            "sample_record_version": 1,
        },
    )


def bind_sample_source(
    records: dict[str, CatalogRecord], sample_event_sha256: str
) -> None:
    for binding in records["trial_definition"].body["sample_bindings"]:
        binding["source_event_sha256"] = sample_event_sha256
    records["trial_definition"].sha256 = digest_json(records["trial_definition"].body)


def trial_request(ids: PathAIds, records: dict[str, CatalogRecord]) -> dict[str, Any]:
    definition = records["trial_definition"]
    acceptance = records["trial_acceptance"]
    projection = records["trial_projection"]
    approval = records["trial_publication_approval"]
    authority = records["trial_allocation_authority"]
    return request(
        event_type="TRIAL_ALLOCATED",
        event_id=ids.trial_event,
        operation_id=ids.trial_op,
        subject_type="trial",
        subject_id=ids.trial,
        actor_id=ids.trial_actor,
        ledger_id=ids.ledger,
        payload={
            "allocation_authority_generation": 1,
            "allocation_authority_id": authority.record_id,
            "allocation_authority_record_sha256": authority.sha256,
            "allocation_authority_schema_version": "trial_allocation_authority_v1",
            "campaign_allocation_event_id": ids.campaign_event,
            "campaign_allocation_event_sha256": "pending-campaign-event",
            "campaign_scope_ids": [ids.campaign],
            "code_identity": definition.body["code_identity"],
            "experiment_allocation_event_id": ids.experiment_event,
            "experiment_allocation_event_sha256": "pending-experiment-event",
            "experiment_id": ids.experiment,
            "initial_disposition": "PLANNED",
            "relation": {"relation_kind": "original"},
            "trial_definition_acceptance_decision_id": acceptance.record_id,
            "trial_definition_acceptance_generation": 1,
            "trial_definition_acceptance_record_sha256": acceptance.sha256,
            "trial_definition_acceptance_schema_version": (
                "trial_definition_acceptance_v1"
            ),
            "trial_definition_authority_id": "trial-definition-authority-1",
            "trial_definition_authority_registry_sha256": AUTHORITY_REGISTRY,
            "trial_definition_authority_version": 1,
            "trial_definition_public_projection_id": projection.record_id,
            "trial_definition_public_projection_schema_version": (
                "public_redacted_projection_v1"
            ),
            "trial_definition_public_projection_sha256": projection.sha256,
            "trial_definition_publication_approval_generation": 1,
            "trial_definition_publication_approval_id": approval.record_id,
            "trial_definition_publication_approval_record_sha256": approval.sha256,
            "trial_definition_publication_approval_schema_version": (
                "trial_definition_public_projection_approval_v1"
            ),
            "trial_definition_record_canonicalization_id": "pit_canonical_json_v1",
            "trial_definition_record_id": definition.record_id,
            "trial_definition_record_schema_version": "trial_definition_record_v1",
            "trial_definition_record_sha256": definition.sha256,
            "trial_definition_record_version": 1,
            "trial_family_id": ids.family,
            "trial_family_source_event_id": ids.family_event,
            "trial_family_source_event_sha256": "pending-family-event",
        },
    )


def bind_parent_digests(
    trial_req: dict[str, Any],
    *,
    campaign_sha256: str,
    experiment_sha256: str,
    family_sha256: str,
) -> None:
    trial_req["payload"]["campaign_allocation_event_sha256"] = campaign_sha256
    trial_req["payload"]["experiment_allocation_event_sha256"] = experiment_sha256
    trial_req["payload"]["trial_family_source_event_sha256"] = family_sha256


def bind_inventory_trial(
    records: dict[str, CatalogRecord], trial_event_sha256: str
) -> None:
    records["inventory_record"].body["trials"][0][
        "trial_allocation_event_sha256"
    ] = trial_event_sha256
    records["inventory_record"].sha256 = digest_json(records["inventory_record"].body)


def seal_request(
    ids: PathAIds,
    records: dict[str, CatalogRecord],
    *,
    predecessor_sequence: int,
    predecessor_sha256: str,
) -> dict[str, Any]:
    inventory = records["inventory_record"]
    acceptance = records["inventory_acceptance"]
    authority = records["seal_authority"]
    return request(
        event_type="CAMPAIGN_INVENTORY_SEALED",
        event_id=ids.seal_event,
        operation_id=ids.seal_op,
        subject_type="campaign",
        subject_id=ids.campaign,
        actor_id=ids.seal_actor,
        ledger_id=ids.ledger,
        payload={
            "campaign_allocation_event_id": ids.campaign_event,
            "campaign_allocation_event_sha256": "pending-campaign-event",
            "campaign_scope_ids": [ids.campaign],
            "inventory_acceptance_decision_id": acceptance.record_id,
            "inventory_acceptance_generation": 1,
            "inventory_acceptance_record_sha256": acceptance.sha256,
            "inventory_acceptance_schema_version": "campaign_inventory_acceptance_v1",
            "inventory_authority_id": "inventory-authority-1",
            "inventory_authority_registry_sha256": AUTHORITY_REGISTRY,
            "inventory_authority_version": 1,
            "inventory_record_canonicalization_id": "pit_canonical_json_v1",
            "inventory_record_id": inventory.record_id,
            "inventory_record_schema_version": "campaign_inventory_record_v1",
            "inventory_record_version": 1,
            "preseal_head": {
                "anchor_schema_version": "campaign_inventory_preseal_head_v1",
                "ledger_id": ids.ledger,
                "predecessor_event_sha256": predecessor_sha256,
                "predecessor_sequence": predecessor_sequence,
            },
            "seal_authority_generation": 1,
            "seal_authority_id": authority.record_id,
            "seal_authority_record_sha256": authority.sha256,
            "seal_authority_schema_version": "campaign_inventory_seal_authority_v1",
            "sealed_semantic_trial_count": 1,
            "sealed_trial_inventory_sha256": inventory.sha256,
        },
    )


def access_capability_record(ids: PathAIds, accessor: str) -> dict[str, Any]:
    return {
        "schema_version": "sample_access_capability_record_v1",
        "canonicalization_id": "pit_canonical_json_v1",
        "access_capability_id": ids.capability,
        "access_capability_record_version": 1,
        "ledger_id": ids.ledger,
        "sample_id": ids.sample,
        "campaign_id": ids.campaign,
        "intent_operation_id": ids.intent_op,
        "intent_event_id": ids.intent_event,
        "accessor_actor_id": accessor,
        "accessor_code_tree_sha256": CODE_TREE,
        "accessor_environment_id": ENVIRONMENT,
        "accessor_environment_lock_sha256": ENV_LOCK,
        "intended_window_id": WINDOW,
        "intended_field_class_ids": [FIELD_CLASS],
        "one_use": True,
    }


def intent_request(
    ids: PathAIds,
    records: dict[str, CatalogRecord],
    *,
    seal_event_id: str,
    seal_event_sha256: str,
    affected_trial_ids: list[str] | None = None,
    evidence_ref_ids: list[str] | None = None,
    accessor: str | None = None,
) -> dict[str, Any]:
    authorization = records["access_authorization"]
    intent_authority = records["intent_authority"]
    accessor = accessor or ids.accessor
    capability_sha256 = digest_json(access_capability_record(ids, accessor))
    return request(
        event_type="ACCESS_INTENT",
        event_id=ids.intent_event,
        operation_id=ids.intent_op,
        subject_type="sample",
        subject_id=ids.sample,
        actor_id=ids.intent_actor,
        ledger_id=ids.ledger,
        payload={
            "access_capability_id": ids.capability,
            "access_capability_record_canonicalization_id": "pit_canonical_json_v1",
            "access_capability_record_schema_version": (
                "sample_access_capability_record_v1"
            ),
            "access_capability_record_sha256": capability_sha256,
            "access_capability_record_version": 1,
            "accessor_code_tree_sha256": CODE_TREE,
            "accessor_environment_id": ENVIRONMENT,
            "accessor_environment_lock_sha256": ENV_LOCK,
            "affected_trial_ids": (
                [ids.trial] if affected_trial_ids is None else affected_trial_ids
            ),
            "authorization_record_id": authorization.record_id,
            "authorization_record_schema_version": "sample_access_authorization_v1",
            "authorization_record_sha256": authorization.sha256,
            "campaign_scope_ids": [ids.campaign],
            "evidence_ref_ids": (
                ["synthetic_intent_evidence_ref"]
                if evidence_ref_ids is None
                else evidence_ref_ids
            ),
            "intended_field_class_ids": [FIELD_CLASS],
            "intended_window_id": WINDOW,
            "intent_authority_generation": 1,
            "intent_authority_id": intent_authority.record_id,
            "intent_authority_record_sha256": intent_authority.sha256,
            "intent_authority_schema_version": "sample_access_intent_authority_v1",
            "inventory_seal_event_id": seal_event_id,
            "inventory_seal_event_sha256": seal_event_sha256,
            "purpose": "validation",
            "sample_id": ids.sample,
        },
    )


def bind_start_authority_intent(
    records: dict[str, CatalogRecord], intent_event_sha256: str
) -> None:
    records["start_authority"].body["access_intent_event_sha256"] = intent_event_sha256
    records["start_authority"].sha256 = digest_json(records["start_authority"].body)


def started_request(
    ids: PathAIds,
    records: dict[str, CatalogRecord],
    *,
    intent_event_sha256: str,
    evidence_ref_ids: list[str] | None = None,
) -> dict[str, Any]:
    authority = records["start_authority"]
    return request(
        event_type="ACCESS_STARTED",
        event_id=ids.started_event,
        operation_id=ids.started_op,
        subject_type="sample",
        subject_id=ids.sample,
        actor_id=ids.start_actor,
        ledger_id=ids.ledger,
        payload={
            "access_capability_id": ids.capability,
            "access_intent_event_id": ids.intent_event,
            "access_intent_event_sha256": intent_event_sha256,
            "campaign_scope_ids": [ids.campaign],
            "evidence_ref_ids": (
                ["synthetic_intent_evidence_ref", "synthetic_start_evidence_ref"]
                if evidence_ref_ids is None
                else evidence_ref_ids
            ),
            "reader_code_tree_sha256": CODE_TREE,
            "reader_environment_id": ENVIRONMENT,
            "reader_environment_lock_sha256": ENV_LOCK,
            "sample_id": ids.sample,
            "start_authority_generation": 1,
            "start_authority_id": authority.record_id,
            "start_authority_record_sha256": authority.sha256,
            "start_authority_schema_version": "sample_access_start_authority_v1",
        },
    )

"""Path A first-checkpoint runtime: synthetic catalogs, DIAGNOSTIC_ONLY."""

from __future__ import annotations

from pathlib import Path

import pytest

from ledger.runtime import (
    CatalogRecord,
    FixedClock,
    LedgerRuntimeError,
    LedgerStore,
    SELECTED_14,
    open_path_a_store,
)
from ledger.schema_registry import load_registry_release
from ledger_path_a_support import (
    STAMP,
    bind_inventory_trial,
    bind_parent_digests,
    bind_sample_source,
    bind_start_authority_intent,
    build_path_a_catalog,
    campaign_request,
    default_ids,
    epoch_request,
    experiment_request,
    family_request,
    intent_request,
    sample_request,
    seal_request,
    started_request,
    trial_request,
    typed_id,
)


PATH_A_TYPES = (
    "LEDGER_EPOCH_CREATED",
    "CAMPAIGN_ALLOCATED",
    "EXPERIMENT_ALLOCATED",
    "TRIAL_FAMILY_REGISTERED",
    "SAMPLE_REGISTERED",
    "TRIAL_ALLOCATED",
    "CAMPAIGN_INVENTORY_SEALED",
    "ACCESS_INTENT",
    "ACCESS_STARTED",
)
UNSELECTED = (
    "CAMPAIGN_AMENDMENT_PROPOSED",
    "CAMPAIGN_INVENTORY_AMENDED",
    "ATTEMPT_COMPLETED",
    "ATTEMPT_FAILED",
    "ATTEMPT_INVALID",
    "ATTEMPT_ABORTED",
    "TRIAL_COMPLETED",
    "TRIAL_FAILED",
    "TRIAL_INVALID",
    "TRIAL_ABORTED",
    "TRIAL_EXCLUDED",
    "ARTIFACT_DISPOSITION_RECORDED",
    "ACCESS_FAILED",
    "ACCESS_ABORTED",
    "ACCESS_CANCELLED",
    "EXPOSURE_DECISION",
    "CAMPAIGN_EVIDENCE_FROZEN",
    "CHECKPOINT_REFERENCE_RECORDED",
    "CAMPAIGN_ACCOUNTING_CLOSED",
    "REVIEW_DECIDED",
    "PROMOTION_DECIDED",
    "CAMPAIGN_ADJUDICATED",
    "EVENT_SUPERSEDED",
)


def _store(tmp_path: Path, catalog, **kwargs) -> LedgerStore:
    return open_path_a_store(
        tmp_path / "path-a.sqlite",
        catalog,
        clock=FixedClock(STAMP),
        **kwargs,
    )


def _assert_code(code: str, callback) -> None:
    with pytest.raises(LedgerRuntimeError) as raised:
        callback()
    assert raised.value.code == code


def _append_through_trial(store, ids, records):
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
    return {
        "epoch": epoch,
        "campaign": campaign,
        "experiment": experiment,
        "family": family,
        "sample": sample,
        "trial": trial,
    }


def _append_through_seal(store, ids, records):
    committed = _append_through_trial(store, ids, records)
    bind_inventory_trial(records, committed["trial"]["event_sha256"])
    seal_req = seal_request(
        ids,
        records,
        predecessor_sequence=committed["trial"]["sequence"],
        predecessor_sha256=committed["trial"]["event_sha256"],
    )
    seal_req["payload"]["campaign_allocation_event_sha256"] = committed["campaign"][
        "event_sha256"
    ]
    committed["seal"] = store.append(seal_req)
    return committed


def _append_path_a(store, ids, records):
    committed = _append_through_seal(store, ids, records)
    intent_req = intent_request(
        ids,
        records,
        seal_event_id=committed["seal"]["event_id"],
        seal_event_sha256=committed["seal"]["event_sha256"],
    )
    committed["intent"] = store.append(intent_req)
    bind_start_authority_intent(records, committed["intent"]["event_sha256"])
    committed["started"] = store.append(
        started_request(
            ids,
            records,
            intent_event_sha256=committed["intent"]["event_sha256"],
        )
    )
    return committed


def test_path_a_happy_path_stops_before_access_completed(tmp_path: Path) -> None:
    ids, catalog, records = build_path_a_catalog()
    store = _store(tmp_path, catalog)
    committed = _append_path_a(store, ids, records)
    types = [event["event_type"] for event in store.events()]
    assert types == list(PATH_A_TYPES)
    assert "ACCESS_COMPLETED" not in types
    assert "EXPOSURE_DECISION" not in types
    assert committed["started"]["event_type"] == "ACCESS_STARTED"
    capability = store.capability(ids.capability)
    assert capability is not None
    assert capability["consumed"] is True
    assert capability["accessor_actor_id"] == ids.accessor
    replayed = store.append(
        started_request(
            ids,
            records,
            intent_event_sha256=committed["intent"]["event_sha256"],
        )
    )
    assert replayed["event_id"] == committed["started"]["event_id"]
    assert replayed["sequence"] == committed["started"]["sequence"]
    assert len(store.events()) == 9


def test_unselected_wire_types_refuse_wire_type_not_selected(tmp_path: Path) -> None:
    ids, catalog, _records = build_path_a_catalog()
    store = _store(tmp_path, catalog)
    store.append(epoch_request(ids))
    vocabulary = load_registry_release("0.10.0")["closed_event_vocabulary"]
    assert len(UNSELECTED) == 23
    assert set(UNSELECTED) == set(vocabulary) - set(SELECTED_14)
    for event_type in UNSELECTED:
        req = epoch_request(ids)
        req["event_type"] = event_type
        req["event_id"] = typed_id("evt", 90)
        req["operation_id"] = typed_id("opn", 90)
        _assert_code("WIRE_TYPE_NOT_SELECTED", lambda req=req: store.append(req))
    assert [event["event_type"] for event in store.events()] == ["LEDGER_EPOCH_CREATED"]


def test_access_completed_and_path_b_events_are_excluded(tmp_path: Path) -> None:
    ids, catalog, _records = build_path_a_catalog()
    store = _store(tmp_path, catalog)
    store.append(epoch_request(ids))
    completed = epoch_request(ids)
    completed["event_type"] = "ACCESS_COMPLETED"
    completed["event_id"] = typed_id("evt", 91)
    completed["operation_id"] = typed_id("opn", 91)
    _assert_code(
        "PATH_A_STOPS_BEFORE_ACCESS_COMPLETED",
        lambda: store.append(completed),
    )
    for event_type in (
        "CAMPAIGN_ENTITY_BOUND",
        "STAGE3_SAMPLE_REFERENCE_BOUND",
        "ATTEMPT_ALLOCATED",
        "ATTEMPT_STARTED",
    ):
        req = epoch_request(ids)
        req["event_type"] = event_type
        req["event_id"] = typed_id("evt", 92)
        req["operation_id"] = typed_id("opn", 92)
        _assert_code("PATH_A_CHECKPOINT_EXCLUDES_EVENT", lambda req=req: store.append(req))


def test_database_path_inside_repository_is_refused(tmp_path: Path) -> None:
    ids, catalog, _records = build_path_a_catalog()
    repo = Path(__file__).resolve().parents[1]
    _assert_code(
        "LEDGER_DATABASE_PATH_IN_REPOSITORY",
        lambda: open_path_a_store(repo / "path-a.sqlite", catalog),
    )
    del ids
    del tmp_path


@pytest.mark.parametrize(
    "field",
    ["sequence", "recorded_at", "previous_event_sha256", "operation_request_sha256"],
)
def test_ingress_commit_fields_are_forbidden(tmp_path: Path, field: str) -> None:
    ids, catalog, _records = build_path_a_catalog()
    store = _store(tmp_path, catalog)
    req = epoch_request(ids)
    req[field] = 0 if field == "sequence" else STAMP
    _assert_code("OPERATION_REQUEST_COMMIT_FIELD_FORBIDDEN", lambda: store.append(req))
    assert store.events() == []


def test_sample_lineage_required(tmp_path: Path) -> None:
    ids, catalog, records = build_path_a_catalog(sample_lineage="")
    records["sample_record"].body.pop("canonical_sample_lineage_id")
    store = _store(tmp_path, catalog)
    store.append(epoch_request(ids))
    store.append(campaign_request(ids))
    store.append(experiment_request(ids))
    store.append(family_request(ids, records))
    _assert_code(
        "SAMPLE_REGISTERED_LINEAGE_REQUIRED",
        lambda: store.append(sample_request(ids, records)),
    )


def test_local_lineage_and_record_duplicates(tmp_path: Path) -> None:
    ids, catalog, records = build_path_a_catalog()
    store = _store(tmp_path, catalog)
    store.append(epoch_request(ids))
    store.append(campaign_request(ids))
    store.append(experiment_request(ids))
    store.append(family_request(ids, records))
    store.append(sample_request(ids, records))
    duplicate_id = sample_request(ids, records)
    duplicate_id["event_id"] = typed_id("evt", 70)
    duplicate_id["operation_id"] = typed_id("opn", 70)
    duplicate_id["subject_id"] = typed_id("smp", 70)
    records["sample_record"].body["sample_id"] = typed_id("smp", 70)
    _assert_code(
        "SAMPLE_REGISTERED_RECORD_DUP",
        lambda: store.append(duplicate_id),
    )
    records["sample_record"].body["sample_id"] = ids.sample
    other_tuple = sample_request(ids, records)
    other_tuple["event_id"] = typed_id("evt", 71)
    other_tuple["operation_id"] = typed_id("opn", 71)
    other_tuple["subject_id"] = typed_id("smp", 71)
    other_tuple["payload"]["sample_record_id"] = "sample-record-other"
    other_tuple["payload"]["sample_record_sha256"] = "77" * 32
    catalog.add(CatalogRecord(
        kind="sample_record",
        record_id="sample-record-other",
        schema_version="stage3_sample_record_v1",
        sha256="77" * 32,
        body={
            **records["sample_record"].body,
            "sample_id": typed_id("smp", 71),
            "canonical_sample_lineage_id": "synthetic-canonical-lineage",
        },
        version=1,
        authority_id="sample-authority-other",
        registry_sha256="88" * 32,
        authority_version=1,
    ))
    _assert_code(
        "SAMPLE_REGISTERED_LINEAGE_DUP",
        lambda: store.append(other_tuple),
    )


def test_trial_family_stale_and_private_producer(tmp_path: Path) -> None:
    ids, catalog, records = build_path_a_catalog(
        trial_producers=[default_ids().trial_reviewer]
    )
    store = _store(tmp_path, catalog)
    store.append(epoch_request(ids))
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
    _assert_code(
        "TRIAL_ALLOCATED_PRIVATE_INPUT_PRODUCER_ROLE_COLLISION",
        lambda: store.append(trial_req),
    )

    ids3, catalog3, records3 = build_path_a_catalog()
    store3 = _store(tmp_path / "stale-family", catalog3)
    store3.append(epoch_request(ids3))
    campaign3 = store3.append(campaign_request(ids3))
    experiment3 = store3.append(experiment_request(ids3))
    family3 = store3.append(family_request(ids3, records3))
    sample3 = store3.append(sample_request(ids3, records3))
    bind_sample_source(records3, sample3["event_sha256"])
    records3["family_acceptance"].valid_until = STAMP
    trial_req3 = trial_request(ids3, records3)
    bind_parent_digests(
        trial_req3,
        campaign_sha256=campaign3["event_sha256"],
        experiment_sha256=experiment3["event_sha256"],
        family_sha256=family3["event_sha256"],
    )
    _assert_code("TRIAL_ALLOCATED_ACCEPTANCE_STALE", lambda: store3.append(trial_req3))


def test_trial_publication_approval_stale_and_content_scope(tmp_path: Path) -> None:
    ids, catalog, records = build_path_a_catalog()
    store = _store(tmp_path, catalog)
    store.append(epoch_request(ids))
    campaign = store.append(campaign_request(ids))
    experiment = store.append(experiment_request(ids))
    family = store.append(family_request(ids, records))
    sample = store.append(sample_request(ids, records))
    bind_sample_source(records, sample["event_sha256"])
    records["sample_publication_approval"].valid_until = STAMP
    trial_req = trial_request(ids, records)
    bind_parent_digests(
        trial_req,
        campaign_sha256=campaign["event_sha256"],
        experiment_sha256=experiment["event_sha256"],
        family_sha256=family["event_sha256"],
    )
    _assert_code(
        "TRIAL_ALLOCATED_PUBLICATION_APPROVAL_STALE",
        lambda: store.append(trial_req),
    )

    ids2, catalog2, records2 = build_path_a_catalog(
        definition_campaign_scope=[typed_id("cmp", 99)]
    )
    store2 = _store(tmp_path / "scope", catalog2)
    store2.append(epoch_request(ids2))
    campaign2 = store2.append(campaign_request(ids2))
    experiment2 = store2.append(experiment_request(ids2))
    family2 = store2.append(family_request(ids2, records2))
    sample2 = store2.append(sample_request(ids2, records2))
    bind_sample_source(records2, sample2["event_sha256"])
    trial_req2 = trial_request(ids2, records2)
    bind_parent_digests(
        trial_req2,
        campaign_sha256=campaign2["event_sha256"],
        experiment_sha256=experiment2["event_sha256"],
        family_sha256=family2["event_sha256"],
    )
    _assert_code("RECORD_CONTENT_MISMATCH", lambda: store2.append(trial_req2))


def test_seal_role_collisions_and_parent_staleness(tmp_path: Path) -> None:
    cases = [
        (
            {"inventory_reviewer": default_ids().inventory_issuer},
            "CAMPAIGN_INVENTORY_SEALED_ROLE_COLLISION",
        ),
        (
            {"inventory_reviewer": default_ids().seal_actor},
            "CAMPAIGN_INVENTORY_SEALED_ROLE_COLLISION",
        ),
        (
            {"inventory_reviewer": default_ids().seal_authority_issuer},
            "CAMPAIGN_INVENTORY_SEALED_ROLE_COLLISION",
        ),
        (
            {"inventory_reviewer": default_ids().trial_issuer},
            "CAMPAIGN_INVENTORY_SEALED_ROLE_COLLISION",
        ),
        (
            {"inventory_issuer": default_ids().seal_actor},
            "CAMPAIGN_INVENTORY_SEALED_ROLE_COLLISION",
        ),
        (
            {"seal_authorized_actor": default_ids().trial_actor},
            "CAMPAIGN_INVENTORY_SEALED_AUTHORITY_ACTOR_MISMATCH",
        ),
        (
            {"inventory_producers": [default_ids().inventory_reviewer]},
            "CAMPAIGN_INVENTORY_SEALED_PRIVATE_INPUT_PRODUCER_ROLE_COLLISION",
        ),
    ]
    for kwargs, code in cases:
        ids, catalog, records = build_path_a_catalog(**kwargs)
        store = _store(tmp_path / code / str(kwargs), catalog)
        committed = _append_through_trial(store, ids, records)
        bind_inventory_trial(records, committed["trial"]["event_sha256"])
        seal_req = seal_request(
            ids,
            records,
            predecessor_sequence=committed["trial"]["sequence"],
            predecessor_sha256=committed["trial"]["event_sha256"],
        )
        seal_req["payload"]["campaign_allocation_event_sha256"] = committed["campaign"][
            "event_sha256"
        ]
        _assert_code(code, lambda seal_req=seal_req, store=store: store.append(seal_req))

    for stale_key, _label in (
        ("family_acceptance", "fam"),
        ("sample_acceptance", "samp"),
        ("trial_acceptance", "def"),
    ):
        ids, catalog, records = build_path_a_catalog()
        store = _store(tmp_path / f"stale-{stale_key}", catalog)
        committed = _append_through_trial(store, ids, records)
        bind_inventory_trial(records, committed["trial"]["event_sha256"])
        records[stale_key].valid_until = STAMP
        seal_req = seal_request(
            ids,
            records,
            predecessor_sequence=committed["trial"]["sequence"],
            predecessor_sha256=committed["trial"]["event_sha256"],
        )
        seal_req["payload"]["campaign_allocation_event_sha256"] = committed["campaign"][
            "event_sha256"
        ]
        _assert_code(
            "CAMPAIGN_INVENTORY_SEALED_ACCEPTANCE_STALE",
            lambda seal_req=seal_req, store=store: store.append(seal_req),
        )


def test_access_intent_empty_trials_evidence_seal_and_stale(tmp_path: Path) -> None:
    ids, catalog, records = build_path_a_catalog()
    store = _store(tmp_path, catalog)
    committed = _append_through_seal(store, ids, records)
    empty_trials = intent_request(
        ids,
        records,
        seal_event_id=committed["seal"]["event_id"],
        seal_event_sha256=committed["seal"]["event_sha256"],
        affected_trial_ids=[],
    )
    _assert_code(
        "ACCESS_INTENT_AFFECTED_TRIAL_SET_EMPTY",
        lambda: store.append(empty_trials),
    )
    empty_refs = intent_request(
        ids,
        records,
        seal_event_id=committed["seal"]["event_id"],
        seal_event_sha256=committed["seal"]["event_sha256"],
        evidence_ref_ids=[],
    )
    _assert_code(
        "ACCESS_INTENT_EVIDENCE_REF_SET_EMPTY",
        lambda: store.append(empty_refs),
    )
    stale_seal = intent_request(
        ids,
        records,
        seal_event_id=committed["seal"]["event_id"],
        seal_event_sha256="99" * 32,
    )
    _assert_code("ACCESS_INTENT_SEAL_NOT_CURRENT", lambda: store.append(stale_seal))

    records["family_acceptance"].valid_until = STAMP
    stale_family = intent_request(
        ids,
        records,
        seal_event_id=committed["seal"]["event_id"],
        seal_event_sha256=committed["seal"]["event_sha256"],
    )
    _assert_code("ACCESS_INTENT_ACCEPTANCE_STALE", lambda: store.append(stale_family))
    records["family_acceptance"].valid_until = None
    records["sample_publication_approval"].valid_until = STAMP
    stale_pub = intent_request(
        ids,
        records,
        seal_event_id=committed["seal"]["event_id"],
        seal_event_sha256=committed["seal"]["event_sha256"],
    )
    _assert_code(
        "ACCESS_INTENT_PUBLICATION_APPROVAL_STALE",
        lambda: store.append(stale_pub),
    )
    assert [event["event_type"] for event in store.events()][-1] == (
        "CAMPAIGN_INVENTORY_SEALED"
    )


def test_access_intent_role_collisions(tmp_path: Path) -> None:
    ids = default_ids()
    variants = [
        ("authorization_issuer", ids.intent_authority_issuer),
        ("authorization_issuer", ids.accessor),
        ("authorization_issuer", ids.inventory_issuer),
        ("authorization_issuer", ids.seal_actor),
        ("intent_authority_issuer", ids.accessor),
        ("intent_authority_issuer", ids.inventory_issuer),
        ("intent_authority_issuer", ids.seal_actor),
        ("accessor", ids.inventory_issuer),
        ("accessor", ids.seal_actor),
        ("inventory_issuer", ids.seal_actor),
    ]
    for index, (field, value) in enumerate(variants):
        kwargs = {field: value}
        catalog_ids, catalog, records = build_path_a_catalog(**kwargs)
        store = _store(tmp_path / f"role-{index}", catalog)
        if field == "inventory_issuer":
            committed = _append_through_trial(store, catalog_ids, records)
            bind_inventory_trial(records, committed["trial"]["event_sha256"])
            seal_req = seal_request(
                catalog_ids,
                records,
                predecessor_sequence=committed["trial"]["sequence"],
                predecessor_sha256=committed["trial"]["event_sha256"],
            )
            seal_req["payload"]["campaign_allocation_event_sha256"] = committed[
                "campaign"
            ]["event_sha256"]
            _assert_code(
                "CAMPAIGN_INVENTORY_SEALED_ROLE_COLLISION",
                lambda seal_req=seal_req, store=store: store.append(seal_req),
            )
            continue
        committed = _append_through_seal(store, catalog_ids, records)
        if field == "accessor":
            records["access_authorization"].body["accessor_actor_id"] = value
        intent_req = intent_request(
            catalog_ids,
            records,
            seal_event_id=committed["seal"]["event_id"],
            seal_event_sha256=committed["seal"]["event_sha256"],
            accessor=records["access_authorization"].body["accessor_actor_id"],
        )
        _assert_code(
            "ACCESS_INTENT_ROLE_COLLISION",
            lambda intent_req=intent_req, store=store: store.append(intent_req),
        )


def test_access_started_empty_evidence_stale_family_and_atomic_rollback(
    tmp_path: Path,
) -> None:
    ids, catalog, records = build_path_a_catalog()
    store = _store(tmp_path, catalog)
    committed = _append_through_seal(store, ids, records)
    intent = store.append(
        intent_request(
            ids,
            records,
            seal_event_id=committed["seal"]["event_id"],
            seal_event_sha256=committed["seal"]["event_sha256"],
        )
    )
    bind_start_authority_intent(records, intent["event_sha256"])
    empty_refs = started_request(
        ids,
        records,
        intent_event_sha256=intent["event_sha256"],
        evidence_ref_ids=[],
    )
    _assert_code(
        "ACCESS_STARTED_EVIDENCE_REF_SET_EMPTY",
        lambda: store.append(empty_refs),
    )
    assert store.capability(ids.capability)["consumed"] is False

    records["family_acceptance"].valid_until = STAMP
    stale = started_request(ids, records, intent_event_sha256=intent["event_sha256"])
    _assert_code("ACCESS_STARTED_ACCEPTANCE_STALE", lambda: store.append(stale))
    records["family_acceptance"].valid_until = None
    assert store.capability(ids.capability)["consumed"] is False

    injected = _store(
        tmp_path / "inject",
        catalog,
        inject_access_started_failure=True,
    )
    # Reuse the same catalog against a fresh database; rebuild Path A.
    ids2, catalog2, records2 = build_path_a_catalog()
    injected = _store(
        tmp_path / "inject2",
        catalog2,
        inject_access_started_failure=True,
    )
    committed2 = _append_through_seal(injected, ids2, records2)
    intent2 = injected.append(
        intent_request(
            ids2,
            records2,
            seal_event_id=committed2["seal"]["event_id"],
            seal_event_sha256=committed2["seal"]["event_sha256"],
        )
    )
    bind_start_authority_intent(records2, intent2["event_sha256"])
    start_req = started_request(
        ids2, records2, intent_event_sha256=intent2["event_sha256"]
    )
    _assert_code("INJECTED_APPEND_REFUSAL", lambda: injected.append(start_req))
    assert injected.capability(ids2.capability)["consumed"] is False
    assert [event["event_type"] for event in injected.events()][-1] == "ACCESS_INTENT"


def test_path_a_does_not_claim_terminal_access_or_profitability() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    runtime = (
        Path(__file__).resolve().parents[1] / "src/ledger/runtime.py"
    ).read_text(encoding="utf-8")
    assert "DIAGNOSTIC_ONLY" in runtime
    assert "profit" not in runtime.lower()
    assert "ACCESS_COMPLETED" in source
    assert "stop" in source.lower() or "PATH_A_STOPS_BEFORE_ACCESS_COMPLETED" in source

"""Path B first-checkpoint runtime: synthetic catalogs, DIAGNOSTIC_ONLY."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from ledger.runtime import (
    FixedClock,
    LedgerRuntimeError,
    LedgerStore,
    SELECTED_14,
    digest_json,
    open_path_b_store,
)
from ledger.schema_registry import load_registry_release
from ledger_path_a_support import CODE_TREE, ENV_LOCK, ENVIRONMENT, STAMP, epoch_request, typed_id
from ledger_path_b_support import (
    append_through_seal,
    attempt_request,
    bind_readiness_after_allocation,
    bind_readiness_after_seal,
    build_path_b_catalog,
    default_path_b_ids,
    refresh_plan_and_authority,
    refresh_readiness,
    started_request,
)


PATH_B_TYPES = (
    "LEDGER_EPOCH_CREATED",
    "CAMPAIGN_ALLOCATED",
    "EXPERIMENT_ALLOCATED",
    "TRIAL_FAMILY_REGISTERED",
    "SAMPLE_REGISTERED",
    "TRIAL_ALLOCATED",
    "CAMPAIGN_INVENTORY_SEALED",
    "ATTEMPT_ALLOCATED",
    "ATTEMPT_STARTED",
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


def _store(tmp_path: Path, catalog) -> LedgerStore:
    return open_path_b_store(
        tmp_path / "path-b.sqlite",
        catalog,
        clock=FixedClock(STAMP),
    )


def _assert_code(code: str, callback) -> None:
    with pytest.raises(LedgerRuntimeError) as raised:
        callback()
    assert raised.value.code == code


def _append_path_b(store, ids, records):
    committed = append_through_seal(store, ids.a, records)
    refresh_plan_and_authority(records)
    bind_readiness_after_seal(records, committed)
    attempt_req = attempt_request(ids, records)
    attempt_req["payload"]["campaign_inventory_seal_event_sha256"] = committed["seal"][
        "event_sha256"
    ]
    attempt_req["payload"]["trial_allocation_event_sha256"] = committed["trial"][
        "event_sha256"
    ]
    committed["attempt"] = store.append(attempt_req)
    bind_readiness_after_allocation(records, committed)
    committed["started"] = store.append(
        started_request(ids, records, committed["attempt"])
    )
    return committed


def test_path_b_happy_path_stops_before_terminal_attempt(tmp_path: Path) -> None:
    ids, catalog, records = build_path_b_catalog()
    store = _store(tmp_path, catalog)
    committed = _append_path_b(store, ids, records)
    types = [event["event_type"] for event in store.events()]
    assert types == list(PATH_B_TYPES)
    assert "ACCESS_COMPLETED" not in types
    assert "EXPOSURE_DECISION" not in types
    assert "ATTEMPT_COMPLETED" not in types
    assert committed["started"]["event_type"] == "ATTEMPT_STARTED"
    capability = store.capability(ids.execute_capability)
    assert capability is not None
    assert capability["consumed"] is False
    assert capability["executor_actor_id"] == ids.executor
    consumed = store.consume_execute(
        capability_id=ids.execute_capability,
        consumer_actor_id=ids.executor,
        trial_id=ids.a.trial,
        attempt_id=ids.attempt,
        code_tree_sha256=CODE_TREE,
        environment_id=ENVIRONMENT,
        environment_lock_sha256=ENV_LOCK,
    )
    assert consumed["consumed"] is True
    replayed = store.append(started_request(ids, records, committed["attempt"]))
    assert replayed["event_id"] == committed["started"]["event_id"]
    assert replayed["sequence"] == committed["started"]["sequence"]
    assert replayed["event_sha256"] == committed["started"]["event_sha256"]
    assert len(store.events()) == 9


def test_unselected_wire_types_refuse_wire_type_not_selected(tmp_path: Path) -> None:
    ids, catalog, _records = build_path_b_catalog()
    store = _store(tmp_path, catalog)
    store.append(epoch_request(ids.a))
    vocabulary = load_registry_release("0.10.0")["closed_event_vocabulary"]
    assert len(UNSELECTED) == 23
    assert set(UNSELECTED) == set(vocabulary) - set(SELECTED_14)
    for event_type in UNSELECTED:
        req = epoch_request(ids.a)
        req["event_type"] = event_type
        req["event_id"] = typed_id("evt", 90)
        req["operation_id"] = typed_id("opn", 90)
        _assert_code("WIRE_TYPE_NOT_SELECTED", lambda req=req: store.append(req))
    assert [event["event_type"] for event in store.events()] == ["LEDGER_EPOCH_CREATED"]


def test_path_b_excludes_access_completed_bindings_and_stage3(tmp_path: Path) -> None:
    ids, catalog, _records = build_path_b_catalog()
    store = _store(tmp_path, catalog)
    store.append(epoch_request(ids.a))
    completed = epoch_request(ids.a)
    completed["event_type"] = "ACCESS_COMPLETED"
    completed["event_id"] = typed_id("evt", 91)
    completed["operation_id"] = typed_id("opn", 91)
    _assert_code(
        "PATH_B_CHECKPOINT_EXCLUDES_EVENT",
        lambda: store.append(completed),
    )
    for event_type in ("CAMPAIGN_ENTITY_BOUND", "STAGE3_SAMPLE_REFERENCE_BOUND"):
        req = epoch_request(ids.a)
        req["event_type"] = event_type
        req["event_id"] = typed_id("evt", 92)
        req["operation_id"] = typed_id("opn", 92)
        _assert_code(
            "PATH_B_CHECKPOINT_EXCLUDES_EVENT",
            lambda req=req: store.append(req),
        )


def test_database_path_inside_repository_is_refused(tmp_path: Path) -> None:
    _ids, catalog, _records = build_path_b_catalog()
    repo = Path(__file__).resolve().parents[1]
    _assert_code(
        "LEDGER_DATABASE_PATH_IN_REPOSITORY",
        lambda: open_path_b_store(repo / "path-b.sqlite", catalog),
    )
    del tmp_path


def test_retry_relation_is_refused(tmp_path: Path) -> None:
    ids, catalog, records = build_path_b_catalog()
    store = _store(tmp_path, catalog)
    committed = append_through_seal(store, ids.a, records)
    refresh_plan_and_authority(records)
    bind_readiness_after_seal(records, committed)
    req = attempt_request(ids, records)
    req["payload"]["campaign_inventory_seal_event_sha256"] = committed["seal"][
        "event_sha256"
    ]
    req["payload"]["trial_allocation_event_sha256"] = committed["trial"]["event_sha256"]
    req["payload"]["relation"] = {
        "attempt_kind": "retry",
        "attempt_ordinal": 2,
        "prior_attempt_id": typed_id("att", 9),
        "prior_terminal_event_id": typed_id("evt", 99),
        "prior_terminal_event_sha256": "99" * 32,
    }
    _assert_code("ATTEMPT_ALLOCATED_RETRY_NOT_SELECTED", lambda: store.append(req))
    assert [event["event_type"] for event in store.events()][-1] == (
        "CAMPAIGN_INVENTORY_SEALED"
    )


def test_family_stale_seal_not_current_and_trial_not_in_seal(tmp_path: Path) -> None:
    ids, catalog, records = build_path_b_catalog()
    store = _store(tmp_path, catalog)
    committed = append_through_seal(store, ids.a, records)
    refresh_plan_and_authority(records)
    bind_readiness_after_seal(records, committed)
    records["family_acceptance"].valid_until = STAMP
    req = attempt_request(ids, records)
    req["payload"]["campaign_inventory_seal_event_sha256"] = committed["seal"][
        "event_sha256"
    ]
    req["payload"]["trial_allocation_event_sha256"] = committed["trial"]["event_sha256"]
    _assert_code("ATTEMPT_ALLOCATED_ACCEPTANCE_STALE", lambda: store.append(req))
    records["family_acceptance"].valid_until = None

    stale_seal = attempt_request(ids, records)
    stale_seal["payload"]["campaign_inventory_seal_event_id"] = committed["seal"][
        "event_id"
    ]
    stale_seal["payload"]["campaign_inventory_seal_event_sha256"] = "99" * 32
    stale_seal["payload"]["trial_allocation_event_sha256"] = committed["trial"][
        "event_sha256"
    ]
    _assert_code("ATTEMPT_ALLOCATED_SEAL_NOT_CURRENT", lambda: store.append(stale_seal))

    missing = attempt_request(ids, records)
    missing["payload"]["campaign_inventory_seal_event_sha256"] = committed["seal"][
        "event_sha256"
    ]
    missing["payload"]["trial_allocation_event_sha256"] = committed["trial"][
        "event_sha256"
    ]
    missing["payload"]["trial_id"] = typed_id("trl", 99)
    _assert_code("ATTEMPT_ALLOCATED_TRIAL_NOT_IN_SEAL", lambda: store.append(missing))


def test_plan_reviewer_private_producer_collision(tmp_path: Path) -> None:
    ids = default_path_b_ids()
    _ids, catalog, records = build_path_b_catalog(
        ids, plan_producers=[ids.plan_reviewer]
    )
    store = _store(tmp_path, catalog)
    committed = append_through_seal(store, ids.a, records)
    refresh_plan_and_authority(records)
    bind_readiness_after_seal(records, committed)
    req = attempt_request(ids, records)
    req["payload"]["campaign_inventory_seal_event_sha256"] = committed["seal"][
        "event_sha256"
    ]
    req["payload"]["trial_allocation_event_sha256"] = committed["trial"]["event_sha256"]
    _assert_code(
        "ATTEMPT_ALLOCATED_PRIVATE_INPUT_PRODUCER_ROLE_COLLISION",
        lambda: store.append(req),
    )


def _through_allocation(tmp_path: Path, **catalog_kwargs):
    ids, catalog, records = build_path_b_catalog(**catalog_kwargs)
    store = _store(tmp_path, catalog)
    committed = append_through_seal(store, ids.a, records)
    refresh_plan_and_authority(records)
    bind_readiness_after_seal(records, committed)
    req = attempt_request(ids, records)
    req["payload"]["campaign_inventory_seal_event_sha256"] = committed["seal"][
        "event_sha256"
    ]
    req["payload"]["trial_allocation_event_sha256"] = committed["trial"]["event_sha256"]
    committed["attempt"] = store.append(req)
    bind_readiness_after_allocation(records, committed)
    return ids, catalog, records, store, committed


def _mutate_readiness(records, mutator) -> None:
    mutator(records["attempt_readiness"].body)
    refresh_readiness(records)


@pytest.mark.parametrize(
    "mutator",
    [
        lambda body: body["inventory_catalog_key"].__setitem__(
            "inventory_record_id", "other-inventory"
        ),
        lambda body: body["family_definition_and_acceptance"][0]["definition"].__setitem__(
            "family_definition_record_id", "other-family"
        ),
        lambda body: body["family_definition_and_acceptance"][0]["acceptance"].__setitem__(
            "family_acceptance_decision_id", "other-family-acceptance"
        ),
        lambda body: body["sample_record_acceptance_projection_publication_approval"][0][
            "record"
        ].__setitem__("sample_record_id", "other-sample"),
        lambda body: body["sample_record_acceptance_projection_publication_approval"][0][
            "acceptance"
        ].__setitem__("sample_acceptance_decision_id", "other-sample-acceptance"),
        lambda body: body["sample_record_acceptance_projection_publication_approval"][0][
            "projection"
        ].__setitem__("sample_public_projection_id", "other-projection"),
        lambda body: body[
            "trial_definition_acceptance_projection_allocation_authority"
        ]["definition"].__setitem__("trial_definition_record_id", "other-definition"),
        lambda body: body["inventory_acceptance"].__setitem__(
            "inventory_acceptance_decision_id", "other-inventory-acceptance"
        ),
        lambda body: body[
            "trial_definition_acceptance_projection_allocation_authority"
        ]["acceptance"].__setitem__(
            "trial_definition_acceptance_decision_id", "other-trial-acceptance"
        ),
        lambda body: body["sample_record_acceptance_projection_publication_approval"][0][
            "publication_approval"
        ].__setitem__("sample_publication_approval_id", "other-pub"),
        lambda body: body["attempt_allocation_authority"].__setitem__(
            "allocation_authority_id", "other-attempt-authority"
        ),
        lambda body: body["attempt_plan_catalog_key"].__setitem__(
            "attempt_plan_record_id", "other-plan"
        ),
        lambda body: body["attempt_plan_acceptance"].__setitem__(
            "attempt_plan_acceptance_decision_id", "other-plan-acceptance"
        ),
        lambda body: body["seal_event_id_sha256"].__setitem__("event_sha256", "99" * 32),
        lambda body: body["attempt_allocation_event"].__setitem__(
            "event_sha256", "99" * 32
        ),
        lambda body: body[
            "trial_definition_acceptance_projection_allocation_authority"
        ]["allocation_authority"].__setitem__(
            "allocation_authority_id", "other-trial-authority"
        ),
        lambda body: body[
            "trial_definition_acceptance_projection_allocation_authority"
        ]["projection"].__setitem__(
            "trial_definition_public_projection_id", "other-trial-projection"
        ),
        lambda body: body[
            "trial_definition_acceptance_projection_allocation_authority"
        ]["publication_approval"].__setitem__(
            "trial_definition_publication_approval_id", "other-trial-approval"
        ),
    ],
)
def test_readiness_tuple_mismatches(tmp_path: Path, mutator) -> None:
    ids, _catalog, records, store, committed = _through_allocation(tmp_path)
    _mutate_readiness(records, mutator)
    _assert_code(
        "ATTEMPT_STARTED_INHERITED_TUPLE_MISMATCH",
        lambda: store.append(started_request(ids, records, committed["attempt"])),
    )
    assert store.capability(ids.execute_capability) is None
    assert [event["event_type"] for event in store.events()][-1] == "ATTEMPT_ALLOCATED"


@pytest.mark.parametrize(
    "index",
    range(5),
)
def test_readiness_retained_source_hash_mismatches(tmp_path: Path, index: int) -> None:
    ids, _catalog, records, store, committed = _through_allocation(tmp_path)

    def mutator(body, index=index):
        body["retained_source_event_id_hash"][index]["source"]["event_sha256"] = (
            "99" * 32
        )

    _mutate_readiness(records, mutator)
    _assert_code(
        "ATTEMPT_STARTED_INHERITED_TUPLE_MISMATCH",
        lambda: store.append(started_request(ids, records, committed["attempt"])),
    )


def test_readiness_campaign_binding_source_mismatch(tmp_path: Path) -> None:
    ids, _catalog, records, store, committed = _through_allocation(tmp_path)

    def mutator(body):
        body["retained_source_event_id_hash"].append(
            {
                "subject_type": "sample",
                "subject_id": typed_id("smp", 9),
                "event_type": "CAMPAIGN_ENTITY_BOUND",
                "source": {
                    "event_id": typed_id("evt", 88),
                    "event_sha256": "99" * 32,
                },
            }
        )

    _mutate_readiness(records, mutator)
    _assert_code(
        "ATTEMPT_STARTED_INHERITED_TUPLE_MISMATCH",
        lambda: store.append(started_request(ids, records, committed["attempt"])),
    )


def test_readiness_sample_and_family_set_mismatches(tmp_path: Path) -> None:
    ids, _catalog, records, store, committed = _through_allocation(tmp_path)
    original_samples = deepcopy(
        records["attempt_readiness"].body[
            "sample_record_acceptance_projection_publication_approval"
        ]
    )
    original_families = deepcopy(
        records["attempt_readiness"].body["family_definition_and_acceptance"]
    )

    def missing_sample(body):
        body["sample_record_acceptance_projection_publication_approval"] = []

    _mutate_readiness(records, missing_sample)
    _assert_code(
        "ATTEMPT_STARTED_INHERITED_TUPLE_MISMATCH",
        lambda: store.append(started_request(ids, records, committed["attempt"])),
    )
    records["attempt_readiness"].body[
        "sample_record_acceptance_projection_publication_approval"
    ] = deepcopy(original_samples)

    def extra_sample(body):
        extra = deepcopy(body["sample_record_acceptance_projection_publication_approval"][0])
        extra["sample_id"] = typed_id("smp", 9)
        body["sample_record_acceptance_projection_publication_approval"].append(extra)

    _mutate_readiness(records, extra_sample)
    _assert_code(
        "ATTEMPT_STARTED_INHERITED_TUPLE_MISMATCH",
        lambda: store.append(started_request(ids, records, committed["attempt"])),
    )
    records["attempt_readiness"].body[
        "sample_record_acceptance_projection_publication_approval"
    ] = deepcopy(original_samples)

    def missing_family(body):
        body["family_definition_and_acceptance"] = []

    _mutate_readiness(records, missing_family)
    _assert_code(
        "ATTEMPT_STARTED_INHERITED_TUPLE_MISMATCH",
        lambda: store.append(started_request(ids, records, committed["attempt"])),
    )
    records["attempt_readiness"].body["family_definition_and_acceptance"] = deepcopy(
        original_families
    )

    def extra_family(body):
        extra = deepcopy(body["family_definition_and_acceptance"][0])
        extra["trial_family_id"] = typed_id("fam", 9)
        body["family_definition_and_acceptance"].append(extra)

    _mutate_readiness(records, extra_family)
    _assert_code(
        "ATTEMPT_STARTED_INHERITED_TUPLE_MISMATCH",
        lambda: store.append(started_request(ids, records, committed["attempt"])),
    )


def test_plan_start_authority_allocation_authority_and_readiness_currentness(
    tmp_path: Path,
) -> None:
    ids, _catalog, records, store, committed = _through_allocation(tmp_path)
    records["attempt_plan_acceptance"].valid_until = STAMP
    _assert_code(
        "ATTEMPT_STARTED_ACCEPTANCE_STALE",
        lambda: store.append(started_request(ids, records, committed["attempt"])),
    )
    records["attempt_plan_acceptance"].valid_until = None

    records["attempt_start_authority"].valid_until = STAMP
    _assert_code(
        "ATTEMPT_STARTED_START_AUTHORITY_STALE",
        lambda: store.append(started_request(ids, records, committed["attempt"])),
    )
    records["attempt_start_authority"].valid_until = None

    records["attempt_allocation_authority"].valid_until = STAMP
    _assert_code(
        "ATTEMPT_STARTED_ALLOCATION_AUTHORITY_STALE",
        lambda: store.append(started_request(ids, records, committed["attempt"])),
    )
    records["attempt_allocation_authority"].valid_until = None

    records["attempt_readiness"].valid_until = STAMP
    _assert_code(
        "ATTEMPT_STARTED_READINESS_NOT_CURRENT",
        lambda: store.append(started_request(ids, records, committed["attempt"])),
    )
    records["attempt_readiness"].valid_until = None
    records["attempt_readiness"].status = "superseded"
    _assert_code(
        "ATTEMPT_STARTED_READINESS_NOT_CURRENT",
        lambda: store.append(started_request(ids, records, committed["attempt"])),
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("code_identity", {"code_commit_id": "othercommit12", "code_identity_kind": "clean_commit", "code_repository_id": "equity-factor-research", "code_tree_sha256": CODE_TREE}),
        ("environment_id", "other-environment"),
        ("input_manifest_sha256", "99" * 32),
        ("retry_policy_sha256", "99" * 32),
        ("expected_output_inventory_sha256", "99" * 32),
    ],
)
def test_inherited_operational_value_mismatch(
    tmp_path: Path, field: str, value: object
) -> None:
    ids, _catalog, records, store, committed = _through_allocation(
        tmp_path / str(field)
    )

    def mutator(body, field=field, value=value):
        body[field] = value

    _mutate_readiness(records, mutator)
    _assert_code(
        "ATTEMPT_STARTED_INHERITED_VALUE_MISMATCH",
        lambda: store.append(started_request(ids, records, committed["attempt"])),
    )


def test_start_authority_executor_mismatch(tmp_path: Path) -> None:
    ids, _catalog, records, store, committed = _through_allocation(tmp_path)
    records["attempt_start_authority"].body["executor_actor_id"] = ids.attempt_start_actor
    records["attempt_start_authority"].sha256 = digest_json(
        records["attempt_start_authority"].body
    )
    _assert_code(
        "ATTEMPT_STARTED_EXECUTOR_MISMATCH",
        lambda: store.append(started_request(ids, records, committed["attempt"])),
    )


def test_execute_consume_rejects_start_actor(tmp_path: Path) -> None:
    ids, catalog, records = build_path_b_catalog()
    store = _store(tmp_path, catalog)
    _append_path_b(store, ids, records)
    _assert_code(
        "CAPABILITY_CONSUMER_MISMATCH",
        lambda: store.consume_execute(
            capability_id=ids.execute_capability,
            consumer_actor_id=ids.attempt_start_actor,
            trial_id=ids.a.trial,
            attempt_id=ids.attempt,
            code_tree_sha256=CODE_TREE,
            environment_id=ENVIRONMENT,
            environment_lock_sha256=ENV_LOCK,
        ),
    )
    assert store.capability(ids.execute_capability)["consumed"] is False


def test_path_b_does_not_claim_access_completed_or_profitability() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    runtime = (
        Path(__file__).resolve().parents[1] / "src/ledger/runtime.py"
    ).read_text(encoding="utf-8")
    assert "DIAGNOSTIC_ONLY" in runtime
    assert "profit" not in runtime.lower()
    assert "ACCESS_COMPLETED" in source
    assert "EXPOSURE_DECISION" in source
    assert "PATH_B_CHECKPOINT_EXCLUDES_EVENT" in source

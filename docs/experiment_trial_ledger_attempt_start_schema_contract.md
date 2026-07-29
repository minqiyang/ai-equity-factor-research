# Experiment and Trial Ledger Attempt Start R1I Contract

Contract ID: `experiment_trial_ledger_attempt_start_schema_r1i`.

Contract version: `0.9.0`.

Owner decision: option `R1I-A`.

This document is the design authority for the bounded Stage 4B-R1I attempt
start release under:

- `docs/research_program_charter.md`;
- `docs/point_in_time_data_methodology_contract.md`;
- `docs/experiment_trial_ledger_contract.md`;
- `docs/experiment_trial_ledger_schema_registry_contract.md`;
- `docs/experiment_trial_ledger_allocation_registration_schema_contract.md`;
- `docs/experiment_trial_ledger_trial_family_registration_schema_contract.md`;
- `docs/experiment_trial_ledger_sample_registration_schema_contract.md`;
- `docs/experiment_trial_ledger_binding_schema_contract.md`;
- `docs/experiment_trial_ledger_trial_allocation_schema_contract.md`;
- `docs/experiment_trial_ledger_campaign_inventory_seal_schema_contract.md`;
  and
- `docs/experiment_trial_ledger_attempt_allocation_schema_contract.md`.

Its publication state is determined by protected-main history and
`docs/current_handoff.md`, not by a status claim inside this document.

## Release Boundary

R1I publishes one new immutable registry release:

- registry schema ID
  `experiment_trial_ledger_payload_schema_registry_v9`;
- registry version `0.9.0`;
- unchanged schema-language ID `ledger_closed_schema_dsl_v1`;
- unchanged schema-language version `0.2.0`; and
- a separate packaged JSON artifact and SHA-256 sidecar.

R1I preserves the accepted 37-event vocabulary. Its supported event set is
exactly:

```text
LEDGER_EPOCH_CREATED
CAMPAIGN_ALLOCATED
EXPERIMENT_ALLOCATED
TRIAL_FAMILY_REGISTERED
SAMPLE_REGISTERED
CAMPAIGN_ENTITY_BOUND
STAGE3_SAMPLE_REFERENCE_BOUND
TRIAL_ALLOCATED
CAMPAIGN_INVENTORY_SEALED
ATTEMPT_ALLOCATED
ATTEMPT_STARTED
```

The other 26 events remain
`SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`. R1I does not overwrite, reinterpret, or
silently upgrade immutable registry releases `0.1.0` through `0.8.0`, their
digests, the default R0 entry point, or prior validator outcomes.

Registry acceptance proves only the closed local shape and literal syntax of a
candidate event. It does not prove that an allocation exists, that external
records are retrievable, that retained bytes match their digests, that roles
are independent, that authorities are current, that an attempt is eligible to
start, that an append or capability mint is atomic or durable, that a
capability is unexpired or consumed exactly once, or that an executor ran.

## Exact Attempt-Start Boundary

`ATTEMPT_STARTED` is the durable immediate pre-execution transition for one
already allocated attempt. It has:

- `event_type` exactly `ATTEMPT_STARTED`;
- `subject_type` exactly `attempt`;
- `subject_id` exactly the earlier allocated
  `att_<32 lowercase hexadecimal digits>` attempt identity;
- one-item sorted-unique `payload.campaign_scope_ids`;
- one exact earlier `ATTEMPT_ALLOCATED` event ID and hash;
- the exact allocated semantic-trial ID;
- one complete external readiness-record tuple;
- one separate current start-actor authority tuple; and
- one ledger-owned `cap_<32 lowercase hexadecimal digits>` one-shot execution
  capability and complete external capability-record tuple.

Attempt identity is represented only by the subject. The payload does not
duplicate it. Trial identity is included because it is an exact cross-check
against the earlier allocation, not another subject.

Validation runs after durable attempt allocation but before start and produces
the readiness evidence pinned below. A failed validation must not emit
`ATTEMPT_STARTED`; it remains an allocated attempt pending an exact accepted
terminal disposition. The start event itself is a pre-execution barrier. At
the instant its append commits, no executor instruction, artifact write,
result production, or protected-sample read has been authorized by this
schema. Execution may begin only after the durable append and one successful
atomic consumption of the exact capability minted with it. `occurred_at`
records the requested start transition time; it does not assert a
first-instruction or completion time.

The event payload contains exactly:

```text
attempt_allocation_event_id
attempt_allocation_event_sha256
campaign_scope_ids
execution_capability_id
execution_capability_record_canonicalization_id
execution_capability_record_schema_version
execution_capability_record_sha256
execution_capability_record_version
readiness_authority_id
readiness_authority_registry_sha256
readiness_authority_version
readiness_record_canonicalization_id
readiness_record_id
readiness_record_schema_version
readiness_record_sha256
readiness_record_version
start_authority_generation
start_authority_id
start_authority_record_sha256
start_authority_schema_version
trial_id
```

Missing, null, unknown, duplicate, wrong-type, unsafe, or additional fields
fail closed. Campaign identity is represented only by the singleton scope.
Private redemption material is never a payload field.

## Complete Canonical Readiness Record

The complete `attempt_start_readiness_record_v1` is repository-external and
private by default. The start event pins it using:

| Field | Exact local schema |
| --- | --- |
| `readiness_authority_id` | `safe_public_id` |
| `readiness_authority_registry_sha256` | lowercase SHA-256 |
| `readiness_authority_version` | I-JSON safe integer, minimum 1 |
| `readiness_record_canonicalization_id` | literal `pit_canonical_json_v1` |
| `readiness_record_id` | `safe_public_id` |
| `readiness_record_schema_version` | literal `attempt_start_readiness_record_v1` |
| `readiness_record_sha256` | lowercase SHA-256 |
| `readiness_record_version` | I-JSON safe integer, minimum 1 |

The authority is an immutable versioned catalog. Retrieval uses the exact
tuple:

```text
(readiness_authority_id,
 readiness_authority_registry_sha256,
 readiness_authority_version,
 readiness_record_id,
 readiness_record_schema_version,
 readiness_record_version,
 readiness_record_canonicalization_id,
 readiness_record_sha256)
```

A catalog miss, record miss, version mismatch, changed bytes, digest mismatch,
unknown schema, stale record, superseded record, or ambiguous result fails
closed. A hash-only placeholder is not a complete readiness record.

The exact complete record binds:

- the ledger, campaign, trial, attempt, and exact earlier attempt-allocation
  event tuple;
- the complete current accepted attempt-plan, trial-definition, inventory,
  family, sample, code, environment, input, retry-policy, and expected-output
  tuples inherited from the allocation;
- a literal readiness outcome of `READY`;
- every deterministic preflight and validation check, its closed check ID,
  validator version, disposition, evidence digest, and failure policy;
- the exact validator, executor, code/tree, environment, lock, interpreter,
  platform, locale, timezone, dependency, and input identities;
- proof that every required source and external authority is retrievable,
  digest-matching, accepted, current, and unrevoked immediately before start;
- proof that the trial and attempt remain open and that no start or terminal
  event already exists for this attempt;
- proof that the campaign inventory chain and attempt allocation remain
  current and that no closure or supersession invalidates them;
- activation and expiry times, currentness generation, explicit supersession,
  and every identity-bearing default; and
- closed versioned nested records and finite ordered or sorted-unique
  collections.

Any non-`READY`, incomplete, stale, changed, ambiguous, failed, or expired
record rejects the start. Validation failure is represented later by an exact
accepted terminal event schema; it does not get relabeled as a start.

## Readiness Role Independence

The complete readiness record identifies both its issuer and one independent
reviewer. The reviewer must be distinct from:

- the readiness-record issuer;
- the executor named by the record;
- the earlier attempt-allocation actor;
- the attempt-plan issuer and attempt-plan acceptance reviewer;
- the trial-definition issuer and acceptance reviewer; and
- any actor whose private input supplies an identity-bearing readiness value.

The readiness issuer must also be distinct from the executor and the earlier
attempt-allocation actor. Identity aliases, delegated accounts with the same
effective principal, reruns, new record versions, new campaigns, and
post-result reclassification do not satisfy independence. These are mandatory
stateful authority checks. The local event carries the pinned record tuple and
does not duplicate private role identities.

## Start Actor Authority

One separate immutable start-authority record is pinned by:

| Field | Exact local schema |
| --- | --- |
| `start_authority_generation` | I-JSON safe integer, minimum 1 |
| `start_authority_id` | `safe_public_id` |
| `start_authority_record_sha256` | lowercase SHA-256 |
| `start_authority_schema_version` | literal `attempt_start_authority_v1` |

The repository-external authority record binds the exact envelope `actor_id`,
ledger, campaign, trial, attempt, allocation tuple, readiness tuple, executor,
allowed start operation, activation interval, generation, issuer, and
revocation/supersession state. It must be current immediately before append.
The envelope `actor_id` remains claimed attribution; the separately retrievable
tuple is the authority evidence. Local schema acceptance neither authenticates
the actor nor grants permission.

## Ledger-Owned One-Shot Execution Capability

The exact capability namespace is:

```text
cap_<32 lowercase hexadecimal digits>
```

The start append atomically mints one new ledger-owned capability identity and
one complete private `attempt_execution_capability_record_v1`. The event pins
that record using:

| Field | Exact local schema |
| --- | --- |
| `execution_capability_id` | `cap_<32 lowercase hexadecimal digits>` |
| `execution_capability_record_canonicalization_id` | literal `pit_canonical_json_v1` |
| `execution_capability_record_schema_version` | literal `attempt_execution_capability_record_v1` |
| `execution_capability_record_sha256` | lowercase SHA-256 |
| `execution_capability_record_version` | I-JSON safe integer, minimum 1 |

The complete external capability record binds the capability, ledger,
campaign, trial, attempt, exact start operation, exact allocation/readiness/
start-authority tuples, intended executor, activation/expiry interval, one-use
policy, and initial `CREATED` state. Private redemption secret, credential,
handle, proof, and transport material remain outside the public ledger event
and outside this repository.

The append and capability-record creation are one atomic transaction. If
either fails, neither is visible. After durable commit, the exact intended
executor may perform one atomic compare-and-set consumption from `CREATED` to
`CONSUMED`. Only that successful consumer may begin execution. Expired,
revoked, already consumed, wrong-executor, wrong-attempt, wrong-readiness, or
wrong-authority redemption fails closed and does not start work.

Exact lost-ack replay of the same `operation_id` and exact operation-request
hash returns the existing start event and the same capability identity; it
does not append again or mint another capability. A changed request,
concurrent different operation, or second consumption conflicts. Secret
delivery, storage, recovery, and transport require a later private runtime
architecture and are not defined by this public schema.

## Stateful Ordering, Currentness, And Anti-Reset Rules

Before append, stateful validation must prove:

- the exact allocation event exists earlier and matches ledger, attempt,
  trial, campaign, plan, relation, and current inventory;
- the attempt is `ALLOCATED`, has no earlier start, has no terminal event, and
  belongs to an open, nonterminal trial and campaign;
- every referenced authority and canonical record is exact, retrievable,
  accepted, current, active, unexpired, and unrevoked;
- readiness outcome is exactly `READY`, all required checks passed, and all
  current plan/executor/environment/input identities still match;
- role-independence constraints hold under effective-principal identity;
- the start actor is authorized for this exact operation immediately before
  append;
- the capability identity and external record have never existed and can be
  created atomically with the event;
- the append durably commits before capability consumption; and
- capability consumption succeeds exactly once before any executor,
  artifact writer, result producer, or protected accessor is invoked.

Exactly one start is permitted per attempt. Allocation retry uses a new attempt
identity under the frozen R1H relation; it never restarts the same attempt. A
new operation ID, alias, clone, rerun, campaign, plan version, readiness
generation, authority generation, capability, post-result reclassification,
or process restart never resets start count, capability consumption,
multiplicity, exposure, or outcome history.

A stale, revoked, expired, superseded, already-started, terminal, closed,
wrong-scope, wrong-source, role-colliding, non-atomic, or non-durable candidate
fails closed. These stateful checks are outside schema-language `0.2.0`.
Shape-valid events are not evidence that any of them occurred.

## Required Killing Evidence

R1I must include independent evidence for:

- byte-exact R0 through R7 artifacts, digests, behavior, and package resources;
- explicit packaged registry `0.9.0` selection and unchanged default R0;
- exact eleven-event supported and 26-event incomplete partitions;
- one independent positive start fixture not generated from the registry;
- exact attempt subject, `att_` namespace, and singleton campaign scope;
- exact earlier allocation event, trial, readiness, start-authority, and
  capability tuples;
- every missing, unknown, duplicate, null, and wrong-type envelope and payload
  field;
- wrong attempt/trial/campaign/event/capability namespaces, digest length/case,
  unsafe public IDs, versions, generations, canonicalization, authority, and
  schema literals;
- private redemption fields and redundant attempt identity rejected;
- shape-valid missing/stale/wrong allocation, non-`READY` or changed readiness,
  role collision, stale/revoked authority, duplicate start, terminal/closed
  state, duplicate capability, non-atomic mint, lost-ack replay mismatch,
  double/concurrent/wrong-executor consumption, and action-before-durable
  append documented as statefully fail closed rather than local `ACCEPT`
  evidence;
- every nonpromoted and unknown event rejected before action; and
- arbitrary self-consistent unpublished promotion rejected by packaged digest
  authority.

Literal tests must not discover expected fields, namespaces, authority names,
supported events, or outcome codes from the implementation under test.
Synthetic fixture IDs and digest strings prove syntax only; they are not
ledger appends, capabilities, attempts, artifacts, protected accesses, or
research results.

## Privacy And Publication Boundary

The complete readiness, start-authority, capability, plan, acceptance, input,
environment, and private identity records; paths; commands; credentials;
queries; restricted sample facts; expected private outputs; raw values; and
performance/result content remain repository-external.

The canonical event carries only typed IDs, safe-public reference IDs, exact
schema/version literals, and synthetic or separately controlled SHA-256
references. A digest is not public merely because it is non-reversible.
Private redemption secret/material is prohibited from the event. A later
public projection must omit every unapproved field/value/digest and requires
its own immutable approval authority. R1I neither creates nor approves such a
projection.

## Non-Goals

R1I does not:

- append, store, retrieve, allocate, validate, start, execute, consume,
  authorize, authenticate, accept, approve, retry, access, review, close, or
  promote anything;
- implement readiness, authority, capability, plan, acceptance, inventory,
  state, idempotency, transaction, recovery, or executor services;
- select a backend, private ledger path, secret store, transaction/recovery
  policy, signature mechanism, provider, dataset, strategy, factor, or
  statistical method;
- promote amendment, terminal-attempt, trial-disposition, artifact, access,
  exposure, closure, review, decision, adjudication, or supersession events;
- copy private records, secrets, credentials, paths, raw values, performance
  values, or outcomes into the repository;
- run a campaign, trial, attempt, capability, protected access, factor,
  backtest, report, or historical interpretation; or
- add paper, brokerage, order, live, or real-money behavior.

Actual allocated-attempt count, started-attempt count, capability count,
execution count, artifact production, and protected-sample access remain zero.

## Next Gate

After R1I is accepted on protected main, perform a read-only dependency/risk
analysis over the remaining 26 incomplete events. Prefer the smallest strict
successor whose exact terminal evidence and artifact boundary can be frozen
without inventing private result fields. Keep `ACCESS_INTENT` as a separate
higher-risk protected-access capability root and the campaign amendment pair
as an optional inventory branch. Surface only a genuine owner-methodology
choice under the bounded reminder policy.

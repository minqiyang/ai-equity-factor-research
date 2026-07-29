# Experiment and Trial Ledger Attempt Allocation R1H Contract

Contract ID: `experiment_trial_ledger_attempt_allocation_schema_r1h`.

Contract version: `0.8.0`.

Owner decision: option `R1H-A`.

This document is the design authority for the bounded Stage 4B-R1H attempt
allocation release under:

- `docs/research_program_charter.md`;
- `docs/point_in_time_data_methodology_contract.md`;
- `docs/experiment_trial_ledger_contract.md`;
- `docs/experiment_trial_ledger_schema_registry_contract.md`;
- `docs/experiment_trial_ledger_allocation_registration_schema_contract.md`;
- `docs/experiment_trial_ledger_trial_family_registration_schema_contract.md`;
- `docs/experiment_trial_ledger_sample_registration_schema_contract.md`;
- `docs/experiment_trial_ledger_binding_schema_contract.md`;
- `docs/experiment_trial_ledger_trial_allocation_schema_contract.md`; and
- `docs/experiment_trial_ledger_campaign_inventory_seal_schema_contract.md`.

Its publication state is determined by protected-main history and
`docs/current_handoff.md`, not by a status claim inside this document.

## Release Boundary

R1H publishes one new immutable registry release:

- registry schema ID
  `experiment_trial_ledger_payload_schema_registry_v8`;
- registry version `0.8.0`;
- unchanged schema-language ID `ledger_closed_schema_dsl_v1`;
- unchanged schema-language version `0.2.0`; and
- a separate packaged JSON artifact and SHA-256 sidecar.

R1H preserves the accepted 37-event vocabulary. Its supported event set is
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
```

The other 27 events remain
`SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`. R1H does not overwrite, reinterpret, or
silently upgrade immutable registry releases `0.1.0` through `0.7.0`, their
digests, the default R0 entry point, or prior validator outcomes.

Registry acceptance proves only the closed local shape and literal syntax of a
candidate event. It does not prove that a trial or inventory seal exists, that
an external attempt plan is retrievable, that retained source bytes match a
digest, that reviewers are independent, that authority/currentness is valid,
that a trial remains open, that an attempt identity or ordinal is unique, that
a retry predecessor is terminal, that a retry is permitted, that an append is
atomic or durable, or that a validator, executor, artifact writer, or protected
accessor ran.

## Exact Attempt Identity And Event Boundary

The exact attempt namespace is:

```text
att_<32 lowercase hexadecimal digits>
```

`ATTEMPT_ALLOCATED` allocates exactly one invocation of one already allocated
semantic trial. It has:

- `event_type` exactly `ATTEMPT_ALLOCATED`;
- `subject_type` exactly `attempt`;
- `subject_id` exactly one newly allocated `attempt_id`;
- one-item sorted-unique `payload.campaign_scope_ids`;
- one exact earlier `TRIAL_ALLOCATED` event ID and hash;
- one exact earlier initial `CAMPAIGN_INVENTORY_SEALED` event ID and hash;
- one complete external attempt-plan record tuple;
- one separate attempt-plan acceptance tuple;
- one separate allocation-actor authority tuple;
- one expected-output inventory SHA-256; and
- one closed first-attempt or retry relation.

The attempt ID is not duplicated in the payload. Exact replay of the same
append operation is idempotency and does not allocate another attempt. Every
operational retry uses a new attempt ID under the same open trial. A rerun
after terminal trial closure is a new semantic trial under the separately
accepted trial relation; it is not an attempt retry.

`ATTEMPT_ALLOCATED` is allocation only. It does not validate inputs, start an
attempt, execute code, open protected content, write artifacts, expose results,
or grant a reusable execution/access capability. `ATTEMPT_STARTED` remains the
separate immediate pre-execution boundary and remains incomplete in R1H.

The event payload contains exactly:

```text
allocation_authority_generation
allocation_authority_id
allocation_authority_record_sha256
allocation_authority_schema_version
attempt_plan_acceptance_decision_id
attempt_plan_acceptance_generation
attempt_plan_acceptance_record_sha256
attempt_plan_acceptance_schema_version
attempt_plan_authority_id
attempt_plan_authority_registry_sha256
attempt_plan_authority_version
attempt_plan_record_canonicalization_id
attempt_plan_record_id
attempt_plan_record_schema_version
attempt_plan_record_sha256
attempt_plan_record_version
campaign_inventory_seal_event_id
campaign_inventory_seal_event_sha256
campaign_scope_ids
expected_output_inventory_sha256
relation
trial_allocation_event_id
trial_allocation_event_sha256
trial_id
```

Missing, null, unknown, duplicate, wrong-type, unsafe, or additional fields
fail closed. Campaign identity is represented only by the singleton scope and
the complete external record; attempt identity is represented only by the
subject.

## Complete Canonical Attempt Plan

The complete `attempt_plan_record_v1` is repository-external and private by
default. The allocation event pins it using:

| Field | Exact local schema |
| --- | --- |
| `attempt_plan_authority_id` | `safe_public_id` |
| `attempt_plan_authority_registry_sha256` | lowercase SHA-256 |
| `attempt_plan_authority_version` | I-JSON safe integer, minimum 1 |
| `attempt_plan_record_canonicalization_id` | literal `pit_canonical_json_v1` |
| `attempt_plan_record_id` | `safe_public_id` |
| `attempt_plan_record_schema_version` | literal `attempt_plan_record_v1` |
| `attempt_plan_record_sha256` | lowercase SHA-256 |
| `attempt_plan_record_version` | I-JSON safe integer, minimum 1 |
| `expected_output_inventory_sha256` | lowercase SHA-256 |

The authority is an immutable versioned catalog. Retrieval uses the exact
tuple:

```text
(attempt_plan_authority_id,
 attempt_plan_authority_registry_sha256,
 attempt_plan_authority_version,
 attempt_plan_record_id,
 attempt_plan_record_schema_version,
 attempt_plan_record_version,
 attempt_plan_record_canonicalization_id,
 attempt_plan_record_sha256)
```

A catalog miss, record miss, version mismatch, changed bytes, digest mismatch,
unknown schema, stale generation, or ambiguous result fails closed. A hash-only
placeholder is not a complete attempt plan.

The exact `attempt_plan_record_v1` complete record binds:

- the ledger, campaign, semantic trial, and newly allocated attempt identity;
- the exact earlier trial-allocation event ID/hash and accepted trial-definition
  authority/catalog/record/acceptance tuple;
- the exact initial campaign-inventory-seal event ID/hash and, when applicable,
  the complete exact accepted amendment chain;
- the closed attempt branch, ordinal, and exact prior terminal attempt event
  tuple for a retry;
- the frozen retry policy, retry budget, allowed predecessor terminal states,
  and typed retry reason;
- validator and executor identities, exact code/tree identity, environment,
  lock hash, interpreter/platform, locale, timezone, and dependency versions;
- immutable data/input identities and the exact sample/access classifications
  inherited from the accepted trial definition;
- the ordered all-and-only expected-output inventory, roles, media/classes,
  canonicalization policy, and required/optional disposition policy;
- the exact canonical bytes whose SHA-256 is
  `expected_output_inventory_sha256`;
- the activation time, currentness/supersession facts, and every
  identity-bearing default; and
- closed versioned nested records and finite ordered or sorted-unique
  collections.

The complete record must equal the already accepted semantic trial definition
where the trial froze code, data, environment, sample, execution, cost,
artifact-role, and retry-policy facts. An attempt plan may narrow an allowed
operational choice only when the frozen policy explicitly permits it. It must
not change the semantic configuration or silently introduce another trial.

R1H does not freeze the later artifact-disposition event schema or a public
artifact projection. The complete private plan predeclares the output
inventory, while the local event schema validates only its exact SHA-256. Any
artifact identity or disposition that depends on a still-incomplete event
remains unusable until that later authority is accepted. Synthetic fixture
digests are syntax evidence only and are not public approval for a real
private digest.

## Attempt Plan Acceptance And Role Independence

One separate immutable acceptance record is pinned by:

| Field | Exact local schema |
| --- | --- |
| `attempt_plan_acceptance_decision_id` | `safe_public_id` |
| `attempt_plan_acceptance_generation` | I-JSON safe integer, minimum 1 |
| `attempt_plan_acceptance_record_sha256` | lowercase SHA-256 |
| `attempt_plan_acceptance_schema_version` | literal `attempt_plan_acceptance_v1` |

The acceptance record binds the exact plan authority/catalog/record tuple,
attempt subject, trial and seal source tuples, singleton campaign scope,
relation, ordinal, retry policy/budget, code/environment, and expected-output
inventory digest. Its reviewer must be distinct from:

- the attempt-plan record issuer;
- the accepted trial-definition issuer;
- the attempt allocation actor; and
- any actor whose private input record supplies an identity-bearing value to
  the plan or acceptance decision.

Acceptance generations are strictly monotonic and exactly one generation is
current. Supersession is explicit and retains every prior byte. Retrieval miss,
ambiguity, changed canonical bytes, digest mismatch, stale acceptance,
self-review, wrong scope, wrong source tuple, or role collision fails closed.

## Allocation Actor Authority

One separate attempt-allocation authority record is pinned by:

| Field | Exact local schema |
| --- | --- |
| `allocation_authority_id` | `safe_public_id` |
| `allocation_authority_generation` | I-JSON safe integer, minimum 1 |
| `allocation_authority_record_sha256` | lowercase SHA-256 |
| `allocation_authority_schema_version` | literal `attempt_allocation_authority_v1` |

The repository-external authority record binds the exact `actor_id`, ledger,
campaign, trial, attempt-plan tuple, allowed allocation operation, activation
interval, generation, issuer, and revocation/supersession state. It must be
active immediately before append. The envelope `actor_id` remains claimed
attribution; the separately retrievable tuple is the authority evidence.
Local schema acceptance neither authenticates the actor nor grants permission.

## Exact First-Attempt And Retry Union

`payload.relation` is a closed `tagged_union` discriminated by
`attempt_kind`.

The `first_attempt` branch has all-and-only:

```text
attempt_kind = first_attempt
attempt_ordinal = 1
```

The `retry` branch has all-and-only:

```text
attempt_kind = retry
attempt_ordinal
prior_attempt_id
prior_terminal_event_id
prior_terminal_event_sha256
```

For a retry, `attempt_ordinal` is a non-Boolean I-JSON-safe integer with a
local minimum of 2. `prior_attempt_id` uses the exact
`att_<32 lowercase hexadecimal digits>` namespace. The prior event ID and
SHA-256 bind one exact earlier current terminal attempt event.

Stateful validation reconstructs every attempt for the trial. The first branch
is legal only when no attempt has previously been allocated. A retry ordinal
must equal the exact prior count plus one, the predecessor must belong to the
same trial and campaign, and its current terminal state and reason must be
allowed by the frozen trial retry policy. The accepted plan and trial budget
determine the finite maximum; R1H does not invent a global retry allowance or
silently raise the frozen budget.

Missing predecessors, nonterminal predecessors, later references, wrong-trial
references, duplicate/skipped ordinals, changed reason, concurrent siblings,
policy/budget excess, or reuse of an attempt ID fails closed. A new alias,
clone, rerun, campaign, plan version, post-result reclassification, or
acceptance generation never resets attempt count, retry budget, multiplicity,
sample exposure, or prior outcome history.

The unchanged schema language can close and discriminate the union and enforce
ordinal minima. It cannot query prior ledger state, compare ordinals, verify
terminality, or enforce the external retry budget. Those remain mandatory
stateful checks rather than local `ACCEPT` evidence.

## Stateful Ordering And Pre-Action Barrier

Before append, stateful validation must prove:

- the attempt ID has never been allocated;
- the trial allocation exists earlier, matches the exact trial ID/campaign,
  remains `PLANNED`, and has no terminal trial disposition;
- the exact initial inventory seal exists earlier, remains current, contains
  the trial through the accepted inventory or amendment path, and still binds
  the retained pre-seal head;
- every applicable amendment event has an accepted exact schema and completes
  before an added trial's attempt allocation;
- the complete plan, acceptance, allocation authority, trial definition,
  family/sample paths, code bytes, environment, and retry policy are exact and
  current;
- the relation and ordinal reconstruct the exact retained attempt history;
- no identity-bearing value was defaulted, omitted, inferred, aliased, or
  changed; and
- the allocation append durably commits before any validator, executor,
  artifact writer, protected accessor, or result-producing process is invoked.

If any source, authority, acceptance, currentness, role-independence, budget,
ordering, append, or durability check fails, no downstream process is invoked.
Exact lost-ack replay returns the existing allocation without another event or
attempt identity. A changed request conflicts.

R1H does not implement those stateful ledger or external-authority checks.
Because the amendment pair and every attempt lifecycle event remain incomplete,
an amended-inventory attempt, attempt start, terminal attempt, retry execution,
artifact disposition, trial closure, or protected access remains fail closed
despite a locally valid `ATTEMPT_ALLOCATED` shape.

## Required Killing Evidence

R1H must include independent evidence for:

- byte-exact R0 through R6 artifacts, digests, behavior, and package resources;
- explicit packaged registry `0.8.0` selection and unchanged default R0;
- exact ten-event supported and 27-event incomplete partitions;
- one independent first-attempt and one independent retry positive fixture;
- exact attempt subject, `att_` namespace, and singleton campaign scope;
- every missing, unknown, duplicate, null, and wrong-type envelope, payload,
  and nested relation field;
- wrong attempt/trial/campaign/event namespaces, digest lengths/case, unsafe
  public IDs, versions, generations, canonicalization, authority, acceptance,
  schema literals, branch tags, and ordinal values;
- first-attempt ordinal 1 and retry ordinal minimum 2 enforced locally;
- cross-branch fields and unknown relation variants rejected;
- shape-valid duplicate IDs, stale source/plan/acceptance/authority, wrong
  campaign/trial/seal, nonterminal or cross-trial predecessor, ordinal skip,
  concurrent retry, retry-budget excess, post-terminal allocation,
  self-review, role collision, and action-before-durable-append documented as
  statefully fail closed rather than local `ACCEPT` evidence;
- every nonpromoted and unknown event rejected before action; and
- arbitrary self-consistent unpublished promotion rejected by packaged digest
  authority.

The independent fixture must not be generated from the registry artifact.
Literal tests must not discover expected fields, namespaces, authority names,
supported events, branches, or outcome codes from the implementation under
test. Synthetic fixture IDs and digest strings prove syntax only; they are not
private plans, ledger appends, attempts, artifacts, or research results.

## Privacy And Publication Boundary

The complete attempt plan, authority records, acceptance record, private
paths, commands, credentials, queries, input identities, restricted sample
facts, expected private outputs, raw values, and performance/result content
remain repository-external.

The canonical event carries only typed IDs, safe-public reference IDs, exact
schema/version literals, and synthetic or separately controlled SHA-256
references. A digest is not public merely because it is non-reversible. A
later public projection must omit every unapproved field/value/digest and
requires its own immutable approval authority. R1H neither creates nor approves
such a projection.

## Non-Goals

R1H does not:

- append, store, retrieve, allocate, authorize, authenticate, accept, approve,
  validate, start, execute, retry, access, review, close, or promote anything;
- implement attempt-plan, acceptance, authority, inventory, or retry-policy
  catalogs;
- select a backend, private ledger path, transaction/recovery policy,
  signature mechanism, provider, dataset, strategy, factor, or statistical
  method;
- promote amendment, attempt-start, terminal-attempt, trial-disposition,
  artifact, access, exposure, closure, review, decision, adjudication, or
  supersession events;
- copy private records, paths, raw values, performance values, or outcomes into
  the repository;
- run a campaign, trial, attempt, protected access, factor, backtest, report,
  or historical interpretation; or
- add paper, brokerage, order, live, or real-money behavior.

Actual allocated-attempt count, trial execution count, artifact production,
and protected-sample access remain zero.

## Next Gate

After R1H is accepted on protected main, perform a read-only dependency/risk
analysis over the remaining 27 incomplete events. `ATTEMPT_STARTED` is the
strict compute-path successor, while `ACCESS_INTENT` remains the independent
protected-access capability root and the campaign amendment pair remains an
optional inventory branch. Continue with the smallest safe family without
inferring exact start capability, terminal evidence, artifact identity,
access authorization, or event boundaries. Surface only a genuine
owner-methodology choice under the bounded reminder policy.

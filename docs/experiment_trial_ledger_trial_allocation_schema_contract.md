# Experiment and Trial Ledger Trial Allocation R1F Contract

Contract ID: `experiment_trial_ledger_trial_allocation_schema_r1f`.

Contract version: `0.6.0`.

Owner decision: option `R1F-A`.

This document is the design authority for the bounded Stage 4B-R1F semantic
trial-allocation release under:

- `docs/research_program_charter.md`;
- `docs/point_in_time_data_methodology_contract.md`;
- `docs/experiment_trial_ledger_contract.md`;
- `docs/experiment_trial_ledger_schema_registry_contract.md`;
- `docs/experiment_trial_ledger_allocation_registration_schema_contract.md`;
- `docs/experiment_trial_ledger_trial_family_registration_schema_contract.md`;
- `docs/experiment_trial_ledger_sample_registration_schema_contract.md`; and
- `docs/experiment_trial_ledger_binding_schema_contract.md`.

Its publication state is determined by protected-main history and
`docs/current_handoff.md`, not by a status claim inside this document.

## Release Boundary

R1F publishes one new immutable registry release:

- registry schema ID
  `experiment_trial_ledger_payload_schema_registry_v6`;
- registry version `0.6.0`;
- unchanged schema-language ID `ledger_closed_schema_dsl_v1`;
- unchanged schema-language version `0.2.0`; and
- a separate packaged JSON artifact and SHA-256 sidecar.

R1F preserves the accepted 37-event vocabulary. Its supported event set is
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
```

The other 29 events remain
`SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`. R1F does not overwrite, reinterpret, or
silently upgrade immutable registry releases `0.1.0` through `0.5.0`, their
digests, the default R0 entry point, or prior validator outcomes.

Registry acceptance proves only the closed local shape and literal syntax of a
candidate event. It does not prove that any parent event exists, that retained
source bytes match a digest, that an external record is retrievable or
current, that reviewers are independent, that actor authority is valid, that
relations are acyclic, that a trial identity is unique, that an append is
durable, or that any research computation occurred.

## Exact Trial Identity and Event Boundary

The exact trial namespace is:

```text
trl_<32 lowercase hexadecimal digits>
```

`TRIAL_ALLOCATED` allocates one new semantic trial identity. It has:

- `event_type` exactly `TRIAL_ALLOCATED`;
- `subject_type` exactly `trial`;
- `subject_id` exactly one newly allocated `trial_id`;
- one-item sorted-unique `payload.campaign_scope_ids`;
- no duplicate trial or campaign identity inside the payload; and
- `payload.initial_disposition` exactly `PLANNED`.

Changing any identity-bearing definition field requires a new `trial_id`.
Exact replay of the same append operation is idempotency, not another trial.
An operational retry uses a new future `attempt_id` under the same open trial.
A rerun after terminal closure uses a new trial ID and the `rerun` relation.

The event payload contains exactly:

```text
allocation_authority_generation
allocation_authority_id
allocation_authority_record_sha256
allocation_authority_schema_version
campaign_allocation_event_id
campaign_allocation_event_sha256
campaign_scope_ids
code_identity
experiment_allocation_event_id
experiment_allocation_event_sha256
experiment_id
initial_disposition
relation
trial_definition_acceptance_decision_id
trial_definition_acceptance_generation
trial_definition_acceptance_record_sha256
trial_definition_acceptance_schema_version
trial_definition_authority_id
trial_definition_authority_registry_sha256
trial_definition_authority_version
trial_definition_public_projection_id
trial_definition_public_projection_schema_version
trial_definition_public_projection_sha256
trial_definition_publication_approval_generation
trial_definition_publication_approval_id
trial_definition_publication_approval_record_sha256
trial_definition_publication_approval_schema_version
trial_definition_record_canonicalization_id
trial_definition_record_id
trial_definition_record_schema_version
trial_definition_record_sha256
trial_definition_record_version
trial_family_id
trial_family_source_event_id
trial_family_source_event_sha256
```

Missing, null, unknown, duplicate, wrong-type, unsafe, or additional fields
fail closed.

## Exact Parent Evidence

The local schemas for direct parent evidence are:

| Field | Exact local schema |
| --- | --- |
| `campaign_scope_ids` | sorted-unique array of `campaign_id`, minimum 1, maximum 1 |
| `campaign_allocation_event_id` | `event_id` |
| `campaign_allocation_event_sha256` | lowercase SHA-256 |
| `experiment_id` | `experiment_id` |
| `experiment_allocation_event_id` | `event_id` |
| `experiment_allocation_event_sha256` | lowercase SHA-256 |
| `trial_family_id` | `trial_family_id` |
| `trial_family_source_event_id` | `event_id` |
| `trial_family_source_event_sha256` | lowercase SHA-256 |
| `initial_disposition` | literal `PLANNED` |

Before append, stateful validation must resolve exact earlier retained events
in the same ledger epoch and prove:

- the campaign source is `CAMPAIGN_ALLOCATED` for the singleton campaign;
- the experiment source is `EXPERIMENT_ALLOCATED` for the exact experiment
  under that campaign;
- the family source is either the direct campaign-scoped
  `TRIAL_FAMILY_REGISTERED` or the exact `CAMPAIGN_ENTITY_BOUND` for the same
  family and campaign;
- every sample binding named by the complete trial-definition record resolves
  through exactly one legal direct, global-plus-binding, or external-reference
  path for the same campaign;
- every referenced event ID and recomputed canonical-byte digest matches;
- every source precedes this allocation; and
- every external authority, acceptance, projection, publication approval, and
  source path remains current immediately before append.

A hash-only stand-in, missing or later event, changed retained bytes, wrong
event type, wrong subject, wrong campaign, mixed origin path, stale authority,
ambiguous source, or incomplete sample set fails closed. Local schema `ACCEPT`
is not parent or currentness proof.

## Complete Canonical Trial Definition

Complete trial-definition records are repository-external and private by
default. `TRIAL_ALLOCATED` pins one exact record using:

| Field | Exact local schema |
| --- | --- |
| `trial_definition_authority_id` | `safe_public_id` |
| `trial_definition_authority_registry_sha256` | lowercase SHA-256 |
| `trial_definition_authority_version` | I-JSON safe integer, minimum 1 |
| `trial_definition_record_canonicalization_id` | literal `pit_canonical_json_v1` |
| `trial_definition_record_id` | `safe_public_id` |
| `trial_definition_record_schema_version` | literal `trial_definition_record_v1` |
| `trial_definition_record_sha256` | lowercase SHA-256 |
| `trial_definition_record_version` | I-JSON safe integer, minimum 1 |

The exact `trial_definition_record_v1` complete record must bind:

- campaign, experiment, global trial-family, and trial identity;
- hypothesis, estimand, expected direction, formula, parameters, horizon,
  universe, preprocessing, neutralization, selection, weighting, and
  constraints;
- the complete sorted sample-binding set, with each `sample_id`, role,
  classification, exact window reference, access policy, source event ID,
  source event SHA-256, and legal origin path;
- immutable data-manifest/input identities, lineage, approved public hashes,
  and private-record references;
- environment ID, lock hash, interpreter, platform, locale, timezone, and
  exact dependency versions;
- feature, availability, decision, execution, label, return-window, split,
  purge, embargo, benchmark, risk-free, cost, slippage, capacity, and
  execution-contract references;
- selection role, expected artifact roles, retry policy, and trial budget
  accounting; and
- private/public projection decisions and every identity-bearing default.

The record must be complete rather than a partial hash manifest. It uses only
closed versioned nested records and finite ordered or sorted-unique
collections. Raw floating-point objects, mutable paths, implicit defaults,
open maps, free-form extension fields, unordered identity-bearing
collections, or lossy key coercion are not valid.

R1F fixes a finite maximum of 32 sample bindings per semantic trial. This is a
schema and review bound, not evidence that 32 samples are methodologically
appropriate. A trial requiring a different bound needs a versioned owner
decision rather than truncation.

## Definition Acceptance and Reviewer Independence

One separate immutable acceptance record is pinned by:

| Field | Exact local schema |
| --- | --- |
| `trial_definition_acceptance_decision_id` | `safe_public_id` |
| `trial_definition_acceptance_generation` | I-JSON safe integer, minimum 1 |
| `trial_definition_acceptance_record_sha256` | lowercase SHA-256 |
| `trial_definition_acceptance_schema_version` | literal `trial_definition_acceptance_v1` |

The acceptance record binds the exact authority/catalog/record tuple, trial
identity, campaign, experiment, family, complete sample set, relation, code
identity, and scope. Its reviewer must be distinct from:

- the trial-definition issuer;
- the allocation actor; and
- any actor who produced a private input record being accepted.

Acceptance generations are strictly monotonic and exactly one generation is
current. Supersession is explicit and leaves prior bytes immutable. Retrieval
miss, ambiguity, changed canonical bytes, digest mismatch, stale acceptance,
self-review, wrong scope, or wrong record tuple fails closed.

## Exact Trial Relation Union

`payload.relation` is a closed `tagged_union` discriminated by
`relation_kind`. Its exact variants are:

### `original`

```text
relation_kind = original
```

No source trial fields are present.

### `child`, `clone`, and `rerun`

Each contains exactly:

```text
relation_kind
source_trial_allocation_event_id
source_trial_allocation_event_sha256
source_trial_id
```

`source_trial_id` uses `trial_id`; the source event ID uses `event_id`; and the
source event hash uses lowercase SHA-256. The discriminator literal matches
the selected branch.

The source must be an exact earlier `TRIAL_ALLOCATED` in the same verified
ledger epoch. Relations are complete and acyclic. A child is a declared
dependency within the registered design, a clone preserves the same semantic
definition under its declared campaign context, and a rerun follows a terminal
source trial after result exposure. None of these relations resets global
family multiplicity, sample exposure, prior outcomes, or selection history.
Aliases, self-reference, cycles, later sources, hidden parents, or changing a
relation after allocation fail closed.

## Exact Code Identity Union

`payload.code_identity` is a closed `tagged_union` discriminated by
`code_identity_kind`.

The `clean_commit` branch contains exactly:

```text
code_commit_id
code_identity_kind
code_repository_id
code_tree_sha256
```

The `dirty_tree` branch contains exactly:

```text
code_base_commit_id
code_base_tree_sha256
code_identity_kind
code_patch_sha256
code_repository_id
code_resulting_tree_sha256
```

Repository and commit IDs use `safe_public_id`; tree and patch digests use
lowercase SHA-256. Missing, cross-branch, or extra fields fail closed.

A clean branch must resolve to the exact retained commit and canonical source
tree. A dirty branch binds the base commit/tree, exact patch bytes, and
resulting canonical tree. Dirty-tree evidence is ineligible for formal
interpretation until a separate independent review verifies the exact tuple;
local shape acceptance or definition acceptance cannot silently waive that
gate. Later cleanup does not rewrite the dirty allocation.

## Allocation Actor Authority

The event pins the actor's allocation authority using:

| Field | Exact local schema |
| --- | --- |
| `allocation_authority_id` | `safe_public_id` |
| `allocation_authority_generation` | I-JSON safe integer, minimum 1 |
| `allocation_authority_record_sha256` | lowercase SHA-256 |
| `allocation_authority_schema_version` | literal `trial_allocation_authority_v1` |

The repository-external authority record binds the exact `actor_id`, allowed
operation, campaign, trial-definition tuple, activation interval, generation,
issuer, and revocation/supersession state. The authority must be active
immediately before append. The event schema validates only reference syntax;
it does not authenticate the actor or grant permission.

## Privacy and Publication Boundary

The complete trial definition, authority records, acceptance record, private
data identities, restricted sample windows, paths, credentials, queries,
commands, raw values, private performance values, and outcome-reconstructible
content remain repository-external.

The event pins one allowlisted public projection and approval:

| Field | Exact local schema |
| --- | --- |
| `trial_definition_public_projection_id` | `safe_public_id` |
| `trial_definition_public_projection_schema_version` | literal `public_redacted_projection_v1` |
| `trial_definition_public_projection_sha256` | lowercase SHA-256 |
| `trial_definition_publication_approval_id` | `safe_public_id` |
| `trial_definition_publication_approval_generation` | I-JSON safe integer, minimum 1 |
| `trial_definition_publication_approval_record_sha256` | lowercase SHA-256 |
| `trial_definition_publication_approval_schema_version` | literal `trial_definition_public_projection_approval_v1` |

The public projection is field/value allowlisted and independently approved.
A digest is not public merely because it is non-reversible. Committed fixtures
contain synthetic IDs and synthetic digest strings only. A later public ledger
projection must omit every non-approved field and value.

## Stateful Uniqueness, Currentness, and Ordering

Before append, stateful validation must prove:

- the trial ID has never been allocated;
- the campaign and experiment are allocated and exact;
- the family and every sample have exactly one complete legal current path;
- the canonical definition, acceptance, publication approval, and allocation
  authority are exact and current;
- the relation source, if any, is earlier, exact, and acyclic;
- the code identity resolves to retained bytes;
- the trial-definition record's trial ID, campaign, experiment, family,
  samples, relation, code identity, and scope equal the event;
- no identity-bearing value was defaulted, omitted, inferred, or changed; and
- the allocation occurs before any validation, execution, attempt allocation,
  protected access, artifact production, or result inspection.

An append failure means no validator, executor, or accessor is invoked.
Supersession leaves historical bytes immutable and blocks new action that
depends on stale state. No clone, rerun, campaign, alias, post-result
reclassification, or external-record revision resets multiplicity or exposure
history.

These are stateful ledger and external-authority rules. R1F does not implement
them, and local schema `ACCEPT` must not be represented as proof of them.

## Required Killing Evidence

R1F must include independent evidence for:

- byte-exact R0 through R4 artifacts, digests, behavior, and package resources;
- explicit packaged registry `0.6.0` selection and unchanged default R0;
- exact `trl_<32 lowercase hex>` namespace;
- exact eight-event supported and 29-event incomplete partitions;
- independent positive clean-original and dirty-rerun fixtures plus literal
  positive child and clone relation cases;
- every missing, unknown, duplicate, null, and wrong-type envelope or payload
  field;
- empty/multi-item/wrong-namespace campaign scopes;
- wrong campaign, experiment, family, trial, event, digest, safe-public-ID,
  version, generation, and literal syntax;
- every relation discriminator, missing source, and cross-branch field killer;
- shape-valid self-source, cycle, later-source, and changed-source cases
  explicitly documented as statefully fail closed rather than local
  `ACCEPT` evidence;
- both code-identity branches and every cross-branch field killer;
- wrong definition, acceptance, projection, approval, allocation-authority,
  and canonicalization literals;
- shape-valid but missing, later, stale, self-reviewed, unauthorized,
  cyclic, mixed-path, duplicate-ID, changed-source, dirty-unreviewed, or
  post-action allocation state explicitly documented as later fail-closed
  cases rather than local `ACCEPT` evidence;
- every nonpromoted and unknown event rejected before action; and
- arbitrary self-consistent unpublished promotion rejected by packaged digest
  authority.

The independent fixture must not be generated from the registry artifact.
Literal tests must not discover expected fields, namespaces, branch names,
supported events, or outcome codes from the implementation under test.

## Non-Goals

R1F does not:

- append, store, allocate, retrieve, authorize, authenticate, accept, approve,
  supersede, validate, execute, access, review, or promote anything;
- implement trial-definition or authority catalogs;
- select a backend, private ledger path, transaction/recovery policy,
  signature mechanism, provider, dataset, strategy, factor, or statistical
  method;
- promote inventory, attempt, lifecycle, access, artifact, closure, review,
  decision, adjudication, or supersession events;
- copy private records, paths, raw values, or performance values into the
  repository;
- run a trial, attempt, protected access, factor, backtest, report, or
  historical interpretation; or
- add paper, brokerage, order, live, or real-money behavior.

Trial execution count, attempt count, and protected-sample access remain zero.

## Next Gate

The transition out of R1F required the workflow to perform a read-only
dependency/risk analysis over the remaining 29 incomplete events. That
analysis selected the bounded successor in
`docs/experiment_trial_ledger_campaign_inventory_seal_schema_contract.md`.
The owner selected the bounded successor in
`docs/experiment_trial_ledger_campaign_inventory_seal_schema_contract.md`.
R1G publishes a separate immutable registry `0.7.0`, promotes only
`CAMPAIGN_INVENTORY_SEALED`, and does not reinterpret this R1F authority. After
R1G is accepted on protected main, the next analysis covers the remaining 28
incomplete events before the smallest next family is selected. A genuinely
material architecture choice receives a concise owner memo and the bounded
reminder policy; otherwise continuation remains automatic.

# Experiment and Trial Ledger Binding R1E Contract

Contract ID: `experiment_trial_ledger_binding_schema_r1e`.

Contract version: `0.5.0`.

Owner decision: option `R1E-A`.

This document is the design authority for the bounded Stage 4B-R1E
campaign-entity and external Stage 3 sample-reference binding release under:

- `docs/point_in_time_data_methodology_contract.md`;
- `docs/experiment_trial_ledger_contract.md`;
- `docs/experiment_trial_ledger_schema_registry_contract.md`;
- `docs/experiment_trial_ledger_allocation_registration_schema_contract.md`;
- `docs/experiment_trial_ledger_trial_family_registration_schema_contract.md`;
  and
- `docs/experiment_trial_ledger_sample_registration_schema_contract.md`.

Its publication state is determined by protected-main history and
`docs/current_handoff.md`, not by a status claim inside this document.

## Release Boundary

R1E publishes one new immutable registry release:

- registry schema ID
  `experiment_trial_ledger_payload_schema_registry_v5`;
- registry version `0.5.0`;
- unchanged schema-language ID `ledger_closed_schema_dsl_v1`;
- unchanged schema-language version `0.2.0`; and
- a separate packaged JSON artifact and SHA-256 sidecar.

R1E preserves the accepted 37-event vocabulary. Its supported event set is
exactly:

```text
LEDGER_EPOCH_CREATED
CAMPAIGN_ALLOCATED
EXPERIMENT_ALLOCATED
TRIAL_FAMILY_REGISTERED
SAMPLE_REGISTERED
CAMPAIGN_ENTITY_BOUND
STAGE3_SAMPLE_REFERENCE_BOUND
```

The other 30 events remain
`SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`. R1E does not overwrite, reinterpret, or
silently upgrade immutable registry releases `0.1.0`, `0.2.0`, `0.3.0`, or
`0.4.0`, their digests, the default R0 entry point, or prior validator
outcomes.

Registry acceptance proves only that a candidate event has the accepted local
shape and literal syntax. It does not prove source-event existence, retained
source bytes, a recomputed source digest, source ordering, prior campaign
allocation, authority retrieval, acceptance or publication currentness,
reviewer independence, uniqueness, path exclusivity, overlap history,
sequence or previous-hash truth, append durability, or sample-exposure
history.

## Exact `CAMPAIGN_ENTITY_BOUND` Boundary

`CAMPAIGN_ENTITY_BOUND` binds one existing ledger-local trial family or sample
identity to one already allocated campaign. The event uses a top-level
`tagged_union` discriminated by `subject_type`; it does not use a generic
entity namespace, redundant payload identity, two nullable identities, or a
free-form kind.

Both branches have:

- `event_type` exactly `CAMPAIGN_ENTITY_BOUND`;
- one existing entity as `subject_id`;
- a one-item `payload.campaign_scope_ids` array containing an exact
  `cmp_<32 lowercase hex>` identity; and
- no duplicate subject or campaign ID inside the payload.

The exact outer branches are:

| `subject_type` | Exact `subject_id` schema | Exact source family |
| --- | --- | --- |
| `trial_family` | `trial_family_id`, `fam_<32 lowercase hex>` | ledger-global `TRIAL_FAMILY_REGISTERED` only |
| `sample` | `sample_id`, `smp_<32 lowercase hex>` | selected by the nested `payload.source_kind` union |

### Trial-family branch

The trial-family payload contains exactly:

```text
campaign_scope_ids
source_registration_event_id
source_registration_event_sha256
```

Its exact local schemas are:

| Field | Exact local schema |
| --- | --- |
| `campaign_scope_ids` | sorted-unique array of `campaign_id`, minimum 1, maximum 1 |
| `source_registration_event_id` | `event_id` |
| `source_registration_event_sha256` | lowercase SHA-256 |

### Sample branch

The sample payload is a nested `tagged_union` discriminated by
`source_kind`. Its exact variants are:

```text
local_registration
external_reference
```

The `local_registration` payload contains exactly:

```text
campaign_scope_ids
source_kind
source_registration_event_id
source_registration_event_sha256
```

The `external_reference` payload contains exactly:

```text
campaign_scope_ids
source_kind
source_reference_event_id
source_reference_event_sha256
```

For both variants, `campaign_scope_ids` is a sorted-unique array of
`campaign_id` with minimum and maximum 1. Each discriminator is the exact
literal matching its branch. Source IDs use `event_id`; source hashes use
lowercase SHA-256.

Missing, null, unknown, duplicated, cross-branch, or mismatched discriminator
fields fail closed. In particular:

- a local branch cannot carry external-reference fields;
- an external branch cannot carry local-registration fields;
- a sample branch cannot carry trial-family source fields outside its nested
  union; and
- a trial-family branch cannot carry `source_kind`.

The common event envelope remains the accepted `ledger_event_v1` envelope.

## Exact Source-Event Authority

Local shape validation checks source ID and digest syntax only. Before append,
stateful validation must resolve the exact source event from retained
same-epoch evidence and prove:

- the source exists earlier in the same ledger epoch;
- retained source bytes parse without duplicate properties;
- recomputing the event digest from the exact retained canonical bytes equals
  the referenced SHA-256;
- the retained event ID equals the referenced event ID;
- event type, subject type, subject ID, and campaign scope match the selected
  branch; and
- the source precedes every consuming trial or protected access.

For `trial_family`, the source must be `TRIAL_FAMILY_REGISTERED` for the exact
subject with empty `campaign_scope_ids`.

For sample `local_registration`, the source must be `SAMPLE_REGISTERED` for
the exact subject with empty `campaign_scope_ids`.

For sample `external_reference`, the source must be
`STAGE3_SAMPLE_REFERENCE_BOUND` for the exact subject. Its singleton campaign
scope is the first campaign in which that external-origin ledger-local
identity was introduced. The new binding campaign may differ, but the source
external authority, record, acceptance, projection, publication-approval,
lineage, and overlap tuple must still be exact and current.

A missing event, hash-only stand-in, noncanonical source, changed bytes,
digest mismatch, wrong type, wrong subject, wrong source path, nonempty global
registration scope, later source, or ambiguous retained event fails closed.
Schema `ACCEPT` is not source proof.

## Minimal Amendment for External-Origin Reuse

R1E-A makes one explicit bounded amendment to the R1A binding architecture.
An existing external-origin `sample_id` may be reused in later campaigns
through the sample `external_reference` branch of
`CAMPAIGN_ENTITY_BOUND`, referencing the exact earlier
`STAGE3_SAMPLE_REFERENCE_BOUND` event ID and hash.

This amendment is required to preserve the R1D-A one-lineage/one-local-identity
and anti-reset decision across campaigns. It does not permit:

- a new `sample_id` for each campaign;
- a synthetic `SAMPLE_REGISTERED`;
- conversion between local and external origin paths;
- a different external record or authority tuple;
- hiding the first campaign or prior exposure history; or
- using `CAMPAIGN_ENTITY_BOUND` as a second origin allocation.

The first external-reference event remains the sole allocation of that
external-origin local sample identity. Later bindings reuse it.

## Exact `STAGE3_SAMPLE_REFERENCE_BOUND` Boundary

`STAGE3_SAMPLE_REFERENCE_BOUND` introduces one external-origin ledger-local
sample identity for one already allocated campaign. It has:

- `subject_type` exactly `sample`;
- `subject_id` exactly one newly allocated
  `smp_<32 lowercase hex>` identity;
- no duplicate sample ID inside its payload; and
- a one-item sorted-unique `payload.campaign_scope_ids` array of exact
  `campaign_id`.

Its payload contains exactly:

```text
campaign_scope_ids
sample_acceptance_decision_id
sample_acceptance_generation
sample_acceptance_record_sha256
sample_acceptance_schema_version
sample_authority_id
sample_authority_registry_sha256
sample_authority_version
sample_public_projection_id
sample_public_projection_schema_version
sample_public_projection_sha256
sample_publication_approval_generation
sample_publication_approval_id
sample_publication_approval_record_sha256
sample_publication_approval_schema_version
sample_record_canonicalization_id
sample_record_id
sample_record_schema_version
sample_record_sha256
sample_record_version
```

These fields use the exact local schemas already frozen for R1D
`SAMPLE_REGISTERED`, except that `campaign_scope_ids` has minimum and maximum
1:

| Field | Exact local schema |
| --- | --- |
| `campaign_scope_ids` | sorted-unique array of `campaign_id`, minimum 1, maximum 1 |
| `sample_authority_id` | `safe_public_id` |
| `sample_authority_registry_sha256` | lowercase SHA-256 |
| `sample_authority_version` | I-JSON safe integer, minimum 1 |
| `sample_record_canonicalization_id` | literal `pit_canonical_json_v1` |
| `sample_record_id` | `safe_public_id` |
| `sample_record_schema_version` | literal `stage3_sample_record_v1` |
| `sample_record_sha256` | lowercase SHA-256 |
| `sample_record_version` | I-JSON safe integer, minimum 1 |
| `sample_acceptance_decision_id` | `safe_public_id` |
| `sample_acceptance_generation` | I-JSON safe integer, minimum 1 |
| `sample_acceptance_record_sha256` | lowercase SHA-256 |
| `sample_acceptance_schema_version` | literal `stage3_sample_acceptance_v1` |
| `sample_public_projection_id` | `safe_public_id` |
| `sample_public_projection_schema_version` | literal `public_redacted_projection_v1` |
| `sample_public_projection_sha256` | lowercase SHA-256 |
| `sample_publication_approval_id` | `safe_public_id` |
| `sample_publication_approval_generation` | I-JSON safe integer, minimum 1 |
| `sample_publication_approval_record_sha256` | lowercase SHA-256 |
| `sample_publication_approval_schema_version` | literal `sample_public_projection_approval_v1` |

Missing, null, Boolean-as-integer, wrong-type, unsafe, unknown, duplicate, or
additional fields fail closed.

## External Authority and Privacy

`STAGE3_SAMPLE_REFERENCE_BOUND` pins the same exact authority, record,
acceptance, public-projection, and publication-approval tuple accepted by
R1D-A. The complete canonical records remain repository-external. Before
append, the stateful resolver must retrieve and verify:

- the pinned immutable authority catalog;
- the complete canonical Stage 3 sample record;
- the separate non-self-issued current acceptance record;
- the allowlisted public projection; and
- the separate current publication-approval record.

The acceptance reviewer must remain distinct from the record producer and the
binding actor. Retrieval miss, ambiguity, noncanonical bytes, schema mismatch,
digest mismatch, stale or superseded acceptance, revoked or superseded
publication approval, self-review, or scope mismatch fails closed.

Complete records, private paths, credentials, account or contract IDs,
restricted queries, signed URLs, raw rows, symbol-level restricted data,
private digests not approved for publication, private performance values, and
outcome-reconstructible content remain repository-external and private. A
digest is not publication safe merely because it is non-reversible. Committed
fixtures use synthetic IDs and synthetic digests only.

`STAGE3_SAMPLE_REFERENCE_BOUND` is private ledger evidence. A later public
ledger projection must omit its fields unless each exact field/value is
independently allowlisted and covered by the pinned publication approval.

## Stateful Path, Uniqueness, and Prior-Allocation Rules

For either promoted event:

- every target campaign must already have one accepted
  `CAMPAIGN_ALLOCATED`;
- the append must occur after the campaign allocation;
- one `(ledger_id, campaign_id, subject_type, subject_id)` binding exists at
  most once; and
- the binding precedes `TRIAL_ALLOCATED`, every attempt, and every protected
  access that consumes it.

For `STAGE3_SAMPLE_REFERENCE_BOUND`:

- no earlier event may allocate the same `sample_id`;
- no other local identity may represent the same provider-neutral canonical
  sample lineage or exact authority/record tuple;
- no local `SAMPLE_REGISTERED` path may exist for the lineage;
- the selected acceptance and publication approval must be current
  immediately before append; and
- the event is the sole external-origin allocation for that identity.

For `CAMPAIGN_ENTITY_BOUND`:

- a directly campaign-scoped registration cannot also have a binding for that
  campaign;
- a ledger-global local registration uses only the matching
  `local_registration` source branch;
- an external-origin sample uses only the matching `external_reference`
  source branch; and
- no binding may change the identity's origin path or source tuple.

Currentness is revalidated immediately before every binding and later before
trial allocation, attempt execution, and protected access. Supersession leaves
historical events immutable but blocks every new consuming action.

Aliases, clones, reruns, new campaigns, window overlap, result access, and
post-result reclassification do not allocate a new identity, switch origin
paths, or reset multiplicity, dependence, or exposure history. A later
campaign cannot manufacture pristine holdout status. Corrections use explicit
supersession and never mutate prior event bytes.

These are stateful ledger and external-authority rules. R1E does not implement
them, and local schema `ACCEPT` must not be represented as proof of them.

## Required Killing Evidence

R1E must include independent evidence for:

- byte-exact R0, R1B, R1C, and R1D artifacts, digests, behavior, and package
  resources;
- explicit selection of packaged registry `0.5.0`;
- the exact seven-event supported set and 30-event incomplete partition;
- independent positive fixtures for trial-family binding, global-local sample
  binding, first external Stage 3 reference, and later external-origin sample
  binding;
- every missing envelope and payload field;
- every top-level, outer-union, nested-union, and payload unknown or duplicate
  field;
- missing, null, unknown, and mismatched `subject_type` and `source_kind`;
- wrong `fam_`, `smp_`, `cmp_`, `evt_`, and digest syntax;
- empty or multi-item campaign scopes;
- local/external source field bleed and trial-family/sample branch bleed;
- wrong Stage 3 record, acceptance, projection, approval, and
  canonicalization literals;
- unsafe authority, record, acceptance, projection, and approval IDs;
- invalid versions, generations, and digests;
- shape-valid candidates with missing, later, changed, stale, self-reviewed,
  wrong-path, duplicate-target, mixed-path, or reset source state, explicitly
  documented as later stateful fail-closed cases rather than local `ACCEPT`
  evidence;
- every nonpromoted event and unknown event rejected before action; and
- arbitrary self-consistent unpublished event promotion rejected by packaged
  digest authority.

The independent fixture must not be generated from the registry artifact.
Literal tests must not discover expected fields, namespaces, supported events,
source variants, or outcome codes from the implementation under test.

## Non-Goals

R1E does not:

- append, store, allocate, register, bind, retrieve, resolve, accept, approve,
  supersede, authenticate, authorize, or execute anything;
- select a provider, dataset, backend, object store, database, private ledger
  path, signature scheme, or recovery mechanism;
- promote `TRIAL_ALLOCATED` or any lifecycle, access, review, closure,
  adjudication, or supersession event;
- copy private sample records, paths, raw values, or performance values into
  the repository;
- run a campaign, trial, attempt, protected access, factor, backtest, or
  historical interpretation; or
- add paper, brokerage, order, live, or real-money behavior.

Trial count, execution-attempt count, and protected-sample access remain zero.

## Next Gate

The owner selected the bounded successor in
`docs/experiment_trial_ledger_trial_allocation_schema_contract.md`. R1F
publishes a separate immutable registry `0.6.0`, promotes only
`TRIAL_ALLOCATED`, and does not reinterpret this R1E authority. After R1F is
accepted on protected main, the remaining-event dependency/risk graph is
analyzed read-only before the smallest next family is selected. Any genuine
owner-methodology gate follows the bounded reminder policy: four reminders at
30-minute intervals, then the heartbeat pauses if the owner has not replied.

## Track B v7 Design Candidate Extension

Status: proposed owner-contract extension for `OD-TB-V7-SCHEMA`; design only.
The accepted plan manifest is pinned in the linked v7 design and its fixture.
The preceding contract remains the frozen baseline. This additive section
specifies required resolved-byte paths and additional predicates for the
single Track B design candidate. Existing payload fields, tuple identity,
canonicalization, privacy rules and stronger role checks remain binding.
These paths are proposed schema additions where the baseline states only
semantic bindings; they are not claims about an inspected external catalog.
An owner catalog lacking any required operand remains inadmissible until
this design and its owner-schema mapping are approved. No request field
can substitute for a missing resolved-byte operand.

### Symmetric origin and later-reference mappings

Stage 3 uses every sample tuple and resolved path in the
[sample owner](experiment_trial_ledger_sample_registration_schema_contract.md#track-b-v7-design-candidate-extension),
including lineage, complete native record identity, roles, acceptance,
projection and publication approval. Both origin events use the complete bundle.
The v7 term `ledger_epoch_id` maps to existing `ledger_id`, introduced once by
`LEDGER_EPOCH_CREATED`; it is not a new payload field or namespace.

Under the writer lock, both origin appends inspect committed origins of both
types across all campaigns. Independently enforce `(ledger_id, sample_id)`,
`(ledger_id, canonical_sample_lineage_id)` and `(ledger_id, complete native
sample authority/record identity tuple)` uniqueness. V7 section 6.4 freezes
the exact refusal precedence. Catalog or acceptance changes do not reset lineage.

External references follow `payload.source_reference_event_id` and
`payload.source_reference_event_sha256`; local references follow
`payload.source_registration_event_id` and
`payload.source_registration_event_sha256`. Recompute retained source hashes.
External target campaign allocation sequence must be strictly greater than
origin campaign allocation sequence. Same campaign maps to
`CAMPAIGN_ENTITY_BOUND_NOT_LATER_CAMPAIGN`, earlier to
`CAMPAIGN_ENTITY_BOUND_EARLIER_CAMPAIGN`, absent allocation to
`CAMPAIGN_ENTITY_BOUND_PARENT_ORDER`. A binding cannot allocate another sample,
change native tuple, mix direct scope/binding or reserve an additional origin.
The remaining exact refusals are in v7 section 6.3.

The [v7 design](experiment_trial_ledger_track_b_v7_design.md) freezes the boundary predicates and refusal
inventory. Its synthetic fixtures check design consistency; they do not
demonstrate append, catalog, currentness, capability or SQLite execution.

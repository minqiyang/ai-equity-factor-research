# Experiment and Trial Ledger Trial-Family Registration R1C Contract

Contract ID:
`experiment_trial_ledger_trial_family_registration_schema_r1c`.

Contract version: `0.3.0`.

Owner decision: option `R1C-A`.

Exact trial-family namespace: `fam_<32 lowercase hex>`.

This document is the design authority for the bounded Stage 4B-R1C
trial-family registration release under:

- `docs/experiment_trial_ledger_contract.md`;
- `docs/experiment_trial_ledger_schema_registry_contract.md`; and
- `docs/experiment_trial_ledger_allocation_registration_schema_contract.md`.

Its publication state is determined by protected-main history and
`docs/current_handoff.md`, not by a status claim inside this document.

## Release Boundary

R1C publishes one new immutable registry release:

- registry schema ID
  `experiment_trial_ledger_payload_schema_registry_v3`;
- registry version `0.3.0`;
- unchanged schema-language ID `ledger_closed_schema_dsl_v1`;
- unchanged schema-language version `0.2.0`; and
- a separate packaged JSON artifact and SHA-256 sidecar.

R1C preserves the accepted 37-event vocabulary. Its supported event set is
exactly:

```text
LEDGER_EPOCH_CREATED
CAMPAIGN_ALLOCATED
EXPERIMENT_ALLOCATED
TRIAL_FAMILY_REGISTERED
```

The other 33 events remain
`SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`. R1C does not overwrite, reinterpret, or
silently upgrade the immutable R0 `0.1.0` or R1B `0.2.0` artifacts, digests,
default R0 entry point, or validator outcomes.

Registry acceptance proves only that a candidate event has the accepted local
shape and literal syntax. It does not prove retrieval, authority, acceptance,
currentness, role independence, prior campaign allocation, uniqueness,
sequence or previous-hash truth, append durability, or family multiplicity
history.

## Exact Event Subject and Scope

`TRIAL_FAMILY_REGISTERED` has:

- `subject_type` exactly `trial_family`;
- `subject_id` exactly one newly registered
  `fam_<32 lowercase hex>` identity; and
- no duplicate trial-family ID inside its payload.

Its `payload.campaign_scope_ids` is a sorted-unique array of exact
`cmp_<32 lowercase hex>` identities:

- empty means a ledger-global registration;
- one through 32 entries means a direct registration covering exactly those
  campaigns; and
- 33 or more entries are invalid.

Every campaign in a nonempty direct scope must already be allocated before the
registration is appended. A global registration and each campaign allocation
are independent siblings after the epoch; a later
`CAMPAIGN_ENTITY_BOUND` event is still required before a global family is used
inside a campaign. These are stateful rules and are not established by local
shape validation.

The maximum of 32 is the common direct-registration bound for this family
release and the later ledger-local sample registration release. Broader reuse
must use ledger-global registration plus explicit campaign binding rather than
an unbounded direct scope.

## Exact Registration Payload

The payload contains exactly these fields:

```text
campaign_scope_ids
family_acceptance_decision_id
family_acceptance_generation
family_acceptance_record_sha256
family_acceptance_schema_version
family_authority_id
family_authority_registry_sha256
family_authority_version
family_definition_canonicalization_id
family_definition_record_id
family_definition_record_sha256
family_definition_record_version
family_definition_schema_version
```

Their exact local schemas are:

| Field | Exact local schema |
| --- | --- |
| `campaign_scope_ids` | sorted-unique array of `campaign_id`, minimum 0, maximum 32 |
| `family_authority_id` | `safe_public_id` |
| `family_authority_registry_sha256` | lowercase SHA-256 |
| `family_authority_version` | I-JSON safe integer, minimum 1 |
| `family_definition_canonicalization_id` | literal `pit_canonical_json_v1` |
| `family_definition_record_id` | `safe_public_id` |
| `family_definition_record_sha256` | lowercase SHA-256 |
| `family_definition_record_version` | I-JSON safe integer, minimum 1 |
| `family_definition_schema_version` | literal `trial_family_definition_v1` |
| `family_acceptance_decision_id` | `safe_public_id` |
| `family_acceptance_generation` | I-JSON safe integer, minimum 1 |
| `family_acceptance_record_sha256` | lowercase SHA-256 |
| `family_acceptance_schema_version` | literal `trial_family_definition_acceptance_v1` |

Missing, null, Boolean-as-integer, wrong-type, unsafe, unknown, duplicate, or
additional fields fail closed. The common event envelope remains the accepted
`ledger_event_v1` envelope.

## Exact Retrievable Family Authority

R1C-A selects an immutable versioned authority catalog plus complete
repository-external canonical records. It does not select a physical storage
provider or private ledger backend.

The registration pins the authority catalog by:

```text
family_authority_id
family_authority_version
family_authority_registry_sha256
family_definition_canonicalization_id
```

It pins one complete family-definition record by:

```text
family_definition_record_id
family_definition_record_version
family_definition_schema_version
family_definition_record_sha256
```

The accepted resolver key is the exact tuple:

```text
(
  family_authority_id,
  family_authority_version,
  family_authority_registry_sha256,
  family_definition_record_id,
  family_definition_record_version,
  family_definition_schema_version,
  family_definition_canonicalization_id,
  family_definition_record_sha256
)
```

The resolver must return the complete canonical record bytes. It must verify
the pinned catalog digest, exact record schema, canonical bytes, and record
digest before use. A retrieval miss, ambiguous record, digest mismatch,
schema mismatch, noncanonical record, or hash-only stand-in fails closed.

The external `trial_family_definition_v1` record must bind:

- the exact authority and record tuple above;
- the exact `trial_family_id`;
- one immutable definition issuer actor reference;
- the global multiplicity/dependence-family meaning;
- a record version and optional exact predecessor under the sole
  `supersedes` definition-generation relation;
- a sorted-unique finite set of distinct `trial_family_id` references under
  the sole cross-family relation `depends_on`, whose exact maximum is fixed by
  the digest-pinned authority catalog schema rather than this event registry;
  and
- no `independent_of`, alias, free-text relation, open metadata, URI, path, or
  executable predicate.

The direct-registration maximum of 32 campaign IDs is not silently reused as a
family-dependence cardinality. Any such bound belongs to the immutable external
authority schema and must be verified through the pinned catalog digest.

## Separate Acceptance and Reviewer Independence

The registration pins a separate complete acceptance record by:

```text
family_acceptance_decision_id
family_acceptance_generation
family_acceptance_schema_version
family_acceptance_record_sha256
```

The accepted resolver key is the exact pinned family-definition tuple plus
those four acceptance fields. The resolver must return complete canonical
`trial_family_definition_acceptance_v1` bytes and verify their schema,
canonicalization, and digest.

The acceptance record must bind:

- the exact authority catalog and family-definition tuple;
- the exact `trial_family_id`;
- the exact global or direct `campaign_scope_ids`;
- one definition issuer actor reference;
- one reviewer actor reference;
- the outcome `accepted`;
- the exact generation;
- an optional predecessor decision under explicit `supersedes`; and
- the decision's canonical bytes and SHA-256.

For formal use, the reviewer must be distinct from both the definition issuer
and the `TRIAL_FAMILY_REGISTERED.actor_id`. R1C shape validation cannot prove
that inequality or authenticate any actor. A later stateful authority must
verify the three roles and permission. Until then, authority-dependent runtime
behavior remains fail closed.

## Anti-Reset and Currentness Policy

The provider-neutral currentness key is exactly:

```text
(family_authority_id, trial_family_id)
```

Acceptance generations are positive safe integers and strictly increase. Once
a family has an accepted generation, exactly one accepted generation is
current. Formal registration and use require that the sole current generation
exists, has outcome `accepted`, binds the exact definition record and scope,
and is not superseded.

Currentness must be checked:

1. immediately before `TRIAL_FAMILY_REGISTERED` append;
2. before every later `TRIAL_ALLOCATED`;
3. at every attempt execution boundary; and
4. at every protected-access boundary.

If a decision is superseded after an earlier event, the historical event
remains immutable, but no later action may treat the old decision as current.

The global multiplicity family identity is stable. Aliases, clones, reruns,
new campaign IDs, result exposure, and post-result reclassification must reuse
the same `trial_family_id`; they cannot allocate a new family to reset prior
trial count or dependence. Definition revisions keep the same
`trial_family_id` and advance through `supersedes`. Genuinely distinct but
dependent families use explicit `depends_on`. No record may self-certify
independence.

These rules require stateful history and an external currentness authority.
They are not local registry predicates and R1C does not implement them.

## Required Killing Evidence

R1C must include independent evidence for:

- byte-exact R0 and R1B artifacts, digests, behavior, and package resources;
- explicit selection of packaged registry `0.3.0`;
- the exact four-event supported set and 33-event incomplete partition;
- independent global and direct positive fixtures;
- every missing payload and envelope field;
- every nested/top-level unknown and raw duplicate property;
- wrong `subject_type`, wrong `fam_` namespace, and duplicated subject fields;
- unsorted, duplicate, wrong-prefix, 33-item, and wrong-type campaign scope;
- unsafe authority/record/decision IDs;
- zero, negative, Boolean, noninteger, and unsafe versions/generations;
- uppercase, wrong-length, and non-string digests;
- wrong definition, acceptance, and canonicalization versions;
- a shape-valid event whose resolver record is missing, explicitly documented
  as a later stateful fail-closed case rather than local `ACCEPT` evidence;
- stale/superseded acceptance, self-review, issuer-reviewer equality,
  registration-actor equality, alias reset, clone reset, rerun reset,
  new-campaign reset, reclassification reset, and false independence,
  explicitly reserved for the later stateful runtime suite; and
- arbitrary self-consistent unpublished event promotion rejected by packaged
  digest authority.

The independent fixture must not be generated from the registry artifact.
Literal tests must not discover expected fields, namespace, supported events,
or outcome codes from the implementation under test.

## Non-Goals

R1C does not:

- append, store, allocate, register, retrieve, resolve, accept, supersede,
  authenticate, authorize, or execute anything;
- select a backend, object store, database, private ledger path, signature
  scheme, or recovery mechanism;
- promote `SAMPLE_REGISTERED`, either binding event, `TRIAL_ALLOCATED`, or any
  lifecycle/access/review/adjudication event;
- copy private family definitions or performance values into the repository;
- run a campaign, trial, attempt, protected access, factor, backtest, or
  historical interpretation; or
- add paper, brokerage, order, live, or real-money behavior.

Trial count, execution-attempt count, and protected-sample access remain zero.

## Next Gate

After R1C is accepted on protected main, R1D must separately select the exact
sample namespace, Stage 3 sample authority, local/external sample registration,
alias/currentness policy, privacy projection, and event schemas. Any genuine
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

### Complete tuple paths

Every field retains its exact baseline local type. Ordered tuples use the order
below; nested objects compare all native keys and values. Acceptance, approval
and authority resolution also includes the complete owning catalog/subject key.
Identical IDs in different owner/schema streams do not merge those streams.

| Tuple | Retained source paths (all fields) |
| --- | --- |
| `family_catalog_key` | `TRIAL_FAMILY_REGISTERED.payload.family_authority_id`, `TRIAL_FAMILY_REGISTERED.payload.family_authority_version`, `TRIAL_FAMILY_REGISTERED.payload.family_authority_registry_sha256`, `TRIAL_FAMILY_REGISTERED.payload.family_definition_record_id`, `TRIAL_FAMILY_REGISTERED.payload.family_definition_record_version`, `TRIAL_FAMILY_REGISTERED.payload.family_definition_schema_version`, `TRIAL_FAMILY_REGISTERED.payload.family_definition_canonicalization_id`, `TRIAL_FAMILY_REGISTERED.payload.family_definition_record_sha256` |
| `family_acceptance` | `TRIAL_FAMILY_REGISTERED.payload.family_acceptance_decision_id`, `TRIAL_FAMILY_REGISTERED.payload.family_acceptance_generation`, `TRIAL_FAMILY_REGISTERED.payload.family_acceptance_schema_version`, `TRIAL_FAMILY_REGISTERED.payload.family_acceptance_record_sha256` |

### Resolved role paths and content bindings

Actor fields use the existing `actor_id` type and resolve to effective
principals before comparison; aliases do not establish independence.
`private_input_producer_actor_ids` is required, sorted-unique, with 0..4096
`actor_id` values. Empty explicitly means no contributing private producer;
omission is invalid. This is an owner-schema extension, not a bound inherited
from campaign scope. Overflow blocks admission pending an owner decision.
The full baseline record contents and canonical bytes remain required; these
paths never replace complete records with partial hash manifests.

| Complete record | Required path | Meaning |
| --- | --- | --- |
| `trial_family_definition_v1` | `issuer_actor_id` | Definition issuer |
| `trial_family_definition_v1` | `private_input_producer_actor_ids` | Contributing producers |
| `trial_family_definition_acceptance_v1` | `issuer_actor_id` | Equals definition issuer |
| `trial_family_definition_acceptance_v1` | `reviewer_actor_id` | Independent reviewer |

At registration, definition issuer, acceptance reviewer and request actor are
pairwise distinct. Revalidation uses the retained registration tuples, binds
`trial_family_id` to its subject and `campaign_scope_ids` to its accepted scope,
proves source bytes and checks sole-current acceptance. The reviewer must be
outside the definition's producer set. Subject/scope/issuer mismatch maps to
`RECORD_CONTENT_MISMATCH`; role equalities and producer membership map separately
to `{EVENT}_ROLE_COLLISION` and `{EVENT}_PRIVATE_INPUT_PRODUCER_ROLE_COLLISION`.
The consuming event qualifies the refusal, including downstream revalidation.

The [v7 design](experiment_trial_ledger_track_b_v7_design.md) freezes the boundary predicates and refusal
inventory. Its synthetic fixtures check design consistency; they do not
demonstrate append, catalog, currentness, capability or SQLite execution.

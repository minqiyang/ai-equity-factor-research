# Experiment and Trial Ledger Campaign Inventory Seal R1G Contract

Contract ID: `experiment_trial_ledger_campaign_inventory_seal_schema_r1g`.

Contract version: `0.7.0`.

Owner decision: option `R1G-A`.

This document is the design authority for the bounded Stage 4B-R1G initial
campaign-inventory-seal release under:

- `docs/research_program_charter.md`;
- `docs/point_in_time_data_methodology_contract.md`;
- `docs/experiment_trial_ledger_contract.md`;
- `docs/experiment_trial_ledger_schema_registry_contract.md`;
- `docs/experiment_trial_ledger_allocation_registration_schema_contract.md`;
- `docs/experiment_trial_ledger_trial_family_registration_schema_contract.md`;
- `docs/experiment_trial_ledger_sample_registration_schema_contract.md`;
- `docs/experiment_trial_ledger_binding_schema_contract.md`; and
- `docs/experiment_trial_ledger_trial_allocation_schema_contract.md`.

Its publication state is determined by protected-main history and
`docs/current_handoff.md`, not by a status claim inside this document.

## Release Boundary

R1G publishes one new immutable registry release:

- registry schema ID
  `experiment_trial_ledger_payload_schema_registry_v7`;
- registry version `0.7.0`;
- unchanged schema-language ID `ledger_closed_schema_dsl_v1`;
- unchanged schema-language version `0.2.0`; and
- a separate packaged JSON artifact and SHA-256 sidecar.

R1G preserves the accepted 37-event vocabulary. Its supported event set is
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
```

The other 28 events remain
`SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`. R1G does not overwrite, reinterpret, or
silently upgrade immutable registry releases `0.1.0` through `0.6.0`, their
digests, the default R0 entry point, or prior validator outcomes.

Registry acceptance proves only the closed local shape and literal syntax of a
candidate event. It does not prove that a parent event exists, that an external
inventory record is retrievable, that retained source bytes match a digest,
that reviewers are independent, that authority/currentness is valid, that the
inventory is complete, that the predecessor is the retained stream head, that
the seal is unique, that an append is atomic or durable, or that any research
computation or protected access occurred.

## Exact Event Identity And Payload

`CAMPAIGN_INVENTORY_SEALED` creates no new campaign or trial identity. It
records the one initial immutable inventory seal for an existing campaign. It
has:

- `event_type` exactly `CAMPAIGN_INVENTORY_SEALED`;
- `subject_type` exactly `campaign`;
- `subject_id` exactly the already allocated `campaign_id`;
- one-item sorted-unique `payload.campaign_scope_ids` containing that same
  campaign ID;
- one exact earlier campaign-allocation event ID and hash;
- one complete external campaign-inventory record tuple;
- one separate inventory-acceptance tuple;
- one separate seal-actor authority tuple;
- one exact sealed semantic-trial count from 1 through 4096; and
- one nested nonrecursive `campaign_inventory_preseal_head_v1`.

The event payload contains exactly:

```text
campaign_allocation_event_id
campaign_allocation_event_sha256
campaign_scope_ids
inventory_acceptance_decision_id
inventory_acceptance_generation
inventory_acceptance_record_sha256
inventory_acceptance_schema_version
inventory_authority_id
inventory_authority_registry_sha256
inventory_authority_version
inventory_record_canonicalization_id
inventory_record_id
inventory_record_schema_version
inventory_record_version
preseal_head
seal_authority_generation
seal_authority_id
seal_authority_record_sha256
seal_authority_schema_version
sealed_semantic_trial_count
sealed_trial_inventory_sha256
```

Missing, null, unknown, duplicate, wrong-type, unsafe, or additional fields
fail closed. Campaign identity is not redundantly copied into the payload
outside `campaign_scope_ids`; the exact subject/scope relation is enforced by
the registry's closed `array_contains_path` predicate.

## Complete Canonical Inventory Record

The complete `campaign_inventory_record_v1` is repository-external and private
by default. The seal pins it using:

| Field | Exact local schema |
| --- | --- |
| `inventory_authority_id` | `safe_public_id` |
| `inventory_authority_registry_sha256` | lowercase SHA-256 |
| `inventory_authority_version` | I-JSON safe integer, minimum 1 |
| `inventory_record_canonicalization_id` | literal `pit_canonical_json_v1` |
| `inventory_record_id` | `safe_public_id` |
| `inventory_record_schema_version` | literal `campaign_inventory_record_v1` |
| `inventory_record_version` | I-JSON safe integer, minimum 1 |
| `sealed_trial_inventory_sha256` | lowercase SHA-256 of the complete canonical record bytes |
| `sealed_semantic_trial_count` | I-JSON safe integer, minimum 1, maximum 4096 |

Schema-language `0.2.0` has no integer-maximum keyword. To preserve that
language byte-for-byte while enforcing the selected bound locally,
`sealed_semantic_trial_count` is the closed enum of every integer from 1
through 4096 in canonical-byte order. This is an encoding of the finite bound,
not an extension of the DSL or a methodological recommendation.

The authority is an immutable versioned catalog. Retrieval uses the exact
tuple:

```text
(inventory_authority_id,
 inventory_authority_registry_sha256,
 inventory_authority_version,
 inventory_record_id,
 inventory_record_schema_version,
 inventory_record_version,
 inventory_record_canonicalization_id,
 sealed_trial_inventory_sha256)
```

A catalog miss, record miss, version mismatch, changed bytes, digest mismatch,
unknown schema, stale generation, or ambiguous result fails closed. A hash-only
placeholder is not a complete record.

The exact `campaign_inventory_record_v1` complete record binds:

- the ledger and campaign identities and exact campaign-allocation source;
- an ordered all-and-only set of 1 through 4096 semantic trial entries;
- for every entry, the exact `trial_id`, earlier `TRIAL_ALLOCATED` event ID and
  event SHA-256, trial-definition record ID/version/SHA-256, experiment ID,
  global trial-family ID, relation, sample-binding set identity, selection
  role, expected artifact roles, and trial-budget accounting;
- all experiment and global trial-family relations across the campaign;
- the complete allowed variation axes and the exact planned-trial budget;
- every sample identity, role, classification, exact window reference, legal
  local/global/external origin path, and protected-access budget;
- frozen review, promotion, statistical, timing, split, benchmark, risk-free,
  cost, slippage, capacity, execution, artifact, access, and privacy policy
  references;
- every identity-bearing default and canonical collection-order rule; and
- its authority, schema, record version, issuance time, and supersession state.

Every trial entry must resolve to an earlier exact retained
`TRIAL_ALLOCATED` event in the same ledger epoch and campaign. The complete
record's count must equal `sealed_semantic_trial_count`; the set and order must
equal the all-and-only intended campaign inventory. Equal counts never
substitute for exact set equality, source-event equality, definition equality,
or currentness.

The maximum of 4096 semantic trials is a schema/review bound, not permission or
methodological evidence that a campaign should use that many trials. A larger
campaign requires a versioned owner decision and new registry release; it must
not be truncated, sharded behind aliases, or silently represented as several
initial seals.

## Inventory Acceptance And Role Independence

One separate immutable acceptance record is pinned by:

| Field | Exact local schema |
| --- | --- |
| `inventory_acceptance_decision_id` | `safe_public_id` |
| `inventory_acceptance_generation` | I-JSON safe integer, minimum 1 |
| `inventory_acceptance_record_sha256` | lowercase SHA-256 |
| `inventory_acceptance_schema_version` | literal `campaign_inventory_acceptance_v1` |

The acceptance record binds the exact authority/catalog/record tuple, complete
inventory digest and count, campaign allocation source, policy references,
scope, and pre-seal eligibility decision. Its reviewer must be distinct from:

- the inventory-record issuer;
- the seal actor;
- every trial-definition issuer whose record is accepted into the inventory;
  and
- any actor whose private record supplies an identity-bearing input to the
  acceptance decision.

One separate seal-actor authority record is pinned by:

| Field | Exact local schema |
| --- | --- |
| `seal_authority_id` | `safe_public_id` |
| `seal_authority_generation` | I-JSON safe integer, minimum 1 |
| `seal_authority_record_sha256` | lowercase SHA-256 |
| `seal_authority_schema_version` | literal `campaign_inventory_seal_authority_v1` |

The authority is current for the exact actor, ledger, campaign, inventory
tuple, scope, and operation immediately before append. The envelope
`actor_id` remains claimed attribution; the authority tuple is the separately
retrievable authorization evidence. Local schema acceptance proves neither
retrieval nor role independence.

## Exact Nonrecursive Pre-Seal Anchor

`payload.preseal_head` is one closed object with all-and-only:

```text
anchor_schema_version
ledger_id
predecessor_event_sha256
predecessor_sequence
```

Its literal schema version is `campaign_inventory_preseal_head_v1`.
`ledger_id` exactly equals the envelope `ledger_id`.
`predecessor_event_sha256` exactly equals the envelope
`previous_event_sha256`. `predecessor_sequence` is a nonnegative I-JSON-safe
integer naming the concrete retained predecessor. Half-null or epoch-empty
anchor forms are not representable.

Stateful append validation must, at one serialized atomic commit boundary:

1. retrieve and validate the exact current inventory, acceptance, and seal
   authority records;
2. prove every inventory trial and parent source exists earlier and is current;
3. compare the complete retained stream head with the exact nested
   `(ledger_id, predecessor_sequence, predecessor_event_sha256)` tuple;
4. require the seal sequence to equal `predecessor_sequence + 1`;
5. assign the envelope previous hash equal to that predecessor hash; and
6. commit exactly one initial seal or commit nothing.

The anchor is inside the operation-request/event preimage. It never names the
seal sequence or seal hash and is therefore nonrecursive. If another append
wins first, any source changes, the retained stream is truncated or replaced,
or the append fails, the seal fails without silent rebasing. Exact replay of
the same operation returns the prior result and creates no second seal.

The unchanged schema language has equality and containment predicates but no
arithmetic predicate. R1G locally proves nested-ledger equality,
previous-hash equality, and subject/scope membership. Exact
`sequence = predecessor_sequence + 1`, current-head comparison, retrieval,
ordering, and atomicity remain mandatory stateful checks and are not
represented as local schema `ACCEPT`.

## Single Initial Seal And Later Amendments

Exactly one initial `CAMPAIGN_INVENTORY_SEALED` is legal for a campaign.
Every listed trial is allocated before the seal. No attempt allocation,
protected-access intent, validation, execution, artifact production, or
result inspection may precede it.

After the initial seal, a new trial cannot be inserted by issuing another
initial seal, changing the external record, changing a digest, changing an
alias, or starting a new acceptance generation. A later addition must use the
separately reviewed `CAMPAIGN_AMENDMENT_PROPOSED` and
`CAMPAIGN_INVENTORY_AMENDED` events:

```text
CAMPAIGN_AMENDMENT_PROPOSED
CAMPAIGN_INVENTORY_AMENDED
```

family in the accepted reservation order. Those events remain
`SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY` in R1G. Result-informed amendments retain
their exposure consequences and cannot reset multiplicity, sample history, or
promotion eligibility.

## Required Killing Evidence

R1G must include independent evidence for:

- byte-exact R0 through R5 artifacts, digests, behavior, and package resources;
- explicit packaged registry `0.7.0` selection and unchanged default R0;
- exact nine-event supported and 28-event incomplete partitions;
- independent standard-count and maximum-count positive fixtures;
- exact campaign subject, singleton scope, and subject/scope equality;
- every missing, unknown, duplicate, null, and wrong-type envelope, payload,
  and nested pre-seal field;
- wrong campaign, ledger, event, digest, safe-public-ID, version, generation,
  count, canonicalization, authority, acceptance, and schema literals;
- trial counts 0, 4097, Boolean, floating, textual, null, and non-I-JSON-safe;
- pre-seal wrong-ledger and previous-hash mismatches rejected locally;
- shape-valid wrong predecessor sequence, stale source, incomplete inventory,
  duplicate initial seal, self-reviewed acceptance, unauthorized actor,
  changed external bytes, post-trial/action seal, and concurrent-head drift
  documented as statefully fail closed rather than local `ACCEPT` evidence;
- every nonpromoted and unknown event rejected before action; and
- arbitrary self-consistent unpublished promotion rejected by packaged digest
  authority.

The independent fixture must not be generated from the registry artifact.
Literal tests must not discover expected fields, limits, authority names,
supported events, or outcome codes from the implementation under test.
Synthetic fixture IDs and digest strings prove syntax only; they are not
private records, campaign evidence, or research results.

## Non-Goals

R1G does not:

- append, store, retrieve, seal, authorize, authenticate, accept, approve,
  amend, allocate an attempt, validate, execute, access, review, or promote
  anything;
- implement inventory, acceptance, or authority catalogs;
- select a backend, private ledger path, transaction/recovery policy,
  signature mechanism, provider, dataset, strategy, factor, or statistical
  method;
- promote amendment, attempt, lifecycle, access, artifact, closure, review,
  decision, adjudication, or supersession events;
- copy private records, paths, raw values, or performance values into the
  repository;
- run a campaign, trial, attempt, protected access, factor, backtest, report,
  or historical interpretation; or
- add paper, brokerage, order, live, or real-money behavior.

Trial execution count, attempt count, and protected-sample access remain zero.

## Next Gate

The transition out of R1G required a read-only dependency/risk analysis over
the remaining 28 incomplete events. That analysis selected
`ATTEMPT_ALLOCATED` as the smallest strict compute-path prerequisite; the
owner selected the bounded successor in
`docs/experiment_trial_ledger_attempt_allocation_schema_contract.md`.
R1H publishes a separate immutable registry `0.8.0`, promotes only
`ATTEMPT_ALLOCATED`, and does not reinterpret this R1G authority. After R1H is
accepted on protected main, the next analysis covers the remaining 27
incomplete events before the smallest next family is selected. A genuinely
material architecture choice receives a concise owner memo and the bounded
reminder policy; otherwise continuation remains automatic.

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
| `inventory_catalog_key` | `CAMPAIGN_INVENTORY_SEALED.payload.inventory_authority_id`, `CAMPAIGN_INVENTORY_SEALED.payload.inventory_authority_registry_sha256`, `CAMPAIGN_INVENTORY_SEALED.payload.inventory_authority_version`, `CAMPAIGN_INVENTORY_SEALED.payload.inventory_record_id`, `CAMPAIGN_INVENTORY_SEALED.payload.inventory_record_schema_version`, `CAMPAIGN_INVENTORY_SEALED.payload.inventory_record_version`, `CAMPAIGN_INVENTORY_SEALED.payload.inventory_record_canonicalization_id`, `CAMPAIGN_INVENTORY_SEALED.payload.sealed_trial_inventory_sha256` |
| `inventory_acceptance` | `CAMPAIGN_INVENTORY_SEALED.payload.inventory_acceptance_decision_id`, `CAMPAIGN_INVENTORY_SEALED.payload.inventory_acceptance_generation`, `CAMPAIGN_INVENTORY_SEALED.payload.inventory_acceptance_schema_version`, `CAMPAIGN_INVENTORY_SEALED.payload.inventory_acceptance_record_sha256` |
| `inventory_authority` | `CAMPAIGN_INVENTORY_SEALED.payload.seal_authority_id`, `CAMPAIGN_INVENTORY_SEALED.payload.seal_authority_generation`, `CAMPAIGN_INVENTORY_SEALED.payload.seal_authority_schema_version`, `CAMPAIGN_INVENTORY_SEALED.payload.seal_authority_record_sha256` |

### Resolved role paths and content bindings

Actor fields use the existing `actor_id` type and resolve to effective
principals before comparison; aliases do not establish independence.
`private_input_producer_actor_ids` is required, sorted-unique, with 0..4096
`actor_id` values. Empty explicitly means no contributing private producer;
omission is invalid. This is an owner-schema extension, not a bound inherited
from campaign scope. Overflow blocks admission pending an owner decision.
The full baseline record contents and canonical bytes remain required; these
paths never replace complete records with partial hash manifests.

| Principal | Exact source |
| --- | --- |
| `inventory_issuer` | `campaign_inventory_record_v1.issuer_actor_id` |
| `inventory_reviewer` | `campaign_inventory_acceptance_v1.reviewer_actor_id` |
| `seal_authority_issuer` | `campaign_inventory_seal_authority_v1.issuer_actor_id` |
| `seal_actor` | `CAMPAIGN_INVENTORY_SEALED request.actor_id` |
| `authorized_seal_actor` | `campaign_inventory_seal_authority_v1.authorized_actor_id` |
| `private_input_producers` | `campaign_inventory_record_v1.private_input_producer_actor_ids` |

Seal actor equals authorized seal actor; otherwise
`CAMPAIGN_INVENTORY_SEALED_AUTHORITY_ACTOR_MISMATCH`. Independently prohibit
reviewer=issuer, reviewer=seal-authority issuer, reviewer=seal actor and
inventory issuer=seal actor, each mapping to
`CAMPAIGN_INVENTORY_SEALED_ROLE_COLLISION`. Reviewer membership in the producer
set maps separately to
`CAMPAIGN_INVENTORY_SEALED_PRIVATE_INPUT_PRODUCER_ROLE_COLLISION`.
The baseline prohibition against reviewer equality with any included trial's
definition issuer also remains mandatory. Seal-authority issuer may equal its
authorized seal actor when that authority explicitly binds the actor.

Freeze source paths as `trials[].trial_id`, `trials[].trial_allocation_event_id`
and `trials[].trial_allocation_event_sha256`, preserving the baseline 1..4096
ordered all-and-only inventory and complete entry bodies. Revalidate every
definition, family and sample; current inventory acceptance does not waive
parent currentness. Bind campaign/allocation/scope and exact pre-seal head
inside the writer lock. The complete inventory byte digest remains
`sealed_trial_inventory_sha256`, never an `inventory_record_sha256` alias.

The [v7 design](experiment_trial_ledger_track_b_v7_design.md) freezes the boundary predicates and refusal
inventory. Its synthetic fixtures check design consistency; they do not
demonstrate append, catalog, currentness, capability or SQLite execution.

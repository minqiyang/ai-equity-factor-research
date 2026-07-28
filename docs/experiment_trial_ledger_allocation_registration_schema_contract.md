# Experiment and Trial Ledger Allocation/Registration R1A Contract

Contract ID:
`experiment_trial_ledger_allocation_registration_schema_r1a`.

Contract version: `0.1.0`.

Owner decision: architecture `A`.

This document records the design-first Stage 4B-R1A decision under the accepted
`docs/experiment_trial_ledger_contract.md` and the protected-main
`docs/experiment_trial_ledger_schema_registry_contract.md`. Its publication
state is determined by protected-main history and `docs/current_handoff.md`,
not by a claim inside this document.

R1A selects the versioned minimal architecture for the allocation and
registration event family. It does not add an event schema, change packaged
registry bytes, or implement a ledger runtime. No event becomes append-valid in
R1A. `LEDGER_EPOCH_CREATED` remains the sole `FROZEN_SUPPORTED` event, and the
other 36 known event types remain
`SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.

## Evidence State and Non-Authorization

R1A is a design decision, not payload-registry acceptance. It freezes:

- immutable coexistence of the R0 and future R1 authorities;
- retention of the accepted 37-event vocabulary;
- reservation-only campaign and experiment allocation;
- entity-as-subject identity, exact subject types, and the accepted campaign
  namespace for the six-event family;
- explicit campaign-scope representation and direct-scope ordering policy;
- the closed schema-language additions required by later event schemas;
- requirements for future reference-based family and Stage 3 sample
  authorities; and
- the local-shape versus stateful-ledger enforcement boundary.

R1A does not establish:

- an exact wire schema for any of the six events;
- a complete payload-schema registry;
- append-only storage, allocation, uniqueness, ordering, recovery, or
  concurrency behavior;
- an accepted family-definition authority or Stage 3 sample-registry
  authority;
- actor authentication, authorization, signatures, capability security, or
  checkpoint latestness;
- a physical backend or private ledger location;
- a campaign, trial, attempt, sample access, dataset review, or historical
  interpretation; or
- LEAN, paper, brokerage, order, live, or real-money behavior.

Trial count, execution-attempt count, and protected-sample access remain zero.
No private path, private data digest, performance value, factor result, or
research outcome is introduced by this contract.

## R0 Registry Artifact Identity and Behavioral Authority

The accepted R0 registry artifact identity remains immutable:

- `src/ledger/schemas/experiment_trial_ledger_payload_schema_registry_v1.json`;
- its external SHA-256 sidecar;
- registry version `0.1.0`; and
- schema-language version `0.1.0`.

The accepted R0 behavioral authority also includes
`src/ledger/schema_registry.py` and `tests/test_ledger_schema_registry.py`. A
later implementation must preserve both R0 artifact files byte-for-byte and
preserve every accepted R0 validator behavior and literal test oracle. A
shared validator module may evolve only through explicit version dispatch
that leaves the R0 path and its outcomes unchanged; a separate versioned
implementation path is also permitted.

R1B must add a separate R1 registry artifact and sidecar with registry version
`0.2.0` and schema-language version `0.2.0`. It must not rewrite, replace,
reinterpret, or silently upgrade the R0 preimage or behavioral authority.

Validation authority must be selected explicitly by packaged registry version
and expected digest. A compatibility entry point may remain bound to R0, but it
must not silently begin validating R1 events. A caller-supplied self-consistent
registry remains non-authoritative unless its exact packaged version and digest
are accepted by a separately reviewed release.

R0 and R1 validation must coexist in source trees, sdists, and wheels. Tests
must prove:

- the R0 artifact and sidecar are unchanged;
- the accepted R0 epoch bytes and event hash are unchanged;
- R0 continues to reject every event candidate newly supported only by R1;
- R1 validates only schemas explicitly frozen in its own authority; and
- arbitrary caller promotion remains rejected.

Every protected-merged registry release is immutable. R1B publishes registry
version `0.2.0`; each later schema-promotion batch must publish a separate,
monotonically newer registry artifact, version, sidecar, and digest rather than
overwrite an earlier R1 artifact. The exact later registry version is assigned
by that batch's accepted design contract. Schema-language version `0.2.0` may
remain unchanged when its semantics are unchanged; any semantic addition or
reinterpretation requires a new schema-language version.

## Closed Event Vocabulary

Architecture A retains the accepted 37-event vocabulary unchanged. R1A neither
adds nor splits an event type.

In particular, `CAMPAIGN_ENTITY_BOUND` remains one event with closed,
discriminator-dependent trial-family and sample variants. It must not be
replaced with two vocabulary events, represented by a generic entity ID, or
approximated with two nullable fields.

The allocation/registration family remains exactly:

```text
CAMPAIGN_ALLOCATED
EXPERIMENT_ALLOCATED
TRIAL_FAMILY_REGISTERED
SAMPLE_REGISTERED
CAMPAIGN_ENTITY_BOUND
STAGE3_SAMPLE_REFERENCE_BOUND
```

`TRIAL_ALLOCATED` and every later family remain outside this decision.

## Reservation-Only Allocation

`CAMPAIGN_ALLOCATED` and `EXPERIMENT_ALLOCATED` reserve typed logical entity
IDs and their immediate campaign scope only. They do not carry objective,
hypothesis, estimand, protocol, budget, sample policy, threshold, inventory,
status, reason, metadata, or free-text fields.

Their exact reservation payload field set is:

```text
campaign_scope_ids
```

The forbidden definition-bearing or open-ended field categories are exactly:

```text
objective
hypothesis
estimand
protocol
budget
sample_policy
threshold
inventory
status
reason
metadata
free_text
```

The complete campaign definition, ordered trial inventory, policies,
thresholds, and experiment definitions must be frozen by later exact,
schema-bound campaign inventory events before any execution attempt or
protected access. Reservation does not satisfy preregistration and cannot be
used to claim a runnable campaign.

This separation prevents an allocation event from containing a partial
definition that later code mistakes for a frozen research protocol. It also
avoids a hash-only definition stand-in.

## Entity Subjects and Namespace Decisions

The allocated, registered, or bound logical entity is the event subject. The
following subject and namespace decisions are frozen for later exact schemas.
Only the campaign prefix is already accepted. R1A does not infer the
experiment, trial-family, or sample prefix from documentation helpers or
rejected fixtures:

| Event | Exact subject type | Subject ID role | Namespace status |
| --- | --- | --- | --- |
| `CAMPAIGN_ALLOCATED` | `campaign` | newly reserved `campaign_id` | accepted `cmp_<32 lowercase hex>` |
| `EXPERIMENT_ALLOCATED` | `experiment` | newly reserved `experiment_id` | exact prefix deferred to the R1B owner gate |
| `TRIAL_FAMILY_REGISTERED` | `trial_family` | newly registered `trial_family_id` | exact prefix deferred to the R1C owner gate |
| `SAMPLE_REGISTERED` | `sample` | newly registered local `sample_id` | exact prefix deferred to the R1D owner gate |
| `CAMPAIGN_ENTITY_BOUND` | `trial_family` or `sample` | existing global entity identity | must match the later accepted family or sample namespace |
| `STAGE3_SAMPLE_REFERENCE_BOUND` | `sample` | newly allocated ledger-local `sample_id` | exact prefix deferred to the R1D owner gate |

Subject IDs must not be duplicated in payload merely to restate identity.
Where a nested reference repeats an entity identity, a later exact schema must
bind that equality with a reviewed local constraint or leave it solely as a
stateful source-record check; it may not rely on prose.

No event may use a generic entity-ID namespace. A later prefix decision is a
human methodology decision and must be ratified before its event is promoted.

The `actor_id` in the common envelope remains external claimed attribution. It
is not a ledger-owned allocation, does not authenticate the actor, and grants
no permission.

## Explicit Campaign Scope

Every event in this family will place `campaign_scope_ids` directly in its
top-level payload. Scope must never be inferred retrospectively from later
events.

The scope formulas are:

| Event or path | Exact semantic scope |
| --- | --- |
| `CAMPAIGN_ALLOCATED` | one-item array containing `subject_id` |
| `EXPERIMENT_ALLOCATED` | one-item array containing the sole parent campaign ID |
| direct `TRIAL_FAMILY_REGISTERED` | nonempty sorted-unique array of all directly covered campaigns |
| global `TRIAL_FAMILY_REGISTERED` | empty array |
| direct `SAMPLE_REGISTERED` | nonempty sorted-unique array of all directly covered campaigns |
| global `SAMPLE_REGISTERED` | empty array |
| `CAMPAIGN_ENTITY_BOUND` | one-item array containing the binding campaign ID |
| `STAGE3_SAMPLE_REFERENCE_BOUND` | one-item array containing the binding campaign ID |

The experiment parent campaign is represented only by its singleton
`campaign_scope_ids`; there is no redundant payload `campaign_id`.

For a direct registration, every campaign listed in `campaign_scope_ids` must
already be allocated before the registration is appended. Architecture A
retains shared direct registration, but forbids pre-filling a future campaign
and legitimizing the scope through later allocation. The finite maximum
cardinality for a shared direct registration remains a required exact-schema
decision; until it is frozen, both registration events remain incomplete.

A ledger-global registration and a campaign allocation are independent
siblings after the epoch. Both must precede a later campaign binding. These
stateful partial-order rules do not become shape-validation claims.

## Schema Language Version 0.2.0

The future R1 authority will extend the closed R0 schema language in one
versioned amendment. It will add only these capabilities:

```text
tagged_union
array_contains_path
safe_public_id
```

### `tagged_union`

A `tagged_union` node has:

- one required discriminator property;
- two or more explicitly named closed variants;
- one exact literal discriminator value per variant;
- one and only one selected branch; and
- no fields from an unselected or unknown branch.

Missing, null, unknown, duplicated, or mismatched discriminators fail closed.
The validator must not try all branches and accept the first coercible result.
`CAMPAIGN_ENTITY_BOUND` will use this construct so `trial_family` selects the
later accepted trial-family identity/source branch and `sample` selects the
later accepted sample branch.

### `array_contains_path`

The `array_contains_path` predicate compares one resolved array with one
resolved scalar path using type-sensitive JSON equality. Registry
meta-validation must prove:

- the array path resolves to a non-null array;
- the scalar schema is compatible with the array item schema; and
- both paths exist in every applicable closed branch.

Combined with `min_items = 1` and `max_items = 1`, it expresses exact singleton
membership. `CAMPAIGN_ALLOCATED` will use it to bind `subject_id` to
`payload.campaign_scope_ids`.

Constraint paths remain ordered path components; repeated property names in a
nested path are legal. Path components must not be subjected to a
collection-uniqueness rule.

### `safe_public_id`

`safe_public_id` is a parameter-free ASCII scalar with length 1 through 128 and
the exact grammar:

```text
[a-z0-9](?:[a-z0-9._-]{0,126}[a-z0-9])?
```

It rejects uppercase, whitespace, slash, backslash, colon, query or fragment
delimiters, percent escapes, `@`, non-ASCII, and path-like or URI-like values.
It is a syntactic reference token only; it does not establish existence,
authority, acceptance, currentness, or publication approval.

No generic object, free string, opaque metadata, executable predicate,
implicit default, coercion, open union, file/network reference, or hash-only
semantic object is added.

## First Implementable Batch: R1B

After R1A is accepted, the first implementation batch may promote only
`CAMPAIGN_ALLOCATED` and `EXPERIMENT_ALLOCATED` in the separate R1 registry.
The R1 registry will then contain three supported events and 34 incomplete
events, so its overall status remains
`SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.

Both events inherit the exact 18-field Stage 4A common envelope. They require:

- their exact event and subject literals from this contract;
- the accepted campaign namespace and an owner-ratified exact experiment
  namespace;
- non-Boolean safe-integer sequence greater than zero;
- non-null lowercase `previous_event_sha256`;
- the accepted ledger, event, operation, actor, canonicalization, timestamp,
  and request-digest types; and
- an all-and-only payload containing non-null `campaign_scope_ids`.

`CAMPAIGN_ALLOCATED` requires:

- one and only one scope item;
- scope item type `campaign_id`; and
- `subject_id` contained in that singleton array.

`EXPERIMENT_ALLOCATED` requires:

- one and only one scope item of type `campaign_id`; and
- no additional payload field.

Campaign existence, experiment parent existence, uniqueness, exact sequence
continuity, previous-hash truth, request-digest truth, authorization, and
definition-before-action remain stateful runtime checks.

R1B must implement and meta-test all three closed schema-language `0.2.0`
capabilities even though its promoted allocation schemas use only
`array_contains_path`. Independent killing tests must cover both
`tagged_union` branches and rejection of unknown, mixed, both, and neither
branches, plus every `safe_public_id` grammar boundary and forbidden
character. Later batches may use these accepted semantics but may not silently
complete or reinterpret them under the same schema-language version.

R1B must not promote the four registration/binding events, implement append,
or select a backend. It remains blocked until the exact experiment ID
namespace is ratified.

## Family Definition Reference Architecture

Architecture A selects the requirement for an immutable, exact, versioned
family-definition reference rather than an inline free-form definition. It
does not accept a concrete family authority.

A later family authority contract must freeze a closed reference graph that
binds:

- authority ID, authority version, canonicalization ID, and authority registry
  digest;
- family-definition record ID, schema version, canonical bytes, and record
  digest;
- exact retrieval and verification behavior.

Whether the family authority requires a separate acceptance decision, who may
issue or review it, and its independence, currentness, and supersession rules
remain human methodology decisions for R1C. R1A does not choose them.

The complete referenced record must be available to the accepted resolver and
must validate against its exact schema. An ID plus digest without retrievable,
schema-valid semantic content is a forbidden hash-only stand-in.

Stateful policy must prevent family multiplicity laundering through aliasing,
cloning, reruns, new campaign IDs, result exposure, or post-result
reclassification. `TRIAL_FAMILY_REGISTERED` remains incomplete until that
authority, relation vocabulary, finite scope bound, anti-reset policy, and
killing vectors are accepted.

## Stage 3 Sample Reference Architecture

Architecture A selects the requirement for an immutable external Stage 3
sample-record reference rather than copying a private sample record into the
event. It does not accept a concrete Stage 3 sample authority.

A later Stage 3 authority contract must freeze:

- registry authority ID, version, canonicalization ID, and registry digest;
- sample-record ID, schema version, canonical bytes, and record digest;
- independent review-decision ID, schema version, canonical bytes, and
  decision digest;
- exact binding of that decision to the sample record, data contract, and
  applicable scope; and
- supersession and currentness behavior.

Shape-valid safe IDs and digests do not prove acceptance. Before every new
trial allocation, at each attempt execution boundary, and at each
protected-access boundary, the runtime must verify that the exact decision is
current, non-self-issued, non-superseded, scope-applicable, and bound to the
exact authority, version, schema, and record digest. The check and the
corresponding consuming action must share an atomic fail-closed boundary whose
exact transaction design remains deferred to the runtime contract. Historical
binding evidence remains retained after later supersession, but supersession
blocks every new consuming action.

Private paths, credentials, account or contract identifiers, signed URLs,
restricted queries, raw rows, performance values, and outcome-reconstructible
content never enter a tracked vector or safe public projection. A digest is not
automatically publication-safe. All repository vectors use synthetic values;
private digests remain in the repository-external private ledger unless
separately approved for publication.

`SAMPLE_REGISTERED` and `STAGE3_SAMPLE_REFERENCE_BOUND` remain incomplete until
the exact sample authority, local/external alias policy, finite collection
bounds, and private/public projection rules are accepted.

## Binding Reference Architecture

`CAMPAIGN_ENTITY_BOUND` will bind one existing ledger-global registration to
one already allocated campaign. Its future exact payload must include:

- singleton `campaign_scope_ids`;
- one closed tagged-union branch;
- exact source registration event ID; and
- exact source registration event SHA-256.

The selected branch determines the subject namespace and required source event
type. Shape validation may check syntax and branch consistency only.

Stateful validation must prove that the source event:

- exists earlier in the same ledger epoch;
- has retained bytes matching the referenced event ID and recomputed digest;
- has the required registration event type and matching subject;
- used empty campaign scope;
- is not paired with a competing direct or external path; and
- precedes every consuming trial or access.

`STAGE3_SAMPLE_REFERENCE_BOUND` allocates one ledger-local sample identity in
the later accepted sample namespace for one external sample record and one
already allocated campaign. A later cross-campaign reuse decision must prevent
the same external record from being reintroduced under unrelated local
identities to reset exposure or dependence history.

Both binding events remain incomplete in R1A and R1B.

## Local Shape Versus Stateful Ledger Rules

The schema registry may enforce only event-local facts:

- exact envelope and payload fields;
- scalar types, literals, typed namespaces, timestamps, and digest syntax;
- required, optional, and nullable behavior;
- closed union branch selection;
- array cardinality, sorting, and uniqueness; and
- exact local cross-field predicates.

The later ledger runtime must enforce:

- epoch and parent existence;
- one-time allocation and registration;
- sequence continuity and previous-hash truth;
- request-digest recomputation and idempotent operation replay;
- direct/global/external path exclusivity;
- all-campaign prior allocation for shared direct registration;
- source-event type, subject, bytes, digest, and ordering truth;
- external authority, record, decision, and currentness truth;
- currentness revalidation at trial allocation, attempt execution, and
  protected-access boundaries;
- family anti-reset and sample alias history;
- actor authorization and protected-access capability;
- durable atomic append, recovery, concurrency, and anti-rollback; and
- campaign inventory completeness before attempt or access.

Returning schema `ACCEPT` must never be described as satisfying a stateful
rule.

## Independent Evidence Requirements

Every later supported event needs:

- a hand-reviewed positive fixture independent of the registry artifact;
- a literal test oracle that does not discover expected fields from the schema
  under test;
- removal of every required field;
- unknown-field attacks at every closed nesting level;
- absent, null, wrong-type, Boolean/integer, wrong-prefix, digest, timestamp,
  scope, ordering, and uniqueness attacks;
- raw duplicate-property attacks before mapping;
- subject, scope, and repeated-reference mismatch attacks;
- one killing vector for every local constraint and every tagged-union branch;
- fixed external registry digest evidence and mutation sensitivity; and
- source-tree, sdist, and wheel resource-loading parity.

R1B must include at least one valid campaign allocation and one valid
experiment allocation, plus exact subject/scope mismatch negatives and
complete meta-tests for all three schema-language `0.2.0` capabilities.
Stateful ordering and allocation attacks belong to the later runtime suite and
must not be presented as registry-vector proof.

The later Stage 3-consuming runtime suite, not the R1B schema-vector suite,
must include a stateful killing vector in which an accepted Stage 3 decision
is superseded after trial allocation but before attempt execution, and the
attempt is rejected.

## Staged Follow-Up

The selected sequence is:

1. **R1A:** this design-only architecture decision; no event promotion.
2. **R1B:** immutable registry `0.2.0`, schema-language `0.2.0`, all three DSL
   meta-test families, the exact experiment namespace decision, and exact
   campaign/experiment allocation schemas only.
3. **R1C:** a new immutable, monotonically versioned registry release; exact
   family-definition authority and acceptance architecture, family namespace,
   family registration, and anti-reset policy.
4. **R1D:** a new immutable, monotonically versioned registry release; exact
   Stage 3 sample authority, sample namespace, local/external sample
   registration, alias policy, and privacy projection.
5. **R1E:** a new immutable, monotonically versioned registry release; exact
   family/sample campaign binding schemas and stateful source reference
   design.
6. Later separately reviewed event families, followed by a 37-of-37 registry
   closure gate.

No later step may infer fields from documentation helpers, rejected fixtures,
or narrative lists. Stage 5 remains blocked until the complete Stage 4b
runtime and all-trial/access enforcement gates are accepted.

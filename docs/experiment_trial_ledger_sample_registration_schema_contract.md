# Experiment and Trial Ledger Sample Registration R1D Contract

Contract ID: `experiment_trial_ledger_sample_registration_schema_r1d`.

Contract version: `0.4.0`.

Owner decision: option `R1D-A`.

Exact ledger-local sample namespace: `smp_<32 lowercase hex>`.

This document is the design authority for the bounded Stage 4B-R1D local
sample-registration release under:

- `docs/point_in_time_data_methodology_contract.md`;
- `docs/experiment_trial_ledger_contract.md`;
- `docs/experiment_trial_ledger_schema_registry_contract.md`;
- `docs/experiment_trial_ledger_allocation_registration_schema_contract.md`;
  and
- `docs/experiment_trial_ledger_trial_family_registration_schema_contract.md`.

Its publication state is determined by protected-main history and
`docs/current_handoff.md`, not by a status claim inside this document.

## Release Boundary

R1D publishes one new immutable registry release:

- registry schema ID
  `experiment_trial_ledger_payload_schema_registry_v4`;
- registry version `0.4.0`;
- unchanged schema-language ID `ledger_closed_schema_dsl_v1`;
- unchanged schema-language version `0.2.0`; and
- a separate packaged JSON artifact and SHA-256 sidecar.

R1D preserves the accepted 37-event vocabulary. Its supported event set is
exactly:

```text
LEDGER_EPOCH_CREATED
CAMPAIGN_ALLOCATED
EXPERIMENT_ALLOCATED
TRIAL_FAMILY_REGISTERED
SAMPLE_REGISTERED
```

The other 32 events remain
`SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`. In particular,
`CAMPAIGN_ENTITY_BOUND` and `STAGE3_SAMPLE_REFERENCE_BOUND` remain incomplete
for R1E. R1D does not overwrite, reinterpret, or silently upgrade immutable
registry releases `0.1.0`, `0.2.0`, or `0.3.0`, their digests, the default R0
entry point, or prior validator outcomes.

Registry acceptance proves only that a candidate event has the accepted local
shape and literal syntax. It does not prove retrieval, authority, acceptance,
publication approval, currentness, reviewer independence, prior campaign
allocation, uniqueness, path exclusivity, overlap history, sequence or
previous-hash truth, append durability, or sample-exposure history.

## Exact Event Subject and Scope

`SAMPLE_REGISTERED` has:

- `subject_type` exactly `sample`;
- `subject_id` exactly one newly registered
  `smp_<32 lowercase hex>` identity; and
- no duplicate sample ID inside its payload.

Its `payload.campaign_scope_ids` is a sorted-unique array of exact
`cmp_<32 lowercase hex>` identities:

- empty means a ledger-global local registration;
- one through 32 entries means a direct local registration covering exactly
  those campaigns; and
- 33 or more entries are invalid.

Every campaign in a nonempty direct scope must already be allocated before the
registration is appended. A global registration and each campaign allocation
are independent siblings after the epoch; a later
`CAMPAIGN_ENTITY_BOUND` event is still required before a global sample is used
inside a campaign. These are stateful rules and are not established by local
shape validation.

The maximum of 32 is the owner-selected common direct-registration bound
already frozen by R1C-A. Broader reuse must use ledger-global registration plus
explicit campaign binding rather than an unbounded direct scope.

## Exact Registration Payload

The payload contains exactly these fields:

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

Their exact local schemas are:

| Field | Exact local schema |
| --- | --- |
| `campaign_scope_ids` | sorted-unique array of `campaign_id`, minimum 0, maximum 32 |
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
additional fields fail closed. The common event envelope remains the accepted
`ledger_event_v1` envelope.

## Exact Retrievable Stage 3 Sample Authority

R1D-A selects one immutable versioned Stage 3 sample-authority catalog plus
complete repository-external canonical sample records. It does not select a
provider, dataset, physical storage service, private ledger backend, or
dataset-review outcome.

The registration pins the authority catalog by:

```text
sample_authority_id
sample_authority_version
sample_authority_registry_sha256
sample_record_canonicalization_id
```

It pins one complete sample record by:

```text
sample_record_id
sample_record_version
sample_record_schema_version
sample_record_sha256
```

The accepted resolver key is the exact tuple:

```text
(
  sample_authority_id,
  sample_authority_version,
  sample_authority_registry_sha256,
  sample_record_id,
  sample_record_version,
  sample_record_schema_version,
  sample_record_canonicalization_id,
  sample_record_sha256
)
```

The resolver must return the complete canonical record bytes. It must verify
the pinned catalog digest, exact record schema, canonical bytes, and record
digest before use. A retrieval miss, ambiguous record, digest mismatch, schema
mismatch, noncanonical record, or hash-only stand-in fails closed.

The external `stage3_sample_record_v1` record must bind the exact authority and
record tuple above, the exact ledger-local `sample_id`, its immutable Stage 3
manifest/window/scope/classification registration, sealing evidence and access
policy, its sample-lineage identity, and overlap relations to every other
applicable sample. Private manifest fields and restricted locators remain in
the complete external record and are not copied into this event payload.

The digest-pinned external authority catalog schema fixes the complete record
keys, finite collection bounds, overlap vocabulary, and any predecessor
relation. The event registry does not replace that external schema with
partial narrative fields.

## Separate Acceptance and Reviewer Independence

The registration pins a separate complete acceptance record by:

```text
sample_acceptance_decision_id
sample_acceptance_generation
sample_acceptance_schema_version
sample_acceptance_record_sha256
```

The accepted resolver key is the exact pinned sample-record tuple plus those
four acceptance fields. The resolver must return complete canonical
`stage3_sample_acceptance_v1` bytes and verify their schema,
canonicalization, and digest.

The acceptance record must bind:

- the exact authority catalog and sample-record tuple;
- the exact `sample_id`;
- the exact global or direct `campaign_scope_ids`;
- one sample-record producer actor reference;
- one reviewer actor reference;
- the outcome `accepted`;
- the exact generation;
- an optional predecessor decision under explicit `supersedes`; and
- the decision's canonical bytes and SHA-256.

For formal use, the reviewer must be distinct from both the sample-record
producer and the `SAMPLE_REGISTERED.actor_id`. R1D shape validation cannot
prove that inequality or authenticate any actor. A later stateful authority
must verify all roles and permission. Until then, authority-dependent runtime
behavior remains fail closed.

## Privacy Projection and Publication Approval

The registration pins one allowlisted public projection by:

```text
sample_public_projection_id
sample_public_projection_schema_version
sample_public_projection_sha256
```

It separately pins the exact publication-approval record by:

```text
sample_publication_approval_id
sample_publication_approval_generation
sample_publication_approval_schema_version
sample_publication_approval_record_sha256
```

The resolver must return complete canonical
`public_redacted_projection_v1` and
`sample_public_projection_approval_v1` bytes. The approval record must bind
the exact projection ID, schema, canonical digest, allowed published hashes,
scope, outcome `approved`, generation, and any explicit predecessor.

Complete records, private paths, credentials, account or contract IDs,
restricted queries, signed URLs, raw rows, symbol-level restricted data,
private performance values, outcome-reconstructible content, and unapproved
digests remain repository-external and private. A digest is not publication
safe merely because it is non-reversible. A public projection may contain
only its closed Stage 3 allowlist of safe IDs and hashes explicitly covered by
the pinned publication approval.

Real private record or approval values do not enter repository fixtures.
Committed vectors use synthetic IDs and synthetic digests only. The later
public ledger projection must omit private event fields unless the exact value
is independently allowlisted and publication-approved.

## Local and External Representation

R1D-A keeps three sample paths mutually exclusive:

1. direct local `SAMPLE_REGISTERED`;
2. ledger-global local `SAMPLE_REGISTERED` followed by the later exact
   `CAMPAIGN_ENTITY_BOUND`; or
3. later campaign-scoped `STAGE3_SAMPLE_REFERENCE_BOUND`, which allocates the
   ledger-local `sample_id` and binds the exact external Stage 3 record without
   backfilling a synthetic `SAMPLE_REGISTERED`.

R1D promotes only the local registration event. R1E must define both binding
schemas, exact source-event references, external reference fields, and
stateful source/path checks before either binding event can be promoted.

Within one ledger epoch, one canonical sample lineage and representation path
has exactly one ledger-local `sample_id`. The same external record cannot be
reintroduced through multiple local identities or mixed local/external paths.
Cross-campaign reuse must reuse the established global identity and later
bindings; it cannot allocate a fresh identity to reset exposure history.

## Anti-Reset and Currentness Policy

The provider-neutral sample currentness key is exactly:

```text
(sample_authority_id, sample_record_id)
```

Acceptance generations are positive safe integers and strictly increase. Once
a sample record has an accepted generation, exactly one accepted generation is
current. Formal registration and use require that the sole current generation
exists, has outcome `accepted`, binds the exact record, projection, publication
approval, and scope, and is not superseded.

Publication-approval generations are also positive, strictly increasing, and
single-current for one `sample_public_projection_id`. Revocation or
supersession leaves prior evidence immutable but blocks new consumption.

Currentness must be checked:

1. immediately before `SAMPLE_REGISTERED` append;
2. before every later sample binding;
3. before every later `TRIAL_ALLOCATED`;
4. at every attempt execution boundary; and
5. at every protected-access boundary.

If a decision is superseded after an earlier event, the historical event
remains immutable, but no later action may treat the old decision as current.

Aliases, clones, new campaign IDs, reruns, result access, or reclassification
must not allocate a new sample identity or reset exposure history. A genuinely
different window or record version may require a distinct immutable record,
but every overlap relation and inherited exposure classification remains
binding; an overlapping window cannot manufacture pristine holdout status.
Corrections advance through explicit supersession and cannot mutate or erase
the prior record.

These rules require stateful history and external currentness authorities.
They are not local registry predicates and R1D does not implement them.

## Required Killing Evidence

R1D must include independent evidence for:

- byte-exact R0, R1B, and R1C artifacts, digests, behavior, and package
  resources;
- explicit selection of packaged registry `0.4.0`;
- the exact five-event supported set and 32-event incomplete partition;
- independent global and direct positive fixtures;
- every missing payload and envelope field;
- every nested/top-level unknown and raw duplicate property;
- wrong `subject_type`, wrong `smp_` namespace, and duplicate subject fields;
- unsorted, duplicate, wrong-prefix, 33-item, and wrong-type campaign scope;
- unsafe authority, record, acceptance, projection, and approval IDs;
- zero, negative, Boolean, noninteger, and unsafe versions or generations;
- uppercase, wrong-length, and non-string digests;
- wrong record, acceptance, projection, approval, and canonicalization
  versions;
- a shape-valid event whose external resolver record is missing, explicitly
  documented as a later stateful fail-closed case rather than local `ACCEPT`
  evidence;
- stale or superseded acceptance, revoked projection approval, self-review,
  mixed local/external paths, alias reset, clone reset, new-campaign reset,
  overlapping-window laundering, and post-access reclassification reset,
  explicitly reserved for the later stateful runtime suite; and
- arbitrary self-consistent unpublished event promotion rejected by packaged
  digest authority.

The independent fixture must not be generated from the registry artifact.
Literal tests must not discover expected fields, namespace, supported events,
or outcome codes from the implementation under test.

## Non-Goals

R1D does not:

- append, store, allocate, register, retrieve, resolve, accept, approve,
  supersede, authenticate, authorize, or execute anything;
- select a provider, dataset, backend, object store, database, private ledger
  path, signature scheme, or recovery mechanism;
- promote either binding event, `TRIAL_ALLOCATED`, or any
  lifecycle/access/review/adjudication event;
- copy private sample records, paths, raw values, or performance values into
  the repository;
- run a campaign, trial, attempt, protected access, factor, backtest, or
  historical interpretation; or
- add paper, brokerage, order, live, or real-money behavior.

Trial count, execution-attempt count, and protected-sample access remain zero.

## Next Gate

After R1D is accepted on protected main, R1E must separately define the exact
`CAMPAIGN_ENTITY_BOUND` and `STAGE3_SAMPLE_REFERENCE_BOUND` schemas, including
closed family/sample branches, exact source event or external-record
references, direct/global/external path exclusivity, and stateful source
currentness requirements. Any genuine owner-methodology gate follows the
bounded reminder policy: four reminders at 30-minute intervals, then the
heartbeat pauses if the owner has not replied.

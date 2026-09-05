# Experiment and Trial Ledger Contract

Status: accepted Stage 4a design contract on protected main via PR #164.
Stage 4b runtime enforcement is not implemented by this document.

Contract ID: `experiment_trial_ledger_contract_v1`.

Contract version: `1.0.0`.

This document is the accepted normative Stage 4a design under
`docs/research_program_charter.md`, the accepted Stage 3
`docs/point_in_time_data_methodology_contract.md`, and
`docs/current_roadmap.md`. It freezes the evidence model required before the
program may treat experiment history as complete.

Contract acceptance is software-process evidence only. It does not implement a
ledger, select a storage backend, migrate legacy logs, inspect private data,
authorize a historical campaign, establish statistical validity, or authorize
LEAN, paper, brokerage, order, or live behavior.

## Scope and Non-Authorization

Stage 4a defines:

- typed immutable identities and ownership relationships;
- semantic trial versus execution-attempt counting;
- allocation-before-action and access-intent-before-read barriers;
- trial, attempt, protected-access, review, and promotion lifecycles;
- campaign inventory sealing, completeness, and closure;
- exact canonical event identity, chaining, correction, and checkpoint rules;
- artifact, failure, code, data, environment, and sample bindings;
- private canonical records and allowlisted public projections; and
- a deterministic conformance matrix for the later runtime.

This stage does not change `src/reporting/experiment_log.py`,
`src/reporting/experiment_registry.py`, any research workflow, any generated
report, or any private EODHD artifact. It adds no database, lock service,
signature service, vendor adapter, credential, dependency, or trading path.

The current schema-v1 JSON experiment logs remain diagnostic/legacy sidecars.
They are overwrite-capable successful-run summaries, not the immutable
all-trial ledger. They must not be placed in the future ledger namespace or
used to prove preallocation, completeness, holdout independence, or formal
historical validity.

## Evidence Objects and Ownership

The v1 identity graph is:

```text
ledger_epoch
  campaign
    experiment
      semantic trial
        execution attempt

global trial family ------- referenced by every related semantic trial
sample registration ------- referenced by trials and protected access
protected access ---------- intent/start/terminal/decision event sequence
artifact manifest --------- referenced by attempt, review, and decision events
review/promotion decision - bound to one sealed campaign evidence version
```

The objects have distinct meanings:

- `ledger_id` identifies one ledger epoch and canonical event stream.
- `campaign_id` identifies one preregistered research objective, trial budget,
  sample policy, evidence thresholds, and ordered trial inventory.
- `experiment_id` identifies one frozen hypothesis, estimand, and protocol
  inside a campaign.
- `trial_family_id` identifies a global multiplicity/dependence family. It
  follows related hypotheses across campaigns and cannot be relabeled after
  allocation or result access.
- `trial_id` identifies exactly one semantic configuration: formula,
  direction, parameters, horizon, universe, preprocessing, neutralization,
  selection, weighting, constraints, benchmark, costs, execution, samples,
  code, data, and environment bindings.
- `attempt_id` identifies one invocation of that frozen trial. An operational
  retry before trial closure uses a new attempt ID under the same trial.
- `sample_id` identifies one immutable manifest/window/scope/classification
  registration under the Stage 3 contract.
- `exposure_id` identifies one protected-access lifecycle.
- `artifact_id` identifies one retained raw-byte artifact or one explicit
  expected-output disposition.
- `event_id`, `review_decision_id`, and `promotion_decision_id` identify
  immutable append records and decisions.

Every ledger-owned logical entity ID is typed, opaque, globally unique,
non-content-derived, and allocated exactly once from its own namespace. Its
wire form is a lowercase prefix plus 32 lowercase hexadecimal digits, such as
`trl_<32-lowercase-hex>`. Stage 4b must freeze and test the production entropy,
collision, and concurrent-allocation policy before runtime use; deterministic
golden IDs prove syntax only. Content hashes never substitute for preallocated
entity IDs.

`LEDGER_EPOCH_CREATED` atomically introduces its ledger-owned `ledger_id`; no
earlier ledger event can allocate it. `event_id` and `operation_id` identify
the append record and append request rather than ledger-owned logical
entities.

`actor_id` is an externally assigned, opaque claimed-attribution reference.
Stage 4a validates only its canonical `act_<32-lowercase-hex>` wire syntax and
binds it into request/event identity. It does not prove the actor's
authenticity, control, authorization, role independence, currentness, or
revocation state, and it grants no append, access, review, promotion, or other
permission. Any formal behavior that depends on those properties must fail
closed until Stage 4b accepts an owner-approved external authority mechanism
with historical activation, replacement, and revocation evidence. Stage 4a
does not choose that mechanism.

Each ledger-owned logical entity ID is allocated exactly once across the
ledger. Later lifecycle, correction, supersession, review, or decision events
intentionally reuse that already allocated ID as a typed subject or reference;
those events do not allocate the entity again. Entity-ID conflict therefore
means a second allocation attempt for an existing ledger-owned logical entity
ID. A ledger-owned typed reference is legal only after its allocation and only
for the allocated entity type.

Changing any identity-bearing trial field creates a new `trial_id`. Exact
replay of one ledger operation is idempotency, not another trial. An execution
retry before trial closure creates a new `attempt_id` but does not change
semantic trial multiplicity. A rerun authorized after a terminal trial creates
a new trial linked by `rerun_of_trial_id`, because prior result exposure may
affect the decision to run again. Campaign reports disclose both semantic
trial count and execution-attempt count.

Parent, child, clone, retry, rerun, and shared-data relations are explicit,
complete, and acyclic. A cloned configuration in another campaign retains the
same global trial-family relation; a new campaign cannot reset known
dependence or prior-trial multiplicity.

## Allocate Before Action

No validator, executor, protected-data accessor, or result-producing process
may run before the relevant allocation event is durably committed. Parent
precedence is an exact partial order, not one total order among independent
siblings:

```text
LEDGER_EPOCH_CREATED
  -> CAMPAIGN_ALLOCATED
       -> EXPERIMENT_ALLOCATED
       -> each direct family/sample or external-sample binding path
  -> each optional ledger-global family/sample registration
CAMPAIGN_ALLOCATED + each selected ledger-global registration
  -> CAMPAIGN_ENTITY_BOUND
EXPERIMENT_ALLOCATED + every completed selected family/sample path
  -> TRIAL_ALLOCATED
  -> CAMPAIGN_INVENTORY_SEALED
  -> ATTEMPT_ALLOCATED or ACCESS_INTENT
```

`EXPERIMENT_ALLOCATED` is campaign-scoped and must follow its
`CAMPAIGN_ALLOCATED`. The experiment, family, and sample parent paths are
independent siblings: they may interleave, but every selected path must finish
before `TRIAL_ALLOCATED`. Each referenced family uses exactly one of these
legal paths:

1. **Direct campaign-scoped registration:** `CAMPAIGN_ALLOCATED` precedes
   `TRIAL_FAMILY_REGISTERED`; that registration's immutable
   `campaign_scope_ids` contains the campaign; and the registration precedes
   `TRIAL_ALLOCATED`.
2. **Ledger-global registration plus campaign binding:** a ledger-global
   `TRIAL_FAMILY_REGISTERED` with empty `campaign_scope_ids` follows
   `LEDGER_EPOCH_CREATED`; after both that registration and
   `CAMPAIGN_ALLOCATED`, `CAMPAIGN_ENTITY_BOUND` names the family, campaign,
   and exact source registration event ID/hash; that binding precedes
   `TRIAL_ALLOCATED`.

Each referenced sample independently uses exactly one of these legal paths:

1. **Direct ledger-local campaign registration:** `CAMPAIGN_ALLOCATED`
   precedes `SAMPLE_REGISTERED`; that registration's immutable
   `campaign_scope_ids` contains the campaign; and the registration precedes
   `TRIAL_ALLOCATED`.
2. **Ledger-global registration plus campaign binding:** a ledger-global
   `SAMPLE_REGISTERED` with empty `campaign_scope_ids` follows
   `LEDGER_EPOCH_CREATED`; after both that registration and
   `CAMPAIGN_ALLOCATED`, `CAMPAIGN_ENTITY_BOUND` names the sample, campaign,
   and exact source registration event ID/hash; that binding precedes
   `TRIAL_ALLOCATED`.
3. **Accepted external Stage 3 registration:** no synthetic
   `SAMPLE_REGISTERED` is backfilled into this ledger. After
   `CAMPAIGN_ALLOCATED`, one campaign-scoped
   `STAGE3_SAMPLE_REFERENCE_BOUND` allocates the ledger-local typed
   `sample_id` used by the trial and binds it to the exact external registry
   authority, external sample-record ID, schema/contract version, immutable
   record SHA-256, and accepted review/decision reference. That binding
   precedes `TRIAL_ALLOCATED`. For each later campaign that reuses the same
   external-origin sample lineage, `CAMPAIGN_ENTITY_BOUND` names that same
   `sample_id`, the later campaign, and the exact first
   `STAGE3_SAMPLE_REFERENCE_BOUND` event ID/hash. The first Stage 3 event
   remains the sole identity allocation; later campaign bindings do not
   synthesize local registration or allocate a replacement identity.

For either direct path, `campaign_scope_ids` is sorted and unique, may list
multiple affected campaigns, and must contain this campaign. For either
ledger-global path, the registration and `CAMPAIGN_ALLOCATED` are independent
siblings: each follows `LEDGER_EPOCH_CREATED`, both precede
`CAMPAIGN_ENTITY_BOUND`, and neither must precede the other.

The parent-path field names in this section describe non-append semantic
ordering facts. Except for the exact epoch payload frozen below, the later
machine-readable registry determines their event payload placement, types,
nullability, unions, and nested schemas.

A direct registration cannot also have `CAMPAIGN_ENTITY_BOUND`; an external
Stage 3 representation cannot also have either local registration path for
the same ledger-local sample ID. An external-origin identity may have later
campaign bindings only when each binding references the exact first Stage 3
event and retains the same external authority, record, acceptance,
projection, publication-approval, lineage, overlap, and exposure history. A
binding to a different registration/reference event, entity, campaign source,
external version, or digest is mismatched. Every referenced parent must
therefore have exactly one completed legal origin path in the same verified
ledger epoch, except that the external Stage 3 record remains in its accepted
registry and is represented by the immutable local reference binding.
Dangling, ambiguous, mismatched, later-created, origin-switching, or
path-order-invalid parents fail before commit and also fail closure
verification.

For a trial:

1. Commit `TRIAL_ALLOCATED` with its full immutable bindings and initial
   `PLANNED` disposition.
2. Commit `ATTEMPT_ALLOCATED` before invoking any validator or executor.
3. Commit `ATTEMPT_STARTED` immediately before execution begins.
4. Commit exactly one terminal attempt event and, after all attempts and
   linked access lifecycles are terminal, one trial disposition.

If either allocation append fails, the validator/executor is not invoked. A
validation failure after allocation is retained as `INVALID`; an environment
or operational failure is retained as `FAILED`; deliberate withdrawal is
`ABORTED`; a preregistered rule that prevents execution is `EXCLUDED`. An
expected output that was never created is recorded as `NOT_PRODUCED` with a
typed reason. No hash is fabricated.

An acknowledgement lost after a durable append is handled through
`operation_id` and `operation_request_sha256`. The store, rather than the
caller, recomputes that digest over exactly one
`ledger_operation_request_v1` object:

```text
operation_request_projection_id
ledger_schema_version
event_schema_version
canonicalization_id
identity_projection_id
ledger_id
event_id
operation_id
event_type
subject_type
subject_id
occurred_at
actor_id
payload
```

The request projection has all-and-only those keys, uses
`pit_canonical_json_v1`, and excludes commit-assigned `sequence`,
`recorded_at`, and `previous_event_sha256` plus
`operation_request_sha256` itself. Its canonical UTF-8 bytes are hashed with
SHA-256. Replaying the exact request returns the original sequence and event
hash without appending. Reusing the operation ID, event ID, or sequence with
different request bytes fails closed before action. Submitting a second
allocation for an existing ledger-owned entity ID also fails; a later
non-allocation event may legally reference the existing ledger-owned typed
entity as described above. Event IDs identify individual append records,
operation IDs identify idempotent requests, and sequences identify commit
positions, so their conflicting reuse is never a lifecycle reference.

## Campaign Inventory and Trial Counting

Before the first attempt or protected access, a campaign commits
`CAMPAIGN_INVENTORY_SEALED` containing:

- the ordered all-and-only trial IDs and their configuration hashes;
- every experiment and global trial-family relation;
- the trial budget and allowed variation axes;
- sample roles and protected-access budget;
- frozen review, promotion, cost, timing, and statistical policy references;
- the canonical inventory bytes and SHA-256; and
- one `campaign_inventory_preseal_head_v1` anchor.

The pre-seal anchor is not the later accounting-closure checkpoint. Its three
fields `(ledger_id, predecessor_sequence, predecessor_event_sha256)` are
included and bound inside the inventory-seal request/event preimage, while the
referenced predecessor event bytes are external to and excluded from that seal
preimage. The seal is committed only at `predecessor_sequence + 1`; its own
sequence/event hash are never named by the anchor, so the anchor is
nonrecursive. The seal's stored `event_sha256` remains outside its event
preimage under the common-envelope rule. The v1 campaign seal requires the
concrete predecessor form; epoch-empty `(null, null)` is not legal because
`LEDGER_EPOCH_CREATED` is already sequence zero. At the same serialized atomic
commit boundary that compares the bound predecessor to the actual current
retained stream head and assigns the seal sequence/envelope
`previous_event_sha256`, the two heads must match exactly. If another append
wins first, the seal fails/conflicts; it must not silently rebase. Before the
first attempt or access, the retained
stream must still contain that exact predecessor sequence/hash;
mutation, replacement, truncation, or a different replay head fails the seal
verification. Exact replay returns the original seal without another append;
a changed request or predecessor head conflicts before action. This pre-seal
ordering anchor has no issuer, retention, or independent-trust role and must
not be called a checkpoint.

An amendment follows an exact reservation order:

1. append `CAMPAIGN_AMENDMENT_PROPOSED` with reason and exposure state;
2. allocate the added parent/trial IDs without running or accessing them;
3. append `CAMPAIGN_INVENTORY_AMENDED` whose all-and-only inventory includes
   those IDs; and
4. only then allocate an attempt or access intent for an added trial.

The amendment retains the previous inventory and records whether any result or
outcome-reconstructible sample was already available. A result-informed
amendment cannot be represented as part of the original preregistered
inventory, cannot erase earlier multiplicity, and cannot support
`RESEARCH_PASS` or higher on already observed evidence under either the
original or amended seal. Such work remains design/development evidence and at
most `DIAGNOSTIC_ONLY` for that sample. Confirmatory promotion requires a new
prospectively sealed campaign, the retained global family/multiplicity lineage,
and a fresh eligible information-independent sample. Retrospective family
assignment, silent trial deletion, and leaderboard-only output are invalid.

Every configured variation counts once as a semantic trial even if it is
`FAILED`, `INVALID`, `ABORTED`, or `EXCLUDED`. Operational retries remain
visible attempts. Folds, splits, and repeated observations inside one frozen
trial are evidence children rather than automatically new trials; changing
their defining configuration is a new trial.

## Trial and Attempt Lifecycles

Trial disposition and attempt execution state are separate.

An attempt starts at `ALLOCATED`, may advance to `RUNNING`, and ends exactly
once as `COMPLETED`, `FAILED`, `INVALID`, or `ABORTED`:

```text
ALLOCATED -> RUNNING | FAILED | INVALID | ABORTED
RUNNING   -> COMPLETED | FAILED | INVALID | ABORTED
terminal  -> no later attempt state
```

A trial starts as `PLANNED` and ends exactly once as `COMPLETED`, `FAILED`,
`INVALID`, `ABORTED`, or `EXCLUDED`:

```text
PLANNED -> COMPLETED | FAILED | INVALID | ABORTED | EXCLUDED
terminal -> no later trial disposition
```

Trial `COMPLETED` requires at least one completed attempt, a sealed expected
output inventory, terminal access lifecycles, and exact artifact dispositions.
It means only that the declared computation completed. It never means
`RESEARCH_PASS`, profitability, robustness, readiness, or promotion.

The charter candidate evidence states remain a different axis:
`INVALID`, `INCONCLUSIVE`, `REJECTED`, `DIAGNOSTIC_ONLY`, `CONDITIONAL`,
`RESEARCH_PASS`, `PORTFOLIO_PASS`, `PAPER_CANDIDATE`, and `LIVE_CANDIDATE`.
A promotion decision may assign only the lowest state supported by completed
gates. `LIVE_CANDIDATE` is a label, not authorization.

A terminal state never reopens. Corrections and supersessions append new events
that reference the original; they do not update, delete, replace, or conceal
the original event. A later execution after terminal closure receives a new
trial and attempt lineage.

## Frozen Trial Bindings

`TRIAL_ALLOCATED` binds:

- campaign, experiment, global trial-family, parent, clone, and rerun IDs;
- the exact versioned full configuration and its canonical SHA-256;
- clean code commit/tree identity, or an immutable dirty-tree patch/tree digest
  that causes formal evidence to remain ineligible until reviewed;
- data manifest/input IDs, allowed private/public hash references, and lineage;
- environment ID, lock hash, interpreter/platform, locale, timezone, and
  dependency versions;
- sample IDs, classifications, roles, exact window references, and access
  policy;
- timing, split, benchmark, risk-free, cost, and execution contract IDs;
- selection role, expected artifact roles, and retry policy; and
- allocation actor, authority reference, and timestamps.

Under the later accepted exact registry, raw floating-point objects, implicit
defaults, unordered identity-bearing collections, registry-unknown fields,
lossy key coercion, and mutable path-based identity are not valid bindings.
Absent and registry-declared `null` remain different. Configuration, code,
data, environment, or sample changes require a new trial.

These `TRIAL_ALLOCATED` bindings are normative semantic requirements, not an
exact Stage 4a payload schema. Their exact field placement, scalar and nested
types, required/nullable status, unions, and nested object/collection schemas
are deferred to the complete machine-readable per-event registry. Until that
registry is separately accepted, a prototype must reject `TRIAL_ALLOCATED` as
`SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`; it cannot infer an append-valid payload
from this narrative or from documentation-only parent-order facts.

## Artifact and Failure Evidence

Each attempt predeclares an expected-output inventory. A terminal record gives
every role exactly one disposition:

- `PRODUCED`: raw-byte SHA-256, byte size, artifact class, and safe evidence
  reference are present;
- `NOT_PRODUCED`: no hash is present and a typed reason is required; or
- `PARTIAL`: retained bytes are hashed, the incomplete status is explicit, and
  a typed failure reason is required.

Failure records retain the phase, stable error code, safe reason code,
responsible attempt, partial artifact inventory, and whether protected
material may have been observed. Free-form stack traces, commands, paths,
credentials, queries, usernames, raw data, and private performance values are
not permitted in a tracked projection.

Post-completion artifact mutation invalidates verification. Output hashes bind
bytes, not truth or validity, and never by themselves satisfy a research gate.

## Protected-Sample Access

Every protected access references pre-existing campaign, experiment, global
trial-family, trial, sample, actor, authorization, tool/process, purpose,
intended window, intended field/artifact classes, actual accessor code
identity, environment ID/lock hash, immutable safe evidence references, and a
frozen affected-trial set. A shared campaign access may instead bind an already
sealed campaign scope whose exact affected trials are part of the identity.
Intent, start, and terminal records each bind the intended or actual reader
code/environment and evidence references; a trial's code binding cannot stand
in for a separate accessor process.

The append-only lifecycle is:

```text
ACCESS_INTENT -> ACCESS_STARTED -> ACCESS_COMPLETED | ACCESS_FAILED | ACCESS_ABORTED
ACCESS_INTENT -> ACCESS_CANCELLED
```

`ACCESS_INTENT` must be durable before the accessor can open or materialize
protected content. A successful append returns a capability bound to the exact
intent; allocation alone is not authorization. In one serialized atomic
barrier, the accessor validates and consumes that exact capability and commits
`ACCESS_STARTED` before any open, read, materialization, or release. A start
append failure means zero access. Concurrent redemption permits one commit;
exact lost-ack replay returns that start event without a second access, while a
different operation or scope fails. The accessor refuses a missing, stale,
mismatched, or already consumed capability. `ACCESS_CANCELLED` is legal only
before start.

Terminal access records contain actual actor/process and reader
code/environment, start/end/record times, actual sample/window and names
observed, immutable safe evidence references, and
`protected_material_observed = NONE | SOME | UNKNOWN`. No canonical access
event, including the private full ledger, may embed raw protected rows, result
payloads, prices, returns, labels, holdings, trades, costs, equity paths,
metric/performance values, directions, magnitudes, ranks, plots, or other
outcome-reconstructible payloads. It retains exact IDs, approved names,
classifications, and references to separately controlled evidence instead.

A failed or aborted access preserves the prior classification only when
contemporaneous evidence proves `NONE`. `SOME`, `UNKNOWN`, a missing terminal
after start, a broader actual scope, or an unavailable prospective intent is
conservative exposure. Broader actual scope is also an unauthorized-access
finding; recording it does not legitimize it. Missing intent, postdated intent,
or reconstructed access sets `backfilled = true`; normal prompt completion
after a prospective intent is not backfill.

Each terminal access is followed by an immutable `EXPOSURE_DECISION`. The
registry first partitions all sample windows at every exact boundary into
atomic intervals. Exact overlap, aliases of the same manifest/window, and
derived-artifact lineage union their append-only exposure facts on each
affected interval. Uncertain overlap adds the uncertainty fact to the whole
possibly affected interval. A correction can add facts but cannot remove them.

Classification is derived, never caller-selected, in this precedence order:

1. confirmed design/tuning influence or selection outside the frozen budget is
   `development`;
2. `UNKNOWN` observation, missing/backfilled access, unknown actor/time/impact,
   missing terminal state, uncertain overlap, or `SOME` with incomplete or
   uncertain evidence is `pseudo_holdout`; complete `SOME` evidence is
   classified by its frozen validation, evaluation, or design purpose below;
3. a complete `SOME` observation with frozen `purpose = design` is
   `development`, even without separately confirmed downstream design/tuning
   influence;
4. one frozen outcome-reconstructible evaluation with no design influence is
   `historical_evaluation` for later campaigns;
5. registered selection inside its frozen trial budget is `validation`; and
6. only a prospectively sealed, information-independent, never-accessed sample
   can remain `holdout`.

The explicit allowed-transition graph is:

```text
holdout              -> holdout | validation | historical_evaluation | pseudo_holdout | development
validation           -> validation | historical_evaluation | pseudo_holdout | development
historical_evaluation -> historical_evaluation | pseudo_holdout | development
pseudo_holdout        -> pseudo_holdout | development
development           -> development
```

For an aggregate sample, each atomic interval retains its own classification;
any single-label summary uses the first applicable precedence rule above, so a
less-exposed interval cannot mask a more-exposed one. `pseudo_holdout` can
never become `historical_evaluation` or `holdout`.
`historical_evaluation` may become `pseudo_holdout` or `development`.

A new pristine holdout requires a distinct, prospectively sealed,
information-independent sample. The known private 2025-05-01 through
2026-05-31 interval has an irrevocable floor of `historical_evaluation`: it may
become `pseudo_holdout` or `development` with stronger exposure facts, but
never `validation` or `holdout`.

A trial or campaign cannot close while an access intent lacks a terminal access
record or exposure decision. If access might have started, unresolved state is
`UNKNOWN_ACCESS` and blocks a holdout claim.

## Immutable Event Envelope and Hashing

Each append has exactly the following identity-bearing event fields:

```text
ledger_schema_version
event_schema_version
canonicalization_id
identity_projection_id
ledger_id
sequence
event_id
operation_id
operation_request_projection_id
operation_request_sha256
event_type
subject_type
subject_id
occurred_at
recorded_at
actor_id
previous_event_sha256
payload
```

The common identity-envelope schema rejects missing or unknown envelope
fields. `sequence` is a non-Boolean, zero-based, contiguous I-JSON-safe integer
assigned at the serialized commit boundary. The first event has
`previous_event_sha256 = null`; every later event contains the exact lowercase
SHA-256 of the immediately prior canonical event preimage. Commit sequence is
authoritative; timestamps never reorder events.

`ledger_event_identity_v1` is the exact object containing all-and-only the
fields above. Its typed values use the accepted `pit_canonical_json_v1`
preprocessing and exact RFC 8785/JCS UTF-8 serialization. The stored
`event_sha256` is the lowercase SHA-256 of those bytes and is outside the
preimage. No other envelope field is ignored. Duplicate JSON properties,
invalid or non-NFC text, ambiguous timestamps or numbers, raw floats,
NaN/infinity, non-string keys, unknown envelope properties, and invalid typed
IDs are rejected rather than coerced.

For `ledger_event_identity_v1`, `occurred_at` and `recorded_at` use the
application-level `ledger_v1_utc_timestamp` subset. Its exact ASCII form is
`YYYY-MM-DDTHH:MM:SS[.fraction]Z` over the proleptic Gregorian calendar,
including year `0000`; hour, minute, and second ranges are respectively
`00`-`23`, `00`-`59`, and `00`-`59`. A fractional second may have arbitrary
precision but must be nonzero and must not end in zero; an exact zero fraction
is omitted. Offsets, lowercase or alternate separators, trailing fractional
zeros, invalid calendar days, and all coercion are rejected.

Ledger event schema v1 rejects every `second = 60`, including historically
announced June and December leap seconds and syntactically plausible
unannounced dates, because this contract pins no leap-second table. This is a
deliberate application-level subset of RFC 3339 timestamp syntax. It does not
change `pit_canonical_json_v1`: the canonical serializer remains responsible
only for deterministic serialization of values already accepted by the
ledger event schema.

The v1 event-type vocabulary is closed at exactly these 37 values:

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
CAMPAIGN_AMENDMENT_PROPOSED
CAMPAIGN_INVENTORY_AMENDED
ATTEMPT_ALLOCATED
ATTEMPT_STARTED
ATTEMPT_COMPLETED
ATTEMPT_FAILED
ATTEMPT_INVALID
ATTEMPT_ABORTED
TRIAL_COMPLETED
TRIAL_FAILED
TRIAL_INVALID
TRIAL_ABORTED
TRIAL_EXCLUDED
ARTIFACT_DISPOSITION_RECORDED
ACCESS_INTENT
ACCESS_STARTED
ACCESS_COMPLETED
ACCESS_FAILED
ACCESS_ABORTED
ACCESS_CANCELLED
EXPOSURE_DECISION
CAMPAIGN_EVIDENCE_FROZEN
CHECKPOINT_REFERENCE_RECORDED
CAMPAIGN_ACCOUNTING_CLOSED
REVIEW_DECIDED
PROMOTION_DECIDED
CAMPAIGN_ADJUDICATED
EVENT_SUPERSEDED
```

An unknown event type is rejected. A later event type requires a versioned
contract amendment; it cannot be introduced as an unknown extension field.
The transition names above make the lifecycle tables concrete but do not
freeze every event-specific payload schema in Stage 4a.

Stage 4a freezes an exact unknown-field-rejecting payload schema only for one
golden event type:

- `LEDGER_EPOCH_CREATED` has all-and-only `campaign_scope_ids`, which is the
  empty array for the ledger-global sequence-zero event. The event atomically
  introduces `ledger_id`; its envelope `actor_id` remains claimed attribution,
  not an in-ledger allocation or authorization record.

`TRIAL_ALLOCATED` and every other vocabulary event retain their narrative
semantic requirements, but their exact required/optional/nullable properties,
placement, types, unions, nested schemas, enum values, collection ordering,
subject rules, and cross-field constraints are intentionally not exact payload
schemas in this PR. Before Stage 4b can claim contract-wide fail-closed
validation or full conformance, a separately reviewed machine-readable
per-event payload schema registry must:

1. cover every event type in the closed vocabulary exactly once;
2. key each schema by ledger schema version, event schema version, and event
   type;
3. freeze the exact subject type, payload properties, required/nullable
   status, scalar/collection types, closed enums, ordering/uniqueness rules,
   typed IDs, and cross-field constraints;
4. reject missing, unknown, or duplicate properties for every payload; and
5. include positive and negative vectors plus a deterministic registry digest.

Until that registry is accepted, a prototype may validate only an explicitly
named event-specific subset. It must label that support
`SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`, reject every unimplemented vocabulary
event, including `TRIAL_ALLOCATED`, and every unknown event before append or
action, and must not claim a contract-wide fail-closed ledger, Stage 4b
conformance, campaign completeness, protected-access enforcement, accounting
closure, review, or promotion.

`tests/fixtures/experiment_trial_ledger_event_v1_golden.json` freezes one tiny
ASCII-only synthetic `LEDGER_EPOCH_CREATED` request/event, their exact
canonical bytes/hashes, a source-key reorder with identical identity, and an
actor-attribution mutation with different request/event hashes. The fixture
proves syntax and identity binding only; it does not authenticate or authorize
either synthetic actor. Its
`incomplete_trial_allocation_stub` is rejection evidence only: both its
sequence-zero form and a sequence/hash-repaired form remain invalid while the
payload registry is deferred. The fixture is contract evidence only, not a
production serializer, private fingerprint, trial execution, or storage
implementation.

An implementation must serialize concurrent appends at one atomic
compare-and-swap/transaction boundary so sequences, ID uniqueness, operation
idempotency, and previous hashes cannot race. Torn or partially committed
records are never visible as committed. Recovery preserves the valid prefix,
surfaces incomplete work, and never rewrites historical event bytes.

## Checkpoints, Closure, and Threat Model

A valid hash chain detects ordinary mutation, insertion, deletion, duplication,
and reordering inside the retained stream. It is tamper-evident, not WORM
storage or proof against an actor who can rewrite the entire chain and replace
its head.

Every event has an immutable semantic campaign-scope set. It is empty only for
a genuinely ledger-global event, and a shared event lists every affected
campaign in sorted unique order. Only the epoch's exact
`payload.campaign_scope_ids` placement is frozen in Stage 4a; the registry
must define the exact representation for every other event without changing
these semantics. When a global family or sample was registered without
campaign scope, a campaign-scoped
`CAMPAIGN_ENTITY_BOUND` event binds that global event ID/hash and becomes the
campaign evidence; scope is never inferred retrospectively.

Accounting closure first fixes the last pre-freeze global event as
`evidence_sequence` and `evidence_event_sha256`, then appends
`CAMPAIGN_EVIDENCE_FROZEN` at the next sequence. The freeze event is an
administrative snapshot outside the evidence preimage and therefore has no
self-reference. It defines one immutable campaign evidence prefix:

```text
(ledger_id, evidence_sequence, evidence_event_sha256,
 campaign_evidence_version_id, campaign_evidence_sha256)
```

`campaign_evidence_prefix_v1` is exactly:

```text
schema_version
canonicalization_id
ledger_id
campaign_id
evidence_sequence
evidence_event_sha256
campaign_events
```

The literal values are
`schema_version = campaign_evidence_prefix_v1` and
`canonicalization_id = pit_canonical_json_v1`. `campaign_events` is an ordered
array whose records have all-and-only `(sequence, event_id, event_sha256)`. It
contains all-and-only committed events at or before `evidence_sequence` whose
immutable semantic campaign scope contains the exact campaign ID, sorted by
strictly increasing sequence. The freeze event is necessarily excluded
because its sequence is later. Missing, extra, duplicate, out-of-order, or
unknown fields fail.

The all-and-only prefix object is canonicalized with
`pit_canonical_json_v1`; `campaign_evidence_sha256` is stored outside that
preimage. It binds campaign-relevant events rather than every unrelated event
in the global stream. A valid later suffix is allowed. Verification requires
the retained stream to reach at least `evidence_sequence` and the event/hash at
that exact position to match; mutation of the prefix or truncation below the
anchor fails.

Formal accounting closure also requires an independently retained immutable
checkpoint encoded as `campaign_evidence_checkpoint_v1`. Its exact canonical
preimage has all-and-only these fields:

```text
schema_version
canonicalization_id
checkpoint_id
ledger_id
campaign_id
evidence_sequence
evidence_event_sha256
freeze_event_sequence
freeze_event_id
freeze_event_sha256
campaign_evidence_version_id
campaign_evidence_sha256
sealed_trial_inventory_sha256
sealed_semantic_trial_count
terminal_semantic_trial_count
allocated_attempt_count
terminal_attempt_count
created_at
issuer_authority_reference
```

The literal values are
`schema_version = campaign_evidence_checkpoint_v1` and
`canonicalization_id = pit_canonical_json_v1`. Missing or unknown fields are
rejected. `checkpoint_id`, `campaign_evidence_version_id`, and
`issuer_authority_reference` are nonempty NFC strings; `ledger_id`,
`campaign_id`, and `freeze_event_id` are their typed opaque IDs. All SHA-256
fields are exactly 64 lowercase hexadecimal characters. Both sequences and
all four counts are non-Boolean, nonnegative I-JSON-safe integers.
`created_at` uses `ledger_v1_utc_timestamp`. `checkpoint_sha256` is outside the
preimage and is the SHA-256 of its exact `pit_canonical_json_v1` bytes.

The checkpoint requires `freeze_event_sequence = evidence_sequence + 1`. The
declared `freeze_event_sequence` selects the exact freeze event, which has the
declared sequence, ID, type, campaign scope, SHA-256, and envelope
`previous_event_sha256 = evidence_event_sha256`; the event at
`evidence_sequence` has the exact `evidence_event_sha256`. Its semantic facts
bind the same cutoff, evidence version/SHA-256, and sealed inventory SHA-256.
The checkpoint therefore anchors both the nonrecursive evidence prefix and its
administrative snapshot.

Between that freeze and its accounting closure, the entire target-campaign
projection is all-and-only exactly one `CHECKPOINT_REFERENCE_RECORDED`, binding
the evidence checkpoint's exact ID and SHA-256. Any other event whose scope
contains the target campaign fails closed; events scoped only to other
campaigns and genuinely global events remain allowed. Missing, duplicate,
wrong-scope, out-of-order, wrong-ID, or wrong-digest references fail closed.
The closure, review, and adjudication continue to bind that same checkpoint
ID/SHA-256 and evidence identity.

`sealed_semantic_trial_count` is the cardinality of the unique sealed trial-ID
set; `terminal_semantic_trial_count` is the cardinality of the same set after
every trial has one current legal terminal disposition. `allocated_attempt_count`
is the cardinality of unique allocated attempt IDs whose trial belongs to the
sealed set; `terminal_attempt_count` is the cardinality of that same attempt
set after every attempt has one current legal terminal state. Each pair of
counts must be equal, but equal counts never substitute for exact set equality,
membership, uniqueness, or current-disposition checks. A same-cardinality ID
substitution fails.

Stage 4a adds no open entity map or lifecycle taxonomy. Its synthetic contract
vector uses one fixed all-excluded trial set and zero allocated/terminal
attempts only to exercise exact set/count relations. Within that vector,
conformance reconstructs sealed IDs from its one exact inventory record and
terminal IDs from exact campaign-scoped `TRIAL_EXCLUDED` records; any other
terminal-trial or attempt-lifecycle event is outside the vector and rejected,
not inferred. Formal extraction of sealed IDs, current trial dispositions,
attempt ownership, and current attempt states depends on the complete Stage 4b
per-event payload schema registry; the runtime remains fail closed until that
registry is accepted and enforced.

This is a closure-only, independently retained checkpoint and is distinct from
the earlier self-excluding `campaign_inventory_preseal_head_v1` ordering anchor.
The provider, storage medium, retention, recovery, signature, and trust policy
are deferred to a separate Stage 4b architecture decision.

An accounting-closure record is valid only when:

1. every sealed trial is present exactly once and belongs to the declared
   experiment and global family;
2. every trial and attempt has a legal terminal state;
3. every retry, rerun, clone, and shared-data relation is retained;
4. every expected artifact has one exact disposition;
5. every protected access and exposure decision is terminal;
6. no orphan, duplicate, sequence gap, chain break, unknown field, or
   unresolved correction exists;
7. sealed and terminal semantic-trial counts reconcile, and allocated and
   terminal attempt counts reconcile;
8. the current code/data/environment/config/artifact identities verify;
9. the immutable campaign inventory and any amendments reconcile; and
10. the independently retained checkpoint binds the exact frozen evidence
    prefix.

An open or stale `PLANNED`, `ALLOCATED`, `RUNNING`, access-intent, or
access-started record blocks accounting closure. Accounting closure may still
be statistically invalid or rejected; it proves event completeness, not
research value or final campaign adjudication.

## Review and Promotion Decisions

Review and promotion are immutable events separate from `attempt_state`,
`trial_disposition`, and `candidate_evidence_state`. They bind:

- the exact campaign seal and trial-inventory hash;
- the exact campaign evidence version/prefix and external checkpoint;
- full semantic trial and attempt counts, including all terminal outcomes;
- config, code, data, environment, sample, output, and access identities;
- reviewer identity, authority, non-producing role, and review time;
- frozen gate/threshold version, finding IDs, dispositions, and evidence refs;
- decision outcome, reason, and predecessor/supersession ID; and
- a decision-specific identity projection and SHA-256.

A producer cannot self-certify the same evidence. Appending the decision itself,
an event scoped only to another campaign, or a genuinely unrelated
ledger-global event does not change the bound evidence prefix and does not
self-stale the decision. The freeze, checkpoint-reference, review, promotion,
and adjudication events are administrative suffixes and do not alter their
bound evidence version. A new campaign evidence-bearing correction, identity,
inventory, output, or access event after the prefix makes that evidence version
stale and requires a new accounting closure, checkpoint, and review. A
threshold, finding, or finding-disposition change stales the decision and
requires a new review without rewriting the evidence prefix. Promotion fails
closed for omitted failures, result-informed same-sample amendments, unresolved
findings, post-result threshold changes, an unanchored prefix, or incomplete
accounting closure. Corrections append; they never rewrite the decision.

A formal campaign is fully adjudicated only after accounting closure and one
`CAMPAIGN_ADJUDICATED` event bind:

- exactly one current review outcome and reason;
- exactly one immutable selection disposition and reason for every semantic
  trial (`SELECTED`, `NOT_SELECTED`, `CONTROL_ONLY`, `INVALIDATED`, or
  `NOT_APPLICABLE`);
- exactly one current `candidate_evidence_state` and reason for every evaluated
  factor, strategy, or portfolio object;
- exactly one promotion, rejection, inconclusive, or invalidation decision for
  each object in scope; and
- the accepted review decision plus the same frozen evidence version and
  checkpoint.

The adjudication also binds the exact current accounting-closure event, sealed
inventory, campaign evidence version and SHA-256, independent evidence
checkpoint ID and SHA-256, review event, and promotion-or-disposition decision.
It preallocates and semantically binds an opaque adjudication checkpoint ID,
but it does not contain the future checkpoint digest.

After that event, an independently retained
`campaign_adjudication_checkpoint_v1` anchors the complete verified chain
through the adjudication event. Its exact canonical preimage has all-and-only
these fields:

```text
schema_version
canonicalization_id
checkpoint_id
ledger_id
campaign_id
checkpoint_generation
previous_checkpoint_id
previous_checkpoint_sha256
campaign_evidence_version_id
campaign_evidence_sha256
campaign_evidence_checkpoint_id
campaign_evidence_checkpoint_sha256
adjudication_event_sequence
adjudication_event_id
adjudication_event_sha256
created_at
issuer_authority_reference
```

The literal values are
`schema_version = campaign_adjudication_checkpoint_v1` and
`canonicalization_id = pit_canonical_json_v1`. `checkpoint_sha256` is stored
outside the preimage and is the SHA-256 of its exact canonical bytes.
Missing or unknown fields are rejected. The schema and canonicalization
values, checkpoint/evidence IDs, `created_at`, and issuer authority reference
are strings; IDs and the authority reference are nonempty NFC text,
`ledger_id` and `campaign_id` are their typed opaque IDs, `created_at` uses
`ledger_v1_utc_timestamp`, `adjudication_event_id` is a typed opaque event ID,
and every SHA-256 field is exactly 64 lowercase hexadecimal characters.
`checkpoint_generation` is a positive non-Boolean
I-JSON-safe integer and `adjudication_event_sequence` is a nonnegative
non-Boolean I-JSON-safe integer. Generation 1 has both
`previous_checkpoint_id = null` and
`previous_checkpoint_sha256 = null`. Every successor is exactly the preceding
generation plus one and binds that predecessor's exact checkpoint ID and
SHA-256. Half-null predecessors, skipped generations, two siblings from one
predecessor, forks, replacement, or a digest mismatch fail closed; all old
checkpoint bytes remain retained.

Checkpoint verification requires the complete retained ledger chain to verify
through the exact adjudication sequence, ID, and event SHA-256. The anchor event
must be `CAMPAIGN_ADJUDICATED`, its immutable scope must include the exact
campaign, and its semantics must bind the current exact closure, evidence
checkpoint, review, promotion-or-disposition decision, inventory, evidence
version, and preallocated checkpoint ID. Deleting, modifying, inserting,
duplicating, reordering, replacing, or truncating any closure/review/decision/
adjudication tail record therefore invalidates the checkpoint.

Verification applies those rules to every retained generation, not only the
head. The retained history starts at generation 1, contains every generation
exactly once, and has strictly increasing adjudication anchors. Its checkpoint
generations, independently retained evidence checkpoints, and all
campaign-scoped `CAMPAIGN_ADJUDICATED` events correspond one-to-one in that
order. Each generation revalidates its exact preallocated checkpoint ID,
evidence version and checkpoint, inventory, closure, review, and
promotion-or-disposition decision. An extra, duplicate, or unaccounted
campaign adjudication, a generation reset, or a coordinated rehash whose old
generation no longer matches its terminal bundle fails closed.

The provider-neutral currentness authority key is exactly
`(ledger_id, campaign_id)`. Before any post-adjudication action scoped to that
campaign, exactly `current_checkpoint_generation + 1` becomes pending; skips,
siblings, and any other pending value are invalid. A pending generation is not
fully adjudicated. Publication of its successor must be monotonic, use the
exact prior ID/SHA-256, reject a skip or sibling, retain prior bytes, and
atomically make that successor the unique current generation. Any later event
whose immutable scope contains the campaign -- including a correction,
finding/disposition change, review, promotion, adjudication, or checkpoint
reference -- immediately makes the old checkpoint non-current and requires a
new freeze, closure, review, decision, adjudication, and generation-plus-one
checkpoint. An event scoped only to another campaign or a genuinely unrelated
ledger-global suffix is allowed. No campaign-scoped
`CHECKPOINT_REFERENCE_RECORDED` is appended after the final adjudication
checkpoint; the adjudication event's preallocated opaque ID avoids that
recursive unanchored suffix.

The Stage 4a contract vector may exercise the explicitly permitted unbound
ledger-global `TRIAL_FAMILY_REGISTERED` path as that unrelated suffix. General
machine proof of which payloads are genuinely global remains deferred to the
complete Stage 4b per-event schema registry.

A local old ledger plus its old checkpoint cannot detect that an entire later
campaign suffix and successor checkpoint were both rolled back. Stage 4b must
therefore obtain owner approval for, and verify, an independent append-only and
anti-rollback latestness/concurrency/signature/authorization/recovery
implementation. Stage 4a chooses no provider, physical backend, signature
scheme, or recovery design. Until that external currentness proof exists and
passes failure tests, the full runtime must remain fail closed and no
implementation may claim a formally fully adjudicated campaign.

Neither accounting closure alone nor a missing, unknown, hash-mismatched,
pending, duplicate, stale, non-current, or externally unverified adjudication
checkpoint may be called a complete formal campaign.

## Private Canonical Record and Public Projection

The full canonical ledger is private, repository-external evidence. It must
retain exact identities, names, classifications, and separately controlled
evidence references, but must never embed private source/result artifacts or
any raw rows, outcome-reconstructible payload, metric/performance value,
direction, magnitude, rank, or plot. No runtime may create a default ledger
database or event stream inside the repository.

A tracked public projection is a separate deterministic allowlisted view.
`ledger_public_projection_v1` has all-and-only these top-level keys:

```text
schema_version
canonicalization_id
public_projection_id
public_ledger_id
public_campaign_id
public_campaign_evidence_version_id
policy_states
entity_counts
classification_transitions
redacted_evidence_refs
published_hashes
published_windows
```

`schema_version` is exactly `ledger_public_projection_v1`, and
`canonicalization_id` is exactly `pit_canonical_json_v1`; every other
discriminator value is rejected.

Nested records also have exact schemas:

- `policy_states`: `(policy_id, state)`;
- `entity_counts`: `(entity_type, count)`;
- `classification_transitions`:
  `(exposure_decision_id, sample_id, classification_before,
  classification_after)`;
- `redacted_evidence_refs`: `(evidence_ref_id)`;
- `published_hashes`:
  `(hash_id, sha256, publication_approval_ref_id)`; and
- `published_windows`: `(window_id, publication_approval_ref_id)`.

Every ID uses the accepted Stage 3 `safe_public_id` grammar. Counts are
non-Boolean nonnegative I-JSON-safe integers. States come from the closed
contract vocabularies. Each array is unique and sorted by its first stable ID;
unknown, missing, duplicate, or out-of-order fields fail closed. Window
disclosure is only an opaque approved ID; timestamps or exact bounds are not in
this v1 public schema. Every digest/window disclosure has its own immutable
publication-approval reference.

The all-and-only object above is canonicalized with
`pit_canonical_json_v1`. `public_projection_sha256` is stored outside the
preimage; no other field is excluded. A tracked projection must not contain:

- absolute or relative private paths, file URIs, query strings, hostnames,
  usernames, account/contract IDs, credentials, command arguments, or stack
  traces;
- raw rows, prices, returns, labels, holdings, trades, costs, equity paths,
  metric values, directions, magnitudes, ranks, plots, or free-text result
  summaries; or
- restricted source hashes or digest publication without an immutable approval
  reference.

Redaction never weakens the private exact-window and access audit. A public
projection hash proves only those published bytes. Unknown-field, path,
file-URI, query, username, raw-value, metric/direction/rank, unapproved-window,
and unapproved-hash rejection vectors are mandatory before runtime
publication. The projection is not a substitute for the private ledger,
checkpoint, dataset review, or formal evidence.

Legacy schema-v1 logs may be referenced only as
`backfilled = true`, `DIAGNOSTIC_ONLY` evidence outside formal completeness.
They cannot establish historical preallocation, all-trial accounting, sample
independence, or a formal candidate state.

## Deterministic Stage 4b Conformance Matrix

This matrix cannot be claimed complete until the separately reviewed
machine-readable per-event payload schema registry covers the entire closed
vocabulary. Tests against the one exact epoch payload or semantic trial-parent
facts alone are partial documentation-contract evidence.

| Case | Frozen contract decision | Required later runtime evidence |
| --- | --- | --- |
| `LEDGER-001` | Each ledger-owned typed logical entity ID is allocated once and may be reused by later typed lifecycle/correction/supersession references; the epoch atomically introduces `ledger_id`, while event/operation IDs and sequences identify append/request/commit records. External `actor_id` is claimed attribution outside ledger allocation and grants no authority. The store recomputes the exact request preimage/hash; exact replay is idempotent, while a second ledger-owned entity allocation or conflicting event/operation/sequence reuse fails before action. | Golden request bytes/hash, epoch-genesis introduction, actor syntax/hash-mutation, legal post-allocation references, duplicate/conflicting allocation, reference-before-allocation, wrong-type reference, same-request replay without a second append, same-operation/different-payload, and event/sequence conflict tests; prove authority-dependent behavior remains blocked before an owner-approved Stage 4b mechanism. |
| `LEDGER-002` | A retry before trial closure is a new attempt under the same immutable trial; a post-terminal rerun is a new linked trial. | Lost-ack replay and retained failed-attempt/retry tests with separate trial/attempt counts. |
| `LEDGER-003` | Attempt and trial transitions follow the frozen tables; terminal records never reopen and corrections append. | Reject illegal, backward, post-terminal, and in-place mutation transitions. |
| `LEDGER-004` | Each family/sample parent follows exactly one direct campaign-scoped, ledger-global plus campaign-binding, or accepted external Stage 3 sample-reference path; all required paths, trial, campaign inventory, and attempt finish in their frozen partial order before validation/execution. The inventory seal binds its exact predecessor head and precedes the first attempt/access. Failed-before-output work remains with explicit artifact dispositions. | Accept every legal path and sibling interleaving; reject dangling, ambiguous, mixed-path, wrong-source binding, wrong-scope, path-order-invalid parents, and changed, missing, truncated, or drifted pre-seal heads before action; fault before validator, executor, and first artifact write; prove no action preceded durable allocation. |
| `LEDGER-005` | Planned but unexecuted `ABORTED` or `EXCLUDED` trials remain in campaign multiplicity and cannot be reused or deleted. | Closure reconciliation retains each configured non-run trial and typed reason. |
| `LEDGER-006` | Crash recovery treats committed events as authority, preserves incomplete work, and uses new attempt IDs for retries. | Fault after each lifecycle boundary and reconstruct every valid prefix after restart. |
| `LEDGER-007` | Atomic commit hides torn/partial writes; recovery never presents a valid prefix as a complete ledger or overwrites history. | Truncation/rollback injection at every serialized or transaction boundary. |
| `LEDGER-008` | Concurrent writers serialize unique contiguous sequences, previous hashes, IDs, and idempotent operations. | Multiprocess unique, exact-replay, and conflicting-request races. |
| `LEDGER-009` | The exact campaign-scoped pre-freeze projection plus independent evidence and adjudication checkpoints detect relevant-event omission/mutation, insertion, deletion, reorder, duplication, replacement, and truncation through final adjudication while permitting only other-campaign or genuinely unrelated global suffixes. | Prove all-and-only scoped-event inclusion, relevant mutation sensitivity, pre-freeze prefix anchoring, closure/review/decision/adjudication tail anchoring, unrelated-suffix invariance, post-adjudication same-campaign staleness, and prefix/tail truncation rejection. |
| `LEDGER-010` | Sequence is authoritative; clock order is not. Object-key order is non-semantic and schema-ordered arrays remain semantic. | Equal/backward clocks, duplicate/gapped sequence, key reorder, and array reorder tests. |
| `LEDGER-011` | The common identity envelope and one frozen `LEDGER_EPOCH_CREATED` payload schema reject ambiguous/lossy values and distinguish absent from null. The ledger v1 timestamp subset rejects every `second = 60` without changing canonical JSON serialization. `TRIAL_ALLOCATED` has semantic parent facts only, and contract-wide payload rejection requires the complete machine-readable registry. | Epoch golden bytes plus envelope/epoch-payload duplicate-key, key-collision, Unicode, occurred/recorded timestamp, announced/unannounced June/December leap-second, and unknown-field negatives; semantic trial-parent path facts; then float, default, nullability, union, nested-schema, ordering, and other schema negatives for every registry event before full conformance. |
| `LEDGER-012` | Every expected output is `PRODUCED`, `NOT_PRODUCED`, or `PARTIAL`; completion requires valid required artifact hashes. | Missing, stale, mutated, partial, and zero-output contract tests. |
| `LEDGER-013` | Review/promotion binds the complete sealed inventory and campaign evidence prefix/checkpoint without self-staling; result-informed same-sample amendments cannot be resealed for promotion; full adjudication covers every trial/object and has one independently retained, externally current adjudication-checkpoint generation. | Reject self/stale review, omitted trials, changed relevant evidence, unresolved findings, result-informed same-sample promotion, missing/duplicate dispositions, unanchored promotion, tail tampering/truncation, bad checkpoint lineage, pending/old/missing successors, and post-adjudication same-campaign events; allow terminal promoted/rejected/inconclusive/invalidated outcomes and unrelated suffixes. |
| `LEDGER-014` | Capability validation/consumption and `ACCESS_STARTED` append are one atomic pre-open barrier; actual reader code/environment/evidence and terminal decisions are mandatory. | Accessor spy for failed/mismatched intent, concurrent double redemption, start-append failure, lost acknowledgement, crash, missing terminal, and broader actual scope. |
| `LEDGER-015` | The explicit exposure-fact/atomic-interval transition graph covers aliases, overlap, backfill, unknown impact, derived lineage, correction, the historical interval, and complete design-purpose `SOME` observation without separately confirmed influence; private events and the exact public schema reject values/leaks. | Exhaust every allowed/forbidden transition and overlap join, attempted upgrade, complete design-purpose `SOME` classification, full-ledger raw-value rejection, public unknown/path/URI/query/value/direction/rank rejection, and unapproved hash/window disclosure. |

Documentation-token tests for this matrix are not runtime append-only evidence.
Stage 4b must implement fault injection, restart, concurrency, tamper,
protected-reader, closure, and privacy behavior before claiming conformance.

## Accepted Decisions and Deferred Implementation

Frozen in the accepted Stage 4a contract for v1:

- semantic trials and execution attempts are separate and both fully counted;
- IDs and protected-access intent are durable before action;
- campaign inventory, variation budget, and family lineage are sealed;
- lifecycle and candidate evidence states are independent;
- the common event identity envelope, closed event vocabulary, and one golden
  `LEDGER_EPOCH_CREATED` payload schema use exact typed canonical bytes;
  semantic `TRIAL_ALLOCATED` binding/order facts are non-append evidence, and a
  later complete machine-readable payload registry is required before
  contract-wide fail-closed claims;
- events form an append-only chain and use immutable supersession;
- formal accounting closure requires a separately retained campaign
  evidence-prefix checkpoint and full completion also requires adjudication;
- protected-access semantics require a closed pre-open barrier and
  classification never upgrades; and
- private canonical evidence and tracked public projections are separate.

Deferred to Stage 4b or later:

- complete machine-readable exact payload schemas for every event in the
  closed vocabulary. The Stage 4B-R0 foundation in
  `docs/experiment_trial_ledger_schema_registry_contract.md` supplies the
  registry meta-contract, digest, duplicate-safe parser, and exact epoch
  schema only; its other 36 events remain
  `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`;
- immutable R1 promotion releases now proceed through
  `docs/experiment_trial_ledger_allocation_registration_schema_contract.md`,
  `docs/experiment_trial_ledger_trial_family_registration_schema_contract.md`,
  `docs/experiment_trial_ledger_sample_registration_schema_contract.md`,
  `docs/experiment_trial_ledger_binding_schema_contract.md`,
  `docs/experiment_trial_ledger_trial_allocation_schema_contract.md`,
  `docs/experiment_trial_ledger_campaign_inventory_seal_schema_contract.md`, and
  `docs/experiment_trial_ledger_attempt_allocation_schema_contract.md`.
  These versioned design authorities preserve the R0 fail-closed boundary and
  do not implement append/storage or stateful currentness;
- physical storage backend (`sqlite3`, a deliberately single-writer event
  store, or another reviewed option);
- transaction, locking, journaling, `fsync`, migration, backup, and recovery
  policy;
- private storage location and access controls;
- external checkpoint provider, retention, and any signature policy;
- cross-platform durability claims and test matrix;
- integration with one synthetic workflow, then parameter sweeps and other
  callers in separate reviewable slices; and
- any private-provider adapter or formal campaign.

Later implementation must not retrofit the legacy reporter in place. It must
continue in the separate ledger namespace, use only caller-supplied temporary
storage in tests until the private location is approved, add no heavyweight
dependency without a separate decision, and preserve every failure. Formal
interpretation remains blocked by Stage 4b, Stage 5, and all later applicable
gates.

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

### Ingress, transaction and scoped currentness

Retain the exact `ledger_operation_request_v1` key list above. Caller-supplied
`sequence`, `recorded_at`, `previous_event_sha256` or
`operation_request_sha256` refuse `OPERATION_REQUEST_COMMIT_FIELD_FORBIDDEN`.
The future store uses `BEGIN IMMEDIATE`, fixes `as_of = Clock.now_utc()` once
after lock acquisition and keeps one catalog snapshot stable through commit.
Catalog mutations serialize against this transaction. It resolves complete
pinned bytes, checks content and sole-current evidence, inspects committed
parents/heads, constructs the store-owned envelope, validates raw event bytes
and inserts in the same transaction. Any refusal rolls back event, head, origin
and capability state. Contending writers re-read state after taking the lock.

Sole-current means exactly one accepted, valid, active, unrevoked and
unsuperseded generation at `as_of` in the owning authority/entity/schema stream.
Retrieval alone does not establish currentness. Existing owner evidence is
required; caller role/currentness labels cannot replace it. Missing/ambiguous
owner evidence blocks admission. Generation comparisons do not cross owner
streams even when a local entity or authority ID matches another stream.

### ACCESS resolved tuples and role paths

The schema-registry owner extension freezes payload field types. The exact
authorization tuple is `authorization_record_id`,
`authorization_record_schema_version`, `authorization_record_sha256`.
The intent-authority tuple is `intent_authority_id`,
`intent_authority_generation`, `intent_authority_schema_version`,
`intent_authority_record_sha256`. The start-authority tuple is
`start_authority_id`, `start_authority_generation`,
`start_authority_schema_version`, `start_authority_record_sha256`.
The capability tuple is `access_capability_id`,
`access_capability_record_version`, `access_capability_record_schema_version`,
`access_capability_record_canonicalization_id`, `access_capability_record_sha256`.
Their resolver scope includes ledger, sample, campaign and exact consuming
intent/operation. These are distinct typed owner tuples, never shortened hashes.

| Principal | Required resolved path |
| --- | --- |
| Authorization issuer | `sample_access_authorization_v1.issuer_actor_id` |
| Intent authority issuer | `sample_access_intent_authority_v1.issuer_actor_id` |
| Accessor | `sample_access_authorization_v1.accessor_actor_id` |
| Inventory issuer | `campaign_inventory_record_v1.issuer_actor_id` |
| Seal actor | Retained seal event `actor_id` |
| Intent actor | `sample_access_intent_authority_v1.authorized_actor_id`, equals request actor |
| Start actor | `sample_access_start_authority_v1.authorized_actor_id`, equals request actor |
| Intended capability consumer | `sample_access_capability_record_v1.accessor_actor_id`, equals authorization accessor |

All role values use existing `actor_id`. The first five principals are pairwise
distinct at intent; a prohibited equality refuses `ACCESS_INTENT_ROLE_COLLISION`.
Accessor comes from resolved authorization, not the intent
actor. The full authorization binds sample/campaign, a nonempty affected trial set,
purpose, window, field classes and accessor code/environment exactly to the
intent. Empty `affected_trial_ids` refuses
`ACCESS_INTENT_AFFECTED_TRIAL_SET_EMPTY`. Intent, start and completion payloads each include nonempty typed
`evidence_ref_ids` that resolve as immutable safe evidence references; empty
arrays refuse `{EVENT}_EVIDENCE_REF_SET_EMPTY`. Unknown extra payload fields
remain rejected.
Intent authority additionally binds authorized actor and operation. Start
authority binds retained intent ID/hash, authorized actor, accessor, sample,
campaign and exact reader. When ACCESS_COMPLETED is later enabled,
`ACCESS_STARTED.recorded_at <= started_at <= ended_at`. Path A does not append
ACCESS_COMPLETED. Authorization and both authorities require current
activation/revocation/supersession evidence at the consuming boundary. The
three-field authorization key does not silently gain a generation field;
currentness is resolved from its owner stream.

The complete ACCESS capability binds its ID, ledger/sample/campaign, exact
intent operation, accessor actor, code/environment/window/classes, activation/
expiry and one-use state. It is minted atomically with intent and consumed in
the same transaction as ACCESS_STARTED. Start failure leaves it unconsumed and
the event/head unchanged. EXECUTE instead becomes consumable only after
ATTEMPT_STARTED commits, by the resolved readiness executor. Neither identity
nor a schema-shaped capability record is production authentication.

### Boundary-qualified refusal ownership

The full v7 test table and structured `required_scenarios` freeze every named
counterexample refusal, with each independent variant materialized separately.
The injected ACCESS rollback fixture uses `INJECTED_APPEND_REFUSAL` solely as a
test injection; it is not a new public runtime wire type or schema refusal.
For sample/family/trial/inventory/plan acceptance at each consuming event,
expired/not-yet-active evidence maps to `{EVENT}_ACCEPTANCE_STALE`, superseded
to `_ACCEPTANCE_SUPERSEDED`, revoked to `_ACCEPTANCE_REVOKED`, and absent,
ambiguous or nonaccepted evidence to `_ACCEPTANCE_NOT_CURRENT`.
Publication approval uses the corresponding `{EVENT}_PUBLICATION_APPROVAL_*`
suffixes. Where multiple currentness faults coexist, deterministic precedence
is revoked, superseded, stale, then not-current. Each killing fixture isolates
one fault with all earlier gates valid. No precedence weakens another guard.

Missing complete bytes/required actor or identity fields map to
`{EVENT}_RECORD_INCOMPLETE`, except the specific local lineage refusal.
Resolved subject/scope/source mismatch maps to `RECORD_CONTENT_MISMATCH`.
Role equalities map to `{EVENT}_ROLE_COLLISION`; producer membership separately
maps to `{EVENT}_PRIVATE_INPUT_PRODUCER_ROLE_COLLISION`. An authority that does
not bind its request actor maps to `{EVENT}_AUTHORITY_ACTOR_MISMATCH`.
Readiness currentness maps to `ATTEMPT_STARTED_READINESS_NOT_CURRENT`;
inherited allocation authority staleness and event start-authority staleness
remain the distinct exact codes in the v7 table. Generic missing/noncurrent
authorization or authority maps to `{EVENT}_AUTHORIZATION_NOT_CURRENT` or
`{EVENT}_AUTHORITY_NOT_CURRENT` respectively, unless a more specific v7 code
applies. This section and the corresponding owner extensions own these design
mappings. Packaged schema-validator behavior remains unchanged.

The [v7 design](experiment_trial_ledger_track_b_v7_design.md) freezes the boundary predicates and refusal
inventory. Its synthetic fixtures check design consistency; they do not
demonstrate append, catalog, currentness, capability or SQLite execution.

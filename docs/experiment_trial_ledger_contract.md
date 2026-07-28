# Experiment and Trial Ledger Contract

Status: proposed Stage 4a design contract; acceptance requires final
current-head review, protected merge, and successful exact merge-head CI.
Stage 4b runtime enforcement is not implemented by this document.

Contract ID: `experiment_trial_ledger_contract_v1`.

Contract version: `1.0.0`.

This document is the normative Stage 4a design under
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

Every entity ID is typed, opaque, globally unique, non-content-derived, and
allocated from its own namespace. Its wire form is a lowercase prefix plus 32
lowercase hexadecimal digits, such as `trl_<32-lowercase-hex>`. Stage 4b must
freeze and test the production entropy, collision, and concurrent-allocation
policy before runtime use; deterministic golden IDs prove syntax only. Content
hashes never substitute for preallocated entity IDs.

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
may run before the relevant allocation event is durably committed. The parent
order is exact:

```text
LEDGER_EPOCH_CREATED
  -> CAMPAIGN_ALLOCATED
  -> EXPERIMENT_ALLOCATED and TRIAL_FAMILY_REGISTERED
  -> SAMPLE_REGISTERED where a sample is referenced
  -> TRIAL_ALLOCATED
  -> CAMPAIGN_INVENTORY_SEALED
  -> ATTEMPT_ALLOCATED or ACCESS_INTENT
```

Every referenced parent must already exist in the same verified ledger epoch
or in the accepted Stage 3 sample registry. Dangling, mismatched, later-created,
or out-of-order parents fail before commit and also fail closure verification.

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
hash without appending. Reusing the operation ID, event ID, entity ID, or
sequence with different request bytes fails closed before action.

## Campaign Inventory and Trial Counting

Before the first attempt or protected access, a campaign commits
`CAMPAIGN_INVENTORY_SEALED` containing:

- the ordered all-and-only trial IDs and their configuration hashes;
- every experiment and global trial-family relation;
- the trial budget and allowed variation axes;
- sample roles and protected-access budget;
- frozen review, promotion, cost, timing, and statistical policy references;
- the canonical inventory bytes and SHA-256; and
- the current ledger checkpoint.

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

Raw floating-point objects, implicit defaults, unordered identity-bearing
collections, unknown fields, lossy key coercion, and mutable path-based
identity are not valid bindings. Absent and schema-declared `null` remain
different. Configuration, code, data, environment, or sample changes require a
new trial.

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
3. one frozen outcome-reconstructible evaluation with no design influence is
   `historical_evaluation` for later campaigns;
4. registered selection inside its frozen trial budget is `validation`; and
5. only a prospectively sealed, information-independent, never-accessed sample
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

The event schema rejects missing or unknown fields. `sequence` is a
non-Boolean, zero-based, contiguous I-JSON-safe integer assigned at the
serialized commit boundary. The first event has
`previous_event_sha256 = null`; every later event contains the exact lowercase
SHA-256 of the immediately prior canonical event preimage. Commit sequence is
authoritative; timestamps never reorder events.

`ledger_event_identity_v1` is the exact object containing all-and-only the
fields above. Its typed values use the accepted `pit_canonical_json_v1`
preprocessing and exact RFC 8785/JCS UTF-8 serialization. The stored
`event_sha256` is the lowercase SHA-256 of those bytes and is outside the
preimage. No other field is ignored. Duplicate JSON properties, invalid or
non-NFC text, ambiguous timestamps or numbers, raw floats, NaN/infinity,
non-string keys, unknown properties, and invalid typed IDs fail closed rather
than being coerced.

`tests/fixtures/experiment_trial_ledger_event_v1_golden.json` freezes one tiny
ASCII-only synthetic allocation request/event, their exact canonical
bytes/hashes, a source-key reorder with identical identity, and an identity
mutation with different request/event hashes. It is contract evidence only,
not a production serializer, private fingerprint, trial execution, or storage
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

Every event-specific payload contains a required `campaign_scope_ids` array of
sorted unique campaign IDs. It is empty only for a genuinely ledger-global
event. A shared event lists every affected campaign. When a global family or
sample was registered before a campaign existed, a campaign-scoped
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
immutable payload `campaign_scope_ids` contains the exact campaign ID, sorted
by strictly increasing sequence. The freeze event is necessarily excluded
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
checkpoint containing exactly a checkpoint schema/version, checkpoint ID,
canonicalization ID, ledger ID, evidence sequence/event SHA-256,
`freeze_event_sequence`, `freeze_event_sha256`, campaign evidence
version/SHA-256, sealed trial-inventory SHA-256, expected/actual entity counts,
creation time, authorized issuer/authority reference, and checkpoint SHA-256.
The checkpoint digest is outside its exact canonical preimage. The freeze
event sequence is exactly `evidence_sequence + 1`; the checkpoint therefore
anchors both the nonrecursive evidence prefix and its administrative snapshot.
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
7. expected and actual semantic-trial and attempt counts reconcile;
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

A producer cannot self-certify the same evidence. Appending the decision itself
or an unrelated campaign event does not change the bound evidence prefix and
does not self-stale the decision. The freeze, checkpoint-reference, review,
promotion, and adjudication events are administrative suffixes and do not
alter their bound evidence version. A new campaign evidence-bearing correction,
identity, inventory, output, or access event after the prefix makes that
evidence version stale and requires a new accounting closure, checkpoint, and
review. A threshold, finding, or finding-disposition change stales the decision
and requires a new review without rewriting the evidence prefix. Promotion
fails closed for omitted failures, result-informed same-sample amendments,
unresolved findings, post-result threshold changes, an unanchored prefix, or
incomplete accounting closure. Corrections append; they never rewrite the
decision.

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

Neither accounting closure alone nor a missing/duplicate/stale adjudication may
be called a complete formal campaign.

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

| Case | Frozen contract decision | Required later runtime evidence |
| --- | --- | --- |
| `LEDGER-001` | Typed entity/event IDs are unique; the store recomputes the exact request preimage/hash; exact operation replay is idempotent and conflicting reuse fails before action. | Golden request bytes/hash, duplicate allocation, same-request replay, same-operation/different-payload, and same-ID/different-request tests. |
| `LEDGER-002` | A retry before trial closure is a new attempt under the same immutable trial; a post-terminal rerun is a new linked trial. | Lost-ack replay and retained failed-attempt/retry tests with separate trial/attempt counts. |
| `LEDGER-003` | Attempt and trial transitions follow the frozen tables; terminal records never reopen and corrections append. | Reject illegal, backward, post-terminal, and in-place mutation transitions. |
| `LEDGER-004` | Parent entities, trial, campaign inventory, and attempt allocate in the frozen order before validation/execution; failed-before-output work remains with explicit artifact dispositions. | Reject dangling/out-of-order parents; fault before validator, executor, and first artifact write; prove no action preceded durable allocation. |
| `LEDGER-005` | Planned but unexecuted `ABORTED` or `EXCLUDED` trials remain in campaign multiplicity and cannot be reused or deleted. | Closure reconciliation retains each configured non-run trial and typed reason. |
| `LEDGER-006` | Crash recovery treats committed events as authority, preserves incomplete work, and uses new attempt IDs for retries. | Fault after each lifecycle boundary and reconstruct every valid prefix after restart. |
| `LEDGER-007` | Atomic commit hides torn/partial writes; recovery never presents a valid prefix as a complete ledger or overwrites history. | Truncation/rollback injection at every serialized or transaction boundary. |
| `LEDGER-008` | Concurrent writers serialize unique contiguous sequences, previous hashes, IDs, and idempotent operations. | Multiprocess unique, exact-replay, and conflicting-request races. |
| `LEDGER-009` | The exact campaign-scoped pre-freeze projection plus an independent checkpoint detects relevant-event omission/mutation, insertion, deletion, reorder, duplication, and truncation below the anchor while permitting administrative and unrelated suffixes. | Prove all-and-only scoped-event inclusion, relevant mutation sensitivity, freeze/review/decision/unrelated-suffix invariance, and prefix-truncation rejection. |
| `LEDGER-010` | Sequence is authoritative; clock order is not. Object-key order is non-semantic and schema-ordered arrays remain semantic. | Equal/backward clocks, duplicate/gapped sequence, key reorder, and array reorder tests. |
| `LEDGER-011` | Typed canonicalization rejects ambiguous/lossy configuration and distinguishes absent from null. | Golden bytes plus duplicate-key, key-collision, float, Unicode, timestamp, default, unknown-field, and unordered-set negatives. |
| `LEDGER-012` | Every expected output is `PRODUCED`, `NOT_PRODUCED`, or `PARTIAL`; completion requires valid required artifact hashes. | Missing, stale, mutated, partial, and zero-output contract tests. |
| `LEDGER-013` | Review/promotion binds the complete sealed inventory and campaign evidence prefix/checkpoint without self-staling; result-informed same-sample amendments cannot be resealed for promotion; full adjudication covers every trial/object. | Reject self/stale review, omitted trials, changed relevant evidence, unresolved findings, result-informed same-sample promotion, missing/duplicate dispositions, and unanchored promotion; allow the decision append and unrelated suffix. |
| `LEDGER-014` | Capability validation/consumption and `ACCESS_STARTED` append are one atomic pre-open barrier; actual reader code/environment/evidence and terminal decisions are mandatory. | Accessor spy for failed/mismatched intent, concurrent double redemption, start-append failure, lost acknowledgement, crash, missing terminal, and broader actual scope. |
| `LEDGER-015` | The explicit exposure-fact/atomic-interval transition graph covers aliases, overlap, backfill, unknown impact, derived lineage, correction, and the historical interval; private events and the exact public schema reject values/leaks. | Exhaust every allowed/forbidden transition and overlap join, attempted upgrade, full-ledger raw-value rejection, public unknown/path/URI/query/value/direction/rank rejection, and unapproved hash/window disclosure. |

Documentation-token tests for this matrix are not runtime append-only evidence.
Stage 4b must implement fault injection, restart, concurrency, tamper,
protected-reader, closure, and privacy behavior before claiming conformance.

## Proposed Decisions and Deferred Implementation

Frozen in this Stage 4a proposal for v1:

- semantic trials and execution attempts are separate and both fully counted;
- IDs and protected-access intent are durable before action;
- campaign inventory, variation budget, and family lineage are sealed;
- lifecycle and candidate evidence states are independent;
- events use exact typed canonical bytes, an append-only chain, and immutable
  supersession;
- formal accounting closure requires a separately retained campaign
  evidence-prefix checkpoint and full completion also requires adjudication;
- protected access fails closed and classification never upgrades; and
- private canonical evidence and tracked public projections are separate.

Deferred to Stage 4b or later:

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

The next implementation PR must not retrofit the legacy reporter in place.
It must introduce a separate ledger namespace, use only caller-supplied
temporary storage in tests until the private location is approved, add no
heavyweight dependency without a separate decision, and preserve every
failure. Formal interpretation remains blocked by Stage 4b, Stage 5, and all
later applicable gates.

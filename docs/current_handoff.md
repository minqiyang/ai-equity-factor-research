# Current Handoff

Updated: 2026-07-28 for the Stage 4B-R1B campaign/experiment allocation
release.

## Canonical State

- Long-term evidence policy: `docs/research_program_charter.md`.
- Accepted Stage 1 split authority: `docs/purged_bounded_split_contract.md`.
- Accepted Stage 2 timing authority:
  `docs/signal_execution_timing_contract.md`.
- Accepted Stage 3 data authority:
  `docs/point_in_time_data_methodology_contract.md`.
- Accepted Stage 4a design authority:
  `docs/experiment_trial_ledger_contract.md`.
- Accepted Stage 4B-R0 registry authority:
  `docs/experiment_trial_ledger_schema_registry_contract.md`.
- Accepted Stage 4B-R1A and active Stage 4B-R1B authority:
  `docs/experiment_trial_ledger_allocation_registration_schema_contract.md`.
- Active roadmap: `docs/current_roadmap.md`.
- Short operational controller: `docs/codex_long_running_controller.md`.
- Verified starting `origin/main`: `9cf5325`, the protected merge of PR #166.
- Starting validation: 913 tests passed with two platform-conditional
  wide-`longdouble` skips; Ruff, compilation, and exact merge-head GitHub CI
  passed.
- Stage 1 split isolation and Stage 2 signal/execution timing are complete on
  protected main. Stage 3 methodology is accepted; it does not accept a
  provider, dataset, license, universe, field, benchmark, or historical claim.
- Stage 4a PR #164 passed 863 tests, Ruff, compilation, build, Skill, repo-map,
  privacy/Unicode/diff, final current-head review, protected merge, and exact
  merge-head GitHub CI at `27f0497`.
- Stage 4B-R0 PR #165 passed 912 tests, Ruff, compilation, build, deterministic
  repo-map, package-resource, privacy/Unicode/diff, three independent final
  reviews, exact-head CI, final current-head Codex review, protected merge, and
  exact merge-head GitHub CI at `4c874eb`.
- Stage 4B-R1A PR #166 passed 913 tests, Ruff, compilation, deterministic
  repo-map, Skill audit, source/sdist/wheel R0 package parity, privacy/Unicode/
  diff gates, three independent post-fix reviews, exact-head CI, one final
  current-head Codex review, protected merge, and exact merge-head GitHub CI
  at `9cf5325`.
- The accepted Stage 4a contract freezes ledger evidence semantics only. The existing
  JSON writer and registry remain diagnostic/legacy; no append-only runtime,
  backend, private ledger, campaign, or formal interpretation is implemented.
  Its exact Stage 4a event payload coverage is deliberately limited to the
  common identity envelope and the synthetic `LEDGER_EPOCH_CREATED` payload.
  The epoch atomically introduces `ledger_id`; `actor_id` is an externally
  assigned claimed-attribution reference rather than a ledger-owned
  allocation. Stage 4a binds its syntax into canonical identity but does not
  authenticate it or grant any permission. Formal behavior that depends on
  actor authority remains fail closed pending a separate Stage 4b owner
  decision.
  `TRIAL_ALLOCATED` retains complete normative binding and parent-order
  semantics but must fail closed as `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY` until
  Stage 4b supplies a separately reviewed complete machine-readable event
  schema registry. A ledger-owned logical entity is allocated once; later typed
  lifecycle, correction, supersession, review, and decision events may
  reference that existing entity without reallocating it.
  Each initial campaign-inventory seal binds a nonrecursive
  `campaign_inventory_preseal_head_v1` anchor inside its request/event
  preimage. The implementation must compare that anchor to the actual current
  stream head and assign the seal sequence/envelope previous hash at one
  serialized atomic boundary before any attempt or access. It is an ordering
  anchor, not the later independently retained closure checkpoint.
  Ledger event timestamps use a conservative application profile that rejects
  every leap second because no immutable leap-second table is pinned. The
  exact `campaign_evidence_checkpoint_v1` reconstructs the scoped evidence
  prefix and binds its cutoff, freeze, inventory, counts, and unique ordered
  reference. A separate version-linked
  `campaign_adjudication_checkpoint_v1` anchors every terminal
  closure/review/promotion/adjudication generation; any later same-campaign
  event makes the old generation non-current.
  Its final P1/P2 remediation passed seven focused contract tests
  (six adjudication-specific), 28 structure tests, and the full 863-test suite
  with two
  platform-conditional skips, plus Ruff, diff, Unicode, and independent
  integrity/scope re-review. The authoritative publication state is the
  protected-main merge and exact merge-head CI, not the prose SHA alone.
- Current phase: research-only. No vendor download, credentials, brokerage,
  orders, paper deployment, live deployment, or real-money execution.

## Research Charter Decision

The program now separates factor, strategy, portfolio, and execution evidence.
Future formal historical interpretation requires:

- point-in-time, tradable, survivorship-aware data methodology;
- frozen timing, execution, benchmark, cost, and sample contracts;
- immutable all-trial accounting, including failures and protected-sample
  access;
- dependence-aware inference and multiple-testing controls;
- purged walk-forward evaluation with correct sample classification; and
- independent reproduction before any later LEAN parity candidacy.

This charter stage changes documentation and workflow control only. It does not
add factors, alter calculations, read private performance values, generate
research evidence, or authorize paper/live behavior.

## Stage 1 Split Decision

`docs/purged_bounded_split_contract.md` defines six explicit inclusive bounds,
hard bounded-test semantics, complete label-interval ownership,
horizon-aware purge, optional embargo, raw-axis masking, warm-up/down metadata,
and typed consumer coverage. `src/features/validation.py` implements the
contract for all four current consumers. Deterministic mutation tests prove
that post-test or cross-edge values cannot change earlier eligible labels or
diagnostics; zero-eligible and metric-empty windows remain visible as
`INVALID`.

## Stage 2 Timing Decision

The implemented policy is
`after_close_signal_next_observed_close_v1`. A close-derived signal becomes
available after its stamped close, uses a non-Boolean observed-row lag of at
least one inside an exact bounded accounting window, executes an idealized
frozen target at the next supported close, and first earns the following
close-to-close return.

`docs/signal_execution_timing_contract.md` is the detailed authority. The
runtime requires exact source axes, bounds, typed source provenance, strict
signal/price/capital values, decision-time target freezing, ordered
drift/trade/cost accounting, a zero initialization anchor, common measured
metric rows, exact benchmark dates, terminal-row accounting, and typed timing
metadata/ledger evidence. This is idealized close-reset software behavior, not
order-fill, capacity, real-data, brokerage, or LEAN evidence.

Stage 2b now requires explicit exact evaluation bounds and exact full-source
price/signal axes plus exact source provenance whose caller-declared baseline
is captured before later mutation.

## Stage 3 Data Methodology Decision

`docs/point_in_time_data_methodology_contract.md` separates:

1. `methodology_contract_accepted`;
2. `dataset_manifest_reviewed`; and
3. `formal_interpretation_eligible`.

This stage can establish only the first gate. The contract requires immutable
data identity, canonicalization, environment, and lineage; evidence-backed
license/entitlement; an exact-version non-self-issued dataset-review decision;
bitemporal availability and revisions; permanent security/listing identity;
historical membership; delistings/corporate actions and terminal value; field
semantics; missing/stale states; calendar/timezone; benchmark/risk-free policy;
a private full manifest with safe public projection; and holdout-exposure
downgrade rules.

The private 2025-05-01 through 2026-05-31 diagnostic interval is confirmed
`historical_evaluation`, not a pristine holdout. Stage 4 must implement the
append-only trial/access ledger. No current dataset becomes `formal_ready`
through this documentation contract.

## Accepted Stage 4a Experiment and Trial Ledger Decision

`docs/experiment_trial_ledger_contract.md` separates one frozen semantic trial
from every execution attempt. It requires:

- typed campaign, experiment, global trial-family, trial, attempt, sample,
  exposure, artifact, event, review, and promotion identities;
- durable trial/attempt allocation before validation or execution;
- a durable exact protected-access intent capability before content release;
- sealed all-and-only campaign inventories plus immutable amendments;
- separate attempt, trial-disposition, and candidate-evidence states;
- explicit produced, partial, and not-produced artifact dispositions;
- exact `pit_canonical_json_v1` event bytes, an append-only previous-hash chain,
  and correction through supersession only;
- one exact synthetic epoch payload plus non-append trial-parent and
  entity-allocation/reference semantic facts; the epoch atomically introduces
  `ledger_id`, while its external `actor_id` is claimed attribution only and
  the complete per-event payload registry remains an explicit Stage 4b
  prerequisite;
- an independently retained head/checkpoint because a chain alone cannot prove
  that a valid tail was not deleted, including exact evidence-prefix and
  version-linked adjudication checkpoints;
- terminal trial/access reconciliation before campaign closure; and
- a repository-external private ledger with a deterministic, allowlisted safe
  public projection.

The current schema-v1 JSON logs cannot prove these properties and remain
`DIAGNOSTIC_ONLY` legacy evidence. Stage 4a added no runtime, storage backend,
dependency, migrated log, research trial, private access, or generated
performance evidence.

## Accepted R0/R1A And Active R1B Allocation Release

Six non-overlapping read-only audits found that Stage 4a intentionally froze
only the common event envelope and `LEDGER_EPOCH_CREATED` payload. Exact
subjects, scopes, fields, nullability, unions, nested structures, enums, and
cross-field constraints remain under-specified for the other 36 event types.
Neither narrative field lists nor the synthetic checkpoint helpers are valid
wire-schema authorities.

`docs/experiment_trial_ledger_schema_registry_contract.md` therefore defines a
small fail-closed R0 boundary:

- one self-contained, packaged ASCII canonical JSON registry;
- exact 37-event vocabulary and disjoint supported/incomplete partitions;
- a duplicate-property-safe standard-library parser;
- deterministic all-content registry SHA-256 with an external sidecar;
- the exact Stage 4a epoch schema and synthetic conformance vectors; and
- `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY` rejection for every other known event,
  plus `UNKNOWN_EVENT_TYPE` for anything outside the vocabulary.

R0 does not accept a complete payload registry and does not implement append,
storage, allocation, lifecycle, access, closure, checkpoint currentness,
review, or promotion behavior. Trial count, attempt count, and holdout access
remain zero. Backend, private location, transaction/recovery, currentness,
actor authority/signature, fork handling, and new production dependencies
remain separate owner decisions.

PR #165 accepted that R0 authority on protected main without changing the
accepted Stage 4a event semantics. Its packaged registry supports only
`LEDGER_EPOCH_CREATED` and rejects the other 36 known events as
`SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.

Six new non-overlapping read-only audits then examined the
allocation/registration family. They agreed that direct promotion would
launder narrative or test-helper facts into false wire-schema coverage. The
owner selected architecture A:

- preserve R0 registry JSON and its sidecar byte-for-byte;
- retain the accepted 37-event vocabulary;
- publish R1B as separate registry/schema-language version `0.2.0` and require
  every later promotion batch to publish a new immutable registry release;
- make campaign and experiment allocation reservation-only;
- use the allocated, registered, or bound entity as subject;
- place `campaign_scope_ids` explicitly in each family payload and require
  every shared direct-scope campaign to be allocated first;
- add only closed tagged-union, array/path-membership, and `safe_public_id`
  capabilities in the versioned R1 language; and
- require future exact retrievable family-definition and Stage 3 sample
  authorities, without accepting either authority and without inferring
  non-campaign typed-ID prefixes from helpers or rejected fixtures.

`docs/experiment_trial_ledger_allocation_registration_schema_contract.md`
records that design. R1A promotes no event and modifies no registry artifact or
runtime. Family, sample, and binding events remain blocked by exact authority,
anti-reset, alias/currentness, finite-bound, and privacy decisions.

Stage 4B-R1A is accepted on protected main through PR #166 and exact merge-head
CI. For R1B, the owner selected option `E1`: the exact experiment namespace is
`exp_<32 lowercase hex>`. That explicit owner ratification, not any helper,
narrative example, or rejected fixture, is the wire-schema authority.

R1B publishes immutable registry `0.2.0`, implements and meta-tests all three
schema-language `0.2.0` additions, and preserves R0 artifact bytes and
validator behavior. Its explicit R1 authority supports exactly three event
types: epoch plus reservation-only campaign and experiment allocation. The
other 34 events remain `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`. Registry acceptance
does not implement append, storage, allocation uniqueness, parent existence,
authorization, ordering, campaign execution, protected access, or research
interpretation. Each later schema-promotion batch must publish a new immutable,
monotonically versioned registry artifact and digest rather than overwrite an
accepted release.

## Verified Implementation Baseline

- Strict local CSV validation and metadata inventory; no downloader.
- Momentum, reversal, volatility, liquidity helpers, Alpha #009/#012,
  preprocessing, combination, and basic diagnostics.
- One bounded long-only equal-weight ranking engine with enforced nonzero
  observed-row lag, frozen targets, drift-aware accounting, signed trades,
  turnover, fixed costs/slippage, optional position clipping, residual cash,
  exact benchmark accounting, and a typed timing ledger.
- Common-window return/benchmark metrics, initial-capital drawdown, tracking
  error, holdings/concentration, and completed holding-episode metrics.
- Deterministic synthetic/fixture reports and a registry of existing JSON logs.
- Private-output-only EODHD diagnostics on a fixed cohort.
- Non-executing LEAN metadata/signal scaffold.

Do not infer a reusable strategy factory, point-in-time universe engine,
calibrated impact/capacity model, immutable all-trial ledger, statistical
validation package, LEAN runtime, or empirical factor/strategy validity.

## Audited Findings

Remaining high-priority methodology blockers:

1. Private diagnostics were calculated and reviewed through 2026-06-26. The
   2025-05-01 through 2026-05-31 interval is confirmed
   `historical_evaluation` and cannot be upgraded to a holdout.
2. Static-universe, delisting, corporate-action, adjusted price/volume,
   provenance/license, and benchmark methodology gaps block formal real-data
   interpretation.

Stage 1 resolves the prior cross-split-label and unbounded-test defects in the
current consumers. Stage 2 resolves the close-only runtime timing, target,
evaluation-window, metric-anchor, benchmark-window, capital-validity, and
metadata contract. Stage 3 defines the data-methodology contract but does not
verify a dataset. Stage 4a defines the accepted trial-ledger contract but does
not enforce it. Stage 4B-R0 only makes its one exact event and every
incomplete/unknown event machine-detectable and fail closed. Stage 4B-R1A
selects the versioned minimal allocation/registration architecture but still
promotes no event. Stage 4B-R1B adds shape validation for only reservation-only
campaign/experiment allocation; it does not implement the stateful ledger.
Additional
blockers include incomplete runtime trial retention,
absent dependence/multiplicity/overfit controls, and diagnostic-only
cost/capacity assumptions. See `docs/current_roadmap.md` for the prioritized
list.

The 2026-07-11 conformance audit remains historical evidence at its audited
SHA. Its prior no-P1/P2 conclusion does not supersede these later findings.

## PR #148 Interaction

At the last verification, PR #148 was an independent Draft governance PR from
an older base that changed only `AGENTS.md`. It was not a predecessor for PRs
#158-#166. The Stage 4B-R1B implementation slice does not edit `AGENTS.md`,
merge/close that draft, or overwrite its policy.

## Next Safe Stage

Complete Stage 4B-R1B in the current isolated worktree. Preserve R0
byte/hash/behavior/package parity; publish the separate immutable `0.2.0`
authority; validate all three closed DSL additions; keep the exact E1
experiment namespace; and promote only reservation-only
`CAMPAIGN_ALLOCATED` and `EXPERIMENT_ALLOCATED`. Require independent positive
fixtures, literal digest and event-set oracles, subject/scope/namespace
killers, arbitrary-promotion rejection, focused and full validation,
independent read-only review, exact-head CI, one final current-head Codex
review, normal protected merge, and exact merge-head CI. Do not enable
auto-merge or merge while CI or review is pending.

After R1B is accepted on protected main, begin a separate R1C design-first
branch. R1C must select the exact trial-family namespace, exact retrievable
family-definition authority and versioning, acceptance/reviewer-independence
architecture, anti-reset/currentness policy, and finite shared direct-scope
bound before promoting `TRIAL_FAMILY_REGISTERED`. Those materially different
valid choices require a new owner decision; do not infer them from helpers or
narrative examples.

Do not call the registry accepted until all 37 events have exact schemas and no
incomplete or wildcard entry remains.

Only after the registry boundary is reviewable should Stage 4b select a
physical backend, private storage location, transaction/recovery policy, or
external checkpoint/currentness authority; materially different valid
architecture choices require an explicit owner decision. That decision must
cover append-only anti-rollback, latest/pending generation queries, fork
handling, authority/signature policy, recovery, and retention. Runtime work
must use a separate ledger namespace and caller-supplied temporary storage in
tests until the private-location decision is accepted. Require behavioral
fault, restart, concurrency, tamper, rollback, access-capability,
campaign-closure, and privacy tests. Do not retrofit the legacy writer, run
real-data campaigns, or interpret historical diagnostics while Stage 4b and
later statistical gates remain incomplete.

## Freshness Checklist

Before continuing:

- fetch and compare `origin/main`;
- verify the previous required stage PR is merged;
- classify unrelated open drafts separately from predecessor gates;
- use a clean branch/worktree and preserve unrelated local changes;
- rerun focused and baseline validation; and
- reread this handoff and the canonical roadmap if the remote head changed.

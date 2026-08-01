# Current Handoff

Updated: 2026-07-31 for the eighteenth PR #177 review-remediation round.

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
- Accepted Stage 4B-R1A/R1B authority:
  `docs/experiment_trial_ledger_allocation_registration_schema_contract.md`.
- Accepted Stage 4B-R1C authority:
  `docs/experiment_trial_ledger_trial_family_registration_schema_contract.md`.
- Accepted Stage 4B-R1D authority:
  `docs/experiment_trial_ledger_sample_registration_schema_contract.md`.
- Accepted Stage 4B-R1E authority:
  `docs/experiment_trial_ledger_binding_schema_contract.md`.
- Accepted Stage 4B-R1F authority:
  `docs/experiment_trial_ledger_trial_allocation_schema_contract.md`.
- Accepted Stage 4B-R1G authority:
  `docs/experiment_trial_ledger_campaign_inventory_seal_schema_contract.md`.
- Accepted Stage 4B-R1H authority:
  `docs/experiment_trial_ledger_attempt_allocation_schema_contract.md`.
- Accepted Stage 4B-R1I authority:
  `docs/experiment_trial_ledger_attempt_start_schema_contract.md`.
- Active Track A/Track B scope authority:
  `docs/eodhd_sp500_diagnostic_campaign_contract.md`.
- Active roadmap: `docs/current_roadmap.md`.
- Short operational controller: `docs/codex_long_running_controller.md`.
- Current protected `origin/main`: `6386c59`, the protected merge of PR #176.
  Its exact merge-head CI run `30492542975` succeeded.
- PR #177 is the current open scope-reset gate on
  `codex/eodhd-diagnostic-scope-reset`; it is not merged. Initial review of
  `3df9a21` found two P1 and two P2 protocol gaps, which commit `97425c0`
  remediated. The second review of `97425c0` found three P2 gaps remediated by
  `4d832c7`; the third review of `4d832c7` found two P2 gaps remediated by
  committed and pushed head `6a7445f`. Exact-head CI run `30684864773` passed
  for `6a7445f`. Its fourth review found two P2 gaps remediated by committed and
  pushed head `e5d72c2`; exact-head CI run `30685562719` passed. The fifth
  review of `e5d72c2` found one P2 remediated by committed and pushed head
  `0179ebb`; exact-head CI run `30686127537` passed. The sixth review of
  `0179ebb` found one P1 and one P2 remediated by committed and pushed head
  `b8149c2`; exact-head CI run `30686852275` passed. The seventh review of
  `b8149c2` found one P2 remediated by committed and pushed head `1f6c801`;
  exact-head CI run `30687469154` passed. The eighth review of `1f6c801` found
  one P2 remediated by committed and pushed head `86f6929`; exact-head CI run
  `30687930346` passed. The ninth review of `86f6929` found one P2: the
  `LOW_VOL_3M` one-day return kind and invalid-anchor behavior were ambiguous.
  That finding was remediated by committed and pushed head `a5b6695`; CI run
  `30688393600` passed on that exact head. The tenth review of `a5b6695` found two P2
  gaps: the forward-return formula/anchors and centered-versus-uncentered
  bootstrap draw reuse were ambiguous. The current branch-head snapshot
  containing this handoff freezes a fail-closed simple endpoint return and one
  shared bootstrap row-index draw across factors and both distributions, with
  no second RNG pass. It includes endpoint and segmented shared-draw golden
  fixtures. Those gaps were remediated by committed and pushed head `bc4c201`;
  exact-head CI run `30689003562` passed. The eleventh review of `bc4c201`
  found one P2: momentum and reversal anchor validation was incomplete. The
  strict-anchor gap was remediated by committed and pushed head `d2ac8cd`;
  exact-head CI run `30689676655` passed. The twelfth review of `d2ac8cd`
  found one P2: the 253/22 lookback counts could be misread as requiring every
  intermediate price rather than only each formula's two referenced anchors.
  The current branch-head snapshot containing this handoff freezes those
  counts as common-calendar position spans, requires exactly the two formula
  anchors to be observed and valid, and gives an interior missing or invalid
  adjusted-close value no factor-value or eligibility effect. Separate MOM/
  REV interior-missing fixtures reject the forbidden full-window-contiguity
  interpretation. That gap was remediated by committed and pushed head
  `12cacaa`; exact-head CI run `30690253765` passed. The thirteenth review of
  `12cacaa` found two P2 gaps: the generic complete-history eligibility gate
  still contradicted endpoint-only MOM/REV behavior, and the machine-readable
  prospective start did not wait for code and dataset-policy freezes. The
  current branch-head snapshot replaces the generic gate with factor-specific
  lookback-position and referenced-anchor validity, binds targets and benchmark
  membership to that rule, and starts prospective counting strictly after the
  latest protocol, runner-code, and dataset-policy freeze timestamp. It adds
  integrated target and staggered-freeze boundary fixtures. Those gaps were
  remediated by committed and pushed head `fc561e4`; exact-head CI run
  `30690874955` passed. The fourteenth review of `fc561e4` found two P2 gaps:
  prospective counting did not aggregate factor-specific eligibility, and the
  random baseline did not freeze behavior for invalid factor months. That
  remediation required all three factor rebalances to be
  decision-time valid for the prospective counter, retains subset-valid dates
  without counting them, and gives both baselines the same retained invalid
  zero-target/full-cash behavior for sparse, tied, or duplicate-key months.
  Random draws are not consumed for invalid months. Those gaps were remediated
  by committed and pushed head `e9c2707`; exact-head CI run `30691526104`
  passed. The fifteenth review of `e9c2707` found one P1 and one P2: segments of
  at most six rows were copied by the bootstrap, and the first-eligibility key
  freeze did not aggregate staggered factor eligibility. The current branch-
  head snapshot uses one-row within-segment resampling for lengths two through
  six, rejects degenerate resampling support, and freezes each listing key once
  campaign-wide at earliest any-factor eligibility. Sixty-record short-segment
  and staggered-factor key fixtures retain the exact 14-trial inventory. Those
  gaps were remediated by committed and pushed head `46679c4`; exact-head CI
  run `30692101398` passed. The sixteenth review of `46679c4` found two P2
  gaps: the prior invalid-month rule incorrectly turned the equal-weight
  baseline and primary benchmark into cash on a tied factor month, and the
  classifier did not consume the already-frozen bootstrap-support gate. That
  remediation kept the factor and random-rank target at zero
  for sparse/tied invalid factor months while the equal-weight baseline and
  primary benchmark remain invested in the nonempty unique eligible universe.
  It retained resulting active returns descriptively and excluded them from
  final-state support. It also passes all-three-factor nondegenerate bootstrap
  support as an explicit classifier coverage input, with hard-validity
  precedence. Integrated tied-month economic and classifier boundary fixtures
  were remediated by committed and pushed head `5b08be6`; exact-head CI run
  `30692981109` passed. The seventeenth review of `5b08be6` found one P1 and one
  P2: an end-of-cutoff signal could have a complete label but no in-cutoff next
  monthly execution, and invalid-month exclusion left the continuous economic
  path ambiguous. The current branch-head snapshot excludes that boundary
  signal before continuous-strategy target freeze without invalidating its
  retained factor diagnostic. It also keeps every valid/tied/valid economic
  path row, target transition, turnover, cost, benchmark return, and active
  return in one unfiltered annualization path. A 22-session July 2024 cutoff
  fixture and a classifier-discriminating three-month path fixture were
  remediated by committed and pushed head `242f373`; exact-head CI run
  `30693611292` passed. The eighteenth review of `242f373` found two P2 gaps:
  freeze/signal comparison lacked a canonical UTC signal-close instant, and
  the 12/24 counter could reach threshold before the final label and strategy
  interval matured. The current branch-head snapshot requires timezone-aware
  freeze instants normalized to UTC and compares them strictly with the frozen-
  calendar official XNYS close converted to UTC. It makes threshold increment
  operational only and delays protected opening until strictly after the later
  of its label and next-month execution maturity, plus the existing Track B and
  authorization gates. Same-day before/at/after-close and 12/24 output-maturity
  fixtures are not pending local authorship. The actual remaining gate is
  exact-head CI on the current head, followed by one current-head Codex review;
  every finding
  restarts that remediation loop. Do not repeat commit or push work from an old
  handoff instruction; resolve current `HEAD`, remote head, CI, and review
  state.
- Current protected-main baseline: 3064 tests passed with two
  platform-conditional wide-`longdouble` skips. The PR #176 release also
  passed Ruff, compileall, deterministic repo-map, Skill audit, immutable
  R0-R7 hashes, exact bounded v8-to-v9 succession, package parity, privacy,
  Unicode/control, cleanup/diff, and final review gates.
- R1I is complete. Do not start R1J or another one-event registry expansion.
- The accepted 37-event vocabulary is preserved as optional
  `full_ledger_profile_v1`; 37/37 coverage is not a prerequisite for Track A or
  the later minimal Track B runtime.
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
- Stage 4B-R1B PR #167 passed 1002 tests with two platform-conditional skips,
  Ruff, compilation, deterministic repo-map, Skill audit, source/sdist/wheel
  R0/R1 package parity, privacy/Unicode/control/diff gates, exact-head CI, and
  final current-head Codex review. Its first review found one nullable
  named-type cycle P2; that issue was reproduced, fixed, regression-tested, and
  re-reviewed before normal protected merge and exact merge-head CI at
  `a6f7d43`.
- Stage 4B-R1C PR #169 passed 1171 tests with two platform-conditional skips,
  Ruff, compilation, deterministic repo-map, Skill audit, source/sdist/wheel
  R0/R1/R2 package parity, privacy/Unicode/control/diff gates, exact-head CI
  run `30470068227`, and one clean final current-head Codex review. It normally
  protected-merged without auto-merge/admin bypass at `68a4c4f`; exact
  merge-head CI run `30471505290` succeeded.
- Stage 4B-R1D PR #170 passed 1404 tests with two platform-conditional skips,
  Ruff, compilation, deterministic repo-map, Skill audit, source/sdist/wheel
  R0/R1/R2/R3 package parity, privacy/path/Unicode/control/diff gates,
  exact-head CI run `30474619015`, and one clean final current-head Codex
  review. It normally protected-merged without auto-merge/admin bypass at
  `8d02e5a`; exact merge-head CI run `30475306672` succeeded.
- Stage 4B-R1E PR #171 passed 1760 tests with two platform-conditional skips,
  Ruff, compilation, deterministic repo-map, Skill audit, source/sdist/wheel
  R0/R1/R2/R3/R4 package parity, privacy/path/Unicode/control/diff gates,
  exact-head CI run `30478013476`, and one clean final current-head Codex
  review. It normally protected-merged without auto-merge/admin bypass at
  `814bf02`; exact merge-head CI run `30478870434` succeeded.
- Stage 4B-R1F PR #172 passed 2198 tests with two platform-conditional skips,
  Ruff, compilation, deterministic repo-map, Skill audit, source/sdist/wheel
  R0-R5 package parity, privacy/Unicode/control/diff gates, exact-head CI run
  `30481526688`, and one clean final current-head Codex review. It normally
  protected-merged without auto-merge/admin bypass at `d9ac67e`; exact
  merge-head CI run `30482706983` succeeded.
- Stage 4B-R1G PR #173 passed 2496 tests with two platform-conditional skips,
  Ruff, compilation, deterministic repo-map, Skill audit, source/sdist/wheel
  R0-R6 package parity, privacy/Unicode/control/diff gates, exact-head CI run
  `30485367220`, and one clean final current-head Codex review. It normally
  protected-merged without auto-merge/admin bypass at `520ed65`; exact
  merge-head CI run `30485940985` succeeded.
- Stage 4B-R1H PR #174 passed 2838 tests with two platform-conditional skips,
  Ruff, compilation, deterministic repo-map, Skill audit, source/sdist/wheel
  R0-R7 package parity, privacy/Unicode/control/diff gates, exact-head CI run
  `30489229758`, and one clean final current-head Codex review. It normally
  protected-merged without auto-merge/admin bypass at `b42b911`; exact
  merge-head CI run `30489691309` succeeded.
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

## Accepted R0 Through R1I And Optional Full Ledger Profile

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

R1B is accepted on protected main through PR #167 and exact merge-head CI run
`30424903896`. For R1C, the owner selected bundle `R1C-A`. That explicit
selection, not any helper, fixture, or narrative example, freezes:

- exact `trial_family_id` namespace `fam_<32 lowercase hex>`;
- an immutable versioned authority catalog plus complete repository-external
  canonical family records retrieved by an exact digest-pinned tuple;
- a separate immutable acceptance record whose reviewer is distinct from both
  the definition issuer and registration actor;
- stable global family identity, strictly monotonic acceptance generations,
  exactly one current accepted generation, explicit supersession, and
  currentness checks before registration, trial allocation, attempt execution,
  and protected access;
- no alias, clone, rerun, new campaign, or post-result reclassification reset;
- `supersedes` for definition generations and `depends_on` across distinct
  families, with no self-declared `independent_of`; and
- a common direct-scope maximum of 32 campaign IDs for family and later local
  sample registration.

`docs/experiment_trial_ledger_trial_family_registration_schema_contract.md`
records the exact R1C authority. R1C publishes a new immutable registry
`0.3.0` under unchanged schema-language `0.2.0`, supports exactly epoch,
campaign allocation, experiment allocation, and trial-family registration,
and leaves the other 33 events `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`. Its local
shape validator cannot prove external retrieval, catalog/record authority,
reviewer independence, currentness, anti-reset history, prior campaign
allocation, uniqueness, authorization, or append behavior; every such
stateful use remains fail closed.

R1C is accepted on protected main through PR #169 and exact merge-head CI run
`30471505290`. For R1D, the owner selected bundle `R1D-A`. That explicit
selection, not any helper, fixture, or narrative example, freezes:

- exact `sample_id` namespace `smp_<32 lowercase hex>`;
- the existing common direct-scope maximum of 32 campaign IDs;
- one immutable versioned Stage 3 sample-authority catalog plus complete
  repository-external canonical sample records retrieved by an exact
  digest-pinned tuple;
- separate non-self-issued acceptance and publication-approval records with
  single-current monotonic generations;
- mutually exclusive direct-local, global-local, and later external-reference
  representation paths;
- one ledger-local identity per canonical sample lineage/path, with no alias,
  clone, new-campaign, overlap, result-access, or reclassification reset;
- private complete records and sensitive values remaining repository-external,
  with allowlisted public projections containing only safe IDs and explicitly
  publication-approved hashes; and
- a bounded R1D release that promotes only `SAMPLE_REGISTERED`, leaving
  `CAMPAIGN_ENTITY_BOUND` and `STAGE3_SAMPLE_REFERENCE_BOUND` incomplete for
  R1E.

`docs/experiment_trial_ledger_sample_registration_schema_contract.md` records
the exact R1D authority. R1D publishes a new immutable registry `0.4.0` under
unchanged schema-language `0.2.0`, supports exactly epoch, campaign allocation,
experiment allocation, trial-family registration, and local sample
registration, and leaves the other 32 events
`SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`. Its local shape validator cannot prove
external retrieval, reviewer independence, acceptance or publication
currentness, prior campaign allocation, path exclusivity, overlap/exposure
history, authorization, or append behavior; every such stateful use remains
fail closed.

R1D is accepted on protected main through PR #170 and exact merge-head CI run
`30475306672`. For R1E, the owner selected bundle `R1E-A`. That explicit
selection freezes:

- one `CAMPAIGN_ENTITY_BOUND` event with a closed outer `subject_type` union
  for exact `trial_family` and `sample` identities;
- singleton campaign scope and exact source event ID/hash syntax;
- trial-family binding only to an empty-scope global
  `TRIAL_FAMILY_REGISTERED`;
- a nested sample `source_kind` union separating empty-scope global
  `SAMPLE_REGISTERED` from an exact earlier external
  `STAGE3_SAMPLE_REFERENCE_BOUND`;
- one campaign-scoped `STAGE3_SAMPLE_REFERENCE_BOUND` that allocates a new
  stable `smp_<32 lowercase hex>` identity and pins the exact R1D Stage 3
  authority, record, acceptance, public-projection, and publication-approval
  tuple;
- later cross-campaign external-origin reuse only through
  `CAMPAIGN_ENTITY_BOUND` referencing the exact first Stage 3 event, never a
  fresh identity or synthetic local registration; and
- fail-closed prior-allocation, retained source bytes/digest/type/subject/scope,
  currentness, unique target binding, path exclusivity, and anti-reset rules.

`docs/experiment_trial_ledger_binding_schema_contract.md` records the exact
R1E authority. R1E publishes a new immutable registry `0.5.0` under unchanged
schema-language `0.2.0`, supports exactly epoch, both allocations, both
registrations, and both binding events, and leaves the other 30 events
`SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`. Its local shape validator cannot prove
retained source truth, external retrieval, role independence, currentness,
prior campaign allocation, path history, uniqueness, authorization, or append
behavior; every such stateful use remains fail closed.

R1E is accepted on protected main through PR #171 and exact merge-head CI run
`30478870434`. For R1F, the owner selected bundle `R1F-A`. That explicit
selection freezes:

- exact semantic trial IDs `trl_<32 lowercase hex>`, one-item campaign scope,
  and initial disposition `PLANNED`;
- exact earlier campaign allocation, experiment allocation, trial-family
  registration or campaign binding, and complete sample-path evidence;
- a complete repository-external canonical trial definition plus separate
  immutable acceptance, public-projection approval, and allocation-actor
  authority records;
- closed `original`/`child`/`clone`/`rerun` relation branches and closed
  `clean_commit`/`dirty_tree` code-identity branches;
- a finite maximum of 32 sample bindings per semantic trial; and
- fail-closed parent/currentness/reviewer-independence/uniqueness/order/
  relation-acyclicity/code-byte/anti-reset rules before any validation,
  execution, attempt, protected access, artifact production, or result
  inspection.

`docs/experiment_trial_ledger_trial_allocation_schema_contract.md` records the
exact R1F authority. R1F publishes a new immutable registry `0.6.0` under
unchanged schema-language `0.2.0`, supports exactly the seven prior events plus
`TRIAL_ALLOCATED`, and leaves the other 29 events
`SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`. Its local shape validator cannot prove
parent existence/order, retained bytes, external retrieval, role independence,
currentness, authority, relation acyclicity, code identity, uniqueness,
authorization, or append behavior; every such stateful use remains fail
closed.

R1F is accepted on protected main through PR #172 and exact merge-head CI run
`30482706983`. The remaining-event dependency/risk graph selected the initial
campaign-inventory seal as the unique smallest prerequisite between trial
allocation and either attempt allocation or protected-access intent. The owner
selected bundle `R1G-A`. That explicit selection freezes:

- campaign subject identity and singleton campaign scope;
- exact earlier campaign allocation;
- a complete repository-external canonical
  `campaign_inventory_record_v1`, retrieved through an immutable
  digest-pinned authority tuple;
- one separate acceptance record whose reviewer differs from the inventory
  issuer, seal actor, accepted trial-definition issuers, and accepted private
  input producers;
- one separate current seal-actor authority record;
- an ordered all-and-only 1-through-4096 trial inventory with exact earlier
  trial event/definition evidence, relations, budgets, variation axes, sample
  roles, protected-access budget, and frozen policy references;
- the exact nested nonrecursive `campaign_inventory_preseal_head_v1`; and
- exactly one initial seal, with every later addition reserved for the
  still-incomplete amendment family.

`docs/experiment_trial_ledger_campaign_inventory_seal_schema_contract.md`
records the exact R1G authority. R1G publishes a new immutable registry
`0.7.0` under unchanged schema-language `0.2.0`, supports exactly the eight
prior events plus `CAMPAIGN_INVENTORY_SEALED`, and leaves the other 28 events
`SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`. Its local shape validator cannot prove
external retrieval, all-and-only inventory completeness, role independence,
authority/currentness, predecessor-head truth, sequence arithmetic, unique
seal, atomic append, or pre-action ordering; every such stateful use remains
fail closed.

R1G is accepted on protected main through PR #173 and exact merge-head CI run
`30485940985`. The remaining-event dependency/risk graph selected
`ATTEMPT_ALLOCATED` as the unique smallest compute-path prerequisite after the
inventory seal. The amendment pair is optional, `ATTEMPT_STARTED` and terminal
attempt/trial/artifact events depend on allocation, and `ACCESS_INTENT` is an
independent higher-risk capability/security root. The owner selected bundle
`R1H-A`. That explicit selection freezes:

- exact attempt IDs `att_<32 lowercase hex>`, attempt subject identity, and
  singleton campaign scope;
- exact earlier trial-allocation and initial campaign-inventory-seal event
  IDs/hashes;
- a complete repository-external canonical `attempt_plan_record_v1`,
  retrieved through an immutable digest-pinned authority tuple;
- an all-and-only expected-output inventory digest inside that complete plan;
- one separate acceptance record whose reviewer differs from the plan issuer,
  accepted trial-definition issuer, allocation actor, and relevant private
  input producers;
- one separate current attempt-allocation actor authority record;
- closed `first_attempt` and `retry` relation branches, with ordinal 1 for the
  first branch and an exact prior terminal attempt reference for retry;
- new attempt identity per retry, strictly monotonic ordinal within the
  accepted trial retry policy/budget, and no alias/clone/rerun/new-campaign/
  post-result reset; and
- an allocation-only event boundary that cannot start validation, execution,
  artifact production, or protected access.

`docs/experiment_trial_ledger_attempt_allocation_schema_contract.md` records
the exact R1H authority. R1H publishes a new immutable registry `0.8.0` under
unchanged schema-language `0.2.0`, supports exactly the nine prior events plus
`ATTEMPT_ALLOCATED`, and leaves the other 27 events
`SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`. Its local shape validator cannot prove
parent existence/order, retained bytes, external retrieval, role independence,
currentness, authority, unique/monotonic ordinal history, terminal retry
predecessor, retry permission/budget, durable append, or the pre-action
barrier; every such stateful use remains fail closed.

R1H is accepted on protected main through PR #174 and exact merge-head CI run
`30489691309`. The remaining-event dependency/risk graph selected
`ATTEMPT_STARTED` as the unique smallest strict compute-path successor. The
campaign amendment pair remains optional, terminal attempt/trial/artifact/
closure events remain downstream, and `ACCESS_INTENT` remains an independent
higher-risk protected-access capability root. The owner selected bundle
`R1I-A`. That explicit selection freezes:

- the existing exact attempt subject, semantic-trial reference, singleton
  campaign scope, and exact earlier attempt-allocation event ID/hash;
- a complete repository-external canonical
  `attempt_start_readiness_record_v1`, retrieved through an immutable
  digest-pinned authority tuple and proving literal `READY` plus exact current
  plan/executor/environment/input identities;
- effective-principal independence among readiness issuer/reviewer, executor,
  earlier allocation actor, attempt-plan issuer, and plan reviewer;
- one separate current attempt-start actor authority record;
- one ledger-owned `cap_<32 lowercase hex>` one-shot execution-capability
  identity and complete private external capability record created atomically
  with the durable start append;
- exact lost-ack replay that returns the same start/capability identity,
  changed-request conflict, and exactly one successful atomic capability
  consumption before any executor begins; and
- exactly one start per attempt, with stale/revoked/expired/terminal/closed/
  duplicate starts rejected and no alias/retry/rerun/new-campaign/restart
  reset.

`docs/experiment_trial_ledger_attempt_start_schema_contract.md` records the
exact R1I authority. R1I publishes a new immutable registry `0.9.0` under
unchanged schema-language `0.2.0`, supports exactly the ten prior events plus
`ATTEMPT_STARTED`, and leaves the other 26 events
`SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`. Its local shape validator cannot prove
source existence/order, retained bytes, external retrieval, literal readiness,
effective-principal independence, authority/currentness, unique start, atomic
capability mint, idempotency, one-time consumption, durable append, execution,
artifact, protected access, or research behavior; every such stateful use
remains fail closed.

R1I is accepted on protected main through PR #176 and exact merge-head CI run
`30492542975`. The accepted registry work is retained unchanged as
`full_ledger_profile_v1`. The remaining 26 incomplete payloads are optional
future hardening and are not the current task queue.

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
campaign/experiment allocation. Stage 4B-R1C adds local shape validation for
only trial-family registration. Stage 4B-R1D adds local sample registration,
and Stage 4B-R1E adds global-entity/external-sample binding shapes with exact
source references. Stage 4B-R1F adds semantic trial-allocation shape with exact
parent, definition, relation, and code-identity references. Stage 4B-R1G adds
the initial campaign-inventory-seal shape with exact external inventory,
acceptance, seal-authority, bounded-count, and pre-seal references. Stage
4B-R1H adds attempt-allocation shape with exact trial/seal, external plan,
acceptance/actor-authority, expected-output, and first/retry references. Stage
4B-R1I adds attempt-start shape with exact allocation/readiness/start-authority
and one-shot capability references. These releases pin external authority and
currentness references but do not implement the stateful ledger, capability
service, or executor. Track A therefore uses a frozen protocol, exact
14-semantic-trial inventory, detached hashes, complete outcome retention, and a
repository-external private bundle. This is sufficient only for
`DIAGNOSTIC_ONLY`; it cannot support formal promotion or prospective access.

The 2026-07-11 conformance audit remains historical evidence at its audited
SHA. Its prior no-P1/P2 conclusion does not supersede these later findings.

## PR #148 Interaction

At the last verification, PR #148 was an independent Draft governance PR from
an older base that changed only `AGENTS.md`. It was not a predecessor for PRs
#158-#176. On 2026-07-29 the owner explicitly required PR #177 to add automatic
review-remediation and bounded scheduled-wait rules to `AGENTS.md`. PR #148 is
still neither a predecessor nor authorized for merge/close, but it now has a
direct file overlap and stale-base conflict risk. Before any future work on
#148, rebase it and compare its review-trigger policy against the newer
protected-main policy; do not overwrite either change silently. Independent
thin-router PR
#168 merged at `4ac5adb` while the first R1C head was being published. Its
overlap was limited to `docs/repo_map.md`, `scripts/repo_map.py`, and
`tests/test_project_structure.py`; there was no R1C contract, registry,
fixture, loader, or focused behavior-test overlap. R1C was normally rebased
onto that merge, retained both scopes, regenerated the repo map, and reran all
local gates before updating its remote head.

## Next Safe Stage

Complete PR 1 scope and campaign reset without data access or performance
calculation:

- keep R1I complete at `6386c59`;
- preserve the accepted registry releases unchanged as optional
  `full_ledger_profile_v1`;
- freeze the exact three-factor protocol and 14-trial inventory;
- reconcile the roadmap, specification, controller, decision/engineering logs,
  and repo map; and
- pass local/full validation and final review before protected merge.

After PR 1 merges, enter the private entitlement, retention, and publication
gate. Probe current EODHD capability without exposing credentials or raw
responses; do not purchase. Written permission must cover frozen-snapshot
retention, aggregate charts/statistics, hashes/counts, and public noncommercial
GitHub use. A missing paid entitlement or unresolved permission is the next
owner stop.

Only after that private gate may PR 2 add public manifest/validator and safe
projection support while private acquisition/normalization remains outside the
repository. Dataset review must be blind to factor and portfolio performance
and must freeze the cutoff, manifest, calendar identity, lineage/terminal
rules, exclusions, and diagnostic-ready or blocked decision.

PR 3 then implements the bounded Stage 5-MVP/6-MVP runner; PR 4 runs and
freezes all 14 outcomes. After PR 3 merges and before the first result-bearing
job, a detached run binding must link the exact code, configuration,
environment, protocol, inventory, and accepted dataset hashes. Only after
Track A closes does the 8-12-event-family Track B runtime become the main
engineering priority. Track B is required before prospective performance
access, but it does not block Track A.

## Freshness Checklist

Before continuing:

- fetch and compare `origin/main`;
- verify the previous required stage PR is merged;
- classify unrelated open drafts separately from predecessor gates;
- use a clean branch/worktree and preserve unrelated local changes;
- rerun focused and baseline validation; and
- reread this handoff and the canonical roadmap if the remote head changed.

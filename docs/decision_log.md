# Decision Log

This log records durable workflow, architecture, and research-process decisions
for the simulated equity factor research project.

It is not an experiment log and must not be used to claim profitability or
investment performance.

## How To Update This Log

- Add a dated entry for decisions that future Codex sessions should preserve.
- State the context, decision, rationale, consequences, and follow-up.
- Keep entries factual and separate observed evidence from assumptions.
- Link or name the relevant files, branches, PRs, checks, or logs when useful.

---

## 2026-07-31 - Freeze Diagnostic Forward Returns And Shared Bootstrap Draws

Context:

- The tenth exact-head Codex review of PR #177 at `a5b6695` found two P2
  ambiguities: the execution-to-endpoint diagnostic return did not distinguish
  simple from log returns, and bootstrap centered/uncentered distributions did
  not state whether they shared draws or consumed two RNG passes.

Decision:

- Define diagnostic forward return as
  `adjusted_close[e+21] / adjusted_close[e] - 1`. Both anchors must be present,
  finite, strictly positive real non-Boolean scalars. Invalid anchors retain
  and invalidate the factor-month outcome with a counted reason and no repair.
- For every bootstrap replicate and chronological segment, draw block starts
  exactly once. Reuse the resulting row-index vector jointly for all factors,
  the uncentered interval table, and the globally null-centered p-value table.
- Use one RNG pass per replicate. Separate centered/uncentered passes and a
  pass-order choice are forbidden.

Rationale:

- Simple and log endpoint returns produce different decile evidence from the
  same prices.
- Two seeded bootstrap passes produce different draws depending on pass order;
  shared indices bind p-value and interval distributions to one immutable
  resampling experiment.

Consequences:

- Separate golden fixtures distinguish endpoint simple/log returns and freeze
  three segmented bootstrap replicates, row indices, uncentered means,
  null-centered means, and the rejected second-pass alternative.
- No data, performance, trial execution, additional hypothesis, merge,
  brokerage, paper, or live behavior is added.

---

## 2026-07-31 - Freeze LOW_VOL_3M Simple Returns And Anchor Validity

Context:

- The ninth exact-head Codex review of PR #177 at `86f6929` found one P2.
  `one_day_adjusted_close_returns` did not distinguish simple from log returns
  or define invalid price-anchor handling.

Decision:

- Define each `LOW_VOL_3M` observation as the adjacent-price simple return
  `adjusted_close[d] / adjusted_close[d-1] - 1` for `d=t-62..t`, inclusive.
  Log returns are forbidden.
- Require exactly 64 anchors from `t-63..t`. Every anchor must be a present,
  finite, strictly positive real numeric scalar other than a Boolean.
- If any anchor fails, retain the listing/signal-date factor value as invalid/
  missing, exclude that listing from the factor-specific decision-time
  eligible set, and count the reason. Filling, interpolation, clipping,
  absolute-value repair, alternate rows, and log fallback are forbidden.

Rationale:

- Simple and log return volatilities can rank securities differently, changing
  deciles, targets, Rank IC, and final diagnostic state.
- Invalid-anchor behavior must be decision-time deterministic and visible,
  rather than silently repaired by an implementation.

Consequences:

- The 63-return golden fixture now freezes distinct simple and forbidden-log
  sample standard deviations and mutates every invalid-anchor class.
- No data, performance, trial execution, additional factor, merge, brokerage,
  paper, or live behavior is added.

---

## 2026-07-31 - Freeze Holm Index Origin And Factor-Order Mapping

Context:

- The eighth exact-head Codex review of PR #177 at `1f6c801` found one P2.
  The code-like adjusted-p formula combined mathematical multipliers with an
  undefined `k` origin, so a zero-based implementation could use multipliers
  4, 3, and 2 instead of Holm's 3, 2, and 1.

Decision:

- Define mathematical `k` as one-based over `1..3` and access a Python sorted
  p-value sequence at `k-1`.
- For each sorted position `k`, compute
  `min(1, max((3-j+1) * sorted_raw_p[j-1] for j in 1..k))`.
- Sort raw p-values stably with frozen factor order as the tie breaker, stop
  sequential rejection at the first non-rejection, and map adjusted values
  back to the original factor order only after the sorted running maximum.

Rationale:

- Explicit index conversion prevents a runner from changing adjusted values,
  rejection decisions, or the final diagnostic state through a plausible
  Python-style interpretation of the same YAML.

Consequences:

- A three-p-value golden fixture freezes sorted order, multiplied values,
  running maxima, factor-order adjusted values, and the rejection set.
- No data, performance, trial execution, additional hypothesis, merge,
  brokerage, paper, or live behavior is added.

---

## 2026-07-31 - Freeze Random-Rank Permutation-To-Target Mapping

Context:

- The seventh exact-head Codex review of PR #177 at `b8149c2` found one P2.
  The baseline froze seed derivation and RNG but did not say which date entered
  the seed, which end of the permutation was selected, or how a non-divisible
  universe determined top-decile size.

Decision:

- Use strict signal date `t`, never execution date, in the factor/month seed
  preimage. Interpret the first 16 SHA-256 hex digits as an unsigned big-endian
  seed for NumPy `PCG64DXSM`.
- Sort canonical listing-key bytes ascending, permute integer indices once, and
  interpret the permutation as high-to-low random rank.
- Reuse the factor-decile remainder rule: select the first
  `N // 10 + (1 if N % 10 else 0)` permuted indices. The final chunk and a
  floor-only size are forbidden.
- Assign `1 / selected_count` to every selected key and serialize the target in
  ascending canonical-key order. The random baseline remains one semantic
  trial and the complete inventory remains exactly 14.

Rationale:

- Otherwise multiple reasonable implementations can produce different
  baseline holdings and returns from the same frozen seed.
- Reusing the existing high-ranked-decile size rule avoids introducing a
  second quantile convention solely for the random baseline.

Consequences:

- A 103-key golden fixture freezes the exact digest, unsigned seed, complete
  permutation, 11 selected canonical keys, equal weights, and serialization.
- No data, performance, trial execution, additional hypothesis or cost case,
  merge, brokerage, paper, or live behavior is added.

---

## 2026-07-31 - Align Diagnostic Costs And Freeze Random-Baseline Cost Basis

Context:

- The sixth exact-head Codex review of PR #177 at `0179ebb` found one P1 and
  one P2. The campaign formula omitted the accepted post-return gross
  multiplier, and the random-rank continuous baseline did not state whether
  its return was gross or net at a frozen cost rate.

Decision:

- On each rebalance row, apply held-position incoming returns first, then
  charge execution cost against post-return equity at the ending close. As a
  beginning-period return impact, cost is
  `gross_multiplier * turnover * bps / 10000` and net row return is gross row
  return minus that impact.
- Multiply every security-level cost contribution by the same gross
  multiplier so the contributions sum exactly to the portfolio cost impact.
- Keep both baselines' 21-row episodic outputs gross and cost-free. Keep the
  equal-weight continuous baseline gross and cost-free. Freeze the random-rank
  continuous baseline as net at the primary 10-bps all-in cost case, using the
  same drifted-weight turnover and execution-to-execution accounting as factor
  strategies.
- Do not emit random-baseline 0-bps or 25-bps continuous variants. The baseline
  remains one semantic trial and the complete inventory remains exactly 14.

Rationale:

- The accepted Stage 2 timing authority charges at the close after the row's
  incoming return. Omitting the gross multiplier understates a post-gain
  charge and overstates a post-loss charge relative to that contract.
- A single cost-frozen random strategy baseline is reproducible and comparable
  to the campaign's primary strategy case without creating a hidden parameter
  search.

Consequences:

- Hand-calculated fixtures cover a nonzero 10% incoming return, turnover 2.0,
  the 25-bps factor stress case, and the 10-bps random-baseline primary case.
- No data, performance, trial execution, extra semantic trial, merge,
  brokerage, paper, or live behavior is added.

---

## 2026-07-31 - Freeze Benchmark-Comparison Final-State Routing

Context:

- The fifth exact-head Codex review of PR #177 at `e5d72c2` found one P2.
  Missing factor-matched constituent returns or SPY dates invalidated their
  comparisons, but the ordered final-state tree did not state whether each gap
  was a hard failure, coverage failure, or false economic predicate.

Decision:

- Any invalid required factor-matched primary-benchmark comparison is a hard-
  validity failure for the campaign and routes to `INVALID_DIAGNOSTIC` under
  the first ordered rule. It may not be omitted, filled, or treated as merely
  economically unsupported.
- The secondary SPY comparison is descriptive only. A missing SPY date retains
  an invalid secondary output and missing count but has no final-state effect
  when every required primary comparison is valid.
- `economically_supported(f)` uses only the valid factor-matched primary-
  benchmark annualized active return at 10 and 25 bps.

Rationale:

- The primary comparison is required for the preregistered economic coherence
  predicate, so incomplete primary evidence cannot support another final state.
- SPY was frozen as a secondary proxy and should not silently become a hard
  requirement for a final state whose primary benchmark is factor-matched.

Consequences:

- Separate fixtures route a primary matched-universe gap to
  `INVALID_DIAGNOSTIC` and show that a SPY-only gap leaves an otherwise
  `POSITIVE_DIAGNOSTIC` state unchanged.
- Both invalid comparisons remain visible in the required evidence outputs.
- No data, performance, trial execution, merge, brokerage, paper, or live
  behavior is added.

---

## 2026-07-31 - Persist Through Review And Freeze Factor-Turnover Predecessors

Context:

- The fourth exact-head Codex review of PR #177 at `6a7445f` found two P2
  gaps. Factor turnover did not specify whether an outcome-invalid intervening
  month remained the next month's predecessor, and the mandatory handoff still
  called already-completed commit/push work pending.
- The owner also corrected the review-wait terminal condition: creating a
  monitor is not completion, and the task must continue through review and any
  safe remediation until the exact current head has no actionable finding.

Decision:

- Freeze factor turnover to the immediately preceding scheduled frozen
  decision-time target, including an intervening zero target and a target whose
  later outcome becomes invalid. Outcome validity is retained separately and
  cannot make turnover skip back to the last outcome-valid target.
- The first scheduled frozen target in the bounded evaluation schedule has
  `not_applicable` turnover. Every later scheduled target has exactly one
  immediate predecessor.
- Treat a pending current-head Codex review as a nonterminal task state. Keep
  the task active, use a single five-minute monitor only when needed, never
  duplicate a review request, and repeat fix, validation, push, CI, and review
  until no actionable finding remains.
- Retain the separate four-run, thirty-minute cap for a genuinely critical
  owner decision; this decision supersedes only the prior eight-run pause rule
  for a pending Codex review.

Rationale:

- Later endpoint missingness must not rewrite a previously knowable target or
  any later decision-time turnover. Skipping an outcome-invalid target would
  make a future diagnostic depend on post-signal information.
- A scheduled callback is an implementation mechanism for waiting, not proof
  that the requested review gate completed.

Consequences:

- A three-month mutation fixture distinguishes the required immediate-target
  turnover from the forbidden last-outcome-valid alternative.
- The handoff records `6a7445f` as committed, pushed, and CI-passed, names the
  fourth-review findings, and directs continuations to current-head CI/review
  state rather than redundant publication work.
- This changes protocol and workflow control only. It adds no data access,
  performance result, merge, brokerage, paper, or live behavior.

---

## 2026-07-31 - Freeze Robustness Sample And Trial Inventory Binding

Context:

- The third exact-head Codex review of PR #177 at `4d832c7` found two P2
  protocol gaps. The evidence bundle named `trial_inventory.json` without
  binding it to the frozen 14-trial JSON bytes, and the final-state robustness
  rules did not choose between factor-specific all-valid Rank IC months and the
  primary common complete-case table.
- Different valid sample choices could change yearly signs,
  leave-one-year-out means, and therefore `POSITIVE_DIAGNOSTIC` versus
  `MIXED_DIAGNOSTIC` after results were visible.

Decision:

- Require bundle `trial_inventory.json` to be an exact byte-for-byte copy of
  `docs/preregistrations/eodhd_sp500_three_factor_trial_inventory_v1.json` at
  the protocol-freeze commit. Its SHA-256 must equal the detached trial-
  inventory freeze hash; parsing, reordering, normalization, or changing one
  trial field cannot satisfy the binding.
- Use only the primary common complete-case monthly Rank IC table for yearly
  and leave-one-year-out values that enter final-state robustness. Each
  factor's all-valid-month table remains descriptive only.
- Freeze yearly grouping to signal-date calendar year. Freeze the
  outcome-independent required-year set to every year with at least one
  scheduled primary-evaluation signal whose full label is inside accepted
  bounds.
- Use every required year in the positive-year fraction denominator and omit
  every required year exactly once for leave-one-year-out. A required year with
  no common-case row, an exact-zero yearly mean, or an empty post-omission table
  fails robustness.

Rationale:

- Child hashing alone proves only that the bundle lists the bytes it contains;
  it does not prove those bytes are the preregistered trial inventory.
- One shared sample basis and an outcome-independent year denominator prevent
  result-informed switching between more favorable missingness patterns.

Consequences:

- A deterministic fixture now demonstrates that the allowed common-case basis
  yields `POSITIVE_DIAGNOSTIC` while the forbidden factor-all-valid basis would
  yield `MIXED_DIAGNOSTIC` on the same configured evidence.
- These changes freeze protocol and audit behavior only. No data, performance,
  trial execution, thread resolution, or merge is authorized.

---

## 2026-07-29 - Remediate Reviews Automatically And Bound Scheduled Waits

Context:

- The second exact-head review of PR #177 found three actionable P2 protocol
  gaps after the first remediation commit.
- The prior workflow treated each review round as a potential owner stop even
  when the finding was safe, concrete, and within the already-authorized
  stage. It also lacked exact polling bounds for a pending Codex review or a
  genuinely critical owner decision.
- Draft PR #148 already edits `AGENTS.md` from an older base, but the owner
  explicitly directed PR #177 to establish the new behavior now.

Decision:

- Fix actionable in-scope review findings immediately without waiting for a
  separate owner confirmation. Revalidate, push, and request one current-head
  rereview after each changed head.
- While only `@codex review` is pending, use one thread-scoped schedule every
  five minutes for at most eight runs. Do not post duplicate review requests;
  stop early when the review completes, the head changes, or a finding arrives.
- When a critical owner decision is genuinely required, use one thread-scoped
  follow-up every thirty minutes for at most four runs. Never make the
  decision on the owner's behalf, and remain paused after the fourth unanswered
  run.
- Freeze `LOW_VOL_3M` as the Python half-open slice `[t-62:t+1]`, exactly 63
  returns ending at `t` from 64 price anchors.
- Permit a zero strategy target only for three signal-time conditions: fewer
  than 100 eligible securities, fewer than 10 distinct finite factor values,
  or duplicate canonical listing-key bytes. Later unselected outcome
  missingness cannot change the target, liquidation, or cash path.
- Require the evidence bundle to contain an exact-byte YAML child whose
  SHA-256 equals the detached protocol-freeze hash. A derived JSON file is not
  authoritative.

Rationale:

- Safe review remediation is ordinary implementation work inside an authorized
  PR, while purchases, protected access, destructive work, external scope
  expansion, and materially different research interpretations remain owner
  decisions.
- Bounded scheduled waits prevent both silent abandonment and unbounded polling
  or reminder spam.
- Exact slices, zero-target predicates, and byte-level evidence binding remove
  implementation-dependent behavior before result access.

Consequences:

- PR #148 now overlaps `AGENTS.md`; it remains untouched but must be rebased and
  compared before future use.
- The review schedule will be created only when the new exact head is actually
  waiting for review. No schedule is needed while actionable findings are being
  fixed.
- The remediation changes protocol and governance only. It does not fetch data,
  calculate performance, resolve review threads, or authorize merge.

---

## 2026-07-29 - Freeze Decision-Time Eligibility And Diagnostic Classification

Context:

- Final review of PR #177 found that the first protocol draft allowed future
  execution/endpoint availability inside the only eligibility definition.
- The draft enumerated five final states without an exhaustive assignment
  rule, left listing-key byte serialization implementation-dependent, and did
  not say whether fixed-bps costs were all-in or composable.

Decision:

- Freeze factor ranks, deciles, long-only targets, and matched-benchmark
  membership using only information known at signal close `t`. Future
  availability or return mutations cannot change those objects.
- Treat missing future outcomes only through explicit invalidation. Do not
  drop, substitute, or renormalize over future survivors.
- Use `listing_lineage_key_bytes_v1`: NFC UTF-8 length-prefixed exchange and
  ticker, strict ASCII dates, and a tagged null/present interval end. Freeze
  the key at first decision-time eligibility so later endpoints cannot rewrite
  historical order or identity.
- Interpret 0/10/25 bps as mutually exclusive all-in diagnostic execution-cost
  cases. No separate commission, spread, slippage, fee, impact, or capacity
  charge may be added.
- Assign the five final states with the ordered decision tree in the canonical
  campaign contract and preregistration. Hard-validity failure precedes
  coverage insufficiency; positive classification requires Holm, 10/25-bps
  economic, and frozen robustness coherence.

Rationale:

- Signal targets and benchmark membership must be invariant to halts,
  delistings, missing endpoints, and provider backfills that occur after the
  signal cutoff.
- Canonical bytes, fixed cost composition, and exhaustive classification
  predicates prevent implementation- or result-dependent choices after the
  protocol freeze.

Consequences:

- Missing selected execution prices or held returns can make the diagnostic
  invalid; this is preferable to silent survivorship conditioning.
- Exact zero fails every strict-positive economic or robustness predicate.
- Economic and robustness predicates constrain the final diagnostic label but
  do not create new discovery hypotheses outside the three-factor Holm family.

---

## 2026-07-29 - Reset To A Diagnostic-First Two-Track Program

Context:

- PR #176 completed R1I on protected main at `6386c59`.
- The roadmap still required completion of the full 37-event payload registry
  before statistical or empirical research.
- The owner determined that event-schema, test, and PR counts had displaced
  empirical research progress and supplied an exact EODHD historical S&P 500
  three-factor diagnostic scope.
- EODHD entitlement, historical-membership coverage, retention after
  cancellation, and public derived-output permission remain unverified.

Decision:

- Preserve the accepted 37-event vocabulary and immutable releases as optional
  `full_ledger_profile_v1`; do not continue R1J or one-event registry PRs.
- Run Track A first: one `DIAGNOSTIC_ONLY` historical EODHD campaign containing
  exactly `MOM_12_1`, `REV_1M`, `LOW_VOL_3M`, two baselines, and nine
  factor/cost strategy trials, for 14 semantic trials total.
- Freeze research choices in a public protocol and a separate JSON inventory.
  Use detached hashes rather than a self-referential preregistration hash.
- Bind cutoff, manifest, calendar, exclusions, coverage thresholds, and dataset
  review in a blinded dataset-acceptance record. After the runner merges and
  before any expanded-data performance access, create a detached run binding
  over code, configuration, environment, protocol, inventory, and accepted
  dataset hashes.
- Require entitlement and written retention/publication permission before
  expanded retrieval, durable retention, or public derived output. Codex must
  not purchase an entitlement.
- After Track A closes, implement Track B as an 8-12-conceptual-event-family
  stateful runtime in at most one design PR and one runtime PR. More than 14
  exact wire types requires a new owner decision.

Rationale:

- A public preregistration, exact trial inventory, immutable code/data/config
  binding, all-outcome retention, content-addressed private bundle, and
  independent review can constrain cherry-picking for a diagnostic campaign
  without pretending to provide formal protected-access evidence.
- A minimal stateful runtime is still needed before prospective performance
  access or formal evidence promotion, but it need not delay the first
  falsifiable historical diagnostic.
- Separating protocol freeze, blinded data acceptance, and the final pre-run
  binding prevents data-quality decisions or runner revisions from becoming
  hidden result-dependent research choices.

Consequences:

- Track A may end only in one of the five allowed `*_DIAGNOSTIC` states.
- Track A can never produce `RESEARCH_PASS`, alpha validation, profitability,
  market-wide validity, paper readiness, or live readiness.
- Weak, negative, mixed, invalid, and cost-erased outcomes remain valid and
  must not stop or disappear from the campaign.
- Track B does not block Track A, but Track B protected-access logging blocks
  opening prospective performance.

Follow-up:

- Resolve the private EODHD entitlement/retention/publication gate.
- Add the public manifest validator and complete a blinded dataset review.
- Implement only the frozen Stage 5-MVP/6-MVP runner, then execute and
  reconcile all 14 trials.
- Report progress using accepted dataset, eligible assets/dates, trial
  reconciliation, bundle completeness, conclusion, prospective months, and
  replication status, not schema, test, or PR counts.

---

## 2026-07-29 - Select R1I-A Attempt Start Authority

Context:

- Stage 4B-R1H is accepted on protected `main` through PR #174 at `b42b911`;
  exact merge-head CI run `30489691309` passed.
- A read-only dependency/risk graph over the remaining 27 incomplete events
  selected `ATTEMPT_STARTED` as the unique smallest strict compute-path
  successor. The campaign-amendment pair remains optional, protected-access
  intent is an independent higher-risk capability root, and terminal attempt,
  trial, artifact, and closure events remain downstream.
- Existing authorities froze durable start immediately before execution but
  did not freeze exact readiness, permission, one-shot capability,
  role-independence, lost-ack, or double-execution semantics. The owner
  selected bundle `R1I-A`.

Decision:

- Promote only `ATTEMPT_STARTED`; keep every terminal, artifact, access,
  exposure, closure, review, promotion, adjudication, supersession, and
  campaign-amendment event incomplete.
- Use the existing `att_<32 lowercase hex>` attempt identity as subject and
  one campaign ID as sorted-unique scope. Bind the exact earlier
  `ATTEMPT_ALLOCATED` event ID/hash and semantic-trial ID.
- Pin one complete repository-external canonical
  `attempt_start_readiness_record_v1` through an immutable digest-pinned
  authority catalog. Require literal `READY`, exact current
  plan/executor/environment/input evidence, and distinct effective principals
  for readiness issuer/reviewer, executor, allocation actor, plan issuer, and
  plan reviewer.
- Pin a separate current `attempt_start_authority_v1` actor-authority record.
- Mint one ledger-owned `cap_<32 lowercase hex>` identity and complete private
  `attempt_execution_capability_record_v1` atomically with the start append.
  Keep redemption secret/material repository-external. Require one atomic
  consumption before execution, exactly one start per attempt, and fail-closed
  expired/revoked/wrong-executor/concurrent/double consumption.
- Exact lost-ack replay of the same operation and request returns the same
  event and capability identity. Changed requests conflict; aliases, retries,
  reruns, new campaigns, record generations, and restarts never reset start or
  consumption history.
- Publish immutable registry `0.9.0` under unchanged schema-language `0.2.0`,
  preserve R0 through R7 bytes/behavior/default selection, and leave the
  other 26 events `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.

Rationale:

- Attempt start is the smallest event that advances the accepted compute path
  without inventing terminal evidence, artifact identity, protected-access
  permission, or private result fields.
- A complete readiness record makes exact validation and current executor
  inputs retrievable without leaking them into the public event.
- A ledger-owned one-shot capability plus atomic consumption separates durable
  authorization from code execution and closes lost-ack/double-start races at
  the future runtime boundary.
- Separate readiness review and start authority avoid self-certified
  execution permission.

Consequences:

- R1I may support exactly eleven events while the other 26 remain incomplete.
- Local schema acceptance remains syntax-only and cannot prove source order,
  record retrieval, readiness, independence, authority, currentness,
  idempotency, atomic mint, single consumption, durable append, execution,
  access, artifact production, or research behavior.
- Private-data access, research execution, brokerage, order, paper, and live
  trading impacts remain zero.

Follow-up:

- Add an independent positive fixture plus literal namespace, source,
  readiness, authority, capability, privacy, currentness, single-start,
  lost-ack, prior-release, package-parity, incomplete-event, and unpublished-
  promotion oracles.
- After protected R1I completion, analyze the remaining 26-event graph before
  choosing the smallest strict successor.

## 2026-07-29 - Select R1H-A Attempt Allocation Authority

Context:

- Stage 4B-R1G is accepted on protected `main` through PR #173 at `520ed65`;
  exact merge-head CI run `30485940985` passed.
- A read-only dependency/risk graph over the remaining 28 incomplete events
  selected `ATTEMPT_ALLOCATED` as the smallest strict prerequisite before
  attempt start, protected access, terminal evidence, and artifact
  disposition.
- Stage 4a and R1G deliberately did not freeze attempt identity, plan
  authority, retry relations, or actor authority. The owner selected bundle
  `R1H-A`.

Decision:

- Promote only `ATTEMPT_ALLOCATED`; keep attempt start, protected access,
  terminal, artifact, disposition, closure, review, promotion, adjudication,
  supersession, and campaign-amendment events incomplete.
- Use `att_<32 lowercase hex>` as the exact attempt namespace, `attempt` as
  subject type, and one campaign ID as the sorted-unique scope.
- Bind the exact earlier `TRIAL_ALLOCATED` and initial
  `CAMPAIGN_INVENTORY_SEALED` event ID/hash pairs.
- Pin one complete repository-external canonical `attempt_plan_record_v1`
  through an immutable digest-pinned authority catalog. Pin a separate
  immutable acceptance whose reviewer differs from the plan issuer,
  trial-definition issuer, allocation actor, and relevant private-input
  producers. Pin a separate current attempt-allocation actor authority.
- Use a closed `first_attempt`/`retry` tagged union. First attempt has literal
  ordinal 1. Retry has ordinal at least 2 and exact prior terminal attempt
  event ID/hash, requires a new attempt ID, and follows a monotonic
  policy-bounded ordinal under the same accepted trial.
- Forbid alias, clone, rerun, new-campaign, and post-result reclassification
  resets. Require source, retrieval, acceptance, role-independence,
  currentness, uniqueness, terminal-predecessor, retry-policy/budget, and
  pre-action checks to fail closed.
- Publish immutable registry `0.8.0` under unchanged schema-language `0.2.0`,
  preserve R0 through R6 bytes/behavior/default selection, and leave the
  other 27 events `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.

Rationale:

- Attempt allocation is the narrowest event that advances the accepted
  partial order without granting execution or protected-access capability.
- A complete external plan keeps private operational detail out of the public
  event while retaining exact retrievability and digest authority.
- Separate acceptance and actor authority prevent plan issuance, review, and
  append permission from collapsing into self-certified evidence.
- Closed first/retry branches make ordinal and predecessor rules reviewable
  without inventing later start, terminal, or artifact wire schemas.

Consequences:

- R1H may support exactly ten events while the other 27 remain incomplete.
- Local schema acceptance remains syntax-only and cannot prove source
  existence/order, plan retrieval, independence, currentness, retry
  permission, durable append, execution, access, artifact production, or
  research behavior.
- Private-data access, research execution, brokerage, order, paper, and live
  trading impacts remain zero.

Follow-up:

- Add independent first-attempt and retry fixtures plus literal namespace,
  source, authority, acceptance, relation, ordinal, currentness, anti-reset,
  incomplete-event, prior-release, package-parity, and unpublished-promotion
  oracles.
- After protected R1H completion, analyze the remaining 27-event graph before
  choosing the next event family.

## 2026-07-29 - Select R1G-A Initial Campaign Inventory Seal Authority

Context:

- Stage 4B-R1F is accepted on protected `main` through PR #172 at `d9ac67e`;
  exact merge-head CI run `30482706983` passed.
- A read-only dependency/risk graph over the remaining 29 incomplete events
  found that `CAMPAIGN_INVENTORY_SEALED` is the unique smallest prerequisite
  after `TRIAL_ALLOCATED` and before either `ATTEMPT_ALLOCATED` or
  `ACCESS_INTENT`.
- Stage 4a deliberately did not freeze the inventory wire representation,
  exact authority/currentness model, role independence, or finite
  campaign-trial bound. The owner selected bundle `R1G-A`.

Decision:

- Promote only `CAMPAIGN_INVENTORY_SEALED`; keep amendment, attempt, access,
  disposition, artifact, closure, review, promotion, adjudication, and
  supersession events incomplete.
- Use the existing campaign as subject with singleton campaign scope and bind
  its exact earlier allocation event.
- Pin one complete repository-external canonical
  `campaign_inventory_record_v1` through an immutable digest-pinned authority
  catalog. The record binds the ordered all-and-only earlier trial allocation
  and definition evidence, experiment/family/sample relations, budgets,
  variation axes, access budget, and frozen policies.
- Pin a separate acceptance record whose reviewer differs from the inventory
  issuer, seal actor, accepted trial-definition issuers, and accepted private
  input producers. Pin the seal actor's separate current authority record.
- Bound one initial inventory to 1 through 4096 semantic trials. A larger
  campaign requires a versioned owner decision; truncation, aliasing, or
  multiple synthetic initial seals are forbidden.
- Bind the exact nested nonrecursive
  `campaign_inventory_preseal_head_v1`; locally enforce subject/scope,
  ledger, and previous-hash equality while keeping predecessor currentness,
  sequence-plus-one, uniqueness, retrieval, ordering, and atomicity as
  mandatory stateful fail-closed checks.
- Publish immutable registry `0.7.0` under unchanged schema-language `0.2.0`,
  preserve R0 through R5 bytes/behavior/default selection, and leave the other
  28 events `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.

Rationale:

- Sealing the initial all-trial inventory is the narrowest event that advances
  the accepted partial order without prematurely choosing attempt or protected
  access identity/capability semantics.
- An external complete record keeps the event bounded while requiring
  retrievable all-and-only evidence rather than a hash-only assertion.
- Separate acceptance and seal authority prevent preregistration review,
  record issuance, and append permission from collapsing into one
  self-certified claim.
- The 4096 bound is finite and reviewable while remaining a schema ceiling,
  not a research budget recommendation.

Consequences:

- R1G may support exactly nine events while the other 28 remain incomplete.
- Local schema acceptance remains syntax-only and cannot be called a sealed
  campaign or append/runtime proof.
- Trial execution, attempt, protected-access, private-data, dependency, and
  trading impacts remain zero.

Follow-up:

- Add independent standard and maximum positive fixtures plus literal
  payload, scope, authority, count, pre-seal, duplicate, incomplete-event,
  prior-release, package-parity, and unpublished-promotion oracles.
- After protected R1G completion, analyze the remaining 28-event graph before
  choosing between the attempt-allocation and protected-access paths.

## 2026-07-29 - Select R1F-A Semantic Trial Allocation Authority

Context:

- Stage 4B-R1E is accepted on protected `main` through PR #171 at `814bf02`;
  exact merge-head CI run `30478870434` passed.
- The accepted Stage 4a contract defines semantic-trial allocation and exact
  parent/binding meaning, but the 0.5.0 registry deliberately leaves
  `TRIAL_ALLOCATED` incomplete.
- The owner selected bundle `R1F-A` and authorized automatic best-path analysis
  after completion.

Decision:

- The exact semantic-trial namespace is `trl_<32 lowercase hex>`.
- `TRIAL_ALLOCATED` allocates one new trial, uses a singleton campaign scope,
  and begins with literal disposition `PLANNED`.
- It pins exact earlier campaign/experiment/family source events and requires
  the complete sample set in the repository-external canonical trial
  definition to resolve through one legal current campaign path.
- The complete definition is retrieved by an exact digest-pinned authority and
  record tuple. Separate immutable records bind definition acceptance,
  allowlisted public projection approval, and allocation-actor authority.
  Acceptance review is independent of the definition issuer, allocation
  actor, and accepted private-input producers.
- The relation vocabulary is the closed union
  `original`/`child`/`clone`/`rerun`. The code-identity vocabulary is the
  closed union `clean_commit`/`dirty_tree`. Sources must be earlier, exact, and
  acyclic; dirty-tree formal interpretation remains separately review-gated.
- A semantic trial has at most 32 sample bindings. Identity-bearing defaults,
  partial records, ambiguous or stale parents, mixed paths, changed retained
  bytes, relation cycles, self-review, and post-action allocation fail closed.
- R1F may publish immutable registry `0.6.0` under unchanged schema-language
  `0.2.0`, promote only `TRIAL_ALLOCATED`, and preserve R0 through R4 bytes,
  behavior, and default selection.

Rationale:

- A trial is the first event whose immutable definition composes allocation,
  family, sample, timing, data, code, cost, selection, artifact, retry, and
  privacy authorities; a closed exact record avoids laundering narrative
  requirements into a partial wire schema.
- Closed relation and code-identity unions make lineage and dirty-source state
  explicit without implying that local shape validation verifies retained
  bytes or runtime state.
- Separate acceptance, publication, and actor-authority records keep method
  review, public disclosure, and permission from collapsing into one
  self-issued assertion.

Consequences:

- R1F's owner-methodology gate is cleared. Registry `0.6.0` may support
  exactly eight events while the other 29 remain
  `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.
- Trial execution, attempt, protected-access, private-data, dependency, and
  trading impacts remain zero.

Follow-up:

- Add independent clean-original and dirty-rerun fixtures plus literal
  child/clone positives and complete namespace/parent/authority/relation/code/
  privacy/scope killing evidence.
- After protected R1F completion, analyze the remaining event dependency/risk
  graph and automatically proceed with the smallest best next slice unless a
  genuine owner-only architecture choice is encountered.

## 2026-07-29 - Select R1E-A Binding Authority

Context:

- Stage 4B-R1D is accepted on protected `main` through PR #170 at `8d02e5a`;
  exact merge-head CI run `30475306672` passed.
- R1A and R1D deliberately left campaign-entity binding, the external Stage 3
  sample-reference event, exact source references, cross-campaign
  external-origin reuse, and their stateful path/currentness rules for a
  separate owner decision.
- The owner selected bundle `R1E-A`.

Decision:

- `CAMPAIGN_ENTITY_BOUND` remains one event with a top-level closed
  `subject_type` union. The exact branches are `trial_family` with
  `fam_<32 lowercase hex>` and `sample` with
  `smp_<32 lowercase hex>`.
- Each campaign binding has singleton `campaign_scope_ids` and an exact source
  event ID and SHA-256. Trial families source only empty-scope global
  `TRIAL_FAMILY_REGISTERED`.
- The sample branch contains a nested closed `source_kind` union:
  `local_registration` sources an empty-scope global `SAMPLE_REGISTERED`;
  `external_reference` sources the exact first
  `STAGE3_SAMPLE_REFERENCE_BOUND` event.
- `STAGE3_SAMPLE_REFERENCE_BOUND` allocates one new external-origin
  `smp_<32 lowercase hex>` identity for one campaign and carries the exact R1D
  Stage 3 authority, record, acceptance, public-projection, and
  publication-approval tuple with singleton scope.
- A later campaign reuses the same external-origin identity only through the
  `external_reference` campaign-binding branch. It must not allocate another
  identity or backfill a synthetic `SAMPLE_REGISTERED`.
- Stateful use fails closed unless the campaign is already allocated; source
  bytes, digest, event ID/type/subject/scope and ordering are exact; authority
  and decisions are current; the target binding is unique; origin paths remain
  exclusive; and aliases, clones, reruns, campaigns, overlap, access, or
  reclassification cannot reset identity or exposure history.
- R1E may publish immutable registry `0.5.0` under unchanged schema-language
  `0.2.0` and promote only `CAMPAIGN_ENTITY_BOUND` and
  `STAGE3_SAMPLE_REFERENCE_BOUND`.

Rationale:

- Closed outer and nested unions prevent generic-entity and nullable-field
  ambiguity.
- Exact retained source references make campaign evidence auditable without
  copying a partial registration or external record into the binding event.
- Reusing the first external-origin identity preserves R1D-A lineage,
  dependence, and exposure history across campaigns instead of allowing a
  per-campaign reset.
- Keeping local shape validation separate from source/currentness/runtime
  enforcement prevents schema acceptance from laundering missing stateful
  evidence.

Consequences:

- R1E's owner-methodology gate is cleared. Registry `0.5.0` may support
  exactly seven events while the other 30 remain
  `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.
- The R1E contract makes a bounded explicit amendment to R1A's former
  registration-only campaign source description for external-origin sample
  reuse.
- Trial, attempt, protected-access, private-data, dependency, and trading
  impacts remain zero.

Follow-up:

- Add independent fixtures for trial-family, global-local sample, first Stage
  3 external reference, and later external-origin reuse paths.
- Add literal union, source-field, namespace, singleton-scope, authority,
  privacy, incomplete-event, prior-release, package-parity, and
  unpublished-promotion oracles.
- After protected R1E completion, orient the next small registry family and
  surface any genuine owner methodology decision before mutation.

## 2026-07-29 - Select R1D-A Local Sample Registration Authority

Context:

- Stage 4B-R1C is accepted on protected `main` through PR #169 at `68a4c4f`;
  exact merge-head CI run `30471505290` passed.
- R1A and R1C deliberately deferred the exact local sample namespace, Stage 3
  sample-record authority, local/external representation boundary,
  acceptance/currentness, privacy projection, and event boundary because
  helpers, fixtures, and narrative examples are not wire-schema authorities.
- The owner selected the recommended bundle `R1D-A`.

Decision:

- The exact ledger-local `sample_id` namespace is
  `smp_<32 lowercase hex>`.
- Local registration uses an immutable versioned Stage 3 sample-authority
  catalog plus complete repository-external canonical records retrieved by one
  exact digest-pinned resolver tuple. Retrieval miss, ambiguity, schema
  mismatch, noncanonical bytes, digest mismatch, or hash-only stand-in fails
  closed.
- Acceptance and public-projection publication approval are separate complete
  immutable records. The acceptance reviewer is distinct from both the sample
  record producer and registration actor. Both authorities use strictly
  increasing, single-current generations.
- Direct local, global local with later campaign binding, and later external
  Stage 3 reference paths are mutually exclusive. One canonical lineage/path
  has one ledger-local identity per epoch; external references are not
  backfilled as synthetic local registrations.
- Aliases, clones, new campaigns, reruns, window overlap, result access, and
  reclassification do not reset identity or exposure history. Overlap cannot
  manufacture pristine holdout status.
- Complete records, private locators and digests, raw values, and performance
  remain external/private. Public projections contain only allowlisted safe IDs
  and explicitly publication-approved hashes.
- Local sample registration retains the owner-selected common maximum of 32
  direct campaign IDs.
- R1D may publish immutable registry `0.4.0` under unchanged schema-language
  `0.2.0` and promote only `SAMPLE_REGISTERED`.

Rationale:

- Complete retrievable records and independent acceptance prevent hash-only or
  self-reviewed sample registration from becoming formal authority.
- Separate publication approval treats non-reversibility as insufficient for
  public disclosure.
- Stable lineage identity and exclusive representation paths prevent exposure
  resets and duplicate local/external identities.
- Keeping both binding events for R1E avoids laundering incomplete stateful
  source, currentness, and path checks into a local shape schema.

Consequences:

- R1D's owner-methodology gate is cleared. The other 32 event types, including
  `CAMPAIGN_ENTITY_BOUND` and `STAGE3_SAMPLE_REFERENCE_BOUND`, remain
  `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.
- Local schema acceptance proves event shape and pinned references only; it
  does not retrieve records, authenticate roles, determine currentness, enforce
  path exclusivity or exposure history, append events, or authorize research.
- Trial, attempt, protected-access, private-data, dependency, and trading
  impacts remain zero.

Follow-up:

- Add independent global/direct fixtures and literal namespace, authority,
  acceptance, currentness, privacy, scope, and unpublished-promotion oracles.
- Prove byte/behavior/package parity for immutable R0, R1B, and R1C releases.
- After protected R1D completion, open separate R1E design authority for both
  binding events and their stateful source/path rules.

## 2026-07-28 - Select R1C-A Trial-Family Registration Authority

Context:

- Stage 4B-R1B is accepted on protected `main` through PR #167 at `a6f7d43`;
  exact merge-head CI run `30424903896` passed.
- R1A/R1B deliberately deferred the exact family namespace, retrievable
  definition authority, acceptance/reviewer-independence model,
  anti-reset/currentness policy, relation vocabulary, and shared direct-scope
  maximum because helpers, fixtures, and narrative examples are not
  wire-schema or methodology authorities.
- The owner selected the recommended bundle `R1C-A`.

Decision:

- The exact `trial_family_id` namespace is `fam_<32 lowercase hex>`.
- Family definitions use an immutable versioned authority catalog plus complete
  repository-external canonical records retrieved by one exact
  schema/canonicalization/catalog/record digest-pinned tuple. Retrieval miss,
  ambiguity, schema mismatch, noncanonical bytes, or digest mismatch fails
  closed.
- Acceptance is a separate immutable canonical record. Its reviewer must be
  distinct from both the definition issuer and registration actor and it binds
  the exact definition tuple and global/direct campaign scope.
- Global multiplicity-family identity is stable. Acceptance generations are
  strictly monotonic, exactly one accepted generation is current, supersession
  is explicit, and currentness is required before registration, trial
  allocation, attempt execution, and protected access.
- Aliases, clones, reruns, new campaigns, result exposure, and post-result
  reclassification do not reset identity or counts. Definition generations use
  `supersedes`; distinct dependent families use `depends_on`; no record may
  self-declare `independent_of`.
- Direct family scope is limited to 32 campaign IDs. The same maximum applies
  to later local sample registration.
- R1C may publish a separate immutable registry `0.3.0` under unchanged
  schema-language `0.2.0` and promote only `TRIAL_FAMILY_REGISTERED`.

Rationale:

- Complete retrievable records prevent hash-only preregistration stand-ins.
- Separate acceptance and role independence prevent self-review from becoming
  formal authority.
- Stable identity and currentness rules prevent multiplicity resets through
  naming, cloning, reruns, campaign changes, or post-result relabeling.
- The finite shared scope bound keeps direct registration auditable while
  retaining global registration plus explicit binding for broad reuse.

Consequences:

- R1C's owner-methodology gate is cleared. The other 33 event types remain
  `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.
- Local schema acceptance proves event shape and pinned references only; it
  does not retrieve records, authenticate roles, determine currentness, enforce
  anti-reset history, allocate campaigns, append events, or authorize research.
- Trial, execution-attempt, protected-access, private-data, dependency, and
  trading impacts remain zero.
- Future owner-methodology gates use at most four owner-facing reminders at
  30-minute intervals. If no owner answer follows the fourth reminder, the
  heartbeat pauses instead of emitting repeated quiet status messages.

Follow-up:

- Add independent global/direct fixtures and literal namespace, authority,
  acceptance, currentness, relation, and scope killing oracles.
- Prove byte/behavior/package parity for immutable R0 and R1 releases.
- After protected R1C completion, open a separate R1D owner gate for the exact
  sample and Stage 3 reference authority.

## 2026-07-28 - Ratify The Experiment Allocation Namespace

Context:

- Stage 4B-R1A is accepted on protected `main` through PR #166 at
  `9cf5325`; exact merge-head CI passed.
- Architecture A deliberately deferred the experiment prefix because helpers,
  narrative examples, and rejected fixtures are not wire-schema authorities.
- R1B cannot promote `EXPERIMENT_ALLOCATED` without one exact owner-ratified
  typed namespace.

Decision:

- The owner selected option `E1`.
- The exact `experiment_id` wire namespace is
  `exp_<32 lowercase hex>`.
- This owner decision, not any pre-existing helper or fixture, is the authority
  for the prefix.
- R1B may use the namespace only in its separate immutable registry `0.2.0`
  authority and exact `EXPERIMENT_ALLOCATED` schema.

Rationale:

- `exp_` is a short, type-specific namespace that remains disjoint from the
  accepted `cmp_` campaign namespace and the other frozen ledger-owned types.
- Explicit ratification prevents accidental promotion of non-authoritative
  documentation or test data into a production wire contract.

Consequences:

- R1B's final owner-methodology gate is cleared.
- The decision authorizes only typed syntax. It does not prove allocation,
  uniqueness, parent existence, authorization, append order, preregistration,
  or any research action.
- Trial-family and sample prefixes remain unresolved owner decisions for later
  releases. Their events remain `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.
- Trial, execution-attempt, protected-access, private-data, and trading impacts
  remain zero.

Follow-up:

- Publish and validate the separate R1 registry/digest without changing R0
  bytes or behavior.
- Meta-test all three schema-language `0.2.0` additions and keep the other 34
  events fail closed.

## 2026-07-28 - Select Versioned Minimal Allocation/Registration Architecture

Context:

- Stage 4B-R0 is accepted on protected `main` through PR #165 at `4c874eb`;
  exact merge-head CI passed.
- Six non-overlapping read-only audits examined campaign/experiment allocation,
  family/sample registration, local/global/external binding, schema-language
  expressiveness, independent vector evidence, and adversarial scope/privacy
  risks.
- The audits agreed that promoting the six-event family from narrative fields
  or test helpers would launder incomplete semantics into false wire-schema
  coverage.
- The owner selected architecture A after reviewing the materially different
  versioned-minimal and definition-bearing alternatives.

Decision:

- Preserve the R0 registry and sidecar byte-for-byte and preserve accepted R0
  validator behavior. Add R1B as separate registry version `0.2.0` artifacts;
  every later promotion batch publishes a new immutable, monotonically
  versioned registry release rather than overwriting an accepted release.
- Retain the accepted 37-event vocabulary. Do not split
  `CAMPAIGN_ENTITY_BOUND`; use a future closed tagged union.
- Make `CAMPAIGN_ALLOCATED` and `EXPERIMENT_ALLOCATED` reservation-only.
  Complete campaign and experiment definitions belong to later exact
  campaign-inventory schemas before attempt or protected access.
- Use the allocated, registered, or bound entity as subject. Preserve the
  accepted `cmp_` campaign namespace; defer exact experiment, trial-family,
  and sample prefixes to owner decisions in R1B, R1C, and R1D.
- Place `campaign_scope_ids` explicitly in each family payload. Every campaign
  in a shared direct registration must already be allocated.
- Version the closed schema language before adding tagged unions,
  array/path membership, or `safe_public_id`; never retrofit those semantics
  into R0.
- Require future exact, immutable, schema-versioned family-definition and
  Stage 3 sample authorities with retrievable canonical records. Preserve the
  selected exact Stage 3 decision-binding/currentness rules, but defer family
  acceptance, reviewer identity/independence, decision schema, and currentness
  policy to R1C. An ID plus digest alone is not sufficient.

Rationale:

- Immutable coexistence preserves accepted R0 reproduction and prevents a
  later validator from silently reinterpreting old evidence.
- Reservation-only allocation keeps identity creation separate from the full
  research protocol and avoids partial or hash-only preregistration.
- Entity subjects and explicit scope make evidence inclusion reviewable without
  redundant scalar fields.
- Closed versioned unions and safe reference tokens prevent generic-ID,
  nullable-arm, path, URI, free-text, and private-data laundering.

Consequences:

- R1A is design-only. `LEDGER_EPOCH_CREATED` remains the sole
  `FROZEN_SUPPORTED` event and all other 36 events remain
  `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.
- Trial count, execution-attempt count, and protected-sample access remain
  zero. No dependency, backend, private data, or trading behavior is added.
- The first implementable follow-up is a separate R1B batch for exact
  campaign/experiment allocation schemas only, after the owner ratifies the
  exact experiment namespace.
- Family, sample, and binding events remain blocked by their exact authority,
  anti-reset, alias/currentness, finite-bound, and privacy decisions.
- R1B must implement and meta-test all three closed schema-language `0.2.0`
  additions even though only array/path membership is consumed by its event
  schemas.

Follow-up:

- Complete R1A documentation gates without changing registry artifacts.
- In R1B, add a separate versioned R1 authority and independent allocation
  vectors, ratify the exact experiment namespace, meta-test all schema-language
  `0.2.0` additions, and prove R0 byte/hash/behavior/package parity.
- Continue with separately reviewed family, sample, and binding decisions
  before the later 37-of-37 closure and runtime architecture gates.

## 2026-07-28 - Start Stage 4B With A Fail-Closed Registry Foundation

Context:

- Stage 4a is accepted on protected `main` through PR #164 at `27f0497`; exact
  merge-head CI passed.
- The accepted contract closes the event vocabulary at 37 values but freezes
  an exact payload schema only for `LEDGER_EPOCH_CREATED`.
- Six non-overlapping read-only audits found that exact subject, campaign
  scope, fields, nullability, unions, nested objects, enums, ordering, safe
  vocabularies, and cross-field constraints remain intentionally unresolved
  for the other 36 events.
- Existing checkpoint helpers and the rejected trial-allocation stub are
  synthetic semantic evidence, not event wire schemas.

Decision:

- Begin Stage 4B with the bounded
  `experiment_trial_ledger_schema_registry_r0` contract.
- Package one self-contained ASCII canonical JSON registry in a separate
  `ledger` namespace. Use the JSON artifact, not Python constants, as the
  registry authority.
- Bind the full registry object, including vocabulary, type definitions,
  schemas, constraints, incomplete-event declarations, and vectors, into one
  canonical lowercase SHA-256 whose sidecar is outside the preimage.
- Parse raw registry and event JSON with duplicate-property detection before a
  mapping exists. Reject floating-point, non-finite, and non-I-JSON numbers.
- Freeze a small closed schema DSL sufficient for the accepted epoch schema;
  later descriptor kinds require a versioned amendment.
- Keep `LEDGER_EPOCH_CREATED` as the sole `FROZEN_SUPPORTED` event. Reject the
  other 36 known events as `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY` and unknown
  events as `UNKNOWN_EVENT_TYPE` before append or action.
- Do not call R0 a complete registry, Stage 4B conformance, or ledger runtime.

Rationale:

- A generic object, free string, opaque metadata map, hash-only stand-in, or
  test-derived fact set would turn name coverage into false schema coverage.
- Exact subject and scope rules determine campaign evidence inclusion and
  checkpoint currentness; guessing them could conceal relevant events.
- The standard library is sufficient for the ASCII R0 registry and avoids a
  premature production-dependency decision.

Consequences:

- Trial count, execution-attempt count, and protected-sample access remain
  zero. No private data, provider, campaign, performance result, or trading
  behavior enters R0.
- The legacy reporting writers and registries remain unchanged.
- Stage 5 and formal interpretation remain blocked.
- Storage backend, private location, transaction/recovery, checkpoint
  currentness, authority/signature, capability security, and fork policy
  remain owner decisions.

Follow-up:

- Add exact schemas in separately reviewed event-family decisions, beginning
  with allocation/registration only after its subject, scope, ID namespaces,
  payload, null/union/order rules, and stateful boundary are frozen.
- Use a separate closure stage to prove 37-of-37 exact coverage with no
  incomplete, wildcard, open-object, or free-text stand-ins. Payload-registry
  acceptance will still not imply runtime completion.

## 2026-07-27 - Freeze Semantic Trials, Attempts, And Ledger Completeness

Context:

- Stage 3 is accepted on protected `main` through PR #163 at `a6c147e`, but no
  dataset is accepted for formal interpretation.
- The existing schema-v1 experiment writer creates overwrite-capable
  successful-run sidecars after computation. It cannot retain
  failed-before-write, abandoned, retried, or overwritten history and is not an
  immutable all-trial ledger.
- A record hash chain alone cannot detect deletion of a valid tail when the
  writer can also replace the retained head.

Decision:

- Propose `docs/experiment_trial_ledger_contract.md` as the Stage 4a design
  authority, subject to final current-head review, protected merge, and exact
  merge-head CI.
- Treat `trial_id` as one frozen semantic configuration and `attempt_id` as one
  invocation. Retain both semantic trial count and execution-attempt count;
  operational retries never erase failed attempts.
- Require durable allocation before validation/execution and a committed exact
  access-intent capability before protected content can be released.
- Seal the complete campaign inventory and global dependence-family lineage;
  preserve failures, invalid/aborted/excluded work, artifacts, access, review,
  and promotion decisions through append-only events and supersessions.
- Bind each initial inventory seal to one
  `campaign_inventory_preseal_head_v1` semantic anchor whose ledger ID and
  exact predecessor sequence/hash are included in the seal request/event
  preimage. Compare that anchor to the actual current stream head at the same
  serialized atomic boundary that assigns the seal sequence and
  `previous_event_sha256`; head drift conflicts rather than rebasing. This
  ordering anchor is not the independently retained closure checkpoint and
  selects no storage backend.
- Reuse `pit_canonical_json_v1` for an exact ledger-event identity projection,
  chain every event to the prior hash, and require an independently retained
  immutable head/checkpoint for formal campaign closure.
- Freeze an exact `campaign_evidence_checkpoint_v1` preimage. Reconstruct its
  all-and-only campaign-scoped evidence prefix from the retained chain; bind
  the cutoff, freeze, sealed inventory, and one ordered checkpoint reference;
  and reconcile sealed/terminal semantic-trial counts plus
  allocated/terminal attempt counts. Equal counts never replace exact set,
  membership, uniqueness, or current-disposition checks.
- Use the application-level `ledger_v1_utc_timestamp` profile for ledger event
  timestamps. It preserves proleptic-Gregorian year `0000`, ordinary UTC
  seconds, and normalized arbitrary-precision nonzero fractions, but rejects
  every `second = 60` because Stage 4a pins no immutable leap-second table.
  This narrows ledger schema acceptance without changing
  `pit_canonical_json_v1` serialization.
- Keep the independently retained evidence-closure checkpoint separate from a
  second exact `campaign_adjudication_checkpoint_v1`. The latter anchors the
  final adjudication event and therefore the complete closure, review,
  promotion/disposition, and adjudication chain. Its preallocated checkpoint
  ID avoids a digest cycle; its generation and predecessor ID/hash form a
  monotone lineage. Any later event scoped to that campaign makes the prior
  adjudication checkpoint non-current and requires a new complete cycle and
  successor checkpoint. An unrelated campaign or truly ledger-global suffix
  does not.
- Treat checkpoint latestness and anti-rollback as an external Stage 4b gate.
  Before any post-adjudication campaign action, the next generation must become
  pending under the independent `(ledger_id, campaign_id)` authority key;
  pending, missing, forked, skipped, or unverifiably current generations fail
  closed. A local old ledger plus old checkpoint cannot prove that a later
  generation was not created and then hidden.
- Allocate each ledger-owned logical typed entity ID exactly once. Later
  lifecycle, correction, supersession, review, and decision records reuse that
  ID as a typed subject or reference; only a second allocation conflicts. Event
  IDs, operation IDs, and sequences continue to identify distinct
  append/request/commit records and cannot be reused inconsistently.
- Treat event `actor_id` as an externally assigned, opaque
  claimed-attribution reference, not a ledger-owned entity allocation.
  `LEDGER_EPOCH_CREATED` atomically introduces `ledger_id`; no earlier event is
  possible. Stage 4a validates only canonical actor syntax and identity
  binding. It does not prove authenticity, control, authorization, role
  independence, currentness, or revocation, and grants no append, access,
  review, or promotion permission. Any formal behavior that depends on those
  properties remains fail closed until Stage 4b accepts an owner-approved
  external mechanism and historical activation/replacement/revocation policy.
  Stage 4a does not select that identity architecture.
- Freeze the exact common identity envelope and the synthetic
  `LEDGER_EPOCH_CREATED` payload in Stage 4a. Keep the complete
  `TRIAL_ALLOCATED` bindings and parent order as normative semantic
  requirements, but reject that event as
  `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY` until Stage 4b accepts a complete
  machine-readable per-event payload-schema registry.
- Keep execution state separate from charter candidate evidence state.
- Keep the full ledger private and repository-external; expose only a
  deterministic allowlisted public projection without paths, credentials, raw
  values, directions, magnitudes, ranks, or private performance.

Rationale:

- Complete multiplicity and failure accounting is necessary before statistical
  evidence can be interpreted.
- Separate trials and attempts prevent infrastructure retries from either
  inflating configuration multiplicity or concealing failed executions.
- Prospective access barriers and monotone sample downgrades prevent
  after-the-fact holdout laundering.

Consequences:

- Stage 4a is a documentation/golden-contract stage only. It adds no runtime,
  database, migrated log, research trial, private access, generated performance
  evidence, dependency, or trading behavior.
- Stage 4a's epoch golden and non-append semantic fact vectors do not establish
  contract-wide payload validation or Stage 4b conformance.
- Stage 4a's adjudication-checkpoint vectors establish exact identity, lineage,
  chain anchoring, and staleness semantics only. They do not implement an
  independent currentness authority or make a campaign formally complete.
- Stage 4a's evidence-checkpoint vector uses one fixed all-excluded trial and
  zero attempts to prove exact prefix/checkpoint bytes and set/count
  relationships. General event payload, scope, inventory, and lifecycle
  extraction remains fail closed until the Stage 4b registry is accepted.
- Legacy logs remain `DIAGNOSTIC_ONLY` references and cannot prove formal
  completeness or holdout independence.
- Stage 5 remains blocked until Stage 4b implements and behaviorally verifies
  the accepted contract.

Follow-up:

- In the first separate Stage 4b slice, freeze the complete machine-readable
  event payload-schema registry, deterministic positive/negative vectors, and
  registry digest. Then choose and justify the storage, transaction/recovery,
  private-location, independent checkpoint/currentness authority, append-only
  anti-rollback, concurrency/fork, signature/authorization, and recovery
  policies in separately reviewable architecture/implementation work; add
  fault, restart, concurrency, tamper, rollback, protected-access, closure, and
  privacy tests before integrating one synthetic workflow.

## 2026-07-27 - Separate Data Methodology, Dataset, And Interpretation Gates

Context:

- Protected `main` at `8a352d3` implements the purged split and explicit
  signal/execution timing contracts, but the repository has no accepted
  provider-agnostic authority for deciding whether a historical dataset is
  point-in-time, licensed, reproducible, privacy-safe, or suitable for formal
  interpretation.
- Existing local-CSV loaders and diagnostics validate selected shapes and
  calculations only. They do not prove historical membership, permanent
  identifiers, delistings, corporate actions, field availability/revisions,
  calendar alignment, benchmark/risk-free suitability, or immutable lineage.
- Private diagnostics previously calculated and reviewed the interval
  2025-05-01 through 2026-05-31.

Decision:

- Adopt `docs/point_in_time_data_methodology_contract.md` as the proposed Stage
  3 provider-agnostic contract.
- Keep `methodology_contract_accepted`, `dataset_manifest_reviewed`, and
  `formal_interpretation_eligible` as separate review decisions. The first
  never implies the second, and the second never implies the third.
- Require immutable content and ordered-manifest hashes, evidence-backed
  license state, versioned canonicalization and environment identity,
  transformation lineage, permanent/listing identifiers, bitemporal membership
  and field availability, corporate-action and delisting treatment, compatible
  price/volume semantics, typed missingness, versioned calendars,
  benchmark/risk-free policy, private/public projections, and an immutable
  exact-version review decision from an authorized non-producing reviewer
  before a dataset-specific review can pass.
- Define `pit_canonical_json_v1` as typed NFC/timestamp/decimal preprocessing
  followed by exact RFC 8785/JCS serialization, with contract and review
  decisions bound to reproducible content/protected-merge identities.
- Classify 2025-05-01 through 2026-05-31 as
  `historical_evaluation`. It cannot later be upgraded to a pristine holdout.
- Assign append-only trial and protected-sample access enforcement to Stage 4.
  Stage 3 defines the record schema and anti-backfill rules but does not claim
  to implement them.
- Treat access to asset/benchmark paths and other inputs capable of
  reconstructing protected outcomes as exposure. Public records carry only
  allowlisted policy states, publication-approved hashes or redacted evidence
  references, and never restricted license evidence or private metric values.

Rationale:

- A general methodology can be reviewed without selecting a vendor or reading
  private values, while a concrete dataset and run still require independent
  evidence.
- Separate gates prevent a loader check, hash, license assertion, static
  cohort, or completed checklist from being mistaken for historical validity.
- Conservative sample classification preserves falsifiability after prior
  exposure.

Consequences:

- Stage 3 is documentation and workflow-control only. It adds no provider,
  downloader, credential, source-data artifact, factor, research result,
  dependency, or trading capability.
- Existing static-universe EODHD work remains `DIAGNOSTIC_ONLY`; no current
  dataset becomes `formal_ready`.
- Formal real-data interpretation remains blocked until a dataset manifest,
  Stage 4 all-trial/access ledger, Stage 5 statistical protocol, and every
  applicable downstream gate pass.

Follow-up:

- Complete Stage 4 as a small reviewable experiment/trial-ledger stage after
  the Stage 3 PR is protected-merged and its exact merge-head CI passes.

## 2026-07-27 - Require Tracked Pre-Mutation Backtest Source Provenance

Context:

- Pandas may promote an entire homogeneous real column to `complex128` after
  one complex assignment.
- Assigning `1+0j` before the evaluation window and assigning the same value
  inside it can produce byte-equivalent final frames. A post-hoc dtype or cell
  snapshot cannot identify which coordinate was written.
- Stage 2 requires both strict bounded-complex rejection and invariance to
  values that are provably outside the bounded accounting window.

Decision:

- Require `source_provenance` on every `run_long_only_backtest` call; provide no
  default or compatibility bypass.
- Treat capture as a caller-declared baseline after final panel construction.
  Enforcement begins at that call and cannot infer mutation/type history
  already erased beforehand.
- Bind each library-issued handle to its role, exact axes, original semantic
  cell/dtype state, current source identity/state, and an immutable chained
  mutation ledger.
- Require any later source write to use the controlled coordinate API.
  Untracked writes, copied/replaced source objects, stale axes, swapped roles,
  malformed records, or replay-inconsistent state fail with
  `source_provenance_invalid`.
- Recover an originally real column promoted to complex only when the ledger
  records a complex write outside the current bounds and each recovered bounded
  cell matches its original real or IEEE-NaN semantics losslessly. Native
  complex sources, bounded complex writes, and lossy conversions retain their
  signal or price domain failure.
- Emit only the allowlisted provenance policy/status strings in result
  metadata. Reject direct and nested provenance objects at the experiment-log
  serializer and scan current committed logs for private field names. Extracted
  primitive values or reconstructed plain mappings remain caller-controlled.

Rationale:

- Mutation-time coordinates are the minimum evidence that distinguishes the
  identical-frame counterexample; dtype-only or snapshot-only provenance is
  information-theoretically insufficient.
- Required provenance avoids a permissive legacy path and makes every current
  caller state its source-construction boundary.
- Internal snapshots are software-control evidence, not vendor lineage,
  point-in-time proof, or research validity.
- The contract proves controlled post-capture history only; it cannot establish
  what happened before the caller-declared baseline.

Consequences:

- The backtest API is intentionally breaking for callers that omit
  provenance.
- Arbitrary pandas mutation after capture invalidates the handle; callers that
  need a controlled test mutation must use the tracked API.
- This closes the Stage 2b provenance decision without adding a dependency,
  changing a factor, reading private results, or creating a research trial.
- The trust boundary is an in-process library-issued handle, not cryptographic
  proof against a malicious caller.

Follow-up:

- Complete the Stage 2b local gates, independent read-only review, GitHub CI,
  and final stable-head Codex review before any protected merge.

## 2026-07-26 - Freeze Signal, Execution, and Metric Timing

Context:

- Protected `main` at `202273b` contains the Stage 1 implementation and a
  637-test software baseline.
- `run_long_only_backtest()` describes every signal as available after its
  timestamp's close but accepts zero lag, silently reindexes signals, and uses
  execution-close price validity while forming target membership.
- A lag-one target set on row `t` is installed only after the return ending on
  `t`; it first earns the return ending on the next source row.
- Annualized return, volatility, Sharpe, tracking error, drawdown, benchmark,
  and warm-up handling do not yet share one declared evaluation anchor.

Decision:

- Adopt `after_close_signal_next_observed_close_v1` as the only timing policy
  for the current close-only backtester.
- Conservatively treat every generic final signal as available strictly after
  its stamped close. Require a non-boolean integer accounting-row lag of at
  least one; lag zero is not a hidden same-close or next-open model.
- Distinguish the full source index `s[0..M]` from the exact bounded accounting
  slice `a[0..N]`. For every scheduled execution `a[j]`, map lag `L` to source
  signal `a[j-L]` and freeze the target immediately after that signal becomes
  available. Pre-anchor `s` rows may support feature calculation but cannot
  satisfy execution lag. Under daily rebalancing, fixture `d0` as `a[0]` maps
  to an idealized target reset at `d1`/`a[1]` close and its first earned return
  over `(d1,d2]`.
- Require exact signal/price axes and timezone compatibility. Freeze ranking,
  selection, constraints, and intended weights from decision-time
  information; execution-close feasibility cannot rerank or redistribute, and
  available signals must be real numeric, non-Boolean, and finite, with only
  IEEE `NaN` denoting an unavailable score. Every held incoming-price endpoint
  and nonzero buy or sell execution leg requires a real numeric, non-Boolean,
  finite, strictly positive price without coercion.
- Preserve the drift-aware order: prior holdings earn the incoming return,
  drift to pre-trade weights, trade to the frozen target, incur close-time
  costs, and become post-trade holdings for the next return.
- Require explicit bounded `evaluation_start` and `evaluation_end`.
  `evaluation_start` is a zero initialization anchor; all period-return metrics
  and benchmark-relative metrics use the same later rows. Bounds must be exact
  scalar timestamps resolved to unique integer positions; partial-label
  strings, implicit rounding, timezone conversion, and non-inclusive slicing
  are invalid.
- Fix daily annualization at a non-boolean integer 252 so basic and
  benchmark-relative metrics cannot use conflicting annualizers.
- Include initial capital in drawdown, keep the benchmark cost-free on the
  identical measured window, and retain the observed-bucket terminal target,
  cost, open-holdings, and no-future-return convention.
- Compute tracking error only from strategy net and cost-free benchmark returns
  selected by exact `measured_return_dates`. Preserve the public helper's zero
  benchmark anchor; a nonzero strategy-anchor sentinel may appear only in a
  direct helper test proving that the anchor is excluded.
- Require initial capital to be a real numeric, non-Boolean, finite positive
  scalar. Validate finite gross return and a finite positive gross multiplier
  before pretrade division, drift, trades, or costs; validate finite net return,
  a finite positive net multiplier, and finite positive resulting equity after
  costs but before equity update, metrics, or a successful result. Direct
  metric helpers independently reject invalid equity curves and return series
  before annualization or drawdown. Failures retain distinct stable evidence
  reasons for the later immutable trial ledger.
- Require typed timing metadata and a Stage 2b event ledger over the sorted
  de-duplicated union of the initialization anchor and resolved rebalance dates.
  The anchor has no incoming interval; later insufficient-lag rows retain their
  measured all-cash incoming interval but have no execution or first-holding
  interval.

Rationale:

- A close-derived signal cannot use that same close as both its final input and
  its fill without a separately defined pre-close or auction information
  model.
- Close-only inputs can support a transparent next-observed-close simulation;
  next-open would require open prices and overnight/intraday decomposition.
- Separating frozen intent from execution feasibility prevents the execution
  close from silently changing portfolio membership.
- Explicit bounds and a shared anchor keep feature warm-up and synthetic
  initialization rows from contaminating strategy-versus-benchmark metrics.
- Separating pretrade gross failure, post-cost net/equity failure, and
  downstream metric-input validation prevents invalid division, complex
  annualization, and misleading successful evidence.

Consequences:

- `docs/signal_execution_timing_contract.md` is the implementation authority
  for Stage 2b.
- Stage 2a does not fix runtime behavior. Zero lag, silent alignment,
  execution-close target filtering, inconsistent metric anchors, and untyped
  metadata remain visible implementation gaps until Stage 2b. The accepted
  signal/incoming/execution-price, capital-validity, and direct metric
  equity/return failure boundaries are also pending.
- Existing Stage 1 one-row price labels and same-row synthetic responses remain
  diagnostic targets, not strategy returns under this execution policy.
- The local model remains idealized close-reset accounting, not MOC, order,
  fill, capacity, brokerage, or LEAN evidence.
- This stage creates zero research trials, changes no factor or result, opens
  no private data, and authorizes no paper or live behavior.

Follow-up:

- Implement the 14-case deterministic timing matrix test-first in Stage 2b,
  migrate every current backtest caller, regenerate only changed synthetic
  artifacts, and pass full CI and final current-head review before merge.

## 2026-07-26 - Freeze The Purged And Bounded Split Contract

Context:

- Protected `main` at `57f3db3` contains the Research Charter Reset and a
  594-test software baseline.
- `make_train_validation_test_split()` still has implicit starts, rejects a
  bounded `test_end`, and cannot retain source history outside the split axes.
- Both current price-derived diagnostic workflows calculate forward returns on
  the complete panel before slicing by signal date. The local fixture workflow
  also calculates unsplit diagnostics from those targets.

Decision:

- Require six explicit inclusive train/validation/test boundaries and allow
  recorded gaps.
- Treat `test_end` as a hard information cutoff even when later source rows
  exist. No post-test value may complete a test label.
- Define price-derived row-horizon labels by exact `signal_date`,
  `label_start`, and `label_end`; purge every label whose complete interval is
  not contained in one configured window.
- Require typed label-kind and derivation metadata. Existing synthetic split
  responses use exact same-row `[t,t]` intervals and cannot claim a price
  forward-return horizon.
- Keep raw split axes visible and mask purged or embargoed target rows to
  `NaN`. Preserve zero-eligible windows as visible `INVALID` evidence.
- Keep purge and optional row-based embargo as independent recorded flags. A
  preregistered explicit gap can satisfy embargo, with exact transition sets
  and partial-gap behavior recorded.
- Record exact feature warm-up dates, in-window purged label warm-down dates,
  ignored post-test dates, and per-candidate exclusion reasons.
- Separate structural eligibility from consumer-level valid/missing target
  cells and usable factor-label pairs; retain `no_usable_label_pairs`.
- Require post-test and cross-boundary mutation-invariance tests before Stage
  1b can be accepted, including independent raw asset and benchmark mutation.

Rationale:

- Non-overlapping signal-date rows do not isolate samples when a target still
  reads a later split's prices.
- A hard information cutoff is the narrow interpretation consistent with the
  charter rule that a complete label interval must belong to one split.
- Masking rather than dropping exclusions keeps sample failures and raw date
  counts auditable without exposing invalid label values to metrics.

Consequences:

- `docs/purged_bounded_split_contract.md` is the implementation authority for
  Stage 1b.
- The current code defects remain present until Stage 1b; this design does not
  validate or reinterpret any existing diagnostic.
- Stage 2 execution timing, nonzero-embargo selection, walk-forward folds,
  point-in-time data, and empirical thresholds remain deferred.
- This stage creates zero research trials, reads no private values, and changes
  no factor, label, strategy, portfolio, cost, benchmark, or LEAN behavior.

Follow-up:

- Implement the contract test-first in Stage 1b, migrate every current
  future-return consumer, regenerate only affected synthetic evidence, and run
  the full current-head validation and review gates.

## 2026-07-26 - Reset The Research Program Around Evidence Gates

Context:

- The verified `a1486ea` baseline is a strong deterministic simulated research
  toolkit, but its prior objective and roadmap do not cover a research-grade
  factor-to-portfolio validation program.
- Read-only audits confirmed cross-split forward labels, ambiguous zero-lag
  after-close execution, fixed-cohort data limitations, incomplete
  all-trial/statistical controls, and prior diagnostic access to the proposed
  2025-05-01 through 2026-05-31 evaluation interval.

Decision:

- Adopt `docs/research_program_charter.md` as the canonical long-term evidence
  policy and keep `docs/current_roadmap.md` as the active stage sequence.
- Separate factor, strategy, portfolio, and execution evidence.
- Require point-in-time data methodology, bounded/purged samples, immutable
  trial accounting, dependence/multiple-testing controls, frozen evaluation,
  and independent reproduction before later LEAN parity candidacy.
- Treat a static or otherwise unverified historical universe as diagnostic
  only, even when its survivorship caveat is documented.
- Keep `EXPERIMENT_LOG.md` as a diagnostic/legacy record until Stage 4 provides
  immutable pre-execution identifiers and complete all-trial retention.
- Require any applicable Codex review to complete on the current head with no
  unresolved actionable findings before auto-merge or normal protected merge;
  an actionable fix requires stable CI and re-review on the new head.
- Classify previously examined data as historical evaluation or pseudo-holdout
  unless a holdout exposure ledger proves a narrower claim.
- Keep the current phase research-only. Paper runtime, live trading, brokerage,
  credentials, and orders remain unauthorized.

Rationale:

- Software reproducibility does not by itself establish empirical validity.
- Adding factors or parameters before timing, data, trial, and inference
  controls would increase hidden research degrees of freedom.
- A precise evidence taxonomy prevents diagnostic calculations from being
  promoted as strategy, portfolio, or deployment evidence.

Consequences:

- The next stage is the purged and bounded split contract, not factor
  expansion, data interpretation, or LEAN work.
- PR #148 remains an independent Draft because it changes only `AGENTS.md`;
  this charter stage avoids that file and does not alter the PR.
- This decision creates no research trial and reads no private performance
  values.

Follow-up:

- Complete Stage 1a design for split boundaries, label ownership, purge,
  optional embargo, and warm-up/down metadata before timing implementation.

## 2026-07-11 - Attribute Episode Returns From Signed Trades

Context:

- Daily positive-return frequency cannot represent holding-episode hit rate.
- Partial resizing and applied trading costs make price-only round trips
  insufficient for average holding-period return.

Decision:

- Define one episode as an uninterrupted run of positive post-trade closing
  weight for one asset; resizing continues it and re-entry after a zero close
  starts another.
- Require signed trade weights from the backtester. Define episode return as
  net portfolio contribution divided by cumulative positive deployed weight.
- Allocate applied daily costs pro rata by absolute signed trade weight. Exclude
  terminal-open episodes rather than inventing an exit.

Rationale:

- Signed trades preserve direction and let episode costs and deployed capital
  reconcile to existing turnover and cost accounting.
- The contract handles resizing without adding tax lots, fill simulation, IRR,
  or another accounting engine.

Consequences:

- Only completed episodes contribute to hit rate and average holding-period
  return; open counts remain visible in assumptions.
- Volume-impact allocation is an accounting convention, not causal impact
  estimation.
- Implementation is deferred to a separate PR.

Follow-up:

- Expose signed trades and implement the two approved metrics with exact
  reconciliation tests.

## 2026-07-11 - Clip Position Caps Without Renormalization

Context:

- Tracking error is implemented and the next roadmap checkpoint is portfolio
  constraint design.
- The current backtester selects equal-weight long-only targets and calculates
  turnover and costs from target changes versus drifted holdings.

Decision:

- The first optional constraint is a per-position maximum applied after
  selection and before trade calculation.
- Breaching weights are clipped. Removed weight is not redistributed or
  renormalized; it remains explicit non-interest-bearing cash.
- Liquidity eligibility remains upstream, while turnover and costs use the
  constrained targets.

Rationale:

- Holding cash preserves the cap without silently changing selection or
  manufacturing exposure to other assets.
- A single narrow constraint can be tested against the existing accounting
  path without implying a general production risk engine.

Consequences:

- Infeasible fully invested targets are valid partial-cash portfolios.
- Sector, factor, beta, volatility, liquidity, and tracking-error constraints
  require separate designs.
- `src/risk/constraints.py` remains placeholder-only until the implementation
  checkpoint is accepted and started.

Follow-up:

- Implement the approved helper and backtester integration in a separate PR.

## 2026-06-29 - Keep EODHD Diagnostics Brief Neutral

Context:

- PR #126 added a private limited factor diagnostics review that may contain
  diagnostic values.
- The next checkpoint needs a brief that can describe diagnostic direction,
  magnitude, and split consistency.
- The brief must not become strategy, portfolio, investment, alpha,
  profitability, or trading-readiness interpretation.

Decision:

- Add `research/eodhd_limited_factor_diagnostics_brief.py` as a
  private-output-only neutral diagnostics brief runner.
- Read the private limited review JSON and write the real-data brief only under
  `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run`.
- Commit synthetic tests and aggregate-count docs only; do not commit private
  logs, private market data, or private diagnostic values.

Rationale:

- Neutral direction, magnitude, and split-consistency labels make diagnostics
  easier to inspect without converting them into performance or investment
  claims.
- Keeping the brief private preserves the local-data boundary while allowing
  audited continuation.

Consequences:

- Future work must preserve the no-strategy/no-performance boundary unless a
  separate reviewed checkpoint explicitly changes scope.
- Strategy runs, backtests, portfolios, PnL, Sharpe, drawdown, trading metrics,
  investment recommendations, profitability claims, alpha claims, and
  trading-readiness language remain out of scope.

Follow-up:

- Decide whether another metadata-only methodology/data-readiness checkpoint is
  needed before any broader research interpretation.

---

## 2026-06-28 - Keep Limited Factor Diagnostics Non-Interpretive

Context:

- PR #125 added a private readiness review with
  `ready_for_limited_factor_diagnostics_review=True`.
- The next checkpoint may inspect already-computed diagnostics, but only inside
  the allowed diagnostics scope.
- The review must not become strategy, portfolio, investment, alpha,
  profitability, or trading-readiness interpretation.

Decision:

- Add `research/eodhd_limited_factor_diagnostics_review.py` as a
  private-output-only limited diagnostics review runner.
- Summarize only factor coverage, factor missingness, IC, Rank IC, quantile
  spread, and split labels.
- Write the real-data limited review only under
  `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run`.
- Commit synthetic tests and aggregate-count docs only; do not commit private
  logs, private market data, or private diagnostic values.

Rationale:

- The readiness review proves the metadata gate is ready for a limited review.
- Keeping the review private and non-interpretive allows diagnostics to be
  inspected without converting them into performance or investment claims.

Consequences:

- Future work must preserve the no-strategy/no-performance boundary unless a
  separate reviewed checkpoint explicitly changes scope.
- Strategy runs, backtests, portfolios, PnL, Sharpe, drawdown, trading metrics,
  investment recommendations, profitability claims, alpha claims, and
  trading-readiness language remain out of scope.

Follow-up:

- Decide whether another metadata-only methodology/data-readiness checkpoint is
  needed before any broader research interpretation.

---

## 2026-06-28 - Keep EODHD Readiness Review Narrow

Context:

- PR #124 added a private experiment-log/readiness handoff for the EODHD
  factor diagnostics dry run.
- The next checkpoint needs to decide only whether the metadata is ready for a
  future limited factor-diagnostics review.
- The review must not become strategy readiness, alpha readiness, trading
  readiness, live-use readiness, or performance interpretation.

Decision:

- Add `research/eodhd_factor_diagnostics_readiness_review.py` as a
  private-output-only readiness runner.
- Name the readiness field `ready_for_limited_factor_diagnostics_review`.
- Write the real-data readiness review only under
  `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run`.
- Commit synthetic tests and aggregate-count docs only; do not commit private
  logs, private market data, or private diagnostic values.

Rationale:

- A narrow metadata gate proves the required artifacts and guardrails exist
  before any human or future script inspects factor diagnostics.
- Avoiding broader readiness names prevents the checkpoint from being mistaken
  for strategy, alpha, trading, or live-use approval.

Consequences:

- Future work may inspect factor diagnostics only inside the explicitly limited
  no-strategy/no-performance boundary.
- Strategy runs, backtests, portfolios, PnL, Sharpe, drawdown, trading metrics,
  profitability claims, alpha claims, and trading-readiness language remain out
  of scope.

Follow-up:

- If continuing, perform a limited factor-diagnostics review that preserves the
  no-strategy/no-performance boundary.

---

## 2026-06-28 - Keep EODHD Factor Diagnostics Experiment Logs Private

Context:

- PR #123 added a private-output-only EODHD factor diagnostics dry run and
  wrote the real-data diagnostics summary under the private bundle.
- The next checkpoint needs an experiment-log/readiness handoff before anyone
  interprets the factor diagnostics.
- The handoff must record private paths, row counts, date range, allowed
  diagnostics, forbidden interpretations, `adjusted_close` policy, and
  static-universe survivorship caveats without committing private market data.

Decision:

- Add `research/eodhd_factor_diagnostics_experiment_log.py` as a
  private-output-only handoff runner.
- Write the real-data experiment log and Markdown handoff only under
  `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run`.
- Commit synthetic tests and aggregate-count docs only; do not commit private
  logs, private market data, or private diagnostic values.

Rationale:

- A structured private handoff makes readiness fields auditable while
  preserving the no-interpretation boundary.
- Keeping the runner narrow avoids adding vendor API code, strategy code, or
  new reporting abstractions.

Consequences:

- Future work can use the private experiment log as readiness input, but must
  still complete a real-data readiness review before interpreting factor
  diagnostics.
- Strategy runs, backtests, portfolios, PnL, Sharpe, drawdown, trading metrics,
  profitability claims, alpha claims, and trading-readiness language remain out
  of scope.

Follow-up:

- Complete the real-data readiness review if continuing toward interpretation.

---

## 2026-06-28 - Keep EODHD Factor Diagnostics Private-Output Only

Context:

- PR #122 checkpointed the private EODHD data-quality diagnostics dry run.
- The next functional checkpoint adds a dry run that computes Alpha#009,
  Alpha#012, IC, Rank IC, and quantile-spread diagnostics from the private
  EODHD bundle.
- These diagnostics are allowed only as research diagnostics, not strategy or
  performance evidence.

Decision:

- Add `research/eodhd_factor_diagnostics_dry_run.py` as a private-output-only
  research script.
- Write the real-data factor diagnostics summary only under
  `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run`.
- Commit synthetic tests and aggregate-count docs only; do not commit private
  data or private diagnostic values.

Rationale:

- Existing loaders, features, diagnostics, and split helpers are sufficient for
  the checkpoint.
- Keeping private values out of repo docs preserves the privacy and
  no-interpretation boundary while still making the workflow auditable.

Consequences:

- Future work must complete a real-data readiness review or experiment-log
  handoff before interpreting the factor diagnostic values.
- Strategy runs, backtests, portfolios, PnL, Sharpe, drawdown, trading metrics,
  profitability claims, alpha claims, and trading-readiness language remain out
  of scope.

Follow-up:

- Prepare the readiness or experiment-log handoff if continuing toward
  interpretation.

---

## 2026-06-28 - Checkpoint Private EODHD Data-Quality Diagnostics

Context:

- PR #121 documented the private-output-only diagnostics dry-run boundary.
- The private EODHD no-performance data-quality diagnostics dry run passed and
  wrote
  `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run/DATA_QUALITY_DIAGNOSTICS_DRY_RUN_SUMMARY.md`.
- The repository needs an aggregate-only checkpoint before any factor
  diagnostics are planned.

Decision:

- Add `docs/eodhd_data_quality_diagnostics_checkpoint.md`.
- Record only aggregate data-quality evidence from the private summary.
- Route the next safe stage to a docs-only factor-diagnostics plan rather than
  factor computation or performance work.

Rationale:

- Data-quality diagnostics are useful readiness evidence but are not factor or
  performance evidence.
- A repo-reviewed checkpoint preserves auditability without committing private
  market data or changing source code.

Consequences:

- Future work may plan factor diagnostics, but it must stay separate from
  returns, IC, Rank IC, quantile spreads, strategy runs, backtests, portfolio
  metrics, profitability, alpha, and trading-readiness claims until reviewed.
- Static-universe survivorship risk and EODHD adjustment-policy ambiguity
  remain visible caveats.

Follow-up:

- Prepare a narrow docs-only factor-diagnostics plan if continuing toward
  real-data factor readiness.

---

## 2026-06-28 - Checkpoint Private EODHD Loader Smoke Before Diagnostics

Context:

- PR #120 added the reviewed plan for a private validation-only EODHD loader
  smoke test.
- The private smoke test then passed outside the repository using existing
  strict loaders and wrote
  `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run/LOADER_SMOKE_TEST_SUMMARY.md`.
- The repository needs an aggregate-only checkpoint before any diagnostics
  dry-run work is scoped.

Decision:

- Add `docs/eodhd_loader_smoke_checkpoint_and_diagnostics_dry_run_plan.md`.
- Record only aggregate loader/schema evidence from the private summary.
- Scope the next diagnostics dry run to data-quality and readiness properties
  only: coverage, calendars, missingness, duplicates, invalid values,
  zero-volume, stale-row, adjustment-policy caveats, and survivorship caveats.

Rationale:

- Loader success is useful readiness evidence but is not research
  interpretation.
- A repo-reviewed checkpoint keeps the workflow auditable without committing
  private market data or changing code.

Consequences:

- Diagnostics may proceed only inside the no-performance boundary.
- Strategy runs, backtests, factor performance, IC, Rank IC, quantile spreads,
  returns, profitability, alpha, robustness, and trading-readiness claims remain
  out of scope.

Follow-up:

- Run or document a private-output-only diagnostics dry run if it can stay
  within this boundary. If source or report changes are needed, stop for a
  separate reviewed plan.

---

## 2026-06-28 - Plan Private EODHD Loader Smoke Test Before Execution

Context:

- PR #119 recorded the completed private EODHD validation-only handoff.
- The private bundle remains outside the repository at
  `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run`.
- The next safe boundary is a loader smoke test, but source, tests, research
  scripts, generated reports, strategy logic, and performance interpretation
  remain out of scope.

Decision:

- Add `docs/eodhd_local_csv_loader_smoke_test_plan.md` before executing the
  loader smoke test.
- Limit the future smoke test to existing strict loaders and metadata-level
  evidence: schema, row counts, date ranges, symbol coverage, missing and
  duplicate counts, invalid-value counts, OHLC consistency, and SPY benchmark
  alignment.
- Require any smoke-test summary to be written only under the private EODHD
  bundle path, not under the repository.

Rationale:

- A short reviewed plan keeps the next private-data operation auditable without
  adding code or committing private market data.
- Loader success would only prove local ingestion readiness, not strategy,
  factor, portfolio, or performance evidence.

Consequences:

- The next stage may run the validation-only loader smoke test using existing
  loaders and private output only.
- Static-universe survivorship risk, raw OHLC versus `adjusted_close`
  adjustment semantics, sample splits, cost/slippage assumptions, execution
  timing, and experiment-log interpretation remain unresolved for research
  interpretation.

Follow-up:

- After this plan merges, execute the loader smoke test only if it can stay
  inside the private-output and no-interpretation boundary.

---

## 2026-06-27 - Record Private EODHD Validation-Only Handoff

Context:

- A private EODHD local CSV bundle exists outside the repository at
  `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run`.
- Private readiness and validation-only summaries reported loader/schema
  validation success without copying raw CSV/JSON data into the repository.
- The repository needs a reviewable handoff before any future loader-smoke-test
  stage can be scoped.

Decision:

- Add `docs/eodhd_local_csv_validation_handoff.md` as a documentation-only
  bridge from private validation evidence to a future reviewed loader smoke
  test.
- Record only aggregate evidence: provider/source, symbol coverage, date range,
  row counts, schema result, benchmark alignment, invalid-value counts, and
  credential-marker scan result.
- Preserve explicit stop-before-strategy language and keep sample split,
  cost/slippage, universe, benchmark, and EODHD adjustment-policy gaps visible.

Rationale:

- The private bundle passed validation-only checks, but that does not make it
  research evidence.
- A repo-reviewed handoff makes the next stage auditable without committing
  private market data or changing loaders, tests, research scripts, reports, or
  strategy logic.

Consequences:

- The next safe stage is a documentation/test-plan or validation-only loader
  smoke test only.
- Strategy runs, factor-performance calculations, backtests, performance
  interpretation, profitability claims, and trading-readiness claims remain
  out of scope.
- Static-universe survivorship risk and raw OHLC versus `adjusted_close`
  adjustment semantics remain unresolved caveats for any later interpretation.

Follow-up:

- Prepare a reviewed experiment-log handoff before any future output is
  interpreted beyond loader/schema readiness.
- Keep the private bundle outside the repository and do not commit raw
  CSV/JSON files.

---

## 2026-06-23 - Require An Explicit Local CSV Readiness Input Package

Context:

- PR #116 reconciled the current roadmap after the committed local fixture
  generated-output refresh.
- The next default boundary is user-provided local CSV readiness inputs.
- The user asked to continue without starting unsafe real-data work, so the
  next safe action is to make the readiness input package explicit.

Decision:

- Require an explicit readiness package before any future local CSV research
  run is loaded, transformed, reported, or interpreted as real-market evidence.
- Treat the package as metadata and planning first: scope statement,
  metadata-only inventory, schema map, readiness audit, experiment handoff
  draft, and explicit approval boundary.
- Keep the default next checkpoint paused until those inputs exist, unless the
  user requests another narrow documentation/test-plan clarification.

Rationale:

- The project can document the gate without reading private/raw local data.
- Real-data interpretation without the package would require assumptions about
  provenance, survivorship, benchmark choice, alignment, splits, costs,
  slippage, and privacy that the project guardrails forbid.

Consequences:

- Future continuations should ask for or review the readiness package before
  touching local CSV contents.
- Documentation-only readiness-template or registry-schema work remains
  possible, but it must not imply that a real-data study can proceed without
  the package.

---

## 2026-06-23 - Pause Default Work At Local CSV Readiness Boundary

Context:

- PR #115 completed the committed synthetic local fixture configured-case
  generated-output refresh.
- The synthetic and local-fixture robustness/reporting sequence now has
  reviewed plans, implementation, tests, and committed generated artifacts.
- No user-provided local CSV bundle, completed readiness audit, or experiment
  handoff is available.

Decision:

- Treat user-provided local CSV readiness inputs as the next default boundary
  before any real-data interpretation.
- Do not add more synthetic or local-fixture generated output by default.
- If the user asks to continue without local data, choose only a
  documentation/test-plan stage that clarifies readiness gates or registry
  schema choices without implying real-data validation.

Rationale:

- More synthetic output would not answer whether stock factors are verifiable
  stock-selection signals on accepted data.
- Proceeding to real-data interpretation without scope, provenance, schema,
  survivorship, benchmark, split, cost/slippage, and readiness-audit evidence
  would violate project guardrails.

Consequences:

- Future continuations should pause at the local CSV readiness boundary unless
  the user supplies the required inputs or explicitly asks for a narrow
  documentation/test-plan clarification.

---

## 2026-06-23 - Allow Protected PR Merge For Eligible Governance Stages

Context:

- The prior workflow required Codex to pause for manual merge after each PR.
- Recent checkpoint work showed that branch protection can be verified, required
  checks can be observed, and PR author/head-owner metadata can confirm the
  branch was pushed by `minqiyang`.

Decision:

- Keep PR creation mandatory for reviewability and branch protection.
- For non-high-risk PRs, allow GitHub auto-merge or normal protected PR merge
  only when GitHub metadata verifies `minqiyang` as author/head owner, branch
  protection or rulesets are verifiable, required checks pass or auto-merge is
  used for pending checks, no required review is pending, and changed-file scope
  matches the declared stage.
- Continue to stop for human review when risk is high or unclear, author/pusher
  identity cannot be verified, protection/check/review status cannot be
  verified, CI is unstable after a bounded wait, or scope is unclear.
- Continue to forbid direct pushes or direct merges to `main`, branch
  protection bypass, ruleset/check/review/merge-queue bypass, and
  `gh pr merge --admin`.

Rationale:

- GitHub-managed auto-merge and normal protected PR merge preserve PR history
  and branch protection while avoiding unnecessary manual merge gates for
  low-risk or otherwise clearly eligible stages.
- Verifying identity from GitHub metadata is safer than trusting local git
  config.

Consequences:

- Staged continuations may proceed through multiple PR-sized stages when each
  PR is eligible and GitHub merges it during the run.
- Existing paused external PR gate behavior still applies to ineligible,
  blocked, high-risk, unclear, or unverified PRs.

---

## 2026-06-12 - Treat Unmerged PR Gates As External Wait State

Context:

- A prior workflow-control rule told Codex to report an unmerged PR gate once
  and pause.
- Active-goal automatic continuations can still resume without a user-stated
  merge, resume, or inspect instruction, which caused repeated pause output for
  the same external PR gate.

Decision:

- Treat any open, closed-unmerged, unknown, or otherwise not-verified-merged PR
  gate as a paused external wait state after one concise current-state report.
- Automatic continuations without explicit user merge/resume/inspect input must
  not query GitHub again, repeat gate reports, print repeated pause notes, mark
  the goal complete, or mark the goal blocked merely because the same external
  PR remains pending.
- If the interface forces a response while paused, use only:
  `Waiting for PR #X to merge; no checks run.`

Rationale:

- A pending PR review or merge is external state, not work Codex can advance by
  rechecking the same gate.
- Completion would be false because the staged goal still depends on the merge.
- Blocked status is also too strong when the workflow is intentionally waiting
  for human review or GitHub merge completion.

Consequences:

- Conservative auto-merge remains unchanged: direct merge is forbidden, `--admin`
  is forbidden, and medium/high/unclear-risk PRs still stop for human review.
- Future staged continuations resume only after the user says the PR merged,
  asks to resume after merge, or asks to inspect the PR.

---

## 2026-06-12 - Plan Local Fixture Robustness Before Refreshing Outputs

Context:

- PR #109 merged the post-synthetic robustness generated-output checkpoint.
- That checkpoint routed the next safe stage to a documentation-only local
  fixture robustness/report refresh plan.
- The local CSV fixture workflow already has split metadata, caveats,
  synthetic-only inventory review, liquidity diagnostics, factor diagnostics,
  and diagnostic-only volume-aware slippage smoke output.

Decision:

- Add `docs/local_fixture_robustness_report_refresh_plan.md` before changing
  fixture workflow behavior or generated artifacts.
- Require future fixture robustness output to preserve all configured cases,
  every configured split, invalid or insufficient rows, deterministic ordering,
  cost/slippage assumptions, diagnostic-only volume-aware fields, and
  guardrail caveats.
- Keep generated-output refresh as a later, separately reviewed stage unless a
  future reviewed implementation scope explicitly includes it.

Rationale:

- The reviewed synthetic all-case format should be mapped onto committed local
  fixtures before another output refresh.
- Planning first reduces the risk of cherry-picked fixture diagnostics,
  hidden invalid cases, or wording that implies real-data evidence.

Consequences:

- The next implementation PR should be test-first and should prove all-case,
  all-split, invalid-row, and guardrail behavior before writing refreshed
  reports or logs.
- Real-data interpretation remains blocked until user-provided data scope,
  provenance, readiness audit, benchmark, and experiment-handoff gates are
  available.

Follow-up:

- After this plan PR merges, add focused local fixture robustness/report
  support tests and implementation without fetching data or changing
  backtester behavior.

---

## 2026-06-12 - Add Checkpoint After Synthetic Robustness Generated Outputs

Context:

- PR #108 merged the deterministic synthetic split-aware robustness Markdown
  report, JSON experiment log, and refreshed experiment registry.
- The current handoff routes the next safe stage to a documentation or
  research-process checkpoint before any real-data interpretation.
- The older roadmap already recommends applying the reviewed robustness format
  to local fixtures only after the synthetic implementation path is complete.

Decision:

- Add `docs/post_synthetic_robustness_generated_output_checkpoint.md` as a
  documentation-only checkpoint.
- Record the completed PR #104-#108 sequence, generated-output state,
  guardrails, remaining gaps, and recommended next roadmap.
- Route the next stage toward a documentation-only local fixture
  robustness/report refresh plan before changing fixture workflows or
  generated artifacts.

Rationale:

- A checkpoint makes the post-#108 state explicit before starting another
  workflow or generated-output branch.
- The local fixture path needs a mapped plan so the all-case split summary,
  invalid rows, cost/slippage assumptions, and caveats remain visible without
  implying user-data validation.

Consequences:

- Future work should not jump directly from synthetic generated outputs to
  real-data interpretation.
- The next PR-sized stage can remain documentation-only and define fixture
  refresh requirements before any source, test, research-script, or generated
  artifact change.

Follow-up:

- After this checkpoint PR merges, create the local fixture robustness/report
  refresh plan unless current evidence or user scope changes.

---

## 2026-06-12 - Commit Synthetic Robustness Generated Outputs After Support Path

Context:

- PR #105 added the deterministic synthetic split-aware robustness demo without
  committed generated outputs.
- PR #106 added explicit report/log support with default no-output module
  execution.
- The current handoff routes the next safe stage to a scoped generated-output
  refresh if caveats, all-case fields, and invalid-case fields are verified.

Decision:

- Commit the default Markdown report and JSON experiment log for the synthetic
  robustness demo.
- Refresh the experiment registry so the new JSON log is discoverable beside
  the other synthetic demo logs.
- Keep the refresh generated-output-only and do not change implementation code
  or tests in this PR.

Rationale:

- The generated artifacts are useful review and handoff evidence only after
  the output-writing path is tested and merged.
- Committing the all-case and invalid-case output makes caveats and failure
  modes visible rather than preserving only favorable diagnostics.

Consequences:

- Reviewers can inspect the generated Markdown/JSON artifacts directly.
- These outputs remain deterministic synthetic diagnostics, not real-market
  evidence, not strategy validation, and not a profitability claim.

Follow-up:

- After this generated-output PR merges, choose the next stage from current
  evidence and avoid real-data interpretation until readiness/provenance gates
  are satisfied.

---

## 2026-06-12 - Pause After One Not-Merged PR Gate Check

Context:

- Repeated automatic continuations can keep rechecking the same previous-stage
  PR when that PR is still not merged.
- The staged workflow already requires a merge gate before starting a new
  stage and forbids Codex from merging PRs without explicit instruction.

Decision:

- Treat open, closed-unmerged, unknown, or otherwise not-verified-merged PR
  state as an immediate pause gate after one current-state status check.
- Do not repeatedly poll PR checks, reviews, branch protection, auto-merge
  eligibility, or baseline validation while that gate remains unmerged.
- Continue to sync `main` and run baseline validation only after the previous
  PR is verified merged.

Rationale:

- One authoritative status check is enough to prove the workflow cannot safely
  start the next stage.
- Repeated rechecks add noise and token cost without changing the external
  merge state.

Consequences:

- Future continuations should report the not-merged gate and pause directly.
- Explicit user requests can still inspect or update a PR, but automatic
  staged continuation should not keep reclassifying the same unmerged gate.

Follow-up:

- If a future continuation still repeats the same not-merged gate, tighten the
  controller or Skill wording further.

---

## 2026-06-12 - Add Report/Log Support Before Generated Output Refresh

Context:

- PR #105 added a deterministic synthetic split-aware robustness demo and
  focused tests, but intentionally left generated reports/logs unchanged.
- The next handoff allowed either explicit caveated report/log support or a
  generated-output refresh if deliberately scoped.

Decision:

- Add opt-in report/log support before refreshing any committed generated
  artifacts.
- Keep default module execution no-output so validation can prove support code
  exists without mutating `reports/`.
- Require the report/log path to preserve all-case diagnostics, invalid-case
  diagnostics, caveats, and separately inspectable cost/slippage assumptions.

Rationale:

- Separating output support from generated artifact refresh keeps review
  smaller and makes report/log schema and caveats testable before committing
  generated files.
- The generated-output refresh should only occur after this support path is
  reviewed.

Consequences:

- Future generated-output PRs should call the explicit output-writing path and
  review the Markdown/JSON diffs for caveats, all-case rows, invalid-case rows,
  and assumption fields.
- Real-data interpretation remains blocked by readiness, provenance,
  survivorship, benchmark/universe, and experiment-handoff gates.

Follow-up:

- After this support PR merges, consider a generated-output refresh for
  `reports/synthetic_split_robustness_demo.md`,
  `reports/experiment_logs/synthetic_split_robustness_demo.json`, and the
  experiment registry.

---

## 2026-06-12 - Implement Synthetic Robustness Demo Without Generated Outputs

Context:

- PR #104 added the plan for synthetic robustness and split-aware validation.
- The plan requires all configured cases and all configured splits to remain
  visible before any generated-output refresh.
- Generated reports and experiment logs are review-sensitive because they can
  be mistaken for stronger evidence than synthetic diagnostics support.

Decision:

- Add the first synthetic split-aware robustness implementation as a research
  helper plus focused tests only.
- Include default identity, inverse, and constant invalid signal cases so the
  all-case table includes favorable, unfavorable, and invalid diagnostics.
- Preserve missing observations across synthetic transforms and record invalid
  reasons instead of silently filling or dropping cases.
- Do not write generated reports or experiment logs in this implementation PR.

Rationale:

- Keeping implementation separate from generated-output refresh makes the PR
  small and keeps review focused on deterministic behavior and guardrails.
- The constant invalid case exercises the insufficient/undefined diagnostic
  path required by the plan without requiring real data or external inputs.

Consequences:

- Future report/log support should reuse the all-case summary rather than
  recomputing or filtering cases.
- Any generated-output PR should explicitly scope output files and verify the
  caveats, all-case table, invalid-case table, and assumption fields.

Follow-up:

- After this PR merges, consider adding caveated report/log support or a
  generated-output refresh for this synthetic robustness demo.

---

## 2026-06-12 - Plan Synthetic Robustness Before Implementation

Context:

- PR #103 refreshed the roadmap and identified robustness and split-aware
  validation policy as the next original-goal gap.
- The repository already has split helpers, synthetic diagnostics, local
  fixture workflows, fixed-bps cost/slippage accounting, and a volume-aware
  diagnostic/precomputed-impact boundary.
- No user-provided local CSV bundle or real-data readiness handoff is
  available.

Decision:

- Add `docs/synthetic_robustness_validation_plan.md` before implementing any
  new robustness summary.
- Require future implementations to report every configured parameter case
  across every configured split, including invalid or insufficient cases.
- Keep transaction costs, fixed-bps slippage, and volume-aware diagnostics or
  precomputed impacts separately inspectable in future logs and reports.

Rationale:

- A plan-first stage reduces the risk of cherry-picking, accidental
  performance framing, or hidden missing-data behavior in future synthetic
  reports.
- Chronological split policy, all-case reporting, and guardrail caveats should
  be reviewed before changing research scripts or generated outputs.

Consequences:

- The next implementation stage should add deterministic tests before or with
  any synthetic robustness code.
- Generated reports/logs should remain unchanged until an explicit
  generated-output stage or implementation PR scopes them.
- Real-data interpretation remains blocked by readiness, provenance,
  survivorship, benchmark/universe, and experiment-handoff gates.

Follow-up:

- After this plan merges, consider a synthetic split-aware robustness
  implementation PR with deterministic tests and no real-data access.

---

## 2026-06-12 - Refresh Roadmap After Volume-Aware Slippage Sequence

Context:

- PR #102 checkpointed the completed volume-aware slippage design, test-plan,
  precomputed-impact implementation, and generated-log refresh sequence.
- `docs/current_roadmap_gap_refresh.md` was written earlier and still
  recommended stages that are now implemented or superseded.
- No user-provided local CSV bundle or real-data readiness handoff is
  available.

Decision:

- Refresh `docs/current_roadmap_gap_refresh.md` from current repository
  evidence.
- Keep the next recommended stage documentation-only:
  `docs/synthetic_robustness_validation_plan.md`.
- Do not proceed directly to new source code, generated-output refresh,
  real-data interpretation, LEAN runtime work, or execution-related scope.

Rationale:

- The repository now has split helpers, synthetic diagnostics, local fixture
  demos, backtest accounting, fixed-bps cost/slippage, and a precomputed
  volume-aware slippage boundary.
- The next original-goal gap is robustness and split-aware validation policy:
  all-case reporting, split windows, benchmark assumptions, cost/slippage
  assumptions, and no-best-only filtering.
- A documentation plan is lower risk than implementation and keeps the next
  code or generated-output stage reviewable.

Consequences:

- Future continuations should route through the updated roadmap and handoff.
- User-provided local CSV interpretation remains blocked by readiness-audit,
  provenance, alignment, benchmark/universe, and experiment-handoff gates.
- GitHub auto-merge may be considered only for clearly low-risk PRs with
  verifiable protections; otherwise stop for human review.

Follow-up:

- After this roadmap refresh PR merges, add a documentation-only synthetic
  robustness and split-aware validation plan.

---

## 2026-06-11 - Checkpoint Completed Precomputed Volume-Aware Slippage Sequence

Context:

- PR #98 added the documentation-only integration design.
- PR #99 added the documentation-only integration test plan.
- PR #100 added the precomputed-impact backtester path with
  `diagnostic_only` as the default.
- PR #101 refreshed affected synthetic JSON experiment logs so full metrics
  payloads include `total_volume_aware_slippage_cost_impact: 0.0` in default
  diagnostic mode.

Decision:

- Add a documentation-only checkpoint for the completed design, test-plan,
  implementation, and generated-log sequence.
- Keep the next stage documentation-only by routing to a post-volume-aware
  roadmap gap refresh before any new code or generated-output stage.
- Preserve the current boundary: no real data, no vendor APIs, no credentials,
  no brokerage, no live or paper trading, no order execution, and no
  profitability claims.

Rationale:

- The volume-aware slippage path now has design, tests, implementation, and
  refreshed synthetic logs, so future stages need a current roadmap rather
  than another integration step by default.
- The older `docs/current_roadmap_gap_refresh.md` predates several completed
  split, liquidity, fixed-bps slippage, volume-aware diagnostic,
  precomputed-impact, and generated-log stages.
- A checkpoint keeps the audit trail explicit before selecting the next
  research-pipeline milestone.

Consequences:

- Future continuations should not treat volume-aware slippage as real-data
  capacity evidence or execution realism.
- User-provided local CSV interpretation remains blocked by readiness-audit,
  provenance, alignment, and experiment-handoff gates.
- The next recommended PR-sized stage is a documentation-only roadmap gap
  refresh.

Follow-up:

- After this checkpoint PR merges, refresh the current roadmap gap document
  from latest repository evidence before choosing additional implementation
  work.

---

## 2026-06-11 - Refresh Synthetic Logs For Default Volume-Aware Metric

Context:

- PR #100 added a precomputed volume-aware slippage boundary to the local
  backtester while keeping `volume_aware_slippage_mode="diagnostic_only"` as
  the default.
- The implementation added a separate
  `total_volume_aware_slippage_cost_impact` metric, with default diagnostic
  value `0.0` when no precomputed impact is applied.
- The current handoff recommended a synthetic generated-output review or
  refresh after PR #100 merged.

Decision:

- Refresh only committed synthetic experiment logs that serialize the full
  backtester metrics payload and therefore need the new default metric field.
- Keep unchanged generated artifacts unchanged when reruns produce no diff.
- Do not modify source code, tests, research scripts, backtester behavior,
  metrics logic, data loaders, diagnostics helper behavior, generated Markdown
  reports, the experiment registry, real-data workflows, or LEAN/runtime code
  in this generated-output PR.

Rationale:

- The committed logs should match the current deterministic synthetic
  backtester schema so downstream registry, report, and audit readers do not
  see stale metric payloads.
- A separate generated-output PR keeps schema refresh diffs from obscuring the
  PR #100 implementation review.
- A `0.0` volume-aware slippage metric in default diagnostic mode is an audit
  field, not a claim about execution realism, real-data capacity, or
  profitability.

Consequences:

- `reports/experiment_logs/synthetic_momentum_demo.json` and
  `reports/experiment_logs/synthetic_combined_score_backtest_demo.json` carry
  the new default metric.
- The synthetic parameter sweep, Markdown reports, and experiment registry do
  not change in this stage because reruns produced no committed diffs there.
- User-provided local CSV interpretation remains blocked by readiness-audit,
  provenance, alignment, and experiment-handoff gates.

Follow-up:

- After this generated-log refresh PR merges, run a documentation-only
  checkpoint for the completed precomputed volume-aware slippage implementation
  plus generated-log refresh sequence before any new code, real-data, or
  LEAN/runtime stage.

---

## 2026-06-11 - Add Precomputed Volume-Aware Slippage Backtester Boundary

Context:

- PR #99 added the documentation-only test plan for volume-aware slippage
  backtester integration.
- The reviewed design and test plan both recommend keeping helper calculation
  outside the backtester and using a precomputed impact boundary for the first
  implementation.

Decision:

- Add a narrow `apply_precomputed_impact` path to `run_long_only_backtest()`.
- Keep `volume_aware_slippage_mode="diagnostic_only"` as the default.
- Add a separate `volume_aware_slippage_costs` result series, separate metrics,
  and explicit assumption fields for applied volume-aware slippage metadata.
- Reject positive fixed-bps slippage plus positive applied volume-aware impact
  by default to avoid hidden double counting.
- Do not make the backtester compute rolling dollar volume, read OHLCV panels,
  fetch data, use vendor APIs, connect to brokers, or place orders.

Rationale:

- A precomputed series keeps date alignment, notional scale, volume policy,
  missing/zero/stale liquidity policy, and participation-cap handling in the
  diagnostic helper boundary.
- Separate result and metric fields keep fixed transaction costs, fixed-bps
  slippage, volume-aware candidate slippage, and total trading impact
  inspectable.
- The default diagnostic mode preserves existing behavior unless callers
  explicitly opt into applied precomputed impact with required metadata.

Consequences:

- Future generated reports and experiment logs may need a separate refresh or
  review stage so new metrics and audit fields are visible and caveated.
- User-provided local CSV interpretation remains blocked by readiness-audit,
  provenance, alignment, and experiment-handoff gates.

Follow-up:

- After this implementation PR merges, review and refresh affected synthetic
  generated outputs in a separate PR if the diff confirms new default fields.

---

## 2026-06-11 - Require Tests Before Volume-Aware Slippage Backtester Implementation

Context:

- PR #98 added the documentation-only backtester integration design for
  volume-aware slippage.
- The design recommends keeping `diagnostic_only` as default and using a
  precomputed-impact boundary if volume-aware slippage is later applied to
  simulated returns.
- No source code, tests, research scripts, generated reports, backtester
  behavior, metrics behavior, or diagnostics behavior changed in this stage.

Decision:

- Add `docs/volume_aware_slippage_backtester_integration_test_plan.md` as the
  acceptance checklist before any implementation.
- Require deterministic unit, integration, failure-mode, guardrail, result
  field, audit field, report-field, and experiment-log tests before or with any
  future code-changing integration PR.
- Keep generated reports unchanged until after a future implementation is
  reviewed and merged.

Rationale:

- Applying volume-aware slippage to net returns is an accounting change, not a
  documentation detail.
- Tests must prove date alignment, separate cost/slippage inspection, zero
  diagnostic behavior, invalid-liquidity failures, and no double counting
  before behavior changes.
- A test plan keeps the next implementation PR smaller and less ambiguous.

Consequences:

- The next possible implementation must keep helper calculation outside the
  backtester, keep `diagnostic_only` as default, and add deterministic tests in
  the same PR.
- Implementation must stop for missing, zero, stale, or incomplete volume
  ambiguity; invalid notional; excessive participation; ambiguous fixed-bps
  plus volume-aware slippage semantics; real-data needs; vendor APIs;
  credentials; brokerage; live or paper trading; order execution; or
  profitability language.

Follow-up:

- After this test-plan PR merges, consider a narrow code-changing
  precomputed-impact implementation PR with deterministic tests and no
  generated-output refresh.

---

## 2026-06-11 - Define Volume-Aware Slippage Backtester Integration Boundary

Context:

- PR #97 merged the post local fixture slippage output refresh checkpoint.
- The repository has a standalone volume-aware slippage diagnostic helper and
  synthetic/local-fixture outputs that report participation and rejected/cap
  counts.
- Candidate volume-aware slippage is still not applied to simulated backtester
  net returns.

Decision:

- Add `docs/volume_aware_slippage_backtester_integration_design.md` as the
  reviewed boundary before any future net-return integration.
- Keep volume-aware slippage diagnostic-only by default.
- If implemented later, prefer a precomputed-impact boundary: compute the
  diagnostic outside the backtester, pass an aligned
  `portfolio_slippage_impact` series plus audit metadata into the backtester or
  wrapper, and deduct it from net returns only under an explicit opt-in.
- Defer internal backtester calculation from price and volume panels until a
  separate design justifies making the backtester own OHLCV semantics.

Rationale:

- Applying volume-aware slippage to returns would change cost accounting and
  report interpretation.
- A precomputed-impact boundary keeps volume validation, notional scale, lagged
  dollar-volume construction, stale-volume handling, and participation caps
  auditable before net-return behavior changes.
- Fixed-bps slippage and volume-aware candidate slippage can be double-counted
  unless a reviewed rule blocks or explicitly permits combination.

Consequences:

- Source code, tests, research scripts, generated reports, loaders, backtester
  behavior, metrics behavior, diagnostics behavior, LEAN code, and real-data
  access remain unchanged in this stage.
- Any future implementation must define strict defaults and stop conditions for
  missing volume, zero volume, stale volume, invalid notional, and excessive
  participation before touching returns.
- Reports and experiment logs must distinguish transaction costs, fixed-bps
  slippage, volume-aware candidate slippage, total trading impact, diagnostic
  flags, and caveats.

Follow-up:

- After this design merges, the next safe stage is a documentation-only
  backtester integration test plan, not implementation.
- Stop if a later stage needs real data, downloads, vendor APIs, credentials,
  brokerage, live or paper trading, order execution, silent missing-data repair,
  or profitability claims.

---

## 2026-06-11 - Require Design Before Volume-Aware Slippage Net-Return Integration

Context:

- PR #90 added the volume-aware slippage design boundary.
- PR #91 added the standalone synthetic-only diagnostic helper.
- PR #92 added a committed synthetic local CSV fixture smoke diagnostic.
- PR #93 checkpointed the smoke diagnostic before generated-output refresh.
- PR #94 refreshed the committed synthetic local CSV fixture report, JSON
  experiment log, and experiment registry with the diagnostic outputs.
- None of those stages applied candidate volume-aware slippage to simulated
  portfolio returns.

Decision:

- Treat the volume-aware slippage design/helper/smoke/output-refresh sequence
  as complete at the diagnostic artifact level.
- Require a separate documentation-only integration design before any future
  stage changes `run_long_only_backtest()`, metrics, reports, or generated
  logs so volume-aware slippage affects simulated net returns.

Rationale:

- Net-return accounting needs explicit semantics for gross returns, fixed
  transaction costs, fixed-bps slippage, candidate volume-aware slippage,
  rejected/capped trades, zero-slippage diagnostics, and caveats.
- A design gate is lower risk than implementation and keeps the next PR
  reviewable.
- Synthetic/local fixture diagnostics are useful for plumbing and audit
  visibility, but they are not real-data evidence or profitability support.

Consequences:

- The next safe stage after the checkpoint can be a documentation-only
  volume-aware slippage backtester integration design.
- Source code, tests, research scripts, generated reports, and backtester
  behavior should remain unchanged until that design is reviewed.
- User-provided local CSV interpretation remains blocked by readiness-audit,
  provenance, schema, alignment, and experiment-handoff gates.

Follow-up:

- Draft `docs/volume_aware_slippage_backtester_integration_design.md` in a
  later PR after the checkpoint merges.
- Stop if the design would require real data, downloads, vendor APIs,
  credentials, live or paper trading, brokerage integration, order execution,
  silent missing-data repair, or profitability claims.

---

## 2026-06-09 - Refresh Local Fixture Outputs Before Backtester Slippage Integration

Context:

- PR #90 added the volume-aware slippage design boundary.
- PR #91 added the standalone synthetic-only diagnostic helper.
- PR #92 added a committed synthetic local CSV fixture smoke diagnostic that
  calls the helper and reports participation plus rejected/cap counts only.
- PR #92 intentionally did not refresh committed generated reports/logs and
  did not integrate volume-aware slippage into backtester net returns.

Decision:

- Treat the volume-aware design, helper, and local fixture smoke diagnostic
  sequence as complete at the code/test level.
- Before considering any backtester net-return integration, refresh the
  committed synthetic local CSV fixture generated report/log/registry in a
  separate narrow stage if the checkpoint is reviewed and merged.
- Keep any generated-output refresh synthetic-only and caveated. It may record
  participation and rejected/cap counts, but it must not treat candidate
  slippage diagnostics as real-data evidence, execution realism, or
  profitability support.

Rationale:

- The repository should not carry stale generated artifacts after a workflow
  report/log writer changes.
- Generated-output refresh is lower risk than backtester integration because
  it does not change source behavior or net returns.
- Separating artifact refresh from code changes keeps PR scope reviewable and
  prevents generated report diffs from hiding implementation changes.

Consequences:

- The next safe stage after the checkpoint can be a local fixture generated
  artifact refresh, not a new alpha, real-data study, or backtester slippage
  integration.
- Volume-aware slippage remains diagnostic-only until a later design stage
  explicitly reviews whether it should affect simulated returns.
- User-provided local CSV interpretation remains blocked by readiness-audit
  and `EXPERIMENT_LOG.md` gates.

Follow-up:

- Refresh `reports/local_csv_fixture_workflow_demo.md`,
  `reports/experiment_logs/local_csv_fixture_workflow_demo.json`, and
  `reports/experiment_registry.md` in a separate stage after this checkpoint
  merges.
- Stop if the refresh would require real data, downloads, vendor APIs,
  credentials, live or paper trading, brokerage integration, order execution,
  backtester behavior changes, or profitability claims.

---

## 2026-06-09 - Keep Volume-Aware Slippage Helper Diagnostic-Only

Context:

- PR #90 added `docs/volume_aware_slippage_design.md`.
- That design recommends a synthetic-only helper or diagnostic stage before
  any backtester net-return integration.
- The current backtester already has fixed-bps slippage, so adding a
  volume-aware path directly to `run_long_only_backtest()` would change
  strategy accounting before the new data and capacity semantics are
  independently tested.

Decision:

- Add a standalone diagnostic helper under `src/backtest/slippage.py`.
- Do not integrate the helper with `run_long_only_backtest()`,
  `calculate_basic_metrics()`, research scripts, generated reports, or local
  CSV workflows in this stage.
- Default to strict behavior: missing lagged capacity, zero or incomplete
  volume windows, zero lagged dollar volume, missing inputs, invalid notional,
  and participation above cap raise instead of being filled, clipped, or
  ignored.

Rationale:

- A standalone helper keeps the PR reviewable and makes the volume-aware
  assumptions testable before they affect simulated returns.
- Explicit `portfolio_notional` prevents normalized backtest capital from
  being mistaken for real tradable capital.
- Strict missing and zero-liquidity behavior preserves the project rule
  against silent missing-data repair.

Consequences:

- Future work can inspect participation and candidate slippage impact on
  deterministic synthetic panels without changing existing backtest output.
- Backtester integration remains a separate reviewed decision after helper
  behavior and caveats are accepted.
- User-provided local CSV interpretation remains blocked by readiness-audit
  and `EXPERIMENT_LOG.md` gates.

Follow-up:

- After this helper is reviewed and merged, consider a synthetic/local-fixture
  smoke diagnostic that reports participation and rejected/capped counts only.
- Stop if the next stage would require real data, downloads, vendor APIs,
  credentials, live or paper trading, brokerage integration, order execution,
  silent fill/clip policies, generated performance interpretation, or
  profitability claims.

---

## 2026-06-09 - Define Volume-Aware Slippage Design Boundary

Context:

- PR #85 designed fixed-bps transaction cost and slippage assumptions.
- PR #86 implemented fixed-bps slippage in the local backtester.
- PR #87 refreshed synthetic reports and logs for fixed-bps slippage fields.
- PR #88 recorded that the fixed-bps slippage path is complete and that
  volume-aware slippage requires a design gate before implementation.
- PR #89 added token-efficient workflow controls, so the current stage can use
  the handoff and repo map instead of broad repo scans.

Decision:

- Add `docs/volume_aware_slippage_design.md` as a documentation-only boundary
  before any volume-aware slippage helper, backtester integration,
  generated-output update, or local CSV interpretation.
- Treat lagged rolling dollar volume, explicit portfolio notional,
  missing/zero-volume handling, participation caps, and adjustment-policy
  compatibility as required design inputs for any future code.
- Keep same-day volume, silent missing-data repair, silent cap clipping, real
  data fetching, broker/order behavior, and execution-realism claims out of
  scope.

Rationale:

- Volume-aware slippage has higher look-ahead and interpretation risk than
  fixed-bps target-weight turnover friction.
- Current backtests are normalized research accounting; dollar-volume
  capacity requires an explicit notional scale before participation can be
  calculated.
- Zero volume, missing volume, stale volume, and incompatible price/volume
  adjustment policies can make a volume-aware estimate invalid even when the
  CSV loader accepts the rows.

Consequences:

- The next possible code stage should be a synthetic-only helper or diagnostic
  stage, not immediate backtester net-return integration.
- Any future implementation must default to strict missing/zero-liquidity and
  participation-cap behavior, with no silent fills or silent clipping.
- User-provided local CSV interpretation remains blocked until readiness audit
  and `EXPERIMENT_LOG.md` gates are complete for a specific dataset.

Follow-up:

- After this design is reviewed and merged, consider a narrow synthetic-only
  participation/slippage diagnostic helper with deterministic tests.
- Stop if implementation would require real data, downloads, vendor APIs,
  credentials, live or paper trading, brokerage integration, order execution,
  silent missing-data repair, or profitability claims.

---

## 2026-06-09 - Require Volume-Aware Slippage Design Before Implementation

Context:

- PR #85 added the simulated slippage and cost assumption design.
- PR #86 implemented the narrow fixed-bps local backtester slippage extension.
- PR #87 refreshed synthetic backtest reports, JSON logs, registry output, and
  current slippage planning docs.
- The fixed-bps path is now represented in design, code, deterministic tests,
  and synthetic generated outputs.
- Volume-aware slippage and market impact remain deferred.

Decision:

- Treat the fixed-bps slippage sequence as complete for the current synthetic
  research pipeline.
- Do not proceed directly to a volume-aware slippage helper or backtester
  extension.
- Require a documentation-only volume-aware slippage design before any
  volume-based cost/slippage implementation, generated-output update, or
  local CSV interpretation.

Rationale:

- Volume-aware slippage has higher leakage and interpretation risk than fixed
  basis-point turnover friction.
- A future model would need explicit policy for adjusted versus raw volume,
  dollar-volume alignment, lag rules, zero volume, missing volume, stale data,
  participation assumptions, liquidity caps, and benchmark/universe mismatch.
- Synthetic/local fixtures can test wiring and edge cases, but they cannot
  prove realistic execution or market impact.

Consequences:

- The next safe repository-internal stage can be a design gate for
  volume-aware slippage.
- Any future implementation must remain synthetic/local-fixture only until
  user-provided local CSV readiness gates are completed for a specific dataset.
- User-provided local CSV interpretation remains blocked by the readiness
  audit and `EXPERIMENT_LOG.md` requirements.
- No source code, tests, research scripts, reports, data access, execution
  behavior, credentials, or performance claims are changed by this decision.

Follow-up:

- Add a documentation-only volume-aware slippage design if no higher-priority
  merge gate, blocker, or stale roadmap issue appears.
- Stop before implementation if the next stage would require real data,
  downloads, vendor APIs, credentials, live or paper trading, brokerage
  integration, order execution, or profitability claims.

---

## 2026-06-09 - Require Slippage And Cost Design Before Implementation

Context:

- PR #84 merged the post-local-CSV-fixture audit rehearsal checkpoint.
- That checkpoint recommends simulated slippage and cost assumption design as
  the next repository-internal stage.
- The local backtester currently applies `transaction_cost_bps` to
  target-weight turnover, but it does not separately represent slippage or
  market impact.
- The project specification requires transaction costs, slippage, turnover,
  and execution assumptions to be explicit.

Decision:

- Add a documentation-only design before any local backtester cost/slippage
  implementation changes.
- Treat the first future implementation, if approved later, as a narrow fixed
  basis-point slippage extension on the current target-weight turnover model.
- Defer volume-aware slippage and market impact until separate policy, data,
  lag, and testing requirements are reviewed.

Rationale:

- Cost and slippage assumptions can materially affect simulated results.
- A design gate prevents a small-looking parameter addition from becoming an
  implicit execution model.
- Fixed-basis-point turnover friction is deterministic and testable, but it
  must remain caveated as simulated research accounting rather than realistic
  execution evidence.

Consequences:

- Backtester source code remains unchanged by this decision.
- Future code must keep transaction cost and slippage assumptions visible in
  outputs and logs.
- Zero-cost or no-slippage runs remain diagnostics only.
- User-provided local CSV interpretation remains blocked by the readiness
  audit and experiment-log gates.

Follow-up:

- After the design is reviewed and merged, consider a narrow synthetic-only
  implementation PR with deterministic tests for separate fixed-bps slippage.
- Stop before implementation if the next stage would require real data,
  broker fills, order execution, credential access, or performance
  interpretation.

---

## 2026-06-08 - Pause User-Provided Local CSV Work At The Readiness Gate

Context:

- PR #83 merged the committed synthetic local CSV fixture readiness audit
  rehearsal.
- The repository now has the future local CSV study plan, checklist, inventory
  validator, audit report template, and synthetic fixture rehearsal artifacts.
- No user-provided local CSV bundle, completed scope statement, completed
  checklist, completed inventory review, completed readiness audit report, or
  prepared user-data `EXPERIMENT_LOG.md` entry is available.
- Starting a user-data smoke run would require external files and human review
  decisions that are not present in the repository context.

Decision:

- Do not proceed to a user-provided local CSV smoke run by default.
- Treat local CSV user-data interpretation as blocked until the required
  bundle, checklist, inventory, readiness audit, and experiment-log gates are
  complete.
- Route the next repository-internal stage toward simulated slippage and cost
  assumption design before any cost/slippage implementation changes.

Rationale:

- The local CSV readiness artifacts are preparation gates, not evidence that a
  specific user dataset is safe to interpret.
- The original project specification requires explicit transaction costs,
  slippage, turnover, and execution assumptions.
- The current backtester has fixed basis-point transaction costs but no
  separate slippage or market-impact model; a design gate keeps that boundary
  reviewable before source code changes.

Consequences:

- Local CSV work remains synthetic, local-fixture only, or documentation-only
  until user data and completed audit artifacts are available.
- The next stage should not fetch data, add vendor APIs, add credentials, add
  live or paper trading, add brokerage/order logic, or claim profitability.
- Backtester source code remains unchanged by this decision.

Follow-up:

- Add a documentation-only simulated slippage and cost assumption design stage.
- Stop before implementation if the design would require real market data,
  broker fills, order execution, or performance interpretation.

---

## 2026-06-07 - Require Universe-Mask Backtest Integration Design Before Code

Context:

- The synthetic liquidity universe helper has merged.
- The local CSV fixture workflow now reports universe-mask counts on committed
  synthetic fixtures only.
- `run_long_only_backtest()` currently consumes prices and signals, not
  universe masks.
- Feeding a universe mask directly into a backtest without a reviewed contract
  could blur universe dates, signal dates, rebalance dates, return measurement
  dates, low-coverage handling, benchmark assumptions, and performance
  interpretation.

Decision:

- Add a documentation-only liquidity universe backtest-integration design
  before any source code consumes a liquidity universe mask in the backtester.
- Treat the likely first implementation as a narrow signal-masking adapter,
  not a broad backtester rewrite.
- Require strict signal/mask alignment, explicit timing, visible low-coverage
  and empty-rebalance summaries, and caveated synthetic-only interpretation.

Rationale:

- The project already has the lower-level universe-mask primitive.
- The next correctness risk is not mask construction; it is unsafe consumption
  of the mask in simulated portfolio research.
- A design gate keeps universe construction, signal masking, portfolio
  selection, costs, slippage, benchmark comparison, and execution timing
  reviewable as separate concerns.

Consequences:

- Backtester source code remains unchanged in this stage.
- Future code should mask signals before ranking and should not silently
  repair missing universe or signal values.
- Future synthetic backtests that consume a universe mask must record universe
  parameters, coverage, low-coverage dates, timing assumptions, and caveats.
- Real user-provided local CSV interpretation remains blocked by the
  real-data readiness audit and experiment-log requirements.

Follow-up:

- After the design is reviewed and merged, the next narrow code stage can add
  a deterministic synthetic `apply_universe_mask_to_signals()` adapter and
  tests, without running a backtest if keeping the PR narrower is safer.

---

## 2026-06-07 - Keep Liquidity Universe Construction Separate From Backtesting

Context:

- The repository has synthetic-only rolling ADV and rolling dollar-volume
  eligibility helpers.
- The committed synthetic local CSV fixture workflow reports liquidity
  eligibility counts.
- No reviewed helper yet defines a final universe mask, an audit summary, or
  how such a mask should interact with factor scores, rebalance schedules,
  costs, slippage, benchmarks, or execution assumptions.
- The active workflow still prohibits real data fetching, downloads,
  credentials, live trading, paper trading, brokerage integration, order
  execution, and profitability claims.

Decision:

- Treat liquidity eligibility, final universe mask construction, and backtest
  consumption as separate stages.
- Add a documentation-only universe construction design before any code uses
  liquidity eligibility as a final research universe mask.
- Do not wire liquidity eligibility directly into the backtester until a later
  reviewed stage defines the universe mask API, audit summary, signal timing,
  rebalance timing, execution assumptions, costs, slippage, and benchmark
  interaction.

Rationale:

- Liquidity filters are a major survivorship-bias and look-ahead-bias risk if
  they are connected directly to portfolio construction without a reviewed
  timing boundary.
- A universe mask needs its own audit summary so low coverage, missing
  eligibility, capped names, additions, removals, and caveats remain visible.
- Keeping the stages separate preserves progress while preventing a liquidity
  helper from being mistaken for a tradable universe or performance result.

Consequences:

- Future liquidity universe code should be synthetic-only and should return a
  mask plus inspectable summary before any report or backtest integration.
- Backtester integration remains blocked until a separate design defines the
  complete signal/universe/rebalance/execution contract.
- User-provided local CSV universe interpretation remains gated by the
  real-data readiness audit and experiment-log requirements.

Follow-up:

- Implement a small synthetic-only universe-mask helper and deterministic tests
  only after `docs/liquidity_universe_construction_design.md` is reviewed and
  merged.

---

## 2026-06-04 - Keep First LEAN-Adjacent Code Signal-Only

Context:

- PR #42 merged the LEAN runnable draft readiness decision.
- That decision found the repository is not ready for runnable LEAN code under
  the current guardrails.
- The active workflow still prohibits real market data fetching, downloads,
  credentials, live trading, paper trading, brokerage integration, order
  execution, and profitability claims.

Decision:

- Define the next LEAN-adjacent code boundary as signal-only and
  metadata-only.
- Do not allow the next code stage to import `AlgorithmImports`, subclass
  `QCAlgorithm`, create `config.json`, run LEAN, subscribe to platform data,
  call history APIs, create portfolio targets, place orders, model fills,
  configure brokerage, or produce backtest results.
- If this design is reviewed and merged, the next possible code PR should be a
  pure-Python `lean/signal_only_momentum_draft.py` plus static scope tests.

Rationale:

- A signal-only draft can make the factor translation boundary auditable
  without introducing runtime dependencies, account access, data-source
  semantics, order semantics, or performance interpretation.
- Keeping the first code step metadata-only preserves forward progress while
  maintaining the existing simulated-research guardrails.

Consequences:

- Runnable LEAN code remains intentionally blocked.
- The future signal-only draft must avoid order dates, target weights,
  brokerage models, fill models, live mode, paper mode, and implemented
  portfolio behavior.
- Static tests should continue to reject data downloads, credential reads,
  runtime LEAN imports, order calls, and profitability or trading-readiness
  claims.

Follow-up:

- After this design is reviewed and merged, create a small code PR for a
  pure-Python LEAN signal-only momentum draft with static guardrail tests, or
  stop if the implementation cannot satisfy the documented boundary.

---

## 2026-06-04 - Defer Runnable LEAN Draft Until Signal-Only Boundary Is Designed

Context:

- PR #41 merged the LEAN scaffold review checklist.
- The repository now has a metadata-only LEAN scaffold and static tests that
  intentionally reject runtime LEAN imports, credential/data imports,
  brokerage calls, and order calls in the scaffold.
- The current workflow guardrails still prohibit real market data fetching,
  downloads, credentials, live trading, paper trading, brokerage integration,
  order execution, and profitability claims.

Decision:

- Do not add a runnable LEAN draft in the next stage.
- Add a readiness decision documenting that runnable LEAN code is not yet
  approved under current guardrails.
- Make the next safe LEAN stage a documentation-only signal-only draft design.

Rationale:

- A normal runnable LEAN algorithm would likely use `AlgorithmImports`,
  `QCAlgorithm`, platform data subscriptions or history, scheduled events,
  portfolio targets, orders, fills, fee models, and slippage models.
- Those pieces may be appropriate in a future simulated LEAN backtest, but they
  need an explicit scope boundary before implementation so they are not
  confused with live trading, brokerage integration, real data fetching, or
  profitability evidence.
- The signal-only design stage can preserve forward progress while keeping the
  implementation bounded and reviewable.

Consequences:

- Future LEAN code remains blocked until the project defines a signal-only
  code boundary and static validation plan.
- The existing non-executing scaffold remains unchanged.
- No source code, tests, research scripts, reports, data access, execution
  behavior, credentials, or performance claims are changed by this decision.

Follow-up:

- Create a documentation-only LEAN signal-only draft design after this decision
  is reviewed and merged.
- If that design cannot avoid runtime, data, credential, order, or
  interpretation risks, stop and document the blocker before code is added.

---

## 2026-06-03 - Refresh WorldQuant Catalog Before More Alpha Work

Context:

- `docs/post_csv_checkpoint_report.md` identified stale wording in
  `docs/worldquant_alpha_catalog.md`.
- The catalog still described the repository as catalog-only even though the
  operator layer and `alpha_009` research feature now exist.
- PR #29 was merged, latest `main` was synced, baseline validation passed, and
  no open pull request gate remained.
- Assumption: refreshing the catalog is the next unblocked safe stage because
  it is documentation-only and directly addresses the latest checkpoint
  recommendation.

Decision:

- Refresh `docs/worldquant_alpha_catalog.md` before implementing another
  formula or expanding data schemas.
- Treat `alpha_009` as implemented research-feature status only, not a full
  strategy, backtest integration, trading recommendation, or profitability
  claim.
- Keep `alpha_012` blocked on volume plus close support and `alpha_101`
  blocked on OHLC support.
- Keep VWAP, market-cap, and industry-neutral categories deferred until the
  required data support and validation rules exist.

Rationale:

- Roadmap documents should not guide future stages from stale pre-`alpha_009`
  assumptions.
- Documentation cleanup is lower risk than starting another formula while the
  data prerequisites and next-stage options are still being clarified.
- The project should continue to avoid bulk WorldQuant 101 implementation.

Consequences:

- Future alpha stages should start from current implementation status rather
  than the original Stage 1 catalog-only milestone.
- Additional formula work should be PR-sized and preceded by explicit formula,
  data, operator, missing-value, and test scope.
- This decision changes documentation only. It does not modify source code,
  data access, strategy logic, backtester behavior, execution assumptions, or
  performance claims.

Follow-up:

- If the next alpha stage is code-changing, run the stricter code PR readiness
  gate: tests plus read-only review with no high or medium issues.
- Consider a future planning stage for volume + close or OHLC schema support
  before `alpha_012` or `alpha_101`.

---

## 2026-06-03 - Bounded Staged Execution Behavior

Context:

- The staged workflow now has a repository-local Skill and long-running
  controller.
- The user clarified that Codex should continue as a bounded staged execution
  agent and should not ask for a new prompt after every small step.
- Assumption: this clarification should be preserved as workflow-control
  documentation and Skill guidance, not treated as a source-code or product
  behavior change.

Decision:

- Add an explicit low-risk ambiguity policy to
  `docs/codex_long_running_controller.md`.
- Expand controller stop conditions to cover dirty working trees before new
  stages, destructive or broad architecture ambiguity, missing credentials or
  external access, new production dependencies, unsafe test failures,
  high/medium review issues, security/privacy/data-loss/irreversible risks,
  scope conflicts, and PR-ready human review gates.
- Update `.agents/skills/staged-quant-workflow/SKILL.md` so future sessions
  continue through low-risk ambiguity with logged assumptions and treat missing
  expected files as workflow scaffolding only when that is low-risk.

Rationale:

- The project needs forward motion without turning every minor ambiguity into a
  user prompt.
- The same behavior must remain bounded by safety, scope, review, and merge
  gates.
- Missing workflow files can be repaired safely in small process PRs, while
  missing product-behavior artifacts require a stop report.

Consequences:

- Future Codex sessions should continue through minor documentation/workflow
  ambiguities after recording assumptions.
- Future sessions must still stop for the defined safety, scope, review, and
  human approval conditions.
- This decision changes process guidance only. It does not modify source code,
  data access, trading behavior, strategy logic, or performance claims.

Follow-up:

- Keep each behavior update PR-sized.
- If this policy causes overreach, record the failure in
  `docs/troubleshooting_log.md` and tighten the stop conditions.

---

## 2026-06-03 - Add Long-Running Workflow Control Artifacts

Context:

- The staged workflow Skill exists at
  `.agents/skills/staged-quant-workflow/SKILL.md`.
- The user requested continuation based on `docs/codex_long_running_controller.md`,
  `docs/decision_log.md`, `docs/troubleshooting_log.md`, `CHANGELOG.md`, and
  `scripts/audit-skills.ps1`.
- On latest `main`, those controller, log, changelog, and audit script files
  were missing.

Decision:

- Add a repository-local long-running controller document.
- Add durable decision and troubleshooting logs.
- Add a changelog.
- Add a local PowerShell Skill audit script.
- Update the staged workflow Skill so future continuations read the controller
  and can run the Skill audit.

Rationale:

- The project now depends on a recurring staged workflow, not a one-off prompt.
- Missing controller and log files make future continuation ambiguous.
- A local Skill audit gives future sessions a deterministic check before
  relying on project Skills.

Consequences:

- Future Codex sessions have explicit startup, stop-condition, logging, and PR
  gate guidance.
- Workflow-control changes remain separate from factor research implementation.
- The repository gains process infrastructure but no source-code, data-access,
  strategy, backtest, or performance-claim changes.

Follow-up:

- Keep the controller concise and update it only when a reusable workflow rule
  is verified.
- Use `docs/troubleshooting_log.md` for detailed failure chains.
- Continue normal staged PR review and do not merge PRs without explicit user
  instruction.

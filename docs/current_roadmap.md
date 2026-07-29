# Current Roadmap

Updated: 2026-07-29 for the Stage 4B-R1F trial-allocation release.

Current protected-main base: `814bf02`, the verified merge of Stage 4B-R1E
PR #171. Its exact merge-head CI run `30478870434` succeeded.

This is the canonical roadmap. `docs/research_program_charter.md` defines the
long-term evidence policy. Older checkpoints, gap refreshes, plans, and audits
remain historical evidence and must not be used as active task queues.
`docs/purged_bounded_split_contract.md` is the accepted and implemented Stage 1
split contract.
`docs/signal_execution_timing_contract.md` is the accepted Stage 2 authority
implemented by the Stage 2b runtime, including the owner-selected required
caller-declared source baseline and controlled post-capture mutation ledger.
`docs/point_in_time_data_methodology_contract.md` is the accepted Stage 3
provider-agnostic authority. It distinguishes accepting a methodology contract,
reviewing one immutable dataset manifest, and becoming eligible for formal
interpretation.
`docs/experiment_trial_ledger_contract.md` is the accepted Stage 4a design
authority. It freezes semantic-trial and execution-attempt identity,
allocation-before-action, campaign completeness, protected-access,
canonical-event, checkpoint, and private/public projection semantics.
`docs/experiment_trial_ledger_schema_registry_contract.md` is the accepted
Stage 4B-R0 authority for a fail-closed registry foundation; it is not a
complete 37-event payload registry or ledger runtime.
`docs/experiment_trial_ledger_allocation_registration_schema_contract.md` is
the accepted Stage 4B-R1A architecture-A and Stage 4B-R1B
campaign/experiment allocation authority. The owner selected experiment
namespace option `E1`, `exp_<32 lowercase hex>`. R1B publishes a separate
immutable registry `0.2.0`, promotes only reservation-only
campaign/experiment allocation, and implements no append or storage runtime.
`docs/experiment_trial_ledger_trial_family_registration_schema_contract.md`
is the accepted Stage 4B-R1C authority. The owner selected bundle `R1C-A`,
including the exact `fam_<32 lowercase hex>` namespace, external retrievable
definition/acceptance authority, reviewer independence, anti-reset/currentness
policy, closed relation vocabulary, and common direct-scope maximum 32.
`docs/experiment_trial_ledger_sample_registration_schema_contract.md` is the
accepted Stage 4B-R1D authority. The owner selected bundle `R1D-A`, including the
exact `smp_<32 lowercase hex>` namespace, digest-pinned external Stage 3 sample
authority, separate acceptance and publication-approval records, mutually
exclusive local/global/external paths, anti-reset/currentness policy, private
complete records with allowlisted public projections, and promotion of only
`SAMPLE_REGISTERED` in immutable registry `0.4.0`.
`docs/experiment_trial_ledger_binding_schema_contract.md` is the accepted Stage
4B-R1E authority. The owner selected bundle `R1E-A`, freezing exact
trial-family/global-local-sample/external-origin-sample campaign binding
branches, singleton campaign scope, exact source-event IDs and digests, and a
campaign-scoped external Stage 3 sample-reference event that allocates one
stable `smp_<32 lowercase hex>` identity. Later campaigns reuse that same
external-origin identity only through an exact first-event reference. R1E
publishes immutable registry `0.5.0`, promotes only
`CAMPAIGN_ENTITY_BOUND` and `STAGE3_SAMPLE_REFERENCE_BOUND`, and adds no
stateful ledger runtime.
`docs/experiment_trial_ledger_trial_allocation_schema_contract.md` is the
active Stage 4B-R1F authority. The owner selected bundle `R1F-A`, freezing
exact `trl_<32 lowercase hex>` semantic-trial identity, singleton campaign
scope, exact prior campaign/experiment/family/sample evidence, complete
repository-external canonical definition and separate acceptance/publication/
actor-authority records, closed relation and code-identity unions, and
fail-closed parent/currentness/uniqueness/order rules. R1F publishes immutable
registry `0.6.0`, promotes only `TRIAL_ALLOCATED`, and adds no append,
authority, retrieval, execution, access, research, or trading runtime.

## Objective

Advance from a deterministic simulated factor-research toolkit to a rigorous
historical factor, strategy, and portfolio validation platform. Require
point-in-time data, frozen timing and execution contracts, complete trial
accounting, realistic costs, multiple-testing controls, and independent
reproduction before any later LEAN paper candidacy.

The current phase is research-only. No vendor download, credentials, brokerage,
orders, paper deployment, live deployment, or real-money execution is
authorized.

## Implemented Baseline

| Area | Current implementation evidence |
| --- | --- |
| Data | Strict local wide, long, benchmark, and OHLCV CSV validation; metadata inventory; no downloader. |
| Factors | 12-1 momentum, short-term reversal, realized volatility, liquidity helpers, Alpha #009/#012, normalization, combination, and reusable panel operators. |
| Diagnostics | Correlation, IC, Rank IC, top-minus-bottom quantile spread, coverage, and explicit purged/bounded train/validation/test slicing with typed label intervals, optional embargo, raw-axis masking, consumer missingness audits, and metric-empty split invalidation. |
| Portfolio | One bounded long-only equal-weight ranking engine with required role-bound source provenance, an enforced after-close/next-observed-close contract, nonzero row lag, frozen targets, strict held/trade-price gates, drift-aware holdings, signed trades, turnover, fixed costs/slippage, optional position clipping, residual cash, exact benchmark accounting, and a typed timing ledger. Target construction currently lives in `src/backtest/portfolio.py`; `src/strategies/` is placeholder-only. |
| Metrics | Common post-anchor net-return rows for annualized return, volatility, unadjusted zero-risk-free Sharpe-style ratio, benchmark/excess return, tracking error, and average turnover; initial-capital-anchored drawdown; full-window total return/turnover/cost; holdings, normalized HHI, and completed holding-episode metrics. |
| Volume impact | Lagged dollar-volume participation diagnostics and optional precomputed return impact; not a calibrated fill, capacity, or market-impact model. |
| Evidence | Deterministic synthetic/fixture reports, JSON experiment logs, and a registry of existing successful logs; not an immutable all-trial ledger. |
| Private diagnostics | Local-only EODHD validation and factor diagnostics on a fixed cohort; not accepted point-in-time real-data interpretation. |
| LEAN | Non-executing metadata/signal scaffold only; no algorithm runtime, parity evidence, brokerage, orders, paper, or live path. |

Protected main has a reported baseline of 1760 passing tests with two
platform-conditional wide-`longdouble` skips after PR #171. Stages 1-3, Stage
4a, Stage 4B-R0, Stage 4B-R1A, Stage 4B-R1B, Stage 4B-R1C, Stage 4B-R1D, and
Stage 4B-R1E are complete.
Stage 4a defines the accepted ledger contract and deterministic synthetic event
fixture; Stage 4B-R0 adds only a fail-closed registry foundation. Neither
implements
append-only storage, inspect data, alter research runtime behavior, migrate
legacy logs, or establish empirical validity.

## Current Research-Validity Findings

### High

1. The private EODHD workflow calculated and reviewed diagnostics through
   2026-06-26. The 2025-05-01 through 2026-05-31 interval is confirmed
   `historical_evaluation`, not a pristine holdout, and cannot be upgraded.
2. The fixed EODHD cohort lacks point-in-time membership, delisting/symbol
   history, resolved corporate-action and adjusted price/volume semantics, and
   complete provenance/license evidence.

Stage 1 resolves the former cross-split-label and unbounded-test defects.
`src/features/validation.py` now enforces six explicit inclusive boundaries,
complete label-interval ownership, a hard bounded test cutoff,
horizon-aware purge, optional embargo, raw-axis target masking,
warm-up/down metadata, and consumer missingness accounting. All four current
split consumers use the typed contract. Deterministic tests cover post-test,
asset/benchmark mutation, cross-edge asset mutation, zero-eligible,
partial-missing, all-missing, and usable-label but metric-empty cases.

Stage 3 defines the provider-agnostic contract: immutable dataset
identity, canonicalization, environment, and lineage; evidence-backed
entitlement; exact-version non-self-issued dataset review; bitemporal
availability; permanent security/listing identity; historical membership;
corporate actions and terminal value; field, missingness, calendar, benchmark,
risk-free, privacy, and exposure-ledger semantics. Contract acceptance does
not verify any current dataset or make the EODHD cohort formally usable.

Stage 4a defines the missing trial-accounting contract: semantic trials and
execution attempts are separate; identities and protected-access intent are
durable before action; campaign inventories and dependence families are
sealed; failures and non-runs remain counted; candidate evidence states remain
separate from execution states; event bytes are canonical and chained; formal
closure requires an independently retained checkpoint; and public projections
cannot carry private performance values. Runtime enforcement remains absent.

### Medium

1. Existing logging covers configured successful demos but remains a legacy
   overwrite-capable sidecar system. Stage 4b has not yet enforced append-only
   records for failed-before-write, abandoned, invalid, or retried work.
2. ICIR, HAC, bootstrap, full quantile monotonicity, factor decay, FDR, DSR,
   PBO/CSCV, permutation/placebo, and leave-out diagnostics are absent or
   partial.
3. Applied volume-impact metadata is caller-asserted rather than a calibrated,
   fully validated capacity contract.
4. No current dataset has passed the new benchmark purpose, investability,
   calendar compatibility, or risk-free evidence contract.

### Low and process hardening

1. Provider-specific absolute private paths remain in legacy diagnostic
   scripts and historical docs. The Stage 3 contract prohibits them in new
   tracked methodology records; runtime path hardening remains a separate
   implementation task.
2. No dependency/environment lock is tracked for independent reproduction.
3. Some historical docs still lack concise successor pointers.

The 2026-07-11 full conformance audit remains useful historical evidence at its
audited SHA. Its "no actionable P1/P2" conclusion does not supersede the later
timing, holdout, statistical, or public-documentation findings above.

## Delivery Sequence

| Stage | Status | Scope | Completion gate |
| --- | --- | --- | --- |
| 0. Research Charter Reset | Complete on protected main via PR #158 | Add the charter and reconcile specification, roadmap, handoff, controller, workflow Skill, and documentation contracts without changing research behavior. | Documentation tests, Skill audit, repo-map refresh, full baseline validation, CI, and final current-head review passed. |
| 1a. Purged/bounded split contract | Complete on protected main via PR #159 | Freeze explicit split starts/ends, bounded test semantics, label start/end ownership, horizon purge, optional embargo, raw-axis target masking, and warm-up/down metadata. | `docs/purged_bounded_split_contract.md`, its hand-calculated boundary matrix, documentation contracts, full gates, and independent read-only review passed. |
| 1b. Purged/bounded split implementation | Complete on protected main via PR #160 | Implement the accepted split contract and remove cross-split labels from every current future-return workflow. | Focused tests prove later prices cannot alter earlier split labels or metrics; raw axes retain masked exclusions; missingness is audited; full local, CI, and final-head review gates passed. |
| 2a. Signal/execution timing contract | Complete on protected main via PR #161 | Freeze the after-close/next-observed-close timeline, signal-lag types, signal/price-value gates, target-freeze rule, accounting order, bounded metric anchors, measured-date tracking error, capital-validity boundaries, benchmark window, terminal policy, metadata, and deterministic Stage 2b matrix. | `docs/signal_execution_timing_contract.md`, documentation contracts, full local/CI gates, and final current-head review passed. |
| 2b. Signal/execution timing implementation | Complete on protected main via PR #162 | Enforce the accepted timing contract across backtest inputs, targets, accounting metadata, metrics, callers, and affected synthetic evidence. Require role-bound immutable provenance captured as a caller-declared baseline; enforcement begins there, and only controlled, coordinate-logged later out-of-window complex writes may authorize lossless bounded dtype recovery. | Zero lag and invalid lag types fail; invalid signal and held/execution-price values fail before their declared boundary; targets use decision-time information; warm-up is excluded; strategy and benchmark share measured rows; invalid initial/gross/net/equity and direct metric inputs fail at their declared boundary; stale/untracked/tampered post-capture state fails closed; identical outside-versus-bounded `1+0j` frames are distinguished; the pre-capture-history limitation is explicit; all `TIMING-*` behavior tests, full local gates, independent review, CI, and final stable-head review passed. |
| 3. Point-in-time data methodology | Complete on protected main via PR #163 | Accept `docs/point_in_time_data_methodology_contract.md` as the provider-agnostic provenance, canonicalization/environment, immutable dataset-review, universe, corporate-action, field, benchmark, missing-data, privacy, and exposure-ledger contract. | The three gates remain separate; all `PIT-*` documentation cases, local/full gates, final current-head review, protected merge, and exact merge-head CI passed; no dataset, vendor, or formal interpretation was accepted. |
| 4a. Experiment/trial ledger contract | Complete on protected main via PR #164 | Freeze semantic trial versus attempt identity, ledger-owned preallocation/reference rules, lifecycle, campaign inventory/accounting closure and adjudication, protected access, canonical request/event chain, exact evidence-prefix/closure checkpoint, version-linked adjudication checkpoint, review binding, and exact private/public projection contracts without selecting a backend or identity architecture. The ledger timestamp profile rejects leap seconds because no immutable table is pinned. Exact event-payload coverage remains limited to the common envelope plus `LEDGER_EPOCH_CREATED`; the epoch atomically introduces `ledger_id`, while `actor_id` is external claimed attribution that grants no permission and authority-dependent behavior remains fail closed pending a Stage 4b owner decision. An initial inventory seal binds an atomically checked, nonrecursive pre-seal stream-head ordering anchor. Trial-parent, entity-allocation/reference, and fixed checkpoint semantic vectors are non-runtime contract facts. | `docs/experiment_trial_ledger_contract.md`, its synthetic epoch/checkpoint goldens and rejection/semantic vectors, all `LEDGER-*` documentation cases, local/full gates, final current-head review, protected merge, and exact merge-head CI passed; complete per-event schemas, runtime currentness, and research trials remain deferred. |
| 4b-R0. Payload-schema registry foundation | Complete on protected main via PR #165; incomplete diagnostic support only | Freeze a self-contained registry meta-contract, exact 37-event vocabulary, deterministic digest, duplicate-safe parser, the accepted epoch schema, and fail-closed dispatch. Keep all other known events `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`; do not use placeholders or synthetic checkpoint facts as wire schemas. | Registry vocabulary, supported/incomplete partitions, digest, parser, exact epoch vectors, and known-incomplete/unknown rejection passed locally, in CI, and under final current-head review; protected merge and exact merge-head CI passed. This gate does not accept a complete registry or Stage 4b runtime. |
| 4b-R1A. Allocation/registration architecture decision | Complete on protected main via PR #166 | Preserve R0 artifacts and behavior; retain the 37-event vocabulary; select reservation-only allocation, entity subjects, explicit scope, versioned closed DSL additions, prior allocation of every shared direct-scope campaign, and requirements for future exact reference-based family/sample authorities without accepting either authority. | The R1A contract, canonical-document reconciliation, documentation tests, full local gates, independent review, exact-head CI, final current-head review, protected merge, and exact merge-head CI passed. All 36 non-epoch events remained `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`; trial, attempt, and protected-access counts remained zero. |
| 4b-R1B. Campaign/experiment allocation schemas | Complete on protected main via PR #167 | Publish immutable R1 registry `0.2.0` and schema-language `0.2.0`; implement and meta-test all three closed DSL additions; promote only exact reservation-only `CAMPAIGN_ALLOCATED` and `EXPERIMENT_ALLOCATED` schemas with independent vectors and packaged R0/R1 parity. The exact experiment namespace is `exp_<32 lowercase hex>`. | R0 artifacts and behavior remain immutable; R1 supports exactly epoch plus the two allocation events and leaves the other 34 incomplete; all three DSL meta-test families, subject/scope killers, arbitrary-promotion rejection, package parity, local/full gates, exact-head CI, final review, protected merge, and exact merge-head CI passed. Every later promotion batch must publish a new immutable, monotonically versioned registry release rather than overwrite `0.2.0`. |
| 4b-R1C. Trial-family registration schema | Complete on protected main via PR #169 | Publish immutable registry `0.3.0` under unchanged schema-language `0.2.0`; preserve R0/R1 bytes and behavior; promote only `TRIAL_FAMILY_REGISTERED` with exact `fam_<32 lowercase hex>` subject IDs, bounded global/direct campaign scope, and pinned external definition and separate acceptance references. | Registry `0.3.0` supports exactly epoch, campaign allocation, experiment allocation, and trial-family registration while leaving the other 33 events incomplete. Independent fixtures and literal namespace/authority/acceptance/currentness/scope oracles, R0/R1/package parity, focused/full gates, exact-head CI, final current-head review, protected merge, and exact merge-head CI passed. Local shape acceptance is not proof of retrieval, reviewer independence, currentness, anti-reset history, or append behavior. |
| 4b-R1D. Sample registration schema | Complete on protected main via PR #170 | Publish immutable registry `0.4.0` under unchanged schema-language `0.2.0`; preserve R0/R1/R2 bytes and behavior; promote only `SAMPLE_REGISTERED` with exact `smp_<32 lowercase hex>` subject IDs, bounded global/direct campaign scope, pinned Stage 3 record and separate acceptance references, and allowlisted projection/publication-approval references. Keep local/global/external paths exclusive and both binding events incomplete for R1E. | Registry `0.4.0` supports exactly epoch, campaign allocation, experiment allocation, trial-family registration, and sample registration while leaving the other 32 events incomplete. Independent fixtures and literal namespace/authority/acceptance/currentness/privacy/scope oracles, R0/R1/R2/package parity, focused/full gates, exact-head CI, final current-head review, protected merge, and exact merge-head CI passed. Local shape acceptance is not proof of retrieval, reviewer independence, publication approval, currentness, path exclusivity, exposure history, or append behavior. |
| 4b-R1E. Campaign-entity and Stage 3 sample-reference binding schemas | Complete on protected main via PR #171 | Publish immutable registry `0.5.0` under unchanged schema-language `0.2.0`; preserve R0/R1/R2/R3 bytes and behavior; promote only `CAMPAIGN_ENTITY_BOUND` and `STAGE3_SAMPLE_REFERENCE_BOUND`. Use closed trial-family/sample and local/external source branches, singleton campaign scope, exact source-event references, stable external-origin sample identity, and fail-closed prior-allocation/currentness/path/anti-reset rules. | Registry `0.5.0` supports exactly seven events and leaves the other 30 incomplete. Independent four-path fixtures, literal branch/source/namespace/scope/authority/privacy oracles, prior-release and package parity, 925 focused and 1760 full tests with two platform skips, exact-head CI, one final current-head review, protected merge, and exact merge-head CI passed. Local shape acceptance is not proof of retained source bytes, authority, currentness, path history, uniqueness, or append behavior. |
| 4b-R1F. Semantic trial-allocation schema | Active in the current tree; owner selected bundle R1F-A | Publish immutable registry `0.6.0` under unchanged schema-language `0.2.0`; preserve R0/R1/R2/R3/R4 bytes and behavior; promote only `TRIAL_ALLOCATED`. Use exact trial identity, singleton campaign scope, exact prior parent/source references, complete canonical trial-definition and independent acceptance/publication/actor-authority tuples, and closed relation/code-identity unions. | Registry `0.6.0` must support exactly eight events and leave the other 29 incomplete. Independent original/rerun fixtures plus literal child/clone cases, namespace/parent/authority/relation/code/privacy/scope killers, prior-release and package parity, focused/full gates, exact-head CI, one final current-head review, protected merge, and exact merge-head CI must pass. Local shape acceptance must not be represented as proof of parent existence/order, retained bytes, authority/currentness, relation acyclicity, uniqueness, append, or research behavior. |
| 4b. Experiment/trial ledger implementation | Blocked by complete 37-event payload-registry acceptance and later runtime architecture decisions | Freeze exact schemas in separately reviewed event-family batches, then close 37-of-37 coverage without incomplete, wildcard, open-object, or free-string stand-ins. Only afterward implement the accepted contract in a separate namespace with atomic allocation, append-only events, restart/concurrency/tamper tests, protected-access capability enforcement, campaign completeness, and safe projection. Material backend/private-location/recovery/checkpoint-currentness architecture choices require a separately recorded owner decision. | Complete registry coverage rejects every missing, unknown, or incompletely specified event before append. Later behavioral tests prove no silent overwrite, backfilled holdout laundering, failed-before-write loss, retry hiding, prefix/tail truncation, currentness rollback, checkpoint fork, or private projection leak. |
| 5. Statistical validation | Blocked by Stage 4b | Add descriptive, dependence-aware, bootstrap, placebo, multiplicity, DSR, PBO, and stability controls in design-first increments. | Registered inference policy and deterministic synthetic/golden tests pass. |
| 6. Canonical factor registry | Blocked by Stages 3-5 | Register interpretable price/volume baselines first; fundamentals wait for filing-availability support. | Formula, direction, source, fields, lag, parameters, fixture, tests, limitations, and trial family are complete. |
| 7. WorldQuant batches | Blocked by Stage 6 | Add 5-10 formulas per compatible data family after operator contracts are ready. | Formula transcription/parity, missing/warm-up, timing, and traceability tests pass; no strategy claim. |
| 8. Factor campaign runner | Blocked by Stages 3-7 | Run broad point-in-time single-factor campaigns across registered horizons and subgroups. | All trials/failures retained; multiple-testing-adjusted promotion only. |
| 9. Strategy factory | Blocked by Stage 8 promotion | Add registered selection, holding, rebalance, buffer, and reviewed long-short families. | Every variant counted; costs and execution frozen. |
| 10. Portfolio/risk engine | Blocked by Stage 9 | Add reviewed exposure, turnover, liquidity, volatility, concentration, weighting, and infeasibility contracts. | Drift-aware accounting and constraint tests pass. |
| 11. Frozen historical evaluation | Blocked by Stages 3-10 | Freeze candidates, rules, costs, metrics, thresholds, and trial policy before purged walk-forward evaluation. | Correct sample classification, complete access ledger, and no tuning on protected results. |
| 12. Independent reproduction | Blocked by Stage 11 promotion | Reproduce promoted results from the frozen manifest through an independent path. | Data/config/code/output and metric parity pass. |
| 13. LEAN parity/paper candidate | Blocked by `PORTFOLIO_PASS` and separate scope decision | Compare signals, holdings, trades, costs, and reconciliation only. | Explicit authorization is still required before paper runtime; live remains unauthorized. |

## Review and Change Policy

- Use one coherent stage per branch and pull request.
- Keep automatic GitHub Codex review disabled and do not request review on a
  Draft PR.
- After local validation and CI are stable, request `@codex review` once on the
  final stable head when review is required. Re-review only after an actionable
  fix changes that head.
- Do not enable auto-merge or merge a review-required PR until Codex review has
  completed on the current head with no unresolved actionable findings.
- Do not let multiple agents edit the roadmap, handoff, same factor/operator,
  or same evidence record concurrently.
- Preserve failures and caveats; do not implement more factors while
  prerequisite timing, data, trial, and statistical gates remain blocked.
- Never direct-push or direct-merge to `main`, bypass required protections or
  reviews, or use `--admin`.

# Current Roadmap

Updated: 2026-07-27 for the Experiment and Trial Ledger Contract.

Protected-main baseline verified before this stage: `a6c147e`, the protected
merge of PR #163, with successful exact merge-head CI.

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
`docs/experiment_trial_ledger_contract.md` is the proposed Stage 4a design
authority. Its local candidate freezes semantic-trial and execution-attempt identity,
allocation-before-action, campaign completeness, protected-access,
canonical-event, checkpoint, and private/public projection semantics. Stage 4b
runtime enforcement remains blocked until the contract completes review,
protected merge, and exact merge-head CI.

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

Protected main has a local baseline of 854 passing tests with two
platform-conditional wide-`longdouble` skips, plus successful PR and exact
merge-head CI for PR #163. Stages 1-3 are complete. Stage 4a defines the ledger
contract candidate and deterministic synthetic event fixture only; it does not implement
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
| 4a. Experiment/trial ledger contract | Local P2-remediation gates passed; exact-current-head CI/final re-review, protected merge, and exact merge-head CI required | Freeze semantic trial versus attempt identity, ledger-owned preallocation/reference rules, lifecycle, campaign inventory/accounting closure and adjudication, protected access, canonical request/event chain and campaign evidence-prefix checkpoint, review binding, and exact private/public projection contracts without selecting a backend or identity architecture. Exact event-payload coverage is limited to the common envelope plus `LEDGER_EPOCH_CREATED`; the epoch atomically introduces `ledger_id`, while `actor_id` is external claimed attribution that grants no permission and any authority-dependent behavior remains fail closed pending a Stage 4b owner decision. An initial inventory seal binds an atomically checked, nonrecursive pre-seal stream-head ordering anchor distinct from the later independent closure checkpoint. Trial-parent and entity-allocation/reference checks are non-append semantic facts. | `docs/experiment_trial_ledger_contract.md`, its synthetic epoch golden and rejection/semantic vectors, all `LEDGER-*` documentation cases, local/full gates, final current-head review, protected merge, and exact merge-head CI pass; the complete per-event schema registry remains deferred and no runtime or research trial is added. |
| 4b. Experiment/trial ledger implementation | Blocked by Stage 4a protected merge and exact merge-head CI | First freeze a complete machine-readable exact payload-schema registry for every closed-vocabulary event with deterministic vectors/digest. Then implement the accepted contract in a separate namespace with atomic allocation, append-only events, restart/concurrency/tamper tests, protected-access capability enforcement, campaign completeness, and safe projection. Material backend/private-location/recovery/checkpoint architecture choices require a separately recorded decision. | Registry coverage rejects every missing, unknown, or incompletely specified event before append. Later behavioral tests prove no silent overwrite, backfilled holdout laundering, failed-before-write loss, retry hiding, prefix truncation, or private projection leak. |
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

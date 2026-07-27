# Current Roadmap

Updated: 2026-07-26 for the Signal, Execution, and Metric Timing Contract.

Protected-main baseline verified before this stage: `202273b`, the merge of PR
#160.

This is the canonical roadmap. `docs/research_program_charter.md` defines the
long-term evidence policy. Older checkpoints, gap refreshes, plans, and audits
remain historical evidence and must not be used as active task queues.
`docs/purged_bounded_split_contract.md` is the accepted and implemented Stage 1
split contract.
`docs/signal_execution_timing_contract.md` is the accepted Stage 2a design
target; code conformance is deferred to Stage 2b.

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
| Portfolio | One long-only equal-weight ranking engine with default one-row lag, drift-aware holdings, signed trades, turnover, fixed costs/slippage, optional position clipping, residual cash, and benchmark accounting. Target construction currently lives in `src/backtest/portfolio.py`; `src/strategies/` is placeholder-only. |
| Metrics | Return, volatility, unadjusted Sharpe-style ratio, drawdown, turnover/cost totals, benchmark/excess return, holdings count, normalized HHI, exact-date tracking error, and completed holding-episode metrics. |
| Volume impact | Lagged dollar-volume participation diagnostics and optional precomputed return impact; not a calibrated fill, capacity, or market-impact model. |
| Evidence | Deterministic synthetic/fixture reports, JSON experiment logs, and a registry of existing successful logs; not an immutable all-trial ledger. |
| Private diagnostics | Local-only EODHD validation and factor diagnostics on a fixed cohort; not accepted point-in-time real-data interpretation. |
| LEAN | Non-executing metadata/signal scaffold only; no algorithm runtime, parity evidence, brokerage, orders, paper, or live path. |

Protected main has 637 passing tests plus successful post-merge CI. The Stage
2a branch changes documentation, repo-map index tooling, and a
documentation-contract test only and has 638 passing tests plus Ruff,
compilation, and package-build evidence. Its current-head GitHub CI and
final-head review remain PR gates. These checks establish software or
documentation behavior, not empirical research validity.

## Current Research-Validity Findings

### High

1. The accepted Stage 2a contract requires a non-boolean integer lag of at
   least one, exact axes, decision-time target freezing, and common metric
   anchors. `run_long_only_backtest()` does not yet enforce those rules: it
   accepts `signal_lag_periods=0`, silently reindexes signals, and lets
   execution-close price availability affect target membership.
2. The private EODHD workflow calculated and reviewed test diagnostics through
   2026-06-26. The 2025-05-01 through 2026-05-31 interval is historical
   evaluation or pseudo-holdout evidence, not presumed pristine holdout data.
3. The fixed EODHD cohort lacks point-in-time membership, delisting/symbol
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

### Medium

1. Feature warm-up and evaluation windows are not consistently separated in
   synthetic momentum metrics.
2. Basic volatility and Sharpe still include the initialization row while
   tracking error excludes it; maximum drawdown lacks an initial-capital
   anchor, and Sharpe assumptions are not fully recorded.
3. Existing logging covers configured successful demos but cannot guarantee
   append-only records for failed-before-write, abandoned, or invalid trials.
4. ICIR, HAC, bootstrap, full quantile monotonicity, factor decay, FDR, DSR,
   PBO/CSCV, permutation/placebo, and leave-out diagnostics are absent or
   partial.
5. Applied volume-impact metadata is caller-asserted rather than a calibrated,
   fully validated capacity contract.
6. Benchmark purpose, return convention, and compatibility remain incomplete
   for formal historical inference.

### Low and process hardening

1. Provider-specific absolute private paths are embedded in tracked scripts and
   docs; no raw private rows are tracked, but the boundary needs a later
   redacted-manifest and path-hardening design.
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
| 2a. Signal/execution timing contract | Complete on this head; behavior not implemented | Freeze the after-close/next-observed-close timeline, signal-lag types, target-freeze rule, accounting order, bounded metric anchors, benchmark window, terminal policy, metadata, and deterministic Stage 2b matrix. | `docs/signal_execution_timing_contract.md` and documentation contracts pass without changing runtime behavior. |
| 2b. Signal/execution timing implementation | Next after Stage 2a merge | Enforce the accepted timing contract across backtest inputs, targets, accounting metadata, metrics, callers, and affected synthetic evidence. | Zero lag and invalid lag types fail; targets use decision-time information; warm-up is excluded; strategy and benchmark share measured rows; all `TIMING-*` behavior tests and full gates pass. |
| 3. Point-in-time data methodology | Blocked by Stage 2b | Define provider-agnostic provenance, universe, delisting/corporate-action, field, benchmark, missing-data, privacy, and holdout-ledger contracts. | Every required methodology field is accepted before formal interpretation; no vendor download is implied. |
| 4. Experiment/trial ledger | Blocked by Stage 3 design dependencies | Allocate immutable IDs before execution and retain every attempted, failed, invalid, aborted, and excluded trial plus hashes and access records. | Append-only and completeness tests pass; no silent overwrite or failed-before-write loss. |
| 5. Statistical validation | Blocked by Stage 4 | Add descriptive, dependence-aware, bootstrap, placebo, multiplicity, DSR, PBO, and stability controls in design-first increments. | Registered inference policy and deterministic synthetic/golden tests pass. |
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

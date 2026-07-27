# Current Roadmap

Updated: 2026-07-26 for the Research Charter Reset.

Baseline SHA verified before this stage: `a1486ea`.

This is the canonical roadmap. `docs/research_program_charter.md` defines the
long-term evidence policy. Older checkpoints, gap refreshes, plans, and audits
remain historical evidence and must not be used as active task queues.

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
| Diagnostics | Correlation, IC, Rank IC, top-minus-bottom quantile spread, coverage, and basic chronological train/validation/test slicing. |
| Portfolio | One long-only equal-weight ranking engine with default one-row lag, drift-aware holdings, signed trades, turnover, fixed costs/slippage, optional position clipping, residual cash, and benchmark accounting. Target construction currently lives in `src/backtest/portfolio.py`; `src/strategies/` is placeholder-only. |
| Metrics | Return, volatility, unadjusted Sharpe-style ratio, drawdown, turnover/cost totals, benchmark/excess return, holdings count, normalized HHI, exact-date tracking error, and completed holding-episode metrics. |
| Volume impact | Lagged dollar-volume participation diagnostics and optional precomputed return impact; not a calibrated fill, capacity, or market-impact model. |
| Evidence | Deterministic synthetic/fixture reports, JSON experiment logs, and a registry of existing successful logs; not an immutable all-trial ledger. |
| Private diagnostics | Local-only EODHD validation and factor diagnostics on a fixed cohort; not accepted point-in-time real-data interpretation. |
| LEAN | Non-executing metadata/signal scaffold only; no algorithm runtime, parity evidence, brokerage, orders, paper, or live path. |

The verified software baseline has 591 passing tests plus Ruff, compilation,
package-build, and exact-head CI evidence. Those checks establish software
behavior, not empirical research validity.

## Current Research-Validity Findings

### High

1. Forward returns are calculated on the full panel before split slicing in
   `research/eodhd_factor_diagnostics_dry_run.py` and
   `research/local_csv_fixture_workflow_demo.py`. Labels at train/validation
   edges can use prices from the next split.
2. `make_train_validation_test_split()` rejects a bounded `test_end` earlier
   than the final input date, so a frozen evaluation window cannot exclude
   later available data.
3. `run_long_only_backtest()` documents signals as known after close but
   accepts `signal_lag_periods=0`, allowing ambiguous same-close target setting.
4. The private EODHD workflow calculated and reviewed test diagnostics through
   2026-06-26. The 2025-05-01 through 2026-05-31 interval is historical
   evaluation or pseudo-holdout evidence, not presumed pristine holdout data.
5. The fixed EODHD cohort lacks point-in-time membership, delisting/symbol
   history, resolved corporate-action and adjusted price/volume semantics, and
   complete provenance/license evidence.

### Medium

1. Feature warm-up and evaluation windows are not consistently separated in
   synthetic momentum metrics.
2. Basic risk metrics do not enforce one common timestamp/anchor contract, and
   Sharpe assumptions are not fully recorded.
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
| 0. Research Charter Reset | Complete on this head | Add the charter and reconcile specification, roadmap, handoff, controller, workflow Skill, and documentation contracts without changing research behavior. | Documentation tests, Skill audit, repo-map refresh, full baseline validation, and independent read-only review pass. |
| 1a. Purged/bounded split contract | Next | Design explicit split starts/ends, bounded test windows, label start/end ownership, horizon purge, optional embargo, and warm-up/down metadata. | Design and deterministic boundary-test matrix accepted before implementation. |
| 1b. Purged/bounded split implementation | Blocked by 1a | Implement the accepted split contract and remove cross-split labels. | Focused tests prove later prices cannot alter earlier split labels or metrics; full gates pass. |
| 2. Signal/execution timing | Blocked by Stage 1 | Freeze feature, availability, decision, execution, and return timestamps; resolve zero-lag and metric-window contracts. | Close-derived signals cannot receive ambiguous same-close fills; timing and anchor tests pass. |
| 3. Point-in-time data methodology | Blocked by Stages 1-2 | Define provider-agnostic provenance, universe, delisting/corporate-action, field, benchmark, missing-data, privacy, and holdout-ledger contracts. | Every required methodology field is accepted before formal interpretation; no vendor download is implied. |
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
- Do not let multiple agents edit the roadmap, handoff, same factor/operator,
  or same evidence record concurrently.
- Preserve failures and caveats; do not implement more factors while
  prerequisite timing, data, trial, and statistical gates remain blocked.
- Never direct-push or direct-merge to `main`, bypass required protections or
  reviews, or use `--admin`.

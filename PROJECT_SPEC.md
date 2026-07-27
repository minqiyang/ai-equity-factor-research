# Project Specification

## Objective

Build a rigorous, reproducible, falsifiable, and auditable historical equity
research platform. The platform should faithfully reproduce published factors,
WorldQuant formulas, institutional rules, strategies, and portfolio methods,
then determine whether they have stable out-of-sample stock-selection or
portfolio value under point-in-time data, frozen rules, realistic costs, and
multiple-testing controls.

Optimize the research process for evidence quality rather than the highest
historical Sharpe ratio. Retain negative, failed, invalid, and inconclusive
results.

`docs/research_program_charter.md` is the canonical long-term evidence policy.
`docs/current_roadmap.md` is the active staged delivery plan.
`docs/signal_execution_timing_contract.md` is the accepted Stage 2 timing
authority. Stage 2b implements it with required, role-bound, immutable source
provenance whose caller-declared baseline is captured before later mutation,
plus a controlled coordinate ledger for any later source write. Enforcement
begins at capture and cannot reconstruct pre-capture history.

## Current Phase and Boundary

The current phase is research-only.

- No brokerage connection, orders, paper deployment, live deployment, or
  real-money execution.
- No vendor download, credential use, or remote data access is authorized by
  this specification.
- The public repository may use synthetic data, committed fixtures, and local
  data only under explicit privacy and methodology gates.
- `lean/` remains a non-executing scaffold until a future `PORTFOLIO_PASS`
  candidate and a separate scope decision authorize parity work.

## Evidence Layers

The project distinguishes:

1. **Factor:** a date-by-asset score and its incremental cross-sectional
   information.
2. **Strategy:** a frozen signal, selection, holding, rebalance, and execution
   rule.
3. **Portfolio:** strategies under benchmark, weighting, exposure, liquidity,
   concentration, capacity, and risk constraints.
4. **Execution:** target-to-order-intent, fill, cost, position, and
   reconciliation behavior.

Evidence from one layer does not certify the next layer. Passing deterministic
tests proves implementation behavior, not historical validity.

## Data and Universe Requirements

- Asset class: listed equities.
- Initial formal baseline: liquid US common stocks, subject to an accepted
  point-in-time universe definition.
- Initial strategy posture: long-only. Long-short research requires a separate
  borrow and shortability contract.
- Every feature must use information available by its declared signal
  availability timestamp.
- Formal data must record provider and license, version/hash, retrieval time,
  permanent identifiers, historical membership, delistings, mergers, ticker
  changes, corporate actions, raw/adjusted field semantics, filing/publication
  times, revision policy, missing/stale behavior, calendar/timezone, benchmark,
  risk-free policy, and private-data boundary.
- A static survivor cohort may be used for diagnostics but not presented as
  point-in-time universe evidence.

No research-grade provider is selected by this specification.

## Factor Program

Begin with interpretable baselines:

- momentum and reversal variants;
- realized and idiosyncratic volatility;
- beta;
- liquidity, turnover, and Amihud-style measures;
- size;
- value;
- profitability and quality;
- investment;
- leverage; and
- volume shocks.

Fundamental factors may enter formal campaigns only after point-in-time filing
availability is supported.

WorldQuant-style formulas enter in reviewed batches of 5-10 by compatible data
family. Every factor requires source traceability, exact formula, expected
direction, required fields, availability lag, parameters, horizon,
preprocessing, neutralization, missing policy, golden fixture, timing tests,
known limitations, and a trial family. A factor implementation is not a
strategy or profitability claim.

## Timing and Sample Isolation

- Record feature time, signal availability, decision, execution, label start,
  label end, and return measurement end.
- Signal inputs must be known before the declared execution time.
- Under the accepted close-only contract, a close-derived signal becomes
  available strictly after its stamped close, the earliest supported idealized
  target reset is the next observed source-row close, and the target first
  earns the following close-to-close return.
- Close-derived daily signals require a non-boolean integer lag of at least one
  observed source row. Lag zero requires a different typed and reviewed
  execution model and is not authorized implicitly.
- Use bounded development, validation, and evaluation windows.
- Purge labels that cross split boundaries; add embargo when overlapping
  labels or the accepted dependence model requires it.
- Keep feature warm-up/down history separate from measured evaluation periods.
- Preserve exact alignment among raw data, factors, ranks, target returns,
  weights, benchmark returns, and reported metrics.
- Never use future prices, future membership, future fundamentals, later
  revisions, future corporate actions, or same-period target returns as
  features.

These timing rules are normative. The Stage 2b backtester rejects zero and
invalid lag types, requires exact full-source axes and exact inclusive
evaluation bounds, requires source provenance captured after final panel
construction as the caller-declared baseline before later mutation, validates
only bounded final-signal values,
freezes targets without execution-close reranking, validates held endpoints
and frozen trade legs in their declared order, and gives period metrics one
common post-anchor window. Untracked source writes fail closed. Typed metadata
and a deterministic timing ledger expose the resolved schedule and
signal/holding intervals. Direct/nested provenance objects are rejected by the
experiment-log serializer, while current committed logs contain only the
allowlisted provenance policy/status; extracted primitives remain a caller
responsibility. This implementation conformance is software evidence only;
exchange-calendar, point-in-time data, cost-capacity, and empirical-validity
gates remain open.

Every protected-sample access must enter the holdout exposure ledger. Previously
examined data is `historical_evaluation` or `pseudo_holdout`, not an untouched
holdout.

## Backtesting Principles

- Use explicit rebalancing and execution dates.
- Apply trades only after signals are available.
- State next-open, next-close, auction, or other execution assumptions.
- Keep target weights, drifted holdings, trades, turnover, costs, and residual
  cash auditable.
- Compare against a preregistered investable benchmark and simple baselines.
- Include explicit transaction costs, slippage, capacity, and stress cases
  before promotion.
- Treat zero-cost or no-slippage output as diagnostic only.
- Define missing, stale, suspended, delisted, and infeasible-target behavior.
- Preserve drift-aware accounting identities.

## Trial and Statistical Discipline

Before a formal run, allocate immutable experiment, campaign, trial-family, and
trial IDs. Record every attempted configuration, failure, abort, invalid run,
data revision, output hash, review outcome, selection decision, and protected
sample access. Do not report only the best configuration.

Formal validation is staged to include:

- IC, Rank IC, dispersion, ICIR, and sign hit rate;
- quantile returns, monotonicity, coverage, and decay;
- HAC/Newey-West and block/bootstrap inference where appropriate;
- permutation/placebo and leave-out stability checks;
- FDR or another registered multiple-testing adjustment;
- Deflated Sharpe Ratio;
- PBO/CSCV or a reviewed practical alternative; and
- purged walk-forward evaluation with a frozen candidate set.

The exact inference method and thresholds must be preregistered before protected
results are viewed.

## Evaluation Framework

Use a multi-objective framework appropriate to the evidence layer:

- net active return;
- Sharpe and Information Ratio with stated assumptions;
- maximum drawdown, downside risk, and CVaR;
- turnover, cost sensitivity, and capacity;
- concentration and benchmark, sector, beta, size, and style exposures;
- fold, subperiod, universe, and parameter stability;
- statistical uncertainty and multiple-testing-adjusted evidence;
- simplicity and economic rationale; and
- later local-to-LEAN parity.

If future-winner recall is studied, predefine the positive class and report
Precision@K, Recall@K, NDCG, Rank IC, breadth, turnover, and net portfolio
results together. Never optimize recall alone.

## Candidate States

Use exactly one evidence state for each evaluated object:

`INVALID`, `INCONCLUSIVE`, `REJECTED`, `DIAGNOSTIC_ONLY`, `CONDITIONAL`,
`RESEARCH_PASS`, `PORTFOLIO_PASS`, `PAPER_CANDIDATE`, or `LIVE_CANDIDATE`.

Use the lowest state supported by completed gates. A candidate label is not
authorization to paper trade or trade live.

## Development Sequence

The canonical sequence is maintained in `docs/current_roadmap.md`:

1. research charter reset;
2. purged and bounded sample splits;
3. signal and execution timing;
4. point-in-time data methodology;
5. immutable experiment and trial ledger;
6. statistical validation;
7. factor registry and interpretable baselines;
8. WorldQuant batches;
9. factor campaign runner;
10. strategy factory;
11. portfolio and risk engine;
12. frozen walk-forward historical evaluation;
13. independent reproduction; and
14. separately gated LEAN parity and paper candidacy.

Each stage uses one coherent pull request. No later stage may imply an earlier
methodology or evidence gate is complete.

## Explicit Non-Goals

- No live trading or real-money execution.
- No brokerage integration, credentials, or order placement.
- No paper deployment under the current phase.
- No self-modifying production strategy.
- No black-box strategy oracle.
- No unsupported claims of alpha, profitability, robustness, investment
  value, or readiness.
- No parameter mining presented as discovery.
- No best-only result reporting.
- No hidden manual edits or removal of failed evidence.
- No external data fetching without separate explicit authorization.

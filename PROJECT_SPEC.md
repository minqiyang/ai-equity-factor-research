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
`docs/point_in_time_data_methodology_contract.md` is the accepted Stage 3
provider-agnostic data authority. It separates acceptance of the methodology
contract from review of a particular immutable dataset manifest and from
eligibility for formal interpretation.
`docs/experiment_trial_ledger_contract.md` is the accepted Stage 4a design
authority. It separates semantic trials from execution attempts, freezes
allocation-before-action and access-intent-before-read semantics, and requires
append-only completeness plus independently retained evidence and adjudication
checkpoints.
`docs/experiment_trial_ledger_schema_registry_contract.md` defines the
protected-main Stage 4B-R0 fail-closed registry foundation. R0 supports only
the exact epoch schema, rejects the other 36 known events as
`SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`, and does not claim a complete payload
registry or Stage 4b runtime enforcement.
`docs/experiment_trial_ledger_allocation_registration_schema_contract.md`
defines the owner-selected Stage 4B-R1A architecture-A decision. It preserves
R0 unchanged, retains the 37-event vocabulary, selects reservation-only
campaign/experiment allocation, entity subjects, explicit campaign scope, a
versioned closed R1 schema-language path, and requirements for future exact
reference-based family and Stage 3 sample authorities. R1A accepts neither
authority and is design-only: it promotes no event, creates no trial or
access, and leaves Stage 4b runtime and Stage 5 blocked.
The same contract now contains the bounded Stage 4B-R1B implementation
authority. The owner ratified `exp_<32 lowercase hex>` as the exact experiment
namespace. A separate immutable registry/schema-language `0.2.0` release
supports only epoch plus reservation-only campaign and experiment allocation,
keeps the other 34 events `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`, and preserves
the R0 artifacts, default entry point, and behavior. Shape validation does not
implement allocation, append, parent existence, uniqueness, authorization,
campaign execution, or research interpretation.
`docs/experiment_trial_ledger_trial_family_registration_schema_contract.md`
defines the owner-selected Stage 4B-R1C-A trial-family registration authority.
It freezes `fam_<32 lowercase hex>`, a common direct-scope maximum of 32,
retrieval of complete repository-external canonical family definitions through
an exact digest-pinned authority tuple, a separate immutable acceptance record
with reviewer independence, stable global family identity, monotonic current
acceptance generations, explicit `supersedes`/`depends_on` relations, and
anti-reset rules. A separate immutable registry `0.3.0` promotes only
`TRIAL_FAMILY_REGISTERED`, keeps the other 33 events incomplete, and preserves
R0/R1 bytes and behavior. Local schema acceptance proves only closed event
shape; retrieval, authority, acceptance currentness, role independence,
history, and append behavior remain fail-closed stateful requirements.
`docs/experiment_trial_ledger_sample_registration_schema_contract.md` defines
the owner-selected Stage 4B-R1D-A local sample-registration authority. It
freezes `smp_<32 lowercase hex>`, the existing direct-scope maximum of 32, an
exact digest-pinned repository-external Stage 3 sample authority, a separate
non-self-issued acceptance record, allowlisted public projection and
publication-approval references, single-current generations, mutually
exclusive local/global/external representation paths, and anti-reset overlap
semantics. A separate immutable registry `0.4.0` promotes only
`SAMPLE_REGISTERED`, keeps both binding events and the other 30 events
incomplete, and preserves R0/R1/R2 bytes and behavior. Local schema acceptance
proves only closed event shape; retrieval, authority, acceptance and
publication currentness, role independence, path exclusivity, exposure
history, prior allocation, and append behavior remain fail-closed stateful
requirements.
`docs/experiment_trial_ledger_binding_schema_contract.md` defines the
owner-selected Stage 4B-R1E-A binding authority. A separate immutable registry
`0.5.0` preserves R0/R1/R2/R3 bytes and behavior while promoting only
`CAMPAIGN_ENTITY_BOUND` and `STAGE3_SAMPLE_REFERENCE_BOUND`. Campaign binding
uses a closed outer subject union and, for samples, a closed local-registration
versus external-reference source union. The first external Stage 3 reference
allocates one `smp_<32 lowercase hex>` identity for one campaign; later
campaigns reuse that same external-origin identity only by binding the exact
first event ID/hash. Local schema acceptance proves only event shape and
reference syntax; retained-source bytes/digests, prior campaign allocation,
authority/currentness, path exclusivity, anti-reset history, uniqueness, and
append behavior remain fail-closed stateful requirements.
`docs/experiment_trial_ledger_trial_allocation_schema_contract.md` defines the
owner-selected Stage 4B-R1F-A semantic trial-allocation authority. A separate
immutable registry `0.6.0` preserves R0/R1/R2/R3/R4 bytes and behavior while
promoting only `TRIAL_ALLOCATED`. It freezes `trl_<32 lowercase hex>`, one
singleton campaign scope, exact earlier campaign/experiment/family/sample
evidence, a complete repository-external canonical trial definition and
independent acceptance/publication/actor-authority records, closed
original/child/clone/rerun relations, and closed clean-commit/dirty-tree code
identity. Local schema acceptance proves only closed event shape; parent
existence and order, external retrieval and currentness, reviewer
independence, actor authority, relation acyclicity, code-byte retention,
uniqueness, append behavior, and pre-action enforcement remain fail-closed
stateful requirements.

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
  risk-free policy, canonicalization and environment identity, an immutable
  non-self-issued dataset-review decision, and the private-data boundary.
- A static survivor cohort may be used for diagnostics but not presented as
  point-in-time universe evidence.

No research-grade provider is selected by this specification.
Accepting the Stage 3 contract does not verify a dataset, entitlement,
historical membership, or field semantics and does not establish
`formal_ready`. A dataset-specific private manifest, safe public projection,
and exact-version immutable review decision issued by an authorized
non-producing reviewer must satisfy the contract for one declared use, while
later trial, statistical, cost, privacy, and evidence-layer gates remain
independently required.

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

Viewing asset or benchmark levels, corporate-action inputs, returns, labels,
or any other data from which protected outcomes can be reconstructed is
protected-sample access, not metadata-only intake.

The private diagnostics covering 2025-05-01 through 2026-05-31 are confirmed
historical access and are classified `historical_evaluation`; that interval
cannot be upgraded to a pristine holdout. Stage 3 defines the exposure schema
and downgrade rules. Stage 4 must implement append-only, pre-access allocation
and completeness enforcement.

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

Before a formal run, allocate immutable campaign, experiment, global
trial-family, semantic-trial, and execution-attempt IDs under
`docs/experiment_trial_ledger_contract.md`. Record every configured variation,
invocation, retry, failure, abort, invalid/excluded run, data revision, output
disposition/hash, review outcome, selection decision, and protected-sample
access. Trial completion is an execution state, not a research pass. Do not
report only the best configuration.

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
5. immutable experiment and trial ledger contract and implementation;
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

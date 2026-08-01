# Research Program Charter

Adopted: 2026-07-26

Status: canonical long-term research intent and evidence policy.

This charter defines what the repository is trying to learn, which evidence is
required, and which research-scope boundaries apply. `PROJECT_SPEC.md` describes
the project contract, `docs/current_roadmap.md` is the active task sequence, and
`docs/current_handoff.md` is the operational entry point. External-action
authority is owned only by [`AGENTS.md`](../AGENTS.md#authority-and-scope).
Historical plans and audits remain evidence, not active task queues.

## Mission

Build a reproducible, falsifiable, and auditable historical equity-research
platform that can:

1. reproduce a published factor, WorldQuant formula, institutional rule,
   strategy, or portfolio method faithfully;
2. evaluate it on point-in-time, tradable, survivorship-aware historical data;
3. freeze rules before protected evaluation;
4. account for every attempted trial and failed result;
5. measure stability, uncertainty, costs, capacity, and multiple-testing risk;
6. determine whether the evidence supports stock-selection, strategy, or
   portfolio value; and
7. allow only a separately gated candidate to proceed to independent
   reproduction and later LEAN parity work.

The objective is evidence quality, not the highest historical Sharpe ratio.
No single metric is sufficient for promotion.

## Current Research Scope Boundary

The current phase is research-only. This section records evidence scope and
non-goals; it grants no authority. External actions remain governed by
[`AGENTS.md`](../AGENTS.md#authority-and-scope).

- Local synthetic and explicitly accepted historical research are in scope
  only through the gates in this charter and the current roadmap.
- Vendor downloads, credentials, remote/private data, brokerage connections,
  orders, paper/live deployment, and real-money execution are outside this phase.
- The existing `lean/` directory remains a non-executing scaffold.
- A future `PORTFOLIO_PASS` or `LIVE_CANDIDATE` label is evidence state only; it
  does not change repository scope or external-action authority.

## Evidence Layers

The program keeps four evidence layers separate.

| Layer | Object being tested | Required conclusion |
| --- | --- | --- |
| Factor | A date-by-asset score computed from information available at the declared time. | Whether the score has incremental cross-sectional information under a registered diagnostic protocol. |
| Strategy | A frozen signal policy, selection rule, holding rule, rebalance schedule, and execution assumption. | Whether the rule has stable out-of-sample value after its stated costs. |
| Portfolio | One or more strategies under benchmark, weighting, exposure, liquidity, concentration, and risk constraints. | Whether active value survives realistic constraints, costs, capacity, and stability tests. |
| Execution | The translation from frozen targets to order intents, simulated fills, positions, costs, and reconciliation. | Whether local and LEAN behavior agree closely enough for a separately gated paper candidate evidence state. |

A factor helper is not a strategy. A strategy backtest is not portfolio
evidence. Portfolio evidence is not execution evidence. Software correctness
is necessary at every layer but is not empirical validation.

## Non-Negotiable Research Principles

### Reproducibility and falsifiability

- Every formal claim must identify the hypothesis, estimand, expected
  direction, universe, horizon, sampling unit, benchmark, and rejection rule.
- A result must be reproducible from a frozen code SHA, configuration, data
  manifest, and environment record.
- Failed, invalid, excluded, abandoned, weak, and inconclusive trials remain
  visible.
- Manual edits to evidence are prohibited unless the edit itself is recorded
  and reproducible.

### Timing and sample isolation

- Record feature time, signal availability time, decision time, execution
  time, label start, label end, and return measurement end.
- A label belongs to a split only when its complete information interval is
  contained in that split.
- Purge horizon-crossing labels at every split edge. Add embargo when
  overlapping labels or a reviewed dependence model requires it.
- Keep feature warm-up history separate from the evaluation window. Record
  warm-up and warm-down rows.
- Close-derived daily signals require a minimum one-row lag unless an explicit,
  reviewed execution model proves a different timestamp contract.
- Bounded evaluation windows must remain bounded even when later data exists.

### Point-in-time and tradability

Formal historical interpretation requires an accepted data methodology that
records:

- provider, license or entitlement, retrieval time, version, and content hash;
- permanent identifiers, ticker history, listings, delistings, mergers, and
  date-effective universe membership;
- corporate actions, dividends, total-return policy, and raw/adjusted
  price-volume semantics;
- filing time, public-availability time, revision policy, and effective dates
  for fundamentals or classifications;
- missing, stale, suspended, and invalid-data behavior;
- exchange calendar, timezone, benchmark, and risk-free-rate policy;
- private storage and publication boundaries; and
- data-quality exceptions and manual transformations.

Without those fields, a run may be a loader check or fixed-cohort diagnostic,
but it is not formal point-in-time universe evidence.

### Costs, capacity, and execution

- Zero-cost or zero-slippage output is diagnostic only and cannot support
  promotion.
- Formal strategy evidence freezes commissions, fees, spread or slippage,
  impact or capacity assumptions, participation limits, cash behavior, and the
  execution price/timestamp before protected evaluation.
- Volume-aware diagnostics are not calibrated fill or market-impact evidence.
- Long-short research additionally requires explicit borrow availability,
  borrow cost, recall, and shortability assumptions.

### Complete trial accounting

Every planned or attempted variation is a trial, including changes to formula,
direction, lookback, horizon, universe, preprocessing, neutralization,
selection, weighting, constraint, benchmark, cost, and execution assumptions.

Before execution, allocate immutable experiment, campaign, trial-family, and
trial identifiers. Retain:

- full configuration and parent/child lineage;
- code SHA, data manifest/hash, and environment;
- planned, running, completed, failed, invalid, aborted, and excluded states;
- output hashes and failure reasons;
- selection role and review outcome;
- promotion or rejection reason; and
- every protected-sample access.

The best result is uninterpretable when the number and dependence of prior
trials are unknown.

### Statistical evidence

The accepted protocol must match the sampling and dependence structure. The
program will add, in reviewed increments:

- mean IC, Rank IC, dispersion, ICIR, and sign hit rate;
- full quantile returns and monotonicity;
- multi-horizon factor decay;
- HAC/Newey-West inference for dependent or overlapping observations;
- block/bootstrap confidence intervals;
- permutation or placebo tests;
- FDR or another registered multiple-testing adjustment;
- Deflated Sharpe Ratio;
- PBO/CSCV or a reviewed practical alternative; and
- leave-one-stock and, after point-in-time classifications exist,
  leave-one-sector diagnostics.

No formal interpretation gate may imply these controls already exist.

## Sample Classification and Holdout Access

Use these labels precisely:

- `development`: available for implementation and design iteration;
- `validation`: available for registered selection within its trial budget;
- `historical_evaluation`: previously examined data used for retrospective
  evaluation;
- `pseudo_holdout`: a nominal holdout whose prior access or design influence
  cannot be ruled out;
- `holdout`: sealed data not used to choose formulas, parameters, costs, gates,
  or architecture; and
- `shadow` or `paper`: forward operational evidence, not a substitute for
  historical robustness.

A holdout exposure ledger must record actor, time, dataset/window, metrics or
artifacts accessed, purpose, and design impact. If pristine status cannot be
proved, downgrade the sample rather than asserting holdout independence.

The private EODHD workflow already calculated and reviewed split diagnostics
through 2026-06-26. Therefore 2025-05-01 through 2026-05-31 is not presumed
pristine and must be classified as historical evaluation or pseudo-holdout
unless an exposure audit proves a narrower claim. This statement records
access scope only; it does not disclose or interpret performance values.

## Evidence Objectives

Pre-register a multi-objective evidence framework appropriate to the layer.
Relevant dimensions include:

- out-of-sample net active return;
- Sharpe and Information Ratio with stated assumptions;
- maximum drawdown, downside risk, and CVaR;
- turnover, cost sensitivity, and capacity;
- concentration and benchmark, sector, beta, size, and style exposures;
- fold, subperiod, universe, and parameter-neighborhood stability;
- statistical uncertainty and multiple-testing-adjusted evidence;
- simplicity and economic rationale; and
- local-to-LEAN parity when that later research gate is accepted.

If a campaign uses "recall," it must define future winners before evaluation,
for example top-decile benchmark-adjusted forward returns. Report Precision@K,
Recall@K, NDCG, Rank IC, selected breadth, turnover, and net portfolio results
together. Recall alone is not an optimization objective.

## Candidate States

Every evaluated factor, strategy, or portfolio has exactly one state:

- `INVALID`
- `INCONCLUSIVE`
- `REJECTED`
- `DIAGNOSTIC_ONLY`
- `CONDITIONAL`
- `RESEARCH_PASS`
- `PORTFOLIO_PASS`
- `PAPER_CANDIDATE`
- `LIVE_CANDIDATE`

Use the lowest state supported by the completed gates. Do not call a diagnostic
"alpha," "profitable," "robust," or "ready" without the corresponding frozen,
reproducible evidence. Reproducibility alone does not establish validity.

## Staged Program

| Stage | Objective | Gate before advancing |
| --- | --- | --- |
| 0. Research charter reset | Reconcile objective, evidence layers, boundaries, roadmap, handoff, controller, and workflow Skill. | Documentation contracts and workflow checks pass; no research behavior changes. |
| 1. Purged and bounded splits | Add explicit split starts/ends, bounded tests, horizon-aware purge, optional embargo, label metadata, and boundary tests. | No label crosses a split; warm-up/down and window metadata are deterministic. |
| 2. Signal and execution timing | Freeze feature, availability, decision, execution, and return timestamps; resolve zero-lag policy. | Close-derived signals cannot receive ambiguous same-close fills. |
| 3. Point-in-time data methodology | Accept provider-agnostic provenance, universe, corporate-action, field, benchmark, missing-data, privacy, and exposure-ledger contracts. | Every required field is accepted before formal interpretation; no download is implied. |
| 4. Experiment and trial ledger | Allocate immutable IDs before execution and retain every state, hash, failure, review, and protected-sample access. | Completeness and append-only behavior pass deterministic tests. |
| 5. Statistical validation | Add descriptive, dependence-aware, bootstrap, placebo, multiplicity, DSR, PBO, and stability controls in design-first increments. | Synthetic/golden tests and a registered inference policy pass. |
| 6. Canonical factor registry | Register interpretable price/volume baselines first; admit fundamentals only after filing-availability support. | Source, formula, direction, fields, lag, parameters, fixtures, tests, limitations, and trial family are complete. |
| 7. WorldQuant batches | Add 5-10 formulas per reviewed data family after operator contracts are ready. | Formula transcription, source, parity, missing/warm-up, and timing tests pass; no strategy claim. |
| 8. Factor campaign runner | Run broad point-in-time single-factor campaigns across registered horizons and subgroups. | All trials and failures retained; multiplicity-adjusted promotion only. |
| 9. Strategy factory | Apply registered selection, holding, rebalance, buffer, and long-short policies to promoted factors. | Every variant counted; costs and execution frozen. |
| 10. Portfolio and risk engine | Add reviewed weighting, exposure, turnover, liquidity, volatility, concentration, and infeasibility contracts. | Drift-aware accounting identities and constraint tests pass. |
| 11. Frozen historical evaluation | Freeze candidates, rules, costs, metrics, thresholds, and trial policy before purged walk-forward evaluation. | No tuning on protected results; correct sample classification and complete access ledger. |
| 12. Independent reproduction | Reproduce promoted evidence from the frozen manifest through an independent reviewer/path. | Data, config, code, output, and metric parity pass. |
| 13. LEAN parity and paper candidate | Compare signals, holdings, trades, costs, and reconciliation for `PORTFOLIO_PASS` candidates only. | Candidate evidence only; paper runtime is outside project scope and remains governed by the `AGENTS.md` authority boundary. |

Controlled live execution is outside this charter and project scope. Candidate
states grant no authority. Any future system would require a separate repository
or package boundary, capital and loss limits, reconciliation, kill switches, and
operational review, with external actions governed only by `AGENTS.md`.

## Promotion and Stop Rules

Stop and issue a decision memo when:

- provenance, license, point-in-time membership, corporate-action semantics, or
  holdout exposure is unresolved;
- a formula, operator, timestamp, benchmark, cost, or statistical method is
  materially ambiguous;
- an unexpected research-validity test fails;
- a new production dependency or broad architecture decision is required;
- shorting lacks borrow evidence;
- private/public boundaries are unclear;
- a result could create an unsupported performance claim; or
- work would involve brokerage, orders, credentials, paper deployment, live
  capital, or owner-set risk limits.

Rejected and inconclusive evidence remains part of the record. A failed gate
does not invite tuning on the same protected sample.

## Repository and Research Responsibility Boundary

This repository owns research contracts, data validation, factor replication,
diagnostics, simulations, evidence, and frozen candidate artifacts. Any future
order-capable execution system should use a separately reviewed boundary so
research changes cannot access credentials or silently change operational
behavior.

Research responsibilities remain separated: the integration owner maintains
the canonical roadmap and handoff, read-only auditors may work in parallel,
and reviewers do not fix their own findings.

External-action authority is defined only by
[`AGENTS.md`](../AGENTS.md#authority-and-scope). GitHub review sequencing is
defined only by the controller's
[GitHub Review Lifecycle](codex_long_running_controller.md#github-review-lifecycle).

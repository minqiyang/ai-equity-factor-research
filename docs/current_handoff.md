# Current Handoff

Updated: 2026-07-26 for the Signal, Execution, and Metric Timing Contract.

## Canonical State

- Long-term evidence policy: `docs/research_program_charter.md`.
- Accepted Stage 1a design: `docs/purged_bounded_split_contract.md`.
- Accepted Stage 2a design:
  `docs/signal_execution_timing_contract.md`.
- Active roadmap: `docs/current_roadmap.md`.
- Short operational controller: `docs/codex_long_running_controller.md`.
- Verified starting `origin/main`: `202273b`, the protected merge of PR #160.
- Starting validation: 637 tests passed; Ruff, compilation, and exact-head
  GitHub CI passed.
- Stage 2a changes documentation, repo-map index tooling, and structure tests
  only. It does not change backtest behavior.
- Stage 2a branch validation has 638 passing tests plus Ruff, compilation,
  package-build, repo-map regeneration, diff, and independent read-only review
  evidence.
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

The accepted design and implementation require:

- six explicit inclusive boundaries for train, validation, and test;
- a hard `test_end` information cutoff even when later source rows exist;
- row-based label start/end metadata and complete interval ownership;
- horizon-aware purge in every window plus optional explicit embargo;
- raw split axes with purged/embargoed targets masked to `NaN`;
- separate feature warm-up, in-window label warm-down, gap, and ignored
  post-test metadata; and
- typed price/synthetic label derivations, consumer-level usable-pair counts,
  and deterministic raw asset/benchmark mutation-invariance tests.

The implementation in `src/features/validation.py` retains the exact source
index, constructs one deterministic ledger row per candidate, calculates only
eligible price labels, and rejects unmasked excluded targets at the
label-aware slicer. Consumer summaries separate structural eligibility,
asset-level target missingness, usable factor-label pairs, and realized
diagnostic coverage. A structurally usable split is still `INVALID` when every
configured factor diagnostic has zero valid dates.

All four current consumers now use the contract:

- the EODHD and committed local-fixture workflows use typed adjusted-close
  price labels and the same structural mask for assets and benchmark;
- the two synthetic split workflows use
  `synthetic_same_row_response`, horizon zero, and exact `[t, t]` intervals;
- retained unsplit diagnostics receive only the masked eligible-label union;
  and
- post-test asset and benchmark mutations, plus cross-edge asset mutations,
  cannot change the applicable upstream eligible labels or metric payloads in
  deterministic tests.

The four-row local fixture honestly reserves one feature warm-up row. Its
three one-row horizon-one windows therefore have zero eligible labels and stay
visible as `INVALID`; no cross-window label is borrowed.

## Stage 2 Timing Decision

The accepted Stage 2a policy is
`after_close_signal_next_observed_close_v1`:

- the full source index is `s[0..M]`, while the exact bounded accounting slice
  is `a[0..N]`; every scheduled execution row `a[j]` uses source signal
  `a[j-L]` and freezes the decision immediately after that signal is available;
- pre-anchor `s` rows may support feature computation but never satisfy
  execution lag or create a target;
- under daily rebalancing, a final signal stamped at `d0` is conservatively
  available strictly after `close[d0]`, and lag one executes its idealized
  frozen target at `close[d1]`;
- that target first earns the return from `close[d1]` to `close[d2]`, recorded
  on `d2`;
- row lag counts exact observed rows inside the bounded accounting slice, not
  calendar days or rebalance periods;
- close-derived lag must be a non-boolean integer at least one;
- prices and signals require exact axes and timezone compatibility;
- available signal values must be real, non-Boolean, and finite, with IEEE
  `NaN` as the sole unavailable-score sentinel;
- the decision-time target cannot be reranked or redistributed with the
  execution close;
- held incoming-return price endpoints and every intended nonzero execution
  leg require real, non-Boolean, finite, strictly positive prices without
  coercion or redistribution;
- explicit `evaluation_start` is a zero initialization anchor, and every
  period metric uses the same post-anchor dates through explicit
  `evaluation_end`;
- both evaluation bounds must be exact scalar timestamps on the source index;
  partial-date strings and implicit label slicing are invalid;
- the benchmark uses the same dates and remains cost-free;
- tracking error subtracts net strategy and benchmark returns only on
  `measured_return_dates`; the public helper retains its required zero benchmark
  anchor while a strategy-anchor sentinel proves exclusion;
- daily annualization is fixed at 252 observed sessions; and
- initial capital must be a real, non-Boolean, finite positive scalar; gross
  return and its multiplier are validated before drift/division/trades/costs,
  while net return, its multiplier, and the resulting equity candidate are
  validated after costs; direct metric equity is validated before
  annualization or drawdown; and
- a terminal row includes its incoming return and configured trade/cost but
  creates no invented future return.

The timing ledger covers the sorted de-duplicated union of the initialization
anchor and resolved scheduled rebalance dates. The anchor has no incoming
interval; a later insufficient-lag row records its all-cash incoming interval
but no execution or first-holding interval.

The model is idealized close-reset accounting, not order-fill, MOC auction,
capacity, brokerage, or LEAN evidence. Current Stage 1 one-row forward labels
and same-row synthetic responses remain diagnostic targets, not executable
strategy returns under this timing policy.

Stage 2a changes documentation, repo-map index tooling, and structure tests
only. It does not change backtest behavior.

`run_long_only_backtest()` still accepts `signal_lag_periods=0`, and basic
volatility/Sharpe still include the initialization row; these remain Stage 2b
gaps. Silent signal reindexing, execution-close target filtering, missing
explicit evaluation bounds, drawdown anchoring, and typed timing metadata are
also pending Stage 2b. Runtime pretrade/post-cost insolvency checks, strict
signal/incoming/execution-price validation, direct-equity/return validation,
and the explicit common-window tracking-error formula are likewise not yet
implemented.

## Verified Implementation Baseline

- Strict local CSV validation and metadata inventory; no downloader.
- Momentum, reversal, volatility, liquidity helpers, Alpha #009/#012,
  preprocessing, combination, and basic diagnostics.
- One long-only equal-weight ranking engine with drift-aware accounting,
  default one-row lag, signed trades, turnover, fixed costs/slippage, optional
  position clipping, residual cash, and benchmark accounting.
- Tracking error, holdings/concentration, and completed holding-episode metrics.
- Deterministic synthetic/fixture reports and a registry of existing JSON logs.
- Private-output-only EODHD diagnostics on a fixed cohort.
- Non-executing LEAN metadata/signal scaffold.

Do not infer a reusable strategy factory, point-in-time universe engine,
calibrated impact/capacity model, immutable all-trial ledger, statistical
validation package, LEAN runtime, or empirical factor/strategy validity.

## Audited Findings

Remaining high-priority methodology blockers:

1. The accepted timing contract is not implemented: after-close signals still
   permit `signal_lag_periods=0`, signals are silently reindexed, and
   execution-close price availability can change target membership.
2. Private test diagnostics were calculated and reviewed through 2026-06-26.
   The 2025-05-01 through 2026-05-31 interval is historical evaluation or
   pseudo-holdout evidence, not presumed pristine.
3. Static-universe, delisting, corporate-action, adjusted price/volume,
   provenance/license, and benchmark methodology gaps block formal real-data
   interpretation.

Stage 1 resolves the prior cross-split-label and unbounded-test defects in the
current consumers. Stage 2a resolves the design ambiguity only; runtime
zero-lag, target-freeze, evaluation-window, metric-anchor, benchmark-window,
capital-validity, and metadata enforcement remain open. Additional blockers
include incomplete trial retention, absent dependence/multiplicity/overfit
controls, and diagnostic-only cost/capacity assumptions. See
`docs/current_roadmap.md` for the prioritized list.

The 2026-07-11 conformance audit remains historical evidence at its audited
SHA. Its prior no-P1/P2 conclusion does not supersede these later findings.

## PR #148 Interaction

At the charter-stage verification, PR #148 was an independent Draft governance
PR from an older base that changed only `AGENTS.md`. It was not a predecessor
for PR #158, #159, or #160. Stage 2a neither edits `AGENTS.md` nor changes that
external PR or its policy.

## Next Safe Stage

After the Stage 2a PR is merged, begin only:

```text
Stage 2b - Signal, execution, and metric timing implementation.
```

Implement `docs/signal_execution_timing_contract.md` test-first. Enforce lag
types and bounds, exact axes, bounded evaluation anchors, decision-time target
freezing, common strategy/benchmark metric rows, initial-capital drawdown, and
typed timing metadata across every current caller. Enforce measured-date
tracking error, strict signal and price-leg inputs, pretrade gross solvency,
post-cost net/equity solvency, and direct metric equity/return validation
before any successful result or geometric metric. Regenerate only
deterministically affected synthetic evidence. Do not interpret historical
diagnostics, add data providers or factors, build a strategy factory, or start
LEAN work in Stage 2b.

## Freshness Checklist

Before continuing:

- fetch and compare `origin/main`;
- verify the previous required stage PR is merged;
- classify unrelated open drafts separately from predecessor gates;
- use a clean branch/worktree and preserve unrelated local changes;
- rerun focused and baseline validation; and
- reread this handoff and the canonical roadmap if the remote head changed.

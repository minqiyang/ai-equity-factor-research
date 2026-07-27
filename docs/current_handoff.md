# Current Handoff

Updated: 2026-07-26 for the Purged and Bounded Split Implementation.

## Canonical State

- Long-term evidence policy: `docs/research_program_charter.md`.
- Accepted Stage 1a design: `docs/purged_bounded_split_contract.md`.
- Active roadmap: `docs/current_roadmap.md`.
- Short operational controller: `docs/codex_long_running_controller.md`.
- Verified starting `origin/main`: `12e0e86`, the protected merge of PR #159.
- Starting validation: 595 tests passed; Ruff, compilation, and exact-head
  GitHub CI passed.
- Stage 1b branch validation currently has 637 passing tests plus Ruff,
  compilation, and package-build evidence.
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

1. After-close signals still permit `signal_lag_periods=0`, leaving same-close
   execution ambiguous.
2. Private test diagnostics were calculated and reviewed through 2026-06-26.
   The 2025-05-01 through 2026-05-31 interval is historical evaluation or
   pseudo-holdout evidence, not presumed pristine.
3. Static-universe, delisting, corporate-action, adjusted price/volume,
   provenance/license, and benchmark methodology gaps block formal real-data
   interpretation.

Stage 1 resolves the prior cross-split-label and unbounded-test defects in the
current consumers. Additional blockers include decision/execution/return
timestamp ambiguity, evaluation-window/metric-anchor inconsistencies,
incomplete trial retention, absent dependence/multiplicity/overfit controls,
and diagnostic-only cost/capacity assumptions. See `docs/current_roadmap.md`
for the prioritized list.

The 2026-07-11 conformance audit remains historical evidence at its audited
SHA. Its prior no-P1/P2 conclusion does not supersede these later findings.

## PR #148 Interaction

At the charter-stage verification, PR #148 was an independent Draft governance
PR from an older base that changed only `AGENTS.md`. It was not a predecessor
for PR #158 or #159. This Stage 1b branch also does not edit `AGENTS.md` or
alter that external PR.

## Next Safe Stage

After the Stage 1b PR is merged, begin only:

```text
Stage 2a - Signal and execution timing contract.
```

Freeze feature, signal-availability, decision, execution, and return
measurement timestamps before changing backtest behavior. Resolve the
close-derived zero-lag policy and metric-window anchors with hand-calculated
tests. Do not interpret historical diagnostics, add data providers, expand the
factor catalog, build a strategy factory, or start LEAN work in Stage 2a.

## Freshness Checklist

Before continuing:

- fetch and compare `origin/main`;
- verify the previous required stage PR is merged;
- classify unrelated open drafts separately from predecessor gates;
- use a clean branch/worktree and preserve unrelated local changes;
- rerun focused and baseline validation; and
- reread this handoff and the canonical roadmap if the remote head changed.

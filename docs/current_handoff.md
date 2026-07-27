# Current Handoff

Updated: 2026-07-26 for the Purged and Bounded Split Contract.

## Canonical State

- Long-term evidence policy: `docs/research_program_charter.md`.
- Accepted Stage 1a design: `docs/purged_bounded_split_contract.md`.
- Active roadmap: `docs/current_roadmap.md`.
- Short operational controller: `docs/codex_long_running_controller.md`.
- Verified starting `origin/main`: `57f3db3`, the protected merge of PR #158.
- Starting validation: 594 tests passed; Ruff, compilation, package build, and
  exact-head GitHub CI passed.
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

## Stage 1a Split Contract Decision

The accepted design requires:

- six explicit inclusive boundaries for train, validation, and test;
- a hard `test_end` information cutoff even when later source rows exist;
- row-based label start/end metadata and complete interval ownership;
- horizon-aware purge in every window plus optional explicit embargo;
- raw split axes with purged/embargoed targets masked to `NaN`;
- separate feature warm-up, in-window label warm-down, gap, and ignored
  post-test metadata; and
- typed price/synthetic label derivations, consumer-level usable-pair counts,
  and deterministic raw asset/benchmark mutation-invariance tests.

The contract preserves zero-eligible windows as visible `INVALID` evidence
rather than borrowing cross-boundary labels. It does not implement the fix.
Current future-return workflows remain diagnostic-only until Stage 1b passes.

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

High-priority methodology blockers:

1. Forward-return labels can cross train/validation/test edges because returns
   are computed before split slicing.
2. The split helper rejects a bounded test end when later data exists.
3. After-close signals still permit `signal_lag_periods=0`, leaving same-close
   execution ambiguous.
4. Private test diagnostics were calculated and reviewed through 2026-06-26.
   The 2025-05-01 through 2026-05-31 interval is historical evaluation or
   pseudo-holdout evidence, not presumed pristine.
5. Static-universe, delisting, corporate-action, adjusted price/volume,
   provenance/license, and benchmark methodology gaps block formal real-data
   interpretation.

Additional blockers include evaluation-window/metric-anchor inconsistencies,
incomplete trial retention, absent dependence/multiplicity/overfit controls,
and diagnostic-only cost/capacity assumptions. See
`docs/current_roadmap.md` for the prioritized list.

The 2026-07-11 conformance audit remains historical evidence at its audited
SHA. Its prior no-P1/P2 conclusion does not supersede these later findings.

## PR #148 Interaction

At the charter-stage verification, PR #148 was an independent Draft governance
PR from an older base that changed only `AGENTS.md`. It was not a predecessor
for PR #158. This Stage 1a branch also does not edit `AGENTS.md` or alter that
external PR.

## Next Safe Stage

After the Stage 1a PR is merged, begin only:

```text
Stage 1b - Purged and bounded sample-split implementation.
```

Implement `docs/purged_bounded_split_contract.md` test-first. Migrate every
current future-return consumer, preserve masked exclusions and exact metadata,
and prove later-price invariance before regenerating any affected synthetic
evidence.

Do not interpret historical diagnostics, add data providers, expand the factor
catalog, resolve zero-lag execution, build a strategy factory, or start LEAN
work in Stage 1b.

## Freshness Checklist

Before continuing:

- fetch and compare `origin/main`;
- verify the previous required stage PR is merged;
- classify unrelated open drafts separately from predecessor gates;
- use a clean branch/worktree and preserve unrelated local changes;
- rerun focused and baseline validation; and
- reread this handoff and the canonical roadmap if the remote head changed.

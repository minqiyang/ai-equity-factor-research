# Current Handoff

Updated: 2026-07-27 for the Point-in-Time Data Methodology Contract.

## Canonical State

- Long-term evidence policy: `docs/research_program_charter.md`.
- Accepted Stage 1 split authority: `docs/purged_bounded_split_contract.md`.
- Accepted Stage 2 timing authority:
  `docs/signal_execution_timing_contract.md`.
- Proposed Stage 3 data authority:
  `docs/point_in_time_data_methodology_contract.md`.
- Active roadmap: `docs/current_roadmap.md`.
- Short operational controller: `docs/codex_long_running_controller.md`.
- Verified starting `origin/main`: `8a352d3`, the protected merge of PR #162.
- Starting validation: 849 tests passed with two platform-conditional
  wide-`longdouble` skips; compilation and exact merge-head GitHub CI passed.
- Stage 1 split isolation and Stage 2 signal/execution timing are complete on
  protected main. Stage 3 defines methodology only; it does not accept a
  provider, dataset, license, universe, field, benchmark, or historical claim.
- Stage 3 post-review-fix local validation has 854 passing tests with the same two
  platform-conditional skips. Ruff, compilation, build, Skill, repo-map, and
  privacy/Unicode/diff gates passed. The digest and open-interval fix heads each
  passed GitHub CI before their required current-head reviews. The latest
  review found and drove consistent diagnostic-versus-formal dataset-review
  scope across the readiness Skill, audit, experiment log, and local-CSV forms.
  Two independent read-only re-reviewers found no remaining actionable P1/P2.
  New-fix-head CI and the required current-head review remain pending.
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

`docs/purged_bounded_split_contract.md` defines six explicit inclusive bounds,
hard bounded-test semantics, complete label-interval ownership,
horizon-aware purge, optional embargo, raw-axis masking, warm-up/down metadata,
and typed consumer coverage. `src/features/validation.py` implements the
contract for all four current consumers. Deterministic mutation tests prove
that post-test or cross-edge values cannot change earlier eligible labels or
diagnostics; zero-eligible and metric-empty windows remain visible as
`INVALID`.

## Stage 2 Timing Decision

The implemented policy is
`after_close_signal_next_observed_close_v1`. A close-derived signal becomes
available after its stamped close, uses a non-Boolean observed-row lag of at
least one inside an exact bounded accounting window, executes an idealized
frozen target at the next supported close, and first earns the following
close-to-close return.

`docs/signal_execution_timing_contract.md` is the detailed authority. The
runtime requires exact source axes, bounds, typed source provenance, strict
signal/price/capital values, decision-time target freezing, ordered
drift/trade/cost accounting, a zero initialization anchor, common measured
metric rows, exact benchmark dates, terminal-row accounting, and typed timing
metadata/ledger evidence. This is idealized close-reset software behavior, not
order-fill, capacity, real-data, brokerage, or LEAN evidence.

Stage 2b now requires explicit exact evaluation bounds and exact full-source
price/signal axes plus exact source provenance whose caller-declared baseline
is captured before later mutation.

## Stage 3 Data Methodology Decision

`docs/point_in_time_data_methodology_contract.md` separates:

1. `methodology_contract_accepted`;
2. `dataset_manifest_reviewed`; and
3. `formal_interpretation_eligible`.

This stage can establish only the first gate. The contract requires immutable
data identity, canonicalization, environment, and lineage; evidence-backed
license/entitlement; an exact-version non-self-issued dataset-review decision;
bitemporal availability and revisions; permanent security/listing identity;
historical membership; delistings/corporate actions and terminal value; field
semantics; missing/stale states; calendar/timezone; benchmark/risk-free policy;
a private full manifest with safe public projection; and holdout-exposure
downgrade rules.

The private 2025-05-01 through 2026-05-31 diagnostic interval is confirmed
`historical_evaluation`, not a pristine holdout. Stage 4 must implement the
append-only trial/access ledger. No current dataset becomes `formal_ready`
through this documentation contract.

## Verified Implementation Baseline

- Strict local CSV validation and metadata inventory; no downloader.
- Momentum, reversal, volatility, liquidity helpers, Alpha #009/#012,
  preprocessing, combination, and basic diagnostics.
- One bounded long-only equal-weight ranking engine with enforced nonzero
  observed-row lag, frozen targets, drift-aware accounting, signed trades,
  turnover, fixed costs/slippage, optional position clipping, residual cash,
  exact benchmark accounting, and a typed timing ledger.
- Common-window return/benchmark metrics, initial-capital drawdown, tracking
  error, holdings/concentration, and completed holding-episode metrics.
- Deterministic synthetic/fixture reports and a registry of existing JSON logs.
- Private-output-only EODHD diagnostics on a fixed cohort.
- Non-executing LEAN metadata/signal scaffold.

Do not infer a reusable strategy factory, point-in-time universe engine,
calibrated impact/capacity model, immutable all-trial ledger, statistical
validation package, LEAN runtime, or empirical factor/strategy validity.

## Audited Findings

Remaining high-priority methodology blockers:

1. Private diagnostics were calculated and reviewed through 2026-06-26. The
   2025-05-01 through 2026-05-31 interval is confirmed
   `historical_evaluation` and cannot be upgraded to a holdout.
2. Static-universe, delisting, corporate-action, adjusted price/volume,
   provenance/license, and benchmark methodology gaps block formal real-data
   interpretation.

Stage 1 resolves the prior cross-split-label and unbounded-test defects in the
current consumers. Stage 2 resolves the close-only runtime timing, target,
evaluation-window, metric-anchor, benchmark-window, capital-validity, and
metadata contract. Stage 3 defines the missing data-methodology contract but
does not verify a dataset. Additional blockers include incomplete trial
retention, absent dependence/multiplicity/overfit controls, and diagnostic-only
cost/capacity assumptions. See `docs/current_roadmap.md` for the prioritized
list.

The 2026-07-11 conformance audit remains historical evidence at its audited
SHA. Its prior no-P1/P2 conclusion does not supersede these later findings.

## PR #148 Interaction

At the charter-stage verification, PR #148 was an independent Draft governance
PR from an older base that changed only `AGENTS.md`. It was not a predecessor
for PRs #158-#162. Stage 3 does not edit `AGENTS.md`, merge/close that draft,
or overwrite its policy.

## Next Safe Stage

After the Stage 3 methodology PR is protected-merged and exact merge-head CI
succeeds, begin:

```text
Stage 4 - Experiment and trial ledger.
```

Allocate immutable experiment, campaign, trial-family, trial, sample, and
access identifiers before execution/access; retain attempted, failed, invalid,
aborted, and excluded states; preserve config/code/data/output hashes and
review decisions; and enforce append-only protected-sample exposure records.
Do not run real-data campaigns or interpret historical diagnostics while the
Stage 4 and later statistical gates remain incomplete.

## Freshness Checklist

Before continuing:

- fetch and compare `origin/main`;
- verify the previous required stage PR is merged;
- classify unrelated open drafts separately from predecessor gates;
- use a clean branch/worktree and preserve unrelated local changes;
- rerun focused and baseline validation; and
- reread this handoff and the canonical roadmap if the remote head changed.

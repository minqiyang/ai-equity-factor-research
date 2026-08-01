# EODHD Historical S&P 500 Diagnostic Campaign

Status: owner-approved scope and protocol reset; no dataset accepted and no
performance calculation authorized by this document.

Decision date: 2026-07-29.

Canonical machine-readable protocol:
`docs/preregistrations/eodhd_sp500_three_factor_diagnostic_v1.yaml`.

Canonical semantic-trial inventory:
`docs/preregistrations/eodhd_sp500_three_factor_trial_inventory_v1.json`.

## Decision

The project no longer requires completion of the 37-event payload registry
before bounded empirical diagnostic work. The accepted 37-event vocabulary and
immutable registry releases remain preserved as `full_ledger_profile_v1`.
Completing that profile is optional future hardening, not the active delivery
queue.

Work proceeds on two tracks:

1. **Track A - diagnostic research now.** Acquire and review a private EODHD
   historical S&P 500 panel, then run exactly the preregistered three-factor,
   14-trial campaign with purged bounded evaluation, baselines, cost
   sensitivity, and a content-addressed repository-external evidence bundle.
2. **Track B - formal evidence infrastructure.** After Track A closes, design
   and implement a minimal stateful runtime covering 8-12 conceptual event
   families. It is required before prospective performance access or formal
   evidence promotion, but it does not block Track A.

Track A's evidence state is permanently `DIAGNOSTIC_ONLY` and it can produce
only a diagnostic classification. It cannot produce
`RESEARCH_PASS`, an alpha-validation claim, a profitability claim, or any
paper/live/trading-readiness claim.

## Frozen Track A Scope

### Provider and sample

- Provider: EODHD.
- Universe: historical S&P 500 membership effective at each signal cutoff.
- Candidate raw coverage: 2014-01-01 through a later blinded dataset-acceptance
  cutoff.
- Primary quality window: 2018-01-01 onward.
- Separate descriptive labels:
  `coverage_all_available`, `coverage_primary_quality_window`, and
  `coverage_pre_2018_limited`.
- Every existing EODHD observation used by this campaign is
  `historical_evaluation`, `diagnostic_only`, and not a pristine holdout.
- The previously accessed 2025-05-01 through 2026-05-31 interval is permanently
  `historical_evaluation`.

Claims are limited to this provider, this reviewed membership reconstruction,
this period, and historical S&P 500 members. Ticker is not treated as a
permanent security identifier.

### Factors

The search family contains exactly:

- `MOM_12_1`:
  `adjusted_close[t-21] / adjusted_close[t-252] - 1`.
- `REV_1M`:
  `-(adjusted_close[t] / adjusted_close[t-21] - 1)`.
- `LOW_VOL_3M`: the negative sample standard deviation (`ddof=1`) of the 63
  one-day adjusted-close returns ending at `t`. Under the runner's Python
  half-open slice convention the exact return slice is `[t-62:t+1]`, which
  includes `t` and requires exactly 64 price anchors.

All factors are oriented so higher is better. No formula, direction, lookback,
cost case, factor, model, liquidity screen, price screen, or parameter variant
may be added after the protocol freeze.

### Calendar, membership, and return timing

- Signal date: the last common XNYS session close of each calendar month.
- Signal availability: after that close.
- Execution: the next common XNYS session close.
- Evaluation: 21 common-calendar close-to-close returns beginning at the
  execution close. With signal close `t` and execution close `e=t+1`, the
  endpoint is common-calendar close `e+21`.
- A security-specific later observation must never substitute for a missing
  common-calendar execution or endpoint.
- A label is valid only when its complete execution-to-end interval lies
  inside the bounded evaluation fold. On the signal axis this label ends at
  `t+22`, so `horizon_purge_signal_axis_rows=22`.
- The label kind is `execution_anchored_forward_return_v1`, with
  `label_start=e=t+1` and `label_end=e+21=t+22`. PR 3 must implement this
  execution-anchored interval explicitly; it must not reuse the current
  signal-anchored `price_forward_return` helper with horizon 21.
- `embargo_rows=0` is frozen because the factors and trials are fixed and no
  model fitting, tuning, or adaptive selection occurs. Any later adaptive use
  requires a new preregistration.
- Primary reporting uses calendar-year walk-forward evaluation folds beginning
  in 2018, plus one final bounded partial-year fold when the frozen cutoff is
  not year-end. Earlier rows may supply factor warm-up only. A fold uses no
  later data and retains all purged, missing, and invalid counts.

Membership must be effective and known by the signal cutoff. Provider date-only
boundary semantics may not be guessed: unresolved addition/removal boundary
rows are invalid until the blinded dataset review records an evidence-backed
inclusive/exclusive rule. Current-constituent substitution and future
membership are forbidden.

### Price fields and terminal events

Factor inputs and diagnostic forward returns use the reviewed EODHD
dividend-and-split-adjusted close return proxy. The campaign must not call it an
exact total-return index until the dataset review verifies the provider
semantics and corporate-action reconciliation.

Raw OHLC, splits, dividends, and volume may be retained privately for audit
only while the active subscription terms or written permission allow that
retention. Volume, liquidity, capacity, and share-level execution are outside
the campaign. Raw close multiplied by provider split-adjusted volume is
forbidden.

No missing execution or terminal endpoint is silently dropped, filled, or
replaced. Delisting, cash acquisition, stock consideration, merger, spinoff,
halt, final distribution, and symbol-successor treatment require explicit
dataset-review evidence. An unresolved return-relevant identity or terminal
event blocks the affected row and is counted. The blinded dataset-acceptance
record must freeze materiality and campaign-invalidation thresholds before
performance access.

### Eligibility and diagnostics

Eligibility is factor-specific and evaluated only with information known at
the signal cutoff `t`. Decision-time eligibility requires:

- point-in-time membership effective and known at `t`;
- listing lineage resolved through `t`;
- complete factor history through `t`;
- a finite factor value at `t`;
- corporate actions announced or effective through `t` treated under the
  blinded accepted policy; and
- at least 100 decision-time eligible securities for a factor-month.

Execution-price availability, forward-endpoint availability, later halts,
later delistings, and every other post-`t` field are forbidden inputs to
decision-time eligibility. At `t`, the runner freezes the ordered eligible
listing-key set, factor ranks, decile assignments, long-only target, and
equal-weight matched-benchmark membership. Mutating any post-`t` availability
or return field must leave those frozen objects byte-identical.

Outcome observation is a separate gate. A factor-month is retained as invalid
if any decision-time eligible listing lacks an accepted finite
execution-to-endpoint return after the frozen lineage and terminal-event rules
are applied; the listing is not removed from ranks, deciles, or the matched
benchmark. A selected strategy listing without a finite accepted execution
price invalidates the affected strategy trial, and a later missing held return
does the same. No substitute listing, renormalization over future survivors,
zero fill, or security-specific next observation is allowed.

A factor-month below the decision-time floor is retained as invalid. No fill
or silent exclusion is allowed. Rank IC uses cross-sectional Spearman
correlation: average ranks for ties followed by Pearson correlation of the two
rank vectors. It requires at least 10 distinct finite factor values and at
least 2 distinct finite forward returns; otherwise the factor-month is
invalid. No winsorization, normalization, or sign reversal is applied.

Deciles use this exact procedure:

1. Sort finite factor values from higher to lower; break equal factor values by
   the canonical listing-lineage key in ascending byte order.
2. Let `base = N // 10` and `remainder = N % 10`.
3. In high-to-low order, the first `remainder` deciles receive `base + 1`
   securities and the rest receive `base`. The first chunk is `D10` and the
   last is `D1`.

Report decile means in `D1` through `D10` order. Adjacent monotonicity values
are `mean(D{k+1}) - mean(D{k})` for `k=1..9`; monotonicity share is the fraction
of those nine differences that are nonnegative, and `fully_monotone` is true
only when all nine are nonnegative. The diagnostic spread is
`mean(D10) - mean(D1)`.

The canonical listing-lineage byte encoding is
`listing_lineage_key_bytes_v1`. It is:

1. the ASCII magic bytes `listing_lineage_key_v1` followed by one zero byte;
2. `exchange` normalized to Unicode NFC, encoded as UTF-8, and prefixed by its
   unsigned 32-bit big-endian byte length;
3. `ticker` encoded by the same NFC/UTF-8/length rule;
4. `effective_from` as exactly ten ASCII bytes in strict Gregorian
   `YYYY-MM-DD` form; and
5. one zero byte for a null/open `effective_to`, or one byte with value 1
   followed by its strict ten-byte ASCII `YYYY-MM-DD` value.

Exchange and ticker must be nonempty Unicode scalar strings and must not
contain control characters. Dates must round-trip through strict Gregorian
date parsing. There is no trimming, case folding, locale collation, or
delimiter-based serialization. Ascending byte order means lexicographic order
over unsigned bytes. This same encoding controls factor-value ties, factor
turnover alignment, and random-baseline input order.

The key is frozen when the listing first becomes decision-time eligible.
`effective_to` means the lineage endpoint known at that first eligibility
cutoff; it is null when no endpoint was then known. A later halt, removal,
symbol change, delisting, or provider backfill cannot rewrite the frozen key.
The subsequently observed actual endpoint remains separate interval/audit
metadata and is tested by the post-`t` mutation oracle.

Factor turnover is target-to-target top-decile turnover, not a cost model:
align the union of canonical listing keys, assign zero to absent or nonselected
names, and calculate `sum(abs(w_t - w_previous))`. Every scheduled signal
month freezes one decision-time factor target: either the ranked top-decile
target or the zero target caused by one of the three enumerated decision-time
conditions below. The first scheduled frozen target inside the bounded
evaluation schedule is `not_applicable`.

For every later scheduled month, `w_previous` is the immediately preceding
scheduled frozen decision-time target, including an intervening zero target.
This predecessor is retained even when that preceding month later becomes
outcome-invalid. Forward-return, endpoint, or comparison validity may flag the
corresponding factor-month outcome invalid, but may not delete its frozen
target, make turnover skip back to the last outcome-valid month, or change any
later turnover. Factor turnover remains a decision-time diagnostic with the
outcome-invalid flag retained separately. No drifted holdings enter this
factor diagnostic.

Each factor reports Rank IC, the ten-decile curve, top-minus-bottom diagnostic
spread, adjacent-decile monotonicity, factor turnover, coverage, invalid
counts, yearly results, leave-one-year-out sensitivity, and contribution
summaries. Top-minus-bottom is not an executable short strategy.

Descriptive Rank IC mean, median, sample standard deviation, and ICIR use all
valid months for that factor. The confirmatory mean, interval, p-value, and Holm
decision use only the common complete-case monthly table defined below. Both
sample counts are reported and are never conflated.

### Strategy diagnostics and benchmarks

For each factor, the simulated strategy is long-only, equal-weight, top
decile. The fixed execution-to-21-row episode remains a factor/decile
diagnostic only. It is never compounded into a strategy equity curve.

The strategy uses one continuous idealized holdings path. A target formed at
signal close `t` resets at execution close `e`; it then earns common-calendar
close-to-close returns after `e` through the next monthly execution close. The
next execution resets the target again. The final included target must have a
later scheduled execution endpoint inside the accepted cutoff; otherwise that
target is retained as invalid for continuous-strategy metrics. Daily holdings,
returns, costs, and benchmarks use the same common calendar.

At each execution, strategy turnover is the undivided sum of absolute changes
from drifted pre-trade weights to the new target. The initial cash-to-target
deployment has turnover 1.0, a complete invested-name switch has turnover 2.0,
and no terminal liquidation is invented after the final measured return.

Exactly three decision-time conditions make a factor rebalance invalid and
produce a zero target at the next execution:

1. fewer than 100 securities remain after the frozen signal-time eligibility
   rules are applied;
2. fewer than 10 distinct finite factor values remain; or
3. the eligible set contains duplicate canonical
   `listing_lineage_key_bytes_v1` values, so a unique target cannot be formed.

No other condition produces a zero target. A later missing execution-to-
endpoint diagnostic outcome for an unselected listing may invalidate the
factor-month or benchmark comparison, but it cannot alter the frozen strategy
target, create a liquidation, or change the cash path. A missing selected
execution price or unresolved held-security return invalidates the affected
strategy trial; it does not retroactively replace the frozen target with zero
and is never filled or repaired through an alternate path. The zero target's
resulting liquidation turnover and non-interest-bearing cash return are
retained only for the three decision-time conditions above.

The primary benchmark is the continuous equal-weight decision-time eligible
universe frozen at the matching factor signal close under the same
execution/reset/cost-free calendar. Its membership is not recomputed from
future execution or endpoint availability. The secondary benchmark is an
EODHD adjusted-close SPY return proxy over the identical daily intervals.
Missing constituent execution or held returns, or missing SPY benchmark dates,
invalidate the comparison; they do not change benchmark membership and are not
filled.

Each baseline semantic trial emits an exact output matrix with rows
`MOM_12_1`, `REV_1M`, and `LOW_VOL_3M` and columns
`episode_21_row_return` and `continuous_daily_return`. These factor-matched
series remain one frozen baseline trial each and do not create extra hypotheses
or semantic trials.

For the random-rank baseline, derive a separate RNG for each factor/month as
follows: SHA-256 the ASCII string
`random_rank_v1|20260729|<factor_id>|<YYYY-MM-DD>`, interpret the first 16 hex
digits as an unsigned integer seed, initialize NumPy `PCG64DXSM`, place
eligible listing keys in ascending byte order, and apply one permutation. No
global mutable RNG stream or iteration-order dependence is allowed.

Cost cases are exactly 0, 10, and 25 bps. Ten bps is primary. Zero bps is
diagnostic only. Each scalar is an all-in fixed-bps diagnostic execution-cost
proxy that bundles commission, bid-ask spread, slippage, exchange/regulatory
fees, and other ordinary execution friction. No separate commission, spread,
slippage, fee, tax, borrow, market-impact, capacity, or participation-rate
charge may be added. This is not a calibrated fill or capacity model.

Strategy cost is `turnover * bps / 10000`, deducted once from portfolio equity
at the execution close; the first market return begins after that close. The
hand-calculated fixtures are:

| Turnover | 0 bps | 10 bps | 25 bps |
| ---: | ---: | ---: | ---: |
| 0.4 | 0.0 | 0.0004 | 0.0010 |
| 1.0 | 0.0 | 0.0010 | 0.0025 |
| 2.0 | 0.0 | 0.0020 | 0.0050 |

## Frozen Statistical Minimum

The primary hypothesis family contains only the three one-sided factor
direction tests:

```text
H0: mean monthly Rank IC <= 0
H1: mean monthly Rank IC > 0
```

Holm controls familywise error at 0.05 across those three p-values. Strategy,
cost, benchmark, decile, yearly, and leave-one-year-out outputs are descriptive
and do not form additional discovery hypotheses.

Holm sorts by raw p-value, with factor order `MOM_12_1`, `REV_1M`,
`LOW_VOL_3M` as the deterministic tie breaker. The sequential thresholds are
`0.05/3`, `0.05/2`, and `0.05`; testing stops at the first non-rejection.
Adjusted sorted p-values are the running maximum of
`(3-k+1) * p_sorted[k]`, capped at 1, then mapped back to factor order.

The dependence-aware method applies to the three primary mean Rank IC effects.
It is an overlapping, non-circular moving-block bootstrap over a common
complete-case monthly Rank IC table:

- block length: 6 monthly records;
- replicates: 20,000;
- minimum valid monthly records for primary inference: 60;
- random baseline seed: 20260729;
- bootstrap seed: 20260730;
- generator: NumPy `PCG64DXSM`;
- percentile quantile method: NumPy `linear`;
- a record is included only when all three factor Rank IC values are valid on
  that signal date; factor-specific non-complete records remain visible in
  coverage but do not enter any of the three primary tests;
- order records chronologically and split them into maximal contiguous segments
  at every fold boundary, purged month, invalid or missing month, or
  leave-one-year-out gap;
- compute each factor's observed mean across all retained records; the null
  table subtracts that factor mean from every value;
- for each replicate, process segments in chronological order; for a segment
  of length `n`, set `L=min(6,n)`, enumerate overlapping non-circular block
  starts `0..n-L`, draw `ceil(n/L)` starts uniformly with replacement,
  concatenate the selected blocks, and truncate to the first `n` rows;
- use identical block-start draws for all three columns, concatenate the
  resampled segments, and compute the unweighted mean across all retained rows,
  so a fold's weight equals its retained complete-case month count;
- consume RNG draws in replicate-major, then chronological-segment order;
- primary one-sided p-value is
  `(1 + count(null_bootstrap_mean >= observed_mean)) / 20001`; and
- uncentered resamples provide the 95% two-sided percentile interval.

The run manifest records Python, NumPy, calendar, and ordered signal-index
identities. Mean, median, sample standard deviation, and monthly ICIR
(`mean / std`, `ddof=1`) are reported. Annualized ICIR, if shown, is labelled
and uses `sqrt(12)`.

For the continuous daily strategy path:

- annualized return:
  `(product(1 + r_d)) ** (252 / valid_daily_returns) - 1`;
- annualized volatility: daily sample standard deviation times `sqrt(252)`;
- Sharpe-style metric: mean 10-bps net daily return divided by its daily sample
  standard deviation, times `sqrt(252)`, with fixed cash rate zero; and
- maximum drawdown uses the daily net equity curve anchored at 1.0.

Gross and net cumulative returns are the product of their respective daily
return paths minus one. Daily active return is strategy return minus the
cost-free matched-benchmark return. Annualized active return is strategy
annualized geometric return minus benchmark annualized geometric return. Cost
drag is gross annualized return minus net annualized return, with total
execution cost also reported separately.

Year contribution to mean Rank IC is `n_year * mean_ic_year / N` and sums to
the full-sample mean. Security gross contribution on daily return `d` is
`pre_return_weight[i,d] * security_return[i,d]`; security cost contribution at
an execution is `-(bps / 10000) * abs(delta_weight[i])`. Aggregate these
arithmetic daily contributions by security and calendar year. They sum to the
corresponding daily gross return and execution cost series, not to compounded
annual return. Rank IC has no additive per-security contribution claim.

Every yearly and leave-one-year-out Rank IC value used by the final-state
robustness predicate comes exclusively from the primary common complete-case
monthly Rank IC table used by all three factor tests. A factor's larger
all-valid-month table remains descriptive and is forbidden for final-state
robustness.

Yearly means group common-case records by signal-date calendar year. The
outcome-independent required-year set is frozen before performance access as
every calendar year containing at least one scheduled primary-evaluation
signal whose complete execution-to-end label lies inside the accepted bounds.
The positive-year fraction denominator is every required year; its numerator
is the number of required years whose common-case mean Rank IC is strictly
positive for that factor. Every required year must contain at least one
common-case record. A missing required-year record set or an exact-zero mean
makes `robustness_supported(f)` false and may not be removed from the
denominator.

Leave-one-year-out is descriptive only. Factor inference drops every label
whose execution-to-end interval intersects the omitted year and reuses the
fixed bootstrap rules without another Holm family. Continuous strategy
sensitivity treats the pre-omission and post-omission portions as separate
cash-started paths with no holdings or cost bridge across the gap; pooled daily
statistics concatenate the two return segments, and maximum drawdown is the
larger segment drawdown.

For final-state robustness, every required year is omitted exactly once from
the same primary common-case source table. If no common-case records remain
after an omission, that omission fails robustness. Otherwise the remaining
unweighted factor mean must be strictly positive. Factor-specific all-valid
rows never enter this predicate.

The Sharpe-style item must be labelled `zero_cash_rate_sharpe_style`, is
diagnostic only, and is not used for factor discovery. No bootstrap interval is
claimed for strategy metrics in this minimum campaign.

## Exact Trial Inventory

The immutable semantic-trial count is 14:

1. equal-weight eligible-universe baseline;
2. fixed-seed random-rank top-decile baseline;
3. `MOM_12_1` factor diagnostics;
4. `REV_1M` factor diagnostics;
5. `LOW_VOL_3M` factor diagnostics;
6-8. `MOM_12_1` at 0, 10, and 25 bps;
9-11. `REV_1M` at 0, 10, and 25 bps;
12-14. `LOW_VOL_3M` at 0, 10, and 25 bps.

An exact technical rerun is an attempt of the same semantic trial. It does not
increase the inventory. Every configured outcome, failure, invalid run, abort,
and not-produced artifact remains visible.

## Freeze Sequence

The protocol must not embed a hash of itself. Freeze uses detached records:

1. **Protocol freeze (this stage):** hash the exact preregistration and trial
   inventory after merge. This freezes factors, directions, trial semantics,
   timing, costs, metrics, inference, seeds, and diagnostic-only claims.
2. **Blinded dataset-acceptance freeze (private gate and PR 2):** bind the
   accepted cutoff, full private manifest hash, safe public projection hash,
   calendar version, lineage/terminal rules, exclusions, coverage thresholds,
   and dataset-review decision. Dataset-quality review remains blind to factor,
   portfolio, and cumulative performance.
3. **Detached run binding (after PR 3 merge and before the first result-bearing
   job):** bind the protected runner code SHA, exact configuration, environment
   identity, protocol hash, inventory hash, and accepted dataset-record hash.

No result-bearing job may run before the detached run binding is complete.

## Entitlement, Retention, and Publication Gate

The current EOD Historical Data - All World plan does not prove access to
historical index membership. A private capability probe must separately record
whether `GSPC.INDX` `HistoricalTickerComponents`, dated historical snapshots,
or an S&P historical-constituents marketplace entitlement is available. Codex
must not purchase any entitlement.

Before expanded retrieval, durable retention, or public derived output, obtain
written permission covering:

- frozen-snapshot retention after cancellation;
- public noncommercial GitHub use;
- aggregate statistics and charts;
- hashes, row counts, and non-sensitive metadata; and
- deletion obligations for raw, normalized, cached, backup, and derived
  artifacts.

Until written permission exists, public repository content is limited to
protocol, schema, validator, and non-provider-authored methodology material.
It contains no derived projection values, hashes, row/security/date counts,
raw rows, ticker lists, private paths, provider responses, or performance
values.

## Track A Evidence

The private bundle is repository-external and contains the artifacts listed in
the machine-readable preregistration. `bundle_manifest.json` lists and verifies
the child artifacts but does not hash itself. A detached root record binds the
bundle-manifest hash, code, configuration, data manifest, semantic-trial
count, attempt count, per-trial status, environment, and final classification.

The required preregistration child is named
`eodhd_sp500_three_factor_diagnostic_v1.yaml` and is an exact byte-for-byte copy
of `docs/preregistrations/eodhd_sp500_three_factor_diagnostic_v1.yaml` at the
protocol-freeze commit. Its child SHA-256 must equal the detached
protocol-freeze SHA-256. A derived `preregistration.json` may be retained only
as a non-authoritative convenience artifact; it cannot replace or satisfy the
exact-YAML child requirement.

The required `trial_inventory.json` child is likewise an exact byte-for-byte
copy of
`docs/preregistrations/eodhd_sp500_three_factor_trial_inventory_v1.json` at the
protocol-freeze commit. Its child SHA-256 must equal the detached trial-
inventory freeze SHA-256. A parsed, reordered, normalized, or field-modified
inventory cannot satisfy this requirement even when its own child hash is
listed in `bundle_manifest.json`.

Final-state assignment is an ordered, mutually exclusive, exhaustive decision
tree. Evaluate it in this order:

1. `INVALID_DIAGNOSTIC` if any hard-validity gate fails: protocol or detached
   binding preceded by result exposure; dataset acceptance other than
   `DIAGNOSTIC_READY`; a hash, inventory, or bundle-integrity failure; anything
   other than exactly 14 terminally reconciled semantic trials and all required
   outputs; a pre-frozen membership/identity/terminal invalidation threshold
   exceeded; a required strategy execution/held-return path invalid; or a Holm
   rejection paired with a nonpositive observed mean Rank IC.
2. Otherwise, `INCONCLUSIVE_DIAGNOSTIC` if any pre-frozen realized coverage
   threshold fails or the common complete-case primary sample contains fewer
   than 60 monthly records.
3. Otherwise, define `holm_supported(f)` as a Holm rejection for factor `f`
   with observed common-complete-case mean Rank IC strictly greater than zero.
   Define `economically_supported(f)` as strictly positive net annualized
   active return for that factor's long-only strategy at both 10 and 25 bps.
   Define `robustness_supported(f)` as strictly positive leave-one-year-out
   common-case mean Rank IC for every required-year omission and a strictly
   greater than 0.5 fraction of required calendar-year common-case mean Rank IC
   values above zero, using all required years as the denominator. Exact zero,
   a missing required-year common-case set, or an empty post-omission table
   fails robustness.
4. `POSITIVE_DIAGNOSTIC` if at least one factor satisfies all three support
   predicates.
5. Otherwise, `MIXED_DIAGNOSTIC` if at least one factor is Holm-supported.
6. Otherwise, `NEGATIVE_DIAGNOSTIC` if all three observed
   common-complete-case mean Rank IC values are strictly below zero.
7. Otherwise, `INCONCLUSIVE_DIAGNOSTIC`.

Strategy and robustness predicates are coherence requirements for the final
diagnostic label, not new discovery hypotheses. They do not change the
three-test Holm family. These labels remain `DIAGNOSTIC_ONLY`; none is a
research-pass, profitability, or deployment claim.

## Prospective Confirmation and Track B

After the full protocol, code, and data policy are frozen, prospective
collection starts at the first eligible monthly signal. Ingestion health and
missing-file checks may be monitored, but factor, portfolio, and cumulative
performance may not be viewed during accumulation.

Six months is operational only. Twelve monthly rebalances is preliminary
evidence only if opening it is separately authorized; opening at month 12
contaminates months 13-24 and requires a new continuation classification.
Twenty-four unopened monthly rebalances is the primary prospective target.

Before any prospective performance access, Track B must implement protected
access logging. Its bounded scope is:

- 8-12 conceptual event families, reusing accepted vocabulary where practical;
- no completion of 37/37 and no second general-purpose DSL;
- at most one design PR and one stdlib-SQLite runtime PR;
- append-only atomic transactions, sequence and previous hash, idempotency,
  restart/replay, retained failed/invalid/aborted work, artifact disposition,
  campaign freeze/closure, review decision, protected access, and safe public
  projection; and
- no more than 14 exact wire event types without a new owner decision.

## Stop Conditions

Stop for owner input when entitlement requires a purchase, written
retention/publication permission is unresolved, historical membership is
materially incomplete, identity or terminal-event reconstruction cannot
support diagnostic use, adjusted-return semantics are inconsistent, private
licensed data could enter public Git, the dataset review is blocked,
preregistration was exposed to expanded results before freeze, validation or
review fails, or brokerage/paper/live scope appears.

Do not stop because all factors fail, costs erase returns, Rank IC is negative,
or the result is mixed. Those are valid diagnostic outcomes.

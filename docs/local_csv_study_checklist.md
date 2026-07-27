# Local CSV Study Checklist

Date: 2026-06-08

This is a documentation-only checklist for a future user-provided local CSV
research run. It is meant to be completed before any user file is loaded,
validated, diagnosed, or interpreted.

It does not load files, fetch data, download data, call vendor APIs, add
credentials, add live trading, add paper trading, connect to a broker, place
orders, run a backtest, generate a real-data report, or claim profitability.

## 1. Use

Copy this checklist into a future issue, PR description, research note, or
experiment draft before a local CSV run starts. Keep incomplete answers visible.
If a required answer is unknown, stop before interpreting results.

This checklist complements:

- `docs/point_in_time_data_methodology_contract.md`
- `docs/user_provided_local_csv_research_plan.md`
- `docs/real_data_readiness_audit.md`
- `EXPERIMENT_LOG.md`

It does not replace the methodology contract, real-data readiness audit,
dataset-manifest review, or the Stage 4 all-trial ledger. Completing it cannot
establish `formal_interpretation_eligible`.

## 2. Scope Statement

Complete this block first.

```text
Run label:

Run type:
  [ ] loader smoke test
  [ ] feature audit
  [ ] diagnostic-only backtest
  [ ] full experiment candidate

Intended interpretation level:
  [ ] ingestion-only
  [ ] feature-calculation-only
  [ ] diagnostic-only simulated workflow
  [ ] dataset-manifest review candidate (not formal evidence)

What question is this run allowed to answer?

What question is this run not allowed to answer?

Stop if this run needs downloads, vendor APIs, credentials, live trading,
paper trading, brokerage integration, order execution, or profitability
language.
```

## 3. File Inventory

Do not include secrets, account identifiers, API keys, credential paths,
private absolute paths, source rows, or private account metadata in the
repository. Maintain any approved local-path mapping outside tracked records;
use only a private-manifest ID and redacted public logical ID here.

| Input | Private-manifest ID | Public logical ID | Source supplied by user | Immutable version | Public hash or private evidence ref | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Adjusted close prices |  |  |  |  |  |  |
| OHLCV prices and volume |  |  |  |  |  |  |
| Benchmark |  |  |  |  |  |  |
| Universe membership |  |  |  |  |  |  |
| Optional factor panel |  |  |  |  |  |  |
| Metadata sidecar |  |  |  |  |  |  |

Record the hash algorithm, actual raw-byte hash, ordered-manifest hash,
retrieval timestamp, extraction scope, and transformation lineage in the
repo-external private manifest. Actual hashes remain in the private manifest.
In this tracked checklist, include only a publication-approved hash or
redacted private-evidence reference and verification state. Stop if an input
lacks an actual private hash and immutable version; a hash plan is not
evidence.

Private-manifest canonicalization and environment evidence:

```text
canonicalization_id:
environment_id:
environment_lock_sha256:
Interpreter/platform:
Locale and process timezone:
Parsing, calendar, and transformation library versions:
```

An ambiguous canonicalization or unlocked/incomplete environment blocks
dataset review and independent reproduction.

## 4. Schema Map

| Input | Selected schema | Required columns present? | Duplicate-date policy | Duplicate date-symbol policy | Status |
| --- | --- | --- | --- | --- | --- |
| Prices | wide price / long price / other |  |  |  |  |
| OHLCV | OHLCV long / other |  |  |  |  |
| Benchmark | benchmark price / benchmark return / other |  |  |  |  |
| Universe | membership / eligibility / other |  |  |  |  |
| Factor panel | wide factor / long factor / other |  |  |  |  |

Stop if the schema must be guessed.

## 5. Provenance And Adjustment Policy

```text
Asset price convention:
  [ ] adjusted close
  [ ] raw close
  [ ] split-adjusted
  [ ] dividend-adjusted
  [ ] total-return adjusted
  [ ] unknown

OHLC convention:

Volume convention:
  [ ] raw share volume
  [ ] adjusted volume
  [ ] unknown

Benchmark convention:

Dataset license state:
  [ ] owner_accepted
  [ ] asserted
  [ ] unknown
  [ ] blocked

Permitted research use and redistribution restriction:

Retrieval timestamp and extraction scope:

Transformation lineage and revision/supersession policy:

Corporate-action handling:

Delisting, merger, stale-row, and symbol-change handling:

Permanent security/listing/issuer identifiers and ticker-alias intervals:

Field publication, availability, ingestion, and revision timestamps:

Exchange calendar, session label, and source/decision timezone:

Typed missingness and stale/zero-volume reasons:

Known manual edits:

Known excluded rows or symbols:
```

Stop if the adjustment policy is unknown for any return, feature, benchmark, or
backtest-like interpretation. An `asserted` license, unknown lineage, or
unreviewed public/private classification also blocks formal interpretation.

## 6. Validation Evidence

Record validation outcomes. Do not repair failures silently.

| Check | Evidence | Issue level | Decision |
| --- | --- | --- | --- |
| Dates parse consistently |  | high / medium / low / none |  |
| Dates are sorted after validation |  | high / medium / low / none |  |
| Duplicate dates absent or rejected |  | high / medium / low / none |  |
| Duplicate `(date, symbol)` rows absent or rejected |  | high / medium / low / none |  |
| Numeric fields reject blanks and missing sentinels before conversion |  | high / medium / low / none |  |
| Missing values counted by file, field, date, and symbol where possible |  | high / medium / low / none |  |
| Non-positive prices absent or rejected |  | high / medium / low / none |  |
| Negative volume absent or rejected |  | high / medium / low / none |  |
| Zero volume counted separately from missing volume |  | high / medium / low / none |  |
| OHLC relationships are valid |  | high / medium / low / none |  |
| Benchmark dates align to intended strategy dates |  | high / medium / low / none |  |
| Raw-byte and ordered-manifest hashes were recomputed |  | high / medium / low / none |  |
| Public projection excludes private paths and source rows |  | high / medium / low / none |  |
| Availability/revision timestamps precede each decision |  | high / medium / low / none |  |
| Exchange calendar, session, and timezone are explicit |  | high / medium / low / none |  |
| Canonicalization and complete environment lock were reviewed |  | high / medium / low / none |  |
| No forward-fill, backward-fill, interpolation, or zero default was used |  | high / medium / low / none |  |

Stop if any high or medium validation issue remains unresolved.

## 7. Universe And Benchmark

```text
Starting universe:

Universe membership source:

Point-in-time membership status:
  [ ] point-in-time
  [ ] static current list
  [ ] unknown

Permanent security/listing/issuer identifier source:

Membership effective interval and `known_at` source:

Ticker-alias effective intervals:

Delisting return, terminal valuation, and merger/conversion policy:

Liquidity rule:

Minimum history rule:

Price filter:

Exclusions:

Survivorship-bias statement:

Benchmark identity:

Why this benchmark matches the intended universe:

Benchmark missing-date policy:

Benchmark version, role, calendar/session, and availability:

Risk-free source/version, tenor, units, day-count, availability, and
missing-date policy:
```

Stop formal interpretation if membership is not point-in-time, identifier
continuity or terminal events are unresolved, or benchmark/risk-free alignment
is unspecified. A survivorship label permits only an explicitly bounded
diagnostic.

## 8. Feature, Signal, And Timing

Keep feature dates, universe dates, rebalance dates, execution dates, and return
measurement dates separate.

| Item | Required answer |
| --- | --- |
| Feature formulas |  |
| Input fields |  |
| Lookback windows |  |
| Skipped windows |  |
| Latest data timestamp available for each signal date |  |
| Field publication/availability/revision timestamp |  |
| Conservative `known_at` no earlier than public/provider/revision/parent availability |  |
| Proof that `known_at <= decision_time` |  |
| Universe membership effective/known-at timestamps |  |
| Calendar, session label, and source/decision timezone |  |
| Signal lag before portfolio formation |  |
| Rebalance timing |  |
| Execution timing assumption |  |
| Return measurement window |  |
| Off-by-one checks planned |  |

Stop if same-period target returns, future universe membership, future prices,
or future benchmark values could enter a feature.

## 9. Sample Split And Parameter Policy

```text
Warm-up exclusion:

In-sample period:

Validation period:

Test or holdout period:

Protected-sample classification:

Append-only access-record ID:

Exposure decision ID:

Fixed parameters:

Parameter grid, if any:

When parameters were chosen:

How weak, failed, ambiguous, or stopped cases will be recorded:
```

Missing, backfilled, unknown-actor/time/impact, or outcome-reconstructible
access cannot retain or establish holdout status. Overlapping windows inherit
the downgrade unless non-overlap is proven prospectively, and classification
may move only toward greater exposure. The previously accessed 2025-05-01
through 2026-05-31 interval is `historical_evaluation`, never a pristine
holdout, and must not be upgraded.

Stop if parameter choices are compared before sample splits and parameter
policy are recorded.

## 10. Costs, Slippage, And Execution Assumptions

Required for any backtest-like diagnostic.

| Assumption | Value | Diagnostic-only caveat |
| --- | --- | --- |
| Transaction cost model |  |  |
| Slippage model |  |  |
| Turnover model |  |  |
| Rebalance frequency |  |  |
| Execution timing |  |  |
| Benchmark comparison |  |  |
| Zero-cost or zero-slippage use |  |  |

Stop if zero-cost or no-slippage output would be presented as realistic
execution evidence.

## 11. Readiness Audit Summary

```text
Real-data readiness audit completed:
  [ ] yes
  [ ] no

High issues:

Medium issues:

Low issues:

Low issues accepted as limitations:

Stop conditions triggered:

Decision:
  [ ] stop before loading files
  [ ] load only for schema smoke test
  [ ] run feature audit only
  [ ] run diagnostic-only workflow
  [ ] prepare dataset manifest for independent review

Program gate evidence (this form cannot grant any gate):
  Methodology contract decision ID:
  Dataset review decision ID:
  Reviewed manifest ID:
  Public projection ID/version/hash or redacted evidence reference:
  Reviewer authority reference:
  Reviewed timestamp:
  Declared use/date/universe/privacy scope:
  Finding IDs and dispositions:
  Dataset review decision:
  Formal-interpretation decision ID:
```

These records are separate decisions. `methodology_contract_accepted` does not
imply `dataset_manifest_reviewed`, and `dataset_manifest_reviewed` does not
imply `formal_interpretation_eligible`. A blank field, checkbox, manifest
author, or this form cannot self-certify `dataset_manifest_reviewed`. Stop if
the immutable decision is absent, self-issued, stale, version-mismatched, or
has any unresolved high or medium issue.

## 12. Experiment Log Preparation

Before any real-data output is committed or interpreted, prepare an
`EXPERIMENT_LOG.md` entry with:

- experiment ID and date.
- private-manifest IDs and redacted public logical IDs; never private absolute
  paths.
- immutable version, retrieval/extraction metadata, lineage, license decision,
  `canonicalization_id`, `environment_id`, `environment_lock_sha256`, and
  privacy classification; actual hashes stay private, with only a
  publication-approved hash or redacted private-evidence reference in the
  tracked record.
- universe and survivorship-bias caveats.
- permanent identifiers, point-in-time membership, corporate actions,
  availability/revisions, calendar/session/timezone, and typed missingness.
- date range and sample splits.
- feature formulas, lookbacks, lags, and timing assumptions.
- parameters and parameter-selection policy.
- benchmark.
- risk-free policy when applicable.
- transaction costs and slippage.
- rebalance and execution timing.
- metrics and limitations.
- missing-data summary.
- failure modes and next action.
- protected-sample classification and append-only access-record ID.
- immutable dataset-review decision ID and exposure-decision ID.

Synthetic JSON sidecar logs are not substitutes for this record.

## 13. Final Gate

Do not interpret results unless every statement below is true.

- [ ] Local files were supplied by the user and no data was fetched.
- [ ] No vendor API, `requests`, `yfinance`, Alpaca, CCXT, credential, token,
      or `.env` path was used.
- [ ] No live trading, paper trading, brokerage integration, order execution,
      or account access was added.
- [ ] No source data was committed unless it is an approved tiny synthetic or
      public fixture.
- [ ] Tracked records contain no private absolute paths or source rows.
- [ ] Private-manifest hashes, immutable version, lineage, license state, and
      the public/private projection were independently reviewed; the tracked
      record exposes no unapproved digest.
- [ ] `canonicalization_id`, `environment_id`, `environment_lock_sha256`,
      locale/timezone, and all parsing/calendar/transformation versions are
      complete and reviewed.
- [ ] No missing values were silently coerced, forward-filled, backward-filled,
      interpolated, or replaced with zero.
- [ ] No unresolved high or medium audit issue remains.
- [ ] The program-gate decision matches the evidence and does not infer formal
      eligibility from contract or manifest acceptance alone.
- [ ] Dataset review is bound to the exact manifest/projection and was issued
      as a non-self-issued exact-version dataset-review decision by an
      authorized non-producing reviewer; this form did not grant it.
- [ ] Missing, backfilled, uncertain, outcome-reconstructible, and overlapping
      protected access was downgraded monotonically and has an exposure
      decision ID.
- [ ] The output language is caveated as simulated research or diagnostics.
- [ ] The output does not claim profitability, robustness, tradeability,
      deployment readiness, investment advice, or future performance.

If any box cannot be checked, stop before interpretation.

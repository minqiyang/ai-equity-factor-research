# Local CSV Readiness Audit Report Template

Date: 2026-06-08

This is a documentation-only report format for a future user-provided local CSV
readiness audit. It is meant to be filled manually before any local CSV result
is interpreted as research evidence.

It does not load files, fetch data, download data, call vendor APIs, add
credentials, add live trading, add paper trading, connect to a broker, place
orders, run a backtest, generate a real-data report, or claim profitability.

Passing this report does not validate a strategy. It only records whether the
local files, schema choices, validation evidence, timing assumptions, and
interpretation boundary are documented enough for a reviewable next step.
It cannot by itself establish `dataset_manifest_reviewed` or
`formal_interpretation_eligible`.

## 1. Use

Copy this report format into a future issue, PR description, research note, or
experiment draft after the local CSV study checklist has been completed and
before any result is interpreted.

This report complements:

- `docs/point_in_time_data_methodology_contract.md`
- `docs/user_provided_local_csv_research_plan.md`
- `docs/local_csv_study_checklist.md`
- `docs/real_data_readiness_audit.md`
- `EXPERIMENT_LOG.md`

It does not replace the methodology contract, study checklist,
dataset-manifest review, or experiment log. Unknown answers must remain
visible. Do not commit private source files, private absolute paths,
credential-like paths, account identifiers, API keys, tokens, or private
account metadata.

## 2. Audit Identity

```text
Audit ID:
Audit date:
Reviewer:
Run label:
Related branch or PR:
Related checklist:
Related experiment-log entry:

Run type:
  [ ] loader smoke test
  [ ] feature audit
  [ ] diagnostic-only backtest
  [ ] full experiment candidate

Allowed interpretation level:
  [ ] ingestion-only
  [ ] feature-calculation-only
  [ ] diagnostic-only simulated workflow
  [ ] dataset-manifest review candidate (not formal evidence)
  [ ] stop before interpretation
```

## 3. Input Inventory Reviewed

Record only the minimum review metadata needed for auditability. Keep the
approved local-path mapping outside tracked records. This public report uses a
private-manifest ID and redacted logical ID; redaction is not optional merely
because a path appears harmless.

| Input | Present? | Schema | Private-manifest ID | Public logical ID | Immutable version | Public hash or private evidence ref | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Adjusted close prices |  |  |  |  |  |  |  |
| OHLCV prices and volume |  |  |  |  |  |  |  |
| Benchmark |  |  |  |  |  |  |  |
| Universe membership |  |  |  |  |  |  |  |
| Optional factor panel |  |  |  |  |  |  |  |
| Metadata sidecar |  |  |  |  |  |  |  |

Record the source name, hash algorithm, actual raw-byte hash,
ordered-manifest hash, retrieval timestamp, extraction scope, transformation
lineage, and revision/supersession history in the repo-external private
manifest. Actual hashes remain in the private manifest. In this tracked report,
include only a publication-approved hash or redacted private-evidence
reference and verification state. Stop interpretation if any private evidence
is missing; a hash plan is not evidence.

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

## 4. Schema And Loader Validation Evidence

This section records validation evidence. It is not a place to repair data
silently.

| Check | Evidence reviewed | Issue level | Decision |
| --- | --- | --- | --- |
| Required columns match selected schema |  | high / medium / low / none |  |
| Dates parse consistently |  | high / medium / low / none |  |
| Dates are sorted after validation |  | high / medium / low / none |  |
| Duplicate dates are absent or rejected |  | high / medium / low / none |  |
| Duplicate `(date, symbol)` rows are absent or rejected |  | high / medium / low / none |  |
| Numeric fields reject blanks and missing sentinels before conversion |  | high / medium / low / none |  |
| Missing values are counted by file, field, date, and symbol where possible |  | high / medium / low / none |  |
| Non-positive prices are absent or separately justified |  | high / medium / low / none |  |
| Negative volume is absent or rejected |  | high / medium / low / none |  |
| Zero volume is counted separately from missing volume |  | high / medium / low / none |  |
| OHLC relationships are valid |  | high / medium / low / none |  |
| Benchmark dates align to intended strategy dates |  | high / medium / low / none |  |
| Raw-byte and ordered-manifest hashes were recomputed |  | high / medium / low / none |  |
| Public projection excludes private paths and source rows |  | high / medium / low / none |  |
| Availability/revision timestamps precede each decision |  | high / medium / low / none |  |
| Exchange calendar, session, and timezone are explicit |  | high / medium / low / none |  |
| Canonicalization and complete environment lock were reviewed |  | high / medium / low / none |  |
| No forward-fill, backward-fill, interpolation, or zero default was used |  | high / medium / low / none |  |

Stop interpretation if any high or medium validation issue remains unresolved.

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

Split, dividend, merger, delisting, stale-row, and symbol-change handling:

Permanent security/listing/issuer identifiers and ticker-alias intervals:

Field publication, availability, ingestion, and revision timestamps:

Exchange calendar, session label, and source/decision timezone:

Typed missingness and stale/zero-volume reasons:

Known manual edits:

Known excluded rows or symbols:
```

Stop interpretation if any return, feature, benchmark, or backtest-like output
depends on an unknown or incompatible adjustment policy. An `asserted` license,
unknown lineage, or unreviewed public/private classification also blocks formal
interpretation.

## 6. Universe And Benchmark Review

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

## 7. Date Alignment And Timing Review

Keep feature dates, universe dates, rebalance dates, execution dates, and return
measurement dates separate.

| Item | Evidence reviewed | Issue level | Decision |
| --- | --- | --- | --- |
| Latest data timestamp is known for each signal date |  | high / medium / low / none |  |
| Field publication/availability/revision timestamps are known |  | high / medium / low / none |  |
| Conservative `known_at` is no earlier than public/provider/revision/parent availability |  | high / medium / low / none |  |
| `known_at <= decision_time` for every consumed record |  | high / medium / low / none |  |
| Membership effective and known-at timestamps are known |  | high / medium / low / none |  |
| Calendar, session label, and source/decision timezone are known |  | high / medium / low / none |  |
| Feature lookbacks do not use future rows |  | high / medium / low / none |  |
| Universe membership is known before the signal date |  | high / medium / low / none |  |
| Liquidity eligibility lag is explicit |  | high / medium / low / none |  |
| Rebalance timing is explicit |  | high / medium / low / none |  |
| Execution timing is explicit |  | high / medium / low / none |  |
| Forward-return measurement starts after signal formation |  | high / medium / low / none |  |
| Off-by-one checks were reviewed |  | high / medium / low / none |  |

Stop interpretation if future prices, future universe membership, future
benchmark values, or same-period target returns could enter a feature.

## 8. Sample Split, Parameters, Costs, And Slippage

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

Transaction cost model:

Slippage model:

Turnover model:

Rebalance frequency:

Execution timing:

Benchmark comparison:

How weak, failed, ambiguous, or stopped cases will be recorded:
```

Missing, backfilled, unknown-actor/time/impact, or outcome-reconstructible
access cannot retain or establish holdout status. Overlapping windows inherit
the downgrade unless non-overlap is proven prospectively, and classification
may move only toward greater exposure. The previously accessed 2025-05-01
through 2026-05-31 interval is `historical_evaluation`, never a pristine
holdout, and must not be upgraded.

Stop interpretation if parameter choices are compared before sample splits and
parameter policy are recorded. Zero-cost or no-slippage output may be used only
as a diagnostic caveat, not as execution evidence.

## 9. Issue Register

Use high for blockers that can change interpretation or violate guardrails. Use
medium for unresolved evidence gaps that can materially affect conclusions. Use
low for caveats that are documented and do not affect date alignment, data
availability, or interpretation.

| ID | Area | Issue | Evidence | Level | Resolution or limitation | Status |
| --- | --- | --- | --- | --- | --- | --- |
|  | provenance |  |  | high / medium / low |  | open / accepted / resolved |
|  | schema |  |  | high / medium / low |  | open / accepted / resolved |
|  | validation |  |  | high / medium / low |  | open / accepted / resolved |
|  | adjustment policy |  |  | high / medium / low |  | open / accepted / resolved |
|  | universe |  |  | high / medium / low |  | open / accepted / resolved |
|  | benchmark |  |  | high / medium / low |  | open / accepted / resolved |
|  | date alignment |  |  | high / medium / low |  | open / accepted / resolved |
|  | missing data |  |  | high / medium / low |  | open / accepted / resolved |
|  | interpretation |  |  | high / medium / low |  | open / accepted / resolved |

Any unresolved high or medium issue stops interpretation.

## 10. Gate Decision

```text
High issues open:

Medium issues open:

Low issues accepted as limitations:

Stop conditions triggered:

Decision:
  [ ] stop before loading files
  [ ] load only for schema smoke test
  [ ] run feature audit only
  [ ] run diagnostic-only workflow
  [ ] prepare dataset manifest for independent review

Decision rationale:

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

Local CSV diagnostics are not profitability evidence. A passed readiness audit
only permits the next reviewed research step under the recorded limitations.
The gate records are separate decisions: `methodology_contract_accepted` does not
imply `dataset_manifest_reviewed`, and `dataset_manifest_reviewed` does not
imply `formal_interpretation_eligible`. A blank field, checkbox, manifest
author, or this form cannot self-certify `dataset_manifest_reviewed`. Stop if
the immutable decision is absent, self-issued, stale, version-mismatched, or
has any unresolved high or medium issue.

## 11. Experiment Log Handoff

Before any real-data output is committed or interpreted, prepare an
`EXPERIMENT_LOG.md` entry that records:

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
- high, medium, and low audit issues.
- failure modes and next action.
- protected-sample classification and append-only access-record ID.
- immutable dataset-review decision ID and exposure-decision ID.

Synthetic JSON sidecar logs are not substitutes for this record.

## 12. Final Stop Statements

Do not interpret or publish results unless every statement below is true.

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
- [ ] Feature dates, universe dates, rebalance dates, execution dates, and
      return measurement dates are distinct.
- [ ] Sample splits, parameter policy, costs, slippage, benchmark, and
      execution timing are recorded before interpretation.
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

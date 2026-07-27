---
name: real-data-readiness-audit
description: Use before interpreting, reporting, committing, or publishing results from user-provided local CSV market data in this project.
---

# Real-Data Readiness Audit

## When to use

Use this Skill in `ai-equity-factor-research` before interpreting, reporting,
committing, or publishing any result derived from user-provided local CSV market
data.

Use it for local CSV experiment readiness, real-data smoke-test review, local
data provenance review, schema and adjustment-policy review, or deciding whether
a result is safe to describe beyond diagnostics.

## When not to use

Do not use this Skill for synthetic-only demos, committed fixture checks,
general staged workflow continuation, PR branch management, or Skill
maintenance. Those remain covered by `staged-quant-workflow` or `skill-maker`.

This Skill does not approve real data fetching, vendor APIs, credentials,
brokerage connections, live or paper trading, order placement, or profitability
claims.

## Desired outcome

Produce a scope-qualified readiness decision before result interpretation:

- `diagnostic_ready` only when the approved diagnostic scope has no unresolved
  high or medium issues.
- `diagnostic_ready_with_low_caveats` only when limitations are documented and
  do not affect provenance, schema validity, date alignment, privacy, or the
  stated diagnostic interpretation.
- `formal_ready` only when no high or medium issues remain and every active
  program gate listed below is implemented and evidenced.
- `blocked` when any required evidence is missing or unresolved.

The audit should make assumptions, caveats, and stop conditions visible before
any local CSV output is treated as research evidence.

## Required inputs/files to inspect

Inspect the current project rules and readiness references:

- `AGENTS.md`
- `PROJECT_SPEC.md`
- `README.md`
- `docs/research_program_charter.md`
- `docs/current_roadmap.md`
- `docs/real_data_readiness_audit.md`
- `docs/csv_data_interface_plan.md`
- `docs/volume_ohlcv_schema_plan.md`
- `docs/liquidity_dollar_volume_universe_plan.md`, when present and relevant
- `EXPERIMENT_LOG.md`
- relevant proposed report, log, or research-script paths

Inspect user-provided CSV paths only after the user explicitly approves each
path for metadata inspection or hashing. Do not inspect `.env`, credentials,
tokens, private keys, account files, or credential-like paths.

## Evidence classification and program gates

This audit can approve metadata inspection, loader checks, and explicitly
caveated fixed-cohort diagnostics. It cannot supersede
`docs/research_program_charter.md` or promote a run to formal historical
evidence while a prerequisite remains blocked in `docs/current_roadmap.md`.

`formal_ready` requires implemented, reviewed, and tested evidence for all of
the following:

- bounded, horizon-purged sample splits and an explicit timing contract.
- provider-agnostic point-in-time membership, delisting, corporate-action,
  field-semantics, provenance/license, benchmark, and missing-data contracts.
- immutable experiment, campaign, trial-family, and trial identifiers allocated
  before execution, including failed and invalid trials.
- the registered statistical and multiple-testing protocol required for the
  claim.
- explicit cost, slippage, turnover, capacity, and execution assumptions
  appropriate to the evidence layer.
- private-data handling and a holdout-exposure classification that does not
  overstate previously examined samples.

Roadmap intent is not implementation evidence. Until these gates are accepted,
the highest possible decision is diagnostic readiness. A static current
constituent list or otherwise unverified historical membership can support only
an explicitly survivorship-biased diagnostic, never `formal_ready`.

## Read-only checks

Start with read-only repo state:

```powershell
git status -sb --untracked-files=all
```

For each user-approved local CSV path, metadata and hashing are allowed only
when explicitly approved:

```powershell
Get-Item -LiteralPath "<approved-local-csv-path>" | Select-Object FullName,Length,LastWriteTime
Get-FileHash -Algorithm SHA256 -LiteralPath "<approved-local-csv-path>"
```

Skip any command that would write files, fetch data, install software, call a
vendor API, read secrets, or mutate git state.

## Data provenance checks

Before any result interpretation, record:

- approved local file path for each input.
- file timestamp, version, or hash when the file may change.
- user-provided source name.
- whether the file is raw export, hand-cleaned, vendor-cleaned, or derived.
- known manual edits, missing symbols, missing dates, stale prices, or excluded
  rows.
- confirmation that no credentials, account IDs, API keys, or private account
  metadata are being committed.

Unknown provenance blocks interpretation.

## Schema and OHLCV checks

Confirm the selected schema and required columns before using data:

- wide adjusted-close price panel.
- long adjusted-close price rows.
- benchmark price or return series.
- OHLCV long rows with `date`, `symbol`, `open`, `high`, `low`, `close`,
  `volume`, and optional `adjusted_close`.
- universe, factor-panel, or metadata schema only when already documented.

Check for exact required column names, duplicate headers, parseable
timezone-naive dates, sorted dates, duplicate dates or `(date, symbol)` rows,
missing symbols, invalid numeric strings, non-finite values, boolean market
data fields, non-positive prices, negative volume, and impossible OHLC
relationships.

Unresolved schema or OHLCV issues block interpretation.

## Date alignment and leakage checks

Keep these dates distinct:

- observation date.
- feature date.
- universe decision date.
- signal date.
- execution date.
- return measurement date.

Confirm that features use only information known before portfolio formation.
Check lookbacks, skipped windows, rolling warm-up periods, signal lag, and
rebalance timing. Same-period target returns, future returns, future universe
membership, future fundamentals, future benchmark data, or same-day close data
without an explicit execution assumption must not enter features.

Unresolved date-alignment or leakage risk blocks interpretation.

## Universe, benchmark, and survivorship checks

Record universe and benchmark assumptions before metrics are interpreted:

- universe definition and eligibility rules.
- verified point-in-time membership for every formal evidence window.
- an explicit survivorship-bias label when a static or otherwise unverified
  cohort is retained for diagnostics only.
- liquidity, dollar-volume, price, stale-data, zero-volume, and minimum-history
  rules when used.
- benchmark symbol or file, date range, adjustment convention, missing dates,
  and reason it matches the intended universe.

Incompatible benchmark coverage, unknown benchmark adjustment, or undocumented
survivorship risk blocks any interpretation. Static or otherwise unverified
historical membership blocks formal interpretation even when its survivorship
caveat is documented.

## Missing data and adjustment policy checks

Document price and volume conventions before calculating returns, features, or
diagnostics:

- raw close, adjusted close, split-adjusted, dividend-adjusted, total-return
  adjusted, or unknown.
- whether OHLC and adjusted-close fields share a compatible convention.
- whether volume is raw, adjusted, or unknown.
- handling of splits, dividends, mergers, symbol changes, delistings, halts,
  stale rows, and zero-volume rows.

Do not forward-fill, backward-fill, zero-fill, interpolate, or infer corporate
actions by default. Unknown adjustment policy blocks interpretation.

## Costs, slippage, and diagnostics-only language checks

Any backtest-like result must state:

- transaction cost model.
- slippage model.
- turnover model.
- rebalance frequency.
- execution timing.
- benchmark choice.
- whether zero-cost or zero-slippage settings are diagnostics only.

Local CSV diagnostics, IC, Rank IC, quantile spread, loader smoke checks, and
synthetic fixture outputs are not profitability evidence. Use caveated language:
diagnostic, smoke test, readiness check, limitation, and not strategy
validation.

## Experiment logging expectations

Before committing or publishing real-data outputs, prepare an `EXPERIMENT_LOG.md`
entry or approved research note with:

- data source and approved local file references.
- schema, provenance, and validation summary.
- universe definition and survivorship caveats.
- date range and train/validation/test or holdout splits.
- feature formulas, lookbacks, lags, and data availability assumptions.
- parameters and parameter-selection policy.
- benchmark, costs, slippage, rebalance, and execution timing.
- metrics, missing-data summary, limitations, failure modes, and next action.

Synthetic JSON sidecar logs are not substitutes for the real-data experiment
record. The current `EXPERIMENT_LOG.md` template is a diagnostic/legacy record,
not the immutable all-trial ledger required by Stage 4. It cannot satisfy
`formal_ready` until the ledger allocates identifiers before execution and
retains every attempted, failed, invalid, aborted, and excluded trial plus
lineage, hashes, review outcomes, and protected-sample access.

## Stop conditions

Stop before interpretation, reporting, committing, or publishing when any of
these are true:

- user did not explicitly approve a local CSV path for inspection.
- a path appears credential-like or may contain secrets.
- provenance is unknown.
- schema, required columns, duplicate rows, invalid numeric values, missing
  values, or OHLCV checks remain unresolved.
- adjustment policy is unknown or incompatible with the intended calculation.
- date alignment, signal lag, execution timing, or leakage risk is unresolved.
- universe membership is static, current-list-based, or otherwise unverified
  for the intended historical dates when formal interpretation is proposed; a
  survivorship caveat permits diagnostics only.
- benchmark coverage or adjustment is incompatible.
- costs, slippage, or diagnostic-only language are absent for a backtest-like
  result.
- any required timing, point-in-time methodology, all-trial ledger,
  statistical, privacy, or holdout-classification program gate lacks accepted
  implementation evidence when formal interpretation is proposed.
- any high or medium readiness issue remains unresolved.
- the result would require real data fetching, vendor APIs, credentials,
  live or paper trading, broker integration, order execution, or profitability
  claims.

## Mistakes to avoid

- Treating a local CSV loader success as research validation.
- Treating a survivorship caveat as a substitute for point-in-time membership.
- Treating unknown adjustment policy as acceptable evidence.
- Silently filling missing prices, volumes, benchmark rows, or universe data.
- Using future membership, future returns, or same-period targets as features.
- Reporting only the best parameter result.
- Committing private local paths, credentials, vendor secrets, or account
  metadata.
- Presenting diagnostics, synthetic fixtures, or smoke tests as profitability,
  robustness, or trading-readiness evidence.
- Duplicating `staged-quant-workflow` branch, PR, merge, and long-running stage
  process inside this Skill.

## Update policy

Update this Skill only after a real-data readiness audit verifies a reusable
lesson. Add concise new stop conditions, stable commands, known pitfalls, or
required evidence fields. Remove stale guidance when project docs change. Keep
this Skill focused on the pre-experiment readiness gate.

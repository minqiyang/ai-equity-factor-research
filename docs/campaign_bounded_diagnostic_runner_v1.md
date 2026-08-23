# Campaign Bounded Diagnostic Runner v1

Public-safe design note for the Track A PR 3 bounded diagnostic runner.
This note is orientation and methodology material. It is not an authority
source. Authority remains in `AGENTS.md`, the campaign contract, the
preregistration, the trial inventory, and the point-in-time contract.

## What this repository ships

PR 3 ships library code under `src/campaign/`, committed synthetic fixtures
under `tests/fixtures/campaign_runner_v1/`, and the tests that bind those
fixtures to the shippable entry points. CI executes only those committed
fixtures. The job is not result-bearing and does not read a private panel.

PR 3 does not run the 14 semantic trials, materialize private rows, grant
performance or result access, or produce factor, portfolio, or cumulative
values from a live dataset.

## Frozen factor-ID owner

`campaign.inference.FACTOR_ORDER` is the single authoritative frozen
factor-ID tuple. The derived registry has no factor-ID string literals and
zips implementation rows against that owner. PR 3 does not edit
`src/campaign/inference.py`. The T-7 scan allows only that module-scope
`FACTOR_ORDER` assignment to contain the ID strings; docstrings, attribute
identifiers, and fixtures are out of that scan.

## Module obligations

The runner adds one module per frozen obligation: registry, lineage,
schedule, eligibility, returns, baselines, paths, benchmarks, diagnostics,
metrics, reconciliation, precondition, runner, and bundle. Existing
protocol-core modules stay reused as-is.

`campaign` may import the standard library, NumPy, itself, and — only from
`precondition.py` — the named `pit_manifest_validator_v1.canonical`
allowance. It may not import `backtest`, `features`, `strategies`, `risk`,
`data`, or `pit_manifest_validator_v1.validator`.

## No generic-helper defaults

Public campaign functions declare no semantic defaults. Protocol constants
are required `RunConfig` fields. Construction format-validates the two
acceptance digests independently as same-role bindings and does not compare
a `FILE_BYTES` digest to a `CANONICAL_IDENTITY` digest.

## Golden fixtures

Runner tests load expected and forbidden values from committed JSON. They
call public `campaign.*` entry points. They do not define nested protocol
closures or keep protocol numbers as Python literals outside fixture loading
and index arithmetic.

## Fail-closed run

`run_campaign` produces no result-bearing bundle unless `precondition`
returns `AUTHORIZED`. Authorization is fail-closed. There is no force flag,
skip-binding switch, or partial-run mode.

## Strict factor-matched benchmark

The primary benchmark is the factor-specific eligible set frozen at signal
close, equal-weighted, cost-free, on the same execution calendar. Missing or
invalid constituent returns retain an invalid comparison. There is no fill,
interpolation, survivor renormalization, or cash substitute.

## Out of scope here

Prospective-confirmation clocks, append succession, terminal-event policy
acceptance, detached run binding, D8, A2, and any 14-trial execution belong
to later authorized stages.

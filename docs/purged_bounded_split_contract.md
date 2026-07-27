# Purged and Bounded Chronological Split Contract

Status: accepted Stage 1a design target; implementation is deferred to Stage
1b.

Baseline: protected `main` merge `57f3db3` (PR #158), with 594 tests passing.

This contract defines how date windows and forward-looking evaluation labels
must be isolated before any historical factor result can be interpreted. It is
a software and methodology contract, not research evidence. It does not
authorize private-data interpretation, factor promotion, strategy testing,
paper trading, or live trading.

## Scope

Stage 1b must implement:

- explicit inclusive starts and ends for train, validation, and test;
- a bounded test window even when the source index contains later rows;
- complete label-interval ownership;
- horizon-aware purge at every split end;
- optional, explicit row-based embargo at downstream split starts;
- separate feature warm-up and label warm-down metadata;
- per-signal label and exclusion metadata; and
- deterministic tests proving that later prices outside a split cannot change
  that split's eligible labels or diagnostics.

This stage does not choose a walk-forward schedule, a pristine holdout, a
factor, a benchmark, a trading clock, or a return execution convention. Stage
2 will separately freeze feature availability, decision, execution, and return
measurement timestamps.

## Verified Current Behavior and Gaps

| Evidence | Current behavior | Consequence |
| --- | --- | --- |
| `src/features/validation.py:45-100` | The helper accepts only `train_end`, `validation_end`, and an optional `test_end`; it rejects `test_end` before the final source date. | Split starts are implicit and a frozen bounded test cannot coexist with later source rows. |
| `src/features/validation.py:103-121` | Panel slicing requires the panel index to equal the concatenated split dates. | A source panel cannot safely retain pre-sample feature history or ignored post-test rows. |
| `research/eodhd_factor_diagnostics_dry_run.py:81-92` | Forward returns are calculated on the full panel and then sliced by signal date. | The final `h` signal rows of train or validation can use prices from the next split. |
| `research/local_csv_fixture_workflow_demo.py:242-267` | Asset and benchmark forward returns are also calculated before the chronological slice. | The committed fixture workflow encodes the same split-edge label leakage. |
| `research/local_csv_fixture_workflow_demo.py:269-349` | Both unsplit and split diagnostics consume the full-panel labels. | Formal use cannot distinguish eligible labels from cross-boundary labels. |
| `tests/test_validation.py:216-223` | A test requires bounded `test_end` to fail. | The present test suite protects behavior that Stage 1b must intentionally replace. |

Computing a feature on complete historical input is not itself the defect.
The defect is assigning an evaluation label to a split when the label's
information interval is not wholly owned by that split.

## Normative Terms

- **Source index**: the complete, validated `DatetimeIndex` supplied to the
  split builder. It may contain feature-history rows before train and ignored
  rows after test.
- **Configured window**: one inclusive `[start, end]` interval for train,
  validation, or test.
- **Candidate signal date**: a source date inside a configured window before
  purge or embargo.
- **Label start**: the first timestamp whose value enters an evaluation target.
- **Label end**: the last timestamp whose value enters that target.
- **Eligible signal date**: a candidate whose complete label interval belongs
  to its configured window and which is not embargoed. Eligibility controls
  target values and metrics; it does not remove the date from the auditable raw
  window axis.
- **Purged date**: a candidate excluded because its label interval is
  unavailable or crosses its configured window end.
- **Embargoed date**: a downstream candidate excluded by the configured
  separation buffer after the preceding window.
- **Feature warm-up date**: a source date made available only as trailing
  feature history before a configured window. It is never an evaluation row
  for the window whose warm-up set contains it; the same timestamp may have an
  evaluation role in an earlier window.
- **Label warm-down date**: a candidate at a configured window tail that can
  serve as a label endpoint for an earlier eligible signal but is itself
  purged as a signal because its own label would cross the window end.
- **Outside-sample date**: any source date not in a configured window or its
  explicitly recorded feature warm-up set.

## Window Contract

### Required boundaries

The split configuration must require all six boundaries:

```text
train_start
train_end
validation_start
validation_end
test_start
test_end
```

They are inclusive timestamp bounds and must satisfy:

```text
train_start <= train_end
train_end < validation_start
validation_start <= validation_end
validation_end < test_start
test_start <= test_end
```

Gaps are allowed and remain outside the evaluation sample. A boundary need not
be an observed source timestamp, but each configured window must realize at
least one candidate date. Metadata must preserve both the configured bounds
and the first and last realized candidate dates.

The source index must be non-empty, unique, strictly increasing, and timezone
compatible with every boundary. The implementation must not sort, deduplicate,
normalize timezones, fill dates, or infer a trading calendar.

### Bounded test semantics

`test_end` is always explicit. It may precede the final source date. Source
rows after `test_end` are ignored by the current protocol and must not:

- become test signal rows;
- complete labels assigned to test;
- affect eligible test diagnostics or counts; or
- silently extend the configured test window.

If later rows should belong to another experiment, that experiment needs a new
frozen configuration and trial record. A caller cannot obtain an extra test
tail by omitting `test_end`. No post-test value may complete a test label.

Earlier owner-plan wording allowed post-window data to support
warm-down/forward labels. The subsequently accepted research charter requires
the complete label interval to be contained in one split, so the charter and
this contract supersede that earlier wording for Stage 1b. The final `h`
candidate dates of test are purged. Using endpoint-only post-window support
would require an explicit charter and trial-definition revision before code
changes.

### Source-panel alignment

The returned split object must retain the exact source index used to construct
eligibility. Any factor, price, benchmark, or label panel sliced with that
object must have exactly the same index, including order and timezone. A raw
window slicer returns all candidate dates. A label-aware slicer retains that
same raw axis but masks every purged or embargoed target value to `NaN`.

This replaces the current requirement that a panel equal only the concatenated
split dates. It permits recorded pre-sample history and ignored post-test data
without permitting silent reindexing.

## Label-Interval Contract

### Required label kinds

Every consumer must declare one of these initial `label_kind` values:

```text
price_forward_return
synthetic_same_row_response
```

`price_forward_return` requires `label_horizon_rows >= 1` and the row-horizon
interval below. `synthetic_same_row_response` requires
`label_horizon_rows == 0`, `label_start == signal_date`, and
`label_end == signal_date`; it must not be described as a realized or forward
price return.

Every candidate must have exactly one interval record. Every non-missing
endpoint must be ordered, present on the exact source index, and compatible
with the candidate signal date. A price-derived `label_end` may be `NaT` only
when `i + h` is unavailable and is then purged; a synthetic same-row endpoint
may never be missing. The consumer metadata must also record a stable
`label_derivation` identifier describing the calculation or synthetic
generator. New label kinds require a separate design change.

### Price-derived row-horizon labels

For the current close-to-close diagnostic label with horizon `h` source rows:

```text
signal_date = source_index[i]
label_start = source_index[i]
label_end = source_index[i + h]
label_value = value[i + h] / value[i] - 1
```

`label_horizon_rows` must be a non-boolean integer at least 1. Row horizon
means the next available source observations, not calendar days.

A label belongs to split `S` only when:

```text
S.configured_start <= signal_date
label_start >= S.configured_start
label_end <= S.configured_end
```

For the current label, `label_start == signal_date`. Stage 2 may later replace
that timing only through a separately reviewed contract.

If `label_end` does not exist, the candidate is purged with
`label_end_unavailable`. If it exists after the configured end, the candidate
is purged with `label_crosses_window_end`. The label value for a purged or
embargoed row must not be passed to diagnostics.

### Explicit non-price synthetic labels

The existing synthetic split demo creates responses directly from the same-row
factor and does not derive them from a future price. Stage 1b must not falsely
describe those values as an `h`-row price return. Such a consumer must either:

- provide the exact `[signal_date, signal_date]` interval and
  `synthetic_same_row_response` kind for every candidate; and
- be renamed or documented as a same-row synthetic response.

Any workflow that derives a target from future source values must use the
price-derived interval and purge contract. A raw chronological window alone is
not sufficient evidence of label isolation.

### Calculation order

Stage 1b must use this logical order:

1. validate the source index and all six bounds;
2. create candidate signal dates;
3. create and record label start/end dates;
4. apply purge and embargo eligibility;
5. calculate or select label values;
6. mask every structurally ineligible target cell to `NaN` while retaining the
   raw split axis;
7. expose target values only for eligible factor/label pairs to split
   diagnostics; and
8. summarize exclusions without publishing excluded label values.

An implementation may vectorize these operations, but it must preserve the
same observable order and metadata. Structural ineligibility is separate from
asset-level missing returns: a structurally excluded row is all-`NaN`, while an
eligible row can still contain asset-specific `NaN`. Unsplit full-panel
diagnostics are not formal split evidence. If retained for a synthetic
demonstration, they must use the union of raw split axes with the same
eligibility mask and remain explicitly diagnostic-only.

## Purge Contract

Purge is evaluated independently inside train, validation, and test. A
candidate is purged when its complete label interval is not contained in the
same configured window.

For a contiguous source index and a row horizon `h`, the final `h` candidate
dates of each window will normally be purged. Irregular calendars do not change
the row count: the implementation follows source-index positions and records
the resulting exact timestamps.

Purged signal dates:

- remain visible in metadata;
- may be used as label endpoint data for earlier eligible dates in the same
  window;
- retain their factor row but expose an all-`NaN` target row to metrics; and
- do not migrate into the next split.

The purged tail is the label warm-down set for that window. Post-test source
rows are not test warm-down rows because the bounded protocol forbids using
them to complete test labels.

## Embargo Contract

`embargo_rows` must be a non-boolean integer at least 0 and defaults to 0. It
must be frozen in the experiment configuration; Stage 1b must not silently
derive or optimize it.

For each train-to-validation and validation-to-test transition:

1. identify the first `embargo_rows` source observations strictly after the
   preceding configured end;
2. intersect those observations with the downstream candidate window; and
3. mark the intersection as embargoed.

An explicit gap can therefore satisfy all or part of an embargo. Metadata must
record the requested embargo, the source dates consumed by a gap, and the
actual downstream dates excluded. Train has no leading embargo, and no
post-test embargo is created because this three-way contract has no downstream
split.

For each transition, metadata must retain three exact ordered sets:

```text
inter_window_gap_dates
gap_dates_consuming_embargo
downstream_embargoed_dates
```

Their counts are derived. Partial satisfaction is valid: for example,
`embargo_rows=3` with one protected source observation in the gap excludes
exactly the first two downstream observations.

Purge and embargo flags are independent. A short window can cause one date to
carry both flags. `is_eligible` is true only when both are false. A non-empty
raw window may have zero eligible dates; the result must retain that window,
mask all target values, and record `no_eligible_labels`. It is `INVALID` for
formal interpretation, not a reason to borrow a cross-boundary label or hide
the failed window.

An embargo is a preregistered dependence buffer, not a substitute for
horizon-aware purge. Later statistical-validation stages may require a
different embargo based on the accepted overlap/dependence model.

## Warm-Up and Warm-Down Contract

`feature_warm_up_rows` must be a non-boolean integer at least 0. It is declared
by the workflow as the maximum trailing row history required by the factors in
that run; it is not inferred from observed results.

For each configured window, the recorded feature warm-up set is the final
`feature_warm_up_rows` source observations strictly before the first realized
candidate date. If insufficient rows exist, construction fails. Warm-up dates
may be used to calculate trailing features but:

- are excluded from target labels and diagnostics for that window;
- do not change the configured window start;
- cannot supply future membership, revisions, or other not-yet-available
  information; and
- must be listed exactly in metadata.

Label warm-down is derived, not configured. It is the set of window-tail
candidate dates purged because their own label end is unavailable or outside
the configured end. Those dates can be endpoints for earlier in-window labels,
but they are not measured signal dates.

This date contract cannot prove that every factor has enough valid values or a
correct availability lag. Factor-specific warm-up and availability checks
remain required.

## Required Metadata

### Per-candidate label ledger

The split result must expose one deterministic row for every candidate signal
date with at least:

| Field | Meaning |
| --- | --- |
| `split_name` | `train`, `validation`, or `test` |
| `label_kind` | `price_forward_return` or `synthetic_same_row_response` |
| `label_derivation` | stable calculation/generator identifier |
| `signal_date` | candidate signal timestamp |
| `label_start` | first timestamp used by the target |
| `label_end` | last timestamp used by the target, or `NaT` when unavailable |
| `is_purged` | label interval is unavailable or crosses the window end |
| `is_embargoed` | date falls in the effective downstream embargo |
| `is_eligible` | neither purge nor embargo applies |
| `exclusion_reasons` | stable ordered reasons; empty for eligible rows |

Allowed initial exclusion reasons are:

```text
label_end_unavailable
label_crosses_window_end
embargo
```

No label values belong in this ledger.

### Per-window summary

Each split must record:

- configured start and end;
- realized candidate start and end;
- candidate and eligible signal dates and counts;
- purged dates and count;
- embargoed dates and count;
- excluded union dates and count;
- whether eligible labels exist and the deterministic invalid reason when they
  do not;
- feature warm-up dates, requested rows, and available rows;
- label warm-down dates and count;
- label horizon rows;
- requested embargo rows;
- embargo rows satisfied by an explicit gap;
- explicit gap dates and counts;
- ignored pre-sample and post-test dates and counts; and
- source-index start, end, row count, and timezone.

Dates serialize in deterministic ISO-8601 order. Counts are derived from the
date sets rather than caller-supplied. The result must preserve enough
metadata to reproduce every inclusion and exclusion decision without reading
factor or return values.

### Consumer-level availability summary

Structural date eligibility remains independent of source missingness. After
applying the structural mask, every migrated consumer must additionally record:

- total eligible target cells;
- valid and missing eligible target cells;
- usable factor-label pairs for each factor/diagnostic input;
- whether any usable pair exists; and
- `no_usable_label_pairs` when structural dates exist but no factor-label pair
  can enter a diagnostic.

An eligible date with all asset targets missing remains structurally eligible
but cannot contribute evidence. Partial asset missingness must reduce usable
cell counts without changing purge or embargo flags. A workflow may not use
`has_eligible_labels=true` as a substitute for these consumer-level
availability checks.

## Hand-Calculated Reference Case

Use a daily source index from `2024-01-01` through `2024-01-18` with:

```text
train       = [2024-01-01, 2024-01-05]
validation  = [2024-01-06, 2024-01-10]
test        = [2024-01-11, 2024-01-15]
label_horizon_rows = 2
embargo_rows = 1
feature_warm_up_rows = 0
```

Expected date sets:

| Split | Eligible | Purged / warm-down | Embargoed |
| --- | --- | --- | --- |
| train | Jan 1, Jan 2, Jan 3 | Jan 4, Jan 5 | none |
| validation | Jan 7, Jan 8 | Jan 9, Jan 10 | Jan 6 |
| test | Jan 12, Jan 13 | Jan 14, Jan 15 | Jan 11 |

Examples:

- the Jan 3 train label ends Jan 5 and is eligible;
- the Jan 4 train label ends Jan 6 and is purged;
- the Jan 6 validation label stays inside validation but is embargoed;
- the Jan 13 test label ends Jan 15 and is eligible;
- the Jan 14 test label ends Jan 16 and is purged even though Jan 16 exists in
  the source; and
- Jan 16 through Jan 18 are outside the bounded test and cannot affect an
  eligible label or metric.

## Deterministic Stage 1b Test Matrix

| ID | Test | Required assertion |
| --- | --- | --- |
| `SPLIT-001` | Hand-calculated reference | Exact candidate, eligible, purged, warm-down, and embargo date sets match the table above. |
| `SPLIT-002` | Six explicit bounds | Missing any start or end is rejected; all configured and realized bounds are recorded. |
| `SPLIT-003` | Inclusive off-index bounds | Bounds between observations select only timestamps inside the inclusive interval and record the realized endpoints. |
| `SPLIT-004` | Bounded test with later source rows | `test_end < source_index[-1]` is accepted; no later row appears in a split. |
| `SPLIT-005` | Post-test append/mutation invariance | Mutating raw post-test asset prices and rerunning the full consumer leaves its eligible targets, complete ledger, counts, status, and metric payload byte-for-byte equal. Appending/removing post-test rows leaves eligible targets and metrics equal; only source/suffix and unavailable-versus-crossing metadata may differ. |
| `SPLIT-006` | Cross-edge mutation invariance | Changing validation prices leaves eligible train labels and metrics unchanged; changing test prices leaves eligible validation labels and metrics unchanged. |
| `SPLIT-007` | Horizon 1 and horizon 3 | Exact purged tails contain 1 and 3 candidate dates per sufficiently long window. |
| `SPLIT-008` | Irregular calendar | Label ends follow source-index rows, not calendar-day arithmetic. |
| `SPLIT-009` | Embargo 0 and 2 | Zero excludes nothing; two excludes the first two downstream source rows when windows are contiguous. |
| `SPLIT-010` | Full and partial gap embargo | A fully satisfying gap excludes no downstream date. With embargo 3 and one protected gap row, exactly the first two downstream observations are excluded; exact transition sets and an off-index-bound variant are asserted. |
| `SPLIT-011` | Purge/embargo overlap | Both flags and both reasons are retained; the date is ineligible and counts remain derived from sets. |
| `SPLIT-012` | Empty eligible window | Every migrated diagnostic consumer retains the raw window with all-`NaN` targets, emits no metric value, records zero eligible count plus `no_eligible_labels`, and classifies it `INVALID`. |
| `SPLIT-013` | Warm-up separation | Exact trailing warm-up dates are recorded and never appear in that window's candidate or metric indexes; insufficient history raises. |
| `SPLIT-014` | Per-row ledger | Every candidate has exact signal/start/end timestamps and stable exclusion flags/reasons. |
| `SPLIT-015` | Source-panel alignment | Missing, reordered, duplicated, or timezone-mismatched panel dates raise; no implicit reindex or fill occurs. |
| `SPLIT-016` | Raw asset/benchmark parity | Mutate raw post-test asset and benchmark prices separately and rerun the full workflows. Eligible target panels, structural intervals/flags, counts, status, and metric payloads remain equal while asset-level missingness stays independent. |
| `SPLIT-017` | Unsplit diagnostic guard | A future-return workflow cannot pass unpurged full-panel labels to formal diagnostics. |
| `SPLIT-018` | Invalid parameters | Boolean/non-integer/negative embargo or warm-up, price horizon below 1, synthetic horizon other than 0, invalid/duplicate/off-index intervals, invalid bounds, and empty candidate windows raise. |
| `SPLIT-019` | Synthetic-label honesty | Both synthetic split consumers emit `synthetic_same_row_response`, horizon 0, exact `[t,t]` intervals, and a derivation identifier; neither describes the response as an `h`-row price return. |
| `SPLIT-020` | Determinism | Repeated construction yields identical metadata ordering, date sets, labels, and summaries. |
| `SPLIT-021` | Raw-axis masking | Factor and target split indexes retain every raw candidate date; purge/embargo rows are all-`NaN` only in the target panel. |
| `SPLIT-022` | Consumer missingness audit | Partial asset target `NaN` values change valid/missing and usable-pair counts without changing structural flags; an all-missing eligible row triggers `no_usable_label_pairs` when no pair remains. |

Focused consumer tests must cover both
`research/eodhd_factor_diagnostics_dry_run.py` with synthetic temporary CSVs
and `research/local_csv_fixture_workflow_demo.py` with committed synthetic
fixtures. They must also cover
`research/synthetic_split_ic_rank_ic_demo.py` and
`research/synthetic_split_robustness_demo.py` for explicit same-row response
metadata. Every consumer needs zero-eligible and partial/all-missing target
coverage. Tests must not open private files or report private values.

## Stage 1b Implementation Boundary

Stage 1b may change:

- `src/features/validation.py` and its exports;
- split and label tests;
- `research/eodhd_factor_diagnostics_dry_run.py` through synthetic temporary
  CSV tests only;
- `research/local_csv_fixture_workflow_demo.py` and its committed synthetic
  fixtures;
- the two synthetic split consumers only as required for six-bound migration
  and honest label-interval metadata;
- their configuration and audit metadata; and
- generated synthetic evidence only when deterministically affected.

It must not:

- interpret private EODHD outputs;
- choose or inspect a protected-sample result;
- change factor formulas, factor direction, strategy logic, portfolio
  construction, costs, execution, or benchmark policy;
- add a data provider or dependency; or
- expand into Stage 2 zero-lag/execution timing.

Implementation starts test-first from the matrix above. Focused tests must
prove invariance before any affected generated synthetic artifact is
regenerated. Full tests, Ruff, compilation, package build, diff checks, current
head CI, and final-head review remain mandatory.

## Accepted Decisions and Deferred Choices

Accepted here:

- all six bounds are explicit and inclusive;
- gaps are allowed and recorded;
- `test_end` is a hard information cutoff;
- row horizons follow the validated source index;
- complete label intervals must remain inside one split;
- purge applies to train, validation, and test;
- embargo is optional, explicit, row-based, and defaults to 0;
- a gap can satisfy embargo;
- feature warm-up is separate from measured rows;
- label warm-down is the purged in-window tail; and
- raw split axes remain visible while only eligible target values enter split
  diagnostics.

Deferred:

- calendar-specific sessions and timestamps;
- next-open versus next-close return measurement;
- the statistical rule for selecting a nonzero embargo;
- walk-forward fold generation;
- protected-sample naming and access control;
- point-in-time universe and corporate-action methodology; and
- any empirical promotion threshold.

Those deferred choices cannot be inferred from Stage 1b results.

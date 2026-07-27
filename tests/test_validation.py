import ast
from dataclasses import replace
import inspect

import numpy as np
import pandas as pd
import pytest
from pandas.testing import (
    assert_frame_equal,
    assert_index_equal,
    assert_series_equal,
)

import features.validation as validation
from features.validation import (
    TrainValidationTestSplit,
    make_price_forward_return_labels,
    make_train_validation_test_split,
    mask_label_panel_by_train_validation_test,
    split_label_panel_by_train_validation_test,
    split_panel_by_train_validation_test,
    summarize_label_availability,
)


def _reference_dates() -> pd.DatetimeIndex:
    return pd.date_range("2024-01-01", periods=18, freq="D")


def _reference_split(
    *,
    horizon: int = 2,
    embargo: int = 1,
    warm_up: int = 0,
    label_kind: str = "price_forward_return",
) -> TrainValidationTestSplit:
    return make_train_validation_test_split(
        _reference_dates(),
        train_start="2024-01-01",
        train_end="2024-01-05",
        validation_start="2024-01-06",
        validation_end="2024-01-10",
        test_start="2024-01-11",
        test_end="2024-01-15",
        label_kind=label_kind,
        label_derivation=(
            "test_close_to_close"
            if label_kind == "price_forward_return"
            else "test_same_row_generator"
        ),
        label_horizon_rows=horizon,
        embargo_rows=embargo,
        feature_warm_up_rows=warm_up,
    )


def _price_panel(index: pd.DatetimeIndex | None = None) -> pd.DataFrame:
    dates = _reference_dates() if index is None else index
    offsets = np.arange(len(dates), dtype=float)
    return pd.DataFrame(
        {
            "AAA": 100.0 + offsets,
            "BBB": 200.0 + 2.0 * offsets,
        },
        index=dates,
    )


def test_split_001_hand_calculated_reference_sets() -> None:
    split = _reference_split()

    assert_index_equal(
        split.train,
        pd.date_range("2024-01-01", "2024-01-05", freq="D"),
    )
    assert_index_equal(
        split.window_metadata["train"].eligible_dates,
        pd.DatetimeIndex(["2024-01-01", "2024-01-02", "2024-01-03"]),
    )
    assert_index_equal(
        split.window_metadata["train"].purged_dates,
        pd.DatetimeIndex(["2024-01-04", "2024-01-05"]),
    )
    assert_index_equal(
        split.window_metadata["validation"].eligible_dates,
        pd.DatetimeIndex(["2024-01-07", "2024-01-08"]),
    )
    assert_index_equal(
        split.window_metadata["validation"].embargoed_dates,
        pd.DatetimeIndex(["2024-01-06"]),
    )
    assert_index_equal(
        split.window_metadata["test"].eligible_dates,
        pd.DatetimeIndex(["2024-01-12", "2024-01-13"]),
    )
    assert_index_equal(
        split.window_metadata["test"].purged_dates,
        pd.DatetimeIndex(["2024-01-14", "2024-01-15"]),
    )
    for name in ("train", "validation", "test"):
        metadata = split.window_metadata[name]
        assert_index_equal(metadata.label_warm_down_dates, metadata.purged_dates)


def test_split_002_requires_and_records_all_six_bounds() -> None:
    signature = inspect.signature(make_train_validation_test_split)
    for name in (
        "train_start",
        "train_end",
        "validation_start",
        "validation_end",
        "test_start",
        "test_end",
    ):
        assert signature.parameters[name].default is inspect.Parameter.empty

    split = _reference_split()
    summary = split.window_summary()

    assert split.train_start == pd.Timestamp("2024-01-01")
    assert split.train_end == pd.Timestamp("2024-01-05")
    assert split.validation_start == pd.Timestamp("2024-01-06")
    assert split.validation_end == pd.Timestamp("2024-01-10")
    assert split.test_start == pd.Timestamp("2024-01-11")
    assert split.test_end == pd.Timestamp("2024-01-15")
    assert summary.loc["train", "configured_start"] == pd.Timestamp("2024-01-01")
    assert summary.loc["train", "realized_start"] == pd.Timestamp("2024-01-01")
    assert summary.loc["test", "configured_end"] == pd.Timestamp("2024-01-15")
    assert summary.loc["test", "realized_end"] == pd.Timestamp("2024-01-15")


def test_split_003_inclusive_off_index_bounds_record_realized_endpoints() -> None:
    dates = pd.date_range("2024-01-01", periods=12, freq="D")
    split = make_train_validation_test_split(
        dates,
        train_start="2023-12-31 12:00",
        train_end="2024-01-03 12:00",
        validation_start="2024-01-04 12:00",
        validation_end="2024-01-07 12:00",
        test_start="2024-01-08 12:00",
        test_end="2024-01-11 12:00",
        label_kind="price_forward_return",
        label_derivation="test_close_to_close",
        label_horizon_rows=1,
    )

    assert_index_equal(split.train, dates[:3])
    assert_index_equal(split.validation, dates[4:7])
    assert_index_equal(split.test, dates[8:11])
    assert split.window_metadata["validation"].realized_start == dates[4]
    assert split.window_metadata["validation"].realized_end == dates[6]


def test_split_004_accepts_bounded_test_and_records_ignored_suffix() -> None:
    split = _reference_split()

    assert split.test_end < split.source_dates[-1]
    assert_index_equal(
        split.ignored_post_test_dates,
        pd.DatetimeIndex(["2024-01-16", "2024-01-17", "2024-01-18"]),
    )
    assert not split.all_dates.isin(split.ignored_post_test_dates).any()


def test_split_005_post_test_price_mutation_leaves_labels_and_metrics_equal() -> None:
    split = _reference_split()
    first_prices = _price_panel()
    second_prices = first_prices.copy()
    second_prices.loc[split.ignored_post_test_dates] *= 100.0

    first = make_price_forward_return_labels(first_prices, split)
    second = make_price_forward_return_labels(second_prices, split)

    assert_frame_equal(first, second)
    assert_frame_equal(
        summarize_label_availability(
            first,
            split,
            factors={"factor": first_prices},
        ),
        summarize_label_availability(
            second,
            split,
            factors={"factor": first_prices},
        ),
    )


def test_split_005_post_test_append_changes_only_suffix_metadata() -> None:
    extended_split = _reference_split()
    truncated_dates = pd.date_range("2024-01-01", "2024-01-15", freq="D")
    truncated_split = make_train_validation_test_split(
        truncated_dates,
        train_start="2024-01-01",
        train_end="2024-01-05",
        validation_start="2024-01-06",
        validation_end="2024-01-10",
        test_start="2024-01-11",
        test_end="2024-01-15",
        label_kind="price_forward_return",
        label_derivation="test_close_to_close",
        label_horizon_rows=2,
        embargo_rows=1,
    )
    extended_labels = make_price_forward_return_labels(
        _price_panel(),
        extended_split,
    )
    truncated_labels = make_price_forward_return_labels(
        _price_panel(truncated_dates),
        truncated_split,
    )

    for split_name in ("train", "validation", "test"):
        extended_metadata = extended_split.window_metadata[split_name]
        truncated_metadata = truncated_split.window_metadata[split_name]
        assert_index_equal(
            extended_metadata.eligible_dates,
            truncated_metadata.eligible_dates,
        )
        assert_index_equal(
            extended_metadata.excluded_dates,
            truncated_metadata.excluded_dates,
        )
        assert extended_metadata.status == truncated_metadata.status
        assert_frame_equal(
            extended_labels.loc[extended_metadata.eligible_dates],
            truncated_labels.loc[truncated_metadata.eligible_dates],
        )
    assert extended_split.ignored_post_test_dates.tolist() == list(
        pd.date_range("2024-01-16", "2024-01-18", freq="D")
    )
    assert truncated_split.ignored_post_test_dates.empty
    assert (
        extended_split.label_ledger.iloc[-1]["exclusion_reasons"]
        == ("label_crosses_window_end",)
    )
    assert (
        truncated_split.label_ledger.iloc[-1]["exclusion_reasons"]
        == ("label_end_unavailable",)
    )


def test_split_006_cross_edge_mutation_cannot_change_upstream_eligible_labels() -> None:
    split = _reference_split(embargo=0)
    prices = _price_panel()
    changed_validation = prices.copy()
    changed_validation.loc[split.validation] *= 10.0
    changed_test = prices.copy()
    changed_test.loc[split.test] *= 10.0

    baseline = make_price_forward_return_labels(prices, split)
    validation_changed = make_price_forward_return_labels(changed_validation, split)
    test_changed = make_price_forward_return_labels(changed_test, split)

    train_dates = split.window_metadata["train"].eligible_dates
    validation_dates = split.window_metadata["validation"].eligible_dates
    assert_frame_equal(baseline.loc[train_dates], validation_changed.loc[train_dates])
    assert_frame_equal(baseline.loc[validation_dates], test_changed.loc[validation_dates])


@pytest.mark.parametrize("horizon", [1, 3])
def test_split_007_purged_tail_matches_horizon(horizon: int) -> None:
    split = _reference_split(horizon=horizon, embargo=0)

    for name in ("train", "validation", "test"):
        assert len(split.window_metadata[name].purged_dates) == horizon


def test_split_008_irregular_calendar_uses_source_rows() -> None:
    dates = pd.DatetimeIndex(
        [
            "2024-01-02",
            "2024-01-05",
            "2024-01-20",
            "2024-02-01",
            "2024-03-15",
            "2024-04-01",
        ]
    )
    split = make_train_validation_test_split(
        dates,
        train_start="2024-01-02",
        train_end="2024-01-20",
        validation_start="2024-02-01",
        validation_end="2024-03-15",
        test_start="2024-04-01",
        test_end="2024-04-01",
        label_kind="price_forward_return",
        label_derivation="test_close_to_close",
        label_horizon_rows=2,
    )

    first = split.label_ledger.iloc[0]
    assert first["signal_date"] == pd.Timestamp("2024-01-02")
    assert first["label_end"] == pd.Timestamp("2024-01-20")


@pytest.mark.parametrize(
    ("embargo", "expected_validation", "expected_test"),
    [
        (0, [], []),
        (
            2,
            ["2024-01-06", "2024-01-07"],
            ["2024-01-11", "2024-01-12"],
        ),
    ],
)
def test_split_009_embargo_zero_and_two(
    embargo: int,
    expected_validation: list[str],
    expected_test: list[str],
) -> None:
    split = _reference_split(horizon=1, embargo=embargo)

    assert_index_equal(
        split.window_metadata["validation"].embargoed_dates,
        pd.DatetimeIndex(expected_validation),
    )
    assert_index_equal(
        split.window_metadata["test"].embargoed_dates,
        pd.DatetimeIndex(expected_test),
    )


def test_split_010_gap_can_fully_or_partially_satisfy_embargo() -> None:
    dates = pd.date_range("2024-01-01", periods=20, freq="D")
    fully_satisfied = make_train_validation_test_split(
        dates,
        train_start="2024-01-01",
        train_end="2024-01-03",
        validation_start="2024-01-07",
        validation_end="2024-01-09",
        test_start="2024-01-13",
        test_end="2024-01-15",
        label_kind="price_forward_return",
        label_derivation="test_close_to_close",
        label_horizon_rows=1,
        embargo_rows=3,
    )
    partial = make_train_validation_test_split(
        dates,
        train_start="2024-01-01",
        train_end="2024-01-03 12:00",
        validation_start="2024-01-04 12:00",
        validation_end="2024-01-09",
        test_start="2024-01-11",
        test_end="2024-01-15",
        label_kind="price_forward_return",
        label_derivation="test_close_to_close",
        label_horizon_rows=1,
        embargo_rows=3,
    )

    full_transition = fully_satisfied.transition_metadata["train_to_validation"]
    assert_index_equal(
        full_transition.gap_dates_consuming_embargo,
        pd.DatetimeIndex(["2024-01-04", "2024-01-05", "2024-01-06"]),
    )
    assert full_transition.downstream_embargoed_dates.empty

    partial_transition = partial.transition_metadata["train_to_validation"]
    assert_index_equal(
        partial_transition.inter_window_gap_dates,
        pd.DatetimeIndex(["2024-01-04"]),
    )
    assert_index_equal(
        partial_transition.gap_dates_consuming_embargo,
        pd.DatetimeIndex(["2024-01-04"]),
    )
    assert_index_equal(
        partial_transition.downstream_embargoed_dates,
        pd.DatetimeIndex(["2024-01-05", "2024-01-06"]),
    )


def test_split_011_purge_and_embargo_overlap_retains_both_reasons() -> None:
    split = make_train_validation_test_split(
        pd.date_range("2024-01-01", periods=8, freq="D"),
        train_start="2024-01-01",
        train_end="2024-01-02",
        validation_start="2024-01-03",
        validation_end="2024-01-04",
        test_start="2024-01-05",
        test_end="2024-01-06",
        label_kind="price_forward_return",
        label_derivation="test_close_to_close",
        label_horizon_rows=2,
        embargo_rows=2,
    )
    row = split.label_ledger.loc[
        split.label_ledger["signal_date"].eq(pd.Timestamp("2024-01-03"))
    ].iloc[0]

    assert bool(row["is_purged"])
    assert bool(row["is_embargoed"])
    assert not bool(row["is_eligible"])
    assert row["exclusion_reasons"] == (
        "label_crosses_window_end",
        "embargo",
    )


def test_split_012_empty_eligible_window_is_retained_and_invalid() -> None:
    split = make_train_validation_test_split(
        pd.date_range("2024-01-01", periods=6, freq="D"),
        train_start="2024-01-01",
        train_end="2024-01-02",
        validation_start="2024-01-03",
        validation_end="2024-01-04",
        test_start="2024-01-05",
        test_end="2024-01-06",
        label_kind="price_forward_return",
        label_derivation="test_close_to_close",
        label_horizon_rows=2,
    )
    labels = make_price_forward_return_labels(
        _price_panel(split.source_dates),
        split,
    )
    by_split = split_label_panel_by_train_validation_test(labels, split)
    availability = summarize_label_availability(
        labels,
        split,
        factors={"factor": _price_panel(split.source_dates)},
    )

    assert_index_equal(by_split["train"].index, split.train)
    assert by_split["train"].isna().all().all()
    assert split.window_metadata["train"].invalid_reason == "no_eligible_labels"
    assert availability.loc["train", "eligible_date_count"] == 0
    assert availability.loc["train", "status"] == "INVALID"


def test_split_013_warm_up_is_window_scoped_and_insufficient_history_raises() -> None:
    split = make_train_validation_test_split(
        _reference_dates(),
        train_start="2024-01-03",
        train_end="2024-01-06",
        validation_start="2024-01-08",
        validation_end="2024-01-11",
        test_start="2024-01-13",
        test_end="2024-01-16",
        label_kind="price_forward_return",
        label_derivation="test_close_to_close",
        label_horizon_rows=1,
        feature_warm_up_rows=2,
    )

    assert_index_equal(
        split.window_metadata["train"].feature_warm_up_dates,
        pd.DatetimeIndex(["2024-01-01", "2024-01-02"]),
    )
    assert_index_equal(
        split.window_metadata["validation"].feature_warm_up_dates,
        pd.DatetimeIndex(["2024-01-06", "2024-01-07"]),
    )
    assert not split.window_metadata["validation"].feature_warm_up_dates.isin(
        split.validation
    ).any()

    with pytest.raises(ValueError, match="feature warm-up"):
        make_train_validation_test_split(
            _reference_dates(),
            train_start="2024-01-02",
            train_end="2024-01-05",
            validation_start="2024-01-06",
            validation_end="2024-01-10",
            test_start="2024-01-11",
            test_end="2024-01-15",
            label_kind="price_forward_return",
            label_derivation="test_close_to_close",
            label_horizon_rows=1,
            feature_warm_up_rows=2,
        )


def test_split_014_ledger_has_one_exact_ordered_row_per_candidate() -> None:
    split = _reference_split()
    ledger = split.label_ledger

    assert list(ledger.columns) == [
        "split_name",
        "label_kind",
        "label_derivation",
        "signal_date",
        "label_start",
        "label_end",
        "is_purged",
        "is_embargoed",
        "is_eligible",
        "exclusion_reasons",
    ]
    assert len(ledger) == len(split.all_dates)
    assert_index_equal(
        pd.DatetimeIndex(ledger["signal_date"]),
        split.all_dates,
        check_names=False,
    )
    jan_4 = ledger.loc[ledger["signal_date"].eq(pd.Timestamp("2024-01-04"))].iloc[0]
    assert jan_4["label_start"] == pd.Timestamp("2024-01-04")
    assert jan_4["label_end"] == pd.Timestamp("2024-01-06")
    assert jan_4["exclusion_reasons"] == ("label_crosses_window_end",)


@pytest.mark.parametrize("mutation", ["missing", "reordered", "duplicate", "timezone"])
def test_split_015_source_panel_alignment_is_exact(mutation: str) -> None:
    split = _reference_split()
    panel = _price_panel()
    if mutation == "missing":
        panel = panel.iloc[:-1]
    elif mutation == "reordered":
        panel = panel.iloc[::-1]
    elif mutation == "duplicate":
        panel = pd.concat([panel.iloc[:1], panel])
    else:
        panel.index = panel.index.tz_localize("UTC")

    with pytest.raises((TypeError, ValueError), match="source index|sorted|duplicate"):
        split_panel_by_train_validation_test(
            panel,
            split,
            panel_role="feature",
        )


def test_split_017_label_slicer_rejects_unmasked_structurally_excluded_values() -> None:
    split = _reference_split()
    raw_unpurged = _price_panel().pct_change(fill_method=None).shift(-1)

    with pytest.raises(ValueError, match="structurally excluded"):
        split_label_panel_by_train_validation_test(raw_unpurged, split)


def test_split_017_feature_slicer_requires_an_explicit_feature_role() -> None:
    split = _reference_split()
    panel = _price_panel()

    with pytest.raises(TypeError, match="panel_role"):
        split_panel_by_train_validation_test(panel, split)  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="label targets"):
        split_panel_by_train_validation_test(
            panel,
            split,
            panel_role="label",  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("field", ["embargo_rows", "feature_warm_up_rows"])
@pytest.mark.parametrize("bad_value", [True, 1.5, -1])
def test_split_018_rejects_invalid_non_negative_integer_parameters(
    field: str,
    bad_value: object,
) -> None:
    kwargs = {
        "embargo_rows": 0,
        "feature_warm_up_rows": 0,
        field: bad_value,
    }
    with pytest.raises((TypeError, ValueError), match=field):
        make_train_validation_test_split(
            _reference_dates(),
            train_start="2024-01-01",
            train_end="2024-01-05",
            validation_start="2024-01-06",
            validation_end="2024-01-10",
            test_start="2024-01-11",
            test_end="2024-01-15",
            label_kind="price_forward_return",
            label_derivation="test_close_to_close",
            label_horizon_rows=1,
            **kwargs,
        )


@pytest.mark.parametrize("bad_horizon", [True, 0, -1, 1.5])
def test_split_018_rejects_invalid_price_horizon(bad_horizon: object) -> None:
    with pytest.raises((TypeError, ValueError), match="label_horizon_rows"):
        _reference_split(horizon=bad_horizon)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_horizon", [1, -1, True])
def test_split_018_rejects_invalid_synthetic_horizon(bad_horizon: object) -> None:
    with pytest.raises((TypeError, ValueError), match="label_horizon_rows"):
        _reference_split(
            horizon=bad_horizon,  # type: ignore[arg-type]
            label_kind="synthetic_same_row_response",
        )


@pytest.mark.parametrize(
    "bounds",
    [
        ("2024-01-05", "2024-01-04", "2024-01-06", "2024-01-10", "2024-01-11", "2024-01-15"),
        ("2024-01-01", "2024-01-05", "2024-01-05", "2024-01-10", "2024-01-11", "2024-01-15"),
        ("2024-01-01", "2024-01-05", "2024-01-06", "2024-01-10", "2024-01-10", "2024-01-15"),
    ],
)
def test_split_018_rejects_invalid_bound_order(bounds: tuple[str, ...]) -> None:
    with pytest.raises(ValueError, match="split boundaries"):
        make_train_validation_test_split(
            _reference_dates(),
            train_start=bounds[0],
            train_end=bounds[1],
            validation_start=bounds[2],
            validation_end=bounds[3],
            test_start=bounds[4],
            test_end=bounds[5],
            label_kind="price_forward_return",
            label_derivation="test_close_to_close",
            label_horizon_rows=1,
        )


def test_split_018_rejects_empty_window_and_timezone_mismatch() -> None:
    with pytest.raises(ValueError, match="validation split"):
        make_train_validation_test_split(
            _reference_dates(),
            train_start="2024-01-01",
            train_end="2024-01-03",
            validation_start="2024-02-01",
            validation_end="2024-02-02",
            test_start="2024-02-03",
            test_end="2024-02-04",
            label_kind="price_forward_return",
            label_derivation="test_close_to_close",
            label_horizon_rows=1,
        )

    with pytest.raises(ValueError, match="timezone"):
        make_train_validation_test_split(
            _reference_dates().tz_localize("UTC"),
            train_start="2024-01-01",
            train_end="2024-01-05",
            validation_start="2024-01-06",
            validation_end="2024-01-10",
            test_start="2024-01-11",
            test_end="2024-01-15",
            label_kind="price_forward_return",
            label_derivation="test_close_to_close",
            label_horizon_rows=1,
        )


@pytest.mark.parametrize(
    "corruption",
    ["duplicate_interval", "unordered_interval", "off_source_interval"],
)
def test_split_018_rejects_corrupted_label_intervals(
    corruption: str,
) -> None:
    split = _reference_split()
    corrupted_ledger = split.label_ledger.copy()
    if corruption == "duplicate_interval":
        corrupted_ledger.iloc[1] = corrupted_ledger.iloc[0]
    elif corruption == "unordered_interval":
        corrupted_ledger = corrupted_ledger.iloc[
            [1, 0, *range(2, len(corrupted_ledger))]
        ].reset_index(drop=True)
    else:
        corrupted_ledger.at[0, "label_end"] = pd.Timestamp("2030-01-01")
    corrupted = replace(split, label_ledger=corrupted_ledger)

    with pytest.raises(ValueError, match="label_ledger.*canonical"):
        make_price_forward_return_labels(_price_panel(), corrupted)


def test_split_018_rejects_forged_window_eligibility() -> None:
    split = _reference_split()
    window_metadata = dict(split.window_metadata)
    train = window_metadata["train"]
    window_metadata["train"] = replace(
        train,
        eligible_dates=train.eligible_dates.append(train.purged_dates[:1]),
    )
    corrupted = replace(split, window_metadata=window_metadata)

    with pytest.raises(ValueError, match="window_metadata.*canonical"):
        mask_label_panel_by_train_validation_test(
            _price_panel(),
            corrupted,
        )


def test_split_019_synthetic_same_row_ledger_is_honest() -> None:
    split = _reference_split(
        horizon=0,
        embargo=0,
        label_kind="synthetic_same_row_response",
    )

    assert split.label_kind == "synthetic_same_row_response"
    assert split.label_horizon_rows == 0
    assert split.label_derivation == "test_same_row_generator"
    assert (
        split.label_ledger["signal_date"] == split.label_ledger["label_start"]
    ).all()
    assert (
        split.label_ledger["signal_date"] == split.label_ledger["label_end"]
    ).all()
    assert not split.label_ledger["is_purged"].any()


def test_split_020_metadata_and_labels_are_deterministic() -> None:
    first = _reference_split()
    second = _reference_split()
    prices = _price_panel()

    assert first.metadata_as_dict() == second.metadata_as_dict()
    assert_frame_equal(first.label_ledger, second.label_ledger)
    assert_frame_equal(
        make_price_forward_return_labels(prices, first),
        make_price_forward_return_labels(prices, second),
    )


def test_split_021_raw_axes_are_retained_while_only_targets_are_masked() -> None:
    split = _reference_split()
    factor = _price_panel()
    raw_factor = split_panel_by_train_validation_test(
        factor,
        split,
        panel_role="feature",
    )
    labels = make_price_forward_return_labels(factor, split)
    targets = split_label_panel_by_train_validation_test(labels, split)

    for name in ("train", "validation", "test"):
        metadata = split.window_metadata[name]
        assert_index_equal(raw_factor[name].index, metadata.candidate_dates)
        assert_index_equal(targets[name].index, metadata.candidate_dates)
        assert_frame_equal(raw_factor[name], factor.loc[metadata.candidate_dates])
        assert targets[name].loc[metadata.excluded_dates].isna().all().all()


def test_split_022_consumer_missingness_is_separate_from_structural_flags() -> None:
    split = _reference_split(embargo=0)
    prices = _price_panel()
    labels = make_price_forward_return_labels(prices, split)
    factor = prices.copy()
    eligible = split.window_metadata["train"].eligible_dates
    labels.loc[eligible[0], "AAA"] = np.nan

    partial = summarize_label_availability(
        labels,
        split,
        factors={"factor": factor},
    )
    assert partial.loc["train", "valid_eligible_target_cells"] == 5
    assert partial.loc["train", "missing_eligible_target_cells"] == 1
    assert partial.loc["train", "usable_factor_label_pairs"] == 5
    assert split.window_metadata["train"].eligible_date_count == 3

    labels.loc[eligible] = np.nan
    missing = summarize_label_availability(
        labels,
        split,
        factors={"factor": factor},
    )
    assert missing.loc["train", "eligible_date_count"] == 3
    assert missing.loc["train", "usable_factor_label_pairs"] == 0
    assert not bool(missing.loc["train", "has_usable_label_pairs"])
    assert missing.loc["train", "invalid_reason"] == "no_usable_label_pairs"
    assert missing.loc["train", "status"] == "INVALID"


def test_label_mask_helper_accepts_series_and_preserves_name() -> None:
    split = _reference_split()
    labels = pd.Series(
        np.arange(len(split.source_dates), dtype=float),
        index=split.source_dates,
        name="benchmark",
    )
    masked = mask_label_panel_by_train_validation_test(labels, split)

    assert isinstance(masked, pd.Series)
    assert masked.name == "benchmark"
    assert_series_equal(
        masked.loc[split.window_metadata["train"].eligible_dates],
        labels.loc[split.window_metadata["train"].eligible_dates],
    )
    assert masked.loc[split.window_metadata["train"].excluded_dates].isna().all()


def test_split_module_has_no_data_trading_or_backtest_imports() -> None:
    source = inspect.getsource(validation)
    tree = ast.parse(source)
    forbidden_terms = {
        "backtest",
        "broker",
        "requests",
        "urllib",
        "yfinance",
        "alpaca",
        "ccxt",
        "reporting",
        "strategies",
    }
    imported_modules: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)

    for module_name in imported_modules:
        assert not any(term in module_name.lower() for term in forbidden_terms)

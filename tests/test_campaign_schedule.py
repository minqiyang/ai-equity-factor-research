"""22-session-month cutoff and fold fixtures."""

from __future__ import annotations

from campaign.schedule import build_campaign_schedule
from campaign_runner_v1_support import load_runner_fixture


def test_session_month_cutoff_excludes_continuous_only() -> None:
    fixture = load_runner_fixture("session_month_cutoff.json")
    built = build_campaign_schedule(**fixture["inputs"])
    expected = fixture["expected"]
    july_sessions = tuple(
        session
        for session in built.session_dates
        if session.startswith("2024-07-")
    )
    by_signal = {row.signal_date: row for row in built.signals}

    assert len(july_sessions) == expected["july_session_count"]
    june = by_signal[expected["june_signal"]["signal_date"]]
    july = by_signal[expected["july_signal"]["signal_date"]]
    assert june.execution_date == expected["june_signal"]["execution_date"]
    assert june.label_end_date == expected["june_signal"]["label_end_date"]
    assert (
        june.factor_label_complete
        is expected["june_signal"]["factor_label_complete"]
    )
    assert (
        june.continuous_included
        is expected["june_signal"]["continuous_included"]
    )
    assert july.execution_date == expected["july_signal"]["execution_date"]
    assert july.label_end_date == expected["july_signal"]["label_end_date"]
    assert (
        july.factor_label_complete
        is expected["july_signal"]["factor_label_complete"]
    )
    assert (
        july.continuous_included
        is expected["july_signal"]["continuous_included"]
    )
    assert built.campaign_invalid is expected["campaign_invalid"]
    assert built.campaign_invalid is not fixture["forbidden"]["campaign_invalid"]
    assert july.continuous_included is not fixture["forbidden"][
        "july_continuous_included"
    ]
    assert june.factor_label_complete
    assert [
        {
            "fold_year": fold.fold_year,
            "bound_end": fold.bound_end,
            "partial": fold.partial,
            "signal_dates": list(fold.signal_dates),
        }
        for fold in built.folds
    ] == expected["folds"]

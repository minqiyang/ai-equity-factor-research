"""Ordered final-state classification for the frozen diagnostic campaign."""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Integral, Real
from typing import Literal, TypeVar

from campaign.inference import FACTOR_ORDER, FactorVector


_T = TypeVar("_T")


DiagnosticState = Literal[
    "INVALID_DIAGNOSTIC",
    "INCONCLUSIVE_DIAGNOSTIC",
    "NEGATIVE_DIAGNOSTIC",
    "MIXED_DIAGNOSTIC",
    "POSITIVE_DIAGNOSTIC",
]


@dataclass(frozen=True)
class DiagnosticInputs:
    """Already-prepared inputs to the frozen ordered decision tree."""

    hard_valid: bool
    prefrozen_coverage_met: bool
    common_months: int
    bootstrap_support_all_three_factors: bool
    primary_matched_benchmark_comparisons_valid: bool
    secondary_spy_comparisons_valid: bool
    mean_rank_ics: FactorVector[float]
    holm_rejections: FactorVector[bool]
    active_return_10bps: FactorVector[float]
    active_return_25bps: FactorVector[float]
    common_case_positive_year_fractions: FactorVector[float]
    common_case_all_loyo_means_positive: FactorVector[bool]


def classify_diagnostic(inputs: DiagnosticInputs) -> DiagnosticState:
    """Evaluate the mutually exclusive frozen final-state rules in order."""

    _validate_inputs(inputs)
    mean_rank_ics = _values(inputs.mean_rank_ics)
    holm_rejections = _values(inputs.holm_rejections)

    if (
        not inputs.hard_valid
        or not inputs.primary_matched_benchmark_comparisons_valid
        or any(
            rejected and mean_rank_ic <= 0.0
            for rejected, mean_rank_ic in zip(
                holm_rejections,
                mean_rank_ics,
                strict=True,
            )
        )
    ):
        return "INVALID_DIAGNOSTIC"
    if (
        not inputs.prefrozen_coverage_met
        or inputs.common_months < 60
        or not inputs.bootstrap_support_all_three_factors
    ):
        return "INCONCLUSIVE_DIAGNOSTIC"

    holm_supported = tuple(
        rejected and mean_rank_ic > 0.0
        for rejected, mean_rank_ic in zip(
            holm_rejections,
            mean_rank_ics,
            strict=True,
        )
    )
    coherent = tuple(
        supported
        and return_10bps > 0.0
        and return_25bps > 0.0
        and positive_year_fraction > 0.5
        and loyo_positive
        for (
            supported,
            return_10bps,
            return_25bps,
            positive_year_fraction,
            loyo_positive,
        ) in zip(
            holm_supported,
            _values(inputs.active_return_10bps),
            _values(inputs.active_return_25bps),
            _values(inputs.common_case_positive_year_fractions),
            _values(inputs.common_case_all_loyo_means_positive),
            strict=True,
        )
    )
    if any(coherent):
        return "POSITIVE_DIAGNOSTIC"
    if any(holm_supported):
        return "MIXED_DIAGNOSTIC"
    if all(value < 0.0 for value in mean_rank_ics):
        return "NEGATIVE_DIAGNOSTIC"
    return "INCONCLUSIVE_DIAGNOSTIC"


def _validate_inputs(inputs: DiagnosticInputs) -> None:
    if not isinstance(inputs, DiagnosticInputs):
        raise TypeError("inputs must be DiagnosticInputs")
    for name in (
        "hard_valid",
        "prefrozen_coverage_met",
        "bootstrap_support_all_three_factors",
        "primary_matched_benchmark_comparisons_valid",
        "secondary_spy_comparisons_valid",
    ):
        if not isinstance(getattr(inputs, name), bool):
            raise TypeError(f"{name} must be a bool")
    if isinstance(inputs.common_months, bool) or not isinstance(
        inputs.common_months, Integral
    ):
        raise TypeError("common_months must be an integer")
    if inputs.common_months < 0:
        raise ValueError("common_months must be nonnegative")

    _validate_real_vector(inputs.mean_rank_ics, name="mean_rank_ics")
    _validate_bool_vector(inputs.holm_rejections, name="holm_rejections")
    _validate_real_vector(inputs.active_return_10bps, name="active_return_10bps")
    _validate_real_vector(inputs.active_return_25bps, name="active_return_25bps")
    fractions = _validate_real_vector(
        inputs.common_case_positive_year_fractions,
        name="common_case_positive_year_fractions",
    )
    if any(value < 0.0 or value > 1.0 for value in fractions):
        raise ValueError(
            "common_case_positive_year_fractions must be between zero and one"
        )
    _validate_bool_vector(
        inputs.common_case_all_loyo_means_positive,
        name="common_case_all_loyo_means_positive",
    )


def _validate_real_vector(
    vector: FactorVector[object],
    *,
    name: str,
) -> tuple[float, float, float]:
    if not isinstance(vector, FactorVector):
        raise TypeError(f"{name} must be a FactorVector")
    validated: list[float] = []
    for factor_id, value in zip(FACTOR_ORDER, _values(vector), strict=True):
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError(
                f"{name}.{factor_id} must be a real non-Boolean scalar"
            )
        numeric = float(value)
        if not math.isfinite(numeric):
            raise ValueError(f"{name}.{factor_id} must be finite")
        validated.append(numeric)
    return tuple(validated)


def _validate_bool_vector(
    vector: FactorVector[object],
    *,
    name: str,
) -> tuple[bool, bool, bool]:
    if not isinstance(vector, FactorVector):
        raise TypeError(f"{name} must be a FactorVector")
    values = _values(vector)
    for factor_id, value in zip(FACTOR_ORDER, values, strict=True):
        if not isinstance(value, bool):
            raise TypeError(f"{name}.{factor_id} must be a bool")
    return values


def _values(vector: FactorVector[_T]) -> tuple[_T, _T, _T]:
    return (vector.MOM_12_1, vector.REV_1M, vector.LOW_VOL_3M)


__all__ = ["DiagnosticInputs", "DiagnosticState", "classify_diagnostic"]

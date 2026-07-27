"""Portfolio target-weight constraints for simulated research."""

from __future__ import annotations

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_complex_dtype, is_numeric_dtype


_GROSS_EXPOSURE_TOLERANCE = 1e-12
_NUMPY_INTEGER_SCALAR_TYPES = frozenset(
    np.dtype(typecode).type for typecode in np.typecodes["AllInteger"]
)
_NUMPY_FLOAT_SCALAR_TYPES = frozenset(
    np.dtype(typecode).type for typecode in np.typecodes["Float"]
)
_EXACT_REAL_SCALAR_TYPES = frozenset(
    {
        int,
        float,
        *_NUMPY_INTEGER_SCALAR_TYPES,
        *_NUMPY_FLOAT_SCALAR_TYPES,
    }
)


def apply_long_only_position_cap(
    target_weights: pd.DataFrame,
    *,
    max_position_weight: float,
) -> pd.DataFrame:
    """Clip long-only targets at a per-position maximum without renormalizing."""

    _validate_target_weights(target_weights)
    cap = _read_exact_finite_real_scalar(max_position_weight)
    if cap is None or not 0.0 < cap <= 1.0:
        raise ValueError(
            "max_position_weight must be greater than 0 and no greater than 1"
        )

    return target_weights.astype(float).clip(upper=cap)


def _read_exact_finite_real_scalar(value: object) -> float | None:
    if type(value) not in _EXACT_REAL_SCALAR_TYPES:
        return None
    try:
        numeric = float(value)
    except (OverflowError, TypeError, ValueError):
        return None
    return numeric if np.isfinite(numeric) else None


def _validate_target_weights(target_weights: pd.DataFrame) -> None:
    if not isinstance(target_weights, pd.DataFrame):
        raise TypeError("target_weights must be a pandas DataFrame")
    if target_weights.empty:
        raise ValueError("target_weights must not be empty")
    if (
        not isinstance(target_weights.index, pd.DatetimeIndex)
        or target_weights.index.has_duplicates
        or not target_weights.index.is_monotonic_increasing
        or target_weights.columns.has_duplicates
    ):
        raise ValueError(
            "target_weights must have unique assets and unique, increasing dates"
        )
    if any(
        is_bool_dtype(dtype)
        or is_complex_dtype(dtype)
        or not is_numeric_dtype(dtype)
        for dtype in target_weights.dtypes
    ):
        raise TypeError(
            "target_weights must contain finite non-negative real weights"
        )

    values = target_weights.to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values < 0.0).any():
        raise ValueError(
            "target_weights must contain finite non-negative real weights"
        )
    if target_weights.sum(axis=1).gt(1.0 + _GROSS_EXPOSURE_TOLERANCE).any():
        raise ValueError("target_weights gross exposure must not exceed 1")

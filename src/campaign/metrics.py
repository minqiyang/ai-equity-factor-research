"""Path metrics on complete valid return and equity series."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math
from numbers import Integral, Real

from campaign.paths import IntervalPoint


_REASON_INSUFFICIENT = "INSUFFICIENT_VALUES"
_REASON_INVALID_RETURN = "RETURN_INVALID"
_REASON_ZERO_VOLATILITY = "ZERO_VOLATILITY"
_REASON_NON_FINITE = "METRIC_NON_FINITE"
_REASON_LENGTH = "SERIES_LENGTH_MISMATCH"
_REASON_INVALID_POINT = "INTERVAL_INVALID"


@dataclass(frozen=True)
class ScalarMetric:
    """One retained scalar metric or an invalid/missing reason."""

    value: float | None
    valid: bool
    reason: str | None


@dataclass(frozen=True)
class ContributionTotal:
    """Arithmetic contribution total for one listing or calendar year."""

    listing_key: bytes | None
    year: int | None
    gross: float
    cost: float


@dataclass(frozen=True)
class ContributionAggregate:
    """Valid-point contribution totals that sum to the path series."""

    by_listing: tuple[ContributionTotal, ...]
    by_year: tuple[ContributionTotal, ...]
    gross_sum: float | None
    cost_sum: float | None
    valid: bool
    reason: str | None


def annualized_geometric_return(
    returns: Sequence[object],
    periods_per_year: object,
) -> ScalarMetric:
    """(product(1 + r)) ** (periods_per_year / n) - 1 on a complete series."""

    parsed = _parse_return_series(returns)
    if not parsed.valid:
        return ScalarMetric(None, False, parsed.reason)
    count = len(parsed.values)
    periods = _positive_int(periods_per_year, "periods_per_year")
    if count == 0:
        return ScalarMetric(None, False, _REASON_INSUFFICIENT)
    product = 1.0
    for value in parsed.values:
        product *= 1.0 + value
    if product <= 0.0 or not math.isfinite(product):
        return ScalarMetric(None, False, _REASON_NON_FINITE)
    result = product ** (periods / count) - 1.0
    if not math.isfinite(result):
        return ScalarMetric(None, False, _REASON_NON_FINITE)
    return ScalarMetric(result, True, None)


def annualized_volatility(
    returns: Sequence[object],
    periods_per_year: object,
    sample_std_ddof: object,
) -> ScalarMetric:
    """Daily sample standard deviation times sqrt(periods_per_year)."""

    parsed = _parse_return_series(returns)
    if not parsed.valid:
        return ScalarMetric(None, False, parsed.reason)
    periods = _positive_int(periods_per_year, "periods_per_year")
    deviation = _sample_std(parsed.values, sample_std_ddof)
    if not deviation.valid:
        return deviation
    if deviation.value is None:
        return ScalarMetric(None, False, _REASON_INSUFFICIENT)
    result = deviation.value * math.sqrt(periods)
    if not math.isfinite(result):
        return ScalarMetric(None, False, _REASON_NON_FINITE)
    return ScalarMetric(result, True, None)


def zero_cash_rate_sharpe_style(
    returns: Sequence[object],
    periods_per_year: object,
    sample_std_ddof: object,
) -> ScalarMetric:
    """Mean daily return over sample std, times sqrt(periods_per_year)."""

    parsed = _parse_return_series(returns)
    if not parsed.valid:
        return ScalarMetric(None, False, parsed.reason)
    periods = _positive_int(periods_per_year, "periods_per_year")
    if not parsed.values:
        return ScalarMetric(None, False, _REASON_INSUFFICIENT)
    deviation = _sample_std(parsed.values, sample_std_ddof)
    if not deviation.valid:
        return deviation
    if deviation.value is None:
        return ScalarMetric(None, False, _REASON_INSUFFICIENT)
    if deviation.value == 0.0:
        return ScalarMetric(None, False, _REASON_ZERO_VOLATILITY)
    mean = sum(parsed.values) / len(parsed.values)
    result = (mean / deviation.value) * math.sqrt(periods)
    if not math.isfinite(result):
        return ScalarMetric(None, False, _REASON_NON_FINITE)
    return ScalarMetric(result, True, None)


def max_drawdown(equity: Sequence[object]) -> ScalarMetric:
    """Peak-to-trough drawdown on a supplied equity curve."""

    if (
        isinstance(equity, (str, bytes, bytearray))
        or not isinstance(equity, Sequence)
    ):
        raise TypeError("equity must be a sequence")
    values: list[float] = []
    for item in equity:
        if not _is_finite_real(item):
            return ScalarMetric(None, False, _REASON_INVALID_RETURN)
        values.append(float(item))
    if not values:
        return ScalarMetric(None, False, _REASON_INSUFFICIENT)
    peak = values[0]
    worst = 0.0
    for value in values:
        if value > peak:
            peak = value
        if peak <= 0.0:
            return ScalarMetric(None, False, _REASON_NON_FINITE)
        drawdown = value / peak - 1.0
        if drawdown < worst:
            worst = drawdown
    if not math.isfinite(worst):
        return ScalarMetric(None, False, _REASON_NON_FINITE)
    return ScalarMetric(worst, True, None)


def cost_drag(
    gross_returns: Sequence[object],
    net_returns: Sequence[object],
    periods_per_year: object,
) -> ScalarMetric:
    """Gross annualized geometric return minus net annualized return."""

    gross = annualized_geometric_return(gross_returns, periods_per_year)
    net = annualized_geometric_return(net_returns, periods_per_year)
    if not gross.valid or not net.valid:
        return ScalarMetric(
            None,
            False,
            gross.reason if not gross.valid else net.reason,
        )
    if gross.value is None or net.value is None:
        return ScalarMetric(None, False, _REASON_INSUFFICIENT)
    result = gross.value - net.value
    if not math.isfinite(result):
        return ScalarMetric(None, False, _REASON_NON_FINITE)
    return ScalarMetric(result, True, None)


def annualized_active_return(
    strategy_returns: Sequence[object],
    benchmark_returns: Sequence[object],
    periods_per_year: object,
) -> ScalarMetric:
    """Strategy annualized geometric return minus benchmark's."""

    if (
        isinstance(strategy_returns, (str, bytes, bytearray))
        or not isinstance(strategy_returns, Sequence)
    ):
        raise TypeError("strategy_returns must be a sequence")
    if (
        isinstance(benchmark_returns, (str, bytes, bytearray))
        or not isinstance(benchmark_returns, Sequence)
    ):
        raise TypeError("benchmark_returns must be a sequence")
    if len(strategy_returns) != len(benchmark_returns):
        return ScalarMetric(None, False, _REASON_LENGTH)
    strategy = annualized_geometric_return(
        strategy_returns,
        periods_per_year,
    )
    benchmark = annualized_geometric_return(
        benchmark_returns,
        periods_per_year,
    )
    if not strategy.valid or not benchmark.valid:
        return ScalarMetric(
            None,
            False,
            strategy.reason if not strategy.valid else benchmark.reason,
        )
    if strategy.value is None or benchmark.value is None:
        return ScalarMetric(None, False, _REASON_INSUFFICIENT)
    result = strategy.value - benchmark.value
    if not math.isfinite(result):
        return ScalarMetric(None, False, _REASON_NON_FINITE)
    return ScalarMetric(result, True, None)


def aggregate_contributions(
    points: Sequence[IntervalPoint],
) -> ContributionAggregate:
    """Sum valid interval contributions by listing key and calendar year."""

    if (
        isinstance(points, (str, bytes, bytearray))
        or not isinstance(points, Sequence)
    ):
        raise TypeError("points must be a sequence")
    by_listing: dict[bytes, list[float]] = {}
    by_year: dict[int, list[float]] = {}
    gross_sum = 0.0
    cost_sum = 0.0
    for point in points:
        if not isinstance(point, IntervalPoint):
            raise TypeError("points must contain IntervalPoint values")
        if not point.valid:
            return ContributionAggregate(
                by_listing=(),
                by_year=(),
                gross_sum=None,
                cost_sum=None,
                valid=False,
                reason=_REASON_INVALID_POINT,
            )
        year = _year_from_session(point.session_date)
        keys = set(point.gross_contributions) | set(point.cost_contributions)
        interval_gross = 0.0
        interval_cost = 0.0
        for listing_key in keys:
            if not isinstance(listing_key, bytes) or not listing_key:
                raise TypeError("contribution keys must be nonempty bytes")
            gross = float(point.gross_contributions.get(listing_key, 0.0))
            cost = float(point.cost_contributions.get(listing_key, 0.0))
            listing = by_listing.setdefault(listing_key, [0.0, 0.0])
            listing[0] += gross
            listing[1] += cost
            interval_gross += gross
            interval_cost += cost
        year_bucket = by_year.setdefault(year, [0.0, 0.0])
        year_bucket[0] += interval_gross
        year_bucket[1] += interval_cost
        gross_sum += interval_gross
        cost_sum += interval_cost
    return ContributionAggregate(
        by_listing=tuple(
            ContributionTotal(key, None, values[0], values[1])
            for key, values in sorted(by_listing.items())
        ),
        by_year=tuple(
            ContributionTotal(None, year, values[0], values[1])
            for year, values in sorted(by_year.items())
        ),
        gross_sum=gross_sum,
        cost_sum=cost_sum,
        valid=True,
        reason=None,
    )


@dataclass(frozen=True)
class _ParsedReturns:
    values: tuple[float, ...]
    valid: bool
    reason: str | None


def _parse_return_series(returns: Sequence[object]) -> _ParsedReturns:
    if (
        isinstance(returns, (str, bytes, bytearray))
        or not isinstance(returns, Sequence)
    ):
        raise TypeError("returns must be a sequence")
    values: list[float] = []
    for item in returns:
        if not _is_finite_real(item):
            return _ParsedReturns((), False, _REASON_INVALID_RETURN)
        values.append(float(item))
    return _ParsedReturns(tuple(values), True, None)


def _sample_std(
    values: Sequence[float],
    sample_std_ddof: object,
) -> ScalarMetric:
    ddof = _nonneg_int(sample_std_ddof, "sample_std_ddof")
    count = len(values)
    if count <= ddof:
        return ScalarMetric(None, False, _REASON_INSUFFICIENT)
    mean = sum(values) / count
    variance = sum((value - mean) ** 2 for value in values) / (count - ddof)
    if variance < 0.0 or not math.isfinite(variance):
        return ScalarMetric(None, False, _REASON_NON_FINITE)
    return ScalarMetric(math.sqrt(variance), True, None)


def _year_from_session(session_date: str) -> int:
    if not isinstance(session_date, str) or len(session_date) < 4:
        raise ValueError("session_date must be strict YYYY-MM-DD")
    return int(session_date[:4])


def _is_finite_real(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, Real):
        return False
    numeric = float(value)
    return math.isfinite(numeric)


def _nonneg_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer")
    integer = int(value)
    if integer < 0:
        raise ValueError(f"{name} must be nonnegative")
    return integer


def _positive_int(value: object, name: str) -> int:
    integer = _nonneg_int(value, name)
    if integer < 1:
        raise ValueError(f"{name} must be positive")
    return integer


__all__ = [
    "ContributionAggregate",
    "ContributionTotal",
    "ScalarMetric",
    "aggregate_contributions",
    "annualized_active_return",
    "annualized_geometric_return",
    "annualized_volatility",
    "cost_drag",
    "max_drawdown",
    "zero_cash_rate_sharpe_style",
]

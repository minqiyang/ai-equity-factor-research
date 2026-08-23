"""Equal-weight and random-rank targets plus the episode diagnostic return."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
import hashlib
import math
from numbers import Real
from types import MappingProxyType

import numpy as np

from campaign.deciles import top_decile_count
from campaign.eligibility import FrozenDecisionTime
from campaign.registry import factor_spec


_REASON_ZERO_TARGET = "ZERO_TARGET"
_REASON_CONSTITUENT_RETURN_MISSING = "CONSTITUENT_RETURN_MISSING"
_REASON_CONSTITUENT_RETURN_INVALID = "CONSTITUENT_RETURN_INVALID"
_BIT_GENERATORS = {
    "PCG64DXSM": np.random.PCG64DXSM,
}


@dataclass(frozen=True)
class WeightTarget:
    """One role-labeled frozen target mapping."""

    weights: MappingProxyType[bytes, float]
    formable: bool
    role: str


@dataclass(frozen=True)
class RandomRankResult:
    """Random-rank target, or a retained invalid zero target."""

    weights: MappingProxyType[bytes, float]
    formable: bool
    permutation: tuple[int, ...] | None
    selected_keys: tuple[bytes, ...]
    preimage: str | None
    preimage_sha256: str | None
    seed: int | None
    consumed_rng: bool


@dataclass(frozen=True)
class EpisodeReturn:
    """One retained static-episode gross return or invalid/missing reason."""

    value: float | None
    valid: bool
    reason: str | None


def equal_weight_universe_target(
    frozen: FrozenDecisionTime,
    role: str,
) -> WeightTarget:
    """Serialize the frozen matched-universe target under a baseline role."""

    if not isinstance(frozen, FrozenDecisionTime):
        raise TypeError("frozen must be FrozenDecisionTime")
    if not isinstance(role, str) or not role:
        raise ValueError("role must be a nonempty string")
    return WeightTarget(
        weights=frozen.matched_benchmark_target,
        formable=frozen.benchmark_formable,
        role=role,
    )


def random_rank_target(
    frozen: FrozenDecisionTime,
    factor_id: str,
    signal_date: str,
    scheme_id: str,
    seed_version: str,
    generator_name: str,
) -> RandomRankResult:
    """Select the remainder-first top decile from one PCG64DXSM permutation."""

    if not isinstance(frozen, FrozenDecisionTime):
        raise TypeError("frozen must be FrozenDecisionTime")
    factor_spec(factor_id)
    _strict_date(signal_date)
    if not isinstance(scheme_id, str) or not scheme_id:
        raise ValueError("scheme_id must be a nonempty string")
    if not isinstance(seed_version, str) or not seed_version:
        raise ValueError("seed_version must be a nonempty string")
    if not isinstance(generator_name, str) or not generator_name:
        raise ValueError("generator_name must be a nonempty string")
    if frozen.zero_target_triggers:
        return RandomRankResult(
            weights=MappingProxyType({}),
            formable=False,
            permutation=None,
            selected_keys=(),
            preimage=None,
            preimage_sha256=None,
            seed=None,
            consumed_rng=False,
        )

    ordered_keys = tuple(
        sorted(item.listing_key for item in frozen.ordered_eligible)
    )
    selected_count = top_decile_count(len(ordered_keys))
    preimage = "|".join((scheme_id, seed_version, factor_id, signal_date))
    digest = hashlib.sha256(preimage.encode("ascii")).hexdigest()
    seed = int(digest[:16], 16)
    try:
        bit_generator = _BIT_GENERATORS[generator_name]
    except KeyError:
        raise ValueError(generator_name) from None
    rng = np.random.Generator(bit_generator(seed))
    permutation = tuple(int(index) for index in rng.permutation(len(ordered_keys)))
    selected_keys = tuple(
        ordered_keys[index] for index in permutation[:selected_count]
    )
    weight = 1.0 / selected_count
    return RandomRankResult(
        weights=MappingProxyType(
            {key: weight for key in sorted(selected_keys)}
        ),
        formable=True,
        permutation=permutation,
        selected_keys=selected_keys,
        preimage=preimage,
        preimage_sha256=digest,
        seed=seed,
        consumed_rng=True,
    )


def episode_gross_return(
    weights: Mapping[bytes, object],
    constituent_returns: Mapping[bytes, object],
) -> EpisodeReturn:
    """Return the static frozen-target episode sum of simple constituent returns."""

    if not isinstance(weights, Mapping):
        raise TypeError("weights must be a mapping")
    if not isinstance(constituent_returns, Mapping):
        raise TypeError("constituent_returns must be a mapping")
    if not weights:
        return EpisodeReturn(None, False, _REASON_ZERO_TARGET)

    total = 0.0
    for listing_key, weight in weights.items():
        if not isinstance(listing_key, bytes) or not listing_key:
            raise TypeError("weights keys must be nonempty bytes")
        numeric_weight = _finite_real(weight, "weight")
        if numeric_weight < 0.0:
            raise ValueError("weights must be nonnegative")
        if listing_key not in constituent_returns:
            return EpisodeReturn(
                None,
                False,
                _REASON_CONSTITUENT_RETURN_MISSING,
            )
        raw_return = constituent_returns[listing_key]
        if raw_return is None:
            return EpisodeReturn(
                None,
                False,
                _REASON_CONSTITUENT_RETURN_MISSING,
            )
        try:
            numeric_return = _finite_real(raw_return, "constituent_return")
        except (TypeError, ValueError):
            return EpisodeReturn(
                None,
                False,
                _REASON_CONSTITUENT_RETURN_INVALID,
            )
        total += numeric_weight * numeric_return
    return EpisodeReturn(total, True, None)


def _strict_date(value: object) -> date:
    if not isinstance(value, str):
        raise ValueError("date must be strict YYYY-MM-DD")
    parsed = date.fromisoformat(value)
    if len(value) != 10 or parsed.isoformat() != value:
        raise ValueError("date must be strict YYYY-MM-DD")
    return parsed


def _finite_real(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real non-Boolean scalar")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError(f"{name} must be finite")
    return numeric


__all__ = [
    "EpisodeReturn",
    "RandomRankResult",
    "WeightTarget",
    "episode_gross_return",
    "equal_weight_universe_target",
    "random_rank_target",
]

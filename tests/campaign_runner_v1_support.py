"""Fixture loading and T-7 scan helpers for campaign runner v1 tests."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


FIXTURE_ROOT = (
    Path(__file__).resolve().parent / "fixtures" / "campaign_runner_v1"
)
CAMPAIGN_ROOT = Path(__file__).resolve().parents[1] / "src" / "campaign"


def load_runner_fixture(name: str) -> dict[str, Any]:
    """Load one committed campaign_runner_v1 JSON fixture."""

    return json_object((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def json_object(text: str) -> dict[str, Any]:
    """Parse a JSON object from committed fixture text."""

    import json

    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise TypeError("fixture root must be an object")
    return payload


def decode_fixture_anchor(item: dict[str, Any]) -> object:
    """Materialize a fixture anchor, including IEEE non-finite sentinels."""

    if "ieee" in item:
        return float(item["ieee"])
    return item["value"]


def encode_runner_listing_key(
    exchange: str,
    ticker: str,
    effective_from: str,
    effective_to: str | None,
) -> bytes:
    """Encode one synthetic fixture listing key."""

    from campaign.listing_key import encode_listing_lineage_key_v1

    return encode_listing_lineage_key_v1(
        exchange,
        ticker,
        effective_from,
        effective_to,
    )


def fixture_ticker(prefix: str, width: int, index: int) -> str:
    """Format a synthetic T000-style ticker label."""

    return f"{prefix}{index:0{width}d}"


def expand_encoded_keys(spec: dict[str, Any]) -> tuple[bytes, ...]:
    """Encode a compact ticker-sequence listing-key spec."""

    return tuple(
        encode_runner_listing_key(
            spec["exchange"],
            fixture_ticker(spec["ticker_prefix"], spec["ticker_width"], index),
            spec["effective_from"],
            spec["effective_to"],
        )
        for index in range(spec["count"])
    )


def listing_decisions_from_numeric_spec(
    spec: dict[str, Any],
) -> tuple[Any, ...]:
    """Build eligible ListingDecision values from a compact numeric spec."""

    from campaign.eligibility import ListingDecision

    key_spec = dict(spec["key_spec"])
    key_spec["count"] = spec["count"]
    keys = list(expand_encoded_keys(key_spec))
    if spec.get("duplicate_last"):
        keys = [keys[0], keys[0]]
    values: list[float] = []
    for index in range(len(keys)):
        if spec["value_mode"] == "constant":
            values.append(float(spec["constant_value"]))
        else:
            values.append(float(index))
    return tuple(
        ListingDecision(key, True, None, value)
        for key, value in zip(keys, values, strict=True)
    )


def expand_decision_time_listings(spec: dict[str, Any]) -> tuple[Any, ...]:
    """Expand a compact at-t listing spec into DecisionTimeListing values."""

    from campaign.eligibility import DecisionTimeListing

    rows = spec.get("rows")
    if rows is None:
        defaults = spec["row_defaults"]
        rows = [
            {
                **defaults,
                "ticker": fixture_ticker(
                    spec["ticker_prefix"],
                    spec["ticker_width"],
                    index,
                ),
            }
            for index in range(spec["count"])
        ]

    listings: list[Any] = []
    for row in rows:
        ticker = row["ticker"]
        identity = row.get(
            "target_identity",
            {
                "resolved_permanent_security_id": f"SECURITY-{ticker}",
                "resolved_listing_id": f"LISTING-{ticker}",
                "resolved_listing_episode_id": f"EPISODE-{ticker}",
            },
        )
        alias_chain = row.get("alias_chain")
        if alias_chain is None:
            alias_chain = [
                {
                    **identity,
                    "source_exchange": spec["exchange"],
                    "source_ticker": ticker,
                    "alias_effective_from": spec["effective_from"],
                    "alias_effective_to": spec["effective_to"],
                    "lineage_resolution_evidence_id": f"EVIDENCE-{ticker}",
                    "transition_to_next": "TARGET_ALIAS",
                }
            ]
        lineage_anchors = row.get("lineage_anchors")
        if lineage_anchors is None:
            template = spec["lineage_template"]
            lineage_anchors = [
                {
                    **alias_chain[-1],
                    "session_date": session,
                    "adjusted_close": price,
                }
                for session, price in zip(
                    template["anchor_sessions"],
                    row["referenced_anchors"],
                    strict=True,
                )
            ]
        listings.append(
            DecisionTimeListing(
                listing_key=encode_runner_listing_key(
                    spec["exchange"],
                    ticker,
                    spec["effective_from"],
                    spec["effective_to"],
                ),
                in_universe_at_t=row["in_universe_at_t"],
                terminal_blocked_at_t=row["terminal_blocked_at_t"],
                lookback_addressable_at_t=row["lookback_addressable_at_t"],
                referenced_anchors=tuple(row["referenced_anchors"]),
                lineage_anchors=tuple(lineage_anchors),
                target_identity=identity,
                alias_chain=tuple(alias_chain),
            )
        )
    return tuple(listings)


def collect_disallowed_factor_id_literals_from_source(
    source: str,
    module_name: str,
    factor_ids: tuple[str, ...],
) -> tuple[tuple[int, str], ...]:
    """Collect disallowed factor-ID literals from one module's source."""

    tree = ast.parse(source, filename=module_name)
    docstring_nodes = _docstring_constant_ids(tree)
    allowed_nodes = _allowed_owner_constant_ids(tree, module_name)
    hits: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant):
            continue
        if not isinstance(node.value, str) or node.value not in factor_ids:
            continue
        if id(node) in docstring_nodes or id(node) in allowed_nodes:
            continue
        hits.append((node.lineno, node.value))
    return tuple(hits)


def collect_disallowed_factor_id_literals(
    factor_ids: tuple[str, ...],
) -> tuple[tuple[str, int, str], ...]:
    """Collect factor-ID string literals outside the sole allowed owner site."""

    hits: list[tuple[str, int, str]] = []
    for module_path in sorted(CAMPAIGN_ROOT.glob("*.py")):
        for lineno, value in collect_disallowed_factor_id_literals_from_source(
            module_path.read_text(encoding="utf-8"),
            module_path.name,
            factor_ids,
        ):
            hits.append((module_path.name, lineno, value))
    return tuple(hits)


def _docstring_constant_ids(tree: ast.AST) -> set[int]:
    node_ids: set[int] = set()

    def consider(body: list[ast.stmt]) -> None:
        if not body:
            return
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            node_ids.add(id(first.value))

    if isinstance(tree, ast.Module):
        consider(tree.body)
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            consider(node.body)
    return node_ids


def _allowed_owner_constant_ids(
    tree: ast.AST,
    module_name: str,
) -> set[int]:
    if module_name != "inference.py" or not isinstance(tree, ast.Module):
        return set()
    allowed: set[int] = set()
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id != "FACTOR_ORDER":
            continue
        for child in ast.walk(node):
            if isinstance(child, ast.Constant):
                allowed.add(id(child))
    return allowed


def runner_weight_map(
    exchange: str,
    effective_from: str,
    effective_to: str | None,
    weights_by_ticker: dict[str, float],
) -> dict[bytes, float]:
    """Encode a ticker-weight mapping into listing-key weights."""

    return {
        encode_runner_listing_key(
            exchange,
            ticker,
            effective_from,
            effective_to,
        ): float(weight)
        for ticker, weight in weights_by_ticker.items()
    }


def runner_return_map(
    exchange: str,
    effective_from: str,
    effective_to: str | None,
    values_by_ticker: dict[str, object],
) -> dict[bytes, object]:
    """Encode a ticker-return mapping into listing-key observations."""

    return {
        encode_runner_listing_key(
            exchange,
            ticker,
            effective_from,
            effective_to,
        ): value
        for ticker, value in values_by_ticker.items()
    }


def runner_holding_interval(
    session_date: str,
    exchange: str,
    effective_from: str,
    effective_to: str | None,
    held_returns_by_ticker: dict[str, object],
    reset_weights_by_ticker: dict[str, object] | None,
) -> Any:
    """Build one campaign HoldingInterval from ticker-keyed fixture maps."""

    from campaign.paths import holding_interval

    reset = None
    if reset_weights_by_ticker is not None:
        reset = runner_weight_map(
            exchange,
            effective_from,
            effective_to,
            {
                ticker: float(weight)  # type: ignore[arg-type]
                for ticker, weight in reset_weights_by_ticker.items()
            },
        )
    return holding_interval(
        session_date,
        runner_return_map(
            exchange,
            effective_from,
            effective_to,
            held_returns_by_ticker,
        ),
        reset,
    )


def uniform_return_map(weights: dict[bytes, float], value: object) -> dict[bytes, object]:
    """Apply one return observation to every supplied listing key."""

    return {listing_key: value for listing_key in weights}


def freeze_numeric_universe(
    spec: dict[str, Any],
    min_eligible_count: int,
    min_distinct_values: int,
    factor_id: str,
    signal_date: str,
) -> Any:
    """Freeze a compact numeric universe under one factor-month identity."""

    from campaign.eligibility import freeze_decision_time

    return freeze_decision_time(
        listing_decisions_from_numeric_spec(spec),
        min_eligible_count,
        min_distinct_values,
        factor_id,
        signal_date,
    )


def dated_uniform_returns(
    session_date: str,
    weights: dict[bytes, float],
    value: object,
) -> Any:
    """Bind a uniform held-return map to one schedule session."""

    from campaign.benchmarks import dated_held_returns

    return dated_held_returns(session_date, uniform_return_map(weights, value))


def strategy_schedule_sessions(strategy: Any) -> tuple[str, ...]:
    """Return the strategy path's ordered session dates."""

    return tuple(point.session_date for point in strategy.points)


def runner_campaign_schedule(session_dates: Any, **overrides: Any) -> Any:
    """Build a CampaignSchedule from supplied session dates."""

    from campaign.schedule import build_campaign_schedule

    dates = tuple(session_dates)
    payload = {
        "session_dates": dates,
        "accepted_cutoff": dates[-1],
        "horizon_return_rows": 1,
        "horizon_purge_signal_axis_rows": 2,
        "embargo_rows": 0,
        "first_fold_year": 2018,
    }
    payload.update(overrides)
    return build_campaign_schedule(**payload)


def fixture_campaign_schedule(spec: dict[str, Any]) -> Any:
    """Build a CampaignSchedule from a fixture schedule object."""

    from campaign.schedule import build_campaign_schedule

    return build_campaign_schedule(**spec)


def strategy_campaign_schedule(strategy: Any) -> Any:
    """Bind a strategy path to a CampaignSchedule of those sessions."""

    return runner_campaign_schedule(strategy_schedule_sessions(strategy))


def fixture_file(name: str) -> Path:
    """Return one campaign_runner_v1 fixture path."""

    return FIXTURE_ROOT / name


def make_run_config(
    locators: dict[str, str],
    digests: dict[str, str],
    protocol: dict[str, Any],
    **overrides: Any,
) -> Any:
    """Construct RunConfig from fixture locators, digests, and protocol."""

    from campaign.runner import RunConfig

    payload = {
        "acceptance_record_file": locators["acceptance_record_file"],
        "acceptance_record_file_sha256": digests["acceptance_record_file_sha256"],
        "acceptance_identity_sha256": digests["acceptance_identity_sha256"],
        "decision_file_sha256": digests["decision_file_sha256"],
        "decision_identity_sha256": digests["decision_identity_sha256"],
        "stage2_grant_file": locators["stage2_grant_file"],
        "stage2_grant_file_sha256": digests["stage2_grant_file_sha256"],
        "protocol_file": locators["protocol_file"],
        "protocol_file_sha256": digests["protocol_file_sha256"],
        "trial_inventory_file": locators["trial_inventory_file"],
        "trial_inventory_file_sha256": digests["trial_inventory_file_sha256"],
        "detached_binding_file": locators["detached_binding_file"],
        "runner_code_sha": protocol["runner_code_sha"],
        "environment_id": protocol["environment_id"],
        "environment_lock_sha256": protocol["environment_lock_sha256"],
        "calendar_id": protocol["calendar_id"],
        "calendar_version": protocol["calendar_version"],
        "prepared_campaign_file": locators["prepared_campaign_file"],
        "prepared_campaign_file_sha256": digests["prepared_campaign_file_sha256"],
        "owner_authorization_file_sha256": digests[
            "owner_authorization_file_sha256"
        ],
        "attempt_state_file": locators["attempt_state_file"],
        "horizon_return_rows": protocol["horizon_return_rows"],
        "horizon_purge_signal_axis_rows": protocol[
            "horizon_purge_signal_axis_rows"
        ],
        "embargo_rows": protocol["embargo_rows"],
        "decile_count": protocol["decile_count"],
        "min_eligible_count": protocol["min_eligible_count"],
        "min_distinct_values": protocol["min_distinct_values"],
        "common_complete_case_month_floor": protocol[
            "common_complete_case_month_floor"
        ],
        "long_segment_block_length": protocol["long_segment_block_length"],
        "bootstrap_replicates": protocol["bootstrap_replicates"],
        "random_rank_seed": protocol["random_rank_seed"],
        "bootstrap_seed": protocol["bootstrap_seed"],
        "familywise_alpha": protocol["familywise_alpha"],
        "cost_bps": tuple(protocol["cost_bps"]),
        "bit_generator": protocol["bit_generator"],
        "quantile_method": protocol["quantile_method"],
    }
    payload.update(overrides)
    return RunConfig(**payload)

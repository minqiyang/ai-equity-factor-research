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


def collect_disallowed_factor_id_literals(
    factor_ids: tuple[str, ...],
) -> tuple[tuple[str, int, str], ...]:
    """Collect factor-ID string literals outside the sole allowed owner site."""

    hits: list[tuple[str, int, str]] = []
    for module_path in sorted(CAMPAIGN_ROOT.glob("*.py")):
        tree = ast.parse(
            module_path.read_text(encoding="utf-8"),
            filename=str(module_path),
        )
        docstring_nodes = _docstring_constant_ids(tree)
        allowed_nodes = _allowed_owner_constant_ids(tree, module_path.name)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant):
                continue
            if not isinstance(node.value, str) or node.value not in factor_ids:
                continue
            if id(node) in docstring_nodes or id(node) in allowed_nodes:
                continue
            hits.append((module_path.name, node.lineno, node.value))
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

"""Frozen, dataset-independent protocol computations for bounded campaigns."""

from campaign.classifier import (
    DiagnosticInputs,
    DiagnosticState,
    classify_diagnostic,
)
from campaign.deciles import (
    DecileBucket,
    RankedListing,
    assign_deciles,
    order_eligible,
    top_decile_count,
)
from campaign.factors import (
    is_valid_price_anchor,
    low_vol_3m_from_anchors,
    mom_12_1_from_anchors,
    rev_1m_from_anchors,
)
from campaign.inference import (
    FACTOR_ORDER,
    BootstrapResult,
    CommonCompleteCaseRankICRecord,
    FactorRobustness,
    FactorVector,
    HolmResult,
    bootstrap_mean_rank_ic,
    draw_segment_indices,
    holm_adjust,
    rank_ic_robustness,
)
from campaign.listing_key import encode_listing_lineage_key_v1
from campaign.turnover import factor_target_turnover

__all__ = [
    "FACTOR_ORDER",
    "BootstrapResult",
    "CommonCompleteCaseRankICRecord",
    "DecileBucket",
    "DiagnosticInputs",
    "DiagnosticState",
    "FactorRobustness",
    "FactorVector",
    "HolmResult",
    "RankedListing",
    "assign_deciles",
    "bootstrap_mean_rank_ic",
    "classify_diagnostic",
    "draw_segment_indices",
    "encode_listing_lineage_key_v1",
    "factor_target_turnover",
    "holm_adjust",
    "is_valid_price_anchor",
    "low_vol_3m_from_anchors",
    "mom_12_1_from_anchors",
    "order_eligible",
    "rank_ic_robustness",
    "rev_1m_from_anchors",
    "top_decile_count",
]

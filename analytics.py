from __future__ import annotations
from typing import List, Dict
import pandas as pd

from domain import Opportunity, RiskAssessment


def compute_basic_kpis(opps: List[Opportunity]) -> Dict[str, float]:
    """Compute simple pipeline KPIs."""
    if not opps:
        return {
            "total_opportunities": 0,
            "total_pipeline": 0.0,
            "weighted_pipeline": 0.0,
            "avg_days_in_stage": 0.0,
        }

    total_pipeline = sum(o.amount for o in opps)
    weighted_pipeline = sum(o.amount * o.probability for o in opps)
    avg_days_in_stage = sum(o.days_in_stage for o in opps) / len(opps)

    return {
        "total_opportunities": float(len(opps)),
        "total_pipeline": float(total_pipeline),
        "weighted_pipeline": float(weighted_pipeline),
        "avg_days_in_stage": float(avg_days_in_stage),
    }


def stage_summary(opps: List[Opportunity]) -> pd.DataFrame:
    """Return a small DataFrame of pipeline by stage."""
    if not opps:
        return pd.DataFrame(columns=["stage", "count", "total_amount"])

    rows = [
        {"stage": o.stage, "amount": o.amount}
        for o in opps
    ]
    df = pd.DataFrame(rows)
    grouped = (
        df.groupby("stage", as_index=False)
        .agg(count=("amount", "size"), total_amount=("amount", "sum"))
        .sort_values("total_amount", ascending=False)
    )
    return grouped


def risk_distribution(
    opps: List[Opportunity],
    risks: List[RiskAssessment],
) -> Dict[str, int]:
    """Count opportunities by risk level."""
    counts: Dict[str, int] = {"Low": 0, "Medium": 0, "High": 0}
    for r in risks:
        if r.level in counts:
            counts[r.level] += 1
        else:
            counts[r.level] = counts.get(r.level, 0) + 1
    return counts

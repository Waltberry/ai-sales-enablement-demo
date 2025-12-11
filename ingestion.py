from __future__ import annotations
from typing import List, IO, Union
import pandas as pd

from domain import Opportunity


def _normalize_probability(p: float) -> float:
    """
    Normalize probability to [0, 1].

    If values are given as 0–100 (percent), convert.
    If already 0–1, leave as-is.
    """
    if p > 1.0:
        return p / 100.0
    return p


def load_opportunities_from_csv(
    file: Union[str, IO[bytes], IO[str]]
) -> List[Opportunity]:
    """
    Load opportunities from a CSV file path or file-like object.
    """
    df = pd.read_csv(file)

    required_cols = [
        "id",
        "account_name",
        "stage",
        "amount",
        "probability",
        "days_in_stage",
        "last_contact_days_ago",
        "notes",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    opportunities: List[Opportunity] = []

    for _, row in df.iterrows():
        prob_raw = float(row["probability"])
        prob = _normalize_probability(prob_raw)

        opp = Opportunity(
            id=str(row["id"]),
            account_name=str(row["account_name"]),
            stage=str(row["stage"]),
            amount=float(row["amount"]),
            probability=prob,
            days_in_stage=int(row["days_in_stage"]),
            last_contact_days_ago=int(row["last_contact_days_ago"]),
            notes=str(row["notes"]) if not pd.isna(row["notes"]) else "",
        )
        opportunities.append(opp)

    return opportunities

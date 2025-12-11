from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Opportunity:
    """Represents a single sales opportunity or deal."""
    id: str
    account_name: str
    stage: str
    amount: float                 # in base currency, e.g. CAD
    probability: float            # 0.0–1.0
    days_in_stage: int
    last_contact_days_ago: int
    notes: str                    # free-text notes / call summary


@dataclass(frozen=True)
class RiskAssessment:
    """Qualitative risk classification for an opportunity."""
    level: str                    # "Low", "Medium", "High"
    reasons: List[str]


@dataclass(frozen=True)
class RecommendedAction:
    """Suggested next actions for the rep."""
    priority: str                 # "Low", "Medium", "High"
    next_steps: List[str]


@dataclass(frozen=True)
class EmailSuggestion:
    """A follow-up email suggestion."""
    subject: str
    body: str                     # multi-line plain text


@dataclass(frozen=True)
class OpportunityInsight:
    """Bundle of all insights for one opportunity."""
    opportunity: Opportunity
    risk: RiskAssessment
    action: RecommendedAction
    email: EmailSuggestion

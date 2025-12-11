from __future__ import annotations
from typing import List
import re

from domain import Opportunity, RiskAssessment, RecommendedAction, EmailSuggestion

# -------------------------------------------------------------------
# Negative / risk-related terms we scan for in notes.
# We'll treat single-word and phrase keywords differently so that
# "hold" does NOT accidentally trigger on "stakeholders".
# -------------------------------------------------------------------
NEGATIVE_SINGLE_WORDS = [
    "delay",
    "concern",
    "budget",
    "expensive",
    "competitor",
    "risk",
    "blocked",
    "pause",
    "hold",
]

NEGATIVE_PHRASES = [
    "on hold",
    "no decision",
    "not moving",
    "not a priority",
    "re-org",
    "reorg",
]


def _has_negative_signals(notes: str) -> bool:
    """
    Return True if we detect clearly negative or blocking language
    in the free-text notes, using word-level checks for single words
    and substring checks for multi-word phrases.
    """
    notes_lower = (notes or "").lower()

    # Tokenize into words: "stakeholders." -> ["stakeholders"]
    tokens = re.findall(r"\b\w+\b", notes_lower)

    # Check single-word negatives as full words
    if any(kw in tokens for kw in NEGATIVE_SINGLE_WORDS):
        return True

    # Check multi-word phrases via substring matching
    if any(phrase in notes_lower for phrase in NEGATIVE_PHRASES):
        return True

    return False


def assess_risk(opp: Opportunity) -> RiskAssessment:
    """
    Simple, explainable risk heuristic.

    Signals we look at:
      - Low win probability
      - Long time in current stage
      - Long time since last contact
      - Negative / blocking language in notes

    We deliberately keep this lightweight and transparent so that
    it can later be replaced or augmented by an LLM-based scorer.
    """
    has_negative = _has_negative_signals(opp.notes or "")

    # ---------- Explicitly treat a clearly healthy case as LOW ----------
    # This matches your test: high-ish probability, short time in stage,
    # recent contact, and no negative notes.
    if (
        opp.probability >= 0.60
        and opp.days_in_stage <= 7
        and opp.last_contact_days_ago <= 7
        and not has_negative
    ):
        return RiskAssessment(
            level="Low",
            reasons=["No major risk signals detected (healthy engagement, good probability)."],
        )

    # ---------- Build up reasons for risk ----------
    reasons: List[str] = []

    # Probability
    if opp.probability < 0.20:
        reasons.append("Very low win probability (< 20%).")
    elif opp.probability < 0.30:
        reasons.append("Low win probability (20–30%).")

    # Time in stage
    if opp.days_in_stage > 45:
        reasons.append("Stuck in current stage for > 45 days.")
    elif opp.days_in_stage > 30:
        reasons.append("In current stage for > 30 days.")

    # Time since last contact
    if opp.last_contact_days_ago > 30:
        reasons.append("No recent contact for > 30 days.")
    elif opp.last_contact_days_ago > 14:
        reasons.append("No recent contact for > 14 days.")

    # Notes sentiment
    if has_negative:
        reasons.append("Negative sentiment or blockers mentioned in notes.")

    # ---------- Map reasons → risk level ----------
    score = len(reasons)

    # High: many issues or very low prob + staleness
    if score >= 3 or (
        opp.probability < 0.20
        and (opp.days_in_stage > 30 or opp.last_contact_days_ago > 14)
    ):
        level = "High"
    # Medium: at least one warning signal
    elif score >= 1:
        level = "Medium"
    # Low: nothing triggered above, but not "ideal healthy"
    else:
        level = "Low"
        reasons = ["No major risk signals detected."]

    return RiskAssessment(level=level, reasons=reasons)


def recommend_actions(opp: Opportunity, risk: RiskAssessment) -> RecommendedAction:
    """
    Suggest next steps based on risk + simple opportunity fields.

    This is deliberately rule-based and readable so it can be
    swapped out for an LLM-generated plan later.
    """
    next_steps: List[str] = []

    if risk.level == "High":
        priority = "High"
        next_steps.append("Schedule a call with the customer within 24–48 hours")
        next_steps.append("Escalate internally and align on a clear win strategy")
    elif risk.level == "Medium":
        priority = "Medium"
        next_steps.append("Book a follow-up meeting this week")
        next_steps.append("Clarify decision timeline and remaining blockers")
    else:
        priority = "Low"
        next_steps.append("Maintain regular touchpoints; confirm next milestone")
        next_steps.append("Explore potential upsell or cross-sell opportunity")

    # Stage-specific guidance
    if opp.stage.lower() in {"negotiation", "proposal"}:
        next_steps.append("Review pricing and commercial terms for potential objections")

    # Extra nudge if it’s been a long time since contact
    if opp.last_contact_days_ago > 21:
        next_steps.append("Acknowledge delay in communication and re-engage with value")

    return RecommendedAction(priority=priority, next_steps=next_steps)


def suggest_email(
    opp: Opportunity,
    risk: RiskAssessment,
    action: RecommendedAction,
) -> EmailSuggestion:
    """
    Generate a simple follow-up email template that *looks* like something
    an LLM might draft, but is produced via transparent rules.

    The email references:
      - account name
      - current stage
      - a couple of recommended next steps
      - tone adjusted by risk level
    """
    subject = f"Next steps on our {opp.stage.lower()} for {opp.account_name}"

    intro = (
        f"Hi {opp.account_name} team,\n\n"
        "I hope you're doing well. I wanted to follow up on our recent discussions "
        f"about your interest in moving forward with our solution."
    )

    if risk.level == "High":
        middle = (
            "\n\nFrom our last conversation, it sounds like there are a few open questions "
            "or concerns that we should address directly so you can make a confident decision."
        )
    elif risk.level == "Medium":
        middle = (
            "\n\nI know you're evaluating options, and I'd like to make sure you have "
            "everything you need to move forward comfortably."
        )
    else:
        middle = (
            "\n\nThanks again for the positive engagement so far. I'd like to keep your "
            "project moving smoothly toward the next milestone."
        )

    # Use the first 1–2 next steps as bullets
    bullet_steps = action.next_steps[:2]
    bullets = "\n".join(f"- {step}" for step in bullet_steps)

    closing = (
        "\n\nHere are a couple of concrete next steps I’d propose:\n"
        f"{bullets}\n\n"
        "Would any of these work for you this week? If there’s someone else on your side "
        "who should be involved, I’m happy to loop them in.\n\n"
        "Best regards,\n"
        "Onyero"
    )

    body = intro + middle + closing
    return EmailSuggestion(subject=subject, body=body)

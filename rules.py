from __future__ import annotations
from typing import List

from domain import Opportunity, RiskAssessment, RecommendedAction, EmailSuggestion


NEGATIVE_KEYWORDS = [
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


def assess_risk(opp: Opportunity) -> RiskAssessment:
    """
    Heuristic risk assessment:
      - low probability
      - long time in stage
      - no recent contact
      - negative sentiment in notes
    """
    reasons: List[str] = []
    score = 0

    if opp.probability < 0.3:
        score += 2
        reasons.append("Low win probability (< 30%)")

    if opp.days_in_stage > 30:
        score += 2
        reasons.append("Stuck in stage (> 30 days)")

    if opp.last_contact_days_ago > 14:
        score += 1
        reasons.append("No recent contact (> 14 days)")

    notes_lower = opp.notes.lower()
    negative_hits = [kw for kw in NEGATIVE_KEYWORDS if kw in notes_lower]
    if negative_hits:
        score += 2
        reasons.append(f"Negative signals in notes: {', '.join(negative_hits)}")

    # Map score → qualitative risk level
    if score >= 4:
        level = "High"
    elif score >= 2:
        level = "Medium"
    else:
        level = "Low"

    if not reasons:
        reasons.append("No major risk signals detected")

    return RiskAssessment(level=level, reasons=reasons)


def recommend_actions(opp: Opportunity, risk: RiskAssessment) -> RecommendedAction:
    """
    Suggest next steps based on risk + simple fields.
    """
    next_steps: List[str] = []

    if risk.level == "High":
        priority = "High"
        next_steps.append("Schedule a call with the customer within 24–48 hours")
        next_steps.append("Escalate internally and align on win strategy")
    elif risk.level == "Medium":
        priority = "Medium"
        next_steps.append("Book a follow-up meeting this week")
        next_steps.append("Clarify decision timeline and remaining blockers")
    else:
        priority = "Low"
        next_steps.append("Maintain regular touchpoints; confirm next milestone")
        next_steps.append("Explore potential upsell or cross-sell")

    if opp.stage.lower() in {"negotiation", "proposal"}:
        next_steps.append("Review pricing and commercial terms for possible objections")

    if opp.last_contact_days_ago > 21:
        next_steps.append("Acknowledge delay in communication and re-engage with value")

    return RecommendedAction(priority=priority, next_steps=next_steps)


def suggest_email(opp: Opportunity, risk: RiskAssessment, action: RecommendedAction) -> EmailSuggestion:
    """
    Generate a simple follow-up email template that looks like something
    an LLM might have drafted, but is rule-based.
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
            "or concerns that we should address directly."
        )
    elif risk.level == "Medium":
        middle = (
            "\n\nI know you're evaluating options, and I'd like to make sure you have "
            "everything you need to make a confident decision."
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

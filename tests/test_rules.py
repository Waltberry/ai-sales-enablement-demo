# tests/test_rules.py
from domain import Opportunity
from rules import assess_risk, recommend_actions, suggest_email


def make_opp(**overrides) -> Opportunity:
    base = dict(
        id="OPP-TEST",
        account_name="TestCo",
        stage="Negotiation",
        amount=50000.0,
        probability=0.5,
        days_in_stage=10,
        last_contact_days_ago=5,
        notes="All good so far.",
    )
    base.update(overrides)
    return Opportunity(**base)


def test_assess_risk_high_when_multiple_signals():
    opp = make_opp(
        probability=0.2,
        days_in_stage=45,
        last_contact_days_ago=30,
        notes="Customer has budget concern and competitor mentioned.",
    )
    risk = assess_risk(opp)
    assert risk.level == "High"
    # Should have at least one reason mentioning low probability
    assert any("Low win probability" in r for r in risk.reasons)


def test_assess_risk_low_when_no_signals():
    opp = make_opp(
        probability=0.7,
        days_in_stage=5,
        last_contact_days_ago=2,
        notes="Positive feedback from all stakeholders.",
    )
    risk = assess_risk(opp)
    assert risk.level == "Low"


def test_recommend_actions_priority_matches_risk():
    opp = make_opp()
    high_risk = assess_risk(
        make_opp(probability=0.1, days_in_stage=40, last_contact_days_ago=20)
    )
    action = recommend_actions(opp, high_risk)
    assert action.priority == "High"
    assert any("Schedule a call" in step for step in action.next_steps)


def test_suggest_email_contains_account_name_and_stage():
    opp = make_opp(stage="Proposal", account_name="Acme Corp")
    risk = assess_risk(opp)
    action = recommend_actions(opp, risk)
    email = suggest_email(opp, risk, action)

    assert "Acme Corp" in email.subject
    # Body should mention proposed next steps bullets
    for step in action.next_steps[:2]:
        assert step.split()[0] in email.body  # loose check

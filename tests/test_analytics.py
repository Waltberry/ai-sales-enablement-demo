# tests/test_analytics.py
from domain import Opportunity
from analytics import compute_basic_kpis, stage_summary, risk_distribution
from rules import assess_risk


def make_opp(id: str, stage: str, amount: float, probability: float) -> Opportunity:
    return Opportunity(
        id=id,
        account_name="Acct",
        stage=stage,
        amount=amount,
        probability=probability,
        days_in_stage=10,
        last_contact_days_ago=3,
        notes="",
    )


def test_compute_basic_kpis_non_empty():
    opps = [
        make_opp("O1", "Discovery", 10000, 0.5),
        make_opp("O2", "Proposal", 20000, 0.7),
    ]
    kpis = compute_basic_kpis(opps)

    assert kpis["total_opportunities"] == 2.0
    assert kpis["total_pipeline"] == 30000.0
    assert kpis["weighted_pipeline"] == 10000 * 0.5 + 20000 * 0.7
    assert kpis["avg_days_in_stage"] == 10.0


def test_stage_summary_groups_by_stage():
    opps = [
        make_opp("O1", "Discovery", 10000, 0.5),
        make_opp("O2", "Discovery", 5000, 0.8),
        make_opp("O3", "Proposal", 20000, 0.6),
    ]
    df = stage_summary(opps)
    assert set(df["stage"].tolist()) == {"Discovery", "Proposal"}
    total_discovery = df[df["stage"] == "Discovery"]["total_amount"].iloc[0]
    assert total_discovery == 15000.0


def test_risk_distribution_counts_levels():
    opps = [
        make_opp("O1", "Discovery", 10000, 0.2),  # likely low or med risk
        make_opp("O2", "Proposal", 30000, 0.1),
    ]
    risks = [assess_risk(o) for o in opps]
    counts = risk_distribution(opps, risks)
    # Just check keys exist and total matches
    assert sum(counts.values()) == len(opps)
    assert set(counts.keys()) >= {"Low", "Medium", "High"}

import io
from pathlib import Path
from typing import List

import pandas as pd
import streamlit as st

from domain import OpportunityInsight
from ingestion import load_opportunities_from_csv
from rules import assess_risk, recommend_actions, suggest_email
from analytics import compute_basic_kpis, stage_summary, risk_distribution


st.set_page_config(
    page_title="AI for Sales Enablement Demo",
    layout="wide",
)


def build_insights(csv_file) -> List[OpportunityInsight]:
    opps = load_opportunities_from_csv(csv_file)
    insights: List[OpportunityInsight] = []

    for opp in opps:
        risk = assess_risk(opp)
        action = recommend_actions(opp, risk)
        email = suggest_email(opp, risk, action)
        insights.append(
            OpportunityInsight(
                opportunity=opp,
                risk=risk,
                action=action,
                email=email,
            )
        )
    return insights


def _demo_csv_bytes() -> bytes:
    """Small in-memory demo CSV."""
    data = """id,account_name,stage,amount,probability,days_in_stage,last_contact_days_ago,notes
OPP-001,Acme Bank,Discovery,50000,0.4,10,5,"Client interested but concerned about integration timeline."
OPP-002,NorthTel,Negotiation,80000,0.25,45,20,"Budget constraints and competitor reference mentioned."
OPP-003,City Health,Proposal,120000,0.6,20,3,"Positive response from stakeholders, waiting on internal approval."
OPP-004,FinPlus,Qualification,30000,0.15,35,30,"Project paused due to internal re-org; risk of delay."
"""
    return data.encode("utf-8")


def _load_sample_from_disk() -> io.BytesIO | None:
    """
    Load data/sample_opportunities.csv as a BytesIO stream
    so it behaves like an uploaded file.
    """
    path = Path("data") / "sample_opportunities.csv"
    if not path.exists():
        st.error(
            "Could not find 'data/sample_opportunities.csv'. "
            "Run `python generate_mock_data.py` from the repo root first."
        )
        return None

    return io.BytesIO(path.read_bytes())


def main() -> None:
    st.title("AI for Sales Enablement – Offline Demo")
    st.caption(
        "Ingest a CSV of opportunities, estimate risk and next steps with simple rules, "
        "and view a pipeline health summary. Designed to be LLM-ready without paid APIs."
    )

    col_left, col_right = st.columns([1.5, 2.5])

    with col_left:
        st.subheader("1. Upload opportunities CSV")

        uploaded = st.file_uploader(
            "Upload CSV with opportunities",
            type=["csv"],
            help=(
                "Columns: id, account_name, stage, amount, probability, "
                "days_in_stage, last_contact_days_ago, notes"
            ),
        )

        use_local_sample = st.button("Load sample_opportunities.csv from ./data")
        use_demo = st.button("Use tiny in-memory demo data")

        csv_file = None
        source_label = ""

        if uploaded is not None:
            csv_file = uploaded
            source_label = "uploaded file"
        elif use_local_sample:
            csv_file = _load_sample_from_disk()
            if csv_file is not None:
                source_label = "data/sample_opportunities.csv"
        elif use_demo:
            csv_file = io.BytesIO(_demo_csv_bytes())
            source_label = "built-in demo sample"

        if csv_file is None:
            st.info(
                "Upload a CSV, click 'Load sample_opportunities.csv from ./data', "
                "or click 'Use tiny in-memory demo data' to see the app in action."
            )
            return

        with st.spinner("Analyzing opportunities..."):
            insights = build_insights(csv_file)

        st.success(f"Loaded {len(insights)} opportunities from {source_label}.")
        st.write("Scroll down to see pipeline health and detailed recommendations.")

    # After insights are built, we can reuse them
    if csv_file is None:
        return

    opps = [ins.opportunity for ins in insights]
    risks = [ins.risk for ins in insights]

    # ---------- Pipeline health ----------
    st.markdown("---")
    st.subheader("2. Pipeline Health Overview")

    kpis = compute_basic_kpis(opps)
    risk_counts = risk_distribution(opps, risks)
    stage_df = stage_summary(opps)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(
            "Total opportunities",
            int(kpis["total_opportunities"]),
        )
    with c2:
        st.metric(
            "Total pipeline",
            f"${kpis['total_pipeline']:,.0f}",
        )
    with c3:
        st.metric(
            "Weighted pipeline",
            f"${kpis['weighted_pipeline']:,.0f}",
        )
    with c4:
        st.metric(
            "Avg. days in stage",
            f"{kpis['avg_days_in_stage']:.1f}",
        )

    col_stage, col_risk = st.columns(2)

    with col_stage:
        st.markdown("**Pipeline by stage**")
        if not stage_df.empty:
            st.dataframe(stage_df, use_container_width=True)
            st.bar_chart(
                stage_df.set_index("stage")["total_amount"]
            )
        else:
            st.write("No data.")

    with col_risk:
        st.markdown("**Risk distribution**")
        risk_df = pd.DataFrame(
            [{"level": k, "count": v} for k, v in risk_counts.items()]
        )
        st.dataframe(risk_df, use_container_width=True)
        st.bar_chart(
            risk_df.set_index("level")["count"]
        )

    # ---------- Detailed opportunity insights ----------
    st.markdown("---")
    st.subheader("3. Opportunity-level recommendations")

    for ins in insights:
        opp = ins.opportunity
        risk = ins.risk
        action = ins.action
        email = ins.email

        with st.expander(f"{opp.id} — {opp.account_name} ({opp.stage})"):
            st.markdown(
                f"**Amount:** ${opp.amount:,.0f}  \n"
                f"**Probability:** {opp.probability * 100:.0f}%  \n"
                f"**Days in stage:** {opp.days_in_stage}  \n"
                f"**Last contact:** {opp.last_contact_days_ago} days ago"
            )

            st.markdown(f"**Risk level:** `{risk.level}`")
            st.markdown("**Risk drivers:**")
            for r in risk.reasons:
                st.write(f"- {r}")

            st.markdown(f"**Recommended priority:** `{action.priority}`")
            st.markdown("**Next steps:**")
            for step in action.next_steps:
                st.write(f"- {step}")

            st.markdown("**Suggested follow-up email:**")
            st.code(
                f"Subject: {email.subject}\n\n{email.body}",
                language="text",
            )

    st.markdown("---")
    st.caption(
        "Note: All intelligence here is rule-based for demo purposes. "
        "In a real deployment, these rules would be replaced or augmented by LLMs, "
        "but the product flow would remain similar."
    )


if __name__ == "__main__":
    main()

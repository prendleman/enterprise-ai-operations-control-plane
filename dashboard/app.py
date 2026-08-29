"""Executive AI Operations dashboard (Streamlit)."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import get_engine
from app.services.ai_ops_service import AIOpsService

st.set_page_config(page_title="AI Operations Control Plane", layout="wide")
st.title("Enterprise AI Operations Dashboard")
st.caption(
    "Synthetic and local telemetry for AI portfolio, governance, cost, and adoption. "
    "Values are labeled simulated/synthetic where applicable."
)

get_engine()
service = AIOpsService()
metrics = service.metrics()
portfolio = service.portfolio()
costs = service.costs()
agents = service.list_agents()
exceptions = service.list_exceptions()
use_cases = portfolio["items"]

c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(8)
c1.metric("AI Initiatives", metrics.get("initiatives", 0))
c2.metric("Active Pilots", metrics.get("active_pilots", 0))
c3.metric("Production AI", metrics.get("production_ai", 0))
c4.metric("Monthly AI Spend", f"${metrics.get('monthly_ai_spend', 0):,.0f}")
c5.metric("Budget Variance", f"${metrics.get('budget_variance', 0):,.0f}")
c6.metric("High-Risk", metrics.get("high_risk_initiatives", 0))
c7.metric("Open Exceptions", metrics.get("open_exceptions", 0))
c8.metric("Active Agents", metrics.get("active_agents", 0))

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["Executive", "Portfolio", "Cost & Usage", "Governance", "Agents", "Adoption"]
)

with tab1:
    st.subheader("Executive Overview")
    st.write(
        f"Budget alert status: **{metrics.get('budget_alert', 'none')}** "
        f"({metrics.get('budget_utilization', 0)}% utilization). "
        f"Metric label: `{metrics.get('label')}`."
    )
    if use_cases:
        df = pd.DataFrame(use_cases)
        fig = px.pie(df, names="lifecycle_stage", title="Initiatives by Lifecycle")
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Portfolio")
    if use_cases:
        df = pd.DataFrame(use_cases)[
            [
                "title",
                "business_unit",
                "lifecycle_stage",
                "priority_score",
                "risk_level",
                "approval_status",
            ]
        ]
        st.dataframe(df, use_container_width=True, hide_index=True)
        fig = px.bar(
            pd.DataFrame(use_cases),
            x="business_unit",
            color="risk_level",
            title="Initiatives by Business Unit / Risk",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No use cases yet. Run `python scripts/seed_data.py`.")

with tab3:
    st.subheader("Cost & Usage (Simulated)")
    st.write("Integration points:", ", ".join(costs.get("integration_points", [])))
    if costs.get("alerts"):
        st.warning("Budget alerts present")
        st.dataframe(pd.DataFrame(costs["alerts"]), use_container_width=True)
    if costs.get("by_provider"):
        prov = pd.DataFrame(
            {
                "provider": list(costs["by_provider"].keys()),
                "spend": list(costs["by_provider"].values()),
            }
        )
        st.plotly_chart(
            px.bar(prov, x="provider", y="spend", title="Spend by Provider"),
            use_container_width=True,
        )
    if costs.get("by_business_unit"):
        units = pd.DataFrame(
            {
                "business_unit": list(costs["by_business_unit"].keys()),
                "spend": list(costs["by_business_unit"].values()),
            }
        )
        st.plotly_chart(
            px.bar(units, x="business_unit", y="spend", title="Spend by Business Unit"),
            use_container_width=True,
        )

with tab4:
    st.subheader("Governance")
    if use_cases:
        df = pd.DataFrame(use_cases)
        st.plotly_chart(
            px.histogram(df, x="risk_level", title="Risk Distribution"),
            use_container_width=True,
        )
        pending = df[df["approval_status"] == "pending"]
        st.write(f"Approval queue: {len(pending)}")
        st.dataframe(pending.head(20), use_container_width=True, hide_index=True)
    st.write("Exceptions")
    st.dataframe(pd.DataFrame(exceptions), use_container_width=True, hide_index=True)

with tab5:
    st.subheader("Agent Registry")
    st.dataframe(pd.DataFrame(agents), use_container_width=True, hide_index=True)

with tab6:
    st.subheader("Adoption")
    st.metric("Business Units Adopting", metrics.get("business_units_adopting", 0))
    st.metric("Monthly Active AI Users", metrics.get("monthly_active_ai_users", 0))
    st.metric("Sandbox Active", metrics.get("sandbox_active", 0))
    st.metric(
        "Pilot→Production Conversion %",
        metrics.get("pilot_to_production_conversion", 0),
    )

service.close()

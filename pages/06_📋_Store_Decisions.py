"""
Page 5: Store Operating Decisions — shadcn/ui
Daily Operating Plan with mode badges.
"""

import streamlit as st
import streamlit_shadcn_ui as ui
import plotly.graph_objects as go
import pandas as pd
from config.settings import OPERATING_MODES
from utils.data_loader import load_stores, load_daily_energy, load_store_sales, load_diesel_inventory, load_solar_generation
from models.store_decision_engine import StoreDecisionEngine
from utils.element_captions import get_page_captions, render_caption
from utils.page_intelligence import render_page_intelligence
from utils.smart_table import render_smart_table

st.set_page_config(page_title="Store Decisions", page_icon="📋", layout="wide")

st.markdown("""
<div style="background:linear-gradient(135deg,#064e3b,#059669);color:white;padding:20px 28px;border-radius:12px;margin-bottom:20px">
    <h2 style="margin:0;color:white">Daily Operating Plan</h2>
    <p style="margin:4px 0 0;opacity:0.85">AI-generated store decisions — FULL / REDUCED / CRITICAL / CLOSE</p>
</div>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_and_plan():
    stores = load_stores()
    energy = load_daily_energy()
    sales = load_store_sales()
    inv = load_diesel_inventory()
    solar = load_solar_generation()
    engine = StoreDecisionEngine()
    plan = engine.generate_daily_plan(stores, energy, sales, inv, solar_df=solar)
    summary = engine.get_summary()
    sector_summary = engine.get_sector_summary()
    alerts = engine.get_alerts()
    return plan, summary, sector_summary, alerts

plan, summary, sector_summary, alerts = load_and_plan()

render_page_intelligence("store_decisions", f"Total stores: {summary['total_stores']}, FULL: {summary['stores_full']}, REDUCED: {summary['stores_reduced']}, CRITICAL: {summary['stores_critical']}, CLOSED: {summary['stores_closed']}, Est profit: {summary['total_estimated_profit']:,.0f} MMK.")

# ── AI Captions ──
captions = get_page_captions("store_decisions", [
    {"id": "d_total", "type": "metric", "title": "Total Stores", "value": str(summary["total_stores"])},
    {"id": "d_full", "type": "metric", "title": "FULL Mode Stores", "value": str(summary["stores_full"])},
    {"id": "d_reduced", "type": "metric", "title": "REDUCED Mode Stores", "value": str(summary["stores_reduced"])},
    {"id": "d_critical", "type": "metric", "title": "CRITICAL Mode Stores", "value": str(summary["stores_critical"])},
    {"id": "d_closed", "type": "metric", "title": "CLOSED Stores", "value": str(summary["stores_closed"])},
    {"id": "d_profit", "type": "metric", "title": "Est. Daily Profit", "value": f"{summary['total_estimated_profit']/1e6:,.1f}M MMK"},
    {"id": "plan_table", "type": "table", "title": "Full Plan Table", "value": f"{len(plan)} stores with modes, reasons, diesel days remaining"},
    {"id": "profitability_chart", "type": "chart", "title": "Diesel Cost vs Margin Break-Even", "value": f"Scatter of {len(plan)} stores by diesel cost vs daily margin"},
    {"id": "sector_cards", "type": "metric", "title": "Sector Summary Cards", "value": f"{len(sector_summary)} sectors with store counts and profit"},
], data_summary=f"Daily plan: {summary['stores_full']} FULL, {summary['stores_reduced']} REDUCED, {summary['stores_critical']} CRITICAL, {summary['stores_closed']} CLOSED. Total profit {summary['total_estimated_profit']/1e6:,.1f}M MMK.")

# ── Mode KPIs ──
cols = st.columns(4)
with cols[0]:
    ui.metric_card(title="Total Stores", content=str(summary["total_stores"]),
                   description="in plan", key="d_total")
    render_caption("d_total", captions)
with cols[1]:
    ui.metric_card(title="FULL", content=str(summary["stores_full"]),
                   description="normal operation", key="d_full")
    render_caption("d_full", captions)
with cols[2]:
    ui.metric_card(title="REDUCED", content=str(summary["stores_reduced"]),
                   description="partial operation", key="d_reduced")
    render_caption("d_reduced", captions)
with cols[3]:
    ui.metric_card(title="CRITICAL", content=str(summary["stores_critical"]),
                   description="essential only", key="d_critical")
    render_caption("d_critical", captions)
cols2 = st.columns(4)
with cols2[0]:
    ui.metric_card(title="CLOSED", content=str(summary["stores_closed"]),
                   description="shutdown", key="d_closed")
    render_caption("d_closed", captions)
with cols2[1]:
    ui.metric_card(title="Est. Profit", content=f"{summary['total_estimated_profit']/1e6:,.1f}M",
                   description="daily MMK", key="d_profit")
    render_caption("d_profit", captions)

st.markdown("")

# ── Tabs ──
tab = ui.tabs(options=["Operating Plan", "Sector View", "Profitability"], default_value="Operating Plan", key="dec_tabs")

if tab == "Operating Plan":
    # Mode filter
    st.markdown("### Store Operating Modes")

    # Store cards by mode
    for mode_key in ["CLOSE", "CRITICAL", "REDUCED", "FULL"]:
        mode_stores = plan[plan["mode"] == mode_key]
        if len(mode_stores) == 0:
            continue

        mode_info = OPERATING_MODES[mode_key]
        variant = {"FULL": "default", "REDUCED": "secondary", "CRITICAL": "destructive", "CLOSE": "outline"}[mode_key]

        st.markdown(f"""
        <div style="background:{mode_info['color']}15;border-left:4px solid {mode_info['color']};padding:12px 16px;border-radius:0 8px 8px 0;margin:12px 0 8px">
            <strong style="color:{mode_info['color']}">{mode_info['label']}</strong> — {len(mode_stores)} stores — {mode_info['description']}
        </div>
        """, unsafe_allow_html=True)

        for _, row in mode_stores.iterrows():
            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
            c1.write(f"**{row['name']}**")
            c2.write(row["reason"][:50])
            c3.write(f"Sales: {row['avg_daily_sales']:,.0f}")
            c4.write(f"Diesel: {row['avg_diesel_cost']:,.0f}")
            with c5:
                ui.badges(badge_list=[(mode_key, variant)], key=f"mode_{row['store_id']}")

    # Full table
    st.markdown("### Full Plan Table")
    display = plan[["name", "sector", "channel", "mode", "reason", "avg_daily_sales",
                     "avg_diesel_cost", "estimated_daily_profit", "diesel_days_remaining"]].copy()
    display["avg_daily_sales"] = display["avg_daily_sales"].apply(
        lambda v: f"{v/1e6:,.1f}M" if abs(v) >= 1e6 else (f"{v/1e3:,.1f}K" if abs(v) >= 1e3 else f"{v:,.0f}"))
    display["avg_diesel_cost"] = display["avg_diesel_cost"].apply(
        lambda v: f"{v/1e6:,.1f}M" if abs(v) >= 1e6 else (f"{v/1e3:,.1f}K" if abs(v) >= 1e3 else f"{v:,.0f}"))
    display["estimated_daily_profit"] = display["estimated_daily_profit"].apply(
        lambda v: f"{v/1e6:,.1f}M" if abs(v) >= 1e6 else (f"{v/1e3:,.1f}K" if abs(v) >= 1e3 else f"{v:,.0f}"))
    display["diesel_days_remaining"] = display["diesel_days_remaining"].apply(lambda v: f"{v:.1f}")
    display.columns = ["Store", "Sector", "Channel", "Mode", "Reason", "Daily Sales",
                        "Diesel Cost", "Est. Profit", "Diesel Days"]
    render_smart_table(display, key="plan_table", title="Daily Operating Plan",
                       severity_col="Mode", max_height=400)
    render_caption("plan_table", captions)

elif tab == "Sector View":
    st.markdown("### Sector Summary")
    for _, row in sector_summary.iterrows():
        with st.container():
            ui.metric_card(title=row["sector"],
                           content=f"{row['total_stores']} stores | Profit: {row['total_profit']:,.0f} MMK",
                           description=f"Full: {row['full']} | Reduced: {row['reduced']} | Critical: {row['critical']} | Closed: {row['closed']}",
                           key=f"ss_{row['sector']}")
    render_caption("sector_cards", captions)

elif tab == "Profitability":
    st.markdown("### Diesel Cost vs Margin — Break-Even Analysis")

    fig = go.Figure()
    for mode in ["FULL", "REDUCED", "CRITICAL", "CLOSE"]:
        md = plan[plan["mode"] == mode]
        if len(md) > 0:
            fig.add_trace(go.Scatter(
                x=md["avg_diesel_cost"], y=md["avg_daily_margin"],
                mode="markers+text", name=OPERATING_MODES[mode]["label"],
                marker=dict(color=OPERATING_MODES[mode]["color"], size=10),
                text=md["name"], textposition="top center", textfont=dict(size=7)))

    max_val = max(plan["avg_diesel_cost"].max(), plan["avg_daily_margin"].max(), 1)
    fig.add_trace(go.Scatter(x=[0, max_val], y=[0, max_val], mode="lines",
                             name="Break-Even", line=dict(color="#94a3b8", dash="dash")))
    fig.update_layout(height=500, margin=dict(l=40, r=20, t=20, b=40),
                      xaxis_title="Diesel Cost (MMK)", yaxis_title="Daily Margin (MMK)",
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", y=1.05))
    st.plotly_chart(fig, use_container_width=True)
    render_caption("profitability_chart", captions)
    st.caption("Below the line = losing money on diesel. Above = profitable.")

# ── Decision Alerts ──
if alerts:
    st.markdown("### Decision Alerts")
    for a in alerts:
        if a["tier"] == 1:
            ui.alert(title="CRITICAL", description=a["message"], key=f"da_{a['store_id']}")
        else:
            st.warning(a["message"])

# AI Insights merged into Page Intelligence at top


# Generate element captions for next visit
from utils.element_captions import generate_pending_captions
generate_pending_captions()

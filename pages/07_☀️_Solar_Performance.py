"""
Page 6: Solar Performance — shadcn/ui
"""

import streamlit as st
import streamlit_shadcn_ui as ui
import plotly.graph_objects as go
import pandas as pd
from utils.data_loader import load_stores, load_daily_energy, load_solar_generation, load_diesel_prices
from models.solar_optimizer import SolarOptimizer
from utils.element_captions import get_page_captions, render_caption
from utils.page_intelligence import render_page_intelligence
from utils.smart_table import render_smart_table

st.set_page_config(page_title="Solar Performance", page_icon="☀️", layout="wide")

st.markdown("""
<div style="background:linear-gradient(135deg,#78350f,#d97706);color:white;padding:20px 28px;border-radius:12px;margin-bottom:20px">
    <h2 style="margin:0;color:white">Solar Performance</h2>
    <p style="margin:4px 0 0;opacity:0.85">Generation tracking, diesel offset, and CAPEX prioritization</p>
</div>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_and_optimize():
    stores = load_stores()
    energy = load_daily_energy()
    solar = load_solar_generation()
    prices = load_diesel_prices()
    price = prices["diesel_price_mmk"].iloc[-1]
    opt = SolarOptimizer()
    results = opt.optimize_all(stores, solar, energy, price)
    summary = opt.get_network_summary()
    capex = opt.get_capex_priority(stores, energy, price)
    return stores, solar, results, summary, capex

stores, solar, results, summary, capex = load_and_optimize()

render_page_intelligence("solar", f"Solar sites: {summary['total_solar_sites']}, Daily generation: {summary['total_daily_solar_kwh']:,.0f} kWh, Diesel offset: {summary['total_diesel_offset_liters']:,.0f} L/day, Daily savings: {summary['total_daily_saving_mmk']:,.0f} MMK, Monthly savings: {summary['total_daily_saving_mmk']*30/1e6:,.1f}M MMK.")

# ── AI Captions ──
_monthly_savings = summary['total_daily_saving_mmk'] * 30
captions = get_page_captions("solar", [
    {"id": "so_sites", "type": "metric", "title": "Solar Sites", "value": f"{summary['total_solar_sites']}/{summary['total_solar_sites']+summary['total_non_solar']} equipped"},
    {"id": "so_kwh", "type": "metric", "title": "Daily Solar Generation", "value": f"{summary['total_daily_solar_kwh']:,.0f} kWh"},
    {"id": "so_offset", "type": "metric", "title": "Diesel Offset", "value": f"{summary['total_diesel_offset_liters']:,.0f} L/day"},
    {"id": "so_save", "type": "metric", "title": "Daily Savings", "value": f"{summary['total_daily_saving_mmk']:,.0f} MMK"},
    {"id": "so_monthly", "type": "metric", "title": "Monthly Savings", "value": f"{_monthly_savings/1e6:,.1f}M MMK projected"},
    {"id": "site_perf_chart", "type": "chart", "title": "Site Performance Bar Chart", "value": f"Solar kWh vs diesel offset for {summary['total_solar_sites']} sites"},
    {"id": "solar_table", "type": "table", "title": "Solar Site Details", "value": f"{summary['total_solar_sites']} solar sites with kWh, diesel saved, daily saving"},
    {"id": "hourly_chart", "type": "chart", "title": "Hourly Solar Pattern", "value": "Average kWh by hour of day, peak 10am-3pm"},
    {"id": "capex_chart", "type": "chart", "title": "CAPEX Priority Bar Chart", "value": f"Top non-solar stores ranked by payback period"},
    {"id": "capex_table", "type": "table", "title": "CAPEX Priority Table", "value": f"{len(capex)} non-solar stores with install cost, monthly saving, payback months"},
], data_summary=f"{summary['total_solar_sites']} solar sites generating {summary['total_daily_solar_kwh']:,.0f} kWh/day, offsetting {summary['total_diesel_offset_liters']:,.0f}L diesel, saving {summary['total_daily_saving_mmk']:,.0f} MMK/day ({_monthly_savings/1e6:,.1f}M/month). {summary['total_non_solar']} stores without solar.")

# ── KPIs ──
cols = st.columns(4)
with cols[0]:
    ui.metric_card(title="Solar Sites", content=f"{summary['total_solar_sites']}/{summary['total_solar_sites']+summary['total_non_solar']}",
                   description="equipped", key="so_sites")
    render_caption("so_sites", captions)
with cols[1]:
    ui.metric_card(title="Daily Solar", content=f"{summary['total_daily_solar_kwh']:,.0f} kWh",
                   description="generation", key="so_kwh")
    render_caption("so_kwh", captions)
with cols[2]:
    ui.metric_card(title="Diesel Offset", content=f"{summary['total_diesel_offset_liters']:,.0f} L/day",
                   description="saved by solar", key="so_offset")
    render_caption("so_offset", captions)
with cols[3]:
    ui.metric_card(title="Daily Savings", content=f"{summary['total_daily_saving_mmk']:,.0f} MMK",
                   description="cost reduction", key="so_save")
    render_caption("so_save", captions)
cols2 = st.columns(4)
with cols2[0]:
    monthly = summary['total_daily_saving_mmk'] * 30
    ui.metric_card(title="Monthly Savings", content=f"{monthly/1e6:,.1f}M MMK",
                   description="projected", key="so_monthly")
    render_caption("so_monthly", captions)

st.markdown("")
tab = ui.tabs(options=["Site Performance", "Hourly Pattern", "CAPEX Priority", "Recommendations"], default_value="Site Performance", key="solar_tabs")

solar_results = results[results["has_solar"] == True].sort_values("cost_saving_mmk", ascending=False)

if tab == "Site Performance":
    fig = go.Figure()
    fig.add_trace(go.Bar(x=solar_results["name"], y=solar_results["daily_solar_kwh"],
                         name="Solar kWh", marker_color="#eab308"))
    fig.add_trace(go.Bar(x=solar_results["name"], y=solar_results["diesel_offset_liters"],
                         name="Diesel Offset (L)", marker_color="#f97316"))
    fig.update_layout(barmode="group", height=400, margin=dict(l=40, r=20, t=20, b=80),
                      xaxis_tickangle=-45, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", y=1.05))
    st.plotly_chart(fig, use_container_width=True)
    render_caption("site_perf_chart", captions)

    _solar_df = solar_results[["name", "daily_solar_kwh", "diesel_offset_liters", "cost_saving_mmk"]].copy()
    _solar_df["daily_solar_kwh"] = _solar_df["daily_solar_kwh"].round(1)
    _solar_df["diesel_offset_liters"] = _solar_df["diesel_offset_liters"].round(1)
    _solar_df["cost_saving_mmk"] = _solar_df["cost_saving_mmk"].round(0)
    _solar_df = _solar_df.rename(columns={
        "name": "Store", "daily_solar_kwh": "Solar kWh",
        "diesel_offset_liters": "Diesel Saved (L)", "cost_saving_mmk": "Daily Saving (MMK)"})
    render_smart_table(_solar_df, key="solar_table", title="Solar Site Details", max_height=350)
    render_caption("solar_table", captions)

elif tab == "Hourly Pattern":
    hourly = solar.groupby("hour")["solar_kwh"].mean().reset_index()
    fig = go.Figure(go.Bar(x=hourly["hour"], y=hourly["solar_kwh"], marker_color="#eab308",
                           text=hourly["solar_kwh"].apply(lambda x: f"{x:.1f}"), textposition="outside"))
    fig.add_vrect(x0=9.5, x1=15.5, fillcolor="rgba(234,179,8,0.08)", layer="below", line_width=0,
                  annotation_text="Solar Peak", annotation_position="top left")
    fig.update_layout(height=400, margin=dict(l=40, r=20, t=20, b=40),
                      xaxis_title="Hour", yaxis_title="Avg kWh", xaxis=dict(tickmode="linear", dtick=1),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)
    render_caption("hourly_chart", captions)

elif tab == "CAPEX Priority":
    if len(capex) > 0:
        st.markdown("### Solar Installation Priority (Non-Solar Stores)")
        st.caption("Ranked by payback period — lower = invest first")
        top = capex.head(15)
        fig = go.Figure(go.Bar(x=top["name"], y=top["payback_months"],
                               marker_color=top["payback_months"].apply(
                                   lambda x: "#22c55e" if x < 18 else ("#f97316" if x < 24 else "#ef4444")),
                               text=top["payback_months"].apply(lambda x: f"{x:.0f}mo"), textposition="outside"))
        fig.update_layout(height=400, margin=dict(l=40, r=20, t=20, b=80),
                          xaxis_tickangle=-45, yaxis_title="Payback (months)",
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
        render_caption("capex_chart", captions)
        _capex_df = capex[["rank", "name", "sector", "est_solar_kw", "est_monthly_saving_mmk",
                            "est_install_cost_mmk", "payback_months"]].copy()
        _capex_df["est_solar_kw"] = _capex_df["est_solar_kw"].round(1)
        _capex_df["est_monthly_saving_mmk"] = _capex_df["est_monthly_saving_mmk"].round(0)
        _capex_df["est_install_cost_mmk"] = _capex_df["est_install_cost_mmk"].round(0)
        _capex_df["payback_months"] = _capex_df["payback_months"].round(1)
        _capex_df = _capex_df.rename(columns={
            "rank": "#", "name": "Store", "sector": "Sector", "est_solar_kw": "Solar kW",
            "est_monthly_saving_mmk": "Monthly Save (MMK)", "est_install_cost_mmk": "Install Cost (MMK)",
            "payback_months": "Payback (mo)"})
        render_smart_table(_capex_df, key="capex_table", title="CAPEX Priority Ranking",
                           highlight_cols={"Payback (mo)": {"good": "low", "thresholds": [18, 24]}},
                           max_height=400)
        render_caption("capex_table", captions)
    else:
        st.info("All stores already have solar!")

elif tab == "Recommendations":
    for _, row in solar_results.iterrows():
        if row["recommendations"]:
            with st.container():
                st.markdown(f"**{row['name']}** ({row['channel']})")
                for rec in row["recommendations"]:
                    st.info(rec)
                st.markdown("")

# AI Insights merged into Page Intelligence at top


# Generate element captions for next visit
from utils.element_captions import generate_pending_captions
generate_pending_captions()

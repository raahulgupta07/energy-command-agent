"""
Energy Intelligence System (EIS) - Main Application
AI-driven Energy Control Tower — shadcn/ui design
"""

import streamlit as st
import streamlit_shadcn_ui as ui
import pandas as pd
from config.settings import DASHBOARD, SECTORS

st.set_page_config(
    page_title=DASHBOARD["page_title"],
    page_icon=DASHBOARD["page_icon"],
    layout=DASHBOARD["layout"],
    initial_sidebar_state="expanded",
)

# ── Global Styles ──
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #0f172a; }
    [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    .block-container { padding-top: 2rem; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stMarkdown h1 { color: #0f172a; font-weight: 800; }
    .stMarkdown h2 { color: #1e293b; font-weight: 700; }
    .nav-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        transition: all 0.2s;
        height: 160px;
        display: flex;
        flex-direction: column;
    }
    .nav-card:hover { border-color: #3b82f6; box-shadow: 0 4px 12px rgba(59,130,246,0.15); }
    .nav-icon { font-size: 1.8rem; margin-bottom: 8px; flex-shrink: 0; }
    .nav-title { font-size: 1rem; font-weight: 700; color: #0f172a; margin-bottom: 4px; flex-shrink: 0; }
    .nav-desc { font-size: 0.85rem; color: #64748b; line-height: 1.4; flex: 1; overflow: hidden; }
    .hero-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0d47a1 100%);
        color: white;
        padding: 32px 36px;
        border-radius: 16px;
        margin-bottom: 24px;
    }
    .hero-title { font-size: 2rem; font-weight: 800; margin: 0; }
    .hero-sub { font-size: 1.05rem; opacity: 0.85; margin-top: 6px; }
</style>
""", unsafe_allow_html=True)

# ── Hero Banner ──
st.markdown("""
<div class="hero-banner">
    <p class="hero-title">Energy Intelligence System</p>
    <p class="hero-sub">AI-Driven Energy Control Tower for Operational Sustainability</p>
</div>
""", unsafe_allow_html=True)

# ── Load Data ──
@st.cache_data(ttl=300)
def load_home_data():
    from utils.data_loader import load_stores, load_daily_energy, load_diesel_prices, load_diesel_inventory, load_fx_rates
    return {
        "stores": load_stores(),
        "energy": load_daily_energy(),
        "prices": load_diesel_prices(),
        "inventory": load_diesel_inventory(),
        "fx": load_fx_rates(),
    }

try:
    data = load_home_data()

    # ── KPI Cards Row 1 ──
    cols = st.columns(4)
    with cols[0]:
        ui.metric_card(title="Total Stores", content=str(len(data["stores"])),
                       description="across 4 sectors", key="mc_stores")
    with cols[1]:
        latest_price = int(data["prices"]["diesel_price_mmk"].iloc[-1])
        prev_price = int(data["prices"]["diesel_price_mmk"].iloc[-2])
        delta = f"{(latest_price - prev_price) / prev_price * 100:+.1f}% from yesterday"
        ui.metric_card(title="Diesel Price", content=f"{latest_price:,} MMK/L",
                       description=delta, key="mc_price")
    with cols[2]:
        latest_fx = int(data["fx"]["usd_mmk"].iloc[-1])
        fx_prev = int(data["fx"]["usd_mmk"].iloc[-2])
        fx_delta = f"{(latest_fx - fx_prev) / fx_prev * 100:+.1f}% from yesterday"
        ui.metric_card(title="USD/MMK Rate", content=f"{latest_fx:,}",
                       description=fx_delta, key="mc_fx")
    with cols[3]:
        avg_bo = data["energy"].groupby("date")["blackout_hours"].mean().iloc[-1]
        ui.metric_card(title="Avg Blackout Today", content=f"{avg_bo:.1f} hrs",
                       description="per store average", key="mc_blackout")

    # ── KPI Cards Row 2 ──
    cols2 = st.columns(4)
    with cols2[0]:
        total_diesel = data["energy"]["diesel_cost_mmk"].sum()
        ui.metric_card(title="Total Diesel Cost", content=f"{total_diesel/1e6:,.0f}M MMK",
                       description="cumulative period", key="mc_diesel")
    with cols2[1]:
        solar = data["stores"]["has_solar"].sum()
        ui.metric_card(title="Solar Sites", content=f"{solar} / {len(data['stores'])}",
                       description=f"{solar/len(data['stores'])*100:.0f}% coverage", key="mc_solar")

    st.markdown("")

    # ── Navigation Grid ──
    st.markdown("### Dashboard Navigation")

    row1 = st.columns(4)
    nav_items_1 = [
        ("1_sector_dashboard", "Sector Dashboard", "Drill into Retail, F&B, Distribution, Property. Store-level operating modes and energy costs."),
        ("2_holdings_dashboard", "Holdings Control Tower", "Group-level KPIs, sector comparison, Energy Resilience Index ranking."),
        ("3_diesel_intelligence", "Diesel Intelligence", "7-day price forecast, buy/hold signals, volatility tracking, FX correlation."),
        ("4_blackout_monitor", "Blackout Monitor", "Township risk heatmap, probability timeline, pattern analysis, alerts."),
    ]
    icons_1 = ["🏪", "🏛️", "⛽", "🔌"]

    for col, (page, title, desc), icon in zip(row1, nav_items_1, icons_1):
        with col:
            st.markdown(f"""
            <div class="nav-card">
                <div class="nav-icon">{icon}</div>
                <div class="nav-title">{title}</div>
                <div class="nav-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("")

    row2 = st.columns(4)
    nav_items_2 = [
        ("5_store_decisions", "Store Decisions", "Daily Operating Plan: FULL / REDUCED / CRITICAL / CLOSE per store."),
        ("6_solar_performance", "Solar Performance", "Generation tracking, diesel offset, load-shifting, CAPEX prioritization."),
        ("7_alerts_center", "Alerts Center", "Tier 1 Critical, Tier 2 Warning, Tier 3 Info — all in one place."),
        ("8_scenario_simulator", "Scenario Simulator", "What-if analysis: diesel price, blackout hours, FX, solar expansion."),
    ]
    icons_2 = ["📋", "☀️", "🚨", "🔮"]

    for col, (page, title, desc), icon in zip(row2, nav_items_2, icons_2):
        with col:
            st.markdown(f"""
            <div class="nav-card">
                <div class="nav-icon">{icon}</div>
                <div class="nav-title">{title}</div>
                <div class="nav-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("")

    # ── Quick Actions ──
    st.markdown("### Quick Actions")
    c1, c2, c3 = st.columns(3)
    with c1:
        if ui.button(text="Upload Data", variant="outline", key="btn_upload"):
            st.switch_page("pages/10_📤_Data_Upload.py")
    with c2:
        if ui.button(text="View Alerts", variant="destructive", key="btn_alerts"):
            st.switch_page("pages/08_🚨_Alerts_Center.py")
    with c3:
        if ui.button(text="Run Scenario", variant="secondary", key="btn_scenario"):
            st.switch_page("pages/09_🔮_Scenario_Simulator.py")

    # ── System Status ──
    st.markdown("### System Status")
    cols = st.columns(3)
    with cols[0]:
        ui.metric_card(title="Data Records", content=f"{len(data['energy']):,}",
                       description="energy records loaded", key="mc_records")
    with cols[1]:
        date_range = f"{data['energy']['date'].min().date()} to {data['energy']['date'].max().date()}"
        ui.metric_card(title="Date Range", content=date_range,
                       description="data coverage", key="mc_dates")
    with cols[2]:
        from config.settings import DATA_SOURCE
        ui.metric_card(title="Data Source", content=DATA_SOURCE.upper(),
                       description="sample or real data", key="mc_source")

except FileNotFoundError:
    st.error("Data not found. Run: `python data/generators/synthetic_data.py`")

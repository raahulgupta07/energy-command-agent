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
    .new-badge {
        display: inline-block;
        background: #10b981;
        color: white;
        padding: 1px 8px;
        border-radius: 10px;
        font-size: 0.65rem;
        font-weight: 700;
        margin-left: 6px;
        vertical-align: middle;
    }
    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 6px;
    }
    .status-green { background: #22c55e; }
    .status-yellow { background: #f59e0b; }
    .status-red { background: #ef4444; }
    .status-gray { background: #94a3b8; }
</style>
""", unsafe_allow_html=True)

# ── Hero Banner ──
st.markdown("""
<div class="hero-banner">
    <p class="hero-title">Energy Intelligence System</p>
    <p class="hero-sub">AI-Driven Energy Control Tower for Operational Sustainability</p>
    <div style="margin-top:12px;display:flex;gap:16px;flex-wrap:wrap;font-size:0.8rem;opacity:0.7">
        <span>55 Stores</span> <span>|</span>
        <span>4 Sectors</span> <span>|</span>
        <span>9 AI Models</span> <span>|</span>
        <span>15 KPIs</span> <span>|</span>
        <span>25 Agent Tools</span> <span>|</span>
        <span>5 Operating Modes</span>
    </div>
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

    # ── KPI Cards Row 1: Core Metrics ──
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

    # ── KPI Cards Row 2: New KPIs ──
    cols2 = st.columns(4)
    with cols2[0]:
        total_diesel = data["energy"]["diesel_cost_mmk"].sum()
        ui.metric_card(title="Total Diesel Cost", content=f"{total_diesel/1e6:,.0f}M MMK",
                       description="cumulative period", key="mc_diesel")
    with cols2[1]:
        solar = data["stores"]["has_solar"].sum()
        ui.metric_card(title="Solar Sites", content=f"{solar} / {len(data['stores'])}",
                       description=f"{solar/len(data['stores'])*100:.0f}% coverage", key="mc_solar")
    with cols2[2]:
        try:
            from utils.database import get_override_stats
            adoption = get_override_stats()
            ui.metric_card(title="AI Adoption Rate", content=f"{adoption['adoption_rate_pct']:.0f}%",
                           description=f"{adoption['accepted']}/{adoption['total']} decisions", key="mc_adoption")
        except Exception:
            ui.metric_card(title="AI Adoption Rate", content="—",
                           description="no decisions yet", key="mc_adoption")
    with cols2[3]:
        try:
            from utils.database import get_compliance_summary
            comp = get_compliance_summary()
            ui.metric_card(title="Data Compliance", content=f"{comp['compliance_pct']:.0f}%",
                           description=f"{comp['total_submissions']} submissions", key="mc_compliance")
        except Exception:
            ui.metric_card(title="Data Compliance", content="—",
                           description="no data yet", key="mc_compliance")

    st.markdown("")

    # ── Navigation Grid ──
    st.markdown("### Dashboard Navigation")

    row1 = st.columns(4)
    nav_items_1 = [
        ("🏪", "Sector Dashboard", "Drill into Retail, F&B, Distribution, Property."),
        ("🏛️", "Holdings Control Tower", "Group KPIs, ERI ranking, <span class='new-badge'>AI Adoption</span> <span class='new-badge'>Data Quality</span>"),
        ("⛽", "Diesel Intelligence", "7-day price forecast, buy/hold signals, FX correlation."),
        ("🔌", "Blackout Monitor", "Township heatmap, probability predictions, <span class='new-badge'>72hr Forecast</span>"),
    ]
    for col, (icon, title, desc) in zip(row1, nav_items_1):
        with col:
            st.markdown(f'<div class="nav-card"><div class="nav-icon">{icon}</div><div class="nav-title">{title}</div><div class="nav-desc">{desc}</div></div>', unsafe_allow_html=True)

    st.markdown("")

    row2 = st.columns(4)
    nav_items_2 = [
        ("📋", "Store Decisions", "Daily plan: 5 modes. <span class='new-badge'>Override UI</span> <span class='new-badge'>EBITDA/hr</span> <span class='new-badge'>Sector Rules</span>"),
        ("☀️", "Solar Performance", "Generation, diesel offset, <span class='new-badge'>Hourly Schedule</span>"),
        ("🚨", "Alerts Center", "Tier 1/2/3 alerts. <span class='new-badge'>Agent Decisions</span> <span class='new-badge'>Cascade Detection</span>"),
        ("🔮", "Scenario Simulator", "What-if: diesel, blackout, FX, solar expansion."),
    ]
    for col, (icon, title, desc) in zip(row2, nav_items_2):
        with col:
            st.markdown(f'<div class="nav-card"><div class="nav-icon">{icon}</div><div class="nav-title">{title}</div><div class="nav-desc">{desc}</div></div>', unsafe_allow_html=True)

    st.markdown("")

    row3 = st.columns(4)
    nav_items_3 = [
        ("📤", "Data Upload", "Upload CSVs, download <span class='new-badge'>Master Template</span>"),
        ("🛡️", "BCP Dashboard", "BCP scores, playbooks, RTO, incidents, drills."),
        ("📄", "Requirements", "Business requirements document."),
        ("⚙️", "System Status", "See below — API, email, scheduler, data freshness."),
    ]
    for col, (icon, title, desc) in zip(row3, nav_items_3):
        with col:
            st.markdown(f'<div class="nav-card"><div class="nav-icon">{icon}</div><div class="nav-title">{title}</div><div class="nav-desc">{desc}</div></div>', unsafe_allow_html=True)

    st.markdown("")

    # ── Quick Actions ──
    st.markdown("### Quick Actions")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if ui.button(text="Upload Data", variant="outline", key="btn_upload"):
            st.switch_page("pages/10_📤_Data_Upload.py")
    with c2:
        if ui.button(text="View Alerts", variant="destructive", key="btn_alerts"):
            st.switch_page("pages/08_🚨_Alerts_Center.py")
    with c3:
        if ui.button(text="Run Scenario", variant="secondary", key="btn_scenario"):
            st.switch_page("pages/09_🔮_Scenario_Simulator.py")
    with c4:
        if ui.button(text="Store Decisions", variant="default", key="btn_decisions"):
            st.switch_page("pages/06_📋_Store_Decisions.py")

    st.markdown("")

    # ══════════════════════════════════════════════════════════════════════════
    # SYSTEM STATUS — Shows what features are active
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0f172a,#1e293b);color:white;padding:20px 24px;border-radius:12px;margin-bottom:16px">
        <h3 style="margin:0;color:white">System Status</h3>
        <p style="margin:4px 0 0;font-size:0.85rem;opacity:0.7">Feature availability and configuration status</p>
    </div>
    """, unsafe_allow_html=True)

    # Status checks
    from config.settings import DATA_SOURCE, EMAIL_CONFIG
    from utils.llm_client import is_llm_available

    api_ok = is_llm_available()
    email_ok = EMAIL_CONFIG.get("enabled", False)

    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        dot = "status-green" if api_ok else "status-red"
        status = "Connected" if api_ok else "Not configured"
        st.markdown(f"""
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:14px 16px">
            <div style="font-size:0.75rem;color:#64748b">OpenRouter API</div>
            <div style="font-size:1rem;font-weight:600;margin-top:4px">
                <span class="status-dot {dot}"></span>{status}
            </div>
            <div style="font-size:0.75rem;color:#94a3b8;margin-top:4px">
                {'AI chat, insights, agents active' if api_ok else 'Rule-based mode only. Add key to .env'}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with sc2:
        dot = "status-green" if email_ok else "status-gray"
        status = "Configured" if email_ok else "Not configured"
        st.markdown(f"""
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:14px 16px">
            <div style="font-size:0.75rem;color:#64748b">Email Alerts (Outlook)</div>
            <div style="font-size:1rem;font-weight:600;margin-top:4px">
                <span class="status-dot {dot}"></span>{status}
            </div>
            <div style="font-size:0.75rem;color:#94a3b8;margin-top:4px">
                {'Morning briefing, critical alerts, reports' if email_ok else 'Set EIS_SMTP_USER in .env to enable'}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with sc3:
        st.markdown(f"""
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:14px 16px">
            <div style="font-size:0.75rem;color:#64748b">Scheduler</div>
            <div style="font-size:1rem;font-weight:600;margin-top:4px">
                <span class="status-dot status-yellow"></span>Manual
            </div>
            <div style="font-size:0.75rem;color:#94a3b8;margin-top:4px">
                Run: python scheduler.py
            </div>
        </div>
        """, unsafe_allow_html=True)

    with sc4:
        st.markdown(f"""
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:14px 16px">
            <div style="font-size:0.75rem;color:#64748b">Data Source</div>
            <div style="font-size:1rem;font-weight:600;margin-top:4px">
                <span class="status-dot status-green"></span>{DATA_SOURCE.upper()}
            </div>
            <div style="font-size:0.75rem;color:#94a3b8;margin-top:4px">
                {len(data['energy']):,} records | {data['energy']['date'].min().date()} to {data['energy']['date'].max().date()}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")

    # ── What's New in v2.0 ──
    with st.expander("What's New in v2.0 — BCP Framework Implementation", expanded=False):
        st.markdown("""
        | Feature | Where to Find It |
        |---------|-----------------|
        | **SELECTIVE mode** (5th operating mode) | Store Decisions → Operating Plan |
        | **EBITDA per hour** (full formula with labour cost) | Store Decisions → Plan Table |
        | **Override / Confirm** buttons | Store Decisions → Override / Confirm tab |
        | **Decision Rights** matrix | Store Decisions → Decision Rights tab |
        | **13 Sector-specific rules** | Store Decisions (auto-applied, shown in reason) |
        | **AI Adoption tracking** | Holdings → AI Adoption tab |
        | **Data Quality tracking** | Holdings → Data Quality tab |
        | **Cold Chain Uptime %** KPI | Holdings → KPI cards |
        | **Generator EBITDA** KPI | Holdings → KPI cards |
        | **Agent Decisions** log | Alerts Center → Agent Decisions tab |
        | **Blackout Cascade** detection | Alerts Center → Critical alerts |
        | **72-hour Blackout** forecast | Blackout Monitor (extended) |
        | **Pre-cooling** recommendations | Spoilage Predictor (integrated) |
        | **Solar hourly schedule** | Solar Optimizer (integrated) |
        | **Supplier delivery scoring** | Stockout Alert (integrated) |
        | **Email reports** (5 types) | Via scheduler: `python scheduler.py` |
        | **Master Data Template** | Data Upload → Download button |
        | **25 agent tools** (was 19) | AI chat on every page |
        """)

except FileNotFoundError:
    st.error("Data not found. Run: `python data/generators/synthetic_data.py`")

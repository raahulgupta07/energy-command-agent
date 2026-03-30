"""
Page 7: Alerts Center — shadcn/ui
Consolidated alerts from all AI models.
"""

import streamlit as st
import streamlit_shadcn_ui as ui
import pandas as pd
from utils.data_loader import (
    load_stores, load_daily_energy, load_store_sales,
    load_diesel_inventory, load_diesel_prices, load_solar_generation, load_temperature_logs,
)
from models.diesel_price_forecast import DieselPriceForecast
from models.blackout_prediction import BlackoutPredictor
from models.store_decision_engine import StoreDecisionEngine
from models.diesel_optimizer import DieselOptimizer
from models.stockout_alert import StockoutAlert
from models.spoilage_predictor import SpoilagePredictor
from utils.element_captions import get_page_captions, render_caption
from utils.page_intelligence import render_page_intelligence
from utils.smart_table import render_smart_table
from utils.database import get_agent_decisions, get_agent_decision_stats

st.set_page_config(page_title="Alerts Center", page_icon="🚨", layout="wide")

st.markdown("""
<div style="background:linear-gradient(135deg,#7f1d1d,#dc2626);color:white;padding:20px 28px;border-radius:12px;margin-bottom:20px">
    <h2 style="margin:0;color:white">Alerts Center</h2>
    <p style="margin:4px 0 0;opacity:0.85">All alerts from all AI models — prioritized by severity</p>
</div>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def collect_alerts():
    data = {
        "stores": load_stores(), "energy": load_daily_energy(), "sales": load_store_sales(),
        "inventory": load_diesel_inventory(), "prices": load_diesel_prices(),
        "solar": load_solar_generation(), "temp": load_temperature_logs(),
    }
    all_alerts = []

    # M1
    dpf = DieselPriceForecast()
    dpf.fit(data["prices"])
    fc = dpf.predict(7)
    rec = dpf.get_buy_recommendation(fc)
    if rec["signal"] in ["BUY NOW", "BUY"]:
        all_alerts.append({"tier": 1 if rec["signal"] == "BUY NOW" else 2,
                           "source": "Diesel Price", "message": f"{rec['signal']}: {rec['reason']}",
                           "action": rec["recommended_action"]})

    # M2
    bp = BlackoutPredictor()
    bp.fit(data["energy"], data["stores"])
    pred = bp.predict_next_day(data["energy"], data["stores"])
    for a in bp.get_alerts(pred):
        a["source"] = "Blackout"
        a["action"] = "Pre-adjust operations"
        all_alerts.append(a)

    # M3
    sde = StoreDecisionEngine()
    sde.generate_daily_plan(data["stores"], data["energy"], data["sales"], data["inventory"], solar_df=data["solar"])
    for a in sde.get_alerts():
        a["source"] = "Store Decision"
        a["action"] = "Execute operating plan"
        all_alerts.append(a)

    # M4
    do = DieselOptimizer()
    do.fit(data["energy"], data["stores"])
    analysis = do.analyze(data["energy"], data["stores"])
    for a in do.get_alerts(analysis):
        a["source"] = "Diesel Optimizer"
        a["action"] = "Schedule maintenance"
        all_alerts.append(a)

    # M6
    sa = StockoutAlert()
    sa.analyze(data["inventory"], data["energy"], data["stores"])
    for a in sa.get_alerts():
        a["source"] = "Stock-Out"
        a["action"] = "Order or reallocate diesel"
        all_alerts.append(a)

    # M7
    sp = SpoilagePredictor()
    sp.fit(data["temp"], data["energy"])
    risk = sp.predict_risk(data["stores"], data["energy"], data["temp"])
    for a in sp.get_alerts(risk):
        a["source"] = "Spoilage"
        a["action"] = "Transfer perishable stock"
        all_alerts.append(a)

    # C4: Blackout Cascade (3+ sites in township)
    try:
        cascades = bp.detect_cascade(pred)
        for a in cascades:
            a["source"] = "Blackout Cascade"
            a["action"] = "Activate crisis protocol"
            all_alerts.append(a)
    except Exception:
        pass

    # C5: Solar Underperformance
    try:
        from models.solar_optimizer import SolarOptimizer
        so = SolarOptimizer()
        current_price = data["prices"]["diesel_price_mmk"].iloc[-1]
        solar_results = so.optimize_all(data["stores"], data["solar"], data["energy"], current_price)
        solar_sites = solar_results[solar_results["has_solar"] == True]
        for _, site in solar_sites.iterrows():
            if site.get("daily_solar_kwh", 0) > 0:
                expected = site.get("solar_capacity_kw", 0) * 4.5
                if expected > 0 and site["daily_solar_kwh"] < expected * 0.8:
                    pct = site["daily_solar_kwh"] / expected * 100
                    all_alerts.append({
                        "tier": 2, "source": "Solar Performance",
                        "message": f"Solar underperformance: {site.get('name', site['store_id'])} — {pct:.0f}% of expected output",
                        "action": "Schedule panel inspection",
                    })
    except Exception:
        pass

    # Deduplicate
    seen = set()
    unique = []
    for a in all_alerts:
        key = a.get("message", "")
        if key not in seen:
            seen.add(key)
            unique.append(a)
    return sorted(unique, key=lambda x: x.get("tier", 3))

all_alerts = collect_alerts()
tier1 = [a for a in all_alerts if a.get("tier") == 1]
tier2 = [a for a in all_alerts if a.get("tier") == 2]
tier3 = [a for a in all_alerts if a.get("tier") == 3]

render_page_intelligence("alerts", f"Total alerts: {len(all_alerts)}, Tier 1 (critical): {len(tier1)}, Tier 2 (warning): {len(tier2)}, Tier 3 (info): {len(tier3)}.")

# ── AI Captions ──
_source_list = ", ".join(set(a.get("source", "Unknown") for a in all_alerts)) if all_alerts else "none"
captions = get_page_captions("alerts", [
    {"id": "a_total", "type": "metric", "title": "Total Alerts", "value": str(len(all_alerts))},
    {"id": "a_t1", "type": "metric", "title": "CRITICAL Alerts", "value": str(len(tier1))},
    {"id": "a_t2", "type": "metric", "title": "WARNING Alerts", "value": str(len(tier2))},
    {"id": "a_t3", "type": "metric", "title": "INFO Alerts", "value": str(len(tier3))},
    {"id": "all_alerts_table", "type": "table", "title": "Full Alert Log", "value": f"{len(all_alerts)} alerts with tier, source, message, action"},
    {"id": "source_table", "type": "table", "title": "Alerts by Source", "value": f"Alert counts from sources: {_source_list}"},
], data_summary=f"{len(all_alerts)} total alerts: {len(tier1)} critical, {len(tier2)} warning, {len(tier3)} info. Sources: {_source_list}.")

# ── KPIs ──
cols = st.columns(4)
with cols[0]:
    ui.metric_card(title="Total Alerts", content=str(len(all_alerts)), description="from 6 models", key="a_total")
    render_caption("a_total", captions)
with cols[1]:
    ui.metric_card(title="CRITICAL", content=str(len(tier1)), description="act now", key="a_t1")
    render_caption("a_t1", captions)
with cols[2]:
    ui.metric_card(title="WARNING", content=str(len(tier2)), description="act today", key="a_t2")
    render_caption("a_t2", captions)
with cols[3]:
    ui.metric_card(title="INFO", content=str(len(tier3)), description="optimize", key="a_t3")
    render_caption("a_t3", captions)

st.markdown("")
tab = ui.tabs(options=["Critical", "Warning", "Info", "All Alerts", "Agent Decisions"], default_value="Critical", key="alert_tabs")

def render_alerts(alerts, color, label):
    if not alerts:
        st.success(f"No {label.lower()} alerts.")
        return
    for i, a in enumerate(alerts):
        ui.alert(title=f"[{a.get('source', 'System')}] {label}",
                 description=a["message"], key=f"alert_{label}_{i}")
        st.caption(f"Action: {a.get('action', 'Review')}")

if tab == "Critical":
    st.markdown("### TIER 1 — CRITICAL (Act NOW)")
    render_alerts(tier1, "#ef4444", "Critical")

elif tab == "Warning":
    st.markdown("### TIER 2 — WARNING (Act TODAY)")
    render_alerts(tier2[:20], "#f97316", "Warning")
    if len(tier2) > 20:
        st.info(f"Showing 20 of {len(tier2)} warnings")

elif tab == "Info":
    st.markdown("### TIER 3 — INFO (Optimize)")
    render_alerts(tier3, "#3b82f6", "Info")

elif tab == "All Alerts":
    st.markdown("### Full Alert Log")
    if all_alerts:
        df = pd.DataFrame(all_alerts)
        cols_show = [c for c in ["tier", "source", "message", "action"] if c in df.columns]
        df_show = df[cols_show].copy()
        df_show.columns = ["Tier", "Source", "Message", "Action"][:len(cols_show)]
        # Map tier numbers to severity labels for badge rendering
        _tier_map = {1: "CRITICAL", 2: "WARNING", 3: "LOW"}
        if "Tier" in df_show.columns:
            df_show["Tier"] = df_show["Tier"].map(lambda x: _tier_map.get(x, str(x)))
        render_smart_table(df_show, key="all_alerts_table", title="Full Alert Log",
                           severity_col="Tier", max_height=500)
        render_caption("all_alerts_table", captions)

elif tab == "Agent Decisions":
    st.markdown("### AI Agent Decision Log")
    st.markdown("""
    <div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:10px;padding:14px 18px;margin-bottom:16px">
        Audit trail of all AI agent decisions — what was recommended, which tools were used, confidence level.
    </div>
    """, unsafe_allow_html=True)

    # Stats
    agent_stats = get_agent_decision_stats()
    st.markdown(f"**Total agent decisions: {agent_stats['total_decisions']}**")
    if agent_stats["by_agent"]:
        ag_cols = st.columns(len(agent_stats["by_agent"]))
        for i, (agent, count) in enumerate(agent_stats["by_agent"].items()):
            with ag_cols[i]:
                ui.metric_card(title=agent, content=str(count), description="decisions", key=f"ag_{agent}")

    # Filters
    fc1, fc2 = st.columns(2)
    with fc1:
        filter_agent = st.selectbox("Filter by Agent", ["All"] + list(agent_stats.get("by_agent", {}).keys()),
                                     key="filter_agent")
    with fc2:
        filter_limit = st.slider("Show last N decisions", 10, 100, 30, key="filter_limit")

    agent_filter = filter_agent if filter_agent != "All" else None
    decisions = get_agent_decisions(limit=filter_limit, agent_name=agent_filter)

    if decisions:
        dec_df = pd.DataFrame(decisions)
        display_cols = ["agent_name", "decision_type", "store_id", "recommendation", "confidence",
                        "tools_used", "model_used", "created_at"]
        display_cols = [c for c in display_cols if c in dec_df.columns]
        dec_display = dec_df[display_cols].copy()

        # Format
        if "confidence" in dec_display.columns:
            dec_display["confidence"] = dec_display["confidence"].apply(
                lambda v: f"{v:.0%}" if pd.notna(v) else "—")
        if "tools_used" in dec_display.columns:
            dec_display["tools_used"] = dec_display["tools_used"].apply(
                lambda v: v[:60] + "..." if isinstance(v, str) and len(v) > 60 else (v or "—"))
        if "recommendation" in dec_display.columns:
            dec_display["recommendation"] = dec_display["recommendation"].apply(
                lambda v: v[:80] + "..." if isinstance(v, str) and len(v) > 80 else (v or "—"))

        col_names = {"agent_name": "Agent", "decision_type": "Type", "store_id": "Store",
                     "recommendation": "Recommendation", "confidence": "Confidence",
                     "tools_used": "Tools", "model_used": "Model", "created_at": "Timestamp"}
        dec_display.columns = [col_names.get(c, c) for c in dec_display.columns]

        render_smart_table(dec_display, key="agent_dec_table", title="Agent Decision Log",
                           max_height=400)
    else:
        st.caption("No agent decisions logged yet. Decisions are recorded when agents run via scheduler or chat.")

# ── Source Breakdown ──
st.markdown("### Alerts by Source")
source_counts = {}
for a in all_alerts:
    s = a.get("source", "Unknown")
    source_counts[s] = source_counts.get(s, 0) + 1
if source_counts:
    src_df = pd.DataFrame([{"Source": k, "Count": v} for k, v in sorted(source_counts.items(), key=lambda x: -x[1])])
    render_smart_table(src_df, key="source_table", title="Alerts by Source", max_height=250)
    render_caption("source_table", captions)

# AI Insights merged into Page Intelligence at top


# Generate element captions for next visit
from utils.element_captions import generate_pending_captions
generate_pending_captions()

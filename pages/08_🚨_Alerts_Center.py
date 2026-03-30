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
tab = ui.tabs(options=["Critical", "Warning", "Info", "All Alerts"], default_value="Critical", key="alert_tabs")

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

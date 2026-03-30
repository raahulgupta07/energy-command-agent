"""
Page 4: Blackout Monitor — shadcn/ui
Township heatmap, predictions, pattern analysis.
"""

import streamlit as st
import streamlit_shadcn_ui as ui
import plotly.graph_objects as go
import pandas as pd
from utils.data_loader import load_stores, load_daily_energy
from models.blackout_prediction import BlackoutPredictor
from utils.element_captions import get_page_captions, render_caption
from utils.page_intelligence import render_page_intelligence
from utils.smart_table import render_smart_table

st.set_page_config(page_title="Blackout Monitor", page_icon="🔌", layout="wide")

st.markdown("""
<div style="background:linear-gradient(135deg,#1e1e1e,#b91c1c);color:white;padding:20px 28px;border-radius:12px;margin-bottom:20px">
    <h2 style="margin:0;color:white">Blackout Monitor</h2>
    <p style="margin:4px 0 0;opacity:0.85">Prediction, township risk mapping, and pattern analysis</p>
</div>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_data():
    return load_stores(), load_daily_energy()

stores, energy = load_data()

@st.cache_resource
def train(_stores, _energy):
    bp = BlackoutPredictor()
    bp.fit(_energy, _stores)
    pred = bp.predict_next_day(_energy, _stores)
    tr = bp.get_township_risk_map(pred)
    alerts = bp.get_alerts(pred)
    return pred, tr, alerts

pred, township_risk, alerts = train(stores, energy)

# ── AI Captions ──
_high_risk_count = str((pred["risk_level"] == "HIGH").sum())
_med_risk_count = str((pred["risk_level"] == "MEDIUM").sum())
_avg_prob = f"{pred['blackout_probability'].mean()*100:.0f}%"
_avg_dur = f"{pred['expected_duration_hours'].mean():.1f} hrs"
_alert_count = str(len(alerts))

render_page_intelligence("blackout", f"High risk stores: {_high_risk_count}, Avg probability: {_avg_prob}, Avg duration: {_avg_dur}, Active alerts: {_alert_count}.")

captions = get_page_captions("blackout", [
    {"id": "high_risk", "type": "metric", "title": "High Risk Stores", "value": _high_risk_count},
    {"id": "med_risk", "type": "metric", "title": "Medium Risk", "value": _med_risk_count},
    {"id": "avg_prob", "type": "metric", "title": "Avg Probability", "value": _avg_prob},
    {"id": "avg_dur", "type": "metric", "title": "Avg Duration", "value": _avg_dur},
    {"id": "alerts_count", "type": "metric", "title": "Alerts", "value": _alert_count},
    {"id": "township_bar", "type": "chart", "title": "Township Risk Bar Chart", "value": f"{len(township_risk)} townships ranked by blackout probability"},
    {"id": "township_table", "type": "table", "title": "Township Risk Table", "value": f"{len(township_risk)} townships with probability, store count, high-risk count"},
    {"id": "pred_table", "type": "table", "title": "Store Predictions Table", "value": f"{len(pred)} stores with probability, risk level, duration, window"},
    {"id": "dow_chart", "type": "chart", "title": "Day-of-Week Blackout Pattern", "value": "Average blackout hours by day of week"},
    {"id": "heatmap_chart", "type": "chart", "title": "Last 30 Days Blackout Heatmap", "value": "Township x date heatmap of blackout hours"},
], data_summary=f"Blackout predictions for {len(pred)} stores. {_high_risk_count} high-risk, {_med_risk_count} medium-risk. Avg probability {_avg_prob}, avg duration {_avg_dur}. {_alert_count} active alerts across {len(township_risk)} townships.")

# ── KPIs ──
cols = st.columns(4)
with cols[0]:
    ui.metric_card(title="High Risk Stores", content=_high_risk_count,
                   description="tomorrow", key="b_high")
    render_caption("high_risk", captions)
with cols[1]:
    ui.metric_card(title="Medium Risk", content=_med_risk_count,
                   description="stores", key="b_med")
    render_caption("med_risk", captions)
with cols[2]:
    ui.metric_card(title="Avg Probability", content=_avg_prob,
                   description="all stores", key="b_avg")
    render_caption("avg_prob", captions)
with cols[3]:
    ui.metric_card(title="Avg Duration", content=_avg_dur,
                   description="expected", key="b_dur")
    render_caption("avg_dur", captions)
cols2 = st.columns(4)
with cols2[0]:
    ui.metric_card(title="Alerts", content=_alert_count,
                   description="blackout warnings", key="b_alerts")
    render_caption("alerts_count", captions)

# ── Alerts ──
if alerts:
    st.markdown("### Active Alerts")
    for a in alerts[:5]:
        ui.alert(title=f"{a['store_name']} ({a['township']})",
                 description=f"{a['probability']*100:.0f}% probability, ~{a['expected_duration']:.1f} hrs, window: {a['likely_window']}",
                 key=f"ba_{a['store_id']}")

st.markdown("")

tab = ui.tabs(options=["Township Map", "Store Predictions", "Patterns"], default_value="Township Map", key="bo_tabs")

if tab == "Township Map":
    col1, col2 = st.columns([2, 1])
    with col1:
        fig = go.Figure(go.Bar(
            x=township_risk["avg_probability"] * 100, y=township_risk["township"], orientation="h",
            marker_color=township_risk["avg_probability"].apply(
                lambda p: "#ef4444" if p >= 0.7 else ("#f97316" if p >= 0.4 else "#22c55e")),
            text=township_risk["avg_probability"].apply(lambda p: f"{p*100:.0f}%"), textposition="outside"))
        fig.update_layout(height=max(400, len(township_risk) * 28),
                          margin=dict(l=150, r=50, t=10, b=40), xaxis_title="Blackout Probability (%)",
                          yaxis=dict(autorange="reversed"),
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
        render_caption("township_bar", captions)
    with col2:
        _tr_display = township_risk[["township", "avg_probability", "num_stores", "high_risk_stores"]].copy()
        _tr_display["avg_probability"] = _tr_display["avg_probability"].apply(lambda v: f"{v*100:.0f}%")
        _tr_display.columns = ["Township", "Probability", "Stores", "High Risk"]
        render_smart_table(_tr_display, key="township_table", title="Township Risk", max_height=500)
        render_caption("township_table", captions)

elif tab == "Store Predictions":
    st.markdown("### All Store Predictions — Tomorrow")
    display = pred[["name", "sector", "township", "blackout_probability", "risk_level",
                     "expected_duration_hours", "likely_window"]].copy()
    display["blackout_probability"] = display["blackout_probability"].apply(lambda v: f"{v*100:.0f}%")
    display["expected_duration_hours"] = display["expected_duration_hours"].apply(lambda v: f"{v:.1f}")
    display.columns = ["Store", "Sector", "Township", "Probability", "Risk Level", "Exp. Hours", "Window"]
    render_smart_table(display, key="pred_table", title="Store Predictions — Tomorrow",
                       severity_col="Risk Level", max_height=500)
    render_caption("pred_table", captions)

elif tab == "Patterns":
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Day-of-Week Pattern")
        ec = energy.copy()
        ec["dow"] = ec["date"].dt.day_name()
        dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        avg = ec.groupby("dow")["blackout_hours"].mean().reindex(dow_order)
        fig = go.Figure(go.Bar(x=dow_order, y=avg.values,
                               marker_color=[("#ef4444" if v > 5 else "#f97316" if v > 3 else "#22c55e") for v in avg.values],
                               text=[f"{v:.1f}h" for v in avg.values], textposition="outside"))
        fig.update_layout(height=350, margin=dict(l=40, r=20, t=20, b=40),
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
        render_caption("dow_chart", captions)

    with col2:
        st.markdown("### Last 30 Days Heatmap")
        recent = energy[energy["date"] >= energy["date"].max() - pd.Timedelta(days=30)]
        merged = recent.merge(stores[["store_id", "township"]], on="store_id")
        pivot = merged.groupby(["township", "date"])["blackout_hours"].mean().reset_index()
        pt = pivot.pivot(index="township", columns="date", values="blackout_hours")
        fig = go.Figure(data=go.Heatmap(z=pt.values, x=pt.columns, y=pt.index,
                                         colorscale="YlOrRd", colorbar=dict(title="Hrs")))
        fig.update_layout(height=350, margin=dict(l=130, r=20, t=10, b=40))
        st.plotly_chart(fig, use_container_width=True)
        render_caption("heatmap_chart", captions)

# AI Insights merged into Page Intelligence at top


# Generate element captions for next visit
from utils.element_captions import generate_pending_captions
generate_pending_captions()

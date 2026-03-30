"""
Page 1: Sector Dashboard — shadcn/ui
Drill-down: Sector → Channel → Store
"""

import streamlit as st
import streamlit_shadcn_ui as ui
import plotly.graph_objects as go
import pandas as pd
from config.settings import SECTORS, OPERATING_MODES
from utils.data_loader import load_stores, load_daily_energy, load_store_sales
from utils.charts import COLORS
from utils.element_captions import get_page_captions, render_caption
from utils.page_intelligence import render_page_intelligence
from utils.rule_insights import render_insight_cards, generate_sector_insights, generate_chart_insight

st.set_page_config(page_title="Sector Dashboard", page_icon="🏪", layout="wide")

st.markdown("""
<div style="background:linear-gradient(135deg,#1e3a5f,#2563eb);color:white;padding:20px 28px;border-radius:12px;margin-bottom:20px">
    <h2 style="margin:0;color:white">Sector Dashboard</h2>
    <p style="margin:4px 0 0;opacity:0.85">Operational view: Sector → Channel → Store</p>
</div>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_data():
    return load_stores(), load_daily_energy(), load_store_sales()

stores, energy, sales = load_data()

# ── Filters via shadcn tabs + select ──
sector = ui.tabs(options=list(SECTORS.keys()), default_value="Retail", key="sector_tabs")
channels = SECTORS[sector]["channels"]

col1, col2 = st.columns([1, 3])
with col1:
    channel = ui.select(label="Channel", options=["All"] + channels, key="channel_select")

# Filter
filtered_stores = stores[stores["sector"] == sector]
if channel and channel != "All":
    filtered_stores = filtered_stores[filtered_stores["channel"] == channel]
store_ids = filtered_stores["store_id"].tolist()

last_30 = energy["date"].max() - pd.Timedelta(days=30)
filtered_energy = energy[(energy["store_id"].isin(store_ids)) & (energy["date"] >= last_30)]
filtered_sales = sales[(sales["store_id"].isin(store_ids)) & (sales["date"] >= last_30)]

# ── Compute KPIs ──
total_energy_cost = filtered_energy["total_energy_cost_mmk"].sum()
total_sales_val = filtered_sales["sales_mmk"].sum()
energy_pct = total_energy_cost / max(total_sales_val, 1) * 100
avg_bo = filtered_energy["blackout_hours"].mean()
solar_n = filtered_stores["has_solar"].sum()

# ── AI Page Intelligence (top of page, before cards) ──
render_page_intelligence(f"sector_{sector}", f"IMPORTANT: This is the {sector} sector ONLY (not the whole network). Sector: {sector}, Channel: {channel or 'All'}, Stores in this sector: {len(filtered_stores)}, Energy cost (this sector): {total_energy_cost/1e6:,.1f}M MMK, Avg blackout (this sector): {avg_bo:.1f} hrs/day, Solar sites (this sector): {int(solar_n)}/{len(filtered_stores)}. Analyze ONLY {sector} sector data.")

# ── AI Captions ──
captions = get_page_captions(f"sector_{sector}", [
    {"id": "stores_count", "type": "metric", "title": "Stores", "value": f"{len(filtered_stores)} in {sector}"},
    {"id": "energy_cost", "type": "metric", "title": "Energy Cost", "value": f"{total_energy_cost/1e6:,.1f}M MMK (last 30 days)"},
    {"id": "energy_pct", "type": "metric", "title": "Energy % of Sales", "value": f"{energy_pct:.1f}%"},
    {"id": "avg_blackout", "type": "metric", "title": "Avg Blackout", "value": f"{avg_bo:.1f} hrs per store/day"},
    {"id": "solar_sites", "type": "metric", "title": "Solar Sites", "value": f"{solar_n}/{len(filtered_stores)} equipped"},
    {"id": "store_table", "type": "table", "title": "Store Performance Table", "value": f"{len(filtered_stores)} stores with sales, energy cost, energy %, blackout hours, status"},
    {"id": "cost_vs_sales", "type": "chart", "title": "Energy Cost vs Sales", "value": "Top 10 stores grouped bar chart comparing sales and energy cost"},
    {"id": "energy_trend", "type": "chart", "title": "Daily Energy Trend", "value": "30-day diesel and grid cost area chart"},
    {"id": "blackout_heatmap", "type": "chart", "title": "Blackout Heatmap", "value": "Store x date heatmap of blackout hours"},
], data_summary=f"Sector: {sector}, Channel: {channel or 'All'}. {len(filtered_stores)} stores, energy cost {total_energy_cost/1e6:,.1f}M MMK, {energy_pct:.1f}% of sales, avg blackout {avg_bo:.1f} hrs/day, {solar_n} solar sites.")

# ── KPI Cards ──
cols = st.columns(4)
with cols[0]:
    ui.metric_card(title="Stores", content=str(len(filtered_stores)),
                   description=f"{sector} sector", key="s_stores")
    render_caption("stores_count", captions)
with cols[1]:
    ui.metric_card(title="Energy Cost", content=f"{total_energy_cost/1e6:,.1f}M",
                   description="last 30 days", key="s_energy")
    render_caption("energy_cost", captions)
with cols[2]:
    ui.metric_card(title="Energy % of Sales", content=f"{energy_pct:.1f}%",
                   description="cost ratio", key="s_pct")
    render_caption("energy_pct", captions)
with cols[3]:
    ui.metric_card(title="Avg Blackout", content=f"{avg_bo:.1f} hrs",
                   description="per store/day", key="s_blackout")
    render_caption("avg_blackout", captions)
cols2 = st.columns(4)
with cols2[0]:
    ui.metric_card(title="Solar Sites", content=f"{solar_n}/{len(filtered_stores)}",
                   description="equipped", key="s_solar")
    render_caption("solar_sites", captions)

st.markdown("")

# ── Key Insights (rule-based, always visible) ──
st.markdown("### Key Insights")
_sector_insights = generate_sector_insights(pd.DataFrame(), filtered_energy, sector, energy_pct, avg_bo)
render_insight_cards(_sector_insights)

st.markdown("")

# ── Store Performance Table ──
store_agg = filtered_energy.groupby("store_id").agg(
    total_energy_cost=("total_energy_cost_mmk", "sum"),
    total_diesel_cost=("diesel_cost_mmk", "sum"),
    avg_blackout=("blackout_hours", "mean"),
    total_diesel_liters=("diesel_consumed_liters", "sum"),
).reset_index()

sales_agg = filtered_sales.groupby("store_id").agg(
    total_sales=("sales_mmk", "sum"),
    total_margin=("gross_margin_mmk", "sum"),
).reset_index()

store_perf = store_agg.merge(sales_agg, on="store_id", how="left")
store_perf = store_perf.merge(filtered_stores[["store_id", "name", "channel", "township", "has_solar"]], on="store_id", how="left")
store_perf["energy_pct"] = (store_perf["total_energy_cost"] / store_perf["total_sales"].clip(lower=1) * 100).round(1)
store_perf["status"] = store_perf["energy_pct"].apply(
    lambda x: "Healthy" if x < 5 else ("Watch" if x < 10 else "At Risk")
)
store_perf = store_perf.sort_values("energy_pct", ascending=False)

# Format for display
display_df = store_perf[["name", "channel", "township", "total_sales", "total_energy_cost", "energy_pct", "avg_blackout", "status"]].copy()
display_df["total_sales"] = display_df["total_sales"].apply(lambda x: f"{x/1e6:,.1f}M")
display_df["total_energy_cost"] = display_df["total_energy_cost"].apply(lambda x: f"{x/1e3:,.0f}K")
display_df["avg_blackout"] = display_df["avg_blackout"].apply(lambda x: f"{x:.1f}h")
display_df["energy_pct"] = display_df["energy_pct"].apply(lambda x: f"{x:.1f}%")
display_df.columns = ["Store", "Channel", "Township", "Sales", "Energy Cost", "Energy %", "Blackout", "Status"]

from utils.smart_table import render_smart_table
render_smart_table(display_df, key="store_perf_table", title="Store Performance",
                   severity_col="Status", max_height=450)
render_caption("store_table", captions)

st.markdown("")

# ── Charts ──
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Energy Cost vs Sales")
    top10 = store_perf.sort_values("total_sales", ascending=False).head(10)
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Sales", x=top10["name"], y=top10["total_sales"],
                         marker_color="#3b82f6", opacity=0.85))
    fig.add_trace(go.Bar(name="Energy Cost", x=top10["name"], y=top10["total_energy_cost"],
                         marker_color="#f97316", opacity=0.85))
    fig.update_layout(barmode="group", height=380, margin=dict(l=40, r=20, t=20, b=80),
                      xaxis_tickangle=-45, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", y=1.05))
    st.plotly_chart(fig, use_container_width=True)
    render_caption("cost_vs_sales", captions)
    # Chart insight
    if len(top10) > 0:
        _worst = top10.sort_values("energy_pct", ascending=False).iloc[0]
        _chart_ins = generate_chart_insight("energy_vs_sales", {
            "top_store_name": _worst.get("name", ""), "top_energy_pct": _worst.get("energy_pct", 0)})
        render_insight_cards(_chart_ins)

with col2:
    st.markdown("### Daily Energy Trend")
    daily = filtered_energy.groupby("date").agg(
        diesel=("diesel_cost_mmk", "sum"), grid=("grid_cost_mmk", "sum")).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily["date"], y=daily["diesel"], name="Diesel",
                             fill="tozeroy", line=dict(color="#f97316")))
    fig.add_trace(go.Scatter(x=daily["date"], y=daily["grid"], name="Grid",
                             fill="tozeroy", line=dict(color="#3b82f6")))
    fig.update_layout(height=380, margin=dict(l=40, r=20, t=20, b=40),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)
    render_caption("energy_trend", captions)
    # Chart insight — trend direction
    if len(daily) >= 14:
        _last7 = daily.tail(7)["diesel"].mean()
        _prev7 = daily.iloc[-14:-7]["diesel"].mean()
        _dir = "increasing" if _last7 > _prev7 * 1.05 else ("decreasing" if _last7 < _prev7 * 0.95 else "stable")
        _trend_ins = generate_chart_insight("energy_trend", {"trend_direction": _dir})
        render_insight_cards(_trend_ins)

# ── Blackout Heatmap ──
st.markdown("### Blackout Heatmap")
bp = filtered_energy.merge(filtered_stores[["store_id", "name"]], on="store_id")
pivot = bp.pivot_table(index="name", columns="date", values="blackout_hours", aggfunc="mean")
fig = go.Figure(data=go.Heatmap(z=pivot.values, x=pivot.columns, y=pivot.index,
                                 colorscale="YlOrRd", colorbar=dict(title="Hours")))
fig.update_layout(height=max(300, len(pivot) * 22), margin=dict(l=160, r=20, t=10, b=40))
st.plotly_chart(fig, use_container_width=True)
render_caption("blackout_heatmap", captions)
# Chart insight — worst blackout store
if len(pivot) > 0:
    _worst_bo_store = pivot.mean(axis=1).idxmax()
    _worst_bo_hrs = pivot.mean(axis=1).max()
    _bo_ins = generate_chart_insight("blackout_heatmap", {"worst_store": _worst_bo_store, "worst_avg_hours": _worst_bo_hrs})
    render_insight_cards(_bo_ins)

# AI Insights merged into Page Intelligence at top


# Generate element captions for next visit
from utils.element_captions import generate_pending_captions
generate_pending_captions()

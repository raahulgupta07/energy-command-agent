"""
Page 2: Holdings Control Tower — shadcn/ui
Group-level KPIs, sector comparison, ERI ranking.
"""

import streamlit as st
import streamlit_shadcn_ui as ui
import plotly.graph_objects as go
import pandas as pd
from config.settings import SECTORS, CURRENCY
from utils.data_loader import load_stores, load_daily_energy, load_store_sales, load_diesel_inventory
from utils.charts import COLORS
from models.holdings_aggregator import HoldingsAggregator
from utils.llm_client import is_llm_available
from utils.element_captions import get_page_captions, render_caption
from utils.page_intelligence import render_page_intelligence
from utils.smart_table import render_smart_table

st.set_page_config(page_title="Holdings Control Tower", page_icon="🏛️", layout="wide")

st.markdown("""
<div style="background:linear-gradient(135deg,#0f172a,#4a148c);color:white;padding:20px 28px;border-radius:12px;margin-bottom:20px">
    <h2 style="margin:0;color:white">Holdings Control Tower</h2>
    <p style="margin:4px 0 0;opacity:0.85">Group Energy Command Center — Strategic View</p>
</div>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_data():
    stores = load_stores()
    energy = load_daily_energy()
    sales = load_store_sales()
    inventory = load_diesel_inventory()
    agg = HoldingsAggregator()
    group = agg.compute_group_kpis(stores, energy, sales, inventory)
    sector = agg.compute_sector_kpis(stores, energy, sales)
    eri = agg.get_eri_ranking(energy, sales, stores)
    return stores, energy, sales, inventory, group, sector, eri

stores, energy, sales, inventory, gk, sk, eri = load_data()

render_page_intelligence("holdings", f"Total stores: {gk['total_stores']}, Energy cost: {gk['total_energy_cost_mmk']/1e9:,.2f}B MMK ({gk['energy_cost_pct_of_sales']:.1f}% of sales), Avg ERI: {gk['avg_eri_pct']:.0f}%, Diesel dependency: {gk['avg_diesel_dependency_pct']:.0f}%, Solar sites: {gk['solar_sites']}, Stores below 2-day diesel: {gk['stores_below_2_days']}.")

# ── AI Captions ──
captions = get_page_captions("holdings", [
    {"id": "total_stores", "type": "metric", "title": "Total Stores", "value": str(gk["total_stores"])},
    {"id": "energy_cost", "type": "metric", "title": "Energy Cost", "value": f"{gk['total_energy_cost_mmk']/1e9:,.2f}B ({gk['energy_cost_pct_of_sales']:.1f}% of sales)"},
    {"id": "ebitda_impact", "type": "metric", "title": "EBITDA Impact", "value": f"{gk['total_ebitda_impact_mmk']/1e9:,.2f}B"},
    {"id": "avg_eri", "type": "metric", "title": "Avg ERI", "value": f"{gk['avg_eri_pct']:.0f}%"},
    {"id": "diesel_dep", "type": "metric", "title": "Diesel Dependency", "value": f"{gk['avg_diesel_dependency_pct']:.0f}%"},
    {"id": "solar_kwh", "type": "metric", "title": "Solar kWh", "value": f"{gk['total_solar_kwh']:,.0f} across {gk['solar_sites']} sites"},
    {"id": "sector_retail", "type": "metric", "title": "Sector: Retail", "value": "sector energy ratio card"},
    {"id": "sector_fnb", "type": "metric", "title": "Sector: F&B", "value": "sector energy ratio card"},
    {"id": "sector_distribution", "type": "metric", "title": "Sector: Distribution", "value": "sector energy ratio card"},
    {"id": "sector_property", "type": "metric", "title": "Sector: Property", "value": "sector energy ratio card"},
    {"id": "sector_bar", "type": "chart", "title": "Sector Energy Cost Bar", "value": f"4 sectors compared by energy cost in MMK"},
    {"id": "sector_table", "type": "table", "title": "Sector Comparison Table", "value": f"{len(sk)} sectors with stores, sales, energy cost, diesel %, solar"},
    {"id": "eri_bar", "type": "chart", "title": "ERI Top 20 Ranking", "value": f"Top 20 stores by Energy Resilience Index, best={eri.iloc[0]['eri_pct']:.0f}%"},
    {"id": "eri_best", "type": "metric", "title": "Best Store", "value": f"{eri.iloc[0]['name']} at {eri.iloc[0]['eri_pct']:.0f}%"},
    {"id": "eri_worst", "type": "metric", "title": "Worst Store", "value": f"{eri.iloc[-1]['name']} at {eri.iloc[-1]['eri_pct']:.0f}%"},
    {"id": "eri_solar", "type": "metric", "title": "Solar Advantage", "value": f"+{eri[eri['has_solar']==True]['eri_pct'].mean() - eri[eri['has_solar']==False]['eri_pct'].mean():.0f}% ERI gap"},
    {"id": "energy_mix_pie", "type": "chart", "title": "Energy Source Mix Pie", "value": "Diesel vs Grid vs Solar cost breakdown"},
    {"id": "diesel_stock", "type": "metric", "title": "Total Diesel Stock", "value": f"{gk['total_diesel_stock_liters']:,.0f} L, {gk['avg_days_coverage']:.1f} days"},
    {"id": "below_2_days", "type": "metric", "title": "Stores Below 2 Days", "value": str(gk["stores_below_2_days"])},
    {"id": "total_bo", "type": "metric", "title": "Total Blackout Hours", "value": f"{gk['total_blackout_hours']:,.0f}, avg {gk['avg_daily_blackout_hours']:.1f} hrs/day"},
], data_summary=f"Holdings group: {gk['total_stores']} stores, energy cost {gk['total_energy_cost_mmk']/1e9:,.2f}B MMK ({gk['energy_cost_pct_of_sales']:.1f}% of sales), ERI {gk['avg_eri_pct']:.0f}%, diesel dependency {gk['avg_diesel_dependency_pct']:.0f}%, {gk['solar_sites']} solar sites, {gk['stores_below_2_days']} stores below 2-day diesel coverage.")

# ── Top KPIs ──
cols = st.columns(4)
with cols[0]:
    ui.metric_card(title="Total Stores", content=str(gk["total_stores"]), description="4 sectors", key="h_stores")
    render_caption("total_stores", captions)
with cols[1]:
    ui.metric_card(title="Energy Cost", content=f"{gk['total_energy_cost_mmk']/1e9:,.2f}B",
                   description=f"{gk['energy_cost_pct_of_sales']:.1f}% of sales", key="h_cost")
    render_caption("energy_cost", captions)
with cols[2]:
    ui.metric_card(title="EBITDA Impact", content=f"{gk['total_ebitda_impact_mmk']/1e9:,.2f}B",
                   description="from disruption", key="h_ebitda")
    render_caption("ebitda_impact", captions)
with cols[3]:
    ui.metric_card(title="Avg ERI", content=f"{gk['avg_eri_pct']:.0f}%",
                   description="resilience index", key="h_eri")
    render_caption("avg_eri", captions)
cols2 = st.columns(4)
with cols2[0]:
    ui.metric_card(title="Diesel Dependency", content=f"{gk['avg_diesel_dependency_pct']:.0f}%",
                   description="of energy cost", key="h_dep")
    render_caption("diesel_dep", captions)
with cols2[1]:
    ui.metric_card(title="Solar kWh", content=f"{gk['total_solar_kwh']:,.0f}",
                   description=f"{gk['solar_sites']} sites", key="h_solar")
    render_caption("solar_kwh", captions)

st.markdown("")

# ── Sector Comparison ──
st.markdown("### Sector Comparison")

tab = ui.tabs(options=["Overview", "ERI Ranking", "Energy Mix"], default_value="Overview", key="holdings_tabs")

if tab == "Overview":
    _sector_caption_ids = {"Retail": "sector_retail", "F&B": "sector_fnb", "Distribution": "sector_distribution", "Property": "sector_property"}
    cols = st.columns(4)
    for i, (_, row) in enumerate(sk.iterrows()):
        with cols[i]:
            ui.metric_card(
                title=row["sector"],
                content=f"{row['energy_cost_pct']:.1f}% energy ratio",
                description=f"{row['num_stores']} stores | {row['solar_sites']} solar",
                key=f"sector_{row['sector']}"
            )
            render_caption(_sector_caption_ids.get(row["sector"], f"sector_{i}"), captions)

    st.markdown("")

    # Sector bar chart
    fig = go.Figure()
    for _, row in sk.iterrows():
        fig.add_trace(go.Bar(name=row["sector"], x=[row["sector"]], y=[row["total_energy_cost"]],
                             marker_color=row["color"], text=f"{row['energy_cost_pct']:.1f}%", textposition="outside"))
    fig.update_layout(showlegend=False, height=380, margin=dict(l=40, r=20, t=30, b=40),
                      yaxis_title=f"Energy Cost ({CURRENCY})",
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)
    render_caption("sector_bar", captions)

    # Sector table
    _sk_display = sk[["sector", "num_stores", "total_sales", "total_energy_cost",
                       "energy_cost_pct", "diesel_dependency_pct", "solar_sites"]].copy()
    _sk_display["total_sales"] = _sk_display["total_sales"].apply(
        lambda v: f"{v/1e6:,.1f}M" if abs(v) >= 1e6 else (f"{v/1e3:,.1f}K" if abs(v) >= 1e3 else f"{v:,.0f}"))
    _sk_display["total_energy_cost"] = _sk_display["total_energy_cost"].apply(
        lambda v: f"{v/1e6:,.1f}M" if abs(v) >= 1e6 else (f"{v/1e3:,.1f}K" if abs(v) >= 1e3 else f"{v:,.0f}"))
    _sk_display["energy_cost_pct"] = _sk_display["energy_cost_pct"].apply(lambda v: f"{v:.1f}%")
    _sk_display["diesel_dependency_pct"] = _sk_display["diesel_dependency_pct"].apply(lambda v: f"{v:.1f}%")
    _sk_display.columns = ["Sector", "Stores", "Sales", "Energy Cost", "Energy %", "Diesel %", "Solar"]
    render_smart_table(_sk_display, key="sector_table", title="Sector KPIs", max_height=250)
    render_caption("sector_table", captions)

elif tab == "ERI Ranking":
    col1, col2 = st.columns([3, 1])

    with col1:
        # Top 20
        top = eri.head(20)
        sector_colors = {s: info["color"] for s, info in SECTORS.items()}
        colors = [sector_colors.get(s, "#999") for s in top["sector"]]

        fig = go.Figure(go.Bar(x=top["eri_pct"], y=top["name"], orientation="h",
                               marker_color=colors,
                               text=top["eri_pct"].apply(lambda x: f"{x:.0f}%"), textposition="outside"))
        fig.update_layout(height=550, margin=dict(l=200, r=50, t=20, b=40),
                          xaxis_title="ERI %", yaxis=dict(autorange="reversed"),
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
        render_caption("eri_bar", captions)

    with col2:
        ui.metric_card(title="Best Store", content=eri.iloc[0]["name"],
                       description=f"ERI: {eri.iloc[0]['eri_pct']:.0f}%", key="eri_best")
        render_caption("eri_best", captions)
        ui.metric_card(title="Worst Store", content=eri.iloc[-1]["name"],
                       description=f"ERI: {eri.iloc[-1]['eri_pct']:.0f}%", key="eri_worst")
        render_caption("eri_worst", captions)

        solar_eri = eri[eri["has_solar"] == True]["eri_pct"].mean()
        non_solar_eri = eri[eri["has_solar"] == False]["eri_pct"].mean()
        ui.metric_card(title="Solar Advantage", content=f"+{solar_eri - non_solar_eri:.0f}%",
                       description=f"Solar: {solar_eri:.0f}% vs Non: {non_solar_eri:.0f}%", key="eri_solar")
        render_caption("eri_solar", captions)

    # Bottom 10
    st.markdown("### Most Vulnerable Stores")
    bottom = eri.tail(10).sort_values("eri_pct")
    for _, row in bottom.iterrows():
        c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
        c1.write(f"**{row['name']}**")
        c2.write(row["sector"])
        with c3:
            ui.badges(badge_list=[(f"{row['eri_pct']:.0f}%", "destructive")], key=f"eri_b_{row['store_id']}")
        c4.write("Solar" if row.get("has_solar") else "No Solar")

elif tab == "Energy Mix":
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Energy Source Mix")
        total_diesel = energy["diesel_cost_mmk"].sum()
        total_grid = energy["grid_cost_mmk"].sum()
        total_solar = energy["solar_kwh"].sum() * 50

        fig = go.Figure(go.Pie(
            labels=["Diesel", "Grid", "Solar"],
            values=[total_diesel, total_grid, total_solar],
            marker=dict(colors=["#f97316", "#3b82f6", "#eab308"]),
            hole=0.45, textinfo="label+percent"))
        fig.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
        render_caption("energy_mix_pie", captions)

    with col2:
        st.markdown("### Inventory & Blackout")
        ui.metric_card(title="Total Diesel Stock", content=f"{gk['total_diesel_stock_liters']:,.0f} L",
                       description=f"Avg {gk['avg_days_coverage']:.1f} days coverage", key="h_stock")
        render_caption("diesel_stock", captions)
        ui.metric_card(title="Stores Below 2 Days", content=str(gk["stores_below_2_days"]),
                       description="need immediate attention", key="h_below2")
        render_caption("below_2_days", captions)
        ui.metric_card(title="Total Blackout Hours", content=f"{gk['total_blackout_hours']:,.0f}",
                       description=f"Avg {gk['avg_daily_blackout_hours']:.1f} hrs/day", key="h_bo")
        render_caption("total_bo", captions)

# AI Insights merged into Page Intelligence at top


# Generate element captions for next visit
from utils.element_captions import generate_pending_captions
generate_pending_captions()

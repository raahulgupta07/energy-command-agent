"""
Page 2: Holdings Control Tower — shadcn/ui
Group-level KPIs, sector comparison, ERI ranking.
"""

import streamlit as st
import streamlit_shadcn_ui as ui
import plotly.graph_objects as go
import pandas as pd
from config.settings import SECTORS, CURRENCY
from utils.data_loader import load_stores, load_daily_energy, load_store_sales, load_diesel_inventory, load_temperature_logs
from utils.charts import COLORS
from models.holdings_aggregator import HoldingsAggregator
from utils.llm_client import is_llm_available
from utils.element_captions import get_page_captions, render_caption
from utils.page_intelligence import render_page_intelligence
from utils.smart_table import render_smart_table
from utils.database import get_override_stats, get_decision_audit, get_compliance_summary, get_quality_report

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

# New KPI row: Adoption, Compliance, Cold Chain, Generator EBITDA
cols3 = st.columns(4)
with cols3[0]:
    _adoption = get_override_stats()
    ui.metric_card(title="AI Adoption Rate", content=f"{_adoption['adoption_rate_pct']:.0f}%",
                   description=f"{_adoption['accepted']}/{_adoption['total']} accepted (target >80%)", key="h_adoption")
with cols3[1]:
    _compliance = get_compliance_summary()
    ui.metric_card(title="Data Compliance", content=f"{_compliance['compliance_pct']:.0f}%",
                   description=f"{_compliance['total_submissions']} submissions (target >95%)", key="h_compliance")
with cols3[2]:
    try:
        from utils.kpi_calculator import cold_chain_uptime_pct
        _temp = load_temperature_logs()
        _uptime = cold_chain_uptime_pct(_temp)
        _avg_uptime = _uptime["uptime_pct"].mean() if len(_uptime) > 0 else 0
        ui.metric_card(title="Cold Chain Uptime", content=f"{_avg_uptime:.1f}%",
                       description=f"{len(_uptime)} cold chain stores (target >99.5%)", key="h_coldchain")
    except Exception:
        ui.metric_card(title="Cold Chain Uptime", content="N/A", description="No temperature data", key="h_coldchain")
with cols3[3]:
    try:
        from utils.kpi_calculator import generator_ebitda_contribution
        _gen_ebitda = generator_ebitda_contribution(energy, sales, stores)
        _loss_making = (_gen_ebitda["status"] == "Loss-making").sum()
        ui.metric_card(title="Gen. Loss-Making", content=str(_loss_making),
                       description=f"of {len(_gen_ebitda)} stores (target: 0)", key="h_gen_loss")
    except Exception:
        ui.metric_card(title="Gen. Loss-Making", content="N/A", description="calculating...", key="h_gen_loss")

st.markdown("")

# ── Email Report + Tabs ──
ec1, ec2, ec3 = st.columns([6, 2, 2])
with ec2:
    if st.button("📧 Email Report", key="email_top", use_container_width=True):
        from utils.email_alerts import is_email_enabled, send_email
        from utils.report_generator import generate_weekly_ebitda_report
        if is_email_enabled():
            from config.settings import EMAIL_CONFIG
            report = generate_weekly_ebitda_report(gk, sk)
            recipients = EMAIL_CONFIG["recipients"].get("holdings_gecc", []) + EMAIL_CONFIG["recipients"].get("cfo", [])
            if recipients:
                send_email(recipients, report["subject"], report["html"])
                st.success(f"Sent to {len(recipients)} recipients")
            else:
                st.warning("No recipients in EMAIL_CONFIG")
        else:
            st.warning("Email not configured — set EIS_SMTP_USER in .env")
with ec3:
    from utils.template_generator import generate_template as _gt
    st.download_button("📋 Data Template", data=_gt(), file_name="EIS_Template.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml",
                       use_container_width=True, key="tpl_holdings")

tab = ui.tabs(options=["Overview", "ERI Ranking", "Energy Mix", "AI Adoption", "Data Quality"],
              default_value="Overview", key="holdings_tabs")

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

elif tab == "AI Adoption":
    st.markdown("### AI Recommendation Adoption Tracking")
    st.markdown("""
    <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:14px 18px;margin-bottom:16px">
        Tracks whether AI COMMANDER recommendations were followed by site managers. Target: <strong>>80% adoption rate</strong>.
    </div>
    """, unsafe_allow_html=True)

    adoption = get_override_stats()
    ac1, ac2, ac3, ac4 = st.columns(4)
    with ac1:
        ui.metric_card(title="Adoption Rate", content=f"{adoption['adoption_rate_pct']:.0f}%",
                       description="target >80%", key="adopt_rate")
    with ac2:
        ui.metric_card(title="Total Decisions", content=str(adoption["total"]),
                       description="tracked", key="adopt_total")
    with ac3:
        ui.metric_card(title="Accepted", content=str(adoption["accepted"]),
                       description="AI followed", key="adopt_accepted")
    with ac4:
        ui.metric_card(title="Overridden", content=str(adoption["overridden"]),
                       description="manager changed", key="adopt_overridden")

    # Recent overrides
    st.markdown("### Recent Override Decisions")
    overrides = get_decision_audit(limit=30)
    if overrides:
        override_df = pd.DataFrame(overrides)
        override_only = override_df[override_df["was_overridden"] == 1]
        if len(override_only) > 0:
            display = override_only[["store_name", "date", "ai_recommended_mode",
                                      "final_mode", "decided_by", "override_reason", "sector"]].copy()
            display.columns = ["Store", "Date", "AI Said", "Manager Changed To", "Decided By", "Reason", "Sector"]
            render_smart_table(display, key="overrides_table", title="Override Log", max_height=300)
        else:
            st.success("No overrides yet — 100% AI adoption!")

        # All decisions table
        with st.expander("All Decisions (including confirmations)"):
            all_display = override_df[["store_name", "date", "ai_recommended_mode",
                                        "final_mode", "was_overridden", "decided_by", "created_at"]].copy()
            all_display["was_overridden"] = all_display["was_overridden"].map({0: "Confirmed", 1: "OVERRIDE"})
            all_display.columns = ["Store", "Date", "AI Mode", "Final Mode", "Status", "By", "Timestamp"]
            render_smart_table(all_display, key="all_decisions_table", title="All Decisions",
                               severity_col="Status", max_height=300)
    else:
        st.caption("No decisions tracked yet. Use the Override/Confirm tab on Store Decisions page.")

    # Email report button
    st.markdown("---")
    if st.button("📧 Email Holdings Report", key="email_holdings", use_container_width=False):
        from utils.email_alerts import is_email_enabled, send_email
        from utils.report_generator import generate_weekly_ebitda_report
        if is_email_enabled():
            from config.settings import EMAIL_CONFIG
            report = generate_weekly_ebitda_report(gk, sk, summary=None)
            recipients = EMAIL_CONFIG["recipients"].get("holdings_gecc", []) + EMAIL_CONFIG["recipients"].get("cfo", [])
            if recipients:
                send_email(recipients, report["subject"], report["html"])
                st.success(f"Report emailed to {len(recipients)} recipients")
            else:
                st.warning("No recipients configured in EMAIL_CONFIG")
        else:
            st.warning("Email not configured. Set EIS_SMTP_USER and EIS_SMTP_PASSWORD in .env")

elif tab == "Data Quality":
    st.markdown("### Data Submission Compliance")
    st.markdown("""
    <div style="background:#fefce8;border:1px solid #fde68a;border-radius:10px;padding:14px 18px;margin-bottom:16px">
        Tracks daily data submissions from all sites. Target: <strong>>95% on-time compliance</strong>.
        Sites below 90% are escalated to Sector leads.
    </div>
    """, unsafe_allow_html=True)

    compliance = get_compliance_summary()
    dc1, dc2, dc3, dc4 = st.columns(4)
    with dc1:
        ui.metric_card(title="Compliance", content=f"{compliance['compliance_pct']:.0f}%",
                       description="target >95%", key="dq_compliance")
    with dc2:
        ui.metric_card(title="Total Submissions", content=str(compliance["total_submissions"]),
                       description="recorded", key="dq_total")
    with dc3:
        ui.metric_card(title="Late Submissions", content=str(compliance["late_count"]),
                       description="after 8 PM deadline", key="dq_late")
    with dc4:
        ui.metric_card(title="Stores Below 90%", content=str(compliance["stores_below_90"]),
                       description="need escalation", key="dq_below90")

    # Quality log
    st.markdown("### Recent Quality Records")
    quality_log = get_quality_report(limit=50)
    if quality_log:
        qdf = pd.DataFrame(quality_log)[["store_name", "date", "completeness_pct",
                                          "is_late", "submitted_by", "created_at"]].copy()
        qdf["is_late"] = qdf["is_late"].map({0: "ON TIME", 1: "LATE"})
        qdf["completeness_pct"] = qdf["completeness_pct"].apply(lambda v: f"{v:.0f}%")
        qdf.columns = ["Store", "Date", "Completeness", "Status", "Submitted By", "Recorded"]
        render_smart_table(qdf, key="quality_table", title="Submission Log",
                           severity_col="Status", max_height=300)
    else:
        st.caption("No quality records yet. Records are created when data is validated on upload or via scheduler.")

    # Missing stores check
    with st.expander("Check Missing Submissions for Today"):
        from utils.data_quality import get_missing_stores
        missing = get_missing_stores(stores, energy)
        if missing:
            st.warning(f"**{len(missing)} stores** have not submitted today's data:")
            for m in missing[:20]:
                st.write(f"- {m}")
            if len(missing) > 20:
                st.write(f"...and {len(missing) - 20} more")
        else:
            st.success("All stores have submitted for the latest date in the dataset.")

# Generate element captions for next visit
from utils.element_captions import generate_pending_captions
generate_pending_captions()

"""
Page 8: Scenario Simulator — Advanced What-If Analysis
Templates, sensitivity, store drill-down, break-even, waterfall, timeline, radar.
"""

import streamlit as st
import streamlit_shadcn_ui as ui
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from utils.data_loader import load_stores, load_daily_energy, load_store_sales, load_diesel_inventory
from utils.element_captions import get_page_captions, render_caption
from utils.page_intelligence import render_page_intelligence
from models.holdings_aggregator import HoldingsAggregator
from config.settings import OPERATING_MODES
from utils.database import save_scenario, get_saved_scenarios, delete_scenario, log_activity

st.set_page_config(page_title="Scenario Simulator", page_icon="🔮", layout="wide")

st.markdown("""
<div style="background:linear-gradient(135deg,#312e81,#7c3aed);color:white;padding:20px 28px;border-radius:12px;margin-bottom:20px">
    <h2 style="margin:0;color:white">Scenario Simulator</h2>
    <p style="margin:4px 0 0;opacity:0.85">What-if analysis: templates, sensitivity, store drill-down, break-even, projections</p>
</div>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_data():
    stores = load_stores()
    energy = load_daily_energy()
    sales = load_store_sales()
    inv = load_diesel_inventory()
    agg = HoldingsAggregator()
    baseline = agg.compute_group_kpis(stores, energy, sales, inv)
    return stores, energy, sales, inv, baseline, agg

stores, energy, sales, inv, baseline, agg = load_data()
saved_list = get_saved_scenarios(limit=30)

# Session state handled by slider widget keys (sl_d, sl_b, sl_f, sl_s)

# ══════════════════════════════════════════════════════════════════════════════
# PRE-BUILT SCENARIO TEMPLATES
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("### Quick Scenario Templates")
TEMPLATES = {
    "Worst Case": {"icon": "💀", "diesel": 40, "blackout": 50, "fx": 25, "solar": 0,
                   "desc": "Diesel +40%, blackouts +50%, FX +25%"},
    "War Escalation": {"icon": "⚔️", "diesel": 30, "blackout": 30, "fx": 20, "solar": 0,
                       "desc": "Diesel +30%, blackouts +30%, FX +20%"},
    "Grid Recovery": {"icon": "🔌", "diesel": -10, "blackout": -30, "fx": 0, "solar": 5,
                      "desc": "Blackouts -30%, diesel -10%, +5 solar"},
    "Solar Push": {"icon": "☀️", "diesel": 0, "blackout": 0, "fx": 0, "solar": 15,
                   "desc": "Add 15 solar sites, no other changes"},
    "Moderate Stress": {"icon": "⚠️", "diesel": 15, "blackout": 15, "fx": 10, "solar": 0,
                        "desc": "Diesel +15%, blackouts +15%, FX +10%"},
    "Best Case": {"icon": "🌟", "diesel": -15, "blackout": -20, "fx": -5, "solar": 10,
                  "desc": "Diesel -15%, blackouts -20%, FX -5%, +10 solar"},
}

tcols = st.columns(6)
for idx, (name, cfg) in enumerate(TEMPLATES.items()):
    with tcols[idx]:
        if st.button(f"{cfg['icon']} {name}", key=f"tmpl_{name}", use_container_width=True):
            # Only set the widget keys (not both value + key)
            st.session_state["sl_d"] = cfg["diesel"]
            st.session_state["sl_b"] = cfg["blackout"]
            st.session_state["sl_f"] = cfg["fx"]
            st.session_state["sl_s"] = cfg["solar"]
            st.rerun()
        st.markdown(f"<div style='font-size:0.68rem;color:#94a3b8;text-align:center;margin-top:-8px'>{cfg['desc']}</div>", unsafe_allow_html=True)

st.markdown("")

# ══════════════════════════════════════════════════════════════════════════════
# LOAD SAVED SCENARIO
# ══════════════════════════════════════════════════════════════════════════════

if saved_list:
    load_col1, load_col2 = st.columns([3, 1])
    with load_col1:
        opts = ["— New scenario —"] + [f"{s['name']} (D:{s['diesel_price_change']:+.0f}% B:{s['blackout_hours_change']:+.0f}%)" for s in saved_list]
        selected = st.selectbox("Load saved", opts, key="load_sc", label_visibility="collapsed")
    with load_col2:
        if st.button("📂 Load", key="load_sc_btn", use_container_width=True):
            if selected != opts[0]:
                idx = opts.index(selected) - 1
                s = saved_list[idx]
                st.session_state["sl_d"] = int(s["diesel_price_change"])
                st.session_state["sl_b"] = int(s["blackout_hours_change"])
                st.session_state["sl_f"] = int(s["fx_change"])
                st.session_state["sl_s"] = int(s["solar_new_sites"])
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# SLIDERS + RUN BUTTON
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("### Adjust Parameters")

# Initialize slider keys if not set
if "sl_d" not in st.session_state:
    st.session_state["sl_d"] = 0
if "sl_b" not in st.session_state:
    st.session_state["sl_b"] = 0
if "sl_f" not in st.session_state:
    st.session_state["sl_f"] = 0
if "sl_s" not in st.session_state:
    st.session_state["sl_s"] = 0

c1, c2, c3, c4 = st.columns(4)
with c1:
    diesel_change = st.slider("Diesel Price %", -20, 50, step=5, key="sl_d")
with c2:
    blackout_change = st.slider("Blackout Hours %", -30, 50, step=5, key="sl_b")
with c3:
    fx_change = st.slider("FX Rate %", -10, 30, step=5, key="sl_f")
with c4:
    solar_new = st.slider("New Solar Sites", 0, 20, step=1, key="sl_s")

st.markdown("")
_, btn_col, _ = st.columns([1, 2, 1])
with btn_col:
    run_clicked = st.button("🚀 Run Scenario & Generate AI Analysis", type="primary", use_container_width=True, key="run_btn")

# ── Execute on Run ──
if run_clicked:
    sc = agg.simulate_scenario(stores, energy, sales, inv,
                                diesel_price_change_pct=diesel_change,
                                blackout_hours_change_pct=blackout_change,
                                fx_change_pct=fx_change, solar_new_sites=solar_new)
    st.session_state["scenario_result"] = sc
    st.session_state["scenario_params"] = {"diesel": diesel_change, "blackout": blackout_change, "fx": fx_change, "solar": solar_new}
    try:
        from utils.database import get_db
        with get_db() as conn:
            conn.execute("DELETE FROM page_intelligence_cache WHERE page_id LIKE 'scenario%'")
            conn.execute("DELETE FROM element_captions_cache WHERE page_id LIKE 'scenario%'")
    except Exception:
        pass

scenario = st.session_state.get("scenario_result")
sc_params = st.session_state.get("scenario_params")

if not scenario or not sc_params:
    st.markdown("""
    <div style="background:#f8fafc;border:2px dashed #cbd5e1;border-radius:12px;padding:30px;text-align:center;margin:12px 0 20px 0">
        <span style="font-size:2rem">🔮</span>
        <div style="color:#475569;font-size:1rem;margin-top:8px;font-weight:600">No scenario executed yet</div>
        <div style="color:#94a3b8;font-size:0.85rem;margin-top:4px">Pick a template or adjust sliders, then click <strong>Run Scenario</strong></div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

d, b, f, s = sc_params["diesel"], sc_params["blackout"], sc_params["fx"], sc_params["solar"]
sc_id = f"scenario_d{d}_b{b}_f{f}_s{s}"

# ── AI Page Intelligence ──
render_page_intelligence(sc_id,
    f"Scenario: Diesel {d:+d}%, Blackout {b:+d}%, FX {f:+d}%, Solar +{s}. "
    f"Energy cost change: {scenario['energy_cost_change_pct']:+.1f}%, EBITDA impact: {scenario['ebitda_impact_pct']:+.1f}%, Stores closed: {scenario['est_stores_closed']}.")

if (d != diesel_change or b != blackout_change or f != fx_change or s != solar_new):
    st.markdown(f"""<div style="background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:8px 14px;margin-bottom:12px;font-size:0.82rem;color:#92400e">
        Showing: Diesel {d:+d}%, Blackout {b:+d}%, FX {f:+d}%, Solar +{s}. <strong>Click Run to update.</strong>
    </div>""", unsafe_allow_html=True)

captions = get_page_captions(sc_id, [
    {"id": "sc_energy", "type": "metric", "title": "Energy Cost", "value": f"{scenario['energy_cost_change_pct']:+.1f}%"},
    {"id": "sc_ebitda", "type": "metric", "title": "EBITDA Impact", "value": f"{scenario['ebitda_impact_pct']:+.1f}%"},
    {"id": "sc_waterfall", "type": "chart", "title": "Cost Waterfall", "value": "Breakdown of cost changes"},
    {"id": "sc_sensitivity", "type": "chart", "title": "Sensitivity Analysis", "value": "Which parameter matters most"},
], data_summary=f"D{d:+d}% B{b:+d}% F{f:+d}% S+{s}. EBITDA {scenario['ebitda_impact_pct']:+.1f}%")

# ── Impact KPIs ──
cols = st.columns(4)
with cols[0]:
    ui.metric_card(title="Energy Cost", content=f"{scenario['scenario_energy_cost']/1e9:,.2f}B",
                   description=f"{scenario['energy_cost_change_pct']:+.1f}% vs current", key="sc_cost")
    render_caption("sc_energy", captions)
with cols[1]:
    ui.metric_card(title="Sales Impact", content=f"{scenario['scenario_sales']/1e9:,.2f}B",
                   description=f"{scenario['sales_change_pct']:+.1f}%", key="sc_sales_c")
    render_caption("sc_ebitda", captions)
with cols[2]:
    ui.metric_card(title="EBITDA Impact", content=f"{scenario['ebitda_impact_pct']:+.1f}%",
                   description="profit change", key="sc_ebitda_c")
with cols[3]:
    if s > 0:
        ui.metric_card(title="Solar Savings", content=f"{scenario['solar_saving_mmk']/1e6:,.1f}M",
                       description=f"+{s} sites", key="sc_sol_c")
    else:
        ui.metric_card(title="Stores Closed", content=str(scenario["est_stores_closed"]),
                       description=f"of {baseline['total_stores']}", key="sc_close_c")

# ── Save ──
st.markdown("")
sv1, sv2, sv3 = st.columns([2, 1, 1])
with sv1:
    sc_name = st.text_input("Name", placeholder="e.g., Worst case Q2", key="sc_name", label_visibility="collapsed")
with sv2:
    if st.button("💾 Save Scenario", type="primary", key="save_sc", use_container_width=True):
        name = sc_name.strip() if sc_name else f"D:{d:+d}% B:{b:+d}% FX:{f:+d}% S:+{s}"
        save_scenario(name, {"diesel_price_change_pct": d, "blackout_hours_change_pct": b, "fx_change_pct": f, "solar_new_sites": s}, scenario)
        log_activity("save_scenario", name, "Scenario Simulator")
        st.success(f"Saved: **{name}**")
with sv3:
    notes = st.text_input("Notes", placeholder="Notes...", key="sc_notes", label_visibility="collapsed")

st.markdown("")

# ══════════════════════════════════════════════════════════════════════════════
# TABS: 7 analysis views
# ══════════════════════════════════════════════════════════════════════════════

tab = ui.tabs(options=["Comparison", "Waterfall", "Sensitivity", "Store Drill-Down",
                        "Break-Even", "Timeline", "Saved Scenarios"],
              default_value="Comparison", key="sc_tabs")

# ── TAB 1: Comparison ──
if tab == "Comparison":
    cats = ["Energy Cost", "Diesel Cost", "Sales", "EBITDA"]
    cur = [scenario["original_energy_cost"]/1e9, scenario["original_diesel_cost"]/1e9,
           scenario["original_sales"]/1e9, scenario["original_ebitda"]/1e9]
    scn = [scenario["scenario_energy_cost"]/1e9, scenario["scenario_diesel_cost"]/1e9,
           scenario["scenario_sales"]/1e9, scenario["scenario_ebitda"]/1e9]
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Current", x=cats, y=cur, marker_color="#3b82f6"))
    fig.add_trace(go.Bar(name="Scenario", x=cats, y=scn, marker_color="#ef4444"))
    fig.update_layout(barmode="group", height=420, yaxis_title="Billion MMK",
                      margin=dict(l=40, r=20, t=20, b=40), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

    # Store modes comparison
    st.markdown("#### Store Operating Modes")
    modes = ["FULL", "REDUCED", "CRITICAL", "CLOSE"]
    cur_m = [baseline["total_stores"], 0, 0, 0]
    scn_m = [scenario["est_stores_full"], scenario["est_stores_reduced"], scenario["est_stores_critical"], scenario["est_stores_closed"]]
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(name="Current", x=modes, y=cur_m, marker_color="#93c5fd"))
    fig2.add_trace(go.Bar(name="Scenario", x=modes, y=scn_m, marker_color=[OPERATING_MODES[m]["color"] for m in modes]))
    fig2.update_layout(barmode="group", height=350, yaxis_title="Stores", margin=dict(l=40, r=20, t=20, b=40),
                       plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig2, use_container_width=True)

# ── TAB 2: Cost Waterfall ──
elif tab == "Waterfall":
    st.markdown("### Cost Impact Waterfall")
    base_cost = scenario["original_energy_cost"] / 1e6
    diesel_impact = (scenario["scenario_diesel_cost"] - scenario["original_diesel_cost"]) / 1e6
    # Estimate blackout impact on sales
    sales_impact = (scenario["scenario_sales"] - scenario["original_sales"]) / 1e6
    solar_save = -scenario["solar_saving_mmk"] / 1e6
    total = scenario["scenario_energy_cost"] / 1e6

    fig = go.Figure(go.Waterfall(
        name="Cost Impact",
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "total"],
        x=["Baseline Cost", "Diesel Impact", "Sales Loss", "Solar Savings", "Scenario Total"],
        y=[base_cost, diesel_impact, abs(sales_impact) if sales_impact < 0 else 0, solar_save, total],
        text=[f"{base_cost:,.0f}M", f"{diesel_impact:+,.0f}M", f"{sales_impact:,.0f}M", f"{solar_save:,.0f}M", f"{total:,.0f}M"],
        textposition="outside",
        connector=dict(line=dict(color="#94a3b8", width=1)),
        increasing=dict(marker_color="#ef4444"),
        decreasing=dict(marker_color="#22c55e"),
        totals=dict(marker_color="#3b82f6"),
    ))
    fig.update_layout(height=450, yaxis_title="Million MMK", margin=dict(l=40, r=20, t=20, b=40),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    render_caption("sc_waterfall", captions)

# ── TAB 3: Sensitivity Analysis ──
elif tab == "Sensitivity":
    st.markdown("### Sensitivity Analysis — Which Parameter Matters Most?")
    st.caption("Each bar shows the EBITDA impact of changing ONE parameter by +10%, holding others at zero.")

    params = [("Diesel Price +10%", 10, 0, 0, 0), ("Blackout Hours +10%", 0, 10, 0, 0),
              ("FX Rate +10%", 0, 0, 10, 0), ("5 Solar Sites", 0, 0, 0, 5)]
    impacts = []
    for label, dp, bp, fp, sp in params:
        r = agg.simulate_scenario(stores, energy, sales, inv,
                                   diesel_price_change_pct=dp, blackout_hours_change_pct=bp,
                                   fx_change_pct=fp, solar_new_sites=sp)
        impacts.append(r["ebitda_impact_pct"])

    colors = ["#ef4444" if i < 0 else "#22c55e" for i in impacts]
    labels = [p[0] for p in params]

    fig = go.Figure(go.Bar(
        x=impacts, y=labels, orientation="h",
        marker_color=colors,
        text=[f"{i:+.2f}%" for i in impacts], textposition="outside"
    ))
    fig.update_layout(height=300, xaxis_title="EBITDA Impact %", margin=dict(l=160, r=60, t=20, b=40),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    fig.add_vline(x=0, line_dash="dash", line_color="#94a3b8")
    st.plotly_chart(fig, use_container_width=True)
    render_caption("sc_sensitivity", captions)

    # Show ranking
    ranked = sorted(zip(labels, impacts), key=lambda x: abs(x[1]), reverse=True)
    st.markdown(f"**Biggest driver:** {ranked[0][0]} ({ranked[0][1]:+.2f}% EBITDA impact)")

# ── TAB 4: Store Drill-Down ──
elif tab == "Store Drill-Down":
    st.markdown("### Store-Level Impact Under This Scenario")

    # Run store decision engine with scenario parameters
    try:
        from models.store_decision_engine import StoreDecisionEngine
        engine = StoreDecisionEngine()
        plan = engine.generate_daily_plan(stores, energy, sales, inv, solar_df=None)
        plan_display = plan[["store_id", "name", "sector", "channel", "mode", "reason",
                             "estimated_daily_profit", "diesel_days_remaining"]].copy()
        plan_display["estimated_daily_profit"] = plan_display["estimated_daily_profit"].apply(lambda x: f"{x/1e3:,.0f}K")
        plan_display["diesel_days_remaining"] = plan_display["diesel_days_remaining"].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")
        plan_display.columns = ["ID", "Store", "Sector", "Channel", "Mode", "Reason", "Est Profit", "Diesel Days"]

        # Filter tabs
        mode_filter = ui.tabs(options=["All", "CLOSE", "CRITICAL", "REDUCED", "FULL"], default_value="All", key="store_drill_filter")
        if mode_filter != "All":
            plan_display = plan_display[plan_display["Mode"] == mode_filter]

        from utils.smart_table import render_smart_table
        render_smart_table(plan_display, key="drill_table", title=f"Store Plan ({len(plan_display)} stores)",
                           severity_col="Mode", max_height=500)

        # Summary cards
        close_n = len(plan[plan["mode"] == "CLOSE"])
        crit_n = len(plan[plan["mode"] == "CRITICAL"])
        if close_n > 0 or crit_n > 0:
            st.markdown(f"""
            <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:12px 16px;margin-top:12px">
                <strong style="color:#dc2626">{close_n} stores CLOSED, {crit_n} CRITICAL</strong>
                <div style="color:#991b1b;font-size:0.85rem;margin-top:4px">
                    Closed: {', '.join(plan[plan['mode']=='CLOSE']['name'].tolist()[:10])}
                </div>
            </div>""", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Could not generate store plan: {e}")

# ── TAB 5: Break-Even Calculator ──
elif tab == "Break-Even":
    st.markdown("### Break-Even Analysis")
    st.caption("At what diesel price increase does the network start losing stores?")

    thresholds = {"First store closes": None, "5 stores close": None, "10 stores close": None, "20 stores close": None}
    for pct in range(0, 55, 5):
        r = agg.simulate_scenario(stores, energy, sales, inv, diesel_price_change_pct=pct)
        closed = r["est_stores_closed"]
        if closed >= 1 and thresholds["First store closes"] is None:
            thresholds["First store closes"] = pct
        if closed >= 5 and thresholds["5 stores close"] is None:
            thresholds["5 stores close"] = pct
        if closed >= 10 and thresholds["10 stores close"] is None:
            thresholds["10 stores close"] = pct
        if closed >= 20 and thresholds["20 stores close"] is None:
            thresholds["20 stores close"] = pct

    bcols = st.columns(4)
    for idx, (label, val) in enumerate(thresholds.items()):
        with bcols[idx]:
            content = f"+{val}%" if val is not None else ">50%"
            color = "#22c55e" if val is None or val > 30 else ("#f59e0b" if val > 15 else "#ef4444")
            ui.metric_card(title=label, content=content, description="diesel price increase", key=f"be_{idx}")

    # Chart: closures vs diesel price
    diesel_range = list(range(-20, 55, 5))
    closures = []
    for pct in diesel_range:
        r = agg.simulate_scenario(stores, energy, sales, inv, diesel_price_change_pct=pct)
        closures.append(r["est_stores_closed"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=diesel_range, y=closures, mode="lines+markers",
                             line=dict(color="#ef4444", width=2), marker=dict(size=6),
                             fill="tozeroy", fillcolor="rgba(239,68,68,0.1)"))
    fig.add_vline(x=d, line_dash="dash", line_color="#7c3aed", annotation_text="Current scenario")
    fig.update_layout(height=400, xaxis_title="Diesel Price Change %", yaxis_title="Stores Closed",
                      margin=dict(l=40, r=20, t=20, b=40), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

# ── TAB 6: Timeline Projection ──
elif tab == "Timeline":
    st.markdown("### 90-Day EBITDA Projection")
    st.caption("How this scenario compounds over 30, 60, and 90 days if conditions persist.")

    base_daily_ebitda = scenario["original_ebitda"] / 180  # ~180 days of data
    sc_daily_ebitda = scenario["scenario_ebitda"] / 180
    days = list(range(1, 91))

    baseline_cum = [base_daily_ebitda * d / 1e9 for d in days]
    scenario_cum = [sc_daily_ebitda * d / 1e9 for d in days]
    gap = [(base_daily_ebitda - sc_daily_ebitda) * d / 1e6 for d in days]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=days, y=baseline_cum, name="Current Trajectory",
                             line=dict(color="#3b82f6", width=2)))
    fig.add_trace(go.Scatter(x=days, y=scenario_cum, name="Scenario Trajectory",
                             line=dict(color="#ef4444", width=2, dash="dash")))
    fig.update_layout(height=400, xaxis_title="Days", yaxis_title="Cumulative EBITDA (Billion MMK)",
                      margin=dict(l=40, r=20, t=20, b=40), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", y=1.05))
    st.plotly_chart(fig, use_container_width=True)

    # Milestone cards
    mc = st.columns(3)
    for idx, day in enumerate([30, 60, 90]):
        with mc[idx]:
            loss = gap[day - 1]
            ui.metric_card(title=f"Day {day} Gap", content=f"{loss:,.0f}M MMK",
                           description="cumulative difference", key=f"tl_{day}")

# ── TAB 7: Saved Scenarios ──
elif tab == "Saved Scenarios":
    st.markdown("### Saved Scenarios")
    saved = get_saved_scenarios(limit=30)
    if not saved:
        st.info("No saved scenarios. Run and save a scenario first.")
    else:
        from utils.smart_table import render_smart_table
        table_data = pd.DataFrame([{
            "Name": s["name"], "Diesel": f"{s['diesel_price_change']:+.0f}%",
            "Blackout": f"{s['blackout_hours_change']:+.0f}%", "FX": f"{s['fx_change']:+.0f}%",
            "Solar": f"+{s['solar_new_sites']}", "EBITDA": f"{s['result_ebitda_impact_pct']:+.1f}%",
            "Closed": s["result_stores_closed"], "Date": s["created_at"][:16] if s["created_at"] else ""
        } for s in saved])
        render_smart_table(table_data, key="saved_table", title="All Saved Scenarios", max_height=350)

        # Radar chart comparing up to 4 saved scenarios
        if len(saved) >= 2:
            st.markdown("### Scenario Comparison Radar")
            radar_scenarios = saved[:4]
            dimensions = ["EBITDA Impact", "Energy Cost Δ", "Stores Closed", "Diesel Δ", "Blackout Δ", "Solar"]

            fig = go.Figure()
            for s in radar_scenarios:
                vals = [
                    -s["result_ebitda_impact_pct"],  # Negate so worse = bigger
                    (s["result_energy_cost"] - scenario["original_energy_cost"]) / scenario["original_energy_cost"] * 100 if scenario["original_energy_cost"] else 0,
                    s["result_stores_closed"] * 2,  # Scale up for visibility
                    abs(s["diesel_price_change"]),
                    abs(s["blackout_hours_change"]),
                    s["solar_new_sites"] * 3,
                ]
                vals.append(vals[0])  # Close the radar
                fig.add_trace(go.Scatterpolar(
                    r=vals, theta=dimensions + [dimensions[0]],
                    fill="toself", name=s["name"][:25], opacity=0.6
                ))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True)), height=450,
                              margin=dict(l=60, r=60, t=40, b=40), showlegend=True)
            st.plotly_chart(fig, use_container_width=True)

        # EBITDA comparison bar
        st.markdown("### EBITDA Impact Comparison")
        names = [s["name"][:30] for s in saved]
        impacts = [s["result_ebitda_impact_pct"] for s in saved]
        colors = ["#22c55e" if e >= 0 else ("#f97316" if e > -10 else "#ef4444") for e in impacts]
        fig = go.Figure(go.Bar(x=names, y=impacts, marker_color=colors,
                                text=[f"{e:+.1f}%" for e in impacts], textposition="outside"))
        fig.update_layout(height=380, yaxis_title="EBITDA %", margin=dict(l=40, r=20, t=20, b=80),
                          xaxis_tickangle=-45, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        fig.add_hline(y=0, line_dash="dash", line_color="#94a3b8")
        st.plotly_chart(fig, use_container_width=True)

        # Delete
        for s in saved:
            with st.expander(f"{s['name']} — {s['created_at'][:16]}"):
                st.markdown(f"Diesel {s['diesel_price_change']:+.0f}%, Blackout {s['blackout_hours_change']:+.0f}%, FX {s['fx_change']:+.0f}%, Solar +{s['solar_new_sites']}")
                st.markdown(f"EBITDA: {s['result_ebitda_impact_pct']:+.1f}% | Closed: {s['result_stores_closed']}")
                if st.button("🗑️ Delete", key=f"del_{s['id']}"):
                    delete_scenario(s["id"])
                    st.rerun()

# Generate pending captions
from utils.element_captions import generate_pending_captions
generate_pending_captions()

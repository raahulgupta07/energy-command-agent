"""
Page 12: BCP Dashboard — Business Continuity Planning
BCP scores, contingency playbooks, RTO, asset register, incidents, drills.
"""

import streamlit as st
import streamlit_shadcn_ui as ui
import plotly.graph_objects as go
import pandas as pd
from utils.data_loader import load_stores, load_daily_energy, load_diesel_inventory, load_store_sales
from utils.page_intelligence import render_page_intelligence
from utils.element_captions import get_page_captions, render_caption
from utils.smart_table import render_smart_table
from models.bcp_engine import BCPEngine
from utils.database import (save_incident, get_incidents, delete_incident,
                             save_drill, complete_drill, get_drills, delete_drill, log_activity)

st.set_page_config(page_title="BCP Dashboard", page_icon="🛡️", layout="wide")

st.markdown("""
<div style="background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 50%,#dc2626 100%);color:white;padding:20px 28px;border-radius:12px;margin-bottom:20px">
    <h2 style="margin:0;color:white">Business Continuity Planning</h2>
    <p style="margin:4px 0 0;opacity:0.85">BCP scores, contingency playbooks, RTO analysis, incident tracking, drill management</p>
</div>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_bcp_data():
    stores = load_stores()
    energy = load_daily_energy()
    inv = load_diesel_inventory()
    try:
        sales = load_store_sales()
    except Exception:
        sales = None
    engine = BCPEngine()
    scores = engine.compute_bcp_scores(stores, energy, inv, sales)
    playbooks = engine.generate_playbooks(stores, energy)
    rto = engine.compute_rto(stores, energy)
    assets = engine.get_critical_assets(stores)
    summary = engine.get_summary()
    return stores, energy, inv, scores, playbooks, rto, assets, summary

stores, energy, inv, scores, playbooks, rto, assets, summary = load_bcp_data()

# ── AI Page Intelligence ──
render_page_intelligence("bcp", f"BCP Summary: {summary['total_stores']} stores, Avg score: {summary['avg_bcp_score']}, "
    f"Resilient(A): {summary['grade_a']}, Adequate(B): {summary['grade_b']}, At Risk(C): {summary['grade_c']}, "
    f"Vulnerable(D): {summary['grade_d']}, Critical(F): {summary['grade_f']}. "
    f"Min score: {summary['min_bcp_score']}, Max score: {summary['max_bcp_score']}.")

# ── KPI Cards ──
cols = st.columns(4)
with cols[0]:
    color = "#22c55e" if summary["avg_bcp_score"] >= 60 else ("#f59e0b" if summary["avg_bcp_score"] >= 40 else "#ef4444")
    ui.metric_card(title="Avg BCP Score", content=f"{summary['avg_bcp_score']}/100",
                   description="network average", key="bcp_avg")
with cols[1]:
    ui.metric_card(title="Resilient Stores", content=f"{summary['grade_a'] + summary['grade_b']}",
                   description=f"Grade A: {summary['grade_a']}, B: {summary['grade_b']}", key="bcp_ok")
with cols[2]:
    ui.metric_card(title="At Risk Stores", content=f"{summary['grade_c'] + summary['grade_d']}",
                   description=f"Grade C: {summary['grade_c']}, D: {summary['grade_d']}", key="bcp_risk")
with cols[3]:
    ui.metric_card(title="Critical (F)", content=str(summary['grade_f']),
                   description="need immediate action", key="bcp_crit")

st.markdown("")

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════

tab = ui.tabs(options=["BCP Scores", "Contingency Playbook", "RTO Analysis",
                        "Asset Register", "Incident Log", "Drill Scheduler"],
              default_value="BCP Scores", key="bcp_tabs")

# ── TAB 1: BCP Scores ──
if tab == "BCP Scores":
    st.markdown("### BCP Resilience Scores")

    # Score distribution chart
    fig = go.Figure()
    grade_colors = {"A": "#22c55e", "B": "#3b82f6", "C": "#f59e0b", "D": "#ef4444", "F": "#7f1d1d"}
    for grade in ["A", "B", "C", "D", "F"]:
        grade_data = scores[scores["grade"] == grade]
        if len(grade_data) > 0:
            fig.add_trace(go.Bar(
                x=grade_data["name"], y=grade_data["bcp_score"],
                name=f"Grade {grade}", marker_color=grade_colors[grade],
                text=grade_data["bcp_score"].apply(lambda x: f"{x:.0f}"),
                textposition="outside"
            ))
    fig.update_layout(height=450, yaxis_title="BCP Score (0-100)", barmode="stack",
                      margin=dict(l=40, r=20, t=20, b=120), xaxis_tickangle=-45,
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    fig.add_hline(y=60, line_dash="dash", line_color="#22c55e", annotation_text="Adequate (60)")
    fig.add_hline(y=40, line_dash="dash", line_color="#f59e0b", annotation_text="At Risk (40)")
    st.plotly_chart(fig, use_container_width=True)

    # Score breakdown radar — worst 5 stores
    st.markdown("#### Weakest Stores — Score Breakdown")
    worst5 = scores.head(5)
    dimensions = ["Power Backup", "Fuel Reserve", "Solar", "Cold Chain", "Operations"]

    fig2 = go.Figure()
    for _, row in worst5.iterrows():
        vals = [row["power_backup_score"], row["fuel_reserve_score"], row["solar_resilience_score"],
                row["cold_chain_score"], row["ops_resilience_score"]]
        vals.append(vals[0])
        fig2.add_trace(go.Scatterpolar(
            r=vals, theta=dimensions + [dimensions[0]],
            fill="toself", name=f"{row['name']} ({row['bcp_score']:.0f})", opacity=0.5
        ))
    fig2.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                       height=400, margin=dict(l=60, r=60, t=40, b=40))
    st.plotly_chart(fig2, use_container_width=True)

    # Full table
    display = scores[["name", "sector", "channel", "bcp_score", "grade", "status",
                       "power_backup_score", "fuel_reserve_score", "solar_resilience_score",
                       "cold_chain_score", "ops_resilience_score", "diesel_days"]].copy()
    display.columns = ["Store", "Sector", "Channel", "BCP Score", "Grade", "Status",
                        "Power", "Fuel", "Solar", "Cold Chain", "Ops", "Diesel Days"]
    render_smart_table(display, key="bcp_scores_table", title="All Stores — BCP Scores",
                       severity_col="Status", max_height=500)

# ── TAB 2: Contingency Playbook ──
elif tab == "Contingency Playbook":
    st.markdown("### Emergency Contingency Playbook")
    st.caption("Pre-defined action plans for each threat level. Print or share with store managers.")

    for level_name, playbook in playbooks.items():
        sev_colors = {"normal": "#3b82f6", "warning": "#f59e0b", "critical": "#ef4444"}
        sev_bg = {"normal": "#eff6ff", "warning": "#fffbeb", "critical": "#fef2f2"}
        color = sev_colors.get(playbook["severity"], "#64748b")
        bg = sev_bg.get(playbook["severity"], "#f8fafc")

        with st.expander(f"{'🟢' if playbook['severity'] == 'normal' else '🟡' if playbook['severity'] == 'warning' else '🔴'} {level_name} ({playbook['duration']})", expanded=False):
            st.markdown(f"""
            <div style="background:{bg};border-left:4px solid {color};border-radius:0 8px 8px 0;padding:14px 18px;margin-bottom:12px">
                <strong style="color:{color};font-size:1rem">{level_name}</strong>
                <div style="color:#475569;font-size:0.85rem;margin-top:4px">Duration: {playbook['duration']}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("**Immediate Actions:**")
            for action in playbook["actions"]:
                st.markdown(f"- {action}")

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"**🧊 Cold Chain:** {playbook['cold_chain']}")
            with c2:
                st.markdown(f"**👥 Staffing:** {playbook['staffing']}")
            with c3:
                st.markdown(f"**⛽ Procurement:** {playbook['procurement']}")

# ── TAB 3: RTO Analysis ──
elif tab == "RTO Analysis":
    st.markdown("### Recovery Time Objective (RTO) Analysis")
    st.caption("Estimated time for each store to resume full operations after total blackout.")

    # RTO distribution chart
    fig = go.Figure()
    rto_colors = {"EXCELLENT": "#22c55e", "GOOD": "#3b82f6", "ACCEPTABLE": "#f59e0b", "NEEDS IMPROVEMENT": "#ef4444"}
    for status in ["NEEDS IMPROVEMENT", "ACCEPTABLE", "GOOD", "EXCELLENT"]:
        data = rto[rto["rto_status"] == status]
        if len(data) > 0:
            fig.add_trace(go.Bar(x=data["name"], y=data["rto_hours"],
                                  name=status, marker_color=rto_colors[status]))
    fig.update_layout(height=420, yaxis_title="RTO (Hours)", barmode="stack",
                      margin=dict(l=40, r=20, t=20, b=120), xaxis_tickangle=-45,
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    fig.add_hline(y=2, line_dash="dash", line_color="#22c55e", annotation_text="Target: 2h")
    st.plotly_chart(fig, use_container_width=True)

    # RTO summary cards
    rc = st.columns(4)
    with rc[0]:
        ui.metric_card(title="Avg RTO", content=f"{rto['rto_hours'].mean():.1f}h", description="network average", key="rto_avg")
    with rc[1]:
        ui.metric_card(title="Best RTO", content=f"{rto['rto_hours'].min():.1f}h",
                       description=rto[rto["rto_hours"] == rto["rto_hours"].min()]["name"].iloc[0], key="rto_best")
    with rc[2]:
        ui.metric_card(title="Worst RTO", content=f"{rto['rto_hours'].max():.1f}h",
                       description=rto[rto["rto_hours"] == rto["rto_hours"].max()]["name"].iloc[0], key="rto_worst")
    with rc[3]:
        ui.metric_card(title="Within Target", content=f"{len(rto[rto['rto_hours'] <= 2])}/{len(rto)}",
                       description="≤ 2 hours", key="rto_target")

    # Full table
    rto_display = rto[["name", "sector", "channel", "rto_hours", "rto_status", "has_solar", "generator_kw", "cold_chain"]].copy()
    rto_display["has_solar"] = rto_display["has_solar"].map({True: "Yes", False: "No"})
    rto_display["cold_chain"] = rto_display["cold_chain"].map({True: "Yes", False: "No"})
    rto_display.columns = ["Store", "Sector", "Channel", "RTO (hrs)", "Status", "Solar", "Generator kW", "Cold Chain"]
    render_smart_table(rto_display, key="rto_table", title="RTO by Store", severity_col="Status", max_height=450)

# ── TAB 4: Asset Register ──
elif tab == "Asset Register":
    st.markdown("### Critical Asset Register")
    st.caption("All generators, solar panels, fuel tanks, and cold chain units mapped per store.")

    # Summary
    total_gen = len(stores)
    total_solar = stores["has_solar"].sum()
    total_cc = stores["cold_chain"].sum()
    total_kw = stores["generator_kw"].sum()

    ac = st.columns(4)
    with ac[0]:
        ui.metric_card(title="Generators", content=str(total_gen), description=f"Total: {total_kw:,} kW", key="asset_gen")
    with ac[1]:
        ui.metric_card(title="Solar Panels", content=str(int(total_solar)), description=f"{total_solar/len(stores)*100:.0f}% coverage", key="asset_solar")
    with ac[2]:
        ui.metric_card(title="Cold Chain Units", content=str(int(total_cc)), description="refrigeration systems", key="asset_cc")
    with ac[3]:
        ui.metric_card(title="Fuel Tanks", content=str(total_gen), description="one per store", key="asset_fuel")

    # Asset table
    asset_display = stores[["store_id", "name", "sector", "township", "generator_kw", "has_solar", "cold_chain"]].copy()
    asset_display["has_solar"] = asset_display["has_solar"].map({True: "☀️ Yes", False: "No"})
    asset_display["cold_chain"] = asset_display["cold_chain"].map({True: "🧊 Yes", False: "No"})
    asset_display["fuel_tank"] = asset_display["generator_kw"].apply(lambda x: f"{x*2}L est.")
    asset_display.columns = ["ID", "Store", "Sector", "Township", "Generator kW", "Solar", "Cold Chain", "Fuel Tank"]
    render_smart_table(asset_display, key="asset_table", title="Asset Register", max_height=500)

# ── TAB 5: Incident Log ──
elif tab == "Incident Log":
    st.markdown("### Incident Log")
    st.caption("Track blackout incidents, response times, losses, and lessons learned.")

    # Log new incident
    with st.expander("➕ Log New Incident", expanded=False):
        ic1, ic2 = st.columns(2)
        with ic1:
            inc_store = st.selectbox("Store", stores["name"].tolist(), key="inc_store")
            inc_type = st.selectbox("Incident Type", ["Blackout", "Generator Failure", "Fuel Shortage",
                                                       "Cold Chain Breach", "Equipment Damage", "Other"], key="inc_type")
            inc_severity = st.selectbox("Severity", ["critical", "high", "medium", "low"], key="inc_sev")
        with ic2:
            inc_duration = st.number_input("Duration (hours)", 0.0, 48.0, 4.0, 0.5, key="inc_dur")
            inc_response = st.number_input("Response Time (min)", 0.0, 240.0, 15.0, 5.0, key="inc_resp")
            inc_loss = st.number_input("Estimated Loss (MMK)", 0, 10000000, 0, 100000, key="inc_loss")
        inc_actions = st.text_area("Actions Taken", key="inc_actions", height=80)
        inc_lessons = st.text_area("Lessons Learned", key="inc_lessons", height=80)

        if st.button("📝 Save Incident", type="primary", key="save_inc"):
            store_row = stores[stores["name"] == inc_store].iloc[0]
            save_incident(store_row["store_id"], inc_store, inc_type, inc_duration,
                         inc_response, inc_loss, inc_actions, inc_lessons, inc_severity,
                         "", pd.Timestamp.now().strftime("%Y-%m-%d"))
            log_activity("log_incident", f"{inc_type} at {inc_store}", "BCP Dashboard")
            st.success("Incident logged!")
            st.rerun()

    # Show incidents
    incidents = get_incidents(limit=50)
    if incidents:
        inc_df = pd.DataFrame(incidents)
        display_inc = inc_df[["store_name", "incident_type", "severity", "duration_hours",
                               "response_time_min", "estimated_loss_mmk", "incident_date"]].copy()
        display_inc["estimated_loss_mmk"] = display_inc["estimated_loss_mmk"].apply(lambda x: f"{x/1e3:,.0f}K" if x else "0")
        display_inc.columns = ["Store", "Type", "Severity", "Duration (h)", "Response (min)", "Loss (MMK)", "Date"]
        render_smart_table(display_inc, key="inc_table", title=f"Incidents ({len(incidents)})",
                           severity_col="Severity", max_height=400)

        # Incident stats
        st.markdown("#### Incident Statistics")
        isc = st.columns(3)
        with isc[0]:
            ui.metric_card(title="Total Incidents", content=str(len(incidents)),
                           description="all time", key="inc_total")
        with isc[1]:
            avg_resp = sum(i["response_time_min"] for i in incidents) / len(incidents)
            ui.metric_card(title="Avg Response Time", content=f"{avg_resp:.0f} min",
                           description="across all incidents", key="inc_resp_avg")
        with isc[2]:
            total_loss = sum(i["estimated_loss_mmk"] or 0 for i in incidents)
            ui.metric_card(title="Total Losses", content=f"{total_loss/1e6:,.1f}M MMK",
                           description="estimated", key="inc_loss_total")
    else:
        st.info("No incidents logged yet. Use the form above to log your first incident.")

# ── TAB 6: Drill Scheduler ──
elif tab == "Drill Scheduler":
    st.markdown("### BCP Drill Scheduler")
    st.caption("Schedule and track BCP drills. Score readiness after completion.")

    # Schedule new drill
    with st.expander("➕ Schedule New Drill", expanded=False):
        dc1, dc2 = st.columns(2)
        with dc1:
            drill_store = st.selectbox("Store", stores["name"].tolist(), key="drill_store")
            drill_type = st.selectbox("Drill Type", ["Full Blackout Simulation", "Generator Switchover",
                                                      "Cold Chain Emergency", "Fuel Shortage Response",
                                                      "Communication Chain Test", "Full BCP Exercise"], key="drill_type")
        with dc2:
            drill_date = st.date_input("Scheduled Date", key="drill_date")
            drill_notes = st.text_input("Notes", key="drill_notes")

        if st.button("📅 Schedule Drill", type="primary", key="save_drill"):
            store_row = stores[stores["name"] == drill_store].iloc[0]
            save_drill(store_row["store_id"], drill_store, drill_type, str(drill_date), drill_notes)
            log_activity("schedule_drill", f"{drill_type} at {drill_store}", "BCP Dashboard")
            st.success("Drill scheduled!")
            st.rerun()

    # Show drills
    drills = get_drills(limit=50)
    if drills:
        # Separate scheduled vs completed
        scheduled = [d for d in drills if d["status"] == "scheduled"]
        completed = [d for d in drills if d["status"] == "completed"]

        if scheduled:
            st.markdown("#### Upcoming Drills")
            for d in scheduled:
                with st.container():
                    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
                    c1.write(f"**{d['store_name']}** — {d['drill_type']}")
                    c2.write(f"📅 {d['scheduled_date']}")
                    with c3:
                        score = st.number_input("Score", 0, 100, 75, key=f"ds_{d['id']}")
                    with c4:
                        if st.button("✅ Complete", key=f"dc_{d['id']}"):
                            complete_drill(d["id"], score)
                            log_activity("complete_drill", f"{d['drill_type']} at {d['store_name']}: {score}/100", "BCP Dashboard")
                            st.rerun()

        if completed:
            st.markdown("#### Completed Drills")
            comp_df = pd.DataFrame(completed)
            disp = comp_df[["store_name", "drill_type", "scheduled_date", "completed_date", "readiness_score"]].copy()
            disp["readiness_score"] = disp["readiness_score"].apply(lambda x: f"{x:.0f}/100" if x else "N/A")
            disp.columns = ["Store", "Drill Type", "Scheduled", "Completed", "Score"]
            render_smart_table(disp, key="drill_completed", title=f"Completed ({len(completed)})", max_height=350)

            # Readiness stats
            avg_readiness = comp_df["readiness_score"].mean()
            st.markdown(f"**Average Readiness Score: {avg_readiness:.0f}/100**")
    else:
        st.info("No drills scheduled yet. Use the form above to schedule your first BCP drill.")

# ── Bottom ──
from utils.element_captions import generate_pending_captions
generate_pending_captions()

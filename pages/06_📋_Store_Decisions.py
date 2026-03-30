"""
Page 5: Store Operating Decisions — shadcn/ui
Daily Operating Plan with mode badges, override UI, and EBITDA/hr.
"""

import streamlit as st
import streamlit_shadcn_ui as ui
import plotly.graph_objects as go
import pandas as pd
from config.settings import OPERATING_MODES, DECISION_RIGHTS
from utils.data_loader import load_stores, load_daily_energy, load_store_sales, load_diesel_inventory, load_solar_generation
from models.store_decision_engine import StoreDecisionEngine
from utils.rule_insights import render_insight_cards, generate_store_decision_insights
from utils.element_captions import get_page_captions, render_caption
from utils.page_intelligence import render_page_intelligence
from utils.smart_table import render_smart_table
from utils.database import save_decision_audit, get_decision_audit, save_recommendation, get_override_stats

st.set_page_config(page_title="Store Decisions", page_icon="📋", layout="wide")

st.markdown("""
<div style="background:linear-gradient(135deg,#064e3b,#059669);color:white;padding:20px 28px;border-radius:12px;margin-bottom:20px">
    <h2 style="margin:0;color:white">Daily Operating Plan</h2>
    <p style="margin:4px 0 0;opacity:0.85">AI-generated store decisions — FULL / SELECTIVE / REDUCED / CRITICAL / CLOSE</p>
</div>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_and_plan():
    stores = load_stores()
    energy = load_daily_energy()
    sales = load_store_sales()
    inv = load_diesel_inventory()
    solar = load_solar_generation()
    engine = StoreDecisionEngine()
    plan = engine.generate_daily_plan(stores, energy, sales, inv, solar_df=solar)
    summary = engine.get_summary()
    sector_summary = engine.get_sector_summary()
    alerts = engine.get_alerts()
    return plan, summary, sector_summary, alerts

plan, summary, sector_summary, alerts = load_and_plan()

render_page_intelligence("store_decisions", f"Total stores: {summary['total_stores']}, FULL: {summary['stores_full']}, SELECTIVE: {summary.get('stores_selective',0)}, REDUCED: {summary['stores_reduced']}, CRITICAL: {summary['stores_critical']}, CLOSED: {summary['stores_closed']}, Est profit: {summary['total_estimated_profit']:,.0f} MMK. Sector rules applied: {summary.get('sector_rules_applied',0)}.")

# ── AI Captions ──
captions = get_page_captions("store_decisions", [
    {"id": "d_total", "type": "metric", "title": "Total Stores", "value": str(summary["total_stores"])},
    {"id": "d_full", "type": "metric", "title": "FULL Mode Stores", "value": str(summary["stores_full"])},
    {"id": "d_selective", "type": "metric", "title": "SELECTIVE Mode Stores", "value": str(summary.get("stores_selective", 0))},
    {"id": "d_reduced", "type": "metric", "title": "REDUCED Mode Stores", "value": str(summary["stores_reduced"])},
    {"id": "d_critical", "type": "metric", "title": "CRITICAL Mode Stores", "value": str(summary["stores_critical"])},
    {"id": "d_closed", "type": "metric", "title": "CLOSED Stores", "value": str(summary["stores_closed"])},
    {"id": "d_profit", "type": "metric", "title": "Est. Daily Profit", "value": f"{summary['total_estimated_profit']/1e6:,.1f}M MMK"},
    {"id": "plan_table", "type": "table", "title": "Full Plan Table", "value": f"{len(plan)} stores with modes, EBITDA/hr, reasons"},
    {"id": "profitability_chart", "type": "chart", "title": "EBITDA/hr by Store", "value": f"Scatter of {len(plan)} stores"},
], data_summary=f"Daily plan: {summary['stores_full']} FULL, {summary.get('stores_selective',0)} SELECTIVE, {summary['stores_reduced']} REDUCED, {summary['stores_critical']} CRITICAL, {summary['stores_closed']} CLOSED. Total profit {summary['total_estimated_profit']/1e6:,.1f}M MMK.")

# ── Mode KPIs ──
cols = st.columns(6)
mode_cards = [
    ("Total Stores", str(summary["total_stores"]), "in plan", "d_total"),
    ("FULL", str(summary["stores_full"]), "normal", "d_full"),
    ("SELECTIVE", str(summary.get("stores_selective", 0)), "essential ops", "d_selective"),
    ("REDUCED", str(summary["stores_reduced"]), "partial", "d_reduced"),
    ("CRITICAL", str(summary["stores_critical"]), "minimum", "d_critical"),
    ("CLOSED", str(summary["stores_closed"]), "shutdown", "d_closed"),
]
for i, (title, content, desc, key) in enumerate(mode_cards):
    with cols[i]:
        ui.metric_card(title=title, content=content, description=desc, key=key)
        render_caption(key, captions)

# Profit + adoption stats
cols2 = st.columns(4)
with cols2[0]:
    ui.metric_card(title="Est. Profit", content=f"{summary['total_estimated_profit']/1e6:,.1f}M",
                   description="daily MMK", key="d_profit")
    render_caption("d_profit", captions)
with cols2[1]:
    override_stats = get_override_stats()
    ui.metric_card(title="AI Adoption", content=f"{override_stats['adoption_rate_pct']:.0f}%",
                   description=f"{override_stats['accepted']}/{override_stats['total']} accepted",
                   key="d_adoption")
with cols2[2]:
    rules_applied = summary.get("sector_rules_applied", 0)
    ui.metric_card(title="Sector Rules", content=str(rules_applied),
                   description="rules applied", key="d_rules")
with cols2[3]:
    neg_gen = summary.get("stores_negative_generator_ebitda", 0)
    ui.metric_card(title="Loss on Generator", content=str(neg_gen),
                   description="stores losing money", key="d_loss_gen")

st.markdown("")

# ── Key Insights (rule-based, always visible) ──
st.markdown("### Key Insights")
_decision_insights = generate_store_decision_insights(summary, plan)
render_insight_cards(_decision_insights)

st.markdown("")

# ── Tabs ──
tab = ui.tabs(options=["Operating Plan", "Override / Confirm", "Sector View", "Profitability", "Decision Rights"],
              default_value="Operating Plan", key="dec_tabs")

if tab == "Operating Plan":
    st.markdown("### Store Operating Modes")

    for mode_key in ["CLOSE", "CRITICAL", "SELECTIVE", "REDUCED", "FULL"]:
        mode_stores = plan[plan["mode"] == mode_key]
        if len(mode_stores) == 0:
            continue

        mode_info = OPERATING_MODES.get(mode_key, OPERATING_MODES["FULL"])
        variant = {"FULL": "default", "SELECTIVE": "secondary", "REDUCED": "secondary",
                    "CRITICAL": "destructive", "CLOSE": "outline"}.get(mode_key, "default")

        st.markdown(f"""
        <div style="background:{mode_info['color']}15;border-left:4px solid {mode_info['color']};padding:12px 16px;border-radius:0 8px 8px 0;margin:12px 0 8px">
            <strong style="color:{mode_info['color']}">{mode_info['label']}</strong> — {len(mode_stores)} stores — {mode_info['description']}
        </div>
        """, unsafe_allow_html=True)

        for _, row in mode_stores.iterrows():
            ebitda_hr = row.get('ebitda_per_hr', 0)
            ebitda_color = "#16a34a" if ebitda_hr > 0 else "#ef4444"
            sector_rule = row.get('sector_rule_applied', '')
            precool = row.get('precool_note', '')
            solar_shift = row.get('solar_shift_note', '')

            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
            c1.write(f"**{row['name']}**")
            c2.markdown(f"<span style='color:{ebitda_color};font-weight:600'>{ebitda_hr:,.0f} MMK/hr</span>", unsafe_allow_html=True)
            c3.write(f"Diesel: {row['diesel_days_remaining']:.1f} days")
            c4.write(row["reason"][:45])
            with c5:
                ui.badges(badge_list=[(mode_key, variant)], key=f"mode_{row['store_id']}")

            # Inline warnings for sector rules, pre-cool, solar shift
            warnings = []
            if sector_rule:
                warnings.append(f"<span style='background:#dbeafe;color:#1e40af;padding:2px 8px;border-radius:4px;font-size:0.75rem'>{sector_rule}</span>")
            if precool:
                warnings.append(f"<span style='background:#fef3c7;color:#92400e;padding:2px 8px;border-radius:4px;font-size:0.75rem'>Pre-cool: {precool}</span>")
            if solar_shift:
                warnings.append(f"<span style='background:#d1fae5;color:#065f46;padding:2px 8px;border-radius:4px;font-size:0.75rem'>Solar: {solar_shift}</span>")
            if warnings:
                st.markdown(" ".join(warnings), unsafe_allow_html=True)

    # Full table with EBITDA/hr columns
    st.markdown("### Full Plan Table")
    display = plan[["name", "sector", "channel", "mode", "reason",
                     "ebitda_per_hr", "ebitda_per_generator_hr", "labour_per_hour",
                     "avg_daily_sales", "avg_diesel_cost", "estimated_daily_profit",
                     "diesel_days_remaining"]].copy()

    for col in ["ebitda_per_hr", "ebitda_per_generator_hr", "labour_per_hour", "avg_daily_sales", "avg_diesel_cost", "estimated_daily_profit"]:
        display[col] = display[col].apply(
            lambda v: f"{v/1e6:,.1f}M" if abs(v) >= 1e6 else (f"{v/1e3:,.1f}K" if abs(v) >= 1e3 else f"{v:,.0f}"))
    display["diesel_days_remaining"] = display["diesel_days_remaining"].apply(lambda v: f"{v:.1f}")
    display.columns = ["Store", "Sector", "Channel", "Mode", "Reason",
                        "EBITDA/hr", "Gen EBITDA/hr", "Labour/hr",
                        "Daily Sales", "Diesel Cost", "Est. Profit", "Diesel Days"]
    render_smart_table(display, key="plan_table", title="Daily Operating Plan",
                       severity_col="Mode", max_height=400)
    render_caption("plan_table", captions)

elif tab == "Override / Confirm":
    st.markdown("### Confirm or Override AI Decisions")
    st.markdown("""
    <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:14px 18px;margin-bottom:16px">
        <strong>How it works:</strong> The AI COMMANDER recommends a mode for each store.
        Site managers <strong>confirm</strong> or <strong>override</strong> with a reason.
        Tracked for adoption rate (target: >80%).
    </div>
    """, unsafe_allow_html=True)

    # Store selector
    store_options = plan["name"].tolist()
    selected_store_name = st.selectbox("Select Store", store_options, key="override_store")
    store_row = plan[plan["name"] == selected_store_name].iloc[0]

    # Show current AI recommendation
    ai_mode = store_row["mode"]
    mode_info = OPERATING_MODES.get(ai_mode, OPERATING_MODES["FULL"])

    st.markdown(f"""
    <div style="background:{mode_info['color']}15;border:2px solid {mode_info['color']};border-radius:10px;padding:16px 20px;margin:12px 0">
        <div style="display:flex;justify-content:space-between;align-items:center">
            <div>
                <div style="font-size:0.8rem;color:#64748b">AI Recommendation</div>
                <div style="font-size:1.3rem;font-weight:700;color:{mode_info['color']}">{mode_info['label']}</div>
                <div style="font-size:0.85rem;color:#475569;margin-top:4px">{store_row['reason']}</div>
            </div>
            <div style="text-align:right">
                <div style="font-size:0.8rem;color:#64748b">EBITDA/hr</div>
                <div style="font-size:1.1rem;font-weight:600">{store_row.get('ebitda_per_hr', 0):,.0f} MMK</div>
                <div style="font-size:0.8rem;color:#64748b">Diesel: {store_row['diesel_days_remaining']:.1f} days</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Sector rule note
    if store_row.get("sector_rule_applied"):
        st.info(f"Sector Rule: {store_row['sector_rule_applied']}")
    if store_row.get("precool_note"):
        st.warning(f"Pre-cool: {store_row['precool_note']}")
    if store_row.get("solar_shift_note"):
        st.success(f"Solar: {store_row['solar_shift_note']}")

    # Decision form
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Confirm AI Decision", type="primary", key="confirm_btn", use_container_width=True):
            save_decision_audit(
                store_row["store_id"], store_row["name"],
                pd.Timestamp.now().strftime("%Y-%m-%d"),
                ai_mode, ai_mode,
                decided_by="Site Manager", sector=store_row["sector"], channel=store_row["channel"]
            )
            save_recommendation(store_row["store_id"], "operating_mode",
                                f"{ai_mode} for {store_row['name']}", accepted=True, source="COMMANDER")
            st.success(f"Confirmed: {store_row['name']} → **{ai_mode}**")
            st.cache_data.clear()

    with col_b:
        with st.expander("Override AI Decision"):
            mode_options = list(OPERATING_MODES.keys())
            override_mode = st.selectbox("Override to:", mode_options,
                                          index=mode_options.index(ai_mode), key="override_mode")
            override_by = st.text_input("Your name:", key="override_by")
            override_reason = st.text_area("Reason for override:", key="override_reason",
                                            placeholder="e.g. Store has enough diesel for 5 more days")

            if st.button("Submit Override", key="override_submit", use_container_width=True):
                if override_reason and override_by:
                    save_decision_audit(
                        store_row["store_id"], store_row["name"],
                        pd.Timestamp.now().strftime("%Y-%m-%d"),
                        ai_mode, override_mode,
                        decided_by=override_by, override_reason=override_reason,
                        sector=store_row["sector"], channel=store_row["channel"]
                    )
                    save_recommendation(store_row["store_id"], "operating_mode",
                                        f"{ai_mode} for {store_row['name']}", accepted=False,
                                        override_reason=override_reason, source="COMMANDER")
                    st.success(f"Override saved: {store_row['name']} → **{override_mode}** (was {ai_mode})")
                    st.cache_data.clear()
                else:
                    st.error("Please provide your name and reason for override")

    # Recent decisions audit
    st.markdown("### Recent Decisions")
    recent = get_decision_audit(limit=20)
    if recent:
        audit_df = pd.DataFrame(recent)[["store_name", "date", "ai_recommended_mode",
                                          "final_mode", "was_overridden", "decided_by",
                                          "override_reason", "created_at"]].copy()
        audit_df.columns = ["Store", "Date", "AI Recommended", "Final Mode", "Overridden",
                            "Decided By", "Reason", "Timestamp"]
        audit_df["Overridden"] = audit_df["Overridden"].map({0: "", 1: "OVERRIDE"})
        render_smart_table(audit_df, key="audit_table", title="Decision Audit Log",
                           severity_col="Overridden", max_height=300)
    else:
        st.caption("No decisions recorded yet. Use Confirm/Override above to start tracking.")

elif tab == "Sector View":
    st.markdown("### Sector Summary")
    for _, row in sector_summary.iterrows():
        selective = row.get("selective", 0)
        with st.container():
            ui.metric_card(title=row["sector"],
                           content=f"{row['total_stores']} stores | Profit: {row['total_profit']:,.0f} MMK",
                           description=f"Full: {row['full']} | Selective: {selective} | Reduced: {row['reduced']} | Critical: {row['critical']} | Closed: {row['closed']}",
                           key=f"ss_{row['sector']}")
    render_caption("sector_cards", captions)

elif tab == "Profitability":
    st.markdown("### EBITDA per Hour — Generator Profitability")

    fig = go.Figure()
    for mode in ["FULL", "SELECTIVE", "REDUCED", "CRITICAL", "CLOSE"]:
        md = plan[plan["mode"] == mode]
        if len(md) > 0:
            mode_info = OPERATING_MODES.get(mode, OPERATING_MODES["FULL"])
            fig.add_trace(go.Scatter(
                x=md["avg_diesel_cost"], y=md["avg_daily_margin"],
                mode="markers+text", name=mode_info["label"],
                marker=dict(color=mode_info["color"], size=10),
                text=md["name"], textposition="top center", textfont=dict(size=7)))

    max_val = max(plan["avg_diesel_cost"].max(), plan["avg_daily_margin"].max(), 1)
    fig.add_trace(go.Scatter(x=[0, max_val], y=[0, max_val], mode="lines",
                             name="Break-Even", line=dict(color="#94a3b8", dash="dash")))
    fig.update_layout(height=500, margin=dict(l=40, r=20, t=20, b=40),
                      xaxis_title="Diesel Cost (MMK)", yaxis_title="Daily Margin (MMK)",
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", y=1.05))
    st.plotly_chart(fig, use_container_width=True)
    render_caption("profitability_chart", captions)
    st.caption("Below the line = losing money on diesel. Above = profitable.")

elif tab == "Decision Rights":
    st.markdown("### Decision Rights Matrix")
    st.markdown("""
    <div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:10px;padding:14px 18px;margin-bottom:16px">
        Who can approve what. COMMANDER recommends automatically — humans confirm or override at each level.
    </div>
    """, unsafe_allow_html=True)

    rights_data = []
    for decision, levels in DECISION_RIGHTS.items():
        rights_data.append({
            "Decision": decision.replace("_", " ").title(),
            "AI (Auto)": levels.get("auto", "—") or "—",
            "Site Manager": levels.get("site_manager", "—") or "—",
            "Sector Lead": levels.get("sector_lead", "—") or "—",
            "Holdings GECC": levels.get("holdings", "—") or "—",
            "CFO/CEO": levels.get("cfo", "—") or "—",
        })
    render_smart_table(pd.DataFrame(rights_data), key="rights_table",
                       title="Decision Approval Matrix", max_height=400)

# ── Decision Alerts ──
if alerts:
    st.markdown("### Decision Alerts")
    for a in alerts[:10]:
        if a["tier"] == 1:
            ui.alert(title="CRITICAL", description=a["message"], key=f"da_{a.get('store_id','')}")
        else:
            st.warning(a["message"])

# Generate element captions for next visit
from utils.element_captions import generate_pending_captions
generate_pending_captions()

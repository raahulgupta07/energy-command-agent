"""
Page: AI Insights — Consolidated view of all AI-generated insights across all dashboards.
Single page showing everything the AI detected, organized by severity and category.
"""

import streamlit as st
import streamlit_shadcn_ui as ui
import pandas as pd
from utils.page_insights import get_all_insights_structured
from utils.llm_client import is_llm_available, get_active_model
from utils.element_captions import get_page_captions, render_caption
from utils.page_intelligence import render_page_intelligence


def _get_agent_status_label():
    try:
        from agents.config import is_agent_mode_available
        if is_agent_mode_available():
            return "⚡ Agent Mode Active (tool-calling AI)"
    except Exception:
        pass
    return "LLM Active" if is_llm_available() else "Rule-based mode"

st.set_page_config(page_title="AI Insights", page_icon="🧠", layout="wide")

st.markdown("""
<div style="background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 40%,#7c3aed 100%);color:white;padding:24px 28px;border-radius:12px;margin-bottom:20px">
    <h2 style="margin:0;color:white">AI Insights Hub</h2>
    <p style="margin:4px 0 0;opacity:0.85">All AI-generated insights across the entire system — one view</p>
    <div style="margin-top:10px;font-size:0.8rem;opacity:0.6">
        Model: """ + get_active_model() + """ | """ + _get_agent_status_label() + """
    </div>
</div>
""", unsafe_allow_html=True)

# ── Load All Insights ──
data = get_all_insights_structured()
insights = data["all"]
counts = data["counts"]

render_page_intelligence("ai_insights", f"Total insights: {counts['total']}, Critical: {counts['critical']}, Warnings: {counts['warning']}, Positive: {counts['positive']}.")

# ── AI Insight Captions ──
captions = get_page_captions("ai_insights", [
    {"id": "ai_total", "type": "metric", "title": "Total Insights", "value": f"{counts['total']} detected this week"},
    {"id": "ai_critical", "type": "metric", "title": "Critical Insights", "value": f"{counts['critical']} requiring immediate action"},
    {"id": "ai_warning", "type": "metric", "title": "Warnings", "value": f"{counts['warning']} to act on today"},
    {"id": "ai_positive", "type": "metric", "title": "Positive Insights", "value": f"{counts['positive']} good news items"},
    {"id": "ai_coverage_table", "type": "table", "title": "Insight Coverage by Dashboard", "value": "Shows insight count and severity breakdown per dashboard page"},
], data_summary=f"Total insights: {counts['total']}, Critical: {counts['critical']}, Warnings: {counts['warning']}, Positive: {counts['positive']}. "
                f"AI insights hub consolidating all system-wide detections.")

# ── KPI Row ──
cols = st.columns(4)
with cols[0]:
    ui.metric_card(title="Total Insights", content=str(counts["total"]),
                   description="detected this week", key="ai_total")
    render_caption("ai_total", captions)
with cols[1]:
    ui.metric_card(title="Critical", content=str(counts["critical"]),
                   description="act now", key="ai_critical")
    render_caption("ai_critical", captions)
with cols[2]:
    ui.metric_card(title="Warnings", content=str(counts["warning"]),
                   description="act today", key="ai_warning")
    render_caption("ai_warning", captions)
with cols[3]:
    ui.metric_card(title="Positive", content=str(counts["positive"]),
                   description="good news", key="ai_positive")
    render_caption("ai_positive", captions)

st.markdown("")

# ── Executive Summary ──
st.markdown("""
<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;padding:18px 22px;margin-bottom:20px">
    <div style="font-weight:700;color:#1e40af;margin-bottom:8px;font-size:1.05rem">Executive Summary</div>
    <div style="color:#1e293b;font-size:0.95rem;line-height:1.6">""" + data["summary"] + """</div>
</div>
""", unsafe_allow_html=True)

# ── LLM Executive Summary (if available) ──
if is_llm_available():
    @st.cache_data(ttl=300)
    def get_llm_summary():
        from utils.page_insights import _get_insight_engine
        ie = _get_insight_engine()
        return ie.get_llm_executive_summary()

    llm_text = get_llm_summary()
    if llm_text and llm_text != data["summary"]:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#faf5ff,#ede9fe);border:1px solid #c4b5fd;border-radius:12px;padding:18px 22px;margin-bottom:20px">
            <div style="font-weight:700;color:#5b21b6;margin-bottom:8px;font-size:1.05rem">AI Executive Summary (LLM)</div>
            <div style="color:#1e293b;font-size:0.95rem;line-height:1.6">{llm_text}</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ── Tabs: By Severity / By Category / Timeline ──
_tab_options = ["By Severity", "By Category", "Full Briefing"]
try:
    from agents.config import is_agent_mode_available
    if is_agent_mode_available():
        _tab_options.append("Agent Briefing")
except Exception:
    pass
tab = ui.tabs(options=_tab_options, default_value="By Severity", key="insight_tabs")

level_styles = {
    "critical": ("#fef2f2", "#ef4444", "#dc2626", "CRITICAL", "Act immediately"),
    "warning": ("#fff7ed", "#f97316", "#ea580c", "WARNING", "Act today"),
    "positive": ("#f0fdf4", "#22c55e", "#16a34a", "POSITIVE", "Good news"),
    "info": ("#f8fafc", "#94a3b8", "#64748b", "INFO", "For awareness"),
}

if tab == "By Severity":
    for level_key in ["critical", "warning", "positive", "info"]:
        level_insights = data["by_level"][level_key]
        if not level_insights:
            continue

        bg, border, text_color, label, desc = level_styles[level_key]

        st.markdown(f"""
        <div style="background:{border};color:white;padding:10px 16px;border-radius:10px 10px 0 0;margin-top:16px;display:flex;justify-content:space-between;align-items:center">
            <strong>{label} ({len(level_insights)})</strong>
            <span style="font-size:0.85rem;opacity:0.8">{desc}</span>
        </div>
        """, unsafe_allow_html=True)

        for i, insight in enumerate(level_insights):
            # Map category to page
            page_map = {
                "energy": "Sector Dashboard",
                "diesel": "Diesel Intelligence",
                "blackout": "Blackout Monitor",
                "solar": "Solar Performance",
                "inventory": "Store Decisions",
                "profitability": "Store Decisions",
                "fx": "Diesel Intelligence",
            }
            page = page_map.get(insight.get("category", ""), "Holdings")

            change_text = ""
            if insight.get("change_pct"):
                change_text = f'<span style="font-weight:700;color:{text_color};margin-left:8px">{insight["change_pct"]:+.1f}%</span>'

            st.markdown(f"""
            <div style="background:{bg};border-left:4px solid {border};border-radius:0 8px 8px 0;padding:10px 16px;margin:2px 0;display:flex;justify-content:space-between;align-items:center">
                <div>
                    <span style="color:#1e293b;font-size:0.9rem">{insight['text']}</span>
                    {change_text}
                </div>
                <span style="background:white;border:1px solid #e2e8f0;padding:2px 10px;border-radius:20px;font-size:0.7rem;color:#64748b;white-space:nowrap;margin-left:12px">{page}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("")

elif tab == "By Category":
    category_info = {
        "energy": ("⚡", "Energy Cost", "#2563eb", "Total energy cost changes across stores and sectors"),
        "diesel": ("⛽", "Diesel Price", "#ea580c", "Diesel price movements, volatility, and procurement signals"),
        "blackout": ("🔌", "Blackout", "#dc2626", "Power outage pattern changes by township"),
        "solar": ("☀️", "Solar", "#eab308", "Solar generation changes and performance"),
        "inventory": ("🛢️", "Diesel Inventory", "#f97316", "Stock levels, coverage days, supply risk"),
        "profitability": ("💰", "Profitability", "#16a34a", "Store margin vs energy cost analysis"),
        "fx": ("💱", "FX Rates", "#7c3aed", "Currency movements affecting diesel import costs"),
    }

    for cat_key, cat_insights in data["by_category"].items():
        icon, name, color, desc = category_info.get(cat_key, ("📊", cat_key.title(), "#64748b", ""))

        st.markdown(f"""
        <div style="background:{color}10;border:1px solid {color}30;border-left:4px solid {color};border-radius:0 12px 12px 0;padding:14px 18px;margin:12px 0 8px">
            <div style="display:flex;align-items:center;gap:8px">
                <span style="font-size:1.3rem">{icon}</span>
                <div>
                    <strong style="color:{color};font-size:1rem">{name}</strong>
                    <span style="color:#64748b;font-size:0.85rem;margin-left:8px">{len(cat_insights)} insight(s)</span>
                </div>
            </div>
            <div style="font-size:0.8rem;color:#94a3b8;margin-top:4px">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

        for insight in cat_insights:
            bg, border, _, label, _ = level_styles.get(insight["level"], ("#f8fafc", "#94a3b8", "#64748b", "INFO", ""))
            st.markdown(f"""
            <div style="background:{bg};border-left:3px solid {border};border-radius:0 6px 6px 0;padding:8px 14px;margin:3px 0 3px 24px">
                <span style="color:{border};font-weight:600;font-size:0.75rem">{label}</span>
                <span style="color:#1e293b;font-size:0.85rem;margin-left:6px">{insight['text']}</span>
            </div>
            """, unsafe_allow_html=True)

elif tab == "Full Briefing":
    st.markdown("### Morning Briefing Text")
    st.markdown("""
    <div style="background:#0f172a;color:#22c55e;font-family:'Courier New',monospace;font-size:0.85rem;padding:20px 24px;border-radius:12px;line-height:1.6;white-space:pre-wrap">""" +
    data["briefing"].replace("\n", "<br>") +
    """</div>""", unsafe_allow_html=True)

elif tab == "Agent Briefing":
    st.markdown("### AI Agent Briefing")
    st.markdown("""
    <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:12px 16px;margin-bottom:12px">
        <strong>⚡ Agentic Mode</strong> — The Briefing Agent autonomously runs models, investigates alerts, and produces a structured executive briefing.
    </div>
    """, unsafe_allow_html=True)
    if st.button("Generate Agent Briefing", type="primary", key="gen_agent_briefing"):
        with st.spinner("🤖 Briefing Agent running models and analyzing..."):
            try:
                from agents.briefing_agent import BriefingAgent
                agent = BriefingAgent()
                result = agent.run("Generate today's morning briefing for the executive team.")
                if result.success:
                    st.markdown(result.text)
                    if result.tool_calls_made:
                        with st.expander(f"Tools used ({len(result.tool_calls_made)})"):
                            for tc in result.tool_calls_made:
                                st.markdown(f"- **{tc['name']}** ({tc['duration_s']}s)")
                else:
                    st.warning("Agent could not complete the briefing. Falling back to standard.")
                    st.text(data["briefing"])
            except Exception as e:
                st.error(f"Agent error: {e}")
                st.text(data["briefing"])

st.divider()

# ── Insight Coverage Map ──
st.markdown("### Insight Coverage by Dashboard")

page_categories = {
    "Sector Dashboard": ["energy", "profitability"],
    "Holdings Control Tower": ["energy", "profitability", "blackout", "diesel", "fx", "solar", "inventory"],
    "Diesel Intelligence": ["diesel", "fx"],
    "Blackout Monitor": ["blackout"],
    "Store Decisions": ["profitability", "energy", "inventory"],
    "Solar Performance": ["solar"],
    "Alerts Center": ["energy", "diesel", "blackout", "solar", "inventory", "profitability", "fx"],
    "Scenario Simulator": ["energy", "diesel", "fx"],
}

coverage_rows = []
for page, cats in page_categories.items():
    page_insights = [i for i in insights if i.get("category") in cats]
    crit = len([i for i in page_insights if i["level"] == "critical"])
    warn = len([i for i in page_insights if i["level"] == "warning"])
    pos = len([i for i in page_insights if i["level"] == "positive"])
    coverage_rows.append({
        "Dashboard": page,
        "Total": len(page_insights),
        "Critical": crit,
        "Warnings": warn,
        "Positive": pos,
        "Categories": ", ".join(cats),
    })

# ── Beautiful Coverage Table ──
CATEGORY_COLORS = {
    "energy": "#3b82f6", "profitability": "#8b5cf6", "blackout": "#ef4444",
    "diesel": "#f59e0b", "fx": "#06b6d4", "solar": "#eab308",
    "inventory": "#22c55e",
}
PAGE_ICONS = {
    "Sector Dashboard": "🏪", "Holdings Control Tower": "🏛️",
    "Diesel Intelligence": "⛽", "Blackout Monitor": "🔌",
    "Store Decisions": "📋", "Solar Performance": "☀️",
    "Alerts Center": "🚨", "Scenario Simulator": "🔮",
}

table_rows_html = ""
for row in coverage_rows:
    page_name = row["Dashboard"]
    icon = PAGE_ICONS.get(page_name, "📄")
    total = row["Total"]
    crit = row["Critical"]
    warn = row["Warnings"]
    pos = row["Positive"]

    # Severity bar
    bar_parts = []
    if crit > 0:
        bar_parts.append(f'<span style="background:#ef4444;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.72rem;font-weight:700">{crit} Critical</span>')
    if warn > 0:
        bar_parts.append(f'<span style="background:#f59e0b;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.72rem;font-weight:700">{warn} Warning</span>')
    if pos > 0:
        bar_parts.append(f'<span style="background:#22c55e;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.72rem;font-weight:700">{pos} Positive</span>')
    if not bar_parts:
        bar_parts.append('<span style="background:#e2e8f0;color:#64748b;padding:2px 8px;border-radius:4px;font-size:0.72rem">No alerts</span>')
    severity_html = " ".join(bar_parts)

    # Category pills
    cats = row["Categories"].split(", ")
    cat_pills = " ".join(
        f'<span style="background:{CATEGORY_COLORS.get(c, "#94a3b8")}15;color:{CATEGORY_COLORS.get(c, "#94a3b8")};border:1px solid {CATEGORY_COLORS.get(c, "#94a3b8")}30;padding:1px 8px;border-radius:10px;font-size:0.68rem;font-weight:600">{c}</span>'
        for c in cats
    )

    # Total badge
    total_bg = "#ef4444" if crit > 0 else "#f59e0b" if warn > 0 else "#22c55e" if pos > 0 else "#e2e8f0"
    total_color = "#fff" if total > 0 else "#64748b"

    table_rows_html += f"""
    <tr style="border-bottom:1px solid #f1f5f9" onmouseover="this.style.background='#f8fafc'" onmouseout="this.style.background='#fff'">
        <td style="padding:12px 14px;display:flex;align-items:center;gap:8px">
            <span style="font-size:1.1rem">{icon}</span>
            <strong style="color:#0f172a;font-size:0.88rem">{page_name}</strong>
        </td>
        <td style="padding:12px 10px;text-align:center">
            <span style="background:{total_bg};color:{total_color};padding:3px 12px;border-radius:6px;font-weight:800;font-size:0.85rem">{total}</span>
        </td>
        <td style="padding:12px 10px">{severity_html}</td>
        <td style="padding:12px 10px">{cat_pills}</td>
    </tr>"""

st.markdown(f"""
<div style="border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;background:#fff">
    <table style="width:100%;border-collapse:collapse">
        <thead>
            <tr style="background:#f8fafc;border-bottom:2px solid #e2e8f0">
                <th style="padding:12px 14px;text-align:left;font-size:0.78rem;font-weight:700;color:#475569">Dashboard</th>
                <th style="padding:12px 10px;text-align:center;font-size:0.78rem;font-weight:700;color:#475569">Total</th>
                <th style="padding:12px 10px;text-align:left;font-size:0.78rem;font-weight:700;color:#475569">Alerts</th>
                <th style="padding:12px 10px;text-align:left;font-size:0.78rem;font-weight:700;color:#475569">Categories</th>
            </tr>
        </thead>
        <tbody>{table_rows_html}</tbody>
    </table>
</div>
""", unsafe_allow_html=True)
render_caption("ai_coverage_table", captions)

st.divider()

# ── How to Activate LLM ──
if not is_llm_available():
    st.markdown("""
    <div style="background:#fefce8;border:1px solid #fde68a;border-radius:12px;padding:16px 20px">
        <strong style="color:#92400e">Enhance with LLM</strong>
        <p style="color:#78350f;font-size:0.9rem;margin:8px 0 0">
        Currently running in <strong>rule-based mode</strong>. To get AI-written executive summaries,
        strategy recommendations, and natural language chat, add your OpenRouter API key:
        </p>
        <code style="background:#fff;padding:8px 12px;border-radius:6px;display:block;margin-top:8px;font-size:0.85rem">
        export OPENROUTER_API_KEY=sk-or-v1-your-key-here
        </code>
        <p style="color:#92400e;font-size:0.8rem;margin-top:8px">
        Models: openai/gpt-4.1-mini (primary) → anthropic/claude-3.5-haiku (fallback)
        </p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ── AI Chat ──
from utils.ai_chat import render_chat_widget
render_chat_widget("AI Insights Hub")

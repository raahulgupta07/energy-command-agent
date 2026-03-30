"""
Rule-Based Insight Generator — data-driven insights without LLM.
Computes actionable insights from actual numbers.
Works with or without API key.

Usage:
    from utils.rule_insights import generate_insights, render_insight_cards
    insights = generate_insights(energy_df, sales_df, stores_df, ...)
    render_insight_cards(insights)
"""

import streamlit as st
import pandas as pd
import numpy as np


def render_insight_cards(insights: list):
    """Render insight cards as styled HTML."""
    if not insights:
        return

    severity_styles = {
        "critical": {"bg": "#fef2f2", "border": "#ef4444", "icon": "🔴", "color": "#991b1b"},
        "warning": {"bg": "#fffbeb", "border": "#f59e0b", "icon": "🟡", "color": "#92400e"},
        "positive": {"bg": "#f0fdf4", "border": "#22c55e", "icon": "🟢", "color": "#166534"},
        "info": {"bg": "#f0f9ff", "border": "#3b82f6", "icon": "🔵", "color": "#1e40af"},
    }

    for insight in insights:
        sev = insight.get("severity", "info")
        style = severity_styles.get(sev, severity_styles["info"])
        action_html = ""
        if insight.get("action"):
            action_color = style["color"]
            action_text = insight["action"]
            action_html = f'<br><span style="color:{action_color};font-weight:600;font-size:0.82rem">Action: {action_text}</span>'
        title = insight.get("title", "")
        detail = insight.get("detail", "")
        st.markdown(f"""
        <div style="background:{style['bg']};border-left:4px solid {style['border']};padding:10px 14px;border-radius:0 8px 8px 0;margin:6px 0;font-size:0.85rem">
            <span>{style['icon']}</span>
            <strong style="color:{style['color']}">{title}</strong>
            <span style="color:#475569"> — {detail}</span>
            {action_html}
        </div>
        """, unsafe_allow_html=True)


def generate_sector_insights(store_perf: pd.DataFrame, filtered_energy: pd.DataFrame,
                               sector: str, energy_pct: float, avg_bo: float) -> list:
    """Generate insights for the Sector Dashboard page."""
    insights = []

    # 1. Energy cost ratio
    if energy_pct > 5:
        insights.append({
            "severity": "critical",
            "title": f"Energy cost at {energy_pct:.1f}% of sales",
            "detail": f"Above 3.5% target. {sector} sector is energy-inefficient.",
            "action": "Review generator efficiency and diesel procurement timing for worst stores.",
        })
    elif energy_pct > 3.5:
        insights.append({
            "severity": "warning",
            "title": f"Energy cost at {energy_pct:.1f}% of sales",
            "detail": "Approaching 3.5% threshold — monitor closely.",
            "action": "Identify stores above 5% and shift operations to solar hours where possible.",
        })
    else:
        insights.append({
            "severity": "positive",
            "title": f"Energy cost {energy_pct:.1f}% of sales — within target",
            "detail": "Below 3.5% threshold. Good energy management.",
        })

    # 2. Worst performing stores
    if len(store_perf) > 0 and "energy_pct" in store_perf.columns:
        at_risk = store_perf[store_perf["energy_pct"] > 8] if store_perf["energy_pct"].dtype != object else pd.DataFrame()
        if len(at_risk) > 0:
            worst = at_risk.iloc[0]
            insights.append({
                "severity": "critical",
                "title": f"{len(at_risk)} stores above 8% energy ratio",
                "detail": f"Worst: {worst.get('name', 'Unknown')} at {worst['energy_pct']:.1f}%.",
                "action": f"Investigate {worst.get('name', 'this store')} — check generator efficiency and diesel consumption.",
            })

    # 3. Blackout trend
    if avg_bo > 6:
        insights.append({
            "severity": "critical",
            "title": f"Average {avg_bo:.1f} hrs/day blackout — severe disruption",
            "detail": "More than 6 hours average. Generator costs will be very high.",
            "action": "Activate SELECTIVE/REDUCED mode for marginal stores. Pre-cool cold chain before peak blackout.",
        })
    elif avg_bo > 3:
        insights.append({
            "severity": "warning",
            "title": f"Average {avg_bo:.1f} hrs/day blackout",
            "detail": "Moderate disruption. Generator running significant hours.",
            "action": "Monitor diesel coverage — ensure all stores have >3 days stock.",
        })
    else:
        insights.append({
            "severity": "positive",
            "title": f"Low blackout impact — {avg_bo:.1f} hrs/day average",
            "detail": "Grid relatively stable for this sector.",
        })

    # 4. Diesel cost trend (last 7 days vs previous 7)
    if len(filtered_energy) > 0:
        recent = filtered_energy.sort_values("date")
        last_7 = recent[recent["date"] > recent["date"].max() - pd.Timedelta(days=7)]
        prev_7 = recent[(recent["date"] > recent["date"].max() - pd.Timedelta(days=14)) &
                         (recent["date"] <= recent["date"].max() - pd.Timedelta(days=7))]
        if len(last_7) > 0 and len(prev_7) > 0:
            recent_cost = last_7["diesel_cost_mmk"].sum()
            prev_cost = prev_7["diesel_cost_mmk"].sum()
            if prev_cost > 0:
                change_pct = (recent_cost - prev_cost) / prev_cost * 100
                if change_pct > 10:
                    insights.append({
                        "severity": "warning",
                        "title": f"Diesel cost up {change_pct:.0f}% vs last week",
                        "detail": f"This week: {recent_cost/1e6:,.1f}M vs last: {prev_cost/1e6:,.1f}M MMK.",
                        "action": "Check if diesel price spike or increased generator usage. Consider bulk purchase if price trending up.",
                    })
                elif change_pct < -10:
                    insights.append({
                        "severity": "positive",
                        "title": f"Diesel cost down {abs(change_pct):.0f}% vs last week",
                        "detail": f"This week: {recent_cost/1e6:,.1f}M vs last: {prev_cost/1e6:,.1f}M MMK.",
                    })

    return insights


def generate_chart_insight(chart_type: str, data: dict) -> list:
    """Generate insights for a specific chart."""
    insights = []

    if chart_type == "energy_vs_sales":
        top_store = data.get("top_store_name", "")
        top_pct = data.get("top_energy_pct", 0)
        if top_pct > 5:
            insights.append({
                "severity": "warning",
                "title": f"Chart insight: {top_store} has highest energy ratio ({top_pct:.1f}%)",
                "detail": "This store's energy cost is disproportionate to its sales — may be loss-making on generator.",
                "action": f"Review {top_store}'s generator efficiency and consider SELECTIVE mode during peak blackout.",
            })

    elif chart_type == "energy_trend":
        trend_direction = data.get("trend_direction", "stable")
        if trend_direction == "increasing":
            insights.append({
                "severity": "warning",
                "title": "Chart insight: Diesel cost trending upward",
                "detail": "Daily diesel cost has been increasing over the last 2 weeks.",
                "action": "Check diesel price trend and consider bulk purchase before further increases.",
            })
        elif trend_direction == "decreasing":
            insights.append({
                "severity": "positive",
                "title": "Chart insight: Diesel cost trending down",
                "detail": "Good — either prices dropping or grid availability improving.",
            })

    elif chart_type == "blackout_heatmap":
        worst_store = data.get("worst_store", "")
        worst_hrs = data.get("worst_avg_hours", 0)
        if worst_hrs > 8:
            insights.append({
                "severity": "critical",
                "title": f"Chart insight: {worst_store} averages {worst_hrs:.1f}hrs blackout",
                "detail": "This store is in a severely affected township.",
                "action": f"Ensure {worst_store} has adequate diesel + consider solar installation priority.",
            })

    return insights


def generate_holdings_insights(group_kpis: dict, sector_kpis=None) -> list:
    """Generate insights for the Holdings Control Tower page."""
    insights = []
    gk = group_kpis

    # ERI
    eri = gk.get("avg_eri_pct", 0)
    if eri < 70:
        insights.append({
            "severity": "critical",
            "title": f"Network resilience at {eri:.0f}% — below 85% target",
            "detail": "Too many stores unprofitable during disruption.",
            "action": "Review bottom 10 ERI stores. Consider solar expansion for worst performers.",
        })
    elif eri < 85:
        insights.append({
            "severity": "warning",
            "title": f"Network resilience at {eri:.0f}% — approaching target",
            "detail": "85% target not yet met.",
        })
    else:
        insights.append({
            "severity": "positive",
            "title": f"Network resilience at {eri:.0f}% — above 85% target",
            "detail": "Good network-wide energy resilience.",
        })

    # Diesel dependency
    diesel_dep = gk.get("avg_diesel_dependency_pct", 0)
    if diesel_dep > 60:
        insights.append({
            "severity": "warning",
            "title": f"Diesel dependency at {diesel_dep:.0f}%",
            "detail": "Network heavily reliant on diesel — vulnerable to price spikes.",
            "action": "Accelerate solar expansion for top 10 highest diesel-dependent stores.",
        })

    # Stores below 2 days coverage
    below_2 = gk.get("stores_below_2_days", 0)
    if below_2 > 0:
        insights.append({
            "severity": "critical",
            "title": f"{below_2} stores below 2 days diesel coverage",
            "detail": "Immediate stockout risk.",
            "action": "Order diesel for these stores TODAY or initiate reallocation from surplus sites.",
        })

    return insights


def generate_store_decision_insights(plan_summary: dict, plan_df: pd.DataFrame = None) -> list:
    """Generate insights for the Store Decisions page."""
    insights = []

    closed = plan_summary.get("stores_closed", 0)
    critical = plan_summary.get("stores_critical", 0)
    selective = plan_summary.get("stores_selective", 0)
    loss_gen = plan_summary.get("stores_negative_generator_ebitda", 0)
    rules = plan_summary.get("sector_rules_applied", 0)

    if closed > 0:
        insights.append({
            "severity": "critical",
            "title": f"{closed} stores recommended for CLOSURE",
            "detail": "Generator economics negative + critically low diesel.",
            "action": "Execute safe shutdown. Secure perishables. Reallocate diesel to profitable stores.",
        })

    if critical > 0:
        insights.append({
            "severity": "critical",
            "title": f"{critical} stores in CRITICAL mode",
            "detail": "Running cold chain only. Minimal staff.",
            "action": "Monitor diesel levels. Prepare for possible closure if no resupply.",
        })

    if selective > 0:
        insights.append({
            "severity": "warning",
            "title": f"{selective} stores in SELECTIVE mode",
            "detail": "Essential operations only — food, cold chain, key sales areas.",
            "action": "Review if any SELECTIVE stores can return to FULL based on solar availability.",
        })

    if loss_gen > 0:
        insights.append({
            "severity": "warning",
            "title": f"{loss_gen} stores losing money on generator",
            "detail": "EBITDA per generator hour is negative — diesel cost exceeds margin.",
            "action": "Switch these stores to SELECTIVE or CLOSE during generator-only hours.",
        })

    if rules > 0:
        insights.append({
            "severity": "info",
            "title": f"{rules} sector rules applied today",
            "detail": "Sector-specific overrides active (e.g., Hypermarket never close, Bakery solar shift).",
        })

    total = plan_summary.get("total_stores", 55)
    full = plan_summary.get("stores_full", 0)
    if full == total:
        insights.append({
            "severity": "positive",
            "title": "All stores operating at FULL capacity",
            "detail": "No disruption impact today. All stores profitable.",
        })

    return insights

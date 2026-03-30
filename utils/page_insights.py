"""
Reusable AI Insights widget for any dashboard page.
Call render_page_insights(page_name, category_filter) to add insights to any page.
"""

import streamlit as st
from utils.llm_client import is_llm_available


def _get_insight_engine():
    """Load data and create InsightEngine. Cached."""
    from utils.data_loader import (
        load_stores, load_daily_energy, load_store_sales,
        load_diesel_inventory, load_diesel_prices,
    )
    from utils.insight_engine import InsightEngine

    stores = load_stores()
    energy = load_daily_energy()
    sales = load_store_sales()
    inv = load_diesel_inventory()
    prices = load_diesel_prices()

    try:
        from utils.data_loader import load_fx_rates
        fx = load_fx_rates()
    except Exception:
        fx = None

    ie = InsightEngine(stores, energy, sales, inv, prices, fx)
    ie.generate_all(lookback_days=7)
    return ie


@st.cache_data(ttl=300)
def _cached_insights():
    """Cache all insights so we don't regenerate per page."""
    ie = _get_insight_engine()
    return ie.insights, ie.get_summary_text(), ie.get_briefing_paragraph()


def render_page_insights(page_name: str, categories: list = None, max_items: int = 6):
    """Render AI Insights section for any page.

    Args:
        page_name: Display name for the section header
        categories: Filter insights to these categories. None = show all.
                    Options: energy, diesel, blackout, solar, inventory, profitability, fx
        max_items: Max number of insights to show
    """
    all_insights, summary, _ = _cached_insights()

    # Filter by category if specified
    if categories:
        insights = [i for i in all_insights if i.get("category") in categories]
    else:
        insights = all_insights

    if not insights:
        return

    # Header
    llm_status = "LLM: Active" if is_llm_available() else "Rule-based mode"
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0f172a,#1e3a5f);color:white;padding:14px 18px;border-radius:12px;margin-bottom:12px">
        <div style="display:flex;align-items:center;gap:8px">
            <span style="font-size:1.2rem">🧠</span>
            <strong>AI Insights — {page_name}</strong>
            <span style="font-size:0.75rem;opacity:0.6;margin-left:auto">{llm_status}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Render insights
    level_styles = {
        "critical": ("#fef2f2", "#ef4444", "CRITICAL"),
        "warning": ("#fff7ed", "#f97316", "WARNING"),
        "positive": ("#f0fdf4", "#22c55e", "POSITIVE"),
        "info": ("#f8fafc", "#94a3b8", "INFO"),
    }

    for insight in insights[:max_items]:
        bg, border, label = level_styles.get(insight["level"], ("#f8fafc", "#94a3b8", "INFO"))
        st.markdown(f"""
        <div style="background:{bg};border-left:4px solid {border};border-radius:0 8px 8px 0;padding:8px 14px;margin:4px 0">
            <span style="color:{border};font-weight:700;font-size:0.8rem">{label}</span>
            <span style="color:#1e293b;font-size:0.85rem;margin-left:8px">{insight['text']}</span>
        </div>
        """, unsafe_allow_html=True)


def get_all_insights_structured() -> dict:
    """Get all insights organized by category and level for the consolidated page."""
    all_insights, summary, briefing = _cached_insights()

    result = {
        "all": all_insights,
        "summary": summary,
        "briefing": briefing,
        "by_level": {
            "critical": [i for i in all_insights if i["level"] == "critical"],
            "warning": [i for i in all_insights if i["level"] == "warning"],
            "positive": [i for i in all_insights if i["level"] == "positive"],
            "info": [i for i in all_insights if i["level"] == "info"],
        },
        "by_category": {},
        "counts": {
            "total": len(all_insights),
            "critical": len([i for i in all_insights if i["level"] == "critical"]),
            "warning": len([i for i in all_insights if i["level"] == "warning"]),
            "positive": len([i for i in all_insights if i["level"] == "positive"]),
            "info": len([i for i in all_insights if i["level"] == "info"]),
        }
    }

    # Group by category
    for i in all_insights:
        cat = i.get("category", "general")
        if cat not in result["by_category"]:
            result["by_category"][cat] = []
        result["by_category"][cat].append(i)

    return result

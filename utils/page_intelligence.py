"""
Page Intelligence — unified AI briefing at the top of each page.
Combines: Page Intelligence + AI Insights (merged into one section).
Includes: Descriptive, Predictive, Prescriptive analysis + Recommendations.
"""

import json
import hashlib
import streamlit as st

from utils.llm_client import call_llm, is_llm_available

SYSTEM_PROMPT = """You are the Chief Energy Intelligence Officer for a Myanmar conglomerate with 55 stores across Retail, F&B, Distribution, and Property sectors facing severe energy disruption.

Generate a comprehensive intelligence briefing with 4 types of analysis.

FORMAT your response as a JSON object:
{
  "headline": "One bold sentence — the single most important finding (max 15 words)",
  "severity": "critical" or "warning" or "normal",
  "descriptive": [
    {"title": "Short title", "detail": "What happened — specific numbers, comparisons vs last week/month", "severity": "critical|warning|normal"}
  ],
  "predictive": [
    {"title": "Short title", "detail": "What will likely happen next based on trends and patterns", "severity": "critical|warning|normal"}
  ],
  "prescriptive": [
    {"title": "Short title", "detail": "What to do RIGHT NOW — specific, actionable steps", "severity": "critical|warning|normal"}
  ],
  "recommendations": [
    {"title": "Short title", "detail": "Strategic recommendation for the next 7-30 days", "severity": "normal"}
  ],
  "bottom_line": "One sentence: the single most urgent action to take today (max 30 words)"
}

RULES:
- EXACTLY 2 items per analysis category (descriptive, predictive, prescriptive, recommendations) — no more
- NEVER just describe what the page shows. Analyze what the DATA reveals.
- Use specific numbers, week-over-week comparisons, anomaly detection
- Be direct, specific, data-driven. No corporate fluff.
- Currency is MMK (Myanmar Kyat)

Output ONLY the JSON object. No markdown, no code fences."""

PAGE_CONTEXT = {
    "ai_insights": "AI Insights Hub — consolidated view of all system-generated alerts and patterns",
    "sector": "Sector Dashboard — operational drill-down by sector, channel, and store",
    "holdings": "Holdings Control Tower — group-level KPIs, cross-sector comparison, strategic view",
    "diesel": "Diesel Intelligence — price forecasting, procurement timing, FX correlation",
    "blackout": "Blackout Monitor — grid outage prediction, township risk mapping, pattern analysis",
    "store_decisions": "Store Decisions — daily operating plan, FULL/REDUCED/CRITICAL/CLOSE modes",
    "solar": "Solar Performance — generation tracking, diesel offset, CAPEX prioritization",
    "alerts": "Alerts Center — all tier 1/2/3 alerts from 8 AI models",
    "scenario": "Scenario Simulator — what-if analysis for diesel price, blackouts, FX, solar expansion",
}

SECTION_CONFIG = {
    "descriptive": {"icon": "📊", "label": "What Happened", "color": "#3b82f6", "bg": "#eff6ff"},
    "predictive": {"icon": "🔮", "label": "What Will Happen", "color": "#8b5cf6", "bg": "#f5f3ff"},
    "prescriptive": {"icon": "🎯", "label": "What To Do Now", "color": "#ef4444", "bg": "#fef2f2"},
    "recommendations": {"icon": "💡", "label": "Strategic Recommendations", "color": "#f59e0b", "bg": "#fffbeb"},
}


def render_page_intelligence(page_id: str, data_summary: str = ""):
    """Render unified AI intelligence briefing at top of page.

    Uses DB persistence — only regenerates when underlying data changes.
    Flow: compute data hash → check DB → if match, display cached → else generate + save.
    """
    if not is_llm_available():
        # Show rule-based fallback instead of nothing
        st.markdown(f"""
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:16px 20px;margin-bottom:16px">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
                <span style="font-size:1.2rem">📊</span>
                <strong style="color:#1e293b">Data Summary</strong>
                <span style="background:#f1f5f9;color:#64748b;padding:2px 10px;border-radius:20px;font-size:0.75rem">Rule-based mode</span>
            </div>
            <p style="margin:0;font-size:0.9rem;color:#475569">{data_summary}</p>
            <p style="margin:8px 0 0;font-size:0.78rem;color:#94a3b8">
                AI insights disabled — set OPENROUTER_API_KEY in .env to enable Descriptive / Predictive / Prescriptive analysis
            </p>
        </div>
        """, unsafe_allow_html=True)
        return

    from utils.database import get_cached_page_intelligence, save_page_intelligence

    enriched = _enrich_summary(page_id, data_summary)
    data_hash = _compute_data_hash(page_id)

    # 1. Check DB cache — instant if data hasn't changed
    cached = get_cached_page_intelligence(page_id, data_hash)
    if cached and cached.get("briefing"):
        _render_briefing(cached["briefing"], cached.get("generated_at", ""))
        return

    # 2. Generate new intelligence (data changed or first run)
    with st.spinner("🧠 AI analyzing page data — new insights generating..."):
        briefing = _generate_intelligence(page_id, enriched)

    if not briefing:
        return

    # 3. Save to DB for persistence
    save_page_intelligence(page_id, data_hash, briefing)

    _render_briefing(briefing)


def _generate_intelligence(page_id: str, data_summary: str) -> dict:
    page_desc = PAGE_CONTEXT.get(page_id, page_id)
    prompt = f"""PAGE: {page_desc}
DATE: {_get_date()}

CURRENT DATA & HISTORICAL COMPARISONS:
{data_summary}

Generate the comprehensive intelligence briefing JSON."""

    try:
        response = call_llm(prompt, SYSTEM_PROMPT, max_tokens=3000, temperature=0.4)
        if not response:
            return {}
        result = _parse_json(response)
        if not isinstance(result, dict):
            return {}
        # Validate required fields exist
        if "headline" not in result:
            return {}
        # Validate all list fields contain proper dicts
        for key in ["descriptive", "predictive", "prescriptive", "recommendations"]:
            if key in result:
                result[key] = [i for i in result[key] if isinstance(i, dict) and i.get("title")]
        return result
    except Exception:
        return {}


def _render_briefing(b: dict, generated_at: str = ""):
    """Render the full intelligence briefing."""
    headline = b.get("headline", "")
    severity = b.get("severity", "normal")
    bottom_line = b.get("bottom_line", "")

    sev = {
        "critical": {"bg": "#fef2f2", "border": "#ef4444", "badge_bg": "#dc2626", "badge": "CRITICAL"},
        "warning": {"bg": "#fffbeb", "border": "#f59e0b", "badge_bg": "#d97706", "badge": "ATTENTION"},
        "normal": {"bg": "#f0fdf4", "border": "#22c55e", "badge_bg": "#16a34a", "badge": "STATUS OK"},
    }
    sc = sev.get(severity, sev["normal"])

    # ── Header with headline ──
    _html(f"""<div style="background:{sc['bg']};border:1px solid {sc['border']};border-radius:12px;
        padding:18px 22px;margin-bottom:16px">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
            <span style="font-size:1.1rem">🧠</span>
            <span style="background:{sc['badge_bg']};color:#fff;padding:3px 10px;border-radius:6px;
                font-size:0.7rem;font-weight:800;letter-spacing:0.5px">{sc['badge']}</span>
            <span style="font-size:0.72rem;color:#94a3b8">AI Page Intelligence</span>
            <span style="font-size:0.68rem;color:#94a3b8;margin-left:auto">{f'Generated: {generated_at}' if generated_at else 'Just generated'}</span>
        </div>
        <div style="font-size:1.15rem;font-weight:700;color:#0f172a;line-height:1.3">
            {_esc(headline)}
        </div>
    </div>""")

    # ── Action Bar (always visible) ──
    if bottom_line:
        _html(f"""<div style="background:#0f172a;color:#e2e8f0;padding:12px 16px;border-radius:8px;
            margin:8px 0 12px 0;font-size:0.85rem;display:flex;align-items:center;gap:8px">
            <span style="font-size:1rem">⚡</span>
            <strong>Action:</strong> {_esc(bottom_line)}
        </div>""")

    # ── 4 Analysis Sections (collapsible) ──
    sections = ["descriptive", "predictive", "prescriptive", "recommendations"]
    has_content = any(b.get(s) for s in sections)

    if has_content:
        with st.expander("📊 View Full Analysis (Descriptive · Predictive · Prescriptive · Recommendations)", expanded=False):
            col1, col2 = st.columns(2)
            for idx, section_key in enumerate(sections):
                items = b.get(section_key, [])
                if not items:
                    continue
                cfg = SECTION_CONFIG[section_key]
                target_col = col1 if idx % 2 == 0 else col2

                with target_col:
                    _html(f"""<div style="display:flex;align-items:center;gap:6px;margin:8px 0 6px 0">
                        <span style="font-size:0.95rem">{cfg['icon']}</span>
                        <span style="font-size:0.82rem;font-weight:700;color:{cfg['color']}">{cfg['label']}</span>
                    </div>""")

                    for item in items[:2]:
                        title = _esc(item.get("title", ""))
                        detail = _esc(item.get("detail", ""))
                        item_sev = item.get("severity", "normal")
                        dot = {"critical": "#ef4444", "warning": "#f59e0b", "normal": "#22c55e"}.get(item_sev, "#94a3b8")

                        _html(f"""<div style="background:{cfg['bg']};border-left:3px solid {cfg['color']};
                            border-radius:0 8px 8px 0;padding:10px 12px;margin:0 0 6px 0">
                            <div style="display:flex;align-items:center;gap:6px;margin-bottom:3px">
                                <span style="width:7px;height:7px;border-radius:50%;background:{dot};flex-shrink:0"></span>
                                <strong style="color:#0f172a;font-size:0.84rem">{title}</strong>
                            </div>
                            <div style="color:#475569;font-size:0.8rem;line-height:1.45">{detail}</div>
                        </div>""")


def _compute_data_hash(page_id: str) -> str:
    """Compute a hash of the actual underlying data.

    Changes when: new data uploaded, new CSV dates, data source toggled.
    Does NOT change on: page refresh, different user, server restart.
    """
    try:
        from utils.data_loader import load_daily_energy, load_diesel_prices
        energy = load_daily_energy()
        prices = load_diesel_prices()

        # Key data fingerprint: latest date + row count + latest price + latest energy stats
        fingerprint = (
            f"{page_id}:"
            f"date={energy['date'].max()}:"
            f"rows={len(energy)}:"
            f"price={prices['diesel_price_mmk'].iloc[-1]:.0f}:"
            f"bo={energy['blackout_hours'].iloc[-1]:.1f}:"
            f"cost={energy['diesel_cost_mmk'].sum():.0f}"
        )
        return hashlib.md5(fingerprint.encode()).hexdigest()
    except Exception:
        # Fallback: hash current date (regenerate daily at most)
        from datetime import date
        return hashlib.md5(f"{page_id}:{date.today()}".encode()).hexdigest()


def _html(content: str):
    try:
        st.markdown(content, unsafe_allow_html=True)
    except Exception:
        pass


def _esc(text: str) -> str:
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _enrich_summary(page_id: str, existing: str) -> str:
    try:
        from utils.data_loader import load_daily_energy, load_diesel_prices, load_stores
        import pandas as pd

        energy = load_daily_energy()
        stores = load_stores()
        latest = energy["date"].max()
        week_ago = latest - pd.Timedelta(days=7)
        two_weeks = latest - pd.Timedelta(days=14)

        this_week = energy[energy["date"] > week_ago]
        last_week = energy[(energy["date"] > two_weeks) & (energy["date"] <= week_ago)]
        parts = [existing]

        if len(this_week) > 0 and len(last_week) > 0:
            bo_now = this_week["blackout_hours"].mean()
            bo_prev = last_week["blackout_hours"].mean()
            bo_chg = ((bo_now - bo_prev) / bo_prev * 100) if bo_prev > 0 else 0
            parts.append(f"Blackout: {bo_now:.1f} hrs avg this week vs {bo_prev:.1f} last week ({bo_chg:+.1f}%).")

            cost_now = this_week["diesel_cost_mmk"].sum()
            cost_prev = last_week["diesel_cost_mmk"].sum()
            cost_chg = ((cost_now - cost_prev) / cost_prev * 100) if cost_prev > 0 else 0
            parts.append(f"Diesel cost: {cost_now/1e6:.1f}M MMK this week vs {cost_prev/1e6:.1f}M last week ({cost_chg:+.1f}%).")

            worst = this_week.groupby("store_id")["blackout_hours"].mean().nlargest(3)
            names = worst.reset_index().merge(stores[["store_id", "name"]], on="store_id")
            top3 = ", ".join(f"{r['name']} ({r['blackout_hours']:.1f}h)" for _, r in names.iterrows())
            parts.append(f"Worst blackout stores: {top3}.")

        try:
            prices = load_diesel_prices()
            p = prices["diesel_price_mmk"]
            parts.append(f"Diesel price: {int(p.iloc[-1]):,} MMK/L, 7d ago {int(p.iloc[-7]):,}, 30d range {int(p.tail(30).min()):,}-{int(p.tail(30).max()):,}.")
        except Exception:
            pass

        try:
            from utils.data_loader import load_diesel_inventory
            inv = load_diesel_inventory()
            lat = inv[inv["date"] == inv["date"].max()]
            crit = (lat["days_of_coverage"] < 1).sum()
            warn = ((lat["days_of_coverage"] >= 1) & (lat["days_of_coverage"] < 2)).sum()
            parts.append(f"Inventory: {crit} stores <1 day (critical), {warn} stores <2 days (warning).")
        except Exception:
            pass

        parts.append(f"Total: {len(stores)} stores, {int(stores['has_solar'].sum())} solar, {int(stores['cold_chain'].sum())} cold chain.")
        return " ".join(parts)
    except Exception:
        return existing


def _parse_json(text: str) -> dict:
    text = text.strip()
    if "```" in text:
        import re
        match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if match:
            text = match.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find('{')
        end = text.rfind('}')
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end+1])
            except json.JSONDecodeError:
                pass
    return {}


def _get_date() -> str:
    try:
        from utils.data_loader import load_daily_energy
        return str(load_daily_energy()["date"].max().date())
    except Exception:
        from datetime import date
        return str(date.today())

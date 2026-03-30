"""
Element Captions — AI-generated analytical insights for every chart, table, and card.
One LLM call per page. Insights compare periods, identify anomalies, and recommend actions.
"""

import json
import hashlib
import streamlit as st

from utils.llm_client import call_llm, is_llm_available

SYSTEM_PROMPT = """You are a senior energy intelligence analyst for a Myanmar conglomerate operating 55 stores across Retail, F&B, Distribution, and Property sectors facing severe energy disruption (frequent blackouts, volatile diesel prices, supply chain risk).

Your job: generate ANALYTICAL INSIGHTS — not descriptions — for dashboard elements.

CRITICAL RULES:
- NEVER just restate the number shown on the card/chart. The user can already see that.
- Instead: explain WHY it matters, HOW it compares to history, WHAT anomaly it reveals, and WHAT ACTION to take.
- Each insight must be 2-3 sentences with genuine analysis.
- Use comparative language: "up X% vs last week", "worst in 30 days", "3x the normal rate"
- Include a clear recommended action or warning.
- Assign a severity: "critical" (red), "warning" (orange), or "insight" (blue/green)

BAD example (just restating): "55 of 55 stores are high-risk."
GOOD example: "severity: critical | Every store is flagged high-risk — unprecedented in the last 90 days. This suggests a grid-wide failure, not localized outages. Activate all backup generators immediately and defer non-essential operations across all sectors."

BAD example: "Diesel price is 2,850 MMK/L."
GOOD example: "severity: warning | Price has climbed 8.2% in 7 days, fastest rise since January. If this trend holds, weekly diesel costs will exceed 45M MMK. Lock in bulk purchase now before crossing the 3,000 MMK threshold."

Output a JSON object mapping element_id to an object with "severity" and "text" fields:
{"element_id": {"severity": "critical|warning|insight", "text": "Your 2-3 sentence analytical insight"}}"""


def get_page_captions(page_id: str, elements: list, data_summary: str = "") -> dict:
    """Get AI insights for elements — non-blocking.

    Returns cached captions instantly from DB. If not cached, generates
    in the background and returns empty dict (captions appear on next page load).
    This ensures the dashboard renders immediately without waiting for LLM.
    """
    if not is_llm_available() or not elements:
        return {}

    from utils.database import get_cached_element_captions, save_element_captions

    data_hash = _compute_data_hash(page_id)

    # 1. Check DB cache — instant return
    cached = get_cached_element_captions(page_id, data_hash)
    if cached and cached.get("captions"):
        return cached["captions"]

    # 2. Not cached — skip for now, generate after page renders
    # Store elements info in session state so we can generate after render
    import streamlit as st
    st.session_state[f"_pending_captions_{page_id}"] = {
        "elements": elements, "data_summary": data_summary, "data_hash": data_hash
    }
    return {}


def generate_pending_captions():
    """Call at the END of a page to generate any pending captions in background.
    Captions will appear on next page load.
    """
    import streamlit as st
    from utils.database import save_element_captions

    pending_keys = [k for k in st.session_state if k.startswith("_pending_captions_")]
    if not pending_keys:
        return

    for key in pending_keys:
        info = st.session_state.pop(key)
        page_id = key.replace("_pending_captions_", "")
        with st.spinner(f"Generating element insights for next visit..."):
            try:
                enriched = _enrich_with_history(page_id, info["data_summary"])
                captions = _generate_captions_batch(page_id, info["elements"], enriched)
                if captions:
                    save_element_captions(page_id, info["data_hash"], captions)
            except Exception:
                pass


def _generate_captions_batch(page_id: str, elements: list, data_summary: str) -> dict:
    """Generate insights via one LLM call with rich context."""
    element_lines = []
    for el in elements:
        el_type = el.get("type", "metric")
        title = el.get("title", "")
        value = el.get("value", "")
        comparison = el.get("comparison", "")
        line = f"- {el['id']} ({el_type}): {title} = {value}"
        if comparison:
            line += f" | Historical: {comparison}"
        element_lines.append(line)

    prompt = f"""Page: {page_id} | Date: {_get_current_date()}

DASHBOARD ELEMENTS (provide analytical insight for each):
{chr(10).join(element_lines)}

HISTORICAL CONTEXT & COMPARISONS:
{data_summary}

Generate a JSON object with analytical insights. Remember: NEVER restate the number — analyze what it MEANS, compare to history, and recommend ACTION."""

    try:
        response = call_llm(prompt, SYSTEM_PROMPT, max_tokens=3000, temperature=0.4)
        if not response:
            return {}
        return _parse_json_response(response)
    except Exception:
        return {}


def render_caption(element_id: str, captions: dict):
    """Render a severity-colored analytical insight below a dashboard element."""
    caption = captions.get(element_id)
    if not caption:
        return

    # Handle both old format (string) and new format (dict with severity+text)
    if isinstance(caption, str):
        severity = "insight"
        text = caption
    elif isinstance(caption, dict):
        severity = caption.get("severity", "insight")
        text = caption.get("text", "")
    else:
        return

    if not text:
        return

    # Severity-based styling
    styles = {
        "critical": {
            "bg": "#fef2f2", "border": "#ef4444", "icon": "🔴",
            "label_bg": "#dc2626", "label_color": "#fff"
        },
        "warning": {
            "bg": "#fffbeb", "border": "#f59e0b", "icon": "🟡",
            "label_bg": "#d97706", "label_color": "#fff"
        },
        "insight": {
            "bg": "#eff6ff", "border": "#3b82f6", "icon": "🔵",
            "label_bg": "#2563eb", "label_color": "#fff"
        },
    }
    s = styles.get(severity, styles["insight"])

    st.markdown(f"""<div style="background:{s['bg']};border-left:4px solid {s['border']};
        border-radius:0 8px 8px 0;padding:10px 14px;margin:6px 0 14px 0;
        font-size:0.82rem;color:#1e293b;line-height:1.5">
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px">
            <span>{s['icon']}</span>
            <span style="background:{s['label_bg']};color:{s['label_color']};
                padding:1px 8px;border-radius:4px;font-size:0.7rem;font-weight:700;
                text-transform:uppercase">{severity}</span>
            <span style="font-size:0.7rem;color:#94a3b8;margin-left:auto">AI Insight</span>
        </div>
        <div>{text}</div>
    </div>""", unsafe_allow_html=True)


def _enrich_with_history(page_id: str, existing_summary: str) -> str:
    """Add historical comparison data to the summary for richer insights."""
    try:
        from utils.data_loader import load_daily_energy, load_diesel_prices, load_stores
        import pandas as pd

        energy = load_daily_energy()
        stores = load_stores()
        latest_date = energy["date"].max()
        week_ago = latest_date - pd.Timedelta(days=7)
        two_weeks_ago = latest_date - pd.Timedelta(days=14)
        month_ago = latest_date - pd.Timedelta(days=30)

        this_week = energy[energy["date"] > week_ago]
        last_week = energy[(energy["date"] > two_weeks_ago) & (energy["date"] <= week_ago)]
        last_month = energy[energy["date"] > month_ago]

        comparisons = [existing_summary]

        # Blackout comparisons
        if len(this_week) > 0 and len(last_week) > 0:
            bo_now = this_week["blackout_hours"].mean()
            bo_prev = last_week["blackout_hours"].mean()
            bo_change = ((bo_now - bo_prev) / bo_prev * 100) if bo_prev > 0 else 0
            comparisons.append(
                f"Blackout hours: This week avg {bo_now:.1f} hrs vs last week {bo_prev:.1f} hrs ({bo_change:+.1f}% change). "
                f"30-day avg: {last_month['blackout_hours'].mean():.1f} hrs."
            )

            # High blackout stores
            high_bo = this_week.groupby("store_id")["blackout_hours"].mean().nlargest(5)
            if len(high_bo) > 0:
                top_stores = high_bo.reset_index().merge(stores[["store_id", "name", "township"]], on="store_id")
                top_list = ", ".join(f"{r['name']} ({r['blackout_hours']:.1f}hrs)" for _, r in top_stores.iterrows())
                comparisons.append(f"Worst blackout stores this week: {top_list}")

        # Diesel cost comparisons
        if len(this_week) > 0 and len(last_week) > 0:
            diesel_now = this_week["diesel_cost_mmk"].sum()
            diesel_prev = last_week["diesel_cost_mmk"].sum()
            diesel_change = ((diesel_now - diesel_prev) / diesel_prev * 100) if diesel_prev > 0 else 0
            comparisons.append(
                f"Diesel cost: This week {diesel_now/1e6:.1f}M MMK vs last week {diesel_prev/1e6:.1f}M MMK ({diesel_change:+.1f}%)."
            )

        # Price trend
        try:
            prices = load_diesel_prices()
            if len(prices) >= 14:
                price_now = prices["diesel_price_mmk"].iloc[-1]
                price_7d = prices["diesel_price_mmk"].iloc[-7]
                price_30d = prices["diesel_price_mmk"].iloc[-30] if len(prices) >= 30 else prices["diesel_price_mmk"].iloc[0]
                comparisons.append(
                    f"Diesel price: {int(price_now):,} MMK/L (7d ago: {int(price_7d):,}, 30d ago: {int(price_30d):,}). "
                    f"30-day range: {int(prices.tail(30)['diesel_price_mmk'].min()):,}-{int(prices.tail(30)['diesel_price_mmk'].max()):,}."
                )
        except Exception:
            pass

        # Solar comparison
        solar_stores = stores[stores["has_solar"] == True]
        if len(solar_stores) > 0 and "solar_kwh" in this_week.columns:
            solar_now = this_week["solar_kwh"].sum()
            solar_prev = last_week["solar_kwh"].sum() if len(last_week) > 0 else 0
            if solar_prev > 0:
                solar_change = (solar_now - solar_prev) / solar_prev * 100
                comparisons.append(f"Solar generation: {solar_now:,.0f} kWh this week vs {solar_prev:,.0f} last week ({solar_change:+.1f}%).")

        # Inventory risk
        try:
            from utils.data_loader import load_diesel_inventory
            inv = load_diesel_inventory()
            latest_inv = inv[inv["date"] == inv["date"].max()]
            critical = (latest_inv["days_of_coverage"] < 1).sum()
            warning = ((latest_inv["days_of_coverage"] >= 1) & (latest_inv["days_of_coverage"] < 2)).sum()
            comparisons.append(f"Diesel inventory: {critical} stores critical (<1 day), {warning} stores warning (<2 days).")
        except Exception:
            pass

        return " ".join(comparisons)

    except Exception:
        return existing_summary


def _parse_json_response(text: str) -> dict:
    """Parse JSON from LLM response, handling both old and new formats."""
    text = text.strip()
    # Remove code fences
    if "```" in text:
        import re
        match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if match:
            text = match.group(1).strip()

    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # Try to find the largest JSON object
    import re
    # Match nested JSON objects
    brace_count = 0
    start = None
    for i, c in enumerate(text):
        if c == '{':
            if brace_count == 0:
                start = i
            brace_count += 1
        elif c == '}':
            brace_count -= 1
            if brace_count == 0 and start is not None:
                try:
                    result = json.loads(text[start:i+1])
                    if isinstance(result, dict):
                        return result
                except json.JSONDecodeError:
                    pass
                start = None

    return {}


def _compute_data_hash(page_id: str) -> str:
    """Hash of actual data — only changes when data changes."""
    try:
        from utils.data_loader import load_daily_energy, load_diesel_prices
        energy = load_daily_energy()
        prices = load_diesel_prices()
        fingerprint = (
            f"captions:{page_id}:"
            f"date={energy['date'].max()}:"
            f"rows={len(energy)}:"
            f"price={prices['diesel_price_mmk'].iloc[-1]:.0f}:"
            f"cost={energy['diesel_cost_mmk'].sum():.0f}"
        )
        return hashlib.md5(fingerprint.encode()).hexdigest()
    except Exception:
        from datetime import date
        return hashlib.md5(f"captions:{page_id}:{date.today()}".encode()).hexdigest()


def _get_current_date() -> str:
    try:
        from utils.data_loader import load_daily_energy
        energy = load_daily_energy()
        return str(energy["date"].max().date())
    except Exception:
        from datetime import date
        return str(date.today())

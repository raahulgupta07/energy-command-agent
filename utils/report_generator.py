"""
Report Generator — Packaged HTML reports for email distribution.
5 report types from BCP Framework document.
"""

from datetime import datetime
from config.settings import CURRENCY
from utils.email_alerts import format_weekly_report


def generate_daily_brief(plan_summary: dict, alert_counts: dict,
                          diesel_rec: dict, stockout_summary: dict,
                          solar_summary: dict, alerts: list = None) -> dict:
    """Generate Daily Energy Brief (H1). Returns dict with subject + html."""
    from utils.email_alerts import format_morning_briefing
    html = format_morning_briefing(plan_summary, alert_counts, diesel_rec,
                                    stockout_summary, solar_summary, alerts)
    date_str = datetime.now().strftime("%Y-%m-%d")
    return {
        "subject": f"EIS Daily Energy Brief — {date_str}",
        "html": html,
        "report_type": "daily_brief",
    }


def generate_weekly_ebitda_report(group_kpis: dict, sector_kpis=None,
                                   plan_summary: dict = None) -> dict:
    """Generate Weekly EBITDA Impact Report (H2). Monday AM."""
    sections = []

    # Group P&L impact
    ebitda_impact = group_kpis.get("total_ebitda_impact_mmk", 0)
    energy_cost = group_kpis.get("total_energy_cost_mmk", 0)
    sections.append({
        "heading": "Group P&L Impact from Energy Disruption",
        "content": f"""
        <div style="display:flex;gap:20px;text-align:center">
            <div style="flex:1"><div style="font-size:1.3rem;font-weight:700;color:#ef4444">{ebitda_impact:,.0f}</div><div style="font-size:0.75rem;color:#64748b">EBITDA Impact ({CURRENCY})</div></div>
            <div style="flex:1"><div style="font-size:1.3rem;font-weight:700;color:#f59e0b">{energy_cost:,.0f}</div><div style="font-size:0.75rem;color:#64748b">Total Energy Cost ({CURRENCY})</div></div>
            <div style="flex:1"><div style="font-size:1.3rem;font-weight:700;color:#3b82f6">{group_kpis.get('avg_eri_pct', 0):.0f}%</div><div style="font-size:0.75rem;color:#64748b">Energy Resilience Index</div></div>
        </div>
        """,
    })

    # Sector breakdown
    if sector_kpis is not None and hasattr(sector_kpis, 'iterrows'):
        rows = ""
        for _, s in sector_kpis.iterrows():
            rows += f"<tr><td style='padding:6px 10px'>{s.get('sector','')}</td><td style='padding:6px 10px;text-align:right'>{s.get('num_stores',0)}</td><td style='padding:6px 10px;text-align:right'>{s.get('total_energy_cost',0):,.0f}</td><td style='padding:6px 10px;text-align:right'>{s.get('energy_cost_pct',0):.1f}%</td></tr>"
        sections.append({
            "heading": "Sector Breakdown",
            "content": f"<table style='width:100%;border-collapse:collapse'><tr style='background:#f1f5f9'><th style='padding:6px 10px;text-align:left'>Sector</th><th style='padding:6px 10px;text-align:right'>Stores</th><th style='padding:6px 10px;text-align:right'>Energy Cost</th><th style='padding:6px 10px;text-align:right'>% of Sales</th></tr>{rows}</table>",
        })

    # Operating plan
    if plan_summary:
        sections.append({
            "heading": "Operating Mode Summary",
            "content": f"""
            FULL: {plan_summary.get('stores_full', 0)} | SELECTIVE: {plan_summary.get('stores_selective', 0)} |
            REDUCED: {plan_summary.get('stores_reduced', 0)} | CRITICAL: {plan_summary.get('stores_critical', 0)} |
            CLOSED: {plan_summary.get('stores_closed', 0)}<br>
            <strong>Stores losing money: {plan_summary.get('stores_losing_money', 0)}</strong>
            """,
        })

    date_str = datetime.now().strftime("%Y-%m-%d")
    return {
        "subject": f"EIS Weekly EBITDA Impact — Week ending {date_str}",
        "html": format_weekly_report("Weekly EBITDA Impact Report", sections),
        "report_type": "weekly_ebitda",
    }


def generate_weekly_risk_report(stockout_summary: dict, diesel_rec: dict,
                                 alert_counts: dict, group_kpis: dict) -> dict:
    """Generate Weekly Risk Dashboard (H3). Monday AM."""
    sections = [
        {
            "heading": "Diesel Coverage",
            "content": f"""
            Critical (< 1 day): <strong style="color:#ef4444">{stockout_summary.get('critical_stores', 0)}</strong> stores<br>
            High risk (< 2 days): <strong style="color:#f59e0b">{stockout_summary.get('high_risk_stores', 0)}</strong> stores<br>
            Avg coverage: <strong>{stockout_summary.get('avg_days_coverage', 0):.1f} days</strong><br>
            Total stock: {stockout_summary.get('total_diesel_stock', 0):,.0f} liters
            """,
        },
        {
            "heading": "Price Trend",
            "content": f"""
            Signal: <strong>{diesel_rec.get('signal', 'N/A')}</strong><br>
            {diesel_rec.get('reason', '')}
            """,
        },
        {
            "heading": "Alert Summary (This Week)",
            "content": f"""
            Critical: <strong style="color:#ef4444">{alert_counts.get('critical', 0)}</strong> |
            Warning: <strong style="color:#f59e0b">{alert_counts.get('warning', 0)}</strong> |
            Info: <strong>{alert_counts.get('info', 0)}</strong>
            """,
        },
        {
            "heading": "Network Resilience",
            "content": f"""
            Energy Resilience Index: <strong>{group_kpis.get('avg_eri_pct', 0):.0f}%</strong> (target: >85%)<br>
            Diesel dependency: <strong>{group_kpis.get('avg_diesel_dependency_pct', 0):.0f}%</strong>
            """,
        },
    ]

    date_str = datetime.now().strftime("%Y-%m-%d")
    return {
        "subject": f"EIS Weekly Risk Dashboard — {date_str}",
        "html": format_weekly_report("Weekly Risk Dashboard", sections),
        "report_type": "weekly_risk",
    }


def generate_monthly_resilience_report(group_kpis: dict, solar_summary: dict) -> dict:
    """Generate Monthly Resilience Report (H4). 1st working day."""
    sections = [
        {
            "heading": "Energy Resilience Index",
            "content": f"Group ERI: <strong>{group_kpis.get('avg_eri_pct', 0):.0f}%</strong> (target: >85%)",
        },
        {
            "heading": "Solar ROI",
            "content": f"""
            Solar sites: {solar_summary.get('total_solar_sites', 0)}<br>
            Daily diesel offset: {solar_summary.get('total_diesel_offset_liters', 0):,.0f} liters<br>
            Daily saving: {solar_summary.get('total_daily_saving_mmk', 0):,.0f} {CURRENCY}
            """,
        },
        {
            "heading": "Recommendations",
            "content": "See Scenario Simulator and Solar Performance dashboards for detailed CAPEX recommendations.",
        },
    ]

    date_str = datetime.now().strftime("%B %Y")
    return {
        "subject": f"EIS Monthly Resilience Report — {date_str}",
        "html": format_weekly_report("Monthly Resilience Report", sections),
        "report_type": "monthly_resilience",
    }


def generate_crisis_report(alert: dict, plan_summary: dict = None,
                            stockout_summary: dict = None) -> dict:
    """Generate Ad-hoc Crisis Report (H5). Triggered by RED alert."""
    from utils.email_alerts import format_critical_alert
    html = format_critical_alert(alert)

    return {
        "subject": f"🚨 EIS CRISIS ALERT — {alert.get('source', 'Energy System')}",
        "html": html,
        "report_type": "crisis",
    }

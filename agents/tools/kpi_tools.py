"""
KPI Tools — compute shared KPI formulas as agent tools.
"""

from agents.tools.registry import tool


@tool("get_energy_cost_pct",
      "Calculate energy cost as % of sales. Can group by store or sector.",
      {"type": "object", "properties": {
          "group_by": {"type": "string", "description": "Group by: store_id or sector (default: sector)"},
      }, "required": []})
def get_energy_cost_pct(group_by: str = "sector"):
    from utils.data_loader import load_daily_energy, load_store_sales, load_stores
    from utils.kpi_calculator import energy_cost_pct_of_sales
    energy = load_daily_energy()
    sales = load_store_sales()
    if group_by == "store_id":
        result = energy_cost_pct_of_sales(energy, sales, group_cols=["store_id"])
    else:
        stores = load_stores()
        energy = energy.merge(stores[["store_id", "sector"]], on="store_id", how="left")
        sales = sales.merge(stores[["store_id", "sector"]], on="store_id", how="left")
        result = energy_cost_pct_of_sales(energy, sales, group_cols=["sector"])
    return result.to_dict(orient="records")


@tool("get_diesel_cost_per_store",
      "Get average daily diesel cost per store.")
def get_diesel_cost_per_store():
    from utils.data_loader import load_daily_energy
    from utils.kpi_calculator import diesel_cost_per_store_per_day
    return diesel_cost_per_store_per_day(load_daily_energy()).to_dict(orient="records")


@tool("get_resilience_index",
      "Calculate Energy Resilience Index (ERI) — % of days profitable despite disruption.")
def get_resilience_index():
    from utils.data_loader import load_daily_energy, load_store_sales
    from utils.kpi_calculator import energy_resilience_index
    result = energy_resilience_index(load_daily_energy(), load_store_sales())
    return result.sort_values("eri_pct", ascending=False).to_dict(orient="records")


@tool("get_diesel_coverage_days",
      "Get days of diesel coverage per store based on current stock and consumption rate.")
def get_diesel_coverage_days():
    from utils.data_loader import load_diesel_inventory
    from utils.kpi_calculator import days_of_diesel_coverage
    return days_of_diesel_coverage(load_diesel_inventory()).to_dict(orient="records")


# ══════════════════════════════════════════════════════════════════════════════
# NEW KPI TOOLS (Phase 11)
# ══════════════════════════════════════════════════════════════════════════════

@tool("get_ebitda_per_hour",
      "Calculate EBITDA per operating hour for each store. Shows revenue, labour, energy cost per hour and whether store is profitable on generator.",
      {"type": "object", "properties": {
          "top_n": {"type": "integer", "description": "Return top/bottom N stores (default: all)"},
      }, "required": []})
def get_ebitda_per_hour(top_n: int = 0):
    from utils.data_loader import load_daily_energy, load_store_sales, load_stores
    from utils.kpi_calculator import ebitda_per_operating_hour
    result = ebitda_per_operating_hour(load_daily_energy(), load_store_sales(), load_stores())
    result = result.sort_values("ebitda_per_hr", ascending=False)
    if top_n > 0:
        return {"top": result.head(top_n).to_dict(orient="records"),
                "bottom": result.tail(top_n).to_dict(orient="records"),
                "total_stores": len(result),
                "profitable_on_generator": int(result["is_profitable_on_generator"].sum())}
    return result.to_dict(orient="records")


@tool("get_cold_chain_uptime",
      "Get cold chain uptime percentage per store. Target: >99.5%.")
def get_cold_chain_uptime():
    from utils.data_loader import load_temperature_logs
    from utils.kpi_calculator import cold_chain_uptime_pct
    temp = load_temperature_logs()
    result = cold_chain_uptime_pct(temp)
    if len(result) == 0:
        return {"error": "No temperature data available"}
    return {"stores": result.to_dict(orient="records"),
            "network_avg_uptime": round(result["uptime_pct"].mean(), 2),
            "critical_stores": int((result["status"] == "Critical").sum())}


@tool("get_data_quality_report",
      "Get data submission compliance report. Shows per-site completeness, late submissions, stores below 90%.")
def get_data_quality_report():
    from utils.database import get_compliance_summary
    return get_compliance_summary()


@tool("get_adoption_rate",
      "Get AI recommendation adoption rate. Shows how many AI decisions were accepted vs overridden by managers.",
      {"type": "object", "properties": {
          "rec_type": {"type": "string", "description": "Filter by recommendation type (e.g. operating_mode, bulk_purchase). Default: all."},
      }, "required": []})
def get_adoption_rate(rec_type: str = None):
    from utils.database import get_override_stats, get_adoption_rate as db_adoption
    override_stats = get_override_stats()
    adoption = db_adoption(rec_type) if rec_type else db_adoption()
    return {"override_stats": override_stats, "adoption": adoption}


@tool("send_alert_email",
      "Send an email alert via Outlook. Requires email to be configured in .env.",
      {"type": "object", "properties": {
          "subject": {"type": "string", "description": "Email subject line"},
          "message": {"type": "string", "description": "Alert message to include in email body"},
          "alert_type": {"type": "string", "description": "Type: critical, briefing, reminder"},
      }, "required": ["subject", "message"]})
def send_alert_email(subject: str, message: str, alert_type: str = "critical"):
    from utils.email_alerts import is_email_enabled, send_email, format_critical_alert
    if not is_email_enabled():
        return {"sent": False, "reason": "Email not configured. Set EIS_SMTP_USER and EIS_SMTP_PASSWORD in .env"}
    alert = {"source": "AI Agent", "message": message, "action": "Review and act",
             "store_name": "", "store_id": ""}
    html = format_critical_alert(alert)
    from config.settings import EMAIL_CONFIG
    recipients = EMAIL_CONFIG["recipients"].get("holdings_gecc", []) + EMAIL_CONFIG["recipients"].get("sector_leads", [])
    if not recipients:
        return {"sent": False, "reason": "No recipients configured in EMAIL_CONFIG"}
    success = send_email(recipients, subject, html)
    return {"sent": success, "recipients": len(recipients)}


@tool("log_decision_override",
      "Record a human override of an AI decision. Saves to decision_audit_log for tracking.",
      {"type": "object", "properties": {
          "store_id": {"type": "string", "description": "Store ID (e.g. RH-001)"},
          "ai_mode": {"type": "string", "description": "What AI recommended (FULL/SELECTIVE/REDUCED/CRITICAL/CLOSE)"},
          "final_mode": {"type": "string", "description": "What manager decided"},
          "decided_by": {"type": "string", "description": "Who made the decision"},
          "reason": {"type": "string", "description": "Why the override"},
      }, "required": ["store_id", "ai_mode", "final_mode", "decided_by", "reason"]})
def log_decision_override(store_id: str, ai_mode: str, final_mode: str,
                           decided_by: str, reason: str):
    from utils.database import save_decision_audit
    import pandas as pd
    save_decision_audit(store_id, store_id, pd.Timestamp.now().strftime("%Y-%m-%d"),
                        ai_mode, final_mode, decided_by, reason)
    return {"logged": True, "store_id": store_id, "ai_mode": ai_mode,
            "final_mode": final_mode, "overridden": ai_mode != final_mode}

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

"""
Data Query Tools — query stores, energy, prices, inventory.
"""

from agents.tools.registry import tool


@tool("query_stores",
      "Query store information. Filter by sector, township, or solar status.",
      {"type": "object", "properties": {
          "sector": {"type": "string", "description": "Filter by sector (Retail/F&B/Distribution/Property)"},
          "township": {"type": "string", "description": "Filter by township name"},
          "has_solar": {"type": "boolean", "description": "Filter by solar equipped"},
      }, "required": []})
def query_stores(sector: str = None, township: str = None, has_solar: bool = None):
    from utils.data_loader import load_stores
    df = load_stores()
    if sector:
        df = df[df["sector"] == sector]
    if township:
        df = df[df["township"].str.contains(township, case=False)]
    if has_solar is not None:
        df = df[df["has_solar"] == has_solar]
    return {"count": len(df), "stores": df.to_dict(orient="records")}


@tool("query_energy_data",
      "Query energy data for stores. Get blackout hours, diesel cost, solar kWh.",
      {"type": "object", "properties": {
          "store_id": {"type": "string", "description": "Filter by store ID"},
          "days": {"type": "integer", "description": "Last N days (default 7)"},
      }, "required": []})
def query_energy_data(store_id: str = None, days: int = 7):
    from utils.data_loader import load_daily_energy
    df = load_daily_energy()
    if store_id:
        df = df[df["store_id"] == store_id]
    df = df.sort_values("date")
    df = df.groupby("store_id").tail(days)
    summary = {
        "records": len(df),
        "avg_blackout_hours": round(df["blackout_hours"].mean(), 1),
        "total_diesel_cost": int(df["diesel_cost_mmk"].sum()),
        "avg_diesel_cost_per_day": int(df["diesel_cost_mmk"].mean()),
    }
    if "solar_kwh" in df.columns:
        summary["total_solar_kwh"] = round(df["solar_kwh"].sum(), 1)
    return summary


@tool("query_diesel_prices",
      "Get recent diesel price history with FX rates.",
      {"type": "object", "properties": {
          "days": {"type": "integer", "description": "Last N days (default 14)"},
      }, "required": []})
def query_diesel_prices(days: int = 14):
    from utils.data_loader import load_diesel_prices
    df = load_diesel_prices().tail(days)
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    return {
        "latest_price": int(latest["diesel_price_mmk"]),
        "previous_price": int(prev["diesel_price_mmk"]),
        "change_pct": round((latest["diesel_price_mmk"] - prev["diesel_price_mmk"]) / prev["diesel_price_mmk"] * 100, 1),
        "period_high": int(df["diesel_price_mmk"].max()),
        "period_low": int(df["diesel_price_mmk"].min()),
        "prices": df[["date", "diesel_price_mmk"]].to_dict(orient="records"),
    }


@tool("query_inventory",
      "Get diesel inventory snapshot. Filter by risk level.",
      {"type": "object", "properties": {
          "risk_level": {"type": "string", "description": "Filter: CRITICAL/HIGH/MEDIUM/LOW"},
      }, "required": []})
def query_inventory(risk_level: str = None):
    from utils.data_loader import load_diesel_inventory, load_stores
    inv = load_diesel_inventory()
    stores = load_stores()
    # Get latest per store
    latest = inv.sort_values("date").groupby("store_id").tail(1)
    latest = latest.merge(stores[["store_id", "name", "sector"]], on="store_id", how="left")
    if "days_of_coverage" in latest.columns:
        latest["risk"] = latest["days_of_coverage"].apply(
            lambda d: "CRITICAL" if d < 1 else "HIGH" if d < 2 else "MEDIUM" if d < 5 else "LOW")
        if risk_level:
            latest = latest[latest["risk"] == risk_level.upper()]
    return {
        "count": len(latest),
        "stores": latest[["store_id", "name", "sector", "diesel_stock_liters",
                          "days_of_coverage"]].to_dict(orient="records") if len(latest) > 0 else [],
    }


@tool("get_latest_metrics",
      "Get today's key metrics across the entire network.")
def get_latest_metrics():
    from utils.data_loader import load_stores, load_daily_energy, load_diesel_prices
    stores = load_stores()
    energy = load_daily_energy()
    prices = load_diesel_prices()
    latest_date = energy["date"].max()
    today = energy[energy["date"] == latest_date]
    return {
        "date": str(latest_date.date()) if hasattr(latest_date, 'date') else str(latest_date),
        "total_stores": len(stores),
        "diesel_price_mmk": int(prices["diesel_price_mmk"].iloc[-1]),
        "avg_blackout_hours": round(today["blackout_hours"].mean(), 1),
        "total_diesel_cost_today": int(today["diesel_cost_mmk"].sum()),
        "solar_sites": int(stores["has_solar"].sum()),
        "sectors": list(stores["sector"].unique()),
    }

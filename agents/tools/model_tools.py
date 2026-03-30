"""
Model Tools — wraps all 8 ML models as agent-callable tools.
"""

from agents.tools.registry import tool


def _load_data():
    """Load all datasets."""
    from utils.data_loader import (
        load_stores, load_daily_energy, load_diesel_prices,
        load_diesel_inventory, load_store_sales, load_solar_generation,
        load_temperature_logs, load_fx_rates
    )
    data = {"stores": load_stores(), "energy": load_daily_energy(),
            "prices": load_diesel_prices(), "inventory": load_diesel_inventory()}
    try:
        data["sales"] = load_store_sales()
    except Exception:
        data["sales"] = None
    try:
        data["solar"] = load_solar_generation()
    except Exception:
        data["solar"] = None
    try:
        data["temperature"] = load_temperature_logs()
    except Exception:
        data["temperature"] = None
    try:
        data["fx"] = load_fx_rates()
    except Exception:
        data["fx"] = None
    return data


# ── M1: Diesel Price Forecast ─────────────────────────────────────────────

@tool("forecast_diesel_price",
      "Run 7-day diesel price forecast. Returns predicted prices and BUY/HOLD signal.",
      {"type": "object", "properties": {
          "days": {"type": "integer", "description": "Forecast days (1-30, default 7)"}
      }, "required": []})
def forecast_diesel_price(days: int = 7):
    from models.diesel_price_forecast import DieselPriceForecast
    data = _load_data()
    m = DieselPriceForecast()
    m.fit(data["prices"])
    fc = m.predict(days=min(days, 30))
    return {
        "forecast": fc.to_dict(orient="records"),
        "volatility": m.get_volatility_index(),
        "recommendation": m.get_buy_recommendation(fc),
    }


# ── M2: Blackout Prediction ──────────────────────────────────────────────

@tool("predict_blackouts",
      "Predict blackout probability per store for tomorrow. Returns risk level, expected duration, likely window.")
def predict_blackouts():
    from models.blackout_prediction import BlackoutPredictor
    data = _load_data()
    m = BlackoutPredictor()
    m.fit(data["energy"], data["stores"])
    preds = m.predict_next_day(data["energy"], data["stores"])
    alerts = m.get_alerts(preds)
    high = preds[preds["risk_level"] == "HIGH"] if "risk_level" in preds.columns else []
    return {
        "high_risk_count": len(high),
        "predictions": preds.to_dict(orient="records"),
        "township_risk": m.get_township_risk_map(preds).to_dict(orient="records"),
        "alerts_count": len(alerts),
    }


# ── M3: Store Decision Engine ────────────────────────────────────────────

@tool("generate_store_plan",
      "Generate Daily Operating Plan — assigns FULL/REDUCED/CRITICAL/CLOSE mode per store.")
def generate_store_plan():
    from models.store_decision_engine import StoreDecisionEngine
    data = _load_data()
    engine = StoreDecisionEngine()
    plan = engine.generate_daily_plan(
        data["stores"], data["energy"], data["sales"],
        data["inventory"], solar_df=data["solar"])
    summary = engine.get_summary()
    alerts = engine.get_alerts()
    return {
        "summary": summary,
        "plan": plan[["store_id", "name", "sector", "mode", "reason",
                       "estimated_daily_profit"]].to_dict(orient="records"),
        "alerts": [{"tier": a["tier"], "message": a["message"]} for a in alerts],
    }


# ── M4: Diesel Optimizer ─────────────────────────────────────────────────

@tool("analyze_diesel_efficiency",
      "Analyze generator fuel efficiency. Detects waste via anomaly detection.")
def analyze_diesel_efficiency():
    from models.diesel_optimizer import DieselOptimizer
    data = _load_data()
    m = DieselOptimizer()
    m.fit(data["energy"], data["stores"])
    results = m.analyze()
    alerts = m.get_alerts()
    return {
        "results": results.to_dict(orient="records") if results is not None else [],
        "alerts": [{"tier": a["tier"], "message": a["message"]} for a in alerts],
    }


# ── M5: Solar Optimizer ──────────────────────────────────────────────────

@tool("optimize_solar_mix",
      "Optimize energy mix (solar/grid/diesel). Returns diesel offset, savings, CAPEX priority.")
def optimize_solar_mix():
    from models.solar_optimizer import SolarOptimizer
    data = _load_data()
    price = int(data["prices"]["diesel_price_mmk"].iloc[-1])
    m = SolarOptimizer()
    results = m.optimize_all(data["stores"], data["solar"], data["energy"], price)
    return {
        "network_summary": m.get_network_summary(),
        "site_results": results.to_dict(orient="records") if results is not None else [],
        "capex_priority": m.get_capex_priority().to_dict(orient="records") if m.get_capex_priority() is not None else [],
    }


# ── M6: Stockout Alert ───────────────────────────────────────────────────

@tool("check_stockout_risk",
      "Analyze diesel stockout risk. Returns days of coverage, risk level, reallocation plan.")
def check_stockout_risk():
    from models.stockout_alert import StockoutAlert
    data = _load_data()
    m = StockoutAlert()
    analysis = m.analyze(data["inventory"], data["energy"], data["stores"])
    return {
        "summary": m.get_summary(),
        "risk_by_store": analysis.to_dict(orient="records"),
        "reallocation_plan": m.get_reallocation_plan(),
        "alerts": [{"tier": a["tier"], "message": a["message"]} for a in m.get_alerts()],
    }


# ── M7: Spoilage Predictor ───────────────────────────────────────────────

@tool("predict_spoilage_risk",
      "Predict food spoilage risk for cold-chain stores. Returns risk per zone (Dairy/Frozen/Fresh).")
def predict_spoilage_risk():
    from models.spoilage_predictor import SpoilagePredictor
    data = _load_data()
    if data["temperature"] is None:
        return {"error": "No temperature data available"}
    m = SpoilagePredictor()
    m.fit(data["temperature"], data["energy"])
    risk = m.predict_risk(data["stores"])
    return {
        "risk": risk.to_dict(orient="records") if risk is not None else [],
        "alerts": [{"tier": a["tier"], "message": a["message"]} for a in m.get_alerts()],
    }


# ── M8: Holdings Aggregator ──────────────────────────────────────────────

@tool("compute_holdings_kpis",
      "Compute group-level KPIs: energy cost %, EBITDA impact, ERI, diesel dependency (27 KPIs).")
def compute_holdings_kpis():
    from models.holdings_aggregator import HoldingsAggregator
    data = _load_data()
    m = HoldingsAggregator()
    group = m.compute_group_kpis(data["stores"], data["energy"], data["sales"], data["inventory"])
    sector = m.compute_sector_kpis(data["stores"], data["energy"], data["sales"])
    return {
        "group_kpis": group,
        "sector_kpis": sector.to_dict(orient="records") if sector is not None else [],
    }


@tool("simulate_scenario",
      "Run what-if scenario. Adjust diesel price, blackouts, FX, solar to see impact.",
      {"type": "object", "properties": {
          "diesel_pct": {"type": "number", "description": "% diesel price change"},
          "blackout_pct": {"type": "number", "description": "% blackout hours change"},
          "fx_pct": {"type": "number", "description": "% FX rate change"},
          "solar_sites": {"type": "integer", "description": "New solar sites (0-20)"},
      }, "required": []})
def simulate_scenario(diesel_pct: float = 0, blackout_pct: float = 0,
                      fx_pct: float = 0, solar_sites: int = 0):
    from models.holdings_aggregator import HoldingsAggregator
    data = _load_data()
    m = HoldingsAggregator()
    m.compute_group_kpis(data["stores"], data["energy"], data["sales"], data["inventory"])
    return m.simulate_scenario(
        data["stores"], data["energy"], data["sales"], data["inventory"],
        diesel_price_change_pct=diesel_pct, blackout_hours_change_pct=blackout_pct,
        fx_change_pct=fx_pct, solar_new_sites=solar_sites)


# ── Run All Models ────────────────────────────────────────────────────────

@tool("run_all_models",
      "Run all 8 AI models. Returns alert counts, plan summary, and morning briefing.")
def run_all_models():
    from alerts.alert_engine import AlertEngine
    e = AlertEngine()
    e.load_data()
    e.run_all_models()
    counts = e.get_alert_counts()
    alerts = e.get_alerts()
    briefing = e.get_morning_briefing()
    return {
        "alert_counts": counts,
        "top_alerts": [{"tier": a["tier"], "source": a["source"],
                        "message": a["message"]} for a in alerts[:15]],
        "briefing_preview": briefing[:2000] if briefing else "",
    }

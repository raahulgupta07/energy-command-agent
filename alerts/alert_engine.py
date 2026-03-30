"""
Consolidated Alert Engine
Runs all AI models, collects alerts, deduplicates, and provides unified output.

Usage:
    from alerts.alert_engine import AlertEngine
    engine = AlertEngine()
    engine.load_data()
    engine.run_all_models()
    alerts = engine.get_alerts()  # All alerts, sorted by tier
    briefing = engine.get_morning_briefing()  # Daily summary
"""

import pandas as pd
from datetime import datetime
from typing import Optional

from utils.data_loader import (
    load_stores, load_daily_energy, load_store_sales,
    load_diesel_inventory, load_diesel_prices, load_solar_generation, load_temperature_logs,
)
from models.diesel_price_forecast import DieselPriceForecast
from models.blackout_prediction import BlackoutPredictor
from models.store_decision_engine import StoreDecisionEngine
from models.diesel_optimizer import DieselOptimizer
from models.solar_optimizer import SolarOptimizer
from models.stockout_alert import StockoutAlert
from models.spoilage_predictor import SpoilagePredictor
from models.holdings_aggregator import HoldingsAggregator
from config.settings import CURRENCY


class AlertEngine:
    """Centralized alert system that orchestrates all AI models."""

    def __init__(self):
        self.data = {}
        self.alerts = []
        self.models = {}
        self.results = {}
        self.run_timestamp = None

    def load_data(self):
        """Load all data sources."""
        self.data = {
            "stores": load_stores(),
            "energy": load_daily_energy(),
            "sales": load_store_sales(),
            "inventory": load_diesel_inventory(),
            "prices": load_diesel_prices(),
            "solar": load_solar_generation(),
            "temp": load_temperature_logs(),
        }
        return self

    def run_all_models(self):
        """Execute all AI models and collect alerts."""
        self.alerts = []
        self.run_timestamp = datetime.now()

        self._run_diesel_price_forecast()
        self._run_blackout_prediction()
        self._run_store_decisions()
        self._run_diesel_optimizer()
        self._run_solar_optimizer()
        self._run_stockout_alert()
        self._run_spoilage_predictor()
        self._run_holdings_aggregator()

        # Deduplicate by message
        seen = set()
        unique = []
        for a in self.alerts:
            key = a.get("message", "")
            if key not in seen:
                seen.add(key)
                unique.append(a)
        self.alerts = sorted(unique, key=lambda x: x.get("tier", 3))

        return self

    def _run_diesel_price_forecast(self):
        """M1: Diesel price forecast and buy/hold signal."""
        model = DieselPriceForecast()
        model.fit(self.data["prices"])
        forecast = model.predict(7)
        recommendation = model.get_buy_recommendation(forecast)
        volatility = model.get_volatility_index()

        self.models["diesel_price"] = model
        self.results["diesel_forecast"] = forecast
        self.results["diesel_recommendation"] = recommendation
        self.results["diesel_volatility"] = volatility

        if recommendation["signal"] in ["BUY NOW", "BUY"]:
            self.alerts.append({
                "tier": 1 if recommendation["signal"] == "BUY NOW" else 2,
                "source": "Diesel Price Forecast",
                "type": "PRICE_ALERT",
                "message": f"Diesel {recommendation['signal']}: {recommendation['reason']}",
                "action": recommendation["recommended_action"],
                "timestamp": self.run_timestamp,
            })

    def _run_blackout_prediction(self):
        """M2: Blackout probability prediction."""
        model = BlackoutPredictor()
        model.fit(self.data["energy"], self.data["stores"])
        predictions = model.predict_next_day(self.data["energy"], self.data["stores"])

        self.models["blackout"] = model
        self.results["blackout_predictions"] = predictions

        for alert in model.get_alerts(predictions):
            alert["source"] = "Blackout Prediction"
            alert["action"] = "Pre-adjust operations, prepare generators"
            alert["timestamp"] = self.run_timestamp
            self.alerts.append(alert)

    def _run_store_decisions(self):
        """M3: Store operating decision engine."""
        model = StoreDecisionEngine()
        blackout_preds = self.results.get("blackout_predictions")

        plan = model.generate_daily_plan(
            self.data["stores"], self.data["energy"], self.data["sales"],
            self.data["inventory"], blackout_predictions=blackout_preds,
            solar_df=self.data["solar"],
        )

        self.models["store_decisions"] = model
        self.results["daily_plan"] = plan
        self.results["plan_summary"] = model.get_summary()
        self.results["sector_summary"] = model.get_sector_summary()

        for alert in model.get_alerts():
            alert["source"] = "Store Decision Engine"
            alert["action"] = "Execute operating plan"
            alert["timestamp"] = self.run_timestamp
            self.alerts.append(alert)

    def _run_diesel_optimizer(self):
        """M4: Diesel consumption optimization."""
        model = DieselOptimizer()
        model.fit(self.data["energy"], self.data["stores"])
        analysis = model.analyze(self.data["energy"], self.data["stores"])

        self.models["diesel_optimizer"] = model
        self.results["efficiency_analysis"] = analysis

        for alert in model.get_alerts(analysis):
            alert["source"] = "Diesel Optimizer"
            alert["action"] = "Schedule generator maintenance"
            alert["timestamp"] = self.run_timestamp
            self.alerts.append(alert)

    def _run_solar_optimizer(self):
        """M5: Solar + diesel energy mix optimization."""
        model = SolarOptimizer()
        current_price = self.data["prices"]["diesel_price_mmk"].iloc[-1]
        results = model.optimize_all(
            self.data["stores"], self.data["solar"], self.data["energy"], current_price
        )

        self.models["solar_optimizer"] = model
        self.results["solar_optimization"] = results
        self.results["solar_summary"] = model.get_network_summary()

    def _run_stockout_alert(self):
        """M6: Diesel stock-out risk."""
        model = StockoutAlert()
        analysis = model.analyze(self.data["inventory"], self.data["energy"], self.data["stores"])

        self.models["stockout"] = model
        self.results["stockout_analysis"] = analysis
        self.results["stockout_summary"] = model.get_summary()
        self.results["reallocation_plan"] = model.get_reallocation_plan()

        for alert in model.get_alerts():
            alert["source"] = "Stock-Out Alert"
            alert["action"] = "Order diesel or reallocate"
            alert["timestamp"] = self.run_timestamp
            self.alerts.append(alert)

    def _run_spoilage_predictor(self):
        """M7: Cold chain spoilage prediction."""
        model = SpoilagePredictor()
        model.fit(self.data["temp"], self.data["energy"])
        risk = model.predict_risk(self.data["stores"], self.data["energy"], self.data["temp"])

        self.models["spoilage"] = model
        self.results["spoilage_risk"] = risk

        for alert in model.get_alerts(risk):
            alert["source"] = "Spoilage Predictor"
            alert["action"] = "Transfer or secure perishable stock"
            alert["timestamp"] = self.run_timestamp
            self.alerts.append(alert)

    def _run_holdings_aggregator(self):
        """M8: Holdings-level aggregation."""
        model = HoldingsAggregator()
        group_kpis = model.compute_group_kpis(
            self.data["stores"], self.data["energy"], self.data["sales"], self.data["inventory"]
        )
        sector_kpis = model.compute_sector_kpis(
            self.data["stores"], self.data["energy"], self.data["sales"]
        )

        self.models["holdings"] = model
        self.results["group_kpis"] = group_kpis
        self.results["sector_kpis"] = sector_kpis

    # ── Output Methods ──

    def get_alerts(self, tier: Optional[int] = None) -> list:
        """Get alerts, optionally filtered by tier."""
        if tier is not None:
            return [a for a in self.alerts if a.get("tier") == tier]
        return self.alerts

    def get_alert_counts(self) -> dict:
        """Get alert count by tier."""
        return {
            "total": len(self.alerts),
            "critical": len([a for a in self.alerts if a.get("tier") == 1]),
            "warning": len([a for a in self.alerts if a.get("tier") == 2]),
            "info": len([a for a in self.alerts if a.get("tier") == 3]),
        }

    def get_morning_briefing(self) -> str:
        """Generate a text-based morning briefing for operators."""
        counts = self.get_alert_counts()
        plan = self.results.get("plan_summary", {})
        rec = self.results.get("diesel_recommendation", {})
        stockout = self.results.get("stockout_summary", {})
        solar = self.results.get("solar_summary", {})

        lines = [
            "=" * 60,
            "ENERGY INTELLIGENCE SYSTEM — MORNING BRIEFING",
            f"Generated: {self.run_timestamp.strftime('%Y-%m-%d %H:%M') if self.run_timestamp else 'N/A'}",
            "=" * 60,
            "",
            "ALERTS SUMMARY",
            f"  Critical (Tier 1): {counts['critical']}",
            f"  Warning  (Tier 2): {counts['warning']}",
            f"  Info     (Tier 3): {counts['info']}",
            "",
            "DAILY OPERATING PLAN",
            f"  Stores FULL:     {plan.get('stores_full', 'N/A')}",
            f"  Stores REDUCED:  {plan.get('stores_reduced', 'N/A')}",
            f"  Stores CRITICAL: {plan.get('stores_critical', 'N/A')}",
            f"  Stores CLOSED:   {plan.get('stores_closed', 'N/A')}",
            f"  Est. Daily Profit: {plan.get('total_estimated_profit', 0):,.0f} {CURRENCY}",
            "",
            "DIESEL PROCUREMENT",
            f"  Signal: {rec.get('signal', 'N/A')}",
            f"  Reason: {rec.get('reason', 'N/A')}",
            f"  Action: {rec.get('recommended_action', 'N/A')}",
            "",
            "DIESEL INVENTORY",
            f"  Critical stores (< 1 day):  {stockout.get('critical_stores', 0)}",
            f"  High risk stores (< 2 days): {stockout.get('high_risk_stores', 0)}",
            f"  Avg days coverage: {stockout.get('avg_days_coverage', 0):.1f}",
            "",
            "SOLAR NETWORK",
            f"  Active solar sites: {solar.get('total_solar_sites', 0)}",
            f"  Daily diesel offset: {solar.get('total_diesel_offset_liters', 0):,.0f} liters",
            f"  Daily savings: {solar.get('total_daily_saving_mmk', 0):,.0f} {CURRENCY}",
            "",
        ]

        # Critical alerts detail
        critical = self.get_alerts(tier=1)
        if critical:
            lines.append("CRITICAL ALERTS (ACT NOW)")
            lines.append("-" * 40)
            for a in critical:
                lines.append(f"  [{a.get('source')}] {a['message']}")
                lines.append(f"  Action: {a.get('action', 'Review immediately')}")
                lines.append("")

        # Warning alerts
        warnings = self.get_alerts(tier=2)
        if warnings:
            lines.append("WARNING ALERTS (ACT TODAY)")
            lines.append("-" * 40)
            for a in warnings[:10]:  # Limit to top 10
                lines.append(f"  [{a.get('source')}] {a['message']}")
            if len(warnings) > 10:
                lines.append(f"  ... and {len(warnings) - 10} more")
            lines.append("")

        # AI Insights Summary
        try:
            from utils.insight_engine import InsightEngine
            fx_data = self.data.get("fx_rates")
            ie = InsightEngine(
                self.data["stores"], self.data["energy"], self.data["sales"],
                self.data["inventory"], self.data["prices"], fx_data
            )
            ie.generate_all(lookback_days=7)
            briefing_text = ie.get_briefing_paragraph()
            lines.append("")
            lines.append(briefing_text)
            lines.append("")

            # Try LLM executive summary
            exec_summary = ie.get_llm_executive_summary(self.results.get("group_kpis"))
            if exec_summary and exec_summary != ie.get_summary_text():
                lines.append("AI EXECUTIVE SUMMARY (LLM)")
                lines.append("=" * 40)
                lines.append(exec_summary)
                lines.append("")
        except Exception:
            pass

        lines.append("=" * 60)
        lines.append("END OF BRIEFING")
        lines.append("=" * 60)

        return "\n".join(lines)

    def get_reallocation_plan(self) -> list:
        """Get diesel reallocation recommendations."""
        return self.results.get("reallocation_plan", [])

    def run_agent_orchestrated(self) -> str:
        """Use the Briefing Agent to produce an AI-driven morning briefing.

        Falls back to standard get_morning_briefing() if agent unavailable.
        """
        try:
            from agents.config import is_agent_mode_available
            if is_agent_mode_available():
                from agents.briefing_agent import BriefingAgent
                agent = BriefingAgent()
                return agent.generate_briefing()
        except Exception:
            pass
        # Fallback
        self.load_data()
        self.run_all_models()
        return self.get_morning_briefing()


# ── CLI Entry Point ──
if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    print("Starting Energy Intelligence System...")
    engine = AlertEngine()

    print("Loading data...")
    engine.load_data()

    print("Running all AI models...")
    engine.run_all_models()

    # Print morning briefing
    print("\n" + engine.get_morning_briefing())

    # Print reallocation plan if any
    realloc = engine.get_reallocation_plan()
    if realloc:
        print("\nDIESEL REALLOCATION PLAN")
        print("-" * 40)
        for r in realloc:
            print(f"  {r['from_store']} → {r['to_store']}: {r['transfer_liters']:.0f}L ({r['priority']})")

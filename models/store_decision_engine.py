"""
Model 3: Store Operating Decision Engine (HIGHEST IMPACT)
Rule-based optimization that decides store operating mode.

Outputs per store:
- Mode: FULL / REDUCED / CRITICAL / CLOSE
- Reason for decision
- Profit per operating hour under current conditions
- Daily Operating Plan (auto-generated morning briefing)
"""

import pandas as pd
import numpy as np
from config.settings import THRESHOLDS, OPERATING_MODES, DIESEL


class StoreDecisionEngine:
    """Determine optimal operating mode for each store based on energy economics."""

    def __init__(self):
        self.decisions = None

    def generate_daily_plan(self, stores_df: pd.DataFrame, energy_df: pd.DataFrame,
                             sales_df: pd.DataFrame, inventory_df: pd.DataFrame,
                             blackout_predictions: pd.DataFrame = None,
                             solar_df: pd.DataFrame = None,
                             target_date=None) -> pd.DataFrame:
        """Generate the Daily Operating Plan for all stores.

        Args:
            stores_df: store master
            energy_df: daily energy data
            sales_df: hourly sales data
            inventory_df: diesel inventory data
            blackout_predictions: output from BlackoutPredictor (optional)
            solar_df: solar generation data (optional)
            target_date: date to plan for (defaults to latest + 1)

        Returns:
            DataFrame: store-level decisions with mode, reason, economics
        """
        if target_date is None:
            target_date = energy_df["date"].max()

        decisions = []

        for _, store in stores_df.iterrows():
            decision = self._decide_store(
                store, energy_df, sales_df, inventory_df,
                blackout_predictions, solar_df, target_date
            )
            decisions.append(decision)

        self.decisions = pd.DataFrame(decisions)

        # Sort: CLOSE first (most urgent), then CRITICAL, REDUCED, FULL
        mode_order = {"CLOSE": 0, "CRITICAL": 1, "REDUCED": 2, "FULL": 3}
        self.decisions["_sort"] = self.decisions["mode"].map(mode_order)
        self.decisions = self.decisions.sort_values("_sort").drop(columns="_sort")

        return self.decisions

    def _decide_store(self, store, energy_df, sales_df, inventory_df,
                       blackout_predictions, solar_df, target_date) -> dict:
        """Decision logic for a single store."""
        sid = store["store_id"]

        # ── Gather store metrics ──
        # Recent energy data (last 7 days average)
        recent_energy = energy_df[
            (energy_df["store_id"] == sid) &
            (energy_df["date"] >= target_date - pd.Timedelta(days=7))
        ]
        avg_diesel_cost = recent_energy["diesel_cost_mmk"].mean() if len(recent_energy) > 0 else 0
        avg_blackout = recent_energy["blackout_hours"].mean() if len(recent_energy) > 0 else 0

        # Recent sales (average daily)
        recent_sales = sales_df[
            (sales_df["store_id"] == sid) &
            (sales_df["date"] >= target_date - pd.Timedelta(days=7))
        ]
        avg_daily_sales = recent_sales.groupby("date")["sales_mmk"].sum().mean() if len(recent_sales) > 0 else 0
        avg_daily_margin = recent_sales.groupby("date")["gross_margin_mmk"].sum().mean() if len(recent_sales) > 0 else 0
        avg_hourly_margin = recent_sales["gross_margin_mmk"].mean() if len(recent_sales) > 0 else 0

        # Diesel inventory
        latest_inv = inventory_df[
            (inventory_df["store_id"] == sid) &
            (inventory_df["date"] == inventory_df["date"].max())
        ]
        diesel_days = latest_inv["days_of_coverage"].values[0] if len(latest_inv) > 0 else 5
        diesel_stock = latest_inv["diesel_stock_liters"].values[0] if len(latest_inv) > 0 else 100

        # Blackout probability (if available)
        blackout_prob = 0.5  # default
        if blackout_predictions is not None and len(blackout_predictions) > 0:
            bp = blackout_predictions[blackout_predictions["store_id"] == sid]
            if len(bp) > 0:
                blackout_prob = bp["blackout_probability"].values[0]

        # Solar availability
        has_solar = store["has_solar"]
        solar_kwh_avg = 0
        if has_solar and solar_df is not None:
            recent_solar = solar_df[
                (solar_df["store_id"] == sid) &
                (solar_df["date"] >= target_date - pd.Timedelta(days=7))
            ]
            solar_kwh_avg = recent_solar.groupby("date")["solar_kwh"].sum().mean() if len(recent_solar) > 0 else 0

        # ── Diesel cost per operating hour ──
        operating_hours = max(1, 16 - avg_blackout)  # Hours on grid
        generator_hours = avg_blackout  # Hours on generator
        diesel_cost_per_hour = avg_diesel_cost / max(generator_hours, 1) if generator_hours > 0 else 0

        # ── Margin per hour ──
        margin_per_hour = avg_hourly_margin

        # ── Cost-to-margin ratio ──
        cost_margin_ratio = diesel_cost_per_hour / max(margin_per_hour, 1) if margin_per_hour > 0 else 999

        # ── DECISION LOGIC ──

        mode = "FULL"
        reason = ""
        priority_score = 0  # Higher = more urgent

        # Rule 1: Diesel critically low → CLOSE
        if diesel_days < THRESHOLDS["diesel_critical_days"]:
            mode = "CLOSE"
            reason = f"Diesel stock critical: {diesel_days:.1f} days remaining"
            priority_score = 100

        # Rule 2: Generator cost exceeds margin AND diesel low → CLOSE
        elif cost_margin_ratio > THRESHOLDS["margin_breakeven_ratio"] and diesel_days < THRESHOLDS["diesel_warning_days"]:
            mode = "CLOSE"
            reason = f"Negative margin (ratio: {cost_margin_ratio:.2f}) + low diesel ({diesel_days:.1f} days)"
            priority_score = 90

        # Rule 3: Generator cost exceeds margin → REDUCED
        elif cost_margin_ratio > THRESHOLDS["margin_breakeven_ratio"]:
            mode = "REDUCED"
            reason = f"Diesel cost exceeds margin (ratio: {cost_margin_ratio:.2f})"
            priority_score = 60

        # Rule 4: High blackout probability + low diesel → CRITICAL
        elif blackout_prob >= THRESHOLDS["blackout_high_prob"] and diesel_days < THRESHOLDS["diesel_warning_days"]:
            mode = "CRITICAL"
            reason = f"High blackout risk ({blackout_prob*100:.0f}%) + low diesel ({diesel_days:.1f} days)"
            priority_score = 70

        # Rule 5: High blackout + cost approaching margin → REDUCED
        elif blackout_prob >= THRESHOLDS["blackout_high_prob"] and cost_margin_ratio > THRESHOLDS["margin_reduce_ratio"]:
            mode = "REDUCED"
            reason = f"High blackout risk ({blackout_prob*100:.0f}%) + tight margins"
            priority_score = 50

        # Rule 6: Solar available during peak → FULL (solar priority)
        elif has_solar and solar_kwh_avg > 0:
            mode = "FULL"
            reason = f"Solar available ({solar_kwh_avg:.0f} kWh/day avg) — prioritize solar hours"
            priority_score = 10

        # Rule 7: Default — profitable
        else:
            mode = "FULL"
            reason = "Profitable operations, normal mode"
            priority_score = 0

        # ── Calculate economics ──
        mode_load = OPERATING_MODES[mode]["load_pct"]
        adjusted_diesel_cost = avg_diesel_cost * mode_load
        adjusted_margin = avg_daily_margin * mode_load
        daily_profit = adjusted_margin - adjusted_diesel_cost

        return {
            "store_id": sid,
            "name": store["name"],
            "sector": store["sector"],
            "channel": store["channel"],
            "township": store["township"],
            "mode": mode,
            "mode_label": OPERATING_MODES[mode]["label"],
            "mode_color": OPERATING_MODES[mode]["color"],
            "reason": reason,
            "priority_score": priority_score,
            "has_solar": has_solar,

            # Economics
            "avg_daily_sales": round(avg_daily_sales, 0),
            "avg_daily_margin": round(avg_daily_margin, 0),
            "avg_diesel_cost": round(avg_diesel_cost, 0),
            "diesel_cost_per_hour": round(diesel_cost_per_hour, 0),
            "margin_per_hour": round(margin_per_hour, 0),
            "cost_margin_ratio": round(cost_margin_ratio, 3),
            "estimated_daily_profit": round(daily_profit, 0),

            # Risk factors
            "diesel_days_remaining": round(diesel_days, 1),
            "blackout_probability": round(blackout_prob, 3),
            "avg_blackout_hours": round(avg_blackout, 1),
            "solar_kwh_avg": round(solar_kwh_avg, 1),
        }

    def get_summary(self) -> dict:
        """Summarize the daily operating plan."""
        if self.decisions is None:
            return {}

        mode_counts = self.decisions["mode"].value_counts().to_dict()
        total_stores = len(self.decisions)

        return {
            "date": str(self.decisions.iloc[0].get("date", "N/A")),
            "total_stores": total_stores,
            "stores_full": mode_counts.get("FULL", 0),
            "stores_reduced": mode_counts.get("REDUCED", 0),
            "stores_critical": mode_counts.get("CRITICAL", 0),
            "stores_closed": mode_counts.get("CLOSE", 0),
            "total_estimated_profit": self.decisions["estimated_daily_profit"].sum(),
            "stores_losing_money": (self.decisions["estimated_daily_profit"] < 0).sum(),
            "avg_diesel_days": self.decisions["diesel_days_remaining"].mean(),
            "critical_diesel_stores": (self.decisions["diesel_days_remaining"] < THRESHOLDS["diesel_warning_days"]).sum(),
        }

    def get_sector_summary(self) -> pd.DataFrame:
        """Summarize decisions by sector."""
        if self.decisions is None:
            return pd.DataFrame()

        return self.decisions.groupby("sector").agg(
            total_stores=("store_id", "count"),
            full=("mode", lambda x: (x == "FULL").sum()),
            reduced=("mode", lambda x: (x == "REDUCED").sum()),
            critical=("mode", lambda x: (x == "CRITICAL").sum()),
            closed=("mode", lambda x: (x == "CLOSE").sum()),
            total_profit=("estimated_daily_profit", "sum"),
            avg_diesel_days=("diesel_days_remaining", "mean"),
        ).reset_index()

    def get_alerts(self) -> list:
        """Generate alerts from decisions."""
        alerts = []

        if self.decisions is None:
            return alerts

        for _, d in self.decisions.iterrows():
            if d["mode"] == "CLOSE":
                alerts.append({
                    "tier": 1,
                    "type": "STORE_CLOSE",
                    "store_id": d["store_id"],
                    "store_name": d["name"],
                    "message": f"CLOSE: {d['name']} — {d['reason']}",
                })
            elif d["mode"] == "CRITICAL":
                alerts.append({
                    "tier": 1,
                    "type": "STORE_CRITICAL",
                    "store_id": d["store_id"],
                    "store_name": d["name"],
                    "message": f"CRITICAL MODE: {d['name']} — {d['reason']}",
                })
            elif d["estimated_daily_profit"] < 0:
                alerts.append({
                    "tier": 2,
                    "type": "NEGATIVE_PROFIT",
                    "store_id": d["store_id"],
                    "store_name": d["name"],
                    "message": f"Negative profit: {d['name']} losing {abs(d['estimated_daily_profit']):,.0f} {DIESEL.get('currency', 'MMK')}/day",
                })

        return alerts

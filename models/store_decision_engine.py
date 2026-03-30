"""
Model 3: Store Operating Decision Engine (HIGHEST IMPACT)
Rule-based optimization that decides store operating mode.

Outputs per store:
- Mode: FULL / SELECTIVE / REDUCED / CRITICAL / CLOSE
- Reason for decision
- EBITDA per operating hour (full formula)
- Sector-specific rule applied
- Daily Operating Plan (auto-generated morning briefing)

Upgrades from BCP Framework doc:
- B1: SELECTIVE mode (5th mode, 65% load)
- B2: Full EBITDA/hr formula (Revenue - COGS - Labour - Energy - Spoilage)
- B3: Per-sector rules (never_auto_close, auto_close_below_breakeven, etc.)
"""

import pandas as pd
import numpy as np
from config.settings import THRESHOLDS, OPERATING_MODES, DIESEL, SECTOR_RULES, LABOUR_COST_PER_HOUR


class StoreDecisionEngine:
    """Determine optimal operating mode for each store based on energy economics."""

    def __init__(self):
        self.decisions = None

    def generate_daily_plan(self, stores_df: pd.DataFrame, energy_df: pd.DataFrame,
                             sales_df: pd.DataFrame, inventory_df: pd.DataFrame,
                             blackout_predictions: pd.DataFrame = None,
                             solar_df: pd.DataFrame = None,
                             target_date=None) -> pd.DataFrame:
        """Generate the Daily Operating Plan for all stores."""
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

        # Sort: CLOSE first (most urgent), then CRITICAL, REDUCED, SELECTIVE, FULL
        mode_order = {"CLOSE": 0, "CRITICAL": 1, "REDUCED": 2, "SELECTIVE": 3, "FULL": 4}
        self.decisions["_sort"] = self.decisions["mode"].map(mode_order).fillna(4)
        self.decisions = self.decisions.sort_values("_sort").drop(columns="_sort")

        return self.decisions

    def _decide_store(self, store, energy_df, sales_df, inventory_df,
                       blackout_predictions, solar_df, target_date) -> dict:
        """Decision logic for a single store."""
        sid = store["store_id"]
        channel = store["channel"]
        sector_rules = SECTOR_RULES.get(channel, {})

        # ── Gather store metrics (last 7 days) ──
        recent_energy = energy_df[
            (energy_df["store_id"] == sid) &
            (energy_df["date"] >= target_date - pd.Timedelta(days=7))
        ]
        avg_diesel_cost = recent_energy["diesel_cost_mmk"].mean() if len(recent_energy) > 0 else 0
        avg_blackout = recent_energy["blackout_hours"].mean() if len(recent_energy) > 0 else 0

        recent_sales = sales_df[
            (sales_df["store_id"] == sid) &
            (sales_df["date"] >= target_date - pd.Timedelta(days=7))
        ]
        avg_daily_sales = recent_sales.groupby("date")["sales_mmk"].sum().mean() if len(recent_sales) > 0 else 0
        avg_daily_margin = recent_sales.groupby("date")["gross_margin_mmk"].sum().mean() if len(recent_sales) > 0 else 0
        avg_hourly_margin = recent_sales["gross_margin_mmk"].mean() if len(recent_sales) > 0 else 0
        avg_hourly_revenue = recent_sales["sales_mmk"].mean() if len(recent_sales) > 0 else 0

        # Diesel inventory
        latest_inv = inventory_df[
            (inventory_df["store_id"] == sid) &
            (inventory_df["date"] == inventory_df["date"].max())
        ]
        diesel_days = latest_inv["days_of_coverage"].values[0] if len(latest_inv) > 0 else 5
        diesel_stock = latest_inv["diesel_stock_liters"].values[0] if len(latest_inv) > 0 else 100

        # Blackout probability
        blackout_prob = 0.5
        if blackout_predictions is not None and len(blackout_predictions) > 0:
            bp = blackout_predictions[blackout_predictions["store_id"] == sid]
            if len(bp) > 0:
                blackout_prob = bp["blackout_probability"].values[0]

        # Solar
        has_solar = store["has_solar"]
        solar_kwh_avg = 0
        if has_solar and solar_df is not None:
            recent_solar = solar_df[
                (solar_df["store_id"] == sid) &
                (solar_df["date"] >= target_date - pd.Timedelta(days=7))
            ]
            solar_kwh_avg = recent_solar.groupby("date")["solar_kwh"].sum().mean() if len(recent_solar) > 0 else 0

        # ── EBITDA per operating hour (B2 — full formula) ──
        operating_hours = max(1, 16 - avg_blackout)
        generator_hours = avg_blackout
        diesel_cost_per_hour = avg_diesel_cost / max(generator_hours, 1) if generator_hours > 0 else 0
        energy_cost_per_hour = (avg_diesel_cost + recent_energy["grid_cost_mmk"].mean()) / 16 if len(recent_energy) > 0 else 0
        margin_per_hour = avg_hourly_margin
        labour_per_hour = LABOUR_COST_PER_HOUR.get(channel, 15000)
        cogs_per_hour = avg_hourly_revenue - avg_hourly_margin

        # Full EBITDA/hr = Margin/hr - Labour/hr - (Energy is already excluded from margin calc for generator)
        ebitda_per_hr = margin_per_hour - labour_per_hour - energy_cost_per_hour
        ebitda_per_generator_hr = margin_per_hour - labour_per_hour - diesel_cost_per_hour

        # Cost-to-margin ratio (backward compatible)
        cost_margin_ratio = diesel_cost_per_hour / max(margin_per_hour, 1) if margin_per_hour > 0 else 999

        # ── DECISION LOGIC (with sector rules) ──
        mode = "FULL"
        reason = ""
        priority_score = 0
        sector_rule_applied = ""

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

        # Rule 3: EBITDA/hr negative on generator → CLOSE or SELECTIVE
        elif ebitda_per_generator_hr < 0 and diesel_days < THRESHOLDS["diesel_warning_days"]:
            mode = "CLOSE"
            reason = f"Generator EBITDA negative ({ebitda_per_generator_hr:,.0f} MMK/hr) + low diesel"
            priority_score = 85

        # Rule 4: EBITDA/hr negative but diesel OK → SELECTIVE (B1)
        elif ebitda_per_generator_hr < 0:
            mode = "SELECTIVE"
            reason = f"Generator EBITDA negative ({ebitda_per_generator_hr:,.0f} MMK/hr) — essential ops only"
            priority_score = 65

        # Rule 5: Generator cost exceeds margin → REDUCED
        elif cost_margin_ratio > THRESHOLDS["margin_breakeven_ratio"]:
            mode = "REDUCED"
            reason = f"Diesel cost exceeds margin (ratio: {cost_margin_ratio:.2f})"
            priority_score = 60

        # Rule 6: High blackout + low diesel → CRITICAL
        elif blackout_prob >= THRESHOLDS["blackout_high_prob"] and diesel_days < THRESHOLDS["diesel_warning_days"]:
            mode = "CRITICAL"
            reason = f"High blackout risk ({blackout_prob*100:.0f}%) + low diesel ({diesel_days:.1f} days)"
            priority_score = 70

        # Rule 7: High blackout + tight margins → SELECTIVE (B1)
        elif blackout_prob >= THRESHOLDS["blackout_high_prob"] and cost_margin_ratio > THRESHOLDS["margin_reduce_ratio"]:
            mode = "SELECTIVE"
            reason = f"High blackout risk ({blackout_prob*100:.0f}%) + tight margins — essential ops only"
            priority_score = 55

        # Rule 8: High blackout but margins OK → REDUCED
        elif blackout_prob >= THRESHOLDS["blackout_high_prob"]:
            mode = "REDUCED"
            reason = f"High blackout risk ({blackout_prob*100:.0f}%) — reduce non-essential load"
            priority_score = 50

        # Rule 9: Solar available → FULL
        elif has_solar and solar_kwh_avg > 0:
            mode = "FULL"
            reason = f"Solar available ({solar_kwh_avg:.0f} kWh/day avg) — prioritize solar hours"
            priority_score = 10

        # Rule 10: Default profitable → FULL
        else:
            mode = "FULL"
            reason = "Profitable operations, normal mode"
            priority_score = 0

        # ── Apply Sector Rules (B3) ──
        min_mode = sector_rules.get("min_mode")
        mode_severity = {"FULL": 0, "SELECTIVE": 1, "REDUCED": 2, "CRITICAL": 3, "CLOSE": 4}

        # Never auto-close rule (Hypermarket, Mall)
        if sector_rules.get("never_auto_close") and mode == "CLOSE":
            fallback = min_mode or "REDUCED"
            sector_rule_applied = f"Sector rule: {channel} never auto-close → {fallback}"
            mode = fallback
            reason += f" [OVERRIDDEN: {channel} cannot auto-close]"

        # Enforce minimum mode
        if min_mode and mode_severity.get(mode, 0) > mode_severity.get(min_mode, 0):
            sector_rule_applied = f"Sector rule: {channel} min mode = {min_mode}"
            mode = min_mode
            reason += f" [FLOOR: {channel} min mode is {min_mode}]"

        # Auto-close below breakeven (Convenience)
        if sector_rules.get("auto_close_below_breakeven") and ebitda_per_generator_hr < 0 and generator_hours > 2:
            if mode not in ("CLOSE",):
                sector_rule_applied = f"Sector rule: {channel} auto-close below breakeven"
                mode = "CLOSE"
                reason = f"Auto-close: {channel} EBITDA/hr negative ({ebitda_per_generator_hr:,.0f} MMK/hr)"
                priority_score = 80

        # Solar window shift recommendation (Bakery)
        solar_shift_note = ""
        if sector_rules.get("shift_to_solar_window") and has_solar and solar_kwh_avg > 0:
            solar_shift_note = "Shift production to solar peak (10am-3pm)"
            if not sector_rule_applied:
                sector_rule_applied = f"Sector rule: {channel} shift to solar window"

        # Pre-cool recommendation (Warehouse, Cold Chain)
        precool_note = ""
        if sector_rules.get("pre_cool_buffer") and blackout_prob > 0.5:
            precool_note = "Pre-cool cold chain before predicted blackout"
            if not sector_rule_applied:
                sector_rule_applied = f"Sector rule: {channel} pre-cool buffer"

        # HVAC reduction (Office, Property)
        hvac_note = ""
        if sector_rules.get("aggressive_hvac_reduction") and mode in ("SELECTIVE", "REDUCED", "CRITICAL"):
            hvac_note = "Reduce HVAC and lighting aggressively"
            if not sector_rule_applied:
                sector_rule_applied = f"Sector rule: {channel} reduce HVAC"

        # ── Calculate economics ──
        mode_load = OPERATING_MODES.get(mode, OPERATING_MODES["FULL"])["load_pct"]
        adjusted_diesel_cost = avg_diesel_cost * mode_load
        adjusted_margin = avg_daily_margin * mode_load
        daily_profit = adjusted_margin - adjusted_diesel_cost

        return {
            "store_id": sid,
            "name": store["name"],
            "sector": store["sector"],
            "channel": channel,
            "township": store["township"],
            "mode": mode,
            "mode_label": OPERATING_MODES.get(mode, OPERATING_MODES["FULL"])["label"],
            "mode_color": OPERATING_MODES.get(mode, OPERATING_MODES["FULL"])["color"],
            "reason": reason,
            "priority_score": priority_score,
            "has_solar": has_solar,

            # Sector rules (B3)
            "sector_rule_applied": sector_rule_applied,
            "solar_shift_note": solar_shift_note,
            "precool_note": precool_note,
            "hvac_note": hvac_note,

            # EBITDA/hr economics (B2)
            "avg_daily_sales": round(avg_daily_sales, 0),
            "avg_daily_margin": round(avg_daily_margin, 0),
            "avg_diesel_cost": round(avg_diesel_cost, 0),
            "diesel_cost_per_hour": round(diesel_cost_per_hour, 0),
            "margin_per_hour": round(margin_per_hour, 0),
            "labour_per_hour": round(labour_per_hour, 0),
            "energy_cost_per_hour": round(energy_cost_per_hour, 0),
            "ebitda_per_hr": round(ebitda_per_hr, 0),
            "ebitda_per_generator_hr": round(ebitda_per_generator_hr, 0),
            "is_profitable_on_generator": ebitda_per_generator_hr > 0,
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

        return {
            "date": str(self.decisions.iloc[0].get("date", "N/A")),
            "total_stores": len(self.decisions),
            "stores_full": mode_counts.get("FULL", 0),
            "stores_selective": mode_counts.get("SELECTIVE", 0),
            "stores_reduced": mode_counts.get("REDUCED", 0),
            "stores_critical": mode_counts.get("CRITICAL", 0),
            "stores_closed": mode_counts.get("CLOSE", 0),
            "total_estimated_profit": self.decisions["estimated_daily_profit"].sum(),
            "stores_losing_money": (self.decisions["estimated_daily_profit"] < 0).sum(),
            "stores_negative_generator_ebitda": (~self.decisions["is_profitable_on_generator"]).sum(),
            "avg_diesel_days": self.decisions["diesel_days_remaining"].mean(),
            "critical_diesel_stores": (self.decisions["diesel_days_remaining"] < THRESHOLDS["diesel_warning_days"]).sum(),
            "sector_rules_applied": (self.decisions["sector_rule_applied"] != "").sum(),
        }

    def get_sector_summary(self) -> pd.DataFrame:
        """Summarize decisions by sector."""
        if self.decisions is None:
            return pd.DataFrame()

        return self.decisions.groupby("sector").agg(
            total_stores=("store_id", "count"),
            full=("mode", lambda x: (x == "FULL").sum()),
            selective=("mode", lambda x: (x == "SELECTIVE").sum()),
            reduced=("mode", lambda x: (x == "REDUCED").sum()),
            critical=("mode", lambda x: (x == "CRITICAL").sum()),
            closed=("mode", lambda x: (x == "CLOSE").sum()),
            total_profit=("estimated_daily_profit", "sum"),
            avg_diesel_days=("diesel_days_remaining", "mean"),
            avg_ebitda_per_hr=("ebitda_per_hr", "mean"),
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
            elif d["mode"] == "SELECTIVE":
                alerts.append({
                    "tier": 2,
                    "type": "STORE_SELECTIVE",
                    "store_id": d["store_id"],
                    "store_name": d["name"],
                    "message": f"SELECTIVE: {d['name']} — {d['reason']}",
                })
            elif not d["is_profitable_on_generator"]:
                alerts.append({
                    "tier": 2,
                    "type": "NEGATIVE_GENERATOR_EBITDA",
                    "store_id": d["store_id"],
                    "store_name": d["name"],
                    "message": f"Generator EBITDA negative: {d['name']} losing {abs(d['ebitda_per_generator_hr']):,.0f} MMK/hr on generator",
                })
            elif d["estimated_daily_profit"] < 0:
                alerts.append({
                    "tier": 2,
                    "type": "NEGATIVE_PROFIT",
                    "store_id": d["store_id"],
                    "store_name": d["name"],
                    "message": f"Negative profit: {d['name']} losing {abs(d['estimated_daily_profit']):,.0f} MMK/day",
                })

        return alerts

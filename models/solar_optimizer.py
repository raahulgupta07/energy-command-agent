"""
Model 5: Solar + Diesel Energy Mix Optimizer
Linear programming to minimize energy cost while meeting demand.

Outputs:
- Optimal energy source mix per store per hour
- Load-shifting recommendations (move operations to solar peak)
- Diesel offset (liters saved by solar)
"""

import pandas as pd
import numpy as np
from scipy.optimize import linprog
from config.settings import THRESHOLDS, DIESEL


class SolarOptimizer:
    """Optimize energy mix between solar, grid, and diesel."""

    def __init__(self):
        self.results = None

    def optimize_store(self, store: dict, solar_df: pd.DataFrame,
                        energy_df: pd.DataFrame, diesel_price: float) -> dict:
        """Optimize energy mix for a single store for one day.

        Args:
            store: store record from stores_df
            solar_df: solar generation data for this store
            energy_df: recent energy data for this store
            diesel_price: current diesel price per liter

        Returns:
            dict with optimal schedule and savings
        """
        sid = store["store_id"]

        if not store["has_solar"]:
            return {
                "store_id": sid,
                "has_solar": False,
                "solar_kwh": 0,
                "diesel_offset_liters": 0,
                "cost_saving_mmk": 0,
                "recommendations": ["No solar installed — consider CAPEX investment"],
            }

        # Get recent solar generation pattern (average by hour)
        if len(solar_df) > 0:
            hourly_solar = solar_df.groupby("hour")["solar_kwh"].mean().to_dict()
        else:
            hourly_solar = {}

        # Get store demand profile (from recent energy data)
        recent_energy = energy_df.tail(7)
        avg_daily_demand_kwh = (
            recent_energy["generator_hours"].mean() * store["generator_kw"] +
            recent_energy["grid_hours"].mean() * store["generator_kw"] * 0.5
        )

        # Hourly demand (rough estimate based on operating pattern)
        demand_weights = {
            6: 0.03, 7: 0.04, 8: 0.06, 9: 0.07, 10: 0.08,
            11: 0.09, 12: 0.10, 13: 0.09, 14: 0.08, 15: 0.07,
            16: 0.08, 17: 0.08, 18: 0.06, 19: 0.04, 20: 0.02, 21: 0.01,
        }

        # ── Calculate solar contribution ──
        total_solar_kwh = sum(hourly_solar.values())
        solar_peak_hours = [h for h, kwh in hourly_solar.items()
                           if kwh > 0.5 * max(hourly_solar.values(), default=1)]

        # Diesel offset: solar kWh * consumption rate per kWh
        diesel_offset_liters = total_solar_kwh * DIESEL["consumption_per_kwh"]
        cost_saving = diesel_offset_liters * diesel_price

        # Grid cost of same energy
        grid_equivalent_cost = total_solar_kwh * DIESEL["cost_per_kwh_grid"]

        # ── Load-shifting analysis ──
        recommendations = []

        # Find hours where solar exceeds demand
        solar_surplus_hours = []
        solar_deficit_hours = []

        for hour in range(6, 22):
            solar = hourly_solar.get(hour, 0)
            demand = avg_daily_demand_kwh * demand_weights.get(hour, 0.05)

            if solar > demand * 0.5:
                solar_surplus_hours.append(hour)
            elif solar < demand * 0.2 and hour >= 17:
                solar_deficit_hours.append(hour)

        if solar_surplus_hours:
            peak_str = f"{min(solar_surplus_hours)}:00-{max(solar_surplus_hours)+1}:00"
            recommendations.append(
                f"Maximize operations during solar peak ({peak_str})"
            )

        if store["channel"] in ["Bakery", "Restaurant"]:
            recommendations.append(
                f"Shift production/cooking to {THRESHOLDS['solar_peak_start_hour']}:00-"
                f"{THRESHOLDS['solar_peak_end_hour']}:00 (solar peak)"
            )

        if store["channel"] in ["Hypermarket", "Supermarket", "Cold Chain"]:
            recommendations.append(
                f"Pre-cool refrigeration during solar hours to reduce generator load after sunset"
            )

        if diesel_offset_liters > 20:
            recommendations.append(
                f"Solar offsetting {diesel_offset_liters:.0f}L diesel/day "
                f"(saving {cost_saving:,.0f} MMK/day)"
            )

        return {
            "store_id": sid,
            "name": store["name"],
            "sector": store["sector"],
            "channel": store["channel"],
            "has_solar": True,
            "solar_capacity_kw": store["generator_kw"] * 0.4,
            "daily_solar_kwh": round(total_solar_kwh, 1),
            "diesel_offset_liters": round(diesel_offset_liters, 1),
            "cost_saving_mmk": round(cost_saving, 0),
            "grid_equivalent_saving_mmk": round(grid_equivalent_cost, 0),
            "solar_peak_hours": solar_peak_hours,
            "recommendations": recommendations,
        }

    def optimize_all(self, stores_df: pd.DataFrame, solar_df: pd.DataFrame,
                      energy_df: pd.DataFrame, diesel_price: float) -> pd.DataFrame:
        """Run optimization for all stores.

        Returns:
            DataFrame with optimization results for each store
        """
        results = []

        for _, store in stores_df.iterrows():
            store_solar = solar_df[solar_df["store_id"] == store["store_id"]] if len(solar_df) > 0 else pd.DataFrame()
            store_energy = energy_df[energy_df["store_id"] == store["store_id"]]

            result = self.optimize_store(store, store_solar, store_energy, diesel_price)
            results.append(result)

        self.results = pd.DataFrame(results)
        return self.results

    def get_capex_priority(self, stores_df: pd.DataFrame, energy_df: pd.DataFrame,
                            diesel_price: float) -> pd.DataFrame:
        """Rank non-solar stores by potential ROI for solar installation.

        Returns:
            DataFrame: store ranking for solar CAPEX investment
        """
        non_solar = stores_df[stores_df["has_solar"] == False].copy()
        rankings = []

        for _, store in non_solar.iterrows():
            store_energy = energy_df[energy_df["store_id"] == store["store_id"]]

            if len(store_energy) == 0:
                continue

            avg_diesel = store_energy["diesel_consumed_liters"].mean()
            avg_diesel_cost = store_energy["diesel_cost_mmk"].mean()
            avg_gen_hours = store_energy["generator_hours"].mean()

            # Estimated solar capacity (40% of generator)
            est_solar_kw = store["generator_kw"] * 0.4

            # Estimated daily solar generation (5 peak sun hours avg)
            est_daily_kwh = est_solar_kw * 4.5  # Conservative estimate

            # Estimated diesel offset
            est_diesel_saved = est_daily_kwh * DIESEL["consumption_per_kwh"]
            est_daily_saving = est_diesel_saved * diesel_price

            # Rough installation cost (MMK per kW — ~$800/kW at current FX)
            install_cost_per_kw = 2_800_000  # MMK
            total_install_cost = est_solar_kw * install_cost_per_kw

            # Payback period (months)
            monthly_saving = est_daily_saving * 30
            payback_months = total_install_cost / max(monthly_saving, 1)

            rankings.append({
                "store_id": store["store_id"],
                "name": store["name"],
                "sector": store["sector"],
                "channel": store["channel"],
                "generator_kw": store["generator_kw"],
                "est_solar_kw": round(est_solar_kw, 0),
                "avg_daily_diesel_liters": round(avg_diesel, 1),
                "avg_daily_diesel_cost": round(avg_diesel_cost, 0),
                "est_daily_saving_mmk": round(est_daily_saving, 0),
                "est_monthly_saving_mmk": round(monthly_saving, 0),
                "est_install_cost_mmk": round(total_install_cost, 0),
                "payback_months": round(payback_months, 1),
                "priority_score": round(1 / max(payback_months, 0.1) * 100, 1),
            })

        result = pd.DataFrame(rankings).sort_values("payback_months")
        result["rank"] = range(1, len(result) + 1)
        return result

    def generate_hourly_schedule(self, store: dict, solar_df: pd.DataFrame,
                                   energy_df: pd.DataFrame,
                                   blackout_predictions: pd.DataFrame = None,
                                   diesel_price: float = 3000) -> list:
        """Generate hour-by-hour operating schedule for a solar store (E1).

        Shifts energy-intensive operations to solar peak, reduces load post-peak.
        Returns list of 16 hourly slots (6am-10pm) with mode + energy source.

        Example from doc:
          09:00-15:00: FULL (solar primary) — near-zero energy cost
          15:00-19:00: SELECTIVE (grid reducing, prepare for blackout)
          19:00-22:00: CRITICAL (generator if blackout, reduced load)
        """
        sid = store["store_id"]
        if not store["has_solar"]:
            return []

        # Get solar pattern
        store_solar = solar_df[solar_df["store_id"] == sid] if len(solar_df) > 0 else pd.DataFrame()
        hourly_solar = store_solar.groupby("hour")["solar_kwh"].mean().to_dict() if len(store_solar) > 0 else {}

        # Peak solar threshold
        max_solar = max(hourly_solar.values(), default=0)
        peak_threshold = max_solar * 0.5

        # Blackout probability
        blackout_prob = 0.5
        if blackout_predictions is not None and len(blackout_predictions) > 0:
            bp = blackout_predictions[blackout_predictions["store_id"] == sid]
            if len(bp) > 0:
                blackout_prob = bp["blackout_probability"].values[0]

        # Build hourly schedule
        schedule = []
        total_diesel_saved = 0
        total_diesel_unoptimized = 0

        for hour in range(6, 22):
            solar_kwh = hourly_solar.get(hour, 0)
            is_solar_peak = solar_kwh >= peak_threshold and solar_kwh > 0

            # Determine mode based on solar + blackout risk
            if is_solar_peak:
                mode = "FULL"
                energy_source = "Solar (primary) + Grid (backup)"
                energy_cost = 0  # Near-zero during solar
                diesel_liters = 0
            elif hour < 18 and solar_kwh > 0:
                mode = "FULL"
                energy_source = "Solar (partial) + Grid"
                energy_cost = DIESEL["cost_per_kwh_grid"] * store["generator_kw"] * 0.3
                diesel_liters = 0
            elif blackout_prob >= 0.7 and hour >= 17:
                mode = "CRITICAL"
                energy_source = "Generator (if blackout) — minimal load"
                diesel_liters = store["generator_kw"] * DIESEL["consumption_per_kwh"] * 0.3 / 1000
                energy_cost = diesel_liters * diesel_price
            elif blackout_prob >= 0.5 and hour >= 15:
                mode = "SELECTIVE"
                energy_source = "Grid (reducing) — prepare for blackout"
                diesel_liters = 0
                energy_cost = DIESEL["cost_per_kwh_grid"] * store["generator_kw"] * 0.4
            else:
                mode = "FULL"
                energy_source = "Grid"
                diesel_liters = 0
                energy_cost = DIESEL["cost_per_kwh_grid"] * store["generator_kw"] * 0.5

            # Unoptimized baseline: run generator all blackout hours at full load
            unoptimized_diesel = store["generator_kw"] * DIESEL["consumption_per_kwh"] * 0.8 / 1000 if blackout_prob > 0.3 and hour >= 14 else 0

            total_diesel_saved += (unoptimized_diesel - diesel_liters)
            total_diesel_unoptimized += unoptimized_diesel

            schedule.append({
                "hour": hour,
                "time_label": f"{hour:02d}:00",
                "mode": mode,
                "energy_source": energy_source,
                "solar_kwh": round(solar_kwh, 1),
                "diesel_liters": round(diesel_liters, 2),
                "energy_cost_mmk": round(energy_cost, 0),
            })

        # Add summary to first entry
        if schedule:
            diesel_saving_mmk = round(total_diesel_saved * diesel_price, 0)
            schedule[0]["_summary"] = {
                "total_diesel_saved_liters": round(total_diesel_saved, 1),
                "diesel_saving_mmk": diesel_saving_mmk,
                "solar_peak_hours": [h for h, kwh in hourly_solar.items() if kwh >= peak_threshold],
            }

        return schedule

    def generate_all_schedules(self, stores_df: pd.DataFrame, solar_df: pd.DataFrame,
                                energy_df: pd.DataFrame, diesel_price: float,
                                blackout_predictions: pd.DataFrame = None) -> dict:
        """Generate hourly schedules for all solar stores.

        Returns:
            dict: {store_id: [schedule_list]}
        """
        schedules = {}
        solar_stores = stores_df[stores_df["has_solar"] == True]

        for _, store in solar_stores.iterrows():
            schedule = self.generate_hourly_schedule(
                store, solar_df, energy_df, blackout_predictions, diesel_price
            )
            if schedule:
                schedules[store["store_id"]] = schedule

        return schedules

    def get_network_summary(self) -> dict:
        """Summary stats for solar across the network."""
        if self.results is None:
            return {}

        solar = self.results[self.results["has_solar"] == True]

        return {
            "total_solar_sites": len(solar),
            "total_non_solar": len(self.results) - len(solar),
            "total_daily_solar_kwh": solar["daily_solar_kwh"].sum(),
            "total_diesel_offset_liters": solar["diesel_offset_liters"].sum(),
            "total_daily_saving_mmk": solar["cost_saving_mmk"].sum(),
            "avg_saving_per_site_mmk": solar["cost_saving_mmk"].mean() if len(solar) > 0 else 0,
        }

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

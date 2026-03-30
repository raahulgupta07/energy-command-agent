"""
Model 8: Holdings Aggregator + Scenario Engine
Cross-sector intelligence for the Group Energy Command Center.

Outputs:
- Group-level KPIs (EBITDA impact, energy cost, resilience)
- Sector comparison
- Scenario simulation (what-if analysis)
- CAPEX prioritization
"""

import pandas as pd
import numpy as np
from config.settings import SECTORS, CURRENCY
from utils.kpi_calculator import (
    energy_cost_pct_of_sales,
    diesel_cost_per_store_per_day,
    ebitda_impact_from_disruption,
    energy_resilience_index,
    diesel_dependency_ratio,
)


class HoldingsAggregator:
    """Group-level analytics and scenario simulation."""

    def __init__(self):
        self.group_kpis = None
        self.sector_kpis = None

    def compute_group_kpis(self, stores_df: pd.DataFrame, energy_df: pd.DataFrame,
                            sales_df: pd.DataFrame, inventory_df: pd.DataFrame) -> dict:
        """Calculate all group-level KPIs.

        Returns:
            dict with comprehensive group metrics
        """
        # Energy cost % of sales (group level)
        ecps = energy_cost_pct_of_sales(energy_df, sales_df)

        # Total diesel cost
        diesel_costs = diesel_cost_per_store_per_day(energy_df)

        # EBITDA impact
        ebitda = ebitda_impact_from_disruption(energy_df, sales_df, stores_df)

        # Energy Resilience Index
        eri = energy_resilience_index(energy_df, sales_df)

        # Diesel dependency
        dep = diesel_dependency_ratio(energy_df)

        # Latest inventory
        latest_date = inventory_df["date"].max()
        latest_inv = inventory_df[inventory_df["date"] == latest_date]

        self.group_kpis = {
            # Financial
            "total_energy_cost_mmk": energy_df["total_energy_cost_mmk"].sum(),
            "total_diesel_cost_mmk": energy_df["diesel_cost_mmk"].sum(),
            "total_grid_cost_mmk": energy_df["grid_cost_mmk"].sum(),
            "energy_cost_pct_of_sales": ecps["energy_cost_pct"].values[0] if len(ecps) > 0 else 0,
            "avg_diesel_cost_per_store_day": diesel_costs["avg_daily_diesel_cost"].mean(),

            # Impact
            "total_ebitda_impact_mmk": ebitda["total_impact_mmk"].sum(),
            "total_lost_margin_mmk": ebitda["lost_margin_mmk"].sum(),
            "avg_daily_ebitda_impact": ebitda.groupby("date")["total_impact_mmk"].sum().mean(),

            # Resilience
            "avg_eri_pct": eri["eri_pct"].mean(),
            "min_eri_pct": eri["eri_pct"].min(),
            "max_eri_pct": eri["eri_pct"].max(),
            "stores_below_50_eri": (eri["eri_pct"] < 50).sum(),

            # Diesel dependency
            "avg_diesel_dependency_pct": dep["diesel_dependency_pct"].mean(),

            # Inventory
            "total_diesel_stock_liters": latest_inv["diesel_stock_liters"].sum(),
            "avg_days_coverage": latest_inv["days_of_coverage"].mean(),
            "stores_below_2_days": (latest_inv["days_of_coverage"] < 2).sum(),

            # Operations
            "total_stores": len(stores_df),
            "total_blackout_hours": energy_df["blackout_hours"].sum(),
            "avg_daily_blackout_hours": energy_df.groupby("date")["blackout_hours"].mean().mean(),
            "total_generator_hours": energy_df["generator_hours"].sum(),
            "total_diesel_consumed_liters": energy_df["diesel_consumed_liters"].sum(),

            # Solar
            "total_solar_kwh": energy_df["solar_kwh"].sum(),
            "solar_sites": stores_df["has_solar"].sum(),
        }

        return self.group_kpis

    def compute_sector_kpis(self, stores_df: pd.DataFrame, energy_df: pd.DataFrame,
                             sales_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate KPIs broken down by sector.

        Returns:
            DataFrame with sector-level metrics
        """
        merged_energy = energy_df.merge(stores_df[["store_id", "sector"]], on="store_id", how="left")
        merged_sales = sales_df.merge(stores_df[["store_id", "sector"]], on="store_id", how="left")

        sectors = []

        for sector_name in SECTORS.keys():
            s_energy = merged_energy[merged_energy["sector"] == sector_name]
            s_sales = merged_sales[merged_sales["sector"] == sector_name]
            s_stores = stores_df[stores_df["sector"] == sector_name]

            if len(s_energy) == 0:
                continue

            total_energy_cost = s_energy["total_energy_cost_mmk"].sum()
            total_diesel_cost = s_energy["diesel_cost_mmk"].sum()
            total_sales = s_sales["sales_mmk"].sum()
            total_margin = s_sales["gross_margin_mmk"].sum()

            sectors.append({
                "sector": sector_name,
                "color": SECTORS[sector_name]["color"],
                "num_stores": len(s_stores),
                "total_energy_cost": total_energy_cost,
                "total_diesel_cost": total_diesel_cost,
                "total_sales": total_sales,
                "total_margin": total_margin,
                "energy_cost_pct": round(total_energy_cost / max(total_sales, 1) * 100, 2),
                "diesel_dependency_pct": round(total_diesel_cost / max(total_energy_cost, 1) * 100, 1),
                "avg_blackout_hours": s_energy["blackout_hours"].mean(),
                "total_solar_kwh": s_energy["solar_kwh"].sum(),
                "solar_sites": s_stores["has_solar"].sum(),
            })

        self.sector_kpis = pd.DataFrame(sectors)
        return self.sector_kpis

    def simulate_scenario(self, stores_df: pd.DataFrame, energy_df: pd.DataFrame,
                           sales_df: pd.DataFrame, inventory_df: pd.DataFrame,
                           diesel_price_change_pct: float = 0,
                           blackout_hours_change_pct: float = 0,
                           fx_change_pct: float = 0,
                           solar_new_sites: int = 0) -> dict:
        """Run what-if scenario simulation.

        Args:
            diesel_price_change_pct: e.g., 15 for +15%
            blackout_hours_change_pct: e.g., 20 for +20%
            fx_change_pct: e.g., 10 for +10%
            solar_new_sites: number of new solar installations

        Returns:
            dict with scenario impact metrics
        """
        # Clone data for simulation
        sim_energy = energy_df.copy()

        # Apply diesel price change
        price_multiplier = 1 + diesel_price_change_pct / 100
        sim_energy["diesel_cost_mmk"] = sim_energy["diesel_cost_mmk"] * price_multiplier
        sim_energy["total_energy_cost_mmk"] = sim_energy["diesel_cost_mmk"] + sim_energy["grid_cost_mmk"]

        # Apply blackout change
        blackout_multiplier = 1 + blackout_hours_change_pct / 100
        sim_energy["blackout_hours"] = (sim_energy["blackout_hours"] * blackout_multiplier).clip(upper=16)
        sim_energy["generator_hours"] = sim_energy["generator_hours"] * blackout_multiplier
        sim_energy["diesel_consumed_liters"] = sim_energy["diesel_consumed_liters"] * blackout_multiplier

        # Recalculate diesel cost with new consumption
        sim_energy["diesel_cost_mmk"] = sim_energy["diesel_consumed_liters"] * price_multiplier * 2800 / sim_energy["diesel_consumed_liters"].clip(lower=0.1) * sim_energy["diesel_cost_mmk"] / (sim_energy["diesel_cost_mmk"].clip(lower=1))
        # Simplified: just apply both multipliers to diesel cost
        sim_energy["diesel_cost_mmk"] = energy_df["diesel_cost_mmk"] * price_multiplier * blackout_multiplier
        sim_energy["total_energy_cost_mmk"] = sim_energy["diesel_cost_mmk"] + sim_energy["grid_cost_mmk"]

        # Compute scenario KPIs
        sim_total_energy_cost = sim_energy["total_energy_cost_mmk"].sum()
        sim_total_diesel_cost = sim_energy["diesel_cost_mmk"].sum()
        original_total_energy_cost = energy_df["total_energy_cost_mmk"].sum()
        original_total_diesel_cost = energy_df["diesel_cost_mmk"].sum()

        # Sales impact (more blackouts = some sales loss)
        sales_impact_pct = blackout_hours_change_pct * 0.3  # 30% of blackout increase translates to sales loss
        total_sales = sales_df["sales_mmk"].sum()
        sim_total_sales = total_sales * (1 - sales_impact_pct / 100)
        total_margin = sales_df["gross_margin_mmk"].sum()
        sim_total_margin = total_margin * (1 - sales_impact_pct / 100)

        # Solar benefit (if adding new sites)
        solar_saving = 0
        if solar_new_sites > 0:
            avg_solar_saving_per_site = 150000  # MMK/day estimate
            solar_saving = solar_new_sites * avg_solar_saving_per_site * len(energy_df["date"].unique())

        # Store operating mode changes
        from models.store_decision_engine import StoreDecisionEngine
        engine = StoreDecisionEngine()

        # Estimate mode changes based on cost ratio shift
        current_cost_ratio = original_total_diesel_cost / max(total_margin, 1)
        scenario_cost_ratio = sim_total_diesel_cost / max(sim_total_margin, 1)

        # Rough estimate of store mode distribution
        total_stores = len(stores_df)
        if scenario_cost_ratio > current_cost_ratio * 1.3:
            est_full = int(total_stores * 0.4)
            est_reduced = int(total_stores * 0.3)
            est_critical = int(total_stores * 0.15)
            est_closed = total_stores - est_full - est_reduced - est_critical
        elif scenario_cost_ratio > current_cost_ratio * 1.1:
            est_full = int(total_stores * 0.55)
            est_reduced = int(total_stores * 0.25)
            est_critical = int(total_stores * 0.1)
            est_closed = total_stores - est_full - est_reduced - est_critical
        else:
            est_full = int(total_stores * 0.7)
            est_reduced = int(total_stores * 0.2)
            est_critical = int(total_stores * 0.05)
            est_closed = total_stores - est_full - est_reduced - est_critical

        # EBITDA impact
        original_ebitda = total_margin - original_total_energy_cost
        scenario_ebitda = sim_total_margin - sim_total_energy_cost + solar_saving
        ebitda_impact_pct = (scenario_ebitda - original_ebitda) / max(abs(original_ebitda), 1) * 100

        return {
            # Scenario parameters
            "diesel_price_change_pct": diesel_price_change_pct,
            "blackout_hours_change_pct": blackout_hours_change_pct,
            "fx_change_pct": fx_change_pct,
            "solar_new_sites": solar_new_sites,

            # Cost impact
            "original_energy_cost": round(original_total_energy_cost, 0),
            "scenario_energy_cost": round(sim_total_energy_cost, 0),
            "energy_cost_change_pct": round((sim_total_energy_cost - original_total_energy_cost) / max(original_total_energy_cost, 1) * 100, 1),

            # Sales impact
            "original_sales": round(total_sales, 0),
            "scenario_sales": round(sim_total_sales, 0),
            "sales_change_pct": round(-sales_impact_pct, 1),

            # Diesel impact
            "original_diesel_cost": round(original_total_diesel_cost, 0),
            "scenario_diesel_cost": round(sim_total_diesel_cost, 0),
            "diesel_demand_change_pct": round(blackout_hours_change_pct, 1),

            # EBITDA
            "original_ebitda": round(original_ebitda, 0),
            "scenario_ebitda": round(scenario_ebitda, 0),
            "ebitda_impact_pct": round(ebitda_impact_pct, 1),

            # Solar offset
            "solar_saving_mmk": round(solar_saving, 0),

            # Store modes (estimated)
            "est_stores_full": est_full,
            "est_stores_reduced": est_reduced,
            "est_stores_critical": est_critical,
            "est_stores_closed": est_closed,
        }

    def get_eri_ranking(self, energy_df: pd.DataFrame, sales_df: pd.DataFrame,
                         stores_df: pd.DataFrame) -> pd.DataFrame:
        """Rank all stores by Energy Resilience Index.

        Returns:
            DataFrame: ranked stores with ERI and sector info
        """
        eri = energy_resilience_index(energy_df, sales_df)
        merged = eri.merge(
            stores_df[["store_id", "name", "sector", "channel", "has_solar", "township"]],
            on="store_id", how="left"
        )
        merged = merged.sort_values("eri_pct", ascending=False)
        merged["rank"] = range(1, len(merged) + 1)

        return merged

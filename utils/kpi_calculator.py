"""
KPI Calculator - Shared formulas used across models and dashboards.
All monetary values in MMK unless noted.
"""

import pandas as pd
import numpy as np


def energy_cost_pct_of_sales(energy_df: pd.DataFrame, sales_df: pd.DataFrame,
                              group_cols: list = None) -> pd.DataFrame:
    """Energy cost as percentage of sales revenue.

    Args:
        energy_df: daily_energy with total_energy_cost_mmk
        sales_df: store_sales with sales_mmk
        group_cols: columns to group by (e.g., ['store_id'], ['sector'])
    """
    # Aggregate sales to daily level
    daily_sales = sales_df.groupby(["date", "store_id"])["sales_mmk"].sum().reset_index()

    merged = energy_df.merge(daily_sales, on=["date", "store_id"], how="left")

    if group_cols:
        result = merged.groupby(group_cols).agg(
            total_energy_cost=("total_energy_cost_mmk", "sum"),
            total_sales=("sales_mmk", "sum"),
        ).reset_index()
    else:
        result = pd.DataFrame([{
            "total_energy_cost": merged["total_energy_cost_mmk"].sum(),
            "total_sales": merged["sales_mmk"].sum(),
        }])

    result["energy_cost_pct"] = (
        result["total_energy_cost"] / result["total_sales"].replace(0, np.nan) * 100
    ).round(2)

    return result


def diesel_cost_per_store_per_day(energy_df: pd.DataFrame) -> pd.DataFrame:
    """Average daily diesel cost per store."""
    return energy_df.groupby("store_id").agg(
        avg_daily_diesel_cost=("diesel_cost_mmk", "mean"),
        total_diesel_cost=("diesel_cost_mmk", "sum"),
        total_diesel_liters=("diesel_consumed_liters", "sum"),
    ).reset_index().round(0)


def ebitda_impact_from_disruption(energy_df: pd.DataFrame, sales_df: pd.DataFrame,
                                   stores_df: pd.DataFrame) -> pd.DataFrame:
    """Estimate profit lost due to blackouts.

    Logic: For each blackout hour, estimate lost sales based on
    average hourly sales for that store. EBITDA impact = lost sales * margin.
    """
    # Average hourly sales per store
    hourly_avg = sales_df.groupby("store_id").agg(
        avg_hourly_sales=("sales_mmk", "mean"),
        avg_hourly_margin=("gross_margin_mmk", "mean"),
    ).reset_index()

    # Daily blackout hours per store
    daily = energy_df[["date", "store_id", "blackout_hours", "diesel_cost_mmk"]].copy()
    daily = daily.merge(hourly_avg, on="store_id", how="left")

    # Lost margin = blackout hours * avg hourly margin (not all lost, some covered by generator)
    # Assume 30% of blackout hours have NO coverage (generator gap)
    daily["uncovered_hours"] = daily["blackout_hours"] * 0.3
    daily["lost_margin_mmk"] = daily["uncovered_hours"] * daily["avg_hourly_margin"]
    daily["total_impact_mmk"] = daily["lost_margin_mmk"] + daily["diesel_cost_mmk"]

    return daily


def energy_resilience_index(energy_df: pd.DataFrame, sales_df: pd.DataFrame) -> pd.DataFrame:
    """ERI: Percentage of operating days where the store was profitable despite disruption.

    A day is 'resilient' if daily gross margin > daily total energy cost.
    """
    daily_sales = sales_df.groupby(["date", "store_id"]).agg(
        daily_margin=("gross_margin_mmk", "sum"),
    ).reset_index()

    merged = energy_df[["date", "store_id", "total_energy_cost_mmk"]].merge(
        daily_sales, on=["date", "store_id"], how="left"
    )
    merged["is_resilient"] = merged["daily_margin"] > merged["total_energy_cost_mmk"]

    eri = merged.groupby("store_id").agg(
        resilient_days=("is_resilient", "sum"),
        total_days=("is_resilient", "count"),
    ).reset_index()
    eri["eri_pct"] = (eri["resilient_days"] / eri["total_days"] * 100).round(1)

    return eri


def solar_coverage_pct(energy_df: pd.DataFrame, stores_df: pd.DataFrame) -> pd.DataFrame:
    """Percentage of total energy demand met by solar (for solar-equipped sites)."""
    solar_stores = stores_df[stores_df["has_solar"] == True]["store_id"].tolist()
    solar_data = energy_df[energy_df["store_id"].isin(solar_stores)].copy()

    # Total demand approximation: grid_hours + generator_hours (in hours of operation)
    solar_data["total_demand_proxy"] = solar_data["grid_hours"] + solar_data["generator_hours"]
    # Solar contribution proxy: solar_kwh / (generator_kw * total_hours) — simplified
    result = solar_data.groupby("store_id").agg(
        total_solar_kwh=("solar_kwh", "sum"),
        total_diesel_liters=("diesel_consumed_liters", "sum"),
        avg_daily_solar=("solar_kwh", "mean"),
    ).reset_index()

    return result


def diesel_dependency_ratio(energy_df: pd.DataFrame) -> pd.DataFrame:
    """Percentage of total energy cost from diesel (vs grid)."""
    result = energy_df.groupby("store_id").agg(
        total_diesel_cost=("diesel_cost_mmk", "sum"),
        total_energy_cost=("total_energy_cost_mmk", "sum"),
    ).reset_index()

    result["diesel_dependency_pct"] = (
        result["total_diesel_cost"] / result["total_energy_cost"].replace(0, np.nan) * 100
    ).round(1)

    return result


def days_of_diesel_coverage(inventory_df: pd.DataFrame, as_of_date=None) -> pd.DataFrame:
    """Current days of diesel coverage per store."""
    if as_of_date is not None:
        data = inventory_df[inventory_df["date"] == pd.to_datetime(as_of_date)]
    else:
        # Latest date
        data = inventory_df[inventory_df["date"] == inventory_df["date"].max()]

    return data[["store_id", "diesel_stock_liters", "days_of_coverage",
                 "supplier_lead_time_days"]].copy()


def generator_efficiency_score(energy_df: pd.DataFrame, stores_df: pd.DataFrame) -> pd.DataFrame:
    """Compare actual diesel consumption vs expected based on generator specs.

    Expected = generator_kw * hours * consumption_rate (from settings)
    Score = (expected - actual) / expected * 100
    Positive = efficient, Negative = wasteful
    """
    merged = energy_df.merge(
        stores_df[["store_id", "generator_kw"]], on="store_id", how="left"
    )

    # Expected consumption: kW * hours * 0.3L/kWh / 1000 * 10 (matching synthetic formula)
    merged["expected_liters"] = (
        merged["generator_kw"] * merged["generator_hours"] * 0.3 * 0.8 / 1000 * 10
    )

    result = merged.groupby("store_id").agg(
        total_actual=("diesel_consumed_liters", "sum"),
        total_expected=("expected_liters", "sum"),
    ).reset_index()

    result["efficiency_score"] = (
        (result["total_expected"] - result["total_actual"])
        / result["total_expected"].replace(0, np.nan) * 100
    ).round(1)

    # Positive = using less than expected (good)
    # Negative = using more than expected (bad)
    result["status"] = result["efficiency_score"].apply(
        lambda x: "Efficient" if x >= 0 else ("Warning" if x >= -15 else "Critical")
    )

    return result

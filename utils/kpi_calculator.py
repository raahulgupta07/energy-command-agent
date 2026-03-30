"""
KPI Calculator - Shared formulas used across models and dashboards.
All monetary values in MMK unless noted.

Existing KPIs (8):
  energy_cost_pct_of_sales, diesel_cost_per_store_per_day,
  ebitda_impact_from_disruption, energy_resilience_index,
  solar_coverage_pct, diesel_dependency_ratio,
  days_of_diesel_coverage, generator_efficiency_score

New KPIs (7) — from BCP Framework doc:
  ebitda_per_operating_hour (B2), generator_ebitda_contribution (G1),
  cold_chain_uptime_pct (G2), solar_diesel_offset_kpi (G6),
  data_submission_compliance (G3), ai_adoption_rate (G5),
  price_response_time (G4)
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


# ══════════════════════════════════════════════════════════════════════════════
# NEW KPIs — from BCP Framework Document
# ══════════════════════════════════════════════════════════════════════════════

def ebitda_per_operating_hour(energy_df: pd.DataFrame, sales_df: pd.DataFrame,
                               stores_df: pd.DataFrame,
                               labour_costs: dict = None) -> pd.DataFrame:
    """EBITDA per operating hour — the core profitability engine (B2).

    Formula: Revenue/hr - COGS/hr - Labour/hr - Energy/hr - Spoilage_Risk/hr

    Args:
        energy_df: daily_energy with diesel_cost_mmk, grid_cost_mmk, generator_hours
        sales_df: store_sales with hourly sales_mmk, gross_margin_mmk
        stores_df: stores with store_id, channel, generator_kw
        labour_costs: dict of channel → MMK/hr (from settings.LABOUR_COST_PER_HOUR)
    """
    if labour_costs is None:
        from config.settings import LABOUR_COST_PER_HOUR
        labour_costs = LABOUR_COST_PER_HOUR

    # Hourly averages per store
    hourly = sales_df.groupby("store_id").agg(
        avg_revenue_per_hr=("sales_mmk", "mean"),
        avg_margin_per_hr=("gross_margin_mmk", "mean"),
    ).reset_index()

    # COGS/hr = revenue - margin
    hourly["avg_cogs_per_hr"] = hourly["avg_revenue_per_hr"] - hourly["avg_margin_per_hr"]

    # Energy cost per hour from daily data
    energy_hourly = energy_df.copy()
    operating_hours = 16  # 6am-10pm
    energy_hourly["energy_cost_per_hr"] = energy_hourly["total_energy_cost_mmk"] / operating_hours
    energy_agg = energy_hourly.groupby("store_id").agg(
        avg_energy_per_hr=("energy_cost_per_hr", "mean"),
        avg_diesel_cost_per_hr=("diesel_cost_mmk", lambda x: x.mean() / operating_hours),
        avg_generator_hours=("generator_hours", "mean"),
    ).reset_index()

    # Merge all
    result = hourly.merge(energy_agg, on="store_id", how="left")
    result = result.merge(stores_df[["store_id", "channel"]], on="store_id", how="left")

    # Labour cost per hour from channel
    result["labour_per_hr"] = result["channel"].map(labour_costs).fillna(15000)

    # Use labour_cost_mmk from sales_df if available
    if "labour_cost_mmk" in sales_df.columns:
        labour_from_data = sales_df.groupby("store_id")["labour_cost_mmk"].mean().reset_index()
        labour_from_data.columns = ["store_id", "labour_from_data"]
        result = result.merge(labour_from_data, on="store_id", how="left")
        # Use actual data where available, else channel default
        result["labour_per_hr"] = result["labour_from_data"].fillna(result["labour_per_hr"])
        result.drop(columns=["labour_from_data"], inplace=True)

    # EBITDA/hr = Margin/hr - Labour/hr - Energy/hr
    # (Margin already excludes COGS, so: Margin - Labour - Energy)
    result["ebitda_per_hr"] = (
        result["avg_margin_per_hr"] - result["labour_per_hr"] - result["avg_energy_per_hr"]
    ).round(0)

    # Generator-specific EBITDA/hr (during generator hours, diesel cost is higher)
    result["ebitda_per_generator_hr"] = (
        result["avg_margin_per_hr"] - result["labour_per_hr"] - result["avg_diesel_cost_per_hr"]
    ).round(0)

    result["is_profitable_on_generator"] = result["ebitda_per_generator_hr"] > 0

    return result[["store_id", "channel", "avg_revenue_per_hr", "avg_margin_per_hr",
                    "avg_cogs_per_hr", "labour_per_hr", "avg_energy_per_hr",
                    "avg_diesel_cost_per_hr", "ebitda_per_hr", "ebitda_per_generator_hr",
                    "is_profitable_on_generator"]]


def generator_ebitda_contribution(energy_df: pd.DataFrame, sales_df: pd.DataFrame,
                                   stores_df: pd.DataFrame,
                                   labour_costs: dict = None) -> pd.DataFrame:
    """Site EBITDA during generator-running hours only (G1). Target: > 0 all sites.

    Isolates profitability during generator operation to answer:
    "Is it worth running the generator at this store?"
    """
    ebitda = ebitda_per_operating_hour(energy_df, sales_df, stores_df, labour_costs)

    result = ebitda[["store_id", "channel", "ebitda_per_generator_hr",
                      "is_profitable_on_generator"]].copy()

    # Merge with avg generator hours to get total contribution
    gen_hours = energy_df.groupby("store_id")["generator_hours"].mean().reset_index()
    gen_hours.columns = ["store_id", "avg_daily_generator_hours"]
    result = result.merge(gen_hours, on="store_id", how="left")

    result["daily_generator_ebitda"] = (
        result["ebitda_per_generator_hr"] * result["avg_daily_generator_hours"]
    ).round(0)

    result["status"] = result["daily_generator_ebitda"].apply(
        lambda x: "Profitable" if x > 0 else ("Breakeven" if x == 0 else "Loss-making")
    )

    return result


def cold_chain_uptime_pct(temp_df: pd.DataFrame) -> pd.DataFrame:
    """Cold chain uptime: hours at correct temperature / total hours (G2). Target: > 99.5%.

    Args:
        temp_df: temperature_logs with store_id, zone, is_breach columns
    """
    if temp_df is None or len(temp_df) == 0:
        return pd.DataFrame(columns=["store_id", "total_readings", "breach_count",
                                      "uptime_pct", "status"])

    result = temp_df.groupby("store_id").agg(
        total_readings=("is_breach", "count"),
        breach_count=("is_breach", "sum"),
    ).reset_index()

    result["uptime_pct"] = (
        (result["total_readings"] - result["breach_count"])
        / result["total_readings"] * 100
    ).round(2)

    result["status"] = result["uptime_pct"].apply(
        lambda x: "Excellent" if x >= 99.5 else ("Good" if x >= 98 else ("Warning" if x >= 95 else "Critical"))
    )

    # Also by zone
    by_zone = temp_df.groupby(["store_id", "zone"]).agg(
        readings=("is_breach", "count"),
        breaches=("is_breach", "sum"),
    ).reset_index()
    by_zone["uptime_pct"] = ((by_zone["readings"] - by_zone["breaches"]) / by_zone["readings"] * 100).round(2)

    return result


def solar_diesel_offset_kpi(energy_df: pd.DataFrame, stores_df: pd.DataFrame,
                             diesel_price_mmk: float = 3000) -> pd.DataFrame:
    """Solar diesel offset: litres and MMK saved per site per day (G6).

    Calculates how much diesel each solar site avoids burning due to solar generation.
    """
    from config.settings import DIESEL

    solar_stores = stores_df[stores_df["has_solar"] == True]["store_id"].tolist()
    solar_data = energy_df[energy_df["store_id"].isin(solar_stores)].copy()

    if len(solar_data) == 0:
        return pd.DataFrame(columns=["store_id", "avg_daily_solar_kwh",
                                      "diesel_offset_liters_per_day", "cost_saving_per_day_mmk"])

    consumption_rate = DIESEL.get("consumption_per_kwh", 0.3)

    result = solar_data.groupby("store_id").agg(
        avg_daily_solar_kwh=("solar_kwh", "mean"),
        total_solar_kwh=("solar_kwh", "sum"),
        days=("date", "nunique"),
    ).reset_index()

    # Diesel offset = solar_kwh * consumption_rate (L/kWh)
    result["diesel_offset_liters_per_day"] = (
        result["avg_daily_solar_kwh"] * consumption_rate
    ).round(1)

    result["cost_saving_per_day_mmk"] = (
        result["diesel_offset_liters_per_day"] * diesel_price_mmk
    ).round(0)

    result["total_diesel_saved_liters"] = (
        result["total_solar_kwh"] * consumption_rate
    ).round(0)

    result["total_cost_saved_mmk"] = (
        result["total_diesel_saved_liters"] * diesel_price_mmk
    ).round(0)

    return result


def data_submission_compliance(quality_log: list = None) -> dict:
    """Data submission compliance KPI (G3). Target: > 95%.

    Reads from data_quality_log DB table.
    Returns dict with compliance metrics.
    """
    if quality_log is None:
        from utils.database import get_compliance_summary
        return get_compliance_summary()
    # If passed a list of dicts
    if not quality_log:
        return {"total_submissions": 0, "avg_completeness": 0, "late_count": 0,
                "compliance_pct": 0, "stores_below_90": 0}
    total = len(quality_log)
    late = sum(1 for q in quality_log if q.get("is_late"))
    avg_comp = sum(q.get("completeness_pct", 100) for q in quality_log) / total
    below_90 = len(set(q["store_id"] for q in quality_log if q.get("completeness_pct", 100) < 90))
    return {
        "total_submissions": total,
        "avg_completeness": round(avg_comp, 1),
        "late_count": late,
        "compliance_pct": round((total - late) / total * 100, 1),
        "stores_below_90": below_90,
    }


def ai_adoption_rate(rec_type: str = None) -> dict:
    """AI recommendation adoption rate KPI (G5). Target: > 80%.

    Reads from recommendation_tracking DB table.
    """
    from utils.database import get_adoption_rate
    return get_adoption_rate(rec_type)


def price_response_time(rec_type: str = "bulk_purchase") -> dict:
    """Price response time KPI (G4). Target: < 4 hours.

    Measures hours from price spike alert to procurement action.
    Reads from recommendation_tracking DB table.
    """
    from utils.database import get_avg_response_time
    return get_avg_response_time(rec_type)

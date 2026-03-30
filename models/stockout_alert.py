"""
Model 6: Diesel Stock-Out Risk Alert
Probabilistic model for diesel inventory risk.

Outputs:
- Days of coverage per site
- Stock-out probability
- Reallocation recommendations
- Auto-escalation triggers
"""

import pandas as pd
import numpy as np
from config.settings import THRESHOLDS


class StockoutAlert:
    """Monitor diesel inventory and predict stock-out risk."""

    def __init__(self):
        self.analysis = None

    def analyze(self, inventory_df: pd.DataFrame, energy_df: pd.DataFrame,
                stores_df: pd.DataFrame, as_of_date=None) -> pd.DataFrame:
        """Analyze stock-out risk for all stores.

        Args:
            inventory_df: diesel inventory data
            energy_df: daily energy data (for consumption trends)
            stores_df: store master
            as_of_date: analysis date (defaults to latest)

        Returns:
            DataFrame with risk analysis per store
        """
        if as_of_date is None:
            as_of_date = inventory_df["date"].max()

        results = []

        for _, store in stores_df.iterrows():
            sid = store["store_id"]

            # Current inventory
            inv = inventory_df[
                (inventory_df["store_id"] == sid) &
                (inventory_df["date"] == as_of_date)
            ]
            if len(inv) == 0:
                continue
            inv = inv.iloc[0]

            # Consumption trend (last 7 days)
            recent_energy = energy_df[
                (energy_df["store_id"] == sid) &
                (energy_df["date"] >= as_of_date - pd.Timedelta(days=7)) &
                (energy_df["date"] <= as_of_date)
            ]

            avg_consumption = recent_energy["diesel_consumed_liters"].mean() if len(recent_energy) > 0 else 0
            max_consumption = recent_energy["diesel_consumed_liters"].max() if len(recent_energy) > 0 else 0
            consumption_trend = 0
            if len(recent_energy) >= 3:
                vals = recent_energy["diesel_consumed_liters"].values
                consumption_trend = (vals[-1] - vals[0]) / max(len(vals), 1)

            # Days of coverage
            stock = inv["diesel_stock_liters"]
            days_coverage = stock / max(avg_consumption, 0.1)
            days_coverage_worst = stock / max(max_consumption, 0.1)

            # Stock-out probability (simple model)
            # Higher probability if: low stock, high consumption, increasing trend, long lead time
            lead_time = inv["supplier_lead_time_days"]

            # Can we survive until next delivery?
            survives_lead_time = days_coverage > lead_time
            buffer_days = days_coverage - lead_time

            # Probability calculation
            if days_coverage < THRESHOLDS["diesel_critical_days"]:
                stockout_prob = 0.95
            elif days_coverage < THRESHOLDS["diesel_warning_days"]:
                stockout_prob = 0.7 + (consumption_trend > 0) * 0.15
            elif buffer_days < 1:
                stockout_prob = 0.5
            elif buffer_days < 2:
                stockout_prob = 0.3
            else:
                stockout_prob = max(0.05, 0.2 - buffer_days * 0.02)

            stockout_prob = np.clip(stockout_prob, 0, 1)

            # Risk level
            if stockout_prob >= 0.7:
                risk_level = "CRITICAL"
            elif stockout_prob >= 0.4:
                risk_level = "HIGH"
            elif stockout_prob >= 0.2:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"

            # Action required
            if risk_level == "CRITICAL":
                action = "IMMEDIATE: Order diesel now or reallocate from nearby site"
            elif risk_level == "HIGH":
                action = "ORDER: Place diesel order within 24 hours"
            elif risk_level == "MEDIUM":
                action = "MONITOR: Check stock in 1-2 days"
            else:
                action = "OK: Sufficient stock"

            results.append({
                "store_id": sid,
                "name": store["name"],
                "sector": store["sector"],
                "channel": store["channel"],
                "township": store["township"],
                "diesel_stock_liters": round(stock, 1),
                "tank_capacity_liters": inv["tank_capacity_liters"],
                "fill_pct": round(stock / inv["tank_capacity_liters"] * 100, 1),
                "avg_daily_consumption": round(avg_consumption, 1),
                "max_daily_consumption": round(max_consumption, 1),
                "consumption_trend": "Increasing" if consumption_trend > 1 else ("Decreasing" if consumption_trend < -1 else "Stable"),
                "days_of_coverage": round(days_coverage, 1),
                "days_coverage_worst": round(days_coverage_worst, 1),
                "supplier_lead_time": round(lead_time, 1),
                "buffer_days": round(buffer_days, 1),
                "stockout_probability": round(stockout_prob, 3),
                "risk_level": risk_level,
                "action": action,
            })

        self.analysis = pd.DataFrame(results).sort_values("stockout_probability", ascending=False)
        return self.analysis

    def get_reallocation_plan(self) -> list:
        """Suggest diesel transfers from surplus to deficit stores.

        Returns:
            list of transfer recommendations
        """
        if self.analysis is None:
            return []

        transfers = []
        critical = self.analysis[self.analysis["risk_level"].isin(["CRITICAL", "HIGH"])].copy()
        surplus = self.analysis[
            (self.analysis["risk_level"] == "LOW") &
            (self.analysis["fill_pct"] > 60)
        ].copy()

        for _, deficit_store in critical.iterrows():
            # Find nearest surplus store (same sector preferred)
            same_sector = surplus[surplus["sector"] == deficit_store["sector"]]
            donor = same_sector.head(1) if len(same_sector) > 0 else surplus.head(1)

            if len(donor) == 0:
                continue

            donor = donor.iloc[0]

            # Calculate transfer amount
            needed = deficit_store["avg_daily_consumption"] * 3  # 3 days supply
            available = donor["diesel_stock_liters"] - (donor["avg_daily_consumption"] * 3)

            transfer_liters = min(needed, max(available, 0))

            if transfer_liters > 10:
                transfers.append({
                    "from_store": donor["name"],
                    "from_store_id": donor["store_id"],
                    "to_store": deficit_store["name"],
                    "to_store_id": deficit_store["store_id"],
                    "transfer_liters": round(transfer_liters, 0),
                    "reason": f"{deficit_store['name']} at {deficit_store['days_of_coverage']:.1f} days coverage",
                    "priority": "URGENT" if deficit_store["risk_level"] == "CRITICAL" else "HIGH",
                })

                # Remove donor from surplus pool
                surplus = surplus[surplus["store_id"] != donor["store_id"]]

        return transfers

    def get_alerts(self) -> list:
        """Generate stock-out alerts."""
        alerts = []

        if self.analysis is None:
            return alerts

        for _, row in self.analysis.iterrows():
            if row["risk_level"] == "CRITICAL":
                alerts.append({
                    "tier": 1,
                    "type": "DIESEL_STOCKOUT",
                    "store_id": row["store_id"],
                    "store_name": row["name"],
                    "message": (
                        f"CRITICAL: {row['name']} — {row['days_of_coverage']:.1f} days diesel remaining, "
                        f"{row['stockout_probability']*100:.0f}% stock-out risk"
                    ),
                })
            elif row["risk_level"] == "HIGH":
                alerts.append({
                    "tier": 2,
                    "type": "DIESEL_LOW",
                    "store_id": row["store_id"],
                    "store_name": row["name"],
                    "message": (
                        f"WARNING: {row['name']} — {row['days_of_coverage']:.1f} days diesel remaining, "
                        f"order within 24 hours"
                    ),
                })

        return alerts

    def score_suppliers(self, inventory_df: pd.DataFrame) -> pd.DataFrame:
        """Score supplier reliability using delivery dates from diesel_inventory (simplified C2).

        Uses: supplier_id, promised_delivery_date, actual_delivery_date columns.
        Returns DataFrame with supplier_id, on_time_pct, avg_delay_days, risk_rating.
        """
        # Filter rows with supplier data
        cols_needed = ["supplier_id", "promised_delivery_date", "actual_delivery_date"]
        has_supplier_data = all(c in inventory_df.columns for c in cols_needed)

        if not has_supplier_data:
            return pd.DataFrame()

        deliveries = inventory_df[
            inventory_df["supplier_id"].notna() &
            (inventory_df["supplier_id"] != "") &
            inventory_df["promised_delivery_date"].notna() &
            (inventory_df["promised_delivery_date"] != "") &
            inventory_df["actual_delivery_date"].notna() &
            (inventory_df["actual_delivery_date"] != "")
        ].copy()

        if len(deliveries) == 0:
            return pd.DataFrame()

        deliveries["promised_delivery_date"] = pd.to_datetime(deliveries["promised_delivery_date"], errors="coerce")
        deliveries["actual_delivery_date"] = pd.to_datetime(deliveries["actual_delivery_date"], errors="coerce")
        deliveries = deliveries.dropna(subset=["promised_delivery_date", "actual_delivery_date"])

        if len(deliveries) == 0:
            return pd.DataFrame()

        deliveries["delay_days"] = (
            deliveries["actual_delivery_date"] - deliveries["promised_delivery_date"]
        ).dt.total_seconds() / 86400

        deliveries["on_time"] = deliveries["delay_days"] <= 0.5  # Within half a day = on time

        result = deliveries.groupby("supplier_id").agg(
            total_deliveries=("on_time", "count"),
            on_time_count=("on_time", "sum"),
            avg_delay_days=("delay_days", "mean"),
            max_delay_days=("delay_days", "max"),
        ).reset_index()

        result["on_time_pct"] = (result["on_time_count"] / result["total_deliveries"] * 100).round(1)

        # Risk rating based on on-time %
        result["reliability_rating"] = result["on_time_pct"].apply(
            lambda x: "A" if x >= 95 else ("B" if x >= 85 else ("C" if x >= 70 else "D"))
        )
        result["risk_level"] = result["on_time_pct"].apply(
            lambda x: "LOW" if x >= 95 else ("MEDIUM" if x >= 85 else ("HIGH" if x >= 70 else "CRITICAL"))
        )

        return result.sort_values("on_time_pct", ascending=False)

    def get_summary(self) -> dict:
        """Network-wide inventory summary."""
        if self.analysis is None:
            return {}

        return {
            "total_stores": len(self.analysis),
            "critical_stores": (self.analysis["risk_level"] == "CRITICAL").sum(),
            "high_risk_stores": (self.analysis["risk_level"] == "HIGH").sum(),
            "medium_risk_stores": (self.analysis["risk_level"] == "MEDIUM").sum(),
            "low_risk_stores": (self.analysis["risk_level"] == "LOW").sum(),
            "total_diesel_stock": self.analysis["diesel_stock_liters"].sum(),
            "avg_days_coverage": self.analysis["days_of_coverage"].mean(),
            "min_days_coverage": self.analysis["days_of_coverage"].min(),
            "stores_below_2_days": (self.analysis["days_of_coverage"] < 2).sum(),
        }

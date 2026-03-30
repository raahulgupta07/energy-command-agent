"""
Model 4: Diesel Consumption Optimizer
Regression for expected consumption + Isolation Forest for anomaly detection.

Outputs:
- Efficiency score per generator
- Waste/anomaly alerts
- Optimal load schedule
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest
from config.settings import THRESHOLDS


class DieselOptimizer:
    """Optimize diesel consumption and detect anomalies."""

    def __init__(self):
        self.regression_model = None
        self.anomaly_model = None
        self.store_baselines = {}

    def fit(self, energy_df: pd.DataFrame, stores_df: pd.DataFrame):
        """Train consumption model and anomaly detector.

        Args:
            energy_df: daily energy data
            stores_df: store master with generator_kw
        """
        merged = energy_df.merge(stores_df[["store_id", "generator_kw"]], on="store_id", how="left")

        # Only use rows where generator ran
        gen_data = merged[merged["generator_hours"] > 0].copy()

        # ── Regression: expected consumption ──
        features = gen_data[["generator_kw", "generator_hours"]].copy()
        features["kw_hours"] = features["generator_kw"] * features["generator_hours"]
        target = gen_data["diesel_consumed_liters"]

        self.regression_model = LinearRegression()
        self.regression_model.fit(features[["generator_kw", "generator_hours", "kw_hours"]], target)

        # ── Anomaly detection: Isolation Forest ──
        gen_data["expected_liters"] = self.regression_model.predict(
            features[["generator_kw", "generator_hours", "kw_hours"]]
        )
        gen_data["consumption_ratio"] = gen_data["diesel_consumed_liters"] / gen_data["expected_liters"].clip(lower=0.1)

        self.anomaly_model = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100,
        )
        self.anomaly_model.fit(gen_data[["consumption_ratio", "generator_hours", "diesel_consumed_liters"]])

        # ── Store baselines ──
        for sid in gen_data["store_id"].unique():
            store_data = gen_data[gen_data["store_id"] == sid]
            self.store_baselines[sid] = {
                "avg_consumption": store_data["diesel_consumed_liters"].mean(),
                "avg_ratio": store_data["consumption_ratio"].mean(),
                "std_ratio": store_data["consumption_ratio"].std(),
            }

        return self

    def analyze(self, energy_df: pd.DataFrame, stores_df: pd.DataFrame) -> pd.DataFrame:
        """Analyze current consumption efficiency for all stores.

        Returns:
            DataFrame: store_id, efficiency_score, status, waste_liters, recommendations
        """
        merged = energy_df.merge(
            stores_df[["store_id", "name", "sector", "channel", "generator_kw"]],
            on="store_id", how="left"
        )

        results = []

        for sid in merged["store_id"].unique():
            store_data = merged[merged["store_id"] == sid]
            gen_data = store_data[store_data["generator_hours"] > 0]

            if len(gen_data) == 0:
                continue

            store_info = stores_df[stores_df["store_id"] == sid].iloc[0]

            # Calculate expected consumption
            features = gen_data[["generator_kw", "generator_hours"]].copy()
            features["kw_hours"] = features["generator_kw"] * features["generator_hours"]
            expected = self.regression_model.predict(features[["generator_kw", "generator_hours", "kw_hours"]])

            total_actual = gen_data["diesel_consumed_liters"].sum()
            total_expected = expected.sum()

            # Efficiency score: positive = efficient, negative = wasteful
            efficiency = (total_expected - total_actual) / max(total_expected, 0.1) * 100

            # Waste in liters
            waste = max(0, total_actual - total_expected)

            # Anomaly detection on recent data (last 7 days)
            recent = gen_data.tail(7)
            recent_features = recent[["generator_kw", "generator_hours"]].copy()
            recent_features["kw_hours"] = recent_features["generator_kw"] * recent_features["generator_hours"]
            recent_expected = self.regression_model.predict(
                recent_features[["generator_kw", "generator_hours", "kw_hours"]]
            )
            recent_ratio = recent["diesel_consumed_liters"].values / np.clip(recent_expected, 0.1, None)

            anomaly_features = pd.DataFrame({
                "consumption_ratio": recent_ratio,
                "generator_hours": recent["generator_hours"].values,
                "diesel_consumed_liters": recent["diesel_consumed_liters"].values,
            })
            anomalies = self.anomaly_model.predict(anomaly_features)
            anomaly_count = (anomalies == -1).sum()

            # Status
            if efficiency < -THRESHOLDS["efficiency_critical_pct"]:
                status = "Critical"
            elif efficiency < -THRESHOLDS["efficiency_warning_pct"]:
                status = "Warning"
            else:
                status = "Efficient"

            # Recommendations
            recommendations = []
            if status == "Critical":
                recommendations.append("Immediate generator maintenance required")
                recommendations.append("Check for fuel leaks or load imbalance")
            elif status == "Warning":
                recommendations.append("Schedule generator inspection")
                recommendations.append("Review load distribution")
            if anomaly_count > 2:
                recommendations.append(f"{anomaly_count} anomalous days detected in last 7 days")

            results.append({
                "store_id": sid,
                "name": store_info["name"],
                "sector": store_info["sector"],
                "channel": store_info["channel"],
                "generator_kw": store_info["generator_kw"],
                "total_actual_liters": round(total_actual, 1),
                "total_expected_liters": round(total_expected, 1),
                "waste_liters": round(waste, 1),
                "efficiency_score": round(efficiency, 1),
                "status": status,
                "anomaly_days_7d": int(anomaly_count),
                "avg_daily_consumption": round(gen_data["diesel_consumed_liters"].mean(), 1),
                "recommendations": "; ".join(recommendations) if recommendations else "Normal operation",
            })

        return pd.DataFrame(results).sort_values("efficiency_score")

    def get_alerts(self, analysis_df: pd.DataFrame) -> list:
        """Generate efficiency alerts."""
        alerts = []

        for _, row in analysis_df.iterrows():
            if row["status"] == "Critical":
                alerts.append({
                    "tier": 2,
                    "type": "EFFICIENCY_CRITICAL",
                    "store_id": row["store_id"],
                    "store_name": row["name"],
                    "message": (
                        f"Generator at {row['name']}: {abs(row['efficiency_score']):.0f}% "
                        f"above expected consumption — {row['waste_liters']:.0f}L wasted"
                    ),
                })
            elif row["anomaly_days_7d"] >= 3:
                alerts.append({
                    "tier": 2,
                    "type": "CONSUMPTION_ANOMALY",
                    "store_id": row["store_id"],
                    "store_name": row["name"],
                    "message": (
                        f"{row['name']}: {row['anomaly_days_7d']} anomalous consumption days "
                        f"in last 7 days — investigate"
                    ),
                })

        return alerts

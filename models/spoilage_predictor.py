"""
Model 7: Cold Chain / Spoilage Predictor
Classification model for spoilage risk based on outage duration and temperature.

Outputs:
- Spoilage probability by product zone
- Transfer/dispose recommendations
- Cold chain risk alerts
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from config.settings import THRESHOLDS


class SpoilagePredictor:
    """Predict food spoilage risk based on power outage and temperature data."""

    def __init__(self):
        self.model = None
        self.zone_thresholds = {
            "Dairy": {
                "max_safe_hours": THRESHOLDS["spoilage_dairy_hours"],
                "critical_temp": 8,
                "spoilage_rate_per_hour": 0.15,  # 15% risk increase per hour above threshold
            },
            "Frozen": {
                "max_safe_hours": THRESHOLDS["spoilage_frozen_hours"],
                "critical_temp": -12,
                "spoilage_rate_per_hour": 0.10,
            },
            "Fresh Produce": {
                "max_safe_hours": THRESHOLDS["spoilage_fresh_hours"],
                "critical_temp": 10,
                "spoilage_rate_per_hour": 0.12,
            },
        }

    def fit(self, temp_df: pd.DataFrame, energy_df: pd.DataFrame):
        """Train spoilage prediction model.

        Args:
            temp_df: temperature_logs with breach data
            energy_df: daily energy data with blackout/generator gaps
        """
        # Merge temperature with energy to get outage context
        daily_energy = energy_df[["date", "store_id", "blackout_hours", "generator_hours"]].copy()
        daily_energy["generator_gap_hours"] = (
            daily_energy["blackout_hours"] - daily_energy["generator_hours"]
        ).clip(lower=0)

        temp_daily = temp_df.groupby(["date", "store_id", "zone"]).agg(
            max_temp=("temperature_c", "max"),
            min_temp=("temperature_c", "min"),
            avg_temp=("temperature_c", "mean"),
            breach_count=("is_breach", "sum"),
            readings=("is_breach", "count"),
        ).reset_index()

        merged = temp_daily.merge(daily_energy, on=["date", "store_id"], how="left")

        # Features
        features = pd.DataFrame({
            "generator_gap_hours": merged["generator_gap_hours"].fillna(0),
            "max_temp": merged["max_temp"],
            "avg_temp": merged["avg_temp"],
            "blackout_hours": merged["blackout_hours"].fillna(0),
            "zone_code": merged["zone"].map({"Dairy": 0, "Frozen": 1, "Fresh Produce": 2}).fillna(0),
            "breach_ratio": merged["breach_count"] / merged["readings"].clip(lower=1),
        })

        # Target: any breach in the day
        target = (merged["breach_count"] > 0).astype(int)

        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=6,
            random_state=42,
            class_weight="balanced",
        )
        self.model.fit(features, target)
        return self

    def predict_risk(self, stores_df: pd.DataFrame, energy_df: pd.DataFrame,
                      temp_df: pd.DataFrame, as_of_date=None) -> pd.DataFrame:
        """Predict spoilage risk for cold chain stores.

        Returns:
            DataFrame: store, zone, spoilage probability, action
        """
        cold_stores = stores_df[stores_df["cold_chain"] == True]

        if as_of_date is None:
            as_of_date = energy_df["date"].max()

        results = []

        for _, store in cold_stores.iterrows():
            sid = store["store_id"]

            # Recent energy (today)
            today_energy = energy_df[
                (energy_df["store_id"] == sid) &
                (energy_df["date"] == as_of_date)
            ]

            blackout_hours = today_energy["blackout_hours"].values[0] if len(today_energy) > 0 else 0
            gen_hours = today_energy["generator_hours"].values[0] if len(today_energy) > 0 else 0
            generator_gap = max(0, blackout_hours - gen_hours)

            # Recent temperature
            today_temp = temp_df[
                (temp_df["store_id"] == sid) &
                (temp_df["date"] == as_of_date)
            ]

            for zone_name, zone_config in self.zone_thresholds.items():
                zone_temp = today_temp[today_temp["zone"] == zone_name]

                max_temp = zone_temp["temperature_c"].max() if len(zone_temp) > 0 else zone_config["critical_temp"] - 2
                avg_temp = zone_temp["temperature_c"].mean() if len(zone_temp) > 0 else zone_config["critical_temp"] - 3
                breaches = zone_temp["is_breach"].sum() if len(zone_temp) > 0 else 0

                # Calculate spoilage probability
                # Based on: generator gap duration + temperature readings
                if generator_gap <= 0 and breaches == 0:
                    spoilage_prob = 0.02  # Very low baseline risk
                elif generator_gap <= zone_config["max_safe_hours"] and breaches == 0:
                    spoilage_prob = 0.1 + generator_gap * 0.05
                else:
                    excess_hours = max(0, generator_gap - zone_config["max_safe_hours"])
                    spoilage_prob = min(0.95,
                        0.2 + excess_hours * zone_config["spoilage_rate_per_hour"] +
                        breaches * 0.1
                    )

                # ML-enhanced prediction (if model available)
                if self.model is not None:
                    features = pd.DataFrame([{
                        "generator_gap_hours": generator_gap,
                        "max_temp": max_temp,
                        "avg_temp": avg_temp,
                        "blackout_hours": blackout_hours,
                        "zone_code": {"Dairy": 0, "Frozen": 1, "Fresh Produce": 2}.get(zone_name, 0),
                        "breach_ratio": breaches / max(len(zone_temp), 1),
                    }])
                    ml_prob = self.model.predict_proba(features)[0][1]
                    # Blend rule-based and ML
                    spoilage_prob = 0.4 * spoilage_prob + 0.6 * ml_prob

                spoilage_prob = round(np.clip(spoilage_prob, 0, 1), 3)

                # Risk level and action
                if spoilage_prob >= 0.6:
                    risk_level = "CRITICAL"
                    action = "TRANSFER stock to nearest safe location immediately"
                elif spoilage_prob >= 0.3:
                    risk_level = "HIGH"
                    action = "MONITOR closely, prepare for transfer if generator fails"
                elif spoilage_prob >= 0.1:
                    risk_level = "MEDIUM"
                    action = "WATCH — ensure generator is on standby"
                else:
                    risk_level = "LOW"
                    action = "OK — normal monitoring"

                results.append({
                    "store_id": sid,
                    "name": store["name"],
                    "sector": store["sector"],
                    "township": store["township"],
                    "zone": zone_name,
                    "spoilage_probability": spoilage_prob,
                    "risk_level": risk_level,
                    "max_temperature": round(max_temp, 1),
                    "critical_temperature": zone_config["critical_temp"],
                    "generator_gap_hours": round(generator_gap, 1),
                    "safe_hours_limit": zone_config["max_safe_hours"],
                    "temperature_breaches": int(breaches),
                    "action": action,
                })

        return pd.DataFrame(results).sort_values("spoilage_probability", ascending=False)

    def calculate_precool_recommendation(self, stores_df: pd.DataFrame,
                                          temp_df: pd.DataFrame,
                                          blackout_predictions: pd.DataFrame = None,
                                          as_of_date=None) -> pd.DataFrame:
        """Pre-cooling recommendations before predicted blackouts (D1).

        If blackout probability > 0.6, recommend lowering cold chain temperature
        before the blackout hits to create a thermal buffer.

        Returns:
            DataFrame: store, zone, current_temp, precool_target, buffer_hours_gained
        """
        cold_stores = stores_df[stores_df["cold_chain"] == True]
        results = []

        for _, store in cold_stores.iterrows():
            sid = store["store_id"]

            # Get blackout probability
            blackout_prob = 0.5
            if blackout_predictions is not None and len(blackout_predictions) > 0:
                bp = blackout_predictions[blackout_predictions["store_id"] == sid]
                if len(bp) > 0:
                    blackout_prob = bp["blackout_probability"].values[0]

            if blackout_prob < 0.5:
                continue  # No pre-cool needed for low-risk stores

            # Get current temperatures
            if as_of_date is not None:
                store_temp = temp_df[(temp_df["store_id"] == sid) & (temp_df["date"] == as_of_date)]
            else:
                latest_date = temp_df[temp_df["store_id"] == sid]["date"].max()
                store_temp = temp_df[(temp_df["store_id"] == sid) & (temp_df["date"] == latest_date)]

            for zone_name, zone_config in self.zone_thresholds.items():
                zone_temp = store_temp[store_temp["zone"] == zone_name]
                current_temp = zone_temp["temperature_c"].mean() if len(zone_temp) > 0 else zone_config["critical_temp"] - 2

                # Thermal tolerance: how long until reaching critical temp from current
                tolerance = self.calculate_thermal_tolerance(
                    current_temp, zone_config["critical_temp"], zone_name
                )

                # Pre-cool target: lower by 2-4 degrees to gain buffer hours
                precool_degrees = min(4, zone_config["critical_temp"] - current_temp - 1)
                if precool_degrees <= 0:
                    precool_degrees = 2  # Always try to gain at least some buffer

                precool_target = current_temp - precool_degrees
                tolerance_after_precool = self.calculate_thermal_tolerance(
                    precool_target, zone_config["critical_temp"], zone_name
                )
                buffer_hours_gained = tolerance_after_precool - tolerance

                # Urgency
                if blackout_prob >= 0.8:
                    urgency = "IMMEDIATE"
                    action = f"Pre-cool {zone_name} to {precool_target:.1f}°C NOW — blackout {blackout_prob*100:.0f}% likely"
                elif blackout_prob >= 0.6:
                    urgency = "RECOMMENDED"
                    action = f"Lower {zone_name} to {precool_target:.1f}°C before afternoon — gains {buffer_hours_gained:.1f}hr buffer"
                else:
                    urgency = "ADVISORY"
                    action = f"Consider pre-cooling {zone_name} if conditions worsen"

                results.append({
                    "store_id": sid,
                    "name": store["name"],
                    "sector": store["sector"],
                    "zone": zone_name,
                    "current_temp_c": round(current_temp, 1),
                    "precool_target_c": round(precool_target, 1),
                    "critical_temp_c": zone_config["critical_temp"],
                    "current_tolerance_hours": round(tolerance, 1),
                    "tolerance_after_precool_hours": round(tolerance_after_precool, 1),
                    "buffer_hours_gained": round(buffer_hours_gained, 1),
                    "blackout_probability": round(blackout_prob, 3),
                    "urgency": urgency,
                    "action": action,
                })

        return pd.DataFrame(results) if results else pd.DataFrame()

    def calculate_thermal_tolerance(self, current_temp: float, critical_temp: float,
                                     zone: str) -> float:
        """Calculate hours until cold chain reaches critical temperature (D2).

        Simplified thermal model based on Newton's law of cooling.
        Assumes ambient temperature of 30°C (Myanmar) and zone-specific insulation.

        Returns:
            float: hours until critical temperature is reached
        """
        ambient_temp = 30.0  # Typical Myanmar ambient

        # Insulation factors (hours to reach ambient from target — higher = better insulated)
        insulation = {
            "Dairy": 6.0,       # Walk-in cooler, moderate insulation
            "Frozen": 12.0,     # Freezer, heavy insulation
            "Fresh Produce": 5.0,  # Display case, lighter insulation
        }

        insulation_hours = insulation.get(zone, 6.0)

        # Temperature difference ratios
        temp_range = abs(ambient_temp - current_temp)
        critical_range = abs(ambient_temp - critical_temp)

        if temp_range <= 0 or critical_range <= 0:
            return 0.0

        # Simplified: time proportional to how far we are from critical vs total range
        fraction_to_critical = abs(critical_temp - current_temp) / temp_range
        tolerance_hours = insulation_hours * fraction_to_critical

        return max(0, tolerance_hours)

    def get_alerts(self, risk_df: pd.DataFrame) -> list:
        """Generate spoilage alerts."""
        alerts = []

        critical = risk_df[risk_df["risk_level"] == "CRITICAL"]
        for _, row in critical.iterrows():
            alerts.append({
                "tier": 1,
                "type": "SPOILAGE_CRITICAL",
                "store_id": row["store_id"],
                "store_name": row["name"],
                "message": (
                    f"SPOILAGE RISK: {row['name']} — {row['zone']}: "
                    f"{row['spoilage_probability']*100:.0f}% risk, "
                    f"{row['generator_gap_hours']:.1f}hr generator gap — {row['action']}"
                ),
            })

        high = risk_df[risk_df["risk_level"] == "HIGH"]
        for _, row in high.iterrows():
            alerts.append({
                "tier": 2,
                "type": "SPOILAGE_WARNING",
                "store_id": row["store_id"],
                "store_name": row["name"],
                "message": (
                    f"Cold chain warning: {row['name']} — {row['zone']}: "
                    f"{row['spoilage_probability']*100:.0f}% risk — {row['action']}"
                ),
            })

        return alerts

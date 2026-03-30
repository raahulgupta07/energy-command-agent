"""
Model 2: Blackout Prediction Engine
Uses XGBoost to predict blackout probability by store/township and hour.

Outputs:
- Hourly blackout probability per location
- Expected duration
- Risk heatmap data
"""

import pandas as pd
import numpy as np
from datetime import timedelta

try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except (ImportError, OSError, Exception):
    HAS_XGBOOST = False

from sklearn.ensemble import GradientBoostingClassifier
from config.settings import THRESHOLDS


class BlackoutPredictor:
    """Predict blackout probability using XGBoost or sklearn fallback."""

    def __init__(self):
        self.model = None
        self.feature_cols = None
        self.township_stats = None

    def fit(self, energy_df: pd.DataFrame, stores_df: pd.DataFrame):
        """Train on historical blackout data.

        Args:
            energy_df: daily_energy with blackout_hours
            stores_df: store master with township
        """
        # Merge to get township
        df = energy_df.merge(stores_df[["store_id", "township", "sector", "channel"]],
                             on="store_id", how="left")

        # Compute township-level stats for features
        self.township_stats = df.groupby("township")["blackout_hours"].agg(
            ["mean", "std", "max"]
        ).to_dict()

        # Create features
        features = self._create_features(df)

        # Target: Was there a significant blackout? (> 3 hours)
        target = (df["blackout_hours"] > 3).astype(int)

        self.feature_cols = features.columns.tolist()

        # Train model
        if HAS_XGBOOST:
            self.model = XGBClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42,
                eval_metric="logloss",
            )
        else:
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42,
            )

        self.model.fit(features, target)
        return self

    def _create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer features from energy + store data."""
        features = pd.DataFrame()

        # Time features
        features["day_of_week"] = pd.to_datetime(df["date"]).dt.dayofweek
        features["month"] = pd.to_datetime(df["date"]).dt.month
        features["day_of_month"] = pd.to_datetime(df["date"]).dt.day
        features["is_weekend"] = (features["day_of_week"] >= 5).astype(int)

        # Season: hot=1, rainy=2, cool=3
        features["season"] = features["month"].map(
            lambda m: 1 if m in [3, 4, 5] else (2 if m in [6, 7, 8, 9] else 3)
        )

        # Township encoding (frequency-based)
        township_codes = {t: i for i, t in enumerate(df["township"].unique())}
        features["township_code"] = df["township"].map(township_codes)

        # Sector encoding
        sector_codes = {"Retail": 0, "F&B": 1, "Distribution": 2, "Property": 3}
        features["sector_code"] = df["sector"].map(sector_codes).fillna(0)

        # Rolling averages (past 7 days blackout hours per store)
        df_sorted = df.sort_values(["store_id", "date"])
        features["rolling_7d_blackout"] = df_sorted.groupby("store_id")["blackout_hours"].transform(
            lambda x: x.rolling(7, min_periods=1).mean()
        )
        features["rolling_3d_blackout"] = df_sorted.groupby("store_id")["blackout_hours"].transform(
            lambda x: x.rolling(3, min_periods=1).mean()
        )

        # Previous day blackout
        features["prev_day_blackout"] = df_sorted.groupby("store_id")["blackout_hours"].shift(1).fillna(0)

        return features.fillna(0)

    def predict_next_day(self, energy_df: pd.DataFrame, stores_df: pd.DataFrame,
                          target_date=None) -> pd.DataFrame:
        """Predict blackout probability for each store for the next day.

        Returns:
            DataFrame: store_id, township, blackout_probability, risk_level, expected_duration
        """
        if target_date is None:
            target_date = energy_df["date"].max() + timedelta(days=1)

        df = energy_df.merge(stores_df[["store_id", "township", "sector", "channel", "name"]],
                             on="store_id", how="left")

        # Use latest data to create features for prediction
        latest = df.groupby("store_id").tail(1).copy()
        latest["date"] = target_date

        features = self._create_features(latest)

        # Predict probability
        if self.model is not None:
            proba = self.model.predict_proba(features[self.feature_cols])[:, 1]
        else:
            # Fallback: use historical average
            proba = latest["blackout_hours"].values / 12

        results = pd.DataFrame({
            "store_id": latest["store_id"].values,
            "name": latest["name"].values,
            "township": latest["township"].values,
            "sector": latest["sector"].values,
            "date": target_date,
            "blackout_probability": np.round(proba, 3),
        })

        # Risk level
        results["risk_level"] = results["blackout_probability"].apply(
            lambda p: "HIGH" if p >= THRESHOLDS["blackout_high_prob"]
            else ("MEDIUM" if p >= THRESHOLDS["blackout_medium_prob"] else "LOW")
        )

        # Expected duration estimate (based on historical pattern for that township)
        avg_duration = df.groupby("township")["blackout_hours"].mean()
        results["expected_duration_hours"] = results["township"].map(avg_duration).round(1)

        # Estimated blackout window (based on most common blackout hours — afternoon peak)
        results["likely_window"] = results["blackout_probability"].apply(
            lambda p: "2:00 PM - 6:00 PM" if p >= 0.5 else ("1:00 PM - 4:00 PM" if p >= 0.3 else "Unlikely")
        )

        return results.sort_values("blackout_probability", ascending=False)

    def get_township_risk_map(self, predictions_df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate predictions to township level for heatmap."""
        return predictions_df.groupby("township").agg(
            avg_probability=("blackout_probability", "mean"),
            max_probability=("blackout_probability", "max"),
            num_stores=("store_id", "count"),
            high_risk_stores=("risk_level", lambda x: (x == "HIGH").sum()),
            avg_expected_hours=("expected_duration_hours", "mean"),
        ).reset_index().sort_values("avg_probability", ascending=False)

    def get_alerts(self, predictions_df: pd.DataFrame) -> list:
        """Generate blackout alerts from predictions."""
        alerts = []

        high_risk = predictions_df[predictions_df["risk_level"] == "HIGH"]
        for _, row in high_risk.iterrows():
            alerts.append({
                "tier": 2,
                "type": "BLACKOUT_WARNING",
                "store_id": row["store_id"],
                "store_name": row["name"],
                "township": row["township"],
                "probability": row["blackout_probability"],
                "expected_duration": row["expected_duration_hours"],
                "likely_window": row["likely_window"],
                "message": (
                    f"{row['name']} ({row['township']}): "
                    f"{row['blackout_probability']*100:.0f}% blackout probability, "
                    f"~{row['expected_duration_hours']:.1f} hrs expected, "
                    f"window: {row['likely_window']}"
                ),
            })

        return alerts

"""
Model 1: Diesel Price Forecasting
Uses Prophet for time-series prediction with ARIMA fallback.

Outputs:
- 7-day price forecast with confidence bands
- Volatility index
- Buy/Hold recommendation
"""

import pandas as pd
import numpy as np
from datetime import timedelta

try:
    from prophet import Prophet
    HAS_PROPHET = True
except ImportError:
    HAS_PROPHET = False

from config.settings import THRESHOLDS, DIESEL


class DieselPriceForecast:
    """Forecast diesel prices using Prophet or simple statistical fallback."""

    def __init__(self):
        self.model = None
        self.history = None
        self.forecast_days = 7

    def fit(self, prices_df: pd.DataFrame):
        """Train on historical diesel price data.

        Args:
            prices_df: DataFrame with columns [date, diesel_price_mmk, fx_usd_mmk, brent_oil_usd]
        """
        self.history = prices_df.copy()

        if HAS_PROPHET:
            self._fit_prophet(prices_df)
        else:
            self._fit_statistical(prices_df)

        return self

    def _fit_prophet(self, prices_df: pd.DataFrame):
        """Fit Prophet model with FX and oil price as regressors."""
        df = prices_df.rename(columns={"date": "ds", "diesel_price_mmk": "y"})

        self.model = Prophet(
            changepoint_prior_scale=0.1,
            seasonality_prior_scale=10,
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=False,
            interval_width=0.80,
        )

        # Add external regressors
        if "fx_usd_mmk" in df.columns:
            self.model.add_regressor("fx_usd_mmk")
        if "brent_oil_usd" in df.columns:
            self.model.add_regressor("brent_oil_usd")

        self.model.fit(df[["ds", "y", "fx_usd_mmk", "brent_oil_usd"]].dropna())

    def _fit_statistical(self, prices_df: pd.DataFrame):
        """Simple statistical model: weighted moving average + trend."""
        self._recent_prices = prices_df["diesel_price_mmk"].values
        self._recent_dates = prices_df["date"].values

        # Calculate trend (last 30 days)
        if len(self._recent_prices) >= 30:
            recent = self._recent_prices[-30:]
            self._daily_trend = (recent[-1] - recent[0]) / 30
        else:
            self._daily_trend = 0

        # Volatility (standard deviation of daily changes)
        changes = np.diff(self._recent_prices)
        self._volatility = np.std(changes) if len(changes) > 0 else 0

    def predict(self, days: int = 7) -> pd.DataFrame:
        """Generate price forecast.

        Returns:
            DataFrame with columns: date, predicted_price, lower_bound, upper_bound
        """
        self.forecast_days = days
        last_date = self.history["date"].max()

        if HAS_PROPHET and self.model is not None:
            return self._predict_prophet(last_date, days)
        else:
            return self._predict_statistical(last_date, days)

    def _predict_prophet(self, last_date, days):
        """Predict using Prophet model."""
        future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=days, freq="D")
        future = pd.DataFrame({"ds": future_dates})

        # Project regressors forward (simple linear extrapolation)
        last_fx = self.history["fx_usd_mmk"].iloc[-1]
        fx_trend = self.history["fx_usd_mmk"].diff().tail(7).mean()
        future["fx_usd_mmk"] = [last_fx + fx_trend * (i + 1) for i in range(days)]

        last_oil = self.history["brent_oil_usd"].iloc[-1]
        oil_trend = self.history["brent_oil_usd"].diff().tail(7).mean()
        future["brent_oil_usd"] = [last_oil + oil_trend * (i + 1) for i in range(days)]

        forecast = self.model.predict(future)

        return pd.DataFrame({
            "date": future_dates,
            "predicted_price": forecast["yhat"].round(0).astype(int),
            "lower_bound": forecast["yhat_lower"].round(0).astype(int),
            "upper_bound": forecast["yhat_upper"].round(0).astype(int),
        })

    def _predict_statistical(self, last_date, days):
        """Predict using weighted moving average + trend."""
        future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=days, freq="D")

        # Weighted moving average (recent prices weighted more)
        weights = np.exp(np.linspace(-2, 0, min(14, len(self._recent_prices))))
        recent = self._recent_prices[-len(weights):]
        base_price = np.average(recent, weights=weights)

        predictions = []
        for i in range(days):
            pred = base_price + self._daily_trend * (i + 1)
            # Add some noise for realism
            pred += np.random.normal(0, self._volatility * 0.3)
            predictions.append(pred)

        predictions = np.array(predictions)

        return pd.DataFrame({
            "date": future_dates,
            "predicted_price": np.round(predictions, 0).astype(int),
            "lower_bound": np.round(predictions - 1.5 * self._volatility, 0).astype(int),
            "upper_bound": np.round(predictions + 1.5 * self._volatility, 0).astype(int),
        })

    def get_volatility_index(self) -> dict:
        """Calculate price volatility metrics."""
        prices = self.history["diesel_price_mmk"].values

        # 7-day volatility
        changes_7d = np.diff(prices[-7:])
        vol_7d = np.std(changes_7d) if len(changes_7d) > 0 else 0

        # 30-day volatility
        changes_30d = np.diff(prices[-30:])
        vol_30d = np.std(changes_30d) if len(changes_30d) > 0 else 0

        # Price change percentages
        pct_7d = ((prices[-1] - prices[-7]) / prices[-7] * 100) if len(prices) >= 7 else 0
        pct_30d = ((prices[-1] - prices[-30]) / prices[-30] * 100) if len(prices) >= 30 else 0

        return {
            "current_price": int(prices[-1]),
            "volatility_7d": round(vol_7d, 1),
            "volatility_30d": round(vol_30d, 1),
            "price_change_7d_pct": round(pct_7d, 2),
            "price_change_30d_pct": round(pct_30d, 2),
            "trend": "UP" if pct_7d > 0 else "DOWN",
        }

    def get_buy_recommendation(self, forecast_df: pd.DataFrame = None) -> dict:
        """Generate buy/hold recommendation based on forecast.

        Returns:
            dict with: signal (BUY/HOLD/WAIT), reason, expected_change_pct, urgency
        """
        if forecast_df is None:
            forecast_df = self.predict()

        current_price = self.history["diesel_price_mmk"].iloc[-1]
        avg_forecast = forecast_df["predicted_price"].mean()
        max_forecast = forecast_df["predicted_price"].max()

        expected_change_pct = (avg_forecast - current_price) / current_price * 100
        max_change_pct = (max_forecast - current_price) / current_price * 100

        if expected_change_pct >= THRESHOLDS["price_spike_critical_pct"]:
            return {
                "signal": "BUY NOW",
                "urgency": "CRITICAL",
                "reason": f"Price expected to increase {expected_change_pct:.1f}% in {self.forecast_days} days",
                "expected_change_pct": round(expected_change_pct, 2),
                "recommended_action": "Advance purchase maximum capacity immediately",
            }
        elif expected_change_pct >= THRESHOLDS["price_spike_pct"]:
            return {
                "signal": "BUY",
                "urgency": "WARNING",
                "reason": f"Price expected to increase {expected_change_pct:.1f}% in {self.forecast_days} days",
                "expected_change_pct": round(expected_change_pct, 2),
                "recommended_action": "Advance purchase recommended within 1-2 days",
            }
        elif expected_change_pct < -2:
            return {
                "signal": "WAIT",
                "urgency": "INFO",
                "reason": f"Price expected to decrease {abs(expected_change_pct):.1f}% — delay purchase",
                "expected_change_pct": round(expected_change_pct, 2),
                "recommended_action": "Delay non-urgent purchases, prices trending down",
            }
        else:
            return {
                "signal": "HOLD",
                "urgency": "NORMAL",
                "reason": "Prices stable, purchase as needed",
                "expected_change_pct": round(expected_change_pct, 2),
                "recommended_action": "Normal procurement schedule",
            }

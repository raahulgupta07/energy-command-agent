"""
Data Loader - Toggle between sample and real data.
Provides consistent loading functions for all 8 data tables.
"""

import pandas as pd
from config.settings import get_data_dir


def _load(filename: str) -> pd.DataFrame:
    """Load a CSV file from the active data directory."""
    path = get_data_dir() / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Data file not found: {path}\n"
            f"Run 'python data/generators/synthetic_data.py' to generate sample data."
        )
    df = pd.read_csv(path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    return df


def load_stores() -> pd.DataFrame:
    return _load("stores.csv")


def load_daily_energy() -> pd.DataFrame:
    return _load("daily_energy.csv")


def load_diesel_prices() -> pd.DataFrame:
    return _load("diesel_prices.csv")


def load_diesel_inventory() -> pd.DataFrame:
    return _load("diesel_inventory.csv")


def load_store_sales() -> pd.DataFrame:
    return _load("store_sales.csv")


def load_solar_generation() -> pd.DataFrame:
    return _load("solar_generation.csv")


def load_temperature_logs() -> pd.DataFrame:
    return _load("temperature_logs.csv")


def load_fx_rates() -> pd.DataFrame:
    return _load("fx_rates.csv")


def load_all() -> dict:
    """Load all datasets into a dictionary."""
    return {
        "stores": load_stores(),
        "daily_energy": load_daily_energy(),
        "diesel_prices": load_diesel_prices(),
        "diesel_inventory": load_diesel_inventory(),
        "store_sales": load_store_sales(),
        "solar_generation": load_solar_generation(),
        "temperature_logs": load_temperature_logs(),
        "fx_rates": load_fx_rates(),
    }

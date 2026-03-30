"""
Energy Intelligence System - Global Configuration
Sectors, channels, stores, thresholds, and data paths.
"""

import os
from pathlib import Path

# ── Project Paths ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SAMPLE_DATA_DIR = DATA_DIR / "sample"
REAL_DATA_DIR = DATA_DIR / "real"

# Toggle: "sample" or "real"
DATA_SOURCE = os.environ.get("EIS_DATA_SOURCE", "sample")

def get_data_dir():
    return REAL_DATA_DIR if DATA_SOURCE == "real" else SAMPLE_DATA_DIR


# ── Currency & Locale ──────────────────────────────────────────────────────────
CURRENCY = "MMK"
CURRENCY_SYMBOL = "K"
DATE_FORMAT = "%Y-%m-%d"
TIMEZONE = "Asia/Yangon"


# ── Sectors & Channels ────────────────────────────────────────────────────────
SECTORS = {
    "Retail": {
        "channels": ["Hypermarket", "Supermarket", "Convenience"],
        "color": "#2196F3",
    },
    "F&B": {
        "channels": ["Bakery", "Restaurant", "Beverage"],
        "color": "#FF9800",
    },
    "Distribution": {
        "channels": ["Warehouse", "Cold Chain", "Logistics"],
        "color": "#4CAF50",
    },
    "Property": {
        "channels": ["Mall", "Office"],
        "color": "#9C27B0",
    },
}


# ── Store Definitions (55 Stores) ─────────────────────────────────────────────
# Townships in Yangon used for location context
TOWNSHIPS = [
    "Hlaing", "Insein", "Kamayut", "Mayangone", "Yankin",
    "Tamwe", "Bahan", "Sanchaung", "Dagon", "North Dagon",
    "South Dagon", "East Dagon", "Thaketa", "Dawbon", "Mingalar Taung Nyunt",
    "Botahtaung", "Pazundaung", "Latha", "Lanmadaw", "Kyimyindaing",
    "North Okkalapa", "South Okkalapa", "Thingangyun", "Shwepyithar", "Hlaing Tharyar",
]

STORES = [
    # ── Retail: Hypermarket (5) ──
    {"store_id": "RH-001", "name": "Hypermarket Hlaing",         "sector": "Retail", "channel": "Hypermarket",  "township": "Hlaing",              "has_solar": True,  "generator_kw": 250, "cold_chain": True},
    {"store_id": "RH-002", "name": "Hypermarket Insein",         "sector": "Retail", "channel": "Hypermarket",  "township": "Insein",              "has_solar": True,  "generator_kw": 250, "cold_chain": True},
    {"store_id": "RH-003", "name": "Hypermarket Yankin",         "sector": "Retail", "channel": "Hypermarket",  "township": "Yankin",              "has_solar": False, "generator_kw": 200, "cold_chain": True},
    {"store_id": "RH-004", "name": "Hypermarket North Dagon",    "sector": "Retail", "channel": "Hypermarket",  "township": "North Dagon",         "has_solar": False, "generator_kw": 200, "cold_chain": True},
    {"store_id": "RH-005", "name": "Hypermarket Shwepyithar",    "sector": "Retail", "channel": "Hypermarket",  "township": "Shwepyithar",         "has_solar": True,  "generator_kw": 300, "cold_chain": True},

    # ── Retail: Supermarket (10) ──
    {"store_id": "RS-001", "name": "Super Kamayut",              "sector": "Retail", "channel": "Supermarket",  "township": "Kamayut",             "has_solar": True,  "generator_kw": 100, "cold_chain": True},
    {"store_id": "RS-002", "name": "Super Mayangone",            "sector": "Retail", "channel": "Supermarket",  "township": "Mayangone",           "has_solar": False, "generator_kw": 100, "cold_chain": True},
    {"store_id": "RS-003", "name": "Super Tamwe",                "sector": "Retail", "channel": "Supermarket",  "township": "Tamwe",               "has_solar": False, "generator_kw": 80,  "cold_chain": True},
    {"store_id": "RS-004", "name": "Super Bahan",                "sector": "Retail", "channel": "Supermarket",  "township": "Bahan",               "has_solar": True,  "generator_kw": 100, "cold_chain": True},
    {"store_id": "RS-005", "name": "Super Sanchaung",            "sector": "Retail", "channel": "Supermarket",  "township": "Sanchaung",           "has_solar": False, "generator_kw": 80,  "cold_chain": True},
    {"store_id": "RS-006", "name": "Super Dagon",                "sector": "Retail", "channel": "Supermarket",  "township": "Dagon",               "has_solar": False, "generator_kw": 80,  "cold_chain": True},
    {"store_id": "RS-007", "name": "Super Thaketa",              "sector": "Retail", "channel": "Supermarket",  "township": "Thaketa",             "has_solar": False, "generator_kw": 80,  "cold_chain": True},
    {"store_id": "RS-008", "name": "Super South Dagon",          "sector": "Retail", "channel": "Supermarket",  "township": "South Dagon",         "has_solar": False, "generator_kw": 80,  "cold_chain": True},
    {"store_id": "RS-009", "name": "Super Thingangyun",          "sector": "Retail", "channel": "Supermarket",  "township": "Thingangyun",         "has_solar": True,  "generator_kw": 100, "cold_chain": True},
    {"store_id": "RS-010", "name": "Super Hlaing Tharyar",       "sector": "Retail", "channel": "Supermarket",  "township": "Hlaing Tharyar",      "has_solar": False, "generator_kw": 80,  "cold_chain": True},

    # ── Retail: Convenience (10) ──
    {"store_id": "RC-001", "name": "Conv. Botahtaung",           "sector": "Retail", "channel": "Convenience",  "township": "Botahtaung",          "has_solar": False, "generator_kw": 30,  "cold_chain": False},
    {"store_id": "RC-002", "name": "Conv. Pazundaung",           "sector": "Retail", "channel": "Convenience",  "township": "Pazundaung",          "has_solar": False, "generator_kw": 30,  "cold_chain": False},
    {"store_id": "RC-003", "name": "Conv. Latha",                "sector": "Retail", "channel": "Convenience",  "township": "Latha",               "has_solar": False, "generator_kw": 25,  "cold_chain": False},
    {"store_id": "RC-004", "name": "Conv. Lanmadaw",             "sector": "Retail", "channel": "Convenience",  "township": "Lanmadaw",            "has_solar": False, "generator_kw": 25,  "cold_chain": False},
    {"store_id": "RC-005", "name": "Conv. Kyimyindaing",         "sector": "Retail", "channel": "Convenience",  "township": "Kyimyindaing",        "has_solar": False, "generator_kw": 25,  "cold_chain": False},
    {"store_id": "RC-006", "name": "Conv. Dawbon",               "sector": "Retail", "channel": "Convenience",  "township": "Dawbon",              "has_solar": False, "generator_kw": 25,  "cold_chain": False},
    {"store_id": "RC-007", "name": "Conv. North Okkalapa",       "sector": "Retail", "channel": "Convenience",  "township": "North Okkalapa",      "has_solar": False, "generator_kw": 30,  "cold_chain": False},
    {"store_id": "RC-008", "name": "Conv. South Okkalapa",       "sector": "Retail", "channel": "Convenience",  "township": "South Okkalapa",      "has_solar": False, "generator_kw": 30,  "cold_chain": False},
    {"store_id": "RC-009", "name": "Conv. Mingalar Taung Nyunt", "sector": "Retail", "channel": "Convenience",  "township": "Mingalar Taung Nyunt","has_solar": False, "generator_kw": 25,  "cold_chain": False},
    {"store_id": "RC-010", "name": "Conv. East Dagon",           "sector": "Retail", "channel": "Convenience",  "township": "East Dagon",          "has_solar": False, "generator_kw": 25,  "cold_chain": False},

    # ── F&B: Bakery (5) ──
    {"store_id": "FB-001", "name": "Bakery Kamayut",             "sector": "F&B",   "channel": "Bakery",       "township": "Kamayut",             "has_solar": True,  "generator_kw": 60,  "cold_chain": True},
    {"store_id": "FB-002", "name": "Bakery Yankin",              "sector": "F&B",   "channel": "Bakery",       "township": "Yankin",              "has_solar": False, "generator_kw": 50,  "cold_chain": True},
    {"store_id": "FB-003", "name": "Bakery Hlaing",              "sector": "F&B",   "channel": "Bakery",       "township": "Hlaing",              "has_solar": False, "generator_kw": 50,  "cold_chain": True},
    {"store_id": "FB-004", "name": "Bakery Bahan",               "sector": "F&B",   "channel": "Bakery",       "township": "Bahan",               "has_solar": True,  "generator_kw": 60,  "cold_chain": True},
    {"store_id": "FB-005", "name": "Bakery Insein",              "sector": "F&B",   "channel": "Bakery",       "township": "Insein",              "has_solar": False, "generator_kw": 50,  "cold_chain": True},

    # ── F&B: Restaurant (5) ──
    {"store_id": "FR-001", "name": "Restaurant Sanchaung",       "sector": "F&B",   "channel": "Restaurant",   "township": "Sanchaung",           "has_solar": False, "generator_kw": 80,  "cold_chain": True},
    {"store_id": "FR-002", "name": "Restaurant Tamwe",           "sector": "F&B",   "channel": "Restaurant",   "township": "Tamwe",               "has_solar": False, "generator_kw": 80,  "cold_chain": True},
    {"store_id": "FR-003", "name": "Restaurant Mayangone",       "sector": "F&B",   "channel": "Restaurant",   "township": "Mayangone",           "has_solar": True,  "generator_kw": 100, "cold_chain": True},
    {"store_id": "FR-004", "name": "Restaurant Dagon",           "sector": "F&B",   "channel": "Restaurant",   "township": "Dagon",               "has_solar": False, "generator_kw": 80,  "cold_chain": True},
    {"store_id": "FR-005", "name": "Restaurant Hlaing Tharyar",  "sector": "F&B",   "channel": "Restaurant",   "township": "Hlaing Tharyar",      "has_solar": False, "generator_kw": 80,  "cold_chain": True},

    # ── F&B: Beverage (5) ──
    {"store_id": "FV-001", "name": "Beverage Botahtaung",        "sector": "F&B",   "channel": "Beverage",     "township": "Botahtaung",          "has_solar": False, "generator_kw": 20,  "cold_chain": False},
    {"store_id": "FV-002", "name": "Beverage Latha",             "sector": "F&B",   "channel": "Beverage",     "township": "Latha",               "has_solar": False, "generator_kw": 20,  "cold_chain": False},
    {"store_id": "FV-003", "name": "Beverage Pazundaung",        "sector": "F&B",   "channel": "Beverage",     "township": "Pazundaung",          "has_solar": False, "generator_kw": 20,  "cold_chain": False},
    {"store_id": "FV-004", "name": "Beverage Kyimyindaing",      "sector": "F&B",   "channel": "Beverage",     "township": "Kyimyindaing",        "has_solar": False, "generator_kw": 20,  "cold_chain": False},
    {"store_id": "FV-005", "name": "Beverage North Okkalapa",    "sector": "F&B",   "channel": "Beverage",     "township": "North Okkalapa",      "has_solar": False, "generator_kw": 20,  "cold_chain": False},

    # ── Distribution: Warehouse (3) ──
    {"store_id": "DW-001", "name": "Warehouse Hlaing Tharyar",   "sector": "Distribution", "channel": "Warehouse",  "township": "Hlaing Tharyar",  "has_solar": True,  "generator_kw": 200, "cold_chain": False},
    {"store_id": "DW-002", "name": "Warehouse Shwepyithar",      "sector": "Distribution", "channel": "Warehouse",  "township": "Shwepyithar",     "has_solar": True,  "generator_kw": 200, "cold_chain": False},
    {"store_id": "DW-003", "name": "Warehouse North Dagon",      "sector": "Distribution", "channel": "Warehouse",  "township": "North Dagon",     "has_solar": False, "generator_kw": 150, "cold_chain": False},

    # ── Distribution: Cold Chain (3) ──
    {"store_id": "DC-001", "name": "Cold Chain Insein",          "sector": "Distribution", "channel": "Cold Chain", "township": "Insein",           "has_solar": True,  "generator_kw": 180, "cold_chain": True},
    {"store_id": "DC-002", "name": "Cold Chain Hlaing",          "sector": "Distribution", "channel": "Cold Chain", "township": "Hlaing",           "has_solar": False, "generator_kw": 150, "cold_chain": True},
    {"store_id": "DC-003", "name": "Cold Chain Mayangone",       "sector": "Distribution", "channel": "Cold Chain", "township": "Mayangone",        "has_solar": False, "generator_kw": 150, "cold_chain": True},

    # ── Distribution: Logistics (2) ──
    {"store_id": "DL-001", "name": "Logistics Hub Shwepyithar",  "sector": "Distribution", "channel": "Logistics",  "township": "Shwepyithar",     "has_solar": False, "generator_kw": 80,  "cold_chain": False},
    {"store_id": "DL-002", "name": "Logistics Hub East Dagon",   "sector": "Distribution", "channel": "Logistics",  "township": "East Dagon",      "has_solar": False, "generator_kw": 80,  "cold_chain": False},

    # ── Property: Mall (4) ──
    {"store_id": "PM-001", "name": "Mall Central Yankin",        "sector": "Property", "channel": "Mall",     "township": "Yankin",              "has_solar": True,  "generator_kw": 500, "cold_chain": True},
    {"store_id": "PM-002", "name": "Mall Junction Insein",       "sector": "Property", "channel": "Mall",     "township": "Insein",              "has_solar": True,  "generator_kw": 400, "cold_chain": True},
    {"store_id": "PM-003", "name": "Mall Plaza Hlaing",          "sector": "Property", "channel": "Mall",     "township": "Hlaing",              "has_solar": False, "generator_kw": 350, "cold_chain": True},
    {"store_id": "PM-004", "name": "Mall City Dagon",            "sector": "Property", "channel": "Mall",     "township": "Dagon",               "has_solar": False, "generator_kw": 350, "cold_chain": True},

    # ── Property: Office (3) ──
    {"store_id": "PO-001", "name": "Office Tower Kamayut",       "sector": "Property", "channel": "Office",   "township": "Kamayut",             "has_solar": True,  "generator_kw": 150, "cold_chain": False},
    {"store_id": "PO-002", "name": "Office Park Bahan",          "sector": "Property", "channel": "Office",   "township": "Bahan",               "has_solar": False, "generator_kw": 120, "cold_chain": False},
    {"store_id": "PO-003", "name": "Office Hub Mayangone",       "sector": "Property", "channel": "Office",   "township": "Mayangone",           "has_solar": False, "generator_kw": 120, "cold_chain": False},
]


# ── Alert Thresholds ──────────────────────────────────────────────────────────
THRESHOLDS = {
    # Diesel stock-out
    "diesel_critical_days": 1,       # TIER 1: < 1 day → CRITICAL
    "diesel_warning_days": 2,        # TIER 2: < 2 days → WARNING
    "diesel_safe_days": 5,           # > 5 days → SAFE

    # Blackout probability
    "blackout_high_prob": 0.8,       # > 80% → pre-adjust operations
    "blackout_medium_prob": 0.5,     # > 50% → prepare generators

    # Store profitability
    "margin_breakeven_ratio": 1.0,   # diesel_cost/margin > 1.0 → losing money
    "margin_reduce_ratio": 0.8,      # diesel_cost/margin > 0.8 → consider reducing

    # Diesel price change
    "price_spike_pct": 5.0,          # > 5% predicted increase → buy alert
    "price_spike_critical_pct": 10.0,# > 10% predicted increase → urgent buy

    # Generator efficiency
    "efficiency_warning_pct": 15.0,  # > 15% above expected → warning
    "efficiency_critical_pct": 25.0, # > 25% above expected → critical

    # Spoilage (outage duration in hours)
    "spoilage_dairy_hours": 2,       # Dairy at risk after 2 hours
    "spoilage_frozen_hours": 4,      # Frozen at risk after 4 hours
    "spoilage_fresh_hours": 3,       # Fresh produce after 3 hours

    # Solar
    "solar_peak_start_hour": 10,     # Solar peak: 10am
    "solar_peak_end_hour": 15,       # Solar peak: 3pm
}


# ── Diesel Parameters ─────────────────────────────────────────────────────────
DIESEL = {
    "base_price_mmk": 2800,          # Base diesel price per liter (MMK)
    "price_range": (2400, 3600),     # Historical price range
    "consumption_per_kwh": 0.3,      # Liters per kWh generated
    "cost_per_kwh_grid": 50,         # Grid electricity cost (MMK/kWh)
    "usd_mmk_base": 3500,            # Base FX rate
    "usd_mmk_range": (3200, 4000),   # FX range
}


# ── Operating Modes ───────────────────────────────────────────────────────────
OPERATING_MODES = {
    "FULL": {
        "label": "Full Operation",
        "color": "#4CAF50",          # Green
        "load_pct": 1.0,
        "description": "All systems on, normal operations",
    },
    "REDUCED": {
        "label": "Reduced Operation",
        "color": "#FF9800",          # Orange
        "load_pct": 0.6,
        "description": "Essential refrigeration + lighting, no kitchen/AC",
    },
    "CRITICAL": {
        "label": "Critical Only",
        "color": "#F44336",          # Red
        "load_pct": 0.3,
        "description": "Refrigeration only, minimal staff",
    },
    "CLOSE": {
        "label": "Closed",
        "color": "#9E9E9E",          # Grey
        "load_pct": 0.0,
        "description": "Shutdown, secure perishables",
    },
}


# ── Data Generation Parameters ────────────────────────────────────────────────
DATA_GEN = {
    "start_date": "2025-10-01",
    "end_date": "2026-03-29",
    "blackout_hours_range": (0, 12),  # 0-12 hours per day
    "avg_blackout_hours": 5,          # Average 5 hours/day
    "solar_sites_count": 14,          # Number of solar-equipped stores
}


# ── Agent Configuration ──────────────────────────────────────────────────────
AGENT_CONFIG = {
    "enabled": os.environ.get("EIS_AGENT_ENABLED", "true").lower() == "true",
    "models": {
        "reasoning": "openai/gpt-5.4-mini",
        "fast": "anthropic/claude-haiku-4.5",
        "summary": "anthropic/claude-3.5-haiku",
    },
    "max_agent_turns": 10,
    "max_tokens": 4096,
    "temperature": 0.3,
}


# ── Dashboard Settings ────────────────────────────────────────────────────────
DASHBOARD = {
    "page_title": "Energy Intelligence System",
    "page_icon": "⚡",
    "layout": "wide",
    "theme_primary": "#1976D2",
    "theme_secondary": "#FF6F00",
    "refresh_interval_seconds": 300,  # Auto-refresh every 5 min
}

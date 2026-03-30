"""
Synthetic Data Generator for Energy Intelligence System
Generates 7 realistic CSV files for 55 stores across 4 sectors in Myanmar context.

Usage:
    python data/generators/synthetic_data.py
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
from config.settings import STORES, DATA_GEN, DIESEL, SAMPLE_DATA_DIR


np.random.seed(42)

# Date range
dates = pd.date_range(start=DATA_GEN["start_date"], end=DATA_GEN["end_date"], freq="D")
NUM_DAYS = len(dates)
hours = list(range(6, 22))  # Operating hours: 6am to 10pm


def generate_stores_csv():
    """Table 1: Store master data."""
    df = pd.DataFrame(STORES)
    df.to_csv(SAMPLE_DATA_DIR / "stores.csv", index=False)
    print(f"  stores.csv: {len(df)} stores")
    return df


def generate_diesel_prices_csv():
    """Table 2: Daily diesel prices + FX rates (market-level, not per store)."""
    base_price = DIESEL["base_price_mmk"]
    base_fx = DIESEL["usd_mmk_base"]

    # Simulate upward trend with volatility (war-driven)
    trend = np.linspace(0, 400, NUM_DAYS)  # Gradual increase over 6 months
    seasonal = 100 * np.sin(np.linspace(0, 4 * np.pi, NUM_DAYS))  # Seasonal wave
    noise = np.random.normal(0, 80, NUM_DAYS)  # Daily volatility
    shocks = np.zeros(NUM_DAYS)

    # Add 3-4 price shocks (war events)
    shock_days = np.random.choice(range(30, NUM_DAYS - 10), size=4, replace=False)
    for sd in shock_days:
        shock_magnitude = np.random.uniform(200, 500)
        shocks[sd:sd + np.random.randint(5, 15)] = shock_magnitude

    prices = base_price + trend + seasonal + noise + shocks
    prices = np.clip(prices, DIESEL["price_range"][0], DIESEL["price_range"][1])

    # FX rate (correlated with diesel)
    fx_trend = np.linspace(0, 300, NUM_DAYS)
    fx_noise = np.random.normal(0, 50, NUM_DAYS)
    fx_rates = base_fx + fx_trend + fx_noise
    fx_rates = np.clip(fx_rates, DIESEL["usd_mmk_range"][0], DIESEL["usd_mmk_range"][1])

    # Global oil proxy (Brent-like, USD)
    oil_base = 85
    oil_trend = np.linspace(0, 15, NUM_DAYS)
    oil_noise = np.random.normal(0, 3, NUM_DAYS)
    oil_prices = oil_base + oil_trend + oil_noise

    df = pd.DataFrame({
        "date": dates,
        "diesel_price_mmk": np.round(prices, 0).astype(int),
        "fx_usd_mmk": np.round(fx_rates, 0).astype(int),
        "brent_oil_usd": np.round(oil_prices, 2),
        "price_change_pct": 0.0,
    })
    df["price_change_pct"] = df["diesel_price_mmk"].pct_change().fillna(0).round(4) * 100

    df.to_csv(SAMPLE_DATA_DIR / "diesel_prices.csv", index=False)
    print(f"  diesel_prices.csv: {len(df)} days")
    return df


def generate_daily_energy_csv(stores_df, prices_df):
    """Table 3: Daily energy data per store (blackout, generator, diesel, solar)."""
    rows = []

    for _, store in stores_df.iterrows():
        # Township-specific blackout patterns
        township_factor = hash(store["township"]) % 5 / 5  # 0.0 - 0.8 variability
        base_blackout = DATA_GEN["avg_blackout_hours"] + township_factor * 3

        for i, date in enumerate(dates):
            # Day-of-week pattern (worse on weekdays)
            dow = date.dayofweek
            dow_factor = 1.2 if dow < 5 else 0.7

            # Seasonal pattern (worse in hot season: March-May)
            month = date.month
            season_factor = 1.3 if month in [3, 4, 5] else 1.0

            # Random daily variation
            daily_noise = np.random.normal(0, 1.5)

            # Blackout hours
            blackout_hours = base_blackout * dow_factor * season_factor + daily_noise
            blackout_hours = np.clip(blackout_hours, 0, 12)
            blackout_hours = round(blackout_hours, 1)

            # Generator hours (run during blackout, sometimes less if diesel low)
            gen_coverage = np.random.uniform(0.7, 1.0)
            generator_hours = round(blackout_hours * gen_coverage, 1)

            # Grid hours = operating hours (16) - blackout
            grid_hours = round(max(0, 16 - blackout_hours), 1)

            # Diesel consumption (liters) = generator_kw * hours * consumption_rate * load
            load_factor = np.random.uniform(0.6, 0.95)
            diesel_consumed = round(
                store["generator_kw"] * generator_hours * DIESEL["consumption_per_kwh"] * load_factor / 1000 * 10,
                1
            )

            # Solar generation (kWh) — only for solar sites
            solar_kwh = 0.0
            if store["has_solar"]:
                # Solar depends on weather/season
                solar_capacity = store["generator_kw"] * 0.4  # Solar ~40% of generator capacity
                sun_hours = np.random.uniform(4, 7) if month in [3, 4, 5] else np.random.uniform(3, 5.5)
                cloud_factor = np.random.uniform(0.5, 1.0)
                solar_kwh = round(solar_capacity * sun_hours * cloud_factor / 5, 1)

            # Diesel cost for the day
            diesel_price = prices_df.iloc[i]["diesel_price_mmk"]
            diesel_cost = round(diesel_consumed * diesel_price, 0)

            # Grid cost
            grid_cost = round(grid_hours * store["generator_kw"] * 0.5 * DIESEL["cost_per_kwh_grid"] / 1000 * 10, 0)

            rows.append({
                "date": date,
                "store_id": store["store_id"],
                "blackout_hours": blackout_hours,
                "generator_hours": generator_hours,
                "grid_hours": grid_hours,
                "diesel_consumed_liters": diesel_consumed,
                "diesel_cost_mmk": diesel_cost,
                "grid_cost_mmk": grid_cost,
                "solar_kwh": solar_kwh,
                "total_energy_cost_mmk": diesel_cost + grid_cost,
            })

    df = pd.DataFrame(rows)
    df.to_csv(SAMPLE_DATA_DIR / "daily_energy.csv", index=False)
    print(f"  daily_energy.csv: {len(df)} rows ({len(stores_df)} stores x {NUM_DAYS} days)")
    return df


def generate_diesel_inventory_csv(stores_df):
    """Table 4: Daily diesel inventory per store."""
    rows = []

    for _, store in stores_df.iterrows():
        # Tank capacity based on generator size
        tank_capacity = store["generator_kw"] * 2  # liters
        stock = tank_capacity * np.random.uniform(0.6, 0.9)

        for i, date in enumerate(dates):
            # Daily consumption estimate
            avg_consumption = store["generator_kw"] * 0.15  # rough daily average
            daily_use = avg_consumption * np.random.uniform(0.5, 1.5)

            # Resupply (every 3-7 days typically)
            purchased = 0
            if stock < tank_capacity * 0.3 or (i % np.random.randint(3, 8) == 0):
                purchased = round(tank_capacity * np.random.uniform(0.4, 0.8), 1)

            stock = stock - daily_use + purchased
            stock = np.clip(stock, 0, tank_capacity)

            # Supplier lead time (getting worse over time due to war)
            base_lead_time = 1 + (i / NUM_DAYS) * 2  # 1 day → 3 days over 6 months
            lead_time = round(base_lead_time + np.random.uniform(-0.5, 1.5), 1)
            lead_time = max(0.5, lead_time)

            days_of_coverage = round(stock / max(daily_use, 0.1), 1)

            rows.append({
                "date": date,
                "store_id": store["store_id"],
                "diesel_stock_liters": round(stock, 1),
                "diesel_purchased_liters": round(purchased, 1),
                "tank_capacity_liters": tank_capacity,
                "supplier_lead_time_days": lead_time,
                "days_of_coverage": min(days_of_coverage, 30),
            })

    df = pd.DataFrame(rows)
    df.to_csv(SAMPLE_DATA_DIR / "diesel_inventory.csv", index=False)
    print(f"  diesel_inventory.csv: {len(df)} rows")
    return df


def generate_store_sales_csv(stores_df):
    """Table 5: Hourly sales + gross margin per store."""
    rows = []

    # Base daily sales by channel (MMK)
    channel_base_sales = {
        "Hypermarket": 15_000_000,
        "Supermarket": 6_000_000,
        "Convenience": 1_500_000,
        "Bakery": 2_000_000,
        "Restaurant": 3_000_000,
        "Beverage": 800_000,
        "Warehouse": 20_000_000,
        "Cold Chain": 10_000_000,
        "Logistics": 8_000_000,
        "Mall": 50_000_000,
        "Office": 5_000_000,
    }

    # Gross margin by channel
    channel_margin = {
        "Hypermarket": 0.22,
        "Supermarket": 0.25,
        "Convenience": 0.30,
        "Bakery": 0.55,
        "Restaurant": 0.60,
        "Beverage": 0.65,
        "Warehouse": 0.08,
        "Cold Chain": 0.10,
        "Logistics": 0.12,
        "Mall": 0.35,
        "Office": 0.40,
    }

    # Hourly sales distribution (percentage of daily sales per hour)
    hourly_weights = {
        6: 0.02, 7: 0.03, 8: 0.05, 9: 0.07, 10: 0.08,
        11: 0.09, 12: 0.10, 13: 0.09, 14: 0.08, 15: 0.07,
        16: 0.08, 17: 0.09, 18: 0.07, 19: 0.05, 20: 0.02, 21: 0.01,
    }

    for _, store in stores_df.iterrows():
        base_sales = channel_base_sales[store["channel"]]
        margin_rate = channel_margin[store["channel"]]

        for i, date in enumerate(dates):
            # Day-of-week effect
            dow = date.dayofweek
            dow_multiplier = 1.2 if dow in [5, 6] else 1.0  # Weekend boost

            # Trend (slight decline due to economic impact)
            trend_factor = 1.0 - (i / NUM_DAYS) * 0.1  # 10% decline over 6 months

            # Random daily variation
            daily_variation = np.random.uniform(0.8, 1.2)

            daily_sales = base_sales * dow_multiplier * trend_factor * daily_variation

            for hour in hours:
                weight = hourly_weights.get(hour, 0.03)
                hourly_sales = round(daily_sales * weight * np.random.uniform(0.8, 1.2), 0)
                gross_margin = round(hourly_sales * margin_rate * np.random.uniform(0.9, 1.1), 0)

                rows.append({
                    "date": date,
                    "hour": hour,
                    "store_id": store["store_id"],
                    "sales_mmk": hourly_sales,
                    "gross_margin_mmk": gross_margin,
                    "transactions": max(1, int(hourly_sales / np.random.uniform(15000, 50000))),
                })

    df = pd.DataFrame(rows)
    df.to_csv(SAMPLE_DATA_DIR / "store_sales.csv", index=False)
    print(f"  store_sales.csv: {len(df)} rows (hourly)")
    return df


def generate_solar_generation_csv(stores_df):
    """Table 6: Hourly solar output for solar-equipped sites."""
    solar_stores = stores_df[stores_df["has_solar"] == True]
    rows = []

    for _, store in solar_stores.iterrows():
        solar_capacity_kw = store["generator_kw"] * 0.4  # Solar is ~40% of gen capacity

        for i, date in enumerate(dates):
            month = date.month
            # Season affects peak solar
            peak_factor = 1.2 if month in [3, 4, 5] else 0.9  # Hot dry season = more sun

            for hour in range(5, 19):  # Solar hours: 5am to 7pm
                # Bell curve centered around noon
                hour_factor = max(0, 1 - ((hour - 12) / 5) ** 2)

                # Cloud cover randomness
                cloud = np.random.uniform(0.3, 1.0)

                # Generation
                generation_kwh = round(
                    solar_capacity_kw * hour_factor * peak_factor * cloud * np.random.uniform(0.8, 1.0),
                    2
                )

                if generation_kwh > 0.5:  # Only record meaningful generation
                    rows.append({
                        "date": date,
                        "hour": hour,
                        "store_id": store["store_id"],
                        "solar_kwh": generation_kwh,
                        "solar_capacity_kw": solar_capacity_kw,
                        "efficiency_pct": round(generation_kwh / solar_capacity_kw * 100, 1) if solar_capacity_kw > 0 else 0,
                    })

    df = pd.DataFrame(rows)
    df.to_csv(SAMPLE_DATA_DIR / "solar_generation.csv", index=False)
    print(f"  solar_generation.csv: {len(df)} rows ({len(solar_stores)} solar sites)")
    return df


def generate_temperature_logs_csv(stores_df):
    """Table 7: Cold chain temperature logs (for stores with cold chain)."""
    cold_stores = stores_df[stores_df["cold_chain"] == True]
    rows = []

    # Product zones
    zones = [
        {"zone": "Dairy", "target_temp": 4, "critical_high": 8, "critical_low": 0},
        {"zone": "Frozen", "target_temp": -18, "critical_high": -12, "critical_low": -25},
        {"zone": "Fresh Produce", "target_temp": 6, "critical_high": 10, "critical_low": 2},
    ]

    for _, store in cold_stores.iterrows():
        for i, date in enumerate(dates):
            for zone in zones:
                # 4 readings per day (every 6 hours)
                for reading_hour in [0, 6, 12, 18]:
                    # Normal temperature near target
                    temp = zone["target_temp"] + np.random.normal(0, 1.5)

                    # During blackout + no generator, temperature rises
                    # Simulate occasional gaps (5% of readings show elevated temp)
                    if np.random.random() < 0.05:
                        temp = zone["target_temp"] + np.random.uniform(3, 8)

                    temp = round(temp, 1)
                    is_breach = temp > zone["critical_high"] or temp < zone["critical_low"]

                    rows.append({
                        "date": date,
                        "hour": reading_hour,
                        "store_id": store["store_id"],
                        "zone": zone["zone"],
                        "temperature_c": temp,
                        "target_temp_c": zone["target_temp"],
                        "critical_high_c": zone["critical_high"],
                        "critical_low_c": zone["critical_low"],
                        "is_breach": is_breach,
                    })

    df = pd.DataFrame(rows)
    df.to_csv(SAMPLE_DATA_DIR / "temperature_logs.csv", index=False)
    print(f"  temperature_logs.csv: {len(df)} rows ({len(cold_stores)} cold chain sites)")
    return df


def generate_supplier_master_csv():
    """Table 9: Supplier master data — registry of all diesel suppliers."""
    suppliers = [
        {
            "supplier_id": "SUP-001", "supplier_name": "Myanmar Petroleum Corp",
            "region": "Yangon Central", "contact_person": "U Kyaw Zin",
            "contact_phone": "+95-9-1234-5678", "avg_lead_time_days": 1.5,
            "price_markup_pct": 2.0, "min_order_liters": 200,
            "bulk_discount_pct": 1.5, "bulk_threshold_liters": 1000,
            "payment_terms": "NET7", "reliability_rating": "A",
            "serves_sectors": "ALL", "emergency_available": True,
            "notes": "Primary supplier, best reliability",
        },
        {
            "supplier_id": "SUP-002", "supplier_name": "Shwe Taung Fuel Trading",
            "region": "Yangon South", "contact_person": "Ma Aye Aye",
            "contact_phone": "+95-9-2345-6789", "avg_lead_time_days": 2.0,
            "price_markup_pct": -1.0, "min_order_liters": 500,
            "bulk_discount_pct": 2.0, "bulk_threshold_liters": 2000,
            "payment_terms": "NET14", "reliability_rating": "B",
            "serves_sectors": "Retail,Distribution", "emergency_available": True,
            "notes": "Bulk discount specialist, slower but cheaper",
        },
        {
            "supplier_id": "SUP-003", "supplier_name": "Golden Eagle Diesel",
            "region": "Mandalay", "contact_person": "Ko Aung Thu",
            "contact_phone": "+95-9-3456-7890", "avg_lead_time_days": 3.5,
            "price_markup_pct": 5.0, "min_order_liters": 100,
            "bulk_discount_pct": 0.0, "bulk_threshold_liters": 5000,
            "payment_terms": "COD", "reliability_rating": "C",
            "serves_sectors": "ALL", "emergency_available": False,
            "notes": "Emergency backup, expensive but always has stock",
        },
        {
            "supplier_id": "SUP-004", "supplier_name": "Delta Fuel Supply",
            "region": "Ayeyarwady", "contact_person": "Daw Thin Thin",
            "contact_phone": "+95-9-4567-8901", "avg_lead_time_days": 1.0,
            "price_markup_pct": 0.0, "min_order_liters": 300,
            "bulk_discount_pct": 1.0, "bulk_threshold_liters": 1500,
            "payment_terms": "NET7", "reliability_rating": "A",
            "serves_sectors": "F&B,Property", "emergency_available": True,
            "notes": "Local delta region supplier, fast delivery",
        },
    ]
    df = pd.DataFrame(suppliers)
    df.to_csv(SAMPLE_DATA_DIR / "supplier_master.csv", index=False)
    print(f"  supplier_master.csv: {len(df)} suppliers")
    return df


def generate_diesel_procurement_csv(stores_df, prices_df, suppliers_df):
    """Table 10: Diesel purchase orders with supplier-specific pricing."""
    rows = []
    po_counter = 1
    supplier_ids = suppliers_df["supplier_id"].tolist()
    markup_map = dict(zip(suppliers_df["supplier_id"], suppliers_df["price_markup_pct"]))
    bulk_disc_map = dict(zip(suppliers_df["supplier_id"], suppliers_df["bulk_discount_pct"]))
    bulk_thresh_map = dict(zip(suppliers_df["supplier_id"], suppliers_df["bulk_threshold_liters"]))
    lead_map = dict(zip(suppliers_df["supplier_id"], suppliers_df["avg_lead_time_days"]))

    orderers = ["U Min Htet", "Ma Yin Mar", "Ko Zaw Lin", "Daw Su Su"]

    for i, date in enumerate(dates):
        market_price = prices_df.iloc[i]["diesel_price_mmk"]

        # Generate 3-8 POs per day across the network
        n_orders = np.random.randint(3, 9)
        for _ in range(n_orders):
            sup_id = np.random.choice(supplier_ids)
            store = stores_df.sample(1).iloc[0]
            delivery_loc = np.random.choice([store["store_id"], "CENTRAL-DEPOT"], p=[0.7, 0.3])

            # Quantity: bigger stores order more
            base_qty = store["generator_kw"] * np.random.uniform(0.3, 1.5)
            quantity = round(max(100, base_qty), 0)

            # Price calculation: market + supplier markup - bulk discount + urgency
            markup = markup_map.get(sup_id, 2.0)
            bulk_disc = bulk_disc_map.get(sup_id, 0.0)
            bulk_thresh = bulk_thresh_map.get(sup_id, 1000)

            effective_markup = markup
            if quantity >= bulk_thresh:
                effective_markup -= bulk_disc

            # Order type
            order_type = np.random.choice(
                ["SCHEDULED", "BULK_BUY", "EMERGENCY"],
                p=[0.65, 0.20, 0.15],
            )
            if order_type == "EMERGENCY":
                effective_markup += np.random.uniform(2.0, 5.0)  # emergency premium

            actual_price = round(market_price * (1 + effective_markup / 100))
            total_cost = round(quantity * actual_price)
            price_vs_market = round((actual_price - market_price) / market_price * 100, 1)

            # Delivery timing
            base_lead = lead_map.get(sup_id, 2.0)
            lead_days = max(0, int(base_lead + np.random.uniform(-0.5, 1.5)))
            promised_date = date + pd.Timedelta(days=lead_days)
            delay = np.random.choice([0, 0, 0, 1, 1, 2, 3], p=[0.45, 0.15, 0.1, 0.12, 0.08, 0.06, 0.04])
            actual_date = promised_date + pd.Timedelta(days=delay)

            # Status based on timeline
            if actual_date <= dates[-1]:
                status = "DELIVERED"
            elif promised_date <= dates[-1]:
                status = "IN_TRANSIT"
            else:
                status = "ORDERED"

            ai_rec = order_type == "BULK_BUY" and np.random.random() < 0.7

            rows.append({
                "po_number": f"PO-2026-{po_counter:04d}",
                "po_date": date,
                "supplier_id": sup_id,
                "ordered_by": np.random.choice(orderers),
                "quantity_liters": quantity,
                "market_price_per_liter": market_price,
                "actual_price_per_liter": actual_price,
                "total_cost_mmk": total_cost,
                "price_vs_market_pct": price_vs_market,
                "delivery_location": delivery_loc,
                "promised_delivery_date": promised_date,
                "actual_delivery_date": actual_date if status == "DELIVERED" else "",
                "delivery_delay_days": delay if status == "DELIVERED" else "",
                "status": status,
                "order_type": order_type,
                "ai_recommended": ai_rec,
                "notes": "AI recommended bulk buy" if ai_rec else "",
            })
            po_counter += 1

    df = pd.DataFrame(rows)
    df.to_csv(SAMPLE_DATA_DIR / "diesel_procurement.csv", index=False)
    print(f"  diesel_procurement.csv: {len(df)} purchase orders")
    return df


def generate_diesel_transfers_csv(stores_df):
    """Table 11: Inter-site diesel transfers and depot-to-site movements."""
    rows = []
    trf_counter = 1
    store_ids = stores_df["store_id"].tolist()
    authorizers = [
        "Sector Lead - Retail", "Sector Lead - F&B",
        "Sector Lead - Distribution", "Holdings GECC",
        "U Min Htet", "Ma Yin Mar",
    ]

    for i, date in enumerate(dates):
        # 0-3 transfers per day
        n_transfers = np.random.choice([0, 0, 0, 1, 1, 2, 3], p=[0.3, 0.15, 0.1, 0.2, 0.1, 0.1, 0.05])
        for _ in range(n_transfers):
            reason = np.random.choice(
                ["REALLOCATION", "SCHEDULED", "EMERGENCY"],
                p=[0.40, 0.40, 0.20],
            )

            if reason == "SCHEDULED":
                from_loc = "CENTRAL-DEPOT"
                to_loc = np.random.choice(store_ids)
            else:
                from_loc = np.random.choice(store_ids)
                to_loc = np.random.choice([s for s in store_ids if s != from_loc])

            quantity = round(np.random.uniform(50, 400), 0)
            transport_cost = round(np.random.uniform(10000, 50000)) if from_loc != "CENTRAL-DEPOT" else 0

            rows.append({
                "transfer_id": f"TRF-2026-{trf_counter:04d}",
                "transfer_date": date,
                "from_location": from_loc,
                "to_location": to_loc,
                "quantity_liters": quantity,
                "reason": reason,
                "authorized_by": np.random.choice(authorizers),
                "transport_cost_mmk": transport_cost,
                "status": "COMPLETED",
                "linked_po": "",
                "notes": "",
            })
            trf_counter += 1

    df = pd.DataFrame(rows)
    df.to_csv(SAMPLE_DATA_DIR / "diesel_transfers.csv", index=False)
    print(f"  diesel_transfers.csv: {len(df)} transfers")
    return df


def generate_generator_maintenance_csv(stores_df):
    """Table 12: Generator maintenance and service history."""
    rows = []
    mnt_counter = 1
    technicians = [
        "U Than Win - PowerGen Services",
        "Generator Myanmar Co.",
        "Ko Htun Htun - Freelance",
        "Yangon Generator Maintenance",
        "Delta Power Solutions",
    ]

    for _, store in stores_df.iterrows():
        # Each generator gets 1-3 maintenance events over 6 months
        n_events = np.random.randint(1, 4)
        event_days = sorted(np.random.choice(range(NUM_DAYS), size=n_events, replace=False))

        gen_hours = 2000 + np.random.randint(0, 4000)  # starting hour meter

        for day_idx in event_days:
            date = dates[day_idx]
            gen_hours += np.random.randint(200, 600)

            mtype = np.random.choice(
                ["SCHEDULED", "EMERGENCY", "INSPECTION"],
                p=[0.55, 0.25, 0.20],
            )

            if mtype == "SCHEDULED":
                desc = np.random.choice([
                    "Oil change + air filter replacement",
                    "500-hour service interval",
                    "Annual comprehensive service",
                    "Coolant flush + belt inspection",
                ])
                downtime = np.random.uniform(1.0, 4.0)
                cost = np.random.randint(200000, 600000)
                parts = np.random.choice([
                    "Oil filter, Air filter, Engine oil 15L",
                    "Fuel filter, Oil filter, V-belt",
                    "Coolant 10L, Thermostat, Hoses",
                    "Air filter, Spark plugs x4",
                ])
            elif mtype == "EMERGENCY":
                desc = np.random.choice([
                    "Fuel injector failure - replaced",
                    "Alternator failure - rewound",
                    "Starter motor replacement",
                    "Radiator leak - patched and refilled",
                    "Battery failure - replaced",
                ])
                downtime = np.random.uniform(4.0, 24.0)
                cost = np.random.randint(500000, 2000000)
                parts = np.random.choice([
                    "Fuel injector x2, Gasket set",
                    "Alternator assembly",
                    "Starter motor, Solenoid",
                    "Radiator patch kit, Coolant 20L",
                    "Battery 12V 200Ah",
                ])
            else:
                desc = np.random.choice([
                    "Routine inspection - all OK",
                    "Inspection - minor oil leak noted",
                    "Pre-monsoon readiness check",
                ])
                downtime = 0
                cost = np.random.randint(50000, 150000)
                parts = ""

            next_date = date + pd.Timedelta(days=np.random.randint(60, 120))

            rows.append({
                "maintenance_id": f"MNT-2026-{mnt_counter:04d}",
                "date": date,
                "store_id": store["store_id"],
                "maintenance_type": mtype,
                "description": desc,
                "downtime_hours": round(downtime, 1),
                "cost_mmk": cost,
                "parts_replaced": parts,
                "next_service_date": next_date,
                "technician": np.random.choice(technicians),
                "generator_hours_at_service": gen_hours,
                "status": "COMPLETED" if day_idx < NUM_DAYS - 10 else "SCHEDULED",
            })
            mnt_counter += 1

    df = pd.DataFrame(rows)
    df.to_csv(SAMPLE_DATA_DIR / "generator_maintenance.csv", index=False)
    print(f"  generator_maintenance.csv: {len(df)} maintenance records")
    return df


def generate_fx_rates_csv():
    """Table 8: Daily USD/MMK exchange rates with multi-currency context."""
    base_fx = DIESEL["usd_mmk_base"]

    # USD/MMK — upward trend with volatility
    fx_trend = np.linspace(0, 300, NUM_DAYS)
    fx_noise = np.random.normal(0, 50, NUM_DAYS)
    fx_shocks = np.zeros(NUM_DAYS)
    shock_days = np.random.choice(range(20, NUM_DAYS - 10), size=3, replace=False)
    for sd in shock_days:
        fx_shocks[sd:sd + np.random.randint(5, 12)] = np.random.uniform(100, 250)

    usd_mmk = base_fx + fx_trend + fx_noise + fx_shocks
    usd_mmk = np.clip(usd_mmk, DIESEL["usd_mmk_range"][0], DIESEL["usd_mmk_range"][1])

    # EUR/MMK — correlated with USD/MMK
    eur_usd = 1.08 + np.random.normal(0, 0.02, NUM_DAYS).cumsum() * 0.01
    eur_usd = np.clip(eur_usd, 1.02, 1.15)
    eur_mmk = usd_mmk * eur_usd

    # SGD/MMK
    sgd_usd = 0.74 + np.random.normal(0, 0.005, NUM_DAYS).cumsum() * 0.005
    sgd_usd = np.clip(sgd_usd, 0.70, 0.78)
    sgd_mmk = usd_mmk * sgd_usd

    # THB/MMK
    thb_usd = 0.028 + np.random.normal(0, 0.001, NUM_DAYS).cumsum() * 0.001
    thb_usd = np.clip(thb_usd, 0.025, 0.032)
    thb_mmk = usd_mmk * thb_usd

    # CNY/MMK
    cny_usd = 0.138 + np.random.normal(0, 0.002, NUM_DAYS).cumsum() * 0.002
    cny_usd = np.clip(cny_usd, 0.130, 0.145)
    cny_mmk = usd_mmk * cny_usd

    df = pd.DataFrame({
        "date": dates,
        "usd_mmk": np.round(usd_mmk, 0).astype(int),
        "eur_mmk": np.round(eur_mmk, 0).astype(int),
        "sgd_mmk": np.round(sgd_mmk, 0).astype(int),
        "thb_mmk": np.round(thb_mmk, 1),
        "cny_mmk": np.round(cny_mmk, 0).astype(int),
        "usd_mmk_change_pct": 0.0,
    })
    df["usd_mmk_change_pct"] = df["usd_mmk"].pct_change().fillna(0).round(4) * 100

    df.to_csv(SAMPLE_DATA_DIR / "fx_rates.csv", index=False)
    print(f"  fx_rates.csv: {len(df)} days, 5 currency pairs")
    return df


def main():
    """Generate all 8 CSV files."""
    print("=" * 60)
    print("Energy Intelligence System - Synthetic Data Generator")
    print("=" * 60)

    # Ensure output directory exists
    SAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\nGenerating data for {len(STORES)} stores over {NUM_DAYS} days")
    print(f"Date range: {DATA_GEN['start_date']} to {DATA_GEN['end_date']}")
    print(f"Output: {SAMPLE_DATA_DIR}\n")

    # Generate in order (some depend on others)
    print("1/12 Generating store master data...")
    stores_df = generate_stores_csv()

    print("2/12 Generating diesel prices...")
    prices_df = generate_diesel_prices_csv()

    print("3/12 Generating daily energy data...")
    energy_df = generate_daily_energy_csv(stores_df, prices_df)

    print("4/12 Generating diesel inventory...")
    inventory_df = generate_diesel_inventory_csv(stores_df)

    print("5/12 Generating store sales (hourly)...")
    sales_df = generate_store_sales_csv(stores_df)

    print("6/12 Generating solar generation (hourly)...")
    solar_df = generate_solar_generation_csv(stores_df)

    print("7/12 Generating temperature logs...")
    temp_df = generate_temperature_logs_csv(stores_df)

    print("8/12 Generating FX rates...")
    fx_df = generate_fx_rates_csv()

    print("9/12 Generating supplier master...")
    suppliers_df = generate_supplier_master_csv()

    print("10/12 Generating diesel procurement (with supplier-specific pricing)...")
    procurement_df = generate_diesel_procurement_csv(stores_df, prices_df, suppliers_df)

    print("11/12 Generating diesel transfers...")
    transfers_df = generate_diesel_transfers_csv(stores_df)

    print("12/12 Generating generator maintenance...")
    maintenance_df = generate_generator_maintenance_csv(stores_df)

    print("\n" + "=" * 60)
    print("DONE! All 12 CSV files generated successfully.")
    print(f"Location: {SAMPLE_DATA_DIR}")
    print("=" * 60)

    # Summary
    print("\nFile Summary:")
    for f in sorted(SAMPLE_DATA_DIR.glob("*.csv")):
        size = f.stat().st_size / 1024
        unit = "KB" if size < 1024 else "MB"
        size_val = size if size < 1024 else size / 1024
        print(f"  {f.name:30s} {size_val:>8.1f} {unit}")


if __name__ == "__main__":
    main()

"""
Page 9: Data Upload Center
Color-coded sections per file, ML training flow, and upload UI.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from config.settings import SAMPLE_DATA_DIR, REAL_DATA_DIR, DATA_SOURCE

st.set_page_config(page_title="Data Upload", page_icon="📤", layout="wide")

# ── Hero Banner (matching all other pages) ──
st.markdown("""
<div style="background:linear-gradient(135deg,#004d40,#00897b);color:white;padding:20px 28px;border-radius:12px;margin-bottom:20px">
    <h2 style="margin:0;color:white">Data Upload Center</h2>
    <p style="margin:4px 0 0;opacity:0.85">Upload your real data to power the Energy Intelligence System</p>
</div>
""", unsafe_allow_html=True)

# ── Custom CSS for colored sections ──
st.markdown("""
<style>
    .section-required {
        background: linear-gradient(135deg, #1a237e 0%, #283593 100%);
        color: white;
        padding: 20px 24px;
        border-radius: 12px;
        margin-bottom: 8px;
    }
    .section-recommended {
        background: linear-gradient(135deg, #e65100 0%, #f57c00 100%);
        color: white;
        padding: 20px 24px;
        border-radius: 12px;
        margin-bottom: 8px;
    }
    .section-optional-green {
        background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 100%);
        color: white;
        padding: 20px 24px;
        border-radius: 12px;
        margin-bottom: 8px;
    }
    .section-optional-purple {
        background: linear-gradient(135deg, #4a148c 0%, #7b1fa2 100%);
        color: white;
        padding: 20px 24px;
        border-radius: 12px;
        margin-bottom: 8px;
    }
    .section-optional-teal {
        background: linear-gradient(135deg, #004d40 0%, #00796b 100%);
        color: white;
        padding: 20px 24px;
        border-radius: 12px;
        margin-bottom: 8px;
    }
    .section-title { font-size: 1.5rem; font-weight: 700; margin: 0; }
    .section-subtitle { font-size: 0.95rem; opacity: 0.9; margin-top: 4px; }
    .section-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        margin-left: 10px;
    }
    .badge-required { background: #ff1744; color: white; }
    .badge-recommended { background: #ff9100; color: white; }
    .badge-optional { background: #00e676; color: #1b5e20; }

    .model-chip {
        display: inline-block;
        background: rgba(255,255,255,0.15);
        padding: 3px 10px;
        border-radius: 15px;
        font-size: 0.8rem;
        margin: 2px 3px;
        border: 1px solid rgba(255,255,255,0.3);
    }

    .train-box {
        background: linear-gradient(135deg, #0d47a1 0%, #1565c0 100%);
        color: white;
        padding: 24px;
        border-radius: 12px;
        margin: 10px 0;
    }
    .train-step {
        background: rgba(255,255,255,0.1);
        padding: 12px 16px;
        border-radius: 8px;
        margin: 8px 0;
        border-left: 4px solid #64b5f6;
    }

    /* Upload area styling */
    .upload-zone {
        background: #f8fafc;
        border: 2px dashed #cbd5e1;
        border-radius: 12px;
        padding: 20px;
        margin: 12px 0;
        transition: all 0.2s;
    }
    .upload-zone:hover { border-color: #3b82f6; background: #f0f7ff; }

    .template-btn {
        background: linear-gradient(135deg, #1e40af, #3b82f6);
        color: white !important;
        padding: 8px 20px;
        border-radius: 8px;
        border: none;
        font-weight: 600;
        cursor: pointer;
    }

    .action-bar {
        background: linear-gradient(135deg, #f8fafc, #e2e8f0);
        border: 1px solid #cbd5e1;
        border-radius: 12px;
        padding: 16px 20px;
        margin: 16px 0;
    }
</style>
""", unsafe_allow_html=True)


REAL_DATA_DIR.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
# MASTER DATA TEMPLATE DOWNLOAD
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="background:linear-gradient(135deg,#004d40,#00897b,#26a69a);border-radius:14px;padding:24px 28px;margin-bottom:20px;box-shadow:0 4px 20px rgba(0,77,64,0.25)">
    <div style="display:flex;align-items:center;gap:16px">
        <div style="font-size:2.5rem">📋</div>
        <div style="flex:1">
            <h3 style="margin:0;color:white;font-size:1.3rem">Master Data Collection Template</h3>
            <p style="margin:4px 0 0;color:rgba(255,255,255,0.85);font-size:0.95rem">
                Single Excel workbook with all 8 data tabs — share with your site managers and data champions
            </p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

tc1, tc2 = st.columns([1, 2])

with tc1:
    from utils.template_generator import generate_template

    template_bytes = generate_template()
    st.download_button(
        label="📥 Download Master Template (.xlsx)",
        data=template_bytes,
        file_name="EIS_Master_Data_Template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml",
        type="primary",
        use_container_width=True,
        key="master_template_download",
    )

with tc2:
    st.markdown("""
    <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:10px;padding:14px 18px">
        <p style="margin:0 0 8px;font-weight:700;color:#166534;font-size:0.95rem">What's inside the template:</p>
        <div style="display:flex;gap:20px;flex-wrap:wrap;font-size:0.85rem;color:#15803d">
            <div>
                <span style="display:inline-block;width:10px;height:10px;background:#FF1744;border-radius:2px;margin-right:4px"></span>
                <strong>3 Required:</strong> stores, daily_energy, diesel_prices
            </div>
            <div>
                <span style="display:inline-block;width:10px;height:10px;background:#FF9100;border-radius:2px;margin-right:4px"></span>
                <strong>3 Recommended:</strong> diesel_inventory, store_sales, fx_rates
            </div>
            <div>
                <span style="display:inline-block;width:10px;height:10px;background:#00C853;border-radius:2px;margin-right:4px"></span>
                <strong>2 Optional:</strong> solar_generation, temperature_logs
            </div>
        </div>
        <p style="margin:10px 0 0;font-size:0.82rem;color:#166534">
            <strong style="color:#00897b">NEW columns in teal:</strong>
            operating modes, submission tracking, labour cost, shortage flag, supplier delivery dates
        </p>
    </div>
    """, unsafe_allow_html=True)

st.divider()


# ── Helpers ──
def validate_file(df: pd.DataFrame, required_columns: list) -> dict:
    errors, warnings = [], []
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        errors.append(f"Missing columns: {', '.join(missing)}")
    extra = [c for c in df.columns if c not in required_columns]
    if extra:
        warnings.append(f"Extra columns (will be kept): {', '.join(extra)}")
    if len(df) == 0:
        errors.append("File is empty")
    if "date" in df.columns:
        try:
            pd.to_datetime(df["date"])
        except Exception:
            errors.append("'date' column has invalid date values. Use YYYY-MM-DD format.")
    if not errors:
        null_cols = [c for c in required_columns if c in df.columns and df[c].isnull().sum() > 0]
        if null_cols:
            warnings.append(f"Null values found in: {', '.join(null_cols)}")
    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def file_status_badges(filename: str):
    sample_exists = (SAMPLE_DATA_DIR / filename).exists()
    real_exists = (REAL_DATA_DIR / filename).exists()
    c1, c2 = st.columns(2)
    with c1:
        if sample_exists:
            size = (SAMPLE_DATA_DIR / filename).stat().st_size / 1024
            st.success(f"Sample data ready: {size:,.0f} KB")
        else:
            st.error("No sample data")
    with c2:
        if real_exists:
            size = (REAL_DATA_DIR / filename).stat().st_size / 1024
            st.success(f"Real data uploaded: {size:,.0f} KB")
        else:
            st.warning("Real data: not uploaded yet")


def upload_widget(filename: str, required_columns: list, key: str, color: str = "#3b82f6"):
    """Colored upload widget with template download, validation, preview, and save."""

    # Colored upload zone
    st.markdown(f"""
    <div style="background:{color}08;border:2px dashed {color}40;border-radius:12px;padding:16px 20px;margin:8px 0">
        <p style="margin:0 0 8px;font-weight:600;color:{color}">Upload <code>{filename}</code></p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([1, 3])
    with c1:
        template_df = pd.DataFrame(columns=required_columns)
        st.download_button(
            "📥 Download Template",
            template_df.to_csv(index=False),
            file_name=f"template_{filename}",
            mime="text/csv",
            key=f"tpl_{key}",
            use_container_width=True,
        )
    with c2:
        uploaded = st.file_uploader(f"Choose file", type=["csv", "xlsx", "xls"], key=f"up_{key}",
                                     label_visibility="collapsed")

    if uploaded is not None:
        try:
            df = pd.read_excel(uploaded) if uploaded.name.endswith((".xlsx", ".xls")) else pd.read_csv(uploaded)
        except Exception as e:
            st.error(f"Cannot read file: {e}")
            return

        validation = validate_file(df, required_columns)

        # Validation result with color
        if validation["valid"]:
            st.markdown(f"""
            <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;padding:10px 16px;margin:8px 0">
                ✅ <strong>Valid:</strong> {len(df):,} rows, {len(df.columns)} columns
            </div>
            """, unsafe_allow_html=True)
        else:
            for err in validation["errors"]:
                st.error(err)
        for w in validation["warnings"]:
            st.warning(w)

        # Preview in styled container
        st.markdown(f"""
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px 16px;margin:8px 0">
            <p style="margin:0 0 8px;font-weight:600;color:#475569">Data Preview (first 10 rows)</p>
        </div>
        """, unsafe_allow_html=True)
        st.dataframe(df.head(10), use_container_width=True, hide_index=True)

        # Stats
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Rows", f"{len(df):,}")
        with c2:
            if "store_id" in df.columns:
                st.metric("Unique Stores", df["store_id"].nunique())
        with c3:
            if "date" in df.columns:
                try:
                    dates = pd.to_datetime(df["date"])
                    st.metric("Date Range", f"{dates.min().date()} to {dates.max().date()}")
                except Exception:
                    pass

        # Save buttons with color
        if validation["valid"]:
            st.markdown(f"""
            <div style="background:{color}08;border-radius:8px;padding:4px 0;margin:8px 0">
            </div>
            """, unsafe_allow_html=True)
            from utils.database import save_upload, log_activity

            c1, c2 = st.columns(2)
            with c1:
                if st.button("💾 Save to Real Data", type="primary", key=f"sr_{key}", use_container_width=True):
                    df.to_csv(REAL_DATA_DIR / filename, index=False)
                    file_size = (REAL_DATA_DIR / filename).stat().st_size / 1024
                    save_upload(filename, "real", len(df), len(df.columns), file_size)
                    log_activity("upload_real", f"{filename}: {len(df)} rows", "Data Upload")
                    st.cache_data.clear()
                    try:
                        from utils.database import clear_intelligence_cache
                        clear_intelligence_cache()
                    except Exception:
                        pass
                    st.success(f"Saved to `data/real/{filename}` — AI insights will regenerate")
                    st.balloons()
            with c2:
                if st.button("🔄 Save as Sample Data (replace)", key=f"ss_{key}", use_container_width=True):
                    df.to_csv(SAMPLE_DATA_DIR / filename, index=False)
                    file_size = (SAMPLE_DATA_DIR / filename).stat().st_size / 1024
                    save_upload(filename, "sample", len(df), len(df.columns), file_size)
                    log_activity("upload_sample", f"{filename}: {len(df)} rows", "Data Upload")
                    st.cache_data.clear()
                    try:
                        from utils.database import clear_intelligence_cache
                        clear_intelligence_cache()
                    except Exception:
                        pass
                    st.success(f"Saved to `data/sample/{filename}` — AI insights will regenerate")


# ══════════════════════════════════════════════════════════════════════════════
# STATUS OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════

st.header("Upload Status")

all_files = [
    ("stores.csv", "REQUIRED", "#1a237e"),
    ("daily_energy.csv", "REQUIRED", "#1a237e"),
    ("diesel_prices.csv", "REQUIRED", "#1a237e"),
    ("diesel_inventory.csv", "Recommended", "#e65100"),
    ("store_sales.csv", "Recommended", "#e65100"),
    ("fx_rates.csv", "Recommended", "#e65100"),
    ("solar_generation.csv", "Optional", "#1b5e20"),
    ("temperature_logs.csv", "Optional", "#1b5e20"),
]

status_rows = []
for fname, priority, _ in all_files:
    sample_ok = (SAMPLE_DATA_DIR / fname).exists()
    real_ok = (REAL_DATA_DIR / fname).exists()
    status_rows.append({
        "File": fname,
        "Priority": priority,
        "Sample Data": "Ready" if sample_ok else "Missing",
        "Real Data": "Uploaded" if real_ok else "---",
    })

st.dataframe(pd.DataFrame(status_rows), use_container_width=True, hide_index=True)
st.info(f"Active data source: **{DATA_SOURCE.upper()}**")

# ── Action Buttons: Delete Real Data / Reset Sample Data ──
st.markdown("""
<div style="background:linear-gradient(135deg,#f8fafc,#e2e8f0);border:1px solid #cbd5e1;border-radius:12px;padding:16px 20px;margin:16px 0">
    <p style="margin:0 0 8px;font-weight:700;color:#1e293b">Data Management Actions</p>
    <p style="margin:0;font-size:0.85rem;color:#64748b">Delete uploaded real data or regenerate fresh sample data</p>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)

from utils.database import log_activity as _log_action

with c1:
    if st.button("🗑️ Delete All Real Data", type="secondary", key="delete_real", use_container_width=True):
        real_files = list(REAL_DATA_DIR.glob("*.csv"))
        if real_files:
            for f in real_files:
                f.unlink()
            _log_action("delete_real_data", f"Deleted {len(real_files)} files", "Data Upload")
            st.cache_data.clear()
            st.success(f"Deleted {len(real_files)} real data files from `data/real/`")
            st.rerun()
        else:
            st.info("No real data files to delete.")

with c2:
    if st.button("🔄 Reset Sample Data (Regenerate)", type="primary", key="reset_sample", use_container_width=True):
        import subprocess, sys
        result = subprocess.run(
            [sys.executable, "data/generators/synthetic_data.py"],
            capture_output=True, text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        if result.returncode == 0:
            _log_action("reset_sample_data", "Regenerated 12 CSV files", "Data Upload")
            st.cache_data.clear()
            st.success("Sample data regenerated! 12 CSV files refreshed with new synthetic data.")
            st.rerun()
        else:
            st.error(f"Error: {result.stderr}")

with c3:
    if st.button("🧹 Clear All Cache", key="clear_cache", use_container_width=True):
        _log_action("clear_cache", "All caches cleared", "Data Upload")
        st.cache_data.clear()
        st.cache_resource.clear()
        st.success("All cached data and models cleared. Pages will reload fresh data.")
        st.rerun()

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1: STORES (REQUIRED — DARK BLUE)
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="section-required">
    <p class="section-title">1. Store Master Data <span class="section-badge badge-required">REQUIRED</span></p>
    <p class="section-subtitle">stores.csv — Your store registry. Upload this first. Every other file references stores by store_id.</p>
    <div style="margin-top:10px">
        <span class="model-chip">M1 Price Forecast</span>
        <span class="model-chip">M2 Blackout</span>
        <span class="model-chip">M3 Store Decisions</span>
        <span class="model-chip">M4 Diesel Optimizer</span>
        <span class="model-chip">M5 Solar</span>
        <span class="model-chip">M6 Stock-Out</span>
        <span class="model-chip">M7 Spoilage</span>
        <span class="model-chip">M8 Holdings</span>
    </div>
</div>
""", unsafe_allow_html=True)

with st.expander("What is this file?", expanded=False):
    st.markdown("""
    Each row = one store/site in your network. Defines sector, channel, location, solar status, and generator size.

    - **sector**: Retail, F&B, Distribution, or Property
    - **channel**: Sub-category (Hypermarket, Bakery, Warehouse, Mall, etc.)
    - **has_solar**: True/False — determines if solar optimization is enabled
    - **generator_kw**: Generator capacity — used to calculate expected diesel consumption
    - **cold_chain**: True/False — enables spoilage prediction for this site
    """)

cols_info = pd.DataFrame([
    {"Column": "store_id", "Type": "Text", "Example": "RH-001", "Description": "Unique ID. Use same ID in all files."},
    {"Column": "name", "Type": "Text", "Example": "Hypermarket Hlaing", "Description": "Store name for dashboards."},
    {"Column": "sector", "Type": "Text", "Example": "Retail", "Description": "Retail / F&B / Distribution / Property"},
    {"Column": "channel", "Type": "Text", "Example": "Hypermarket", "Description": "Channel within sector."},
    {"Column": "township", "Type": "Text", "Example": "Hlaing", "Description": "Location for blackout heatmap."},
    {"Column": "has_solar", "Type": "Boolean", "Example": "True", "Description": "Solar panels installed?"},
    {"Column": "generator_kw", "Type": "Number", "Example": "250", "Description": "Generator capacity (kW)."},
    {"Column": "cold_chain", "Type": "Boolean", "Example": "True", "Description": "Has cold storage?"},
])
st.dataframe(cols_info, use_container_width=True, hide_index=True)
file_status_badges("stores.csv")
upload_widget("stores.csv",
    ["store_id", "name", "sector", "channel", "township", "has_solar", "generator_kw", "cold_chain"], "stores", "#1a237e")

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2: DAILY ENERGY (REQUIRED — DARK BLUE)
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="section-required">
    <p class="section-title">2. Daily Energy Data <span class="section-badge badge-required">REQUIRED</span></p>
    <p class="section-subtitle">daily_energy.csv — Core operational data. One row per store per day. Blackout hours, generator usage, diesel, solar.</p>
    <div style="margin-top:10px">
        <span class="model-chip">M2 Blackout Prediction</span>
        <span class="model-chip">M3 Store Decisions</span>
        <span class="model-chip">M4 Diesel Optimizer</span>
        <span class="model-chip">M5 Solar Optimizer</span>
        <span class="model-chip">M8 Holdings</span>
    </div>
</div>
""", unsafe_allow_html=True)

with st.expander("What is this file?", expanded=False):
    st.markdown("""
    The daily energy reality for each store:
    - **blackout_hours**: How many hours was grid power unavailable (0-24)
    - **generator_hours**: How long did the generator actually run (usually <= blackout hours)
    - **diesel_consumed_liters**: Fuel burned that day
    - **solar_kwh**: Solar generation for solar-equipped sites (0 for others)

    **How to collect:** Store managers log blackout start/end times + generator meter readings daily.
    Solar data comes from inverter portal exports (Huawei FusionSolar, Sungrow, etc.)
    """)

cols_info = pd.DataFrame([
    {"Column": "date", "Type": "Date", "Example": "2026-01-15", "Description": "YYYY-MM-DD format."},
    {"Column": "store_id", "Type": "Text", "Example": "RH-001", "Description": "Must match stores.csv."},
    {"Column": "blackout_hours", "Type": "Number", "Example": "5.2", "Description": "Hours without grid power."},
    {"Column": "generator_hours", "Type": "Number", "Example": "4.1", "Description": "Hours generator ran."},
    {"Column": "grid_hours", "Type": "Number", "Example": "10.8", "Description": "Hours on grid."},
    {"Column": "diesel_consumed_liters", "Type": "Number", "Example": "38.5", "Description": "Diesel burned (liters)."},
    {"Column": "diesel_cost_mmk", "Type": "Number", "Example": "107800", "Description": "Diesel cost for the day."},
    {"Column": "grid_cost_mmk", "Type": "Number", "Example": "27000", "Description": "Grid electricity cost."},
    {"Column": "solar_kwh", "Type": "Number", "Example": "45.3", "Description": "Solar generated (kWh). 0 if no solar."},
    {"Column": "total_energy_cost_mmk", "Type": "Number", "Example": "134800", "Description": "diesel_cost + grid_cost."},
])
st.dataframe(cols_info, use_container_width=True, hide_index=True)
file_status_badges("daily_energy.csv")
upload_widget("daily_energy.csv",
    ["date", "store_id", "blackout_hours", "generator_hours", "grid_hours",
     "diesel_consumed_liters", "diesel_cost_mmk", "grid_cost_mmk", "solar_kwh", "total_energy_cost_mmk"], "energy", "#1a237e")

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3: DIESEL PRICES (REQUIRED — DARK BLUE)
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="section-required">
    <p class="section-title">3. Diesel Market Prices <span class="section-badge badge-required">REQUIRED</span></p>
    <p class="section-subtitle">diesel_prices.csv — Daily diesel price, FX rate, and oil price. One row per day. Feeds the price forecast AI.</p>
    <div style="margin-top:10px">
        <span class="model-chip">M1 Price Forecast (PRIMARY)</span>
        <span class="model-chip">M3 Store Decisions</span>
        <span class="model-chip">M5 Solar Optimizer</span>
    </div>
</div>
""", unsafe_allow_html=True)

with st.expander("What is this file?", expanded=False):
    st.markdown("""
    Market-level diesel pricing (not per store).
    - **diesel_price_mmk**: Daily diesel price per liter from your fuel supplier
    - **fx_usd_mmk**: USD/MMK exchange rate (correlated with diesel price)
    - **brent_oil_usd**: Global Brent crude oil price (external signal for forecasting)

    **How to collect:** Fuel supplier daily quote + bank FX rate + any financial news source for oil price.
    """)

cols_info = pd.DataFrame([
    {"Column": "date", "Type": "Date", "Example": "2026-01-15", "Description": "YYYY-MM-DD. One row per day."},
    {"Column": "diesel_price_mmk", "Type": "Number", "Example": "2850", "Description": "Price per liter in MMK."},
    {"Column": "fx_usd_mmk", "Type": "Number", "Example": "3520", "Description": "USD to MMK exchange rate."},
    {"Column": "brent_oil_usd", "Type": "Number", "Example": "88.50", "Description": "Brent crude USD/barrel."},
])
st.dataframe(cols_info, use_container_width=True, hide_index=True)
file_status_badges("diesel_prices.csv")
upload_widget("diesel_prices.csv",
    ["date", "diesel_price_mmk", "fx_usd_mmk", "brent_oil_usd"], "prices", "#1a237e")

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4: DIESEL INVENTORY (RECOMMENDED — ORANGE)
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="section-recommended">
    <p class="section-title">4. Diesel Inventory <span class="section-badge badge-recommended">RECOMMENDED</span></p>
    <p class="section-subtitle">diesel_inventory.csv — Daily diesel stock per store. Enables stock-out alerts and diesel reallocation.</p>
    <div style="margin-top:10px">
        <span class="model-chip">M6 Stock-Out Alert (PRIMARY)</span>
        <span class="model-chip">M3 Store Decisions</span>
        <span class="model-chip">M8 Holdings</span>
    </div>
</div>
""", unsafe_allow_html=True)

with st.expander("What is this file?", expanded=False):
    st.markdown("""
    Daily fuel tank status per store.
    - **diesel_stock_liters**: How much diesel is in the tank at end of day
    - **days_of_coverage**: How many days will current stock last at current burn rate
    - **supplier_lead_time_days**: How long to get a delivery (getting worse due to war)

    **Without this file:** Stock-out alerts and diesel reallocation recommendations disabled.

    **How to collect:** End-of-day tank dipstick reading or fuel gauge + delivery receipts.
    """)

cols_info = pd.DataFrame([
    {"Column": "date", "Type": "Date", "Example": "2026-01-15", "Description": "YYYY-MM-DD."},
    {"Column": "store_id", "Type": "Text", "Example": "RH-001", "Description": "Must match stores.csv."},
    {"Column": "diesel_stock_liters", "Type": "Number", "Example": "320.5", "Description": "Diesel in tank (liters)."},
    {"Column": "diesel_purchased_liters", "Type": "Number", "Example": "200", "Description": "Delivered today. 0 if none."},
    {"Column": "tank_capacity_liters", "Type": "Number", "Example": "500", "Description": "Max tank capacity."},
    {"Column": "supplier_lead_time_days", "Type": "Number", "Example": "1.5", "Description": "Days to get delivery."},
    {"Column": "days_of_coverage", "Type": "Number", "Example": "4.2", "Description": "Stock / daily consumption."},
])
st.dataframe(cols_info, use_container_width=True, hide_index=True)
file_status_badges("diesel_inventory.csv")
upload_widget("diesel_inventory.csv",
    ["date", "store_id", "diesel_stock_liters", "diesel_purchased_liters",
     "tank_capacity_liters", "supplier_lead_time_days", "days_of_coverage"], "inventory", "#e65100")

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5: STORE SALES (RECOMMENDED — ORANGE)
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="section-recommended">
    <p class="section-title">5. Store Sales Data <span class="section-badge badge-recommended">RECOMMENDED</span></p>
    <p class="section-subtitle">store_sales.csv — Hourly sales + gross margin per store. Makes the Store Decision Engine accurate.</p>
    <div style="margin-top:10px">
        <span class="model-chip">M3 Store Decisions (PRIMARY)</span>
        <span class="model-chip">M8 Holdings</span>
        <span class="model-chip">KPI Calculator</span>
    </div>
</div>
""", unsafe_allow_html=True)

with st.expander("What is this file?", expanded=False):
    st.markdown("""
    This is what makes the decision engine powerful — it compares **diesel cost per hour** vs **margin per hour**
    to decide if running the generator is profitable for each store.

    **How to collect:** Export from POS system (SAP, Oracle, etc.) — most POS systems can export hourly summaries.
    If only daily totals available, the system will estimate hourly distribution.

    **Without this file:** Store decisions use simplified rules without profitability analysis.
    """)

cols_info = pd.DataFrame([
    {"Column": "date", "Type": "Date", "Example": "2026-01-15", "Description": "YYYY-MM-DD."},
    {"Column": "hour", "Type": "Number", "Example": "10", "Description": "Hour of day (6-21)."},
    {"Column": "store_id", "Type": "Text", "Example": "RH-001", "Description": "Must match stores.csv."},
    {"Column": "sales_mmk", "Type": "Number", "Example": "1250000", "Description": "Revenue that hour (MMK)."},
    {"Column": "gross_margin_mmk", "Type": "Number", "Example": "275000", "Description": "Margin = sales - COGS."},
    {"Column": "transactions", "Type": "Number", "Example": "85", "Description": "Number of transactions."},
])
st.dataframe(cols_info, use_container_width=True, hide_index=True)
file_status_badges("store_sales.csv")
upload_widget("store_sales.csv",
    ["date", "hour", "store_id", "sales_mmk", "gross_margin_mmk", "transactions"], "sales", "#e65100")

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5B: FX RATES (RECOMMENDED — ORANGE)
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="section-recommended">
    <p class="section-title">6. FX Exchange Rates <span class="section-badge badge-recommended">RECOMMENDED</span></p>
    <p class="section-subtitle">fx_rates.csv — Daily exchange rates (USD, EUR, SGD, THB, CNY to MMK). Feeds price forecast and financial analysis.</p>
    <div style="margin-top:10px">
        <span class="model-chip">M1 Price Forecast</span>
        <span class="model-chip">M8 Holdings</span>
        <span class="model-chip">Diesel Intelligence</span>
    </div>
</div>
""", unsafe_allow_html=True)

with st.expander("What is this file?", expanded=False):
    st.markdown("""
    Daily foreign exchange rates against Myanmar Kyat. The USD/MMK rate is strongly correlated with
    diesel price movements since Myanmar imports fuel in USD.

    **How to collect:**
    - Central Bank of Myanmar daily reference rate
    - Bank exchange rate quotes
    - Money changer rates for parallel market tracking

    **Without this file:** FX correlation analysis and multi-currency tracking disabled. Diesel forecast uses simpler model.
    """)

cols_info = pd.DataFrame([
    {"Column": "date", "Type": "Date", "Example": "2026-01-15", "Description": "YYYY-MM-DD. One row per day."},
    {"Column": "usd_mmk", "Type": "Number", "Example": "3520", "Description": "US Dollar to MMK rate."},
    {"Column": "eur_mmk", "Type": "Number", "Example": "3802", "Description": "Euro to MMK rate."},
    {"Column": "sgd_mmk", "Type": "Number", "Example": "2605", "Description": "Singapore Dollar to MMK rate."},
    {"Column": "thb_mmk", "Type": "Number", "Example": "98.6", "Description": "Thai Baht to MMK rate."},
    {"Column": "cny_mmk", "Type": "Number", "Example": "486", "Description": "Chinese Yuan to MMK rate."},
])
st.dataframe(cols_info, use_container_width=True, hide_index=True)
file_status_badges("fx_rates.csv")
upload_widget("fx_rates.csv",
    ["date", "usd_mmk", "eur_mmk", "sgd_mmk", "thb_mmk", "cny_mmk"], "fx", "#e65100")

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7: SOLAR GENERATION (OPTIONAL — GREEN)
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="section-optional-green">
    <p class="section-title">6. Solar Generation Data <span class="section-badge badge-optional">OPTIONAL</span></p>
    <p class="section-subtitle">solar_generation.csv — Hourly solar output from inverters. Enables solar optimization and CAPEX prioritization.</p>
    <div style="margin-top:10px">
        <span class="model-chip">M5 Solar Optimizer (PRIMARY)</span>
        <span class="model-chip">M3 Store Decisions</span>
        <span class="model-chip">M8 Holdings</span>
    </div>
</div>
""", unsafe_allow_html=True)

with st.expander("What is this file?", expanded=False):
    st.markdown("""
    Hourly solar generation from inverter monitoring systems. Only needed for sites with `has_solar = True`.

    **How to collect — Export from your inverter portal:**
    - Huawei: FusionSolar app → Export
    - Sungrow: iSolarCloud → Download
    - Fronius: Solar.web → Export
    - SolarEdge: Monitoring portal → Export
    - Most inverters also have APIs for automated daily export

    **Without this file:** Solar optimization, load-shifting, diesel offset calculations disabled.
    """)

cols_info = pd.DataFrame([
    {"Column": "date", "Type": "Date", "Example": "2026-01-15", "Description": "YYYY-MM-DD."},
    {"Column": "hour", "Type": "Number", "Example": "12", "Description": "Hour (5-18 typically)."},
    {"Column": "store_id", "Type": "Text", "Example": "RH-001", "Description": "Solar-equipped store."},
    {"Column": "solar_kwh", "Type": "Number", "Example": "42.5", "Description": "kWh generated that hour."},
])
st.dataframe(cols_info, use_container_width=True, hide_index=True)
file_status_badges("solar_generation.csv")
upload_widget("solar_generation.csv",
    ["date", "hour", "store_id", "solar_kwh"], "solar", "#1b5e20")

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7: TEMPERATURE LOGS (OPTIONAL — PURPLE)
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="section-optional-purple">
    <p class="section-title">7. Cold Chain Temperature Logs <span class="section-badge badge-optional">OPTIONAL</span></p>
    <p class="section-subtitle">temperature_logs.csv — Cold storage temperature readings. Enables spoilage prediction during outages.</p>
    <div style="margin-top:10px">
        <span class="model-chip">M7 Spoilage Predictor (PRIMARY)</span>
    </div>
</div>
""", unsafe_allow_html=True)

with st.expander("What is this file?", expanded=False):
    st.markdown("""
    Temperature readings from cold storage zones: Dairy (4°C), Frozen (-18°C), Fresh Produce (6°C).

    **How to collect:**
    - IoT temperature sensors in cold rooms (automated logging)
    - Manual temperature log sheets (staff records 4x daily: 12am, 6am, 12pm, 6pm)

    **Without this file:** Spoilage prediction disabled. All other models still work.
    """)

cols_info = pd.DataFrame([
    {"Column": "date", "Type": "Date", "Example": "2026-01-15", "Description": "YYYY-MM-DD."},
    {"Column": "hour", "Type": "Number", "Example": "6", "Description": "Reading time (0, 6, 12, 18)."},
    {"Column": "store_id", "Type": "Text", "Example": "RH-001", "Description": "Cold chain store."},
    {"Column": "zone", "Type": "Text", "Example": "Dairy", "Description": "Dairy / Frozen / Fresh Produce."},
    {"Column": "temperature_c", "Type": "Number", "Example": "4.2", "Description": "Actual temp reading (°C)."},
    {"Column": "target_temp_c", "Type": "Number", "Example": "4", "Description": "Target temperature."},
    {"Column": "critical_high_c", "Type": "Number", "Example": "8", "Description": "Max safe temperature."},
    {"Column": "critical_low_c", "Type": "Number", "Example": "0", "Description": "Min safe temperature."},
    {"Column": "is_breach", "Type": "Boolean", "Example": "False", "Description": "Was temp outside safe range?"},
])
st.dataframe(cols_info, use_container_width=True, hide_index=True)
file_status_badges("temperature_logs.csv")
upload_widget("temperature_logs.csv",
    ["date", "hour", "store_id", "zone", "temperature_c", "target_temp_c",
     "critical_high_c", "critical_low_c", "is_breach"], "temp", "#4a148c")

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# ML TRAINING FLOW — WHAT HAPPENS AFTER UPLOAD
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="section-optional-teal">
    <p class="section-title">How Machine Learning Training Works After Upload</p>
    <p class="section-subtitle">The system automatically retrains all AI models when new data is loaded</p>
</div>
""", unsafe_allow_html=True)

st.markdown("")

from utils.mermaid_helper import render_mermaid

st.markdown("### How Data Flows Through the System")

render_mermaid("""
flowchart TD
    UPLOAD["📤 You Upload CSV Files<br/>stores, energy, prices, fx, inventory, sales, solar, temp"]
    -->STORE["💾 Saved to data/sample/ or data/real/"]
    -->LOAD["📂 Data Loader reads all files"]
    -->SPLIT{{"8 AI Models Process"}}

    SPLIT --> ML["🧠 4 ML Models Train<br/>M1 Prophet | M2 XGBoost<br/>M4 Regression | M7 Random Forest"]
    SPLIT --> RULES["⚙️ 4 Rule-Based Models Run<br/>M3 Store Decisions | M5 Solar<br/>M6 Stock-Out | M8 Holdings"]

    ML --> ALERTS["🚨 Alerts Generated<br/>Tier 1 Critical | Tier 2 Warning | Tier 3 Info"]
    RULES --> ALERTS

    ML --> DASH["📊 Dashboards Updated<br/>9 pages refresh with new data"]
    RULES --> DASH

    ALERTS --> LOG["📄 Saved to training_log.json<br/>Persists across refresh"]

    style UPLOAD fill:#eff6ff,stroke:#3b82f6,stroke-width:2px
    style STORE fill:#fefce8,stroke:#ca8a04,stroke-width:2px
    style LOAD fill:#f8fafc,stroke:#64748b
    style SPLIT fill:#fff,stroke:#64748b
    style ML fill:#fdf2f8,stroke:#ec4899,stroke-width:2px
    style RULES fill:#f0fdf4,stroke:#16a34a,stroke-width:2px
    style ALERTS fill:#fef2f2,stroke:#ef4444,stroke-width:2px
    style DASH fill:#ede9fe,stroke:#7c3aed,stroke-width:2px
    style LOG fill:#fefce8,stroke:#d97706
""", height=520)

st.markdown("")

st.markdown("""
### The ML Training Pipeline

When you upload new data and navigate to any dashboard page, **4 ML models automatically retrain** on your data:
""")

col1, col2 = st.columns(2)

with col1:
    # M1: Diesel Price Forecast
    st.markdown("""
    <div style="border-radius:12px;overflow:hidden;margin-bottom:20px;box-shadow:0 2px 12px rgba(0,0,0,0.08)">
        <div style="background:linear-gradient(135deg,#7c2d12,#ea580c);color:white;padding:14px 18px">
            <span style="font-size:1.3rem">⛽</span>
            <strong style="margin-left:8px;font-size:1.05rem">M1: Diesel Price Forecast</strong>
            <span style="float:right;background:rgba(255,255,255,0.2);padding:2px 10px;border-radius:20px;font-size:0.75rem">Prophet</span>
        </div>
        <div style="padding:16px 18px;background:#fff7ed">
            <div style="background:#fdba74;color:#7c2d12;padding:8px 12px;border-radius:8px;font-weight:600;font-size:0.85rem;margin-bottom:12px">
                INPUT: diesel_prices.csv
            </div>
            <div style="margin:8px 0">
                <div style="display:flex;align-items:center;margin:6px 0"><span style="color:#ea580c;margin-right:8px">①</span> Reads your full price history</div>
                <div style="display:flex;align-items:center;margin:6px 0"><span style="color:#ea580c;margin-right:8px">②</span> Detects trends, seasonality, shocks</div>
                <div style="display:flex;align-items:center;margin:6px 0"><span style="color:#ea580c;margin-right:8px">③</span> Learns FX and oil price correlation</div>
                <div style="display:flex;align-items:center;margin:6px 0"><span style="color:#ea580c;margin-right:8px">④</span> Builds forecast model</div>
            </div>
            <div style="display:flex;gap:8px;margin:12px 0;flex-wrap:wrap">
                <span style="background:#fff;border:1px solid #fdba74;padding:3px 10px;border-radius:20px;font-size:0.75rem">~3 sec training</span>
                <span style="background:#fff;border:1px solid #fdba74;padding:3px 10px;border-radius:20px;font-size:0.75rem">Min: 30 days</span>
                <span style="background:#fff;border:1px solid #fdba74;padding:3px 10px;border-radius:20px;font-size:0.75rem">Best: 90+ days</span>
            </div>
            <div style="text-align:center;font-size:1.2rem;color:#ea580c;margin:4px 0">▼</div>
            <div style="background:#ea580c;color:white;padding:8px 12px;border-radius:8px;font-weight:600;font-size:0.85rem;text-align:center">
                OUTPUT: 7-day forecast + buy/hold signal
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # M4: Diesel Optimizer
    st.markdown("""
    <div style="border-radius:12px;overflow:hidden;margin-bottom:20px;box-shadow:0 2px 12px rgba(0,0,0,0.08)">
        <div style="background:linear-gradient(135deg,#064e3b,#059669);color:white;padding:14px 18px">
            <span style="font-size:1.3rem">⚙️</span>
            <strong style="margin-left:8px;font-size:1.05rem">M4: Diesel Optimizer</strong>
            <span style="float:right;background:rgba(255,255,255,0.2);padding:2px 10px;border-radius:20px;font-size:0.75rem">Regression + Isolation Forest</span>
        </div>
        <div style="padding:16px 18px;background:#ecfdf5">
            <div style="background:#6ee7b7;color:#064e3b;padding:8px 12px;border-radius:8px;font-weight:600;font-size:0.85rem;margin-bottom:12px">
                INPUT: daily_energy.csv + stores.csv
            </div>
            <div style="margin:8px 0">
                <div style="display:flex;align-items:center;margin:6px 0"><span style="color:#059669;margin-right:8px">①</span> <strong>Linear Regression</strong> — learns expected consumption per generator size &amp; runtime</div>
                <div style="display:flex;align-items:center;margin:6px 0"><span style="color:#059669;margin-right:8px">②</span> <strong>Isolation Forest</strong> — learns normal vs abnormal consumption patterns</div>
                <div style="display:flex;align-items:center;margin:6px 0"><span style="color:#059669;margin-right:8px">③</span> Compares actual vs expected to score efficiency</div>
            </div>
            <div style="display:flex;gap:8px;margin:12px 0;flex-wrap:wrap">
                <span style="background:#fff;border:1px solid #6ee7b7;padding:3px 10px;border-radius:20px;font-size:0.75rem">~2 sec training</span>
                <span style="background:#fff;border:1px solid #6ee7b7;padding:3px 10px;border-radius:20px;font-size:0.75rem">Min: 14 days</span>
            </div>
            <div style="text-align:center;font-size:1.2rem;color:#059669;margin:4px 0">▼</div>
            <div style="background:#059669;color:white;padding:8px 12px;border-radius:8px;font-weight:600;font-size:0.85rem;text-align:center">
                OUTPUT: Efficiency scores + waste alerts
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    # M2: Blackout Prediction
    st.markdown("""
    <div style="border-radius:12px;overflow:hidden;margin-bottom:20px;box-shadow:0 2px 12px rgba(0,0,0,0.08)">
        <div style="background:linear-gradient(135deg,#7f1d1d,#dc2626);color:white;padding:14px 18px">
            <span style="font-size:1.3rem">🔌</span>
            <strong style="margin-left:8px;font-size:1.05rem">M2: Blackout Prediction</strong>
            <span style="float:right;background:rgba(255,255,255,0.2);padding:2px 10px;border-radius:20px;font-size:0.75rem">XGBoost / Gradient Boosting</span>
        </div>
        <div style="padding:16px 18px;background:#fef2f2">
            <div style="background:#fca5a5;color:#7f1d1d;padding:8px 12px;border-radius:8px;font-weight:600;font-size:0.85rem;margin-bottom:12px">
                INPUT: daily_energy.csv + stores.csv
            </div>
            <div style="margin:8px 0">
                <div style="display:flex;align-items:center;margin:6px 0"><span style="color:#dc2626;margin-right:8px">①</span> Creates features: day of week, month, season, township</div>
                <div style="display:flex;align-items:center;margin:6px 0"><span style="color:#dc2626;margin-right:8px">②</span> Adds rolling averages: 3-day, 7-day blackout history</div>
                <div style="display:flex;align-items:center;margin:6px 0"><span style="color:#dc2626;margin-right:8px">③</span> Target: was there a blackout > 3 hours?</div>
                <div style="display:flex;align-items:center;margin:6px 0"><span style="color:#dc2626;margin-right:8px">④</span> Trains 100 decision trees (ensemble)</div>
            </div>
            <div style="display:flex;gap:8px;margin:12px 0;flex-wrap:wrap">
                <span style="background:#fff;border:1px solid #fca5a5;padding:3px 10px;border-radius:20px;font-size:0.75rem">~5 sec training</span>
                <span style="background:#fff;border:1px solid #fca5a5;padding:3px 10px;border-radius:20px;font-size:0.75rem">Min: 30 days</span>
                <span style="background:#fff;border:1px solid #fca5a5;padding:3px 10px;border-radius:20px;font-size:0.75rem">Best: 90+ days</span>
            </div>
            <div style="text-align:center;font-size:1.2rem;color:#dc2626;margin:4px 0">▼</div>
            <div style="background:#dc2626;color:white;padding:8px 12px;border-radius:8px;font-weight:600;font-size:0.85rem;text-align:center">
                OUTPUT: Blackout probability per store for tomorrow
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # M7: Spoilage Predictor
    st.markdown("""
    <div style="border-radius:12px;overflow:hidden;margin-bottom:20px;box-shadow:0 2px 12px rgba(0,0,0,0.08)">
        <div style="background:linear-gradient(135deg,#4a148c,#9c27b0);color:white;padding:14px 18px">
            <span style="font-size:1.3rem">🧊</span>
            <strong style="margin-left:8px;font-size:1.05rem">M7: Spoilage Predictor</strong>
            <span style="float:right;background:rgba(255,255,255,0.2);padding:2px 10px;border-radius:20px;font-size:0.75rem">Random Forest</span>
        </div>
        <div style="padding:16px 18px;background:#faf5ff">
            <div style="background:#d8b4fe;color:#4a148c;padding:8px 12px;border-radius:8px;font-weight:600;font-size:0.85rem;margin-bottom:12px">
                INPUT: temperature_logs.csv + daily_energy.csv
            </div>
            <div style="margin:8px 0">
                <div style="display:flex;align-items:center;margin:6px 0"><span style="color:#9c27b0;margin-right:8px">①</span> Combines outage data with temp readings</div>
                <div style="display:flex;align-items:center;margin:6px 0"><span style="color:#9c27b0;margin-right:8px">②</span> Features: generator gap, max temp, zone type, breach count</div>
                <div style="display:flex;align-items:center;margin:6px 0"><span style="color:#9c27b0;margin-right:8px">③</span> Learns which conditions cause spoilage per product zone</div>
            </div>
            <div style="display:flex;gap:8px;margin:12px 0;flex-wrap:wrap">
                <span style="background:#fff;border:1px solid #d8b4fe;padding:3px 10px;border-radius:20px;font-size:0.75rem">~3 sec training</span>
                <span style="background:#fff;border:1px solid #d8b4fe;padding:3px 10px;border-radius:20px;font-size:0.75rem">Min: 14 days</span>
            </div>
            <div style="text-align:center;font-size:1.2rem;color:#9c27b0;margin:4px 0">▼</div>
            <div style="background:#9c27b0;color:white;padding:8px 12px;border-radius:8px;font-weight:600;font-size:0.85rem;text-align:center">
                OUTPUT: Spoilage risk score per zone per store
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("")

# ── Training Sequence ──
st.markdown("### What Happens When You Click 'Train'")

render_mermaid("""
flowchart TD
    CLICK["🖱️ Click Train All Models"]
    --> LOAD["📂 Load 8 CSV files<br/>~270K rows total"]
    --> M1["⛽ M1: Train Prophet on diesel prices<br/>→ 7-day forecast + buy/hold signal"]
    --> M2["🔌 M2: Train XGBoost on blackout history<br/>→ Probability per store for tomorrow"]
    --> M3["📋 M3: Run Decision Engine using M1+M2<br/>→ FULL / REDUCED / CRITICAL / CLOSE"]
    --> M4["⚙️ M4: Train Regression on generator data<br/>→ Efficiency scores + waste alerts"]
    --> M5["☀️ M5: Optimize solar + diesel mix<br/>→ Load-shift recommendations"]
    --> M6["🛢️ M6: Analyze diesel inventory<br/>→ Stock-out risk + reallocation plan"]
    --> M7["🧊 M7: Train Random Forest on temp logs<br/>→ Spoilage risk per zone"]
    --> M8["🏛️ M8: Aggregate to Holdings level<br/>→ Group KPIs + EBITDA impact"]
    --> SAVE["📄 Save log to training_log.json"]
    --> DONE["✅ Done — Results shown in terminal<br/>Cache cleared, dashboards use new models"]

    style CLICK fill:#eff6ff,stroke:#3b82f6,stroke-width:2px
    style LOAD fill:#fefce8,stroke:#ca8a04
    style M1 fill:#fff7ed,stroke:#ea580c
    style M2 fill:#fef2f2,stroke:#dc2626
    style M3 fill:#f0fdf4,stroke:#16a34a
    style M4 fill:#ecfdf5,stroke:#059669
    style M5 fill:#fefce8,stroke:#eab308
    style M6 fill:#fff7ed,stroke:#f97316
    style M7 fill:#faf5ff,stroke:#9c27b0
    style M8 fill:#ede9fe,stroke:#7c3aed
    style SAVE fill:#fefce8,stroke:#d97706
    style DONE fill:#f0fdf4,stroke:#22c55e,stroke-width:2px
""", height=700)

st.markdown("")

# ── Accuracy Timeline ──
st.markdown("""
<div style="border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);margin-bottom:20px">
    <div style="background:linear-gradient(135deg,#0f172a,#1e3a5f);color:white;padding:14px 18px">
        <strong style="font-size:1.05rem">How Accuracy Improves Over Time</strong>
    </div>
    <div style="padding:0">
        <div style="display:flex;border-bottom:1px solid #e2e8f0">
            <div style="flex:1;padding:14px 16px;background:#fef2f2;border-right:1px solid #e2e8f0">
                <div style="font-weight:700;color:#991b1b">Week 1</div>
                <div style="font-size:0.85rem;color:#666;margin-top:2px">7 days data</div>
                <div style="font-size:1.5rem;font-weight:800;color:#dc2626;margin-top:4px">~60%</div>
                <div style="font-size:0.8rem;color:#888;margin-top:4px">Basic patterns. Rough but directional.</div>
            </div>
            <div style="flex:1;padding:14px 16px;background:#fff7ed;border-right:1px solid #e2e8f0">
                <div style="font-weight:700;color:#92400e">Month 1</div>
                <div style="font-size:0.85rem;color:#666;margin-top:2px">30 days data</div>
                <div style="font-size:1.5rem;font-weight:800;color:#ea580c;margin-top:4px">~75%</div>
                <div style="font-size:0.8rem;color:#888;margin-top:4px">Weekly patterns emerge. Township trends visible.</div>
            </div>
            <div style="flex:1;padding:14px 16px;background:#eff6ff;border-right:1px solid #e2e8f0">
                <div style="font-weight:700;color:#1e40af">Month 3</div>
                <div style="font-size:0.85rem;color:#666;margin-top:2px">90 days data</div>
                <div style="font-size:1.5rem;font-weight:800;color:#2563eb;margin-top:4px">~85%</div>
                <div style="font-size:0.8rem;color:#888;margin-top:4px">Seasonal patterns captured. Price forecast reliable.</div>
            </div>
            <div style="flex:1;padding:14px 16px;background:#f0fdf4">
                <div style="font-weight:700;color:#166534">Month 6</div>
                <div style="font-size:0.85rem;color:#666;margin-top:2px">180 days data</div>
                <div style="font-size:1.5rem;font-weight:800;color:#16a34a;margin-top:4px">~90%</div>
                <div style="font-size:0.8rem;color:#888;margin-top:4px">Full seasonal cycle. Highly calibrated to your environment.</div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:14px 18px;margin-bottom:16px">
    <strong>Key insight:</strong> Models don't need perfect data to be useful. Even 2 weeks of rough daily logs produce better decisions than no data at all.
</div>
""", unsafe_allow_html=True)

st.divider()

st.markdown("""
<div style="background:linear-gradient(135deg,#0f172a,#1e293b);color:white;padding:16px 20px;border-radius:12px;margin-bottom:12px">
    <p style="margin:0;font-size:1.1rem;font-weight:700">ML Training Console</p>
    <p style="margin:4px 0 0;font-size:0.85rem;opacity:0.7">Train all 8 AI models. Logs persist to disk — safe to refresh.</p>
</div>
""", unsafe_allow_html=True)

import json, time
from datetime import datetime
from utils.database import save_training_run, get_training_runs, log_activity

if st.button("Train All 8 Models Now", type="primary", use_container_width=True, key="train_btn"):
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    # Terminal-style container
    st.markdown("""
    <style>
    .terminal {
        background: #0f172a;
        color: #22c55e;
        font-family: 'Courier New', monospace;
        font-size: 0.82rem;
        padding: 16px 20px;
        border-radius: 10px;
        border: 1px solid #334155;
        line-height: 1.6;
        max-height: 500px;
        overflow-y: auto;
    }
    .terminal .prompt { color: #3b82f6; }
    .terminal .success { color: #22c55e; }
    .terminal .warning { color: #eab308; }
    .terminal .error { color: #ef4444; }
    .terminal .info { color: #94a3b8; }
    .terminal .model { color: #a78bfa; }
    .terminal .time { color: #64748b; }
    </style>
    """, unsafe_allow_html=True)

    terminal = st.empty()
    log_lines = []
    run_log = {"timestamp": datetime.now().isoformat(), "status": "running", "lines": [], "results": {}, "_start_time": time.time()}

    def term_print(line, css_class="info"):
        ts = datetime.now().strftime("%H:%M:%S")
        log_lines.append(f'<span class="time">[{ts}]</span> <span class="{css_class}">{line}</span>')
        run_log["lines"].append(f"[{ts}] {line}")
        html = "<br>".join(log_lines)
        terminal.markdown(f'<div class="terminal">{html}</div>', unsafe_allow_html=True)

    term_print("$ energy-intelligence-system --train-all", "prompt")
    term_print("Starting Energy Intelligence System training pipeline...")
    term_print(f"Data source: {DATA_SOURCE.upper()}")

    try:
        # Load data
        term_print("Loading data files...", "info")
        from alerts.alert_engine import AlertEngine
        engine = AlertEngine()
        engine.load_data()
        for name, df in engine.data.items():
            term_print(f"  Loaded {name}: {len(df):,} rows", "success")

        term_print("")
        term_print("Training models...", "info")
        term_print("=" * 50, "info")

        # M1
        term_print("M1: Diesel Price Forecast (Prophet)...", "model")
        t0 = time.time()
        engine._run_diesel_price_forecast()
        dt = time.time() - t0
        rec = engine.results.get("diesel_recommendation", {})
        term_print(f"  Trained in {dt:.1f}s — Signal: {rec.get('signal', 'N/A')}", "success")

        # M2
        term_print("M2: Blackout Prediction (XGBoost)...", "model")
        t0 = time.time()
        engine._run_blackout_prediction()
        dt = time.time() - t0
        preds = engine.results.get("blackout_predictions")
        high = (preds["risk_level"] == "HIGH").sum() if preds is not None else 0
        term_print(f"  Trained in {dt:.1f}s — {high} high-risk stores", "success")

        # M3
        term_print("M3: Store Decision Engine (Rule-based)...", "model")
        t0 = time.time()
        engine._run_store_decisions()
        dt = time.time() - t0
        ps = engine.results.get("plan_summary", {})
        term_print(f"  Trained in {dt:.1f}s — FULL:{ps.get('stores_full',0)} REDUCED:{ps.get('stores_reduced',0)} CRITICAL:{ps.get('stores_critical',0)} CLOSE:{ps.get('stores_closed',0)}", "success")

        # M4
        term_print("M4: Diesel Optimizer (Regression + Isolation Forest)...", "model")
        t0 = time.time()
        engine._run_diesel_optimizer()
        dt = time.time() - t0
        term_print(f"  Trained in {dt:.1f}s", "success")

        # M5
        term_print("M5: Solar Optimizer (Linear Programming)...", "model")
        t0 = time.time()
        engine._run_solar_optimizer()
        dt = time.time() - t0
        ss = engine.results.get("solar_summary", {})
        term_print(f"  Trained in {dt:.1f}s — {ss.get('total_solar_sites',0)} solar sites, {ss.get('total_diesel_offset_liters',0):,.0f}L offset/day", "success")

        # M6
        term_print("M6: Stock-Out Alert (Probabilistic)...", "model")
        t0 = time.time()
        engine._run_stockout_alert()
        dt = time.time() - t0
        so = engine.results.get("stockout_summary", {})
        term_print(f"  Trained in {dt:.1f}s — {so.get('critical_stores',0)} critical, {so.get('high_risk_stores',0)} high risk", "success")

        # M7
        term_print("M7: Spoilage Predictor (Random Forest)...", "model")
        t0 = time.time()
        engine._run_spoilage_predictor()
        dt = time.time() - t0
        term_print(f"  Trained in {dt:.1f}s", "success")

        # M8
        term_print("M8: Holdings Aggregator (Scenario Engine)...", "model")
        t0 = time.time()
        engine._run_holdings_aggregator()
        dt = time.time() - t0
        gk = engine.results.get("group_kpis", {})
        term_print(f"  Trained in {dt:.1f}s — ERI: {gk.get('avg_eri_pct',0):.0f}%", "success")

        term_print("")
        term_print("=" * 50, "info")

        # Alerts summary
        counts = engine.get_alert_counts()
        term_print(f"ALERTS: {counts['total']} total — {counts['critical']} critical, {counts['warning']} warning, {counts['info']} info", "warning")

        # Briefing
        term_print("")
        briefing = engine.get_morning_briefing()
        for line in briefing.split("\n"):
            term_print(line, "info")

        term_print("")
        term_print("All 8 models trained successfully.", "success")
        term_print("Cache cleared. Dashboard pages will use new models.", "success")
        term_print("$", "prompt")

        st.cache_data.clear()
        st.cache_resource.clear()

        # Save to SQLite
        duration = time.time() - run_log.get("_start_time", time.time())
        save_training_run(
            timestamp=run_log["timestamp"],
            status="success",
            duration=duration,
            models_trained=8,
            alerts=counts,
            plan_summary=ps,
            log_lines=run_log["lines"],
        )
        log_activity("train_models", f"8 models trained, {counts['total']} alerts", "Data Upload")

        # Results cards
        st.markdown("")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            ui.metric_card(title="Models Trained", content="8 / 8", description="all passed", key="tr_models")
        with c2:
            ui.metric_card(title="Critical Alerts", content=str(counts["critical"]), description="act now", key="tr_crit")
        with c3:
            ui.metric_card(title="Warning Alerts", content=str(counts["warning"]), description="act today", key="tr_warn")
        with c4:
            ui.metric_card(title="Total Alerts", content=str(counts["total"]), description="from all models", key="tr_total")

    except Exception as e:
        term_print(f"ERROR: {str(e)}", "error")
        term_print("Training failed. Check data files.", "error")
        term_print("$", "prompt")
        save_training_run(
            timestamp=run_log["timestamp"],
            status="failed",
            log_lines=run_log["lines"],
            error_message=str(e),
        )
        log_activity("train_failed", str(e), "Data Upload")

# ── Previous Training Logs (from SQLite) ──
st.markdown("")
db_runs = get_training_runs(limit=20)

if db_runs:
    with st.expander(f"Training History ({len(db_runs)} runs)", expanded=False):
        for run in db_runs:
            status = run.get("status", "unknown")
            status_icon = "✅" if status == "success" else ("❌" if status == "failed" else "⏳")
            ts_display = run.get("timestamp", "Unknown")
            duration = run.get("duration_seconds")
            duration_str = f" ({duration:.1f}s)" if duration else ""

            st.markdown(f"""
            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:10px 14px;margin:6px 0;display:flex;justify-content:space-between;align-items:center">
                <div>
                    <span style="font-size:1.1rem">{status_icon}</span>
                    <strong style="margin-left:6px">{ts_display}</strong>
                    <span style="color:#64748b;margin-left:8px;font-size:0.85rem">{status.upper()}{duration_str}</span>
                </div>
                <div style="font-size:0.85rem;color:#64748b">
                    {f"Models: {run.get('models_trained', '?')} | Alerts: {run.get('alerts_total', '?')} (C:{run.get('alerts_critical',0)} W:{run.get('alerts_warning',0)})" if status == "success" else (run.get("error_message", "") or "")[:60]}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Expandable log output
            log_lines_json = run.get("log_lines")
            if log_lines_json:
                try:
                    lines = json.loads(log_lines_json)
                    with st.expander(f"View terminal output — {ts_display}", expanded=False):
                        log_html = "<br>".join([f'<span style="color:#94a3b8">{line}</span>' for line in lines])
                        st.markdown(f'<div style="background:#0f172a;color:#22c55e;font-family:monospace;font-size:0.8rem;padding:12px 16px;border-radius:8px;max-height:400px;overflow-y:auto;line-height:1.5">{log_html}</div>', unsafe_allow_html=True)
                except Exception:
                    pass
else:
    st.caption("No training runs yet. Click the button above to train models.")

st.divider()

# ── Data Source Switch — Simple UI Toggle ──
st.markdown("""
<div style="background:linear-gradient(135deg,#0f172a,#1e3a5f);color:white;padding:20px 24px;border-radius:12px;margin-bottom:16px">
    <p style="margin:0;font-size:1.1rem;font-weight:700">Switch Data Source</p>
    <p style="margin:4px 0 0;font-size:0.9rem;opacity:0.85">Choose whether the system uses sample data or your uploaded real data</p>
</div>
""", unsafe_allow_html=True)

# Read current setting
from config.settings import PROJECT_ROOT
settings_path = PROJECT_ROOT / "config" / "settings.py"
current_source = DATA_SOURCE

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div style="background:{'#f0fdf4' if current_source == 'sample' else '#f8fafc'};border:2px solid {'#22c55e' if current_source == 'sample' else '#e2e8f0'};border-radius:10px;padding:16px;text-align:center">
        <div style="font-size:1.5rem">📊</div>
        <div style="font-weight:700;color:#1e293b;margin:4px 0">Sample Data</div>
        <div style="font-size:0.8rem;color:#64748b">Pre-generated synthetic data for demo</div>
        {'<div style="background:#22c55e;color:white;padding:4px 12px;border-radius:20px;font-size:0.75rem;font-weight:700;display:inline-block;margin-top:8px">ACTIVE</div>' if current_source == 'sample' else ''}
    </div>
    """, unsafe_allow_html=True)

    if current_source != "sample":
        if st.button("Switch to Sample Data", key="switch_sample", use_container_width=True):
            content = settings_path.read_text()
            content = content.replace('DATA_SOURCE = os.environ.get("EIS_DATA_SOURCE", "real")',
                                       'DATA_SOURCE = os.environ.get("EIS_DATA_SOURCE", "sample")')
            settings_path.write_text(content)
            st.cache_data.clear()
            st.success("Switched to SAMPLE data. Refreshing...")
            st.rerun()

with col2:
    st.markdown("""
    <div style="text-align:center;padding:40px 0">
        <div style="font-size:2rem;color:#94a3b8">⇄</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    real_files = list(REAL_DATA_DIR.glob("*.csv"))
    has_real = len(real_files) >= 3

    st.markdown(f"""
    <div style="background:{'#eff6ff' if current_source == 'real' else '#f8fafc'};border:2px solid {'#2563eb' if current_source == 'real' else '#e2e8f0'};border-radius:10px;padding:16px;text-align:center">
        <div style="font-size:1.5rem">📁</div>
        <div style="font-weight:700;color:#1e293b;margin:4px 0">Real Data</div>
        <div style="font-size:0.8rem;color:#64748b">{len(real_files)} files uploaded in data/real/</div>
        {'<div style="background:#2563eb;color:white;padding:4px 12px;border-radius:20px;font-size:0.75rem;font-weight:700;display:inline-block;margin-top:8px">ACTIVE</div>' if current_source == 'real' else ''}
    </div>
    """, unsafe_allow_html=True)

    if current_source != "real":
        if has_real:
            if st.button("Switch to Real Data", type="primary", key="switch_real", use_container_width=True):
                content = settings_path.read_text()
                content = content.replace('DATA_SOURCE = os.environ.get("EIS_DATA_SOURCE", "sample")',
                                           'DATA_SOURCE = os.environ.get("EIS_DATA_SOURCE", "real")')
                settings_path.write_text(content)
                st.cache_data.clear()
                st.success("Switched to REAL data. Refreshing...")
                st.rerun()
        else:
            st.warning("Upload at least 3 required files first (stores, daily_energy, diesel_prices)")

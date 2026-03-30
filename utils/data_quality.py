"""
Data Quality Engine — Validation, scoring, and compliance tracking.

Validates incoming energy records against business rules from the BCP Framework doc.
Tracks per-site submission compliance and flags issues.

Rules from doc Section 5.3:
- Every site must submit daily by 8:00 PM
- generator_hours + grid_hours must not exceed 24
- Diesel stock variance > 20% vs previous day triggers validation request
- Missing data handled with site average imputation — flagged in output
- Data quality score reported weekly — sites below 90% escalated
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
from utils.database import save_quality_log, get_quality_report, get_compliance_summary


# ══════════════════════════════════════════════════════════════════════════════
# RECORD VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

def validate_energy_record(row: dict) -> dict:
    """Validate a single daily_energy record against business rules.

    Args:
        row: dict with daily_energy columns

    Returns:
        dict with is_valid, completeness_pct, issues list
    """
    issues = []
    required_fields = [
        "date", "store_id", "blackout_hours", "generator_hours",
        "grid_hours", "diesel_consumed_liters", "diesel_cost_mmk",
    ]

    # Check required fields
    missing = [f for f in required_fields if not row.get(f) and row.get(f) != 0]
    if missing:
        issues.append(f"Missing required fields: {', '.join(missing)}")

    # Rule: generator_hours + grid_hours <= 24
    gen_hrs = float(row.get("generator_hours", 0) or 0)
    grid_hrs = float(row.get("grid_hours", 0) or 0)
    if gen_hrs + grid_hrs > 24.5:  # Small tolerance for rounding
        issues.append(f"generator_hours ({gen_hrs}) + grid_hours ({grid_hrs}) = {gen_hrs + grid_hrs:.1f} exceeds 24")

    # Rule: blackout_hours should be reasonable (0-24)
    blackout = float(row.get("blackout_hours", 0) or 0)
    if blackout < 0 or blackout > 24:
        issues.append(f"blackout_hours ({blackout}) outside valid range 0-24")

    # Rule: diesel consumed should be non-negative
    diesel = float(row.get("diesel_consumed_liters", 0) or 0)
    if diesel < 0:
        issues.append(f"diesel_consumed_liters ({diesel}) is negative")

    # Rule: if generator ran, diesel should be consumed
    if gen_hrs > 1 and diesel == 0:
        issues.append(f"Generator ran {gen_hrs}hrs but diesel_consumed is 0 — check meter")

    # Completeness: count non-null fields out of all expected
    all_fields = [
        "date", "store_id", "blackout_hours", "generator_hours", "grid_hours",
        "diesel_consumed_liters", "diesel_cost_mmk", "grid_cost_mmk",
        "solar_kwh", "total_energy_cost_mmk",
    ]
    filled = sum(1 for f in all_fields if row.get(f) is not None and row.get(f) != "")
    completeness = round(filled / len(all_fields) * 100, 1)

    return {
        "is_valid": len(issues) == 0,
        "completeness_pct": completeness,
        "issues": issues,
    }


def check_stock_variance(store_id: str, today_stock: float,
                          yesterday_stock: float) -> Optional[dict]:
    """Flag if diesel stock variance > 20% vs previous day.

    Returns issue dict if variance exceeds threshold, None otherwise.
    """
    if yesterday_stock <= 0:
        return None

    variance_pct = abs(today_stock - yesterday_stock) / yesterday_stock * 100

    if variance_pct > 20:
        direction = "increase" if today_stock > yesterday_stock else "decrease"
        return {
            "store_id": store_id,
            "issue": f"Diesel stock {direction} of {variance_pct:.0f}% "
                     f"({yesterday_stock:.0f}L → {today_stock:.0f}L) — verify reading",
            "variance_pct": round(variance_pct, 1),
            "severity": "HIGH" if variance_pct > 40 else "MEDIUM",
        }
    return None


# ══════════════════════════════════════════════════════════════════════════════
# BATCH VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

def validate_daily_energy_batch(energy_df: pd.DataFrame,
                                 inventory_df: pd.DataFrame = None) -> pd.DataFrame:
    """Validate all records in a daily_energy DataFrame.

    Returns DataFrame with store_id, date, is_valid, completeness_pct, issues.
    """
    results = []

    for _, row in energy_df.iterrows():
        validation = validate_energy_record(row.to_dict())
        results.append({
            "store_id": row.get("store_id", ""),
            "date": row.get("date", ""),
            "is_valid": validation["is_valid"],
            "completeness_pct": validation["completeness_pct"],
            "issues": "; ".join(validation["issues"]) if validation["issues"] else "",
            "issue_count": len(validation["issues"]),
        })

    # Check stock variance if inventory data available
    if inventory_df is not None and len(inventory_df) > 0:
        inv_sorted = inventory_df.sort_values(["store_id", "date"])
        for store_id in inv_sorted["store_id"].unique():
            store_inv = inv_sorted[inv_sorted["store_id"] == store_id]
            if len(store_inv) >= 2:
                today = store_inv.iloc[-1]
                yesterday = store_inv.iloc[-2]
                variance = check_stock_variance(
                    store_id,
                    today["diesel_stock_liters"],
                    yesterday["diesel_stock_liters"],
                )
                if variance:
                    # Find matching result row and append issue
                    for r in results:
                        if r["store_id"] == store_id and str(r["date"]) == str(today["date"]):
                            r["issues"] = (r["issues"] + "; " if r["issues"] else "") + variance["issue"]
                            r["issue_count"] += 1
                            break

    return pd.DataFrame(results)


# ══════════════════════════════════════════════════════════════════════════════
# SUBMISSION SCORING
# ══════════════════════════════════════════════════════════════════════════════

def score_submission(store_id: str, store_name: str, date: str,
                      energy_row: dict = None, submitted_by: str = "",
                      submitted_at: str = None, deadline_hour: int = 20) -> dict:
    """Score a single store's daily submission and save to DB.

    Args:
        store_id: store identifier
        store_name: store display name
        date: submission date (YYYY-MM-DD)
        energy_row: the daily_energy record (None if not submitted)
        submitted_by: data champion name (from daily_energy.submitted_by)
        submitted_at: timestamp (from daily_energy.submitted_at)
        deadline_hour: submission deadline (default 8 PM = 20)

    Returns:
        dict with completeness_pct, issues, is_late
    """
    if energy_row is None:
        # Not submitted at all
        result = {
            "completeness_pct": 0,
            "issues": ["NOT SUBMITTED"],
            "is_late": True,
            "submitted_by": "",
            "submitted_at": None,
        }
    else:
        validation = validate_energy_record(energy_row)
        # Check if late
        is_late = False
        if submitted_at:
            try:
                sub_time = pd.to_datetime(submitted_at)
                deadline = pd.to_datetime(date) + timedelta(hours=deadline_hour)
                is_late = sub_time > deadline
            except Exception:
                pass

        result = {
            "completeness_pct": validation["completeness_pct"],
            "issues": validation["issues"],
            "is_late": is_late,
            "submitted_by": submitted_by or energy_row.get("submitted_by", ""),
            "submitted_at": submitted_at or energy_row.get("submitted_at", ""),
        }

    # Save to database
    save_quality_log(
        store_id=store_id,
        store_name=store_name,
        date=date,
        completeness_pct=result["completeness_pct"],
        issues=result["issues"],
        submitted_by=result["submitted_by"],
        submitted_at=result["submitted_at"],
        is_late=result["is_late"],
    )

    return result


def score_all_submissions(stores_df: pd.DataFrame, energy_df: pd.DataFrame,
                           target_date: str = None) -> pd.DataFrame:
    """Score submissions for all stores for a given date.

    Returns DataFrame with per-store compliance status.
    """
    if target_date is None:
        target_date = energy_df["date"].max()

    target_date_str = str(pd.to_datetime(target_date).date())
    today_energy = energy_df[energy_df["date"] == pd.to_datetime(target_date)]

    results = []
    for _, store in stores_df.iterrows():
        sid = store["store_id"]
        store_data = today_energy[today_energy["store_id"] == sid]

        if len(store_data) > 0:
            row = store_data.iloc[0].to_dict()
            score = score_submission(
                sid, store["name"], target_date_str, row,
                submitted_by=row.get("submitted_by", ""),
                submitted_at=row.get("submitted_at", ""),
            )
            status = "ON TIME" if not score["is_late"] and score["completeness_pct"] >= 90 else (
                "LATE" if score["is_late"] else "INCOMPLETE"
            )
        else:
            score = score_submission(sid, store["name"], target_date_str, None)
            status = "MISSING"

        results.append({
            "store_id": sid,
            "name": store["name"],
            "sector": store["sector"],
            "channel": store["channel"],
            "date": target_date_str,
            "completeness_pct": score["completeness_pct"],
            "is_late": score["is_late"],
            "issue_count": len(score["issues"]),
            "issues": "; ".join(score["issues"]) if score["issues"] else "",
            "submitted_by": score["submitted_by"],
            "status": status,
        })

    return pd.DataFrame(results)


# ══════════════════════════════════════════════════════════════════════════════
# COMPLIANCE REPORTING
# ══════════════════════════════════════════════════════════════════════════════

def get_network_compliance(stores_df: pd.DataFrame = None) -> dict:
    """Get network-wide compliance stats from DB.

    Returns dict with compliance metrics + list of stores below 90%.
    """
    summary = get_compliance_summary()

    # Get per-store breakdown if we have recent quality logs
    quality_log = get_quality_report(limit=500)
    if quality_log:
        store_scores = {}
        for entry in quality_log:
            sid = entry["store_id"]
            if sid not in store_scores:
                store_scores[sid] = []
            store_scores[sid].append(entry.get("completeness_pct", 100))

        # Stores below 90% average
        below_90 = [
            {"store_id": sid, "avg_completeness": round(np.mean(scores), 1)}
            for sid, scores in store_scores.items()
            if np.mean(scores) < 90
        ]
        summary["stores_below_90_list"] = sorted(below_90, key=lambda x: x["avg_completeness"])
    else:
        summary["stores_below_90_list"] = []

    return summary


def get_missing_stores(stores_df: pd.DataFrame, energy_df: pd.DataFrame,
                        target_date=None) -> list:
    """Get list of stores that haven't submitted for a given date.

    Used by the 8 PM submission reminder.
    """
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")

    submitted = energy_df[
        energy_df["date"] == pd.to_datetime(target_date)
    ]["store_id"].unique().tolist()

    all_stores = stores_df["store_id"].unique().tolist()
    missing_ids = [s for s in all_stores if s not in submitted]

    # Get names
    store_map = dict(zip(stores_df["store_id"], stores_df["name"]))
    return [f"{sid} — {store_map.get(sid, sid)}" for sid in missing_ids]

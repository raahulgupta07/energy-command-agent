"""
SQLite Database Layer for Energy Intelligence System.
Single file database: data/eis.db
Handles: training logs, upload history, chat messages, insights cache, activity log.
Thread-safe for 10+ concurrent users.
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

_data_dir = Path(__file__).parent.parent / "data"
_db_dir = _data_dir / "db"
_db_dir.mkdir(parents=True, exist_ok=True)
DB_PATH = _db_dir / "eis.db"


@contextmanager
def get_db():
    """Thread-safe database connection with WAL mode for concurrent reads."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")  # Allow concurrent reads
    conn.execute("PRAGMA busy_timeout=5000")  # Wait up to 5s if locked
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create all tables if they don't exist."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS training_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'running',
                duration_seconds REAL,
                models_trained INTEGER DEFAULT 0,
                alerts_total INTEGER DEFAULT 0,
                alerts_critical INTEGER DEFAULT 0,
                alerts_warning INTEGER DEFAULT 0,
                alerts_info INTEGER DEFAULT 0,
                plan_summary TEXT,
                log_lines TEXT,
                error_message TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS upload_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                destination TEXT NOT NULL,
                rows_count INTEGER,
                columns_count INTEGER,
                file_size_kb REAL,
                validation_status TEXT,
                validation_errors TEXT,
                uploaded_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS insights_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                insights_json TEXT NOT NULL,
                summary_text TEXT,
                briefing_text TEXT,
                llm_summary TEXT,
                generated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                detail TEXT,
                page TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS bcp_incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id TEXT NOT NULL,
                store_name TEXT,
                incident_type TEXT NOT NULL,
                duration_hours REAL,
                response_time_min REAL,
                estimated_loss_mmk REAL DEFAULT 0,
                actions_taken TEXT,
                lessons_learned TEXT,
                severity TEXT DEFAULT 'medium',
                reported_by TEXT,
                incident_date TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS bcp_drills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id TEXT NOT NULL,
                store_name TEXT,
                drill_type TEXT NOT NULL,
                scheduled_date TEXT NOT NULL,
                completed_date TEXT,
                status TEXT DEFAULT 'scheduled',
                readiness_score REAL,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS page_intelligence_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page_id TEXT NOT NULL,
                data_hash TEXT NOT NULL,
                briefing_json TEXT NOT NULL,
                model_used TEXT,
                generated_at TEXT DEFAULT (datetime('now')),
                UNIQUE(page_id, data_hash)
            );

            CREATE TABLE IF NOT EXISTS element_captions_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page_id TEXT NOT NULL,
                data_hash TEXT NOT NULL,
                captions_json TEXT NOT NULL,
                model_used TEXT,
                generated_at TEXT DEFAULT (datetime('now')),
                UNIQUE(page_id, data_hash)
            );

            CREATE TABLE IF NOT EXISTS saved_scenarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                diesel_price_change REAL DEFAULT 0,
                blackout_hours_change REAL DEFAULT 0,
                fx_change REAL DEFAULT 0,
                solar_new_sites INTEGER DEFAULT 0,
                result_energy_cost REAL,
                result_diesel_cost REAL,
                result_sales REAL,
                result_ebitda REAL,
                result_ebitda_impact_pct REAL,
                result_stores_full INTEGER,
                result_stores_reduced INTEGER,
                result_stores_critical INTEGER,
                result_stores_closed INTEGER,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)


# ══════════════════════════════════════════════════════════════════════════════
# TRAINING RUNS
# ══════════════════════════════════════════════════════════════════════════════

def save_training_run(timestamp: str, status: str, duration: float = None,
                       models_trained: int = 0, alerts: dict = None,
                       plan_summary: dict = None, log_lines: list = None,
                       error_message: str = None) -> int:
    """Save a training run to the database. Returns the run ID."""
    alerts = alerts or {}
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO training_runs (timestamp, status, duration_seconds, models_trained,
                alerts_total, alerts_critical, alerts_warning, alerts_info,
                plan_summary, log_lines, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, status, duration, models_trained,
            alerts.get("total", 0), alerts.get("critical", 0),
            alerts.get("warning", 0), alerts.get("info", 0),
            json.dumps(plan_summary) if plan_summary else None,
            json.dumps(log_lines) if log_lines else None,
            error_message,
        ))
        return cursor.lastrowid


def get_training_runs(limit: int = 20) -> list:
    """Get recent training runs, newest first."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM training_runs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_training_run(run_id: int) -> dict:
    """Get a single training run by ID."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM training_runs WHERE id = ?", (run_id,)
        ).fetchone()
        return dict(row) if row else None


# ══════════════════════════════════════════════════════════════════════════════
# UPLOAD HISTORY
# ══════════════════════════════════════════════════════════════════════════════

def save_upload(filename: str, destination: str, rows_count: int = 0,
                columns_count: int = 0, file_size_kb: float = 0,
                validation_status: str = "valid", validation_errors: str = None) -> int:
    """Record a file upload."""
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO upload_history (filename, destination, rows_count, columns_count,
                file_size_kb, validation_status, validation_errors)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (filename, destination, rows_count, columns_count,
              file_size_kb, validation_status, validation_errors))

        # Also log the activity
        conn.execute("""
            INSERT INTO activity_log (action, detail, page)
            VALUES (?, ?, ?)
        """, ("upload", f"{filename} → {destination} ({rows_count} rows)", "Data Upload"))

        return cursor.lastrowid


def get_upload_history(limit: int = 50) -> list:
    """Get recent uploads, newest first."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM upload_history ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


# ══════════════════════════════════════════════════════════════════════════════
# CHAT MESSAGES
# ══════════════════════════════════════════════════════════════════════════════

def save_chat_message(page: str, role: str, content: str) -> int:
    """Save a chat message."""
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO chat_messages (page, role, content)
            VALUES (?, ?, ?)
        """, (page, role, content))
        return cursor.lastrowid


def get_chat_messages(page: str, limit: int = 50) -> list:
    """Get chat messages for a page, oldest first."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM chat_messages WHERE page = ? ORDER BY id ASC LIMIT ?",
            (page, limit)
        ).fetchall()
        return [dict(r) for r in rows]


def clear_chat_messages(page: str):
    """Clear all chat messages for a page."""
    with get_db() as conn:
        conn.execute("DELETE FROM chat_messages WHERE page = ?", (page,))


def clear_all_chat():
    """Clear all chat messages."""
    with get_db() as conn:
        conn.execute("DELETE FROM chat_messages")


# ══════════════════════════════════════════════════════════════════════════════
# INSIGHTS CACHE
# ══════════════════════════════════════════════════════════════════════════════

def save_insights(insights: list, summary: str = None,
                   briefing: str = None, llm_summary: str = None) -> int:
    """Cache generated insights."""
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO insights_cache (insights_json, summary_text, briefing_text, llm_summary)
            VALUES (?, ?, ?, ?)
        """, (json.dumps(insights), summary, briefing, llm_summary))
        return cursor.lastrowid


def get_latest_insights() -> dict:
    """Get most recent cached insights."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM insights_cache ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row:
            r = dict(row)
            r["insights"] = json.loads(r["insights_json"]) if r["insights_json"] else []
            return r
        return None


# ══════════════════════════════════════════════════════════════════════════════
# SAVED SCENARIOS
# ══════════════════════════════════════════════════════════════════════════════

def save_scenario(name: str, params: dict, results: dict, notes: str = None) -> int:
    """Save a scenario simulation."""
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO saved_scenarios (name, diesel_price_change, blackout_hours_change,
                fx_change, solar_new_sites, result_energy_cost, result_diesel_cost,
                result_sales, result_ebitda, result_ebitda_impact_pct,
                result_stores_full, result_stores_reduced, result_stores_critical,
                result_stores_closed, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            params.get("diesel_price_change_pct", 0),
            params.get("blackout_hours_change_pct", 0),
            params.get("fx_change_pct", 0),
            params.get("solar_new_sites", 0),
            results.get("scenario_energy_cost", 0),
            results.get("scenario_diesel_cost", 0),
            results.get("scenario_sales", 0),
            results.get("scenario_ebitda", 0),
            results.get("ebitda_impact_pct", 0),
            results.get("est_stores_full", 0),
            results.get("est_stores_reduced", 0),
            results.get("est_stores_critical", 0),
            results.get("est_stores_closed", 0),
            notes,
        ))
        return cursor.lastrowid


def get_saved_scenarios(limit: int = 50) -> list:
    """Get saved scenarios, newest first."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM saved_scenarios ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def delete_scenario(scenario_id: int):
    """Delete a saved scenario."""
    with get_db() as conn:
        conn.execute("DELETE FROM saved_scenarios WHERE id = ?", (scenario_id,))


# ══════════════════════════════════════════════════════════════════════════════
# ACTIVITY LOG
# ══════════════════════════════════════════════════════════════════════════════

def log_activity(action: str, detail: str = None, page: str = None):
    """Log a user activity."""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO activity_log (action, detail, page)
            VALUES (?, ?, ?)
        """, (action, detail, page))


def get_activity_log(limit: int = 100) -> list:
    """Get recent activity, newest first."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM activity_log ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


# ══════════════════════════════════════════════════════════════════════════════
# STATS
# ══════════════════════════════════════════════════════════════════════════════

def get_db_stats() -> dict:
    """Get database statistics."""
    with get_db() as conn:
        stats = {}
        for table in ["training_runs", "upload_history", "chat_messages", "insights_cache", "activity_log"]:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            stats[table] = count
        stats["db_size_kb"] = round(DB_PATH.stat().st_size / 1024, 1) if DB_PATH.exists() else 0
        return stats


# ══════════════════════════════════════════════════════════════════════════════
# PAGE INTELLIGENCE CACHE
# ══════════════════════════════════════════════════════════════════════════════

def get_cached_page_intelligence(page_id: str, data_hash: str) -> dict:
    """Get cached page intelligence if data hasn't changed."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT briefing_json, generated_at FROM page_intelligence_cache WHERE page_id = ? AND data_hash = ?",
            (page_id, data_hash)
        ).fetchone()
        if row:
            try:
                return {"briefing": json.loads(row["briefing_json"]), "generated_at": row["generated_at"]}
            except (json.JSONDecodeError, KeyError):
                pass
    return {}


def save_page_intelligence(page_id: str, data_hash: str, briefing: dict, model_used: str = ""):
    """Save page intelligence to DB. Replaces existing entry for same page+hash."""
    with get_db() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO page_intelligence_cache (page_id, data_hash, briefing_json, model_used)
               VALUES (?, ?, ?, ?)""",
            (page_id, data_hash, json.dumps(briefing, default=str), model_used)
        )


def get_cached_element_captions(page_id: str, data_hash: str) -> dict:
    """Get cached element captions if data hasn't changed."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT captions_json, generated_at FROM element_captions_cache WHERE page_id = ? AND data_hash = ?",
            (page_id, data_hash)
        ).fetchone()
        if row:
            try:
                return {"captions": json.loads(row["captions_json"]), "generated_at": row["generated_at"]}
            except (json.JSONDecodeError, KeyError):
                pass
    return {}


def save_element_captions(page_id: str, data_hash: str, captions: dict, model_used: str = ""):
    """Save element captions to DB."""
    with get_db() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO element_captions_cache (page_id, data_hash, captions_json, model_used)
               VALUES (?, ?, ?, ?)""",
            (page_id, data_hash, json.dumps(captions, default=str), model_used)
        )


# ══════════════════════════════════════════════════════════════════════════════
# BCP INCIDENTS
# ══════════════════════════════════════════════════════════════════════════════

def save_incident(store_id, store_name, incident_type, duration_hours, response_time_min,
                  estimated_loss_mmk=0, actions_taken="", lessons_learned="",
                  severity="medium", reported_by="", incident_date=""):
    with get_db() as conn:
        return conn.execute(
            """INSERT INTO bcp_incidents (store_id, store_name, incident_type, duration_hours,
               response_time_min, estimated_loss_mmk, actions_taken, lessons_learned,
               severity, reported_by, incident_date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (store_id, store_name, incident_type, duration_hours, response_time_min,
             estimated_loss_mmk, actions_taken, lessons_learned, severity, reported_by, incident_date)
        ).lastrowid


def get_incidents(limit=50):
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM bcp_incidents ORDER BY incident_date DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]


def delete_incident(incident_id):
    with get_db() as conn:
        conn.execute("DELETE FROM bcp_incidents WHERE id = ?", (incident_id,))


# ══════════════════════════════════════════════════════════════════════════════
# BCP DRILLS
# ══════════════════════════════════════════════════════════════════════════════

def save_drill(store_id, store_name, drill_type, scheduled_date, notes=""):
    with get_db() as conn:
        return conn.execute(
            """INSERT INTO bcp_drills (store_id, store_name, drill_type, scheduled_date, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (store_id, store_name, drill_type, scheduled_date, notes)
        ).lastrowid


def complete_drill(drill_id, readiness_score, notes=""):
    with get_db() as conn:
        conn.execute(
            """UPDATE bcp_drills SET status = 'completed', completed_date = datetime('now'),
               readiness_score = ?, notes = ? WHERE id = ?""",
            (readiness_score, notes, drill_id)
        )


def get_drills(limit=50):
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM bcp_drills ORDER BY scheduled_date DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]


def delete_drill(drill_id):
    with get_db() as conn:
        conn.execute("DELETE FROM bcp_drills WHERE id = ?", (drill_id,))


def clear_intelligence_cache():
    """Clear all cached intelligence and captions (call after data upload)."""
    with get_db() as conn:
        conn.execute("DELETE FROM page_intelligence_cache")
        conn.execute("DELETE FROM element_captions_cache")


# Initialize database on import
init_db()

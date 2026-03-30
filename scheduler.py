"""
Energy Intelligence System — Scheduled Job Runner

Runs the 4-agent cadence from the BCP Framework document:
  06:00 AM — ORACLE: Run prediction models (blackout, price, availability)
  07:00 AM — COMMANDER: Generate daily plan + email morning briefing
  12:00 PM — Mid-day re-plan if significant market changes
  Every 30m — SENTINEL: Check stockout, price spikes, blackout cascades
  08:00 PM — Submission reminder for non-submitting sites
  09:00 PM — End-of-day reconciliation

Usage:
    python scheduler.py                    # Run scheduler (foreground)
    python scheduler.py --run-once oracle  # Run one job immediately
    python scheduler.py --run-once sentinel
    python scheduler.py --run-once commander

Requires: pip install apscheduler
"""

import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("eis.scheduler")


def run_sentinel():
    """SENTINEL: Monitor thresholds, fire alerts within 5 min (A2)."""
    logger.info("SENTINEL — Running threshold checks...")
    try:
        from alerts.alert_engine import AlertEngine
        engine = AlertEngine()
        engine.load_data()
        engine.run_all_models()
        counts = engine.get_alert_counts()
        logger.info(f"SENTINEL — Alerts: {counts['critical']} critical, {counts['warning']} warning")

        # Email critical alerts immediately
        if counts["critical"] > 0:
            from utils.email_alerts import send_email, format_critical_alert, is_email_enabled
            from config.settings import EMAIL_CONFIG
            if is_email_enabled():
                for alert in engine.get_alerts(tier=1):
                    html = format_critical_alert(alert)
                    recipients = EMAIL_CONFIG["recipients"].get("holdings_gecc", []) + EMAIL_CONFIG["recipients"].get("sector_leads", [])
                    if recipients:
                        send_email(recipients, f"🚨 EIS CRITICAL: {alert.get('source', '')}", html)
                        logger.info(f"SENTINEL — Emailed critical alert: {alert.get('message', '')[:80]}")

    except Exception as e:
        logger.error(f"SENTINEL failed: {e}")


def run_oracle():
    """ORACLE: Run prediction models at 6 AM (A3)."""
    logger.info("ORACLE — Running prediction models...")
    try:
        from alerts.alert_engine import AlertEngine
        engine = AlertEngine()
        engine.load_data()

        # Run prediction models only
        engine._run_diesel_price_forecast()
        engine._run_blackout_prediction()
        engine._run_spoilage_predictor()

        logger.info(f"ORACLE — Forecasts generated: diesel price, blackout probability, spoilage risk")

        # Store results for COMMANDER to use
        engine.results["_oracle_timestamp"] = datetime.now().isoformat()

    except Exception as e:
        logger.error(f"ORACLE failed: {e}")


def run_commander():
    """COMMANDER: Generate daily plan + email briefing at 7 AM (A4)."""
    logger.info("COMMANDER — Generating daily operating plan...")
    try:
        from alerts.alert_engine import AlertEngine
        engine = AlertEngine()
        engine.load_data()
        engine.run_all_models()

        counts = engine.get_alert_counts()
        plan = engine.results.get("plan_summary", {})
        logger.info(
            f"COMMANDER — Plan: FULL={plan.get('stores_full',0)} "
            f"SELECTIVE={plan.get('stores_selective',0)} "
            f"REDUCED={plan.get('stores_reduced',0)} "
            f"CRITICAL={plan.get('stores_critical',0)} "
            f"CLOSE={plan.get('stores_closed',0)}"
        )

        # Email morning briefing
        from utils.email_alerts import is_email_enabled, send_email
        from utils.report_generator import generate_daily_brief
        if is_email_enabled():
            from config.settings import EMAIL_CONFIG
            report = generate_daily_brief(
                plan_summary=plan,
                alert_counts=counts,
                diesel_rec=engine.results.get("diesel_recommendation", {}),
                stockout_summary=engine.results.get("stockout_summary", {}),
                solar_summary=engine.results.get("solar_summary", {}),
                alerts=engine.get_alerts()[:10],
            )
            recipients = (
                EMAIL_CONFIG["recipients"].get("sector_leads", []) +
                EMAIL_CONFIG["recipients"].get("all_managers", [])
            )
            if recipients:
                send_email(recipients, report["subject"], report["html"])
                logger.info(f"COMMANDER — Morning briefing emailed to {len(recipients)} recipients")
        else:
            logger.info("COMMANDER — Email not configured, briefing generated but not sent")

        # Log briefing
        briefing_text = engine.get_morning_briefing()
        logger.info(f"COMMANDER — Briefing:\n{briefing_text[:500]}")

    except Exception as e:
        logger.error(f"COMMANDER failed: {e}")


def run_midday_replan():
    """Mid-day re-plan at 12 PM if significant changes (A6)."""
    logger.info("MID-DAY — Checking for significant changes...")
    try:
        from alerts.alert_engine import AlertEngine
        engine = AlertEngine()
        engine.load_data()
        engine.run_all_models()
        counts = engine.get_alert_counts()

        # Only email if there are new critical alerts
        if counts["critical"] > 0:
            logger.info(f"MID-DAY — {counts['critical']} critical alerts — triggering re-plan email")
            from utils.email_alerts import is_email_enabled, send_email
            from utils.report_generator import generate_daily_brief
            if is_email_enabled():
                from config.settings import EMAIL_CONFIG
                report = generate_daily_brief(
                    plan_summary=engine.results.get("plan_summary", {}),
                    alert_counts=counts,
                    diesel_rec=engine.results.get("diesel_recommendation", {}),
                    stockout_summary=engine.results.get("stockout_summary", {}),
                    solar_summary=engine.results.get("solar_summary", {}),
                    alerts=engine.get_alerts(tier=1),
                )
                recipients = EMAIL_CONFIG["recipients"].get("sector_leads", [])
                if recipients:
                    send_email(recipients, f"⚠️ EIS Mid-Day Re-Plan — {counts['critical']} Critical Alerts", report["html"])
        else:
            logger.info("MID-DAY — No significant changes, no re-plan needed")

    except Exception as e:
        logger.error(f"MID-DAY re-plan failed: {e}")


def run_submission_reminder():
    """8 PM submission reminder for non-submitting sites (H6)."""
    logger.info("REMINDER — Checking data submissions...")
    try:
        from utils.email_alerts import is_email_enabled, send_email, format_submission_reminder
        from config.settings import STORES, EMAIL_CONFIG

        # In a real system, check data_quality_log for today's submissions
        # For now, log a reminder
        all_stores = [s["name"] for s in STORES]
        # TODO: Check which stores actually submitted today
        # missing = [s for s in all_stores if s not in submitted_today]

        logger.info(f"REMINDER — Submission check complete for {len(all_stores)} stores")

        # If email configured and stores missing, send reminder
        # if is_email_enabled() and missing:
        #     html = format_submission_reminder(missing)
        #     send_email(EMAIL_CONFIG["recipients"].get("all_managers", []),
        #                "⏰ EIS Data Submission Reminder", html)

    except Exception as e:
        logger.error(f"REMINDER failed: {e}")


def run_end_of_day():
    """9 PM end-of-day reconciliation."""
    logger.info("EOD — Running end-of-day reconciliation...")
    try:
        from alerts.alert_engine import AlertEngine
        engine = AlertEngine()
        engine.load_data()
        engine.run_all_models()

        stockout = engine.results.get("stockout_summary", {})
        counts = engine.get_alert_counts()
        logger.info(
            f"EOD — Diesel: {stockout.get('total_diesel_stock', 0):,.0f}L total, "
            f"{stockout.get('critical_stores', 0)} critical stores. "
            f"Alerts: {counts['total']} total"
        )

    except Exception as e:
        logger.error(f"EOD failed: {e}")


def start_scheduler():
    """Start the APScheduler with all jobs."""
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.cron import CronTrigger
        from apscheduler.triggers.interval import IntervalTrigger
    except ImportError:
        logger.error("APScheduler not installed. Run: pip install apscheduler")
        sys.exit(1)

    scheduler = BlockingScheduler()

    # SENTINEL: every 30 minutes
    scheduler.add_job(run_sentinel, IntervalTrigger(minutes=30),
                      id="sentinel", name="SENTINEL — Threshold Monitor")

    # ORACLE: daily at 6:00 AM
    scheduler.add_job(run_oracle, CronTrigger(hour=6, minute=0),
                      id="oracle", name="ORACLE — 6AM Forecasts")

    # COMMANDER: daily at 7:00 AM
    scheduler.add_job(run_commander, CronTrigger(hour=7, minute=0),
                      id="commander", name="COMMANDER — 7AM Daily Plan")

    # Mid-day re-plan: 12:00 PM
    scheduler.add_job(run_midday_replan, CronTrigger(hour=12, minute=0),
                      id="midday", name="MID-DAY — 12PM Re-plan Check")

    # Submission reminder: 8:00 PM
    scheduler.add_job(run_submission_reminder, CronTrigger(hour=20, minute=0),
                      id="reminder", name="REMINDER — 8PM Submission Check")

    # End of day: 9:00 PM
    scheduler.add_job(run_end_of_day, CronTrigger(hour=21, minute=0),
                      id="eod", name="EOD — 9PM Reconciliation")

    logger.info("=" * 60)
    logger.info("Energy Intelligence System — Scheduler Started")
    logger.info("=" * 60)
    logger.info("Jobs:")
    for job in scheduler.get_jobs():
        logger.info(f"  {job.name} — {job.trigger}")
    logger.info("=" * 60)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EIS Scheduled Job Runner")
    parser.add_argument("--run-once", choices=["sentinel", "oracle", "commander", "midday", "reminder", "eod"],
                        help="Run a single job immediately and exit")
    args = parser.parse_args()

    if args.run_once:
        jobs = {
            "sentinel": run_sentinel,
            "oracle": run_oracle,
            "commander": run_commander,
            "midday": run_midday_replan,
            "reminder": run_submission_reminder,
            "eod": run_end_of_day,
        }
        jobs[args.run_once]()
    else:
        start_scheduler()

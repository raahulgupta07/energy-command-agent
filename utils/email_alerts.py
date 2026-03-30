"""
Email Alert System — Outlook SMTP
Sends HTML email alerts, briefings, and reports via Outlook.

All credentials from environment variables (EIS_SMTP_*).
Degrades gracefully if email not configured.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from config.settings import EMAIL_CONFIG, CURRENCY

logger = logging.getLogger(__name__)


def is_email_enabled() -> bool:
    """Check if email is configured."""
    return bool(EMAIL_CONFIG.get("sender") and EMAIL_CONFIG.get("password"))


def send_email(to: list, subject: str, html_body: str, cc: list = None) -> bool:
    """Send HTML email via Outlook SMTP.

    Args:
        to: list of recipient email addresses
        subject: email subject line
        html_body: HTML content
        cc: optional CC list

    Returns:
        True if sent successfully, False otherwise
    """
    if not is_email_enabled():
        logger.warning("Email not configured — skipping send. Set EIS_SMTP_USER and EIS_SMTP_PASSWORD.")
        return False

    if not to:
        logger.warning("No recipients specified — skipping send.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_CONFIG["sender"]
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)

    msg.attach(MIMEText(html_body, "html"))

    try:
        server = smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"])
        server.ehlo()
        server.starttls()
        server.login(EMAIL_CONFIG["sender"], EMAIL_CONFIG["password"])

        all_recipients = to + (cc or [])
        server.sendmail(EMAIL_CONFIG["sender"], all_recipients, msg.as_string())
        server.quit()

        logger.info(f"Email sent: '{subject}' → {', '.join(to)}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed — check EIS_SMTP_USER and EIS_SMTP_PASSWORD")
        return False
    except smtplib.SMTPConnectError:
        logger.error(f"Cannot connect to SMTP server {EMAIL_CONFIG['smtp_server']}:{EMAIL_CONFIG['smtp_port']}")
        return False
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL TEMPLATES
# ══════════════════════════════════════════════════════════════════════════════

_HEADER = """
<div style="background:linear-gradient(135deg,#0f172a,#1e3a5f);color:white;padding:20px 24px;border-radius:12px 12px 0 0">
    <h2 style="margin:0;color:white">{title}</h2>
    <p style="margin:4px 0 0;opacity:0.8;font-size:0.9rem">{subtitle}</p>
</div>
"""

_FOOTER = """
<div style="background:#f1f5f9;padding:12px 20px;border-radius:0 0 12px 12px;font-size:0.8rem;color:#64748b;margin-top:8px">
    Energy Intelligence System | Generated {timestamp} | <a href="{dashboard_url}">Open Dashboard</a>
</div>
"""

_METRIC_ROW = '<div style="display:inline-block;text-align:center;padding:8px 16px;margin:4px"><div style="font-size:1.4rem;font-weight:700;color:{color}">{value}</div><div style="font-size:0.75rem;color:#64748b">{label}</div></div>'

_ALERT_ROW = '<div style="background:{bg};border-left:4px solid {border};padding:8px 12px;margin:4px 0;border-radius:4px;font-size:0.85rem">{icon} <strong>{source}:</strong> {message}</div>'


def format_morning_briefing(plan_summary: dict, alert_counts: dict,
                             diesel_rec: dict, stockout_summary: dict,
                             solar_summary: dict, alerts: list = None,
                             dashboard_url: str = "http://localhost:8510") -> str:
    """Format the 7AM Daily Energy Brief as HTML email (H1)."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Metrics row
    metrics = "".join([
        _METRIC_ROW.format(value=plan_summary.get("stores_full", 0), label="FULL", color="#4CAF50"),
        _METRIC_ROW.format(value=plan_summary.get("stores_selective", 0), label="SELECTIVE", color="#2196F3"),
        _METRIC_ROW.format(value=plan_summary.get("stores_reduced", 0), label="REDUCED", color="#FF9800"),
        _METRIC_ROW.format(value=plan_summary.get("stores_critical", 0), label="CRITICAL", color="#F44336"),
        _METRIC_ROW.format(value=plan_summary.get("stores_closed", 0), label="CLOSED", color="#9E9E9E"),
    ])

    # Alert summary
    alert_html = ""
    if alerts:
        for a in alerts[:10]:
            tier = a.get("tier", 3)
            if tier == 1:
                bg, border, icon = "#fef2f2", "#ef4444", "🔴"
            elif tier == 2:
                bg, border, icon = "#fffbeb", "#f59e0b", "🟡"
            else:
                bg, border, icon = "#f0f9ff", "#3b82f6", "🔵"
            alert_html += _ALERT_ROW.format(
                bg=bg, border=border, icon=icon,
                source=a.get("source", ""), message=a.get("message", "")
            )
    else:
        alert_html = '<div style="padding:8px;color:#16a34a">No critical alerts</div>'

    # Diesel signal
    signal = diesel_rec.get("signal", "N/A")
    signal_color = "#ef4444" if "BUY" in signal else "#16a34a"

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:640px;margin:0 auto">
        {_HEADER.format(title="Daily Energy Brief", subtitle=f"Generated {ts} — {plan_summary.get('total_stores', 55)} stores")}
        <div style="background:white;padding:20px 24px;border:1px solid #e2e8f0">
            <h3 style="margin:0 0 12px;color:#1e293b">Operating Plan</h3>
            <div style="text-align:center;margin:12px 0">{metrics}</div>
            <div style="text-align:center;font-size:0.85rem;color:#64748b">
                Est. Daily Profit: <strong>{plan_summary.get('total_estimated_profit', 0):,.0f} {CURRENCY}</strong>
            </div>

            <hr style="border:none;border-top:1px solid #e2e8f0;margin:16px 0">

            <h3 style="margin:0 0 8px;color:#1e293b">Diesel Procurement</h3>
            <div style="background:#f8fafc;padding:10px 14px;border-radius:8px;margin:8px 0">
                Signal: <strong style="color:{signal_color}">{signal}</strong><br>
                {diesel_rec.get('reason', '')}
            </div>

            <hr style="border:none;border-top:1px solid #e2e8f0;margin:16px 0">

            <h3 style="margin:0 0 8px;color:#1e293b">Alerts ({alert_counts.get('total', 0)})</h3>
            {alert_html}

            <hr style="border:none;border-top:1px solid #e2e8f0;margin:16px 0">

            <div style="display:flex;gap:20px">
                <div style="flex:1">
                    <h4 style="margin:0 0 4px;color:#1e293b">Diesel Inventory</h4>
                    <div style="font-size:0.85rem">
                        Critical: <strong style="color:#ef4444">{stockout_summary.get('critical_stores', 0)}</strong> stores<br>
                        Avg coverage: <strong>{stockout_summary.get('avg_days_coverage', 0):.1f} days</strong>
                    </div>
                </div>
                <div style="flex:1">
                    <h4 style="margin:0 0 4px;color:#1e293b">Solar Network</h4>
                    <div style="font-size:0.85rem">
                        Active: <strong>{solar_summary.get('total_solar_sites', 0)}</strong> sites<br>
                        Offset: <strong>{solar_summary.get('total_diesel_offset_liters', 0):,.0f}L</strong>/day
                    </div>
                </div>
            </div>
        </div>
        {_FOOTER.format(timestamp=ts, dashboard_url=dashboard_url)}
    </div>
    """
    return html


def format_critical_alert(alert: dict, dashboard_url: str = "http://localhost:8510") -> str:
    """Format a critical (Tier 1) alert as HTML email (H5)."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:640px;margin:0 auto">
        <div style="background:#dc2626;color:white;padding:20px 24px;border-radius:12px 12px 0 0">
            <h2 style="margin:0;color:white">🚨 CRITICAL ALERT</h2>
            <p style="margin:4px 0 0;opacity:0.9">{alert.get('source', 'Energy Intelligence System')}</p>
        </div>
        <div style="background:white;padding:20px 24px;border:2px solid #fca5a5">
            <div style="background:#fef2f2;padding:16px;border-radius:8px;margin:8px 0">
                <p style="margin:0;font-size:1.05rem;font-weight:600;color:#991b1b">{alert.get('message', '')}</p>
            </div>
            <div style="margin:16px 0">
                <strong>Recommended Action:</strong><br>
                <div style="background:#f0fdf4;padding:10px 14px;border-radius:8px;margin-top:4px;color:#166534">
                    {alert.get('action', 'Review and take immediate action')}
                </div>
            </div>
            <div style="font-size:0.85rem;color:#64748b">
                Store: {alert.get('store_name', alert.get('store_id', 'N/A'))}<br>
                Time: {ts}
            </div>
        </div>
        {_FOOTER.format(timestamp=ts, dashboard_url=dashboard_url)}
    </div>
    """
    return html


def format_weekly_report(title: str, sections: list,
                          dashboard_url: str = "http://localhost:8510") -> str:
    """Format a weekly report (EBITDA Impact or Risk Dashboard) as HTML (H2, H3).

    Args:
        title: report title
        sections: list of {"heading": str, "content": str (HTML)}
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    sections_html = ""
    for s in sections:
        sections_html += f"""
        <div style="margin:16px 0">
            <h3 style="margin:0 0 8px;color:#1e293b">{s['heading']}</h3>
            <div style="background:#f8fafc;padding:12px 16px;border-radius:8px">{s['content']}</div>
        </div>
        """

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:640px;margin:0 auto">
        {_HEADER.format(title=title, subtitle=f"Week ending {datetime.now().strftime('%Y-%m-%d')}")}
        <div style="background:white;padding:20px 24px;border:1px solid #e2e8f0">
            {sections_html}
        </div>
        {_FOOTER.format(timestamp=ts, dashboard_url=dashboard_url)}
    </div>
    """
    return html


def format_submission_reminder(missing_stores: list,
                                deadline: str = "8:00 PM",
                                dashboard_url: str = "http://localhost:8510") -> str:
    """Format a submission reminder email for non-submitting sites (H6)."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    store_list = "".join([
        f'<div style="padding:4px 0;border-bottom:1px solid #f1f5f9">• {s}</div>'
        for s in missing_stores[:20]
    ])
    if len(missing_stores) > 20:
        store_list += f'<div style="padding:4px 0;color:#64748b">...and {len(missing_stores)-20} more</div>'

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:640px;margin:0 auto">
        <div style="background:#f59e0b;color:white;padding:20px 24px;border-radius:12px 12px 0 0">
            <h2 style="margin:0;color:white">⏰ Data Submission Reminder</h2>
            <p style="margin:4px 0 0;opacity:0.9">Deadline: {deadline} today</p>
        </div>
        <div style="background:white;padding:20px 24px;border:1px solid #fde68a">
            <p style="margin:0 0 12px">The following <strong>{len(missing_stores)} stores</strong> have not submitted today's energy data:</p>
            <div style="background:#fffbeb;padding:12px 16px;border-radius:8px">{store_list}</div>
            <p style="margin:12px 0 0;font-size:0.85rem;color:#92400e">
                Please submit via the Data Upload page or contact your data champion.
            </p>
        </div>
        {_FOOTER.format(timestamp=ts, dashboard_url=dashboard_url)}
    </div>
    """
    return html

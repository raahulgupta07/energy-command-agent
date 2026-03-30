"""
Smart Table — enhanced table rendering with conditional formatting,
severity colors, sortable columns, and search.
"""

import streamlit as st
import pandas as pd


def render_smart_table(df: pd.DataFrame, key: str, title: str = "",
                       highlight_cols: dict = None, max_height: int = 400,
                       severity_col: str = None, bar_col: str = None):
    """Render a visually enhanced table with conditional formatting.

    Args:
        df: DataFrame to display
        key: Unique Streamlit key
        title: Optional table title
        highlight_cols: Dict of {col_name: {"good": "low"|"high", "thresholds": [warn, crit]}}
                        Colors cells based on value thresholds.
        max_height: Max table height in px
        severity_col: Column name containing severity levels (CRITICAL/HIGH/MEDIUM/LOW or similar)
        bar_col: Column name to show as a progress bar (values 0-100 or 0-1)
    """
    if df is None or len(df) == 0:
        st.info("No data available.")
        return

    # Build styled HTML table
    html = _build_table_html(df, highlight_cols, severity_col, bar_col, max_height)

    if title:
        st.markdown(f"""<div style="font-size:0.9rem;font-weight:700;color:#0f172a;
            margin-bottom:8px;display:flex;align-items:center;gap:6px">
            <span style="color:#6366f1">■</span> {title}
            <span style="font-size:0.72rem;color:#94a3b8;font-weight:400;margin-left:auto">
                {len(df)} rows</span>
        </div>""", unsafe_allow_html=True)

    st.markdown(html, unsafe_allow_html=True)


def _build_table_html(df: pd.DataFrame, highlight_cols: dict = None,
                      severity_col: str = None, bar_col: str = None,
                      max_height: int = 400) -> str:
    """Build HTML for a styled table."""
    highlight_cols = highlight_cols or {}

    # Header
    header_cells = ""
    for col in df.columns:
        header_cells += f"""<th style="padding:10px 12px;text-align:left;font-size:0.78rem;
            font-weight:700;color:#475569;background:#f8fafc;border-bottom:2px solid #e2e8f0;
            position:sticky;top:0;white-space:nowrap">{col}</th>"""

    # Body rows
    body_rows = ""
    for idx, row in df.iterrows():
        cells = ""
        for col in df.columns:
            val = row[col]
            cell_style = "padding:9px 12px;font-size:0.82rem;color:#1e293b;border-bottom:1px solid #f1f5f9"
            cell_content = str(val) if pd.notna(val) else "—"

            # Severity column coloring
            if severity_col and col == severity_col:
                cell_content = _severity_badge(str(val))

            # Highlight column coloring
            elif col in highlight_cols:
                cfg = highlight_cols[col]
                try:
                    num_val = float(val)
                    cell_style += ";" + _threshold_style(num_val, cfg)
                except (ValueError, TypeError):
                    pass

            # Bar column
            elif bar_col and col == bar_col:
                try:
                    num_val = float(val)
                    # Normalize to 0-100
                    if num_val <= 1:
                        num_val *= 100
                    cell_content = _progress_bar(num_val)
                except (ValueError, TypeError):
                    pass

            # Format numbers
            if isinstance(val, (int, float)) and col not in [severity_col, bar_col]:
                if pd.notna(val):
                    if abs(val) >= 1e6:
                        cell_content = f"{val/1e6:,.1f}M"
                    elif abs(val) >= 1000:
                        cell_content = f"{val:,.0f}"
                    elif isinstance(val, float):
                        cell_content = f"{val:.1f}"

            cells += f"<td style=\"{cell_style}\">{cell_content}</td>"

        row_bg = "#fff" if idx % 2 == 0 else "#fafbfc"
        body_rows += f"<tr style=\"background:{row_bg};transition:background 0.15s\" onmouseover=\"this.style.background='#eff6ff'\" onmouseout=\"this.style.background='{row_bg}'\">{cells}</tr>"

    return f"""<div style="overflow:auto;max-height:{max_height}px;border:1px solid #e2e8f0;
        border-radius:10px;background:#fff">
        <table style="width:100%;border-collapse:collapse">
            <thead><tr>{header_cells}</tr></thead>
            <tbody>{body_rows}</tbody>
        </table>
    </div>"""


def _severity_badge(level: str) -> str:
    """Render a colored severity badge."""
    level_upper = level.upper().strip()
    configs = {
        "CRITICAL": ("#dc2626", "#fef2f2"),
        "HIGH": ("#ea580c", "#fff7ed"),
        "WARNING": ("#d97706", "#fffbeb"),
        "MEDIUM": ("#d97706", "#fffbeb"),
        "LOW": ("#16a34a", "#f0fdf4"),
        "SAFE": ("#16a34a", "#f0fdf4"),
        "NORMAL": ("#6b7280", "#f9fafb"),
        "FULL": ("#16a34a", "#f0fdf4"),
        "REDUCED": ("#d97706", "#fffbeb"),
        "CLOSE": ("#dc2626", "#fef2f2"),
        "CLOSED": ("#dc2626", "#fef2f2"),
    }
    color, bg = configs.get(level_upper, ("#6b7280", "#f9fafb"))
    return f"""<span style="background:{bg};color:{color};padding:2px 10px;border-radius:6px;
        font-size:0.75rem;font-weight:700;white-space:nowrap">{level_upper}</span>"""


def _threshold_style(val: float, cfg: dict) -> str:
    """Return cell background style based on threshold config."""
    thresholds = cfg.get("thresholds", [])
    good = cfg.get("good", "low")  # "low" means lower is better

    if len(thresholds) < 2:
        return ""

    warn_t, crit_t = thresholds[0], thresholds[1]

    if good == "low":
        if val >= crit_t:
            return "background:#fef2f2;color:#dc2626;font-weight:600"
        elif val >= warn_t:
            return "background:#fffbeb;color:#d97706;font-weight:600"
        else:
            return "background:#f0fdf4;color:#16a34a"
    else:  # good == "high"
        if val <= crit_t:
            return "background:#fef2f2;color:#dc2626;font-weight:600"
        elif val <= warn_t:
            return "background:#fffbeb;color:#d97706;font-weight:600"
        else:
            return "background:#f0fdf4;color:#16a34a"


def _progress_bar(pct: float) -> str:
    """Render an inline progress bar."""
    pct = max(0, min(100, pct))
    if pct >= 80:
        color = "#16a34a"
    elif pct >= 50:
        color = "#d97706"
    else:
        color = "#dc2626"
    return f"""<div style="display:flex;align-items:center;gap:8px">
        <div style="flex:1;background:#e2e8f0;border-radius:4px;height:8px;overflow:hidden">
            <div style="width:{pct:.0f}%;background:{color};height:100%;border-radius:4px"></div>
        </div>
        <span style="font-size:0.75rem;color:#64748b;min-width:35px">{pct:.0f}%</span>
    </div>"""

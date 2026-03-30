"""
Reusable Plotly chart components for the Energy Intelligence System.
Consistent styling with Myanmar-themed color palette.
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import streamlit as st
from config.settings import OPERATING_MODES, SECTORS, CURRENCY


# ── Color Palette ──────────────────────────────────────────────────────────────
COLORS = {
    "primary": "#1976D2",
    "secondary": "#FF6F00",
    "success": "#4CAF50",
    "warning": "#FF9800",
    "danger": "#F44336",
    "info": "#2196F3",
    "grey": "#9E9E9E",
    "dark": "#263238",
    "light": "#ECEFF1",
    "diesel": "#FF6F00",
    "grid": "#2196F3",
    "solar": "#FFC107",
}

MODE_COLORS = {k: v["color"] for k, v in OPERATING_MODES.items()}


def _apply_layout(fig, title=None, height=400):
    """Apply consistent layout styling."""
    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=40, r=20, t=50, b=40),
        font=dict(family="Inter, sans-serif", size=12),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(0,0,0,0.05)")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(0,0,0,0.05)")
    return fig


# ── KPI Cards ──────────────────────────────────────────────────────────────────

def kpi_card(label: str, value: str, delta: str = None, delta_color: str = "normal"):
    """Render a Streamlit metric card."""
    st.metric(label=label, value=value, delta=delta, delta_color=delta_color)


def kpi_row(metrics: list):
    """Render a row of KPI cards.

    Args:
        metrics: list of dicts with keys: label, value, delta (optional), delta_color (optional)
    """
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            kpi_card(
                label=m["label"],
                value=m["value"],
                delta=m.get("delta"),
                delta_color=m.get("delta_color", "normal"),
            )


# ── Energy Charts ──────────────────────────────────────────────────────────────

def energy_cost_vs_sales_bar(energy_df: pd.DataFrame, sales_df: pd.DataFrame,
                              group_col: str = "store_id", title: str = None) -> go.Figure:
    """Bar chart comparing energy cost vs sales by grouping."""
    daily_sales = sales_df.groupby(["date", "store_id"])["sales_mmk"].sum().reset_index()

    merged = energy_df.merge(daily_sales, on=["date", "store_id"], how="left")
    agg = merged.groupby(group_col).agg(
        energy_cost=("total_energy_cost_mmk", "sum"),
        sales=("sales_mmk", "sum"),
    ).reset_index().sort_values("sales", ascending=False).head(20)

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Sales", x=agg[group_col], y=agg["sales"],
                         marker_color=COLORS["primary"], opacity=0.8))
    fig.add_trace(go.Bar(name="Energy Cost", x=agg[group_col], y=agg["energy_cost"],
                         marker_color=COLORS["diesel"], opacity=0.8))

    fig.update_layout(barmode="group")
    return _apply_layout(fig, title=title or "Energy Cost vs Sales")


def diesel_trend_line(prices_df: pd.DataFrame, forecast_df: pd.DataFrame = None,
                       title: str = None) -> go.Figure:
    """Line chart of diesel prices with optional forecast overlay."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=prices_df["date"], y=prices_df["diesel_price_mmk"],
        name="Actual Price", mode="lines",
        line=dict(color=COLORS["diesel"], width=2),
    ))

    if forecast_df is not None and len(forecast_df) > 0:
        fig.add_trace(go.Scatter(
            x=forecast_df["date"], y=forecast_df["predicted_price"],
            name="Forecast", mode="lines",
            line=dict(color=COLORS["danger"], width=2, dash="dash"),
        ))
        if "upper_bound" in forecast_df.columns:
            fig.add_trace(go.Scatter(
                x=forecast_df["date"], y=forecast_df["upper_bound"],
                name="Upper Bound", mode="lines",
                line=dict(width=0), showlegend=False,
            ))
            fig.add_trace(go.Scatter(
                x=forecast_df["date"], y=forecast_df["lower_bound"],
                name="Confidence Band", mode="lines",
                line=dict(width=0), fill="tonexty",
                fillcolor="rgba(244,67,54,0.15)", showlegend=True,
            ))

    return _apply_layout(fig, title=title or f"Diesel Price Trend ({CURRENCY}/liter)")


def blackout_heatmap(energy_df: pd.DataFrame, stores_df: pd.DataFrame,
                      title: str = None) -> go.Figure:
    """Heatmap of blackout hours by township and date."""
    merged = energy_df.merge(stores_df[["store_id", "township"]], on="store_id", how="left")

    pivot = merged.groupby(["township", "date"])["blackout_hours"].mean().reset_index()
    pivot_table = pivot.pivot(index="township", columns="date", values="blackout_hours")

    fig = go.Figure(data=go.Heatmap(
        z=pivot_table.values,
        x=pivot_table.columns,
        y=pivot_table.index,
        colorscale="YlOrRd",
        colorbar=dict(title="Blackout Hours"),
    ))

    return _apply_layout(fig, title=title or "Blackout Hours by Township", height=500)


def store_mode_table(decisions: pd.DataFrame) -> go.Figure:
    """Color-coded table showing store operating modes."""
    colors = [MODE_COLORS.get(m, COLORS["grey"]) for m in decisions["mode"]]

    fig = go.Figure(data=[go.Table(
        header=dict(
            values=["Store", "Sector", "Channel", "Mode", "Reason"],
            fill_color=COLORS["dark"],
            font=dict(color="white", size=12),
            align="left",
        ),
        cells=dict(
            values=[
                decisions.get("name", decisions.get("store_id", "")),
                decisions.get("sector", ""),
                decisions.get("channel", ""),
                decisions.get("mode", ""),
                decisions.get("reason", ""),
            ],
            fill_color=[
                [COLORS["light"]] * len(decisions),
                [COLORS["light"]] * len(decisions),
                [COLORS["light"]] * len(decisions),
                colors,
                [COLORS["light"]] * len(decisions),
            ],
            font=dict(size=11),
            align="left",
        ),
    )])

    return _apply_layout(fig, title="Daily Operating Plan", height=max(300, len(decisions) * 25 + 100))


def solar_vs_diesel_pie(solar_kwh: float, diesel_kwh: float, grid_kwh: float,
                         title: str = None) -> go.Figure:
    """Pie chart of energy source mix."""
    fig = go.Figure(data=[go.Pie(
        labels=["Solar", "Diesel Generator", "Grid"],
        values=[solar_kwh, diesel_kwh, grid_kwh],
        marker=dict(colors=[COLORS["solar"], COLORS["diesel"], COLORS["grid"]]),
        hole=0.4,
        textinfo="label+percent",
    )])

    return _apply_layout(fig, title=title or "Energy Source Mix", height=350)


def resilience_ranking_bar(eri_df: pd.DataFrame, stores_df: pd.DataFrame,
                            top_n: int = 20, title: str = None) -> go.Figure:
    """Horizontal bar chart ranking stores by Energy Resilience Index."""
    merged = eri_df.merge(stores_df[["store_id", "name", "sector"]], on="store_id", how="left")
    merged = merged.sort_values("eri_pct", ascending=True).tail(top_n)

    sector_colors = {s: info["color"] for s, info in SECTORS.items()}
    colors = [sector_colors.get(s, COLORS["grey"]) for s in merged["sector"]]

    fig = go.Figure(data=[go.Bar(
        x=merged["eri_pct"],
        y=merged["name"],
        orientation="h",
        marker_color=colors,
        text=merged["eri_pct"].apply(lambda x: f"{x}%"),
        textposition="outside",
    )])

    return _apply_layout(fig, title=title or "Energy Resilience Index (Top Stores)", height=max(400, top_n * 25))


def scenario_comparison(current: dict, scenario: dict, title: str = None) -> go.Figure:
    """Side-by-side bar chart comparing current vs scenario metrics."""
    categories = list(current.keys())
    current_vals = list(current.values())
    scenario_vals = list(scenario.values())

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Current", x=categories, y=current_vals,
                         marker_color=COLORS["primary"]))
    fig.add_trace(go.Bar(name="Scenario", x=categories, y=scenario_vals,
                         marker_color=COLORS["danger"]))

    fig.update_layout(barmode="group")
    return _apply_layout(fig, title=title or "Scenario Comparison")


def alert_badge(tier: int, count: int) -> str:
    """Return HTML badge for alert tier."""
    colors = {1: "#F44336", 2: "#FF9800", 3: "#2196F3"}
    labels = {1: "CRITICAL", 2: "WARNING", 3: "INFO"}
    color = colors.get(tier, "#9E9E9E")
    label = labels.get(tier, "UNKNOWN")
    return f'<span style="background-color:{color};color:white;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:bold">{label}: {count}</span>'

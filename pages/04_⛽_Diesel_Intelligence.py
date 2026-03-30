"""
Page 3: Diesel Intelligence — shadcn/ui
Price forecast, buy/hold signal, volatility, FX.
"""

import streamlit as st
import streamlit_shadcn_ui as ui
import plotly.graph_objects as go
from utils.data_loader import load_diesel_prices, load_fx_rates
from models.diesel_price_forecast import DieselPriceForecast
from utils.element_captions import get_page_captions, render_caption
from utils.page_intelligence import render_page_intelligence

st.set_page_config(page_title="Diesel Intelligence", page_icon="⛽", layout="wide")

st.markdown("""
<div style="background:linear-gradient(135deg,#7c2d12,#ea580c);color:white;padding:20px 28px;border-radius:12px;margin-bottom:20px">
    <h2 style="margin:0;color:white">Diesel Intelligence</h2>
    <p style="margin:4px 0 0;opacity:0.85">Price forecasting, procurement signals, and market analysis</p>
</div>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_and_forecast():
    prices = load_diesel_prices()
    fx = load_fx_rates()
    model = DieselPriceForecast()
    model.fit(prices)
    forecast = model.predict(7)
    vol = model.get_volatility_index()
    rec = model.get_buy_recommendation(forecast)
    return prices, fx, forecast, vol, rec

prices, fx, forecast, vol, rec = load_and_forecast()

# ── Signal Banner ──
signal = rec["signal"]
signal_bg = {"BUY NOW": "#dc2626", "BUY": "#ea580c", "HOLD": "#2563eb", "WAIT": "#16a34a"}
st.markdown(f"""
<div style="background:{signal_bg.get(signal,'#64748b')};color:white;padding:16px 24px;border-radius:10px;margin-bottom:16px;display:flex;justify-content:space-between;align-items:center">
    <div>
        <span style="font-size:1.6rem;font-weight:800">{signal}</span>
        <span style="margin-left:16px;opacity:0.9">{rec['reason']}</span>
    </div>
    <div style="text-align:right">
        <div style="font-size:0.85rem;opacity:0.8">Expected Change</div>
        <div style="font-size:1.2rem;font-weight:700">{rec['expected_change_pct']:+.1f}%</div>
    </div>
</div>
""", unsafe_allow_html=True)

render_page_intelligence("diesel", f"Current price: {vol['current_price']:,} MMK/L, Volatility: {vol['volatility_7d']:.0f} MMK, Signal: {signal}, FX rate: {int(fx['usd_mmk'].iloc[-1]):,} USD/MMK, Trend: {vol['trend']}, 7d change: {vol['price_change_7d_pct']:+.1f}%.")

# ── AI Captions ──
captions = get_page_captions("diesel", [
    {"id": "signal_banner", "type": "metric", "title": "Buy/Hold Signal", "value": f"{signal}, expected change {rec['expected_change_pct']:+.1f}%"},
    {"id": "d_price", "type": "metric", "title": "Diesel Price", "value": f"{vol['current_price']:,} MMK/L"},
    {"id": "d_fx", "type": "metric", "title": "USD/MMK Rate", "value": f"{int(fx['usd_mmk'].iloc[-1]):,}"},
    {"id": "d_7d", "type": "metric", "title": "7-Day Price Change", "value": f"{vol['price_change_7d_pct']:+.1f}%"},
    {"id": "d_30d", "type": "metric", "title": "30-Day Price Change", "value": f"{vol['price_change_30d_pct']:+.1f}%"},
    {"id": "d_vol", "type": "metric", "title": "7-Day Volatility", "value": f"{vol['volatility_7d']:.0f} MMK std dev"},
    {"id": "d_trend", "type": "metric", "title": "Price Trend", "value": vol["trend"]},
    {"id": "forecast_chart", "type": "chart", "title": "7-Day Price Forecast", "value": f"Current {vol['current_price']:,}, 7d change {vol['price_change_7d_pct']:+.1f}%, trend {vol['trend']}"},
    {"id": "history_chart", "type": "chart", "title": "Price History (180 days)", "value": f"Range {int(prices['diesel_price_mmk'].min())}-{int(prices['diesel_price_mmk'].max())} MMK/L"},
    {"id": "fx_chart", "type": "chart", "title": "Multi-currency FX Chart", "value": f"USD/MMK at {int(fx['usd_mmk'].iloc[-1]):,}"},
    {"id": "fx_corr_chart", "type": "chart", "title": "USD/MMK vs Diesel Scatter", "value": "Correlation between FX rate and diesel price"},
    {"id": "fx_table", "type": "table", "title": "14-Day FX Rates Table", "value": "5 currency pairs over 14 days"},
    {"id": "forecast_table", "type": "table", "title": "7-Day Forecast Detail", "value": f"Predicted range {int(forecast['predicted_price'].min())}-{int(forecast['predicted_price'].max())} MMK"},
], data_summary=f"Diesel {vol['current_price']:,} MMK/L, {vol['trend']} trend, 7d change {vol['price_change_7d_pct']:+.1f}%, signal {signal}, USD/MMK {int(fx['usd_mmk'].iloc[-1]):,}")
render_caption("signal_banner", captions)

# ── KPIs ──
# FX data from separate file
latest_fx = int(fx["usd_mmk"].iloc[-1])
prev_fx = int(fx["usd_mmk"].iloc[-2])
fx_7d_ago = int(fx["usd_mmk"].iloc[-7]) if len(fx) >= 7 else latest_fx
fx_change_7d = (latest_fx - fx_7d_ago) / fx_7d_ago * 100

cols = st.columns(4)
with cols[0]:
    ui.metric_card(title="Diesel Price", content=f"{vol['current_price']:,} MMK/L",
                   description="per liter", key="d_price")
    render_caption("d_price", captions)
with cols[1]:
    ui.metric_card(title="USD/MMK Rate", content=f"{latest_fx:,}",
                   description=f"{fx_change_7d:+.1f}% (7d)", key="d_fx")
    render_caption("d_fx", captions)
with cols[2]:
    ui.metric_card(title="7-Day Change", content=f"{vol['price_change_7d_pct']:+.1f}%",
                   description="diesel price", key="d_7d")
    render_caption("d_7d", captions)
with cols[3]:
    ui.metric_card(title="30-Day Change", content=f"{vol['price_change_30d_pct']:+.1f}%",
                   description="diesel price", key="d_30d")
    render_caption("d_30d", captions)
cols2 = st.columns(4)
with cols2[0]:
    ui.metric_card(title="Volatility (7d)", content=f"{vol['volatility_7d']:.0f} MMK",
                   description="std deviation", key="d_vol")
    render_caption("d_vol", captions)
with cols2[1]:
    ui.metric_card(title="Trend", content=vol["trend"],
                   description="direction", key="d_trend")
    render_caption("d_trend", captions)

st.markdown("")

# ── Forecast Chart ──
st.markdown("### 7-Day Price Forecast")

fig = go.Figure()
recent = prices.tail(60)
fig.add_trace(go.Scatter(x=recent["date"], y=recent["diesel_price_mmk"],
                         name="Actual", mode="lines", line=dict(color="#f97316", width=2)))
fig.add_trace(go.Scatter(x=forecast["date"], y=forecast["predicted_price"],
                         name="Forecast", mode="lines+markers",
                         line=dict(color="#ef4444", width=2, dash="dash"), marker=dict(size=6)))
fig.add_trace(go.Scatter(x=forecast["date"], y=forecast["upper_bound"],
                         mode="lines", line=dict(width=0), showlegend=False))
fig.add_trace(go.Scatter(x=forecast["date"], y=forecast["lower_bound"],
                         name="80% Confidence", mode="lines", line=dict(width=0),
                         fill="tonexty", fillcolor="rgba(239,68,68,0.12)"))
fig.update_layout(height=400, margin=dict(l=40, r=20, t=20, b=40),
                  plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                  legend=dict(orientation="h", y=1.05))
st.plotly_chart(fig, use_container_width=True)
render_caption("forecast_chart", captions)

# ── Action Box ──
st.markdown(f"""
<div style="background:#fffbeb;border:1px solid #fbbf24;border-radius:10px;padding:16px 20px;margin-bottom:20px">
    <strong>Recommended Action:</strong> {rec['recommended_action']}
</div>
""", unsafe_allow_html=True)

# ── Tabs: History / FX / Forecast Table ──
tab = ui.tabs(options=["Price History", "FX Rates", "FX Correlation", "Forecast Detail"], default_value="Price History", key="diesel_tabs")

if tab == "Price History":
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=prices["date"], y=prices["diesel_price_mmk"],
                             name="Diesel", mode="lines", line=dict(color="#f97316", width=1.5),
                             fill="tozeroy", fillcolor="rgba(249,115,22,0.08)"))
    fig.update_layout(height=350, margin=dict(l=40, r=20, t=20, b=40),
                      yaxis_title="MMK/L", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)
    render_caption("history_chart", captions)

elif tab == "FX Rates":
    # Multi-currency FX dashboard
    st.markdown("### Exchange Rates (MMK)")

    # FX KPI cards
    currencies = [
        ("USD/MMK", "usd_mmk", "#2563eb"),
        ("EUR/MMK", "eur_mmk", "#7c3aed"),
        ("SGD/MMK", "sgd_mmk", "#059669"),
        ("THB/MMK", "thb_mmk", "#ea580c"),
        ("CNY/MMK", "cny_mmk", "#dc2626"),
    ]
    fx_cols = st.columns(4)
    for col, (label, col_name, color) in zip(fx_cols, currencies[:4]):
        with col:
            val = fx[col_name].iloc[-1]
            prev = fx[col_name].iloc[-2]
            chg = (val - prev) / prev * 100
            fmt = f"{val:,.0f}" if val > 100 else f"{val:,.1f}"
            ui.metric_card(title=label, content=fmt, description=f"{chg:+.2f}% daily", key=f"fx_{col_name}")
    fx_cols2 = st.columns(4)
    for col, (label, col_name, color) in zip(fx_cols2, currencies[4:]):
        with col:
            val = fx[col_name].iloc[-1]
            prev = fx[col_name].iloc[-2]
            chg = (val - prev) / prev * 100
            fmt = f"{val:,.0f}" if val > 100 else f"{val:,.1f}"
            ui.metric_card(title=label, content=fmt, description=f"{chg:+.2f}% daily", key=f"fx_{col_name}")

    # All currencies chart
    fig = go.Figure()
    for label, col_name, color in currencies:
        fig.add_trace(go.Scatter(x=fx["date"], y=fx[col_name], name=label,
                                 mode="lines", line=dict(color=color, width=1.5)))
    fig.update_layout(height=400, margin=dict(l=40, r=20, t=20, b=40),
                      yaxis_title="MMK", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", y=1.05))
    st.plotly_chart(fig, use_container_width=True)
    render_caption("fx_chart", captions)

    # FX table
    fx_display = fx.tail(14).copy()
    fx_display["date"] = fx_display["date"].dt.strftime("%Y-%m-%d")
    ui.table(data=fx_display[["date", "usd_mmk", "eur_mmk", "sgd_mmk", "thb_mmk", "cny_mmk"]].rename(columns={
        "date": "Date", "usd_mmk": "USD/MMK", "eur_mmk": "EUR/MMK",
        "sgd_mmk": "SGD/MMK", "thb_mmk": "THB/MMK", "cny_mmk": "CNY/MMK"}),
        maxHeight=400, key="fx_table")
    render_caption("fx_table", captions)

elif tab == "FX Correlation":
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### USD/MMK vs Diesel Price")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=fx["usd_mmk"], y=prices["diesel_price_mmk"],
                                 mode="markers", marker=dict(color="#f97316", size=5, opacity=0.5)))
        fig.update_layout(height=350, margin=dict(l=40, r=20, t=20, b=40),
                          xaxis_title="USD/MMK", yaxis_title="Diesel (MMK/L)",
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
        render_caption("fx_corr_chart", captions)
    with col2:
        st.markdown("### USD/MMK Trend")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=fx["date"], y=fx["usd_mmk"], mode="lines",
                                 line=dict(color="#2563eb", width=1.5),
                                 fill="tozeroy", fillcolor="rgba(37,99,235,0.08)"))
        fig.update_layout(height=350, margin=dict(l=40, r=20, t=20, b=40),
                          yaxis_title="MMK per USD", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

elif tab == "Forecast Detail":
    fc = forecast.copy()
    fc["date"] = fc["date"].dt.strftime("%Y-%m-%d (%a)")
    ui.table(data=fc.rename(columns={
        "date": "Date", "predicted_price": "Predicted (MMK)",
        "lower_bound": "Lower", "upper_bound": "Upper"}),
        maxHeight=300, key="forecast_table")
    render_caption("forecast_table", captions)

st.divider()
# AI Insights merged into Page Intelligence at top


# Generate element captions for next visit
from utils.element_captions import generate_pending_captions
generate_pending_captions()

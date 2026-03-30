"""
Page 0: Business Requirements & Context
Complete requirement document explaining the why, what, and how of the Energy Intelligence System.
"""

import streamlit as st
import streamlit_shadcn_ui as ui
import pandas as pd
from utils.mermaid_helper import render_mermaid

st.set_page_config(page_title="Requirements", page_icon="📄", layout="wide")

st.markdown("""
<div style="background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 50%,#0d47a1 100%);color:white;padding:28px 32px;border-radius:14px;margin-bottom:24px">
    <h2 style="margin:0;color:white;font-size:1.8rem">Business Requirements Document</h2>
    <p style="margin:6px 0 0;opacity:0.85;font-size:1.05rem">Energy Intelligence System — BCP + AI Operating Model for Volatile Energy Markets</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1: CONTEXT & PROBLEM
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="background:#fef2f2;border-left:4px solid #dc2626;padding:16px 20px;border-radius:0 10px 10px 0;margin-bottom:20px">
    <h3 style="margin:0;color:#991b1b">1. Business Context & Problem Statement</h3>
</div>
""", unsafe_allow_html=True)

st.markdown("""
#### The Crisis

A multi-sector conglomerate operating **55+ stores across 4 business sectors** (Retail, F&B, Distribution, Property)
in Myanmar faces **severe energy disruption** driven by the Middle East war. The situation creates a triple threat:

1. **Frequent electricity blackouts** — unpredictable grid outages lasting 4-12 hours daily
2. **Volatile diesel prices** — fuel costs swinging 5-15% within days due to global oil market disruption
3. **Uncertain diesel supply** — supplier lead times increasing, periodic shortages, risk of fuel stock-outs

#### Why This Matters

Energy is no longer a utility cost line — it has become a **strategic control tower variable** that directly
impacts whether stores can operate, whether food spoils, whether the business makes or loses money on any given day.

#### The Current Problem

Without an intelligence system, the organization is:

- **Reactive** — responding to blackouts after they happen, not before
- **Blind** — no visibility into which stores are profitable under generator power vs. which are losing money
- **Fragmented** — each store/sector making isolated diesel decisions without network-level optimization
- **Exposed** — no early warning for diesel stock-outs, price spikes, or spoilage risk
""")

cols = st.columns(4)
with cols[0]:
    ui.metric_card(title="Sectors Affected", content="4", description="Retail, F&B, Distribution, Property", key="r_sectors")
with cols[1]:
    ui.metric_card(title="Stores at Risk", content="55+", description="across 25 townships", key="r_stores")
with cols[2]:
    ui.metric_card(title="Avg Daily Blackout", content="5+ hours", description="per store per day", key="r_blackout")
with cols[3]:
    ui.metric_card(title="Diesel Price Volatility", content="5-15%", description="weekly swings", key="r_volatility")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2: STRATEGIC SHIFT
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="background:#eff6ff;border-left:4px solid #2563eb;padding:16px 20px;border-radius:0 10px 10px 0;margin-bottom:20px">
    <h3 style="margin:0;color:#1e40af">2. Strategic Shift: From "Energy Cost" to "Energy Intelligence System"</h3>
</div>
""", unsafe_allow_html=True)

st.markdown("""
#### The Old Approach (Tracking)
Simply monitoring blackout hours, diesel consumption, and price fluctuations — **reporting what happened**.

#### The New Approach (Intelligence)
Build an **AI-driven Energy Control Tower** that performs 4 functions:
""")

cols = st.columns(4)
with cols[0]:
    st.markdown("""
    <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:16px;text-align:center;height:160px">
        <div style="font-size:2rem">📡</div>
        <h4 style="margin:8px 0 4px;color:#166534">1. SENSE</h4>
        <p style="font-size:0.85rem;color:#15803d">Real-time visibility into energy status across all 55+ sites</p>
    </div>
    """, unsafe_allow_html=True)
with cols[1]:
    st.markdown("""
    <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:16px;text-align:center;height:160px">
        <div style="font-size:2rem">🧠</div>
        <h4 style="margin:8px 0 4px;color:#1e40af">2. PREDICT</h4>
        <p style="font-size:0.85rem;color:#2563eb">Forecast what will happen next — prices, blackouts, stock-outs, spoilage</p>
    </div>
    """, unsafe_allow_html=True)
with cols[2]:
    st.markdown("""
    <div style="background:#fefce8;border:1px solid #fef08a;border-radius:10px;padding:16px;text-align:center;height:160px">
        <div style="font-size:2rem">⚖️</div>
        <h4 style="margin:8px 0 4px;color:#854d0e">3. DECIDE</h4>
        <p style="font-size:0.85rem;color:#a16207">Determine the best operational choice for each store every morning</p>
    </div>
    """, unsafe_allow_html=True)
with cols[3]:
    st.markdown("""
    <div style="background:#fdf2f8;border:1px solid #fbcfe8;border-radius:10px;padding:16px;text-align:center;height:160px">
        <div style="font-size:2rem">🚀</div>
        <h4 style="margin:8px 0 4px;color:#9d174d">4. ACT</h4>
        <p style="font-size:0.85rem;color:#be185d">Automate alerts and trigger actions across the organization</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3: DATA REQUIREMENTS
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="background:#f0fdf4;border-left:4px solid #16a34a;padding:16px 20px;border-radius:0 10px 10px 0;margin-bottom:20px">
    <h3 style="margin:0;color:#166534">3. Data Requirements — 4 Core Data Sources</h3>
</div>
""", unsafe_allow_html=True)

st.markdown("""
The system is built on **4 primary data streams** plus supplementary data from solar inverters and cold chain sensors:
""")

data_sources = pd.DataFrame([
    {"#": "1", "Data Source": "Electricity Blackout Hours", "Frequency": "Daily per store",
     "What It Captures": "Duration and timing of grid power outages by location/township",
     "Business Value": "Predict blackouts, plan generator usage, pre-adjust store operations"},
    {"#": "2", "Data Source": "Generator Diesel Consumption", "Frequency": "Daily per store",
     "What It Captures": "Generator runtime hours, diesel burned (liters), load profile",
     "Business Value": "Optimize consumption, detect waste, calculate true operating cost"},
    {"#": "3", "Data Source": "Diesel Availability & Inventory", "Frequency": "Daily per store",
     "What It Captures": "Tank stock levels, supplier lead times, delivery schedules",
     "Business Value": "Prevent stock-outs, enable cross-network diesel reallocation"},
    {"#": "4", "Data Source": "Diesel Daily Price", "Frequency": "Daily (market level)",
     "What It Captures": "Diesel price per liter, FX rate (USD/MMK), global oil proxy",
     "Business Value": "Forecast prices, time bulk purchases, plan cash flow"},
])
ui.table(data=data_sources, maxHeight=300, key="data_table")

st.markdown("""
**Supplementary data sources:**

| Source | Priority | Value |
|--------|----------|-------|
| **Solar inverter data** (kWh, peak hours, efficiency) | Recommended | Optimize energy mix, reduce diesel dependency, prioritize CAPEX |
| **Store sales & margin** (hourly POS data) | Recommended | Determine if running generator is profitable per store per hour |
| **Cold chain temperature logs** | Optional | Predict food spoilage during power outages |
""")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4: AI USE CASES
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="background:#fefce8;border-left:4px solid #ca8a04;padding:16px 20px;border-radius:0 10px 10px 0;margin-bottom:20px">
    <h3 style="margin:0;color:#854d0e">4. AI Use Cases — 8 Models</h3>
</div>
""", unsafe_allow_html=True)

st.markdown("The system deploys **8 AI/ML models** that work together to convert raw data into actionable decisions:")

use_cases = [
    {"Model": "M1: Diesel Price Forecast", "ML Type": "Prophet (Time-Series)",
     "Input": "Daily diesel price, FX rate, oil price",
     "Output": "7-day price forecast + buy/hold signal",
     "Business Decision": "When to buy diesel in bulk vs. wait for price drop",
     "Example Alert": "Diesel expected to increase 8% in 3 days → advance purchase recommended"},

    {"Model": "M2: Blackout Prediction", "ML Type": "XGBoost (Classification)",
     "Input": "Historical outage patterns by township, time, season",
     "Output": "Hourly blackout probability per store, risk heatmap",
     "Business Decision": "Pre-adjust operations before blackout hits",
     "Example Alert": "Tomorrow 2-6 PM: 80% blackout probability in North Dagon"},

    {"Model": "M3: Store Decision Engine", "ML Type": "Rule-Based Optimization",
     "Input": "Sales/hr, margin, diesel cost/hr, blackout forecast, solar",
     "Output": "Per-store mode: FULL / REDUCED / CRITICAL / CLOSE",
     "Business Decision": "Which stores to run full, reduce, or shut down today",
     "Example Alert": "Store B: diesel cost > margin → switch to reduced mode"},

    {"Model": "M4: Diesel Consumption Optimizer", "ML Type": "Regression + Isolation Forest",
     "Input": "Generator runtime, load profile, consumption per hour",
     "Output": "Efficiency score, waste alerts, optimal load schedule",
     "Business Decision": "Identify generators wasting fuel, schedule maintenance",
     "Example Alert": "Generator at Store B running 20% above expected consumption"},

    {"Model": "M5: Solar + Diesel Mix Optimizer", "ML Type": "Linear Programming (scipy)",
     "Input": "Solar kWh from inverters, demand profile, diesel cost",
     "Output": "Optimal energy source mix, load-shifting recommendations",
     "Business Decision": "Shift energy-intensive operations to solar peak hours",
     "Example Alert": "Shift bakery production to 10am-3pm → save 800K MMK/week"},

    {"Model": "M6: Diesel Stock-Out Risk", "ML Type": "Probabilistic Model",
     "Input": "Current stock, daily consumption rate, supplier lead times",
     "Output": "Days of coverage per site, stock-out probability",
     "Business Decision": "Reallocate diesel from surplus to deficit stores",
     "Example Alert": "Store C: 1.2 days diesel remaining → order immediately"},

    {"Model": "M7: Cold Chain Spoilage Predictor", "ML Type": "Random Forest (Classification)",
     "Input": "Outage duration, generator gaps, temperature readings",
     "Output": "Spoilage probability by product zone (Dairy/Frozen/Fresh)",
     "Business Decision": "Transfer perishable stock before spoilage occurs",
     "Example Alert": "Store C: 3-hour generator gap → 60% dairy spoilage risk"},

    {"Model": "M8: Holdings Aggregator", "ML Type": "Aggregation + Scenario Engine",
     "Input": "All sector data rolled up to group level",
     "Output": "Group KPIs, EBITDA impact, scenario simulation",
     "Business Decision": "Strategic resource allocation, solar CAPEX prioritization",
     "Example Alert": "What if diesel +15%? → 12 stores need to close, EBITDA -18%"},
]

for uc in use_cases:
    with st.expander(f"**{uc['Model']}** — {uc['ML Type']}"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Input:** {uc['Input']}")
            st.markdown(f"**Output:** {uc['Output']}")
            st.markdown(f"**ML Type:** {uc['ML Type']}")
        with col2:
            st.markdown(f"**Business Decision:** {uc['Business Decision']}")
            st.info(f"Example: *{uc['Example Alert']}*")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5: ARCHITECTURE
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="background:#f5f3ff;border-left:4px solid #7c3aed;padding:16px 20px;border-radius:0 10px 10px 0;margin-bottom:20px">
    <h3 style="margin:0;color:#5b21b6">5. System Architecture — Federated Energy Intelligence</h3>
</div>
""", unsafe_allow_html=True)

st.markdown("The system uses a **two-layer federated model** — sector-level operations feed into Holdings-level strategy:")

# Architecture — Mermaid flowchart
render_mermaid("""
graph LR
    subgraph SECTOR["Sector Level (Daily, Operational)"]
        R["🏪 Retail<br/>25 stores<br/>Hyper | Super | Conv."]
        F["🍽️ F&B<br/>15 stores<br/>Bakery | Rest. | Bev."]
        D["📦 Distribution<br/>8 stores<br/>WH | Cold Chain | Logistics"]
        P["🏢 Property<br/>7 stores<br/>Mall | Office"]
    end

    subgraph HOLDINGS["Holdings Control Tower (Weekly, Strategic)"]
        CMD["🏛️ Group Energy<br/>Command Center"]
        INT["Cross-sector comparison<br/>EBITDA impact<br/>Diesel reallocation<br/>CAPEX priority<br/>Scenario simulation"]
        DEC["Override closures<br/>Allocate diesel<br/>Approve solar CAPEX<br/>Set shutdown policies"]
        CMD --> INT
        CMD --> DEC
    end

    R --> CMD
    F --> CMD
    D --> CMD
    P --> CMD

    style SECTOR fill:#eff6ff,stroke:#3b82f6,stroke-width:2px
    style HOLDINGS fill:#f0fdf4,stroke:#16a34a,stroke-width:2px
    style CMD fill:#0f172a,color:#fff,stroke:#1e3a5f
    style R fill:#dbeafe,stroke:#2563eb
    style F fill:#ffedd5,stroke:#ea580c
    style D fill:#dcfce7,stroke:#16a34a
    style P fill:#ede9fe,stroke:#7c3aed
""", height=420)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6: DECISION FRAMEWORK
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="background:#fff7ed;border-left:4px solid #ea580c;padding:16px 20px;border-radius:0 10px 10px 0;margin-bottom:20px">
    <h3 style="margin:0;color:#c2410c">6. Decision Framework — 3-Tier Alert System</h3>
</div>
""", unsafe_allow_html=True)

st.markdown("The system generates **automated decisions and alerts** at 3 severity levels:")

tier_data = pd.DataFrame([
    {"Tier": "TIER 1 — CRITICAL", "Action": "Act NOW", "Response Time": "Immediate",
     "Examples": "Diesel stock < 1 day | Spoilage risk > 60% | Generator failure | Store must close"},
    {"Tier": "TIER 2 — WARNING", "Action": "Act TODAY", "Response Time": "Within hours",
     "Examples": "Diesel price spike +8% in 3 days | 80% blackout probability tomorrow | Generator 25% above normal consumption"},
    {"Tier": "TIER 3 — INFO", "Action": "Optimize this week", "Response Time": "1-3 days",
     "Examples": "Shift bakery to solar peak hours | Solar offset improved 12% | Consider solar install at site X"},
])
ui.table(data=tier_data, maxHeight=200, key="tier_table")

st.markdown("""
#### Daily Operating Rhythm

| Time | Activity | Owner |
|------|----------|-------|
| **6:00 AM** | AI generates Daily Operating Plan (mode per store) | System |
| **6:30 AM** | Sector managers review plan + critical alerts | Sector leads |
| **7:00 AM** | Stores execute: FULL / REDUCED / CRITICAL / CLOSE | Store managers |
| **Throughout day** | Real-time alerts fire as conditions change | System → All |
| **6:00 PM** | Evening review: actual vs planned, costs, incidents | Sector leads |
| **Weekly** | Holdings reviews: EBITDA impact, strategic decisions | C-Suite |
""")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7: SOLAR INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="background:#fefce8;border-left:4px solid #eab308;padding:16px 20px;border-radius:0 10px 10px 0;margin-bottom:20px">
    <h3 style="margin:0;color:#854d0e">7. Solar Integration Requirement</h3>
</div>
""", unsafe_allow_html=True)

st.markdown("""
Some sites already have solar panels with full inverter data. Solar is integrated as the **priority energy source**
with the lowest marginal cost, transforming the energy equation:
""")

# Energy balance equation
st.markdown("""
<div style="background:linear-gradient(135deg,#78350f,#d97706);color:white;border-radius:12px;padding:20px 24px;margin:12px 0;text-align:center">
    <div style="font-size:0.85rem;opacity:0.8;margin-bottom:6px">Site Energy Balance (per day)</div>
    <div style="font-size:1.3rem;font-weight:700">
        Total Demand = <span style="background:#16a34a;padding:4px 12px;border-radius:6px">Solar</span>
        + <span style="background:#2563eb;padding:4px 12px;border-radius:6px">Grid</span>
        + <span style="background:#dc2626;padding:4px 12px;border-radius:6px">Diesel Generator</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Cost per kWh cards
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div style="background:#f0fdf4;border:2px solid #86efac;border-radius:10px;padding:16px;text-align:center">
        <div style="font-size:1.5rem">☀️</div>
        <div style="font-weight:700;color:#166534;font-size:1.1rem">Solar</div>
        <div style="font-size:1.4rem;font-weight:800;color:#16a34a">~0 MMK/kWh</div>
        <div style="font-size:0.8rem;color:#666;margin-top:4px">After CAPEX recovery</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div style="background:#eff6ff;border:2px solid #93c5fd;border-radius:10px;padding:16px;text-align:center">
        <div style="font-size:1.5rem">🔌</div>
        <div style="font-weight:700;color:#1e40af;font-size:1.1rem">Grid</div>
        <div style="font-size:1.4rem;font-weight:800;color:#2563eb">~50 MMK/kWh</div>
        <div style="font-size:0.8rem;color:#666;margin-top:4px">Fixed tariff</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div style="background:#fef2f2;border:2px solid #fca5a5;border-radius:10px;padding:16px;text-align:center">
        <div style="font-size:1.5rem">⛽</div>
        <div style="font-weight:700;color:#991b1b;font-size:1.1rem">Diesel Generator</div>
        <div style="font-size:1.4rem;font-weight:800;color:#dc2626">150-300 MMK/kWh</div>
        <div style="font-size:0.8rem;color:#666;margin-top:4px">Highest &amp; most volatile</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("")

# Solar use cases
solar_cases = [
    ("🔄", "Load-Shifting", "Move energy-intensive operations (bakery, pre-cooling) to solar peak hours (10am-3pm)", "#16a34a"),
    ("⛽", "Diesel Avoidance", "Track liters of diesel replaced by solar daily — direct cost saving", "#ea580c"),
    ("📊", "CAPEX Prioritization", "Rank non-solar stores by payback period for investment decisions", "#2563eb"),
    ("🔧", "Fault Detection", "Alert when solar output drops below expected — panel cleaning, inverter issue", "#7c3aed"),
]
cols = st.columns(4)
for col, (icon, title, desc, color) in zip(cols, solar_cases):
    with col:
        st.markdown(f"""
        <div style="border-top:3px solid {color};background:#f8fafc;border-radius:0 0 10px 10px;padding:14px;height:140px">
            <div style="font-size:1.3rem">{icon}</div>
            <div style="font-weight:700;color:{color};margin:4px 0;font-size:0.9rem">{title}</div>
            <div style="font-size:0.8rem;color:#64748b">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8: STORE PROFITABILITY UNDER CONSTRAINT
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="background:#fdf2f8;border-left:4px solid #ec4899;padding:16px 20px;border-radius:0 10px 10px 0;margin-bottom:20px">
    <h3 style="margin:0;color:#9d174d">8. Core Use Case: Store Profitability Under Energy Constraint</h3>
</div>
""", unsafe_allow_html=True)

st.markdown("This is the **most critical AI use case**. The system calculates **Profit per Operating Hour** under different energy scenarios:")

# Scenario cards
scenarios = [
    ("🔌 Grid ON", "Grid electricity", "Low cost, stable", "FULL operation", "#22c55e", "#f0fdf4"),
    ("⛽ Generator ON", "Diesel", "High cost, variable", "Run if margin > cost", "#ea580c", "#fff7ed"),
    ("☀️ Solar Peak", "Solar panels", "Near zero cost", "FULL, maximize load", "#eab308", "#fefce8"),
    ("⚫ No Power", "None available", "No cost, no revenue", "CLOSE or CRITICAL", "#64748b", "#f8fafc"),
]
cols = st.columns(4)
for col, (title, source, cost, decision, color, bg) in zip(cols, scenarios):
    with col:
        st.markdown(f"""
        <div style="background:{bg};border:1px solid {color}30;border-top:3px solid {color};border-radius:0 0 10px 10px;padding:14px;text-align:center;height:150px">
            <div style="font-weight:700;color:{color};font-size:0.95rem">{title}</div>
            <div style="font-size:0.8rem;color:#666;margin:6px 0">{source}<br/>{cost}</div>
            <div style="background:{color};color:white;padding:4px 10px;border-radius:6px;font-size:0.8rem;font-weight:600;margin-top:8px;display:inline-block">{decision}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("")

# Decision flow — Mermaid flowchart
st.markdown("**Decision Logic Flow — For each store, every morning:**")

render_mermaid("""
flowchart TD
    START["🏪 For Each Store<br/>Every Morning"] --> M2["Get Blackout Probability<br/>from M2 Model"]
    M2 --> SOLAR{"Has Solar?<br/>Peak Hours?"}

    SOLAR -->|"YES"| FULL_SOLAR["☀️ FULL MODE<br/>Solar Priority"]
    SOLAR -->|"NO"| COMPARE{"Compare:<br/>Diesel Cost/hr<br/>vs Margin/hr"}

    COMPARE -->|"Margin > Diesel Cost"| STOCK_HIGH{"Diesel Stock<br/>Level?"}
    COMPARE -->|"Margin < Diesel Cost"| STOCK_LOW{"Diesel Stock<br/>Level?"}

    STOCK_HIGH -->|"> 2 days"| FULL["✅ FULL<br/>All systems on"]
    STOCK_HIGH -->|"< 2 days"| REDUCED1["🟡 REDUCED<br/>Essential only"]

    STOCK_LOW -->|"> 1 day"| REDUCED2["🟡 REDUCED<br/>Essential only"]
    STOCK_LOW -->|"< 1 day"| CLOSE["🔴 CLOSE<br/>Shutdown"]

    style START fill:#ec4899,color:#fff,stroke:#be185d
    style M2 fill:#ede9fe,stroke:#7c3aed
    style SOLAR fill:#fefce8,stroke:#ca8a04
    style FULL_SOLAR fill:#22c55e,color:#fff,stroke:#16a34a
    style COMPARE fill:#fff7ed,stroke:#ea580c
    style STOCK_HIGH fill:#f0fdf4,stroke:#22c55e
    style STOCK_LOW fill:#fef2f2,stroke:#ef4444
    style FULL fill:#22c55e,color:#fff,stroke:#16a34a
    style REDUCED1 fill:#f97316,color:#fff,stroke:#ea580c
    style REDUCED2 fill:#f97316,color:#fff,stroke:#ea580c
    style CLOSE fill:#64748b,color:#fff,stroke:#475569
""", height=550)

st.markdown("")

# Example output as styled cards
st.markdown("**Example Daily Operating Plan output:**")
examples = [
    ("Hypermarket Hlaing", "FULL", "#22c55e", "Solar available, profitable on generator"),
    ("Super Tamwe", "REDUCED", "#f97316", "Diesel cost exceeds margin, cut kitchen/AC"),
    ("Conv. Dawbon", "CLOSE", "#64748b", "Diesel under 1 day, negative profit on generator"),
    ("Mall Central", "FULL", "#22c55e", "Strategic location override (Holdings decision)"),
]
for name, mode, color, reason in examples:
    st.markdown(f"""
    <div style="display:flex;align-items:center;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:10px 16px;margin:6px 0">
        <div style="flex:2;font-weight:600;color:#1e293b">{name}</div>
        <div style="flex:1"><span style="background:{color};color:white;padding:4px 14px;border-radius:6px;font-weight:700;font-size:0.85rem">{mode}</span></div>
        <div style="flex:3;font-size:0.85rem;color:#64748b">{reason}</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 9: CHANNEL-LEVEL STRATEGY
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="background:#ecfdf5;border-left:4px solid #059669;padding:16px 20px;border-radius:0 10px 10px 0;margin-bottom:20px">
    <h3 style="margin:0;color:#065f46">9. Channel-Level Strategy</h3>
</div>
""", unsafe_allow_html=True)

st.markdown("""
Each channel has different energy sensitivity and operational flexibility:

#### Retail Channels
| Channel | Strategy | Flexibility |
|---------|----------|------------|
| Hypermarket | Always operate (anchor store, brand impact) | Low — must stay open |
| Supermarket | Selective optimization (reduce non-essential) | Medium |
| Convenience | Highly flexible (close/open fast, low fixed cost) | High — can close quickly |

#### F&B Channels
| Channel | Strategy | Energy Priority |
|---------|----------|----------------|
| Bakery | Shift production timing to solar peak hours | Ovens during solar, packaging anytime |
| Restaurant | Reduce menu items / operating hours during blackout | Kitchen is highest energy user |
| Beverage Kiosk | Shutdown during peak diesel cost | Very low margin vs energy cost |

#### Distribution Channels
| Channel | Strategy | Critical Need |
|---------|----------|--------------|
| Warehouse | Can tolerate short blackouts (no refrigeration) | Lighting + systems |
| Cold Chain | **Highest priority** — product value at risk | Refrigeration must run 24/7 |
| Logistics | Route optimization around blackout timing | Charging, loading equipment |

#### Property Channels
| Channel | Strategy | Consideration |
|---------|----------|--------------|
| Mall | Run generator for tenant commitments | Revenue from tenants depends on power |
| Office | Reduce to essential floors/zones | Can partially shut down |
""")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 10: ENABLERS
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="background:#f8fafc;border-left:4px solid #475569;padding:16px 20px;border-radius:0 10px 10px 0;margin-bottom:20px">
    <h3 style="margin:0;color:#1e293b">10. Implementation Enablers</h3>
</div>
""", unsafe_allow_html=True)

tab = ui.tabs(options=["Data Enablers", "System Enablers", "People & Governance"], default_value="Data Enablers", key="enabler_tabs")

if tab == "Data Enablers":
    st.markdown("""
    **Principle: "Perfect data is not required. Structured, consistent data is."**

    #### Minimum Viable Data (Start Immediately)
    - Daily blackout hours per store (manual log)
    - Generator runtime + diesel consumption (meter reading)
    - Diesel purchase price (supplier quote)
    - Store sales (POS export)

    #### Data Collection Phases
    | Phase | Method | Effort |
    |-------|--------|--------|
    | Phase 1 (Week 1) | Microsoft Forms / Google Forms, daily submission | 5 min/store/day |
    | Phase 2 (Month 1) | Integrate with POS (sales), Finance (diesel) | IT support needed |
    | Phase 3 (Month 3+) | IoT sensors on generators, automated fuel tracking | CAPEX investment |

    #### Common Failure to Avoid
    - Waiting for "perfect system" before starting
    - Over-complicating data structure
    - **Start simple, standardize early**
    """)

elif tab == "System Enablers":
    st.markdown("""
    **Principle: "System should drive decisions, not just display data"**

    #### Current Stack (build on top, not new system)
    - SAP (finance / procurement)
    - Microsoft 365 (Power BI, Excel, SharePoint)
    - Existing data platform

    #### Required Components
    | Layer | Phase 1 | Phase 2 | Phase 3 |
    |-------|---------|---------|---------|
    | Data | CSV/Excel files | Central database | Real-time feeds |
    | Analytics | This Streamlit app | + Power BI | + Advanced ML |
    | Alerts | Dashboard alerts | + Viber/WhatsApp | + Automated triggers |
    | AI | Rule-based + simple ML | Trained models | Auto-retraining |

    #### Common Failure to Avoid
    - Building dashboards without decision triggers
    - Every dashboard must answer: **"What action should I take today?"**
    """)

elif tab == "People & Governance":
    st.markdown("""
    **Principle: "This is an operating model change, not a reporting exercise"**

    #### New Roles Required
    | Role | Scope | Profile |
    |------|-------|---------|
    | Sector Energy Champion (x4) | Data accuracy, daily decision execution | Ops/Finance hybrid |
    | Group Energy Control Lead (x1) | Cross-sector optimization, dashboard oversight | Senior leadership |
    | Data/Analytics Support (x2) | Build models, maintain dashboards | Analyst |

    #### Decision Rights
    | Decision | Owner |
    |----------|-------|
    | Store operating mode (daily) | **Sector** |
    | Diesel allocation across network | **Holdings** |
    | Emergency override / strategic location | **Holdings** |
    | Solar CAPEX approval | **Holdings** |
    | Generator purchase / replacement | **Holdings** |

    #### Governance Rhythm
    - **Daily 6:30 AM** — Review AI-generated operating plan
    - **Weekly** — Holdings reviews energy cost, risk, performance
    - **Monthly** — Strategic decisions: CAPEX, network optimization
    """)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 11: KPIs
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="background:#eef2ff;border-left:4px solid #4f46e5;padding:16px 20px;border-radius:0 10px 10px 0;margin-bottom:20px">
    <h3 style="margin:0;color:#3730a3">11. Key Performance Indicators</h3>
</div>
""", unsafe_allow_html=True)

kpi_data = pd.DataFrame([
    {"KPI": "Energy Cost % of Sales", "Level": "Store / Sector / Group", "Target": "< 5%", "Why": "Core efficiency metric"},
    {"KPI": "Diesel Cost per Store per Day", "Level": "Store", "Target": "Minimize", "Why": "Direct cost control"},
    {"KPI": "EBITDA Impact from Disruption", "Level": "Sector / Group", "Target": "Minimize", "Why": "Profit lost to blackouts"},
    {"KPI": "Energy Resilience Index (ERI)", "Level": "Store", "Target": "> 80%", "Why": "% of days profitable despite disruption"},
    {"KPI": "Solar Coverage %", "Level": "Store", "Target": "> 40%", "Why": "Reduce diesel dependency"},
    {"KPI": "Diesel Dependency Ratio", "Level": "Sector / Group", "Target": "< 50%", "Why": "Strategic risk indicator"},
    {"KPI": "Days of Diesel Coverage", "Level": "Store", "Target": "> 5 days", "Why": "Supply chain buffer"},
    {"KPI": "Generator Efficiency Score", "Level": "Store", "Target": "> 0%", "Why": "Detect waste and maintenance needs"},
])
ui.table(data=kpi_data, maxHeight=350, key="kpi_table")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 12: IMPLEMENTATION ROADMAP
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="background:#f0fdf4;border-left:4px solid #22c55e;padding:16px 20px;border-radius:0 10px 10px 0;margin-bottom:20px">
    <h3 style="margin:0;color:#166534">12. Implementation Roadmap</h3>
</div>
""", unsafe_allow_html=True)

st.markdown("""
| Phase | Timeline | Deliverables | Outcome |
|-------|----------|-------------|---------|
| **Phase 1** | Days 1-2 | Project setup, sample data generator, data utilities | Foundation ready, demo-able |
| **Phase 2** | Days 3-5 | All 8 AI models built and tested | Intelligence engine working |
| **Phase 3** | Days 6-8 | 8 dashboard pages + main app | Full UI operational |
| **Phase 4** | Days 9-10 | Alert engine, integration testing, deployment | Production-ready system |
| **Phase 5** | Week 2-4 | Upload real data, train models, validate | System calibrated to reality |
| **Phase 6** | Month 2+ | Add IoT, expand solar, advanced ML | Full automation |
""")

st.markdown("""
#### Strategic Insight

In volatile environments, organizations evolve into 3 types:

| Type | Behavior | Outcome |
|------|----------|---------|
| **Reactive** | Track diesel, react to blackouts | Survive, barely |
| **Managed** | Plan usage, control cost | Stable, not optimal |
| **Intelligent** (your target) | Predict, optimize, allocate dynamically | **Competitive advantage** |

**The companies that win treat energy as a controllable P&L lever, not just a cost.**
They shift from "keep all stores open" to "operate selectively for profit."
They centralize decisions via a control tower, not leave to individual store managers.
""")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 13: DATA STORAGE
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="background:#1e293b;border-left:4px solid #3b82f6;padding:16px 20px;border-radius:0 10px 10px 0;margin-bottom:20px">
    <h3 style="margin:0;color:#93c5fd">13. Where Data is Stored</h3>
</div>
""", unsafe_allow_html=True)

st.markdown("All data lives inside the project folder. Nothing is sent to the cloud — everything runs locally.")

render_mermaid("""
flowchart TD
    subgraph PROJECT["📁 Energy Command Agent/"]
        subgraph DATA["📂 data/"]
            SAMPLE["📂 sample/<br/>Pre-generated synthetic CSVs<br/>7 data files"]
            REAL["📂 real/<br/>Your uploaded real CSVs<br/>Uploaded via Data Upload page"]
            GENERATORS["📂 generators/<br/>synthetic_data.py<br/>Creates sample data"]
            TRAINLOG["📄 training_log.json<br/>ML training history & logs"]
        end

        subgraph MODELS["📂 models/"]
            M1["diesel_price_forecast.py"]
            M2["blackout_prediction.py"]
            M3["store_decision_engine.py"]
            M4["diesel_optimizer.py"]
            M5["solar_optimizer.py"]
            M6["stockout_alert.py"]
            M7["spoilage_predictor.py"]
            M8["holdings_aggregator.py"]
        end

        subgraph CONFIG["📂 config/"]
            SETTINGS["settings.py<br/>DATA_SOURCE = sample or real<br/>Thresholds, store defs"]
        end

        APP["📄 app.py<br/>Main Streamlit app"]
    end

    SETTINGS -->|"tells system<br/>which folder"| SAMPLE
    SETTINGS -->|"or"| REAL
    SAMPLE --> MODELS
    REAL --> MODELS
    MODELS --> APP

    style PROJECT fill:#f8fafc,stroke:#334155
    style DATA fill:#eff6ff,stroke:#3b82f6
    style MODELS fill:#f0fdf4,stroke:#16a34a
    style CONFIG fill:#fefce8,stroke:#ca8a04
    style SAMPLE fill:#dbeafe,stroke:#2563eb
    style REAL fill:#dcfce7,stroke:#16a34a
    style TRAINLOG fill:#fef3c7,stroke:#d97706
    style APP fill:#ede9fe,stroke:#7c3aed
""", height=550)

# Data files table
st.markdown("### Data Files Detail")

data_files = pd.DataFrame([
    {"File": "stores.csv", "Location": "data/sample/ or data/real/", "Size": "~4 KB", "Content": "55 store records — sector, channel, township, solar, generator"},
    {"File": "daily_energy.csv", "Location": "data/sample/ or data/real/", "Size": "~565 KB", "Content": "9,900 rows — blackout hours, diesel, solar per store per day"},
    {"File": "diesel_prices.csv", "Location": "data/sample/ or data/real/", "Size": "~6 KB", "Content": "180 rows — daily diesel price, FX, oil price"},
    {"File": "fx_rates.csv", "Location": "data/sample/ or data/real/", "Size": "~8 KB", "Content": "180 rows — USD, EUR, SGD, THB, CNY to MMK daily"},
    {"File": "diesel_inventory.csv", "Location": "data/sample/ or data/real/", "Size": "~389 KB", "Content": "9,900 rows — stock levels, purchases, lead times"},
    {"File": "store_sales.csv", "Location": "data/sample/ or data/real/", "Size": "~6 MB", "Content": "158,400 rows — hourly sales and margin per store"},
    {"File": "solar_generation.csv", "Location": "data/sample/ or data/real/", "Size": "~875 KB", "Content": "24,300 rows — hourly solar output for 15 sites"},
    {"File": "temperature_logs.csv", "Location": "data/sample/ or data/real/", "Size": "~3.2 MB", "Content": "69,120 rows — cold chain temp readings"},
    {"File": "training_log.json", "Location": "data/", "Size": "Variable", "Content": "ML training run history, logs, alert counts"},
])
ui.table(data=data_files, maxHeight=350, key="storage_table")

st.markdown("""
**Key points:**
- **Sample data** = synthetic data generated by `synthetic_data.py` — for demo and testing
- **Real data** = your uploaded CSVs — switch via the toggle on the Data Upload page
- **Training logs** = persist across browser refreshes — safe to close and come back
- **No cloud/database** = everything is local CSV files — easy to backup, export, or migrate
- **Models train in-memory** = no saved model files, retrain fresh each time from data (fast, always up-to-date)
""")

st.divider()

st.markdown("""
<div style="background:#0f172a;color:white;padding:20px 24px;border-radius:12px;text-align:center">
    <p style="font-size:1.1rem;margin:0">This system transforms energy disruption from a <strong>survival challenge</strong> into a <strong>strategic advantage</strong>.</p>
    <p style="font-size:0.9rem;opacity:0.7;margin-top:8px">Energy Intelligence System — Built for volatile markets</p>
</div>
""", unsafe_allow_html=True)

# Energy Intelligence System (EIS) - Energy Command Agent

## Project Overview

An AI-driven Energy Control Tower + Business Continuity Planning (BCP) system for a Myanmar-based conglomerate operating across Retail, F&B, Distribution, and Property sectors. The system converts raw energy data (blackout hours, diesel consumption, diesel prices, FX rates, solar generation) into daily operational decisions, automated alerts, strategic intelligence, and continuity planning across 55+ stores.

**Context:** Middle East war has caused severe energy disruption — frequent blackouts, volatile diesel prices, uncertain fuel supply. This system turns energy chaos into a competitive advantage.

## Tech Stack

- **Backend/Models:** Python 3.11+
- **Dashboard:** Streamlit (multi-page app) + streamlit-shadcn-ui
- **UI Components:** streamlit-shadcn-ui (metric cards, tabs, tables, badges, buttons)
- **Smart Tables:** Custom HTML tables with severity badges, conditional formatting, hover effects (`utils/smart_table.py`)
- **ML:** Prophet (time-series), XGBoost (classification), scikit-learn, scipy
- **LLM:** OpenRouter (GPT-5.4-mini primary, Claude Haiku 4.5 + Claude 3.5 Haiku fallback)
- **Agentic AI:** Multi-agent system via OpenRouter tool-calling (GPT-5.4-mini + Claude Haiku 4.5)
- **AI Insights:** Per-page intelligence (Descriptive/Predictive/Prescriptive/Recommendations) + per-element captions, DB-persisted
- **Charts:** Plotly (bar, line, scatter, heatmap, waterfall, radar, polar) + Mermaid (flowcharts with zoom/pan)
- **Database:** SQLite (eis.db — training logs, chat, scenarios, BCP incidents, drills, AI cache)
- **Data:** Pandas, NumPy, CSV files

## Architecture

```
Data Sources → CSV Files → 9 AI Models → 12 Dashboard Pages
                  ↓                           ↓
              SQLite DB          ←→      LLM (OpenRouter)
    (logs, chat, scenarios,          (insights, chat, summaries)
     BCP incidents, drills,               ↓
     AI intelligence cache)        Agentic Layer (agents/)
                                   ├── Commander Agent (orchestrator)
                                   ├── Chat Agent (tool-calling Q&A)
                                   ├── Briefing Agent (autonomous briefing)
                                   └── 4 Specialists (diesel, ops, solar, risk)
```

**Federated Model:**
- Sector Level (Daily, Operational): Retail, F&B, Distribution, Property
- Holdings Level (Weekly, Strategic): Group Energy Command Center
- BCP Level (Continuous): Business Continuity Planning across all stores

---

## 12 Dashboard Pages

| # | Page | Icon | Purpose |
|---|------|------|---------|
| 1 | AI Insights Hub | 🧠 | Consolidated AI insights + LLM chat + Agent Briefing tab |
| 2 | Sector Dashboard | 🏪 | Drill: Sector → Channel → Store (sector-specific AI intelligence) |
| 3 | Holdings Control Tower | 🏛️ | Group KPIs, ERI ranking, sector comparison |
| 4 | Diesel Intelligence | ⛽ | Price forecast, buy/hold signal, FX rates |
| 5 | Blackout Monitor | 🔌 | Township heatmap, probability predictions |
| 6 | Store Decisions | 📋 | Daily Operating Plan: FULL/REDUCED/CRITICAL/CLOSE |
| 7 | Solar Performance | ☀️ | Generation, diesel offset, CAPEX priority |
| 8 | Alerts Center | 🚨 | Tier 1/2/3 alerts from all models |
| 9 | Scenario Simulator | 🔮 | Templates, sensitivity, store drill-down, break-even, waterfall, timeline, radar |
| 10 | Data Upload | 📤 | Upload CSVs, train models, switch data source |
| 11 | Requirements | 📄 | Business requirements document |
| 12 | **BCP Dashboard** | 🛡️ | **BCP scores, contingency playbooks, RTO, asset register, incidents, drills** |

---

## 9 AI Models

| # | Model | File | ML Type | Output |
|---|-------|------|---------|--------|
| M1 | Diesel Price Forecast | `models/diesel_price_forecast.py` | Prophet / ARIMA | 7-day forecast + buy/hold signal |
| M2 | Blackout Prediction | `models/blackout_prediction.py` | XGBoost / GBM | Hourly probability per store |
| M3 | Store Decision Engine | `models/store_decision_engine.py` | Rule-based optimization | FULL/REDUCED/CRITICAL/CLOSE |
| M4 | Diesel Optimizer | `models/diesel_optimizer.py` | Regression + Isolation Forest | Efficiency score + waste alerts |
| M5 | Solar Optimizer | `models/solar_optimizer.py` | Linear Programming | Optimal energy mix + load shifting |
| M6 | Stock-Out Alert | `models/stockout_alert.py` | Probabilistic | Days of coverage + reallocation |
| M7 | Spoilage Predictor | `models/spoilage_predictor.py` | Random Forest | Risk score per cold chain zone |
| M8 | Holdings Aggregator | `models/holdings_aggregator.py` | Aggregation + Simulation | Group KPIs + what-if scenarios |
| **M9** | **BCP Engine** | **`models/bcp_engine.py`** | **Weighted scoring + rule-based** | **BCP scores, playbooks, RTO, asset register** |

---

## BCP System (`models/bcp_engine.py` + `pages/12_🛡️_BCP_Dashboard.py`)

### BCP Score Formula (0-100, weighted composite)

| Component | Weight | What It Measures | Scoring |
|-----------|--------|-----------------|---------|
| Power Backup | 25% | Generator kW vs channel average | 150% of avg = 100, 100% = 67 |
| Fuel Reserve | 25% | Days of diesel coverage | 7+ days = 100, <1 day = 0 |
| Solar Resilience | 15% | Has solar + generation level | Solar + high output = 100 |
| Cold Chain Risk | 15% | Generator covers blackout hours? | Full coverage = 100, 4h+ gap = 0 |
| Operational Resilience | 20% | Avg blackout survivability | ≤2h avg = 100, >10h = 0 |

### BCP Grades

| Grade | Score | Status | Action Required |
|-------|-------|--------|----------------|
| A | 80-100 | RESILIENT | Maintain current posture |
| B | 60-79 | ADEQUATE | Minor improvements needed |
| C | 40-59 | AT RISK | Significant gaps to address |
| D | 20-39 | VULNERABLE | Urgent remediation required |
| F | 0-19 | CRITICAL | Immediate intervention needed |

### 6 BCP Dashboard Tabs

| Tab | Features |
|-----|----------|
| **BCP Scores** | Bar chart (all stores, color by grade), radar chart (weakest 5 stores breakdown), full smart table |
| **Contingency Playbook** | 4 threat levels (4h/8h/12h/24h+) with actions, cold chain protocol, staffing, procurement |
| **RTO Analysis** | Recovery Time Objective per store, bar chart, summary cards, target benchmarking |
| **Asset Register** | Generators, solar panels, cold chain units, fuel tanks per store |
| **Incident Log** | Log blackout incidents (type, duration, response time, loss, lessons). Stats tracking. |
| **Drill Scheduler** | Schedule BCP drills, mark complete with readiness score, track completion rate |

### BCP Database Tables

| Table | Purpose |
|-------|---------|
| `bcp_incidents` | Incident log: store, type, duration, response time, loss, actions, lessons |
| `bcp_drills` | Drill schedule: store, type, date, status, readiness score |

---

## Scenario Simulator (Advanced — 7 Tabs)

| Tab | Feature |
|-----|---------|
| **Comparison** | Current vs Scenario grouped bars + store mode distribution |
| **Waterfall** | Cost breakdown: Baseline → +Diesel → +Sales Loss → -Solar → Total |
| **Sensitivity** | Which parameter (diesel/blackout/FX/solar) hits EBITDA hardest |
| **Store Drill-Down** | Which stores switch to CLOSE/CRITICAL, filterable by mode |
| **Break-Even** | At what diesel % do 1/5/10/20 stores close? Threshold chart |
| **Timeline** | 90-day EBITDA projection — current vs scenario trajectory |
| **Saved Scenarios** | Smart table + radar chart (up to 4 scenarios) + EBITDA comparison |

**Pre-built Templates:** Worst Case, War Escalation, Grid Recovery, Solar Push, Moderate Stress, Best Case

---

## AI Intelligence System

### Page Intelligence (`utils/page_intelligence.py`)

Every page gets an AI-generated briefing at the top with 4 analysis types:
- **📊 Descriptive** — What happened (comparisons vs last week)
- **🔮 Predictive** — What will likely happen next
- **🎯 Prescriptive** — What to do RIGHT NOW
- **💡 Recommendations** — Strategic 7-30 day recommendations

Collapsible by default. Severity-colored (CRITICAL/ATTENTION/STATUS OK). Action bar at bottom.

### Element Captions (`utils/element_captions.py`)

Every chart, table, and metric card gets an AI annotation. Severity-colored (red/orange/blue).
- Non-blocking: generates in background, appears on next page load
- DB-persisted: only regenerates when data changes (not on refresh)

### Smart Tables (`utils/smart_table.py`)

Enhanced HTML tables with:
- Severity badges (CRITICAL/HIGH/MEDIUM/LOW/FULL/REDUCED/CLOSE colored pills)
- Conditional cell coloring based on thresholds
- Progress bars for percentage columns
- Hover effects, striped rows, sticky headers, rounded corners
- Auto number formatting (M/K suffixes)

### Persistence

| Cache | Storage | Invalidation |
|-------|---------|-------------|
| Page Intelligence | `page_intelligence_cache` table | Data hash changes (new upload, new dates) |
| Element Captions | `element_captions_cache` table | Data hash changes |
| Both cleared on | Data upload (auto) | `clear_intelligence_cache()` called |

---

## Agentic AI System (`agents/`)

### Agent Architecture

```
User Question / Trigger
        │
   Commander Agent (GPT-5.4-mini via OpenRouter)
        ├── Diesel Specialist (GPT-5.4-mini)
        ├── Operations Specialist (GPT-5.4-mini)
        ├── Solar Specialist (Claude Haiku 4.5)
        └── Risk Specialist (GPT-5.4-mini)

Chat Agent — tool-calling Q&A on every page (23 tools)
Briefing Agent — autonomous C-suite morning briefing
```

### 23 Registered Tools

| Category | Tools |
|----------|-------|
| **ML Models (10)** | `forecast_diesel_price`, `predict_blackouts`, `generate_store_plan`, `analyze_diesel_efficiency`, `optimize_solar_mix`, `check_stockout_risk`, `predict_spoilage_risk`, `compute_holdings_kpis`, `simulate_scenario`, `run_all_models` |
| **Data Queries (5)** | `query_stores`, `query_energy_data`, `query_diesel_prices`, `query_inventory`, `get_latest_metrics` |
| **KPI Calculators (4)** | `get_energy_cost_pct`, `get_diesel_cost_per_store`, `get_resilience_index`, `get_diesel_coverage_days` |
| **Commander (4)** | `delegate_to_diesel_agent`, `delegate_to_operations_agent`, `delegate_to_solar_agent`, `delegate_to_risk_agent` |

### Agent Files

```
agents/
├── __init__.py
├── config.py                  # Models, limits, is_agent_mode_available()
├── model_router.py            # Routes task types → OpenRouter model IDs
├── base.py                    # BaseAgent class with agentic tool-use loop
├── chat_agent.py              # Agentic chat (23 tools)
├── commander.py               # Orchestrator → delegates to 4 specialists
├── briefing_agent.py          # Autonomous morning briefing
├── tools/
│   ├── registry.py            # @tool decorator + execute_tool()
│   ├── model_tools.py         # 10 ML model tools
│   ├── data_tools.py          # 5 data query tools
│   └── kpi_tools.py           # 4 KPI calculator tools
└── specialists/
    ├── diesel_agent.py        # Diesel procurement specialist
    ├── operations_agent.py    # Store operations specialist
    ├── solar_agent.py         # Solar/energy mix specialist (Claude Haiku 4.5)
    └── risk_agent.py          # Spoilage/stockout risk specialist
```

### Graceful Fallback

```
Level 1: Full agentic     (OpenRouter key + GPT-5.4-mini/Claude Haiku available)
Level 2: Basic agentic    (OpenRouter key + any model)
Level 3: Current behavior (OpenRouter key, text summaries only)
Level 4: No API key       (Pure rule-based — everything still works)
```

---

## Database (SQLite)

**File:** `data/eis.db`

| Table | Purpose |
|-------|---------|
| `training_runs` | ML training history: timestamp, duration, alerts, terminal logs |
| `upload_history` | Every file upload: filename, rows, destination, validation |
| `chat_messages` | AI chat history: persists across page refreshes |
| `saved_scenarios` | Scenario Simulator: saved what-if scenarios with all parameters + results |
| `insights_cache` | Cached rule-based AI insights |
| `activity_log` | All user actions: train, upload, delete, switch data, etc. |
| `page_intelligence_cache` | AI page intelligence briefings (keyed by page_id + data_hash) |
| `element_captions_cache` | AI element captions (keyed by page_id + data_hash) |
| `bcp_incidents` | BCP incident log: store, type, duration, response, losses, lessons |
| `bcp_drills` | BCP drill schedule: store, type, date, status, readiness score |

---

## Data Files (12 CSVs)

| File | Rows | Priority | Description |
|------|------|----------|-------------|
| `stores.csv` | 55 | REQUIRED | Store master: sector, channel, township, solar, generator |
| `daily_energy.csv` | 9,900 | REQUIRED | Blackout hours, generator hours, diesel, solar per store/day |
| `diesel_prices.csv` | 180 | REQUIRED | Daily market diesel price, FX rate, oil price (benchmark) |
| `fx_rates.csv` | 180 | Recommended | USD, EUR, SGD, THB, CNY to MMK daily |
| `diesel_inventory.csv` | 9,900 | Recommended | Per-site tank storage levels, days of coverage |
| `store_sales.csv` | 158,400 | Recommended | Hourly sales and margin per store |
| `solar_generation.csv` | 24,300 | Optional | Hourly solar output for 15 solar-equipped sites |
| `temperature_logs.csv` | 69,120 | Optional | Cold chain temperature readings for 32 sites |
| `supplier_master.csv` | 4 | Procurement | Supplier registry: pricing tiers, reliability, payment terms |
| `diesel_procurement.csv` | ~986 | Procurement | Purchase orders with actual supplier-specific pricing |
| `diesel_transfers.csv` | ~114 | Procurement | Inter-site fuel transfers and depot-to-site movements |
| `generator_maintenance.csv` | ~111 | Procurement | Generator service history and maintenance schedule |

### Diesel Pricing Model
```
diesel_prices.csv = Market benchmark price (same for everyone)
supplier_master.csv = Each supplier has price_markup_pct (+2%, -1%, +5%)
diesel_procurement.csv = Actual price per PO = market x markup ± bulk discount ± emergency premium
```

**Storage:** `data/sample/` (synthetic) or `data/real/` (uploaded). Toggle via Data Upload page.

**Master Data Template:** Downloadable Excel workbook (13 sheets) with all column definitions, sample data, and dropdown validations. Available on the Data Upload page.

---

## Project Structure

```
energy-intelligence-system/
├── CLAUDE.md                           # This file
├── README.md                           # Setup + deployment guide
├── .env.example                        # Environment variables template
├── .gitignore                          # Git exclusions
├── app.py                              # Main Streamlit app (home page)
├── requirements.txt                    # Python dependencies (pinned versions)
├── Dockerfile                          # Container build (non-root user)
├── docker-compose.yml                  # Container orchestration (env from .env)
├── .dockerignore                       # Docker build exclusions
├── config/
│   └── settings.py                     # Sectors, stores, thresholds, AGENT_CONFIG
├── data/
│   ├── generators/synthetic_data.py    # Generates 12 sample CSVs
│   ├── sample/                         # Generated sample CSVs (8 operational + 4 procurement)
│   ├── real/                           # User-uploaded real CSVs
│   └── eis.db                          # SQLite database (10 tables)
├── models/
│   ├── diesel_price_forecast.py        # M1: Prophet
│   ├── blackout_prediction.py          # M2: XGBoost
│   ├── store_decision_engine.py        # M3: Rule-based
│   ├── diesel_optimizer.py             # M4: Regression + Isolation Forest
│   ├── solar_optimizer.py              # M5: Linear Programming
│   ├── stockout_alert.py              # M6: Probabilistic
│   ├── spoilage_predictor.py          # M7: Random Forest
│   ├── holdings_aggregator.py          # M8: Aggregation + Scenarios
│   └── bcp_engine.py                   # M9: BCP scoring, playbooks, RTO
├── agents/                             # Agentic AI Layer
│   ├── config.py, base.py, model_router.py
│   ├── chat_agent.py, commander.py, briefing_agent.py
│   ├── tools/ (registry, model_tools, data_tools, kpi_tools)
│   └── specialists/ (diesel, operations, solar, risk)
├── pages/
│   ├── 01-11 (original pages)
│   └── 12_🛡️_BCP_Dashboard.py         # BCP: scores, playbooks, RTO, incidents, drills
├── alerts/
│   └── alert_engine.py                 # Alert system + run_agent_orchestrated()
└── utils/
    ├── ai_chat.py                      # AI chat widget (agentic + fallback)
    ├── charts.py                       # Reusable Plotly components
    ├── data_loader.py                  # Load CSVs (sample/real toggle)
    ├── database.py                     # SQLite: 10 tables, all CRUD ops
    ├── element_captions.py             # AI captions per chart/table/card (DB-persisted)
    ├── insight_engine.py               # Rule-based + LLM insight generator
    ├── kpi_calculator.py               # 8 shared KPI formulas
    ├── llm_client.py                   # OpenRouter (env var, no hardcoded keys)
    ├── mermaid_helper.py               # Mermaid diagrams with zoom/pan
    ├── page_insights.py                # Legacy insights widget
    ├── page_intelligence.py            # AI page intelligence (4-type analysis, DB-persisted)
    ├── smart_table.py                  # Enhanced HTML tables with severity badges
    └── template_generator.py           # Master Excel template (13 sheets, formatted)
```

---

## Commands

```bash
# Setup
cp .env.example .env          # Then edit .env with your API key
pip install -r requirements.txt
python data/generators/synthetic_data.py
streamlit run app.py

# Docker (production)
cp .env.example .env           # Edit with real values
docker compose up -d --build
docker logs energy-command-agent -f
docker compose down
```

---

## Environment Variables

All env vars are configured via `.env` file (see `.env.example`).

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | For AI features | (none) | OpenRouter API key. Without it, system runs rule-based only. |
| `EIS_DATA_SOURCE` | No | `sample` | Data source: `sample` or `real` |
| `EIS_AGENT_ENABLED` | No | `true` | Enable/disable agentic AI mode |
| `EIS_SMTP_SERVER` | For email | (none) | Outlook SMTP server (smtp.office365.com) |
| `EIS_SMTP_PORT` | For email | `587` | SMTP port |
| `EIS_SMTP_USER` | For email | (none) | Email sender address |
| `EIS_SMTP_PASSWORD` | For email | (none) | Email app password |

**Security:** No API keys are hardcoded. All secrets come from `.env` file (excluded from git).

---

## AI Enhancement Roadmap

| Phase | What | Status |
|-------|------|--------|
| 5A | Auto-generated insights + LLM summaries + AI Chat | Done |
| **6A** | **Agentic AI — tool-calling agents via OpenRouter** | **Done** |
| **6B** | **AI Page Intelligence (Descriptive/Predictive/Prescriptive/Recommendations)** | **Done** |
| **6C** | **AI Element Captions — per chart/table/card, DB-persisted** | **Done** |
| **6D** | **Smart Tables — severity badges, conditional formatting** | **Done** |
| **7A** | **Scenario Simulator — templates, sensitivity, waterfall, break-even, timeline, radar** | **Done** |
| **7B** | **BCP Dashboard — scores, playbooks, RTO, assets, incidents, drills** | **Done** |
| 8A | Financial P&L Dashboard — revenue vs energy cost, budget vs actual | Planned |
| 8B | Cash Flow Forecast — weekly diesel procurement needs | Planned |
| 8C | Carbon/ESG Dashboard — emissions tracking, solar offset | Planned |
| 8D | Automated Weekly PDF Report | Planned |
| 8E | Generator Maintenance Scheduler | Planned |

---

## Design Principles

1. **Decision-first** — every page answers "what should I do today?"
2. **Max 4 cards per row** — consistent layout across all pages
3. **Federated model** — sector autonomy + Holdings control
4. **Hybrid AI** — rule engine (free, instant) + LLM (polished) + agents (autonomous)
5. **Persistent intelligence** — AI insights stored in DB, only regenerate on data change
6. **Color-coded severity** — red (critical), orange (warning), green (ok) everywhere
7. **Collapsible depth** — headline + action always visible, detail in expanders
8. **Smart tables** — severity badges, conditional colors, formatted numbers
9. **Graceful degradation** — agents → LLM → rule-based, always works without API keys
10. **BCP-integrated** — continuity planning embedded in the operational tool, not separate

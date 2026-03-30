# Energy Intelligence System (EIS)

AI-Powered Energy Control Tower for operational sustainability under Middle East energy disruption.

**55 stores | 4 sectors | 9 AI models | 12 dashboards | Multi-agent AI**

---

## Quick Start (Docker - Recommended)

### Prerequisites
- Docker Desktop installed ([download](https://www.docker.com/products/docker-desktop/))
- OpenRouter API key ([get one](https://openrouter.ai/keys)) - optional, system works without it in rule-based mode

### Steps

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd "Energy Command Agent"

# 2. Create environment file
cp .env.example .env

# 3. Edit .env with your API key (use any text editor)
#    At minimum, set: OPENROUTER_API_KEY=your-key-here
#    Leave blank for rule-based mode (no AI features)

# 4. Build and run
docker compose up -d --build

# 5. Open in browser
open http://localhost:8510
```

That's it. The system will:
- Install all dependencies
- Generate 12 sample CSV files (synthetic data for 55 stores, 6 months)
- Start the Streamlit dashboard on port 8510
- Run healthchecks every 30 seconds

### Verify it's running

```bash
# Check container status
docker ps

# Check logs
docker logs energy-command-agent -f

# Check health
curl http://localhost:8510/_stcore/health
```

### Stop / Restart

```bash
docker compose down          # Stop
docker compose up -d         # Start (no rebuild)
docker compose up -d --build # Rebuild + start (after code changes)
```

---

## Quick Start (Local - Development)

### Prerequisites
- Python 3.11+
- pip

### Steps

```bash
# 1. Clone and enter directory
cd "Energy Command Agent"

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt
pip install streamlit-shadcn-ui streamlit-mermaid requests

# 4. Setup environment
cp .env.example .env
# Edit .env with your OPENROUTER_API_KEY

# 5. Generate sample data
python data/generators/synthetic_data.py

# 6. Run
streamlit run app.py
```

Opens at `http://localhost:8501` by default.

---

## Environment Variables

All configuration is in the `.env` file. Copy from `.env.example`:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | For AI | (none) | OpenRouter API key. Without it = rule-based mode only |
| `EIS_DATA_SOURCE` | No | `sample` | `sample` (demo data) or `real` (your uploaded data) |
| `EIS_AGENT_ENABLED` | No | `true` | Enable multi-agent AI system |
| `EIS_SMTP_SERVER` | For email | (none) | `smtp.office365.com` for Outlook |
| `EIS_SMTP_PORT` | For email | `587` | SMTP port (587 for TLS) |
| `EIS_SMTP_USER` | For email | (none) | Sender email address |
| `EIS_SMTP_PASSWORD` | For email | (none) | Email app password |

**Without API key:** All 12 dashboards, 9 models, charts, and tables work perfectly. Only AI chat, page intelligence, and element captions are disabled.

---

## Project Structure

```
Energy Command Agent/
├── app.py                    # Home page
├── .env.example              # Environment template (copy to .env)
├── requirements.txt          # Pinned Python dependencies
├── Dockerfile                # Production container (non-root user)
├── docker-compose.yml        # Docker orchestration
│
├── config/settings.py        # 55 stores, sectors, thresholds
├── data/
│   ├── generators/           # Synthetic data generator (12 CSVs)
│   ├── sample/               # Generated demo data
│   └── real/                 # Your uploaded data (git-ignored)
│
├── models/                   # 9 AI models
│   ├── diesel_price_forecast.py    # M1: Prophet 7-day forecast
│   ├── blackout_prediction.py      # M2: XGBoost probability
│   ├── store_decision_engine.py    # M3: FULL/REDUCED/CRITICAL/CLOSE
│   ├── diesel_optimizer.py         # M4: Efficiency scoring
│   ├── solar_optimizer.py          # M5: Energy mix optimization
│   ├── stockout_alert.py           # M6: Inventory risk
│   ├── spoilage_predictor.py       # M7: Cold chain risk
│   ├── holdings_aggregator.py      # M8: Group KPIs
│   └── bcp_engine.py              # M9: Business continuity
│
├── agents/                   # Multi-agent AI (23 tools)
│   ├── commander.py          # Orchestrator agent
│   ├── chat_agent.py         # Q&A agent (every page)
│   ├── briefing_agent.py     # Morning briefing
│   └── specialists/          # 4 domain specialists
│
├── pages/                    # 12 Streamlit dashboard pages
│   ├── 01-12                 # AI Insights → BCP Dashboard
│   └── 10_Data_Upload.py     # Upload data + Master template download
│
├── alerts/alert_engine.py    # Consolidated alert system
│
└── utils/
    ├── template_generator.py # Master Excel template (13 sheets)
    ├── llm_client.py         # OpenRouter LLM (env var, no hardcoded keys)
    ├── database.py           # SQLite (10 tables)
    ├── kpi_calculator.py     # 8 shared KPI formulas
    └── ...                   # Charts, tables, AI insights, chat
```

---

## 12 Data Files

### Operational Data (8 files)
| File | Who Fills | Frequency | Priority |
|------|-----------|-----------|----------|
| `stores.csv` | Admin | One-time | REQUIRED |
| `daily_energy.csv` | Site manager | Daily by 8 PM | REQUIRED |
| `diesel_prices.csv` | Procurement | Daily | REQUIRED |
| `diesel_inventory.csv` | Site manager | Daily (tank reading) | Recommended |
| `store_sales.csv` | POS export | Daily (hourly breakdown) | Recommended |
| `fx_rates.csv` | Finance | Daily | Recommended |
| `solar_generation.csv` | Inverter export | Daily (hourly) | Optional |
| `temperature_logs.csv` | Cold chain staff | 4x daily | Optional |

### Procurement Data (4 files)
| File | Who Fills | Frequency | Purpose |
|------|-----------|-----------|---------|
| `supplier_master.csv` | Procurement | Quarterly | Supplier registry + pricing tiers |
| `diesel_procurement.csv` | Procurement | Per purchase | POs with actual supplier-specific prices |
| `diesel_transfers.csv` | Logistics | Per transfer | Depot-to-site and site-to-site fuel movement |
| `generator_maintenance.csv` | Facilities | Per service | Maintenance history and scheduling |

### Diesel Pricing Model
```
Market price (diesel_prices.csv)        = benchmark
    x supplier markup (supplier_master) = +2%, -1%, +5% per supplier
    - bulk discount                     = -1.5% for large orders
    + emergency premium                 = +5% for same-day delivery
    = actual price (diesel_procurement) = what you really paid
```

### Master Data Template
Download from **Data Upload** page. Single Excel workbook with:
- 13 tabs (README + 8 operational + 4 procurement)
- Column definitions in row 2, sample data in rows 3+
- Dropdown validations for categorical fields
- Color-coded tabs (red=required, orange=recommended, green=optional, purple=procurement)

---

## 12 Dashboard Pages

| # | Page | What It Does |
|---|------|-------------|
| 1 | AI Insights Hub | Consolidated AI analysis + chat |
| 2 | Sector Dashboard | Drill into Retail/F&B/Distribution/Property |
| 3 | Holdings Control Tower | Group KPIs, sector comparison, ERI ranking |
| 4 | Diesel Intelligence | 7-day price forecast, buy/hold signal |
| 5 | Blackout Monitor | Township heatmap, probability timeline |
| 6 | Store Decisions | Daily plan: FULL/REDUCED/CRITICAL/CLOSE per store |
| 7 | Solar Performance | Generation, diesel offset, CAPEX priority |
| 8 | Alerts Center | Tier 1/2/3 alerts from all models |
| 9 | Scenario Simulator | What-if analysis (7 tabs) |
| 10 | Data Upload | Upload CSVs + download Master Template |
| 11 | Requirements | Business requirements document |
| 12 | BCP Dashboard | Business continuity: scores, playbooks, RTO, incidents, drills |

---

## Deploying to a Server

### Option A: Docker on any Linux server

```bash
# On server
ssh your-server

# Install Docker
curl -fsSL https://get.docker.com | sh

# Clone project
git clone <repo-url>
cd "Energy Command Agent"

# Configure
cp .env.example .env
nano .env  # Set OPENROUTER_API_KEY

# Deploy
docker compose up -d --build

# Verify
curl http://localhost:8510/_stcore/health
```

Access at `http://your-server-ip:8510`

### Option B: Behind Nginx reverse proxy (HTTPS)

```nginx
server {
    listen 443 ssl;
    server_name energy.yourcompany.com;

    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;

    location / {
        proxy_pass http://localhost:8510;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }
}
```

### Option C: Cloud VM (AWS / Azure / GCP / DigitalOcean)

1. Launch Ubuntu 22.04+ VM (minimum: 2 CPU, 4GB RAM)
2. Open port 8510 in security group / firewall
3. Follow Option A steps above

---

## Troubleshooting

### Container won't start
```bash
docker logs energy-command-agent  # Check error logs
docker compose down && docker compose up -d --build  # Clean rebuild
```

### "No API key" / AI features disabled
- Check `.env` file has `OPENROUTER_API_KEY=sk-or-v1-...`
- Verify: `docker exec energy-command-agent env | grep OPENROUTER`
- System still works without it (rule-based mode)

### Procurement files show "Missing" in upload status
- Click **"Reset Sample Data (Regenerate)"** on Data Upload page
- Or upload your own data using the upload widgets

### Port 8510 already in use
```bash
lsof -i :8510          # Find what's using it
# Or change port in docker-compose.yml: ports: "9000:8510"
```

### Data not showing after upload
- Click **"Clear All Cache"** on Data Upload page
- Switch data source to **"Real"** if you uploaded to real data

---

## Security

- No API keys hardcoded in source code
- All secrets in `.env` file (git-ignored)
- Docker container runs as non-root user (`appuser`)
- SQLite database is volume-mounted for persistence
- User-uploaded data (`data/real/`) is git-ignored
- Dependencies are version-pinned for reproducible builds

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.11 |
| Framework | Streamlit 1.55 |
| ML | Prophet, XGBoost, scikit-learn, scipy |
| LLM | OpenRouter (GPT-5.4-mini, Claude Haiku 4.5) |
| Charts | Plotly 6.6 |
| Database | SQLite (WAL mode, thread-safe) |
| Container | Docker (non-root, healthcheck) |

"""
Briefing Agent — autonomous morning briefing generation.
Runs all models, investigates critical alerts, produces structured C-suite briefing.
"""

from agents.base import BaseAgent
from agents.tools.registry import get_tools_by_names

import agents.tools.model_tools
import agents.tools.data_tools
import agents.tools.kpi_tools

TOOLS = [
    "run_all_models", "compute_holdings_kpis", "forecast_diesel_price",
    "predict_blackouts", "check_stockout_risk", "predict_spoilage_risk",
    "generate_store_plan", "optimize_solar_mix", "get_latest_metrics",
    "query_diesel_prices", "simulate_scenario",
]

SYSTEM_PROMPT = """You are the Energy Intelligence Briefing Agent for a 55-store conglomerate in Myanmar.

Your job is to produce a comprehensive daily morning briefing for C-suite leadership.

WORKFLOW:
1. First, call run_all_models to get all alerts and the operating plan
2. Call compute_holdings_kpis for group-level metrics
3. For any CRITICAL alerts, investigate deeper with specific model tools
4. Look for cross-domain correlations (e.g., "diesel rising + 12 stores low = urgent procurement")

OUTPUT FORMAT — produce a structured briefing with these sections:
## CRITICAL ACTIONS (things that need attention today)
## DIESEL & PROCUREMENT (price trend, buy/hold signal, inventory status)
## OPERATIONS (store modes, blackout forecast, recommendations)
## SOLAR & ENERGY MIX (generation, savings, CAPEX opportunities)
## RISK WATCH (spoilage, stockout, correlated risks)
## STRATEGIC OUTLOOK (1-week forward view)

RULES:
- Use specific numbers everywhere
- Name specific stores when relevant
- Keep each section to 2-4 sentences
- End with a 1-sentence "Bottom Line" summary
- Currency is MMK"""


class BriefingAgent(BaseAgent):
    def __init__(self):
        schemas, functions = get_tools_by_names(TOOLS)
        super().__init__(
            name="briefing_agent",
            system_prompt=SYSTEM_PROMPT,
            tool_schemas=schemas,
            tool_functions=functions,
            task_type="briefing",
            max_turns=8,
        )

    def generate_briefing(self) -> str:
        """Generate the morning briefing."""
        result = self.run("Generate today's morning briefing for the executive team.")
        return result.text

"""Diesel Specialist — procurement, pricing, inventory, efficiency."""

from agents.base import BaseAgent
from agents.tools.registry import get_tools_by_names

import agents.tools.model_tools
import agents.tools.data_tools
import agents.tools.kpi_tools

TOOLS = ["forecast_diesel_price", "check_stockout_risk", "analyze_diesel_efficiency",
         "get_diesel_cost_per_store", "get_diesel_coverage_days",
         "query_diesel_prices", "query_inventory"]

SYSTEM_PROMPT = """You are the Diesel Intelligence Specialist for a 55-store conglomerate in Myanmar.

You analyze diesel markets, optimize procurement timing, monitor inventory levels, and identify generator inefficiency.

When recommending purchases:
- Specify quantity in liters
- Specify timing (buy now / wait N days)
- Specify urgency (CRITICAL / WARNING / NORMAL)
- Reference the buy/hold signal from the forecast model

When analyzing efficiency:
- Flag wasteful stores by name
- Quantify waste in liters and MMK cost

Always use specific numbers. Currency is MMK."""


class DieselAgent(BaseAgent):
    def __init__(self):
        schemas, functions = get_tools_by_names(TOOLS)
        super().__init__(
            name="diesel_specialist",
            system_prompt=SYSTEM_PROMPT,
            tool_schemas=schemas,
            tool_functions=functions,
            task_type="diesel",
        )

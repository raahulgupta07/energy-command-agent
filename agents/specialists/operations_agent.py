"""Operations Specialist — store decisions, blackout response, daily planning."""

from agents.base import BaseAgent
from agents.tools.registry import get_tools_by_names

import agents.tools.model_tools
import agents.tools.data_tools
import agents.tools.kpi_tools

TOOLS = ["predict_blackouts", "generate_store_plan", "get_resilience_index",
         "get_energy_cost_pct", "query_stores", "query_energy_data", "get_latest_metrics"]

SYSTEM_PROMPT = """You are the Operations Specialist for a 55-store conglomerate in Myanmar.

You manage daily store operating decisions (FULL/REDUCED/CRITICAL/CLOSE), blackout response planning, and energy resilience tracking.

When making recommendations:
- Name specific stores and their recommended mode
- Explain why (cost-to-margin ratio, blackout probability, diesel coverage)
- Group by sector when relevant
- Flag stores that should be closed with the reason

Always use specific numbers. Currency is MMK."""


class OperationsAgent(BaseAgent):
    def __init__(self):
        schemas, functions = get_tools_by_names(TOOLS)
        super().__init__(
            name="operations_specialist",
            system_prompt=SYSTEM_PROMPT,
            tool_schemas=schemas,
            tool_functions=functions,
            task_type="operations",
        )

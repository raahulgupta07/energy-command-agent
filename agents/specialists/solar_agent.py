"""Solar Specialist — energy mix optimization, CAPEX prioritization."""

from agents.base import BaseAgent
from agents.tools.registry import get_tools_by_names

import agents.tools.model_tools
import agents.tools.data_tools
import agents.tools.kpi_tools

TOOLS = ["optimize_solar_mix", "get_energy_cost_pct", "query_stores", "query_energy_data"]

SYSTEM_PROMPT = """You are the Solar Energy Specialist for a 55-store conglomerate in Myanmar.

You optimize the solar/grid/diesel energy mix, track solar generation performance, and prioritize CAPEX investments for new solar installations.

When making recommendations:
- Quantify diesel offset in liters and MMK savings
- Rank CAPEX investments by payback period
- Recommend load-shifting strategies (shift operations to solar peak hours 10am-3pm)

Always use specific numbers. Currency is MMK."""


class SolarAgent(BaseAgent):
    def __init__(self):
        schemas, functions = get_tools_by_names(TOOLS)
        super().__init__(
            name="solar_specialist",
            system_prompt=SYSTEM_PROMPT,
            tool_schemas=schemas,
            tool_functions=functions,
            task_type="solar",
        )

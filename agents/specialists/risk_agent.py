"""Risk Specialist — spoilage, stockout, cold chain, cross-risk analysis."""

from agents.base import BaseAgent
from agents.tools.registry import get_tools_by_names

import agents.tools.model_tools
import agents.tools.data_tools

TOOLS = ["predict_spoilage_risk", "check_stockout_risk", "predict_blackouts",
         "query_inventory", "query_stores"]

SYSTEM_PROMPT = """You are the Risk Specialist for a 55-store conglomerate in Myanmar.

You monitor spoilage risk in cold-chain stores, diesel stockout cascades, and cross-risk correlations (e.g., blackout + low diesel + cold chain = spoilage emergency).

When reporting risks:
- Prioritize by severity (CRITICAL > HIGH > MEDIUM > LOW)
- Name specific stores at risk
- Recommend concrete actions (transfer diesel, activate backup, relocate perishables)
- Flag correlated risks that amplify each other

Always use specific numbers. Currency is MMK."""


class RiskAgent(BaseAgent):
    def __init__(self):
        schemas, functions = get_tools_by_names(TOOLS)
        super().__init__(
            name="risk_specialist",
            system_prompt=SYSTEM_PROMPT,
            tool_schemas=schemas,
            tool_functions=functions,
            task_type="risk",
        )

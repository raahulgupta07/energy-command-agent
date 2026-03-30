"""
Commander Agent — top-level orchestrator that delegates to specialists.
"""

import json
from agents.base import BaseAgent, AgentResult
from agents.tools.registry import tool, get_tools_by_names

import agents.tools.data_tools


# ── Delegation tools (call specialist agents as tools) ────────────────────

@tool("delegate_to_diesel_agent",
      "Delegate a diesel/fuel/procurement question to the Diesel Specialist agent.",
      {"type": "object", "properties": {
          "question": {"type": "string", "description": "The question to ask the diesel specialist"}
      }, "required": ["question"]})
def delegate_to_diesel_agent(question: str):
    from agents.specialists.diesel_agent import DieselAgent
    agent = DieselAgent()
    result = agent.run(question)
    return {"specialist": "diesel", "response": result.text,
            "tools_used": [tc["name"] for tc in result.tool_calls_made],
            "success": result.success}


@tool("delegate_to_operations_agent",
      "Delegate a store operations/blackout/planning question to the Operations Specialist.",
      {"type": "object", "properties": {
          "question": {"type": "string", "description": "The question to ask the operations specialist"}
      }, "required": ["question"]})
def delegate_to_operations_agent(question: str):
    from agents.specialists.operations_agent import OperationsAgent
    agent = OperationsAgent()
    result = agent.run(question)
    return {"specialist": "operations", "response": result.text,
            "tools_used": [tc["name"] for tc in result.tool_calls_made],
            "success": result.success}


@tool("delegate_to_solar_agent",
      "Delegate a solar/renewable energy question to the Solar Specialist.",
      {"type": "object", "properties": {
          "question": {"type": "string", "description": "The question to ask the solar specialist"}
      }, "required": ["question"]})
def delegate_to_solar_agent(question: str):
    from agents.specialists.solar_agent import SolarAgent
    agent = SolarAgent()
    result = agent.run(question)
    return {"specialist": "solar", "response": result.text,
            "tools_used": [tc["name"] for tc in result.tool_calls_made],
            "success": result.success}


@tool("delegate_to_risk_agent",
      "Delegate a risk/spoilage/stockout question to the Risk Specialist.",
      {"type": "object", "properties": {
          "question": {"type": "string", "description": "The question to ask the risk specialist"}
      }, "required": ["question"]})
def delegate_to_risk_agent(question: str):
    from agents.specialists.risk_agent import RiskAgent
    agent = RiskAgent()
    result = agent.run(question)
    return {"specialist": "risk", "response": result.text,
            "tools_used": [tc["name"] for tc in result.tool_calls_made],
            "success": result.success}


COMMANDER_TOOLS = [
    "delegate_to_diesel_agent", "delegate_to_operations_agent",
    "delegate_to_solar_agent", "delegate_to_risk_agent",
    "query_stores", "query_energy_data", "query_diesel_prices",
    "get_latest_metrics",
]

SYSTEM_PROMPT = """You are the Energy Command Agent — the strategic coordinator for a 55-store conglomerate in Myanmar facing energy disruption.

You have 4 specialist agents you can delegate to:
- **Diesel Specialist**: procurement timing, price forecasts, inventory, generator efficiency
- **Operations Specialist**: store operating modes (FULL/REDUCED/CRITICAL/CLOSE), blackout planning
- **Solar Specialist**: energy mix optimization, CAPEX prioritization
- **Risk Specialist**: spoilage, stockout cascades, cross-risk correlation

RULES:
- For domain-specific questions, delegate to the right specialist
- For cross-domain questions (e.g., "full risk assessment"), delegate to MULTIPLE specialists and synthesize
- You also have direct data query tools for quick lookups
- Always synthesize specialist responses into a unified recommendation
- Be concise but specific. Use numbers. Currency is MMK.
- End every response with a clear "RECOMMENDED ACTIONS" section"""


class CommanderAgent(BaseAgent):
    def __init__(self):
        schemas, functions = get_tools_by_names(COMMANDER_TOOLS)
        super().__init__(
            name="commander",
            system_prompt=SYSTEM_PROMPT,
            tool_schemas=schemas,
            tool_functions=functions,
            task_type="commander",
            max_turns=8,
        )

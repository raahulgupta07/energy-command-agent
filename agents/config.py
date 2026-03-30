"""
Agent Configuration — models, limits, feature flags.
All LLM calls route through OpenRouter.
"""

import os

AGENT_ENABLED = os.environ.get("EIS_AGENT_ENABLED", "true").lower() == "true"

AGENT_MODELS = {
    "reasoning": "openai/gpt-5.4-mini",
    "fast": "anthropic/claude-haiku-4.5",
    "summary": "anthropic/claude-3.5-haiku",
}

AGENT_CONFIG = {
    "enabled": AGENT_ENABLED,
    "max_agent_turns": 10,
    "max_tokens_default": 4096,
    "temperature_default": 0.3,
    "max_tool_result_rows": 30,
}

AGENT_MODEL_MAP = {
    "commander": AGENT_MODELS["reasoning"],
    "chat": AGENT_MODELS["reasoning"],
    "briefing": AGENT_MODELS["reasoning"],
    "diesel": AGENT_MODELS["reasoning"],
    "operations": AGENT_MODELS["reasoning"],
    "solar": AGENT_MODELS["fast"],
    "risk": AGENT_MODELS["reasoning"],
}


def is_agent_mode_available() -> bool:
    from utils.llm_client import is_llm_available
    return AGENT_CONFIG["enabled"] and is_llm_available()

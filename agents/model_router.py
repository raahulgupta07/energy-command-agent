"""
Model Router — selects the right OpenRouter model ID for each task type.
Fallback chain: Claude Sonnet 4 → Gemini Flash → GPT-4.1-mini
"""

from agents.config import AGENT_MODELS, AGENT_MODEL_MAP


def select_model(task_type: str) -> str:
    """Return OpenRouter model ID based on task type.

    Args:
        task_type: One of "commander", "diesel", "operations", "risk",
                   "solar", "chat", "briefing", "quick_followup", "summary"

    Returns:
        str: OpenRouter model ID (e.g. "anthropic/claude-sonnet-4")
    """
    return AGENT_MODEL_MAP.get(task_type, AGENT_MODELS["reasoning"])


def get_fallback_chain(primary_model: str) -> list:
    """Return ordered fallback models if primary fails.

    Args:
        primary_model: The preferred model ID

    Returns:
        list: Ordered list of model IDs to try
    """
    all_models = [
        AGENT_MODELS["reasoning"],
        AGENT_MODELS["fast"],
        AGENT_MODELS["summary"],
    ]
    # Put primary first, then others in order
    chain = [primary_model]
    for m in all_models:
        if m not in chain:
            chain.append(m)
    return chain

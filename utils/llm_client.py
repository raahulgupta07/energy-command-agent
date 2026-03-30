"""
LLM Client — OpenRouter with auto-fallback.
Primary: GPT-5.4-mini | Fallback: Claude Haiku 4.5, Claude 3.5 Haiku
Works without API key (returns None, system uses rule-based insights).
"""

import os
import json
import requests
from typing import Optional

# OpenRouter config — requires OPENROUTER_API_KEY env var
# System degrades gracefully to rule-based mode if not set
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Model priority — try in order
MODELS = [
    "openai/gpt-5.4-mini",
    "anthropic/claude-haiku-4.5",
    "anthropic/claude-3.5-haiku",
]


def is_llm_available() -> bool:
    """Check if LLM is configured."""
    return bool(OPENROUTER_API_KEY)


def get_active_model() -> str:
    """Return the primary model name."""
    return MODELS[0] if is_llm_available() else "rule-based (no API key)"


def call_llm(prompt: str, system_prompt: str = None, max_tokens: int = 1000,
             temperature: float = 0.3) -> Optional[str]:
    """Call OpenRouter LLM with auto-fallback.

    Returns:
        str: LLM response text, or None if no API key or all models fail.
    """
    if not OPENROUTER_API_KEY:
        return None

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://energy-intelligence-system.local",
        "X-Title": "Energy Intelligence System",
    }

    for model in MODELS:
        try:
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            response = requests.post(OPENROUTER_URL, headers=headers,
                                     json=payload, timeout=30)

            if response.status_code == 200:
                data = response.json()
                text = data["choices"][0]["message"]["content"]
                return text
            else:
                continue  # Try next model

        except Exception:
            continue  # Try next model

    return None  # All models failed


def generate_executive_summary(insights: list, kpis: dict = None) -> Optional[str]:
    """Generate a polished executive summary from rule-based insights.

    Args:
        insights: list of insight dicts from InsightEngine
        kpis: optional dict of current KPIs

    Returns:
        str: Executive summary paragraph, or None if LLM unavailable
    """
    if not insights:
        return None

    system_prompt = """You are an energy intelligence analyst for a conglomerate in Myanmar.
You write concise, actionable executive summaries for C-suite leadership.
Focus on: what changed, why it matters, and what to do about it.
Use specific numbers. Be direct. No fluff. Max 150 words."""

    insight_text = "\n".join([f"- [{i['level'].upper()}] {i['text']}" for i in insights[:15]])

    kpi_text = ""
    if kpis:
        kpi_text = f"""
Current KPIs:
- Total stores: {kpis.get('total_stores', 'N/A')}
- Energy cost % of sales: {kpis.get('energy_cost_pct_of_sales', 'N/A')}%
- Avg ERI: {kpis.get('avg_eri_pct', 'N/A')}%
- Diesel dependency: {kpis.get('avg_diesel_dependency_pct', 'N/A')}%
"""

    prompt = f"""Based on these automated insights from our Energy Intelligence System, write a brief executive summary:

{insight_text}
{kpi_text}
Write 3-4 sentences covering: key risk, biggest change, and recommended action."""

    return call_llm(prompt, system_prompt)


def generate_sector_insights(sector: str, insights: list) -> Optional[str]:
    """Generate sector-specific insights summary."""
    if not insights:
        return None

    system_prompt = f"""You are an energy analyst reporting on the {sector} sector.
Write a brief 2-3 sentence summary of what's happening. Be specific with numbers. Max 80 words."""

    insight_text = "\n".join([f"- {i['text']}" for i in insights[:10]])

    prompt = f"""Summarize these {sector} sector energy insights:

{insight_text}

Focus on the most impactful change and what action to take."""

    return call_llm(prompt, system_prompt)


def call_llm_with_tools(messages: list, tools: list = None, model: str = None,
                        max_tokens: int = 4096, temperature: float = 0.3) -> Optional[dict]:
    """Call OpenRouter with tool/function calling support.

    Uses OpenAI-compatible function calling format.

    Args:
        messages: list of message dicts [{role, content}]
        tools: list of tool schemas in OpenAI format (optional)
        model: OpenRouter model ID (defaults to primary model)
        max_tokens: max response tokens
        temperature: sampling temperature

    Returns:
        dict: Full response JSON, or None if all models fail.
              response["choices"][0]["message"] contains either:
              - "content" (text response) or
              - "tool_calls" (function calls to execute)
    """
    if not OPENROUTER_API_KEY:
        return None

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://energy-intelligence-system.local",
        "X-Title": "Energy Intelligence System",
    }

    models_to_try = [model] if model else MODELS
    # Add fallbacks
    for m in MODELS:
        if m not in models_to_try:
            models_to_try.append(m)

    for m in models_to_try:
        try:
            payload = {
                "model": m,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            if tools:
                payload["tools"] = tools

            response = requests.post(OPENROUTER_URL, headers=headers,
                                     json=payload, timeout=60)

            if response.status_code == 200:
                return response.json()
            else:
                continue
        except Exception:
            continue

    return None


def answer_data_question(question: str, context: str) -> Optional[str]:
    """Answer a user's natural language question about the data.

    Args:
        question: user's question
        context: relevant data context (KPIs, insights, recent data)

    Returns:
        str: AI answer, or None if LLM unavailable
    """
    system_prompt = """You are an AI assistant for the Energy Intelligence System — an energy management platform
for a conglomerate in Myanmar with 55+ stores across Retail, F&B, Distribution, and Property sectors.

You answer questions about energy costs, diesel prices, blackout patterns, solar performance,
store profitability, and operational decisions.

Rules:
- Use specific numbers from the context provided
- Be concise (max 100 words)
- If you don't have enough data to answer, say so
- Suggest which dashboard page to check for more detail
- Currency is MMK (Myanmar Kyat)"""

    prompt = f"""Context from the system:
{context}

User question: {question}

Answer concisely with data-driven insight."""

    return call_llm(prompt, system_prompt, max_tokens=500)

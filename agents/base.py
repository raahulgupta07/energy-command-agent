"""
BaseAgent — agentic loop via OpenRouter tool-calling.
"""

import json
import time
import logging
from dataclasses import dataclass, field
from typing import Optional

from agents.config import AGENT_CONFIG, AGENT_MODEL_MAP
from agents.tools.registry import execute_tool

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    text: str
    tool_calls_made: list = field(default_factory=list)
    model_used: str = ""
    turns: int = 0
    success: bool = True


class BaseAgent:
    def __init__(self, name: str, system_prompt: str, tool_schemas: list,
                 tool_functions: dict, task_type: str = "chat",
                 max_turns: int = None):
        self.name = name
        self.system_prompt = system_prompt
        self.tool_schemas = tool_schemas
        self.tool_functions = tool_functions
        self.model = AGENT_MODEL_MAP.get(task_type, AGENT_MODEL_MAP["chat"])
        self.max_turns = max_turns or AGENT_CONFIG["max_agent_turns"]

    def run(self, user_message: str, context: dict = None,
            conversation_history: list = None) -> AgentResult:
        from utils.llm_client import call_llm_with_tools

        messages = []
        system_content = self.system_prompt
        if context:
            system_content += "\n\nContext:\n" + "\n".join(
                f"- {k}: {v}" for k, v in context.items())
        messages.append({"role": "system", "content": system_content})

        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})

        tool_calls_made = []
        turns = 0

        while turns < self.max_turns:
            turns += 1
            response = call_llm_with_tools(
                messages=messages,
                tools=self.tool_schemas or None,
                model=self.model,
                max_tokens=AGENT_CONFIG["max_tokens_default"],
                temperature=AGENT_CONFIG["temperature_default"],
            )

            if response is None:
                return AgentResult(
                    text="AI models are temporarily unavailable.",
                    tool_calls_made=tool_calls_made,
                    model_used=self.model, turns=turns, success=False)

            message = response.get("choices", [{}])[0].get("message", {})
            model_used = response.get("model", self.model)
            tool_calls = message.get("tool_calls")

            if not tool_calls:
                return AgentResult(
                    text=message.get("content", ""),
                    tool_calls_made=tool_calls_made,
                    model_used=model_used, turns=turns, success=True)

            # Execute tool calls
            messages.append({
                "role": "assistant",
                "content": message.get("content"),
                "tool_calls": tool_calls,
            })

            for tc in tool_calls:
                tool_name = tc["function"]["name"]
                try:
                    tool_args = json.loads(tc["function"]["arguments"])
                except (json.JSONDecodeError, KeyError):
                    tool_args = {}

                tool_call_id = tc.get("id", f"call_{tool_name}_{turns}")
                logger.info(f"[{self.name}] Tool: {tool_name}({tool_args})")

                start = time.time()
                result_str = execute_tool(tool_name, tool_args)
                elapsed = round(time.time() - start, 1)

                tool_calls_made.append({
                    "name": tool_name, "input": tool_args,
                    "output_preview": result_str[:200], "duration_s": elapsed})

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": result_str,
                })

        return AgentResult(
            text="Reached analysis limit. Here's what I found so far.",
            tool_calls_made=tool_calls_made,
            model_used=self.model, turns=turns, success=False)

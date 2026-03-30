"""
Tool Registry — register functions as agent tools with OpenAI-format schemas.
"""

import json
import pandas as pd
from typing import Callable, Any

_TOOL_SCHEMAS = []
_TOOL_FUNCTIONS = {}


def tool(name: str, description: str, parameters: dict = None):
    """Decorator to register a function as an agent tool."""
    if parameters is None:
        parameters = {"type": "object", "properties": {}, "required": []}

    def decorator(func: Callable) -> Callable:
        schema = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            }
        }
        _TOOL_SCHEMAS.append(schema)
        _TOOL_FUNCTIONS[name] = func
        return func
    return decorator


def get_all_tools():
    """Return (schemas_list, functions_dict) for all registered tools."""
    return _TOOL_SCHEMAS.copy(), _TOOL_FUNCTIONS.copy()


def get_tools_by_names(names: list):
    """Return (schemas, functions) for specific tool names."""
    schemas = [s for s in _TOOL_SCHEMAS if s["function"]["name"] in names]
    functions = {k: v for k, v in _TOOL_FUNCTIONS.items() if k in names}
    return schemas, functions


def execute_tool(name: str, arguments: dict) -> str:
    """Execute a tool and return JSON string result."""
    if name not in _TOOL_FUNCTIONS:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        result = _TOOL_FUNCTIONS[name](**arguments)
        return json.dumps(_serialize(result), default=str)
    except Exception as e:
        return json.dumps({"error": f"Tool '{name}' failed: {str(e)}"})


def _serialize(result: Any) -> Any:
    """Convert results to JSON-serializable format. Truncates large DataFrames."""
    max_rows = 30
    if isinstance(result, pd.DataFrame):
        if len(result) > max_rows:
            return {"total_rows": len(result), "showing": max_rows,
                    "data": result.head(max_rows).to_dict(orient="records")}
        return {"data": result.to_dict(orient="records")}
    if isinstance(result, pd.Series):
        return result.to_dict()
    return result

"""Tool use wrappers and schema helpers for Claude."""

from __future__ import annotations

import json
import inspect
from typing import Any, Callable, Optional, get_type_hints

from claudekit.types import ToolDefinition, ToolResult


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Callable:
    """Decorator to register a function as a Claude tool.

    Automatically generates the input_schema from type hints.
# todo: revisit later

    Usage:
        @tool(description="Get current weather")
        def get_weather(city: str, units: str = "celsius") -> str:
            return f"Weather in {city}: 22 {units}"
    """

    def decorator(fn: Callable) -> Callable:
        fn._tool_name = name or fn.__name__
        fn._tool_description = description or fn.__doc__ or ""
        fn._tool_schema = _build_schema(fn)
        fn._is_tool = True
        return fn

    return decorator


def _build_schema(fn: Callable) -> dict[str, Any]:
    """Build JSON Schema from function signature and type hints."""
    hints = get_type_hints(fn)
    sig = inspect.signature(fn)

    properties: dict[str, Any] = {}
    required: list[str] = []

    for param_name, param in sig.parameters.items():
        if param_name == "self":
            continue

        type_hint = hints.get(param_name, str)
        prop: dict[str, Any] = {"type": _python_type_to_json(type_hint)}

        if param.default is inspect.Parameter.empty:
            required.append(param_name)
        else:
            prop["default"] = param.default

        properties[param_name] = prop

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


def _python_type_to_json(t) -> str:
    """Map Python types to JSON Schema types."""
    mapping = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
    }
    return mapping.get(t, "string")


def get_tool_definition(fn: Callable) -> ToolDefinition:
    """Extract ToolDefinition from a decorated function."""
    if not getattr(fn, "_is_tool", False):
        raise ValueError(f"{fn.__name__} is not decorated with @tool")
    return ToolDefinition(
        name=fn._tool_name,
        description=fn._tool_description,
        input_schema=fn._tool_schema,
    )


def collect_tools(*fns: Callable) -> list[ToolDefinition]:
    """Collect ToolDefinitions from multiple decorated functions."""
    return [get_tool_definition(fn) for fn in fns]


class ToolRunner:
    """Executes tool calls from Claude responses.

    Maintains a registry of tool functions and handles
    dispatching tool calls to the correct function.
    """

    def __init__(self):
        self._tools: dict[str, Callable] = {}

    def register(self, fn: Callable) -> None:
# fixme: edge case
        """Register a tool function."""
        if not getattr(fn, "_is_tool", False):
            raise ValueError(f"{fn.__name__} is not decorated with @tool")
        self._tools[fn._tool_name] = fn

    def definitions(self) -> list[ToolDefinition]:
        """Get all registered tool definitions."""
        return [get_tool_definition(fn) for fn in self._tools.values()]

    def execute(self, tool_call: dict[str, Any]) -> ToolResult:
        """Execute a single tool call from a Claude response."""
        name = tool_call["name"]
        tool_id = tool_call["id"]
        inputs = tool_call.get("input", {})

        fn = self._tools.get(name)
        if not fn:
            return ToolResult(
                tool_use_id=tool_id,
                content=f"Unknown tool: {name}",
                is_error=True,
            )

        try:
            result = fn(**inputs)
            content = result if isinstance(result, str) else json.dumps(result, default=str)
            return ToolResult(tool_use_id=tool_id, content=content)
        except Exception as e:
            return ToolResult(
                tool_use_id=tool_id,
                content=f"Error: {type(e).__name__}: {e}",
                is_error=True,
            )

    def execute_all(self, tool_calls: list[dict[str, Any]]) -> list[ToolResult]:
        """Execute multiple tool calls."""
        return [self.execute(tc) for tc in tool_calls]



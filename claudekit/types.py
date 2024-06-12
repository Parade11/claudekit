"""Type definitions for claudekit."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Message:
    """A conversation message."""

    role: str  # "user", "assistant"
    content: str | list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {"role": self.role, "content": self.content}

    @classmethod
    def user(cls, text: str) -> "Message":
        return cls(role="user", content=text)

    @classmethod
    def assistant(cls, text: str) -> "Message":
        return cls(role="assistant", content=text)


@dataclass
class ToolDefinition:
    """Defines a tool that Claude can call."""

    name: str
    description: str
    input_schema: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


@dataclass
class ToolResult:
    """Result of a tool execution."""

    tool_use_id: str
    content: str
    is_error: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "tool_result",
            "tool_use_id": self.tool_use_id,
            "content": self.content,
            "is_error": self.is_error,
        }


@dataclass
class Usage:
    """Token usage from a response."""

    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class CompletionResponse:
    """Normalized response from Claude."""

    content: str
    model: str
    stop_reason: Optional[str] = None
    usage: Usage = field(default_factory=Usage)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    raw: Optional[dict] = None

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


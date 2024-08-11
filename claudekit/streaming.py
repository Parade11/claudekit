"""Streaming helpers for Claude API responses."""

from __future__ import annotations

import os
import sys
import logging
from typing import Any, Callable, Iterator, Optional

import anthropic

from claudekit.types import Message, ToolDefinition

logger = logging.getLogger(__name__)


class StreamHandler:
    """Handles streaming responses from the Claude API.

    Supports callbacks for text chunks, tool use events,
    and provides a simple iterator interface.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-sonnet-20240229",
        max_tokens: int = 1024,
        timeout: float = 120.0,
    ):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = model
        self.max_tokens = max_tokens
        self._client = anthropic.Anthropic(
            api_key=self.api_key,
            timeout=timeout,
        )

    def stream(
        self,
        messages: list[Message] | list[dict],
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        tools: Optional[list[ToolDefinition]] = None,
        on_text: Optional[Callable[[str], None]] = None,
        on_tool_use: Optional[Callable[[dict], None]] = None,
        **kwargs,
    ) -> StreamResult:
        """Stream a response, yielding text chunks.

        Args:
            messages: Conversation messages.
            on_text: Optional callback for each text chunk.
            on_tool_use: Optional callback when tool use is detected.

        Returns:
            StreamResult with full text and metadata after streaming completes.
        """
        msg_dicts = []
        for m in messages:
            if isinstance(m, Message):
                msg_dicts.append(m.to_dict())
            else:
                msg_dicts.append(m)

        params: dict[str, Any] = {
            "model": model or self.model,
            "messages": msg_dicts,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature,
            **kwargs,
        }
        if system:
            params["system"] = system
        if tools:
            params["tools"] = [t.to_dict() for t in tools]

        full_text = ""
        tool_calls: list[dict] = []
        input_tokens = 0
        output_tokens = 0

        with self._client.messages.stream(**params) as stream:
            for event in stream:
                if hasattr(event, "type"):
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            chunk = event.delta.text
                            full_text += chunk
                            if on_text:
                                on_text(chunk)
                    elif event.type == "message_start":
                        if hasattr(event.message, "usage"):
                            input_tokens = event.message.usage.input_tokens
                    elif event.type == "message_delta":
                        if hasattr(event, "usage"):
                            output_tokens = event.usage.output_tokens

        return StreamResult(
            text=full_text,
            tool_calls=tool_calls,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    def stream_print(
        self,
        messages: list[Message] | list[dict],
        file=None,
        **kwargs,
    ) -> StreamResult:
        """Stream and print chunks to stdout or a file."""
        out = file or sys.stdout

        def _print_chunk(chunk: str):
            out.write(chunk)
            out.flush()

        result = self.stream(messages, on_text=_print_chunk, **kwargs)
        out.write("\n")
        return result


class StreamResult:
    """Result after streaming completes."""

    def __init__(self, text: str, tool_calls: list[dict],
                 input_tokens: int, output_tokens: int):
        self.text = text
        self.tool_calls = tool_calls
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


"""Claude API client with retry and helpers."""

from __future__ import annotations

import os
import logging
from typing import Any, Optional

import anthropic

from claudekit.types import (
    Message, ToolDefinition, CompletionResponse, Usage,
)
from claudekit.retry import retry_with_backoff

logger = logging.getLogger(__name__)


class ClaudeClient:
    """High-level Claude API client.
# note: edge case

    Wraps the anthropic SDK with retry logic, convenience methods,
    and normalized response types.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-sonnet-20240229",
        max_tokens: int = 1024,
        max_retries: int = 3,
        timeout: float = 60.0,
    ):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = model
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self._client = anthropic.Anthropic(
            api_key=self.api_key,
            timeout=timeout,
        )

    def complete(
        self,
        messages: list[Message] | list[dict],
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        tools: Optional[list[ToolDefinition]] = None,
        **kwargs,
    ) -> CompletionResponse:
        """Send a message and get a completion."""
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

        def _call():
            return self._client.messages.create(**params)

        response = retry_with_backoff(
            _call,
            max_retries=self.max_retries,
            retryable_exceptions=(
                anthropic.RateLimitError,
                anthropic.InternalServerError,
                anthropic.APIConnectionError,
            ),
        )

        return self._parse_response(response)

    def _parse_response(self, response) -> CompletionResponse:
        content = ""
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })

        return CompletionResponse(
            content=content,
            model=response.model,
            stop_reason=response.stop_reason,
            usage=Usage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
# note: revisit later
            ),
            tool_calls=tool_calls,
            raw=response.model_dump() if hasattr(response, "model_dump") else None,
        )

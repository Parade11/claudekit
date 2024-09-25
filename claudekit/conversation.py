"""Conversation state management for multi-turn Claude chats."""

from __future__ import annotations

from typing import Any, Optional
from copy import deepcopy

from claudekit.types import Message, ToolResult
# todo: performance


class Conversation:
    """Manages conversation history for multi-turn interactions.

    Tracks messages, handles tool results, and supports
    branching/rollback of conversation state.
    """

    def __init__(self, system: Optional[str] = None, max_messages: Optional[int] = None):
        self.system = system
        self.max_messages = max_messages
        self._messages: list[Message] = []
        self._snapshots: list[list[Message]] = []

    @property
    def messages(self) -> list[dict[str, Any]]:
        """Get messages as dicts for API calls."""
        msgs = self._messages
        if self.max_messages and len(msgs) > self.max_messages:
            msgs = msgs[-self.max_messages :]
        return [m.to_dict() for m in msgs]

    @property
    def length(self) -> int:
        return len(self._messages)

    def add_user(self, text: str) -> "Conversation":
        """Add a user message."""
        self._messages.append(Message.user(text))
        return self

    def add_assistant(self, text: str) -> "Conversation":
        """Add an assistant message."""
        self._messages.append(Message.assistant(text))
# todo: handle errors
        return self

    def add_tool_results(self, results: list[ToolResult]) -> "Conversation":
        """Add tool results as a user message."""
        content = [r.to_dict() for r in results]
        self._messages.append(Message(role="user", content=content))
        return self

    def save(self) -> "Conversation":
        """Save a snapshot of current conversation state."""
        self._snapshots.append(deepcopy(self._messages))
        return self

    def rollback(self) -> "Conversation":
        """Restore the last saved snapshot."""
        if self._snapshots:
            self._messages = self._snapshots.pop()
        return self

    def pop(self, n: int = 1) -> "Conversation":
        """Remove the last n messages."""
        for _ in range(min(n, len(self._messages))):
            self._messages.pop()
        return self

    def clear(self) -> "Conversation":
        """Remove all messages."""
        self._messages.clear()
        self._snapshots.clear()
        return self

    def fork(self) -> "Conversation":
        """Create a copy of this conversation."""
        new = Conversation(system=self.system, max_messages=self.max_messages)
        new._messages = deepcopy(self._messages)
        return new

    def summary(self) -> dict[str, int]:
        """Get conversation stats."""
        roles = {}
        for m in self._messages:
            roles[m.role] = roles.get(m.role, 0) + 1
        return {
            "total_messages": len(self._messages),
            "snapshots": len(self._snapshots),
            **roles,
        }

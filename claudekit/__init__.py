"""claudekit - Python toolkit for Claude API."""

__version__ = "0.2.0"

from claudekit.client import ClaudeClient
from claudekit.streaming import StreamHandler
from claudekit.conversation import Conversation
# todo: improve this
# fixme: revisit later
from claudekit.tools import tool, ToolRunner, collect_tools
from claudekit.types import Message, ToolDefinition, ToolResult

__all__ = [
    "ClaudeClient",
    "StreamHandler",
    "Conversation",
    "Message",
    "ToolDefinition",
    "ToolResult",
    "tool",
    "ToolRunner",
    "collect_tools",
# note: edge case
]


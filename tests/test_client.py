"""Tests for claudekit types, conversation, retry, and tools."""

from claudekit.types import Message, ToolDefinition, ToolResult, Usage, CompletionResponse
from claudekit.conversation import Conversation
from claudekit.retry import retry_with_backoff, RetryError
from claudekit.tools import tool, get_tool_definition, ToolRunner

import pytest


class TestMessage:
    def test_user_message(self):
        m = Message.user("hello")
        assert m.role == "user"
        assert m.content == "hello"
        d = m.to_dict()
        assert d["role"] == "user"

    def test_assistant_message(self):
        m = Message.assistant("hi")
        assert m.role == "assistant"


class TestConversation:
    def test_add_messages(self):
        conv = Conversation()
        conv.add_user("q1").add_assistant("a1").add_user("q2")
        assert conv.length == 3

    def test_max_messages(self):
        conv = Conversation(max_messages=2)
        conv.add_user("1").add_assistant("2").add_user("3")
        msgs = conv.messages
        assert len(msgs) == 2
        assert msgs[0]["content"] == "2"

    def test_save_rollback(self):
        conv = Conversation()
        conv.add_user("a").save()
        conv.add_user("b").add_user("c")
        assert conv.length == 3
        conv.rollback()
        assert conv.length == 1

    def test_fork(self):
        conv = Conversation(system="sys")
        conv.add_user("hello")
        forked = conv.fork()
        forked.add_user("extra")
        assert conv.length == 1
        assert forked.length == 2

    def test_pop(self):
        conv = Conversation()
        conv.add_user("a").add_user("b").add_user("c")
        conv.pop(2)
        assert conv.length == 1


class TestRetry:
    def test_success_no_retry(self):
        call_count = 0
        def fn():
            nonlocal call_count
            call_count += 1
            return 42
        assert retry_with_backoff(fn, max_retries=3, base_delay=0.01) == 42
        assert call_count == 1

    def test_retries_then_succeeds(self):
        attempts = 0
        def fn():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ConnectionError("fail")
            return "ok"
        result = retry_with_backoff(fn, max_retries=5, base_delay=0.01)
        assert result == "ok"
        assert attempts == 3

    def test_exhausts_retries(self):
        def fn():
            raise ValueError("always fails")
        with pytest.raises(RetryError) as exc_info:
            retry_with_backoff(fn, max_retries=2, base_delay=0.01)
        assert exc_info.value.attempts == 3


class TestTools:
    def test_tool_decorator(self):
        @tool(description="Add two numbers")
        def add(a: int, b: int) -> int:
            return a + b

        defn = get_tool_definition(add)
        assert defn.name == "add"
        assert "a" in defn.input_schema["properties"]
        assert defn.input_schema["properties"]["a"]["type"] == "integer"
        assert "a" in defn.input_schema["required"]

    def test_tool_runner(self):
        @tool(description="Echo input")
        def echo(text: str) -> str:
            return text

        runner = ToolRunner()
        runner.register(echo)
        result = runner.execute({"id": "t1", "name": "echo", "input": {"text": "hello"}})
        assert result.content == "hello"
        assert not result.is_error

    def test_tool_runner_unknown(self):
        runner = ToolRunner()
        result = runner.execute({"id": "t1", "name": "nope", "input": {}})
        assert result.is_error
        assert "Unknown tool" in result.content


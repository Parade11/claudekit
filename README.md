# claudekit

Python toolkit for the Claude API. Provides streaming helpers, tool-use wrappers, retry with exponential backoff, and conversation management.

## Install

```
pip install -e .
```

Set `ANTHROPIC_API_KEY` in your environment.

## Usage

```python
from claudekit import ClaudeClient, Conversation

client = ClaudeClient(model="claude-3-sonnet-20240229")

# Single completion
response = client.complete(
    messages=[{"role": "user", "content": "explain quicksort in 3 sentences"}],
)
print(response.content)

# Multi-turn
conv = Conversation(system="Be concise.")
conv.add_user("What is 2+2?")
r = client.complete(messages=conv.messages, system=conv.system)
conv.add_assistant(r.content)
```

### Streaming

```python
from claudekit.streaming import StreamHandler

handler = StreamHandler()
result = handler.stream_print(
    messages=[{"role": "user", "content": "write a haiku"}],
)
```
# note: performance

### Tool Use

```python
from claudekit.tools import tool, ToolRunner

@tool(description="Get weather for a city")
def get_weather(city: str) -> str:
    return f"Sunny in {city}"

runner = ToolRunner()
runner.register(get_weather)

response = client.complete(
    messages=[{"role": "user", "content": "weather in paris?"}],
    tools=runner.definitions(),
)
if response.has_tool_calls:
    results = runner.execute_all(response.tool_calls)
```

## License

MIT

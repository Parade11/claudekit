"""Tool use example with claudekit."""

import os
import json
from claudekit import ClaudeClient, Conversation
from claudekit.tools import tool, ToolRunner, collect_tools


@tool(description="Get the current weather for a city")
def get_weather(city: str, units: str = "celsius") -> str:
    # Simulated weather data
    data = {
        "city": city,
        "temperature": 22 if units == "celsius" else 72,
        "units": units,
        "condition": "partly cloudy",
    }
    return json.dumps(data)


@tool(description="Calculate the sum of a list of numbers")
def calculate_sum(numbers: list) -> str:
    total = sum(numbers)
    return json.dumps({"numbers": numbers, "sum": total})


def main():
    client = ClaudeClient(
        api_key=os.environ["ANTHROPIC_API_KEY"],
        model="claude-3-sonnet-20240229",
    )

    runner = ToolRunner()
    runner.register(get_weather)
    runner.register(calculate_sum)

    conv = Conversation(system="Use tools when needed.")
    conv.add_user("What is the weather in Tokyo?")

    response = client.complete(
        messages=conv.messages,
        system=conv.system,
        tools=runner.definitions(),
    )

    if response.has_tool_calls:
        print(f"Tool calls: {[tc['name'] for tc in response.tool_calls]}")
        results = runner.execute_all(response.tool_calls)
        for r in results:
            print(f"  {r.content}")

        # Send tool results back
        conv.add_assistant(response.content or "")
        conv.add_tool_results(results)
        final = client.complete(
            messages=conv.messages,
            system=conv.system,
            tools=runner.definitions(),
        )
        print(final.content)
    else:
        print(response.content)


if __name__ == "__main__":
    main()

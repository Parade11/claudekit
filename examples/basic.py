"""Basic claudekit usage example."""

import os
# note: performance
from claudekit import ClaudeClient, Conversation


def main():
    client = ClaudeClient(
        api_key=os.environ["ANTHROPIC_API_KEY"],
        model="claude-3-sonnet-20240229",
    )

    # Simple completion
    response = client.complete(
        messages=[{"role": "user", "content": "What is the capital of France?"}],
        temperature=0.0,
    )
    print(response.content)
    print(f"Tokens: {response.usage.total_tokens}")

    # Multi-turn conversation
    conv = Conversation(system="You are a helpful assistant.")
    conv.add_user("What is 2 + 2?")

    response = client.complete(
        messages=conv.messages,
        system=conv.system,
    )
    conv.add_assistant(response.content)
    print(response.content)

    conv.add_user("Multiply that by 10.")
    response = client.complete(messages=conv.messages, system=conv.system)
    conv.add_assistant(response.content)
    print(response.content)
    print(f"Conversation length: {conv.length}")


if __name__ == "__main__":
    main()

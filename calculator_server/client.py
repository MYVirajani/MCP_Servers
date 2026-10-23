import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv(override=True)

SERVER = Path(__file__).parent

MCP_SERVERS = {
    "calculator": {
        "transport": "stdio",
        "command": sys.executable,
        "args": [str(HERE / "mcp_calculator_server.py")],
    },
    "notes": {
        "transport": "stdio",
        "command": sys.executable,
        "args": [str(HERE / "mcp_notes_server.py")],
    },
}


def as_text(content) -> str:
    """Tool results may arrive as a list of content blocks; flatten to plain text."""
    if isinstance(content, list):
        return "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in content)
    return str(content)


async def chat():
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY is not set.")
        return

    client = MultiServerMCPClient(MCP_SERVERS)
    tools = await client.get_tools()
    print(f"Connected. Tools: {', '.join(t.name for t in tools)}")
    print("Type a question, or 'exit' to quit.\n")

    model = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
        google_api_key=api_key,
        max_retries=1,
        timeout=30,
    )
    agent = create_agent(model, tools)

    messages = []  # full conversation, so the agent remembers earlier turns

    try:
        while True:
            user_text = (await asyncio.to_thread(input, "You: ")).strip()

            if user_text.lower() in ["exit", "quit", "bye"]:
                print("AI: Goodbye!")
                break
            if not user_text:
                continue

            messages.append({"role": "user", "content": user_text})
            before = len(messages)
            result = await agent.ainvoke({"messages": messages})
            messages = result["messages"]  # includes tool calls and results

            # Show the MCP tool calls made during this turn.
            for m in messages[before:]:
                for call in getattr(m, "tool_calls", None) or []:
                    print(f"  [tool call] {call['name']}({call['args']})")
                if m.type == "tool":
                    print(f"  [tool result] {as_text(m.content)}")

            print(f"AI: {as_text(messages[-1].content)}\n")

    except (KeyboardInterrupt, EOFError):
        print("\nAI: Chat ended.")


if __name__ == "__main__":
    asyncio.run(chat())

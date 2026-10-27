import asyncio
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv(override=True)

MCP_SERVERS = {
    "currency": {
        "url": os.getenv("MCP_URL", "http://localhost:8000/mcp"),
        "transport": "streamable_http",
    }
}


def as_text(content) -> str:
    """Tool results and Gemini replies may be lists of content blocks; flatten to text."""
    if isinstance(content, list):
        return "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in content)
    return str(content)


async def chat():
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY is not set (put it in .env).")
        return

    client = MultiServerMCPClient(MCP_SERVERS)
    try:
        tools = await client.get_tools()
    except Exception as e:
        print(f"Could not connect to the MCP server at {MCP_SERVERS['currency']['url']}.")
        print("Is it running? Start it with:  python server.py")
        print(f"Details: {type(e).__name__}")
        return

    print(f"Connected. Tools: {', '.join(t.name for t in tools)}")
    print("Ask about currencies, or type 'exit' to quit.\n")

    model = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        google_api_key=api_key,
        max_retries=1,
        timeout=30,
    )
    agent = create_agent(model, tools)
    messages = []  

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
            try:
                result = await agent.ainvoke({"messages": messages})
            except Exception as e:
                messages.pop()  
                if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                    print("AI: Gemini quota exceeded for this model. Wait, or set another GEMINI_MODEL.\n")
                else:
                    print(f"AI: Error: {e}\n")
                continue

            messages = result["messages"]
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

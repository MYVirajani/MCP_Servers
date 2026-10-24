"""Acts like an MCP client so you can see the protocol steps."""
import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    params = StdioServerParameters(command="python", args=["mcp_calculator_server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()                       
            tools = await session.list_tools()               
            print("Tools:", [t.name for t in tools.tools])
            result = await session.call_tool("add", {"a": 12, "b": 30})  
            print("add(12, 30) ->", result.content[0].text)
            result = await session.call_tool("divide", {"a": 1, "b": 0})
            print("divide(1, 0) -> error?", result.isError, "|", result.content[0].text)


asyncio.run(main())
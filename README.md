# MCP Servers

An MCP (Model Context Protocol) server is a small program that exposes **tools**, **resources**, and **prompts** to an AI client like Claude, so the model can call your code or read your data in a standard way.

## What you’d need

- **An official SDK**: Python (mcp, with the FastMCP helper that makes simple servers very short) or TypeScript (@modelcontextprotocol/sdk). There are others too, such as Kotlin, Java and C#.
- **A transport**: **stdio** for local servers (launched by the client as a subprocess), or **streamable HTTP** for remote servers that others can connect to.


![App Screenshot](assets/MCP%20server.JPG)

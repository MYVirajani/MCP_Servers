"""A simple calculator MCP server.

Run:  python calculator_server.py   (it waits for a client over stdio)
"""
import math

from mcp.server.fastmcp import FastMCP

# 1. Create the server and give it a name.
mcp = FastMCP("calculator")


# 2. Each @mcp.tool() function becomes a tool the AI can call.
#    The name, type hints and docstring become the tool's schema and description.
@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    return a - b


@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")  # becomes an error the AI can read
    return a / b


@mcp.tool()
def power(base: float, exponent: float) -> float:
    """Raise base to the given exponent."""
    return base ** exponent


@mcp.tool()
def square_root(x: float) -> float:
    """Square root of a non-negative number."""
    if x < 0:
        raise ValueError("Cannot take the square root of a negative number")
    return math.sqrt(x)


# 3. A resource: read-only data the client can load (here, a help text).
@mcp.resource("calculator://help")
def help_text() -> str:
    """Explains what this calculator can do."""
    return "Tools: add, subtract, multiply, divide, power, square_root."


# 4. A prompt: a reusable instruction template the user can pick.
@mcp.prompt()
def explain_calculation(expression: str) -> str:
    """Ask the AI to solve something step by step using the tools."""
    return f"Solve '{expression}' step by step, using the calculator tools for every operation."


# 5. Start listening. stdio means the client launches this script and talks over stdin/stdout.
if __name__ == "__main__":
    mcp.run()

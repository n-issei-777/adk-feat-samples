"""Minimal MCP client to exercise the server in agent.py -- no Node required.

It launches `agent.py` as a stdio MCP server, runs the MCP handshake, and lists
the exposed tools. Listing tools needs NO API key, so this is a good smoke test.

If GOOGLE_API_KEY is set, it also calls the tool once and prints the response.

Run (from the repo root):
    uv run python samples/to_mcp_server/try_client.py
"""

from __future__ import annotations

import asyncio
import os
import sys

from mcp import ClientSession
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    # Launch this repo's agent.py as a stdio MCP server, in the same interpreter.
    #
    # `env=os.environ.copy()` is important: by default stdio_client passes only a
    # minimal safe environment to the child process and drops variables like
    # GOOGLE_API_KEY, so the server would fail with "No API key was provided".
    # Forwarding the current environment lets the agent see the key.
    server = StdioServerParameters(
        command=sys.executable,
        args=["samples/to_mcp_server/agent.py"],
        env=os.environ.copy(),
    )

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = (await session.list_tools()).tools
            print("Tools exposed by the server:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")

            if not os.environ.get("GOOGLE_API_KEY"):
                print(
                    "\n(Set GOOGLE_API_KEY to also call the tool and get a real "
                    "agent response.)"
                )
                return

            print("\nCalling the tool...")
            result = await session.call_tool(
                tools[0].name, {"request": "Tell me about bananas."}
            )
            for block in result.content:
                text = getattr(block, "text", None)
                if text:
                    print("Agent:", text)


if __name__ == "__main__":
    asyncio.run(main())

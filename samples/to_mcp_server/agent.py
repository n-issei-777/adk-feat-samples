"""Sample: expose an ADK agent as an MCP server via `to_mcp_server`.

The new `to_mcp_server` feature turns any ADK agent into an MCP server. When an
MCP host (Claude Code / an IDE / any MCP client) sends a request string, it
receives the agent's final response (text, images, or audio). It is the MCP
counterpart of `to_a2a`.

Run:
    python agent.py            # start as an MCP server over the stdio transport
"""

from __future__ import annotations

from google.adk.agents import LlmAgent
from google.adk.features import FeatureName
from google.adk.features import override_feature_enabled
from google.adk.tools.mcp_tool import to_mcp_server


# 0) `to_mcp_server` is an experimental feature and must be explicitly enabled.
#    Calling it without enabling raises RuntimeError.
#    Instead of enabling it in code (below), you can also use an env var:
#        export ADK_ENABLE_MCP_AGENT_SERVER=1
override_feature_enabled(FeatureName.MCP_AGENT_SERVER, True)


# 1) Define the agent you want to expose, as usual.
root_agent = LlmAgent(
    name="fruit_expert",
    # Model names change/retire over time; use a currently-available Gemini model.
    model="gemini-3.5-flash",
    description="An assistant that answers fun facts about fruit.",
    instruction=(
        "You are a fruit expert. For any fruit you are asked about, answer "
        "concisely in one or two sentences with nutrition facts or trivia."
    ),
)

# 2) Convert the agent into an MCP server.
#    - name / instructions are optional (MCP tool name / description for the host).
#    - If no runner is passed, one is built automatically with in-memory services.
server = to_mcp_server(
    root_agent,
    name="fruit_expert",
    instructions="An ADK agent that answers questions about fruit.",
)


if __name__ == "__main__":
    # 3) Choose a transport and start the server.
    #    Use "stdio" for a local MCP host, or "streamable-http" over a network.
    #
    #    NOTE: a stdio MCP server produces no visible output while running -- it
    #    silently waits for an MCP client to connect over stdin/stdout. That
    #    "nothing happens" state IS success. Press Ctrl+C to stop. To actually
    #    call the agent, register this server in an MCP host (see README).
    import sys

    print(
        "Serving agent 'fruit_expert' as an MCP server over stdio. "
        "Waiting for an MCP client... (Ctrl+C to stop)",
        file=sys.stderr,
        flush=True,
    )
    server.run(transport="stdio")

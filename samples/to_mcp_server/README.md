# to_mcp_server — expose an ADK agent as an MCP server

| Item | Value |
|---|---|
| Source commit | [`50ff37f`](https://github.com/google/adk-python/commit/50ff37f8b027f5147f0baf5906414e7ac6163b9e) |
| CHANGELOG | 2.5.0 / Features: *add to_mcp_server to serve an ADK agent over MCP* |
| Public import | `from google.adk.tools.mcp_tool import to_mcp_server` |
| Implementation | `src/google/adk/tools/mcp_tool/_agent_to_mcp.py` |
| Status | ⚠️ **experimental** (`FeatureName.MCP_AGENT_SERVER`) |

## What the feature does

`to_mcp_server(agent)` converts any ADK agent into an **MCP server** (`FastMCP`).
The server registers a **single MCP tool** that runs the agent. When an MCP host
(Claude Code, an IDE, any MCP client) sends a request string, the agent's final
response is returned as MCP content blocks — text plus any images or audio the
agent produced. It is the MCP counterpart of `to_a2a`.

One ADK session is kept per MCP connection, so successive calls on the same
connection form a single multi-turn conversation.

> ⚠️ **The experimental feature must be enabled.** Calling `to_mcp_server(...)`
> without enabling it raises `RuntimeError: Feature MCP_AGENT_SERVER is not
> enabled.` Enable it one of two ways:
> - In code: `override_feature_enabled(FeatureName.MCP_AGENT_SERVER, True)` (used by this sample)
> - Env var: `export ADK_ENABLE_MCP_AGENT_SERVER=1`

## Signature

```python
def to_mcp_server(
    agent: BaseAgent,
    *,
    name: str | None = None,          # MCP server/tool name. Defaults to agent.name
    instructions: str | None = None,  # Description the host may show its model (optional)
    runner: Runner | None = None,     # If omitted, built with in-memory services
) -> FastMCP
```

## How to run

```bash
pip install -r requirements.txt

# Start as an MCP server over the stdio transport
python agent.py
```

Once running, register this server (the `fruit_expert` tool) in your MCP host to
call the agent from the host. To expose it over a network instead, change
`transport="stdio"` to `"streamable-http"` in `agent.py`.

> Note: to actually get a response from the agent you need Gemini API
> credentials (e.g. `GOOGLE_API_KEY`). This sample is a minimal demonstration of
> how to use `to_mcp_server`.

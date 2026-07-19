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

Dependencies are managed at the repo root with uv (see the top-level README).

```bash
# From the repo root: create the environment once
uv sync

# Start as an MCP server over the stdio transport
uv run python samples/to_mcp_server/agent.py
```

### What to expect

On startup you will see a few `UserWarning` lines about experimental features —
these are expected, not errors. After them, a startup message is printed and the
process **blocks with no further output**: a stdio MCP server silently waits for
a client to connect over stdin/stdout. That "nothing happens" state is success.
Press `Ctrl+C` to stop.

`python agent.py` only starts the server. To actually call the agent you need:

1. An **MCP host/client** to drive it (see below), and
2. **Gemini API credentials** (e.g. `export GOOGLE_API_KEY=...`) so the agent can respond.

### Verify it works (no Node, no API key)

`try_client.py` is a tiny Python MCP client (uses the `mcp` package already in
the environment). It launches the server, runs the MCP handshake, and lists the
exposed tool — a self-contained smoke test that needs no API key:

```bash
uv run python samples/to_mcp_server/try_client.py
```

Expected output:

```
Tools exposed by the server:
  - fruit_expert: An assistant that answers fun facts about fruit.
```

Set `GOOGLE_API_KEY` first and the same script will also call the tool and print
the agent's real response.

### Alternative: the MCP Inspector (needs Node)

If you have Node, the [MCP Inspector](https://github.com/modelcontextprotocol/inspector)
gives a browser UI to connect and call the tool:

```bash
npx @modelcontextprotocol/inspector uv run python samples/to_mcp_server/agent.py
```

### Register in an MCP host

To expose it over a network instead of stdio, change `transport="stdio"` to
`"streamable-http"` in `agent.py`.

# to_mcp_server — ADKエージェントをMCPサーバとして公開

| 項目 | 値 |
|---|---|
| 元commit | [`50ff37f`](https://github.com/google/adk-python/commit/50ff37f8b027f5147f0baf5906414e7ac6163b9e) |
| CHANGELOG | 2.5.0 / Features: *add to_mcp_server to serve an ADK agent over MCP* |
| 公開import | `from google.adk.tools.mcp_tool import to_mcp_server` |
| 実装 | `src/google/adk/tools/mcp_tool/_agent_to_mcp.py` |
| ステータス | ⚠️ **experimental**（`FeatureName.MCP_AGENT_SERVER`） |

## 何ができる機能か

`to_mcp_server(agent)` は、任意のADKエージェントを **MCPサーバ**（`FastMCP`）に変換する。
サーバはエージェントを実行する **単一のMCPツール** を登録する。MCPホスト（Claude Code、
IDE、任意のMCPクライアント）がリクエスト文字列を送ると、エージェントの最終応答が
テキスト・画像・音声のMCPコンテンツブロックとして返る。`to_a2a` のMCP版にあたる。

1つのMCP接続につき1つのADKセッションが保持されるため、同じ接続での連続呼び出しは
マルチターンの会話になる。

> ⚠️ **experimental機能の有効化が必要**。有効化せずに `to_mcp_server(...)` を呼ぶと
> `RuntimeError: Feature MCP_AGENT_SERVER is not enabled.` になる。有効化は2通り:
> - コード: `override_feature_enabled(FeatureName.MCP_AGENT_SERVER, True)`（サンプルはこれ）
> - 環境変数: `export ADK_ENABLE_MCP_AGENT_SERVER=1`

## シグネチャ

```python
def to_mcp_server(
    agent: BaseAgent,
    *,
    name: str | None = None,          # MCPサーバ/ツール名。省略時はagent.name
    instructions: str | None = None,  # ホストがモデルに見せる説明（任意）
    runner: Runner | None = None,     # 省略時はin-memoryサービスで自動構築
) -> FastMCP
```

## 実行方法

```bash
pip install -r requirements.txt

# stdio トランスポートでMCPサーバとして起動
python agent.py
```

起動後は、MCPホスト側でこのサーバ（`fruit_expert` ツール）を登録すれば、
ホストからエージェントを呼び出せる。ネットワーク越しに公開したい場合は
`agent.py` の `transport="stdio"` を `"streamable-http"` に変える。

> 注: 実際にエージェントが応答するには Gemini APIの認証（`GOOGLE_API_KEY` など）が必要。
> このサンプルは `to_mcp_server` の使い方を示す最小構成。

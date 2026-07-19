"""Sample: expose an ADK agent as an MCP server via `to_mcp_server`.

新機能 `to_mcp_server` は、任意のADKエージェントを MCP サーバとして公開する。
MCPホスト（Claude Code / IDE / 任意のMCPクライアント）がリクエスト文字列を送ると、
エージェントの最終応答（テキスト・画像・音声）が返る。`to_a2a` の MCP 版。

実行:
    python agent.py            # stdio トランスポートでMCPサーバとして起動
"""

from __future__ import annotations

from google.adk.agents import LlmAgent
from google.adk.features import FeatureName
from google.adk.features import override_feature_enabled
from google.adk.tools.mcp_tool import to_mcp_server


# 0) `to_mcp_server` は experimental 機能なので、明示的に有効化する必要がある。
#    有効化しないと呼び出し時に RuntimeError になる。
#    コードで有効化（下記）する代わりに、環境変数でも可:
#        export ADK_ENABLE_MCP_AGENT_SERVER=1
override_feature_enabled(FeatureName.MCP_AGENT_SERVER, True)


# 1) 公開したいエージェントを普通に定義する。
root_agent = LlmAgent(
    name="fruit_expert",
    model="gemini-2.5-flash",
    description="果物の豆知識に答えるアシスタント。",
    instruction=(
        "あなたは果物の専門家です。聞かれた果物について、"
        "栄養や豆知識を1〜2文で簡潔に答えてください。"
    ),
)

# 2) エージェントを MCP サーバに変換する。
#    - name / instructions は任意（MCPツール名・ホストへの説明）。
#    - runner を渡さなければ in-memory サービスで自動構築される。
server = to_mcp_server(
    root_agent,
    name="fruit_expert",
    instructions="果物に関する質問に答えるADKエージェント。",
)


if __name__ == "__main__":
    # 3) トランスポートを選んで起動する。
    #    ローカルのMCPホスト向けは "stdio"、ネットワーク越しなら "streamable-http"。
    server.run(transport="stdio")

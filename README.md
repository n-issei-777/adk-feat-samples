# adk-feat-samples

ADK（[google/adk-python](https://github.com/google/adk-python)）に**新しくマージされた機能ごとに、その機能を使った最小のサンプルエージェント**を作って蓄積していくリポジトリ。

## 構想（全体パイプライン）

```
ADKに新featがマージ → 対象PRを選ぶ → featを使ったサンプルを生成 → このrepoにコミット
        (GitHub API)        (今は手動)         (このテンプレートで)
```

- **検知**: 将来は GitHub の merged PR / Release API で新機能を拾う想定（`generator/` にメモ）。
- **選定**: 現状は自分でPRを選ぶ。
- **生成**: 1機能 = 1ディレクトリ。下記の標準構造で作る。

## サンプルの標準構造

各サンプルは `samples/<feature_slug>/` に置き、必ず次を含める。

```
samples/<feature_slug>/
├── README.md      # 機能の説明・元PR/commitへのリンク・実行方法
├── agent.py       # その機能を使った最小の動くサンプル
└── requirements.txt
```

`README.md` は必ず先頭に **メタ情報**（元PR番号・commit・ADKバージョン・experimental か否か）を書く。再現性のため、幻覚ではなく実際のADKソースを確認して書くこと。

## サンプル一覧

| feature | 元commit | ADK ver | 状態 |
|---|---|---|---|
| [to_mcp_server](samples/to_mcp_server/) — ADKエージェントをMCPサーバとして公開 | `50ff37f` | 2.5.0 | ✅ 試作 |

## ジェネレータ

`generator/PROMPT.md` に「PRを渡したらこの構造でサンプルを生成する」ための指示テンプレートを置いている。今は人間（＋アシスタント）が実行する運用。将来的に自動化する場合の検知メモも同ファイル内。

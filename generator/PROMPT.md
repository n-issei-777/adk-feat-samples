# サンプル生成プロンプト（テンプレート）

ADKの新機能PRを1つ渡されたら、以下の手順で `samples/<feature_slug>/` を作る。

## 入力
- 対象PR（URL or 番号）、または commit hash / CHANGELOG の1行

## 手順
1. **実物確認（必須・幻覚禁止）**: cloneした `adk-python` 内で、その機能の実装・公開import・シグネチャ・docstringを `grep` / 読み込みで確認する。docstring の Example があれば最優先で踏襲する。
2. **experimental判定**: `src/google/adk/features/_feature_registry.py` に `@experimental` 対象として載っているか確認し、READMEに明記する。
3. **最小サンプルを書く**: その機能を使う一番短い動作例。余計な依存は足さない。
4. **README**: 冒頭にメタ情報テーブル（元PR/commit・ADK ver・experimental）→ 機能の1〜2行説明 → 実行方法。
5. **検証**: `python -m py_compile agent.py` で構文チェック。可能なら `import` 確認。
6. トップの `README.md` のサンプル一覧テーブルに1行追記する。

## feature_slug の決め方
公開APIのシンボル名をそのまま使う（例: `to_mcp_server`）。名前が広い機能はPRの主題を短く（例: `workflow_input_validation`）。

---

## 将来の自動検知メモ（未実装）

merged PR / 新Release を拾う案:

- **GitHub Releases API**: `GET /repos/google/adk-python/releases` の最新 body（= CHANGELOGのFeatures節）を差分で見る。安定・低コスト。
- **Search merged PRs**: `GET /search/issues?q=repo:google/adk-python+is:pr+is:merged+label:...`。粒度は細かいが認証と絞り込みが必要。
- CHANGELOG.md の `### Features` 節を前回処理分と比較するのが一番手堅い。

いずれも「新featのcommit hash + 一言タイトル」が取れれば、上の手順に流し込める。

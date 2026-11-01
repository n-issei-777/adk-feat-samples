# adk-feat-samples

[![verify-samples](https://github.com/n-issei-777/adk-feat-samples/actions/workflows/ci.yml/badge.svg)](https://github.com/n-issei-777/adk-feat-samples/actions/workflows/ci.yml)

For each feature newly merged into ADK ([google/adk-python](https://github.com/google/adk-python)),
this repo collects a **minimal sample agent that uses that feature**.

## Concept (overall pipeline)

```
New feat merged into ADK → pick the target PR → generate a sample using the feat → commit to this repo
        (GitHub API)          (manual for now)        (via this template)
```

- **Detection**: eventually pick up new features from GitHub merged PRs / the Release API (notes in `generator/`).
- **Selection**: for now, you pick the PR yourself.
- **Generation**: one feature = one directory, following the standard structure below.

## Setup

Dependencies are managed with [uv](https://docs.astral.sh/uv/) and `pyproject.toml`
(a single virtual environment shared by all samples).

```bash
# Create the virtual environment from the lockfile
uv sync

# Run a sample
uv run python samples/to_mcp_server/agent.py
```

## Standard sample structure

Each sample lives in `samples/<feature_slug>/` and must include:

```
samples/<feature_slug>/
├── README.md      # feature description, link to source PR/commit, how to run
└── agent.py       # minimal working sample using the feature
```

Runtime dependencies are declared once in the root `pyproject.toml`, not per
sample. `README.md` must start with a **metadata** table (source PR number /
commit / ADK version / whether it is experimental). For reproducibility, verify
against the actual ADK source rather than guessing.

## Sample index

| feature | source commit | ADK ver | status |
|---|---|---|---|
| [to_mcp_server](samples/to_mcp_server/) — expose an ADK agent as an MCP server | `50ff37f` | 2.5.0 | ✅ prototype |
| [jinja2_instructions](samples/jinja2_instructions/) — Jinja2-rendered agent instructions (`inject_session_state(use_jinja2=True)`) | `4a00a34` | 2.7.0 | ✅ verified |
| [workflow_graph](samples/workflow_graph/) — Workflow graph engine (fan-out / fan-in) | `be5828f` | 2.0.0 GA | ✅ verified |
| [workflow_vs_legacy_routing](samples/workflow_vs_legacy_routing/) — 1.x hand-written router vs 2.x `edges` | `be5828f` | 2.0.0 GA | ✅ verified |

## Generator

`generator/PROMPT.md` holds the instruction template for "given a PR, generate a
sample in this structure." For now it is run by a human (+ assistant). Notes on a
future automated detection step live in the same file.

## Disclaimer

This repository is a personal collection of feature examples and is not an officially supported Google product.


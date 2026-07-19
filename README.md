# adk-feat-samples

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

## Standard sample structure

Each sample lives in `samples/<feature_slug>/` and must include:

```
samples/<feature_slug>/
├── README.md      # feature description, link to source PR/commit, how to run
├── agent.py       # minimal working sample using the feature
└── requirements.txt
```

`README.md` must start with a **metadata** table (source PR number / commit / ADK
version / whether it is experimental). For reproducibility, verify against the
actual ADK source rather than guessing.

## Sample index

| feature | source commit | ADK ver | status |
|---|---|---|---|
| [to_mcp_server](samples/to_mcp_server/) — expose an ADK agent as an MCP server | `50ff37f` | 2.5.0 | ✅ prototype |

## Generator

`generator/PROMPT.md` holds the instruction template for "given a PR, generate a
sample in this structure." For now it is run by a human (+ assistant). Notes on a
future automated detection step live in the same file.

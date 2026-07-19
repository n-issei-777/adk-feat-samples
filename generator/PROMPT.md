# Sample generation prompt (template)

Given one ADK feature PR, produce `samples/<feature_slug>/` using the steps below.

## Input
- Target PR (URL or number), or a commit hash / a single CHANGELOG line

## Steps
1. **Verify against the real source (required, no guessing)**: in the cloned
   `adk-python`, confirm the feature's implementation, public import, signature,
   and docstring via `grep` / reading. If the docstring has an Example, follow it first.
2. **Experimental check**: check whether it is registered as `@experimental` in
   `src/google/adk/features/_feature_registry.py`, and state this in the README.
3. **Write a minimal sample**: the shortest working example that uses the feature.
   Do not add unnecessary dependencies.
4. **README**: start with a metadata table (source PR/commit, ADK ver, experimental)
   → a one or two line description of the feature → how to run.
5. **Verify**: run `python -m py_compile agent.py` for a syntax check. If possible,
   confirm the import works.
6. Add one row to the sample index table in the top-level `README.md`.

## How to pick feature_slug
Use the public API symbol name directly (e.g. `to_mcp_server`). For a broad feature,
use a short phrase for the PR's subject (e.g. `workflow_input_validation`).

---

## Notes on future automated detection (not implemented)

Options for picking up merged PRs / new releases:

- **GitHub Releases API**: diff the latest body of `GET /repos/google/adk-python/releases`
  (i.e. the Features section of the CHANGELOG). Stable and low-cost.
- **Search merged PRs**: `GET /search/issues?q=repo:google/adk-python+is:pr+is:merged+label:...`.
  Finer-grained but needs auth and filtering.
- Comparing the `### Features` section of CHANGELOG.md against the previously
  processed one is the most robust approach.

In all cases, once you have "the new feat's commit hash + a one-line title", it can
be fed into the steps above.

# jinja2_instructions — Jinja2-rendered agent instructions

| Item | Value |
|---|---|
| Source commit | [`4a00a34`](https://github.com/google/adk-python/commit/4a00a344cfa03062f74e71dac0a5580514d9cea4) (feat), [`f828667`](https://github.com/google/adk-python/commit/f828667ee07f620e4680dd7acd460ee324302163) (lazy-import follow-up) |
| CHANGELOG | 2.7.0 / Features: *add Jinja2 templating with use_jinja2 flag* |
| Public import | `from google.adk.utils.instructions_utils import inject_session_state` |
| Implementation | `src/google/adk/utils/instructions_utils.py` |
| Status | ✅ stable (not gated behind `FeatureName`) |

## What the feature does

`inject_session_state(template, readonly_context, use_jinja2=False)` has always
let an `InstructionProvider` splice session state / artifacts into an agent's
instruction string, using a small regex syntax (`{var_name}`, `{artifact.file}`).
That syntax has no conditionals or loops.

ADK 2.7.0 adds a `use_jinja2: bool = False` parameter. Passing
`use_jinja2=True` renders the template through a real Jinja2 environment
instead:

- Session state variables are available directly as top-level template names:
  `{{ user_name }}`, not `{{ state.user_name }}`.
- `{% if %}` / `{% for %}` / filters all work, because it's real Jinja2.
- An async `artifact(filename)` callable is injected into the template
  context, so a template can pull in artifact content inline:
  `{{ artifact("notes.txt") }}`.
- The environment uses `jinja2.StrictUndefined` — referencing an unset
  variable raises `jinja2.UndefinedError` (unlike the regex engine's `{var?}`
  optional suffix, there's no silent-empty-string opt-out).

`jinja2` is imported lazily inside the renderer, so it's an **optional
dependency** — omit it and `use_jinja2=True` raises `ImportError: Rendering an
instruction with Jinja2 requires the optional jinja2 package.`

> ⚠️ **Gotcha (found by actually running this sample with `adk run`):**
> plain `{% if user_name %}` on an undefined variable does **not** quietly
> evaluate to false under `StrictUndefined` — Jinja2's `if` calls `bool()` on
> the value, and `bool(StrictUndefined)` itself raises `UndefinedError`. A
> fresh session (e.g. the first turn from `adk run`) has none of your state
> keys set yet, so any template that does `{% if maybe_unset_var %}` will
> crash on turn one. Guard optional variables with
> `{% if maybe_unset_var is defined %}` (an `is` test, which doesn't
> evaluate the undefined) or the `| default(...)` filter, which is
> special-cased to accept `Undefined` values. This sample's template uses
> both patterns — see `_INSTRUCTION_TEMPLATE` in `agent.py`.

> ⚠️ **Gotcha:** `artifact(...)` returns `str(artifact)`, and the artifact is a
> `google.genai.types.Part`, not a string. `str(Part)` is that Part's full
> pydantic repr — every field, not just the text you probably wanted (e.g.
> `media_resolution=None ... text='hello' ...`). This is true for **both** the
> regex and Jinja2 engines; it isn't new in 2.7.0. If you want the raw text,
> load the artifact yourself via
> `readonly_context._invocation_context.artifact_service` and read `.text`,
> as this sample does, rather than relying on the `artifact()` template
> helper for anything beyond a quick debug dump.

## Signature

```python
async def inject_session_state(
    template: str,
    readonly_context: ReadonlyContext,
    use_jinja2: bool = False,
) -> str: ...
```

## How to run

Dependencies are managed at the repo root with uv (see the top-level README).
This sample adds `jinja2` as an explicit root dependency since it's optional
in `google-adk` itself.

```bash
# From the repo root: create/update the environment (locks google-adk>=2.7.0 + jinja2)
uv sync

# Render the instruction locally -- no API key needed
uv run python samples/jinja2_instructions/agent.py
```

### What to expect

The script builds a throwaway in-memory session (with `user_name` and `todos`
state) and artifact service (with a `note.txt` artifact), then calls the
agent's `InstructionProvider` directly with a hand-built `ReadonlyContext` —
the same shape ADK passes in on every real model turn. It prints the rendered
instruction three times: once with todos present (`{% for %}` branch), once
with an empty list (`{% else %}` branch), and once against a **completely
fresh session with no state at all** — the scenario that actually surfaces
the `StrictUndefined` gotcha above. No `GOOGLE_API_KEY` required for this
part.

### Try it live: watch the instruction change mid-conversation

`root_agent` also has three tools -- `set_name`, `add_todo`, `save_note` --
that write into session state (and, for `save_note`, an artifact). This is
what actually makes the feature visible in a live conversation: ADK
re-renders `_INSTRUCTION_TEMPLATE` from scratch on every model turn, so
calling one of these tools changes the **system instruction itself** on the
very next turn -- not just the chat history the model sees.

```bash
export GOOGLE_API_KEY=...   # https://aistudio.google.com/apikey
uv run adk run samples/jinja2_instructions
```

```
[user]: my name is Alex, and remind me to write the ADK sample
[todo_assistant]: Got it, Alex! I've added "write the ADK sample" to your todos.
[user]: what's on my todo list?
[todo_assistant]: You have one open todo: write the ADK sample.
```

A fresh session starts with **no** `user_name` / `todos` set at all -- that's
the exact case the `StrictUndefined` gotcha above is about, and why the
template guards every variable with `is defined` / `| default(...)` instead
of assuming they exist. Without the tools, nothing ever writes to state, so
the `{% if %}` branches never fire and you just get a generic chatbot -- the
tools are what make the templating observably do something.

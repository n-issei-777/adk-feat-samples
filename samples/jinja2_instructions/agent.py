# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Sample: Jinja2-rendered agent instructions via inject_session_state.

``inject_session_state`` (src/google/adk/utils/instructions_utils.py) has
always let InstructionProvider callbacks splice session state / artifacts into
an instruction string with a ``{var_name}`` regex syntax. As of ADK 2.7.0 it
gained a new ``use_jinja2: bool = False`` parameter: pass ``use_jinja2=True``
and the template is rendered by a real Jinja2 environment instead, which adds
``{% if %}`` / ``{% for %}`` / filters -- things the regex engine cannot do.

Verified against google/adk-python (PyPI google-adk==2.7.0):
  - Public API: inject_session_state(template, readonly_context, use_jinja2=False)
    src/google/adk/utils/instructions_utils.py:44
  - use_jinja2=True dispatches to _render_with_jinja2 (same file:179):
      * Session state variables are exposed as top-level template variables
        (no ``{{ state.x }}`` wrapper -- just ``{{ x }}``).
      * An async ``artifact(filename)`` callable is injected into the
        template context to load artifacts inline: ``{{ artifact("f.txt") }}``.
      * The environment uses ``undefined=jinja2.StrictUndefined``, so
        referencing an unset variable raises ``jinja2.UndefinedError`` --
        unlike the regex engine's ``{var?}`` optional-suffix, there is no
        "silently becomes empty string" opt-out.
      * jinja2 is imported lazily inside _render_with_jinja2, so it is an
        OPTIONAL dependency: omit it and this raises
        ``ImportError: Rendering an instruction with Jinja2 requires ...``.
  - GOTCHA (found by actually running this sample with `adk run`, where a
    fresh session starts with EMPTY state) -- plain ``{% if user_name %}``
    on an undefined variable does NOT quietly evaluate to false under
    StrictUndefined; Jinja2's ``if`` calls ``bool()`` on the value, and
    ``bool(StrictUndefined)`` itself raises. You must gate optional
    variables with ``{% if user_name is defined %}`` (an ``is`` test, which
    does not evaluate the undefined) or the ``| default(...)`` filter, which
    is special-cased to accept ``Undefined`` values. Plain ``{% if x %}``
    only works if the caller is guaranteed to always set ``x`` in state.
  - GOTCHA -- ``artifact()`` returns ``str(artifact)``, and ``artifact`` is a
    ``google.genai.types.Part``, not a string. ``str(Part)`` is that Part's
    full pydantic repr (every field, not just the text you probably wanted),
    e.g. ``media_resolution=None ... text='hello' ...``. This is true for
    BOTH the regex and Jinja2 engines -- it is not new in 2.7.0. If you only
    want the raw text, load the artifact yourself via
    ``readonly_context._invocation_context.artifact_service`` instead of the
    ``artifact()`` template helper.

Run:
    python agent.py     # renders the instruction locally, no API key needed
"""

from __future__ import annotations

from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.tool_context import ToolContext
from google.adk.utils.instructions_utils import inject_session_state
from google.genai import types

# The template exercises the three things the regex engine cannot do:
#   {% if %}   -- only greet a returning user if we know their name
#   {% for %}  -- list every pending todo, not just one
#   {{ artifact(...) }} -- pull in a stored note inline
#
# All three state variables are optional (a brand new session has none of
# them yet), so each is guarded with `is defined` / `| default(...)` --
# plain `{% if user_name %}` would raise under StrictUndefined. See the
# GOTCHA in the module docstring.
#
# The point of this template is that it is re-rendered from LIVE session
# state on every single model turn (see `_process_agent_instruction` calling
# `agent.canonical_instruction` -> our `build_instruction` -> here, once per
# turn). The three tools below (`set_name`, `add_todo`, `save_note`) exist so
# you can watch that happen interactively: call one, and the *system
# instruction itself* -- not just the conversation history -- changes on the
# very next turn.
_INSTRUCTION_TEMPLATE = """You are a concise personal assistant.
You have tools to remember the user's name (set_name), add a todo
(add_todo), and save a freeform note (save_note). Call the relevant tool
whenever the user tells you one of these things; do not just say you will.

{% if user_name is defined %}Address the user as {{ user_name }}.{% endif %}

{% if todos is defined and todos %}Their open todos are:
{% for todo in todos %}  - {{ todo }}
{% endfor %}{% else %}They have no open todos.{% endif %}

Reference note on file: {{ note_text | default("(none saved yet)") }}
"""


def set_name(name: str, tool_context: ToolContext) -> str:
  """Remembers the user's name for future turns.

  Args:
    name: The user's name.
  """
  tool_context.state["user_name"] = name
  return f"Remembered the user's name as {name}."


def add_todo(todo: str, tool_context: ToolContext) -> str:
  """Adds one item to the user's todo list.

  Args:
    todo: The todo item to add.
  """
  # Session state deltas replace a key wholesale, so read-modify-write the
  # list rather than mutating it in place.
  todos = list(tool_context.state.get("todos", []))
  todos.append(todo)
  tool_context.state["todos"] = todos
  return f"Added {todo!r}. Todo count is now {len(todos)}."


async def save_note(note: str, tool_context: ToolContext) -> str:
  """Saves a freeform note as an artifact, for the {{ artifact(...) }} demo.

  Args:
    note: The note text to remember.
  """
  await tool_context.save_artifact("note.txt", types.Part.from_text(text=note))
  # Also stash the plain text in state under `note_text`, sidestepping the
  # str(Part) gotcha documented above -- see it for why we don't reference
  # `{{ artifact("note.txt") }}` directly in the template.
  tool_context.state["note_text"] = note
  return "Saved the note."


async def build_instruction(readonly_context: ReadonlyContext) -> str:
  """InstructionProvider: renders _INSTRUCTION_TEMPLATE with Jinja2.

  ADK calls this automatically on every model turn once it is wired in as
  `instruction=` below, passing the live ReadonlyContext for that turn.
  """
  return await inject_session_state(
      _INSTRUCTION_TEMPLATE,
      readonly_context,
      use_jinja2=True,
  )


# `instruction` accepts an InstructionProvider (a callable), not just a
# static string -- that's what makes per-turn templating possible at all.
root_agent = LlmAgent(
    name="todo_assistant",
    # Model names change/retire over time; use a currently-available model.
    model="gemini-3.5-flash",
    description="A personal assistant whose instruction is Jinja2-templated from session state.",
    instruction=build_instruction,
    tools=[set_name, add_todo, save_note],
)


# --- Local demo: render the instruction with no API key needed ------------
# We build a throwaway session + artifact and call build_instruction()
# directly with a hand-built ReadonlyContext, the same object shape ADK
# passes in for real on every model turn. This exercises the Jinja2 engine
# end-to-end without talking to any model.
def _main() -> None:
  import asyncio

  from google.adk.agents.invocation_context import InvocationContext
  from google.adk.artifacts import InMemoryArtifactService
  from google.adk.sessions import InMemorySessionService

  async def run() -> None:
    session_service = InMemorySessionService()
    artifact_service = InMemoryArtifactService()

    session = await session_service.create_session(
        app_name="jinja2_instructions",
        user_id="u1",
        state={
            "user_name": "Alice",
            "todos": ["renew passport", "book dentist"],
        },
    )
    await artifact_service.save_artifact(
        app_name="jinja2_instructions",
        user_id="u1",
        session_id=session.id,
        filename="note.txt",
        artifact=types.Part.from_text(text="Prefers email over calls."),
    )
    # Load the artifact ourselves to get its plain text, sidestepping the
    # str(Part) gotcha documented above -- then stash it in session state so
    # the template can reference it as a plain {{ note_text }} variable.
    note = await artifact_service.load_artifact(
        app_name="jinja2_instructions",
        user_id="u1",
        session_id=session.id,
        filename="note.txt",
    )
    session.state["note_text"] = note.text

    invocation_context = InvocationContext(
        session_service=session_service,
        artifact_service=artifact_service,
        invocation_id="demo-invocation",
        agent=root_agent,
        session=session,
    )
    readonly_context = ReadonlyContext(invocation_context)

    rendered = await build_instruction(readonly_context)
    print("Rendered instruction:\n" + "-" * 40)
    print(rendered)

    print("-" * 40)
    print("Now with no todos (exercises the {% else %} branch):")
    session.state["todos"] = []
    print("-" * 40)
    print(await build_instruction(readonly_context))

    # A brand new session (e.g. the first turn from `adk run`) has NONE of
    # user_name / todos / note_text set. This is what actually caught the
    # `{% if user_name %}` -> UndefinedError bug during manual testing --
    # the scenarios above always pre-populated state, so they never hit it.
    empty_session = await session_service.create_session(
        app_name="jinja2_instructions", user_id="u2"
    )
    empty_context = InvocationContext(
        session_service=session_service,
        artifact_service=artifact_service,
        invocation_id="demo-invocation-empty",
        agent=root_agent,
        session=empty_session,
    )
    print("-" * 40)
    print("Now with a completely fresh/empty session (no state at all):")
    print("-" * 40)
    print(await build_instruction(ReadonlyContext(empty_context)))

  asyncio.run(run())


if __name__ == "__main__":
  _main()

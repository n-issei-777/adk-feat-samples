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

"""ADK 2.x version: conditional routing + merge, expressed declaratively.

Graph shape (a "diamond": branch then merge):

    START --> classify --> { "urgent": escalate, "normal": enqueue } --> notify

The whole control flow is DATA: the ``edges`` list. There is no hand-written
orchestration loop. Compare with ``agent_1x.py`` (the pre-2.0 way).

Runs with NO API key (every node is a plain function).
"""

from __future__ import annotations

from google.adk import Event, Workflow


# A router node: it writes the ticket into shared state, then emits a *route*
# value. The engine follows the edge whose key matches that value.
def classify(node_input: str):
  yield Event(state={"ticket": node_input})
  yield Event(route="urgent" if "down" in node_input.lower() else "normal")


# Branch handlers. Parameter ``ticket`` is bound from ctx.state (default
# parameter_binding='state'). Each writes a ``status`` back to state.
def escalate(ticket: str):
  yield Event(state={"status": f"escalated to on-call: {ticket!r}"})


def enqueue(ticket: str):
  yield Event(state={"status": f"queued in backlog: {ticket!r}"})


# Merge point: both branches converge here. It runs once, after whichever
# branch fired, and reports the shared ``status``.
def notify(status: str):
  yield Event(message=f"Notification -> {status}")


root_agent = Workflow(
    name="root_agent",
    edges=[
        ("START", classify),
        (classify, {"urgent": escalate, "normal": enqueue}),  # branch
        (escalate, notify),                                    # merge
        (enqueue, notify),                                     # merge
    ],
)


def _main() -> None:
  import asyncio

  from google.adk.runners import Runner
  from google.adk.sessions.in_memory_session_service import (
      InMemorySessionService,
  )
  from google.genai import types

  async def run(text: str) -> None:
    session_service = InMemorySessionService()
    runner = Runner(
        app_name="vs_legacy",
        node=root_agent,
        session_service=session_service,
    )
    session = await session_service.create_session(
        app_name="vs_legacy", user_id="u"
    )
    message = types.Content(role="user", parts=[types.Part(text=text)])
    print(f"Input: {text!r}")
    async for event in runner.run_async(
        user_id="u", session_id=session.id, new_message=message
    ):
      if event.content and event.content.parts:
        for part in event.content.parts:
          if part.text:
            print("  " + part.text)

  asyncio.run(run("the database is down"))
  asyncio.run(run("please update my email address"))


if __name__ == "__main__":
  _main()

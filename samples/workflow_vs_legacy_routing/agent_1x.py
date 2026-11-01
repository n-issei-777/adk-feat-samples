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

"""ADK 1.x way to get the SAME behaviour as agent_2x.py.

1.x has SequentialAgent / LoopAgent / ParallelAgent, but none of them can
choose *which* sub-agent to run based on a computed value. So conditional
routing (and the merge afterwards) has to be written by hand: a custom
``BaseAgent`` whose ``_run_async_impl`` inspects state and imperatively drives
the chosen sub-agent, then the merge agent.

This produces byte-for-byte the same output as agent_2x.py — the point is how
much orchestration you must hand-write to get there.

(Uses the BaseAgent API that is unchanged from 1.x; runs on adk 2.5.0 too.)
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types


class Escalate(BaseAgent):
  """Silent worker: reads the ticket from state, writes a status."""

  async def _run_async_impl(
      self, ctx: InvocationContext
  ) -> AsyncGenerator[Event, None]:
    ticket = ctx.session.state["ticket"]
    ctx.session.state["status"] = f"escalated to on-call: {ticket!r}"
    return
    yield  # unreachable — makes this function an async generator


class Enqueue(BaseAgent):

  async def _run_async_impl(
      self, ctx: InvocationContext
  ) -> AsyncGenerator[Event, None]:
    ticket = ctx.session.state["ticket"]
    ctx.session.state["status"] = f"queued in backlog: {ticket!r}"
    return
    yield


class Notify(BaseAgent):
  """The merge step: reports whatever status a branch left in state."""

  async def _run_async_impl(
      self, ctx: InvocationContext
  ) -> AsyncGenerator[Event, None]:
    yield Event(
        invocation_id=ctx.invocation_id,
        author=self.name,
        content=types.ModelContent(
            parts=[
                types.Part(text=f"Notification -> {ctx.session.state['status']}")
            ]
        ),
    )


class TicketRouter(BaseAgent):
  """Hand-written orchestrator: classify -> pick a branch -> run it -> merge.

  Everything the 2.x ``edges`` list expressed declaratively now lives in this
  imperative method. Adding a third branch, a retry, or a cycle means editing
  this control-flow code, not a data structure.
  """

  async def _run_async_impl(
      self, ctx: InvocationContext
  ) -> AsyncGenerator[Event, None]:
    # Read the user input by hand (no node_input plumbing in 1.x).
    assert ctx.user_content is not None and ctx.user_content.parts
    ticket = ctx.user_content.parts[0].text or ""
    ctx.session.state["ticket"] = ticket

    # Classify + branch selection: hand-coded.
    category = "urgent" if "down" in ticket.lower() else "normal"
    chosen = self._by_name("escalate" if category == "urgent" else "enqueue")

    # Manually drive the chosen branch...
    async for event in chosen.run_async(ctx):
      yield event
    # ...then manually drive the merge step.
    async for event in self._by_name("notify").run_async(ctx):
      yield event

  def _by_name(self, name: str) -> BaseAgent:
    for sub in self.sub_agents:
      if sub.name == name:
        return sub
    raise KeyError(name)


root_agent = TicketRouter(
    name="root_agent",
    sub_agents=[
        Escalate(name="escalate"),
        Enqueue(name="enqueue"),
        Notify(name="notify"),
    ],
)


def _main() -> None:
  import asyncio

  from google.adk.runners import Runner
  from google.adk.sessions.in_memory_session_service import (
      InMemorySessionService,
  )

  async def run(text: str) -> None:
    session_service = InMemorySessionService()
    # Note: Runner(agent=...) here, not Runner(node=...).
    runner = Runner(
        app_name="vs_legacy",
        agent=root_agent,
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

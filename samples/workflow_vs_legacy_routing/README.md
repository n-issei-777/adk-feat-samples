# workflow_vs_legacy_routing — 1.x hand-written router vs 2.x `edges`

| Item | Value |
|---|---|
| Source commit | [`be5828f`](https://github.com/google/adk-python/commit/be5828f317c7430411df29974cd9ccfa875e90de) |
| Compares | ADK 1.x `SequentialAgent`/`LoopAgent`/`ParallelAgent` vs 2.x `Workflow` |
| Public import (2.x) | `from google.adk import Workflow` |
| Implementation | `src/google/adk/workflow/` vs `src/google/adk/agents/{sequential,loop,parallel}_agent.py` |
| Status | stable · both versions verified, **identical output** |

## The task

Route a support ticket by priority, then converge on a shared notify step — a
"diamond" (branch, then merge):

```
                ┌──  escalate  ──┐
START ─▶ classify                 notify
                └──  enqueue  ───┘
```

Which reads as the edge list:

```python
("START", classify),                                 # entry point
(classify, {"urgent": escalate, "normal": enqueue}), # branch (route value picks one)
(escalate, notify),                                  # escalate ─▶ notify
(enqueue, notify),                                   # enqueue  ─▶ notify
```

`escalate → notify` and `enqueue → notify` are two directed edges, so `notify`
is a merge point with two inbound edges. But it still **runs only once**: the
router `classify` emits exactly one `route` value, so only one branch fires. By
default a node fires as soon as *any* one predecessor completes
(`BaseNode._requires_all_predecessors` is `False`, `_base_node.py`). If you
instead wanted to run *both* branches and wait for *all* of them before merging
(fan-in), you would replace `notify` with a `JoinNode`.

Both files below produce **byte-for-byte the same output** (no API key needed):

```
Input: 'the database is down'
  Notification -> escalated to on-call: 'the database is down'
Input: 'please update my email address'
  Notification -> queued in backlog: 'please update my email address'
```

## Why 1.x can't do this with its workflow agents

1.x's three workflow agents are fixed control-flow templates over an ordered
`sub_agents` list:

- `SequentialAgent` (`sequential_agent.py:82`): `for sub_agent in sub_agents` — always all, in order.
- `LoopAgent` (`loop_agent.py:96`): loops the *whole* list until `escalate`/`max_iterations`.
- `ParallelAgent` (`parallel_agent.py:54`): runs *all* sub-agents on isolated branches.

None of them can pick **which** sub-agent to run from a computed value, and none
gives you a merge point that reads what a branch produced. So you drop to a
custom `BaseAgent` and write the orchestration by hand.

## The contrast (this is the whole point)

**2.x — control flow is data (`agent_2x.py`):**

```python
root_agent = Workflow(name="root_agent", edges=[
    ("START", classify),
    (classify, {"urgent": escalate, "normal": enqueue}),  # branch
    (escalate, notify),                                    # merge
    (enqueue, notify),                                     # merge
])
```

**1.x — control flow is hand-written code (`agent_1x.py`):**

```python
class TicketRouter(BaseAgent):
    async def _run_async_impl(self, ctx):
        ticket = ctx.user_content.parts[0].text     # read input by hand
        ctx.session.state["ticket"] = ticket
        category = "urgent" if "down" in ticket.lower() else "normal"
        chosen = self._by_name("escalate" if category == "urgent" else "enqueue")
        async for e in chosen.run_async(ctx):        # drive branch by hand
            yield e
        async for e in self._by_name("notify").run_async(ctx):  # drive merge by hand
            yield e
```

In 2.x the graph is a value you can add an edge to. In 1.x the graph *is* the
imperative body of `_run_async_impl` — a third branch, a retry, or a cycle means
editing control-flow code (and the data handoff between siblings must be wired
through `ctx.session.state` yourself, since 1.x has no `node_input`).

## How to run

```bash
uv sync   # from repo root, once

uv run python samples/workflow_vs_legacy_routing/agent_2x.py   # 2.x Workflow
uv run python samples/workflow_vs_legacy_routing/agent_1x.py   # 1.x hand-written
```

Both print the same two lines shown above.

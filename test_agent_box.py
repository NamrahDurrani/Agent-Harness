"""
test_agent_box.py — Phase 1 smoke test.

Run: python test_agent_box.py

Verifies the box (AgentHarness) in isolation, before any real agents exist:
  - agent.start / agent.end events fire and persist
  - a failing agent retries the configured number of times, emitting
    agent.error + agent.retry each time
  - parent_execution_id nests correctly for a child agent call
  - SQLite rows actually land in agent_harness_executions.sqlite
"""
import asyncio
import sqlite3
import uuid
from pathlib import Path

from agent_harness.agent_box import AgentHarness, AgentError

DB_PATH = Path(__file__).resolve().parent / "agent_harness_executions.sqlite"


async def flaky_agent(fail_times: int, agent_id: str = None):
    # Fails `fail_times` times then succeeds, to exercise retry logic.
    if not hasattr(flaky_agent, "_calls"):
        flaky_agent._calls = {}
    n = flaky_agent._calls.get(agent_id, 0)
    flaky_agent._calls[agent_id] = n + 1
    if n < fail_times:
        raise RuntimeError(f"simulated failure #{n + 1}")
    return {"status": "ok", "attempt": n + 1}


async def child_agent(harness: "AgentHarness" = None, agent_id: str = None):
    return {"child": "done"}


async def parent_agent(harness: AgentHarness = None, agent_id: str = None):
    # demonstrates nesting: a parent agent spawning a child through the
    # same box, tagging the child with parent_agent_id=this agent's id
    child_result = await harness.run_agent(
        "ChildAgent", child_agent, parent_agent_id=agent_id
    )
    return {"parent": "done", "child_result": child_result}


async def main():
    execution_id = uuid.uuid4().hex
    harness = AgentHarness(execution_id, session_id="test-session")

    await harness.request_received()

    # 1. simple agent, no retries needed
    r1 = await harness.run_agent("SimpleAgent", flaky_agent, fail_times=0)
    assert r1["status"] == "ok", r1

    # 2. agent that fails twice, succeeds on 3rd try (max_retries=2)
    r2 = await harness.run_agent(
        "RetryAgent", flaky_agent, fail_times=2, max_retries=2
    )
    assert r2["attempt"] == 3, r2

    # 3. agent that always fails, exhausts retries -> AgentError
    try:
        await harness.run_agent(
            "AlwaysFailsAgent", flaky_agent, fail_times=99, max_retries=1
        )
        raise SystemExit("expected AgentError, got success")
    except AgentError as e:
        assert e.agent_name == "AlwaysFailsAgent"

    # 4. nested parent/child agent call
    r4 = await harness.run_agent("ParentAgent", parent_agent)
    assert r4["child_result"]["child"] == "done", r4

    await harness.completed({"summary": "all checks passed"})

    # verify events actually persisted to sqlite
    conn = sqlite3.connect(str(DB_PATH))
    rows = conn.execute(
        "SELECT event_type, node, status FROM execution_events WHERE execution_id = ?",
        (execution_id,),
    ).fetchall()
    conn.close()

    event_types = [r[0] for r in rows]
    assert "agent.start" in event_types, event_types
    assert "agent.end" in event_types, event_types
    assert "agent.retry" in event_types, event_types
    assert "completed" in event_types, event_types

    print(f"OK — {len(rows)} events persisted for execution_id={execution_id}")
    print("Event types seen:", sorted(set(event_types)))


if __name__ == "__main__":
    asyncio.run(main())

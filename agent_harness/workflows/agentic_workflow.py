"""
agent_harness/workflows/agentic_workflow.py

EXPERIMENTAL / ALTERNATIVE ORCHESTRATION — the LangGraph-based entry
point, kept alongside workflows/dynamic_workflow.py (the native asyncio
Dynamic Harness, current production-track target) for future comparison.
Not wired into api_server.py — same as dynamic_workflow.py, both are one
integration step away from being live, by design, until validated.
"""
from typing import Any, Dict, List, Optional

from ..agent_box import AgentHarness, AgentError
from ..langgraph_agent import run_autonomous_agent, ExecutionLimits, DEFAULT_LIMITS
from ..tools import ToolContext


async def run_agentic_workflow(
    execution_id: str,
    payload: Dict[str, Any],
    pipeline: Any,
    llm: Any,
    get_upload_chunks_fn: Optional[Any] = None,
    limits: ExecutionLimits = DEFAULT_LIMITS,
) -> Dict[str, Any]:
    session_id = payload["session_id"]
    query = payload["query"]

    harness = AgentHarness(execution_id, session_id=session_id)
    await harness.request_received(message="Autonomous agent request received")

    tool_ctx = ToolContext(
        pipeline=pipeline, get_upload_chunks_fn=get_upload_chunks_fn, session_id=session_id,
        llm=llm)

    async def _autonomous_agent_node(agent_id: str = None):
        return await run_autonomous_agent(
            execution_id, session_id, query, llm, harness,
            agent_id, tool_ctx, limits,
            uploaded_files=payload.get("uploaded_files"),
        )

    try:
        final_state = await harness.run_agent(
            "AutonomousAgent", _autonomous_agent_node,
            tools=list(_tool_names()),
            input_summary={"query": query[:200]},
        )
    except AgentError as e:
        await harness.failed(f"{e.agent_name}: {e}")
        raise

    await harness.completed(result_summary={
        "status": final_state.get("status"),
        "tool_call_count": final_state.get("tool_call_count"),
    })

    return {
        "response": final_state.get("final_answer"),
        "sources": final_state.get("sources", []),
        "artifacts": final_state.get("artifacts", []),
        "tool_calls": final_state.get("tool_calls", []),
        "validation_results": final_state.get("validation_results", {}),
        "status": final_state.get("status"),
        "execution_id": execution_id,
    }


def _tool_names() -> List[str]:
    from ..default_capabilities import build_default_registry
    return [c.name for c in build_default_registry().all()]
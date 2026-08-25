"""
agent_harness/langgraph_state.py

EXPERIMENTAL / ALTERNATIVE ORCHESTRATION — kept intentionally alongside
the native asyncio Dynamic Harness (dynamic_harness.py) for future
comparison/benchmarking, per project decision. Not on the current
production path — nothing in workflows/dynamic_workflow.py or
chat_workflow.py/report_workflow.py imports this.

Strongly-typed state for the LangGraph-based autonomous agent loop
(langgraph_agent.py). Kept separate from `agent_state.ReportAgentState`
(the fixed Supervisor -> RAG -> Writer -> PDF -> QA tree) and from
task_state.Task (the native Dynamic Harness's state) — three different
orchestration experiments, three different state shapes, on purpose.
"""
from typing import Any, Dict, List, Optional, TypedDict


class ToolCall(TypedDict):
    call_id: str
    tool: str
    args: Dict[str, Any]


class ToolResult(TypedDict):
    call_id: str
    tool: str
    ok: bool
    output: Any
    error: Optional[str]


class AutonomousAgentState(TypedDict, total=False):
    # ── identity / goal ──────────────────────────────────────────────
    execution_id: str
    session_id: str
    user_query: str
    goal: str
    role: str

    # ── reasoning ─────────────────────────────────────────────────────
    messages: List[Dict[str, str]]           # [{"role": ..., "content": ...}]
    plan: List[str]
    current_step: int

    # ── tool execution (this turn's pending call + the running log) ───
    pending_tool_calls: List[ToolCall]
    tool_calls: List[ToolCall]
    tool_results: List[ToolResult]
    iteration_count: int
    tool_call_count: int
    retry_counts: Dict[str, int]              # call_id -> retries used

    # ── accumulated evidence ────────────────────────────────────────
    uploaded_files: List[Dict[str, Any]]
    retrieved_context: List[Dict[str, Any]]
    sources: List[Dict[str, Any]]
    artifacts: List[Dict[str, Any]]

    # ── control / outcome ────────────────────────────────────────────
    validation_results: Dict[str, Any]
    errors: List[Dict[str, Any]]
    execution_events: List[Dict[str, Any]]
    status: str                               # "running" | "completed" | "failed" | "waiting_for_user"
    final_answer: Optional[str]


def new_state(
    execution_id: str,
    session_id: str,
    user_query: str,
    role: str = "You are an autonomous agriculture research and document assistant.",
    uploaded_files: Optional[List[Dict[str, Any]]] = None,
) -> AutonomousAgentState:
    return AutonomousAgentState(
        execution_id=execution_id,
        session_id=session_id,
        user_query=user_query,
        goal=user_query,
        role=role,
        messages=[{"role": "user", "content": user_query}],
        plan=[],
        current_step=0,
        pending_tool_calls=[],
        tool_calls=[],
        tool_results=[],
        iteration_count=0,
        tool_call_count=0,
        retry_counts={},
        uploaded_files=uploaded_files or [],
        retrieved_context=[],
        sources=[],
        artifacts=[],
        validation_results={},
        errors=[],
        execution_events=[],
        status="running",
        final_answer=None,
    )
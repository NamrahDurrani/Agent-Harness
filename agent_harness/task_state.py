"""
agent_harness/task_state.py

Structured state for the dynamic harness (MASTER PROMPT spec, Sections
11/32/33). Plain dataclasses mutated directly by dynamic_harness.py's
asyncio-native execution loop — NOT a LangGraph TypedDict/StateGraph.
This replaces the removed langgraph_state.AutonomousAgentState.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AgentResult:
    """Section 33 — every capability handler returns ONE of these. The
    harness makes routing/verification/recovery decisions off these
    fields, not by re-parsing arbitrary prose every time."""
    status: str                      # "success" | "failure" | "partial"
    output: Any = None
    confidence: float = 1.0          # 0..1 — meaningful only when the handler can actually estimate it
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlanStep:
    """Section 32 — one node in the structured plan. `depends_on` is what
    makes both parallel execution (Section 10) and dependency-respecting
    sequencing possible from the SAME data structure — the harness never
    needs a separate "is this sequential or parallel" flag; it just asks
    "which pending steps have every dependency satisfied right now"."""
    id: str
    capability: str
    agent_name: str
    args: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    optional: bool = False           # Section 35 — an optional step failing doesn't fail the task
    status: str = "pending"          # pending | running | success | failed | skipped
    retries: int = 0
    result: Optional[AgentResult] = None
    verification: Optional[Dict[str, Any]] = None
    failure_class: Optional[str] = None   # set by the harness on failure — see failure_recovery.py


@dataclass
class Task:
    """Section 11 — the harness's execution state. Deliberately NOT tied
    to the existing SQLite execution_logger schema — that's still the
    system of record for agent.*/tool.*/etc events (via AgentHarness,
    unchanged); this is the harness's own in-memory working state for
    ONE execution, analogous to what ReportAgentState was for the old
    fixed report tree, but for a dynamically-planned task."""
    execution_id: str
    session_id: str
    user_request: str
    goal: str = ""
    output_type: str = ""            # "chat_answer" | "pdf" | ...
    required_content: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    validation_requirements: List[str] = field(default_factory=list)
    plan: List[PlanStep] = field(default_factory=list)
    completed_step_ids: List[str] = field(default_factory=list)
    failed_step_ids: List[str] = field(default_factory=list)
    replans: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    sources: List[Dict[str, Any]] = field(default_factory=list)
    final_output: Optional[str] = None
    status: str = "running"          # running | completed | failed
    started_at: float = field(default_factory=time.time)

    def step(self, step_id: str) -> PlanStep:
        for s in self.plan:
            if s.id == step_id:
                return s
        raise KeyError(step_id)

    def ready_steps(self) -> List[PlanStep]:
        """Every pending step whose dependencies have all REACHED A
        TERMINAL STATE — success, failed, OR skipped — can be dispatched
        (Section 10). Using only "success" here would deadlock the plan
        the moment an optional dependency gets skipped (e.g.
        document_compose depending on an image_search that found no
        images and was skipped): the dependent would wait forever for a
        dependency that will never become "success". Each dependent
        handler is responsible for checking whether a given dependency
        actually succeeded before using its output (see
        dynamic_harness._resolve_dependency_args) — dependency
        SATISFACTION (can we proceed) and dependency SUCCESS (is there
        real data to use) are deliberately different questions."""
        terminal = {s.id for s in self.plan if s.status in ("success", "failed", "skipped")}
        return [s for s in self.plan
                if s.status == "pending" and set(s.depends_on).issubset(terminal)]

    def is_stuck(self) -> bool:
        """True when nothing is running/pending-and-ready and nothing
        remains to be dispatched — either everything finished, or the
        plan is deadlocked (a dependency on a step that failed and was
        never replanned around). The harness treats this as "stop", not
        "loop forever" (Section 17)."""
        pending = [s for s in self.plan if s.status == "pending"]
        running = [s for s in self.plan if s.status == "running"]
        return bool(pending) and not running and not self.ready_steps()

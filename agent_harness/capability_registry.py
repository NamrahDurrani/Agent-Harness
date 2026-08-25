"""
agent_harness/capability_registry.py

Section 31 — a central, DECLARED registry of what the system can do. The
planner (planner.py) consults this to decide what's available; it never
invents a capability that isn't registered here, and the router never
routes to an agent/tool this registry doesn't say is allowed for that
capability (Section 21 — permissions).

Each Capability wraps an EXISTING implementation (tools.py's run_*
functions, which themselves wrap rag_pipeline.py / mcp_weather_advisor /
mcp_pdf_export / mcp_tools / memory_store — nothing reimplemented here,
same principle the tool layer was already built on).
"""
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional

from .task_state import AgentResult

# handler signature: async def handler(ctx, **args) -> AgentResult
HandlerFn = Callable[..., Awaitable[AgentResult]]
# verify signature: (AgentResult, task_constraints) -> {"ok": bool, "issues": [...]}
VerifyFn = Callable[[AgentResult, Dict[str, Any]], Dict[str, Any]]


@dataclass
class Capability:
    name: str
    purpose: str                     # shown to the TaskAnalyzer/Planner LLM call — internals stay hidden
    handler: HandlerFn
    agent_name: str                  # the harness-tree label this shows up as (Section 18's agent table)
    required_tools: List[str] = field(default_factory=list)   # documentation / permission surface
    depends_on_capabilities: List[str] = field(default_factory=list)  # typical prerequisites, used as a planning hint
    optional_by_default: bool = False
    permissions: List[str] = field(default_factory=list)      # Section 21
    verify: Optional[VerifyFn] = None
    failure_class: str = "TOOL"      # default classification if the handler raises — see failure_recovery.py
    parallel_safe: bool = True       # False for anything that must run alone (e.g. PDF render writing one file)


class CapabilityRegistry:
    def __init__(self):
        self._capabilities: Dict[str, Capability] = {}

    def register(self, cap: Capability) -> None:
        self._capabilities[cap.name] = cap

    def get(self, name: str) -> Optional[Capability]:
        return self._capabilities.get(name)

    def all(self) -> List[Capability]:
        return list(self._capabilities.values())

    def manifest_for_prompt(self) -> str:
        """What the TaskAnalyzer/Planner LLM call sees — name + purpose
        + typical prerequisites only. Same "hide the internals, show the
        contract" principle the old format_tool_manifest_for_prompt()
        used."""
        lines = []
        for c in self._capabilities.values():
            dep = f" (usually needs: {', '.join(c.depends_on_capabilities)})" if c.depends_on_capabilities else ""
            opt = " [optional-capable]" if c.optional_by_default else ""
            lines.append(f"- {c.name}: {c.purpose}{dep}{opt}")
        return "\n".join(lines)

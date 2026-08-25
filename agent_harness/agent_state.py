"""
agent_harness/agent_state.py

Structured, explicit state passed between the Supervisor and its child
agents. No global/uncontrolled state — each agent function receives this
object (or reads/writes specific fields on it) and returns it back up.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ReportAgentState:
    execution_id: str
    session_id: str
    user_query: str
    parent_execution_id: Optional[str] = None

    plan: List[str] = field(default_factory=list)

    retrieved_documents: List[Dict[str, Any]] = field(default_factory=list)
    ranked_documents: List[Dict[str, Any]] = field(default_factory=list)
    sources: List[Dict[str, Any]] = field(default_factory=list)

    report_content: Optional[Dict[str, Any]] = None

    pdf_structure: Optional[Dict[str, Any]] = None
    pdf_layout: Optional[Dict[str, Any]] = None
    pdf_path: Optional[str] = None

    validation_results: Optional[Dict[str, Any]] = None

    errors: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "running"

    def record_error(self, agent_name: str, error: Any) -> None:
        self.errors.append({"agent": agent_name, "error": str(error)[:500]})

    def to_dict(self) -> Dict[str, Any]:
        """Matches the Supervisor state shape described in the spec (section 1)."""
        return {
            "execution_id": self.execution_id,
            "session_id": self.session_id,
            "query": self.user_query,
            "plan": self.plan,
            "sources": self.sources,
            "report_content": self.report_content,
            "pdf_path": self.pdf_path,
            "validation": self.validation_results,
            "status": self.status,
        }

from dataclasses import dataclass, field
from typing import Dict, Any
import time

@dataclass
class ExecutionState:
    execution_id: str
    workflow: str = "unknown"
    status: str = "queued"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    meta: Dict[str, Any] = field(default_factory=dict)


# Simple in-memory store (single-process)
_store: Dict[str, ExecutionState] = {}


def create_state(execution_id: str, workflow: str = "unknown", meta: dict = None) -> ExecutionState:
    s = ExecutionState(execution_id=execution_id, workflow=workflow, status="running", meta=meta or {})
    _store[execution_id] = s
    return s


def get_state(execution_id: str) -> ExecutionState:
    return _store.get(execution_id)


def set_status(execution_id: str, status: str):
    s = _store.get(execution_id)
    if not s:
        return
    s.status = status
    s.updated_at = time.time()


def set_meta(execution_id: str, key: str, value):
    s = _store.get(execution_id)
    if not s:
        return
    s.meta[key] = value
    s.updated_at = time.time()

"""
agent_harness/artifact_store.py

Tiny SQLite-backed registry mapping execution_id -> generated files, so
GET /api/artifacts/{id} and GET /api/artifacts/{id}/download work even
after the SSE stream for that execution has closed. Same isolation
pattern memory_store.py already uses (own table, own connect()) —
untouched, unrelated to this file.

dynamic_workflow.py calls register_artifact() once per item in
task.artifacts right after `task = await dynamic.run(task)` returns.
api_server.py's two new routes (/api/artifacts/{id} and
/api/artifacts/{id}/download) call get_artifact().
"""
import json
import os
import sqlite3
import time
from typing import Any, Dict, List, Optional

_DB_PATH = os.path.join(os.path.dirname(__file__), "artifacts.db")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_table_if_missing() -> None:
    conn = _connect()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS artifacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                path TEXT NOT NULL,
                code_blocks TEXT,
                created_at REAL NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()


# FIX: this used to be a bare `create_table_if_missing()` call, which
# runs the moment this module is imported. If that CREATE TABLE fails —
# disk full, permissions, a locked file, anything — the exception
# propagates straight out of `import agent_harness.artifact_store`,
# which cascades into `import agent_harness.workflows.dynamic_workflow`
# failing too (it imports this module), which sets
# _DYNAMIC_HARNESS_AVAILABLE = False in api_server.py — disabling the
# ENTIRE /api/chat/dynamic feature over what should have been a
# localized, recoverable problem. Catching it here means only the
# actual affected calls (register_artifact / get_artifact, if the DB
# genuinely can't be written) fail — not the whole harness.
try:
    create_table_if_missing()
except Exception as _artifact_store_init_err:
    print(f"[ARTIFACT_STORE] table setup failed at import time "
          f"(disk full? permissions?): {_artifact_store_init_err}")


def register_artifact(execution_id: str, session_id: str, filename: str,
                       file_type: str, path: str,
                       code_blocks: Optional[List[Dict[str, str]]] = None) -> None:
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO artifacts (execution_id, session_id, filename, file_type, path, code_blocks, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (execution_id, session_id, filename, file_type, path,
             json.dumps(code_blocks or []), time.time()),
        )
        conn.commit()
    finally:
        conn.close()


def get_artifact(execution_id: str) -> Optional[Dict[str, Any]]:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM artifacts WHERE execution_id = ? ORDER BY id DESC LIMIT 1",
            (execution_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()
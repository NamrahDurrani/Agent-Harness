"""
agent_harness/memory_store.py

Part 26 of the harness spec: separate memory kinds instead of dumping
everything into every prompt. This file owns exactly one slice —
"long-term useful memory" — a small per-session key/value store the
autonomous agent can explicitly read from and write to via the
save_memory / retrieve_memory tools (tools.py). Everything else (short-
term task state, conversation history, agriculture RAG knowledge,
uploaded-document storage) already exists elsewhere in the project and
is untouched — this is additive, not a replacement for any of it.

Deliberately its OWN sqlite file/table rather than reusing db_schema.py
or execution_logger.py's schema — same isolation principle
execution_logger.py already follows for harness execution events (its
own table, doesn't touch the app's other tables). Kept intentionally
tiny: no embeddings, no ranking — the agent decides what's worth saving
and what's worth asking for, per Part 26/27 ("don't inject all memory
into every prompt; create a context-selection mechanism" — here, that
mechanism IS the agent explicitly calling retrieve_memory when it thinks
something might be relevant, rather than this file deciding for it).
"""
import os
import sqlite3
import time
from typing import Any, Dict, List, Optional

_DB_PATH = os.path.join(os.path.dirname(__file__), "agent_memory.db")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_table_if_missing() -> None:
    conn = _connect()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at REAL NOT NULL,
                UNIQUE(session_id, key)
            )
        """)
        conn.commit()
    finally:
        conn.close()


create_table_if_missing()


def save_memory(session_id: str, key: str, value: str) -> None:
    """Upsert — saving the same key again overwrites the previous value
    rather than accumulating duplicates, since this is meant to hold
    current durable facts ("preferred unit: acres"), not a log."""
    conn = _connect()
    try:
        conn.execute(
            """INSERT INTO agent_memory (session_id, key, value, created_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(session_id, key) DO UPDATE SET value=excluded.value, created_at=excluded.created_at""",
            (session_id, key, value, time.time()),
        )
        conn.commit()
    finally:
        conn.close()


def retrieve_memory(session_id: str, query: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    """query=None returns everything saved for the session (most recent
    first). Otherwise a simple substring filter on key OR value — no
    embeddings, deliberately cheap; this store is meant for a handful of
    durable facts per session, not a second RAG index."""
    conn = _connect()
    try:
        if query:
            like = f"%{query}%"
            rows = conn.execute(
                """SELECT key, value, created_at FROM agent_memory
                   WHERE session_id = ? AND (key LIKE ? OR value LIKE ?)
                   ORDER BY created_at DESC LIMIT ?""",
                (session_id, like, like, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT key, value, created_at FROM agent_memory
                   WHERE session_id = ? ORDER BY created_at DESC LIMIT ?""",
                (session_id, limit),
            ).fetchall()
        return [{"key": r["key"], "value": r["value"], "created_at": r["created_at"]} for r in rows]
    finally:
        conn.close()

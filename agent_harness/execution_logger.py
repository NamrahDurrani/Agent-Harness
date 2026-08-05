import sqlite3
import json
import asyncio
from typing import Dict, Any
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "agent_harness_executions.sqlite"

_CREATE_SQL = '''
CREATE TABLE IF NOT EXISTS execution_events (
    id TEXT PRIMARY KEY,
    execution_id TEXT,
    ts REAL,
    event_type TEXT,
    node TEXT,
    function_name TEXT,
    tool_name TEXT,
    duration_ms REAL,
    status TEXT,
    input_summary TEXT,
    output_summary TEXT,
    meta JSON
);
'''


def _get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    return conn


def create_table_if_missing():
    conn = _get_conn()
    try:
        conn.execute(_CREATE_SQL)
        conn.commit()
    finally:
        conn.close()


async def persist_event(event: Dict[str, Any]):
    # Run DB write in threadpool to avoid blocking event loop
    def _write(e):
        conn = _get_conn()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO execution_events (id, execution_id, ts, event_type, node, function_name, tool_name, duration_ms, status, input_summary, output_summary, meta) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    e.get("event_id"),
                    e.get("execution_id"),
                    e.get("timestamp"),
                    e.get("type"),
                    e.get("node"),
                    e.get("function_name"),
                    e.get("tool_name"),
                    e.get("duration_ms"),
                    e.get("status"),
                    json.dumps(e.get("input_summary")) if e.get("input_summary") is not None else None,
                    json.dumps(e.get("output_summary")) if e.get("output_summary") is not None else None,
                    json.dumps(e.get("meta")) if e.get("meta") is not None else None,
                )
            )
            conn.commit()
        finally:
            conn.close()

    await asyncio.to_thread(_write, event)

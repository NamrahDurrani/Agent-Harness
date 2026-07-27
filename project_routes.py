"""
project_routes.py
=================
FastAPI router for Project Management endpoints.

Add to api_server.py:
    from project_routes import router as project_router
    app.include_router(project_router)

Endpoints
---------
POST   /api/projects                  Create project
GET    /api/projects                  List all projects
GET    /api/projects/{id}             Get project detail
PATCH  /api/projects/{id}             Rename/update project
DELETE /api/projects/{id}             Delete project + all its docs/chats

POST   /api/projects/{id}/documents   Upload & ingest PDF via Docling
GET    /api/projects/{id}/documents   List project documents
DELETE /api/projects/{id}/documents/{doc_id}  Delete document

POST   /api/projects/{id}/memory      Add memory note
DELETE /api/projects/{id}/memory/{idx}  Delete memory note by index

POST   /api/documents/global          Upload to global knowledge base
GET    /api/documents/global          List global documents
DELETE /api/documents/global/{doc_id} Delete global document
"""

import os
import uuid
import json
import shutil
import sqlite3
import time
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

router = APIRouter()
security = HTTPBearer(auto_error=False)

# ── Storage paths ────────────────────────────────────────────────────────────
PROJECTS_DB    = "projects.db"
UPLOAD_DIR     = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  Database setup
# ═══════════════════════════════════════════════════════════════════════════════

def get_db():
    conn = sqlite3.connect(PROJECTS_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_projects_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            emoji       TEXT DEFAULT '🌱',
            description TEXT DEFAULT '',
            created_at  TEXT NOT NULL,
            owner       TEXT DEFAULT 'default'
        );

        CREATE TABLE IF NOT EXISTS project_documents (
            id          TEXT PRIMARY KEY,
            project_id  TEXT,             -- NULL = global
            scope       TEXT NOT NULL,    -- 'project' | 'global'
            filename    TEXT NOT NULL,
            filepath    TEXT NOT NULL,    -- server-side path after ingestion
            size_bytes  INTEGER,
            num_chunks  INTEGER DEFAULT 0,
            uploaded_at TEXT NOT NULL,
            status      TEXT DEFAULT 'pending'  -- pending|indexed|error
        );

        CREATE TABLE IF NOT EXISTS project_memory (
            id          TEXT PRIMARY KEY,
            project_id  TEXT NOT NULL,
            note        TEXT NOT NULL,
            created_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS project_chats (
            id          TEXT PRIMARY KEY,
            project_id  TEXT,             -- NULL = standalone
            title       TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            last_msg    TEXT DEFAULT ''
        );
    """)
    conn.commit()
    conn.close()

init_projects_db()


# ═══════════════════════════════════════════════════════════════════════════════
#  Pydantic models
# ═══════════════════════════════════════════════════════════════════════════════

class ProjectCreate(BaseModel):
    name:        str
    emoji:       str = "🌱"
    description: str = ""

class ProjectUpdate(BaseModel):
    name:        Optional[str] = None
    emoji:       Optional[str] = None
    description: Optional[str] = None

class MemoryNote(BaseModel):
    note: str

class ChatCreate(BaseModel):
    title:      str
    project_id: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _now():
    return time.strftime("%Y-%m-%d %H:%M:%S")

def _ingest_with_docling(filepath: str, project_id: Optional[str], scope: str) -> int:
    """
    Ingest a PDF via Docling → chunk → add to ChromaDB.
    Returns number of chunks added.
    Falls back to PyMuPDF if Docling not installed.
    """
    from mcp_tools import dispatch as mcp_dispatch
    result = mcp_dispatch("docling_ingest", {
        "file_path":  filepath,
        "project_id": project_id,
        "scope":      scope,
    })

    if "error" in result:
        # Docling not available — fall back to existing vector_store ingestion
        print(f"  [INGEST] Docling unavailable ({result['error']}), using PyMuPDF fallback")
        try:
            import vector_store
            vector_store.ingest_pdf(filepath)
            return -1  # unknown chunk count from legacy path
        except Exception as e:
            raise RuntimeError(f"Both Docling and PyMuPDF ingestion failed: {e}")

    chunks = result.get("chunks", [])
    num_chunks = len(chunks)

    if num_chunks > 0:
        try:
            import vector_store
            # vector_store.add_chunks expects list of dicts with 'text', 'source', 'scope', 'project_id'
            # If your vector_store doesn't support scope yet, it just ingests globally.
            if hasattr(vector_store, "add_chunks"):
                vector_store.add_chunks(chunks)
            else:
                # Legacy: re-ingest from file
                vector_store.ingest_pdf(filepath)
        except Exception as e:
            print(f"  [INGEST] ChromaDB add failed: {e}")

    return num_chunks


# ═══════════════════════════════════════════════════════════════════════════════
#  Project CRUD
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/api/projects", status_code=201)
def create_project(body: ProjectCreate):
    pid = str(uuid.uuid4())
    conn = get_db()
    conn.execute(
        "INSERT INTO projects (id, name, emoji, description, created_at) VALUES (?,?,?,?,?)",
        (pid, body.name, body.emoji, body.description, _now())
    )
    conn.commit()
    conn.close()
    return {"id": pid, "name": body.name, "emoji": body.emoji,
            "description": body.description, "created_at": _now()}


@router.get("/api/projects")
def list_projects():
    conn = get_db()
    rows = conn.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
    result = []
    for r in rows:
        pid = r["id"]
        docs  = conn.execute("SELECT COUNT(*) FROM project_documents WHERE project_id=?", (pid,)).fetchone()[0]
        chats = conn.execute("SELECT COUNT(*) FROM project_chats WHERE project_id=?", (pid,)).fetchone()[0]
        mem   = conn.execute("SELECT COUNT(*) FROM project_memory WHERE project_id=?", (pid,)).fetchone()[0]
        result.append({**dict(r), "doc_count": docs, "chat_count": chats, "memory_count": mem})
    conn.close()
    return result


@router.get("/api/projects/{project_id}")
def get_project(project_id: str):
    conn = get_db()
    proj = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    if not proj:
        raise HTTPException(404, "Project not found")
    proj = dict(proj)

    proj["documents"] = [dict(r) for r in
        conn.execute("SELECT * FROM project_documents WHERE project_id=? ORDER BY uploaded_at DESC",
                     (project_id,)).fetchall()]
    proj["chats"] = [dict(r) for r in
        conn.execute("SELECT * FROM project_chats WHERE project_id=? ORDER BY created_at DESC",
                     (project_id,)).fetchall()]
    proj["memory"] = [dict(r) for r in
        conn.execute("SELECT * FROM project_memory WHERE project_id=? ORDER BY created_at ASC",
                     (project_id,)).fetchall()]
    conn.close()
    return proj


@router.patch("/api/projects/{project_id}")
def update_project(project_id: str, body: ProjectUpdate):
    conn = get_db()
    proj = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    if not proj:
        raise HTTPException(404, "Project not found")
    updates = {k: v for k, v in body.dict().items() if v is not None}
    if updates:
        set_clause = ", ".join(f"{k}=?" for k in updates)
        conn.execute(f"UPDATE projects SET {set_clause} WHERE id=?",
                     (*updates.values(), project_id))
        conn.commit()
    conn.close()
    return {"status": "ok"}


@router.delete("/api/projects/{project_id}")
def delete_project(project_id: str):
    conn = get_db()
    # Remove uploads from disk
    docs = conn.execute("SELECT filepath FROM project_documents WHERE project_id=?",
                        (project_id,)).fetchall()
    for d in docs:
        try: os.remove(d["filepath"])
        except: pass
    conn.executescript(f"""
        DELETE FROM project_documents WHERE project_id='{project_id}';
        DELETE FROM project_memory     WHERE project_id='{project_id}';
        DELETE FROM project_chats      WHERE project_id='{project_id}';
        DELETE FROM projects           WHERE id='{project_id}';
    """)
    conn.commit()
    conn.close()
    return {"status": "deleted"}


# ═══════════════════════════════════════════════════════════════════════════════
#  Document upload — project scope
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/api/projects/{project_id}/documents", status_code=201)
async def upload_project_document(
    project_id: str,
    file: UploadFile = File(...),
):
    # Save file to disk
    dest_dir = UPLOAD_DIR / "projects" / project_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    filepath = str(dest_dir / file.filename)

    contents = await file.read()
    with open(filepath, "wb") as f:
        f.write(contents)

    # Ingest via Docling
    try:
        num_chunks = _ingest_with_docling(filepath, project_id, "project")
    except Exception as e:
        num_chunks = 0
        print(f"  [UPLOAD] Ingestion error: {e}")

    doc_id = str(uuid.uuid4())
    conn   = get_db()
    conn.execute(
        "INSERT INTO project_documents (id, project_id, scope, filename, filepath, size_bytes, num_chunks, uploaded_at, status)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        (doc_id, project_id, "project", file.filename, filepath,
         len(contents), num_chunks, _now(), "indexed" if num_chunks else "error")
    )
    conn.commit()
    conn.close()

    return {
        "id":         doc_id,
        "filename":   file.filename,
        "size_bytes": len(contents),
        "num_chunks": num_chunks,
        "scope":      "project",
        "project_id": project_id,
        "status":     "indexed",
    }


@router.get("/api/projects/{project_id}/documents")
def list_project_documents(project_id: str):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM project_documents WHERE project_id=? ORDER BY uploaded_at DESC",
        (project_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.delete("/api/projects/{project_id}/documents/{doc_id}")
def delete_project_document(project_id: str, doc_id: str):
    conn = get_db()
    row  = conn.execute("SELECT filepath FROM project_documents WHERE id=? AND project_id=?",
                        (doc_id, project_id)).fetchone()
    if row:
        try: os.remove(row["filepath"])
        except: pass
        conn.execute("DELETE FROM project_documents WHERE id=?", (doc_id,))
        conn.commit()
    conn.close()
    return {"status": "deleted"}


# ═══════════════════════════════════════════════════════════════════════════════
#  Global Knowledge Library
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/api/documents/global", status_code=201)
async def upload_global_document(file: UploadFile = File(...)):
    dest_dir = UPLOAD_DIR / "global"
    dest_dir.mkdir(parents=True, exist_ok=True)
    filepath = str(dest_dir / file.filename)
    contents = await file.read()
    with open(filepath, "wb") as f:
        f.write(contents)

    try:
        num_chunks = _ingest_with_docling(filepath, None, "global")
    except Exception as e:
        num_chunks = 0
        print(f"  [GLOBAL UPLOAD] Ingestion error: {e}")

    doc_id = str(uuid.uuid4())
    conn   = get_db()
    conn.execute(
        "INSERT INTO project_documents (id, project_id, scope, filename, filepath, size_bytes, num_chunks, uploaded_at, status)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        (doc_id, None, "global", file.filename, filepath,
         len(contents), num_chunks, _now(), "indexed")
    )
    conn.commit()
    conn.close()
    return {"id": doc_id, "filename": file.filename, "scope": "global", "num_chunks": num_chunks}


@router.get("/api/documents/global")
def list_global_documents():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM project_documents WHERE scope='global' ORDER BY uploaded_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.delete("/api/documents/global/{doc_id}")
def delete_global_document(doc_id: str):
    conn = get_db()
    row  = conn.execute("SELECT filepath FROM project_documents WHERE id=? AND scope='global'",
                        (doc_id,)).fetchone()
    if row:
        try: os.remove(row["filepath"])
        except: pass
        conn.execute("DELETE FROM project_documents WHERE id=?", (doc_id,))
        conn.commit()
    conn.close()
    return {"status": "deleted"}


# ═══════════════════════════════════════════════════════════════════════════════
#  Project Memory
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/api/projects/{project_id}/memory", status_code=201)
def add_memory_note(project_id: str, body: MemoryNote):
    mid = str(uuid.uuid4())
    conn = get_db()
    conn.execute(
        "INSERT INTO project_memory (id, project_id, note, created_at) VALUES (?,?,?,?)",
        (mid, project_id, body.note, _now())
    )
    conn.commit()
    conn.close()
    return {"id": mid, "note": body.note}


@router.delete("/api/projects/{project_id}/memory/{memory_id}")
def delete_memory_note(project_id: str, memory_id: str):
    conn = get_db()
    conn.execute("DELETE FROM project_memory WHERE id=? AND project_id=?",
                 (memory_id, project_id))
    conn.commit()
    conn.close()
    return {"status": "deleted"}


# ═══════════════════════════════════════════════════════════════════════════════
#  Project Chats
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/api/chats", status_code=201)
def create_chat(body: ChatCreate):
    cid = str(uuid.uuid4())
    conn = get_db()
    conn.execute(
        "INSERT INTO project_chats (id, project_id, title, created_at) VALUES (?,?,?,?)",
        (cid, body.project_id, body.title, _now())
    )
    conn.commit()
    conn.close()
    return {"id": cid, "title": body.title, "project_id": body.project_id}


@router.patch("/api/chats/{chat_id}")
def rename_chat(chat_id: str, body: dict):
    title = body.get("title", "")
    if not title:
        raise HTTPException(400, "title required")
    conn = get_db()
    conn.execute("UPDATE project_chats SET title=? WHERE id=?", (title, chat_id))
    conn.commit()
    conn.close()
    return {"status": "ok"}


@router.delete("/api/chats/{chat_id}")
def delete_chat(chat_id: str):
    conn = get_db()
    conn.execute("DELETE FROM project_chats WHERE id=?", (chat_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted"}

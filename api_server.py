# """
# FastAPI bridge — Agentic RAG Platform
# ======================================
# Endpoints:
#   POST /api/chat               — sync chat
#   POST /api/chat/async         — async chat + webhook
#   GET  /api/jobs/{id}          — job polling
#   GET  /api/status             — pipeline status
#   GET  /api/health             — health check
#   GET  /api/sessions           — list sessions
#   GET  /api/sessions/{id}      — session history
#   DELETE /api/sessions/{id}    — delete session
#   PATCH /api/sessions/{id}     — rename session
#   GET  /api/sessions/{id}/export — download chat as .md or .json
#   POST /api/upload             — upload user file (max 3), registers for session
#   GET  /api/uploads            — list uploaded files
#   DELETE /api/uploads/{id}     — delete uploaded file
#   POST /api/tools/weather      — weather tool
#   POST /api/tools/price        — crop price tool
#   POST /api/tools/calculate    — calculator tool
#   POST /api/tools/sowing       — sowing calendar tool
#   GET  /api/logs               — recent pipeline logs (PostgreSQL)
#   GET  /api/pdf/{filename}     — serve PDF inline
#   POST /api/mcp/run            — MCP tool dispatcher
# """

# import os
# import sys
# import io
# import time
# import uuid
# import traceback
# import json
# import shutil
# from contextlib import redirect_stdout
# from typing import Optional, List, Dict

# from fastapi import (
#     FastAPI, BackgroundTasks, HTTPException,
#     UploadFile, File, Form
# )
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import FileResponse, JSONResponse, Response
# from pydantic import BaseModel
# import requests as _requests

# sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# import db_schema
# import vector_store
# from rag_pipeline import AgenticRAGPipeline, inspect_last_query as _inspect
# from rag_pipeline import build_upload_chunks
# from auth_routes import router as auth_router, init_auth_schema

# # ── Import project_routes only if the file exists ────────────────────────────
# try:
#     from project_routes import router as project_router
#     _HAS_PROJECT_ROUTES = True
# except ImportError:
#     _HAS_PROJECT_ROUTES = False
#     print("[STARTUP] project_routes.py not found — /api/projects endpoints disabled.")

# # ── FIX: mcp_pdf_export was never actually imported in the active code path.
# # The only import existed inside a large commented-out legacy block above,
# # so /api/sessions/{id}/export/pdf called _mcp_pdf(...) which was undefined
# # → NameError → caught by the generic except → HTTP 500 "Export failed".
# try:
#     from mcp_pdf_export import mcp_generate_pdf as _mcp_pdf
#     _PDF_EXPORT_AVAILABLE = True
#     print("[STARTUP] mcp_pdf_export loaded — PDF export enabled")
# except ImportError as e:
#     _PDF_EXPORT_AVAILABLE = False
#     _mcp_pdf = None
#     print(f"[STARTUP] mcp_pdf_export not found — PDF export disabled ({e})")

# # ═══════════════════════════════════════════════════════════════════════════════
# #  SESSION FILES — maps session_id → list of uploaded file paths
# #  MUST be defined at module level before any endpoint uses it
# # ═══════════════════════════════════════════════════════════════════════════════
# SESSION_FILES: Dict[str, List[str]] = {}

# # ── Upload directory ──────────────────────────────────────────────────────────
# UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_uploads")
# os.makedirs(UPLOAD_DIR, exist_ok=True)
# MAX_USER_FILES = 20   # increased — auto-purge handles per-session cleanup

# # ── PDF directory ─────────────────────────────────────────────────────────────
# PDF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdfs")
# os.makedirs(PDF_DIR, exist_ok=True)

# # ═══════════════════════════════════════════════════════════════════════════════
# #  FastAPI app
# # ═══════════════════════════════════════════════════════════════════════════════
# app = FastAPI(title="Agentic RAG API")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# app.include_router(auth_router)
# init_auth_schema()

# if _HAS_PROJECT_ROUTES:
#     app.include_router(project_router)

# # ═══════════════════════════════════════════════════════════════════════════════
# #  PostgreSQL logging (optional — silent if not configured)
# # ═══════════════════════════════════════════════════════════════════════════════
# _pg_conn = None

# def _get_pg():
#     global _pg_conn
#     if _pg_conn is not None:
#         try:
#             _pg_conn.cursor().execute("SELECT 1")
#             return _pg_conn
#         except Exception:
#             _pg_conn = None

#     pg_url = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")
#     if not pg_url:
#         host = os.environ.get("POSTGRES_HOST")
#         if not host:
#             return None
#         db   = os.environ.get("POSTGRES_DB", "agri_rag")
#         user = os.environ.get("POSTGRES_USER", "postgres")
#         pwd  = os.environ.get("POSTGRES_PASSWORD", "")
#         port = os.environ.get("POSTGRES_PORT", "5432")
#         pg_url = f"postgresql://{user}:{pwd}@{host}:{port}/{db}"
#     try:
#         import psycopg2
#         _pg_conn = psycopg2.connect(pg_url)
#         _pg_conn.autocommit = True
#         _init_pg_schema(_pg_conn)
#         return _pg_conn
#     except Exception as e:
#         print(f"[PG] Not available: {e}")
#         return None


# def _init_pg_schema(conn):
#     cur = conn.cursor()
#     cur.execute("""
#     CREATE TABLE IF NOT EXISTS pg_sessions (
#         session_id  TEXT PRIMARY KEY,
#         title       TEXT NOT NULL DEFAULT 'New Chat',
#         created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
#         updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
#     );
#     CREATE TABLE IF NOT EXISTS pg_messages (
#         msg_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
#         session_id  TEXT NOT NULL,
#         role        TEXT NOT NULL,
#         content     TEXT NOT NULL,
#         used_rag    BOOLEAN,
#         tokens_used INTEGER,
#         created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
#     );
#     CREATE TABLE IF NOT EXISTS pg_pipeline_logs (
#         log_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
#         session_id  TEXT,
#         query_id    TEXT,
#         step_name   TEXT NOT NULL,
#         input_text  TEXT,
#         output_text TEXT,
#         duration_ms REAL,
#         status      TEXT DEFAULT 'ok',
#         logged_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
#     );
#     CREATE TABLE IF NOT EXISTS pg_tool_calls (
#         call_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
#         session_id  TEXT,
#         tool_name   TEXT NOT NULL,
#         input_args  JSONB,
#         output      JSONB,
#         duration_ms REAL,
#         status      TEXT DEFAULT 'ok',
#         called_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
#     );
#     CREATE TABLE IF NOT EXISTS pg_user_files (
#         file_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
#         original_name TEXT NOT NULL,
#         stored_name   TEXT NOT NULL,
#         file_path     TEXT NOT NULL,
#         chunk_count   INTEGER DEFAULT 0,
#         status        TEXT DEFAULT 'pending',
#         uploaded_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
#     );
#     """)
#     conn.commit()
#     print("[PG] Schema ready.")


# def _pg_log(table: str, data: dict):
#     conn = _get_pg()
#     if not conn:
#         return
#     try:
#         import psycopg2.extras
#         cols   = ", ".join(data.keys())
#         vals   = ", ".join(["%s"] * len(data))
#         values = [json.dumps(v) if isinstance(v, dict) else v for v in data.values()]
#         conn.cursor().execute(f"INSERT INTO {table} ({cols}) VALUES ({vals})", values)
#     except Exception as e:
#         print(f"[PG] Log failed: {e}")


# # ═══════════════════════════════════════════════════════════════════════════════
# #  Upload metadata helpers
# # ═══════════════════════════════════════════════════════════════════════════════
# _UPLOADS_META = os.path.join(UPLOAD_DIR, ".meta.json")


# def _load_uploads() -> list:
#     if os.path.exists(_UPLOADS_META):
#         try:
#             return json.load(open(_UPLOADS_META))
#         except Exception:
#             pass
#     return []


# def _save_uploads(uploads: list):
#     json.dump(uploads, open(_UPLOADS_META, "w"), indent=2)


# def _update_upload_status(file_id: str, status: str, chunks: int):
#     uploads = _load_uploads()
#     for u in uploads:
#         if u.get("file_id") == file_id:
#             u["status"]      = status
#             u["chunk_count"] = chunks
#     _save_uploads(uploads)


# def _purge_orphaned_uploads():
#     """On startup: remove any upload metadata entries whose file no longer exists on disk.
#     This fixes 'Maximum 3 files allowed' errors caused by stale .meta.json entries."""
#     uploads = _load_uploads()
#     valid = [u for u in uploads if os.path.exists(u.get("file_path", ""))]
#     if len(valid) < len(uploads):
#         print(f"[UPLOAD] Purged {len(uploads) - len(valid)} orphaned upload record(s) from meta.")
#         _save_uploads(valid)


# # ═══════════════════════════════════════════════════════════════════════════════
# #  Lazy pipeline singleton
# # ═══════════════════════════════════════════════════════════════════════════════
# _pipeline: Optional[AgenticRAGPipeline] = None
# _pipeline_init_error: Optional[str]     = None


# def get_pipeline() -> AgenticRAGPipeline:
#     global _pipeline, _pipeline_init_error
#     if _pipeline is None and _pipeline_init_error is None:
#         try:
#             db_schema.init_db()
#             _pipeline = AgenticRAGPipeline()
#         except Exception as exc:
#             _pipeline_init_error = f"{type(exc).__name__}: {exc}"
#             print("\n[FATAL] Pipeline failed to initialise:")
#             traceback.print_exc()
#     if _pipeline is None:
#         raise RuntimeError(_pipeline_init_error or "Pipeline failed to initialise")
#     return _pipeline


# # ═══════════════════════════════════════════════════════════════════════════════
# #  Pydantic models
# # ═══════════════════════════════════════════════════════════════════════════════

# class ChatRequest(BaseModel):
#     session_id: str
#     query: str
#     force_web: bool = False   # UI "Web Search ON" toggle — skip RAG, search live web

# class ChatResponse(BaseModel):
#     response:    str
#     trace:       Optional[str]       = None
#     used_rag:    Optional[bool]      = None
#     source_type: Optional[str]       = None   # "RAG" | "WEB" | "MCP" | "UPLOAD"
#     mcp_tool:    Optional[str]       = None   # name of MCP tool if source_type=="MCP"
#     sources:     Optional[List[dict]] = None  # structured sources for collapsed UI panel

# class AsyncChatRequest(BaseModel):
#     session_id:   str
#     query:        str
#     callback_url: Optional[str] = None

# class JobAcceptedResponse(BaseModel):
#     job_id: str
#     status: str = "pending"

# class JobStatusResponse(BaseModel):
#     job_id:            str
#     status:            str
#     response:          Optional[str]  = None
#     trace:             Optional[str]  = None
#     used_rag:          Optional[bool] = None
#     error_detail:      Optional[str]  = None
#     webhook_delivered: Optional[bool] = None

# class RenameRequest(BaseModel):
#     title: str

# class ToolRequest(BaseModel):
#     query:      str
#     session_id: Optional[str] = None

# class MCPRunRequest(BaseModel):
#     tool:       str
#     params:     dict            = {}
#     session_id: Optional[str]  = None


# # ═══════════════════════════════════════════════════════════════════════════════
# #  Retry wrapper
# # ═══════════════════════════════════════════════════════════════════════════════
# RETRYABLE_ERRORS = (ConnectionError, ConnectionResetError,
#                     ConnectionAbortedError, TimeoutError)


# def run_pipeline_with_retry(pipeline, session_id, query,
#                             upload_chunks=None, force_web=False, max_attempts=3):
#     last_exc = None
#     for attempt in range(1, max_attempts + 1):
#         try:
#             return pipeline.run(
#                 session_id=session_id,
#                 user_query=query,
#                 upload_chunks=upload_chunks or [],
#                 force_web=force_web,
#             )
#         except RETRYABLE_ERRORS as exc:
#             last_exc = exc
#             wait = attempt * 1.5
#             print(f"[RETRY] Attempt {attempt}/{max_attempts} "
#                   f"({type(exc).__name__}) — retrying in {wait}s")
#             time.sleep(wait)
#         except Exception as exc:
#             msg = str(exc).lower()
#             if any(kw in msg for kw in
#                    ("connection", "10054", "reset", "timeout", "aborted")):
#                 last_exc = exc
#                 time.sleep(attempt * 1.5)
#                 continue
#             raise
#     raise last_exc


# # ═══════════════════════════════════════════════════════════════════════════════
# #  Core query executor (shared by sync + async paths)
# # ═══════════════════════════════════════════════════════════════════════════════

# def _execute_query(session_id: str,
#                    query: str,
#                    force_web: bool = False) -> tuple:
#     """
#     Returns (response, trace, used_rag, source_type, mcp_tool, sources).
#       source_type: "RAG" | "WEB" | "MCP" | "UPLOAD"
#       mcp_tool:    name of the MCP tool if source_type=="MCP", else None
#       sources:     structured sources list from PipelineResult.sources, or []
#     """
#     if not force_web and vector_store.collection_size() == 0:
#         return (
#             "⚠️ The knowledge base is empty. "
#             "Run `python main.py --index` first, then restart the API server.",
#             None, None, None, None, [],
#         )

#     pipeline = get_pipeline()

#     # ── Gather upload chunks for this session ─────────────────────────────
#     upload_chunks: List[dict] = []
#     has_uploads = False
#     session_file_paths = SESSION_FILES.get(session_id, [])
#     print(f"  [SESSION_FILES] session={session_id!r} has {len(session_file_paths)} file(s) registered")
#     for fpath in session_file_paths:
#         if os.path.exists(fpath):
#             try:
#                 chunks = build_upload_chunks(fpath)
#                 upload_chunks.extend(chunks)
#                 if chunks:
#                     has_uploads = True
#             except Exception as e:
#                 print(f"  [SESSION_FILES] Could not load '{fpath}': {e}")
#         else:
#             print(f"  [SESSION_FILES] WARNING: file no longer on disk: {fpath}")

#     response = run_pipeline_with_retry(
#         pipeline, session_id, query,
#         upload_chunks=upload_chunks,
#         force_web=force_web,
#     )

#     # ── FIX: pipeline.run() returns a PipelineResult object, not a plain
#     # string. Passing that object straight into ChatResponse(response=...)
#     # is what caused: "ValidationError: response — Input should be a valid
#     # string [input_type=PipelineResult]". Unpack it into a real string here,
#     # and grab .sources / .source_type / .used_rag directly from it instead
#     # of re-deriving them from SQL step-name guessing below.
#     _pipeline_sources = []
#     if hasattr(response, "answer"):
#         pipeline_result   = response
#         response          = pipeline_result.answer
#         _pipeline_sources = pipeline_result.sources or []
#         _pipeline_source_type = pipeline_result.source_type
#         _pipeline_used_rag    = pipeline_result.used_rag
#     else:
#         # Backward-compat: some rag_pipeline.py versions still return a
#         # plain string. In that case fall through to the SQL-based
#         # source_type detection below, unchanged.
#         _pipeline_source_type = None
#         _pipeline_used_rag    = None

#     # ── Read used_rag + step info from SQLite to determine source_type ────
#     used_rag    = _pipeline_used_rag
#     source_type = _pipeline_source_type
#     mcp_tool    = None
#     trace_lines = []

#     try:
#         conn = db_schema.get_connection()

#         # Get latest query_id for this session
#         q_row = conn.execute("""
#             SELECT q.query_id, r.used_rag
#             FROM queries q
#             LEFT JOIN responses r ON r.query_id = q.query_id
#             WHERE q.session_id = ?
#             ORDER BY q.timestamp DESC LIMIT 1
#         """, (session_id,)).fetchone()

#         if q_row:
#             # FIX: only overwrite with the DB-derived value if PipelineResult
#             # didn't already give us a definitive answer above. Previously
#             # this always overwrote used_rag from the DB even when we had a
#             # reliable value straight from the pipeline object.
#             if used_rag is None:
#                 used_rag = bool(q_row["used_rag"]) if q_row["used_rag"] is not None else None
#             qid = q_row["query_id"]

#             # Read all pipeline steps for trace panel
#             steps = conn.execute("""
#                 SELECT step_name, duration_ms, status, input_text, output_text
#                 FROM pipeline_steps WHERE query_id=? ORDER BY step_order
#             """, (qid,)).fetchall()

#             for s in steps:
#                 trace_lines.append(
#                     f"[{s['step_name']}] {s['duration_ms']:.0f}ms | {s['status']}"
#                 )
#                 # FIX: only run this MCP-detection-from-step-names fallback
#                 # when the pipeline itself didn't already tell us source_type.
#                 # Previously this ran unconditionally, and 'mcp_dispatch' gets
#                 # logged even when the tool check returns NO_TOOL — so every
#                 # single response got tagged "MCP" regardless of what actually
#                 # answered the question.
#                 if _pipeline_source_type is None and (
#                     s["step_name"] in ("mcp_dispatch", "mcp_tool") or
#                     s["step_name"].startswith("mcp_")
#                 ):
#                     source_type = "MCP"
#                     try:
#                         out = s["output_text"] or ""
#                         if "MCP Tool:" in out:
#                             mcp_tool = out.split("MCP Tool:")[1].split("]")[0].strip()
#                     except Exception:
#                         pass

#             # Determine source_type from step names if MCP not detected above
#             if source_type is None:
#                 step_names = [s["step_name"] for s in steps]
#                 if has_uploads and used_rag:
#                     source_type = "UPLOAD"
#                 elif used_rag:
#                     source_type = "RAG"
#                 elif any("tavily" in n or "web_search" in n or "web" in n
#                          for n in step_names):
#                     source_type = "WEB"
#                 elif force_web:
#                     source_type = "WEB"   # explicit toggle, even if step names didn't match
#                 else:
#                     source_type = "WEB"   # fallback path also uses web search

#         conn.close()
#     except Exception as e:
#         print(f"  [EXECUTE] DB read error: {e}")

#     # ── Also check if MCP was called (logged in mcp_context) ─────────────
#     # FIX: only fall back to this text-scan when pipeline didn't already
#     # tell us. Also guard against `response` not being a string here.
#     if _pipeline_source_type is None and source_type != "MCP":
#         if isinstance(response, str) and "[MCP Tool:" in response:
#             source_type = "MCP"
#             try:
#                 mcp_tool = response.split("[MCP Tool:")[1].split("]")[0].strip()
#             except Exception:
#                 pass

#     # ── Build trace string ─────────────────────────────────────────────────
#     trace = None
#     if trace_lines:
#         trace = "\n".join(trace_lines)
#     else:
#         buf = io.StringIO()
#         try:
#             with redirect_stdout(buf):
#                 _inspect()
#             trace = buf.getvalue().strip() or None
#         except Exception:
#             pass

#     return response, trace, used_rag, source_type, mcp_tool, _pipeline_sources


# def _friendly_error(exc: Exception) -> str:
#     msg = str(exc)
#     if any(kw in msg.lower() for kw in
#            ("connection", "10054", "reset", "aborted", "timeout")):
#         return (
#             "⚠️ The remote model connection dropped mid-response. "
#             "This is usually transient — please try again. "
#             "If it keeps happening, the Qwen server/tunnel may need restarting."
#         )
#     return f"❌ Backend error: {type(exc).__name__}: {exc}"


# # ═══════════════════════════════════════════════════════════════════════════════
# #  Health / Status
# # ═══════════════════════════════════════════════════════════════════════════════

# @app.get("/api/health")
# def health():
#     try:
#         db_schema.init_db()
#         count = vector_store.collection_size()
#         return {"ok": True, "chunks": count}
#     except Exception as exc:
#         return JSONResponse(status_code=500,
#                             content={"ok": False, "error": str(exc)})


# @app.get("/api/status")
# def status():
#     backend = os.environ.get("LLM_BACKEND", "groq").upper()
#     model_map = {
#         "GROQ":        os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant"),
#         "QWEN_REMOTE": os.environ.get("QWEN_REMOTE_MODEL", "Qwen (remote)"),
#         "QWEN_LOCAL":  "Qwen (local)",
#         "OLLAMA":      os.environ.get("OLLAMA_MODEL", "ollama"),
#     }
#     model_name = model_map.get(backend, backend)
#     try:
#         chunk_count = vector_store.collection_size()
#     except Exception as exc:
#         return {"chunk_count": 0, "backend": backend,
#                 "model": model_name, "vector_store_error": str(exc)}

#     return {
#         "chunk_count":     chunk_count,
#         "backend":         backend,
#         "model":           model_name,
#         "embedding_model": vector_store.EMBEDDING_MODEL,
#         "vector_db":       "ChromaDB",
#         "retrieval":       "BM25 + Sentence Embeddings",
#         "fusion":          "RRF",
#         "pipeline_ready":  _pipeline is not None,
#         "pipeline_error":  _pipeline_init_error,
#     }


# # ═══════════════════════════════════════════════════════════════════════════════
# #  Sync Chat
# # ═══════════════════════════════════════════════════════════════════════════════

# @app.post("/api/chat", response_model=ChatResponse)
# def chat(req: ChatRequest):
#     t0 = time.time()
#     try:
#         response, trace, used_rag, source_type, mcp_tool, sources = \
#             _execute_query(req.session_id, req.query, force_web=req.force_web)
#         print(f"[CHAT] {time.time()-t0:.2f}s  "
#               f"query={req.query[:60]!r}  "
#               f"force_web={req.force_web}  "
#               f"source={source_type}  used_rag={used_rag}  mcp_tool={mcp_tool}  "
#               f"sources={len(sources or [])}")
#         return ChatResponse(
#             response=response,
#             trace=trace,
#             used_rag=used_rag,
#             source_type=source_type,
#             mcp_tool=mcp_tool,
#             sources=sources or [],
#         )
#     except Exception as exc:
#         print("\n" + "="*70)
#         print("[ERROR] /api/chat failed")
#         traceback.print_exc()
#         print("="*70 + "\n")
#         return JSONResponse(
#             status_code=500,
#             content={"response": _friendly_error(exc),
#                      "trace": None, "error_detail": str(exc)},
#         )


# # ═══════════════════════════════════════════════════════════════════════════════
# #  Async Chat + Webhook
# # ═══════════════════════════════════════════════════════════════════════════════
# WEBHOOK_MAX_ATTEMPTS = 3
# WEBHOOK_TIMEOUT      = 10


# def _deliver_webhook(job_id: str, callback_url: str, payload: dict):
#     conn = db_schema.get_connection()
#     for attempt in range(1, WEBHOOK_MAX_ATTEMPTS + 1):
#         try:
#             resp = _requests.post(callback_url, json=payload,
#                                   timeout=WEBHOOK_TIMEOUT)
#             conn.execute("UPDATE jobs SET webhook_attempts=? WHERE job_id=?",
#                          (attempt, job_id))
#             if resp.status_code < 300:
#                 conn.execute(
#                     "UPDATE jobs SET webhook_delivered=1 WHERE job_id=?",
#                     (job_id,))
#                 conn.commit()
#                 conn.close()
#                 return
#         except Exception as exc:
#             conn.execute("UPDATE jobs SET webhook_attempts=? WHERE job_id=?",
#                          (attempt, job_id))
#             print(f"[WEBHOOK] job {job_id} attempt {attempt} failed: {exc}")
#         conn.commit()
#         if attempt < WEBHOOK_MAX_ATTEMPTS:
#             time.sleep(attempt * 2)
#     conn.close()


# def _process_job(job_id: str, session_id: str,
#                  query: str, callback_url: Optional[str]):
#     conn = db_schema.get_connection()
#     conn.execute("UPDATE jobs SET status='running' WHERE job_id=?", (job_id,))
#     conn.commit()
#     conn.close()

#     try:
#         response, trace, used_rag, source_type, mcp_tool, sources = \
#             _execute_query(session_id, query)
#         conn = db_schema.get_connection()
#         conn.execute("""
#             UPDATE jobs
#             SET status='done', result_response=?, result_trace=?,
#                 used_rag=?, completed_at=datetime('now')
#             WHERE job_id=?
#         """, (response, trace,
#               int(used_rag) if used_rag is not None else None, job_id))
#         conn.commit()
#         conn.close()
#         status_val, error_detail = "done", None
#     except Exception as exc:
#         traceback.print_exc()
#         response, trace, used_rag, source_type, mcp_tool, sources = \
#             _friendly_error(exc), None, None, None, None, []
#         conn = db_schema.get_connection()
#         conn.execute("""
#             UPDATE jobs
#             SET status='error', error_detail=?, completed_at=datetime('now')
#             WHERE job_id=?
#         """, (str(exc), job_id))
#         conn.commit()
#         conn.close()
#         status_val, error_detail = "error", str(exc)

#     if callback_url:
#         _deliver_webhook(job_id, callback_url, {
#             "job_id": job_id, "session_id": session_id,
#             "status": status_val, "response": response,
#             "trace": trace, "used_rag": used_rag,
#             "error_detail": error_detail,
#         })


# @app.post("/api/chat/async", response_model=JobAcceptedResponse, status_code=202)
# def chat_async(req: AsyncChatRequest, background_tasks: BackgroundTasks):
#     job_id = str(uuid.uuid4())
#     conn   = db_schema.get_connection()
#     conn.execute("INSERT OR IGNORE INTO sessions (session_id) VALUES (?)",
#                  (req.session_id,))
#     conn.execute(
#         "INSERT INTO jobs (job_id, session_id, query, status, callback_url) "
#         "VALUES (?,?,?,'pending',?)",
#         (job_id, req.session_id, req.query, req.callback_url))
#     conn.commit()
#     conn.close()
#     background_tasks.add_task(
#         _process_job, job_id, req.session_id, req.query, req.callback_url)
#     print(f"[ASYNC] queued job {job_id}")
#     return JobAcceptedResponse(job_id=job_id)


# @app.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
# def get_job(job_id: str):
#     conn = db_schema.get_connection()
#     row  = conn.execute("SELECT * FROM jobs WHERE job_id=?",
#                         (job_id,)).fetchone()
#     conn.close()
#     if not row:
#         raise HTTPException(404, "Job not found")
#     return JobStatusResponse(
#         job_id=row["job_id"],
#         status=row["status"],
#         response=row["result_response"],
#         trace=row["result_trace"],
#         used_rag=bool(row["used_rag"]) if row["used_rag"] is not None else None,
#         error_detail=row["error_detail"],
#         webhook_delivered=bool(row["webhook_delivered"]),
#     )


# # ═══════════════════════════════════════════════════════════════════════════════
# #  Session endpoints
# # ═══════════════════════════════════════════════════════════════════════════════

# @app.get("/api/sessions")
# def list_sessions():
#     conn = db_schema.get_connection()
#     try:
#         # Ensure title column exists
#         try:
#             conn.execute("ALTER TABLE sessions ADD COLUMN title TEXT")
#             conn.commit()
#         except Exception:
#             pass

#         rows = conn.execute("""
#             SELECT
#                 s.session_id,
#                 s.created_at,
#                 s.title,
#                 COUNT(q.query_id) AS message_count,
#                 (SELECT original_query FROM queries
#                  WHERE session_id = s.session_id
#                  ORDER BY timestamp ASC LIMIT 1) AS first_query,
#                 (SELECT MAX(timestamp) FROM queries
#                  WHERE session_id = s.session_id) AS last_activity
#             FROM sessions s
#             JOIN queries q ON q.session_id = s.session_id
#             GROUP BY s.session_id
#             ORDER BY last_activity DESC
#             LIMIT 100
#         """).fetchall()
#         return {
#             "sessions": [
#                 {
#                     "session_id":    r["session_id"],
#                     "created_at":    r["created_at"],
#                     "title":         r["title"],
#                     "message_count": r["message_count"],
#                     "preview":       (r["title"] or r["first_query"] or "")[:80],
#                     "last_activity": r["last_activity"],
#                 }
#                 for r in rows
#             ]
#         }
#     finally:
#         conn.close()


# @app.get("/api/sessions/{session_id}")
# def get_session_history(session_id: str):
#     conn = db_schema.get_connection()
#     try:
#         rows = conn.execute("""
#             SELECT q.query_id, q.original_query, q.timestamp AS query_ts,
#                    r.final_response, r.timestamp AS response_ts, r.used_rag
#             FROM queries q
#             LEFT JOIN responses r ON r.query_id = q.query_id
#             WHERE q.session_id = ?
#             ORDER BY q.timestamp ASC
#         """, (session_id,)).fetchall()
#         messages = []
#         for r in rows:
#             messages.append({"role": "user",
#                              "content": r["original_query"],
#                              "ts": r["query_ts"]})
#             if r["final_response"]:
#                 messages.append({
#                     "role":     "assistant",
#                     "content":  r["final_response"],
#                     "ts":       r["response_ts"],
#                     "used_rag": bool(r["used_rag"]) if r["used_rag"] is not None else None,
#                 })
#         return {"session_id": session_id, "messages": messages}
#     finally:
#         conn.close()


# @app.delete("/api/sessions/{session_id}")
# def delete_session(session_id: str):
#     conn = db_schema.get_connection()
#     try:
#         query_ids = [r["query_id"] for r in conn.execute(
#             "SELECT query_id FROM queries WHERE session_id=?",
#             (session_id,)).fetchall()]
#         for qid in query_ids:
#             conn.execute("DELETE FROM responses WHERE query_id=?", (qid,))
#             step_ids = [r["step_id"] for r in conn.execute(
#                 "SELECT step_id FROM pipeline_steps WHERE query_id=?",
#                 (qid,)).fetchall()]
#             for sid in step_ids:
#                 conn.execute("DELETE FROM llm_calls WHERE step_id=?", (sid,))
#             conn.execute("DELETE FROM retrieved_docs WHERE query_id=?", (qid,))
#             conn.execute("DELETE FROM pipeline_steps WHERE query_id=?", (qid,))
#         conn.execute("DELETE FROM queries WHERE session_id=?", (session_id,))
#         conn.execute("DELETE FROM sessions WHERE session_id=?", (session_id,))
#         conn.commit()
#         # Also clear session files from memory
#         SESSION_FILES.pop(session_id, None)
#         return {"deleted": True, "session_id": session_id}
#     finally:
#         conn.close()


# @app.patch("/api/sessions/{session_id}")
# def rename_session(session_id: str, req: RenameRequest):
#     conn = db_schema.get_connection()
#     row  = conn.execute("SELECT session_id FROM sessions WHERE session_id=?",
#                         (session_id,)).fetchone()
#     conn.close()
#     if not row:
#         raise HTTPException(404, "Session not found")

#     conn = db_schema.get_connection()
#     try:
#         conn.execute("ALTER TABLE sessions ADD COLUMN title TEXT")
#         conn.commit()
#     except Exception:
#         pass
#     conn.execute("UPDATE sessions SET title=? WHERE session_id=?",
#                  (req.title.strip(), session_id))
#     conn.commit()
#     conn.close()

#     try:
#         pg = _get_pg()
#         if pg:
#             pg.cursor().execute(
#                 "INSERT INTO pg_sessions (session_id, title) VALUES (%s,%s) "
#                 "ON CONFLICT (session_id) DO UPDATE "
#                 "SET title=EXCLUDED.title, updated_at=NOW()",
#                 (session_id, req.title.strip()))
#     except Exception:
#         pass

#     return {"session_id": session_id, "title": req.title.strip()}


# @app.get("/api/sessions/{session_id}/export")
# def export_session(session_id: str, format: str = "markdown"):
#     conn = db_schema.get_connection()
#     try:
#         session_row = conn.execute(
#             "SELECT session_id, created_at, title FROM sessions WHERE session_id=?",
#             (session_id,)).fetchone()
#         if not session_row:
#             raise HTTPException(404, "Session not found")
#         rows = conn.execute("""
#             SELECT q.original_query, q.timestamp AS query_ts,
#                    r.final_response, r.timestamp AS response_ts, r.used_rag
#             FROM queries q
#             LEFT JOIN responses r ON r.query_id = q.query_id
#             WHERE q.session_id = ?
#             ORDER BY q.timestamp ASC
#         """, (session_id,)).fetchall()
#     finally:
#         conn.close()

#     title     = session_row["title"] or "Untitled Chat"
#     safe_base = "".join(
#         c if c.isalnum() or c in " -_" else "" for c in title
#     ).strip() or session_id[:8]

#     if format == "json":
#         payload = {
#             "session_id": session_id,
#             "title":      title,
#             "created_at": session_row["created_at"],
#             "messages": [
#                 {
#                     "user":         r["original_query"],
#                     "user_ts":      r["query_ts"],
#                     "assistant":    r["final_response"],
#                     "assistant_ts": r["response_ts"],
#                     "used_rag":     bool(r["used_rag"]) if r["used_rag"] is not None else None,
#                 }
#                 for r in rows
#             ],
#         }
#         return Response(
#             content=json.dumps(payload, indent=2),
#             media_type="application/json",
#             headers={"Content-Disposition":
#                      f'attachment; filename="{safe_base}.json"'},
#         )

#     lines = [f"# {title}", "",
#              f"_Exported {time.strftime('%Y-%m-%d %H:%M')} · "
#              f"session `{session_id[:8]}…`_", ""]
#     for r in rows:
#         lines += [f"**You** _{r['query_ts']}_", "", r["original_query"], ""]
#         if r["final_response"]:
#             tag = " (web/direct)" if r["used_rag"] is False else ""
#             lines += [f"**Assistant**{tag} _{r['response_ts']}_",
#                       "", r["final_response"], ""]
#         lines += ["---", ""]

#     return Response(
#         content="\n".join(lines),
#         media_type="text/markdown",
#         headers={"Content-Disposition":
#                  f'attachment; filename="{safe_base}.md"'},
#     )


# # ═══════════════════════════════════════════════════════════════════════════════
# #  PDF Export via MCP
# # ═══════════════════════════════════════════════════════════════════════════════

# @app.get("/api/sessions/{session_id}/export/pdf")
# def export_session_pdf(session_id: str):
#     """
#     MCP PDF Export Tool
#     -------------------
#     Flow:
#       Frontend PDF button
#         → GET /api/sessions/{id}/export/pdf
#         → mcp_generate_pdf() reads: chat messages, pipeline steps,
#           retrieved sources, LLM call metadata from SQLite
#         → Builds styled HTML report
#         → Converts HTML → PDF via weasyprint (falls back to HTML)
#         → Browser triggers download

#     Install weasyprint for true PDF output:
#         pip install weasyprint
#     """
#     if not _PDF_EXPORT_AVAILABLE:
#         raise HTTPException(503, "PDF export module not loaded on the server — "
#                              "check startup logs for mcp_pdf_export import error.")

#     conn = db_schema.get_connection()
#     try:
#         result = _mcp_pdf(session_id, conn)
#     except Exception as e:
#         raise HTTPException(500, f"PDF generation failed: {e}")
#     finally:
#         conn.close()

#     if result["type"] == "error":
#         raise HTTPException(404, result["detail"])

#     if result["type"] == "pdf":
#         return Response(
#             content=result["bytes"],
#             media_type="application/pdf",
#             headers={
#                 "Content-Disposition":
#                     f'attachment; filename="{result["filename"]}"',
#                 "X-Export-Type": "pdf",
#             },
#         )
#     else:
#         # HTML fallback (weasyprint not installed)
#         return Response(
#             content=result["html"],
#             media_type="text/html",
#             headers={
#                 "Content-Disposition":
#                     f'attachment; filename="{result["filename"]}"',
#                 "X-Export-Type": "html",
#             },
#         )


# # ═══════════════════════════════════════════════════════════════════════════════
# #  File upload
# # ═══════════════════════════════════════════════════════════════════════════════

# def _bg_index_user_file(file_id: str, file_path: str, original_name: str):
#     """Background: extract + embed uploaded file into ChromaDB user_uploads."""
#     try:
#         from rag_pipeline import build_upload_chunks as _buc
#         chunks = _buc(file_path, source_label=original_name)
#         if not chunks:
#             _update_upload_status(file_id, "error", 0)
#             return

#         client = vector_store._get_client()
#         ef     = vector_store._get_ef()
#         col    = client.get_or_create_collection(
#             name="user_uploads",
#             embedding_function=ef,
#             metadata={"hnsw:space": "cosine"},
#         )
#         texts, ids, metas = [], [], []
#         for chunk in chunks:
#             texts.append(chunk["chunk_text"])
#             ids.append(str(uuid.uuid4()))
#             metas.append({
#                 "source_file":  original_name,
#                 "page_num":     chunk.get("page_num", 0),
#                 "file_id":      file_id,
#                 "user_upload":  True,
#             })
#         for i in range(0, len(texts), 128):
#             col.add(documents=texts[i:i+128],
#                     ids=ids[i:i+128],
#                     metadatas=metas[i:i+128])

#         _update_upload_status(file_id, "indexed", len(chunks))
#         print(f"[UPLOAD] '{original_name}' → {len(chunks)} chunks in user_uploads")
#     except Exception as e:
#         _update_upload_status(file_id, "error", 0)
#         print(f"[UPLOAD] Background indexing error: {e}")


# @app.get("/api/uploads")
# def list_uploads():
#     return {"uploads": _load_uploads()}


# @app.post("/api/upload")
# async def upload_file(
#     background_tasks: BackgroundTasks,
#     file:       UploadFile = File(...),
#     # Accept both naming conventions from the frontend
#     session_id: Optional[str] = Form(None),
#     sessionId:  Optional[str] = Form(None),
# ):
#     """
#     Upload a PDF / TXT / DOCX (max 3 at any time).
#     Accepts `session_id` or `sessionId` from the frontend form.
#     The file is:
#       1. Saved to disk under user_uploads/
#       2. Registered in SESSION_FILES[session_id] so subsequent chat
#          calls in this session can find and search it.
#       3. Indexed into ChromaDB in the background.
#     """
#     # Accept either field name from the frontend
#     resolved_session_id = session_id or sessionId or "global"

#     # ── File type check ───────────────────────────────────────────────────
#     allowed = {".pdf", ".txt", ".docx"}
#     fname   = file.filename or ""
#     ext     = os.path.splitext(fname)[1].lower()
#     if ext not in allowed:
#         raise HTTPException(
#             400, f"File type '{ext}' not allowed. Supported: {', '.join(allowed)}")

#     # ── Auto-purge previous uploads for this session so quota is never hit ────
#     uploads = _load_uploads()
#     old_for_session = [u for u in uploads if u.get('session_id') == resolved_session_id]
#     for old in old_for_session:
#         try:
#             if os.path.exists(old.get('file_path', '')):
#                 os.remove(old['file_path'])
#         except Exception:
#             pass
#         try:
#             _client = vector_store._get_client()
#             _col    = _client.get_collection('user_uploads')
#             _res    = _col.get(where={'file_id': old['file_id']})
#             if _res and _res.get('ids'):
#                 _col.delete(ids=_res['ids'])
#         except Exception:
#             pass
#         fpath = old.get('file_path', '')
#         sid   = old.get('session_id', '')
#         if sid and sid in SESSION_FILES:
#             SESSION_FILES[sid] = [p for p in SESSION_FILES[sid] if p != fpath]
#         print(f"[UPLOAD] Auto-purged '{old.get('original_name')}' for session {resolved_session_id[:8]}")
#     uploads = [u for u in uploads if u.get('session_id') != resolved_session_id]
#     _save_uploads(uploads)

#     # ── Safety-net quota check ────────────────────────────────────────────────────
#     if len(uploads) >= MAX_USER_FILES:
#         raise HTTPException(
#             400,
#             f'Server storage full ({MAX_USER_FILES} files). An admin must clear old uploads.')
#     # ── Save to disk ──────────────────────────────────────────────────────
#     file_id   = str(uuid.uuid4())
#     safe_name = f"{file_id}{ext}"
#     file_path = os.path.join(UPLOAD_DIR, safe_name)
#     content   = await file.read()
#     with open(file_path, "wb") as f:
#         f.write(content)

#     # ── Register with session so _execute_query can find it ──────────────
#     if resolved_session_id not in SESSION_FILES:
#         SESSION_FILES[resolved_session_id] = []
#     if file_path not in SESSION_FILES[resolved_session_id]:
#         SESSION_FILES[resolved_session_id].append(file_path)

#     # ── Persist metadata ──────────────────────────────────────────────────
#     meta = {
#         "file_id":       file_id,
#         "original_name": fname,
#         "stored_name":   safe_name,
#         "file_path":     file_path,
#         "session_id":    resolved_session_id,
#         "size_bytes":    len(content),
#         "status":        "processing",
#         "chunk_count":   0,
#         "uploaded_at":   time.strftime("%Y-%m-%dT%H:%M:%S"),
#     }
#     uploads.append(meta)
#     _save_uploads(uploads)

#     # ── Log to PG (optional) ──────────────────────────────────────────────
#     try:
#         pg = _get_pg()
#         if pg:
#             pg.cursor().execute(
#                 "INSERT INTO pg_user_files "
#                 "(file_id, original_name, stored_name, file_path) "
#                 "VALUES (%s::uuid, %s, %s, %s)",
#                 (file_id, fname, safe_name, file_path))
#     except Exception:
#         pass

#     # ── Background indexing ───────────────────────────────────────────────
#     background_tasks.add_task(
#         _bg_index_user_file, file_id, file_path, fname)

#     print(f"[UPLOAD] '{fname}' saved → {safe_name} "
#           f"(session={resolved_session_id})")

#     return {
#         "file_id":    file_id,
#         "filename":   fname,
#         "session_id": resolved_session_id,
#         "status":     "processing",
#         "message":    "File uploaded. Indexing in background — you can chat with it now.",
#     }


# @app.delete("/api/uploads/{file_id}")
# def delete_upload(file_id: str):
#     uploads = _load_uploads()
#     target  = next((u for u in uploads if u.get("file_id") == file_id), None)
#     if not target:
#         raise HTTPException(404, "File not found")

#     # Remove from disk
#     if os.path.exists(target.get("file_path", "")):
#         os.remove(target["file_path"])

#     # Remove from ChromaDB
#     try:
#         client  = vector_store._get_client()
#         col     = client.get_collection("user_uploads")
#         results = col.get(where={"file_id": file_id})
#         if results and results.get("ids"):
#             col.delete(ids=results["ids"])
#     except Exception:
#         pass

#     # Remove from in-memory session map
#     sid   = target.get("session_id", "")
#     fpath = target.get("file_path", "")
#     if sid and sid in SESSION_FILES:
#         SESSION_FILES[sid] = [p for p in SESSION_FILES[sid] if p != fpath]

#     _save_uploads([u for u in uploads if u.get("file_id") != file_id])
#     return {"deleted": True, "file_id": file_id}


# # ═══════════════════════════════════════════════════════════════════════════════
# #  MCP tool dispatcher  (fixes 404 on POST /api/mcp/run)
# # ═══════════════════════════════════════════════════════════════════════════════

# @app.post("/api/mcp/run")
# def mcp_run(req: MCPRunRequest):
#     """
#     Call any registered MCP tool by name.
#     Body:  { "tool": "weather", "params": {"location": "Lahore"} }
#     """
#     try:
#         from mcp_tools import dispatch, TOOL_MANIFEST
#         result = dispatch(req.tool, req.params)
#         _pg_log("pg_tool_calls", {
#             "session_id": req.session_id,
#             "tool_name":  req.tool,
#             "input_args": json.dumps(req.params),
#             "output":     json.dumps(result, default=str),
#         })
#         return {"tool": req.tool, "params": req.params, "result": result}
#     except ImportError:
#         raise HTTPException(
#             503,
#             "mcp_tools.py not found in project root. "
#             "Add it (from previous deliverables) to enable MCP.")
#     except Exception as e:
#         raise HTTPException(500, f"MCP tool error: {e}")


# @app.get("/api/mcp/tools")
# def list_mcp_tools():
#     """List all available MCP tools and their descriptions."""
#     try:
#         from mcp_tools import TOOL_MANIFEST
#         return {"tools": TOOL_MANIFEST}
#     except ImportError:
#         return {"tools": [], "error": "mcp_tools.py not installed"}


# # ═══════════════════════════════════════════════════════════════════════════════
# #  Built-in tool routes
# # ═══════════════════════════════════════════════════════════════════════════════

# @app.post("/api/tools/weather")
# def tool_weather(req: ToolRequest):
#     try:
#         from tools import get_weather, format_weather, _extract_city
#         t0     = time.time()
#         city   = _extract_city(req.query)
#         result = get_weather(city)
#         text   = format_weather(result)
#         ms     = (time.time() - t0) * 1000
#         _pg_log("pg_tool_calls", {
#             "session_id": req.session_id, "tool_name": "weather",
#             "input_args": json.dumps({"city": city}),
#             "output": json.dumps(result), "duration_ms": ms,
#         })
#         return {"tool": "weather", "city": city, "result": result, "formatted": text}
#     except ImportError:
#         # tools.py not present — use MCP weather instead
#         try:
#             from mcp_tools import dispatch
#             result = dispatch("weather", {"location": req.query})
#             return {"tool": "weather", "result": result,
#                     "formatted": str(result)}
#         except Exception as e:
#             raise HTTPException(503, f"Weather tool unavailable: {e}")


# @app.post("/api/tools/price")
# def tool_price(req: ToolRequest):
#     try:
#         from tools import get_crop_price, format_crop_price, _extract_crop_name
#         t0     = time.time()
#         crop   = _extract_crop_name(req.query)
#         result = get_crop_price(crop)
#         text   = format_crop_price(result)
#         ms     = (time.time() - t0) * 1000
#         _pg_log("pg_tool_calls", {
#             "session_id": req.session_id, "tool_name": "crop_price",
#             "input_args": json.dumps({"crop": crop}),
#             "output": json.dumps(result), "duration_ms": ms,
#         })
#         return {"tool": "crop_price", "crop": crop,
#                 "result": result, "formatted": text}
#     except ImportError:
#         raise HTTPException(503, "tools.py not installed")


# @app.post("/api/tools/calculate")
# def tool_calculate(req: ToolRequest):
#     try:
#         from tools import calculate, _extract_expr
#         t0     = time.time()
#         expr   = _extract_expr(req.query)
#         result = calculate(expr)
#         text   = (f"`{result['expression']}` = **{result['formatted']}**"
#                   if "result" in result
#                   else f"Error: {result.get('error')}")
#         ms     = (time.time() - t0) * 1000
#         _pg_log("pg_tool_calls", {
#             "session_id": req.session_id, "tool_name": "calculator",
#             "input_args": json.dumps({"expression": expr}),
#             "output": json.dumps(result), "duration_ms": ms,
#         })
#         return {"tool": "calculator", "expression": expr,
#                 "result": result, "formatted": text}
#     except ImportError:
#         raise HTTPException(503, "tools.py not installed")


# @app.post("/api/tools/sowing")
# def tool_sowing(req: ToolRequest):
#     try:
#         from tools import (get_sowing_calendar, format_sowing,
#                            _extract_crop_name, _extract_province)
#         t0     = time.time()
#         crop   = _extract_crop_name(req.query)
#         prov   = _extract_province(req.query)
#         result = get_sowing_calendar(crop, prov)
#         text   = format_sowing(result)
#         ms     = (time.time() - t0) * 1000
#         _pg_log("pg_tool_calls", {
#             "session_id": req.session_id, "tool_name": "sowing",
#             "input_args": json.dumps({"crop": crop, "province": prov}),
#             "output": json.dumps(result), "duration_ms": ms,
#         })
#         return {"tool": "sowing", "crop": crop, "province": prov,
#                 "result": result, "formatted": text}
#     except ImportError:
#         # Fall back to MCP crop_calendar
#         try:
#             from mcp_tools import dispatch
#             result = dispatch("crop_calendar", {"crop": req.query})
#             return {"tool": "sowing", "result": result,
#                     "formatted": str(result)}
#         except Exception as e:
#             raise HTTPException(503, f"Sowing tool unavailable: {e}")


# # ═══════════════════════════════════════════════════════════════════════════════
# #  PostgreSQL logs
# # ═══════════════════════════════════════════════════════════════════════════════

# @app.get("/api/logs")
# def get_logs(limit: int = 50, session_id: Optional[str] = None):
#     pg = _get_pg()
#     if not pg:
#         return {"error": "PostgreSQL not configured", "logs": []}
#     try:
#         cur = pg.cursor()
#         if session_id:
#             cur.execute(
#                 "SELECT * FROM pg_pipeline_logs WHERE session_id=%s "
#                 "ORDER BY logged_at DESC LIMIT %s",
#                 (session_id, limit))
#         else:
#             cur.execute(
#                 "SELECT * FROM pg_pipeline_logs ORDER BY logged_at DESC LIMIT %s",
#                 (limit,))
#         cols = [d[0] for d in cur.description]
#         rows = [dict(zip(cols, r)) for r in cur.fetchall()]
#         return {"logs": rows, "count": len(rows)}
#     except Exception as e:
#         return {"error": str(e), "logs": []}


# # ═══════════════════════════════════════════════════════════════════════════════
# #  PDF serving
# # ═══════════════════════════════════════════════════════════════════════════════

# @app.get("/api/pdf/{filename}")
# def serve_pdf(filename: str):
#     safe_name = os.path.basename(filename)
#     pdf_path  = os.path.join(PDF_DIR, safe_name)
#     if not os.path.exists(pdf_path):
#         return JSONResponse(
#             status_code=404,
#             content={"error": f"PDF '{safe_name}' not found in pdfs/ folder."})
#     return FileResponse(
#         pdf_path,
#         media_type="application/pdf",
#         filename=safe_name,
#         headers={"Content-Disposition": f"inline; filename={safe_name}"},
#     )


# # ═══════════════════════════════════════════════════════════════════════════════
# #  Serve React build
# # ═══════════════════════════════════════════════════════════════════════════════
# DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")
# if os.path.isdir(DIST):
#     app.mount("/assets",
#               StaticFiles(directory=os.path.join(DIST, "assets")),
#               name="assets")

#     @app.get("/{full_path:path}")
#     def serve_spa(full_path: str):
#         return FileResponse(os.path.join(DIST, "index.html"))


# # ═══════════════════════════════════════════════════════════════════════════════
# #  Entry point
# # ═══════════════════════════════════════════════════════════════════════════════
# if __name__ == "__main__":
#     import uvicorn

#     print("\n" + "="*60)
#     print("STARTUP CHECKS")
#     print("="*60)

#     _purge_orphaned_uploads()   # fix stale upload quota on restart
#     db_schema.init_db()
#     count = vector_store.collection_size()
#     print(f"  Vector store      : {count:,} chunks")
#     if count == 0:
#         print("  EMPTY — run: python main.py --index")

#     backend = os.environ.get("LLM_BACKEND", "groq").upper()
#     print(f"  LLM_BACKEND       : {backend}")
#     if backend == "GROQ" and not os.environ.get("GROQ_API_KEY"):
#         print("  ⚠️  GROQ_API_KEY is not set!")
#     if backend == "QWEN_REMOTE":
#         base  = os.environ.get("QWEN_REMOTE_BASE_URL")
#         model = os.environ.get("QWEN_REMOTE_MODEL")
#         print(f"  QWEN_REMOTE_BASE_URL : {base  or '⚠️  NOT SET'}")
#         print(f"  QWEN_REMOTE_MODEL    : {model or '⚠️  NOT SET'}")
#         if base:
#             try:
#                 import requests
#                 r = requests.get(f"{base}/v1/models", timeout=5)
#                 print(f"  Qwen /v1/models : HTTP {r.status_code}")
#             except Exception as e:
#                 print(f"  ⚠️  Could not reach Qwen remote: {e}")

#     print("="*60)
#     print("🚀 Starting API server at http://localhost:8000")
#     print("="*60 + "\n")

#     uvicorn.run(app, host="127.0.0.1", port=8001, reload=False)




"""
FastAPI bridge — Agentic RAG Platform
======================================
Endpoints:
  POST /api/chat               — sync chat
  POST /api/chat/async         — async chat + webhook
  GET  /api/jobs/{id}          — job polling
  GET  /api/status             — pipeline status
  GET  /api/health             — health check
  GET  /api/sessions           — list sessions
  GET  /api/sessions/{id}      — session history
  DELETE /api/sessions/{id}    — delete session
  PATCH /api/sessions/{id}     — rename session
  GET  /api/sessions/{id}/export — download chat as .md or .json
  POST /api/upload             — upload user file (max 3), registers for session
  GET  /api/uploads            — list uploaded files
  DELETE /api/uploads/{id}     — delete uploaded file
  POST /api/tools/weather      — weather tool
  POST /api/tools/price        — crop price tool
  POST /api/tools/calculate    — calculator tool
  POST /api/tools/sowing       — sowing calendar tool
  GET  /api/logs               — recent pipeline logs (PostgreSQL)
  GET  /api/pdf/{filename}     — serve PDF inline
  POST /api/mcp/run            — MCP tool dispatcher
"""

import os
import sys
import io
import time
import uuid
import traceback
import json
import shutil
from contextlib import redirect_stdout
from typing import Optional, List, Dict

from fastapi import (
    FastAPI, BackgroundTasks, HTTPException,
    UploadFile, File, Form
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel
import requests as _requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Ensure stdout/stderr use UTF-8 where possible (prevents UnicodeEncodeError on Windows
# when code prints emoji or other non-encodable characters). This is a surgical runtime fix
# that avoids crashing the entire process on startup due to print() of warnings containing emoji.
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

import db_schema
import vector_store
from rag_pipeline import AgenticRAGPipeline, inspect_last_query as _inspect
from rag_pipeline import build_upload_chunks
from auth_routes import router as auth_router, init_auth_schema

# ── Import project_routes only if the file exists ────────────────────────────
try:
    from project_routes import router as project_router
    _HAS_PROJECT_ROUTES = True
except ImportError:
    _HAS_PROJECT_ROUTES = False
    print("[STARTUP] project_routes.py not found — /api/projects endpoints disabled.")

# ── FIX: mcp_pdf_export was never actually imported in the active code path.
# The only import existed inside a large commented-out legacy block above,
# so /api/sessions/{id}/export/pdf called _mcp_pdf(...) which was undefined
# → NameError → caught by the generic except → HTTP 500 "Export failed".
try:
    from mcp_pdf_export import mcp_generate_pdf as _mcp_pdf
    _PDF_EXPORT_AVAILABLE = True
    print("[STARTUP] mcp_pdf_export loaded — PDF export enabled")
except ImportError as e:
    _PDF_EXPORT_AVAILABLE = False
    _mcp_pdf = None
    print(f"[STARTUP] mcp_pdf_export not found — PDF export disabled ({e})")

# ── STT (Stage 2: speech-to-text, validated standalone before this wiring) ─
try:
    from speech_layer import transcribe_audio
    _STT_AVAILABLE = True
    print("[STARTUP] speech_layer loaded — /api/stt enabled")
except ImportError as e:
    _STT_AVAILABLE = False
    transcribe_audio = None
    print(f"[STARTUP] speech_layer not found — /api/stt disabled ({e})")

# ── TTS (Stage 3: text-to-speech, MMS-TTS single engine, en + ur) ──────────
try:
    from tts import get_tts_service
    _TTS_AVAILABLE = True
    print("[STARTUP] tts loaded — /api/tts enabled")
except ImportError as e:
    _TTS_AVAILABLE = False
    get_tts_service = None
    print(f"[STARTUP] tts not found — /api/tts disabled ({e})")

# ═══════════════════════════════════════════════════════════════════════════════
#  SESSION FILES — maps session_id → list of uploaded file paths
#  MUST be defined at module level before any endpoint uses it
# ═══════════════════════════════════════════════════════════════════════════════
SESSION_FILES: Dict[str, List[str]] = {}

# ── Upload directory ──────────────────────────────────────────────────────────
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
MAX_USER_FILES = 20   # increased — auto-purge handles per-session cleanup

# ── PDF directory ─────────────────────────────────────────────────────────────
PDF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdfs")
os.makedirs(PDF_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  FastAPI app
# ═══════════════════════════════════════════════════════════════════════════════
app = FastAPI(title="Agentic RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
init_auth_schema()

if _HAS_PROJECT_ROUTES:
    app.include_router(project_router)

# ═══════════════════════════════════════════════════════════════════════════════
#  PostgreSQL logging (optional — silent if not configured)
# ═══════════════════════════════════════════════════════════════════════════════
_pg_conn = None

def _get_pg():
    global _pg_conn
    if _pg_conn is not None:
        try:
            _pg_conn.cursor().execute("SELECT 1")
            return _pg_conn
        except Exception:
            _pg_conn = None

    pg_url = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")
    if not pg_url:
        host = os.environ.get("POSTGRES_HOST")
        if not host:
            return None
        db   = os.environ.get("POSTGRES_DB", "agri_rag")
        user = os.environ.get("POSTGRES_USER", "postgres")
        pwd  = os.environ.get("POSTGRES_PASSWORD", "")
        port = os.environ.get("POSTGRES_PORT", "5432")
        pg_url = f"postgresql://{user}:{pwd}@{host}:{port}/{db}"
    try:
        import psycopg2
        _pg_conn = psycopg2.connect(pg_url)
        _pg_conn.autocommit = True
        _init_pg_schema(_pg_conn)
        return _pg_conn
    except Exception as e:
        print(f"[PG] Not available: {e}")
        return None


def _init_pg_schema(conn):
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pg_sessions (
        session_id  TEXT PRIMARY KEY,
        title       TEXT NOT NULL DEFAULT 'New Chat',
        created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS pg_messages (
        msg_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        session_id  TEXT NOT NULL,
        role        TEXT NOT NULL,
        content     TEXT NOT NULL,
        used_rag    BOOLEAN,
        tokens_used INTEGER,
        created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS pg_pipeline_logs (
        log_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        session_id  TEXT,
        query_id    TEXT,
        step_name   TEXT NOT NULL,
        input_text  TEXT,
        output_text TEXT,
        duration_ms REAL,
        status      TEXT DEFAULT 'ok',
        logged_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS pg_tool_calls (
        call_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        session_id  TEXT,
        tool_name   TEXT NOT NULL,
        input_args  JSONB,
        output      JSONB,
        duration_ms REAL,
        status      TEXT DEFAULT 'ok',
        called_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS pg_user_files (
        file_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        original_name TEXT NOT NULL,
        stored_name   TEXT NOT NULL,
        file_path     TEXT NOT NULL,
        chunk_count   INTEGER DEFAULT 0,
        status        TEXT DEFAULT 'pending',
        uploaded_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """)
    conn.commit()
    print("[PG] Schema ready.")


def _pg_log(table: str, data: dict):
    conn = _get_pg()
    if not conn:
        return
    try:
        import psycopg2.extras
        cols   = ", ".join(data.keys())
        vals   = ", ".join(["%s"] * len(data))
        values = [json.dumps(v) if isinstance(v, dict) else v for v in data.values()]
        conn.cursor().execute(f"INSERT INTO {table} ({cols}) VALUES ({vals})", values)
    except Exception as e:
        print(f"[PG] Log failed: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
#  Upload metadata helpers
# ═══════════════════════════════════════════════════════════════════════════════
_UPLOADS_META = os.path.join(UPLOAD_DIR, ".meta.json")


def _load_uploads() -> list:
    if os.path.exists(_UPLOADS_META):
        try:
            return json.load(open(_UPLOADS_META))
        except Exception:
            pass
    return []


def _save_uploads(uploads: list):
    json.dump(uploads, open(_UPLOADS_META, "w"), indent=2)


def _update_upload_status(file_id: str, status: str, chunks: int):
    uploads = _load_uploads()
    for u in uploads:
        if u.get("file_id") == file_id:
            u["status"]      = status
            u["chunk_count"] = chunks
    _save_uploads(uploads)


def _purge_orphaned_uploads():
    """On startup: remove any upload metadata entries whose file no longer exists on disk.
    This fixes 'Maximum 3 files allowed' errors caused by stale .meta.json entries."""
    uploads = _load_uploads()
    valid = [u for u in uploads if os.path.exists(u.get("file_path", ""))]
    if len(valid) < len(uploads):
        print(f"[UPLOAD] Purged {len(uploads) - len(valid)} orphaned upload record(s) from meta.")
        _save_uploads(valid)


# ═══════════════════════════════════════════════════════════════════════════════
#  Lazy pipeline singleton — THREAD-SAFE
#
#  FIX: the previous version had no lock. When multiple requests arrived at
#  once (e.g. the frontend's initial page-load firing /api/status, /api/sessions,
#  and a chat request in parallel), each one independently found _pipeline is
#  None and started its OWN AgenticRAGPipeline(), each of which loads the full
#  embedding model into RAM. Six simultaneous loads of a several-hundred-MB
#  model is exactly what produced "memory allocation of 340 bytes failed" and
#  crashed the server. A simple lock makes every request after the first one
#  just wait for the in-progress initialization instead of starting a new one.
# ═══════════════════════════════════════════════════════════════════════════════
import threading

_pipeline: Optional[AgenticRAGPipeline] = None
_pipeline_init_error: Optional[str]     = None
_pipeline_lock = threading.Lock()


def get_pipeline() -> AgenticRAGPipeline:
    global _pipeline, _pipeline_init_error

    # Fast path: already initialized, no lock needed for the common case
    if _pipeline is not None:
        return _pipeline
    if _pipeline_init_error is not None:
        raise RuntimeError(_pipeline_init_error)

    # Slow path: acquire the lock so only ONE thread actually initializes.
    # Every other concurrent caller blocks here until init finishes, then
    # falls through to the checks above on their next call — no duplicate
    # AgenticRAGPipeline() instances, no duplicate embedding-model loads.
    with _pipeline_lock:
        # Re-check inside the lock — another thread may have finished
        # initializing while we were waiting to acquire it.
        if _pipeline is not None:
            return _pipeline
        if _pipeline_init_error is not None:
            raise RuntimeError(_pipeline_init_error)

        try:
            db_schema.init_db()
            _pipeline = AgenticRAGPipeline()
        except Exception as exc:
            _pipeline_init_error = f"{type(exc).__name__}: {exc}"
            print("\n[FATAL] Pipeline failed to initialise:")
            traceback.print_exc()

    if _pipeline is None:
        raise RuntimeError(_pipeline_init_error or "Pipeline failed to initialise")
    return _pipeline


# ═══════════════════════════════════════════════════════════════════════════════
#  Pydantic models
# ═══════════════════════════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    session_id: str
    query: str
    force_web: bool = False   # UI "Web Search ON" toggle — skip RAG, search live web

class ChatResponse(BaseModel):
    response:    str
    trace:       Optional[str]       = None
    used_rag:    Optional[bool]      = None
    source_type: Optional[str]       = None   # "RAG" | "WEB" | "MCP" | "UPLOAD"
    mcp_tool:    Optional[str]       = None   # name of MCP tool if source_type=="MCP"
    sources:     Optional[List[dict]] = None  # structured sources for collapsed UI panel

class AsyncChatRequest(BaseModel):
    session_id:   str
    query:        str
    callback_url: Optional[str] = None

class JobAcceptedResponse(BaseModel):
    job_id: str
    status: str = "pending"

class JobStatusResponse(BaseModel):
    job_id:            str
    status:            str
    response:          Optional[str]  = None
    trace:             Optional[str]  = None
    used_rag:          Optional[bool] = None
    error_detail:      Optional[str]  = None
    webhook_delivered: Optional[bool] = None

class RenameRequest(BaseModel):
    title: str

class ToolRequest(BaseModel):
    query:      str
    session_id: Optional[str] = None

class MCPRunRequest(BaseModel):
    tool:       str
    params:     dict            = {}
    session_id: Optional[str]  = None


# ═══════════════════════════════════════════════════════════════════════════════
#  Retry wrapper
# ═══════════════════════════════════════════════════════════════════════════════
RETRYABLE_ERRORS = (ConnectionError, ConnectionResetError,
                    ConnectionAbortedError, TimeoutError)


def run_pipeline_with_retry(pipeline, session_id, query,
                            upload_chunks=None, upload_file_ids=None,
                            force_web=False, max_attempts=3):
    last_exc = None
    for attempt in range(1, max_attempts + 1):
        try:
            return pipeline.run(
                session_id=session_id,
                user_query=query,
                upload_chunks=upload_chunks or [],
                upload_file_ids=upload_file_ids or [],
                force_web=force_web,
            )
        except RETRYABLE_ERRORS as exc:
            last_exc = exc
            wait = attempt * 1.5
            print(f"[RETRY] Attempt {attempt}/{max_attempts} "
                  f"({type(exc).__name__}) — retrying in {wait}s")
            time.sleep(wait)
        except Exception as exc:
            msg = str(exc).lower()
            if any(kw in msg for kw in
                   ("connection", "10054", "reset", "timeout", "aborted")):
                last_exc = exc
                time.sleep(attempt * 1.5)
                continue
            raise
    raise last_exc


# ═══════════════════════════════════════════════════════════════════════════════
#  Core query executor (shared by sync + async paths)
# ═══════════════════════════════════════════════════════════════════════════════

def _execute_query(session_id: str,
                   query: str,
                   force_web: bool = False) -> tuple:
    """
    Returns (response, trace, used_rag, source_type, mcp_tool, sources).
      source_type: "RAG" | "WEB" | "MCP" | "UPLOAD"
      mcp_tool:    name of the MCP tool if source_type=="MCP", else None
      sources:     structured sources list from PipelineResult.sources, or []
    """
    if not force_web and vector_store.collection_size() == 0:
        return (
            "⚠️ The knowledge base is empty. "
            "Run `python main.py --index` first, then restart the API server.",
            None, None, None, None, [],
        )

    pipeline = get_pipeline()

    # ── Gather upload chunks + file_ids for this session ────────────────────
    # FIX: previously only `upload_chunks` (freshly re-extracted from disk,
    # on EVERY chat message) was ever passed to pipeline.run(). `upload_file_ids`
    # was never passed, so rag_pipeline's Stage A — vector search over the
    # properly embedded `user_uploads` ChromaDB collection built by
    # _bg_index_user_file() — never ran. All chat answers about uploaded docs
    # were falling back to a placeholder-scored BM25 pass over freshly
    # re-extracted raw text, discarding the real embeddings entirely and
    # re-running extraction (including Docling, if installed) on every message.
    #
    # Fix: look up this session's indexed file_ids from upload metadata and
    # pass them through, so the real vector index gets queried. Only fall
    # back to re-extracting from disk for files that are NOT YET indexed
    # (still processing in the background) — that's the one case where the
    # vector collection genuinely has nothing yet.
    upload_chunks:   List[dict] = []
    upload_file_ids: List[str] = []
    has_uploads = False
    session_file_paths = SESSION_FILES.get(session_id, [])
    print(f"  [SESSION_FILES] session={session_id!r} has {len(session_file_paths)} file(s) registered")

    _uploads_meta = {u["file_path"]: u for u in _load_uploads()
                      if u.get("session_id") == session_id}

    for fpath in session_file_paths:
        if not os.path.exists(fpath):
            print(f"  [SESSION_FILES] WARNING: file no longer on disk: {fpath}")
            continue

        meta = _uploads_meta.get(fpath)
        if meta and meta.get("status") == "indexed" and meta.get("file_id"):
            upload_file_ids.append(meta["file_id"])
            has_uploads = True
        else:
            # Not indexed yet (or metadata missing) — fall back to raw
            # extraction so the user isn't left without an answer while
            # background indexing is still running.
            try:
                chunks = build_upload_chunks(fpath)
                upload_chunks.extend(chunks)
                if chunks:
                    has_uploads = True
            except Exception as e:
                print(f"  [SESSION_FILES] Could not load '{fpath}': {e}")

    response = run_pipeline_with_retry(
        pipeline, session_id, query,
        upload_chunks=upload_chunks,
        upload_file_ids=upload_file_ids,
        force_web=force_web,
    )

    # ── FIX: pipeline.run() returns a PipelineResult object, not a plain
    # string. Passing that object straight into ChatResponse(response=...)
    # is what caused: "ValidationError: response — Input should be a valid
    # string [input_type=PipelineResult]". Unpack it into a real string here,
    # and grab .sources / .source_type / .used_rag directly from it instead
    # of re-deriving them from SQL step-name guessing below.
    _pipeline_sources = []
    if hasattr(response, "answer"):
        pipeline_result   = response
        response          = pipeline_result.answer
        _pipeline_sources = pipeline_result.sources or []
        _pipeline_source_type = pipeline_result.source_type
        _pipeline_used_rag    = pipeline_result.used_rag
    else:
        # Backward-compat: some rag_pipeline.py versions still return a
        # plain string. In that case fall through to the SQL-based
        # source_type detection below, unchanged.
        _pipeline_source_type = None
        _pipeline_used_rag    = None

    # ── Read used_rag + step info from SQLite to determine source_type ────
    used_rag    = _pipeline_used_rag
    source_type = _pipeline_source_type
    mcp_tool    = None
    trace_lines = []

    try:
        conn = db_schema.get_connection()

        # Get latest query_id for this session
        q_row = conn.execute("""
            SELECT q.query_id, r.used_rag
            FROM queries q
            LEFT JOIN responses r ON r.query_id = q.query_id
            WHERE q.session_id = ?
            ORDER BY q.timestamp DESC LIMIT 1
        """, (session_id,)).fetchone()

        if q_row:
            # FIX: only overwrite with the DB-derived value if PipelineResult
            # didn't already give us a definitive answer above. Previously
            # this always overwrote used_rag from the DB even when we had a
            # reliable value straight from the pipeline object.
            if used_rag is None:
                used_rag = bool(q_row["used_rag"]) if q_row["used_rag"] is not None else None
            qid = q_row["query_id"]

            # Read all pipeline steps for trace panel
            steps = conn.execute("""
                SELECT step_name, duration_ms, status, input_text, output_text
                FROM pipeline_steps WHERE query_id=? ORDER BY step_order
            """, (qid,)).fetchall()

            for s in steps:
                trace_lines.append(
                    f"[{s['step_name']}] {s['duration_ms']:.0f}ms | {s['status']}"
                )
                # FIX: only run this MCP-detection-from-step-names fallback
                # when the pipeline itself didn't already tell us source_type.
                # Previously this ran unconditionally, and 'mcp_dispatch' gets
                # logged even when the tool check returns NO_TOOL — so every
                # single response got tagged "MCP" regardless of what actually
                # answered the question.
                if _pipeline_source_type is None and (
                    s["step_name"] in ("mcp_dispatch", "mcp_tool") or
                    s["step_name"].startswith("mcp_")
                ):
                    source_type = "MCP"
                    try:
                        out = s["output_text"] or ""
                        if "MCP Tool:" in out:
                            mcp_tool = out.split("MCP Tool:")[1].split("]")[0].strip()
                    except Exception:
                        pass

            # Determine source_type from step names if MCP not detected above
            if source_type is None:
                step_names = [s["step_name"] for s in steps]
                if has_uploads and used_rag:
                    source_type = "UPLOAD"
                elif used_rag:
                    source_type = "RAG"
                elif any("tavily" in n or "web_search" in n or "web" in n
                         for n in step_names):
                    source_type = "WEB"
                elif force_web:
                    source_type = "WEB"   # explicit toggle, even if step names didn't match
                else:
                    source_type = "WEB"   # fallback path also uses web search

        conn.close()
    except Exception as e:
        print(f"  [EXECUTE] DB read error: {e}")

    # ── Also check if MCP was called (logged in mcp_context) ─────────────
    # FIX: only fall back to this text-scan when pipeline didn't already
    # tell us. Also guard against `response` not being a string here.
    if _pipeline_source_type is None and source_type != "MCP":
        if isinstance(response, str) and "[MCP Tool:" in response:
            source_type = "MCP"
            try:
                mcp_tool = response.split("[MCP Tool:")[1].split("]")[0].strip()
            except Exception:
                pass

    # ── Build trace string ─────────────────────────────────────────────────
    trace = None
    if trace_lines:
        trace = "\n".join(trace_lines)
    else:
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                _inspect()
            trace = buf.getvalue().strip() or None
        except Exception:
            pass

    # ── FINAL SAFETY NET ────────────────────────────────────────────────────
    # No matter what happened above, response MUST be a plain string before
    # it leaves this function — otherwise Pydantic's ChatResponse(response=...)
    # raises "Input should be a valid string [input_type=PipelineResult]".
    if not isinstance(response, str):
        if hasattr(response, "answer"):
            _pipeline_sources = getattr(response, "sources", None) or _pipeline_sources
            if source_type is None:
                source_type = getattr(response, "source_type", None)
            if used_rag is None:
                used_rag = getattr(response, "used_rag", None)
            response = response.answer
        else:
            response = str(response)

    return response, trace, used_rag, source_type, mcp_tool, _pipeline_sources


def _friendly_error(exc: Exception) -> str:
    msg = str(exc)
    if any(kw in msg.lower() for kw in
           ("connection", "10054", "reset", "aborted", "timeout")):
        return (
            "⚠️ The remote model connection dropped mid-response. "
            "This is usually transient — please try again. "
            "If it keeps happening, the Qwen server/tunnel may need restarting."
        )
    return f"❌ Backend error: {type(exc).__name__}: {exc}"


# ═══════════════════════════════════════════════════════════════════════════════
#  Health / Status
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/health")
def health():
    try:
        db_schema.init_db()
        count = vector_store.collection_size()
        return {"ok": True, "chunks": count}
    except Exception as exc:
        return JSONResponse(status_code=500,
                            content={"ok": False, "error": str(exc)})


@app.get("/api/status")
def status():
    backend = os.environ.get("LLM_BACKEND", "groq").upper()
    model_map = {
        "GROQ":        os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant"),
        "QWEN_REMOTE": os.environ.get("QWEN_REMOTE_MODEL", "Qwen (remote)"),
        "QWEN_LOCAL":  "Qwen (local)",
        "OLLAMA":      os.environ.get("OLLAMA_MODEL", "ollama"),
    }
    model_name = model_map.get(backend, backend)
    try:
        chunk_count = vector_store.collection_size()
    except Exception as exc:
        return {"chunk_count": 0, "backend": backend,
                "model": model_name, "vector_store_error": str(exc)}

    return {
        "chunk_count":     chunk_count,
        "backend":         backend,
        "model":           model_name,
        "embedding_model": vector_store.EMBEDDING_MODEL,
        "vector_db":       "ChromaDB",
        "retrieval":       "BM25 + Sentence Embeddings",
        "fusion":          "RRF",
        "pipeline_ready":  _pipeline is not None,
        "pipeline_error":  _pipeline_init_error,
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  Sync Chat
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    t0 = time.time()
    try:
        response, trace, used_rag, source_type, mcp_tool, sources = \
            _execute_query(req.session_id, req.query, force_web=req.force_web)
        print(f"[CHAT] {time.time()-t0:.2f}s  "
              f"query={req.query[:60]!r}  "
              f"force_web={req.force_web}  "
              f"source={source_type}  used_rag={used_rag}  mcp_tool={mcp_tool}  "
              f"sources={len(sources or [])}")
        # Belt-and-braces: never let a non-string reach the Pydantic model
        if not isinstance(response, str):
            response = getattr(response, "answer", None) or str(response)

        return ChatResponse(
            response=response,
            trace=trace,
            used_rag=used_rag,
            source_type=source_type,
            mcp_tool=mcp_tool,
            sources=sources or [],
        )
    except Exception as exc:
        print("\n" + "="*70)
        print("[ERROR] /api/chat failed")
        traceback.print_exc()
        print("="*70 + "\n")
        return JSONResponse(
            status_code=500,
            content={"response": _friendly_error(exc),
                     "trace": None, "error_detail": str(exc)},
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  Async Chat + Webhook
# ═══════════════════════════════════════════════════════════════════════════════
WEBHOOK_MAX_ATTEMPTS = 3
WEBHOOK_TIMEOUT      = 10


def _deliver_webhook(job_id: str, callback_url: str, payload: dict):
    conn = db_schema.get_connection()
    for attempt in range(1, WEBHOOK_MAX_ATTEMPTS + 1):
        try:
            resp = _requests.post(callback_url, json=payload,
                                  timeout=WEBHOOK_TIMEOUT)
            conn.execute("UPDATE jobs SET webhook_attempts=? WHERE job_id=?",
                         (attempt, job_id))
            if resp.status_code < 300:
                conn.execute(
                    "UPDATE jobs SET webhook_delivered=1 WHERE job_id=?",
                    (job_id,))
                conn.commit()
                conn.close()
                return
        except Exception as exc:
            conn.execute("UPDATE jobs SET webhook_attempts=? WHERE job_id=?",
                         (attempt, job_id))
            print(f"[WEBHOOK] job {job_id} attempt {attempt} failed: {exc}")
        conn.commit()
        if attempt < WEBHOOK_MAX_ATTEMPTS:
            time.sleep(attempt * 2)
    conn.close()


def _process_job(job_id: str, session_id: str,
                 query: str, callback_url: Optional[str]):
    conn = db_schema.get_connection()
    conn.execute("UPDATE jobs SET status='running' WHERE job_id=?", (job_id,))
    conn.commit()
    conn.close()

    try:
        response, trace, used_rag, source_type, mcp_tool, sources = \
            _execute_query(session_id, query)
        conn = db_schema.get_connection()
        conn.execute("""
            UPDATE jobs
            SET status='done', result_response=?, result_trace=?,
                used_rag=?, completed_at=datetime('now')
            WHERE job_id=?
        """, (response, trace,
              int(used_rag) if used_rag is not None else None, job_id))
        conn.commit()
        conn.close()
        status_val, error_detail = "done", None
    except Exception as exc:
        traceback.print_exc()
        response, trace, used_rag, source_type, mcp_tool, sources = \
            _friendly_error(exc), None, None, None, None, []
        conn = db_schema.get_connection()
        conn.execute("""
            UPDATE jobs
            SET status='error', error_detail=?, completed_at=datetime('now')
            WHERE job_id=?
        """, (str(exc), job_id))
        conn.commit()
        conn.close()
        status_val, error_detail = "error", str(exc)

    if callback_url:
        _deliver_webhook(job_id, callback_url, {
            "job_id": job_id, "session_id": session_id,
            "status": status_val, "response": response,
            "trace": trace, "used_rag": used_rag,
            "error_detail": error_detail,
        })


@app.post("/api/chat/async", response_model=JobAcceptedResponse, status_code=202)
def chat_async(req: AsyncChatRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    conn   = db_schema.get_connection()
    conn.execute("INSERT OR IGNORE INTO sessions (session_id) VALUES (?)",
                 (req.session_id,))
    conn.execute(
        "INSERT INTO jobs (job_id, session_id, query, status, callback_url) "
        "VALUES (?,?,?,'pending',?)",
        (job_id, req.session_id, req.query, req.callback_url))
    conn.commit()
    conn.close()
    background_tasks.add_task(
        _process_job, job_id, req.session_id, req.query, req.callback_url)
    print(f"[ASYNC] queued job {job_id}")
    return JobAcceptedResponse(job_id=job_id)


@app.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: str):
    conn = db_schema.get_connection()
    row  = conn.execute("SELECT * FROM jobs WHERE job_id=?",
                        (job_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Job not found")
    return JobStatusResponse(
        job_id=row["job_id"],
        status=row["status"],
        response=row["result_response"],
        trace=row["result_trace"],
        used_rag=bool(row["used_rag"]) if row["used_rag"] is not None else None,
        error_detail=row["error_detail"],
        webhook_delivered=bool(row["webhook_delivered"]),
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  Session endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/sessions")
def list_sessions():
    conn = db_schema.get_connection()
    try:
        # Ensure title column exists
        try:
            conn.execute("ALTER TABLE sessions ADD COLUMN title TEXT")
            conn.commit()
        except Exception:
            pass

        rows = conn.execute("""
            SELECT
                s.session_id,
                s.created_at,
                s.title,
                COUNT(q.query_id) AS message_count,
                (SELECT original_query FROM queries
                 WHERE session_id = s.session_id
                 ORDER BY timestamp ASC LIMIT 1) AS first_query,
                (SELECT MAX(timestamp) FROM queries
                 WHERE session_id = s.session_id) AS last_activity
            FROM sessions s
            JOIN queries q ON q.session_id = s.session_id
            GROUP BY s.session_id
            ORDER BY last_activity DESC
            LIMIT 100
        """).fetchall()
        return {
            "sessions": [
                {
                    "session_id":    r["session_id"],
                    "created_at":    r["created_at"],
                    "title":         r["title"],
                    "message_count": r["message_count"],
                    "preview":       (r["title"] or r["first_query"] or "")[:80],
                    "last_activity": r["last_activity"],
                }
                for r in rows
            ]
        }
    finally:
        conn.close()


@app.get("/api/sessions/{session_id}")
def get_session_history(session_id: str):
    conn = db_schema.get_connection()
    try:
        rows = conn.execute("""
            SELECT q.query_id, q.original_query, q.timestamp AS query_ts,
                   r.final_response, r.timestamp AS response_ts, r.used_rag
            FROM queries q
            LEFT JOIN responses r ON r.query_id = q.query_id
            WHERE q.session_id = ?
            ORDER BY q.timestamp ASC
        """, (session_id,)).fetchall()
        messages = []
        for r in rows:
            messages.append({"role": "user",
                             "content": r["original_query"],
                             "ts": r["query_ts"]})
            if r["final_response"]:
                messages.append({
                    "role":     "assistant",
                    "content":  r["final_response"],
                    "ts":       r["response_ts"],
                    "used_rag": bool(r["used_rag"]) if r["used_rag"] is not None else None,
                })
        return {"session_id": session_id, "messages": messages}
    finally:
        conn.close()


@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str):
    conn = db_schema.get_connection()
    try:
        query_ids = [r["query_id"] for r in conn.execute(
            "SELECT query_id FROM queries WHERE session_id=?",
            (session_id,)).fetchall()]
        for qid in query_ids:
            conn.execute("DELETE FROM responses WHERE query_id=?", (qid,))
            step_ids = [r["step_id"] for r in conn.execute(
                "SELECT step_id FROM pipeline_steps WHERE query_id=?",
                (qid,)).fetchall()]
            for sid in step_ids:
                conn.execute("DELETE FROM llm_calls WHERE step_id=?", (sid,))
            conn.execute("DELETE FROM retrieved_docs WHERE query_id=?", (qid,))
            conn.execute("DELETE FROM pipeline_steps WHERE query_id=?", (qid,))
        conn.execute("DELETE FROM queries WHERE session_id=?", (session_id,))
        conn.execute("DELETE FROM sessions WHERE session_id=?", (session_id,))
        conn.commit()
        # Also clear session files from memory
        SESSION_FILES.pop(session_id, None)
        return {"deleted": True, "session_id": session_id}
    finally:
        conn.close()


@app.patch("/api/sessions/{session_id}")
def rename_session(session_id: str, req: RenameRequest):
    conn = db_schema.get_connection()
    row  = conn.execute("SELECT session_id FROM sessions WHERE session_id=?",
                        (session_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Session not found")

    conn = db_schema.get_connection()
    try:
        conn.execute("ALTER TABLE sessions ADD COLUMN title TEXT")
        conn.commit()
    except Exception:
        pass
    conn.execute("UPDATE sessions SET title=? WHERE session_id=?",
                 (req.title.strip(), session_id))
    conn.commit()
    conn.close()

    try:
        pg = _get_pg()
        if pg:
            pg.cursor().execute(
                "INSERT INTO pg_sessions (session_id, title) VALUES (%s,%s) "
                "ON CONFLICT (session_id) DO UPDATE "
                "SET title=EXCLUDED.title, updated_at=NOW()",
                (session_id, req.title.strip()))
    except Exception:
        pass

    return {"session_id": session_id, "title": req.title.strip()}


@app.get("/api/sessions/{session_id}/export")
def export_session(session_id: str, format: str = "markdown"):
    conn = db_schema.get_connection()
    try:
        session_row = conn.execute(
            "SELECT session_id, created_at, title FROM sessions WHERE session_id=?",
            (session_id,)).fetchone()
        if not session_row:
            raise HTTPException(404, "Session not found")
        rows = conn.execute("""
            SELECT q.original_query, q.timestamp AS query_ts,
                   r.final_response, r.timestamp AS response_ts, r.used_rag
            FROM queries q
            LEFT JOIN responses r ON r.query_id = q.query_id
            WHERE q.session_id = ?
            ORDER BY q.timestamp ASC
        """, (session_id,)).fetchall()
    finally:
        conn.close()

    title     = session_row["title"] or "Untitled Chat"
    safe_base = "".join(
        c if c.isalnum() or c in " -_" else "" for c in title
    ).strip() or session_id[:8]

    if format == "json":
        payload = {
            "session_id": session_id,
            "title":      title,
            "created_at": session_row["created_at"],
            "messages": [
                {
                    "user":         r["original_query"],
                    "user_ts":      r["query_ts"],
                    "assistant":    r["final_response"],
                    "assistant_ts": r["response_ts"],
                    "used_rag":     bool(r["used_rag"]) if r["used_rag"] is not None else None,
                }
                for r in rows
            ],
        }
        return Response(
            content=json.dumps(payload, indent=2),
            media_type="application/json",
            headers={"Content-Disposition":
                     f'attachment; filename="{safe_base}.json"'},
        )

    lines = [f"# {title}", "",
             f"_Exported {time.strftime('%Y-%m-%d %H:%M')} · "
             f"session `{session_id[:8]}…`_", ""]
    for r in rows:
        lines += [f"**You** _{r['query_ts']}_", "", r["original_query"], ""]
        if r["final_response"]:
            tag = " (web/direct)" if r["used_rag"] is False else ""
            lines += [f"**Assistant**{tag} _{r['response_ts']}_",
                      "", r["final_response"], ""]
        lines += ["---", ""]

    return Response(
        content="\n".join(lines),
        media_type="text/markdown",
        headers={"Content-Disposition":
                 f'attachment; filename="{safe_base}.md"'},
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  PDF Export via MCP
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/sessions/{session_id}/export/pdf")
def export_session_pdf(session_id: str):
    """
    MCP PDF Export Tool
    -------------------
    Flow:
      Frontend PDF button
        → GET /api/sessions/{id}/export/pdf
        → mcp_generate_pdf() reads: chat messages, pipeline steps,
          retrieved sources, LLM call metadata from SQLite
        → Builds styled HTML report
        → Converts HTML → PDF via weasyprint (falls back to HTML)
        → Browser triggers download

    Install weasyprint for true PDF output:
        pip install weasyprint
    """
    if not _PDF_EXPORT_AVAILABLE:
        raise HTTPException(503, "PDF export module not loaded on the server — "
                             "check startup logs for mcp_pdf_export import error.")

    conn = db_schema.get_connection()
    try:
        result = _mcp_pdf(session_id, conn)
    except Exception as e:
        raise HTTPException(500, f"PDF generation failed: {e}")
    finally:
        conn.close()

    if result["type"] == "error":
        raise HTTPException(404, result["detail"])

    if result["type"] == "pdf":
        return Response(
            content=result["bytes"],
            media_type="application/pdf",
            headers={
                "Content-Disposition":
                    f'attachment; filename="{result["filename"]}"',
                "X-Export-Type": "pdf",
            },
        )
    else:
        # HTML fallback (weasyprint not installed)
        return Response(
            content=result["html"],
            media_type="text/html",
            headers={
                "Content-Disposition":
                    f'attachment; filename="{result["filename"]}"',
                "X-Export-Type": "html",
            },
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  File upload
# ═══════════════════════════════════════════════════════════════════════════════

def _bg_index_user_file(file_id: str, file_path: str, original_name: str):
    """Background: extract + embed uploaded file into ChromaDB user_uploads."""
    try:
        from rag_pipeline import build_upload_chunks as _buc
        chunks = _buc(file_path, source_label=original_name)
        if not chunks:
            _update_upload_status(file_id, "error", 0)
            return

        client = vector_store._get_client()
        ef     = vector_store._get_ef()
        col    = client.get_or_create_collection(
            name="user_uploads",
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )
        texts, ids, metas = [], [], []
        for chunk in chunks:
            texts.append(chunk["chunk_text"])
            ids.append(str(uuid.uuid4()))
            metas.append({
                "source_file":  original_name,
                "page_num":     chunk.get("page_num", 0),
                "file_id":      file_id,
                "user_upload":  True,
            })
        for i in range(0, len(texts), 128):
            col.add(documents=texts[i:i+128],
                    ids=ids[i:i+128],
                    metadatas=metas[i:i+128])

        _update_upload_status(file_id, "indexed", len(chunks))
        print(f"[UPLOAD] '{original_name}' → {len(chunks)} chunks in user_uploads")
    except Exception as e:
        _update_upload_status(file_id, "error", 0)
        print(f"[UPLOAD] Background indexing error: {e}")


@app.get("/api/uploads")
def list_uploads():
    return {"uploads": _load_uploads()}


@app.post("/api/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file:       UploadFile = File(...),
    # Accept both naming conventions from the frontend
    session_id: Optional[str] = Form(None),
    sessionId:  Optional[str] = Form(None),
):
    """
    Upload a PDF / TXT / DOCX (max 3 at any time).
    Accepts `session_id` or `sessionId` from the frontend form.
    The file is:
      1. Saved to disk under user_uploads/
      2. Registered in SESSION_FILES[session_id] so subsequent chat
         calls in this session can find and search it.
      3. Indexed into ChromaDB in the background.
    """
    # Accept either field name from the frontend
    resolved_session_id = session_id or sessionId or "global"

    # ── File type check ───────────────────────────────────────────────────
    allowed = {".pdf", ".txt", ".docx"}
    fname   = file.filename or ""
    ext     = os.path.splitext(fname)[1].lower()
    if ext not in allowed:
        raise HTTPException(
            400, f"File type '{ext}' not allowed. Supported: {', '.join(allowed)}")

    # ── Auto-purge previous uploads for this session so quota is never hit ────
    uploads = _load_uploads()
    old_for_session = [u for u in uploads if u.get('session_id') == resolved_session_id]
    for old in old_for_session:
        try:
            if os.path.exists(old.get('file_path', '')):
                os.remove(old['file_path'])
        except Exception:
            pass
        try:
            _client = vector_store._get_client()
            _col    = _client.get_collection('user_uploads')
            _res    = _col.get(where={'file_id': old['file_id']})
            if _res and _res.get('ids'):
                _col.delete(ids=_res['ids'])
        except Exception:
            pass
        fpath = old.get('file_path', '')
        sid   = old.get('session_id', '')
        if sid and sid in SESSION_FILES:
            SESSION_FILES[sid] = [p for p in SESSION_FILES[sid] if p != fpath]
        print(f"[UPLOAD] Auto-purged '{old.get('original_name')}' for session {resolved_session_id[:8]}")
    uploads = [u for u in uploads if u.get('session_id') != resolved_session_id]
    _save_uploads(uploads)

    # ── Safety-net quota check ────────────────────────────────────────────────────
    if len(uploads) >= MAX_USER_FILES:
        raise HTTPException(
            400,
            f'Server storage full ({MAX_USER_FILES} files). An admin must clear old uploads.')
    # ── Save to disk ──────────────────────────────────────────────────────
    file_id   = str(uuid.uuid4())
    safe_name = f"{file_id}{ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    content   = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # ── Register with session so _execute_query can find it ──────────────
    if resolved_session_id not in SESSION_FILES:
        SESSION_FILES[resolved_session_id] = []
    if file_path not in SESSION_FILES[resolved_session_id]:
        SESSION_FILES[resolved_session_id].append(file_path)

    # ── Persist metadata ──────────────────────────────────────────────────
    meta = {
        "file_id":       file_id,
        "original_name": fname,
        "stored_name":   safe_name,
        "file_path":     file_path,
        "session_id":    resolved_session_id,
        "size_bytes":    len(content),
        "status":        "processing",
        "chunk_count":   0,
        "uploaded_at":   time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    uploads.append(meta)
    _save_uploads(uploads)

    # ── Log to PG (optional) ──────────────────────────────────────────────
    try:
        pg = _get_pg()
        if pg:
            pg.cursor().execute(
                "INSERT INTO pg_user_files "
                "(file_id, original_name, stored_name, file_path) "
                "VALUES (%s::uuid, %s, %s, %s)",
                (file_id, fname, safe_name, file_path))
    except Exception:
        pass

    # ── Background indexing ───────────────────────────────────────────────
    background_tasks.add_task(
        _bg_index_user_file, file_id, file_path, fname)

    print(f"[UPLOAD] '{fname}' saved → {safe_name} "
          f"(session={resolved_session_id})")

    return {
        "file_id":    file_id,
        "filename":   fname,
        "session_id": resolved_session_id,
        "status":     "processing",
        "message":    "File uploaded. Indexing in background — you can chat with it now.",
    }


@app.delete("/api/uploads/{file_id}")
def delete_upload(file_id: str):
    uploads = _load_uploads()
    target  = next((u for u in uploads if u.get("file_id") == file_id), None)
    if not target:
        raise HTTPException(404, "File not found")

    # Remove from disk
    if os.path.exists(target.get("file_path", "")):
        os.remove(target["file_path"])

    # Remove from ChromaDB
    try:
        client  = vector_store._get_client()
        col     = client.get_collection("user_uploads")
        results = col.get(where={"file_id": file_id})
        if results and results.get("ids"):
            col.delete(ids=results["ids"])
    except Exception:
        pass

    # Remove from in-memory session map
    sid   = target.get("session_id", "")
    fpath = target.get("file_path", "")
    if sid and sid in SESSION_FILES:
        SESSION_FILES[sid] = [p for p in SESSION_FILES[sid] if p != fpath]

    _save_uploads([u for u in uploads if u.get("file_id") != file_id])
    return {"deleted": True, "file_id": file_id}


# ═══════════════════════════════════════════════════════════════════════════════
#  STT — Speech-to-Text  (Stage 2 of the multilingual voice pipeline)
#  Validated standalone via test_speech_layer.py before this wiring:
#    - medium model + agriculture vocabulary hint correctly transcribes
#      both English and Urdu, including domain terms like گندم (wheat)
# ═══════════════════════════════════════════════════════════════════════════════

class STTResponse(BaseModel):
    text:       str
    language:   str
    confidence: float
    duration:   float


@app.post("/api/stt", response_model=STTResponse)
async def speech_to_text(
    audio:    UploadFile = File(...),
    language: Optional[str] = Form(None),   # "ur" | "en" | None (auto-detect)
):
    """
    Transcribe an uploaded audio file to text.

    Accepts any format faster-whisper/ffmpeg can decode: .wav, .mp3, .m4a,
    .webm (the format browsers record to via MediaRecorder), .ogg.

    Returns the SAME shape validated in test_speech_layer.py:
        { text, language, confidence, duration }

    This endpoint does NOT call the chat pipeline — it only transcribes.
    The frontend is expected to take the returned `text` and send it to
    the existing /api/chat endpoint as a normal text query. This keeps STT
    and the RAG/translation pipeline as separate, independently-testable
    stages, matching how they were validated.
    """
    if not _STT_AVAILABLE:
        raise HTTPException(503, "STT module not loaded on the server — "
                             "check startup logs for speech_layer import error.")

    allowed_ext = {".wav", ".mp3", ".m4a", ".webm", ".ogg", ".mp4", ".flac"}
    fname = audio.filename or "audio"
    ext   = os.path.splitext(fname)[1].lower()
    if ext not in allowed_ext:
        raise HTTPException(
            400, f"Audio type '{ext}' not supported. Use: {', '.join(sorted(allowed_ext))}")

    # ── Save to a temp file — faster-whisper reads from disk, not from
    # an in-memory buffer, and ffmpeg (used internally for decoding)
    # needs a real file path.
    tmp_dir = os.path.join(UPLOAD_DIR, "_stt_tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_path = os.path.join(tmp_dir, f"{uuid.uuid4().hex}{ext}")

    try:
        content = await audio.read()
        with open(tmp_path, "wb") as f:
            f.write(content)

        result = transcribe_audio(tmp_path, language_hint=language)

        return STTResponse(
            text=result["text"],
            language=result["language"],
            confidence=result["confidence"],
            duration=result["duration"],
        )
    except Exception as e:
        print(f"[STT] Transcription failed: {e}")
        raise HTTPException(500, f"Transcription failed: {e}")
    finally:
        # Always clean up the temp audio file, even on failure
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════════
#  TTS — Text-to-Speech  (Stage 3: Meta MMS-TTS, single engine, en + ur)
#  Validated standalone via test_tts.py before this wiring.
# ═══════════════════════════════════════════════════════════════════════════════

class TTSRequest(BaseModel):
    text:     str
    language: str = "en"   # "en" | "ur" | "roman_ur" | "mixed"


@app.post("/api/tts")
async def text_to_speech(req: TTSRequest):
    """
    Generate speech audio from text.

    Request:  { "text": "...", "language": "ur" }
    Response: audio/wav bytes

    By the time text reaches here, your chat pipeline has already
    translated the answer into native Urdu script (if needed) before
    returning it to the frontend — so "roman_ur"/"mixed" are treated the
    same as "ur": the text is already correct, just route to the Urdu
    MMS-TTS model.

    This endpoint does NOT call the chat pipeline — same separation-of-
    concerns principle as /api/stt.
    """
    if not _TTS_AVAILABLE:
        raise HTTPException(503, "TTS module not loaded on the server — "
                             "check startup logs for tts.py import error.")

    text = req.text.strip()
    if not text:
        raise HTTPException(400, "Empty text — nothing to speak.")

    lang = req.language.lower().strip()
    if lang in ("roman_ur", "mixed"):
        lang = "ur"

    try:
        service = get_tts_service()
        wav_bytes, mime_type = service.speak(text, lang)
        return Response(content=wav_bytes, media_type=mime_type)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        print(f"[TTS] Synthesis failed: {e}")
        raise HTTPException(500, f"TTS synthesis failed: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
#  MCP tool dispatcher  (fixes 404 on POST /api/mcp/run)
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/mcp/run")
def mcp_run(req: MCPRunRequest):
    """
    Call any registered MCP tool by name.
    Body:  { "tool": "weather", "params": {"location": "Lahore"} }
    """
    try:
        from mcp_tools import dispatch, TOOL_MANIFEST
        result = dispatch(req.tool, req.params)
        _pg_log("pg_tool_calls", {
            "session_id": req.session_id,
            "tool_name":  req.tool,
            "input_args": json.dumps(req.params),
            "output":     json.dumps(result, default=str),
        })
        return {"tool": req.tool, "params": req.params, "result": result}
    except ImportError:
        raise HTTPException(
            503,
            "mcp_tools.py not found in project root. "
            "Add it (from previous deliverables) to enable MCP.")
    except Exception as e:
        raise HTTPException(500, f"MCP tool error: {e}")


@app.get("/api/mcp/tools")
def list_mcp_tools():
    """List all available MCP tools and their descriptions."""
    try:
        from mcp_tools import TOOL_MANIFEST
        return {"tools": TOOL_MANIFEST}
    except ImportError:
        return {"tools": [], "error": "mcp_tools.py not installed"}


# ═══════════════════════════════════════════════════════════════════════════════
#  Built-in tool routes
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/tools/weather")
def tool_weather(req: ToolRequest):
    try:
        from tools import get_weather, format_weather, _extract_city
        t0     = time.time()
        city   = _extract_city(req.query)
        result = get_weather(city)
        text   = format_weather(result)
        ms     = (time.time() - t0) * 1000
        _pg_log("pg_tool_calls", {
            "session_id": req.session_id, "tool_name": "weather",
            "input_args": json.dumps({"city": city}),
            "output": json.dumps(result), "duration_ms": ms,
        })
        return {"tool": "weather", "city": city, "result": result, "formatted": text}
    except ImportError:
        # tools.py not present — use MCP weather instead
        try:
            from mcp_tools import dispatch
            result = dispatch("weather", {"location": req.query})
            return {"tool": "weather", "result": result,
                    "formatted": str(result)}
        except Exception as e:
            raise HTTPException(503, f"Weather tool unavailable: {e}")


@app.post("/api/tools/price")
def tool_price(req: ToolRequest):
    try:
        from tools import get_crop_price, format_crop_price, _extract_crop_name
        t0     = time.time()
        crop   = _extract_crop_name(req.query)
        result = get_crop_price(crop)
        text   = format_crop_price(result)
        ms     = (time.time() - t0) * 1000
        _pg_log("pg_tool_calls", {
            "session_id": req.session_id, "tool_name": "crop_price",
            "input_args": json.dumps({"crop": crop}),
            "output": json.dumps(result), "duration_ms": ms,
        })
        return {"tool": "crop_price", "crop": crop,
                "result": result, "formatted": text}
    except ImportError:
        raise HTTPException(503, "tools.py not installed")


@app.post("/api/tools/calculate")
def tool_calculate(req: ToolRequest):
    try:
        from tools import calculate, _extract_expr
        t0     = time.time()
        expr   = _extract_expr(req.query)
        result = calculate(expr)
        text   = (f"`{result['expression']}` = **{result['formatted']}**"
                  if "result" in result
                  else f"Error: {result.get('error')}")
        ms     = (time.time() - t0) * 1000
        _pg_log("pg_tool_calls", {
            "session_id": req.session_id, "tool_name": "calculator",
            "input_args": json.dumps({"expression": expr}),
            "output": json.dumps(result), "duration_ms": ms,
        })
        return {"tool": "calculator", "expression": expr,
                "result": result, "formatted": text}
    except ImportError:
        raise HTTPException(503, "tools.py not installed")


@app.post("/api/tools/sowing")
def tool_sowing(req: ToolRequest):
    try:
        from tools import (get_sowing_calendar, format_sowing,
                           _extract_crop_name, _extract_province)
        t0     = time.time()
        crop   = _extract_crop_name(req.query)
        prov   = _extract_province(req.query)
        result = get_sowing_calendar(crop, prov)
        text   = format_sowing(result)
        ms     = (time.time() - t0) * 1000
        _pg_log("pg_tool_calls", {
            "session_id": req.session_id, "tool_name": "sowing",
            "input_args": json.dumps({"crop": crop, "province": prov}),
            "output": json.dumps(result), "duration_ms": ms,
        })
        return {"tool": "sowing", "crop": crop, "province": prov,
                "result": result, "formatted": text}
    except ImportError:
        # Fall back to MCP crop_calendar
        try:
            from mcp_tools import dispatch
            result = dispatch("crop_calendar", {"crop": req.query})
            return {"tool": "sowing", "result": result,
                    "formatted": str(result)}
        except Exception as e:
            raise HTTPException(503, f"Sowing tool unavailable: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
#  PostgreSQL logs
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/logs")
def get_logs(limit: int = 50, session_id: Optional[str] = None):
    pg = _get_pg()
    if not pg:
        return {"error": "PostgreSQL not configured", "logs": []}
    try:
        cur = pg.cursor()
        if session_id:
            cur.execute(
                "SELECT * FROM pg_pipeline_logs WHERE session_id=%s "
                "ORDER BY logged_at DESC LIMIT %s",
                (session_id, limit))
        else:
            cur.execute(
                "SELECT * FROM pg_pipeline_logs ORDER BY logged_at DESC LIMIT %s",
                (limit,))
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return {"logs": rows, "count": len(rows)}
    except Exception as e:
        return {"error": str(e), "logs": []}


# ═══════════════════════════════════════════════════════════════════════════════
#  PDF serving
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/pdf/{filename}")
def serve_pdf(filename: str):
    safe_name = os.path.basename(filename)
    pdf_path  = os.path.join(PDF_DIR, safe_name)
    if not os.path.exists(pdf_path):
        return JSONResponse(
            status_code=404,
            content={"error": f"PDF '{safe_name}' not found in pdfs/ folder."})
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=safe_name,
        headers={"Content-Disposition": f"inline; filename={safe_name}"},
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  Serve React build
# ═══════════════════════════════════════════════════════════════════════════════
DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")
if os.path.isdir(DIST):
    app.mount("/assets",
              StaticFiles(directory=os.path.join(DIST, "assets")),
              name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        return FileResponse(os.path.join(DIST, "index.html"))


# ═══════════════════════════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════════════════════════
try:
    from agent_harness import router as agent_harness_router
    app.include_router(agent_harness_router)
    print("[HARNESS] agent_harness.router included")
except Exception as e:
    print(f"[HARNESS] agent_harness router failed to import: {e}")

if __name__ == "__main__":

    import uvicorn

    print("\n" + "="*60)
    print("STARTUP CHECKS")
    print("="*60)

    _purge_orphaned_uploads()   # fix stale upload quota on restart
    db_schema.init_db()
    count = vector_store.collection_size()
    print(f"  Vector store      : {count:,} chunks")
    if count == 0:
        print("  EMPTY — run: python main.py --index")

    backend = os.environ.get("LLM_BACKEND", "groq").upper()
    print(f"  LLM_BACKEND       : {backend}")
    if backend == "GROQ" and not os.environ.get("GROQ_API_KEY"):
        print("  ⚠️  GROQ_API_KEY is not set!")
    if backend == "QWEN_REMOTE":
        base  = os.environ.get("QWEN_REMOTE_BASE_URL")
        model = os.environ.get("QWEN_REMOTE_MODEL")
        print(f"  QWEN_REMOTE_BASE_URL : {base  or '⚠️  NOT SET'}")
        print(f"  QWEN_REMOTE_MODEL    : {model or '⚠️  NOT SET'}")
        if base:
            try:
                import requests
                r = requests.get(f"{base}/v1/models", timeout=5)
                print(f"  Qwen /v1/models : HTTP {r.status_code}")
            except Exception as e:
                print(f"  ⚠️  Could not reach Qwen remote: {e}")

    print("="*60)
    print("🚀 Starting API server at http://localhost:8001")
    print("="*60 + "\n")

    uvicorn.run(app, host="127.0.0.1", port=8001, reload=False)
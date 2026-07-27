"""
rag_pipeline.py  (AgriBot — fully fixed)
==========================================

  User Query
    → [1] Query Rewriter          (history-aware, topic-shift safe)
    → [2] Orchestrator            (advisory only — RAG always runs first)
    → [2b] MCP Tool Dispatch      (weather / crop_calendar / unit_converter ONLY)
    → [3] Retrieve                (ChromaDB vector + BM25 + session-upload chunks)
    → [4] RRF Re-rank
    → [5] Relevance Evaluator
         ├─ sufficient / partial  → [6] Generate grounded answer
         └─ none (after retries)  → [7] Tavily web fallback (only now)

═══════════════════════════════════════════════════════════════
FIXES vs original  (read these before editing)
═══════════════════════════════════════════════════════════════

FIX 1 — Model changed to Groq's Llama-3.3-70B (production quality).
         Set env var GROQ_MODEL to override without editing code.
         If you have an xAI key, set XAI_API_KEY and LLM_BACKEND=xai.

FIX 2 — Tavily removed from MCP tool manifest entirely.
         It was the root cause of "[MCP tavily]" appearing on EVERY response.
         Tavily now runs ONLY inside _generate_from_web(), which is called:
           (a) when user clicks "Web Search" toggle  (force_web=True), OR
           (b) after MAX_RETRIES RAG attempts all return "none" from evaluator.

FIX 3 — MCP source_type tag fixed.
         mcp_dispatch logging a NO_TOOL result no longer causes api_server to
         label the response as "MCP".  Only tool steps that actually ran with
         a real result are counted as MCP source.

FIX 4 — Orchestrator now defaults to RAG.
         Previous version let the LLM route queries to DIRECT (web/general),
         skipping the PDF index for questions that were clearly in-scope.
         Orchestrator is now ADVISORY ONLY — RAG always runs first.

FIX 5 — Context window expanded: max_chars 2500 → 4500.
         Small context was truncating relevant evidence before the LLM could
         read it, causing "not in document" answers.

FIX 6 — Conversation history capped to last 3 turns.
         Long history was causing the query rewriter to over-apply earlier
         context to unrelated new queries ("sticky" first-turn context bug).
         A topic-shift instruction is also added to the rewriter prompt.

FIX 7 — Evaluator no longer hard-fails on "partial" after first retry.
         If docs are topically related but incomplete, the answer is generated
         from those partial docs rather than escalating to web search.

FIX 8 — Sources now returned as structured JSON alongside the answer text.
         The plain-text "SOURCES: …" block is stripped from the answer.
         api_server.py passes sources[] to the frontend as a separate field.
         The React UI can then show a collapsed "Sources" button (like ChatGPT)
         that expands on click to show clickable links / document refs.

═══════════════════════════════════════════════════════════════
Installation (run these ONCE in your terminal)
═══════════════════════════════════════════════════════════════

  pip install groq rank-bm25 tavily-python --break-system-packages

  # If you want xAI Grok instead of Groq Llama:
  pip install openai --break-system-packages

Environment variables (set in your shell or .env file):
  GROQ_API_KEY=gsk_...          ← required for default Groq backend
  GROQ_MODEL=llama-3.3-70b-versatile  ← optional override
  TAVILY_API_KEY=tvly-...       ← optional; web fallback disabled without it
  LLM_BACKEND=groq              ← groq | xai | ollama | qwen_local | qwen_remote
  XAI_API_KEY=xai-...           ← only needed if LLM_BACKEND=xai
"""
import os
import re
import time
import uuid
import json
from typing import List, Dict, Any, Tuple, Optional
from rank_bm25 import BM25Okapi
from groq import Groq
import db_schema
import vector_store

# ── Multilingual text layer (Stage 1: text-only Urdu/English support) ──────
# Graceful import: if language_layer.py or its dependencies (transformers,
# torch) aren't installed yet, the pipeline runs exactly as before —
# English-only — with a one-time startup notice instead of crashing.
try:
    from language_layer import detect_language, translate_to_english, translate_from_english
    _LANG_LAYER_AVAILABLE = True
except ImportError as e:
    _LANG_LAYER_AVAILABLE = False
    print(f"[PIPELINE] language_layer.py not available — English-only mode. ({e})")

# ── MCP tools (graceful fallback if not installed) ───────────────────────────
try:
    from mcp_tools import dispatch as mcp_dispatch, format_tool_manifest_for_prompt
    # tavily_web_search and tavily_format are called via dispatch("tavily_search", ...)
    # not imported directly — they live inside mcp_tools._tool_tavily_search
    _MCP_AVAILABLE = True
    print("[PIPELINE] MCP tools loaded successfully.")
except Exception as e:
    _MCP_AVAILABLE = False
    print(f"[PIPELINE] mcp_tools import failed: {e}")
    print("[PIPELINE] MCP + Tavily disabled — check mcp_tools.py exists and has no errors.")
    # Stub so code that references mcp_dispatch doesn't NameError
    def mcp_dispatch(tool_name, params): return {"error": "MCP not available"}
    def format_tool_manifest_for_prompt(): return ""

# Compatibility stubs for any code that calls tavily_web_search / tavily_format directly
def tavily_web_search(query, **kw):
    if _MCP_AVAILABLE:
        result = mcp_dispatch("tavily_search", {"query": query, **kw})
        return result.get("results", [])
    return []

def tavily_format(results, **kw):
    if not results:
        return ""
    lines = []
    for i, r in enumerate(results if isinstance(results, list) else [], 1):
        lines.append(f"[Web {i}] {r.get('title','')} — {r.get('url','')}")
        lines.append(r.get('content', r.get('snippet', ''))[:400])
    return "\n\n".join(lines)

# ── LLM backend selection ────────────────────────────────────────────────────
LLM_BACKEND = os.environ.get("LLM_BACKEND", "groq").lower()

if LLM_BACKEND == "ollama":
    from llm_client_ollama import OllamaClient
elif LLM_BACKEND == "qwen_local":
    from llm_client_qwen_local import QwenLocalClient, QWEN_MODEL_ID
elif LLM_BACKEND == "qwen_remote":
    from llm_client_qwen_remote import QwenRemoteClient, QWEN_REMOTE_MODEL

# ── Configuration ─────────────────────────────────────────────────────────────
# FIX 1: upgraded model; override via GROQ_MODEL env var
GROQ_MODEL   = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
TOP_K_VECTOR = 10
TOP_K_BM25   = 10
TOP_K_FINAL  = 7
MAX_RETRIES  = 2

if LLM_BACKEND == "ollama":
    ACTIVE_MODEL_NAME = OLLAMA_MODEL
elif LLM_BACKEND == "qwen_local":
    ACTIVE_MODEL_NAME = QWEN_MODEL_ID
elif LLM_BACKEND == "qwen_remote":
    ACTIVE_MODEL_NAME = QWEN_REMOTE_MODEL
elif LLM_BACKEND == "xai":
    ACTIVE_MODEL_NAME = os.environ.get("XAI_MODEL", "grok-beta")
else:
    ACTIVE_MODEL_NAME = GROQ_MODEL


# ══════════════════════════════════════════════════════════════════════════════
#  DB logging helpers
# ══════════════════════════════════════════════════════════════════════════════

def _log_step(query_id, step_name, step_order,
              input_text="", output_text="", duration_ms=0.0, status="ok"):
    step_id = str(uuid.uuid4())
    conn = db_schema.get_connection()
    conn.execute(
        """INSERT INTO pipeline_steps
           (step_id, query_id, step_name, step_order,
            input_text, output_text, duration_ms, status)
           VALUES (?,?,?,?,?,?,?,?)""",
        (step_id, query_id, step_name, step_order,
         input_text[:4000], output_text[:4000], duration_ms, status),
    )
    conn.commit()
    conn.close()
    print(f"  [STEP {step_order}] {step_name} | {duration_ms:.0f}ms | {status}")
    return step_id


def _log_llm_call(step_id, model_name, system_prompt, user_prompt, response_text, usage):
    call_id = str(uuid.uuid4())
    conn = db_schema.get_connection()
    conn.execute(
        """INSERT INTO llm_calls
           (call_id, step_id, model_name, system_prompt, user_prompt,
            response_text, prompt_tokens, completion_tokens, total_tokens)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (call_id, step_id, model_name,
         system_prompt[:2000], user_prompt[:4000], response_text[:4000],
         usage.get("prompt_tokens", 0),
         usage.get("completion_tokens", 0),
         usage.get("total_tokens", 0)),
    )
    conn.commit()
    conn.close()
    return call_id


def _log_retrieved_docs(query_id, step_id, docs):
    conn = db_schema.get_connection()
    for doc in docs:
        conn.execute(
            """INSERT INTO retrieved_docs
               (doc_id, query_id, step_id, chunk_text, source_file,
                page_num, vector_score, bm25_score, rrf_score, final_rank)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (str(uuid.uuid4()), query_id, step_id,
             doc.get("chunk_text", "")[:2000],
             doc.get("source_file", ""),
             doc.get("page_num", 0),
             doc.get("vector_score"),
             doc.get("bm25_score"),
             doc.get("rrf_score"),
             doc.get("final_rank")),
        )
    conn.commit()
    conn.close()


def _log_response(query_id, final_response, used_rag, retry_count):
    conn = db_schema.get_connection()
    conn.execute(
        """INSERT INTO responses
           (response_id, query_id, final_response, used_rag, retry_count)
           VALUES (?,?,?,?,?)""",
        (str(uuid.uuid4()), query_id, final_response, int(used_rag), retry_count),
    )
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
#  LLM Client
# ══════════════════════════════════════════════════════════════════════════════

class LLMClient:
    """Default Groq backend (Llama-3.3-70B)."""

    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not set.  Get a free key at https://console.groq.com"
            )
        
        self.client = Groq(api_key=api_key)

    def call(self, system_prompt, user_prompt, max_tokens=512, temperature=0.1):
        response = self.client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        text  = response.choices[0].message.content.strip()
        usage = {
            "prompt_tokens":     response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens":      response.usage.total_tokens,
        }
        return text, usage


class XAIClient:
    """
    xAI Grok backend — uses OpenAI-compatible SDK.

    pip install openai
    Set env:  LLM_BACKEND=xai   XAI_API_KEY=xai-...
    """

    def __init__(self):
        api_key = os.environ.get("XAI_API_KEY", "")
        if not api_key:
            raise ValueError(
                "XAI_API_KEY not set.  Get a key at https://console.x.ai"
            )
        from openai import OpenAI
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1",
        )
        self.model = os.environ.get("XAI_MODEL", "grok-beta")
        print(f"[PIPELINE] xAI backend: {self.model}")

    def call(self, system_prompt, user_prompt, max_tokens=512, temperature=0.1):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        text  = response.choices[0].message.content.strip()
        usage = {
            "prompt_tokens":     response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens":      response.usage.total_tokens,
        }
        return text, usage


def get_llm_client():
    if LLM_BACKEND == "ollama":
        print(f"[PIPELINE] Backend: Ollama ({OLLAMA_MODEL})")
        return OllamaClient(model=OLLAMA_MODEL)
    elif LLM_BACKEND == "qwen_local":
        print(f"[PIPELINE] Backend: Qwen local ({QWEN_MODEL_ID})")
        return QwenLocalClient(model_id=QWEN_MODEL_ID)
    elif LLM_BACKEND == "qwen_remote":
        print(f"[PIPELINE] Backend: Qwen remote ({QWEN_REMOTE_MODEL})")
        return QwenRemoteClient(model=QWEN_REMOTE_MODEL)
    elif LLM_BACKEND == "xai":
        return XAIClient()
    else:
        print(f"[PIPELINE] Backend: Groq ({GROQ_MODEL})")
        return LLMClient()


# ══════════════════════════════════════════════════════════════════════════════
#  BM25 Index
# ══════════════════════════════════════════════════════════════════════════════

class BM25Index:
    def __init__(self):
        self._corpus:   List[str]  = []
        self._metadata: List[Dict] = []
        self._bm25 = None

    def build_from_collection(self):
        collection = vector_store._get_collection()
        if collection.count() == 0:
            print("[BM25] WARNING: Empty collection.")
            return
        results        = collection.get(include=["documents", "metadatas"])
        self._corpus   = results["documents"]
        self._metadata = results["metadatas"]
        self._bm25     = BM25Okapi([d.lower().split() for d in self._corpus])
        print(f"[BM25] Index built: {len(self._corpus)} docs")

    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        if self._bm25 is None or not self._corpus:
            return []
        scores = self._bm25.get_scores(query.lower().split())
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        results = []
        for idx, score in ranked[:top_k]:
            meta = self._metadata[idx] if idx < len(self._metadata) else {}
            results.append({
                "chunk_text":  self._corpus[idx],
                "source_file": meta.get("source_file", "unknown"),
                "page_num":    meta.get("page_num", 0),
                "bm25_score":  round(float(score), 4),
            })
        return results


# ══════════════════════════════════════════════════════════════════════════════
#  RRF Reranking
# ══════════════════════════════════════════════════════════════════════════════

def rrf_rerank(vector_results, bm25_results, top_k=7, k=60):
    rrf_scores: Dict[str, float] = {}
    doc_map:    Dict[str, Dict]  = {}

    def _key(doc):
        return f"{doc['source_file']}|{doc['page_num']}|{doc['chunk_text'][:100]}"

    for rank, doc in enumerate(vector_results, 1):
        key = _key(doc)
        rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (k + rank)
        if key not in doc_map:
            doc_map[key] = {**doc, "bm25_score": None}

    for rank, doc in enumerate(bm25_results, 1):
        key = _key(doc)
        rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (k + rank)
        if key not in doc_map:
            doc_map[key] = {**doc, "vector_score": None}
        else:
            doc_map[key]["bm25_score"] = doc.get("bm25_score")

    sorted_keys = sorted(rrf_scores, key=lambda kk: rrf_scores[kk], reverse=True)
    reranked = []
    for final_rank, key in enumerate(sorted_keys[:top_k], 1):
        entry = {
            **doc_map[key],
            "rrf_score":  round(rrf_scores[key], 6),
            "final_rank": final_rank,
        }
        reranked.append(entry)
    return reranked


# ══════════════════════════════════════════════════════════════════════════════
#  Source extraction  (FIX 8 — structured sources, not inline text block)
# ══════════════════════════════════════════════════════════════════════════════

def _top_keywords(text: str, n: int = 15) -> List[str]:
    from collections import Counter
    STOP = {
        "that","this","with","from","have","been","they","also","such",
        "which","when","were","will","more","than","into","some","each",
        "most","over","only","used","using","their","these","about",
    }
    words = [w.lower() for w in re.findall(r'\b[a-zA-Z]{4,}\b', text)
             if w.lower() not in STOP]
    return [w for w, _ in Counter(words).most_common(n)]


def _build_sources_from_docs(docs: List[Dict]) -> List[Dict]:
    """
    Build a structured sources list from retrieved docs.
    Each source dict has:
        num        int   — citation number shown inline as [1], [2], …
        label      str   — human-readable short name
        source_file str  — file name
        page       int   — page or chunk index
        is_upload  bool  — True if from session-uploaded file
        url        str   — empty for PDFs; populated for web results
        keywords   list  — for citation matching
    """
    sources = []
    seen = set()
    for i, doc in enumerate(docs, 1):
        sf  = doc.get("source_file", "unknown")
        pg  = doc.get("page_num", 0)
        key = f"{sf}|{pg}"
        if key in seen:
            continue
        seen.add(key)
        sources.append({
            "num":         i,
            "label":       f"{sf} — p.{pg}",
            "source_file": sf,
            "page":        pg,
            "is_upload":   bool(doc.get("from_upload")),
            "url":         "",
            "keywords":    _top_keywords(doc.get("chunk_text", "")),
        })
    return sources


def _build_sources_from_web(results: List[Dict]) -> List[Dict]:
    """Build sources list from Tavily web results."""
    sources = []
    for i, r in enumerate(results, 1):
        combined_text = f"{r.get('title', '')} {r.get('content', '')[:400]}"
        sources.append({
            "num":         i,
            "label":       r.get("site_name", r.get("url", "")),
            "source_file": r.get("url", ""),
            "page":        0,
            "is_upload":   False,
            "url":         r.get("url", ""),
            "keywords":    _top_keywords(combined_text),
        })
    return sources


def _inject_inline_citations(answer: str, sources: List[Dict]) -> str:
    """
    Annotate sentences in the LLM answer with [N] tags where source N's
    keywords appear.  The plain-text SOURCES block is NOT appended —
    sources are returned separately as structured data (FIX 8).
    """
    # Strip any SOURCES block the LLM may have generated
    answer = re.sub(r'\n*SOURCES:[\s\S]*$',            '', answer, flags=re.IGNORECASE).strip()
    answer = re.sub(r'\n*\*\*Web sources.*?\*\*[\s\S]*$', '', answer, flags=re.IGNORECASE).strip()
    answer = re.sub(r'[\(\[]\s*Source:[^\)\]]*[\)\]]', '', answer, flags=re.IGNORECASE).strip()
    answer = re.sub(r'\(?\bpage\s+\d+\)?',             '', answer, flags=re.IGNORECASE).strip()

    if not sources:
        return answer

    sentences = re.split(r'(?<=[.!?])\s+', answer)
    annotated = []
    for sent in sentences:
        sent_lower = sent.lower()
        hits = []
        for src in sources:
            matches = sum(1 for kw in src["keywords"] if kw in sent_lower)
            if matches >= 1:
                hits.append((matches, src["num"]))
        if hits:
            hits.sort(reverse=True)
            tags = "".join(f"[{num}]" for _, num in hits[:2])
            annotated.append(sent + tags)
        else:
            annotated.append(sent)

    cited = " ".join(annotated)
    # Guarantee at least one citation
    if sources and not re.search(r'\[\d+\]', cited):
        cited = cited.rstrip() + f"[{sources[0]['num']}]"
    return cited.strip()


def _build_context(docs: List[Dict], max_chars: int = 4500) -> str:
    """FIX 5: max_chars raised from 2500 to 4500."""
    parts, total = [], 0
    for doc in docs:
        header  = (f"[Source: {doc['source_file']} | Page {doc['page_num']} | "
                   f"Rank: {doc.get('final_rank', '?')}]")
        snippet = doc["chunk_text"][:600]
        entry   = f"{header}\n{snippet}"
        if total + len(entry) > max_chars:
            break
        parts.append(entry)
        total += len(entry)
    return "\n\n---\n\n".join(parts)


# ══════════════════════════════════════════════════════════════════════════════
#  Conversation Memory  (FIX 6 — capped to 3 turns)
# ══════════════════════════════════════════════════════════════════════════════

class ConversationMemory:
    """
    Retrieves the last N turns from the DB for a session.
    FIX 6: max_turns=3 prevents stale history from bleeding into new topics.
    """

    def __init__(self, max_turns: int = 3):
        self.max_turns = max_turns

    def get_formatted(self, session_id: str) -> str:
        conn = db_schema.get_connection()
        try:
            rows = conn.execute(
                """SELECT q.original_query, r.final_response
                   FROM queries q
                   LEFT JOIN responses r ON r.query_id = q.query_id
                   WHERE q.session_id = ?
                   ORDER BY q.timestamp DESC LIMIT ?""",
                (session_id, self.max_turns),
            ).fetchall()
        finally:
            conn.close()

        if not rows:
            return "No previous conversation."
        lines = []
        for row in reversed(rows):
            lines.append(f"User: {row['original_query'][:300]}")
            if row["final_response"]:
                # Strip inline citation tags from stored history to keep it clean
                resp = re.sub(r'\[\d+\]', '', row["final_response"])
                lines.append(f"Assistant: {resp[:300]}")
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
#  Session-upload helpers
# ══════════════════════════════════════════════════════════════════════════════

def _chunk_text_simple(text: str, chunk_size: int = 600, overlap: int = 100) -> List[str]:
    """Character-level chunker for uploaded document text."""
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start + chunk_size])
        start += chunk_size - overlap
    return [c.strip() for c in chunks if c.strip()]


def _extract_text_from_path(filepath: str) -> str:
    """
    Extract plain text from an uploaded file.
    Priority: Docling (best) → PyMuPDF → python-docx → plain text read.
    """
    filepath = filepath.strip()
    ext = os.path.splitext(filepath)[1].lower()

    # ── 1. Docling (handles PDFs, DOCX, PPTX with proper layout) ─────────────
    try:
        from docling.document_converter import DocumentConverter
        result = DocumentConverter().convert(filepath)
        text   = result.document.export_to_markdown()
        if text.strip():
            print(f"  [UPLOAD] Docling: {len(text)} chars from {os.path.basename(filepath)}")
            return text
    except Exception:
        pass

    # ── 2. PyMuPDF for PDFs ──────────────────────────────────────────────────
    if ext == ".pdf":
        try:
            import fitz
            doc   = fitz.open(filepath)
            pages = [page.get_text() for page in doc]
            doc.close()
            text  = "\n\n".join(pages)
            if text.strip():
                print(f"  [UPLOAD] PyMuPDF: {len(text)} chars")
                return text
        except Exception as e:
            print(f"  [UPLOAD] PyMuPDF failed: {e}")

    # ── 3. python-docx for Word files ────────────────────────────────────────
    if ext in (".docx", ".doc"):
        try:
            import docx
            doc  = docx.Document(filepath)
            text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            if text.strip():
                print(f"  [UPLOAD] python-docx: {len(text)} chars")
                return text
        except Exception as e:
            print(f"  [UPLOAD] python-docx failed: {e}")

    # ── 4. Plain text fallback ────────────────────────────────────────────────
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        if text.strip():
            print(f"  [UPLOAD] Plain text read: {len(text)} chars")
            return text
    except Exception as e:
        print(f"  [UPLOAD] Plain text read failed: {e}")

    print(f"  [UPLOAD] ERROR: Could not extract text from {filepath}")
    return ""


def build_upload_chunks(filepath: str, source_label: str = None) -> List[Dict]:
    """
    Extract text from an uploaded file and return RAG-ready chunk dicts
    that merge with ChromaDB results for RRF ranking.
    Called from api_server.py after a file is saved to disk.
    """
    if not source_label:
        source_label = os.path.basename(filepath)

    text = _extract_text_from_path(filepath)
    if not text:
        print(f"  [UPLOAD] No text extracted — file may be empty or unsupported: {filepath}")
        return []

    raw_chunks = _chunk_text_simple(text)
    chunks = []
    for i, chunk in enumerate(raw_chunks):
        chunks.append({
            "chunk_text":   chunk,
            "source_file":  source_label,
            "page_num":     i,
            "vector_score": 0.5,
            "bm25_score":   None,
            "rrf_score":    None,
            "final_rank":   None,
            "from_upload":  True,
        })
    print(f"  [UPLOAD] {len(chunks)} chunks ready from '{source_label}'")
    return chunks


# ══════════════════════════════════════════════════════════════════════════════
#  Return type for pipeline.run()
# ══════════════════════════════════════════════════════════════════════════════

class PipelineResult:
    """
    What run() returns.  Both fields go to api_server.py.

    answer   str        — LLM text with inline [N] citation tags
    sources  List[Dict] — structured source list, rendered by frontend as a
                          collapsed "Sources" button (FIX 8)

    Each source dict:
        num        int   — matches [N] in answer
        label      str   — human-readable name
        source_file str  — filename or URL
        page       int   — page number (0 for web)
        is_upload  bool  — True if from session-uploaded file
        url        str   — clickable URL if web source, else ""
    """
    __slots__ = ("answer", "sources", "used_rag", "retry_count", "source_type")

    def __init__(self, answer, sources, used_rag=True, retry_count=0, source_type="RAG"):
        self.answer       = answer
        self.sources      = sources
        self.used_rag     = used_rag
        self.retry_count  = retry_count
        self.source_type  = source_type  # "RAG" | "MCP" | "WEB" | "DIRECT"


# ══════════════════════════════════════════════════════════════════════════════
#  The Agentic RAG Pipeline
# ══════════════════════════════════════════════════════════════════════════════

class AgenticRAGPipeline:

    def __init__(self):
        print("\n[PIPELINE] Initializing AgriBot pipeline...")
        self.llm    = get_llm_client()
        self.bm25   = BM25Index()
        self.memory = ConversationMemory(max_turns=3)  # FIX 6
        db_schema.init_db()
        print("[PIPELINE] Ready.\n")

    def _ensure_bm25_built(self):
        if self.bm25._bm25 is None:
            self.bm25.build_from_collection()

    # ── Sanitize rewritten query ──────────────────────────────────────────────

    @staticmethod
    def _sanitize_rewrite(rewritten: str, original_query: str) -> str:
        text = rewritten.strip().strip('"').strip()
        if len(text) > 220:
            return original_query
        words = text.lower().split()
        for n in (2, 3):
            grams = [" ".join(words[i:i+n]) for i in range(len(words) - n + 1)]
            if grams:
                most_common = max(set(grams), key=grams.count)
                if grams.count(most_common) >= 3:
                    return original_query
        if text.count("?") > 1 or text.count(",") > 6 or not text:
            return original_query
        return text

    # ── Agent 1: Query Rewriter ───────────────────────────────────────────────

    def _query_rewriter(self, query_id, original_query, conversation_history,
                        evaluator_feedback="", step_order=1):
        t0 = time.time()
        feedback_section = ""
        if evaluator_feedback:
            feedback_section = (
                f"\n\nIMPORTANT — previous retrieval found nothing useful.\n"
                f"Evaluator feedback: {evaluator_feedback}\n"
                f"Rewrite the query differently to address this gap."
            )

        # FIX 6: topic-shift instruction added so new unrelated queries aren't
        # contaminated by the last conversation turn
        system = (
            "You are a query rewriting assistant for a retrieval system.\n\n"
            "STRICT RULES:\n"
            "1. Output ONE rewritten query. One sentence. Under 25 words.\n"
            "2. NEVER invent named entities not in the original query.\n"
            "3. Do NOT explain, list alternatives, or repeat phrases.\n"
            "4. If the query is already clear and standalone, return it unchanged.\n"
            "5. TOPIC SHIFT RULE: If the new query is about a completely different\n"
            "   topic than the conversation history, write it as a standalone query\n"
            "   WITHOUT referencing the history at all.\n\n"
            "Examples:\n"
            "Original: What diseases did they study?\n"
            "History: User asked about PARC wheat research.\n"
            "Rewritten: What diseases did PARC study in wheat research?\n\n"
            "Original: How do I convert 5 acres to hectares?\n"
            "History: User asked about cotton pests.\n"
            "Rewritten: How do I convert 5 acres to hectares?"
        )
        # FIX 6: only last 600 chars of history (≈ 3 turns) to avoid over-conditioning
        user = (
            f"Conversation history (last 3 turns):\n"
            f"{conversation_history[-600:]}\n\n"
            f"Original query: {original_query}"
            f"{feedback_section}\n\n"
            "Rewritten query (one sentence, under 25 words):"
        )

        rewritten, usage = self.llm.call(system, user, max_tokens=80, temperature=0.0)
        rewritten = self._sanitize_rewrite(rewritten, original_query)
        duration  = (time.time() - t0) * 1000

        step_id = _log_step(query_id, "query_rewriter", step_order,
                            input_text=original_query, output_text=rewritten,
                            duration_ms=duration)
        _log_llm_call(step_id, ACTIVE_MODEL_NAME, system, user, rewritten, usage)
        print(f"  [REWRITER] '{original_query}' → '{rewritten}'")
        return rewritten

    # ── Agent 2: Orchestrator (advisory only) ─────────────────────────────────

    def _orchestrator(self, query_id, rewritten_query, step_order=2):
        """
        FIX 4: Orchestrator is now ADVISORY ONLY.
        Its output is logged to the Trace panel for diagnostics, but the
        pipeline always attempts RAG first regardless of the decision.
        The only path that skips RAG is force_web=True (UI web toggle).
        """
        t0 = time.time()
        system = (
            "You are a routing assistant for an agricultural knowledge base.\n\n"
            "The knowledge base contains: FAO crop disease guidelines, "
            "PARC annual report 2023-24, Punjab agriculture service rules 2007, "
            "plus any user-uploaded documents.\n\n"
            "DEFAULT TO RAG unless the question is a pure arithmetic calculation, "
            "a common knowledge greeting, or a general chitchat message.\n\n"
            "Always output RAG for anything about:\n"
            "  - crops, diseases, pests, yield, fertilizer, soil, seeds\n"
            "  - irrigation, water, land, farming practices\n"
            "  - PARC, FAO, Punjab agriculture, government schemes\n"
            "  - uploaded document summaries\n"
            "  - ANY question when the user has uploaded a file this session\n\n"
            "Output ONLY one word: 'RAG' or 'DIRECT'."
        )
        user = (
            f"Question: {rewritten_query}\n\n"
            "Decision (RAG or DIRECT):"
        )
        decision_text, usage = self.llm.call(system, user, max_tokens=10)
        duration  = (time.time() - t0) * 1000
        needs_rag = "DIRECT" not in decision_text.upper()  # default to RAG

        step_id = _log_step(query_id, "orchestrator", step_order,
                            input_text=rewritten_query,
                            output_text=f"Advisory decision: {'RAG' if needs_rag else 'DIRECT'} (RAG runs anyway)",
                            duration_ms=duration)
        _log_llm_call(step_id, ACTIVE_MODEL_NAME, system, user, decision_text, usage)
        print(f"  [ORCHESTRATOR] Advisory: {'RAG' if needs_rag else 'DIRECT'} (RAG always runs)")
        return needs_rag

    # ── Step 2b: MCP Tool Dispatch ────────────────────────────────────────────

    def _mcp_dispatch(self, rewritten_query: str,
                      query_id: str = "", step_order: int = 0) -> Tuple[str, bool]:
        """
        Ask the LLM if a structured MCP tool (weather, crop_calendar,
        unit_converter) enriches the answer.

        FIX 2: Tavily removed from TOOL_MANIFEST so the LLM can never pick it
        here. This eliminates [MCP tavily] appearing on every response.

        FIX 3: Returns (context_string, tool_actually_ran: bool).
        api_server.py uses tool_actually_ran to set source_type="MCP" only
        when a real tool executed — not just because mcp_dispatch was logged.

        Returns:
            context  str   — non-empty only if a tool actually ran
            ran      bool  — True only when a real tool produced a result
        """
        if not _MCP_AVAILABLE:
            return "", False

        t0 = time.time()
        try:
            tool_system = (
                "You decide whether to call an MCP tool to enrich the answer.\n\n"
                + format_tool_manifest_for_prompt()
                + "\n\nCRITICAL RULES:\n"
                + "- Only call a tool when the query EXPLICITLY asks for weather,\n"
                + "  crop timing, or a unit conversion.\n"
                + "- Do NOT call any tool for general questions about agriculture,\n"
                + "  crop diseases, farming techniques, or document content.\n"
                + "- If no tool fits, output exactly: NO_TOOL\n\n"
                + "If a tool fits, output ONLY valid JSON:\n"
                + '{"tool": "<name>", "params": {<key>: <value>}}'
            )
            decision, _ = self.llm.call(
                tool_system,
                f"Query: {rewritten_query}",
                max_tokens=80, temperature=0.0,
            )
            decision = decision.strip()

            if decision == "NO_TOOL" or not decision.startswith("{"):
                # Log the check but return ran=False so source_type stays "RAG"
                if query_id:
                    _log_step(query_id, "mcp_dispatch", step_order,
                              input_text=rewritten_query,
                              output_text="NO_TOOL",
                              duration_ms=(time.time() - t0) * 1000)
                return "", False  # FIX 3

            call        = json.loads(decision)
            tool_name   = call.get("tool", "")
            tool_params = call.get("params", {})

            result = mcp_dispatch(tool_name, tool_params)

            if "error" in result:
                err_msg = result["error"]
                print(f"  [MCP] Tool '{tool_name}' error: {err_msg}")
                if query_id:
                    _log_step(query_id, f"mcp_{tool_name}", step_order,
                              input_text=rewritten_query,
                              output_text=f"ERROR: {err_msg}",
                              duration_ms=(time.time() - t0) * 1000,
                              status="error")
                return "", False  # FIX 3

            context  = (
                f"\n[MCP Tool: {tool_name}]\n"
                + json.dumps(result, indent=2, default=str)
                + "\n"
            )
            duration = (time.time() - t0) * 1000
            print(f"  [MCP] '{tool_name}' executed and injected ({duration:.0f}ms)")

            if query_id:
                _log_step(query_id, f"mcp_{tool_name}", step_order,
                          input_text=json.dumps(tool_params),
                          output_text=context[:2000],
                          duration_ms=duration)

            return context, True  # FIX 3: ran=True

        except Exception as e:
            print(f"  [MCP] Dispatch skipped: {e}")
            return "", False

    # ── Step 3: Retrieve ──────────────────────────────────────────────────────

    def _retrieve(self, query_id, rewritten_query,
                  upload_chunks: List[Dict] = None,
                  upload_file_ids: List[str] = None,
                  step_order=3):
        """
        Hybrid retrieval: ChromaDB vector (main PDFs) + ChromaDB vector
        (user_uploads) + BM25 (main PDFs) + BM25 (upload chunks).

        FIX: two-stage upload search.
          Stage A (vector): query the user_uploads ChromaDB collection filtered
                            by session file_ids — real embeddings, synonym-aware.
          Stage B (BM25):   keyword fallback over raw chunks for the brief window
                            before background indexing finishes.
        """
        t0 = time.time()

        # ── Main PDF collection ───────────────────────────────────────────────
        vector_results = vector_store.similarity_search(rewritten_query, top_k=TOP_K_VECTOR)
        for doc in vector_results:
            doc.setdefault("bm25_score", None)

        bm25_results = self.bm25.search(rewritten_query, top_k=TOP_K_BM25)

        upload_vector_hits = []
        upload_bm25_hits   = []

        # ── Stage A: vector search in user_uploads ChromaDB collection ────────
        if upload_file_ids:
            try:
                client = vector_store._get_client()
                ef     = vector_store._get_ef()
                try:
                    u_col = client.get_collection(name="user_uploads", embedding_function=ef)
                    if u_col.count() > 0:
                        where_filter = (
                            {"file_id": {"$in": upload_file_ids}}
                            if len(upload_file_ids) > 1
                            else {"file_id": upload_file_ids[0]}
                        )
                        u_res = u_col.query(
                            query_texts=[rewritten_query],
                            n_results=min(TOP_K_VECTOR, u_col.count()),
                            where=where_filter,
                            include=["documents", "metadatas", "distances"],
                        )
                        for txt, meta, dist in zip(
                            u_res.get("documents", [[]])[0],
                            u_res.get("metadatas", [[]])[0],
                            u_res.get("distances", [[]])[0],
                        ):
                            upload_vector_hits.append({
                                "chunk_text":   txt,
                                "source_file":  meta.get("source_file", "upload"),
                                "page_num":     meta.get("page_num", 0),
                                "vector_score": round(1.0 - dist, 4),
                                "bm25_score":   None,
                                "from_upload":  True,
                            })
                        print(f"  [UPLOAD-VEC] {len(upload_vector_hits)} vector hits from user_uploads")
                except Exception:
                    pass   # collection doesn't exist yet — fall through to Stage B
            except Exception as e:
                print(f"  [UPLOAD-VEC] user_uploads query error: {e}")

        # ── Stage B: BM25 keyword fallback over raw upload_chunks ─────────────
        # Runs when: no file_ids given, OR indexing not finished yet (< 3 vector hits)
        if upload_chunks and len(upload_vector_hits) < 3:
            query_words = set(rewritten_query.lower().split())
            for chunk in upload_chunks:
                text_words = set(chunk["chunk_text"].lower().split())
                overlap    = len(query_words & text_words)
                if overlap > 0:
                    upload_bm25_hits.append({
                        **chunk,
                        "bm25_score":   round(overlap / max(len(query_words), 1), 4),
                        "vector_score": chunk.get("vector_score", 0.5),
                        "from_upload":  True,
                    })
            upload_bm25_hits.sort(key=lambda x: x["bm25_score"], reverse=True)
            upload_bm25_hits = upload_bm25_hits[:TOP_K_BM25]
            print(f"  [UPLOAD-BM25] {len(upload_bm25_hits)} BM25 hits from raw chunks (fallback)")
        elif not upload_chunks and not upload_file_ids:
            print("  [UPLOAD] No session upload chunks or file_ids for this query")

        # ── Merge upload hits into retrieval pools ────────────────────────────
        if upload_vector_hits:
            vector_results = upload_vector_hits + vector_results
        if upload_bm25_hits:
            bm25_results = upload_bm25_hits + bm25_results
            bm25_results = bm25_results[:TOP_K_BM25 * 2]

        duration = (time.time() - t0) * 1000
        summary  = (f"Vector: {len(vector_results)} | BM25: {len(bm25_results)} "
                    f"(incl. {len(upload_chunks or [])} upload chunks)")
        step_id  = _log_step(query_id, "retrieval", step_order,
                             input_text=rewritten_query, output_text=summary,
                             duration_ms=duration)
        _log_retrieved_docs(query_id, step_id, vector_results + bm25_results)
        print(f"  [RETRIEVAL] {summary}")
        return vector_results, bm25_results

    # ── Step 4: RRF Reranking ─────────────────────────────────────────────────

    def _rerank(self, query_id, vector_results, bm25_results, step_order=4):
        t0       = time.time()
        reranked = rrf_rerank(vector_results, bm25_results, top_k=TOP_K_FINAL)
        duration = (time.time() - t0) * 1000

        summary = f"RRF merged → top {len(reranked)} docs"
        step_id = _log_step(query_id, "reranking", step_order,
                            input_text=f"vector:{len(vector_results)} bm25:{len(bm25_results)}",
                            output_text=summary, duration_ms=duration)
        _log_retrieved_docs(query_id, step_id, reranked)
        print(f"  [RERANK] {summary}")
        for d in reranked:
            tag = " [UPLOAD]" if d.get("from_upload") else ""
            print(f"    rank={d['final_rank']} rrf={d['rrf_score']:.5f} "
                  f"src={d['source_file']} p.{d['page_num']}{tag}")
        return reranked

    # ── Agent 3: Relevance Evaluator ──────────────────────────────────────────

    def _evaluator(self, query_id, original_query, rewritten_query, docs, step_order=5):
        t0      = time.time()
        context = _build_context(docs, max_chars=2000)

        system = (
            "You are a document relevance evaluator.\n\n"
            "Classify retrieved documents into one of:\n"
            '  "sufficient" — directly answer the question\n'
            '  "partial"    — topically related but incomplete\n'
            '  "none"       — completely unrelated\n\n'
            'Output ONLY JSON: {"verdict": "sufficient"|"partial"|"none", "feedback": "<30 words>"}'
        )
        user = (
            f"Question: {original_query}\n"
            f"Rewritten: {rewritten_query}\n\n"
            f"Documents:\n{context}\n\n"
            "Evaluation (JSON only):"
        )

        eval_text, usage = self.llm.call(system, user, max_tokens=120)
        duration = (time.time() - t0) * 1000

        verdict, feedback = "none", eval_text
        try:
            m = re.search(r'\{.*?\}', eval_text, re.DOTALL)
            if m:
                parsed   = json.loads(m.group())
                verdict  = str(parsed.get("verdict", "none")).lower()
                feedback = parsed.get("feedback", eval_text)
        except Exception:
            low     = eval_text.lower()
            verdict = ("sufficient" if "sufficient" in low
                       else ("partial" if "partial" in low else "none"))

        is_relevant = verdict in ("sufficient", "partial")
        step_id     = _log_step(query_id, "relevance_evaluator", step_order,
                                input_text=rewritten_query,
                                output_text=f"verdict={verdict} | {feedback}",
                                duration_ms=duration)
        _log_llm_call(step_id, ACTIVE_MODEL_NAME, system, user, eval_text, usage)
        icon = {"sufficient": "✓", "partial": "~", "none": "✗"}.get(verdict, "?")
        print(f"  [EVALUATOR] {verdict.upper()} {icon} | {feedback[:80]}")
        return is_relevant, feedback, verdict

    # ── Agent 4: Generate grounded answer (RAG path) ──────────────────────────

    def _generate_grounded(self, query_id, original_query, rewritten_query,
                           docs, conversation_history, verdict="sufficient",
                           mcp_context="", step_order=6) -> Tuple[str, List[Dict]]:
        """
        FIX 5: context expanded to 4500 chars.
        FIX 8: returns (answer_with_citations, sources_list) separately.
        """
        t0      = time.time()
        context = _build_context(docs, max_chars=4500)  # FIX 5

        confidence_instruction = (
            "The retrieved documents are only PARTIALLY relevant — give the best "
            "partial answer using what is available."
            if verdict == "partial" else
            "The retrieved documents directly support answering this question."
        )

        upload_sources = list({d["source_file"] for d in docs if d.get("from_upload")})
        upload_note    = (
            f"\nNote: The user uploaded these files this session — treat them as "
            f"primary sources: {', '.join(upload_sources)}.\n"
            if upload_sources else ""
        )

        system = (
            "You are AgriBot, an expert agricultural research assistant.\n"
            f"{confidence_instruction}\n"
            f"{upload_note}"
            "Answer using ONLY the provided documents. "
            "Do not add general knowledge not in the documents.\n\n"
            "Output format:\n"
            "DIRECT ANSWER: <one clear sentence>\n\n"
            "EXPLANATION:\n<3-5 sentences>\n\n"
            "Do NOT write SOURCES — they are added automatically."
        )
        mcp_section = f"\nAdditional tool context:\n{mcp_context}\n" if mcp_context else ""
        user = (
            f"Documents:\n{context}\n"
            f"{mcp_section}"
            f"Conversation history:\n{conversation_history}\n\n"
            f"Question: {rewritten_query}\n\n"
            "Answer:"
        )

        raw_answer, usage = self.llm.call(system, user, max_tokens=700, temperature=0.15)

        # FIX 8: build structured sources, inject inline tags
        sources = _build_sources_from_docs(docs)
        answer  = _inject_inline_citations(raw_answer, sources)

        duration = (time.time() - t0) * 1000
        step_id  = _log_step(query_id, "main_llm_grounded", step_order,
                             input_text=rewritten_query, output_text=answer, duration_ms=duration)
        _log_llm_call(step_id, ACTIVE_MODEL_NAME, system, user, answer, usage)
        return answer, sources

    # ── Agent 5: Generate from web (force_web or RAG exhausted) ──────────────

    def _generate_from_web(self, query_id, original_query, rewritten_query,
                           conversation_history, mcp_context="",
                           step_order=3) -> Tuple[str, List[Dict]]:
        """
        FIX 2: Tavily ONLY runs here — never from the MCP orchestrator.
        This is the ONLY entry point to Tavily web search.
        Called when:
          (a) force_web=True  (user clicked "Web Search" toggle)
          (b) evaluator returns "none" after MAX_RETRIES RAG attempts
        Returns (answer_with_citations, sources_list).
        """
        t0 = time.time()
        print(f"  [WEB] Searching: {rewritten_query!r}")

        results: List[Dict] = []

        if _MCP_AVAILABLE:
            # FIX: search with original_query first — the rewriter sometimes
            # narrows the query too much (e.g. "PASSCO tagline" → "PASSCO vision statement
            # Pakistan" which Tavily can't answer). Try original first, fall back
            # to rewritten if original returns nothing useful.
            results = tavily_web_search(original_query, max_results=6)
            if not results:
                results = tavily_web_search(rewritten_query, max_results=6)

        if not results:
            # Trusted-sites scraper fallback
            try:
                from web_extractor import get_web_context
                web_chunks = get_web_context(
                    rewritten_query, max_search_results=6, top_chunks=4, max_extract_pages=3)
                if web_chunks:
                    print(f"  [WEB FALLBACK] {len(web_chunks)} chunks from trusted sites")
                    web_ctx   = ""
                    for i, c in enumerate(web_chunks, 1):
                        web_ctx += (
                            f"[Web {i}] {c['site_name']}\nURL: {c['url']}\n"
                            f"{c['text'][:500]}\n\n"
                        )
                    sites_str = ", ".join(dict.fromkeys(c["site_name"] for c in web_chunks))
                    system = (
                        f"You are AgriBot. Answer ONLY from the content below from: {sites_str}.\n"
                        "RULES: 1) Only use [Web N] blocks. 2) Cite sources by name. "
                        "3) No prior knowledge.\n\n"
                        "Format: DIRECT ANSWER: <sentence>\n\nEXPLANATION:\n<3-5 sentences>"
                    )
                    mcp_sec = f"\nTool context:\n{mcp_context}\n" if mcp_context else ""
                    user    = (f"Question: {rewritten_query}\n\nWeb content:\n{web_ctx}"
                               f"{mcp_sec}Conversation:\n{conversation_history}\n\nAnswer:")
                    try:
                        raw_answer, usage = self.llm.call(system, user, max_tokens=500, temperature=0.3)
                    except Exception as e:
                        raw_answer, usage = f"Model error: {e}", {}

                    sources = _build_sources_from_web([
                        {"title": c.get("title", ""),
                         "url":   c.get("url", ""),
                         "content": c.get("text", ""),
                         "site_name": c.get("site_name", ""),
                         "score": 1.0}
                        for c in web_chunks
                    ])
                    answer  = _inject_inline_citations(raw_answer, sources)
                    dur     = (time.time() - t0) * 1000
                    step_id = _log_step(query_id, "web_search_fallback", step_order,
                                        input_text=rewritten_query, output_text=answer, duration_ms=dur)
                    if usage:
                        _log_llm_call(step_id, ACTIVE_MODEL_NAME, system, user, answer, usage)
                    return answer, sources
            except Exception as e:
                print(f"  [WEB FALLBACK] Trusted-sites failed: {e}")

        if not results:
            msg = (
                "DIRECT ANSWER: No relevant information found via web search.\n\n"
                "EXPLANATION: Tavily returned no results and the trusted-sites "
                "fallback also found nothing. Please check that TAVILY_API_KEY is "
                "set (free key at https://app.tavily.com) and try rephrasing."
            )
            _log_step(query_id, "web_search_tavily", step_order,
                      input_text=rewritten_query, output_text=msg,
                      duration_ms=(time.time() - t0) * 1000)
            return msg, []

        # Tavily results → grounded answer
        web_ctx   = tavily_format(results, max_chars_per_result=500)
        sites_str = ", ".join(dict.fromkeys(r["site_name"] for r in results))
        system = (
            f"You are AgriBot. Answer ONLY from the web content below from: {sites_str}.\n\n"
            "RULES:\n1. Only use [Web N] blocks.\n2. Name each source.\n3. No prior knowledge.\n\n"
            "Format:\nDIRECT ANSWER: <one clear sentence>\n\n"
            "EXPLANATION:\n<3-5 sentences citing sources by name>\n\n"
            "Do NOT write SOURCES — added automatically."
        )
        mcp_sec = f"\nTool context:\n{mcp_context}\n" if mcp_context else ""
        user    = (f"Question: {rewritten_query}\n\nWeb content:\n{web_ctx}\n"
                   f"{mcp_sec}Conversation:\n{conversation_history}\n\nAnswer:")

        try:
            raw_answer, usage = self.llm.call(system, user, max_tokens=500, temperature=0.3)
        except Exception as e:
            raw_answer, usage = f"Model error: {e}", {}

        sources = _build_sources_from_web(results)
        answer  = _inject_inline_citations(raw_answer, sources)
        dur     = (time.time() - t0) * 1000
        step_id = _log_step(query_id, "web_search_tavily", step_order,
                            input_text=rewritten_query, output_text=answer, duration_ms=dur)
        if usage:
            _log_llm_call(step_id, ACTIVE_MODEL_NAME, system, user, answer, usage)
        return answer, sources

    # ── Main pipeline entry point ─────────────────────────────────────────────

    # ── Multilingual entry point (Stage 1: text-only) ──────────────────────
    def run(self, session_id: str, user_query: str,
            upload_chunks: List[Dict] = None,
            upload_file_ids: List[str] = None,
            force_web: bool = False) -> PipelineResult:
        """
        Public entry point. Wraps _run_core() with language detection and
        translation so the farmer can type Urdu, Roman Urdu, or English and
        get an answer back in the same language — without touching any of
        the retrieval/generation logic inside _run_core().

        Flow:
          1. Detect language of user_query: en | ur | roman_ur | mixed
          2. If non-English: normalize Roman Urdu terms and/or translate
             to English via NLLB-200 — this becomes the query _run_core()
             actually searches and generates with (English PDFs need an
             English query for good retrieval).
          3. Run the existing English pipeline completely unchanged.
          4. If the original query was non-English, translate the answer
             back before returning it. Citations/sources are left as-is —
             translating [1][2] tags would break them, and source labels
             (filenames, URLs) don't need translation.

        If language_layer.py isn't installed, this silently falls back to
        pure English-only behavior — no crash, no behavior change.
        """
        if not _LANG_LAYER_AVAILABLE:
            return self._run_core(session_id, user_query, upload_chunks,
                                  upload_file_ids, force_web)

        detected_lang = detect_language(user_query)
        print(f"[LANG] Detected: {detected_lang!r} for query: {user_query[:60]!r}")

        if detected_lang == "en":
            return self._run_core(session_id, user_query, upload_chunks,
                                  upload_file_ids, force_web)

        # Translate the farmer's query into English for retrieval + generation
        query_for_pipeline = translate_to_english(user_query, detected_lang, self.llm)
        print(f"[LANG] Translated query → {query_for_pipeline[:80]!r}")

        result = self._run_core(session_id, query_for_pipeline, upload_chunks,
                                upload_file_ids, force_web)

        # Translate the answer back to the farmer's language.
        # Inline [N] citation tags are plain ASCII digits in brackets —
        # NLLB passes them through unchanged, so translation doesn't break
        # the sources panel wiring.
        result.answer = translate_from_english(result.answer, detected_lang, self.llm)
        print(f"[LANG] Translated answer back to {detected_lang!r}")

        return result

    def _run_core(self, session_id: str, user_query: str,
            upload_chunks: List[Dict] = None,
            upload_file_ids: List[str] = None,
            force_web: bool = False) -> PipelineResult:
        """
        Execute the full pipeline. This is the ORIGINAL English-only pipeline
        logic, unchanged — renamed from run() to _run_core() so the new
        run() wrapper below can do language detection/translation around it
        without touching any retrieval, generation, or MCP logic in here.

        Args:
            session_id:     Unique session identifier.
            user_query:     The user's raw question.
            upload_chunks:    Chunks from session-uploaded files.
            upload_file_ids: file_id list for user_uploads ChromaDB query.
            force_web:       True when the UI "Web Search" toggle is ON.
                            Skips the PDF index and goes straight to Tavily.

        Returns:
            PipelineResult with .answer, .sources, .source_type, etc.
        """
        print(f"\n{'='*60}")
        print(f"[PIPELINE] Query: {user_query}")
        print(f"[PIPELINE] force_web={force_web} | upload_chunks={len(upload_chunks or [])} | file_ids={upload_file_ids or []}")
        print(f"{'='*60}")

        # DB records
        conn = db_schema.get_connection()
        conn.execute("INSERT OR IGNORE INTO sessions (session_id) VALUES (?)", (session_id,))
        query_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO queries (query_id, session_id, original_query) VALUES (?,?,?)",
            (query_id, session_id, user_query)
        )
        conn.commit()
        conn.close()

        conversation_history = self.memory.get_formatted(session_id)
        retry_count  = 0
        step_counter = 1

        # ── Step 1: Query Rewriter ────────────────────────────────────────────
        rewritten_query = self._query_rewriter(
            query_id, user_query, conversation_history, step_order=step_counter)
        step_counter += 1

        # ── Step 2: Orchestrator (advisory, logged only) ──────────────────────
        # FIX 4: result is logged but never gates the RAG path
        _needs_rag = self._orchestrator(
            query_id, rewritten_query, step_order=step_counter)
        step_counter += 1

        # ── Step 2b: MCP Tool Dispatch ────────────────────────────────────────
        # FIX 2 + FIX 3: Tavily absent from manifest; ran flag prevents false MCP tag
        mcp_context, mcp_ran = self._mcp_dispatch(
            rewritten_query, query_id=query_id, step_order=step_counter)
        step_counter += 1

        # ── Web search override (UI toggle) ───────────────────────────────────
        if force_web:
            answer, sources = self._generate_from_web(
                query_id, user_query, rewritten_query,
                conversation_history, mcp_context=mcp_context,
                step_order=step_counter)
            _log_response(query_id, answer, used_rag=False, retry_count=0)
            print("\n[PIPELINE] WEB response generated (force_web=True).")
            return PipelineResult(
                answer=answer, sources=sources,
                used_rag=False, retry_count=0,
                source_type="WEB",
            )

        # ── RAG path — always runs (FIX 4) ────────────────────────────────────
        self._ensure_bm25_built()
        evaluator_feedback = ""
        final_verdict      = "none"

        while retry_count <= MAX_RETRIES:
            if retry_count > 0:
                print(f"\n  [RETRY {retry_count}/{MAX_RETRIES}]")
                rewritten_query = self._query_rewriter(
                    query_id, user_query, conversation_history,
                    evaluator_feedback=evaluator_feedback,
                    step_order=step_counter)
                step_counter += 1

            # Step 3: Retrieve
            vector_results, bm25_results = self._retrieve(
                query_id, rewritten_query,
                upload_chunks=upload_chunks,
                upload_file_ids=upload_file_ids,
                step_order=step_counter)
            step_counter += 1

            # Step 4: RRF Rerank
            reranked_docs = self._rerank(
                query_id, vector_results, bm25_results, step_order=step_counter)
            step_counter += 1

            # Step 5: Relevance Evaluator
            is_relevant, evaluator_feedback, verdict = self._evaluator(
                query_id, user_query, rewritten_query,
                reranked_docs, step_order=step_counter)
            step_counter += 1
            final_verdict = verdict

            if is_relevant:
                break  # sufficient or partial → proceed to generation

            retry_count += 1

            # FIX 7: on last retry if we still have "partial", use those docs
            if retry_count > MAX_RETRIES:
                if final_verdict == "partial" and reranked_docs:
                    print("\n[PIPELINE] Partial docs on final retry — generating from partial.")
                    break

                # FIX: never fall back to web search when the user has an
                # uploaded file in this session. Meta-queries like "summarize
                # what I just uploaded" or "what does this document say"
                # contain no content keywords for vector/BM25 retrieval to
                # match against — the evaluator correctly says "none" for
                # THOSE matching purposes, but that doesn't mean the answer
                # should come from the open web. It means we should treat
                # the uploaded file as authoritative and summarize directly
                # from it, bypassing the relevance-matching step entirely.
                if upload_chunks:
                    print("\n[PIPELINE] No relevant docs via retrieval, but "
                          "an uploaded file exists this session — "
                          "generating directly from uploaded content "
                          "instead of web search.")
                    # Use the uploaded chunks in original document order
                    # (not relevance-ranked) — this gives a coherent basis
                    # for whole-document summarization requests, which is
                    # exactly the case retrieval-by-keyword-match can't serve.
                    upload_only_docs = [
                        {**c, "final_rank": i + 1, "rrf_score": 1.0,
                         "bm25_score": c.get("bm25_score"),
                         "vector_score": c.get("vector_score", 0.5)}
                        for i, c in enumerate(upload_chunks[:TOP_K_FINAL])
                    ]
                    answer, sources = self._generate_grounded(
                        query_id, user_query, rewritten_query,
                        upload_only_docs, conversation_history,
                        verdict="sufficient", mcp_context=mcp_context,
                        step_order=step_counter)
                    _log_response(query_id, answer, used_rag=True, retry_count=retry_count)
                    return PipelineResult(
                        answer=answer, sources=sources,
                        used_rag=True, retry_count=retry_count,
                        source_type="UPLOAD",
                    )

                print(f"\n[PIPELINE] No relevant docs after {MAX_RETRIES} retries — web fallback.")
                answer, sources = self._generate_from_web(
                    query_id, user_query, rewritten_query,
                    conversation_history, mcp_context=mcp_context,
                    step_order=step_counter)
                _log_response(query_id, answer, used_rag=False, retry_count=retry_count)
                return PipelineResult(
                    answer=answer, sources=sources,
                    used_rag=False, retry_count=retry_count,
                    source_type="WEB",
                )

        # ── Step 6: Generate grounded answer ──────────────────────────────────
        answer, sources = self._generate_grounded(
            query_id, user_query, rewritten_query,
            reranked_docs, conversation_history,
            verdict=final_verdict, mcp_context=mcp_context,
            step_order=step_counter)

        _log_response(query_id, answer, used_rag=True, retry_count=retry_count)
        print(f"\n[PIPELINE] RAG response generated (retries={retry_count}).")

        # FIX 3: MCP tag only when a real tool ran
        source_type = "MCP" if mcp_ran else "RAG"
        return PipelineResult(
            answer=answer, sources=sources,
            used_rag=True, retry_count=retry_count,
            source_type=source_type,
        )


# ══════════════════════════════════════════════════════════════════════════════
#  DB inspection helper (unchanged)
# ══════════════════════════════════════════════════════════════════════════════

def inspect_last_query():
    conn  = db_schema.get_connection()
    query = conn.execute(
        "SELECT * FROM queries ORDER BY timestamp DESC LIMIT 1").fetchone()
    if not query:
        print("No queries logged yet.")
        return

    print(f"\n{'='*60}\nQuery: {query['original_query']}\nID: {query['query_id']}")
    steps = conn.execute(
        "SELECT * FROM pipeline_steps WHERE query_id=? ORDER BY step_order",
        (query["query_id"],)).fetchall()
    print(f"\nPipeline steps ({len(steps)}):")
    for s in steps:
        print(f"  [{s['step_order']}] {s['step_name']:25s} {s['duration_ms']:6.0f}ms  {s['status']}")

    llm_calls = conn.execute(
        """SELECT lc.total_tokens FROM llm_calls lc
           JOIN pipeline_steps ps ON lc.step_id=ps.step_id
           WHERE ps.query_id=?""", (query["query_id"],)).fetchall()
    total_tok = sum(r["total_tokens"] or 0 for r in llm_calls)
    print(f"\nLLM calls: {len(llm_calls)} | Tokens: {total_tok}")

    response = conn.execute(
        "SELECT * FROM responses WHERE query_id=?", (query["query_id"],)).fetchone()
    if response:
        print(f"\nRAG={bool(response['used_rag'])}, retries={response['retry_count']}")
        print(response["final_response"][:400])
    conn.close()
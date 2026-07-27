#!/usr/bin/env python3
"""
check_startup.py  —  AgriBot Pre-flight Check
===============================================
Run this BEFORE starting the server to verify everything is in place.

Usage:
    python check_startup.py

If all checks pass, run:
    uvicorn api_server:app --reload --port 8001
"""

import os, sys, importlib, subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
PASS = "✓"
FAIL = "✗"
WARN = "⚠"

errors   = []
warnings = []

def ok(msg):  print(f"  {PASS}  {msg}")
def err(msg): print(f"  {FAIL}  {msg}"); errors.append(msg)
def warn(msg):print(f"  {WARN}  {msg}"); warnings.append(msg)

print("\n" + "="*60)
print("  AgriBot — Pre-flight Startup Check")
print("="*60)

# ── 1. Required Python files ──────────────────────────────────────────────────
print("\n[1] Project files")
REQUIRED_FILES = [
    ("api_server.py",        "Main FastAPI server"),
    ("auth_routes.py",       "Authentication endpoints — rename from 'auth_routes (1).py'"),
    ("rag_pipeline.py",      "RAG pipeline"),
    ("vector_store.py",      "ChromaDB wrapper"),
    ("mcp_tools.py",         "MCP tools (weather, calendar, converter)"),
    ("mcp_email.py",         "Welcome email MCP"),
    ("mcp_weather_advisor.py","Weather + sowing advisor MCP"),
    ("db_schema.py",         "SQLite schema"),
    ("main.py",              "Index builder"),
]
OPTIONAL_FILES = [
    ("mcp_pdf_export.py",    "PDF export — pip install weasyprint to enable"),
    ("project_routes.py",    "Project management routes"),
    ("website_crawler.py",   "Website crawler — Layer 2 knowledge"),
    ("auth_backend.py",      "Legacy auth (replaced by auth_routes.py)"),
]
for fname, desc in REQUIRED_FILES:
    path = PROJECT_DIR / fname
    if path.exists():
        ok(f"{fname}  ({desc})")
    else:
        err(f"{fname} MISSING — {desc}")

print("\n  Optional files:")
for fname, desc in OPTIONAL_FILES:
    path = PROJECT_DIR / fname
    if path.exists():
        ok(f"{fname}  ({desc})")
    else:
        warn(f"{fname} not found — {desc}")

# ── 2. Python packages ────────────────────────────────────────────────────────
print("\n[2] Python packages")
REQUIRED_PKGS = [
    ("fastapi",          "FastAPI web framework"),
    ("uvicorn",          "ASGI server"),
    ("pydantic",         "Request/response models"),
    ("chromadb",         "Vector database"),
    ("groq",             "Groq LLM client"),
    ("rank_bm25",        "BM25 keyword search"),
    ("sentence_transformers", "Embeddings (needed by chromadb)"),
    ("PyMuPDF",          "PDF text extraction (import as fitz)"),
    ("bs4",              "BeautifulSoup — web crawler"),
    ("trafilatura",      "HTML text cleaner — web crawler"),
]
OPTIONAL_PKGS = [
    ("tavily",           "Web search — pip install tavily-python"),
    ("weasyprint",       "PDF export — pip install weasyprint"),
    ("apscheduler",      "Weekly crawl scheduler"),
    ("jwt",              "JWT auth — pip install PyJWT"),
    ("bcrypt",           "Password hashing"),
    ("docx",             "Word doc extraction — pip install python-docx"),
]
for pkg, desc in REQUIRED_PKGS:
    try:
        importlib.import_module(pkg)
        ok(f"{pkg}")
    except ImportError:
        err(f"{pkg} not installed — {desc}")
        errors.append(f"pip install {pkg}")

print("\n  Optional packages:")
for pkg, desc in OPTIONAL_PKGS:
    try:
        importlib.import_module(pkg)
        ok(f"{pkg}")
    except ImportError:
        warn(f"{pkg} not installed — {desc}")

# ── 3. Environment variables ──────────────────────────────────────────────────
print("\n[3] Environment variables")
GROQ_KEY = os.environ.get("GROQ_API_KEY","")
if GROQ_KEY:
    ok(f"GROQ_API_KEY set ({GROQ_KEY[:8]}...)")
else:
    err("GROQ_API_KEY not set — get free key at https://console.groq.com")

TAVILY_KEY = os.environ.get("TAVILY_API_KEY","")
if TAVILY_KEY:
    ok(f"TAVILY_API_KEY set ({TAVILY_KEY[:8]}...)")
else:
    warn("TAVILY_API_KEY not set — web search disabled (optional)")

SMTP_USER = os.environ.get("AGRIBOT_EMAIL_FROM","") or os.environ.get("SMTP_USER","")
SMTP_PASS = os.environ.get("AGRIBOT_EMAIL_PASSWORD","") or os.environ.get("SMTP_PASS","")
if SMTP_USER and SMTP_PASS:
    ok(f"Email configured ({SMTP_USER})")
else:
    warn("Email not configured — welcome emails disabled (optional)")
    warn("Set AGRIBOT_EMAIL_FROM + AGRIBOT_EMAIL_PASSWORD")

MODEL = os.environ.get("GROQ_MODEL","llama-3.3-70b-versatile")
ok(f"GROQ_MODEL = {MODEL}")

# ── 4. ChromaDB / vector store ────────────────────────────────────────────────
print("\n[4] Knowledge base")
try:
    sys.path.insert(0, str(PROJECT_DIR))
    import vector_store
    count = vector_store.collection_size()
    if count > 0:
        ok(f"ChromaDB: {count:,} chunks indexed")
        ok(f"Embedding model: {vector_store.EMBEDDING_MODEL}")
    else:
        err("ChromaDB empty — run: python main.py --index")
        err("If you changed embedding model, first run: python main.py --index --reset")
except Exception as e:
    err(f"ChromaDB error: {e}")

# ── 5. pdfs folder ────────────────────────────────────────────────────────────
print("\n[5] PDF knowledge base")
pdf_dir = PROJECT_DIR / "pdfs"
if pdf_dir.exists():
    pdfs = list(pdf_dir.glob("*.pdf"))
    if pdfs:
        total_mb = sum(p.stat().st_size for p in pdfs) / 1_048_576
        ok(f"{len(pdfs)} PDFs in pdfs/ folder ({total_mb:.1f} MB)")
    else:
        warn("pdfs/ folder is empty — run: python download_agri_docs.py")
else:
    warn("pdfs/ folder not found — create it and add PDFs")

# ── 6. Auth DB ────────────────────────────────────────────────────────────────
print("\n[6] Auth database")
db_files = list(PROJECT_DIR.glob("*.db"))
if db_files:
    ok(f"DB files: {[f.name for f in db_files]}")
else:
    warn("No .db files yet — will be created on first run")

# ── 7. Vite proxy ─────────────────────────────────────────────────────────────
print("\n[7] Frontend proxy config")
vite_config = PROJECT_DIR / "vite.config.js"
if not vite_config.exists():
    vite_config = PROJECT_DIR / "vite.config.ts"
if vite_config.exists():
    content = vite_config.read_text()
    if "8001" in content:
        ok("vite.config.js proxies to port 8001 ✓")
    elif "8000" in content:
        warn("vite.config.js proxies to port 8000 but api_server runs on 8001")
        warn("Fix: change target to http://localhost:8001 in vite.config.js")
    else:
        warn("Could not verify proxy port in vite.config.js")
else:
    warn("vite.config.js not found — check your proxy configuration")

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "="*60)
if errors:
    print(f"  {len(errors)} ERROR(S) — fix these before starting:")
    for e in errors:
        print(f"    {FAIL} {e}")
    print()
if warnings:
    print(f"  {len(warnings)} WARNING(S) — optional but recommended:")
    for w in warnings:
        print(f"    {WARN} {w}")
    print()

if not errors:
    print("  ALL REQUIRED CHECKS PASSED ✓")
    print()
    print("  Start the backend:")
    print("    uvicorn api_server:app --reload --port 8001")
    print()
    print("  In a second terminal, start the frontend:")
    print("    npm run dev")
    print()
    print("  Open: http://localhost:5173")
else:
    print(f"  Fix the {len(errors)} error(s) above then re-run: python check_startup.py")
print("="*60 + "\n")

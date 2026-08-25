"""
vector_store.py
===============
ChromaDB vector store for Agentic RAG Platform.

Embedding model: BAAI/bge-m3  (upgraded from all-MiniLM-L6-v2)
  - Multilingual: handles English, Urdu, Roman-Urdu, domain terminology
  - 1024-dim dense vectors — much stronger retrieval than MiniLM 384-dim
  - HuggingFace: https://huggingface.co/BAAI/bge-m3
  - First run downloads ~570MB, then cached locally — no re-download

IMPORTANT: Switching embedding models requires a full re-index.
  Run:  python vector_store.py --reset
  Then: python build_pakistan_agri_kb.py

API surface (unchanged — fully backward-compatible):
  EMBEDDING_MODEL        str
  _get_client()          → chromadb.PersistentClient
  _get_ef()              → embedding function
  _get_collection()      → chromadb.Collection  (COLLECTION_NAME)
  collection_size()      → int
  similarity_search()    → List[dict]  keys: chunk_text, source_file, page_num, vector_score, doc_id
  index_chunks()         → int  (accepts List[dict] OR List[Tuple[str,str,int]])
  reset_collection()     → None
"""

import os
import sys
import uuid
from typing import List, Dict, Any, Tuple, Union

import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings
from chromadb.utils import embedding_functions

# ── Config ─────────────────────────────────────────────────────────────────────
BASE_DIR = (
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if os.path.basename(os.path.dirname(os.path.abspath(__file__))) == "src"
    else os.path.dirname(os.path.abspath(__file__))
)

CHROMA_DIR      = os.path.join(BASE_DIR, "chroma_db")
COLLECTION_NAME = os.environ.get("CHROMA_COLLECTION", "agriculture_docs")

# ── Embedding model ─────────────────────────────────────────────────────────────
# BAAI/bge-m3 — requested explicitly. 2.27 GB download, needs 3+ GB free
# disk space (check with: Get-PSDrive C  on Windows).
#   - 1024-dim vectors, state-of-the-art multilingual retrieval quality
#   - Multilingual: handles English, Urdu, Roman-Urdu, domain terms
#   - No API key required — runs fully offline after first download
#
# If you hit disk-space errors again, override without editing code:
#   $env:EMBEDDING_MODEL = "intfloat/multilingual-e5-base"   # 278 MB fallback
#
# To use HuggingFace API (cloud) instead of local model:
#   NOT RECOMMENDED — adds latency, costs money, needs internet for every query.
#   For this project, local models are always better.

EMBEDDING_MODEL = os.environ.get(
    "EMBEDDING_MODEL",
    "intfloat/multilingual-e5-base"   # 278 MB fallback, CPU-friendly multilingual (English/Urdu)
)

# ── Singletons ─────────────────────────────────────────────────────────────────
_client: chromadb.PersistentClient = None
_collection = None
_ef = None


# ── Embedding function ─────────────────────────────────────────────────────────

def _get_ef():
    """
    Local SentenceTransformer embedding using intfloat/multilingual-e5-base.
    Runs fully offline after first download — no API key ever needed.
    Download size: ~278 MB (cached in huggingface hub cache after first run).
    Override model with env var: EMBEDDING_MODEL=<model-name>
    Requires:  pip install sentence-transformers
    """
    global _ef
    if _ef is None:
        size_hint = "~278 MB" if "e5-base" in EMBEDDING_MODEL else "~117 MB" if "e5-small" in EMBEDDING_MODEL else "varies"
        print(f"[VECTOR] Loading '{EMBEDDING_MODEL}' locally "
              f"(first download {size_hint}, then instant from cache)...")
        _ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL,
            device="cpu",
        )
        print("[VECTOR] Embedding model ready.")
    return _ef


def _get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        os.makedirs(CHROMA_DIR, exist_ok=True)
        _client = chromadb.PersistentClient(path=CHROMA_DIR)
        print(f"[VECTOR] ChromaDB initialized at {CHROMA_DIR}")
    return _client


def _get_collection():
    """Return (or create) the main ChromaDB collection with bge-m3 embeddings."""
    global _collection
    if _collection is None:
        client = _get_client()
        ef     = _get_ef()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )
        print(f"[VECTOR] Collection '{COLLECTION_NAME}' ready "
              f"({_collection.count()} documents)")
    return _collection


# ── Public API ─────────────────────────────────────────────────────────────────

def collection_size() -> int:
    try:
        return _get_collection().count()
    except Exception:
        return 0


def index_chunks(
    chunks: Union[List[Dict], List[Tuple]],
    batch_size: int = 64,   # smaller batches — bge-m3 is heavier than MiniLM
    verbose: bool = True,
) -> int:
    """
    Add chunks to ChromaDB. Accepts two formats:

    Format A (dict, from build_pakistan_agri_kb.py and rag_pipeline.py):
        [{"chunk_text": str, "source_file": str, "page_num": int, ...}, ...]

    Format B (tuple, legacy):
        [(chunk_text, source_file, page_num), ...]

    Returns number of chunks successfully indexed.
    """
    collection = _get_collection()

    # Normalise to list of dicts
    normalised: List[Dict] = []
    for item in chunks:
        if isinstance(item, dict):
            normalised.append(item)
        elif isinstance(item, (tuple, list)) and len(item) >= 2:
            normalised.append({
                "chunk_text":  item[0],
                "source_file": item[1],
                "page_num":    item[2] if len(item) > 2 else 0,
            })
        else:
            continue

    added = 0
    for i in range(0, len(normalised), batch_size):
        batch = normalised[i : i + batch_size]
        ids, docs, metas = [], [], []
        for chunk in batch:
            text = chunk.get("chunk_text", "").strip()
            if not text:
                continue
            ids.append(str(uuid.uuid4()))
            docs.append(text)
            # Preserve all string/int/float/bool metadata fields
            meta = {
                k: v for k, v in chunk.items()
                if k != "chunk_text" and isinstance(v, (str, int, float, bool))
            }
            meta.setdefault("source_file", chunk.get("source_file", "unknown"))
            meta.setdefault("page_num",    chunk.get("page_num", 0))
            metas.append(meta)

        if not ids:
            continue

        try:
            collection.add(documents=docs, ids=ids, metadatas=metas)
            added += len(ids)
            if verbose:
                print(f"  [VECTOR] Batch {i//batch_size + 1}: "
                      f"{added}/{len(normalised)} indexed")
        except Exception as e:
            print(f"  [VECTOR] Batch {i//batch_size + 1} error: {e}")

    if verbose:
        print(f"[VECTOR] Collection total: {collection.count()} docs")
    return added


def similarity_search(
    query: str,
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    """
    Semantic search using bge-m3 embeddings.

    Returns list of dicts (same schema as before):
        chunk_text, source_file, page_num, vector_score, doc_id
    """
    collection = _get_collection()
    if collection.count() == 0:
        print("[VECTOR] WARNING: Empty collection — run build_pakistan_agri_kb.py first.")
        return []

    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    output = []
    for doc, meta, dist, did in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
        results["ids"][0],
    ):
        output.append({
            "doc_id":       did,
            "chunk_text":   doc,
            "source_file":  meta.get("source_file", "unknown"),
            "page_num":     meta.get("page_num", 0),
            "vector_score": round(1.0 - dist, 4),   # cosine distance → similarity
        })
    return output


def reset_collection():
    """
    Delete and recreate the collection.
    Required when switching embedding models — vectors from different
    embedding spaces cannot coexist in the same collection.

    After reset, re-run build_pakistan_agri_kb.py to re-index.
    """
    global _collection, _ef
    client = _get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"[VECTOR] Deleted collection '{COLLECTION_NAME}'")
    except Exception:
        pass
    _collection = None
    _ef = None
    print("[VECTOR] Collection reset. Re-run build_pakistan_agri_kb.py to re-index with bge-m3.")


# ── CLI helper ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if "--reset" in sys.argv:
        reset_collection()
    else:
        print(f"Embedding model : {EMBEDDING_MODEL}")
        print(f"Collection name : {COLLECTION_NAME}")
        print(f"Collection size : {collection_size()} chunks")
        if collection_size() > 0:
            print("\nSample search: 'wheat rust disease Punjab'")
            results = similarity_search("wheat rust disease Punjab", top_k=3)
            for r in results:
                print(f"\n  [{r['source_file']} p.{r['page_num']}] score={r['vector_score']}")
                print(f"  {r['chunk_text'][:200]}...")
"""
website_crawler.py  —  AgriBot Trusted Website Crawler
========================================================
Crawls 20 trusted Pakistan agriculture websites, extracts clean text,
chunks it, embeds it, and stores it in ChromaDB collection "website_index".

This is Layer 2 of the Hybrid Knowledge Architecture:
  PDF RAG (Layer 1)  +  Website Index (Layer 2)  +  Live Search (Layer 3)

The website index is searched alongside PDFs in every RAG query,
giving you fresh content from PARC, Punjab Agriculture, PASSCO etc.
without downloading any PDFs.

INSTALL (run once):
    pip install requests beautifulsoup4 lxml trafilatura apscheduler --break-system-packages

USAGE:
    # Full crawl (first time, takes 10-20 min)
    python website_crawler.py --crawl

    # Quick update (only changed pages, run weekly)
    python website_crawler.py --update

    # See what's indexed
    python website_crawler.py --stats
"""

import os
import re
import json
import time
import hashlib
import argparse
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

# ── Config ────────────────────────────────────────────────────────────────────
CRAWLER_DB   = Path("crawler.db")          # SQLite: tracks pages + hashes
CHUNK_SIZE   = 600                         # chars per chunk
CHUNK_OVERLAP= 100
MAX_PAGES_PER_SITE = 40                    # don't over-crawl
REQUEST_PAUSE = 1.5                        # seconds between requests
CRAWL_TIMEOUT = 10
MIN_TEXT_LEN  = 150                        # skip stub pages
CHROMA_COLLECTION = "website_index"

HEADERS = {
    "User-Agent": "AgriBot/1.0 (Pakistan Agriculture Research Assistant; +https://agribot.pk)",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ur;q=0.5",
}

# ══════════════════════════════════════════════════════════════════════════════
#  TRUSTED SITES — 20 Pakistan agriculture sources
#  Format: { url, name, category, priority (1=highest), depth }
# ══════════════════════════════════════════════════════════════════════════════

TRUSTED_SITES = [
    # ── Government — highest priority ─────────────────────────────────────────
    {
        "url":      "https://parc.gov.pk",
        "name":     "PARC",
        "category": "government_research",
        "priority": 1,
        "depth":    2,
        "focus":    ["research", "crop", "variety", "annual", "publication"],
    },
    {
        "url":      "https://agripunjab.gov.pk",
        "name":     "Punjab Agriculture Department",
        "category": "government_provincial",
        "priority": 1,
        "depth":    2,
        "focus":    ["crop", "package", "pest", "disease", "fertilizer", "extension"],
    },
    {
        "url":      "https://sindhagri.gos.pk",
        "name":     "Sindh Agriculture Department",
        "category": "government_provincial",
        "priority": 2,
        "depth":    2,
        "focus":    ["crop", "disease", "irrigation", "policy"],
    },
    {
        "url":      "https://mnfsr.gov.pk",
        "name":     "MNFSR Pakistan",
        "category": "government_federal",
        "priority": 1,
        "depth":    2,
        "focus":    ["food", "security", "policy", "statistics", "publication"],
    },
    {
        "url":      "https://passco.gov.pk",
        "name":     "PASSCO",
        "category": "government_federal",
        "priority": 2,
        "depth":    2,
        "focus":    ["storage", "procurement", "wheat", "grain", "depot"],
    },
    {
        "url":      "https://narc.gov.pk",
        "name":     "NARC",
        "category": "government_research",
        "priority": 1,
        "depth":    2,
        "focus":    ["variety", "research", "crop", "publication", "seed"],
    },
    {
        "url":      "https://nfdc.gov.pk",
        "name":     "NFDC",
        "category": "government_federal",
        "priority": 2,
        "depth":    2,
        "focus":    ["fertilizer", "recommendation", "soil", "nutrient"],
    },
    # ── Research institutions ─────────────────────────────────────────────────
    {
        "url":      "https://www.uaar.edu.pk",
        "name":     "UAAR (Pir Mehr Ali Shah University)",
        "category": "university",
        "priority": 2,
        "depth":    2,
        "focus":    ["agriculture", "research", "publication", "faculty"],
    },
    {
        "url":      "https://www.sau.edu.pk",
        "name":     "Sindh Agriculture University",
        "category": "university",
        "priority": 3,
        "depth":    1,
        "focus":    ["research", "crop", "faculty"],
    },
    {
        "url":      "https://www.luawms.edu.pk",
        "name":     "LUAWMS Balochistan",
        "category": "university",
        "priority": 3,
        "depth":    1,
        "focus":    ["agriculture", "research", "balochistan"],
    },
    # ── International — Pakistan-relevant pages ───────────────────────────────
    {
        "url":      "https://www.fao.org/pakistan",
        "name":     "FAO Pakistan",
        "category": "international",
        "priority": 1,
        "depth":    2,
        "focus":    ["pakistan", "crop", "food", "security", "agriculture"],
    },
    {
        "url":      "https://www.icarda.org/pakistan",
        "name":     "ICARDA Pakistan",
        "category": "international",
        "priority": 2,
        "depth":    2,
        "focus":    ["barley", "lentil", "chickpea", "wheat", "pakistan"],
    },
    {
        "url":      "https://www.irri.org/countries/pakistan",
        "name":     "IRRI Pakistan",
        "category": "international",
        "priority": 2,
        "depth":    2,
        "focus":    ["rice", "pakistan", "variety", "yield"],
    },
    # ── Market & Economics ────────────────────────────────────────────────────
    {
        "url":      "https://www.pbs.gov.pk",
        "name":     "Pakistan Bureau of Statistics",
        "category": "government_data",
        "priority": 2,
        "depth":    1,
        "focus":    ["agriculture", "statistics", "census", "crop"],
    },
    {
        "url":      "https://www.commerce.gov.pk",
        "name":     "Ministry of Commerce Pakistan",
        "category": "government_data",
        "priority": 3,
        "depth":    1,
        "focus":    ["agriculture", "export", "trade", "commodity"],
    },
    # ── Extension & Farmer-Facing ─────────────────────────────────────────────
    {
        "url":      "https://kisaan.pk",
        "name":     "Kisaan Pakistan",
        "category": "extension",
        "priority": 2,
        "depth":    2,
        "focus":    ["crop", "pest", "disease", "farming", "tip"],
    },
    {
        "url":      "https://pakissan.com",
        "name":     "Pakissan",
        "category": "extension",
        "priority": 2,
        "depth":    2,
        "focus":    ["crop", "farming", "pest", "advice", "Pakistan"],
    },
    {
        "url":      "https://www.aari.res.in",  # Punjab AARI India — useful for shared crop science
        "name":     "AARI Punjab",
        "category": "research",
        "priority": 3,
        "depth":    1,
        "focus":    ["wheat", "rice", "cotton", "variety", "disease"],
    },
    # ── Weather & Climate ─────────────────────────────────────────────────────
    {
        "url":      "https://www.pmd.gov.pk",
        "name":     "Pakistan Meteorological Department",
        "category": "weather",
        "priority": 1,
        "depth":    1,
        "focus":    ["weather", "rainfall", "forecast", "climate", "agro"],
    },
    {
        "url":      "https://www.finance.gov.pk",
        "name":     "Ministry of Finance — Economic Survey",
        "category": "government_data",
        "priority": 1,
        "depth":    1,
        "focus":    ["agriculture", "survey", "chapter", "crop", "gdp"],
    },
]


# ══════════════════════════════════════════════════════════════════════════════
#  SQLite — tracks pages crawled, content hash, last updated
# ══════════════════════════════════════════════════════════════════════════════

def init_crawler_db():
    conn = sqlite3.connect(CRAWLER_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS crawled_pages (
            url          TEXT PRIMARY KEY,
            site_name    TEXT,
            category     TEXT,
            title        TEXT,
            content_hash TEXT,
            chunk_count  INTEGER DEFAULT 0,
            last_crawled TEXT,
            status       TEXT DEFAULT 'ok'
        )
    """)
    conn.commit()
    conn.close()


def _db():
    c = sqlite3.connect(CRAWLER_DB)
    c.row_factory = sqlite3.Row
    return c


# ══════════════════════════════════════════════════════════════════════════════
#  Text extraction
# ══════════════════════════════════════════════════════════════════════════════

def extract_text(html: str, url: str) -> tuple:
    """Returns (title, clean_text) using trafilatura first, BS4 fallback."""
    title = ""
    text  = ""

    # Method 1: trafilatura (best quality)
    try:
        import trafilatura
        extracted = trafilatura.extract(
            html, include_tables=True, include_links=False,
            include_images=False, no_fallback=False,
        )
        if extracted and len(extracted) > MIN_TEXT_LEN:
            text = extracted
    except Exception:
        pass

    # Method 2: BeautifulSoup fallback
    if not text:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")
            for tag in soup(["script", "style", "nav", "footer", "header",
                              "aside", "form", "iframe", "noscript"]):
                tag.decompose()
            text = " ".join(soup.get_text(" ", strip=True).split())
            text = re.sub(r'\s{3,}', '\n\n', text)
        except Exception:
            pass

    # Extract title
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        t    = soup.find("title")
        if t:
            title = t.get_text(strip=True)
            title = re.sub(r'\s*[|–—-].*$', '', title).strip()
    except Exception:
        title = urlparse(url).path.strip("/").replace("/", " — ")

    return title, text


def chunk_text(text: str, source_url: str, site_name: str,
               category: str, title: str) -> List[Dict]:
    """Split text into overlapping chunks with rich metadata."""
    chunks = []
    start  = 0
    idx    = 0
    while start < len(text):
        end   = start + CHUNK_SIZE
        chunk = text[start:end].strip()
        if chunk:
            chunks.append({
                "text":      chunk,
                "source":    source_url,
                "site_name": site_name,
                "category":  category,
                "title":     title,
                "chunk_idx": idx,
                "type":      "website",
            })
            idx += 1
        start = end - CHUNK_OVERLAP
    return chunks


# ══════════════════════════════════════════════════════════════════════════════
#  ChromaDB — website_index collection
# ══════════════════════════════════════════════════════════════════════════════

def _get_website_collection():
    """Get or create the website_index ChromaDB collection."""
    import chromadb
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

    ef     = SentenceTransformerEmbeddingFunction(model_name="intfloat/multilingual-e5-base")
    client = chromadb.PersistentClient(path="./chroma_db")
    col    = client.get_or_create_collection(
        name=CHROMA_COLLECTION,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )
    return col


def index_chunks_to_chroma(chunks: List[Dict], url: str):
    """Upsert chunks into website_index ChromaDB collection."""
    if not chunks:
        return
    try:
        col = _get_website_collection()
        ids, docs, metas = [], [], []
        for c in chunks:
            uid = hashlib.md5(f"{url}::{c['chunk_idx']}".encode()).hexdigest()
            ids.append(uid)
            docs.append(c["text"])
            metas.append({
                "source":    c["source"],
                "site_name": c["site_name"],
                "category":  c["category"],
                "title":     c["title"],
                "type":      "website",
            })
        col.upsert(ids=ids, documents=docs, metadatas=metas)
    except Exception as e:
        print(f"    [CHROMA] Index error: {e}")


def search_website_index(query: str, top_k: int = 6) -> List[Dict]:
    """
    Search the website_index ChromaDB collection.
    Returns list of dicts: {text, source, site_name, category, title, score}
    Called from rag_pipeline._retrieve() alongside main PDF collection.
    """
    try:
        col = _get_website_collection()
        if col.count() == 0:
            return []
        results = col.query(
            query_texts=[query],
            n_results=min(top_k, col.count()),
            include=["documents", "metadatas", "distances"],
        )
        out = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            out.append({
                "chunk_text":  doc,
                "source_file": meta.get("site_name", "website"),
                "page_num":    0,
                "vector_score": round(1.0 - dist, 4),
                "bm25_score":  None,
                "from_website": True,
                "url":         meta.get("source", ""),
                "title":       meta.get("title", ""),
                "site_name":   meta.get("site_name", ""),
                "category":    meta.get("category", ""),
            })
        return out
    except Exception as e:
        print(f"  [WEBSITE_INDEX] Search error: {e}")
        return []


# ══════════════════════════════════════════════════════════════════════════════
#  Crawler
# ══════════════════════════════════════════════════════════════════════════════

def crawl_site(site: Dict, update_only: bool = False) -> int:
    """Crawl one site. Returns number of pages indexed."""
    import requests
    from collections import deque

    base_url  = site["url"].rstrip("/")
    site_name = site["name"]
    category  = site["category"]
    max_depth = site.get("depth", 2)
    focus_kws = site.get("focus", [])

    visited   = set()
    queue     = deque([(base_url, 0)])
    pages_done= 0
    db        = _db()

    print(f"\n  Crawling: {site_name}")
    print(f"  URL: {base_url} | max_pages: {MAX_PAGES_PER_SITE} | depth: {max_depth}")

    while queue and pages_done < MAX_PAGES_PER_SITE:
        url, depth = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        # Skip non-HTML resources
        if re.search(r'\.(jpg|jpeg|png|gif|svg|css|js|ico|woff|pdf|zip|rar|docx)(\?|$)', url, re.I):
            continue

        # Check if page changed (for update_only mode)
        if update_only:
            row = db.execute("SELECT content_hash, last_crawled FROM crawled_pages WHERE url=?",
                             (url,)).fetchone()
            if row:
                # Skip if crawled in the last 6 days
                last = datetime.fromisoformat(row["last_crawled"])
                if datetime.now() - last < timedelta(days=6):
                    continue

        try:
            resp = requests.get(url, headers=HEADERS, timeout=CRAWL_TIMEOUT,
                                verify=False, allow_redirects=True)
            if resp.status_code != 200:
                continue
            if "text/html" not in resp.headers.get("Content-Type", ""):
                continue
            html = resp.text
        except Exception as e:
            print(f"    skip {url}: {e}")
            continue

        # Extract text
        title, text = extract_text(html, url)
        if len(text) < MIN_TEXT_LEN:
            time.sleep(0.3)
            continue

        # Content-hash — skip if unchanged
        content_hash = hashlib.md5(text.encode()).hexdigest()
        existing = db.execute("SELECT content_hash FROM crawled_pages WHERE url=?",
                              (url,)).fetchone()
        if existing and existing["content_hash"] == content_hash:
            pages_done += 1
            time.sleep(0.3)
            continue

        # Chunk + index
        chunks = chunk_text(text, url, site_name, category, title)
        index_chunks_to_chroma(chunks, url)

        # Record in DB
        db.execute("""
            INSERT OR REPLACE INTO crawled_pages
            (url, site_name, category, title, content_hash, chunk_count, last_crawled, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'ok')
        """, (url, site_name, category, title, content_hash,
              len(chunks), datetime.now().isoformat()))
        db.commit()

        pages_done += 1
        print(f"    [{pages_done:02d}] {title[:60]:<60} {len(chunks)} chunks")

        # Discover links for next depth level
        if depth < max_depth:
            try:
                from bs4 import BeautifulSoup
                soup  = BeautifulSoup(html, "lxml")
                links = []
                for a in soup.find_all("a", href=True):
                    href = urljoin(url, a["href"]).split("#")[0].split("?")[0]
                    if not href.startswith(base_url):
                        continue
                    if href in visited:
                        continue
                    # Prioritise focus keyword URLs
                    path_lower = href.lower()
                    score = sum(1 for kw in focus_kws if kw in path_lower)
                    links.append((score, href))
                # Sort: focused pages first
                links.sort(key=lambda x: x[0], reverse=True)
                for _, href in links[:20]:
                    if href not in visited:
                        queue.append((href, depth + 1))
            except Exception:
                pass

        time.sleep(REQUEST_PAUSE)

    db.close()
    return pages_done


def crawl_all(update_only: bool = False):
    """Crawl all trusted sites, sorted by priority."""
    import urllib3
    urllib3.disable_warnings()

    init_crawler_db()
    sites_sorted = sorted(TRUSTED_SITES, key=lambda s: s["priority"])
    total_pages  = 0

    print(f"\n{'='*60}")
    print(f"  AgriBot Website Crawler — {'UPDATE' if update_only else 'FULL CRAWL'}")
    print(f"  Sites: {len(sites_sorted)} | Mode: {'changed pages only' if update_only else 'all pages'}")
    print(f"{'='*60}")

    for site in sites_sorted:
        pages = crawl_site(site, update_only=update_only)
        total_pages += pages

    # Print summary
    db  = _db()
    col = None
    try:
        col = _get_website_collection()
        chunk_count = col.count()
    except Exception:
        chunk_count = 0

    rows = db.execute("SELECT COUNT(*) as n FROM crawled_pages WHERE status='ok'").fetchone()
    db.close()

    print(f"\n{'='*60}")
    print(f"  CRAWL COMPLETE")
    print(f"  Pages crawled  : {rows['n']}")
    print(f"  Website chunks : {chunk_count:,}")
    print(f"  Collection     : {CHROMA_COLLECTION}")
    print(f"{'='*60}")
    print(f"\n  Next: restart api_server to use the new website index.")


def print_stats():
    init_crawler_db()
    db = _db()
    rows = db.execute("""
        SELECT site_name, COUNT(*) as pages, SUM(chunk_count) as chunks
        FROM crawled_pages WHERE status='ok'
        GROUP BY site_name ORDER BY chunks DESC
    """).fetchall()

    print(f"\n{'='*55}")
    print(f"  {'Site':<35} {'Pages':>6} {'Chunks':>8}")
    print(f"  {'-'*35} {'------':>6} {'--------':>8}")
    for r in rows:
        print(f"  {r['site_name']:<35} {r['pages']:>6} {r['chunks']:>8}")

    try:
        col = _get_website_collection()
        total = col.count()
        print(f"\n  ChromaDB website_index total: {total:,} chunks")
    except Exception as e:
        print(f"\n  ChromaDB: {e}")
    db.close()


# ══════════════════════════════════════════════════════════════════════════════
#  APScheduler — weekly auto-update
# ══════════════════════════════════════════════════════════════════════════════

def start_scheduler():
    """
    Start background scheduler — runs update crawl every Sunday at 2am.
    Call this from api_server.py startup:
        from website_crawler import start_scheduler
        start_scheduler()
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            lambda: crawl_all(update_only=True),
            trigger="cron",
            day_of_week="sun",
            hour=2,
            minute=0,
            id="weekly_website_crawl",
            replace_existing=True,
        )
        scheduler.start()
        print("[CRAWLER] Weekly update scheduler started (Sundays at 2am)")
        return scheduler
    except ImportError:
        print("[CRAWLER] APScheduler not installed — auto-update disabled.")
        print("          pip install apscheduler --break-system-packages")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AgriBot Website Crawler")
    parser.add_argument("--crawl",  action="store_true", help="Full crawl all sites")
    parser.add_argument("--update", action="store_true", help="Update changed pages only")
    parser.add_argument("--stats",  action="store_true", help="Show index statistics")
    args = parser.parse_args()

    if args.crawl:
        crawl_all(update_only=False)
    elif args.update:
        crawl_all(update_only=True)
    elif args.stats:
        print_stats()
    else:
        parser.print_help()
        print("\nQuick start:")
        print("  python website_crawler.py --crawl    # first time")
        print("  python website_crawler.py --update   # weekly refresh")
        print("  python website_crawler.py --stats    # see what's indexed")

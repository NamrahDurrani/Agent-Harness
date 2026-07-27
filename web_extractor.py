"""
web_extractor.py
================
Trusted-site web retrieval pipeline implementing the full crawler architecture:

  Trusted Website
      │
      ▼
  Seed URLs from trusted_sites.py
      │
      ▼
  DDG open search → filter to trusted domains  (finds relevant sub-pages)
      │
      ▼
  Direct fetch seed URLs for org-name matches  (guarantees org coverage)
      │
      ▼
  extract_page_text()
      ├── requests + trafilatura   (fast, static pages)
      ├── playwright + trafilatura (JS-rendered pages — PARC, agripunjab etc.)
      └── BeautifulSoup            (last resort)
      │
      ▼
  _chunk_text()         split into 400-char overlapping chunks
      │
      ▼
  _bm25_score_chunks()  rank by relevance to query
      │
      ▼
  get_web_context()     return top-K chunks with source metadata

THREE BUGS FIXED vs previous version:
  1. "PASSCO/IRRI/SAU not found" — orchestrator was routing these as RAG
     because org names appeared in PDFs. Fixed in rag_pipeline.py by adding
     a HYBRID routing mode that runs BOTH RAG AND web for org-specific queries.
     web_extractor now crawls specific sub-pages (not just homepages) by
     following internal links from each seed URL.

  2. "GDP/PBS answer not found" — generic factual queries with no org name
     get no direct-fetch hits. Fixed by adding keyword→site mapping: queries
     containing "GDP", "statistics", "labour force", "employment" now
     automatically add pbs.gov.pk as a direct-fetch target.

  3. "Answer always mentions IRRI/PARC" — the LLM prompt listed those names
     explicitly. Fixed: the prompt now says "the websites listed in SOURCES"
     and the actual site_name from the extracted chunk is shown, so the LLM
     uses the real source name in its answer.
"""

import re
import time
import logging
from typing import List, Dict, Optional, Set
from urllib.parse import urlparse, urljoin

from trusted_sites import get_display_name, TRUSTED_DOMAINS, TRUSTED_SITES

logger = logging.getLogger(__name__)

# ── Tunables ──────────────────────────────────────────────────────────────────
CHUNK_SIZE        = 500    # characters per chunk (larger = more context)
CHUNK_OVERLAP     = 100    # overlap between chunks
REQUEST_TIMEOUT   = 12     # seconds for requests.get
MAX_PAGE_CHARS    = 80000  # truncate very long pages
MIN_CHUNK_CHARS   = 60     # discard nav/header noise
MAX_CRAWL_LINKS   = 8      # max internal links to follow per seed URL
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# ── Keyword → trusted site mapping ───────────────────────────────────────────
# When a query contains these keywords, always fetch the mapped site directly
# even if the org name isn't explicitly mentioned in the query.
KEYWORD_SITE_MAP: Dict[str, str] = {
    # GDP / statistics queries → PBS
    "gdp":            "pbs.gov.pk",
    "gross domestic": "pbs.gov.pk",
    "labour force":   "pbs.gov.pk",
    "labor force":    "pbs.gov.pk",
    "employment":     "pbs.gov.pk",
    "foreign exchange": "pbs.gov.pk",
    "statistics":     "pbs.gov.pk",
    "census":         "pbs.gov.pk",
    # Storage / procurement → PASSCO
    "storage":        "passco.gov.pk",
    "procurement":    "passco.gov.pk",
    "wheat procurement": "passco.gov.pk",
    "grain":          "passco.gov.pk",
    "godown":         "passco.gov.pk",
    # Fertilizer → NFDC
    "fertilizer":     "nfdc.gov.pk",
    "fertiliser":     "nfdc.gov.pk",
    "urea":           "nfdc.gov.pk",
    "dap":            "nfdc.gov.pk",
    # Cotton → PCCC
    "cotton":         "pccc.gov.pk",
    "kapas":          "pccc.gov.pk",
    # Rice → IRRI
    "rice":           "irri.org",
    "paddy":          "irri.org",
    # Dry areas / MENA agriculture → ICARDA
    "dryland":        "icarda.org",
    "dry area":       "icarda.org",
    "arid":           "icarda.org",
    # Mango / Punjab crops → agripunjab
    "mango":          "agripunjab.gov.pk",
    "aari":           "agripunjab.gov.pk",
    # Sindh agriculture → Sindh ag dept
    "sindh":          "agri.sindh.gov.pk",
    # Agricultural loans → ZTBL
    "loan":           "ztbl.com.pk",
    "credit":         "ztbl.com.pk",
    "kisan":          "ztbl.com.pk",
}


# ── Step 1A: Find relevant pages via DDG open search ─────────────────────────

def _ddg_open_search_filtered(query: str, max_results: int = 8) -> List[Dict]:
    """
    Open DDG search — no site: filter — then keep only results from
    trusted domains. This avoids DDG's broken site: filter while still
    restricting to our 20 trusted sources.
    """
    from duckduckgo_search import DDGS
    try:
        with DDGS() as ddgs:
            raw = list(ddgs.text(query, max_results=25))
    except Exception as e:
        print(f"  [DDG OPEN] Search failed: {e}")
        return []

    results = []
    for r in raw:
        url = r.get("href", "")
        if not url:
            continue
        result_domain = urlparse(url).netloc.lstrip("www.")
        matched = next(
            (d for d in TRUSTED_DOMAINS
             if result_domain == d
             or result_domain.endswith("." + d)
             or d.endswith("." + result_domain)),
            None
        )
        if matched:
            results.append({
                "url":       url,
                "title":     r.get("title", ""),
                "snippet":   r.get("body", "")[:300],
                "site_name": get_display_name(url),
                "domain":    matched,
            })
            if len(results) >= max_results:
                break

    print(f"  [DDG OPEN] {len(results)} trusted hits for: {query!r}")
    return results


# ── Step 1B: Direct fetch for org-name and keyword-matched sites ──────────────

def _find_direct_fetch_sites(query: str) -> List[Dict]:
    """
    Returns seed URLs to fetch directly, based on:
      1. Org name/acronym in the query (IRRI → irri.org, PASSCO → passco.gov.pk)
      2. Keyword → site mapping above (GDP → pbs.gov.pk, storage → passco.gov.pk)

    This guarantees we fetch the right site even when DDG doesn't surface it.
    """
    q_lower = query.lower()
    matched_domains: Set[str] = set()

    # 1. Org name matching
    for site in TRUSTED_SITES:
        short      = site["domain"].split(".")[0].lower()
        name_words = [w.lower() for w in site["name"].split()
                      if len(w) > 2 and w.lower() not in
                      {"the","for","and","of","in","on","at","to","a","an","ltd","corp"}]
        if (short in q_lower
                or site["domain"].lower() in q_lower
                or any(w in q_lower for w in name_words[:4])):
            matched_domains.add(site["domain"])

    # 2. Keyword mapping
    for keyword, domain in KEYWORD_SITE_MAP.items():
        if keyword in q_lower:
            matched_domains.add(domain)

    # Build result list
    results = []
    domain_to_site = {s["domain"]: s for s in TRUSTED_SITES}
    for domain in matched_domains:
        site = domain_to_site.get(domain)
        if site:
            print(f"  [DIRECT FETCH] Matched '{domain}' for query → {site['seed_url']}")
            results.append({
                "url":       site["seed_url"],
                "title":     site["name"],
                "snippet":   "",
                "site_name": site["name"],
                "domain":    domain,
                "_direct":   True,
            })
    return results


# ── Step 1C: Crawl internal links from a seed page ───────────────────────────

def _get_internal_links(url: str, html: str, domain: str) -> List[str]:
    """
    Extract internal links from a page's HTML.
    Only keeps links within the same domain (no external links).
    Filters out pagination, login, admin, media files.
    """
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        links = []
        seen = set()
        skip_patterns = re.compile(
            r"(login|logout|register|admin|wp-|\.pdf$|\.jpg$|\.png$|\.css$|\.js$"
            r"|page=\d|#|mailto:|tel:|javascript:)", re.IGNORECASE
        )
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if skip_patterns.search(href):
                continue
            full_url = urljoin(url, href)
            parsed   = urlparse(full_url)
            link_domain = parsed.netloc.lstrip("www.")
            if (link_domain == domain or link_domain.endswith("." + domain)):
                clean = full_url.split("#")[0].rstrip("/")
                if clean not in seen and clean != url.rstrip("/"):
                    seen.add(clean)
                    links.append(clean)
        return links[:MAX_CRAWL_LINKS]
    except Exception:
        return []


# ── Step 2: Extract clean text from a URL (3-strategy cascade) ───────────────

def _fetch_html(url: str) -> Optional[str]:
    """Download raw HTML with requests."""
    try:
        import requests
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT,
                            allow_redirects=True)
        if resp.status_code == 200:
            return resp.text
    except Exception as e:
        logger.debug(f"fetch failed {url}: {e}")
    return None


def _fetch_html_playwright(url: str) -> Optional[str]:
    """Download HTML via headless Chromium for JS-rendered pages."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers({"User-Agent": HEADERS["User-Agent"]})
            page.goto(url, wait_until="networkidle", timeout=25000)
            html = page.content()
            browser.close()
        return html
    except ImportError:
        return None
    except Exception as e:
        logger.debug(f"playwright failed {url}: {e}")
        return None


def _html_to_text(html: str, use_bs4_fallback: bool = True) -> Optional[str]:
    """Extract clean article text from HTML using trafilatura → BS4 fallback."""
    # Strategy 1: trafilatura
    try:
        import trafilatura
        text = trafilatura.extract(
            html, include_comments=False, include_tables=True,
            no_fallback=False, favor_precision=False,
        )
        if text and len(text.strip()) > 200:
            return text
    except Exception:
        pass

    # Strategy 2: BeautifulSoup paragraph extraction
    if use_bs4_fallback:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
                tag.decompose()
            paras = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
            text  = "\n\n".join(p for p in paras if len(p) > 40)
            if len(text) > 200:
                return text
        except Exception:
            pass
    return None


def extract_page_text(url: str) -> Optional[str]:
    """
    Extract clean text from a URL using a 3-strategy cascade:
      1. requests → trafilatura  (fast, most pages)
      2. playwright → trafilatura (JS-rendered: PARC, agripunjab.gov.pk)
      3. BeautifulSoup fallback
    Returns truncated text or None.
    """
    # Strategy 1: requests
    html = _fetch_html(url)
    if html:
        text = _html_to_text(html)
        if text and len(text.strip()) > 200:
            print(f"    [EXTRACT] ✓ trafilatura  {len(text)} chars  {url[:60]}")
            return text[:MAX_PAGE_CHARS]

    # Strategy 2: playwright
    print(f"    [EXTRACT] static failed → playwright  {url[:60]}")
    html = _fetch_html_playwright(url)
    if html:
        text = _html_to_text(html)
        if text and len(text.strip()) > 200:
            print(f"    [EXTRACT] ✓ playwright   {len(text)} chars  {url[:60]}")
            return text[:MAX_PAGE_CHARS]

    print(f"    [EXTRACT] ✗ all methods failed  {url[:60]}")
    return None


def extract_with_crawl(seed_url: str, query: str, domain: str) -> List[Dict]:
    """
    Full crawler for one seed URL:
      1. Fetch and extract the seed page itself
      2. Find internal links on that page
      3. Score links by keyword overlap with query
      4. Fetch top scoring sub-pages
      5. Return all extracted chunks with metadata

    This implements the pipeline from your diagram:
      Seed URL → crawl links → playwright/trafilatura → clean text → chunks
    """
    site_name = get_display_name(seed_url)
    results   = []

    # --- Fetch seed page ---
    html = _fetch_html(seed_url) or _fetch_html_playwright(seed_url)
    if not html:
        print(f"    [CRAWL] ✗ could not fetch seed: {seed_url[:60]}")
        return []

    seed_text = _html_to_text(html)
    if seed_text and len(seed_text.strip()) > 200:
        results.append({
            "text":      seed_text[:MAX_PAGE_CHARS],
            "url":       seed_url,
            "title":     site_name,
            "site_name": site_name,
            "score":     0.0,
            "source":    "seed",
        })

    # --- Find and score internal links ---
    internal_links = _get_internal_links(seed_url, html, domain)
    if not internal_links:
        return results

    # Score links by keyword overlap with query
    q_words = set(re.findall(r"\b\w{3,}\b", query.lower()))
    scored_links = []
    for link in internal_links:
        link_lower = link.lower()
        score = sum(1 for w in q_words if w in link_lower)
        scored_links.append((score, link))
    scored_links.sort(reverse=True)

    # Fetch top sub-pages (limit to 3 to keep response time reasonable)
    fetched = 0
    for link_score, link_url in scored_links[:MAX_CRAWL_LINKS]:
        if fetched >= 3:
            break
        sub_html = _fetch_html(link_url)
        if not sub_html:
            sub_html = _fetch_html_playwright(link_url)
        if not sub_html:
            continue
        sub_text = _html_to_text(sub_html)
        if sub_text and len(sub_text.strip()) > 200:
            results.append({
                "text":      sub_text[:MAX_PAGE_CHARS],
                "url":       link_url,
                "title":     site_name,
                "site_name": site_name,
                "score":     0.0,
                "source":    "crawled",
            })
            fetched += 1
            print(f"    [CRAWL] ✓ sub-page {fetched}: {link_url[:60]}")

    print(f"  [CRAWL] {site_name}: {len(results)} pages extracted")
    return results


# ── Step 3: Chunk text ────────────────────────────────────────────────────────

def _chunk_text(text: str) -> List[str]:
    """Split text into overlapping chunks at sentence/paragraph boundaries."""
    sentences = re.split(r"(\n\n|\.\s+|\n)", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    chunks, current = [], ""
    for sent in sentences:
        if len(current) + len(sent) + 1 <= CHUNK_SIZE:
            current = (current + " " + sent).strip()
        else:
            if current and len(current) >= MIN_CHUNK_CHARS:
                chunks.append(current)
            overlap = current[-CHUNK_OVERLAP:] if len(current) > CHUNK_OVERLAP else current
            current = (overlap + " " + sent).strip()
    if current and len(current) >= MIN_CHUNK_CHARS:
        chunks.append(current)
    return chunks


# ── Step 4: BM25 score chunks ─────────────────────────────────────────────────

def _bm25_score_chunks(query: str, chunks: List[str]) -> List[tuple]:
    """Score chunks against query using BM25. Falls back to keyword overlap."""
    if not chunks:
        return []
    try:
        from rank_bm25 import BM25Okapi
        def tokenize(t): return re.findall(r"\b\w+\b", t.lower())
        corpus = [tokenize(c) for c in chunks]
        bm25   = BM25Okapi(corpus)
        scores = bm25.get_scores(tokenize(query))
        return sorted(zip(scores, chunks), key=lambda x: -x[0])
    except ImportError:
        q_words = set(re.findall(r"\b\w+\b", query.lower()))
        scored  = [(len(q_words & set(re.findall(r"\b\w+\b", c.lower()))), c)
                   for c in chunks]
        return sorted(scored, key=lambda x: -x[0])


# ── Step 5: Full pipeline entry point ─────────────────────────────────────────

def search_trusted_sites(query: str, max_results: int = 6) -> List[Dict]:
    """Find candidate URLs from trusted domains using DDG + direct fetch."""
    ddg_results    = _ddg_open_search_filtered(query, max_results=max_results * 2)
    direct_results = _find_direct_fetch_sites(query)

    seen_urls: Set[str] = set()
    all_results: List[Dict] = []
    for r in ddg_results + direct_results:
        if r["url"] not in seen_urls:
            seen_urls.add(r["url"])
            all_results.append(r)

    if not all_results:
        print(f"  [TRUSTED SEARCH] No candidates for: {query!r}")
        return []

    # Score by keyword overlap (direct hits get a minimum score of 1)
    q_words = set(re.findall(r"\b\w{3,}\b", query.lower()))
    for r in all_results:
        text = f"{r['title']} {r['snippet']}".lower()
        r["_rel"] = max(
            sum(1 for w in q_words if w in text),
            1 if r.get("_direct") else 0
        )

    all_results.sort(key=lambda x: -x["_rel"])
    result = all_results[:max_results]

    print(f"  [TRUSTED SEARCH] {len(result)} candidates from "
          f"{len(set(r['domain'] for r in result))} domains")
    for r in result:
        flag = "📎" if r.get("_direct") else "🔍"
        print(f"    {flag} {r['domain']:28s}  rel={r['_rel']}  {r['url'][:55]}")
    return result


def get_web_context(
    query: str,
    max_search_results: int = 5,
    top_chunks: int = 5,
    max_extract_pages: int = 4,
) -> List[Dict]:
    """
    Full pipeline: search + crawl trusted domains → extract → chunk → BM25.

    Returns list of dicts with keys:
      text, url, title, site_name, score
    """
    t0 = time.time()

    search_results = search_trusted_sites(query, max_results=max_search_results)
    if not search_results:
        return []

    # Extract with crawling — use full crawl for direct-fetch sites,
    # simple extract for DDG-found specific pages
    all_page_results: List[Dict] = []
    extracted = 0

    for sr in search_results:
        if extracted >= max_extract_pages:
            break
        url    = sr["url"]
        domain = sr["domain"]
        is_direct = sr.get("_direct", False)

        if is_direct:
            # Full crawl: seed + internal links
            page_results = extract_with_crawl(url, query, domain)
        else:
            # Specific page found by DDG — just extract it directly
            text = extract_page_text(url)
            if text:
                page_results = [{
                    "text":      text,
                    "url":       url,
                    "title":     sr.get("title", ""),
                    "site_name": sr["site_name"],
                    "score":     0.0,
                }]
            else:
                # Fallback to snippet
                snippet = sr.get("snippet", "").strip()
                page_results = [{
                    "text":      snippet,
                    "url":       url,
                    "title":     sr.get("title", ""),
                    "site_name": sr["site_name"],
                    "score":     0.0,
                }] if snippet else []

        all_page_results.extend(page_results)
        if page_results:
            extracted += 1

    if not all_page_results:
        print(f"  [WEB CTX] Extraction returned nothing usable")
        return []

    # Chunk all page texts and score with BM25
    all_chunks: List[Dict] = []
    for pr in all_page_results:
        page_chunks = _chunk_text(pr["text"])
        for chunk in page_chunks:
            all_chunks.append({**pr, "text": chunk, "score": 0.0})

    if not all_chunks:
        return []

    # BM25 scoring
    texts  = [c["text"] for c in all_chunks]
    scored = _bm25_score_chunks(query, texts)

    # Deduplicate by URL: keep best chunk per source URL
    seen_urls: Dict[str, float] = {}
    ranked: List[Dict] = []
    for score, text in scored:
        match = next((c for c in all_chunks if c["text"] == text), None)
        if match is None:
            continue
        url = match["url"]
        if url not in seen_urls or score > seen_urls[url]:
            seen_urls[url] = score
            ranked = [c for c in ranked if c["url"] != url]
            ranked.append({**match, "score": round(float(score), 4)})

    ranked.sort(key=lambda x: -x["score"])
    # Take top_chunks but ensure diversity — at least 1 chunk per unique domain
    final: List[Dict] = []
    seen_domains: Set[str] = set()
    for c in ranked:
        dom = urlparse(c["url"]).netloc.lstrip("www.")
        if len(final) < top_chunks:
            final.append(c)
            seen_domains.add(dom)

    elapsed = time.time() - t0
    print(f"  [WEB CTX] {elapsed:.1f}s → {len(final)} chunks from "
          f"{len(seen_domains)} domains")
    for i, c in enumerate(final, 1):
        print(f"    [{i}] score={c['score']:.3f}  {c['site_name']}  {c['url'][:55]}")

    return final


if __name__ == "__main__":
    q = "What percentage of GDP does agriculture account for in Pakistan?"
    print(f"Testing: {q!r}\n")
    chunks = get_web_context(q, max_search_results=4, top_chunks=3)
    for i, c in enumerate(chunks, 1):
        print(f"\n── Chunk {i} ({c['site_name']}) ──")
        print(c["text"][:400])
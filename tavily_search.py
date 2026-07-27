"""
tavily_search.py
================
Drop-in web search module using the Tavily Search API.

Tavily is purpose-built for LLM agents — it returns clean, pre-extracted
text snippets (no HTML scraping needed), ranks by relevance, and supports
domain filtering.  It replaces the old DuckDuckGo + web_extractor approach
which was failing because:
  1. DuckDuckGo rate-limits aggressively in CI/server environments.
  2. The trusted-sites scraper fetches full HTML pages and often gets
     blocked or returns irrelevant boilerplate.

Setup
-----
1. pip install tavily-python
2. Set env var:  TAVILY_API_KEY=tvly-xxxxxxxxxxxx
   Get a free key (1,000 searches/month) at https://tavily.com

Usage
-----
    from tavily_search import tavily_web_search

    results = tavily_web_search("Ug99 wheat rust Punjab 2024", max_results=5)
    for r in results:
        print(r["title"], r["url"])
        print(r["content"])   # clean extracted text, ~200-500 chars each
"""

import os
from typing import List, Dict, Optional

# ── Lazy import so the rest of the codebase still loads if tavily
#    is not installed (falls back gracefully).
try:
    from tavily import TavilyClient as _TavilyClient
    _TAVILY_AVAILABLE = True
except ImportError:
    _TAVILY_AVAILABLE = False


def tavily_web_search(
    query: str,
    max_results: int = 5,
    search_depth: str = "basic",          # "basic" (fast) | "advanced" (deeper)
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    topic: str = "general",               # "general" | "news"
) -> List[Dict]:
    """
    Search the web using Tavily and return clean text results.

    Returns a list of dicts:
        [
          {
            "title":   str,
            "url":     str,
            "content": str,   # clean extracted text snippet
            "score":   float, # Tavily relevance score 0-1
          },
          ...
        ]

    On any error (missing key, network timeout, etc.) returns [].
    """
    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        print("  [TAVILY] TAVILY_API_KEY not set — skipping web search.")
        return []

    if not _TAVILY_AVAILABLE:
        print("  [TAVILY] tavily-python not installed. Run: pip install tavily-python")
        return []

    try:
        client = _TavilyClient(api_key=api_key)
        kwargs = dict(
            query=query,
            max_results=max_results,
            search_depth=search_depth,
            topic=topic,
            include_raw_content=False,  # snippets only — faster + cheaper
        )
        if include_domains:
            kwargs["include_domains"] = include_domains
        if exclude_domains:
            kwargs["exclude_domains"] = exclude_domains

        response = client.search(**kwargs)
        results = response.get("results", [])

        cleaned = []
        for r in results:
            cleaned.append({
                "title":   r.get("title", ""),
                "url":     r.get("url", ""),
                "content": r.get("content", ""),
                "score":   r.get("score", 0.0),
                "site_name": _domain_label(r.get("url", "")),
            })
        print(f"  [TAVILY] Got {len(cleaned)} results for: {query!r}")
        return cleaned

    except Exception as e:
        print(f"  [TAVILY] Search failed: {e}")
        return []


def format_for_llm(results: List[Dict], max_chars_per_result: int = 500) -> str:
    """
    Format Tavily results into a numbered context block for the LLM prompt.
    Each entry looks like:
        [Web 1] PARC Pakistan — https://parc.gov.pk
        <content snippet>
    """
    if not results:
        return ""
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(
            f"[Web {i}] {r['site_name']} — {r['url']}\n"
            f"{r['content'][:max_chars_per_result]}"
        )
    return "\n\n".join(lines)


def _domain_label(url: str) -> str:
    """Extract a human-readable site label from a URL."""
    try:
        from urllib.parse import urlparse
        host = urlparse(url).netloc.lower()
        # Strip www. prefix
        host = host.removeprefix("www.")
        return host
    except Exception:
        return url

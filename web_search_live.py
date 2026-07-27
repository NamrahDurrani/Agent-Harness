"""
web_search_live.py
===================
Real, open-internet web search — NOT limited to the 20 trusted_sites.py
domains. This is opt-in per query (the user clicks a "Search the web"
button/toggle in the UI), mirroring how ChatGPT/Perplexity gate live
search behind explicit intent rather than firing it on every message.

Why a separate module from web_crawler.py / web_method_replacement.py:
  - web_crawler.py pre-indexes 20 trusted domains into ChromaDB — good
    for "answer only from vetted ag sources", but that's a DIFFERENT
    feature from "search the whole internet right now". Keep both:
      * default chat -> local PDFs -> trusted-site fallback (existing)
      * "Search web" button -> this module (new, open internet)
  - No pre-indexing needed here: results are fetched live per-query.

Search backend: DuckDuckGo via the `ddgs` package — free, no API key,
good enough for a same-day build. If you have more time later, swap
`_search()` for Tavily (https://tavily.com, built specifically for
LLM RAG — cleaner snippets, still has a free tier) or Bing/Google
Custom Search for higher result quality. The rest of this file
(synthesis + citation injection) doesn't need to change either way —
only `_search()` does.

pip install ddgs --break-system-packages
"""

import re
import time
from collections import Counter
from typing import List, Dict, Tuple

try:
    from ddgs import DDGS
except ImportError:
    DDGS = None


def _search(query: str, max_results: int = 6) -> List[Dict]:
    """
    Live web search across the open internet.
    Returns list of {title, url, snippet}.
    """
    if DDGS is None:
        raise RuntimeError(
            "ddgs not installed. Run: pip install ddgs --break-system-packages"
        )
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append({
                "title":   r.get("title", ""),
                "url":     r.get("href", ""),
                "snippet": r.get("body", ""),
            })
    return results


def _inject_web_citations(llm_answer: str, sources: List[Dict]) -> Tuple[str, List[int]]:
    """
    Same keyword-fingerprint approach as web_citation_injector.py —
    reused here so both search modes (trusted-site + live) produce
    citations in the identical [Web N] format the frontend already
    knows how to render.
    """
    answer = re.sub(r'\n*SOURCES:[\s\S]*$', '', llm_answer, flags=re.IGNORECASE).strip()

    stopwords = {"that", "this", "with", "from", "have", "been", "they",
                 "also", "such", "which", "when", "were", "will", "more"}
    fingerprints = []
    for src in sources:
        text = f"{src['title']} {src['snippet']}"
        words = [w.lower() for w in re.findall(r'\b[a-zA-Z]{4,}\b', text)
                 if w.lower() not in stopwords]
        top_words = [w for w, _ in Counter(words).most_common(12)]
        fingerprints.append({"num": src["num"], "keywords": top_words})

    sentences = re.split(r'(?<=[.!?])\s+', answer)
    annotated, used = [], set()
    for sent in sentences:
        sent_lower = sent.lower()
        hits = []
        for fp in fingerprints:
            matches = sum(1 for kw in fp["keywords"] if kw in sent_lower)
            if matches >= 2:
                hits.append((matches, fp["num"]))
        if hits:
            hits.sort(reverse=True)
            tags = "".join(f"[Web {n}]" for _, n in hits[:2])
            used.update(n for _, n in hits[:2])
            annotated.append(sent + tags)
        else:
            annotated.append(sent)

    cited = " ".join(annotated)
    if not used and sources:
        used.add(sources[0]["num"])
        cited = cited.rstrip() + f" [Web {sources[0]['num']}]"

    return cited.strip(), sorted(used)


def answer_with_live_web_search(
    query: str,
    llm_client,
    conversation_history: str = "",
    max_results: int = 6,
) -> Dict:
    """
    Full flow: search the open internet -> synthesize an answer with the
    LLM -> inject [Web N] citations -> return structured result.

    Args:
        query:                 the user's question
        llm_client:             any object with .call(system, user, max_tokens,
                                temperature) -> (text, usage_dict) — reuse the
                                same LLMClient/QwenRemoteClient instance your
                                pipeline already uses (see get_llm_client() in
                                rag_pipeline.py), so backend choice stays
                                consistent across the app.
        conversation_history:  optional prior turns for follow-up questions
        max_results:           how many search results to fetch

    Returns dict:
        {
          "answer": str,          # markdown-ish answer with [Web N] tags inline
          "sources": [ {num, title, url}, ... ],   # only sources actually cited
          "raw_results_count": int,
          "duration_ms": float,
        }
    """
    t0 = time.time()

    raw_results = _search(query, max_results=max_results)
    if not raw_results:
        return {
            "answer": "I searched the web but couldn't find relevant results for this query. Try rephrasing it.",
            "sources": [],
            "raw_results_count": 0,
            "duration_ms": (time.time() - t0) * 1000,
        }

    sources = [
        {"num": i + 1, "title": r["title"], "url": r["url"], "snippet": r["snippet"]}
        for i, r in enumerate(raw_results)
    ]

    context_block = "\n\n".join(
        f"[Web {s['num']}] {s['title']}\n{s['snippet']}" for s in sources
    )
    sources_list = "\n".join(f"[Web {s['num']}] {s['title']} — {s['url']}" for s in sources)

    system = (
        "You are a helpful research assistant with access to live web search "
        "results. Answer the user's question using ONLY the search results "
        "provided below — do not use prior knowledge for facts that could be "
        "time-sensitive (prices, current events, statistics, current officeholders).\n\n"
        "STRICT FORMAT:\n"
        "DIRECT ANSWER: <one clear sentence>\n\n"
        "EXPLANATION:\n"
        "<2-5 sentences, citing sources inline as [Web 1], [Web 2] etc. "
        "immediately after the sentence that uses them. Never write a raw URL "
        "in the explanation — only [Web N] tags.>\n\n"
        "If the search results don't actually answer the question, say so "
        "plainly instead of guessing."
    )
    user = (
        f"Search results:\n{context_block}\n\n"
        f"Available sources:\n{sources_list}\n\n"
        f"Conversation history:\n{conversation_history}\n\n"
        f"Question: {query}\n\nAnswer:"
    )

    raw_answer, usage = llm_client.call(system, user, max_tokens=500, temperature=0.2)
    cited_answer, used_nums = _inject_web_citations(raw_answer, sources)

    used_sources = [s for s in sources if s["num"] in used_nums]
    sources_block = "\n".join(f"[Web {s['num']}] {s['title']} — {s['url']}" for s in used_sources)
    final_answer = cited_answer + "\n\nSOURCES:\n" + sources_block

    return {
        "answer": final_answer,
        "sources": [{"num": s["num"], "title": s["title"], "url": s["url"]} for s in used_sources],
        "raw_results_count": len(raw_results),
        "duration_ms": (time.time() - t0) * 1000,
        "usage": usage,
    }

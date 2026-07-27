# ── Web citation injector (add this near _inject_citations in rag_pipeline.py) ─

def _inject_web_citations(llm_answer: str, web_sources: list) -> str:
    """
    Post-process the LLM web answer to guarantee [Web N] citations are
    injected inline and a clean SOURCES block appears at the end.
    Mirrors _inject_citations() which does the same for PDF results.
    """
    import re
    from collections import Counter

    # Strip anything the LLM wrote as SOURCES (rebuild it cleanly below)
    answer = re.sub(r'\n*SOURCES:[\s\S]*$', '', llm_answer, flags=re.IGNORECASE).strip()

    # Build keyword fingerprints for each web source
    # (same approach as _inject_citations for PDFs)
    source_keywords = []
    for src in web_sources:
        text = src.get("chunk_text", "") or src.get("site_name", "")
        stopwords = {"that", "this", "with", "from", "have", "been", "they",
                     "also", "such", "which", "when", "were", "will", "more"}
        words = [w.lower() for w in re.findall(r'\b[a-zA-Z]{4,}\b', text)
                 if w.lower() not in stopwords]
        top_words = [w for w, _ in Counter(words).most_common(12)]
        source_keywords.append({
            "num":       src["num"],
            "site_name": src.get("site_name", ""),
            "url":       src.get("url", ""),
            "keywords":  top_words,
        })

    # Annotate sentences with [Web N] where keywords match
    sentences    = re.split(r'(?<=[.!?])\s+', answer)
    annotated    = []
    used_sources = set()

    for sent in sentences:
        sent_lower = sent.lower()
        hits = []
        for src in source_keywords:
            matches = sum(1 for kw in src["keywords"] if kw in sent_lower)
            if matches >= 2:
                hits.append((matches, src["num"]))
        if hits:
            hits.sort(reverse=True)
            tags = "".join(f"[Web {num}]" for _, num in hits[:2])
            used_sources.update(num for _, num in hits[:2])
            annotated.append(sent + tags)
        else:
            annotated.append(sent)

    cited_text = " ".join(annotated)

    # Guarantee at least one citation
    if not used_sources and web_sources:
        used_sources.add(web_sources[0]["num"])
        cited_text = cited_text.rstrip() + f"[Web {web_sources[0]['num']}]"

    # Build clean SOURCES block
    sources_lines = []
    for src in source_keywords:
        if src["num"] in used_sources:
            sources_lines.append(
                f"[Web {src['num']}] {src['site_name']} — {src['url']}"
            )

    sources_block = "SOURCES:\n" + "\n".join(sources_lines)
    return cited_text.strip() + "\n\n" + sources_block

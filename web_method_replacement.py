    def _generate_from_web(
        self,
        query_id: str,
        original_query: str,
        rewritten_query: str,
        conversation_history: str,
        step_order: int,
    ) -> str:
        """
        Web knowledge fallback — searches the pre-indexed trusted website
        ChromaDB collection instead of live DuckDuckGo fetching.

        Why pre-indexed:
          - Pakistani govt sites (PASSCO, agripunjab, PARC) are JS-rendered.
            Live Playwright adds 15-30s latency per query.
          - Pre-indexed collection gives sub-second retrieval.
          - Run `python web_crawler.py --crawl` once to populate it.
        """
        t0 = time.time()

        # ── 1. Search pre-indexed trusted web collection ───────────────────────
        web_context = ""
        web_sources = []

        try:
            from web_crawler import search_web_collection, web_collection_size

            col_size = web_collection_size()
            print(f"  [WEB SEARCH] Searching {col_size} pre-indexed web chunks...")

            if col_size == 0:
                print("  [WEB SEARCH] ⚠ Web collection empty. Run: python web_crawler.py --crawl")
                raise ValueError("Web collection not indexed yet")

            results = search_web_collection(rewritten_query, top_k=7)

            if not results:
                raise ValueError("No relevant web chunks found")

            # Deduplicate by URL — show max 3 chunks per source URL
            seen_urls: dict = {}
            for r in results:
                url = r["source_url"]
                if url not in seen_urls:
                    seen_urls[url] = []
                seen_urls[url].append(r["chunk_text"])

            # Build numbered context + sources list
            num = 1
            for url, chunks in list(seen_urls.items())[:5]:
                site_name = r["site_name"] if "site_name" in r else url
                combined  = " ".join(chunks[:2])[:600]  # max 600 chars per source
                web_context += f"[Web {num}] {site_name}\n{combined}\n\n"
                web_sources.append({
                    "num":       num,
                    "site_name": site_name,
                    "url":       url,
                })
                num += 1

            print(f"  [WEB SEARCH] Found {len(web_sources)} relevant sources "
                  f"from trusted sites")

        except Exception as e:
            print(f"  [WEB SEARCH] Failed: {e}")
            # Hard fallback: tell user collection needs crawling
            answer = (
                "🌐 **This topic was not found in the trusted agricultural knowledge sources.**\n\n"
                "**EXPLANATION:**\n"
                "The query was searched across trusted agricultural websites "
                "(PARC, FAO, IRRI, CGIAR, ICARDA, agripunjab.gov.pk, and others) "
                "but no relevant content was found. This topic may be outside the "
                "scope of agricultural research, or the trusted sites may not have "
                "indexed content on this specific subject.\n\n"
                "**To fix this:** Run `python web_crawler.py --crawl` to index "
                "the trusted websites, then try again."
            )
            _log_step(
                query_id, "web_search_fallback", step_order,
                input_text=rewritten_query, output_text=answer,
                duration_ms=(time.time() - t0) * 1000, status="error",
            )
            return answer

        # ── 2. Build numbered context for LLM ─────────────────────────────────
        sources_for_prompt = "\n".join(
            f"[Web {s['num']}] {s['site_name']} — {s['url']}"
            for s in web_sources
        )

        system = (
            "You are a helpful agricultural research assistant. "
            "The answer was NOT found in the local PDF knowledge base. "
            "You are given content from trusted agricultural websites below. "
            "Answer ONLY from the provided web content.\n\n"
            "STRICT FORMAT — follow exactly:\n\n"
            "DIRECT ANSWER: <one clear sentence>\n\n"
            "EXPLANATION:\n"
            "<detailed explanation — cite sources as [Web 1], [Web 2] etc. "
            "immediately after each sentence that uses that source. "
            "NEVER write a URL or site name inside the explanation. "
            "ONLY use [Web N] numbers.>\n\n"
            "SOURCES:\n"
            "[Web 1] <site name> — <url>\n"
            "[Web 2] <site name> — <url>\n"
            "(only list sources you actually cited)\n\n"
            "EXAMPLE:\n"
            "DIRECT ANSWER: PASSCO is Pakistan's national grain storage agency.\n\n"
            "EXPLANATION:\n"
            "PASSCO manages strategic grain reserves across Pakistan [Web 1]. "
            "It operates modern silos in all four provinces [Web 1].\n\n"
            "SOURCES:\n"
            "[Web 1] Pakistan Agriculture Storage & Services Corporation (PASSCO) "
            "— https://www.passco.gov.pk"
        )
        user = (
            f"Trusted web content:\n{web_context}\n"
            f"Available sources:\n{sources_for_prompt}\n\n"
            f"Conversation history:\n{conversation_history}\n\n"
            f"Question: {rewritten_query}\n\n"
            "Answer (DIRECT ANSWER → EXPLANATION with [Web N] → SOURCES):"
        )

        try:
            raw_answer, usage = self.llm.call(
                system, user, max_tokens=600, temperature=0.2
            )
            # Post-process: inject [Web N] citations just like PDF citations
            answer = _inject_web_citations(raw_answer, web_sources)
        except Exception as e:
            answer = f"Web search found relevant content but generation failed: {e}"
            usage  = {}

        duration = (time.time() - t0) * 1000

        step_id = _log_step(
            query_id, "web_search_fallback", step_order,
            input_text=rewritten_query,
            output_text=answer,
            duration_ms=duration,
        )
        if usage:
            _log_llm_call(
                step_id, ACTIVE_MODEL_NAME, system, user, answer, usage
            )

        return answer

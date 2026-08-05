"""
mcp_pdf_export.py
=================
MCP Tool: Generate a professional PDF report from a chat session.

Pipeline:
  Frontend button click
      → GET /api/sessions/{id}/export/pdf
      → FastAPI calls mcp_generate_pdf(session_id, db_conn)
      → Read: chat messages, pipeline steps, retrieved sources, metadata
      → Build styled HTML report
      → Convert HTML → PDF  (weasyprint, pure Python — no Chrome/Puppeteer)
      → Return PDF bytes → browser triggers download

Install dependencies:
    pip install weasyprint  (converts HTML to PDF)
    # On Windows also: pip install weasyprint pillow
    # On Ubuntu/Debian: sudo apt-get install libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0

If weasyprint is not installed the function falls back to returning
the HTML report directly (with a note at the top), so the workflow
still works even without the optional dependency.

Usage from api_server.py:
    from mcp_pdf_export import mcp_generate_pdf

    @app.get("/api/sessions/{session_id}/export/pdf")
    def export_pdf(session_id: str):
        conn = db_schema.get_connection()
        try:
            result = mcp_generate_pdf(session_id, conn)
        finally:
            conn.close()
        if result["type"] == "pdf":
            return Response(
                content=result["bytes"],
                media_type="application/pdf",
                headers={"Content-Disposition":
                         f'attachment; filename="{result["filename"]}"'},
            )
        else:   # HTML fallback
            return Response(
                content=result["html"],
                media_type="text/html",
                headers={"Content-Disposition":
                         f'attachment; filename="{result["filename"]}"'},
            )
"""

import re
import time
import html as _html
from typing import Optional
# from mcp_pdf_export import mcp_generate_pdf


# ── Try weasyprint (optional — graceful fallback to HTML) ─────────────────────
try:
    from weasyprint import HTML as _WeasyprintHTML
    _WEASYPRINT = True
except ImportError:
    _WEASYPRINT = False


# ═══════════════════════════════════════════════════════════════════════════════
#  HTML template & CSS
# ═══════════════════════════════════════════════════════════════════════════════

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
  --green:      #4a7a2e;
  --green-light:#e8f4e0;
  --green-dim:  #6a9a4e;
  --amber:      #b07010;
  --amber-light:#fdf3dc;
  --text:       #1a2010;
  --text-sub:   #4a6035;
  --border:     #c8dab8;
  --surface:    #f6faf2;
  --white:      #ffffff;
  --danger:     #c0392b;
  --danger-bg:  #fdf0ef;
  --shadow:     0 2px 8px rgba(60,80,40,0.10);
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
  font-size: 11pt;
  color: var(--text);
  background: var(--white);
  line-height: 1.55;
}

/* ── PAGE LAYOUT ── */
@page {
  size: A4;
  margin: 18mm 16mm 20mm 16mm;
  @top-center { content: element(running-header); }
  @bottom-center {
    content: "Page " counter(page) " of " counter(pages);
    font-size: 8pt;
    color: #888;
  }
}

/* ── RUNNING HEADER ── */
#running-header {
  position: running(running-header);
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border);
  padding-bottom: 4px;
  font-size: 8pt;
  color: var(--text-sub);
}

/* ── COVER PAGE ── */
.cover {
  page: cover;
  min-height: 240mm;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-start;
  padding: 30mm 0 20mm 0;
  page-break-after: always;
}

.cover-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--green);
  color: white;
  font-size: 9pt;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 5px 14px;
  border-radius: 20px;
  margin-bottom: 22px;
}

.cover-title {
  font-size: 26pt;
  font-weight: 700;
  color: var(--text);
  line-height: 1.2;
  margin-bottom: 8px;
  border-left: 5px solid var(--green);
  padding-left: 16px;
}

.cover-subtitle {
  font-size: 12pt;
  color: var(--text-sub);
  font-weight: 400;
  padding-left: 21px;
  margin-bottom: 36px;
}

.cover-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-left: 21px;
}

.cover-meta-row {
  font-size: 9.5pt;
  color: var(--text-sub);
}

.cover-meta-row strong {
  color: var(--text);
  font-weight: 600;
  display: inline-block;
  min-width: 90px;
}

.cover-divider {
  width: 100%;
  height: 2px;
  background: linear-gradient(to right, var(--green), transparent);
  margin: 28px 0;
}

/* ── SECTION HEADERS ── */
.section-header {
  font-size: 13pt;
  font-weight: 700;
  color: var(--green);
  border-bottom: 2px solid var(--green-light);
  padding-bottom: 5px;
  margin: 22px 0 14px 0;
  page-break-after: avoid;
}

.section-header.amber { color: var(--amber); border-color: var(--amber-light); }

/* ── STATS ROW ── */
.stats-row {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.stat-card {
  flex: 1;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px 14px;
  text-align: center;
}

.stat-value {
  font-size: 20pt;
  font-weight: 700;
  color: var(--green);
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 8.5pt;
  color: var(--text-sub);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* ── CHAT BUBBLES ── */
.exchange {
  margin-bottom: 18px;
  page-break-inside: avoid;
}

.msg-user {
  background: #e6f2da;
  border: 1px solid #b8d9a0;
  border-radius: 10px 10px 4px 10px;
  padding: 10px 14px;
  margin-left: 40px;
  margin-bottom: 6px;
  font-size: 10.5pt;
}

.msg-label {
  font-size: 8pt;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 4px;
}

.msg-label.user   { color: var(--green); }
.msg-label.bot    { color: var(--text-sub); }

.msg-bot {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 4px 10px 10px 10px;
  padding: 10px 14px;
  margin-right: 20px;
  margin-bottom: 6px;
  font-size: 10.5pt;
}

.msg-ts {
  font-size: 7.5pt;
  color: #aaa;
  margin-top: 4px;
  text-align: right;
}

.source-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 7.5pt;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 12px;
  margin-left: 6px;
  vertical-align: middle;
}

.badge-rag  { background: #e6f2da; border: 1px solid #6a9a4e; color: #4a7a2e; }
.badge-web  { background: var(--amber-light); border: 1px solid #d09030; color: var(--amber); }
.badge-direct { background: #f0f0f0; border: 1px solid #ccc; color: #666; }

/* Citation tags */
.cite { color: var(--green); font-weight: 600; font-size: 8.5pt; vertical-align: super; }
.cite-web { color: var(--amber); font-weight: 600; font-size: 8.5pt; vertical-align: super; }

/* ── PIPELINE TRACE TABLE ── */
.trace-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 9.5pt;
  margin-bottom: 16px;
}

.trace-table th {
  background: var(--green-light);
  color: var(--green);
  font-weight: 600;
  font-size: 8pt;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 6px 10px;
  text-align: left;
  border: 1px solid var(--border);
}

.trace-table td {
  padding: 6px 10px;
  border: 1px solid var(--border);
  vertical-align: top;
}

.trace-table tr:nth-child(even) td { background: var(--surface); }

.step-ok    { color: var(--green); font-weight: 600; }
.step-err   { color: var(--danger); font-weight: 600; }

.duration-bar {
  display: inline-block;
  height: 8px;
  background: var(--green-light);
  border: 1px solid var(--green-dim);
  border-radius: 4px;
  margin-left: 6px;
  vertical-align: middle;
}

/* ── SOURCES TABLE ── */
.sources-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 9pt;
}

.sources-table th {
  background: var(--amber-light);
  color: var(--amber);
  font-weight: 600;
  font-size: 8pt;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 6px 10px;
  border: 1px solid #e0c070;
}

.sources-table td {
  padding: 6px 10px;
  border: 1px solid #e8d8a0;
  vertical-align: top;
}

.sources-table tr:nth-child(even) td { background: var(--amber-light); }

/* ── FOOTER NOTE ── */
.footer-note {
  border-top: 1px solid var(--border);
  padding-top: 12px;
  margin-top: 30px;
  font-size: 8pt;
  color: #aaa;
  text-align: center;
}

/* ── RECOMMENDATIONS HIGHLIGHT ── */
.recommendation {
  background: linear-gradient(90deg, rgba(250,249,240,1) 0%, rgba(241,250,233,1) 100%);
  border-left: 4px solid var(--amber);
  padding: 10px 12px;
  margin: 10px 0 18px 0;
  border-radius: 6px;
  font-size: 10pt;
}
.recommendation strong { color: var(--amber); }
"""


# ═══════════════════════════════════════════════════════════════════════════════
#  Data fetch helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _fetch_session_data(session_id: str, conn) -> dict:
    """Pull all data for the session from SQLite."""

    session_row = conn.execute(
        "SELECT session_id, created_at, title FROM sessions WHERE session_id=?",
        (session_id,)
    ).fetchone()

    if not session_row:
        return None

    # Chat messages with used_rag flag
    msg_rows = conn.execute("""
        SELECT q.query_id, q.original_query, q.timestamp AS query_ts,
               r.final_response, r.timestamp AS response_ts, r.used_rag,
               r.retry_count
        FROM queries q
        LEFT JOIN responses r ON r.query_id = q.query_id
        WHERE q.session_id = ?
        ORDER BY q.timestamp ASC
    """, (session_id,)).fetchall()

    # Pipeline steps for all queries in this session
    query_ids = [r["query_id"] for r in msg_rows if r["query_id"]]
    pipeline_rows = []
    for qid in query_ids:
        steps = conn.execute("""
            SELECT step_name, step_order, duration_ms, status, input_text, output_text
            FROM pipeline_steps
            WHERE query_id = ?
            ORDER BY step_order
        """, (qid,)).fetchall()
        pipeline_rows.append({"query_id": qid, "steps": steps})

    # Retrieved docs for the session (from reranking step)
    retrieved_rows = []
    for qid in query_ids:
        docs = conn.execute("""
            SELECT rd.source_file, rd.page_num, rd.rrf_score, rd.final_rank
            FROM retrieved_docs rd
            WHERE rd.query_id = ?
              AND rd.rrf_score IS NOT NULL
            ORDER BY rd.final_rank
            LIMIT 5
        """, (qid,)).fetchall()
        if docs:
            retrieved_rows.append({"query_id": qid, "docs": docs})

    # LLM call summary
    llm_rows = conn.execute("""
        SELECT lc.model_name, SUM(lc.total_tokens) AS total_tokens, COUNT(*) AS call_count
        FROM llm_calls lc
        JOIN pipeline_steps ps ON lc.step_id = ps.step_id
        JOIN queries q ON ps.query_id = q.query_id
        WHERE q.session_id = ?
        GROUP BY lc.model_name
    """, (session_id,)).fetchall()

    return {
        "session": dict(session_row),
        "messages": [dict(r) for r in msg_rows],
        "pipeline": pipeline_rows,
        "retrieved": retrieved_rows,
        "llm_summary": [dict(r) for r in llm_rows],
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  HTML report builder
# ═══════════════════════════════════════════════════════════════════════════════

def _esc(s) -> str:
    """HTML-escape a value safely."""
    if s is None:
        return ""
    return _html.escape(str(s))


def _render_message_text(text: str) -> str:
    """Convert plain text with [N] citation tags to HTML with styled spans."""
    if not text:
        return ""
    text = _esc(text)
    # Convert [Web N] citations
    text = re.sub(
        r'\[Web\s*(\d+)\]',
        r'<span class="cite-web">[Web \1]</span>',
        text
    )
    # Convert [N] document citations
    text = re.sub(
        r'\[(\d+)\]',
        r'<span class="cite">[\1]</span>',
        text
    )
    # Convert newlines
    text = text.replace("\n", "<br>")
    return text


def _build_html(data: dict, session_id: str) -> str:
    """Build the full HTML report string."""

    session       = data["session"]
    messages      = data["messages"]
    pipeline_data = data["pipeline"]
    retrieved     = data["retrieved"]
    llm_summary   = data["llm_summary"]

    title    = session.get("title") or "Chat Session"
    created  = session.get("created_at", "")[:16].replace("T", " ")
    exported = time.strftime("%Y-%m-%d %H:%M")

    # ── Stats ────────────────────────────────────────────────────────────────
    total_msgs   = len([m for m in messages if m.get("final_response")])
    rag_count    = sum(1 for m in messages if m.get("used_rag") == 1)
    web_count    = sum(1 for m in messages if m.get("used_rag") == 0)
    total_tokens = sum(r["total_tokens"] or 0 for r in llm_summary) if llm_summary else 0
    model_name   = llm_summary[0]["model_name"] if llm_summary else "—"
    # Total pipeline time across all queries
    all_durations = []
    for p in pipeline_data:
        for s in p["steps"]:
            if s["duration_ms"]:
                all_durations.append(float(s["duration_ms"]))
    total_ms = sum(all_durations)

    # ── Build sources list across all messages ────────────────────────────────
    all_sources = {}  # "filename|page" -> {source_file, page_num, count}
    for r_data in retrieved:
        for doc in r_data["docs"]:
            key = f"{doc['source_file']}|{doc['page_num']}"
            if key not in all_sources:
                all_sources[key] = {
                    "source_file": doc["source_file"],
                    "page_num":    doc["page_num"],
                    "count":       0,
                    "rrf_score":   doc["rrf_score"],
                }
            all_sources[key]["count"] += 1

    # ── HTML assembly ─────────────────────────────────────────────────────────
    parts = [f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width">
  <title>{_esc(title)} — Agentic RAG Report</title>
  <style>{_CSS}</style>
</head>
<body>

<!-- RUNNING HEADER (appears on every page via CSS running element) -->
<div id="running-header">
  <span>🌾 Agentic RAG — Agricultural Knowledge Base</span>
  <span>Session: {_esc(session_id[:8])}… · Exported {_esc(exported)}</span>
</div>

<!-- ══════════════════════════════════════════════════════════════════
     COVER PAGE
══════════════════════════════════════════════════════════════════ -->
<div class="cover">
  <div class="cover-badge">🌾 Agentic RAG · Agricultural Research Assistant</div>
  <div class="cover-title">{_esc(title)}</div>
  <div class="cover-subtitle">Session Export Report</div>
  <div class="cover-divider"></div>
  <div class="cover-meta">
    <div class="cover-meta-row"><strong>Session ID</strong>{_esc(session_id[:8])}…{_esc(session_id[-4:])}</div>
    <div class="cover-meta-row"><strong>Created</strong>{_esc(created)}</div>
    <div class="cover-meta-row"><strong>Exported</strong>{_esc(exported)}</div>
    <div class="cover-meta-row"><strong>Messages</strong>{total_msgs} exchanges</div>
    <div class="cover-meta-row"><strong>Model</strong>{_esc(model_name)}</div>
    <div class="cover-meta-row"><strong>Tokens used</strong>{total_tokens:,}</div>
  </div>
</div>

<!-- ══════════════════════════════════════════════════════════════════
     SUMMARY STATS
══════════════════════════════════════════════════════════════════ -->
<div class="section-header">Session Summary</div>

<div class="stats-row">
  <div class="stat-card">
    <div class="stat-value">{total_msgs}</div>
    <div class="stat-label">Total Exchanges</div>
  </div>
  <div class="stat-card">
    <div class="stat-value">{rag_count}</div>
    <div class="stat-label">RAG Answers</div>
  </div>
  <div class="stat-card">
    <div class="stat-value">{web_count}</div>
    <div class="stat-label">Web Search Answers</div>
  </div>
  <div class="stat-card">
    <div class="stat-value">{total_tokens:,}</div>
    <div class="stat-label">Total Tokens</div>
  </div>
  <div class="stat-card">
    <div class="stat-value">{total_ms/1000:.1f}s</div>
    <div class="stat-label">Total Pipeline Time</div>
  </div>
</div>
"""]

    # ── CONVERSATION ──────────────────────────────────────────────────────────
    parts.append('<div class="section-header">Conversation</div>\n')

    for i, msg in enumerate(messages, 1):
        query     = msg.get("original_query", "")
        response  = msg.get("final_response", "")
        query_ts  = (msg.get("query_ts") or "")[:16].replace("T", " ")
        resp_ts   = (msg.get("response_ts") or "")[:16].replace("T", " ")
        used_rag  = msg.get("used_rag")

        if used_rag == 1:
            badge = '<span class="source-badge badge-rag">RAG</span>'
        elif used_rag == 0:
            badge = '<span class="source-badge badge-web">🌐 Web</span>'
        else:
            badge = '<span class="source-badge badge-direct">Direct</span>'

        parts.append(f"""<div class="exchange">
  <div class="msg-label user">You — #{i}</div>
  <div class="msg-user">{_render_message_text(query)}</div>
  <div class="msg-ts">{_esc(query_ts)}</div>
""")
        if response:
            parts.append(f"""  <div class="msg-label bot">RAG Assistant {badge}</div>
  <div class="msg-bot">{_render_message_text(response)}</div>
  <div class="msg-ts">{_esc(resp_ts)}</div>
""")
        parts.append("</div>\n")

    # ── RECOMMENDATIONS EXTRACTION (optional) ─────────────────────────────────
    recs = []
    try:
        for msg in messages:
            resp_text = (msg.get("final_response") or "")
            if resp_text and re.search(r"\b(recommend|suggest|advis)\w*", resp_text, flags=re.I):
                # take the first 300 chars as the recommendation snippet
                snip = resp_text.strip().replace('\n', ' ')[:600]
                recs.append(snip)
    except Exception:
        recs = []

    if recs:
        parts.append('<div class="section-header amber">Key Recommendations</div>\n')
        for r in recs:
            parts.append(f'<div class="recommendation"><strong>Recommendation:</strong> {_esc(r)}</div>\n')

    # ── SOURCES CITED ─────────────────────────────────────────────────────────
    if all_sources:
        parts.append('<div class="section-header amber">Knowledge Sources Referenced</div>\n')
        parts.append('<table class="sources-table"><thead><tr>')
        parts.append('<th>#</th><th>Document</th><th>Page</th><th>RRF Score</th><th>Times Retrieved</th>')
        parts.append('</tr></thead><tbody>\n')
        for idx, (_, src) in enumerate(
            sorted(all_sources.items(), key=lambda x: -x[1]["count"]), 1
        ):
            parts.append(
                f'<tr><td>{idx}</td>'
                f'<td>{_esc(src["source_file"])}</td>'
                f'<td>{_esc(src["page_num"])}</td>'
                f'<td>{float(src["rrf_score"]):.5f}</td>'
                f'<td>{src["count"]}</td></tr>\n'
            )
        parts.append('</tbody></table>\n')

    # ── PIPELINE TRACE ────────────────────────────────────────────────────────
    if pipeline_data:
        parts.append('<div class="section-header">Pipeline Execution Trace</div>\n')
        max_dur = max(
            (float(s["duration_ms"]) for p in pipeline_data for s in p["steps"] if s["duration_ms"]),
            default=1.0
        )
        for p_idx, p_data in enumerate(pipeline_data, 1):
            msg_num = p_idx
            msg_preview = (messages[p_idx - 1]["original_query"][:60] + "…"
                           if p_idx <= len(messages) and messages[p_idx - 1]["original_query"]
                           else "")
            if p_data["steps"]:
                parts.append(f'<p style="font-size:9pt;color:#888;margin:10px 0 4px 0;">'
                              f'Message #{msg_num}: <em>{_esc(msg_preview)}</em></p>')
                parts.append('<table class="trace-table"><thead><tr>')
                parts.append('<th>Step</th><th>Order</th><th>Duration</th><th>Status</th><th>Output Summary</th>')
                parts.append('</tr></thead><tbody>\n')

                for step in p_data["steps"]:
                    dur     = float(step["duration_ms"]) if step["duration_ms"] else 0.0
                    bar_w   = max(4, int(60 * dur / max_dur))
                    status  = step["status"] or "ok"
                    cls     = "step-ok" if status == "ok" else "step-err"
                    out_snip = (step["output_text"] or "")[:80]
                    parts.append(
                        f'<tr>'
                        f'<td>{_esc(step["step_name"])}</td>'
                        f'<td style="text-align:center">{_esc(step["step_order"])}</td>'
                        f'<td>{dur:.0f}ms'
                        f'<span class="duration-bar" style="width:{bar_w}px"></span></td>'
                        f'<td class="{cls}">{_esc(status)}</td>'
                        f'<td style="font-size:8.5pt;color:#666">{_esc(out_snip)}</td>'
                        f'</tr>\n'
                    )
                parts.append('</tbody></table>\n')

    # ── FOOTER ────────────────────────────────────────────────────────────────
    parts.append(f"""
<div class="footer-note">
  Generated by Agentic RAG Platform · Agricultural Knowledge Assistant ·
  {_esc(exported)} · Session {_esc(session_id[:8])}
</div>

</body>
</html>""")

    return "".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
#  Public API
# ═══════════════════════════════════════════════════════════════════════════════

def mcp_generate_pdf(session_id: str, conn) -> dict:
    """
    MCP tool entry point.

    Returns:
        { "type": "pdf",  "bytes": <bytes>, "filename": "Chat.pdf"  }   — if weasyprint present
        { "type": "html", "html":  <str>,   "filename": "Chat.html" }   — fallback
        { "type": "error","detail": <str> }                              — session not found
    """
    data = _fetch_session_data(session_id, conn)
    if data is None:
        return {"type": "error", "detail": f"Session '{session_id}' not found in database."}

    title    = data["session"].get("title") or "Chat"
    safe_title = re.sub(r'[^\w\s-]', '', title).strip()[:60] or "Chat"
    date_str   = time.strftime("%Y-%m-%d")
    filename   = f"{safe_title}_{date_str}"

    html_content = _build_html(data, session_id)

    if _WEASYPRINT:
        try:
            pdf_bytes = _WeasyprintHTML(string=html_content).write_pdf()
            return {
                "type":     "pdf",
                "bytes":    pdf_bytes,
                "filename": f"{filename}.pdf",
            }
        except Exception as e:
            print(f"[PDF_EXPORT] weasyprint failed ({e}), falling back to HTML")

    # HTML fallback
    return {
        "type":     "html",
        "html":     html_content,
        "filename": f"{filename}.html",
    }

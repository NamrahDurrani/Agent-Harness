/**
 * AgriBot.jsx — Complete AgriBot UI
 * Open WebUI-inspired layout · Light/Dark/System theme · Settings panel
 * All chat/RAG/MCP/upload logic wired to real /api/* endpoints
 * 
 * Props: username, token, onLogout, email (optional)
 */
import { useState, useRef, useEffect, useCallback } from "react";
import { ttsService } from "./services/tts";
import agribotIcon from "./assets/agribot-icon.png";
import { getThemeColors } from "./theme";

// ═══════════════════════════════════════════════════════════════════
//  THEME SYSTEM — see ./theme.js (shared with Dashboard.jsx)
// ═══════════════════════════════════════════════════════════════════

// ═══════════════════════════════════════════════════════════════════
//  ICONS  (inline SVG paths)
// ═══════════════════════════════════════════════════════════════════
const Icon = ({ d, size = 16, stroke, fill = "none", style: sx = {} }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill={fill}
    stroke={stroke} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round"
    style={{ flexShrink: 0, ...sx }}>
    <path d={d} />
  </svg>
);
const I = {
  send:      "M22 2L11 13M22 2L15 22 11 13 2 9l20-7z",
  plus:      "M12 5v14M5 12h14",
  chat:      "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z",
  folder:    "M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z",
  trash:     "M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6",
  edit:      "M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z",
  upload:    "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12",
  search:    "M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z",
  settings:  "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z",
  user:      "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
  sun:       "M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42M12 5a7 7 0 1 0 0 14A7 7 0 0 0 12 5z",
  moon:      "M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z",
  monitor:   "M2 3h20v14H2zM8 21h8M12 17v4",
  x:         "M18 6L6 18M6 6l12 12",
  chevD:     "M6 9l6 6 6-6",
  chevR:     "M9 18l6-6-6-6",
  copy:      "M20 9H11a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2v-9a2 2 0 0 0-2-2zM5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1",
  check:     "M20 6L9 17 4 12",
  thumbUp:   "M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3",
  thumbDn:   "M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zM17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17",
  regen:     "M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15",
  share:     "M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8M16 6l-4-4-4 4M12 2v13",
  sources:   "M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2zM22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z",
  trace:     "M3 3h18v18H3zM9 9h6M9 13h6M9 17h4",
  globe:     "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zM2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z",
  tool:      "M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z",
  book:      "M4 19.5A2.5 2.5 0 0 1 6.5 17H20M4 19.5A2.5 2.5 0 0 0 6.5 22H20V2H6.5A2.5 2.5 0 0 0 4 4.5v15z",
  file:      "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6",
  pdf:       "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M11 13H8M16 13h-2M11 17H8",
  speaker:   "M11 5L6 9H2v6h4l5 4V5z",
  speakerHi: "M11 5L6 9H2v6h4l5 4V5zM19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07",
  pause:     "M6 4h4v16H6zM14 4h4v16h-4z",
  logout:    "M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9",
  wheat:     "M12 2a10 10 0 0 1 0 20M12 2C6.48 2 2 6.48 2 12M12 22c0-5.52-4.48-10-10-10M12 12c0-5.52 4.48-10 10-10M12 12c5.52 0 10 4.48 10 10",
  export:    "M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8M16 6l-4-4-4 4M12 2v13",
  bell:      "M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 0 1-3.46 0",
  mic:       "M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3zM19 10v2a7 7 0 0 1-14 0v-2M12 19v4M8 23h8",
};

// ═══════════════════════════════════════════════════════════════════
//  UTILITIES
// ═══════════════════════════════════════════════════════════════════
const nowTs = () => new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

// ─────────────────────────────────────────────────────────────────────────
// Citation system — matches the REAL backend contract.
//
// Backend (_build_sources_from_docs / _build_sources_from_web in
// rag_pipeline.py) returns a structured `sources` ARRAY on the API
// response, e.g.:
//   [{ num: 1, label: "file.pdf — p.12", source_file: "file.pdf",
//      page: 12, is_upload: false, url: "" },
//    { num: 2, label: "parc.gov.pk", source_file: "https://parc.gov.pk/...",
//      page: 0, is_upload: false, url: "https://parc.gov.pk/..." }]
//
// Inline citation tags in the answer TEXT are always plain [N] — never
// "[Web N]" — because _inject_inline_citations() in rag_pipeline.py uses
// the same numbering for both doc and web sources. There is also no
// "SOURCES:
// " text block anymore; it's stripped server-side.
// ─────────────────────────────────────────────────────────────────────────

function isWebSource(src) {
  return !!src.url;   // web sources have a url; doc sources have url === ""
}

function openSource(src) {
  if (!src) return;
  if (isWebSource(src)) {
    window.open(src.url, "_blank");
  } else {
    window.open(`/api/pdf/${encodeURIComponent(src.source_file)}#page=${src.page || 1}`, "_blank");
  }
}

function isUrduText(text) {
  if (!text) return false;
  const urduChars = (text.match(/[\u0600-\u06FF\u0750-\u077F]/g) || []).length;
  const totalChars = text.replace(/\s/g, "").length || 1;
  return urduChars / totalChars > 0.15;
}

function CitationText({ text, sources, C }) {
  const parts = text.split(/(\[\d+\])/g);
  return parts.map((part, i) => {
    const m = part.match(/^\[(\d+)\]$/);
    if (m) {
      const num = +m[1];
      const src = sources.find(s => s.num === num);
      const web = src && isWebSource(src);
      return (
        <sup key={i} onClick={() => openSource(src)}
          title={src ? (web ? src.label : `${src.source_file} p.${src.page}`) : ""}
          style={{
            cursor: src ? "pointer" : "default",
            display: "inline-flex", alignItems: "center", justifyContent: "center",
            width: 15, height: 15, marginLeft: 2,
            color: src ? (web ? C.amber : C.accent) : C.textMute,
            fontWeight: 700, fontSize: "0.62em", borderRadius: "50%",
            background: src ? (web ? C.amberBg : C.accentBg) : "transparent",
            border: src ? `1px solid ${web ? C.amberDim : C.accentDim}` : "none",
            verticalAlign: "super", lineHeight: 1,
          }}>
          {num}
        </sup>
      );
    }
    return <span key={i}>{part.split("\n").map((l, j, a) => <span key={j}>{l}{j < a.length - 1 && <br />}</span>)}</span>;
  });
}

// ─────────────────────────────────────────────────────────────────────────
// Right-side Sources Panel — open/close toggle, lists clickable sources
// for whichever message the user clicked the "sources" icon on. Replaces
// the previous inline References list (which had a broken toggle).
// ─────────────────────────────────────────────────────────────────────────
function SourcesPanel({ open, onClose, sources, label, C }) {
  return (
    <div style={{
      width: open ? 300 : 0, minWidth: open ? 300 : 0,
      background: C.surface, borderLeft: `1px solid ${C.border}`,
      display: "flex", flexDirection: "column", overflow: "hidden",
      transition: "width 0.22s ease, min-width 0.22s ease", flexShrink: 0,
    }}>
      {open && (
        <>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "14px 16px", borderBottom: `1px solid ${C.border}`, flexShrink: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <Icon d={I.sources} size={16} stroke={C.accent} />
              <span style={{ fontSize: 14, fontWeight: 700, color: C.text }}>Sources</span>
            </div>
            <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", padding: 4 }}>
              <Icon d={I.x} size={16} stroke={C.textSub} />
            </button>
          </div>

          {label && (
            <div style={{ padding: "10px 16px", fontSize: 11.5, color: C.textMute, borderBottom: `1px solid ${C.border}`, lineHeight: 1.5, overflow: "hidden", textOverflow: "ellipsis", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>
              For: <span style={{ color: C.textSub }}>{label}</span>
            </div>
          )}

          <div style={{ flex: 1, overflowY: "auto", padding: 12 }}>
            {(!sources || sources.length === 0) ? (
              <div style={{ color: C.textMute, fontSize: 12.5, textAlign: "center", marginTop: 40, lineHeight: 1.7 }}>
                No sources for this answer.<br />Click the 📖 icon under any<br />AgriBot reply to view its references here.
              </div>
            ) : (
              sources.map((s, i) => {
                const web = isWebSource(s);
                return (
                  <div key={i} onClick={() => openSource(s)}
                    style={{ display: "flex", alignItems: "flex-start", gap: 8, padding: "10px 10px", borderRadius: 10, cursor: "pointer", marginBottom: 6, border: `1px solid ${C.border}`, background: C.surface2 }}
                    onMouseEnter={e => { e.currentTarget.style.borderColor = web ? C.amber : C.accent; e.currentTarget.style.background = web ? C.amberBg : C.accentBg; }}
                    onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.background = C.surface2; }}>
                    <span style={{ minWidth: 22, height: 22, borderRadius: 6, background: web ? C.amberDim : C.accentDim, border: `1px solid ${web ? C.amber : C.accent}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 10, fontWeight: 700, color: web ? C.amber : C.accent, flexShrink: 0 }}>{s.num}</span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 12.5, fontWeight: 600, color: C.text, wordBreak: "break-word" }}>
                        {web ? s.label : s.source_file}
                      </div>
                      {!web && (
                        <div style={{ fontSize: 11, color: C.textMute, marginTop: 2 }}>Page {s.page}</div>
                      )}
                      <div style={{ fontSize: 10.5, color: web ? C.amberDim : C.accentDim, marginTop: 4, display: "flex", alignItems: "center", gap: 3 }}>
                        {web ? "Open in browser ↗" : "Open PDF ↗"}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
//  AGENT EXECUTION PANEL — live harness tree via SSE
//
//  Renders ONLY events actually received from /agent/events/{execution_id}.
//  A node appears the instant its real agent.start event arrives and
//  never before — there is no pre-declared/fake tree shape here. Status,
//  duration, retry_count, tools, and input/output summaries are exactly
//  what the backend's AgentHarness (agent_box.py) put in the event.
//
//  NOTE on the `parentAgentId` field below: agent_box.py's events carry
//  the parent AGENT's id under the JSON key "parent_execution_id" (a
//  pre-existing naming choice in the harness, not something invented
//  here) — it is NOT the overall workflow's execution_id. Each event's
//  top-level "execution_id" field is the actual run id; we already know
//  that one client-side since we generated it before subscribing.
// ═══════════════════════════════════════════════════════════════════
function formatDuration(ms) {
  if (ms == null) return "";
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function AgentNodeIcon({ status, C }) {
  if (status === "running") {
    return <span style={{ display: "inline-block", width: 8, height: 8, borderRadius: "50%", background: C.accent, animation: "agriPulse 1.1s ease-in-out infinite", flexShrink: 0 }} />;
  }
  if (status === "completed") return <span style={{ color: C.accent, fontWeight: 700, flexShrink: 0 }}>✓</span>;
  if (status === "failed") return <span style={{ color: "#e74c3c", fontWeight: 700, flexShrink: 0 }}>✕</span>;
  if (status === "retrying") return <span style={{ color: C.amber || "#b07010", fontWeight: 700, flexShrink: 0 }}>⚠</span>;
  return <span style={{ color: C.textMute, flexShrink: 0 }}>○</span>;
}

function AgentTreeNode({ node, C, depth, selectedId, onSelect }) {
  const [collapsed, setCollapsed] = useState(false);
  const hasChildren = node.children && node.children.length > 0;
  const isSelected = selectedId === node.agentId;

  return (
    <div>
      <div
        onClick={() => onSelect(node.agentId)}
        style={{
          display: "flex", alignItems: "center", gap: 7,
          padding: "5px 8px", marginLeft: depth * 16,
          borderRadius: 6, cursor: "pointer",
          background: isSelected ? C.accentBg : "transparent",
          border: `1px solid ${isSelected ? C.accentDim : "transparent"}`,
        }}
        onMouseEnter={e => { if (!isSelected) e.currentTarget.style.background = C.surface2; }}
        onMouseLeave={e => { if (!isSelected) e.currentTarget.style.background = "transparent"; }}
      >
        {hasChildren && (
          <span onClick={e => { e.stopPropagation(); setCollapsed(c => !c); }}
            style={{ width: 12, color: C.textMute, fontSize: 10, cursor: "pointer", flexShrink: 0 }}>
            {collapsed ? "▸" : "▾"}
          </span>
        )}
        {!hasChildren && <span style={{ width: 12, flexShrink: 0 }} />}
        <AgentNodeIcon status={node.status} C={C} />
        <span style={{ fontSize: 12.5, color: C.text, fontWeight: node.status === "running" ? 700 : 500, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
          {node.name}
        </span>
        {node.retryCount > 0 && (
          <span style={{ fontSize: 10, color: C.amber || "#b07010", background: C.amberBg || "rgba(176,112,16,0.12)", padding: "1px 6px", borderRadius: 8, flexShrink: 0 }}>
            retry {node.retryCount}
          </span>
        )}
        <span style={{ flex: 1 }} />
        <span style={{ fontSize: 11, color: C.textMute, flexShrink: 0 }}>
          {node.status === "running" ? "running…" : formatDuration(node.durationMs)}
        </span>
      </div>
      {hasChildren && !collapsed && node.children.map(child => (
        <AgentTreeNode key={child.agentId} node={child} C={C} depth={depth + 1} selectedId={selectedId} onSelect={onSelect} />
      ))}
    </div>
  );
}

function AgentExecutionPanel({ open, onClose, executionId, nodes, execStatus, execError, C }) {
  const [selectedId, setSelectedId] = useState(null);

  // Build tree from the flat { agentId -> node } map every render — trees
  // here are small (a dozen-ish agents), no need to memoize.
  const roots = [];
  if (nodes) {
    const byId = nodes;
    const childrenOf = {};
    Object.values(byId).forEach(n => {
      const pid = n.parentAgentId || "__root__";
      (childrenOf[pid] = childrenOf[pid] || []).push(n);
    });
    const attach = (n) => { n.children = (childrenOf[n.agentId] || []).sort((a, b) => a.startedAt - b.startedAt); n.children.forEach(attach); return n; };
    (childrenOf["__root__"] || []).sort((a, b) => a.startedAt - b.startedAt).forEach(n => roots.push(attach(n)));
  }
  const selectedNode = selectedId ? nodes[selectedId] : null;

  return (
    <div style={{
      width: open ? 340 : 0, minWidth: open ? 340 : 0,
      background: C.surface, borderLeft: `1px solid ${C.border}`,
      display: "flex", flexDirection: "column", overflow: "hidden",
      transition: "width 0.22s ease, min-width 0.22s ease", flexShrink: 0,
    }}>
      {open && (
        <>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "14px 16px", borderBottom: `1px solid ${C.border}`, flexShrink: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <Icon d={I.trace} size={16} stroke={C.accent} />
              <span style={{ fontSize: 14, fontWeight: 700, color: C.text }}>Agent Execution</span>
            </div>
            <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", padding: 4 }}>
              <Icon d={I.x} size={16} stroke={C.textSub} />
            </button>
          </div>

          {executionId && (
            <div style={{ padding: "8px 16px", fontSize: 10.5, color: C.textMute, borderBottom: `1px solid ${C.border}`, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ fontFamily: "monospace" }}>{executionId.slice(0, 12)}…</span>
              <span style={{
                fontWeight: 700,
                color: execStatus === "completed" ? C.accent : execStatus === "error" ? "#e74c3c" : C.textSub,
              }}>
                {execStatus === "connecting" ? "◌ CONNECTING…" : execStatus === "running" ? "● RUNNING" : execStatus === "completed" ? "✓ COMPLETED" : execStatus === "error" ? "✕ FAILED" : ""}
              </span>
            </div>
          )}

          <div style={{ flex: 1, overflowY: "auto", padding: "10px 8px" }}>
            {roots.length === 0 ? (
              <div style={{ color: C.textMute, fontSize: 12.5, textAlign: "center", marginTop: 40, lineHeight: 1.7 }}>
                No execution yet.<br />Send a message or export a PDF<br />to see the live agent tree here.
              </div>
            ) : (
              roots.map(n => <AgentTreeNode key={n.agentId} node={n} C={C} depth={0} selectedId={selectedId} onSelect={id => setSelectedId(id === selectedId ? null : id)} />)
            )}
            {execError && (
              <div style={{ margin: "10px 8px", padding: "8px 10px", borderRadius: 8, background: "rgba(231,76,60,0.1)", border: "1px solid #e74c3c", fontSize: 11.5, color: "#e74c3c" }}>
                {execError}
              </div>
            )}
          </div>

          {selectedNode && (
            <div style={{ borderTop: `1px solid ${C.border}`, padding: "12px 16px", maxHeight: 240, overflowY: "auto", flexShrink: 0, background: C.surface2 }}>
              <div style={{ fontSize: 12.5, fontWeight: 700, color: C.text, marginBottom: 6 }}>{selectedNode.name}</div>
              <div style={{ fontSize: 11, color: C.textSub, display: "grid", gridTemplateColumns: "auto 1fr", gap: "3px 8px" }}>
                <span style={{ color: C.textMute }}>Status</span><span>{selectedNode.status}</span>
                <span style={{ color: C.textMute }}>Duration</span><span>{formatDuration(selectedNode.durationMs)}</span>
                {selectedNode.tools && selectedNode.tools.length > 0 && (
                  <><span style={{ color: C.textMute }}>Tools</span><span>{selectedNode.tools.join(", ")}</span></>
                )}
                {selectedNode.retryCount > 0 && (
                  <><span style={{ color: C.textMute }}>Retries</span><span>{selectedNode.retryCount}</span></>
                )}
                {selectedNode.inputSummary && (
                  <><span style={{ color: C.textMute }}>Input</span><span style={{ wordBreak: "break-word" }}>{selectedNode.inputSummary}</span></>
                )}
                {selectedNode.outputSummary && (
                  <><span style={{ color: C.textMute }}>Output</span><span style={{ wordBreak: "break-word" }}>{selectedNode.outputSummary}</span></>
                )}
                {selectedNode.error && (
                  <><span style={{ color: "#e74c3c" }}>Error</span><span style={{ color: "#e74c3c", wordBreak: "break-word" }}>{selectedNode.error}</span></>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
//  CODE NARRATION BLOCK — the "Analyzing ▾ [Python]" collapsible block.
//
//  Rendered from real `code.block` SSE events (agent_harness's
//  code_narration.py emits the ACTUAL source of the render/chart/compose
//  function before it runs) — not a fabricated summary, so this is
//  honest about what "View Analysis" shows later.
// ═══════════════════════════════════════════════════════════════════
function CodeNarrationBlock({ label, code, C, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div style={{ border: `1px solid ${C.border}`, borderRadius: 10, overflow: "hidden", margin: "6px 0", background: C.surface }}>
      <button onClick={() => setOpen(o => !o)}
        style={{ width: "100%", display: "flex", alignItems: "center", gap: 8, padding: "9px 12px", background: C.surface2, border: "none", cursor: "pointer", fontFamily: "inherit" }}>
        <Icon d={I.chevD} size={12} stroke={C.textSub} style={{ transform: open ? "none" : "rotate(-90deg)", transition: "transform 0.15s" }} />
        <span style={{ fontSize: 12, fontWeight: 600, color: C.textSub }}>{label}</span>
      </button>
      {open && (
        <pre style={{ margin: 0, padding: "10px 14px", fontSize: 11.5, lineHeight: 1.6, color: C.text, background: "rgba(0,0,0,0.25)", overflowX: "auto", fontFamily: "'JetBrains Mono', Consolas, monospace" }}>
          {code}
        </pre>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
//  DOCUMENT CARD — the 📄 filename chip that appears once
//  `artifact.preview` fires. Styled after the existing "attached file"
//  card above the user bubble (same icon-box + name/type layout), so it
//  reads as the same visual language rather than a bolted-on new pattern.
// ═══════════════════════════════════════════════════════════════════
function DocumentCard({ executionId, filename, fileType, C, onOpen }) {
  const downloadUrl = `/api/artifacts/${executionId}/download`;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6, margin: "8px 0", maxWidth: 320 }}>
      <a href={downloadUrl} download
        style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12.5, color: C.accent, fontWeight: 600, textDecoration: "none" }}>
        <Icon d={I.export} size={13} stroke={C.accent} />
        Download {filename}
      </a>
      <div onClick={() => onOpen(executionId, filename, fileType)}
        style={{ display: "flex", alignItems: "center", gap: 10, background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: "9px 14px 9px 10px", cursor: "pointer", transition: "border-color 0.15s" }}
        onMouseEnter={e => e.currentTarget.style.borderColor = C.accent}
        onMouseLeave={e => e.currentTarget.style.borderColor = C.border}>
        <div style={{ width: 34, height: 34, borderRadius: 8, background: "rgba(224,54,42,0.1)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <Icon d={I.pdf} size={16} stroke="#e0362a" />
        </div>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontSize: 12.5, fontWeight: 700, color: C.text, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }} title={filename}>
            {filename}
          </div>
          <div style={{ fontSize: 10.5, color: C.textMute, marginTop: 1 }}>{(fileType || "pdf").toUpperCase()}</div>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
//  DOCUMENT VIEWER PANEL — right-side panel, sibling of
//  AgentExecutionPanel / SourcesPanel (same slide-open width pattern),
//  opened by clicking a DocumentCard.
// ═══════════════════════════════════════════════════════════════════
function DocumentViewerPanel({ open, onClose, executionId, filename, fileType, onViewAnalysis, C }) {
  return (
    <div style={{
      width: open ? 420 : 0, minWidth: open ? 420 : 0,
      background: C.surface, borderLeft: `1px solid ${C.border}`,
      display: "flex", flexDirection: "column", overflow: "hidden",
      transition: "width 0.22s ease, min-width 0.22s ease", flexShrink: 0,
    }}>
      {open && executionId && (
        <>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "14px 16px", borderBottom: `1px solid ${C.border}`, flexShrink: 0 }}>
            <div style={{ minWidth: 0, display: "flex", flexDirection: "column" }}>
              <span style={{ fontSize: 10.5, color: C.textMute }}>Library</span>
              <span style={{ fontSize: 13.5, fontWeight: 700, color: C.text, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{filename}</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 4, flexShrink: 0 }}>
              <a href={`/api/artifacts/${executionId}/download`} download title="Download"
                style={{ display: "flex", padding: 6, borderRadius: 6 }}>
                <Icon d={I.export} size={16} stroke={C.textSub} />
              </a>
              <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", padding: 6 }}>
                <Icon d={I.x} size={16} stroke={C.textSub} />
              </button>
            </div>
          </div>

          <div style={{ flex: 1, background: "#525659", display: "flex" }}>
            {fileType === "pdf" ? (
              <iframe src={`/api/artifacts/${executionId}/download`} title={filename}
                style={{ flex: 1, border: "none" }} />
            ) : (
              <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#ccc", fontSize: 12.5, textAlign: "center", padding: 20 }}>
                Preview isn't available for .{fileType} files — use Download to open it.
              </div>
            )}
          </div>

          <div style={{ padding: 12, borderTop: `1px solid ${C.border}`, flexShrink: 0 }}>
            <button onClick={() => onViewAnalysis(executionId)}
              style={{ width: "100%", padding: "9px 14px", borderRadius: 8, border: `1px solid ${C.border}`, background: C.surface2, color: C.text, fontSize: 12.5, fontWeight: 600, cursor: "pointer", fontFamily: "inherit" }}>
              View Analysis
            </button>
          </div>
        </>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
//  ANALYSIS MODAL — "View Analysis": every code.block the harness
//  narrated while building this document, fetched from
//  GET /api/artifacts/{execution_id} (artifact_store.py).
// ═══════════════════════════════════════════════════════════════════
function AnalysisModal({ executionId, onClose, C }) {
  const [blocks, setBlocks] = useState(null);   // null = loading

  useEffect(() => {
    if (!executionId) return;
    setBlocks(null);
    fetch(`/api/artifacts/${executionId}`)
      .then(r => r.json())
      .then(d => setBlocks(d.code_blocks || []))
      .catch(() => setBlocks([]));
  }, [executionId]);

  if (!executionId) return null;

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.65)", zIndex: 2100, display: "flex", alignItems: "center", justifyContent: "center" }}
      onClick={onClose}>
      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 16, padding: 22, width: 620, maxWidth: "90vw", maxHeight: "80vh", overflowY: "auto", boxShadow: C.shadow }}
        onClick={e => e.stopPropagation()}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
          <span style={{ fontSize: 15, fontWeight: 700, color: C.text }}>Analysis</span>
          <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", padding: 4 }}>
            <Icon d={I.x} size={16} stroke={C.textSub} />
          </button>
        </div>
        {blocks === null ? (
          <div style={{ color: C.textMute, fontSize: 12.5, textAlign: "center", padding: 24 }}>Loading…</div>
        ) : blocks.length === 0 ? (
          <div style={{ color: C.textMute, fontSize: 12.5, textAlign: "center", padding: 24 }}>No code was recorded for this document.</div>
        ) : (
          blocks.map((b, i) => <CodeNarrationBlock key={i} label={b.label} code={b.code} C={C} defaultOpen={i === 0} />)
        )}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
//  MESSAGE BUBBLE
// ═══════════════════════════════════════════════════════════════════
function Message({ msg, C, token, onRegenerate, onShowSources, onExportPDF, msgId, onOpenDocument }) {
  const { role, content, ts, sources = [], attachedFiles = [], scopedToUpload, artifact = null, codeBlocks = [] } = msg;
  const isUser = role === "user";
  const [copied, setCopied] = useState(false);
  const [liked, setLiked]   = useState(null);

  // ── TTS playback state for this message's speaker button ──────────────
  // "idle" | "loading" | "playing" | "paused"
  const [ttsState, setTtsState] = useState("idle");

  useEffect(() => {
    const unsub = ttsService.onStateChange((id, state) => {
      if (id === msgId) {
        setTtsState(state === "stopped" ? "idle" : state);
      } else if (state === "playing") {
        // A different message started playing — this one is no longer active
        setTtsState(s => (s === "playing" || s === "paused") ? "idle" : s);
      }
    });
    return unsub;
  }, [msgId]);

  // Detect language from the actual text so TTS routes to the right MMS
  // model — same Urdu-Unicode-range heuristic used server-side in
  // language_layer.py's detect_language(), kept simple here since we only
  // need "en" vs "ur" for routing, not the full en/ur/roman_ur/mixed split.
  const detectSpeechLang = (text) => {
    const urduChars = (text.match(/[\u0600-\u06FF]/g) || []).length;
    const totalChars = text.replace(/\s/g, "").length || 1;
    return (urduChars / totalChars) > 0.15 ? "ur" : "en";
  };

  const handleSpeakerClick = async () => {
    if (ttsState === "loading") return;   // ignore repeated clicks while fetching
    setTtsState("loading");
    try {
      const lang = detectSpeechLang(content);
      const state = await ttsService.toggle(msgId, content, lang);
      setTtsState(state);
    } catch (err) {
      console.error("TTS failed:", err);
      setTtsState("idle");
      alert("Unable to generate speech. " + (err.message || ""));
    }
  };

  const Btn = ({ ic, title, onClick, active, col }) => (
    <button onClick={onClick} title={title} style={{ background: "none", border: "none", cursor: "pointer", padding: "3px 5px", borderRadius: 6, display: "flex", alignItems: "center", opacity: 0.5, transition: "opacity 0.15s" }}
      onMouseEnter={e => { e.currentTarget.style.opacity = "1"; e.currentTarget.style.background = C.surface2; }}
      onMouseLeave={e => { e.currentTarget.style.opacity = "0.5"; e.currentTarget.style.background = "none"; }}>
      <Icon d={I[ic]} size={13} stroke={active ? (col || C.accent) : C.textSub} />
    </button>
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: isUser ? "flex-end" : "flex-start", gap: 4, maxWidth: "100%" }}>
      {/* Label row */}
      <div style={{ display: "flex", alignItems: "center", gap: 6, flexDirection: isUser ? "row-reverse" : "row" }}>
        <div style={{ width: 28, height: 28, borderRadius: "50%", background: isUser ? C.accentDim : C.surface2, border: `1.5px solid ${isUser ? C.accent : C.border}`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, fontSize: isUser ? 12 : 14 }}>
          {isUser ? <Icon d={I.user} size={14} stroke={C.accent} /> : "🌾"}
        </div>
        <span style={{ fontSize: 11, color: C.textMute }}>
          {isUser ? "You" : "AgriBot"} · {ts}
        </span>
      </div>

      {/* Attached file card(s) — rendered ABOVE the bubble, like ChatGPT.
          Snapshotted onto the message at send time (see sendMessage),
          so it always reflects what was actually attached to THIS
          message even if the composer's attachment later changes. */}
      {isUser && attachedFiles.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4 }}>
          {attachedFiles.map((f, i) => (
            <div key={i} style={{
              display: "flex", alignItems: "center", gap: 10,
              background: C.surface, border: `1px solid ${C.border}`,
              borderRadius: 12, padding: "9px 14px 9px 10px", maxWidth: 260,
              boxShadow: "0 1px 3px rgba(0,0,0,0.15)",
            }}>
              <div style={{ width: 34, height: 34, borderRadius: 8, background: "rgba(224,54,42,0.1)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <Icon d={I.file} size={16} stroke="#e0362a" />
              </div>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: 12.5, fontWeight: 700, color: C.text, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }} title={f.name}>
                  {f.name}
                </div>
                <div style={{ fontSize: 10.5, color: C.textMute, marginTop: 1 }}>PDF</div>
              </div>
            </div>
          ))}
          {scopedToUpload && (
            <span style={{ display: "inline-flex", alignItems: "center", gap: 5, padding: "2px 10px", borderRadius: 20, border: `1px solid ${C.accent}`, background: C.accentBg, fontSize: 11, fontWeight: 600, color: C.accent }}>
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: C.accent, flexShrink: 0 }} />
              This document only
            </span>
          )}
        </div>
      )}

      {/* Bubble — user messages keep the chat-bubble look; bot messages flow
          borderless like Claude/ChatGPT, no surrounding box. Urdu text
          gets a larger font size, taller line-height, and RTL direction —
          Arabic-script glyphs read poorly at Latin-script sizing. */}
      <div style={isUser
        ? { maxWidth: "76%", background: C.userBub, border: `1px solid ${C.accentDim}`, borderRadius: "16px 4px 16px 16px", padding: "10px 15px", color: C.text, wordBreak: "break-word", ...(isUrduText(content) ? { fontSize: 19, lineHeight: 2, direction: "rtl", textAlign: "right", fontFamily: "'Noto Nastaliq Urdu','Jameel Noori Nastaleeq',serif" } : { fontSize: 14, lineHeight: 1.7 }) }
        : { maxWidth: "88%", padding: "4px 2px", color: C.text, wordBreak: "break-word", ...(isUrduText(content) ? { fontSize: 19, lineHeight: 2.1, direction: "rtl", textAlign: "right", fontFamily: "'Noto Nastaliq Urdu','Jameel Noori Nastaleeq',serif" } : { fontSize: 14.5, lineHeight: 1.75 }) }
      }>
        {isUser ? (
          <span style={{ whiteSpace: "pre-wrap" }}>{content}</span>
        ) : (
          <div style={{ whiteSpace: "pre-wrap" }}><CitationText text={content} sources={sources} C={C} /></div>
        )}

        {/* Live "Analyzing" code blocks — real code.block SSE events
            narrated while this document was being generated. */}
        {!isUser && codeBlocks.length > 0 && (
          <div style={{ marginTop: 8 }}>
            {codeBlocks.map((b, i) => <CodeNarrationBlock key={i} label={b.label} code={b.code} C={C} defaultOpen={false} />)}
          </div>
        )}

        {/* Generated document card — appears once artifact.preview fires
            for this message's execution. */}
        {!isUser && artifact && (
          <DocumentCard executionId={artifact.executionId} filename={artifact.filename}
            fileType={artifact.fileType} C={C} onOpen={onOpenDocument} />
        )}
      </div>

      {/* Action bar for bot messages */}
      {!isUser && (
        <div style={{ display: "flex", gap: 2, paddingLeft: 4 }}>
          <Btn ic={copied ? "check" : "copy"} title="Copy" active={copied} col={C.accent} onClick={() => { navigator.clipboard.writeText(content); setCopied(true); setTimeout(() => setCopied(false), 1500); }} />
          {/* Speaker — TTS playback, exactly like ChatGPT's voice button */}
          <Btn
            ic={ttsState === "loading" ? "speaker" : ttsState === "playing" ? "pause" : "speaker"}
            title={ttsState === "loading" ? "Generating audio…" : ttsState === "playing" ? "Pause" : ttsState === "paused" ? "Resume" : "Listen"}
            active={ttsState === "playing" || ttsState === "paused"}
            col={C.accent}
            onClick={handleSpeakerClick}
          />
          <Btn ic="thumbUp"  title="Good"       active={liked === "up"}   col={C.accent}  onClick={() => setLiked(l => l === "up"   ? null : "up")}   />
          <Btn ic="thumbDn"  title="Bad"        active={liked === "dn"}   col={C.danger}  onClick={() => setLiked(l => l === "dn"   ? null : "dn")}   />
          <Btn ic="share"    title="Share"      onClick={() => navigator.clipboard.writeText(content)} />
          {onRegenerate && <Btn ic="regen" title="Regenerate" onClick={onRegenerate} />}
          {onExportPDF && <Btn ic="pdf" title="Download this conversation as PDF" onClick={onExportPDF} />}
          <div style={{ width: 1, height: 14, background: C.border, margin: "auto 2px" }} />
          <Btn ic="sources" title={sources.length ? "Open sources panel" : "No sources for this answer"}
            active={false} col={C.accent}
            onClick={() => onShowSources && onShowSources(sources, content)} />
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
//  TYPING INDICATOR
// ═══════════════════════════════════════════════════════════════════
function TypingDots({ C }) {
  return (
    <div style={{ display: "flex", alignItems: "flex-start", gap: 8 }}>
      <div style={{ width: 28, height: 28, borderRadius: "50%", background: C.surface2, border: `1.5px solid ${C.border}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14 }}>🌾</div>
      <div style={{ background: C.botBub, border: `1px solid ${C.border}`, borderRadius: "4px 16px 16px 16px", padding: "12px 16px", display: "flex", gap: 6, alignItems: "center" }}>
        {[0, 0.2, 0.4].map((d, i) => (
          <div key={i} style={{ width: 7, height: 7, borderRadius: "50%", background: C.accentDim, animation: "agriPulse 1.2s ease-in-out infinite", animationDelay: `${d}s` }} />
        ))}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
//  WELCOME SCREEN
// ═══════════════════════════════════════════════════════════════════

// Time-of-day greeting pools — one is picked at random from whichever
// bucket matches the current hour, refreshed each time Welcome mounts
// (new chat / page load), same idea as Claude's rotating greetings.
const _GREETINGS = {
  morning: [
    "Good morning! Ready to dig into today's agricultural questions?",
    "Morning! What's growing on your mind today?",
    "Rise and shine — ask me anything about crops, weather, or your fields.",
  ],
  afternoon: [
    "Good afternoon! What can I help you look into today?",
    "Hope your day's going well — what's on your mind?",
    "Afternoon! Ask away — crops, weather, prices, all of it.",
  ],
  evening: [
    "Good evening! What can I help you with tonight?",
    "Evening! Let's wrap up any questions before the day ends.",
    "How can I help you this evening?",
  ],
  night: [
    "Working late? I'm here whenever you need me.",
    "Good night — one more question before you go?",
    "Still up? Ask away, I don't sleep.",
  ],
};

function _pickGreeting() {
  const h = new Date().getHours();
  const bucket = h < 5 ? "night" : h < 12 ? "morning" : h < 17 ? "afternoon" : h < 21 ? "evening" : "night";
  const pool = _GREETINGS[bucket];
  return pool[Math.floor(Math.random() * pool.length)];
}

function Welcome({ C, onSend, username }) {
  const [greeting] = useState(_pickGreeting);
  const prompts = [
    "What wheat diseases are monitored in Punjab?",
    "Is today's weather good for wheat sowing in Lahore?",
    "Convert 50 acres to hectares",
    "Summarise PARC's 2023-24 research highlights",
    "Which FAO guidelines cover Ug99 rust?",
    "When should I sow cotton in Sindh?",
  ];
  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "32px 24px", gap: 28 }}>
      <div style={{ textAlign: "center" }}>
        <div style={{ fontSize: 52, marginBottom: 12 }}>🌾</div>
        <h2 style={{ fontSize: 26, fontWeight: 800, color: C.text, letterSpacing: "-0.03em", margin: "0 0 8px" }}>Welcome to AgriBot</h2>
        <p style={{ fontSize: 14, color: C.textSub, maxWidth: 440, lineHeight: 1.6, margin: 0 }}>
          {greeting}
        </p>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, width: "100%", maxWidth: 580 }}>
        {prompts.map((p, i) => (
          <button key={i} onClick={() => onSend(p)}
            style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: "11px 15px", color: C.textSub, fontSize: 12.5, textAlign: "left", cursor: "pointer", lineHeight: 1.5, transition: "all 0.15s", fontFamily: "inherit" }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = C.accent; e.currentTarget.style.color = C.text; e.currentTarget.style.background = C.accentBg; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.color = C.textSub; e.currentTarget.style.background = C.surface; }}>
            {p}
          </button>
        ))}
      </div>
    </div>
  );
}

function SettingsModal({ C, open, onClose, username, email, themeMode, setThemeMode }) {
  const [tab, setTab] = useState("profile");
  if (!open) return null;
  const themes = [
    { id: "light",  label: "Light",  ic: "sun",     desc: "Light green interface" },
    { id: "dark",   label: "Dark",   ic: "moon",    desc: "Dark green (default)" },
    { id: "system", label: "System", ic: "monitor", desc: "Follow OS preference" },
  ];
  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.65)", zIndex: 2000, display: "flex", alignItems: "center", justifyContent: "center" }} onClick={onClose}>
      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 18, width: 560, maxWidth: "94vw", maxHeight: "85vh", overflow: "hidden", boxShadow: C.shadow, display: "flex", flexDirection: "column" }} onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div style={{ padding: "20px 24px 16px", borderBottom: `1px solid ${C.border}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <Icon d={I.settings} size={20} stroke={C.accent} />
            <span style={{ fontSize: 17, fontWeight: 700, color: C.text }}>Settings</span>
          </div>
          <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", padding: 4 }}>
            <Icon d={I.x} size={18} stroke={C.textSub} />
          </button>
        </div>
        {/* Tab row */}
        <div style={{ display: "flex", borderBottom: `1px solid ${C.border}`, padding: "0 24px" }}>
          {[["profile", I.user, "Profile"], ["appearance", I.sun, "Appearance"]].map(([id, ic, label]) => (
            <button key={id} onClick={() => setTab(id)} style={{ display: "flex", alignItems: "center", gap: 6, padding: "12px 16px 10px", background: "none", border: "none", borderBottom: `2px solid ${tab === id ? C.accent : "transparent"}`, cursor: "pointer", fontSize: 13, fontWeight: 600, color: tab === id ? C.accent : C.textSub, transition: "color 0.15s", fontFamily: "inherit" }}>
              <Icon d={ic} size={14} stroke={tab === id ? C.accent : C.textSub} />{label}
            </button>
          ))}
        </div>
        {/* Content */}
        <div style={{ flex: 1, overflowY: "auto", padding: 24 }}>
          {tab === "profile" && (
            <div>
              {/* Avatar */}
              <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 24 }}>
                <div style={{ width: 64, height: 64, borderRadius: "50%", background: C.accentBg, border: `2px solid ${C.accent}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 26, fontWeight: 700, color: C.accent }}>
                  {(username || "U")[0].toUpperCase()}
                </div>
                <div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: C.text }}>{username}</div>
                  <div style={{ fontSize: 12, color: C.textMute, marginTop: 2 }}>AgriBot Member</div>
                </div>
              </div>
              {/* Fields (read-only display) */}
              {[["Username", username || "—"], ["Email", email || "Not configured"]].map(([label, val]) => (
                <div key={label} style={{ marginBottom: 14 }}>
                  <div style={{ fontSize: 11, color: C.textSub, marginBottom: 5, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em" }}>{label}</div>
                  <div style={{ background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 8, padding: "10px 14px", fontSize: 14, color: C.text }}>
                    {val}
                  </div>
                </div>
              ))}
              <div style={{ marginTop: 20, padding: "12px 14px", background: C.accentBg, border: `1px solid ${C.accentDim}`, borderRadius: 10, fontSize: 12.5, color: C.textSub, lineHeight: 1.6 }}>
                🌾 <strong style={{ color: C.accent }}>AgriBot</strong> — Agricultural Knowledge Assistant. Powered by Groq LLM, ChromaDB vector search, BM25 retrieval, RRF fusion, Tavily web search, and MCP tools.
              </div>
            </div>
          )}
          {tab === "appearance" && (
            <div>
              <div style={{ fontSize: 13, color: C.textSub, marginBottom: 18, lineHeight: 1.6 }}>
                Choose your preferred color theme. <strong>Light</strong> uses a fresh light-green palette. <strong>Dark</strong> uses the original deep dark green. <strong>System</strong> follows your OS setting.
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {themes.map(t => (
                  <div key={t.id} onClick={() => setThemeMode(t.id)}
                    style={{ display: "flex", alignItems: "center", gap: 14, padding: "14px 16px", background: themeMode === t.id ? C.accentBg : C.surface2, border: `2px solid ${themeMode === t.id ? C.accent : C.border}`, borderRadius: 12, cursor: "pointer", transition: "all 0.15s" }}>
                    <div style={{ width: 40, height: 40, borderRadius: 10, background: t.id === "light" ? "#e8f4e0" : t.id === "dark" ? "#141c0f" : "linear-gradient(135deg,#e8f4e0 50%,#141c0f 50%)", border: `1px solid ${C.border}`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                      <Icon d={I[t.ic]} size={18} stroke={t.id === "light" ? "#4a8a1e" : t.id === "dark" ? "#7ab648" : "#7ab648"} />
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 14, fontWeight: 600, color: C.text }}>{t.label}</div>
                      <div style={{ fontSize: 12, color: C.textSub, marginTop: 2 }}>{t.desc}</div>
                    </div>
                    {themeMode === t.id && (
                      <div style={{ width: 20, height: 20, borderRadius: "50%", background: C.accent, display: "flex", alignItems: "center", justifyContent: "center" }}>
                        <Icon d={I.check} size={12} stroke="#fff" />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
//  MAIN AGRIBOT COMPONENT
// ═══════════════════════════════════════════════════════════════════
const PROJ_EMOJIS = ["🌱", "🌾", "🪴", "🌽", "🍃", "🌿", "🌻", "🌴", "🫘", "🍀"];

export default function AgriBot({ username = "user", email = "", token, onLogout, onGoToDashboard, initialAction }) {
  // ── Theme ─────────────────────────────────────────────────────────
  const [themeMode, setThemeMode] = useState(() => localStorage.getItem("agribot_theme") || "dark");
  const C = getThemeColors(themeMode);
  useEffect(() => { localStorage.setItem("agribot_theme", themeMode); }, [themeMode]);

  // ── Sidebar ───────────────────────────────────────────────────────
  const [sideOpen, setSideOpen]   = useState(true);
  const [sideSearch, setSideSearch] = useState("");

  // ── Projects (localStorage) ───────────────────────────────────────
  const [projects, setProjects]   = useState(() => { try { return JSON.parse(localStorage.getItem(`agribot_projects_${username}`) || "[]"); } catch { return []; } });
  const [expandedPjs, setExpandedPjs] = useState(new Set());
  const saveProjects = ps => { setProjects(ps); localStorage.setItem(`agribot_projects_${username}`, JSON.stringify(ps)); };

  // ── Sessions ──────────────────────────────────────────────────────
  const [apiSessions, setApiSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null); // { sessionId, projectId, title }
  const [msgCache, setMsgCache]     = useState({});         // { [sessionId]: Message[] }
  const [webSearchOn, setWebSearchOn] = useState(false);
  const [loading, setLoading]       = useState(false);
  const [input, setInput]           = useState("");
  const [trace, setTrace]           = useState(null);

  // ── Upload ────────────────────────────────────────────────────────
  const [uploadStatus, setUploadStatus]   = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [scopeToUpload, setScopeToUpload] = useState(true); // "Answer only from this document" —
                                                              // defaults ON once a file is attached,
                                                              // since that's the overwhelming intent
                                                              // when someone uploads a specific PDF

  // ── Status ────────────────────────────────────────────────────────
  const [chunkCount, setChunkCount] = useState(0);
  const [statusData, setStatusData] = useState(null);

  // ── Modals ────────────────────────────────────────────────────────
  const [showSettings, setShowSettings] = useState(false);
  const [showNewProj, setShowNewProj]   = useState(false);
  const [newProjName, setNewProjName]   = useState("");
  const [newProjEmoji, setNewProjEmoji] = useState("🌱");
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  // ── Right-side Sources panel ────────────────────────────────────────
  const [sourcesPanelOpen, setSourcesPanelOpen]       = useState(false);
  const [sourcesPanelSources, setSourcesPanelSources] = useState([]);
  const [sourcesPanelLabel, setSourcesPanelLabel]     = useState("");

  // ── Agent Execution panel (live harness tree via SSE) ───────────────
  const [execPanelOpen, setExecPanelOpen]   = useState(false);
  const [execNodes, setExecNodes]           = useState({});   // { agentId: node }
  const [execExecutionId, setExecExecutionId] = useState(null);
  const [execStatus, setExecStatus]         = useState("idle"); // idle | running | completed | error
  const [execError, setExecError]           = useState(null);
  const execEventSourceRef = useRef(null);

  // ── Live document-generation extras for the CURRENT execution ───────
  // Snapshotted onto the bot message once sendMessage's fetch resolves
  // (see sendMessage) — kept separate from execNodes since these render
  // INSIDE the chat bubble, not in the Agent Execution side panel.
  const [execCodeBlocks, setExecCodeBlocks] = useState([]);   // [{label, code}]
  const [execArtifact, setExecArtifact]     = useState(null); // {executionId, filename, fileType}

  // ── Right-side Document Viewer panel + Analysis modal ───────────────
  const [docPanelOpen, setDocPanelOpen] = useState(false);
  const [docPanelData, setDocPanelData] = useState(null); // {executionId, filename, fileType}
  const [analysisExecId, setAnalysisExecId] = useState(null);

  const openDocumentViewer = (executionId, filename, fileType) => {
    setDocPanelData({ executionId, filename, fileType: fileType || "pdf" });
    setDocPanelOpen(true);
    setExecPanelOpen(false); // one right-side panel at a time, same as Sources vs Exec today
    setSourcesPanelOpen(false);
  };

  // Opens /agent/events/{executionId} BEFORE the actual /api/chat or
  // /export/pdf request is sent, so events published during that request
  // are actually caught live instead of arriving after the fact.
  // Returns a Promise that resolves once the SSE connection is actually
  // open (EventSource.onopen) — the server's /agent/events/{id} handler
  // has by then already registered the subscriber on the EventBus
  // (bus.subscribe() runs synchronously before the StreamingResponse is
  // returned, so headers can't reach the browser before it). Callers
  // MUST await this before firing the actual /api/chat or
  // /export/pdf request — otherwise, on a fast query, the whole backend
  // workflow can finish and publish all its events before the SSE
  // subscriber is registered, and every event is lost (EventBus has no
  // replay/history for late subscribers). A short timeout fallback
  // prevents hanging forever if onopen never fires for some reason.
  const subscribeToExecution = useCallback((executionId) => {
    if (execEventSourceRef.current) { execEventSourceRef.current.close(); }
    setExecNodes({});
    setExecExecutionId(executionId);
    setExecStatus("connecting");
    setExecError(null);
    setExecCodeBlocks([]);
    setExecArtifact(null);

    const es = new EventSource(`/agent/events/${executionId}`);
    execEventSourceRef.current = es;

    const opened = new Promise(resolve => {
      let done = false;
      es.onopen = () => { if (!done) { done = true; setExecStatus("running"); resolve(); } };
      setTimeout(() => { if (!done) { done = true; resolve(); } }, 1500); // fallback — don't hang forever
    });

    es.onmessage = (msg) => {
      let evt;
      try { evt = JSON.parse(msg.data); } catch { return; }

      if (evt.type === "agent.start") {
        setExecNodes(prev => ({
          ...prev,
          [evt.agent_id]: {
            agentId: evt.agent_id,
            // NOTE: agent_box.py's own event shape stores the parent
            // AGENT's id under "parent_execution_id" — not the workflow's
            // execution_id (that's the separate top-level evt.execution_id
            // field, which we already know client-side).
            parentAgentId: evt.parent_execution_id || null,
            name: evt.agent_name,
            status: "running",
            durationMs: null,
            retryCount: 0,
            tools: evt.tools || [],
            inputSummary: evt.input_summary || null,
            outputSummary: null,
            error: null,
            startedAt: evt.timestamp || Date.now() / 1000,
          },
        }));
      } else if (evt.type === "agent.end") {
        setExecNodes(prev => {
          const existing = prev[evt.agent_id];
          if (!existing) return prev;
          return {
            ...prev,
            [evt.agent_id]: {
              ...existing,
              status: evt.status === "failed" ? "failed" : "completed",
              durationMs: evt.duration_ms,
              outputSummary: evt.output_summary || null,
            },
          };
        });
      } else if (evt.type === "agent.error") {
        setExecNodes(prev => {
          const existing = prev[evt.agent_id];
          if (!existing) return prev;
          return { ...prev, [evt.agent_id]: { ...existing, status: "retrying", error: evt.error || null, retryCount: evt.retry_count || 0 } };
        });
      } else if (evt.type === "agent.retry") {
        setExecNodes(prev => {
          const existing = prev[evt.agent_id];
          if (!existing) return prev;
          return { ...prev, [evt.agent_id]: { ...existing, retryCount: evt.attempt ? evt.attempt - 1 : (existing.retryCount + 1) } };
        });
      } else if (evt.type === "code.block") {
        // Real source code narrated by agent_harness/code_narration.py
        // right before a render/chart/compose handler runs — this is
        // what powers the "Analyzing ▾ [Python]" block inline in chat.
        const meta = evt.meta || {};
        setExecCodeBlocks(prev => [...prev, { label: meta.label, code: meta.code }]);
      } else if (evt.type === "artifact.preview") {
        // Fired by dynamic_workflow.py right after artifact_store's
        // register_artifact() — powers the document card in chat.
        const meta = evt.meta || {};
        setExecArtifact({
          executionId: meta.execution_id || executionId,
          filename: meta.filename,
          fileType: meta.file_type,
        });
      } else if (evt.type === "execution.error") {
        setExecStatus("error");
        setExecError((evt.meta && evt.meta.error) || "Execution failed");
      } else if (evt.type === "completed") {
        setExecStatus("completed");
        es.close();
      }
    };

    es.onerror = () => {
      // Connection dropped (e.g. server restarted) — stop trying rather
      // than spamming reconnects against a request that already finished.
      es.close();
    };

    return opened;
  }, []);

  useEffect(() => () => { if (execEventSourceRef.current) execEventSourceRef.current.close(); }, []);
  const openSourcesPanel = (sources, label) => {
    setSourcesPanelSources(sources || []);
    setSourcesPanelLabel(label ? label.slice(0, 100) : "");
    setSourcesPanelOpen(true);
    setDocPanelOpen(false);
  };

  // ── Voice input (mic) — Urdu/English speech via Web Speech API ────────
  const [recording, setRecording] = useState(false);
  const [micLang, setMicLang]     = useState(() => localStorage.getItem("agribot_mic_lang") || "en-US");
  const recognitionRef = useRef(null);
  const toggleMic = (langOverride) => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) { alert("Voice input isn't supported in this browser. Try Chrome or Edge."); return; }
    if (recording) { recognitionRef.current?.stop(); return; }
    const recog = new SpeechRecognition();
    recog.lang = langOverride || micLang;
    recog.interimResults = true;
    recog.continuous = false;
    recog.onresult = (e) => {
      let transcript = "";
      for (let i = 0; i < e.results.length; i++) transcript += e.results[i][0].transcript;
      setInput(transcript);
    };
    recog.onerror = () => setRecording(false);
    recog.onend   = () => setRecording(false);
    recognitionRef.current = recog;
    recog.start();
    setRecording(true);
  };
  const toggleMicLang = () => {
    const next = micLang === "en-US" ? "ur-PK" : "en-US";
    setMicLang(next);
    localStorage.setItem("agribot_mic_lang", next);
  };

  const chatRef      = useRef(null);
  const textareaRef  = useRef(null);
  const fileInputRef = useRef(null);
  const [plusMenuOpen, setPlusMenuOpen] = useState(false);
  const plusMenuRef = useRef(null);
  useEffect(() => {
    if (!plusMenuOpen) return;
    const onClickOutside = (e) => { if (plusMenuRef.current && !plusMenuRef.current.contains(e.target)) setPlusMenuOpen(false); };
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [plusMenuOpen]);

  const authHdr = () => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : { "Content-Type": "application/json" };

  // ── Auto-scroll ───────────────────────────────────────────────────
  useEffect(() => { if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight; }, [msgCache, activeSession, loading]);

  // ── Poll /api/status ──────────────────────────────────────────────
  useEffect(() => {
    const f = () => fetch("/api/status").then(r => r.json()).then(d => { setStatusData(d); setChunkCount(d.chunk_count || 0); }).catch(() => {});
    f(); const id = setInterval(f, 10000); return () => clearInterval(id);
  }, []);

  // ── Load sessions ─────────────────────────────────────────────────
  const fetchSessions = useCallback(() => {
    fetch("/api/sessions", { headers: authHdr() }).then(r => r.json()).then(d => setApiSessions(d.sessions || [])).catch(() => {});
  }, [token]);
  useEffect(() => { fetchSessions(); }, [fetchSessions]);

  // ── Session helpers ───────────────────────────────────────────────
  const openNewChat = (projectId = null) => {
    const sessionId = crypto.randomUUID();
    const proj = projectId ? projects.find(p => p.id === projectId) : null;
    const title = proj ? `${proj.emoji} New chat` : "New chat";
    setActiveSession({ sessionId, projectId, title });
    setTrace(null); setInput(""); setUploadedFiles([]);
    if (projectId) {
      saveProjects(projects.map(p => p.id !== projectId ? p : { ...p, sessions: [...(p.sessions || []), { sessionId, title: "New chat" }] }));
    }
  };

  // If mounted from Dashboard.jsx's "New chat" / "New project" boxes,
  // auto-trigger the corresponding action once on mount.
  useEffect(() => {
    if (initialAction === "newChat") openNewChat(null);
    else if (initialAction === "newProject") setShowNewProj(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const openSession = (sessionId, projectId = null) => {    const apiS = apiSessions.find(s => s.session_id === sessionId);
    const title = apiS?.title || apiS?.preview || "Chat";
    const proj = projectId ? projects.find(p => p.id === projectId) : null;
    setActiveSession({ sessionId, projectId, title: proj ? `${proj.emoji} ${title}` : title });
    setTrace(null); setInput(""); setUploadedFiles([]);
    if (!msgCache[sessionId]) {
      fetch(`/api/sessions/${sessionId}`, { headers: authHdr() }).then(r => r.json()).then(d => {
        const msgs = (d.messages || []).map(m => ({ role: m.role, content: m.content, ts: m.ts || nowTs(), sourceType: m.source_type, sources: m.sources || [] }));
        setMsgCache(prev => ({ ...prev, [sessionId]: msgs }));
      }).catch(() => {});
    }
  };

  const deleteSession = async (sid, e) => {
    e?.stopPropagation();
    if (!confirm("Delete this conversation?")) return;
    await fetch(`/api/sessions/${sid}`, { method: "DELETE", headers: authHdr() }).catch(() => {});
    setMsgCache(prev => { const n = { ...prev }; delete n[sid]; return n; });
    if (activeSession?.sessionId === sid) setActiveSession(null);
    fetchSessions();
  };

  // ── Send message ──────────────────────────────────────────────────
  const sendMessage = async (text) => {
    const q = (text || input).trim();
    if (!q || loading || !activeSession) return;
    setInput("");
    const userMsg = {
      role: "user", content: q, ts: nowTs(),
      attachedFiles: uploadedFiles.map(f => ({ name: f.name })),
      scopedToUpload: uploadedFiles.length > 0 && scopeToUpload,
    };
    const sid = activeSession.sessionId;
    setMsgCache(prev => ({ ...prev, [sid]: [...(prev[sid] || []), userMsg] }));
    setLoading(true); setTrace(null);

    // Generate the execution_id CLIENT-SIDE and subscribe to its SSE
    // stream before the request goes out, so the agent tree is actually
    // live instead of only appearing after /api/chat's blocking call
    // returns. Falls back gracefully (no live tree, chat still works) if
    // the browser lacks crypto.randomUUID (very old browsers only).
    const clientExecutionId = (typeof crypto !== "undefined" && crypto.randomUUID) ? crypto.randomUUID().replace(/-/g, "") : null;
    if (clientExecutionId) { await subscribeToExecution(clientExecutionId); setExecPanelOpen(true); }

    // Route document-generation requests to the Dynamic Harness endpoint
    // instead of the fixed /api/chat pipeline — a plain heuristic on the
    // query text, not a UI toggle, so nothing changes for ordinary
    // questions (Section 29: additive, don't alter existing behavior).
    // See api_server.py's /api/chat/dynamic for what runs on this path.
    const isDocRequest = /\b(pdf|docx|document|report|generate a file|word doc)\b/i.test(q);
    const endpoint = isDocRequest ? "/api/chat/dynamic" : "/api/chat";

    try {
      const res = await fetch(endpoint, {
        method: "POST", headers: authHdr(),
        body: JSON.stringify({ session_id: sid, query: q, force_web: webSearchOn, execution_id: clientExecutionId, scope_to_upload: uploadedFiles.length > 0 && scopeToUpload }),
      });
      const data = await res.json();
      // FIX: a non-2xx response (e.g. the dynamic harness returning 503
      // before it ever creates agent state) still parses as JSON, so this
      // was never being checked — it silently fell through to the generic
      // "No response." with no clue what actually failed. Surface
      // data.response (routes in this file always include one, even on
      // error) or data.detail (FastAPI's default HTTPException shape) if
      // present, before giving up and showing the generic fallback.
      if (!res.ok && !data.response) {
        throw new Error(data.detail || data.error_detail || `Request failed (${res.status})`);
      }
      // FIX: this used to build `artifact` ONLY from execArtifact, which
      // is populated live by the SSE "artifact.preview" event handler.
      // That event arrives on a SEPARATE connection from this fetch's
      // response — a race, not a guarantee. data.artifacts is now
      // included directly in /api/chat/dynamic's response body (see the
      // api_server.py fix), so it's authoritative and race-free: prefer
      // it, and only fall back to the live SSE value if the response
      // body's artifacts array is somehow empty.
      const responseArtifact = (data.artifacts && data.artifacts.length > 0)
        ? (() => {
            const a = data.artifacts[data.artifacts.length - 1];
            return { executionId: clientExecutionId, filename: a.ref, fileType: a.type || "pdf" };
          })()
        : null;
      const botMsg = {
        role: "assistant", content: data.response || "No response.", ts: nowTs(),
        sourceType: data.source_type, mcpTool: data.mcp_tool, sources: data.sources || [],
        // Snapshot this execution's code.block / artifact.preview events
        // (accumulated live via SSE above) onto the message they belong
        // to, so they render inside THIS bubble permanently, not just
        // while this was the "current" execution.
        codeBlocks: isDocRequest ? execCodeBlocks : [],
        artifact: isDocRequest ? (responseArtifact || execArtifact || null) : null,
      };
      setMsgCache(prev => ({ ...prev, [sid]: [...(prev[sid] || []), botMsg] }));
      if (data.trace) setTrace(data.trace);
      // Auto-title
      const msgs = msgCache[sid] || [];
      if (msgs.filter(m => m.role === "user").length === 0) {
        const autoTitle = q.slice(0, 42) + (q.length > 42 ? "…" : "");
        setActiveSession(prev => ({ ...prev, title: autoTitle }));
      }
    } catch (err) {
      setMsgCache(prev => ({ ...prev, [sid]: [...(prev[sid] || []), { role: "assistant", content: `❌ Backend error: ${err.message}`, ts: nowTs() }] }));
      setExecStatus("error"); setExecError(err.message);
    } finally {
      setLoading(false); fetchSessions();
    }
  };

  // ── Upload ────────────────────────────────────────────────────────
  const uploadFile = async (file) => {
    if (!activeSession) { alert("Open or create a chat first."); return; }
    const ext = "." + file.name.split(".").pop().toLowerCase();
    if (![".pdf", ".txt", ".docx"].includes(ext)) { alert("Allowed: PDF, TXT, DOCX"); return; }
    setUploadStatus("uploading"); setUploadedFiles([]);
    try {
      const listRes = await fetch("/api/uploads"); // get existing
      if (listRes.ok) { const ld = await listRes.json(); await Promise.all((ld.uploads || []).map(u => fetch(`/api/uploads/${u.file_id}`, { method: "DELETE" }))); }
      const fd = new FormData(); fd.append("file", file); fd.append("session_id", activeSession.sessionId);
      const res = await fetch("/api/upload", { method: "POST", body: fd });
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || `Upload failed (${res.status})`); }
      const d = await res.json();
      setUploadedFiles([{ name: file.name, fileId: d.file_id }]);
      setUploadStatus("done"); setTimeout(() => setUploadStatus(null), 3500);
    } catch (err) { setUploadStatus("error"); alert(`Upload failed: ${err.message}`); setTimeout(() => setUploadStatus(null), 4000); }
  };

  // ── Export PDF ────────────────────────────────────────────────────
  const exportPDF = async () => {
    if (!activeSession) return;
    const clientExecutionId = (typeof crypto !== "undefined" && crypto.randomUUID) ? crypto.randomUUID().replace(/-/g, "") : null;
    if (clientExecutionId) { await subscribeToExecution(clientExecutionId); setExecPanelOpen(true); }
    try {
      const url = `/api/sessions/${activeSession.sessionId}/export/pdf` + (clientExecutionId ? `?execution_id=${clientExecutionId}` : "");
      const res = await fetch(url, { headers: authHdr() });
      if (!res.ok) throw new Error(`Export failed (${res.status})`);
      const blob = await res.blob();
      const m = res.headers.get("Content-Disposition")?.match(/filename="([^"]+)"/);
      const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = m ? m[1] : "agribot_export.pdf";
      document.body.appendChild(a); a.click(); a.remove();
    } catch (err) {
      alert(`PDF export: ${err.message}`);
      setExecStatus("error"); setExecError(err.message);
    }
  };

  // ── Project CRUD ──────────────────────────────────────────────────
  const createProject = () => {
    if (!newProjName.trim()) return;
    const proj = { id: "p" + Date.now(), name: newProjName.trim(), emoji: newProjEmoji, sessions: [] };
    saveProjects([...projects, proj]);
    setNewProjName(""); setNewProjEmoji("🌱"); setShowNewProj(false);
    setExpandedPjs(prev => new Set([...prev, proj.id]));
  };

  const deleteProject = (id) => {
    if (!confirm("Delete this project and all its chats?")) return;
    saveProjects(projects.filter(p => p.id !== id));
    if (activeSession?.projectId === id) setActiveSession(null);
  };

  // ── Sidebar filtering ─────────────────────────────────────────────
  const sq = sideSearch.toLowerCase();
  const projSessionIds = new Set(projects.flatMap(p => (p.sessions || []).map(s => s.sessionId)));
  const recentSessions = apiSessions.filter(s => !projSessionIds.has(s.session_id) && (!sq || (s.title || s.preview || "").toLowerCase().includes(sq)));
  const filteredProjs  = projects.filter(p => !sq || p.name.toLowerCase().includes(sq));
  const currentMsgs    = (activeSession && msgCache[activeSession.sessionId]) || [];

  const sideWidth = sideOpen ? 260 : 0;

  // ═════════════════════════════════════════════════════════════════
  //  RENDER
  // ═════════════════════════════════════════════════════════════════
  return (
    <>
      <style>{`
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: ${C.bg}; overflow: hidden; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-thumb { background: ${C.border}; border-radius: 3px; }
        @keyframes agriPulse { 0%,100%{opacity:.3;transform:scale(.85)} 50%{opacity:1;transform:scale(1.1)} }
        textarea { resize: none; }
      `}</style>

      <div style={{ display: "flex", height: "100vh", fontFamily: "'Inter','Segoe UI',system-ui,sans-serif", color: C.text, overflow: "hidden", background: C.bg }}>

        {/* ╔══════════════════════════════════════════════════════════╗
            ║  SIDEBAR                                                  ║
            ╚══════════════════════════════════════════════════════════╝ */}
        <div style={{ width: sideWidth, minWidth: sideWidth, background: C.surface, borderRight: `1px solid ${C.border}`, display: "flex", flexDirection: "column", transition: "width 0.22s ease, min-width 0.22s ease", overflow: "hidden", flexShrink: 0 }}>
          {sideOpen && (<>
            {/* Logo — click to go back to the Dashboard */}
            <div style={{ padding: "16px 14px 10px", flexShrink: 0 }}>
              <div onClick={onGoToDashboard} title="Go to Dashboard"
                style={{ display: "flex", alignItems: "center", gap: 9, marginBottom: 12, cursor: onGoToDashboard ? "pointer" : "default" }}>
                <img src={agribotIcon} alt="AgriBot" style={{ width: 26, height: 26, borderRadius: 7, flexShrink: 0 }} />
                <span style={{ fontSize: 16, fontWeight: 800, color: C.text, letterSpacing: "-0.02em" }}>AgriBot</span>
              </div>
              {/* Search */}
              <div style={{ display: "flex", alignItems: "center", gap: 6, background: C.inputBg, border: `1px solid ${C.border}`, borderRadius: 8, padding: "6px 10px" }}>
                <Icon d={I.search} size={13} stroke={C.textMute} />
                <input value={sideSearch} onChange={e => setSideSearch(e.target.value)} placeholder="Search chats…"
                  style={{ flex: 1, background: "transparent", border: "none", outline: "none", color: C.text, fontSize: 12, fontFamily: "inherit" }} />
              </div>
            </div>

            {/* New Chat button */}
            <div style={{ padding: "4px 10px 8px", flexShrink: 0 }}>
              <button onClick={() => openNewChat(null)}
                style={{ width: "100%", display: "flex", alignItems: "center", gap: 8, padding: "8px 12px", background: C.accent, border: "none", borderRadius: 9, color: "#fff", fontSize: 13, fontWeight: 700, cursor: "pointer", fontFamily: "inherit", transition: "opacity 0.15s" }}
                onMouseEnter={e => e.currentTarget.style.opacity = "0.88"}
                onMouseLeave={e => e.currentTarget.style.opacity = "1"}>
                <Icon d={I.plus} size={15} stroke="#fff" /> New chat
              </button>
            </div>

            <div style={{ flex: 1, overflowY: "auto", padding: "0 6px 8px" }}>
              {/* Recent chats */}
              {recentSessions.length > 0 && (<>
                <div style={{ padding: "8px 8px 4px", fontSize: 10, fontWeight: 700, color: C.textMute, textTransform: "uppercase", letterSpacing: "0.08em" }}>Recent Chats</div>
                {recentSessions.map(s => (
                  <SideItem key={s.session_id} label={s.title || s.preview || "Untitled"} icon={I.chat}
                    active={activeSession?.sessionId === s.session_id} C={C}
                    onClick={() => openSession(s.session_id, null)}
                    onDelete={e => deleteSession(s.session_id, e)} />
                ))}
              </>)}

              {/* Projects */}
              <div style={{ padding: "12px 8px 4px", fontSize: 10, fontWeight: 700, color: C.textMute, textTransform: "uppercase", letterSpacing: "0.08em", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span>Projects</span>
                <button onClick={() => setShowNewProj(true)} style={{ background: "none", border: "none", cursor: "pointer", padding: 2, color: C.accent }}>
                  <Icon d={I.plus} size={13} stroke={C.accent} />
                </button>
              </div>
              {filteredProjs.map(proj => {
                const isExp = expandedPjs.has(proj.id);
                const isAct = activeSession?.projectId === proj.id;
                return (
                  <div key={proj.id}>
                    <div style={{ display: "flex", alignItems: "center", margin: "1px 0", borderRadius: 8, background: isAct ? C.accentBg : "transparent", overflow: "hidden" }}>
                      <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 7, padding: "7px 8px 7px 10px", cursor: "pointer", color: isAct ? C.accent : C.textSub, fontSize: 13, fontWeight: isAct ? 600 : 400, overflow: "hidden" }}
                        onClick={() => { setExpandedPjs(prev => new Set([...prev, proj.id])); }}>
                        <span style={{ fontSize: 15, flexShrink: 0 }}>{proj.emoji}</span>
                        <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{proj.name}</span>
                      </div>
                      <button onClick={() => setExpandedPjs(prev => { const s = new Set(prev); s.has(proj.id) ? s.delete(proj.id) : s.add(proj.id); return s; })} style={{ background: "none", border: "none", cursor: "pointer", padding: "7px 8px", color: C.textMute }}>
                        <Icon d={isExp ? I.chevD : I.chevR} size={12} stroke={C.textMute} />
                      </button>
                      <button onClick={() => deleteProject(proj.id)} style={{ background: "none", border: "none", cursor: "pointer", padding: "7px 6px", color: C.textMute, opacity: 0.5 }}
                        onMouseEnter={e => e.currentTarget.style.opacity = "1"}
                        onMouseLeave={e => e.currentTarget.style.opacity = "0.5"}>
                        <Icon d={I.trash} size={11} stroke={C.danger} />
                      </button>
                    </div>
                    {isExp && (
                      <div style={{ paddingLeft: 8 }}>
                        {(proj.sessions || []).map(sess => {
                          const apiS = apiSessions.find(a => a.session_id === sess.sessionId);
                          return <SideItem key={sess.sessionId} label={apiS?.title || apiS?.preview || sess.title || "Chat"} icon={I.chat} indent active={activeSession?.sessionId === sess.sessionId} C={C} onClick={() => openSession(sess.sessionId, proj.id)} onDelete={e => deleteSession(sess.sessionId, e)} />;
                        })}
                        <div onClick={() => openNewChat(proj.id)}
                          style={{ display: "flex", alignItems: "center", gap: 6, padding: "5px 8px 5px 20px", cursor: "pointer", color: C.textMute, fontSize: 12, borderRadius: 7 }}
                          onMouseEnter={e => e.currentTarget.style.color = C.accent}
                          onMouseLeave={e => e.currentTarget.style.color = C.textMute}>
                          <Icon d={I.plus} size={12} stroke="currentColor" /> New chat
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}

              {/* Knowledge base links */}
              <div style={{ padding: "12px 8px 4px", fontSize: 10, fontWeight: 700, color: C.textMute, textTransform: "uppercase", letterSpacing: "0.08em" }}>Knowledge Base</div>
              {[["PARC Report 2023-24", "PARC Annual Report 2023-24_compressed.pdf"], ["FAO Crop Guidelines", "i5550e.pdf"], ["Punjab Agri Rules", "PbAgriDeptExtenAdapReseWing_SR_2007_20070612.pdf"]].map(([label, file]) => (
                <div key={file} onClick={() => window.open(`/api/pdf/${encodeURIComponent(file)}`, "_blank")}
                  style={{ display: "flex", alignItems: "center", gap: 7, padding: "5px 8px 5px 12px", cursor: "pointer", color: C.textMute, fontSize: 12, borderRadius: 7 }}
                  onMouseEnter={e => e.currentTarget.style.color = C.accent}
                  onMouseLeave={e => e.currentTarget.style.color = C.textMute}>
                  <Icon d={I.book} size={13} stroke="currentColor" />
                  <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{label}</span>
                  <span style={{ fontSize: 10, color: C.accentDim }}>↗</span>
                </div>
              ))}
            </div>

            {/* User footer */}
            <div style={{ padding: "8px 10px", borderTop: `1px solid ${C.border}`, position: "relative" }}>
              {userMenuOpen && (
                <div style={{ position: "absolute", bottom: "100%", left: 10, right: 10, background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, boxShadow: C.shadow, overflow: "hidden", zIndex: 100 }}>
                  {[
                    ["Settings", I.settings, () => { setShowSettings(true); setUserMenuOpen(false); }],
                    ["Sign out",  I.logout,   () => { setUserMenuOpen(false); onLogout?.(); }],
                  ].map(([label, ic, action]) => (
                    <button key={label} onClick={action}
                      style={{ width: "100%", display: "flex", alignItems: "center", gap: 9, padding: "10px 14px", background: "none", border: "none", cursor: "pointer", color: C.textSub, fontSize: 13, fontFamily: "inherit", textAlign: "left", transition: "background 0.12s" }}
                      onMouseEnter={e => e.currentTarget.style.background = C.surface2}
                      onMouseLeave={e => e.currentTarget.style.background = "none"}>
                      <Icon d={ic} size={15} stroke={C.textSub} />{label}
                    </button>
                  ))}
                </div>
              )}
              <button onClick={() => setUserMenuOpen(u => !u)}
                style={{ width: "100%", display: "flex", alignItems: "center", gap: 9, padding: "8px 10px", background: userMenuOpen ? C.accentBg : "transparent", border: `1px solid ${userMenuOpen ? C.accent : "transparent"}`, borderRadius: 10, cursor: "pointer", transition: "all 0.15s", fontFamily: "inherit" }}>
                <div style={{ width: 30, height: 30, borderRadius: "50%", background: C.accentBg, border: `1.5px solid ${C.accent}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 700, color: C.accent, flexShrink: 0 }}>
                  {(username || "U")[0].toUpperCase()}
                </div>
                <span style={{ flex: 1, fontSize: 13, color: C.textSub, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", textAlign: "left" }}>{username}</span>
                <Icon d={I.chevD} size={12} stroke={C.textMute} />
              </button>
            </div>
          </>)}
        </div>

        {/* ╔══════════════════════════════════════════════════════════╗
            ║  MAIN CONTENT                                             ║
            ╚══════════════════════════════════════════════════════════╝ */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>

          {/* Header */}
          <div style={{ height: 54, background: C.surface, borderBottom: `1px solid ${C.border}`, display: "flex", alignItems: "center", gap: 10, padding: "0 16px", flexShrink: 0 }}>
            {/* Sidebar toggle */}
            <button onClick={() => setSideOpen(o => !o)}
              style={{ background: "none", border: "none", cursor: "pointer", padding: "6px 8px", borderRadius: 7, display: "flex", alignItems: "center" }}
              onMouseEnter={e => e.currentTarget.style.background = C.surface2}
              onMouseLeave={e => e.currentTarget.style.background = "none"}>
              <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke={C.textSub} strokeWidth={1.8} strokeLinecap="round">
                <line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" />
              </svg>
            </button>

            <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 8, overflow: "hidden" }}>
              {activeSession ? (
                <>
                  <span style={{ fontSize: 14, fontWeight: 600, color: C.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{activeSession.title}</span>
                  {activeSession.projectId && <span style={{ fontSize: 11, color: C.textMute, flexShrink: 0 }}>· {projects.find(p => p.id === activeSession.projectId)?.name}</span>}
                </>
              ) : (
                <span style={{ fontSize: 15, fontWeight: 700, color: C.text }}>AgriBot</span>
              )}
            </div>

            {/* Header controls */}
            <div style={{ display: "flex", alignItems: "center", gap: 6, flexShrink: 0 }}>
              {/* Dashboard button */}
              {onGoToDashboard && (
                <button onClick={onGoToDashboard} title="Go to Dashboard"
                  style={{ display: "flex", alignItems: "center", gap: 6, padding: "6px 12px", borderRadius: 8, border: `1px solid ${C.border}`, background: "transparent", cursor: "pointer", fontSize: 12.5, fontWeight: 600, color: C.textSub, fontFamily: "inherit" }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = C.accent; e.currentTarget.style.color = C.text; }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.color = C.textSub; }}>
                  <Icon d={I.grid || I.folder} size={13} stroke="currentColor" />
                  Dashboard
                </button>
              )}

              {/* Web search status badge — read-only; toggle now lives in the
                  "+" dropdown next to the composer, see below */}
              {webSearchOn && (
                <div title="Web search is ON — toggle it from the + menu next to the composer"
                  style={{ display: "flex", alignItems: "center", gap: 5, padding: "4px 10px", borderRadius: 8, border: `1px solid ${C.accent}`, background: C.accentBg, fontSize: 12, fontWeight: 600, color: C.accent }}>
                  <Icon d={I.globe} size={13} stroke={C.accent} />
                  Web ON
                </div>
              )}

              {/* Sources panel toggle */}
              <button onClick={() => setSourcesPanelOpen(o => !o)} title={sourcesPanelOpen ? "Close sources panel" : "Open sources panel"}
                style={{ display: "flex", alignItems: "center", justifyContent: "center", width: 34, height: 34, borderRadius: 8, border: `1px solid ${sourcesPanelOpen ? C.accent : C.border}`, background: sourcesPanelOpen ? C.accentBg : "transparent", cursor: "pointer" }}
                onMouseEnter={e => e.currentTarget.style.borderColor = C.accent}
                onMouseLeave={e => e.currentTarget.style.borderColor = sourcesPanelOpen ? C.accent : C.border}>
                <Icon d={I.sources} size={15} stroke={sourcesPanelOpen ? C.accent : C.textSub} />
              </button>

              {/* Agent Execution panel toggle */}
              <button onClick={() => setExecPanelOpen(o => !o)} title={execPanelOpen ? "Close agent execution panel" : "Open agent execution panel"}
                style={{ display: "flex", alignItems: "center", justifyContent: "center", width: 34, height: 34, borderRadius: 8, border: `1px solid ${execPanelOpen ? C.accent : C.border}`, background: execPanelOpen ? C.accentBg : "transparent", cursor: "pointer", position: "relative" }}
                onMouseEnter={e => e.currentTarget.style.borderColor = C.accent}
                onMouseLeave={e => e.currentTarget.style.borderColor = execPanelOpen ? C.accent : C.border}>
                <Icon d={I.trace} size={15} stroke={execPanelOpen ? C.accent : C.textSub} />
                {execStatus === "running" && (
                  <span style={{ position: "absolute", top: 3, right: 3, width: 7, height: 7, borderRadius: "50%", background: C.accent, animation: "agriPulse 1.1s ease-in-out infinite" }} />
                )}
              </button>
            </div>
          </div>

          {/* Chat area */}
          <div ref={chatRef} style={{ flex: 1, overflowY: "auto", padding: "24px 20px", display: "flex", flexDirection: "column", gap: 18 }}>
            {!activeSession ? (
              <Welcome C={C} onSend={(p) => { openNewChat(null); setTimeout(() => sendMessage(p), 80); }} username={username} />
            ) : currentMsgs.length === 0 ? (
              <Welcome C={C} onSend={sendMessage} username={username} />
            ) : currentMsgs.map((m, i) => (
              <Message key={i} msg={m} C={C} token={token}
                msgId={`${activeSession}-${i}`}
                onShowSources={openSourcesPanel}
                onOpenDocument={openDocumentViewer}
                onExportPDF={m.role === "assistant" ? exportPDF : null}
                onRegenerate={m.role === "assistant" ? () => { const prev = [...currentMsgs].reverse().find((x, j) => j > currentMsgs.length - 1 - i && x.role === "user"); if (prev) sendMessage(prev.content); } : null} />
            ))}
            {loading && <TypingDots C={C} />}
          </div>

          {/* Input area */}
          <div style={{ padding: "10px 16px 14px", borderTop: `1px solid ${C.border}`, background: C.surface, flexShrink: 0 }}>
            {/* Upload status */}
            {uploadStatus && (
              <div style={{ marginBottom: 8, padding: "5px 12px", borderRadius: 8, fontSize: 12, display: "flex", alignItems: "center", gap: 6, background: uploadStatus === "done" ? C.accentBg : uploadStatus === "error" ? C.dangerBg : C.amberBg, border: `1px solid ${uploadStatus === "done" ? C.accentDim : uploadStatus === "error" ? C.danger : C.amberDim}`, color: uploadStatus === "done" ? C.accent : uploadStatus === "error" ? "#e8938a" : C.amber }}>
                {uploadStatus === "uploading" && "⏳ Uploading & indexing…"}
                {uploadStatus === "done"      && "✓ Document ready — ask about it now"}
                {uploadStatus === "error"     && "✗ Upload failed"}
              </div>
            )}
            {/* File attachment cards — ChatGPT-style: icon square + filename + type */}
            {uploadedFiles.length > 0 && (
              <div style={{ marginBottom: 10 }}>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  {uploadedFiles.map((f, i) => (
                    <div key={f.fileId}
                      style={{
                        display: "flex", alignItems: "center", gap: 10,
                        background: C.surface, border: `1px solid ${C.border}`,
                        borderRadius: 12, padding: "9px 14px 9px 10px",
                        maxWidth: 260, boxShadow: themeMode === "light" ? "0 1px 3px rgba(0,0,0,0.06)" : "0 1px 3px rgba(0,0,0,0.3)",
                        position: "relative",
                      }}>
                      <div style={{
                        width: 34, height: 34, borderRadius: 8, background: "rgba(224,54,42,0.1)",
                        display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
                      }}>
                        <Icon d={I.file} size={16} stroke="#e0362a" />
                      </div>
                      <div style={{ minWidth: 0 }}>
                        <div style={{
                          fontSize: 12.5, fontWeight: 700, color: C.text,
                          whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
                        }} title={f.name}>
                          {f.name}
                        </div>
                        <div style={{ fontSize: 10.5, color: C.textMute, marginTop: 1 }}>PDF</div>
                      </div>
                      <button
                        onClick={() => setUploadedFiles(prev => prev.filter((_, j) => j !== i))}
                        title="Remove"
                        style={{
                          position: "absolute", top: -6, right: -6, width: 18, height: 18,
                          borderRadius: "50%", background: C.textMute, color: C.surface,
                          border: `2px solid ${C.surface}`, cursor: "pointer", fontSize: 11,
                          lineHeight: 1, display: "flex", alignItems: "center", justifyContent: "center", padding: 0,
                        }}>
                        ×
                      </button>
                    </div>
                  ))}
                </div>
                <button onClick={() => setScopeToUpload(v => !v)}
                  title={scopeToUpload ? "Answers are scoped to this document only — click to also use the general knowledge base" : "Answers blend this document with the general knowledge base — click to scope to this document only"}
                  style={{ display: "inline-flex", alignItems: "center", gap: 5, marginTop: 7, padding: "2px 10px", borderRadius: 20, border: `1px solid ${scopeToUpload ? C.accent : C.border}`, background: scopeToUpload ? C.accentBg : "transparent", cursor: "pointer", fontSize: 11, fontWeight: 600, color: scopeToUpload ? C.accent : C.textMute, fontFamily: "inherit" }}>
                  <span style={{ width: 6, height: 6, borderRadius: "50%", background: scopeToUpload ? C.accent : C.textMute, flexShrink: 0 }} />
                  {scopeToUpload ? "This document only" : "Document + knowledge base"}
                </button>
              </div>
            )}
            {!activeSession && <div style={{ fontSize: 12, color: C.textMute, textAlign: "center", marginBottom: 8 }}>Click <strong style={{ color: C.accent }}>New chat</strong> or select a conversation</div>}
            <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
              <input ref={fileInputRef} type="file" accept=".pdf,.txt,.docx" style={{ display: "none" }} onChange={e => { if (e.target.files[0]) { uploadFile(e.target.files[0]); e.target.value = ""; } }} />

              {/* "+" menu — Upload / Voice input (EN/UR) / Web search, all in one place */}
              <div ref={plusMenuRef} style={{ position: "relative", flexShrink: 0, alignSelf: "flex-end" }}>
                {recording ? (
                  <button onClick={() => activeSession && toggleMic()} title="Stop recording"
                    style={{ width: 40, height: 40, borderRadius: 10, border: `1px solid ${C.danger}`, background: C.dangerBg, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", position: "relative" }}>
                    <Icon d={I.mic} size={16} stroke={C.danger} />
                    <span style={{ position: "absolute", top: -3, right: -3, width: 9, height: 9, borderRadius: "50%", background: C.danger, animation: "agriPulse 1.1s ease-in-out infinite" }} />
                  </button>
                ) : (
                  <button onClick={() => activeSession && setPlusMenuOpen(o => !o)} disabled={!activeSession} title="Attach, speak, or search the web"
                    style={{ width: 40, height: 40, borderRadius: 10, border: `1px solid ${plusMenuOpen ? C.accent : C.border}`, background: plusMenuOpen ? C.accentBg : C.inputBg, cursor: !activeSession ? "not-allowed" : "pointer", display: "flex", alignItems: "center", justifyContent: "center", opacity: !activeSession ? 0.4 : 1, transition: "all 0.15s" }}>
                    <Icon d={I.plus} size={18} stroke={plusMenuOpen ? C.accent : C.textSub} />
                  </button>
                )}

                {plusMenuOpen && (
                  <div style={{
                    position: "absolute", bottom: "calc(100% + 8px)", left: 0, width: 240,
                    background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12,
                    boxShadow: "0 10px 30px rgba(0,0,0,0.25)", padding: 6, zIndex: 20,
                  }}>
                    <button onClick={() => { fileInputRef.current?.click(); setPlusMenuOpen(false); }}
                      style={{ width: "100%", display: "flex", alignItems: "center", gap: 10, padding: "9px 10px", borderRadius: 8, border: "none", background: "transparent", cursor: "pointer", fontFamily: "inherit", textAlign: "left" }}
                      onMouseEnter={e => e.currentTarget.style.background = C.surface2}
                      onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                      <Icon d={I.upload} size={15} stroke={C.textSub} />
                      <span style={{ fontSize: 13, color: C.text }}>Upload PDF / TXT / DOCX</span>
                    </button>

                    <button onClick={() => { setMicLang("en-US"); localStorage.setItem("agribot_mic_lang", "en-US"); setPlusMenuOpen(false); toggleMic("en-US"); }}
                      style={{ width: "100%", display: "flex", alignItems: "center", gap: 10, padding: "9px 10px", borderRadius: 8, border: "none", background: "transparent", cursor: "pointer", fontFamily: "inherit", textAlign: "left" }}
                      onMouseEnter={e => e.currentTarget.style.background = C.surface2}
                      onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                      <Icon d={I.mic} size={15} stroke={C.textSub} />
                      <span style={{ fontSize: 13, color: C.text }}>Voice input — English</span>
                    </button>

                    <button onClick={() => { setMicLang("ur-PK"); localStorage.setItem("agribot_mic_lang", "ur-PK"); setPlusMenuOpen(false); toggleMic("ur-PK"); }}
                      style={{ width: "100%", display: "flex", alignItems: "center", gap: 10, padding: "9px 10px", borderRadius: 8, border: "none", background: "transparent", cursor: "pointer", fontFamily: "inherit", textAlign: "left" }}
                      onMouseEnter={e => e.currentTarget.style.background = C.surface2}
                      onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                      <Icon d={I.mic} size={15} stroke={C.textSub} />
                      <span style={{ fontSize: 13, color: C.text }}>Voice input — Urdu</span>
                    </button>

                    <div style={{ height: 1, background: C.border, margin: "5px 4px" }} />

                    <button onClick={() => { setWebSearchOn(w => !w); setPlusMenuOpen(false); }}
                      style={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10, padding: "9px 10px", borderRadius: 8, border: "none", background: "transparent", cursor: "pointer", fontFamily: "inherit", textAlign: "left" }}
                      onMouseEnter={e => e.currentTarget.style.background = C.surface2}
                      onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                      <span style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <Icon d={I.globe} size={15} stroke={webSearchOn ? C.accent : C.textSub} />
                        <span style={{ fontSize: 13, color: C.text }}>Web search</span>
                      </span>
                      <span style={{
                        width: 32, height: 18, borderRadius: 10, background: webSearchOn ? C.accent : C.border,
                        position: "relative", transition: "background 0.15s", flexShrink: 0,
                      }}>
                        <span style={{ position: "absolute", top: 2, left: webSearchOn ? 16 : 2, width: 14, height: 14, borderRadius: "50%", background: "#fff", transition: "left 0.15s" }} />
                      </span>
                    </button>
                  </div>
                )}
              </div>

              {/* Textarea */}
              <div style={{ flex: 1, background: C.inputBg, border: `1px solid ${activeSession ? C.borderHi : C.border}`, borderRadius: 12, padding: "10px 14px" }}>
                <textarea ref={textareaRef} rows={2} value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
                  placeholder={uploadedFiles.length > 0 ? `Ask about ${uploadedFiles[0].name}…` : webSearchOn ? "Web search ON — ask anything (Tavily)…" : activeSession ? "Ask AgriBot… (Enter to send, Shift+Enter for newline)" : "Select or create a chat first"}
                  disabled={!activeSession}
                  style={{ width: "100%", background: "transparent", border: "none", outline: "none", color: C.text, fontSize: 14, fontFamily: "inherit", lineHeight: 1.55, minHeight: 44 }} />
              </div>
              {/* Send */}
              <button onClick={() => sendMessage()} disabled={loading || !input.trim() || !activeSession}
                style={{ width: 42, height: 42, borderRadius: 12, border: "none", background: (loading || !input.trim() || !activeSession) ? C.surface2 : C.accent, cursor: (loading || !input.trim() || !activeSession) ? "not-allowed" : "pointer", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, alignSelf: "flex-end", transition: "background 0.15s" }}>
                <Icon d={I.send} size={17} stroke={(loading || !input.trim() || !activeSession) ? C.textMute : "#fff"} />
              </button>
            </div>
            <div style={{ fontSize: 10, color: C.textMute, textAlign: "center", marginTop: 6 }}>
              AgriBot · Powered by Groq + ChromaDB + Tavily · Always verify important agricultural decisions
            </div>
          </div>
        </div>

        {/* Right-side clickable Sources panel */}
        <SourcesPanel
          open={sourcesPanelOpen}
          onClose={() => setSourcesPanelOpen(false)}
          sources={sourcesPanelSources}
          label={sourcesPanelLabel}
          C={C}
        />

        {/* Right-side live Agent Execution panel */}
        <AgentExecutionPanel
          open={execPanelOpen}
          onClose={() => setExecPanelOpen(false)}
          executionId={execExecutionId}
          nodes={execNodes}
          execStatus={execStatus}
          execError={execError}
          C={C}
        />

        {/* Right-side Document Viewer panel — opened from a DocumentCard
            in chat or from the Agent Execution panel's artifact. Same
            slide-open slot pattern as Sources/Agent Execution above;
            only one of the three is meaningfully open at once
            (see openDocumentViewer). */}
        <DocumentViewerPanel
          open={docPanelOpen}
          onClose={() => setDocPanelOpen(false)}
          executionId={docPanelData?.executionId}
          filename={docPanelData?.filename}
          fileType={docPanelData?.fileType}
          onViewAnalysis={setAnalysisExecId}
          C={C}
        />
      </div>

      {/* ── New Project Modal ── */}
      {showNewProj && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.65)", zIndex: 2000, display: "flex", alignItems: "center", justifyContent: "center" }} onClick={() => setShowNewProj(false)}>
          <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 16, padding: 28, width: 400, maxWidth: "90vw", boxShadow: C.shadow }} onClick={e => e.stopPropagation()}>
            <div style={{ fontSize: 16, fontWeight: 700, color: C.text, marginBottom: 20 }}>New Project</div>
            <div style={{ marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: C.textSub, marginBottom: 6, fontWeight: 600 }}>ICON</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {PROJ_EMOJIS.map(e => <button key={e} onClick={() => setNewProjEmoji(e)} style={{ fontSize: 18, padding: "4px 8px", borderRadius: 8, border: `1px solid ${newProjEmoji === e ? C.accent : C.border}`, background: newProjEmoji === e ? C.accentBg : C.surface2, cursor: "pointer", fontFamily: "inherit" }}>{e}</button>)}
              </div>
            </div>
            <div style={{ marginBottom: 20 }}>
              <div style={{ fontSize: 11, color: C.textSub, marginBottom: 6, fontWeight: 600 }}>PROJECT NAME</div>
              <input value={newProjName} onChange={e => setNewProjName(e.target.value)} placeholder="e.g. Wheat Disease Research"
                onKeyDown={e => e.key === "Enter" && createProject()}
                style={{ width: "100%", background: C.inputBg, border: `1px solid ${C.border}`, borderRadius: 8, padding: "10px 12px", color: C.text, fontSize: 13, fontFamily: "inherit", outline: "none" }} />
            </div>
            <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
              <button onClick={() => setShowNewProj(false)} style={{ padding: "8px 16px", borderRadius: 8, border: `1px solid ${C.border}`, background: "transparent", color: C.textSub, cursor: "pointer", fontFamily: "inherit" }}>Cancel</button>
              <button onClick={createProject} disabled={!newProjName.trim()} style={{ padding: "8px 16px", borderRadius: 8, border: "none", background: newProjName.trim() ? C.accent : C.surface2, color: newProjName.trim() ? "#fff" : C.textMute, cursor: newProjName.trim() ? "pointer" : "not-allowed", fontFamily: "inherit", fontWeight: 700 }}>Create</button>
            </div>
          </div>
        </div>
      )}

      {/* Settings modal */}
      <SettingsModal C={C} open={showSettings} onClose={() => setShowSettings(false)} username={username} email={email} themeMode={themeMode} setThemeMode={setThemeMode} />

      {/* "View Analysis" modal — the code.block trail for one document */}
      {analysisExecId && (
        <AnalysisModal executionId={analysisExecId} onClose={() => setAnalysisExecId(null)} C={C} />
      )}
    </>
  );
}

// ── Sidebar item helper ────────────────────────────────────────────
function SideItem({ label, icon, active, onClick, onDelete, C, indent = false }) {
  const [hover, setHover] = useState(false);
  return (
    <div onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      style={{ display: "flex", alignItems: "center", margin: "1px 0", borderRadius: 8, background: active ? C.accentBg : hover ? C.surface2 : "transparent", overflow: "hidden" }}>
      <div onClick={onClick} style={{ flex: 1, display: "flex", alignItems: "center", gap: 7, padding: `6px 8px 6px ${indent ? 22 : 10}px`, cursor: "pointer", color: active ? C.accent : C.textSub, fontSize: 12.5, fontWeight: active ? 600 : 400, overflow: "hidden" }}>
        <Icon d={icon} size={13} stroke={active ? C.accent : C.textSub} />
        <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{label}</span>
      </div>
      {hover && onDelete && (
        <button onClick={onDelete} style={{ background: "none", border: "none", cursor: "pointer", padding: "6px 8px", color: C.textMute, opacity: 0.6, flexShrink: 0 }}
          onMouseEnter={e => e.currentTarget.style.opacity = "1"}
          onMouseLeave={e => e.currentTarget.style.opacity = "0.6"}>
          <Icon d={I.trash} size={11} stroke={C.danger} />
        </button>
      )}
    </div>
  );
}
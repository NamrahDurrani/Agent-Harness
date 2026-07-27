// // /**
// //  * ProjectManager.jsx
// //  * ==================
// //  * Unified component: original RAGDashboard UI/quality + ChatGPT-style
// //  * project sidebar + real /api/chat calls.
// //  *
// //  * Props:
// //  *   username  string   — logged-in username
// //  *   token     string   — JWT for auth headers
// //  *   onLogout  fn       — called when user clicks logout
// //  */

// // import { useState, useRef, useEffect, useCallback } from "react";

// // // ── Palette ────────────────────────────────────────────────────────────────────
// // const C = {
// //   bg:        "#0c1108",
// //   surface:   "#141c0f",
// //   surface2:  "#1c2614",
// //   surface3:  "#222e18",
// //   border:    "#2a3d1e",
// //   borderHi:  "#3d5a2a",
// //   accent:    "#7ab648",
// //   accentDim: "#4a7a1e",
// //   accentBg:  "rgba(122,182,72,0.10)",
// //   amber:     "#e8a020",
// //   amberDim:  "#7a4e00",
// //   amberBg:   "rgba(232,160,32,0.10)",
// //   text:      "#dde8cc",
// //   textSub:   "#7a9460",
// //   textMute:  "#4a6035",
// //   userBub:   "#1a2e10",
// //   botBub:    "#0f1a08",
// //   danger:    "#c0392b",
// //   dangerBg:  "rgba(192,57,43,0.12)",
// // };

// // // ── SVG Icon helper ────────────────────────────────────────────────────────────
// // const Icon = ({ d, size = 16, stroke = C.textSub, fill = "none" }) => (
// //   <svg width={size} height={size} viewBox="0 0 24 24" fill={fill}
// //     stroke={stroke} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round"
// //     style={{ flexShrink: 0 }}>
// //     <path d={d} />
// //   </svg>
// // );

// // const ICONS = {
// //   leaf:      "M12 2a4 4 0 0 1 4 4v2h2a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2V6a4 4 0 0 1 4-4z",
// //   chat:      "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z",
// //   folder:    "M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z",
// //   file:      "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H8",
// //   plus:      "M12 5v14M5 12h14",
// //   trash:     "M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6",
// //   edit:      "M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z",
// //   upload:    "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12",
// //   download:  "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3",
// //   globe:     "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zM2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z",
// //   book:      "M4 19.5A2.5 2.5 0 0 1 6.5 17H20M4 19.5A2.5 2.5 0 0 0 6.5 22H20V2H6.5A2.5 2.5 0 0 0 4 4.5v15z",
// //   chevD:     "M6 9l6 6 6-6",
// //   chevR:     "M9 18l6-6-6-6",
// //   chevL:     "M15 18l-6-6 6-6",
// //   x:         "M18 6L6 18M6 6l12 12",
// //   search:    "M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z",
// //   memory:    "M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3M12 17h.01",
// //   send:      "M22 2L11 13M22 2L15 22 11 13 2 9l20-7z",
// //   check:     "M20 6L9 17 4 12",
// //   copy:      "M20 9H11a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2v-9a2 2 0 0 0-2-2zM5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1",
// //   thumbUp:   "M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3",
// //   thumbDown: "M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zM17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17",
// //   share:     "M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8M16 6l-4-4-4 4M12 2v13",
// //   trace:     "M3 3h18v18H3zM9 9h6M9 13h6M9 17h4",
// //   bot:       "M12 2a4 4 0 0 1 4 4v2h2a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2V6a4 4 0 0 1 4-4zM9 10H7v2h2v-2zm8 0h-2v2h2v-2zm-5 4h-2v2h2v-2z",
// //   user:      "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
// //   snapshot:  "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H8",
// //   reset:     "M1 4v6h6M23 20v-6h-6M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15",
// //   sources:   "M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2zM22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z",
// //   regen:     "M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15",
// //   export:    "M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8M16 6l-4-4-4 4M12 2v13",
// // };

// // // ── Utility ───────────────────────────────────────────────────────────────────
// // const now = () => new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

// // // ── Citation parser (from original RAGDashboard) ───────────────────────────────
// // function parseSources(content) {
// //   const sourcesMatch = content.match(/SOURCES:\s*\n([\s\S]+)$/i);
// //   const mainText = sourcesMatch
// //     ? content.slice(0, content.indexOf(sourcesMatch[0])).trim()
// //     : content;
// //   const sources = [];
// //   if (sourcesMatch) {
// //     const lines = sourcesMatch[1].trim().split("\n").filter(Boolean);
// //     lines.forEach(line => {
// //       const docMatch = line.match(/\[(\d+)\]\s*(.+?)\s*\|\s*[Pp]age\s*(\d+)/);
// //       if (docMatch) {
// //         sources.push({ num: parseInt(docMatch[1]), filename: docMatch[2].trim(), page: parseInt(docMatch[3]), type: "document" });
// //         return;
// //       }
// //       const webMatch = line.match(/\[Web\s*(\d+)\]\s*(.+?)\s*—\s*(https?:\/\/\S+)/);
// //       if (webMatch) {
// //         sources.push({ num: parseInt(webMatch[1]), title: webMatch[2].trim(), url: webMatch[3].trim(), type: "web" });
// //       }
// //     });
// //   }
// //   return { mainText, sources };
// // }

// // function renderTextWithCitations(text, sources, onCiteClick) {
// //   const parts = text.split(/(\[(?:Web\s*)?\d+\])/g);
// //   return parts.map((part, i) => {
// //     const match = part.match(/^\[(?:Web\s*)?(\d+)\]$/);
// //     if (match) {
// //       const num = parseInt(match[1]);
// //       const isWeb = part.toLowerCase().includes("web");
// //       const src = sources.find(s => s.num === num && (isWeb ? s.type === "web" : s.type === "document"))
// //                || sources.find(s => s.num === num);
// //       return (
// //         <sup key={i} onClick={() => src && onCiteClick(src)}
// //           title={src ? (src.type === "document" ? `${src.filename} — Page ${src.page}` : src.title) : ""}
// //           style={{
// //             cursor: src ? "pointer" : "default",
// //             color: src ? (src.type === "web" ? C.amber : C.accent) : C.textMute,
// //             fontWeight: 700, fontSize: "0.72em", marginLeft: 1,
// //             padding: "1px 4px", borderRadius: 3,
// //             background: src ? (src.type === "web" ? "#2a1e00" : "#16301a") : "transparent",
// //             border: src ? `1px solid ${src.type === "web" ? C.amberDim : C.accentDim}` : "none",
// //             userSelect: "none",
// //           }}>
// //           {part}
// //         </sup>
// //       );
// //     }
// //     return (
// //       <span key={i}>
// //         {part.split("\n").map((line, j, arr) => (
// //           <span key={j}>{line}{j < arr.length - 1 && <br />}</span>
// //         ))}
// //       </span>
// //     );
// //   });
// // }

// // function SourcesList({ sources }) {
// //   if (!sources.length) return null;
// //   const open = (src) => {
// //     if (src.type === "document") window.open(`/api/pdf/${encodeURIComponent(src.filename)}#page=${src.page}`, "_blank");
// //     else window.open(src.url, "_blank");
// //   };
// //   return (
// //     <div style={{ marginTop: 12, paddingTop: 10, borderTop: `1px solid ${C.border}` }}>
// //       <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: C.textMute, marginBottom: 6 }}>
// //         References
// //       </div>
// //       {sources.map((src, i) => (
// //         <div key={i} onClick={() => open(src)}
// //           style={{ display: "flex", alignItems: "flex-start", gap: 7, marginBottom: 5, cursor: "pointer", padding: "5px 7px", borderRadius: 7, transition: "background 0.15s" }}
// //           onMouseEnter={e => e.currentTarget.style.background = C.surface2}
// //           onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
// //           <span style={{ minWidth: 20, height: 20, borderRadius: 4, flexShrink: 0, background: src.type === "document" ? C.accentDim : C.amberDim, border: `1px solid ${src.type === "document" ? C.accent : C.amber}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 9, fontWeight: 700, color: src.type === "document" ? C.accent : C.amber }}>
// //             {src.num}
// //           </span>
// //           <div style={{ fontSize: 11.5, color: C.textSub, lineHeight: 1.5 }}>
// //             {src.type === "document" ? (
// //               <><span style={{ color: C.text, fontWeight: 500 }}>{src.filename}</span><span style={{ color: C.textMute }}> — Page {src.page}</span><span style={{ color: C.accentDim, fontSize: 10, marginLeft: 5 }}>↗ open PDF</span></>
// //             ) : (
// //               <><span style={{ color: C.text, fontWeight: 500 }}>{src.title}</span><span style={{ color: C.amberDim, fontSize: 10, marginLeft: 5 }}>↗ web</span></>
// //             )}
// //           </div>
// //         </div>
// //       ))}
// //     </div>
// //   );
// // }

// // // ── Message bubble ─────────────────────────────────────────────────────────────
// // function Message({ role, content, ts, usedRag, onRegenerate }) {
// //   const [copied, setCopied] = useState(false);
// //   const [liked, setLiked]   = useState(null);
// //   const [showSrc, setShowSrc] = useState(true);
// //   const isUser = role === "user";

// //   const ActionBtn = ({ icon, title, onClick, active, activeColor }) => (
// //     <button onClick={onClick} title={title}
// //       style={{ background: "none", border: "none", cursor: "pointer", padding: "4px 5px", borderRadius: 6, display: "flex", alignItems: "center", opacity: 0.55, transition: "opacity 0.15s" }}
// //       onMouseEnter={e => { e.currentTarget.style.opacity = "1"; e.currentTarget.style.background = C.surface2; }}
// //       onMouseLeave={e => { e.currentTarget.style.opacity = "0.55"; e.currentTarget.style.background = "none"; }}>
// //       <Icon d={icon} size={14} stroke={active ? (activeColor || C.accent) : C.textSub} />
// //     </button>
// //   );

// //   const ragBadge = !isUser && usedRag !== null && usedRag !== undefined && (
// //     <span style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 9.5, fontWeight: 600, letterSpacing: "0.03em", padding: "2px 7px", borderRadius: 20, background: usedRag ? "#16301a" : "#2a2210", border: `1px solid ${usedRag ? C.accentDim : C.amberDim}`, color: usedRag ? C.accent : C.amber, marginLeft: 6 }}>
// //       {usedRag ? "RAG" : "🌐 Web"}
// //     </span>
// //   );

// //   return (
// //     <div style={{ display: "flex", flexDirection: "column", alignItems: isUser ? "flex-end" : "flex-start", gap: 4 }}>
// //       <div style={{ display: "flex", alignItems: "center", gap: 6, flexDirection: isUser ? "row-reverse" : "row" }}>
// //         <div style={{ width: 26, height: 26, borderRadius: "50%", background: isUser ? C.accentDim : "#1a2610", border: `1px solid ${isUser ? C.accent : C.border}`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
// //           <Icon d={isUser ? ICONS.user : ICONS.bot} size={13} stroke={isUser ? C.accent : C.textSub} />
// //         </div>
// //         <span style={{ fontSize: 11, color: C.textMute, display: "flex", alignItems: "center" }}>
// //           {isUser ? "You" : "RAG Assistant"} · {ts}{ragBadge}
// //         </span>
// //       </div>

// //       <div style={{ maxWidth: "78%", background: isUser ? C.userBub : C.botBub, border: `1px solid ${isUser ? C.accentDim : C.border}`, borderRadius: isUser ? "14px 4px 14px 14px" : "4px 14px 14px 14px", padding: "10px 14px", lineHeight: 1.65, fontSize: 14, color: C.text }}>
// //         {isUser ? (
// //           <span style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>{content}</span>
// //         ) : (() => {
// //           const { mainText, sources } = parseSources(content);
// //           const onCiteClick = src => {
// //             if (src.type === "document") window.open(`/api/pdf/${encodeURIComponent(src.filename)}#page=${src.page}`, "_blank");
// //             else window.open(src.url, "_blank");
// //           };
// //           return (
// //             <>
// //               <div style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
// //                 {renderTextWithCitations(mainText, sources, onCiteClick)}
// //               </div>
// //               {showSrc && <SourcesList sources={sources} />}
// //             </>
// //           );
// //         })()}
// //       </div>

// //       {!isUser && (
// //         <div style={{ display: "flex", alignItems: "center", gap: 1, paddingLeft: 4, marginTop: -2 }}>
// //           <ActionBtn icon={copied ? ICONS.check : ICONS.copy} title="Copy" onClick={() => { navigator.clipboard.writeText(content); setCopied(true); setTimeout(() => setCopied(false), 1500); }} active={copied} activeColor={C.accent} />
// //           <ActionBtn icon={ICONS.thumbUp} title="Good response" onClick={() => setLiked(l => l === "up" ? null : "up")} active={liked === "up"} activeColor={C.accent} />
// //           <ActionBtn icon={ICONS.thumbDown} title="Bad response" onClick={() => setLiked(l => l === "down" ? null : "down")} active={liked === "down"} activeColor={C.danger} />
// //           <ActionBtn icon={ICONS.share} title="Share" onClick={() => navigator.clipboard.writeText(content)} />
// //           {onRegenerate && <ActionBtn icon={ICONS.regen} title="Regenerate" onClick={onRegenerate} />}
// //           <div style={{ width: 1, height: 14, background: C.border, margin: "0 3px" }} />
// //           <ActionBtn icon={ICONS.sources} title={showSrc ? "Hide sources" : "Show sources"} onClick={() => setShowSrc(s => !s)} active={showSrc} activeColor={C.accent} />
// //         </div>
// //       )}
// //     </div>
// //   );
// // }

// // // ── Typing dots ────────────────────────────────────────────────────────────────
// // function TypingDots() {
// //   return (
// //     <div style={{ display: "flex", alignItems: "flex-start", gap: 6 }}>
// //       <div style={{ width: 26, height: 26, borderRadius: "50%", background: "#1a2610", border: `1px solid ${C.border}`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
// //         <Icon d={ICONS.bot} size={13} stroke={C.textSub} />
// //       </div>
// //       <div style={{ background: C.botBub, border: `1px solid ${C.border}`, borderRadius: "4px 14px 14px 14px", padding: "12px 16px", display: "flex", gap: 5, alignItems: "center" }}>
// //         {[0, 0.18, 0.36].map((delay, i) => (
// //           <div key={i} style={{ width: 7, height: 7, borderRadius: "50%", background: C.accentDim, animation: "pulse 1.2s ease-in-out infinite", animationDelay: `${delay}s` }} />
// //         ))}
// //       </div>
// //     </div>
// //   );
// // }

// // // ── Trace panel ────────────────────────────────────────────────────────────────
// // function TracePanel({ trace }) {
// //   return (
// //     <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
// //       <div style={{ padding: "14px 16px 10px", borderBottom: `1px solid ${C.border}`, display: "flex", alignItems: "center", gap: 8 }}>
// //         <Icon d={ICONS.trace} size={15} stroke={C.amber} />
// //         <span style={{ fontSize: 13, fontWeight: 600, color: C.amber }}>Pipeline trace</span>
// //       </div>
// //       <div style={{ flex: 1, overflowY: "auto", padding: "12px 14px" }}>
// //         {!trace ? (
// //           <div style={{ color: C.textMute, fontSize: 12, textAlign: "center", marginTop: 40, lineHeight: 1.7 }}>
// //             Pipeline step timings<br />appear here after each query
// //           </div>
// //         ) : (
// //           <pre style={{ fontFamily: "'JetBrains Mono','Fira Code',monospace", fontSize: 11, color: C.textSub, lineHeight: 1.75, whiteSpace: "pre-wrap", wordBreak: "break-word", margin: 0 }}>
// //             {trace}
// //           </pre>
// //         )}
// //       </div>
// //     </div>
// //   );
// // }

// // // ── Welcome screen ─────────────────────────────────────────────────────────────
// // function Welcome({ onSend }) {
// //   const prompts = [
// //     "What wheat diseases are monitored in Punjab?",
// //     "Summarise PARC's 2023-24 research highlights",
// //     "What is the role of the Agriculture Extension Wing?",
// //     "Which FAO guidelines cover Ug99 rust?",
// //   ];
// //   return (
// //     <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: 32, gap: 28 }}>
// //       <div style={{ textAlign: "center" }}>
// //         <div style={{ fontSize: 40, marginBottom: 12 }}>🌾</div>
// //         <div style={{ fontSize: 22, fontWeight: 700, color: C.text, letterSpacing: "-0.02em", marginBottom: 6 }}>
// //           Agricultural RAG Assistant
// //         </div>
// //         <div style={{ fontSize: 13, color: C.textSub, maxWidth: 380, lineHeight: 1.6 }}>
// //           Ask about PARC Annual Report 2023-24, FAO Crop Monitoring Guidelines, or Punjab Agriculture Rules.
// //         </div>
// //       </div>
// //       <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, width: "100%", maxWidth: 560 }}>
// //         {prompts.map((p, i) => (
// //           <button key={i} onClick={() => onSend(p)}
// //             style={{ background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 10, padding: "10px 14px", color: C.textSub, fontSize: 12, textAlign: "left", cursor: "pointer", lineHeight: 1.5, transition: "border-color 0.15s, color 0.15s", fontFamily: "inherit" }}
// //             onMouseEnter={e => { e.currentTarget.style.borderColor = C.accent; e.currentTarget.style.color = C.text; }}
// //             onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.color = C.textSub; }}>
// //             {p}
// //           </button>
// //         ))}
// //       </div>
// //     </div>
// //   );
// // }

// // // ── Sidebar item ───────────────────────────────────────────────────────────────
// // const SideItem = ({ icon, label, active, onClick, indent = 0, muted = false }) => (
// //   <div onClick={onClick}
// //     style={{ display: "flex", alignItems: "center", gap: 8, padding: `7px 12px 7px ${12 + indent * 16}px`, borderRadius: 8, cursor: "pointer", margin: "1px 6px", background: active ? C.accentBg : "transparent", color: active ? C.accent : muted ? C.textMute : C.textSub, fontSize: 13, fontWeight: active ? 600 : 400, transition: "all 0.12s" }}>
// //     {icon}
// //     <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{label}</span>
// //   </div>
// // );

// // // ── Modal ──────────────────────────────────────────────────────────────────────
// // const Modal = ({ open, onClose, title, children, width = 480 }) => {
// //   if (!open) return null;
// //   return (
// //     <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center" }}
// //       onClick={onClose}>
// //       <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 14, padding: "24px 28px", width, maxWidth: "90vw", maxHeight: "80vh", overflowY: "auto" }}
// //         onClick={e => e.stopPropagation()}>
// //         <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
// //           <span style={{ fontSize: 16, fontWeight: 700, color: C.text }}>{title}</span>
// //           <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer" }}>
// //             <Icon d={ICONS.x} stroke={C.textSub} size={18} />
// //           </button>
// //         </div>
// //         {children}
// //       </div>
// //     </div>
// //   );
// // };

// // const TextInput = ({ label, value, onChange, placeholder, multiline = false }) => (
// //   <div style={{ marginBottom: 14 }}>
// //     {label && <label style={{ fontSize: 12, color: C.textSub, display: "block", marginBottom: 6 }}>{label}</label>}
// //     {multiline
// //       ? <textarea value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
// //           style={{ width: "100%", background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 8, padding: "10px 12px", color: C.text, fontSize: 13, fontFamily: "inherit", outline: "none", resize: "vertical", minHeight: 80, boxSizing: "border-box" }} />
// //       : <input value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
// //           style={{ width: "100%", background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 8, padding: "10px 12px", color: C.text, fontSize: 13, fontFamily: "inherit", outline: "none", boxSizing: "border-box" }} />
// //     }
// //   </div>
// // );

// // const Btn = ({ children, onClick, variant = "ghost", danger = false, style: sx = {}, disabled = false }) => {
// //   const base = { display: "inline-flex", alignItems: "center", gap: 6, padding: "7px 12px", borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: disabled ? "not-allowed" : "pointer", border: "none", transition: "all 0.15s", opacity: disabled ? 0.5 : 1, fontFamily: "inherit" };
// //   const variants = {
// //     primary: { background: C.accent, color: C.bg },
// //     ghost:   { background: "transparent", color: danger ? C.danger : C.textSub, border: `1px solid ${danger ? C.danger + "55" : C.border}` },
// //     surface: { background: C.surface2, color: C.text, border: `1px solid ${C.border}` },
// //   };
// //   return <button style={{ ...base, ...variants[variant], ...sx }} onClick={onClick} disabled={disabled}>{children}</button>;
// // };

// // // ── Status badge ───────────────────────────────────────────────────────────────
// // function StatusBadge({ chunks }) {
// //   const ok = chunks > 0;
// //   return (
// //     <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "4px 10px", borderRadius: 20, background: ok ? "#1a3310" : "#3a1010", border: `1px solid ${ok ? C.accentDim : C.danger}`, fontSize: 12, color: ok ? C.accent : "#e74c3c" }}>
// //       <div style={{ width: 7, height: 7, borderRadius: "50%", background: ok ? C.accent : C.danger, boxShadow: ok ? `0 0 6px ${C.accent}` : "none" }} />
// //       {ok ? `${chunks.toLocaleString()} chunks` : "Empty — index first"}
// //     </div>
// //   );
// // }

// // // ════════════════════════════════════════════════════════════════════════════════
// // //  Main component
// // // ════════════════════════════════════════════════════════════════════════════════
// // const EMOJIS = ["🌱", "🌾", "🪴", "🌽", "🍃", "🌿", "🌻", "🌴", "🫘", "🍀"];

// // export default function ProjectManager({ username = "user", token, onLogout }) {
// //   // ── Projects / chats ─────────────────────────────────────────────────────
// //   const [projects, setProjects]           = useState([]);
// //   const [expandedProjects, setExpandedProjects] = useState(new Set());
// //   const [selectedProject, setSelectedProject]   = useState(null);

// //   // ── Active session: maps to a real /api session_id per chat ──────────────
// //   // activeSession: { sessionId, projectId|null, title }
// //   const [activeSession, setActiveSession] = useState(null);

// //   // ── Per-session message cache: { [sessionId]: [...messages] } ────────────
// //   const [msgCache, setMsgCache]   = useState({});
// //   const [loading, setLoading]     = useState(false);
// //   const [trace, setTrace]         = useState(null);
// //   const [input, setInput]         = useState("");

// //   // ── Backend / sidebar state ───────────────────────────────────────────────
// //   const [apiSessions, setApiSessions] = useState([]);   // /api/sessions list
// //   const [status, setStatus]           = useState(null);
// //   const [chunkCount, setChunkCount]   = useState(0);
// //   const [statusError, setStatusError] = useState(null);
// //   const [sideSearch, setSideSearch]   = useState("");
// //   const [showTrace, setShowTrace]     = useState(true);

// //   // ── Modals ────────────────────────────────────────────────────────────────
// //   const [showNewProject, setShowNewProject] = useState(false);
// //   const [newProjName, setNewProjName]       = useState("");
// //   const [newProjDesc, setNewProjDesc]       = useState("");
// //   const [newProjEmoji, setNewProjEmoji]     = useState("🌱");
// //   const [showRename, setShowRename]         = useState(false);
// //   const [renameTarget, setRenameTarget]     = useState(null);
// //   const [renameName, setRenameName]         = useState("");
// //   const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
// //   const [deleteTarget, setDeleteTarget]     = useState(null);

// //   const chatRef    = useRef(null);
// //   const textareaRef = useRef(null);

// //   const authHeaders = () => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : { "Content-Type": "application/json" };

// //   // ── Scroll to bottom ──────────────────────────────────────────────────────
// //   useEffect(() => {
// //     if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
// //   }, [msgCache, activeSession, loading]);

// //   // ── Poll /api/status ──────────────────────────────────────────────────────
// //   useEffect(() => {
// //     const fetch_ = () => {
// //       fetch("/api/status").then(r => r.json()).then(d => {
// //         setStatus(d);
// //         setChunkCount(d.chunk_count || 0);
// //         setStatusError(d.vector_store_error || d.pipeline_error || null);
// //       }).catch(err => { setStatusError(`Cannot reach API: ${err.message}`); setChunkCount(0); });
// //     };
// //     fetch_();
// //     const id = setInterval(fetch_, 8000);
// //     return () => clearInterval(id);
// //   }, []);

// //   // ── Load /api/sessions list ───────────────────────────────────────────────
// //   const fetchApiSessions = useCallback(() => {
// //     fetch("/api/sessions", { headers: authHeaders() })
// //       .then(r => r.json())
// //       .then(d => setApiSessions(d.sessions || []))
// //       .catch(() => {});
// //   }, [token]);

// //   useEffect(() => { fetchApiSessions(); }, [fetchApiSessions]);

// //   // ── Load projects from localStorage ──────────────────────────────────────
// //   useEffect(() => {
// //     try {
// //       const saved = localStorage.getItem(`rag_projects_${username}`);
// //       if (saved) setProjects(JSON.parse(saved));
// //     } catch (_) {}
// //   }, [username]);

// //   const saveProjects = (ps) => {
// //     setProjects(ps);
// //     try { localStorage.setItem(`rag_projects_${username}`, JSON.stringify(ps)); } catch (_) {}
// //   };

// //   // ── Open a session (or create new) ───────────────────────────────────────
// //   const openNewChat = (projectId = null) => {
// //     const sessionId = crypto.randomUUID();
// //     const proj = projectId ? projects.find(p => p.id === projectId) : null;
// //     const session = { sessionId, projectId, title: proj ? `${proj.emoji} New chat` : "New chat" };
// //     setActiveSession(session);
// //     setTrace(null);
// //     setInput("");
// //     // Register in project's session list
// //     if (projectId) {
// //       const updated = projects.map(p => {
// //         if (p.id !== projectId) return p;
// //         return { ...p, sessions: [...(p.sessions || []), { sessionId, title: "New chat", date: new Date().toISOString().slice(0, 10) }] };
// //       });
// //       saveProjects(updated);
// //     }
// //   };

// //   const openExistingSession = (sessionId, projectId = null) => {
// //     const proj = projectId ? projects.find(p => p.id === projectId) : null;
// //     const apiSess = apiSessions.find(s => s.session_id === sessionId);
// //     const title = apiSess?.title || apiSess?.preview || "Chat";
// //     setActiveSession({ sessionId, projectId, title: proj ? `${proj.emoji} ${title}` : title });
// //     setTrace(null);
// //     setInput("");
// //     // Load history if not cached
// //     if (!msgCache[sessionId]) {
// //       fetch(`/api/sessions/${sessionId}`, { headers: authHeaders() })
// //         .then(r => r.json())
// //         .then(d => {
// //           const msgs = (d.messages || []).map(m => ({
// //             role: m.role, content: m.content, ts: m.ts || now(), usedRag: m.used_rag,
// //           }));
// //           setMsgCache(prev => ({ ...prev, [sessionId]: msgs }));
// //         }).catch(() => {});
// //     }
// //   };

// //   // ── Send message ──────────────────────────────────────────────────────────
// //   const sendMessage = async (text) => {
// //     const q = (text || input).trim();
// //     if (!q || loading || !activeSession) return;
// //     setInput("");
// //     const userMsg = { role: "user", content: q, ts: now() };
// //     setMsgCache(prev => ({ ...prev, [activeSession.sessionId]: [...(prev[activeSession.sessionId] || []), userMsg] }));
// //     setLoading(true);
// //     setTrace(null);

// //     try {
// //       const res = await fetch("/api/chat", {
// //         method: "POST",
// //         headers: authHeaders(),
// //         body: JSON.stringify({ session_id: activeSession.sessionId, query: q }),
// //       });
// //       const data = await res.json();
// //       const botMsg = { role: "assistant", content: data.response || "No response received.", ts: now(), usedRag: data.used_rag };
// //       setMsgCache(prev => ({ ...prev, [activeSession.sessionId]: [...(prev[activeSession.sessionId] || []), botMsg] }));
// //       if (data.trace) setTrace(data.trace);

// //       // Auto-title the session from first message
// //       const currentMsgs = msgCache[activeSession.sessionId] || [];
// //       if (currentMsgs.filter(m => m.role === "user").length === 0) {
// //         const autoTitle = q.slice(0, 40) + (q.length > 40 ? "…" : "");
// //         setActiveSession(prev => ({ ...prev, title: autoTitle }));
// //         if (activeSession.projectId) {
// //           const updated = projects.map(p => {
// //             if (p.id !== activeSession.projectId) return p;
// //             return { ...p, sessions: (p.sessions || []).map(s => s.sessionId === activeSession.sessionId ? { ...s, title: autoTitle } : s) };
// //           });
// //           saveProjects(updated);
// //         }
// //       }
// //     } catch (err) {
// //       const errMsg = { role: "assistant", content: `❌ Could not reach the backend.\n\nError: ${err.message}`, ts: now() };
// //       setMsgCache(prev => ({ ...prev, [activeSession.sessionId]: [...(prev[activeSession.sessionId] || []), errMsg] }));
// //     } finally {
// //       setLoading(false);
// //       fetchApiSessions();
// //     }
// //   };

// //   // ── Delete session ────────────────────────────────────────────────────────
// //   const deleteSession = async (sessionId) => {
// //     if (!confirm("Delete this conversation permanently?")) return;
// //     await fetch(`/api/sessions/${sessionId}`, { method: "DELETE", headers: authHeaders() }).catch(() => {});
// //     setMsgCache(prev => { const n = { ...prev }; delete n[sessionId]; return n; });
// //     if (activeSession?.sessionId === sessionId) setActiveSession(null);
// //     fetchApiSessions();
// //   };

// //   // ── Export session ────────────────────────────────────────────────────────
// //   const exportSession = async (sessionId, format) => {
// //     try {
// //       const res = await fetch(`/api/sessions/${sessionId}/export?format=${format}`, { headers: authHeaders() });
// //       if (!res.ok) throw new Error(`Export failed (${res.status})`);
// //       const blob = await res.blob();
// //       const disposition = res.headers.get("Content-Disposition") || "";
// //       const match = disposition.match(/filename="([^"]+)"/);
// //       const filename = match ? match[1] : `chat.${format === "json" ? "json" : "md"}`;
// //       const url = URL.createObjectURL(blob);
// //       const a = document.createElement("a"); a.href = url; a.download = filename;
// //       document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
// //     } catch (err) { alert(`Export failed: ${err.message}`); }
// //   };

// //   // ── Rename session ────────────────────────────────────────────────────────
// //   const commitRename = async () => {
// //     if (!renameName.trim() || !renameTarget) return;
// //     if (renameTarget.type === "session") {
// //       await fetch(`/api/sessions/${renameTarget.id}`, {
// //         method: "PATCH", headers: authHeaders(),
// //         body: JSON.stringify({ title: renameName.trim() }),
// //       }).catch(() => {});
// //       fetchApiSessions();
// //     } else if (renameTarget.type === "project") {
// //       const updated = projects.map(p => p.id === renameTarget.id ? { ...p, name: renameName.trim() } : p);
// //       saveProjects(updated);
// //       if (selectedProject?.id === renameTarget.id) setSelectedProject(prev => ({ ...prev, name: renameName.trim() }));
// //     }
// //     setShowRename(false); setRenameTarget(null); setRenameName("");
// //   };

// //   // ── Project CRUD ──────────────────────────────────────────────────────────
// //   const createProject = () => {
// //     if (!newProjName.trim()) return;
// //     const proj = { id: "p" + Date.now(), name: newProjName.trim(), emoji: newProjEmoji, description: newProjDesc.trim(), createdAt: new Date().toISOString().slice(0, 10), sessions: [] };
// //     const updated = [...projects, proj];
// //     saveProjects(updated);
// //     setNewProjName(""); setNewProjDesc(""); setNewProjEmoji("🌱");
// //     setShowNewProject(false);
// //     setExpandedProjects(prev => new Set([...prev, proj.id]));
// //   };

// //   const deleteProject = (id) => {
// //     const updated = projects.filter(p => p.id !== id);
// //     saveProjects(updated);
// //     if (selectedProject?.id === id) setSelectedProject(null);
// //     if (activeSession?.projectId === id) setActiveSession(null);
// //     setShowDeleteConfirm(false); setDeleteTarget(null);
// //   };

// //   // ── Filtered sidebar lists ────────────────────────────────────────────────
// //   const search = sideSearch.toLowerCase();
// //   const filteredApiSessions = apiSessions.filter(s =>
// //     !search || (s.title || s.preview || "").toLowerCase().includes(search)
// //   ).filter(s => {
// //     // Only show sessions not "owned" by a project
// //     const allProjectSessionIds = new Set(projects.flatMap(p => (p.sessions || []).map(ss => ss.sessionId)));
// //     return !allProjectSessionIds.has(s.session_id);
// //   });

// //   const filteredProjects = projects.filter(p => !search || p.name.toLowerCase().includes(search));
// //   const currentMessages  = (activeSession && msgCache[activeSession.sessionId]) || [];

// //   // ── Render ────────────────────────────────────────────────────────────────
// //   return (
// //     <>
// //       <style>{`
// //         * { box-sizing: border-box; margin: 0; padding: 0; }
// //         body { background: ${C.bg}; }
// //         ::-webkit-scrollbar { width: 5px; }
// //         ::-webkit-scrollbar-track { background: transparent; }
// //         ::-webkit-scrollbar-thumb { background: ${C.border}; border-radius: 4px; }
// //         @keyframes pulse { 0%,100% { opacity:0.3; transform:scale(0.85); } 50% { opacity:1; transform:scale(1.1); } }
// //       `}</style>

// //       <div style={{ display: "flex", height: "100vh", fontFamily: "'Inter','Segoe UI',system-ui,sans-serif", color: C.text, overflow: "hidden", background: C.bg }}>

// //         {/* ══════════════════════════════════════════════════════════════════
// //             SIDEBAR
// //         ══════════════════════════════════════════════════════════════════ */}
// //         <div style={{ width: 248, background: C.surface, borderRight: `1px solid ${C.border}`, display: "flex", flexDirection: "column", height: "100vh", flexShrink: 0 }}>
// //           {/* Logo + search */}
// //           <div style={{ padding: "14px 12px 10px", borderBottom: `1px solid ${C.border}` }}>
// //             <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
// //               <Icon d={ICONS.leaf} size={20} stroke={C.accent} />
// //               <span style={{ fontWeight: 700, fontSize: 15, color: C.text }}>Agentic RAG</span>
// //             </div>
// //             <div style={{ display: "flex", alignItems: "center", gap: 6, background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 8, padding: "6px 10px" }}>
// //               <Icon d={ICONS.search} size={14} />
// //               <input value={sideSearch} onChange={e => setSideSearch(e.target.value)} placeholder="Search…"
// //                 style={{ flex: 1, background: "transparent", border: "none", outline: "none", color: C.text, fontSize: 12, fontFamily: "inherit" }} />
// //             </div>
// //           </div>

// //           <div style={{ flex: 1, overflowY: "auto", padding: "8px 0" }}>
// //             {/* New Chat */}
// //             <div style={{ padding: "4px 8px 8px" }}>
// //               <Btn variant="surface" onClick={() => openNewChat(null)} style={{ width: "100%", justifyContent: "center" }}>
// //                 <Icon d={ICONS.plus} size={14} stroke={C.accent} /> New chat
// //               </Btn>
// //             </div>

// //             {/* ── Recent Chats (from /api/sessions, not in any project) ── */}
// //             <div style={{ padding: "8px 14px 4px", fontSize: 11, fontWeight: 700, color: C.textMute, letterSpacing: "0.08em" }}>RECENT CHATS</div>
// //             {filteredApiSessions.length === 0 && (
// //               <div style={{ fontSize: 12, color: C.textMute, padding: "4px 18px" }}>No chats yet</div>
// //             )}
// //             {filteredApiSessions.map(s => (
// //               <div key={s.session_id} style={{ position: "relative" }}>
// //                 <SideItem
// //                   icon={<Icon d={ICONS.chat} size={14} />}
// //                   label={s.title || s.preview || "Untitled"}
// //                   active={activeSession?.sessionId === s.session_id}
// //                   onClick={() => openExistingSession(s.session_id, null)}
// //                 />
// //                 {/* delete button on hover via a wrapper is complex; simplified to always-visible tiny trash */}
// //                 <button onClick={e => { e.stopPropagation(); deleteSession(s.session_id); }}
// //                   title="Delete"
// //                   style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", opacity: 0.4, padding: 2 }}>
// //                   <Icon d={ICONS.trash} size={11} stroke={C.danger} />
// //                 </button>
// //               </div>
// //             ))}

// //             {/* ── Projects ── */}
// //             <div style={{ padding: "12px 14px 4px", fontSize: 11, fontWeight: 700, color: C.textMute, letterSpacing: "0.08em", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
// //               <span>PROJECTS</span>
// //               <button onClick={() => setShowNewProject(true)} style={{ background: "none", border: "none", cursor: "pointer", padding: 2 }}>
// //                 <Icon d={ICONS.plus} size={14} stroke={C.accent} />
// //               </button>
// //             </div>

// //             {filteredProjects.map(proj => {
// //               const isExpanded = expandedProjects.has(proj.id);
// //               const isSelected = activeSession?.projectId === proj.id;
// //               return (
// //                 <div key={proj.id}>
// //                   <div style={{ display: "flex", alignItems: "center", margin: "1px 6px", borderRadius: 8, background: isSelected ? C.accentBg : "transparent" }}>
// //                     <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 8, padding: "7px 8px 7px 12px", color: isSelected ? C.accent : C.textSub, fontSize: 13, fontWeight: isSelected ? 600 : 400, cursor: "pointer", overflow: "hidden" }}
// //                       onClick={() => { setSelectedProject(proj); setExpandedProjects(prev => new Set([...prev, proj.id])); }}>
// //                       <span style={{ fontSize: 15 }}>{proj.emoji}</span>
// //                       <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{proj.name}</span>
// //                     </div>
// //                     <button onClick={e => { e.stopPropagation(); setExpandedProjects(prev => { const s = new Set(prev); s.has(proj.id) ? s.delete(proj.id) : s.add(proj.id); return s; }); }}
// //                       style={{ background: "none", border: "none", cursor: "pointer", padding: "7px 8px", color: C.textMute }}>
// //                       <Icon d={isExpanded ? ICONS.chevD : ICONS.chevR} size={13} stroke={C.textMute} />
// //                     </button>
// //                   </div>
// //                   {isExpanded && (
// //                     <div>
// //                       {(proj.sessions || []).map(sess => {
// //                         const apiS = apiSessions.find(a => a.session_id === sess.sessionId);
// //                         const label = apiS?.title || apiS?.preview || sess.title || "Chat";
// //                         return (
// //                           <SideItem key={sess.sessionId} indent={1}
// //                             icon={<Icon d={ICONS.chat} size={13} />}
// //                             label={label}
// //                             muted
// //                             active={activeSession?.sessionId === sess.sessionId}
// //                             onClick={() => openExistingSession(sess.sessionId, proj.id)}
// //                           />
// //                         );
// //                       })}
// //                       <SideItem indent={1} muted
// //                         icon={<Icon d={ICONS.plus} size={13} stroke={C.textMute} />}
// //                         label="New chat"
// //                         onClick={() => openNewChat(proj.id)}
// //                       />
// //                     </div>
// //                   )}
// //                 </div>
// //               );
// //             })}

// //             {/* ── Knowledge base PDFs ── */}
// //             <div style={{ padding: "12px 14px 4px", fontSize: 11, fontWeight: 700, color: C.textMute, letterSpacing: "0.08em" }}>KNOWLEDGE BASE</div>
// //             {[
// //               { label: "PARC Report 2023-24",  file: "PARC Annual Report 2023-24_compressed.pdf" },
// //               { label: "FAO Crop Guidelines",  file: "i5550e.pdf" },
// //               { label: "Punjab Agri Rules",    file: "PbAgriDeptExtenAdapReseWing_SR_2007_20070612.pdf" },
// //             ].map(({ label, file }) => (
// //               <div key={file} onClick={() => window.open(`/api/pdf/${encodeURIComponent(file)}`, "_blank")}
// //                 style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 12px 6px 18px", cursor: "pointer", color: C.textSub, fontSize: 12 }}>
// //                 <Icon d={ICONS.book} size={13} stroke={C.textMute} />
// //                 <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{label}</span>
// //                 <span style={{ color: C.accentDim, fontSize: 10 }}>↗</span>
// //               </div>
// //             ))}
// //           </div>

// //           {/* User footer */}
// //           <div style={{ padding: "10px 14px", borderTop: `1px solid ${C.border}`, display: "flex", alignItems: "center", gap: 8 }}>
// //             <div style={{ width: 30, height: 30, borderRadius: "50%", background: C.accentBg, border: `1px solid ${C.accent}44`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 700, color: C.accent }}>
// //               {username[0].toUpperCase()}
// //             </div>
// //             <span style={{ flex: 1, fontSize: 12, color: C.textSub, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{username}</span>
// //             {onLogout && (
// //               <button onClick={onLogout} title="Sign out" style={{ background: "none", border: "none", cursor: "pointer" }}>
// //                 <Icon d={ICONS.x} size={14} stroke={C.textMute} />
// //               </button>
// //             )}
// //           </div>
// //         </div>

// //         {/* ══════════════════════════════════════════════════════════════════
// //             MAIN CHAT AREA
// //         ══════════════════════════════════════════════════════════════════ */}
// //         <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
// //           {/* Header */}
// //           <div style={{ padding: "0 20px", height: 52, display: "flex", alignItems: "center", gap: 12, background: C.surface, borderBottom: `1px solid ${C.border}`, flexShrink: 0 }}>
// //             <span style={{ fontSize: 16 }}>🌾</span>
// //             <div style={{ flex: 1 }}>
// //               <span style={{ fontSize: 14, fontWeight: 600, color: C.text }}>
// //                 {activeSession ? activeSession.title : "Agricultural Knowledge Base"}
// //               </span>
// //               {activeSession?.projectId && (
// //                 <span style={{ fontSize: 11, color: C.textMute, marginLeft: 8 }}>
// //                   · {projects.find(p => p.id === activeSession.projectId)?.name}
// //                 </span>
// //               )}
// //             </div>
// //             <StatusBadge chunks={chunkCount} />
// //             <button onClick={() => setShowTrace(t => !t)} title={showTrace ? "Hide trace" : "Show trace"}
// //               style={{ background: "none", border: `1px solid ${C.border}`, borderRadius: 6, padding: "4px 8px", cursor: "pointer", color: C.amber, fontSize: 12, display: "flex", alignItems: "center", gap: 5 }}>
// //               <Icon d={ICONS.trace} size={13} stroke={C.amber} />
// //               Trace
// //             </button>
// //             {activeSession && (
// //               <button onClick={() => exportSession(activeSession.sessionId, "markdown")} title="Export as Markdown"
// //                 style={{ background: "none", border: `1px solid ${C.border}`, borderRadius: 6, padding: "4px 8px", cursor: "pointer", color: C.textSub, fontSize: 12, display: "flex", alignItems: "center", gap: 5 }}>
// //                 <Icon d={ICONS.export} size={13} stroke={C.textSub} />
// //                 Export
// //               </button>
// //             )}
// //           </div>

// //           {/* Chat area */}
// //           <div ref={chatRef} style={{ flex: 1, overflowY: "auto", padding: "20px 24px", display: "flex", flexDirection: "column", gap: 16 }}>
// //             {!activeSession ? (
// //               <Welcome onSend={(p) => { openNewChat(null); setTimeout(() => sendMessage(p), 50); }} />
// //             ) : currentMessages.length === 0 ? (
// //               <Welcome onSend={sendMessage} />
// //             ) : (
// //               currentMessages.map((m, i) => (
// //                 <Message key={i} role={m.role} content={m.content} ts={m.ts} usedRag={m.usedRag}
// //                   onRegenerate={m.role === "assistant" ? () => {
// //                     const prev = currentMessages.slice(0, i).reverse().find(x => x.role === "user");
// //                     if (prev) sendMessage(prev.content);
// //                   } : null}
// //                 />
// //               ))
// //             )}
// //             {loading && <TypingDots />}
// //           </div>

// //           {/* Input */}
// //           <div style={{ padding: "12px 20px 16px", borderTop: `1px solid ${C.border}`, background: C.surface }}>
// //             {!activeSession && (
// //               <div style={{ fontSize: 12, color: C.textMute, textAlign: "center", marginBottom: 8 }}>
// //                 Click <strong style={{ color: C.accent }}>+ New chat</strong> or select a conversation to start.
// //               </div>
// //             )}
// //             <div style={{ display: "flex", gap: 10, alignItems: "flex-end" }}>
// //               <div style={{ flex: 1, background: C.surface2, border: `1px solid ${activeSession ? C.borderHi : C.border}`, borderRadius: 10, padding: "10px 14px" }}>
// //                 <textarea ref={textareaRef} rows={2} value={input}
// //                   onChange={e => setInput(e.target.value)}
// //                   onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
// //                   placeholder={activeSession ? "Ask about crops, diseases, PARC activities… (Enter to send)" : "Select or create a chat first"}
// //                   disabled={!activeSession}
// //                   style={{ width: "100%", background: "transparent", border: "none", outline: "none", color: C.text, fontSize: 14, fontFamily: "inherit", resize: "none", lineHeight: 1.5 }} />
// //               </div>
// //               <button onClick={() => sendMessage()} disabled={loading || !input.trim() || !activeSession}
// //                 style={{ width: 42, height: 42, borderRadius: 10, border: "none", background: C.accent, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", alignSelf: "flex-end", flexShrink: 0, opacity: (loading || !input.trim() || !activeSession) ? 0.4 : 1, transition: "opacity 0.15s" }}>
// //                 <Icon d={ICONS.send} size={16} stroke="#fff" />
// //               </button>
// //             </div>
// //           </div>
// //         </div>

// //         {/* ══════════════════════════════════════════════════════════════════
// //             TRACE PANEL (collapsible)
// //         ══════════════════════════════════════════════════════════════════ */}
// //         {showTrace && (
// //           <div style={{ width: 280, background: C.surface, borderLeft: `1px solid ${C.border}`, display: "flex", flexDirection: "column", overflow: "hidden", flexShrink: 0 }}>
// //             <TracePanel trace={trace} />
// //             {/* Pipeline config at bottom */}
// //             <div style={{ padding: "12px 14px", borderTop: `1px solid ${C.border}` }}>
// //               <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: C.textMute, marginBottom: 8 }}>Pipeline</div>
// //               {[
// //                 ["Vector DB",   status?.vector_db || "ChromaDB"],
// //                 ["Retrieval",   status?.retrieval || "BM25 + Embeddings"],
// //                 ["Fusion",      status?.fusion    || "RRF"],
// //                 ["Chunks",      chunkCount.toLocaleString()],
// //               ].map(([k, v]) => (
// //                 <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "4px 8px", background: C.surface2, borderRadius: 6, marginBottom: 4, fontSize: 12 }}>
// //                   <span style={{ color: C.textSub }}>{k}</span>
// //                   <span style={{ color: C.text }}>{v}</span>
// //                 </div>
// //               ))}
// //               {statusError && (
// //                 <div style={{ marginTop: 8, background: C.dangerBg, border: `1px solid ${C.danger}`, borderRadius: 8, padding: "8px 10px", fontSize: 11.5, color: "#e8938a", lineHeight: 1.5 }}>
// //                   {statusError}
// //                 </div>
// //               )}
// //             </div>
// //           </div>
// //         )}
// //       </div>

// //       {/* ── Modals ─────────────────────────────────────────────────────────── */}

// //       {/* New Project */}
// //       <Modal open={showNewProject} onClose={() => setShowNewProject(false)} title="Create new project">
// //         <div style={{ marginBottom: 14 }}>
// //           <label style={{ fontSize: 12, color: C.textSub, display: "block", marginBottom: 6 }}>Icon</label>
// //           <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
// //             {EMOJIS.map(e => (
// //               <button key={e} onClick={() => setNewProjEmoji(e)}
// //                 style={{ fontSize: 20, padding: "4px 8px", borderRadius: 8, cursor: "pointer", border: `1px solid ${newProjEmoji === e ? C.accent : C.border}`, background: newProjEmoji === e ? C.accentBg : C.surface2, fontFamily: "inherit" }}>
// //                 {e}
// //               </button>
// //             ))}
// //           </div>
// //         </div>
// //         <TextInput label="Project name" value={newProjName} onChange={setNewProjName} placeholder="e.g. Wheat Disease Research" />
// //         <TextInput label="Description (optional)" value={newProjDesc} onChange={setNewProjDesc} placeholder="What is this project about?" multiline />
// //         <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", marginTop: 4 }}>
// //           <Btn onClick={() => setShowNewProject(false)}>Cancel</Btn>
// //           <Btn variant="primary" onClick={createProject} disabled={!newProjName.trim()}>Create project</Btn>
// //         </div>
// //       </Modal>

// //       {/* Rename */}
// //       <Modal open={showRename} onClose={() => { setShowRename(false); setRenameTarget(null); }} title={`Rename ${renameTarget?.type || "item"}`} width={400}>
// //         <TextInput label="New name" value={renameName} onChange={setRenameName} placeholder="Enter new name" />
// //         <div style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
// //           <Btn onClick={() => { setShowRename(false); setRenameTarget(null); }}>Cancel</Btn>
// //           <Btn variant="primary" onClick={commitRename} disabled={!renameName.trim()}>Save</Btn>
// //         </div>
// //       </Modal>

// //       {/* Delete confirm */}
// //       <Modal open={showDeleteConfirm} onClose={() => { setShowDeleteConfirm(false); setDeleteTarget(null); }} title="Confirm deletion" width={380}>
// //         <div style={{ fontSize: 13, color: C.textSub, marginBottom: 20, lineHeight: 1.6 }}>
// //           Delete <strong style={{ color: C.text }}>{deleteTarget?.name}</strong>? This will remove all its chats and data.
// //         </div>
// //         <div style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
// //           <Btn onClick={() => { setShowDeleteConfirm(false); setDeleteTarget(null); }}>Cancel</Btn>
// //           <button onClick={() => { if (deleteTarget?.type === "project") deleteProject(deleteTarget.id); }}
// //             style={{ padding: "7px 14px", borderRadius: 8, background: C.danger, color: "#fff", border: "none", cursor: "pointer", fontWeight: 600, fontSize: 13, fontFamily: "inherit" }}>
// //             Delete
// //           </button>
// //         </div>
// //       </Modal>
// //     </>
// //   );
// // }

// /**
//  * ProjectManager.jsx — Enhanced
//  * ==============================
//  * NEW features (over base version):
//  *  1. ◀▶ Sidebar collapse/expand toggle
//  *  2. 🌐 Tavily web search toggle in header — fires tavily_search MCP tool
//  *     and injects live web results into the LLM context before answering
//  *  3. 📄 PDF export of current chat (top-right, beside chunk badge)
//  *  4. ✏️  Rename for BOTH recent chats AND projects in sidebar
//  *  5. ➕ File-upload button ("+") in every query box — uploads doc and
//  *     answers questions grounded in that uploaded document
//  *  6. MCP tool call display in trace panel (weather, crop_calendar, etc.)
//  *
//  * Props: username, token, onLogout  (same as before — no API changes needed)
//  */

// import { useState, useRef, useEffect, useCallback } from "react";

// // ── Palette ───────────────────────────────────────────────────────────────────
// const C = {
//   bg:        "#0c1108",
//   surface:   "#141c0f",
//   surface2:  "#1c2614",
//   surface3:  "#222e18",
//   border:    "#2a3d1e",
//   borderHi:  "#3d5a2a",
//   accent:    "#7ab648",
//   accentDim: "#4a7a1e",
//   accentBg:  "rgba(122,182,72,0.10)",
//   amber:     "#e8a020",
//   amberDim:  "#7a4e00",
//   amberBg:   "rgba(232,160,32,0.10)",
//   teal:      "#2bbfa0",
//   tealDim:   "#0d5a48",
//   tealBg:    "rgba(43,191,160,0.10)",
//   text:      "#dde8cc",
//   textSub:   "#7a9460",
//   textMute:  "#4a6035",
//   userBub:   "#1a2e10",
//   botBub:    "#0f1a08",
//   danger:    "#c0392b",
//   dangerBg:  "rgba(192,57,43,0.12)",
// };

// // ── Icon ──────────────────────────────────────────────────────────────────────
// const Icon = ({ d, size = 16, stroke = C.textSub, fill = "none" }) => (
//   <svg width={size} height={size} viewBox="0 0 24 24" fill={fill}
//     stroke={stroke} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round"
//     style={{ flexShrink: 0 }}>
//     <path d={d} />
//   </svg>
// );

// const ICONS = {
//   leaf:      "M12 2a4 4 0 0 1 4 4v2h2a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2V6a4 4 0 0 1 4-4z",
//   chat:      "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z",
//   folder:    "M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z",
//   file:      "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H8",
//   plus:      "M12 5v14M5 12h14",
//   trash:     "M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6",
//   edit:      "M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z",
//   upload:    "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12",
//   download:  "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3",
//   globe:     "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zM2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z",
//   book:      "M4 19.5A2.5 2.5 0 0 1 6.5 17H20M4 19.5A2.5 2.5 0 0 0 6.5 22H20V2H6.5A2.5 2.5 0 0 0 4 4.5v15z",
//   chevD:     "M6 9l6 6 6-6",
//   chevR:     "M9 18l6-6-6-6",
//   chevL:     "M15 18l-6-6 6-6",
//   panelOpen: "M3 12h18M3 6h18M3 18h18",
//   panelClose:"M3 6h7M3 12h7M3 18h7M17 6l4 6-4 6",
//   x:         "M18 6L6 18M6 6l12 12",
//   search:    "M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z",
//   send:      "M22 2L11 13M22 2L15 22 11 13 2 9l20-7z",
//   check:     "M20 6L9 17 4 12",
//   copy:      "M20 9H11a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2v-9a2 2 0 0 0-2-2zM5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1",
//   thumbUp:   "M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3",
//   thumbDown: "M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zM17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17",
//   share:     "M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8M16 6l-4-4-4 4M12 2v13",
//   trace:     "M3 3h18v18H3zM9 9h6M9 13h6M9 17h4",
//   bot:       "M12 2a4 4 0 0 1 4 4v2h2a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2V6a4 4 0 0 1 4-4zM9 10H7v2h2v-2zm8 0h-2v2h2v-2zm-5 4h-2v2h2v-2z",
//   user:      "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
//   snapshot:  "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H8",
//   reset:     "M1 4v6h6M23 20v-6h-6M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15",
//   sources:   "M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2zM22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z",
//   regen:     "M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15",
//   export:    "M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8M16 6l-4-4-4 4M12 2v13",
//   pdf:       "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M11 13H8M16 13h-2M11 17H8M16 17h-2",
//   tool:      "M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z",
//   attach:    "M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48",
//   weather:   "M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9z",
// };

// // ── Utilities ─────────────────────────────────────────────────────────────────
// const now = () => new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

// // ── Citation parser ───────────────────────────────────────────────────────────
// function parseSources(content) {
//   const sourcesMatch = content.match(/SOURCES:\s*\n([\s\S]+)$/i);
//   const mainText = sourcesMatch
//     ? content.slice(0, content.indexOf(sourcesMatch[0])).trim()
//     : content;
//   const sources = [];
//   if (sourcesMatch) {
//     const lines = sourcesMatch[1].trim().split("\n").filter(Boolean);
//     lines.forEach(line => {
//       const docMatch = line.match(/\[(\d+)\]\s*(.+?)\s*\|\s*[Pp]age\s*(\d+)/);
//       if (docMatch) {
//         sources.push({ num: parseInt(docMatch[1]), filename: docMatch[2].trim(), page: parseInt(docMatch[3]), type: "document" });
//         return;
//       }
//       const webMatch = line.match(/\[Web\s*(\d+)\]\s*(.+?)\s*—\s*(https?:\/\/\S+)/);
//       if (webMatch) {
//         sources.push({ num: parseInt(webMatch[1]), title: webMatch[2].trim(), url: webMatch[3].trim(), type: "web" });
//       }
//     });
//   }
//   return { mainText, sources };
// }

// function renderTextWithCitations(text, sources, onCiteClick) {
//   const parts = text.split(/(\[(?:Web\s*)?\d+\])/g);
//   return parts.map((part, i) => {
//     const match = part.match(/^\[(?:Web\s*)?(\d+)\]$/);
//     if (match) {
//       const num = parseInt(match[1]);
//       const isWeb = part.toLowerCase().includes("web");
//       const src = sources.find(s => s.num === num && (isWeb ? s.type === "web" : s.type === "document"))
//                || sources.find(s => s.num === num);
//       return (
//         <sup key={i} onClick={() => src && onCiteClick(src)}
//           title={src ? (src.type === "document" ? `${src.filename} — Page ${src.page}` : src.title) : ""}
//           style={{
//             cursor: src ? "pointer" : "default",
//             color: src ? (src.type === "web" ? C.amber : C.accent) : C.textMute,
//             fontWeight: 700, fontSize: "0.72em", marginLeft: 1,
//             padding: "1px 4px", borderRadius: 3,
//             background: src ? (src.type === "web" ? "#2a1e00" : "#16301a") : "transparent",
//             border: src ? `1px solid ${src.type === "web" ? C.amberDim : C.accentDim}` : "none",
//             userSelect: "none",
//           }}>
//           {part}
//         </sup>
//       );
//     }
//     return (
//       <span key={i}>
//         {part.split("\n").map((line, j, arr) => (
//           <span key={j}>{line}{j < arr.length - 1 && <br />}</span>
//         ))}
//       </span>
//     );
//   });
// }

// function SourcesList({ sources }) {
//   if (!sources.length) return null;
//   const open = (src) => {
//     if (src.type === "document") window.open(`/api/pdf/${encodeURIComponent(src.filename)}#page=${src.page}`, "_blank");
//     else window.open(src.url, "_blank");
//   };
//   return (
//     <div style={{ marginTop: 12, paddingTop: 10, borderTop: `1px solid ${C.border}` }}>
//       <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: C.textMute, marginBottom: 6 }}>
//         References
//       </div>
//       {sources.map((src, i) => (
//         <div key={i} onClick={() => open(src)}
//           style={{ display: "flex", alignItems: "flex-start", gap: 7, marginBottom: 5, cursor: "pointer", padding: "5px 7px", borderRadius: 7, transition: "background 0.15s" }}
//           onMouseEnter={e => e.currentTarget.style.background = C.surface2}
//           onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
//           <span style={{ minWidth: 20, height: 20, borderRadius: 4, flexShrink: 0, background: src.type === "document" ? C.accentDim : C.amberDim, border: `1px solid ${src.type === "document" ? C.accent : C.amber}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 9, fontWeight: 700, color: src.type === "document" ? C.accent : C.amber }}>
//             {src.num}
//           </span>
//           <div style={{ fontSize: 11.5, color: C.textSub, lineHeight: 1.5 }}>
//             {src.type === "document" ? (
//               <><span style={{ color: C.text, fontWeight: 500 }}>{src.filename}</span><span style={{ color: C.textMute }}> — Page {src.page}</span><span style={{ color: C.accentDim, fontSize: 10, marginLeft: 5 }}>↗ open PDF</span></>
//             ) : (
//               <><span style={{ color: C.text, fontWeight: 500 }}>{src.title}</span><span style={{ color: C.amberDim, fontSize: 10, marginLeft: 5 }}>↗ web</span></>
//             )}
//           </div>
//         </div>
//       ))}
//     </div>
//   );
// }

// // ── Message bubble ────────────────────────────────────────────────────────────
// function Message({ role, content, ts, usedRag, uploadedFile, webSearched, onRegenerate }) {
//   const [copied, setCopied] = useState(false);
//   const [liked, setLiked]   = useState(null);
//   const [showSrc, setShowSrc] = useState(true);
//   const isUser = role === "user";

//   const ActionBtn = ({ icon, title, onClick, active, activeColor }) => (
//     <button onClick={onClick} title={title}
//       style={{ background: "none", border: "none", cursor: "pointer", padding: "4px 5px", borderRadius: 6, display: "flex", alignItems: "center", opacity: 0.55, transition: "opacity 0.15s" }}
//       onMouseEnter={e => { e.currentTarget.style.opacity = "1"; e.currentTarget.style.background = C.surface2; }}
//       onMouseLeave={e => { e.currentTarget.style.opacity = "0.55"; e.currentTarget.style.background = "none"; }}>
//       <Icon d={icon} size={14} stroke={active ? (activeColor || C.accent) : C.textSub} />
//     </button>
//   );

//   const ragBadge = !isUser && usedRag !== null && usedRag !== undefined && (
//     <span style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 9.5, fontWeight: 600, letterSpacing: "0.03em", padding: "2px 7px", borderRadius: 20, background: usedRag ? "#16301a" : "#2a2210", border: `1px solid ${usedRag ? C.accentDim : C.amberDim}`, color: usedRag ? C.accent : C.amber, marginLeft: 6 }}>
//       {usedRag ? "RAG" : "🌐 Web"}
//     </span>
//   );

//   const webBadge = !isUser && webSearched && (
//     <span style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 9.5, fontWeight: 600, padding: "2px 7px", borderRadius: 20, background: C.tealBg, border: `1px solid ${C.tealDim}`, color: C.teal, marginLeft: 6 }}>
//       🌐 Tavily
//     </span>
//   );

//   return (
//     <div style={{ display: "flex", flexDirection: "column", alignItems: isUser ? "flex-end" : "flex-start", gap: 4 }}>
//       <div style={{ display: "flex", alignItems: "center", gap: 6, flexDirection: isUser ? "row-reverse" : "row" }}>
//         <div style={{ width: 26, height: 26, borderRadius: "50%", background: isUser ? C.accentDim : "#1a2610", border: `1px solid ${isUser ? C.accent : C.border}`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
//           <Icon d={isUser ? ICONS.user : ICONS.bot} size={13} stroke={isUser ? C.accent : C.textSub} />
//         </div>
//         <span style={{ fontSize: 11, color: C.textMute, display: "flex", alignItems: "center", flexWrap: "wrap", gap: 2 }}>
//           {isUser ? "You" : "RAG Assistant"} · {ts}{ragBadge}{webBadge}
//         </span>
//       </div>

//       {/* File attachment badge on user message */}
//       {isUser && uploadedFile && (
//         <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "5px 10px", background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 8, fontSize: 11, color: C.textSub, maxWidth: "78%" }}>
//           <Icon d={ICONS.attach} size={12} stroke={C.accent} />
//           <span style={{ color: C.accent, fontWeight: 500 }}>{uploadedFile}</span>
//           <span style={{ color: C.textMute }}>· attached</span>
//         </div>
//       )}

//       <div style={{ maxWidth: "78%", background: isUser ? C.userBub : C.botBub, border: `1px solid ${isUser ? C.accentDim : C.border}`, borderRadius: isUser ? "14px 4px 14px 14px" : "4px 14px 14px 14px", padding: "10px 14px", lineHeight: 1.65, fontSize: 14, color: C.text }}>
//         {isUser ? (
//           <span style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>{content}</span>
//         ) : (() => {
//           const { mainText, sources } = parseSources(content);
//           const onCiteClick = src => {
//             if (src.type === "document") window.open(`/api/pdf/${encodeURIComponent(src.filename)}#page=${src.page}`, "_blank");
//             else window.open(src.url, "_blank");
//           };
//           return (
//             <>
//               <div style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
//                 {renderTextWithCitations(mainText, sources, onCiteClick)}
//               </div>
//               {showSrc && <SourcesList sources={sources} />}
//             </>
//           );
//         })()}
//       </div>

//       {!isUser && (
//         <div style={{ display: "flex", alignItems: "center", gap: 1, paddingLeft: 4, marginTop: -2 }}>
//           <ActionBtn icon={copied ? ICONS.check : ICONS.copy} title="Copy" onClick={() => { navigator.clipboard.writeText(content); setCopied(true); setTimeout(() => setCopied(false), 1500); }} active={copied} activeColor={C.accent} />
//           <ActionBtn icon={ICONS.thumbUp} title="Good response" onClick={() => setLiked(l => l === "up" ? null : "up")} active={liked === "up"} activeColor={C.accent} />
//           <ActionBtn icon={ICONS.thumbDown} title="Bad response" onClick={() => setLiked(l => l === "down" ? null : "down")} active={liked === "down"} activeColor={C.danger} />
//           <ActionBtn icon={ICONS.share} title="Copy to clipboard" onClick={() => navigator.clipboard.writeText(content)} />
//           {onRegenerate && <ActionBtn icon={ICONS.regen} title="Regenerate" onClick={onRegenerate} />}
//           <div style={{ width: 1, height: 14, background: C.border, margin: "0 3px" }} />
//           <ActionBtn icon={ICONS.sources} title={showSrc ? "Hide sources" : "Show sources"} onClick={() => setShowSrc(s => !s)} active={showSrc} activeColor={C.accent} />
//         </div>
//       )}
//     </div>
//   );
// }

// // ── Typing dots ───────────────────────────────────────────────────────────────
// function TypingDots() {
//   return (
//     <div style={{ display: "flex", alignItems: "flex-start", gap: 6 }}>
//       <div style={{ width: 26, height: 26, borderRadius: "50%", background: "#1a2610", border: `1px solid ${C.border}`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
//         <Icon d={ICONS.bot} size={13} stroke={C.textSub} />
//       </div>
//       <div style={{ background: C.botBub, border: `1px solid ${C.border}`, borderRadius: "4px 14px 14px 14px", padding: "12px 16px", display: "flex", gap: 5, alignItems: "center" }}>
//         {[0, 0.18, 0.36].map((delay, i) => (
//           <div key={i} style={{ width: 7, height: 7, borderRadius: "50%", background: C.accentDim, animation: "pulse 1.2s ease-in-out infinite", animationDelay: `${delay}s` }} />
//         ))}
//       </div>
//     </div>
//   );
// }

// // ── Trace panel ───────────────────────────────────────────────────────────────
// function TracePanel({ trace, webSearchResults, mcpCalls, status, statusError }) {
//   const [tab, setTab] = useState("trace");
//   return (
//     <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
//       {/* Tabs */}
//       <div style={{ display: "flex", borderBottom: `1px solid ${C.border}`, flexShrink: 0 }}>
//         {[["trace","Trace",ICONS.trace,C.amber], ["web","Web Search",ICONS.globe,C.teal], ["mcp","MCP Tools",ICONS.tool,C.accent]].map(([id,label,ic,col]) => (
//           <button key={id} onClick={() => setTab(id)} style={{ flex:1, padding:"10px 4px", background:"none", border:"none", borderBottom:`2px solid ${tab===id?col:"transparent"}`, cursor:"pointer", fontSize:11, fontWeight:600, color:tab===id?col:C.textMute, display:"flex", alignItems:"center", justifyContent:"center", gap:4, transition:"all 0.15s" }}>
//             <Icon d={ic} size={12} stroke={tab===id?col:C.textMute} />{label}
//           </button>
//         ))}
//       </div>

//       <div style={{ flex: 1, overflowY: "auto", padding: "12px 14px" }}>
//         {tab === "trace" && (
//           !trace ? (
//             <div style={{ color: C.textMute, fontSize: 12, textAlign: "center", marginTop: 40, lineHeight: 1.7 }}>
//               Pipeline step timings<br />appear here after each query
//             </div>
//           ) : (
//             <pre style={{ fontFamily: "'JetBrains Mono','Fira Code',monospace", fontSize: 11, color: C.textSub, lineHeight: 1.75, whiteSpace: "pre-wrap", wordBreak: "break-word", margin: 0 }}>
//               {trace}
//             </pre>
//           )
//         )}

//         {tab === "web" && (
//           webSearchResults?.length > 0 ? (
//             <div>
//               <div style={{ fontSize: 11, color: C.teal, fontWeight: 600, marginBottom: 10 }}>
//                 {webSearchResults.length} web results retrieved via Tavily
//               </div>
//               {webSearchResults.map((r, i) => (
//                 <div key={i} style={{ marginBottom: 10, padding: "8px 10px", background: C.surface2, borderRadius: 8, border: `1px solid ${C.border}` }}>
//                   <div style={{ fontSize: 11.5, fontWeight: 600, color: C.text, marginBottom: 3 }}>{r.title}</div>
//                   <div style={{ fontSize: 10.5, color: C.textSub, marginBottom: 4, lineHeight: 1.5 }}>{r.content?.slice(0,200)}…</div>
//                   <a href={r.url} target="_blank" rel="noreferrer" style={{ fontSize: 10, color: C.amber }}>{r.url?.slice(0,60)}</a>
//                 </div>
//               ))}
//             </div>
//           ) : (
//             <div style={{ color: C.textMute, fontSize: 12, textAlign: "center", marginTop: 40, lineHeight: 1.7 }}>
//               Enable 🌐 Web Search in the header,<br />then ask a question to see live results.
//             </div>
//           )
//         )}

//         {tab === "mcp" && (
//           mcpCalls?.length > 0 ? (
//             <div>
//               <div style={{ fontSize: 11, color: C.accent, fontWeight: 600, marginBottom: 10 }}>
//                 {mcpCalls.length} MCP tool call{mcpCalls.length !== 1 ? "s" : ""} this session
//               </div>
//               {mcpCalls.map((call, i) => (
//                 <div key={i} style={{ marginBottom: 10, padding: "8px 10px", background: C.surface2, borderRadius: 8, border: `1px solid ${C.border}` }}>
//                   <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
//                     <span style={{ fontSize: 11.5, fontWeight: 700, color: C.accent }}>⚡ {call.tool}</span>
//                     <span style={{ fontSize: 10, color: call.ok ? C.accent : C.danger }}>{call.ok ? "✓ ok" : "✗ error"}</span>
//                   </div>
//                   <pre style={{ fontSize: 10, color: C.textSub, margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
//                     {JSON.stringify(call.params, null, 1).slice(0,200)}
//                   </pre>
//                   {call.preview && <div style={{ fontSize: 10.5, color: C.text, marginTop: 4 }}>{call.preview}</div>}
//                 </div>
//               ))}
//             </div>
//           ) : (
//             <div style={{ color: C.textMute, fontSize: 12, textAlign: "center", marginTop: 40, lineHeight: 1.7 }}>
//               MCP tool calls (weather, crop<br />calendar, unit converter…)<br />appear here after each query.
//             </div>
//           )
//         )}
//       </div>

//       {/* Pipeline config at bottom */}
//       <div style={{ padding: "12px 14px", borderTop: `1px solid ${C.border}` }}>
//         <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: C.textMute, marginBottom: 8 }}>Pipeline</div>
//         {[
//           ["Vector DB",  status?.vector_db || "ChromaDB"],
//           ["Retrieval",  status?.retrieval || "BM25 + Embeddings"],
//           ["Fusion",     status?.fusion    || "RRF"],
//           ["Chunks",     (status?.chunk_count || 0).toLocaleString()],
//         ].map(([k, v]) => (
//           <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "4px 8px", background: C.surface2, borderRadius: 6, marginBottom: 4, fontSize: 12 }}>
//             <span style={{ color: C.textSub }}>{k}</span>
//             <span style={{ color: C.text }}>{v}</span>
//           </div>
//         ))}
//         {statusError && (
//           <div style={{ marginTop: 8, background: C.dangerBg, border: `1px solid ${C.danger}`, borderRadius: 8, padding: "8px 10px", fontSize: 11.5, color: "#e8938a", lineHeight: 1.5 }}>
//             {statusError}
//           </div>
//         )}
//       </div>
//     </div>
//   );
// }

// // ── Welcome screen ────────────────────────────────────────────────────────────
// function Welcome({ onSend }) {
//   const prompts = [
//     "What wheat diseases are monitored in Punjab?",
//     "Is today's weather good for wheat sowing in Lahore?",
//     "Convert 50 acres to hectares",
//     "Which FAO guidelines cover Ug99 rust?",
//     "Summarise PARC's 2023-24 research highlights",
//     "What is the role of the Agriculture Extension Wing?",
//   ];
//   return (
//     <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: 32, gap: 28 }}>
//       <div style={{ textAlign: "center" }}>
//         <div style={{ fontSize: 40, marginBottom: 12 }}>🌾</div>
//         <div style={{ fontSize: 22, fontWeight: 700, color: C.text, letterSpacing: "-0.02em", marginBottom: 6 }}>
//           Agricultural RAG Assistant
//         </div>
//         <div style={{ fontSize: 13, color: C.textSub, maxWidth: 440, lineHeight: 1.6 }}>
//           Grounded in PARC Annual Report, FAO Crop Guidelines, and Punjab Agri Rules.
//           MCP tools: weather, crop calendar, unit converter, Tavily web search.
//         </div>
//       </div>
//       <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, width: "100%", maxWidth: 560 }}>
//         {prompts.map((p, i) => (
//           <button key={i} onClick={() => onSend(p)}
//             style={{ background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 10, padding: "10px 14px", color: C.textSub, fontSize: 12, textAlign: "left", cursor: "pointer", lineHeight: 1.5, transition: "border-color 0.15s, color 0.15s", fontFamily: "inherit" }}
//             onMouseEnter={e => { e.currentTarget.style.borderColor = C.accent; e.currentTarget.style.color = C.text; }}
//             onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.color = C.textSub; }}>
//             {p}
//           </button>
//         ))}
//       </div>
//     </div>
//   );
// }

// // ── Sidebar item ──────────────────────────────────────────────────────────────
// const SideItem = ({ icon, label, active, onClick, indent = 0, muted = false }) => (
//   <div onClick={onClick}
//     style={{ display: "flex", alignItems: "center", gap: 8, padding: `7px 12px 7px ${12 + indent * 16}px`, borderRadius: 8, cursor: "pointer", margin: "1px 6px", background: active ? C.accentBg : "transparent", color: active ? C.accent : muted ? C.textMute : C.textSub, fontSize: 13, fontWeight: active ? 600 : 400, transition: "all 0.12s" }}>
//     {icon}
//     <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{label}</span>
//   </div>
// );

// // ── Modal ─────────────────────────────────────────────────────────────────────
// const Modal = ({ open, onClose, title, children, width = 480 }) => {
//   if (!open) return null;
//   return (
//     <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center" }}
//       onClick={onClose}>
//       <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 14, padding: "24px 28px", width, maxWidth: "90vw", maxHeight: "80vh", overflowY: "auto" }}
//         onClick={e => e.stopPropagation()}>
//         <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
//           <span style={{ fontSize: 16, fontWeight: 700, color: C.text }}>{title}</span>
//           <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer" }}>
//             <Icon d={ICONS.x} stroke={C.textSub} size={18} />
//           </button>
//         </div>
//         {children}
//       </div>
//     </div>
//   );
// };

// const TextInput = ({ label, value, onChange, placeholder, multiline = false, autoFocus = false }) => (
//   <div style={{ marginBottom: 14 }}>
//     {label && <label style={{ fontSize: 12, color: C.textSub, display: "block", marginBottom: 6 }}>{label}</label>}
//     {multiline
//       ? <textarea value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
//           style={{ width: "100%", background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 8, padding: "10px 12px", color: C.text, fontSize: 13, fontFamily: "inherit", outline: "none", resize: "vertical", minHeight: 80, boxSizing: "border-box" }} />
//       : <input value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder} autoFocus={autoFocus}
//           style={{ width: "100%", background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 8, padding: "10px 12px", color: C.text, fontSize: 13, fontFamily: "inherit", outline: "none", boxSizing: "border-box" }} />
//     }
//   </div>
// );

// const Btn = ({ children, onClick, variant = "ghost", danger = false, style: sx = {}, disabled = false }) => {
//   const base = { display: "inline-flex", alignItems: "center", gap: 6, padding: "7px 12px", borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: disabled ? "not-allowed" : "pointer", border: "none", transition: "all 0.15s", opacity: disabled ? 0.5 : 1, fontFamily: "inherit" };
//   const variants = {
//     primary: { background: C.accent, color: C.bg },
//     ghost:   { background: "transparent", color: danger ? C.danger : C.textSub, border: `1px solid ${danger ? C.danger + "55" : C.border}` },
//     surface: { background: C.surface2, color: C.text, border: `1px solid ${C.border}` },
//   };
//   return <button style={{ ...base, ...variants[variant], ...sx }} onClick={onClick} disabled={disabled}>{children}</button>;
// };

// function StatusBadge({ chunks }) {
//   const ok = chunks > 0;
//   return (
//     <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "4px 10px", borderRadius: 20, background: ok ? "#1a3310" : "#3a1010", border: `1px solid ${ok ? C.accentDim : C.danger}`, fontSize: 12, color: ok ? C.accent : "#e74c3c", whiteSpace: "nowrap" }}>
//       <div style={{ width: 7, height: 7, borderRadius: "50%", background: ok ? C.accent : C.danger, boxShadow: ok ? `0 0 6px ${C.accent}` : "none" }} />
//       {ok ? `${chunks.toLocaleString()} chunks` : "Empty"}
//     </div>
//   );
// }

// // ── PDF chat export ───────────────────────────────────────────────────────────
// function exportChatAsPDF(messages, sessionTitle) {
//   if (!messages || messages.length === 0) {
//     alert("No messages to export yet.");
//     return;
//   }
//   const escHtml = s => s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
//   const date = new Date().toLocaleString();
//   const rows = messages.map(m => {
//     const isUser = m.role === "user";
//     const label = isUser ? "You" : "RAG Assistant";
//     const align = isUser ? "right" : "left";
//     const mlAuto = isUser ? "auto" : "0";
//     const bg = isUser ? "#1a2e10" : "#0f1a08";
//     const borderColor = isUser ? "#4a7a1e" : "#2a3d1e";
//     return `
//       <div style="margin-bottom:18px;text-align:${align}">
//         <div style="font-size:11px;color:#7a9460;margin-bottom:4px">${label} · ${m.ts || ""}</div>
//         <div style="display:inline-block;max-width:78%;background:${bg};border:1px solid ${borderColor};border-radius:12px;padding:10px 14px;font-size:13px;line-height:1.7;color:#dde8cc;white-space:pre-wrap;word-break:break-word;margin-left:${mlAuto};text-align:left">${escHtml(m.content)}</div>
//       </div>`;
//   }).join("");

//   const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"/><title>${escHtml(sessionTitle || "RAG Chat")}</title>
//   <style>@page{size:A4;margin:20mm 18mm}body{background:#0c1108;color:#dde8cc;font-family:'Segoe UI',sans-serif;font-size:13px;padding:0}
//   .cover{border-bottom:1px solid #2a3d1e;padding-bottom:16px;margin-bottom:24px}.cover h1{font-size:20px;font-weight:700;color:#dde8cc;margin-bottom:6px}
//   .cover .meta{font-size:11px;color:#7a9460}@media print{body{-webkit-print-color-adjust:exact;print-color-adjust:exact}}</style>
//   </head><body>
//   <div class="cover"><h1>🌾 ${escHtml(sessionTitle || "RAG Conversation")}</h1>
//   <div class="meta">Exported ${date} · ${messages.length} messages</div></div>
//   ${rows}</body></html>`;

//   const iframe = document.createElement("iframe");
//   iframe.style.cssText = "position:fixed;top:-9999px;left:-9999px;width:0;height:0;opacity:0;";
//   document.body.appendChild(iframe);
//   iframe.contentDocument.open();
//   iframe.contentDocument.write(html);
//   iframe.contentDocument.close();
//   setTimeout(() => {
//     iframe.contentWindow.print();
//     setTimeout(() => document.body.removeChild(iframe), 3000);
//   }, 500);
// }

// // ═══════════════════════════════════════════════════════════════════════════════
// //  MAIN COMPONENT
// // ═══════════════════════════════════════════════════════════════════════════════
// const EMOJIS = ["🌱", "🌾", "🪴", "🌽", "🍃", "🌿", "🌻", "🌴", "🫘", "🍀"];

// export default function ProjectManager({ username = "user", token, onLogout }) {
//   // ── Projects / chats ──────────────────────────────────────────────────────
//   const [projects, setProjects]               = useState([]);
//   const [expandedProjects, setExpandedProjects] = useState(new Set());
//   const [selectedProject, setSelectedProject] = useState(null);
//   const [activeSession, setActiveSession]     = useState(null);
//   const [msgCache, setMsgCache]               = useState({});
//   const [loading, setLoading]                 = useState(false);
//   const [trace, setTrace]                     = useState(null);
//   const [input, setInput]                     = useState("");

//   // ── New: sidebar collapsed ────────────────────────────────────────────────
//   const [sidebarOpen, setSidebarOpen]         = useState(true);

//   // ── New: web search (Tavily) ──────────────────────────────────────────────
//   const [webSearch, setWebSearch]             = useState(false);
//   const [webSearchResults, setWebSearchResults] = useState([]);

//   // ── New: MCP call log ─────────────────────────────────────────────────────
//   const [mcpCalls, setMcpCalls]               = useState([]);

//   // ── New: file upload state ────────────────────────────────────────────────
//   const [pendingFile, setPendingFile]         = useState(null); // { name, fileId } after upload
//   const [uploadingFile, setUploadingFile]     = useState(false);
//   const fileInputRef                          = useRef(null);

//   // ── Backend ───────────────────────────────────────────────────────────────
//   const [apiSessions, setApiSessions]         = useState([]);
//   const [status, setStatus]                   = useState(null);
//   const [chunkCount, setChunkCount]           = useState(0);
//   const [statusError, setStatusError]         = useState(null);
//   const [sideSearch, setSideSearch]           = useState("");
//   const [showTrace, setShowTrace]             = useState(true);

//   // ── Modals ────────────────────────────────────────────────────────────────
//   const [showNewProject, setShowNewProject]   = useState(false);
//   const [newProjName, setNewProjName]         = useState("");
//   const [newProjDesc, setNewProjDesc]         = useState("");
//   const [newProjEmoji, setNewProjEmoji]       = useState("🌱");
//   const [showRename, setShowRename]           = useState(false);
//   const [renameTarget, setRenameTarget]       = useState(null);
//   const [renameName, setRenameName]           = useState("");
//   const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
//   const [deleteTarget, setDeleteTarget]       = useState(null);

//   const chatRef     = useRef(null);
//   const textareaRef = useRef(null);

//   const authHeaders = () => token
//     ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` }
//     : { "Content-Type": "application/json" };

//   // ── Scroll ────────────────────────────────────────────────────────────────
//   useEffect(() => {
//     if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
//   }, [msgCache, activeSession, loading]);

//   // ── Poll /api/status ──────────────────────────────────────────────────────
//   useEffect(() => {
//     const fetch_ = () => {
//       fetch("/api/status").then(r => r.json()).then(d => {
//         setStatus(d); setChunkCount(d.chunk_count || 0);
//         setStatusError(d.vector_store_error || d.pipeline_error || null);
//       }).catch(err => { setStatusError(`Cannot reach API: ${err.message}`); setChunkCount(0); });
//     };
//     fetch_(); const id = setInterval(fetch_, 8000); return () => clearInterval(id);
//   }, []);

//   // ── Load sessions ─────────────────────────────────────────────────────────
//   const fetchApiSessions = useCallback(() => {
//     fetch("/api/sessions", { headers: authHeaders() })
//       .then(r => r.json())
//       .then(d => setApiSessions(d.sessions || []))
//       .catch(() => {});
//   }, [token]);

//   useEffect(() => { fetchApiSessions(); }, [fetchApiSessions]);

//   // ── Load projects from localStorage ───────────────────────────────────────
//   useEffect(() => {
//     try {
//       const saved = localStorage.getItem(`rag_projects_${username}`);
//       if (saved) setProjects(JSON.parse(saved));
//     } catch (_) {}
//   }, [username]);

//   const saveProjects = (ps) => {
//     setProjects(ps);
//     try { localStorage.setItem(`rag_projects_${username}`, JSON.stringify(ps)); } catch (_) {}
//   };

//   // ── Open session ──────────────────────────────────────────────────────────
//   const openNewChat = (projectId = null) => {
//     const sessionId = crypto.randomUUID();
//     const proj = projectId ? projects.find(p => p.id === projectId) : null;
//     const session = { sessionId, projectId, title: proj ? `${proj.emoji} New chat` : "New chat" };
//     setActiveSession(session); setTrace(null); setInput("");
//     setPendingFile(null); setWebSearchResults([]); setMcpCalls([]);
//     if (projectId) {
//       const updated = projects.map(p => {
//         if (p.id !== projectId) return p;
//         return { ...p, sessions: [...(p.sessions || []), { sessionId, title: "New chat", date: new Date().toISOString().slice(0, 10) }] };
//       });
//       saveProjects(updated);
//     }
//   };

//   const openExistingSession = (sessionId, projectId = null) => {
//     const proj = projectId ? projects.find(p => p.id === projectId) : null;
//     const apiSess = apiSessions.find(s => s.session_id === sessionId);
//     const title = apiSess?.title || apiSess?.preview || "Chat";
//     setActiveSession({ sessionId, projectId, title: proj ? `${proj.emoji} ${title}` : title });
//     setTrace(null); setInput(""); setPendingFile(null); setWebSearchResults([]); setMcpCalls([]);
//     if (!msgCache[sessionId]) {
//       fetch(`/api/sessions/${sessionId}`, { headers: authHeaders() })
//         .then(r => r.json())
//         .then(d => {
//           const msgs = (d.messages || []).map(m => ({ role: m.role, content: m.content, ts: m.ts || now(), usedRag: m.used_rag }));
//           setMsgCache(prev => ({ ...prev, [sessionId]: msgs }));
//         }).catch(() => {});
//     }
//   };

//   // ── FILE UPLOAD ("+") ─────────────────────────────────────────────────────
//   const handleFileSelect = async (e) => {
//     const file = e.target.files?.[0];
//     if (!file || !activeSession) return;
//     e.target.value = "";

//     setUploadingFile(true);
//     try {
//       const fd = new FormData();
//       fd.append("file", file);
//       const r = await fetch("/api/upload", {
//         method: "POST",
//         headers: token ? { Authorization: `Bearer ${token}` } : {},
//         body: fd,
//       });
//       if (!r.ok) throw new Error(`Upload failed (${r.status})`);
//       const data = await r.json();
//       setPendingFile({ name: file.name, fileId: data.file_id });
//     } catch (err) {
//       alert(`File upload failed: ${err.message}\n\nMake sure the API server is running and /api/upload endpoint exists.`);
//     } finally {
//       setUploadingFile(false);
//     }
//   };

//   // ── SEND MESSAGE ──────────────────────────────────────────────────────────
//   const sendMessage = async (text) => {
//     const q = (text || input).trim();
//     if (!q || loading || !activeSession) return;
//     setInput("");

//     const attachedFile = pendingFile;
//     setPendingFile(null);

//     const userMsg = {
//       role: "user", content: q, ts: now(),
//       uploadedFile: attachedFile?.name || null,
//     };
//     setMsgCache(prev => ({
//       ...prev,
//       [activeSession.sessionId]: [...(prev[activeSession.sessionId] || []), userMsg],
//     }));
//     setLoading(true);
//     setTrace(null);
//     setWebSearchResults([]);

//     try {
//       // ── Step 1: Tavily web search (if enabled) ────────────────────────────
//       let webCtx = "";
//       let webResults = [];
//       if (webSearch) {
//         try {
//           const wr = await fetch("/api/mcp/run", {
//             method: "POST",
//             headers: authHeaders(),
//             body: JSON.stringify({ query: q, session_id: activeSession.sessionId }),
//           });
//           if (wr.ok) {
//             const wd = await wr.json();
//             // Try tavily_search tool result
//             if (wd.results?.tavily_search?.results?.length) {
//               webResults = wd.results.tavily_search.results;
//               setWebSearchResults(webResults);
//               webCtx = webResults.slice(0, 4).map((r, i) => `[Web ${i+1}] ${r.title}\n${r.content}`).join("\n\n");
//               // Log MCP call
//               setMcpCalls(prev => [...prev, {
//                 tool: "tavily_search", ok: true,
//                 params: { query: q },
//                 preview: `${webResults.length} results from Tavily`,
//               }]);
//             }
//             // Also capture any other MCP tool calls (weather, calendar, etc.)
//             if (wd.mcp_calls) {
//               wd.mcp_calls.forEach(c => setMcpCalls(prev => [...prev, c]));
//             }
//           }
//         } catch (e) {
//           console.warn("[Web search] MCP run failed:", e.message);
//         }
//       }

//       // ── Step 2: Build enriched query with web context ─────────────────────
//       let enrichedQuery = q;
//       if (attachedFile?.fileId) {
//         enrichedQuery = `[Referring to uploaded file: ${attachedFile.name} (id:${attachedFile.fileId})]\n${q}`;
//       }
//       if (webCtx) {
//         enrichedQuery = `${enrichedQuery}\n\nLIVE WEB SEARCH RESULTS (use these for current information):\n${webCtx}`;
//       }

//       // ── Step 3: RAG chat ───────────────────────────────────────────────────
//       const res = await fetch("/api/chat", {
//         method: "POST",
//         headers: authHeaders(),
//         body: JSON.stringify({
//           session_id: activeSession.sessionId,
//           query: enrichedQuery,
//           ...(attachedFile?.fileId ? { file_id: attachedFile.fileId } : {}),
//         }),
//       });
//       const data = await res.json();

//       // Capture any MCP calls returned from the pipeline
//       if (data.mcp_calls) {
//         data.mcp_calls.forEach(c => setMcpCalls(prev => [...prev, c]));
//       }

//       const botMsg = {
//         role: "assistant",
//         content: data.response || "No response received.",
//         ts: now(),
//         usedRag: data.used_rag,
//         webSearched: webResults.length > 0,
//       };
//       setMsgCache(prev => ({
//         ...prev,
//         [activeSession.sessionId]: [...(prev[activeSession.sessionId] || []), botMsg],
//       }));
//       if (data.trace) setTrace(data.trace);

//       // Auto-title
//       const currentMsgs = msgCache[activeSession.sessionId] || [];
//       if (currentMsgs.filter(m => m.role === "user").length === 0) {
//         const autoTitle = q.slice(0, 40) + (q.length > 40 ? "…" : "");
//         setActiveSession(prev => ({ ...prev, title: autoTitle }));
//         if (activeSession.projectId) {
//           const updated = projects.map(p => {
//             if (p.id !== activeSession.projectId) return p;
//             return { ...p, sessions: (p.sessions || []).map(s => s.sessionId === activeSession.sessionId ? { ...s, title: autoTitle } : s) };
//           });
//           saveProjects(updated);
//         }
//       }
//     } catch (err) {
//       const errMsg = { role: "assistant", content: `❌ Could not reach the backend.\n\nError: ${err.message}`, ts: now() };
//       setMsgCache(prev => ({ ...prev, [activeSession.sessionId]: [...(prev[activeSession.sessionId] || []), errMsg] }));
//     } finally {
//       setLoading(false);
//       fetchApiSessions();
//     }
//   };

//   // ── Delete session ────────────────────────────────────────────────────────
//   const deleteSession = async (sessionId) => {
//     if (!confirm("Delete this conversation permanently?")) return;
//     await fetch(`/api/sessions/${sessionId}`, { method: "DELETE", headers: authHeaders() }).catch(() => {});
//     setMsgCache(prev => { const n = { ...prev }; delete n[sessionId]; return n; });
//     if (activeSession?.sessionId === sessionId) setActiveSession(null);
//     fetchApiSessions();
//   };

//   // ── Rename ────────────────────────────────────────────────────────────────
//   const openRename = (type, id, currentName, e) => {
//     e?.stopPropagation();
//     setRenameTarget({ type, id });
//     setRenameName(currentName || "");
//     setShowRename(true);
//   };

//   const commitRename = async () => {
//     if (!renameName.trim() || !renameTarget) return;
//     if (renameTarget.type === "session") {
//       await fetch(`/api/sessions/${renameTarget.id}`, {
//         method: "PATCH", headers: authHeaders(),
//         body: JSON.stringify({ title: renameName.trim() }),
//       }).catch(() => {});
//       fetchApiSessions();
//       if (activeSession?.sessionId === renameTarget.id) {
//         setActiveSession(prev => ({ ...prev, title: renameName.trim() }));
//       }
//     } else if (renameTarget.type === "project") {
//       const updated = projects.map(p => p.id === renameTarget.id ? { ...p, name: renameName.trim() } : p);
//       saveProjects(updated);
//       if (selectedProject?.id === renameTarget.id) setSelectedProject(prev => ({ ...prev, name: renameName.trim() }));
//     }
//     setShowRename(false); setRenameTarget(null); setRenameName("");
//   };

//   // ── Project CRUD ──────────────────────────────────────────────────────────
//   const createProject = () => {
//     if (!newProjName.trim()) return;
//     const proj = { id: "p" + Date.now(), name: newProjName.trim(), emoji: newProjEmoji, description: newProjDesc.trim(), createdAt: new Date().toISOString().slice(0, 10), sessions: [] };
//     saveProjects([...projects, proj]);
//     setNewProjName(""); setNewProjDesc(""); setNewProjEmoji("🌱");
//     setShowNewProject(false);
//     setExpandedProjects(prev => new Set([...prev, proj.id]));
//   };

//   const deleteProject = (id) => {
//     saveProjects(projects.filter(p => p.id !== id));
//     if (selectedProject?.id === id) setSelectedProject(null);
//     if (activeSession?.projectId === id) setActiveSession(null);
//     setShowDeleteConfirm(false); setDeleteTarget(null);
//   };

//   // ── Filtered lists ────────────────────────────────────────────────────────
//   const search = sideSearch.toLowerCase();
//   const allProjectSessionIds = new Set(projects.flatMap(p => (p.sessions || []).map(ss => ss.sessionId)));
//   const filteredApiSessions  = apiSessions.filter(s => !allProjectSessionIds.has(s.session_id) && (!search || (s.title || s.preview || "").toLowerCase().includes(search)));
//   const filteredProjects     = projects.filter(p => !search || p.name.toLowerCase().includes(search));
//   const currentMessages      = (activeSession && msgCache[activeSession.sessionId]) || [];

//   // ─────────────────────────────────────────────────────────────────────────
//   return (
//     <>
//       <style>{`
//         * { box-sizing: border-box; margin: 0; padding: 0; }
//         body { background: ${C.bg}; }
//         ::-webkit-scrollbar { width: 5px; }
//         ::-webkit-scrollbar-track { background: transparent; }
//         ::-webkit-scrollbar-thumb { background: ${C.border}; border-radius: 4px; }
//         @keyframes pulse { 0%,100% { opacity:0.3; transform:scale(0.85); } 50% { opacity:1; transform:scale(1.1); } }
//         .sidebar-item-actions { display: none; }
//         .sidebar-row:hover .sidebar-item-actions { display: flex; }
//       `}</style>

//       <div style={{ display: "flex", height: "100vh", fontFamily: "'Inter','Segoe UI',system-ui,sans-serif", color: C.text, overflow: "hidden", background: C.bg }}>

//         {/* ══════════════════════════════════════════════════════════════════
//             SIDEBAR  (Feature 1: collapsible)
//         ══════════════════════════════════════════════════════════════════ */}
//         <div style={{
//           width: sidebarOpen ? 248 : 0,
//           background: C.surface,
//           borderRight: sidebarOpen ? `1px solid ${C.border}` : "none",
//           display: "flex", flexDirection: "column", height: "100vh", flexShrink: 0,
//           overflow: "hidden",
//           transition: "width 0.2s ease",
//         }}>
//           {/* Logo + search */}
//           <div style={{ padding: "14px 12px 10px", borderBottom: `1px solid ${C.border}`, flexShrink: 0 }}>
//             <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
//               <Icon d={ICONS.leaf} size={20} stroke={C.accent} />
//               <span style={{ fontWeight: 700, fontSize: 15, color: C.text }}>Agentic RAG</span>
//             </div>
//             <div style={{ display: "flex", alignItems: "center", gap: 6, background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 8, padding: "6px 10px" }}>
//               <Icon d={ICONS.search} size={14} />
//               <input value={sideSearch} onChange={e => setSideSearch(e.target.value)} placeholder="Search…"
//                 style={{ flex: 1, background: "transparent", border: "none", outline: "none", color: C.text, fontSize: 12, fontFamily: "inherit" }} />
//             </div>
//           </div>

//           <div style={{ flex: 1, overflowY: "auto", padding: "8px 0" }}>
//             {/* New Chat */}
//             <div style={{ padding: "4px 8px 8px" }}>
//               <Btn variant="surface" onClick={() => openNewChat(null)} style={{ width: "100%", justifyContent: "center" }}>
//                 <Icon d={ICONS.plus} size={14} stroke={C.accent} /> New chat
//               </Btn>
//             </div>

//             {/* ── Recent Chats ── */}
//             <div style={{ padding: "8px 14px 4px", fontSize: 11, fontWeight: 700, color: C.textMute, letterSpacing: "0.08em" }}>RECENT CHATS</div>
//             {filteredApiSessions.length === 0 && (
//               <div style={{ fontSize: 12, color: C.textMute, padding: "4px 18px" }}>No chats yet</div>
//             )}
//             {filteredApiSessions.map(s => {
//               const label = s.title || s.preview || "Untitled";
//               return (
//                 <div key={s.session_id} className="sidebar-row"
//                   style={{ position: "relative", display: "flex", alignItems: "center", margin: "1px 6px", borderRadius: 8, background: activeSession?.sessionId === s.session_id ? C.accentBg : "transparent" }}>
//                   <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 8, padding: "7px 36px 7px 12px", color: activeSession?.sessionId === s.session_id ? C.accent : C.textSub, fontSize: 13, fontWeight: activeSession?.sessionId === s.session_id ? 600 : 400, cursor: "pointer", overflow: "hidden" }}
//                     onClick={() => openExistingSession(s.session_id, null)}>
//                     <Icon d={ICONS.chat} size={14} stroke="currentColor" />
//                     <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{label}</span>
//                   </div>
//                   {/* Feature 4: rename + delete for recent chats */}
//                   <div className="sidebar-item-actions" style={{ position: "absolute", right: 6, gap: 2 }}>
//                     <button onClick={e => openRename("session", s.session_id, label, e)} title="Rename"
//                       style={{ background: "none", border: "none", cursor: "pointer", padding: 3, borderRadius: 4, opacity: 0.6 }}>
//                       <Icon d={ICONS.edit} size={11} stroke={C.textSub} />
//                     </button>
//                     <button onClick={e => { e.stopPropagation(); deleteSession(s.session_id); }} title="Delete"
//                       style={{ background: "none", border: "none", cursor: "pointer", padding: 3, borderRadius: 4, opacity: 0.6 }}>
//                       <Icon d={ICONS.trash} size={11} stroke={C.danger} />
//                     </button>
//                   </div>
//                 </div>
//               );
//             })}

//             {/* ── Projects ── */}
//             <div style={{ padding: "12px 14px 4px", fontSize: 11, fontWeight: 700, color: C.textMute, letterSpacing: "0.08em", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
//               <span>PROJECTS</span>
//               <button onClick={() => setShowNewProject(true)} style={{ background: "none", border: "none", cursor: "pointer", padding: 2 }}>
//                 <Icon d={ICONS.plus} size={14} stroke={C.accent} />
//               </button>
//             </div>

//             {filteredProjects.map(proj => {
//               const isExpanded = expandedProjects.has(proj.id);
//               const isSelected = activeSession?.projectId === proj.id;
//               return (
//                 <div key={proj.id}>
//                   <div className="sidebar-row" style={{ display: "flex", alignItems: "center", margin: "1px 6px", borderRadius: 8, background: isSelected ? C.accentBg : "transparent", position: "relative" }}>
//                     <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 8, padding: "7px 8px 7px 12px", color: isSelected ? C.accent : C.textSub, fontSize: 13, fontWeight: isSelected ? 600 : 400, cursor: "pointer", overflow: "hidden" }}
//                       onClick={() => { setSelectedProject(proj); setExpandedProjects(prev => new Set([...prev, proj.id])); }}>
//                       <span style={{ fontSize: 15 }}>{proj.emoji}</span>
//                       <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{proj.name}</span>
//                     </div>
//                     {/* Feature 4: rename + delete for projects */}
//                     <div className="sidebar-item-actions" style={{ gap: 2 }}>
//                       <button onClick={e => openRename("project", proj.id, proj.name, e)} title="Rename project"
//                         style={{ background: "none", border: "none", cursor: "pointer", padding: 3, borderRadius: 4, opacity: 0.6 }}>
//                         <Icon d={ICONS.edit} size={11} stroke={C.textSub} />
//                       </button>
//                       <button onClick={e => { e.stopPropagation(); setDeleteTarget({ type: "project", id: proj.id, name: proj.name }); setShowDeleteConfirm(true); }} title="Delete project"
//                         style={{ background: "none", border: "none", cursor: "pointer", padding: 3, borderRadius: 4, opacity: 0.6 }}>
//                         <Icon d={ICONS.trash} size={11} stroke={C.danger} />
//                       </button>
//                     </div>
//                     <button onClick={e => { e.stopPropagation(); setExpandedProjects(prev => { const s = new Set(prev); s.has(proj.id) ? s.delete(proj.id) : s.add(proj.id); return s; }); }}
//                       style={{ background: "none", border: "none", cursor: "pointer", padding: "7px 8px", color: C.textMute, flexShrink: 0 }}>
//                       <Icon d={isExpanded ? ICONS.chevD : ICONS.chevR} size={13} stroke={C.textMute} />
//                     </button>
//                   </div>
//                   {isExpanded && (
//                     <div>
//                       {(proj.sessions || []).map(sess => {
//                         const apiS = apiSessions.find(a => a.session_id === sess.sessionId);
//                         const label = apiS?.title || apiS?.preview || sess.title || "Chat";
//                         return (
//                           <div key={sess.sessionId} className="sidebar-row" style={{ position: "relative", display: "flex", alignItems: "center" }}>
//                             <SideItem indent={1}
//                               icon={<Icon d={ICONS.chat} size={13} stroke="currentColor" />}
//                               label={label}
//                               muted
//                               active={activeSession?.sessionId === sess.sessionId}
//                               onClick={() => openExistingSession(sess.sessionId, proj.id)}
//                             />
//                             <div className="sidebar-item-actions" style={{ position: "absolute", right: 10, gap: 2 }}>
//                               <button onClick={e => openRename("session", sess.sessionId, label, e)} title="Rename"
//                                 style={{ background: "none", border: "none", cursor: "pointer", padding: 3, borderRadius: 4, opacity: 0.6 }}>
//                                 <Icon d={ICONS.edit} size={11} stroke={C.textSub} />
//                               </button>
//                               <button onClick={e => { e.stopPropagation(); deleteSession(sess.sessionId); }} title="Delete"
//                                 style={{ background: "none", border: "none", cursor: "pointer", padding: 3, borderRadius: 4, opacity: 0.6 }}>
//                                 <Icon d={ICONS.trash} size={11} stroke={C.danger} />
//                               </button>
//                             </div>
//                           </div>
//                         );
//                       })}
//                       <SideItem indent={1} muted
//                         icon={<Icon d={ICONS.plus} size={13} stroke={C.textMute} />}
//                         label="New chat"
//                         onClick={() => openNewChat(proj.id)}
//                       />
//                     </div>
//                   )}
//                 </div>
//               );
//             })}

//             {/* ── Knowledge base PDFs ── */}
//             <div style={{ padding: "12px 14px 4px", fontSize: 11, fontWeight: 700, color: C.textMute, letterSpacing: "0.08em" }}>KNOWLEDGE BASE</div>
//             {[
//               { label: "PARC Report 2023-24",  file: "PARC Annual Report 2023-24_compressed.pdf" },
//               { label: "FAO Crop Guidelines",  file: "i5550e.pdf" },
//               { label: "Punjab Agri Rules",    file: "PbAgriDeptExtenAdapReseWing_SR_2007_20070612.pdf" },
//             ].map(({ label, file }) => (
//               <div key={file} onClick={() => window.open(`/api/pdf/${encodeURIComponent(file)}`, "_blank")}
//                 style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 12px 6px 18px", cursor: "pointer", color: C.textSub, fontSize: 12 }}>
//                 <Icon d={ICONS.book} size={13} stroke={C.textMute} />
//                 <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{label}</span>
//                 <span style={{ color: C.accentDim, fontSize: 10 }}>↗</span>
//               </div>
//             ))}
//           </div>

//           {/* User footer */}
//           <div style={{ padding: "10px 14px", borderTop: `1px solid ${C.border}`, display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
//             <div style={{ width: 30, height: 30, borderRadius: "50%", background: C.accentBg, border: `1px solid ${C.accent}44`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 700, color: C.accent }}>
//               {username[0].toUpperCase()}
//             </div>
//             <span style={{ flex: 1, fontSize: 12, color: C.textSub, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{username}</span>
//             {onLogout && (
//               <button onClick={onLogout} title="Sign out" style={{ background: "none", border: "none", cursor: "pointer" }}>
//                 <Icon d={ICONS.x} size={14} stroke={C.textMute} />
//               </button>
//             )}
//           </div>
//         </div>

//         {/* ══════════════════════════════════════════════════════════════════
//             MAIN CHAT AREA
//         ══════════════════════════════════════════════════════════════════ */}
//         <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", minWidth: 0 }}>
//           {/* Header */}
//           <div style={{ padding: "0 16px", height: 52, display: "flex", alignItems: "center", gap: 10, background: C.surface, borderBottom: `1px solid ${C.border}`, flexShrink: 0 }}>
//             {/* Feature 1: sidebar toggle button */}
//             <button onClick={() => setSidebarOpen(o => !o)} title={sidebarOpen ? "Close sidebar" : "Open sidebar"}
//               style={{ background: "none", border: `1px solid ${C.border}`, borderRadius: 7, padding: "5px 7px", cursor: "pointer", display: "flex", alignItems: "center", flexShrink: 0 }}>
//               <Icon d={sidebarOpen ? ICONS.panelClose : ICONS.panelOpen} size={15} stroke={C.textSub} />
//             </button>

//             <span style={{ fontSize: 16 }}>🌾</span>
//             <div style={{ flex: 1, minWidth: 0 }}>
//               <span style={{ fontSize: 14, fontWeight: 600, color: C.text }}>
//                 {activeSession ? activeSession.title : "Agricultural Knowledge Base"}
//               </span>
//               {activeSession?.projectId && (
//                 <span style={{ fontSize: 11, color: C.textMute, marginLeft: 8 }}>
//                   · {projects.find(p => p.id === activeSession.projectId)?.name}
//                 </span>
//               )}
//             </div>

//             {/* Feature 2: Tavily web search toggle */}
//             <button onClick={() => setWebSearch(w => !w)}
//               title={webSearch ? "Web search ON (Tavily) — click to disable" : "Web search OFF — click to enable Tavily"}
//               style={{
//                 display: "flex", alignItems: "center", gap: 5, padding: "4px 10px", borderRadius: 20,
//                 background: webSearch ? C.tealBg : "transparent",
//                 border: `1px solid ${webSearch ? C.teal : C.border}`,
//                 cursor: "pointer", fontSize: 12, fontWeight: 600,
//                 color: webSearch ? C.teal : C.textMute,
//                 transition: "all 0.15s",
//               }}>
//               <div style={{ width: 7, height: 7, borderRadius: "50%", background: webSearch ? C.teal : C.textMute, boxShadow: webSearch ? `0 0 5px ${C.teal}` : "none", transition: "all 0.15s" }} />
//               Web Search {webSearch ? "ON" : "OFF"}
//             </button>

//             {/* Feature 3: PDF export of current chat */}
//             <StatusBadge chunks={chunkCount} />
//             {activeSession && (
//               <button
//                 onClick={() => exportChatAsPDF(currentMessages, activeSession.title)}
//                 title="Download chat as PDF"
//                 style={{ display: "flex", alignItems: "center", gap: 5, padding: "4px 10px", borderRadius: 8, background: "none", border: `1px solid ${C.border}`, cursor: "pointer", fontSize: 12, color: C.textSub, whiteSpace: "nowrap" }}>
//                 <Icon d={ICONS.pdf} size={13} stroke={C.textSub} />
//                 Save PDF
//               </button>
//             )}
//             <button onClick={() => setShowTrace(t => !t)} title={showTrace ? "Hide trace" : "Show trace"}
//               style={{ background: "none", border: `1px solid ${C.border}`, borderRadius: 6, padding: "4px 8px", cursor: "pointer", color: C.amber, fontSize: 12, display: "flex", alignItems: "center", gap: 5, whiteSpace: "nowrap" }}>
//               <Icon d={ICONS.trace} size={13} stroke={C.amber} />
//               Trace
//             </button>
//           </div>

//           {/* Chat area */}
//           <div ref={chatRef} style={{ flex: 1, overflowY: "auto", padding: "20px 24px", display: "flex", flexDirection: "column", gap: 16 }}>
//             {!activeSession ? (
//               <Welcome onSend={(p) => { openNewChat(null); setTimeout(() => sendMessage(p), 50); }} />
//             ) : currentMessages.length === 0 ? (
//               <Welcome onSend={sendMessage} />
//             ) : (
//               currentMessages.map((m, i) => (
//                 <Message key={i} role={m.role} content={m.content} ts={m.ts} usedRag={m.usedRag}
//                   uploadedFile={m.uploadedFile}
//                   webSearched={m.webSearched}
//                   onRegenerate={m.role === "assistant" ? () => {
//                     const prev = currentMessages.slice(0, i).reverse().find(x => x.role === "user");
//                     if (prev) sendMessage(prev.content);
//                   } : null}
//                 />
//               ))
//             )}
//             {loading && <TypingDots />}
//           </div>

//           {/* Input (Feature 5: "+" file upload button) */}
//           <div style={{ padding: "12px 20px 16px", borderTop: `1px solid ${C.border}`, background: C.surface, flexShrink: 0 }}>
//             {!activeSession && (
//               <div style={{ fontSize: 12, color: C.textMute, textAlign: "center", marginBottom: 8 }}>
//                 Click <strong style={{ color: C.accent }}>+ New chat</strong> or select a conversation to start.
//               </div>
//             )}

//             {/* Pending file badge */}
//             {pendingFile && (
//               <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 8, padding: "5px 10px", background: C.accentBg, border: `1px solid ${C.accentDim}`, borderRadius: 8, width: "fit-content" }}>
//                 <Icon d={ICONS.attach} size={12} stroke={C.accent} />
//                 <span style={{ fontSize: 12, color: C.accent, fontWeight: 500 }}>{pendingFile.name}</span>
//                 <span style={{ fontSize: 11, color: C.textSub }}>will be used in next message</span>
//                 <button onClick={() => setPendingFile(null)} style={{ background: "none", border: "none", cursor: "pointer", padding: 0, marginLeft: 4 }}>
//                   <Icon d={ICONS.x} size={11} stroke={C.textSub} />
//                 </button>
//               </div>
//             )}

//             {uploadingFile && (
//               <div style={{ fontSize: 12, color: C.teal, marginBottom: 8 }}>⏳ Uploading document…</div>
//             )}

//             <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
//               {/* Feature 5: file upload "+" button */}
//               <button
//                 onClick={() => fileInputRef.current?.click()}
//                 disabled={!activeSession || uploadingFile}
//                 title="Attach a document (PDF, TXT, DOCX) to your message"
//                 style={{
//                   width: 38, height: 38, borderRadius: 9, border: `1px solid ${C.border}`,
//                   background: C.surface2, cursor: activeSession ? "pointer" : "not-allowed",
//                   display: "flex", alignItems: "center", justifyContent: "center",
//                   flexShrink: 0, alignSelf: "flex-end",
//                   opacity: activeSession ? 1 : 0.4, transition: "all 0.15s",
//                   color: pendingFile ? C.accent : C.textSub,
//                 }}
//                 onMouseEnter={e => { if (activeSession) e.currentTarget.style.borderColor = C.accent; }}
//                 onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; }}>
//                 <Icon d={ICONS.attach} size={15} stroke={pendingFile ? C.accent : C.textSub} />
//               </button>
//               <input ref={fileInputRef} type="file" accept=".pdf,.txt,.docx,.csv,.md"
//                 style={{ display: "none" }} onChange={handleFileSelect} />

//               <div style={{ flex: 1, background: C.surface2, border: `1px solid ${activeSession ? C.borderHi : C.border}`, borderRadius: 10, padding: "10px 14px" }}>
//                 <textarea ref={textareaRef} rows={2} value={input}
//                   onChange={e => setInput(e.target.value)}
//                   onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
//                   placeholder={
//                     !activeSession ? "Select or create a chat first" :
//                     webSearch ? "Ask anything — web search is ON (Tavily)… (Enter to send)" :
//                     "Ask about crops, diseases, PARC activities… (Enter to send)"
//                   }
//                   disabled={!activeSession}
//                   style={{ width: "100%", background: "transparent", border: "none", outline: "none", color: C.text, fontSize: 14, fontFamily: "inherit", resize: "none", lineHeight: 1.5 }} />
//               </div>
//               <button onClick={() => sendMessage()} disabled={loading || !input.trim() || !activeSession}
//                 style={{ width: 42, height: 42, borderRadius: 10, border: "none", background: C.accent, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", alignSelf: "flex-end", flexShrink: 0, opacity: (loading || !input.trim() || !activeSession) ? 0.4 : 1, transition: "opacity 0.15s" }}>
//                 <Icon d={ICONS.send} size={16} stroke="#fff" />
//               </button>
//             </div>
//           </div>
//         </div>

//         {/* ══════════════════════════════════════════════════════════════════
//             TRACE PANEL (collapsible)
//         ══════════════════════════════════════════════════════════════════ */}
//         {showTrace && (
//           <div style={{ width: 290, background: C.surface, borderLeft: `1px solid ${C.border}`, display: "flex", flexDirection: "column", overflow: "hidden", flexShrink: 0 }}>
//             <TracePanel
//               trace={trace}
//               webSearchResults={webSearchResults}
//               mcpCalls={mcpCalls}
//               status={status}
//               statusError={statusError}
//             />
//           </div>
//         )}
//       </div>

//       {/* ── Modals ───────────────────────────────────────────────────────── */}

//       {/* New Project */}
//       <Modal open={showNewProject} onClose={() => setShowNewProject(false)} title="Create new project">
//         <div style={{ marginBottom: 14 }}>
//           <label style={{ fontSize: 12, color: C.textSub, display: "block", marginBottom: 6 }}>Icon</label>
//           <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
//             {EMOJIS.map(e => (
//               <button key={e} onClick={() => setNewProjEmoji(e)}
//                 style={{ fontSize: 20, padding: "4px 8px", borderRadius: 8, cursor: "pointer", border: `1px solid ${newProjEmoji === e ? C.accent : C.border}`, background: newProjEmoji === e ? C.accentBg : C.surface2, fontFamily: "inherit" }}>
//                 {e}
//               </button>
//             ))}
//           </div>
//         </div>
//         <TextInput label="Project name" value={newProjName} onChange={setNewProjName} placeholder="e.g. Wheat Disease Research" autoFocus />
//         <TextInput label="Description (optional)" value={newProjDesc} onChange={setNewProjDesc} placeholder="What is this project about?" multiline />
//         <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", marginTop: 4 }}>
//           <Btn onClick={() => setShowNewProject(false)}>Cancel</Btn>
//           <Btn variant="primary" onClick={createProject} disabled={!newProjName.trim()}>Create project</Btn>
//         </div>
//       </Modal>

//       {/* Feature 4: Rename modal (sessions + projects) */}
//       <Modal open={showRename} onClose={() => { setShowRename(false); setRenameTarget(null); }}
//         title={`Rename ${renameTarget?.type === "project" ? "project" : "conversation"}`} width={400}>
//         <TextInput label="New name" value={renameName} onChange={setRenameName}
//           placeholder={renameTarget?.type === "project" ? "Project name" : "Conversation title"}
//           autoFocus />
//         <div style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
//           <Btn onClick={() => { setShowRename(false); setRenameTarget(null); }}>Cancel</Btn>
//           <Btn variant="primary" onClick={commitRename} disabled={!renameName.trim()}>Save</Btn>
//         </div>
//       </Modal>

//       {/* Delete confirm */}
//       <Modal open={showDeleteConfirm} onClose={() => { setShowDeleteConfirm(false); setDeleteTarget(null); }} title="Confirm deletion" width={380}>
//         <div style={{ fontSize: 13, color: C.textSub, marginBottom: 20, lineHeight: 1.6 }}>
//           Delete <strong style={{ color: C.text }}>{deleteTarget?.name}</strong>? This will remove all its chats and data.
//         </div>
//         <div style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
//           <Btn onClick={() => { setShowDeleteConfirm(false); setDeleteTarget(null); }}>Cancel</Btn>
//           <button onClick={() => { if (deleteTarget?.type === "project") deleteProject(deleteTarget.id); }}
//             style={{ padding: "7px 14px", borderRadius: 8, background: C.danger, color: "#fff", border: "none", cursor: "pointer", fontWeight: 600, fontSize: 13, fontFamily: "inherit" }}>
//             Delete
//           </button>
//         </div>
//       </Modal>
//     </>
//   );
// }


// import { useState, useRef, useEffect, useCallback } from "react";

// // ── Palette ───────────────────────────────────────────────────────────────────
// const C = {
//   bg:        "#0c1108",
//   surface:   "#141c0f",
//   surface2:  "#1c2614",
//   surface3:  "#222e18",
//   border:    "#2a3d1e",
//   borderHi:  "#3d5a2a",
//   accent:    "#7ab648",
//   accentDim: "#4a7a1e",
//   accentBg:  "rgba(122,182,72,0.10)",
//   amber:     "#e8a020",
//   amberDim:  "#7a4e00",
//   amberBg:   "rgba(232,160,32,0.10)",
//   teal:      "#2bbfa0",
//   tealDim:   "#0d5a48",
//   tealBg:    "rgba(43,191,160,0.10)",
//   text:      "#dde8cc",
//   textSub:   "#7a9460",
//   textMute:  "#4a6035",
//   userBub:   "#1a2e10",
//   botBub:    "#0f1a08",
//   danger:    "#c0392b",
//   dangerBg:  "rgba(192,57,43,0.12)",
// };

// // ── Icon ──────────────────────────────────────────────────────────────────────
// const Icon = ({ d, size = 16, stroke = C.textSub, fill = "none" }) => (
//   <svg width={size} height={size} viewBox="0 0 24 24" fill={fill}
//     stroke={stroke} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round"
//     style={{ flexShrink: 0 }}>
//     <path d={d} />
//   </svg>
// );

// const ICONS = {
//   leaf:      "M12 2a4 4 0 0 1 4 4v2h2a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2V6a4 4 0 0 1 4-4z",
//   chat:      "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z",
//   folder:    "M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z",
//   file:      "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H8",
//   plus:      "M12 5v14M5 12h14",
//   trash:     "M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6",
//   edit:      "M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z",
//   upload:    "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12",
//   download:  "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3",
//   globe:     "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zM2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z",
//   book:      "M4 19.5A2.5 2.5 0 0 1 6.5 17H20M4 19.5A2.5 2.5 0 0 0 6.5 22H20V2H6.5A2.5 2.5 0 0 0 4 4.5v15z",
//   chevD:     "M6 9l6 6 6-6",
//   chevR:     "M9 18l6-6-6-6",
//   chevL:     "M15 18l-6-6 6-6",
//   panelOpen: "M3 12h18M3 6h18M3 18h18",
//   panelClose:"M3 6h7M3 12h7M3 18h7M17 6l4 6-4 6",
//   x:         "M18 6L6 18M6 6l12 12",
//   search:    "M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z",
//   send:      "M22 2L11 13M22 2L15 22 11 13 2 9l20-7z",
//   check:     "M20 6L9 17 4 12",
//   copy:      "M20 9H11a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2v-9a2 2 0 0 0-2-2zM5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1",
//   thumbUp:   "M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3",
//   thumbDown: "M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zM17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17",
//   share:     "M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8M16 6l-4-4-4 4M12 2v13",
//   trace:     "M3 3h18v18H3zM9 9h6M9 13h6M9 17h4",
//   bot:       "M12 2a4 4 0 0 1 4 4v2h2a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2V6a4 4 0 0 1 4-4zM9 10H7v2h2v-2zm8 0h-2v2h2v-2zm-5 4h-2v2h2v-2z",
//   user:      "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
//   snapshot:  "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H8",
//   reset:     "M1 4v6h6M23 20v-6h-6M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15",
//   sources:   "M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2zM22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z",
//   regen:     "M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15",
//   export:    "M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8M16 6l-4-4-4 4M12 2v13",
//   pdf:       "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M11 13H8M16 13h-2M11 17H8M16 17h-2",
//   tool:      "M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z",
//   attach:    "M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48",
//   weather:   "M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9z",
// };

// // ── Utilities ─────────────────────────────────────────────────────────────────
// const now = () => new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

// // ── Citation parser ───────────────────────────────────────────────────────────
// function parseSources(content) {
//   const sourcesMatch = content.match(/SOURCES:\s*\n([\s\S]+)$/i);
//   const mainText = sourcesMatch
//     ? content.slice(0, content.indexOf(sourcesMatch[0])).trim()
//     : content;
//   const sources = [];
//   if (sourcesMatch) {
//     const lines = sourcesMatch[1].trim().split("\n").filter(Boolean);
//     lines.forEach(line => {
//       const docMatch = line.match(/\[(\d+)\]\s*(.+?)\s*\|\s*[Pp]age\s*(\d+)/);
//       if (docMatch) {
//         sources.push({ num: parseInt(docMatch[1]), filename: docMatch[2].trim(), page: parseInt(docMatch[3]), type: "document" });
//         return;
//       }
//       const webMatch = line.match(/\[Web\s*(\d+)\]\s*(.+?)\s*—\s*(https?:\/\/\S+)/);
//       if (webMatch) {
//         sources.push({ num: parseInt(webMatch[1]), title: webMatch[2].trim(), url: webMatch[3].trim(), type: "web" });
//       }
//     });
//   }
//   return { mainText, sources };
// }

// function renderTextWithCitations(text, sources, onCiteClick) {
//   const parts = text.split(/(\[(?:Web\s*)?\d+\])/g);
//   return parts.map((part, i) => {
//     const match = part.match(/^\[(?:Web\s*)?(\d+)\]$/);
//     if (match) {
//       const num = parseInt(match[1]);
//       const isWeb = part.toLowerCase().includes("web");
//       const src = sources.find(s => s.num === num && (isWeb ? s.type === "web" : s.type === "document"))
//                || sources.find(s => s.num === num);
//       return (
//         <sup key={i} onClick={() => src && onCiteClick(src)}
//           title={src ? (src.type === "document" ? `${src.filename} — Page ${src.page}` : src.title) : ""}
//           style={{
//             cursor: src ? "pointer" : "default",
//             color: src ? (src.type === "web" ? C.amber : C.accent) : C.textMute,
//             fontWeight: 700, fontSize: "0.72em", marginLeft: 1,
//             padding: "1px 4px", borderRadius: 3,
//             background: src ? (src.type === "web" ? "#2a1e00" : "#16301a") : "transparent",
//             border: src ? `1px solid ${src.type === "web" ? C.amberDim : C.accentDim}` : "none",
//             userSelect: "none",
//           }}>
//           {part}
//         </sup>
//       );
//     }
//     return (
//       <span key={i}>
//         {part.split("\n").map((line, j, arr) => (
//           <span key={j}>{line}{j < arr.length - 1 && <br />}</span>
//         ))}
//       </span>
//     );
//   });
// }

// function SourcesList({ sources }) {
//   if (!sources.length) return null;
//   const open = (src) => {
//     if (src.type === "document") window.open(`/api/pdf/${encodeURIComponent(src.filename)}#page=${src.page}`, "_blank");
//     else window.open(src.url, "_blank");
//   };
//   return (
//     <div style={{ marginTop: 12, paddingTop: 10, borderTop: `1px solid ${C.border}` }}>
//       <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: C.textMute, marginBottom: 6 }}>
//         References
//       </div>
//       {sources.map((src, i) => (
//         <div key={i} onClick={() => open(src)}
//           style={{ display: "flex", alignItems: "flex-start", gap: 7, marginBottom: 5, cursor: "pointer", padding: "5px 7px", borderRadius: 7, transition: "background 0.15s" }}
//           onMouseEnter={e => e.currentTarget.style.background = C.surface2}
//           onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
//           <span style={{ minWidth: 20, height: 20, borderRadius: 4, flexShrink: 0, background: src.type === "document" ? C.accentDim : C.amberDim, border: `1px solid ${src.type === "document" ? C.accent : C.amber}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 9, fontWeight: 700, color: src.type === "document" ? C.accent : C.amber }}>
//             {src.num}
//           </span>
//           <div style={{ fontSize: 11.5, color: C.textSub, lineHeight: 1.5 }}>
//             {src.type === "document" ? (
//               <><span style={{ color: C.text, fontWeight: 500 }}>{src.filename}</span><span style={{ color: C.textMute }}> — Page {src.page}</span><span style={{ color: C.accentDim, fontSize: 10, marginLeft: 5 }}>↗ open PDF</span></>
//             ) : (
//               <><span style={{ color: C.text, fontWeight: 500 }}>{src.title}</span><span style={{ color: C.amberDim, fontSize: 10, marginLeft: 5 }}>↗ web</span></>
//             )}
//           </div>
//         </div>
//       ))}
//     </div>
//   );
// }

// // ── Message bubble ────────────────────────────────────────────────────────────
// function Message({ role, content, ts, usedRag, uploadedFile, sourceType, mcpTool, onRegenerate }) {
//   const [copied, setCopied] = useState(false);
//   const [liked, setLiked]   = useState(null);
//   const [showSrc, setShowSrc] = useState(true);
//   const isUser = role === "user";

//   const ActionBtn = ({ icon, title, onClick, active, activeColor }) => (
//     <button onClick={onClick} title={title}
//       style={{ background: "none", border: "none", cursor: "pointer", padding: "4px 5px", borderRadius: 6, display: "flex", alignItems: "center", opacity: 0.55, transition: "opacity 0.15s" }}
//       onMouseEnter={e => { e.currentTarget.style.opacity = "1"; e.currentTarget.style.background = C.surface2; }}
//       onMouseLeave={e => { e.currentTarget.style.opacity = "0.55"; e.currentTarget.style.background = "none"; }}>
//       <Icon d={icon} size={14} stroke={active ? (activeColor || C.accent) : C.textSub} />
//     </button>
//   );

//   // Source badge: reflects exactly what the backend reports via
//   // ChatResponse.source_type — "RAG" | "UPLOAD" | "MCP" | "WEB".
//   // This is the source of truth (server-side), not a client-side guess.
//   const sourceBadge = !isUser && sourceType && (
//     <span style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 9.5, fontWeight: 600, letterSpacing: "0.03em", padding: "2px 7px", borderRadius: 20,
//       background: sourceType === "RAG" ? "#16301a" : sourceType === "UPLOAD" ? "#16301a" : sourceType === "MCP" ? "#1a2a3a" : "#2a2210",
//       border: `1px solid ${sourceType === "RAG" || sourceType === "UPLOAD" ? C.accentDim : sourceType === "MCP" ? "#3a7ab0" : C.amberDim}`,
//       color: sourceType === "RAG" || sourceType === "UPLOAD" ? C.accent : sourceType === "MCP" ? "#5aa0d8" : C.amber, marginLeft: 6 }}>
//       {sourceType === "RAG" && "📚 RAG"}
//       {sourceType === "UPLOAD" && "📎 Uploaded doc"}
//       {sourceType === "MCP" && `⚡ MCP${mcpTool ? `: ${mcpTool}` : ""}`}
//       {sourceType === "WEB" && "🌐 Web"}
//     </span>
//   );

//   const ragBadge = !isUser && !sourceType && usedRag !== null && usedRag !== undefined && (
//     <span style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 9.5, fontWeight: 600, letterSpacing: "0.03em", padding: "2px 7px", borderRadius: 20, background: usedRag ? "#16301a" : "#2a2210", border: `1px solid ${usedRag ? C.accentDim : C.amberDim}`, color: usedRag ? C.accent : C.amber, marginLeft: 6 }}>
//       {usedRag ? "RAG" : "🌐 Web"}
//     </span>
//   );

//   return (
//     <div style={{ display: "flex", flexDirection: "column", alignItems: isUser ? "flex-end" : "flex-start", gap: 4 }}>
//       <div style={{ display: "flex", alignItems: "center", gap: 6, flexDirection: isUser ? "row-reverse" : "row" }}>
//         <div style={{ width: 26, height: 26, borderRadius: "50%", background: isUser ? C.accentDim : "#1a2610", border: `1px solid ${isUser ? C.accent : C.border}`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
//           <Icon d={isUser ? ICONS.user : ICONS.bot} size={13} stroke={isUser ? C.accent : C.textSub} />
//         </div>
//         <span style={{ fontSize: 11, color: C.textMute, display: "flex", alignItems: "center", flexWrap: "wrap", gap: 2 }}>
//           {isUser ? "You" : "RAG Assistant"} · {ts}{sourceBadge}{ragBadge}
//         </span>
//       </div>

//       {/* File attachment badge on user message */}
//       {isUser && uploadedFile && (
//         <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "5px 10px", background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 8, fontSize: 11, color: C.textSub, maxWidth: "78%" }}>
//           <Icon d={ICONS.attach} size={12} stroke={C.accent} />
//           <span style={{ color: C.accent, fontWeight: 500 }}>{uploadedFile}</span>
//           <span style={{ color: C.textMute }}>· attached</span>
//         </div>
//       )}

//       <div style={{ maxWidth: "78%", background: isUser ? C.userBub : C.botBub, border: `1px solid ${isUser ? C.accentDim : C.border}`, borderRadius: isUser ? "14px 4px 14px 14px" : "4px 14px 14px 14px", padding: "10px 14px", lineHeight: 1.65, fontSize: 14, color: C.text }}>
//         {isUser ? (
//           <span style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>{content}</span>
//         ) : (() => {
//           const { mainText, sources } = parseSources(content);
//           const onCiteClick = src => {
//             if (src.type === "document") window.open(`/api/pdf/${encodeURIComponent(src.filename)}#page=${src.page}`, "_blank");
//             else window.open(src.url, "_blank");
//           };
//           return (
//             <>
//               <div style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
//                 {renderTextWithCitations(mainText, sources, onCiteClick)}
//               </div>
//               {showSrc && <SourcesList sources={sources} />}
//             </>
//           );
//         })()}
//       </div>

//       {!isUser && (
//         <div style={{ display: "flex", alignItems: "center", gap: 1, paddingLeft: 4, marginTop: -2 }}>
//           <ActionBtn icon={copied ? ICONS.check : ICONS.copy} title="Copy" onClick={() => { navigator.clipboard.writeText(content); setCopied(true); setTimeout(() => setCopied(false), 1500); }} active={copied} activeColor={C.accent} />
//           <ActionBtn icon={ICONS.thumbUp} title="Good response" onClick={() => setLiked(l => l === "up" ? null : "up")} active={liked === "up"} activeColor={C.accent} />
//           <ActionBtn icon={ICONS.thumbDown} title="Bad response" onClick={() => setLiked(l => l === "down" ? null : "down")} active={liked === "down"} activeColor={C.danger} />
//           <ActionBtn icon={ICONS.share} title="Copy to clipboard" onClick={() => navigator.clipboard.writeText(content)} />
//           {onRegenerate && <ActionBtn icon={ICONS.regen} title="Regenerate" onClick={onRegenerate} />}
//           <div style={{ width: 1, height: 14, background: C.border, margin: "0 3px" }} />
//           <ActionBtn icon={ICONS.sources} title={showSrc ? "Hide sources" : "Show sources"} onClick={() => setShowSrc(s => !s)} active={showSrc} activeColor={C.accent} />
//         </div>
//       )}
//     </div>
//   );
// }

// // ── Typing dots ───────────────────────────────────────────────────────────────
// function TypingDots() {
//   return (
//     <div style={{ display: "flex", alignItems: "flex-start", gap: 6 }}>
//       <div style={{ width: 26, height: 26, borderRadius: "50%", background: "#1a2610", border: `1px solid ${C.border}`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
//         <Icon d={ICONS.bot} size={13} stroke={C.textSub} />
//       </div>
//       <div style={{ background: C.botBub, border: `1px solid ${C.border}`, borderRadius: "4px 14px 14px 14px", padding: "12px 16px", display: "flex", gap: 5, alignItems: "center" }}>
//         {[0, 0.18, 0.36].map((delay, i) => (
//           <div key={i} style={{ width: 7, height: 7, borderRadius: "50%", background: C.accentDim, animation: "pulse 1.2s ease-in-out infinite", animationDelay: `${delay}s` }} />
//         ))}
//       </div>
//     </div>
//   );
// }

// // ── Trace panel ───────────────────────────────────────────────────────────────
// function TracePanel({ trace, status, statusError }) {
//   return (
//     <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
//       {/* Header — single Trace label, no tabs */}
//       <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "10px 14px", borderBottom: `1px solid ${C.border}`, flexShrink: 0 }}>
//         <Icon d={ICONS.trace} size={13} stroke={C.amber} />
//         <span style={{ fontSize: 12, fontWeight: 700, color: C.amber }}>Trace</span>
//       </div>

//       <div style={{ flex: 1, overflowY: "auto", padding: "12px 14px" }}>
//         {!trace ? (
//           <div style={{ color: C.textMute, fontSize: 12, textAlign: "center", marginTop: 40, lineHeight: 1.7 }}>
//             Pipeline step timings<br />appear here after each query
//           </div>
//         ) : (
//           <pre style={{ fontFamily: "'JetBrains Mono','Fira Code',monospace", fontSize: 11, color: C.textSub, lineHeight: 1.75, whiteSpace: "pre-wrap", wordBreak: "break-word", margin: 0 }}>
//             {trace}
//           </pre>
//         )}
//       </div>

//       {/* Pipeline config at bottom */}
//       <div style={{ padding: "12px 14px", borderTop: `1px solid ${C.border}` }}>
//         <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: C.textMute, marginBottom: 8 }}>Pipeline</div>
//         {[
//           ["Vector DB",  status?.vector_db || "ChromaDB"],
//           ["Retrieval",  status?.retrieval || "BM25 + Embeddings"],
//           ["Fusion",     status?.fusion    || "RRF"],
//           ["Chunks",     (status?.chunk_count || 0).toLocaleString()],
//         ].map(([k, v]) => (
//           <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "4px 8px", background: C.surface2, borderRadius: 6, marginBottom: 4, fontSize: 12 }}>
//             <span style={{ color: C.textSub }}>{k}</span>
//             <span style={{ color: C.text }}>{v}</span>
//           </div>
//         ))}
//         {statusError && (
//           <div style={{ marginTop: 8, background: C.dangerBg, border: `1px solid ${C.danger}`, borderRadius: 8, padding: "8px 10px", fontSize: 11.5, color: "#e8938a", lineHeight: 1.5 }}>
//             {statusError}
//           </div>
//         )}
//       </div>
//     </div>
//   );
// }

// // ── Welcome screen ────────────────────────────────────────────────────────────
// function Welcome({ onSend }) {
//   const prompts = [
//     "What wheat diseases are monitored in Punjab?",
//     "Is today's weather good for wheat sowing in Lahore?",
//     "Convert 50 acres to hectares",
//     "Which FAO guidelines cover Ug99 rust?",
//     "Summarise PARC's 2023-24 research highlights",
//     "What is the role of the Agriculture Extension Wing?",
//   ];
//   return (
//     <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: 32, gap: 28 }}>
//       <div style={{ textAlign: "center" }}>
//         <div style={{ fontSize: 40, marginBottom: 12 }}>🌾</div>
//         <div style={{ fontSize: 22, fontWeight: 700, color: C.text, letterSpacing: "-0.02em", marginBottom: 6 }}>
//           Agricultural RAG Assistant
//         </div>
//         <div style={{ fontSize: 13, color: C.textSub, maxWidth: 440, lineHeight: 1.6 }}>
//           Grounded in PARC Annual Report, FAO Crop Guidelines, and Punjab Agri Rules.
//           MCP tools: weather, crop calendar, unit converter, Tavily web search.
//         </div>
//       </div>
//       <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, width: "100%", maxWidth: 560 }}>
//         {prompts.map((p, i) => (
//           <button key={i} onClick={() => onSend(p)}
//             style={{ background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 10, padding: "10px 14px", color: C.textSub, fontSize: 12, textAlign: "left", cursor: "pointer", lineHeight: 1.5, transition: "border-color 0.15s, color 0.15s", fontFamily: "inherit" }}
//             onMouseEnter={e => { e.currentTarget.style.borderColor = C.accent; e.currentTarget.style.color = C.text; }}
//             onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.color = C.textSub; }}>
//             {p}
//           </button>
//         ))}
//       </div>
//     </div>
//   );
// }

// // ── Sidebar item ──────────────────────────────────────────────────────────────
// const SideItem = ({ icon, label, active, onClick, indent = 0, muted = false }) => (
//   <div onClick={onClick}
//     style={{ display: "flex", alignItems: "center", gap: 8, padding: `7px 12px 7px ${12 + indent * 16}px`, borderRadius: 8, cursor: "pointer", margin: "1px 6px", background: active ? C.accentBg : "transparent", color: active ? C.accent : muted ? C.textMute : C.textSub, fontSize: 13, fontWeight: active ? 600 : 400, transition: "all 0.12s" }}>
//     {icon}
//     <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{label}</span>
//   </div>
// );

// // ── Modal ─────────────────────────────────────────────────────────────────────
// const Modal = ({ open, onClose, title, children, width = 480 }) => {
//   if (!open) return null;
//   return (
//     <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center" }}
//       onClick={onClose}>
//       <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 14, padding: "24px 28px", width, maxWidth: "90vw", maxHeight: "80vh", overflowY: "auto" }}
//         onClick={e => e.stopPropagation()}>
//         <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
//           <span style={{ fontSize: 16, fontWeight: 700, color: C.text }}>{title}</span>
//           <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer" }}>
//             <Icon d={ICONS.x} stroke={C.textSub} size={18} />
//           </button>
//         </div>
//         {children}
//       </div>
//     </div>
//   );
// };

// const TextInput = ({ label, value, onChange, placeholder, multiline = false, autoFocus = false }) => (
//   <div style={{ marginBottom: 14 }}>
//     {label && <label style={{ fontSize: 12, color: C.textSub, display: "block", marginBottom: 6 }}>{label}</label>}
//     {multiline
//       ? <textarea value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
//           style={{ width: "100%", background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 8, padding: "10px 12px", color: C.text, fontSize: 13, fontFamily: "inherit", outline: "none", resize: "vertical", minHeight: 80, boxSizing: "border-box" }} />
//       : <input value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder} autoFocus={autoFocus}
//           style={{ width: "100%", background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 8, padding: "10px 12px", color: C.text, fontSize: 13, fontFamily: "inherit", outline: "none", boxSizing: "border-box" }} />
//     }
//   </div>
// );

// const Btn = ({ children, onClick, variant = "ghost", danger = false, style: sx = {}, disabled = false }) => {
//   const base = { display: "inline-flex", alignItems: "center", gap: 6, padding: "7px 12px", borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: disabled ? "not-allowed" : "pointer", border: "none", transition: "all 0.15s", opacity: disabled ? 0.5 : 1, fontFamily: "inherit" };
//   const variants = {
//     primary: { background: C.accent, color: C.bg },
//     ghost:   { background: "transparent", color: danger ? C.danger : C.textSub, border: `1px solid ${danger ? C.danger + "55" : C.border}` },
//     surface: { background: C.surface2, color: C.text, border: `1px solid ${C.border}` },
//   };
//   return <button style={{ ...base, ...variants[variant], ...sx }} onClick={onClick} disabled={disabled}>{children}</button>;
// };

// function StatusBadge({ chunks }) {
//   const ok = chunks > 0;
//   return (
//     <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "4px 10px", borderRadius: 20, background: ok ? "#1a3310" : "#3a1010", border: `1px solid ${ok ? C.accentDim : C.danger}`, fontSize: 12, color: ok ? C.accent : "#e74c3c", whiteSpace: "nowrap" }}>
//       <div style={{ width: 7, height: 7, borderRadius: "50%", background: ok ? C.accent : C.danger, boxShadow: ok ? `0 0 6px ${C.accent}` : "none" }} />
//       {ok ? `${chunks.toLocaleString()} chunks` : "Empty"}
//     </div>
//   );
// }

// // ── PDF chat export ───────────────────────────────────────────────────────────
// function exportChatAsPDF(messages, sessionTitle) {
//   if (!messages || messages.length === 0) {
//     alert("No messages to export yet.");
//     return;
//   }
//   const escHtml = s => s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
//   const date = new Date().toLocaleString();
//   const rows = messages.map(m => {
//     const isUser = m.role === "user";
//     const label = isUser ? "You" : "RAG Assistant";
//     const align = isUser ? "right" : "left";
//     const mlAuto = isUser ? "auto" : "0";
//     const bg = isUser ? "#1a2e10" : "#0f1a08";
//     const borderColor = isUser ? "#4a7a1e" : "#2a3d1e";
//     return `
//       <div style="margin-bottom:18px;text-align:${align}">
//         <div style="font-size:11px;color:#7a9460;margin-bottom:4px">${label} · ${m.ts || ""}</div>
//         <div style="display:inline-block;max-width:78%;background:${bg};border:1px solid ${borderColor};border-radius:12px;padding:10px 14px;font-size:13px;line-height:1.7;color:#dde8cc;white-space:pre-wrap;word-break:break-word;margin-left:${mlAuto};text-align:left">${escHtml(m.content)}</div>
//       </div>`;
//   }).join("");

//   const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"/><title>${escHtml(sessionTitle || "RAG Chat")}</title>
//   <style>@page{size:A4;margin:20mm 18mm}body{background:#0c1108;color:#dde8cc;font-family:'Segoe UI',sans-serif;font-size:13px;padding:0}
//   .cover{border-bottom:1px solid #2a3d1e;padding-bottom:16px;margin-bottom:24px}.cover h1{font-size:20px;font-weight:700;color:#dde8cc;margin-bottom:6px}
//   .cover .meta{font-size:11px;color:#7a9460}@media print{body{-webkit-print-color-adjust:exact;print-color-adjust:exact}}</style>
//   </head><body>
//   <div class="cover"><h1>🌾 ${escHtml(sessionTitle || "RAG Conversation")}</h1>
//   <div class="meta">Exported ${date} · ${messages.length} messages</div></div>
//   ${rows}</body></html>`;

//   const iframe = document.createElement("iframe");
//   iframe.style.cssText = "position:fixed;top:-9999px;left:-9999px;width:0;height:0;opacity:0;";
//   document.body.appendChild(iframe);
//   iframe.contentDocument.open();
//   iframe.contentDocument.write(html);
//   iframe.contentDocument.close();
//   setTimeout(() => {
//     iframe.contentWindow.print();
//     setTimeout(() => document.body.removeChild(iframe), 3000);
//   }, 500);
// }

// // ═══════════════════════════════════════════════════════════════════════════════
// //  MAIN COMPONENT
// // ═══════════════════════════════════════════════════════════════════════════════
// const EMOJIS = ["🌱", "🌾", "🪴", "🌽", "🍃", "🌿", "🌻", "🌴", "🫘", "🍀"];

// export default function ProjectManager({ username = "user", token, onLogout }) {
//   // ── Projects / chats ──────────────────────────────────────────────────────
//   const [projects, setProjects]               = useState([]);
//   const [expandedProjects, setExpandedProjects] = useState(new Set());
//   const [selectedProject, setSelectedProject] = useState(null);
//   const [activeSession, setActiveSession]     = useState(null);
//   const [msgCache, setMsgCache]               = useState({});
//   const [loading, setLoading]                 = useState(false);
//   const [trace, setTrace]                     = useState(null);
//   const [input, setInput]                     = useState("");

//   // ── New: sidebar collapsed ────────────────────────────────────────────────
//   const [sidebarOpen, setSidebarOpen]         = useState(true);

//   // ── New: web search toggle — sent to backend as force_web ──────────────────
//   const [webSearch, setWebSearch]             = useState(false);

//   // ── New: file upload state ────────────────────────────────────────────────
//   const [pendingFile, setPendingFile]         = useState(null); // { name, fileId } after upload
//   const [uploadingFile, setUploadingFile]     = useState(false);
//   const fileInputRef                          = useRef(null);

//   // ── Backend ───────────────────────────────────────────────────────────────
//   const [apiSessions, setApiSessions]         = useState([]);
//   const [status, setStatus]                   = useState(null);
//   const [chunkCount, setChunkCount]           = useState(0);
//   const [statusError, setStatusError]         = useState(null);
//   const [sideSearch, setSideSearch]           = useState("");
//   const [showTrace, setShowTrace]             = useState(true);

//   // ── Modals ────────────────────────────────────────────────────────────────
//   const [showNewProject, setShowNewProject]   = useState(false);
//   const [newProjName, setNewProjName]         = useState("");
//   const [newProjDesc, setNewProjDesc]         = useState("");
//   const [newProjEmoji, setNewProjEmoji]       = useState("🌱");
//   const [showRename, setShowRename]           = useState(false);
//   const [renameTarget, setRenameTarget]       = useState(null);
//   const [renameName, setRenameName]           = useState("");
//   const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
//   const [deleteTarget, setDeleteTarget]       = useState(null);

//   const chatRef     = useRef(null);
//   const textareaRef = useRef(null);

//   const authHeaders = () => token
//     ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` }
//     : { "Content-Type": "application/json" };

//   // ── Scroll ────────────────────────────────────────────────────────────────
//   useEffect(() => {
//     if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
//   }, [msgCache, activeSession, loading]);

//   // ── Poll /api/status ──────────────────────────────────────────────────────
//   useEffect(() => {
//     const fetch_ = () => {
//       fetch("/api/status").then(r => r.json()).then(d => {
//         setStatus(d); setChunkCount(d.chunk_count || 0);
//         setStatusError(d.vector_store_error || d.pipeline_error || null);
//       }).catch(err => { setStatusError(`Cannot reach API: ${err.message}`); setChunkCount(0); });
//     };
//     fetch_(); const id = setInterval(fetch_, 8000); return () => clearInterval(id);
//   }, []);

//   // ── Load sessions ─────────────────────────────────────────────────────────
//   const fetchApiSessions = useCallback(() => {
//     fetch("/api/sessions", { headers: authHeaders() })
//       .then(r => r.json())
//       .then(d => setApiSessions(d.sessions || []))
//       .catch(() => {});
//   }, [token]);

//   useEffect(() => { fetchApiSessions(); }, [fetchApiSessions]);

//   // ── Load projects from localStorage ───────────────────────────────────────
//   useEffect(() => {
//     try {
//       const saved = localStorage.getItem(`rag_projects_${username}`);
//       if (saved) setProjects(JSON.parse(saved));
//     } catch (_) {}
//   }, [username]);

//   const saveProjects = (ps) => {
//     setProjects(ps);
//     try { localStorage.setItem(`rag_projects_${username}`, JSON.stringify(ps)); } catch (_) {}
//   };

//   // ── Open session ──────────────────────────────────────────────────────────
//   const openNewChat = (projectId = null) => {
//     const sessionId = crypto.randomUUID();
//     const proj = projectId ? projects.find(p => p.id === projectId) : null;
//     const session = { sessionId, projectId, title: proj ? `${proj.emoji} New chat` : "New chat" };
//     setActiveSession(session); setTrace(null); setInput("");
//     setPendingFile(null);
//     if (projectId) {
//       const updated = projects.map(p => {
//         if (p.id !== projectId) return p;
//         return { ...p, sessions: [...(p.sessions || []), { sessionId, title: "New chat", date: new Date().toISOString().slice(0, 10) }] };
//       });
//       saveProjects(updated);
//     }
//   };

//   const openExistingSession = (sessionId, projectId = null) => {
//     const proj = projectId ? projects.find(p => p.id === projectId) : null;
//     const apiSess = apiSessions.find(s => s.session_id === sessionId);
//     const title = apiSess?.title || apiSess?.preview || "Chat";
//     setActiveSession({ sessionId, projectId, title: proj ? `${proj.emoji} ${title}` : title });
//     setTrace(null); setInput(""); setPendingFile(null);
//     if (!msgCache[sessionId]) {
//       fetch(`/api/sessions/${sessionId}`, { headers: authHeaders() })
//         .then(r => r.json())
//         .then(d => {
//           const msgs = (d.messages || []).map(m => ({ role: m.role, content: m.content, ts: m.ts || now(), usedRag: m.used_rag }));
//           setMsgCache(prev => ({ ...prev, [sessionId]: msgs }));
//         }).catch(() => {});
//     }
//   };

//   // ── FILE UPLOAD ("+") ─────────────────────────────────────────────────────
//   const handleFileSelect = async (e) => {
//     const file = e.target.files?.[0];
//     if (!file || !activeSession) return;
//     e.target.value = "";

//     setUploadingFile(true);
//     try {
//       const fd = new FormData();
//       fd.append("file", file);
//       // CRITICAL: /api/upload requires session_id (or sessionId) as a form
//       // field to register the file under SESSION_FILES[session_id] — without
//       // this it silently falls back to a "global" bucket that this chat
//       // session never looks at, so uploaded docs were never actually used.
//       fd.append("session_id", activeSession.sessionId);
//       const r = await fetch("/api/upload", {
//         method: "POST",
//         headers: token ? { Authorization: `Bearer ${token}` } : {},
//         body: fd,
//       });
//       if (!r.ok) throw new Error(`Upload failed (${r.status})`);
//       const data = await r.json();
//       setPendingFile({ name: file.name, fileId: data.file_id });
//     } catch (err) {
//       alert(`File upload failed: ${err.message}\n\nMake sure the API server is running and /api/upload endpoint exists.`);
//     } finally {
//       setUploadingFile(false);
//     }
//   };

//   // ── SEND MESSAGE ──────────────────────────────────────────────────────────
//   const sendMessage = async (text) => {
//     const q = (text || input).trim();
//     if (!q || loading || !activeSession) return;
//     setInput("");

//     const attachedFile = pendingFile;
//     setPendingFile(null);

//     const userMsg = {
//       role: "user", content: q, ts: now(),
//       uploadedFile: attachedFile?.name || null,
//     };
//     setMsgCache(prev => ({
//       ...prev,
//       [activeSession.sessionId]: [...(prev[activeSession.sessionId] || []), userMsg],
//     }));
//     setLoading(true);
//     setTrace(null);

//     try {
//       // ── Single call to /api/chat ────────────────────────────────────────
//       // The backend now owns the whole routing decision:
//       //   • force_web=false (default): the pipeline ALWAYS checks the 3
//       //     indexed PDFs first (RAG), and only falls back to live Tavily
//       //     web search if the relevance evaluator finds nothing useful.
//       //   • force_web=true (Web Search toggle ON): skip the knowledge base
//       //     and answer straight from the open internet.
//       // MCP tools (weather / crop_calendar / unit_converter / tavily_search)
//       // are dispatched automatically server-side on every query — no
//       // separate pre-fetch call needed (that call used the wrong request
//       // shape and was silently failing, which is why "MCP wasn't working").
//       // Uploaded files are matched to this chat purely by session_id
//       // (sent below during upload), so we don't need to pass a file_id here.
//       const res = await fetch("/api/chat", {
//         method: "POST",
//         headers: authHeaders(),
//         body: JSON.stringify({
//           session_id: activeSession.sessionId,
//           query: q,
//           force_web: webSearch,
//         }),
//       });
//       const data = await res.json();

//       const botMsg = {
//         role: "assistant",
//         content: data.response || "No response received.",
//         ts: now(),
//         usedRag: data.used_rag,
//         sourceType: data.source_type,   // "RAG" | "WEB" | "MCP" | "UPLOAD"
//         mcpTool: data.mcp_tool || null,
//       };
//       setMsgCache(prev => ({
//         ...prev,
//         [activeSession.sessionId]: [...(prev[activeSession.sessionId] || []), botMsg],
//       }));
//       if (data.trace) setTrace(data.trace);

//       // Auto-title
//       const currentMsgs = msgCache[activeSession.sessionId] || [];
//       if (currentMsgs.filter(m => m.role === "user").length === 0) {
//         const autoTitle = q.slice(0, 40) + (q.length > 40 ? "…" : "");
//         setActiveSession(prev => ({ ...prev, title: autoTitle }));
//         if (activeSession.projectId) {
//           const updated = projects.map(p => {
//             if (p.id !== activeSession.projectId) return p;
//             return { ...p, sessions: (p.sessions || []).map(s => s.sessionId === activeSession.sessionId ? { ...s, title: autoTitle } : s) };
//           });
//           saveProjects(updated);
//         }
//       }
//     } catch (err) {
//       const errMsg = { role: "assistant", content: `❌ Could not reach the backend.\n\nError: ${err.message}`, ts: now() };
//       setMsgCache(prev => ({ ...prev, [activeSession.sessionId]: [...(prev[activeSession.sessionId] || []), errMsg] }));
//     } finally {
//       setLoading(false);
//       fetchApiSessions();
//     }
//   };

//   // ── Delete session ────────────────────────────────────────────────────────
//   const deleteSession = async (sessionId) => {
//     if (!confirm("Delete this conversation permanently?")) return;
//     await fetch(`/api/sessions/${sessionId}`, { method: "DELETE", headers: authHeaders() }).catch(() => {});
//     setMsgCache(prev => { const n = { ...prev }; delete n[sessionId]; return n; });
//     if (activeSession?.sessionId === sessionId) setActiveSession(null);
//     fetchApiSessions();
//   };

//   // ── Rename ────────────────────────────────────────────────────────────────
//   const openRename = (type, id, currentName, e) => {
//     e?.stopPropagation();
//     setRenameTarget({ type, id });
//     setRenameName(currentName || "");
//     setShowRename(true);
//   };

//   const commitRename = async () => {
//     if (!renameName.trim() || !renameTarget) return;
//     if (renameTarget.type === "session") {
//       await fetch(`/api/sessions/${renameTarget.id}`, {
//         method: "PATCH", headers: authHeaders(),
//         body: JSON.stringify({ title: renameName.trim() }),
//       }).catch(() => {});
//       fetchApiSessions();
//       if (activeSession?.sessionId === renameTarget.id) {
//         setActiveSession(prev => ({ ...prev, title: renameName.trim() }));
//       }
//     } else if (renameTarget.type === "project") {
//       const updated = projects.map(p => p.id === renameTarget.id ? { ...p, name: renameName.trim() } : p);
//       saveProjects(updated);
//       if (selectedProject?.id === renameTarget.id) setSelectedProject(prev => ({ ...prev, name: renameName.trim() }));
//     }
//     setShowRename(false); setRenameTarget(null); setRenameName("");
//   };

//   // ── Project CRUD ──────────────────────────────────────────────────────────
//   const createProject = () => {
//     if (!newProjName.trim()) return;
//     const proj = { id: "p" + Date.now(), name: newProjName.trim(), emoji: newProjEmoji, description: newProjDesc.trim(), createdAt: new Date().toISOString().slice(0, 10), sessions: [] };
//     saveProjects([...projects, proj]);
//     setNewProjName(""); setNewProjDesc(""); setNewProjEmoji("🌱");
//     setShowNewProject(false);
//     setExpandedProjects(prev => new Set([...prev, proj.id]));
//   };

//   const deleteProject = (id) => {
//     saveProjects(projects.filter(p => p.id !== id));
//     if (selectedProject?.id === id) setSelectedProject(null);
//     if (activeSession?.projectId === id) setActiveSession(null);
//     setShowDeleteConfirm(false); setDeleteTarget(null);
//   };

//   // ── Filtered lists ────────────────────────────────────────────────────────
//   const search = sideSearch.toLowerCase();
//   const allProjectSessionIds = new Set(projects.flatMap(p => (p.sessions || []).map(ss => ss.sessionId)));
//   const filteredApiSessions  = apiSessions.filter(s => !allProjectSessionIds.has(s.session_id) && (!search || (s.title || s.preview || "").toLowerCase().includes(search)));
//   const filteredProjects     = projects.filter(p => !search || p.name.toLowerCase().includes(search));
//   const currentMessages      = (activeSession && msgCache[activeSession.sessionId]) || [];

//   // ─────────────────────────────────────────────────────────────────────────
//   return (
//     <>
//       <style>{`
//         * { box-sizing: border-box; margin: 0; padding: 0; }
//         body { background: ${C.bg}; }
//         ::-webkit-scrollbar { width: 5px; }
//         ::-webkit-scrollbar-track { background: transparent; }
//         ::-webkit-scrollbar-thumb { background: ${C.border}; border-radius: 4px; }
//         @keyframes pulse { 0%,100% { opacity:0.3; transform:scale(0.85); } 50% { opacity:1; transform:scale(1.1); } }
//         .sidebar-item-actions { display: none; }
//         .sidebar-row:hover .sidebar-item-actions { display: flex; }
//       `}</style>

//       <div style={{ display: "flex", height: "100vh", fontFamily: "'Inter','Segoe UI',system-ui,sans-serif", color: C.text, overflow: "hidden", background: C.bg }}>

//         {/* ══════════════════════════════════════════════════════════════════
//             SIDEBAR  (Feature 1: collapsible)
//         ══════════════════════════════════════════════════════════════════ */}
//         <div style={{
//           width: sidebarOpen ? 248 : 0,
//           background: C.surface,
//           borderRight: sidebarOpen ? `1px solid ${C.border}` : "none",
//           display: "flex", flexDirection: "column", height: "100vh", flexShrink: 0,
//           overflow: "hidden",
//           transition: "width 0.2s ease",
//         }}>
//           {/* Logo + search */}
//           <div style={{ padding: "14px 12px 10px", borderBottom: `1px solid ${C.border}`, flexShrink: 0 }}>
//             <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
//               <Icon d={ICONS.leaf} size={20} stroke={C.accent} />
//               <span style={{ fontWeight: 700, fontSize: 15, color: C.text }}>Agentic RAG</span>
//             </div>
//             <div style={{ display: "flex", alignItems: "center", gap: 6, background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 8, padding: "6px 10px" }}>
//               <Icon d={ICONS.search} size={14} />
//               <input value={sideSearch} onChange={e => setSideSearch(e.target.value)} placeholder="Search…"
//                 style={{ flex: 1, background: "transparent", border: "none", outline: "none", color: C.text, fontSize: 12, fontFamily: "inherit" }} />
//             </div>
//           </div>

//           <div style={{ flex: 1, overflowY: "auto", padding: "8px 0" }}>
//             {/* New Chat */}
//             <div style={{ padding: "4px 8px 8px" }}>
//               <Btn variant="surface" onClick={() => openNewChat(null)} style={{ width: "100%", justifyContent: "center" }}>
//                 <Icon d={ICONS.plus} size={14} stroke={C.accent} /> New chat
//               </Btn>
//             </div>

//             {/* ── Recent Chats ── */}
//             <div style={{ padding: "8px 14px 4px", fontSize: 11, fontWeight: 700, color: C.textMute, letterSpacing: "0.08em" }}>RECENT CHATS</div>
//             {filteredApiSessions.length === 0 && (
//               <div style={{ fontSize: 12, color: C.textMute, padding: "4px 18px" }}>No chats yet</div>
//             )}
//             {filteredApiSessions.map(s => {
//               const label = s.title || s.preview || "Untitled";
//               return (
//                 <div key={s.session_id} className="sidebar-row"
//                   style={{ position: "relative", display: "flex", alignItems: "center", margin: "1px 6px", borderRadius: 8, background: activeSession?.sessionId === s.session_id ? C.accentBg : "transparent" }}>
//                   <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 8, padding: "7px 36px 7px 12px", color: activeSession?.sessionId === s.session_id ? C.accent : C.textSub, fontSize: 13, fontWeight: activeSession?.sessionId === s.session_id ? 600 : 400, cursor: "pointer", overflow: "hidden" }}
//                     onClick={() => openExistingSession(s.session_id, null)}>
//                     <Icon d={ICONS.chat} size={14} stroke="currentColor" />
//                     <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{label}</span>
//                   </div>
//                   {/* Feature 4: rename + delete for recent chats */}
//                   <div className="sidebar-item-actions" style={{ position: "absolute", right: 6, gap: 2 }}>
//                     <button onClick={e => openRename("session", s.session_id, label, e)} title="Rename"
//                       style={{ background: "none", border: "none", cursor: "pointer", padding: 3, borderRadius: 4, opacity: 0.6 }}>
//                       <Icon d={ICONS.edit} size={11} stroke={C.textSub} />
//                     </button>
//                     <button onClick={e => { e.stopPropagation(); deleteSession(s.session_id); }} title="Delete"
//                       style={{ background: "none", border: "none", cursor: "pointer", padding: 3, borderRadius: 4, opacity: 0.6 }}>
//                       <Icon d={ICONS.trash} size={11} stroke={C.danger} />
//                     </button>
//                   </div>
//                 </div>
//               );
//             })}

//             {/* ── Projects ── */}
//             <div style={{ padding: "12px 14px 4px", fontSize: 11, fontWeight: 700, color: C.textMute, letterSpacing: "0.08em", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
//               <span>PROJECTS</span>
//               <button onClick={() => setShowNewProject(true)} style={{ background: "none", border: "none", cursor: "pointer", padding: 2 }}>
//                 <Icon d={ICONS.plus} size={14} stroke={C.accent} />
//               </button>
//             </div>

//             {filteredProjects.map(proj => {
//               const isExpanded = expandedProjects.has(proj.id);
//               const isSelected = activeSession?.projectId === proj.id;
//               return (
//                 <div key={proj.id}>
//                   <div className="sidebar-row" style={{ display: "flex", alignItems: "center", margin: "1px 6px", borderRadius: 8, background: isSelected ? C.accentBg : "transparent", position: "relative" }}>
//                     <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 8, padding: "7px 8px 7px 12px", color: isSelected ? C.accent : C.textSub, fontSize: 13, fontWeight: isSelected ? 600 : 400, cursor: "pointer", overflow: "hidden" }}
//                       onClick={() => { setSelectedProject(proj); setExpandedProjects(prev => new Set([...prev, proj.id])); }}>
//                       <span style={{ fontSize: 15 }}>{proj.emoji}</span>
//                       <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{proj.name}</span>
//                     </div>
//                     {/* Feature 4: rename + delete for projects */}
//                     <div className="sidebar-item-actions" style={{ gap: 2 }}>
//                       <button onClick={e => openRename("project", proj.id, proj.name, e)} title="Rename project"
//                         style={{ background: "none", border: "none", cursor: "pointer", padding: 3, borderRadius: 4, opacity: 0.6 }}>
//                         <Icon d={ICONS.edit} size={11} stroke={C.textSub} />
//                       </button>
//                       <button onClick={e => { e.stopPropagation(); setDeleteTarget({ type: "project", id: proj.id, name: proj.name }); setShowDeleteConfirm(true); }} title="Delete project"
//                         style={{ background: "none", border: "none", cursor: "pointer", padding: 3, borderRadius: 4, opacity: 0.6 }}>
//                         <Icon d={ICONS.trash} size={11} stroke={C.danger} />
//                       </button>
//                     </div>
//                     <button onClick={e => { e.stopPropagation(); setExpandedProjects(prev => { const s = new Set(prev); s.has(proj.id) ? s.delete(proj.id) : s.add(proj.id); return s; }); }}
//                       style={{ background: "none", border: "none", cursor: "pointer", padding: "7px 8px", color: C.textMute, flexShrink: 0 }}>
//                       <Icon d={isExpanded ? ICONS.chevD : ICONS.chevR} size={13} stroke={C.textMute} />
//                     </button>
//                   </div>
//                   {isExpanded && (
//                     <div>
//                       {(proj.sessions || []).map(sess => {
//                         const apiS = apiSessions.find(a => a.session_id === sess.sessionId);
//                         const label = apiS?.title || apiS?.preview || sess.title || "Chat";
//                         return (
//                           <div key={sess.sessionId} className="sidebar-row" style={{ position: "relative", display: "flex", alignItems: "center" }}>
//                             <SideItem indent={1}
//                               icon={<Icon d={ICONS.chat} size={13} stroke="currentColor" />}
//                               label={label}
//                               muted
//                               active={activeSession?.sessionId === sess.sessionId}
//                               onClick={() => openExistingSession(sess.sessionId, proj.id)}
//                             />
//                             <div className="sidebar-item-actions" style={{ position: "absolute", right: 10, gap: 2 }}>
//                               <button onClick={e => openRename("session", sess.sessionId, label, e)} title="Rename"
//                                 style={{ background: "none", border: "none", cursor: "pointer", padding: 3, borderRadius: 4, opacity: 0.6 }}>
//                                 <Icon d={ICONS.edit} size={11} stroke={C.textSub} />
//                               </button>
//                               <button onClick={e => { e.stopPropagation(); deleteSession(sess.sessionId); }} title="Delete"
//                                 style={{ background: "none", border: "none", cursor: "pointer", padding: 3, borderRadius: 4, opacity: 0.6 }}>
//                                 <Icon d={ICONS.trash} size={11} stroke={C.danger} />
//                               </button>
//                             </div>
//                           </div>
//                         );
//                       })}
//                       <SideItem indent={1} muted
//                         icon={<Icon d={ICONS.plus} size={13} stroke={C.textMute} />}
//                         label="New chat"
//                         onClick={() => openNewChat(proj.id)}
//                       />
//                     </div>
//                   )}
//                 </div>
//               );
//             })}

//             {/* ── Knowledge base PDFs ── */}
//             <div style={{ padding: "12px 14px 4px", fontSize: 11, fontWeight: 700, color: C.textMute, letterSpacing: "0.08em" }}>KNOWLEDGE BASE</div>
//             {[
//               { label: "PARC Report 2023-24",  file: "PARC Annual Report 2023-24_compressed.pdf" },
//               { label: "FAO Crop Guidelines",  file: "i5550e.pdf" },
//               { label: "Punjab Agri Rules",    file: "PbAgriDeptExtenAdapReseWing_SR_2007_20070612.pdf" },
//             ].map(({ label, file }) => (
//               <div key={file} onClick={() => window.open(`/api/pdf/${encodeURIComponent(file)}`, "_blank")}
//                 style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 12px 6px 18px", cursor: "pointer", color: C.textSub, fontSize: 12 }}>
//                 <Icon d={ICONS.book} size={13} stroke={C.textMute} />
//                 <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{label}</span>
//                 <span style={{ color: C.accentDim, fontSize: 10 }}>↗</span>
//               </div>
//             ))}
//           </div>

//           {/* User footer */}
//           <div style={{ padding: "10px 14px", borderTop: `1px solid ${C.border}`, display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
//             <div style={{ width: 30, height: 30, borderRadius: "50%", background: C.accentBg, border: `1px solid ${C.accent}44`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 700, color: C.accent }}>
//               {username[0].toUpperCase()}
//             </div>
//             <span style={{ flex: 1, fontSize: 12, color: C.textSub, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{username}</span>
//             {onLogout && (
//               <button onClick={onLogout} title="Sign out" style={{ background: "none", border: "none", cursor: "pointer" }}>
//                 <Icon d={ICONS.x} size={14} stroke={C.textMute} />
//               </button>
//             )}
//           </div>
//         </div>

//         {/* ══════════════════════════════════════════════════════════════════
//             MAIN CHAT AREA
//         ══════════════════════════════════════════════════════════════════ */}
//         <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", minWidth: 0 }}>
//           {/* Header */}
//           <div style={{ padding: "0 16px", height: 52, display: "flex", alignItems: "center", gap: 10, background: C.surface, borderBottom: `1px solid ${C.border}`, flexShrink: 0 }}>
//             {/* Feature 1: sidebar toggle button */}
//             <button onClick={() => setSidebarOpen(o => !o)} title={sidebarOpen ? "Close sidebar" : "Open sidebar"}
//               style={{ background: "none", border: `1px solid ${C.border}`, borderRadius: 7, padding: "5px 7px", cursor: "pointer", display: "flex", alignItems: "center", flexShrink: 0 }}>
//               <Icon d={sidebarOpen ? ICONS.panelClose : ICONS.panelOpen} size={15} stroke={C.textSub} />
//             </button>

//             <span style={{ fontSize: 16 }}>🌾</span>
//             <div style={{ flex: 1, minWidth: 0 }}>
//               <span style={{ fontSize: 14, fontWeight: 600, color: C.text }}>
//                 {activeSession ? activeSession.title : "Agricultural Knowledge Base"}
//               </span>
//               {activeSession?.projectId && (
//                 <span style={{ fontSize: 11, color: C.textMute, marginLeft: 8 }}>
//                   · {projects.find(p => p.id === activeSession.projectId)?.name}
//                 </span>
//               )}
//             </div>

//             {/* Feature 2: Tavily web search toggle */}
//             <button onClick={() => setWebSearch(w => !w)}
//               title={webSearch ? "Web search ON (Tavily) — click to disable" : "Web search OFF — click to enable Tavily"}
//               style={{
//                 display: "flex", alignItems: "center", gap: 5, padding: "4px 10px", borderRadius: 20,
//                 background: webSearch ? C.tealBg : "transparent",
//                 border: `1px solid ${webSearch ? C.teal : C.border}`,
//                 cursor: "pointer", fontSize: 12, fontWeight: 600,
//                 color: webSearch ? C.teal : C.textMute,
//                 transition: "all 0.15s",
//               }}>
//               <div style={{ width: 7, height: 7, borderRadius: "50%", background: webSearch ? C.teal : C.textMute, boxShadow: webSearch ? `0 0 5px ${C.teal}` : "none", transition: "all 0.15s" }} />
//               Web Search {webSearch ? "ON" : "OFF"}
//             </button>

//             {/* Feature 3: PDF export of current chat */}
//             <StatusBadge chunks={chunkCount} />
//             {activeSession && (
//               <button
//                 onClick={() => exportChatAsPDF(currentMessages, activeSession.title)}
//                 title="Download chat as PDF"
//                 style={{ display: "flex", alignItems: "center", gap: 5, padding: "4px 10px", borderRadius: 8, background: "none", border: `1px solid ${C.border}`, cursor: "pointer", fontSize: 12, color: C.textSub, whiteSpace: "nowrap" }}>
//                 <Icon d={ICONS.pdf} size={13} stroke={C.textSub} />
//                 Save PDF
//               </button>
//             )}
//             <button onClick={() => setShowTrace(t => !t)} title={showTrace ? "Hide trace" : "Show trace"}
//               style={{ background: "none", border: `1px solid ${C.border}`, borderRadius: 6, padding: "4px 8px", cursor: "pointer", color: C.amber, fontSize: 12, display: "flex", alignItems: "center", gap: 5, whiteSpace: "nowrap" }}>
//               <Icon d={ICONS.trace} size={13} stroke={C.amber} />
//               Trace
//             </button>
//           </div>

//           {/* Chat area */}
//           <div ref={chatRef} style={{ flex: 1, overflowY: "auto", padding: "20px 24px", display: "flex", flexDirection: "column", gap: 16 }}>
//             {!activeSession ? (
//               <Welcome onSend={(p) => { openNewChat(null); setTimeout(() => sendMessage(p), 50); }} />
//             ) : currentMessages.length === 0 ? (
//               <Welcome onSend={sendMessage} />
//             ) : (
//               currentMessages.map((m, i) => (
//                 <Message key={i} role={m.role} content={m.content} ts={m.ts} usedRag={m.usedRag}
//                   uploadedFile={m.uploadedFile}
//                   sourceType={m.sourceType}
//                   mcpTool={m.mcpTool}
//                   onRegenerate={m.role === "assistant" ? () => {
//                     const prev = currentMessages.slice(0, i).reverse().find(x => x.role === "user");
//                     if (prev) sendMessage(prev.content);
//                   } : null}
//                 />
//               ))
//             )}
//             {loading && <TypingDots />}
//           </div>

//           {/* Input (Feature 5: "+" file upload button) */}
//           <div style={{ padding: "12px 20px 16px", borderTop: `1px solid ${C.border}`, background: C.surface, flexShrink: 0 }}>
//             {!activeSession && (
//               <div style={{ fontSize: 12, color: C.textMute, textAlign: "center", marginBottom: 8 }}>
//                 Click <strong style={{ color: C.accent }}>+ New chat</strong> or select a conversation to start.
//               </div>
//             )}

//             {/* Pending file badge */}
//             {pendingFile && (
//               <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 8, padding: "5px 10px", background: C.accentBg, border: `1px solid ${C.accentDim}`, borderRadius: 8, width: "fit-content" }}>
//                 <Icon d={ICONS.attach} size={12} stroke={C.accent} />
//                 <span style={{ fontSize: 12, color: C.accent, fontWeight: 500 }}>{pendingFile.name}</span>
//                 <span style={{ fontSize: 11, color: C.textSub }}>will be used in next message</span>
//                 <button onClick={() => setPendingFile(null)} style={{ background: "none", border: "none", cursor: "pointer", padding: 0, marginLeft: 4 }}>
//                   <Icon d={ICONS.x} size={11} stroke={C.textSub} />
//                 </button>
//               </div>
//             )}

//             {uploadingFile && (
//               <div style={{ fontSize: 12, color: C.teal, marginBottom: 8 }}>⏳ Uploading document…</div>
//             )}

//             <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
//               {/* Feature 5: file upload "+" button */}
//               <button
//                 onClick={() => fileInputRef.current?.click()}
//                 disabled={!activeSession || uploadingFile}
//                 title="Attach a document (PDF, TXT, DOCX) to your message"
//                 style={{
//                   width: 38, height: 38, borderRadius: 9, border: `1px solid ${C.border}`,
//                   background: C.surface2, cursor: activeSession ? "pointer" : "not-allowed",
//                   display: "flex", alignItems: "center", justifyContent: "center",
//                   flexShrink: 0, alignSelf: "flex-end",
//                   opacity: activeSession ? 1 : 0.4, transition: "all 0.15s",
//                   color: pendingFile ? C.accent : C.textSub,
//                 }}
//                 onMouseEnter={e => { if (activeSession) e.currentTarget.style.borderColor = C.accent; }}
//                 onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; }}>
//                 <Icon d={ICONS.attach} size={15} stroke={pendingFile ? C.accent : C.textSub} />
//               </button>
//               <input ref={fileInputRef} type="file" accept=".pdf,.txt,.docx,.csv,.md"
//                 style={{ display: "none" }} onChange={handleFileSelect} />

//               <div style={{ flex: 1, background: C.surface2, border: `1px solid ${activeSession ? C.borderHi : C.border}`, borderRadius: 10, padding: "10px 14px" }}>
//                 <textarea ref={textareaRef} rows={2} value={input}
//                   onChange={e => setInput(e.target.value)}
//                   onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
//                   placeholder={
//                     !activeSession ? "Select or create a chat first" :
//                     webSearch ? "Ask anything — web search is ON (Tavily)… (Enter to send)" :
//                     "Ask about crops, diseases, PARC activities… (Enter to send)"
//                   }
//                   disabled={!activeSession}
//                   style={{ width: "100%", background: "transparent", border: "none", outline: "none", color: C.text, fontSize: 14, fontFamily: "inherit", resize: "none", lineHeight: 1.5 }} />
//               </div>
//               <button onClick={() => sendMessage()} disabled={loading || !input.trim() || !activeSession}
//                 style={{ width: 42, height: 42, borderRadius: 10, border: "none", background: C.accent, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", alignSelf: "flex-end", flexShrink: 0, opacity: (loading || !input.trim() || !activeSession) ? 0.4 : 1, transition: "opacity 0.15s" }}>
//                 <Icon d={ICONS.send} size={16} stroke="#fff" />
//               </button>
//             </div>
//           </div>
//         </div>

//         {/* ══════════════════════════════════════════════════════════════════
//             TRACE PANEL (collapsible)
//         ══════════════════════════════════════════════════════════════════ */}
//         {showTrace && (
//           <div style={{ width: 290, background: C.surface, borderLeft: `1px solid ${C.border}`, display: "flex", flexDirection: "column", overflow: "hidden", flexShrink: 0 }}>
//             <TracePanel
//               trace={trace}
//               status={status}
//               statusError={statusError}
//             />
//           </div>
//         )}
//       </div>

//       {/* ── Modals ───────────────────────────────────────────────────────── */}

//       {/* New Project */}
//       <Modal open={showNewProject} onClose={() => setShowNewProject(false)} title="Create new project">
//         <div style={{ marginBottom: 14 }}>
//           <label style={{ fontSize: 12, color: C.textSub, display: "block", marginBottom: 6 }}>Icon</label>
//           <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
//             {EMOJIS.map(e => (
//               <button key={e} onClick={() => setNewProjEmoji(e)}
//                 style={{ fontSize: 20, padding: "4px 8px", borderRadius: 8, cursor: "pointer", border: `1px solid ${newProjEmoji === e ? C.accent : C.border}`, background: newProjEmoji === e ? C.accentBg : C.surface2, fontFamily: "inherit" }}>
//                 {e}
//               </button>
//             ))}
//           </div>
//         </div>
//         <TextInput label="Project name" value={newProjName} onChange={setNewProjName} placeholder="e.g. Wheat Disease Research" autoFocus />
//         <TextInput label="Description (optional)" value={newProjDesc} onChange={setNewProjDesc} placeholder="What is this project about?" multiline />
//         <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", marginTop: 4 }}>
//           <Btn onClick={() => setShowNewProject(false)}>Cancel</Btn>
//           <Btn variant="primary" onClick={createProject} disabled={!newProjName.trim()}>Create project</Btn>
//         </div>
//       </Modal>

//       {/* Feature 4: Rename modal (sessions + projects) */}
//       <Modal open={showRename} onClose={() => { setShowRename(false); setRenameTarget(null); }}
//         title={`Rename ${renameTarget?.type === "project" ? "project" : "conversation"}`} width={400}>
//         <TextInput label="New name" value={renameName} onChange={setRenameName}
//           placeholder={renameTarget?.type === "project" ? "Project name" : "Conversation title"}
//           autoFocus />
//         <div style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
//           <Btn onClick={() => { setShowRename(false); setRenameTarget(null); }}>Cancel</Btn>
//           <Btn variant="primary" onClick={commitRename} disabled={!renameName.trim()}>Save</Btn>
//         </div>
//       </Modal>

//       {/* Delete confirm */}
//       <Modal open={showDeleteConfirm} onClose={() => { setShowDeleteConfirm(false); setDeleteTarget(null); }} title="Confirm deletion" width={380}>
//         <div style={{ fontSize: 13, color: C.textSub, marginBottom: 20, lineHeight: 1.6 }}>
//           Delete <strong style={{ color: C.text }}>{deleteTarget?.name}</strong>? This will remove all its chats and data.
//         </div>
//         <div style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
//           <Btn onClick={() => { setShowDeleteConfirm(false); setDeleteTarget(null); }}>Cancel</Btn>
//           <button onClick={() => { if (deleteTarget?.type === "project") deleteProject(deleteTarget.id); }}
//             style={{ padding: "7px 14px", borderRadius: 8, background: C.danger, color: "#fff", border: "none", cursor: "pointer", fontWeight: 600, fontSize: 13, fontFamily: "inherit" }}>
//             Delete
//           </button>
//         </div>
//       </Modal>
//     </>
//   );
// }




// // /**
// //  * ProjectManager.jsx
// //  * ==================
// //  * Unified component: original RAGDashboard UI/quality + ChatGPT-style
// //  * project sidebar + real /api/chat calls.
// //  *
// //  * Props:
// //  *   username  string   — logged-in username
// //  *   token     string   — JWT for auth headers
// //  *   onLogout  fn       — called when user clicks logout
// //  */

// // import { useState, useRef, useEffect, useCallback } from "react";

// // // ── Palette ────────────────────────────────────────────────────────────────────
// // const C = {
// //   bg:        "#0c1108",
// //   surface:   "#141c0f",
// //   surface2:  "#1c2614",
// //   surface3:  "#222e18",
// //   border:    "#2a3d1e",
// //   borderHi:  "#3d5a2a",
// //   accent:    "#7ab648",
// //   accentDim: "#4a7a1e",
// //   accentBg:  "rgba(122,182,72,0.10)",
// //   amber:     "#e8a020",
// //   amberDim:  "#7a4e00",
// //   amberBg:   "rgba(232,160,32,0.10)",
// //   text:      "#dde8cc",
// //   textSub:   "#7a9460",
// //   textMute:  "#4a6035",
// //   userBub:   "#1a2e10",
// //   botBub:    "#0f1a08",
// //   danger:    "#c0392b",
// //   dangerBg:  "rgba(192,57,43,0.12)",
// // };

// // // ── SVG Icon helper ────────────────────────────────────────────────────────────
// // const Icon = ({ d, size = 16, stroke = C.textSub, fill = "none" }) => (
// //   <svg width={size} height={size} viewBox="0 0 24 24" fill={fill}
// //     stroke={stroke} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round"
// //     style={{ flexShrink: 0 }}>
// //     <path d={d} />
// //   </svg>
// // );

// // const ICONS = {
// //   leaf:      "M12 2a4 4 0 0 1 4 4v2h2a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2V6a4 4 0 0 1 4-4z",
// //   chat:      "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z",
// //   folder:    "M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z",
// //   file:      "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H8",
// //   plus:      "M12 5v14M5 12h14",
// //   trash:     "M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6",
// //   edit:      "M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z",
// //   upload:    "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12",
// //   download:  "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3",
// //   globe:     "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zM2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z",
// //   book:      "M4 19.5A2.5 2.5 0 0 1 6.5 17H20M4 19.5A2.5 2.5 0 0 0 6.5 22H20V2H6.5A2.5 2.5 0 0 0 4 4.5v15z",
// //   chevD:     "M6 9l6 6 6-6",
// //   chevR:     "M9 18l6-6-6-6",
// //   chevL:     "M15 18l-6-6 6-6",
// //   x:         "M18 6L6 18M6 6l12 12",
// //   search:    "M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z",
// //   memory:    "M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3M12 17h.01",
// //   send:      "M22 2L11 13M22 2L15 22 11 13 2 9l20-7z",
// //   check:     "M20 6L9 17 4 12",
// //   copy:      "M20 9H11a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2v-9a2 2 0 0 0-2-2zM5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1",
// //   thumbUp:   "M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3",
// //   thumbDown: "M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zM17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17",
// //   share:     "M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8M16 6l-4-4-4 4M12 2v13",
// //   trace:     "M3 3h18v18H3zM9 9h6M9 13h6M9 17h4",
// //   bot:       "M12 2a4 4 0 0 1 4 4v2h2a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2V6a4 4 0 0 1 4-4zM9 10H7v2h2v-2zm8 0h-2v2h2v-2zm-5 4h-2v2h2v-2z",
// //   user:      "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
// //   snapshot:  "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H8",
// //   reset:     "M1 4v6h6M23 20v-6h-6M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15",
// //   sources:   "M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2zM22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z",
// //   regen:     "M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15",
// //   export:    "M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8M16 6l-4-4-4 4M12 2v13",
// // };

// // // ── Utility ───────────────────────────────────────────────────────────────────
// // const now = () => new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

// // // ── Citation parser (from original RAGDashboard) ───────────────────────────────
// // function parseSources(content) {
// //   const sourcesMatch = content.match(/SOURCES:\s*\n([\s\S]+)$/i);
// //   const mainText = sourcesMatch
// //     ? content.slice(0, content.indexOf(sourcesMatch[0])).trim()
// //     : content;
// //   const sources = [];
// //   if (sourcesMatch) {
// //     const lines = sourcesMatch[1].trim().split("\n").filter(Boolean);
// //     lines.forEach(line => {
// //       const docMatch = line.match(/\[(\d+)\]\s*(.+?)\s*\|\s*[Pp]age\s*(\d+)/);
// //       if (docMatch) {
// //         sources.push({ num: parseInt(docMatch[1]), filename: docMatch[2].trim(), page: parseInt(docMatch[3]), type: "document" });
// //         return;
// //       }
// //       const webMatch = line.match(/\[Web\s*(\d+)\]\s*(.+?)\s*—\s*(https?:\/\/\S+)/);
// //       if (webMatch) {
// //         sources.push({ num: parseInt(webMatch[1]), title: webMatch[2].trim(), url: webMatch[3].trim(), type: "web" });
// //       }
// //     });
// //   }
// //   return { mainText, sources };
// // }

// // function renderTextWithCitations(text, sources, onCiteClick) {
// //   const parts = text.split(/(\[(?:Web\s*)?\d+\])/g);
// //   return parts.map((part, i) => {
// //     const match = part.match(/^\[(?:Web\s*)?(\d+)\]$/);
// //     if (match) {
// //       const num = parseInt(match[1]);
// //       const isWeb = part.toLowerCase().includes("web");
// //       const src = sources.find(s => s.num === num && (isWeb ? s.type === "web" : s.type === "document"))
// //                || sources.find(s => s.num === num);
// //       return (
// //         <sup key={i} onClick={() => src && onCiteClick(src)}
// //           title={src ? (src.type === "document" ? `${src.filename} — Page ${src.page}` : src.title) : ""}
// //           style={{
// //             cursor: src ? "pointer" : "default",
// //             color: src ? (src.type === "web" ? C.amber : C.accent) : C.textMute,
// //             fontWeight: 700, fontSize: "0.72em", marginLeft: 1,
// //             padding: "1px 4px", borderRadius: 3,
// //             background: src ? (src.type === "web" ? "#2a1e00" : "#16301a") : "transparent",
// //             border: src ? `1px solid ${src.type === "web" ? C.amberDim : C.accentDim}` : "none",
// //             userSelect: "none",
// //           }}>
// //           {part}
// //         </sup>
// //       );
// //     }
// //     return (
// //       <span key={i}>
// //         {part.split("\n").map((line, j, arr) => (
// //           <span key={j}>{line}{j < arr.length - 1 && <br />}</span>
// //         ))}
// //       </span>
// //     );
// //   });
// // }

// // function SourcesList({ sources }) {
// //   if (!sources.length) return null;
// //   const open = (src) => {
// //     if (src.type === "document") window.open(`/api/pdf/${encodeURIComponent(src.filename)}#page=${src.page}`, "_blank");
// //     else window.open(src.url, "_blank");
// //   };
// //   return (
// //     <div style={{ marginTop: 12, paddingTop: 10, borderTop: `1px solid ${C.border}` }}>
// //       <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: C.textMute, marginBottom: 6 }}>
// //         References
// //       </div>
// //       {sources.map((src, i) => (
// //         <div key={i} onClick={() => open(src)}
// //           style={{ display: "flex", alignItems: "flex-start", gap: 7, marginBottom: 5, cursor: "pointer", padding: "5px 7px", borderRadius: 7, transition: "background 0.15s" }}
// //           onMouseEnter={e => e.currentTarget.style.background = C.surface2}
// //           onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
// //           <span style={{ minWidth: 20, height: 20, borderRadius: 4, flexShrink: 0, background: src.type === "document" ? C.accentDim : C.amberDim, border: `1px solid ${src.type === "document" ? C.accent : C.amber}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 9, fontWeight: 700, color: src.type === "document" ? C.accent : C.amber }}>
// //             {src.num}
// //           </span>
// //           <div style={{ fontSize: 11.5, color: C.textSub, lineHeight: 1.5 }}>
// //             {src.type === "document" ? (
// //               <><span style={{ color: C.text, fontWeight: 500 }}>{src.filename}</span><span style={{ color: C.textMute }}> — Page {src.page}</span><span style={{ color: C.accentDim, fontSize: 10, marginLeft: 5 }}>↗ open PDF</span></>
// //             ) : (
// //               <><span style={{ color: C.text, fontWeight: 500 }}>{src.title}</span><span style={{ color: C.amberDim, fontSize: 10, marginLeft: 5 }}>↗ web</span></>
// //             )}
// //           </div>
// //         </div>
// //       ))}
// //     </div>
// //   );
// // }

// // // ── Message bubble ─────────────────────────────────────────────────────────────
// // function Message({ role, content, ts, usedRag, onRegenerate }) {
// //   const [copied, setCopied] = useState(false);
// //   const [liked, setLiked]   = useState(null);
// //   const [showSrc, setShowSrc] = useState(true);
// //   const isUser = role === "user";

// //   const ActionBtn = ({ icon, title, onClick, active, activeColor }) => (
// //     <button onClick={onClick} title={title}
// //       style={{ background: "none", border: "none", cursor: "pointer", padding: "4px 5px", borderRadius: 6, display: "flex", alignItems: "center", opacity: 0.55, transition: "opacity 0.15s" }}
// //       onMouseEnter={e => { e.currentTarget.style.opacity = "1"; e.currentTarget.style.background = C.surface2; }}
// //       onMouseLeave={e => { e.currentTarget.style.opacity = "0.55"; e.currentTarget.style.background = "none"; }}>
// //       <Icon d={icon} size={14} stroke={active ? (activeColor || C.accent) : C.textSub} />
// //     </button>
// //   );

// //   const ragBadge = !isUser && usedRag !== null && usedRag !== undefined && (
// //     <span style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 9.5, fontWeight: 600, letterSpacing: "0.03em", padding: "2px 7px", borderRadius: 20, background: usedRag ? "#16301a" : "#2a2210", border: `1px solid ${usedRag ? C.accentDim : C.amberDim}`, color: usedRag ? C.accent : C.amber, marginLeft: 6 }}>
// //       {usedRag ? "RAG" : "🌐 Web"}
// //     </span>
// //   );

// //   return (
// //     <div style={{ display: "flex", flexDirection: "column", alignItems: isUser ? "flex-end" : "flex-start", gap: 4 }}>
// //       <div style={{ display: "flex", alignItems: "center", gap: 6, flexDirection: isUser ? "row-reverse" : "row" }}>
// //         <div style={{ width: 26, height: 26, borderRadius: "50%", background: isUser ? C.accentDim : "#1a2610", border: `1px solid ${isUser ? C.accent : C.border}`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
// //           <Icon d={isUser ? ICONS.user : ICONS.bot} size={13} stroke={isUser ? C.accent : C.textSub} />
// //         </div>
// //         <span style={{ fontSize: 11, color: C.textMute, display: "flex", alignItems: "center" }}>
// //           {isUser ? "You" : "RAG Assistant"} · {ts}{ragBadge}
// //         </span>
// //       </div>

// //       <div style={{ maxWidth: "78%", background: isUser ? C.userBub : C.botBub, border: `1px solid ${isUser ? C.accentDim : C.border}`, borderRadius: isUser ? "14px 4px 14px 14px" : "4px 14px 14px 14px", padding: "10px 14px", lineHeight: 1.65, fontSize: 14, color: C.text }}>
// //         {isUser ? (
// //           <span style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>{content}</span>
// //         ) : (() => {
// //           const { mainText, sources } = parseSources(content);
// //           const onCiteClick = src => {
// //             if (src.type === "document") window.open(`/api/pdf/${encodeURIComponent(src.filename)}#page=${src.page}`, "_blank");
// //             else window.open(src.url, "_blank");
// //           };
// //           return (
// //             <>
// //               <div style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
// //                 {renderTextWithCitations(mainText, sources, onCiteClick)}
// //               </div>
// //               {showSrc && <SourcesList sources={sources} />}
// //             </>
// //           );
// //         })()}
// //       </div>

// //       {!isUser && (
// //         <div style={{ display: "flex", alignItems: "center", gap: 1, paddingLeft: 4, marginTop: -2 }}>
// //           <ActionBtn icon={copied ? ICONS.check : ICONS.copy} title="Copy" onClick={() => { navigator.clipboard.writeText(content); setCopied(true); setTimeout(() => setCopied(false), 1500); }} active={copied} activeColor={C.accent} />
// //           <ActionBtn icon={ICONS.thumbUp} title="Good response" onClick={() => setLiked(l => l === "up" ? null : "up")} active={liked === "up"} activeColor={C.accent} />
// //           <ActionBtn icon={ICONS.thumbDown} title="Bad response" onClick={() => setLiked(l => l === "down" ? null : "down")} active={liked === "down"} activeColor={C.danger} />
// //           <ActionBtn icon={ICONS.share} title="Share" onClick={() => navigator.clipboard.writeText(content)} />
// //           {onRegenerate && <ActionBtn icon={ICONS.regen} title="Regenerate" onClick={onRegenerate} />}
// //           <div style={{ width: 1, height: 14, background: C.border, margin: "0 3px" }} />
// //           <ActionBtn icon={ICONS.sources} title={showSrc ? "Hide sources" : "Show sources"} onClick={() => setShowSrc(s => !s)} active={showSrc} activeColor={C.accent} />
// //         </div>
// //       )}
// //     </div>
// //   );
// // }

// // // ── Typing dots ────────────────────────────────────────────────────────────────
// // function TypingDots() {
// //   return (
// //     <div style={{ display: "flex", alignItems: "flex-start", gap: 6 }}>
// //       <div style={{ width: 26, height: 26, borderRadius: "50%", background: "#1a2610", border: `1px solid ${C.border}`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
// //         <Icon d={ICONS.bot} size={13} stroke={C.textSub} />
// //       </div>
// //       <div style={{ background: C.botBub, border: `1px solid ${C.border}`, borderRadius: "4px 14px 14px 14px", padding: "12px 16px", display: "flex", gap: 5, alignItems: "center" }}>
// //         {[0, 0.18, 0.36].map((delay, i) => (
// //           <div key={i} style={{ width: 7, height: 7, borderRadius: "50%", background: C.accentDim, animation: "pulse 1.2s ease-in-out infinite", animationDelay: `${delay}s` }} />
// //         ))}
// //       </div>
// //     </div>
// //   );
// // }

// // // ── Trace panel ────────────────────────────────────────────────────────────────
// // function TracePanel({ trace }) {
// //   return (
// //     <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
// //       <div style={{ padding: "14px 16px 10px", borderBottom: `1px solid ${C.border}`, display: "flex", alignItems: "center", gap: 8 }}>
// //         <Icon d={ICONS.trace} size={15} stroke={C.amber} />
// //         <span style={{ fontSize: 13, fontWeight: 600, color: C.amber }}>Pipeline trace</span>
// //       </div>
// //       <div style={{ flex: 1, overflowY: "auto", padding: "12px 14px" }}>
// //         {!trace ? (
// //           <div style={{ color: C.textMute, fontSize: 12, textAlign: "center", marginTop: 40, lineHeight: 1.7 }}>
// //             Pipeline step timings<br />appear here after each query
// //           </div>
// //         ) : (
// //           <pre style={{ fontFamily: "'JetBrains Mono','Fira Code',monospace", fontSize: 11, color: C.textSub, lineHeight: 1.75, whiteSpace: "pre-wrap", wordBreak: "break-word", margin: 0 }}>
// //             {trace}
// //           </pre>
// //         )}
// //       </div>
// //     </div>
// //   );
// // }

// // // ── Welcome screen ─────────────────────────────────────────────────────────────
// // function Welcome({ onSend }) {
// //   const prompts = [
// //     "What wheat diseases are monitored in Punjab?",
// //     "Summarise PARC's 2023-24 research highlights",
// //     "What is the role of the Agriculture Extension Wing?",
// //     "Which FAO guidelines cover Ug99 rust?",
// //   ];
// //   return (
// //     <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: 32, gap: 28 }}>
// //       <div style={{ textAlign: "center" }}>
// //         <div style={{ fontSize: 40, marginBottom: 12 }}>🌾</div>
// //         <div style={{ fontSize: 22, fontWeight: 700, color: C.text, letterSpacing: "-0.02em", marginBottom: 6 }}>
// //           Agricultural RAG Assistant
// //         </div>
// //         <div style={{ fontSize: 13, color: C.textSub, maxWidth: 380, lineHeight: 1.6 }}>
// //           Ask about PARC Annual Report 2023-24, FAO Crop Monitoring Guidelines, or Punjab Agriculture Rules.
// //         </div>
// //       </div>
// //       <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, width: "100%", maxWidth: 560 }}>
// //         {prompts.map((p, i) => (
// //           <button key={i} onClick={() => onSend(p)}
// //             style={{ background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 10, padding: "10px 14px", color: C.textSub, fontSize: 12, textAlign: "left", cursor: "pointer", lineHeight: 1.5, transition: "border-color 0.15s, color 0.15s", fontFamily: "inherit" }}
// //             onMouseEnter={e => { e.currentTarget.style.borderColor = C.accent; e.currentTarget.style.color = C.text; }}
// //             onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.color = C.textSub; }}>
// //             {p}
// //           </button>
// //         ))}
// //       </div>
// //     </div>
// //   );
// // }

// // // ── Sidebar item ───────────────────────────────────────────────────────────────
// // const SideItem = ({ icon, label, active, onClick, indent = 0, muted = false }) => (
// //   <div onClick={onClick}
// //     style={{ display: "flex", alignItems: "center", gap: 8, padding: `7px 12px 7px ${12 + indent * 16}px`, borderRadius: 8, cursor: "pointer", margin: "1px 6px", background: active ? C.accentBg : "transparent", color: active ? C.accent : muted ? C.textMute : C.textSub, fontSize: 13, fontWeight: active ? 600 : 400, transition: "all 0.12s" }}>
// //     {icon}
// //     <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{label}</span>
// //   </div>
// // );

// // // ── Modal ──────────────────────────────────────────────────────────────────────
// // const Modal = ({ open, onClose, title, children, width = 480 }) => {
// //   if (!open) return null;
// //   return (
// //     <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center" }}
// //       onClick={onClose}>
// //       <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 14, padding: "24px 28px", width, maxWidth: "90vw", maxHeight: "80vh", overflowY: "auto" }}
// //         onClick={e => e.stopPropagation()}>
// //         <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
// //           <span style={{ fontSize: 16, fontWeight: 700, color: C.text }}>{title}</span>
// //           <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer" }}>
// //             <Icon d={ICONS.x} stroke={C.textSub} size={18} />
// //           </button>
// //         </div>
// //         {children}
// //       </div>
// //     </div>
// //   );
// // };

// // const TextInput = ({ label, value, onChange, placeholder, multiline = false }) => (
// //   <div style={{ marginBottom: 14 }}>
// //     {label && <label style={{ fontSize: 12, color: C.textSub, display: "block", marginBottom: 6 }}>{label}</label>}
// //     {multiline
// //       ? <textarea value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
// //           style={{ width: "100%", background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 8, padding: "10px 12px", color: C.text, fontSize: 13, fontFamily: "inherit", outline: "none", resize: "vertical", minHeight: 80, boxSizing: "border-box" }} />
// //       : <input value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
// //           style={{ width: "100%", background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 8, padding: "10px 12px", color: C.text, fontSize: 13, fontFamily: "inherit", outline: "none", boxSizing: "border-box" }} />
// //     }
// //   </div>
// // );

// // const Btn = ({ children, onClick, variant = "ghost", danger = false, style: sx = {}, disabled = false }) => {
// //   const base = { display: "inline-flex", alignItems: "center", gap: 6, padding: "7px 12px", borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: disabled ? "not-allowed" : "pointer", border: "none", transition: "all 0.15s", opacity: disabled ? 0.5 : 1, fontFamily: "inherit" };
// //   const variants = {
// //     primary: { background: C.accent, color: C.bg },
// //     ghost:   { background: "transparent", color: danger ? C.danger : C.textSub, border: `1px solid ${danger ? C.danger + "55" : C.border}` },
// //     surface: { background: C.surface2, color: C.text, border: `1px solid ${C.border}` },
// //   };
// //   return <button style={{ ...base, ...variants[variant], ...sx }} onClick={onClick} disabled={disabled}>{children}</button>;
// // };

// // // ── Status badge ───────────────────────────────────────────────────────────────
// // function StatusBadge({ chunks }) {
// //   const ok = chunks > 0;
// //   return (
// //     <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "4px 10px", borderRadius: 20, background: ok ? "#1a3310" : "#3a1010", border: `1px solid ${ok ? C.accentDim : C.danger}`, fontSize: 12, color: ok ? C.accent : "#e74c3c" }}>
// //       <div style={{ width: 7, height: 7, borderRadius: "50%", background: ok ? C.accent : C.danger, boxShadow: ok ? `0 0 6px ${C.accent}` : "none" }} />
// //       {ok ? `${chunks.toLocaleString()} chunks` : "Empty — index first"}
// //     </div>
// //   );
// // }

// // // ════════════════════════════════════════════════════════════════════════════════
// // //  Main component
// // // ════════════════════════════════════════════════════════════════════════════════
// // const EMOJIS = ["🌱", "🌾", "🪴", "🌽", "🍃", "🌿", "🌻", "🌴", "🫘", "🍀"];

// // export default function ProjectManager({ username = "user", token, onLogout }) {
// //   // ── Projects / chats ─────────────────────────────────────────────────────
// //   const [projects, setProjects]           = useState([]);
// //   const [expandedProjects, setExpandedProjects] = useState(new Set());
// //   const [selectedProject, setSelectedProject]   = useState(null);

// //   // ── Active session: maps to a real /api session_id per chat ──────────────
// //   // activeSession: { sessionId, projectId|null, title }
// //   const [activeSession, setActiveSession] = useState(null);

// //   // ── Per-session message cache: { [sessionId]: [...messages] } ────────────
// //   const [msgCache, setMsgCache]   = useState({});
// //   const [loading, setLoading]     = useState(false);
// //   const [trace, setTrace]         = useState(null);
// //   const [input, setInput]         = useState("");

// //   // ── Backend / sidebar state ───────────────────────────────────────────────
// //   const [apiSessions, setApiSessions] = useState([]);   // /api/sessions list
// //   const [status, setStatus]           = useState(null);
// //   const [chunkCount, setChunkCount]   = useState(0);
// //   const [statusError, setStatusError] = useState(null);
// //   const [sideSearch, setSideSearch]   = useState("");
// //   const [showTrace, setShowTrace]     = useState(true);

// //   // ── Modals ────────────────────────────────────────────────────────────────
// //   const [showNewProject, setShowNewProject] = useState(false);
// //   const [newProjName, setNewProjName]       = useState("");
// //   const [newProjDesc, setNewProjDesc]       = useState("");
// //   const [newProjEmoji, setNewProjEmoji]     = useState("🌱");
// //   const [showRename, setShowRename]         = useState(false);
// //   const [renameTarget, setRenameTarget]     = useState(null);
// //   const [renameName, setRenameName]         = useState("");
// //   const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
// //   const [deleteTarget, setDeleteTarget]     = useState(null);

// //   const chatRef    = useRef(null);
// //   const textareaRef = useRef(null);

// //   const authHeaders = () => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : { "Content-Type": "application/json" };

// //   // ── Scroll to bottom ──────────────────────────────────────────────────────
// //   useEffect(() => {
// //     if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
// //   }, [msgCache, activeSession, loading]);

// //   // ── Poll /api/status ──────────────────────────────────────────────────────
// //   useEffect(() => {
// //     const fetch_ = () => {
// //       fetch("/api/status").then(r => r.json()).then(d => {
// //         setStatus(d);
// //         setChunkCount(d.chunk_count || 0);
// //         setStatusError(d.vector_store_error || d.pipeline_error || null);
// //       }).catch(err => { setStatusError(`Cannot reach API: ${err.message}`); setChunkCount(0); });
// //     };
// //     fetch_();
// //     const id = setInterval(fetch_, 8000);
// //     return () => clearInterval(id);
// //   }, []);

// //   // ── Load /api/sessions list ───────────────────────────────────────────────
// //   const fetchApiSessions = useCallback(() => {
// //     fetch("/api/sessions", { headers: authHeaders() })
// //       .then(r => r.json())
// //       .then(d => setApiSessions(d.sessions || []))
// //       .catch(() => {});
// //   }, [token]);

// //   useEffect(() => { fetchApiSessions(); }, [fetchApiSessions]);

// //   // ── Load projects from localStorage ──────────────────────────────────────
// //   useEffect(() => {
// //     try {
// //       const saved = localStorage.getItem(`rag_projects_${username}`);
// //       if (saved) setProjects(JSON.parse(saved));
// //     } catch (_) {}
// //   }, [username]);

// //   const saveProjects = (ps) => {
// //     setProjects(ps);
// //     try { localStorage.setItem(`rag_projects_${username}`, JSON.stringify(ps)); } catch (_) {}
// //   };

// //   // ── Open a session (or create new) ───────────────────────────────────────
// //   const openNewChat = (projectId = null) => {
// //     const sessionId = crypto.randomUUID();
// //     const proj = projectId ? projects.find(p => p.id === projectId) : null;
// //     const session = { sessionId, projectId, title: proj ? `${proj.emoji} New chat` : "New chat" };
// //     setActiveSession(session);
// //     setTrace(null);
// //     setInput("");
// //     // Register in project's session list
// //     if (projectId) {
// //       const updated = projects.map(p => {
// //         if (p.id !== projectId) return p;
// //         return { ...p, sessions: [...(p.sessions || []), { sessionId, title: "New chat", date: new Date().toISOString().slice(0, 10) }] };
// //       });
// //       saveProjects(updated);
// //     }
// //   };

// //   const openExistingSession = (sessionId, projectId = null) => {
// //     const proj = projectId ? projects.find(p => p.id === projectId) : null;
// //     const apiSess = apiSessions.find(s => s.session_id === sessionId);
// //     const title = apiSess?.title || apiSess?.preview || "Chat";
// //     setActiveSession({ sessionId, projectId, title: proj ? `${proj.emoji} ${title}` : title });
// //     setTrace(null);
// //     setInput("");
// //     // Load history if not cached
// //     if (!msgCache[sessionId]) {
// //       fetch(`/api/sessions/${sessionId}`, { headers: authHeaders() })
// //         .then(r => r.json())
// //         .then(d => {
// //           const msgs = (d.messages || []).map(m => ({
// //             role: m.role, content: m.content, ts: m.ts || now(), usedRag: m.used_rag,
// //           }));
// //           setMsgCache(prev => ({ ...prev, [sessionId]: msgs }));
// //         }).catch(() => {});
// //     }
// //   };

// //   // ── Send message ──────────────────────────────────────────────────────────
// //   const sendMessage = async (text) => {
// //     const q = (text || input).trim();
// //     if (!q || loading || !activeSession) return;
// //     setInput("");
// //     const userMsg = { role: "user", content: q, ts: now() };
// //     setMsgCache(prev => ({ ...prev, [activeSession.sessionId]: [...(prev[activeSession.sessionId] || []), userMsg] }));
// //     setLoading(true);
// //     setTrace(null);

// //     try {
// //       const res = await fetch("/api/chat", {
// //         method: "POST",
// //         headers: authHeaders(),
// //         body: JSON.stringify({ session_id: activeSession.sessionId, query: q }),
// //       });
// //       const data = await res.json();
// //       const botMsg = { role: "assistant", content: data.response || "No response received.", ts: now(), usedRag: data.used_rag };
// //       setMsgCache(prev => ({ ...prev, [activeSession.sessionId]: [...(prev[activeSession.sessionId] || []), botMsg] }));
// //       if (data.trace) setTrace(data.trace);

// //       // Auto-title the session from first message
// //       const currentMsgs = msgCache[activeSession.sessionId] || [];
// //       if (currentMsgs.filter(m => m.role === "user").length === 0) {
// //         const autoTitle = q.slice(0, 40) + (q.length > 40 ? "…" : "");
// //         setActiveSession(prev => ({ ...prev, title: autoTitle }));
// //         if (activeSession.projectId) {
// //           const updated = projects.map(p => {
// //             if (p.id !== activeSession.projectId) return p;
// //             return { ...p, sessions: (p.sessions || []).map(s => s.sessionId === activeSession.sessionId ? { ...s, title: autoTitle } : s) };
// //           });
// //           saveProjects(updated);
// //         }
// //       }
// //     } catch (err) {
// //       const errMsg = { role: "assistant", content: `❌ Could not reach the backend.\n\nError: ${err.message}`, ts: now() };
// //       setMsgCache(prev => ({ ...prev, [activeSession.sessionId]: [...(prev[activeSession.sessionId] || []), errMsg] }));
// //     } finally {
// //       setLoading(false);
// //       fetchApiSessions();
// //     }
// //   };

// //   // ── Delete session ────────────────────────────────────────────────────────
// //   const deleteSession = async (sessionId) => {
// //     if (!confirm("Delete this conversation permanently?")) return;
// //     await fetch(`/api/sessions/${sessionId}`, { method: "DELETE", headers: authHeaders() }).catch(() => {});
// //     setMsgCache(prev => { const n = { ...prev }; delete n[sessionId]; return n; });
// //     if (activeSession?.sessionId === sessionId) setActiveSession(null);
// //     fetchApiSessions();
// //   };

// //   // ── Export session ────────────────────────────────────────────────────────
// //   const exportSession = async (sessionId, format) => {
// //     try {
// //       const res = await fetch(`/api/sessions/${sessionId}/export?format=${format}`, { headers: authHeaders() });
// //       if (!res.ok) throw new Error(`Export failed (${res.status})`);
// //       const blob = await res.blob();
// //       const disposition = res.headers.get("Content-Disposition") || "";
// //       const match = disposition.match(/filename="([^"]+)"/);
// //       const filename = match ? match[1] : `chat.${format === "json" ? "json" : "md"}`;
// //       const url = URL.createObjectURL(blob);
// //       const a = document.createElement("a"); a.href = url; a.download = filename;
// //       document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
// //     } catch (err) { alert(`Export failed: ${err.message}`); }
// //   };

// //   // ── Rename session ────────────────────────────────────────────────────────
// //   const commitRename = async () => {
// //     if (!renameName.trim() || !renameTarget) return;
// //     if (renameTarget.type === "session") {
// //       await fetch(`/api/sessions/${renameTarget.id}`, {
// //         method: "PATCH", headers: authHeaders(),
// //         body: JSON.stringify({ title: renameName.trim() }),
// //       }).catch(() => {});
// //       fetchApiSessions();
// //     } else if (renameTarget.type === "project") {
// //       const updated = projects.map(p => p.id === renameTarget.id ? { ...p, name: renameName.trim() } : p);
// //       saveProjects(updated);
// //       if (selectedProject?.id === renameTarget.id) setSelectedProject(prev => ({ ...prev, name: renameName.trim() }));
// //     }
// //     setShowRename(false); setRenameTarget(null); setRenameName("");
// //   };

// //   // ── Project CRUD ──────────────────────────────────────────────────────────
// //   const createProject = () => {
// //     if (!newProjName.trim()) return;
// //     const proj = { id: "p" + Date.now(), name: newProjName.trim(), emoji: newProjEmoji, description: newProjDesc.trim(), createdAt: new Date().toISOString().slice(0, 10), sessions: [] };
// //     const updated = [...projects, proj];
// //     saveProjects(updated);
// //     setNewProjName(""); setNewProjDesc(""); setNewProjEmoji("🌱");
// //     setShowNewProject(false);
// //     setExpandedProjects(prev => new Set([...prev, proj.id]));
// //   };

// //   const deleteProject = (id) => {
// //     const updated = projects.filter(p => p.id !== id);
// //     saveProjects(updated);
// //     if (selectedProject?.id === id) setSelectedProject(null);
// //     if (activeSession?.projectId === id) setActiveSession(null);
// //     setShowDeleteConfirm(false); setDeleteTarget(null);
// //   };

// //   // ── Filtered sidebar lists ────────────────────────────────────────────────
// //   const search = sideSearch.toLowerCase();
// //   const filteredApiSessions = apiSessions.filter(s =>
// //     !search || (s.title || s.preview || "").toLowerCase().includes(search)
// //   ).filter(s => {
// //     // Only show sessions not "owned" by a project
// //     const allProjectSessionIds = new Set(projects.flatMap(p => (p.sessions || []).map(ss => ss.sessionId)));
// //     return !allProjectSessionIds.has(s.session_id);
// //   });

// //   const filteredProjects = projects.filter(p => !search || p.name.toLowerCase().includes(search));
// //   const currentMessages  = (activeSession && msgCache[activeSession.sessionId]) || [];

// //   // ── Render ────────────────────────────────────────────────────────────────
// //   return (
// //     <>
// //       <style>{`
// //         * { box-sizing: border-box; margin: 0; padding: 0; }
// //         body { background: ${C.bg}; }
// //         ::-webkit-scrollbar { width: 5px; }
// //         ::-webkit-scrollbar-track { background: transparent; }
// //         ::-webkit-scrollbar-thumb { background: ${C.border}; border-radius: 4px; }
// //         @keyframes pulse { 0%,100% { opacity:0.3; transform:scale(0.85); } 50% { opacity:1; transform:scale(1.1); } }
// //       `}</style>

// //       <div style={{ display: "flex", height: "100vh", fontFamily: "'Inter','Segoe UI',system-ui,sans-serif", color: C.text, overflow: "hidden", background: C.bg }}>

// //         {/* ══════════════════════════════════════════════════════════════════
// //             SIDEBAR
// //         ══════════════════════════════════════════════════════════════════ */}
// //         <div style={{ width: 248, background: C.surface, borderRight: `1px solid ${C.border}`, display: "flex", flexDirection: "column", height: "100vh", flexShrink: 0 }}>
// //           {/* Logo + search */}
// //           <div style={{ padding: "14px 12px 10px", borderBottom: `1px solid ${C.border}` }}>
// //             <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
// //               <Icon d={ICONS.leaf} size={20} stroke={C.accent} />
// //               <span style={{ fontWeight: 700, fontSize: 15, color: C.text }}>Agentic RAG</span>
// //             </div>
// //             <div style={{ display: "flex", alignItems: "center", gap: 6, background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 8, padding: "6px 10px" }}>
// //               <Icon d={ICONS.search} size={14} />
// //               <input value={sideSearch} onChange={e => setSideSearch(e.target.value)} placeholder="Search…"
// //                 style={{ flex: 1, background: "transparent", border: "none", outline: "none", color: C.text, fontSize: 12, fontFamily: "inherit" }} />
// //             </div>
// //           </div>

// //           <div style={{ flex: 1, overflowY: "auto", padding: "8px 0" }}>
// //             {/* New Chat */}
// //             <div style={{ padding: "4px 8px 8px" }}>
// //               <Btn variant="surface" onClick={() => openNewChat(null)} style={{ width: "100%", justifyContent: "center" }}>
// //                 <Icon d={ICONS.plus} size={14} stroke={C.accent} /> New chat
// //               </Btn>
// //             </div>

// //             {/* ── Recent Chats (from /api/sessions, not in any project) ── */}
// //             <div style={{ padding: "8px 14px 4px", fontSize: 11, fontWeight: 700, color: C.textMute, letterSpacing: "0.08em" }}>RECENT CHATS</div>
// //             {filteredApiSessions.length === 0 && (
// //               <div style={{ fontSize: 12, color: C.textMute, padding: "4px 18px" }}>No chats yet</div>
// //             )}
// //             {filteredApiSessions.map(s => (
// //               <div key={s.session_id} style={{ position: "relative" }}>
// //                 <SideItem
// //                   icon={<Icon d={ICONS.chat} size={14} />}
// //                   label={s.title || s.preview || "Untitled"}
// //                   active={activeSession?.sessionId === s.session_id}
// //                   onClick={() => openExistingSession(s.session_id, null)}
// //                 />
// //                 {/* delete button on hover via a wrapper is complex; simplified to always-visible tiny trash */}
// //                 <button onClick={e => { e.stopPropagation(); deleteSession(s.session_id); }}
// //                   title="Delete"
// //                   style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", opacity: 0.4, padding: 2 }}>
// //                   <Icon d={ICONS.trash} size={11} stroke={C.danger} />
// //                 </button>
// //               </div>
// //             ))}

// //             {/* ── Projects ── */}
// //             <div style={{ padding: "12px 14px 4px", fontSize: 11, fontWeight: 700, color: C.textMute, letterSpacing: "0.08em", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
// //               <span>PROJECTS</span>
// //               <button onClick={() => setShowNewProject(true)} style={{ background: "none", border: "none", cursor: "pointer", padding: 2 }}>
// //                 <Icon d={ICONS.plus} size={14} stroke={C.accent} />
// //               </button>
// //             </div>

// //             {filteredProjects.map(proj => {
// //               const isExpanded = expandedProjects.has(proj.id);
// //               const isSelected = activeSession?.projectId === proj.id;
// //               return (
// //                 <div key={proj.id}>
// //                   <div style={{ display: "flex", alignItems: "center", margin: "1px 6px", borderRadius: 8, background: isSelected ? C.accentBg : "transparent" }}>
// //                     <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 8, padding: "7px 8px 7px 12px", color: isSelected ? C.accent : C.textSub, fontSize: 13, fontWeight: isSelected ? 600 : 400, cursor: "pointer", overflow: "hidden" }}
// //                       onClick={() => { setSelectedProject(proj); setExpandedProjects(prev => new Set([...prev, proj.id])); }}>
// //                       <span style={{ fontSize: 15 }}>{proj.emoji}</span>
// //                       <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{proj.name}</span>
// //                     </div>
// //                     <button onClick={e => { e.stopPropagation(); setExpandedProjects(prev => { const s = new Set(prev); s.has(proj.id) ? s.delete(proj.id) : s.add(proj.id); return s; }); }}
// //                       style={{ background: "none", border: "none", cursor: "pointer", padding: "7px 8px", color: C.textMute }}>
// //                       <Icon d={isExpanded ? ICONS.chevD : ICONS.chevR} size={13} stroke={C.textMute} />
// //                     </button>
// //                   </div>
// //                   {isExpanded && (
// //                     <div>
// //                       {(proj.sessions || []).map(sess => {
// //                         const apiS = apiSessions.find(a => a.session_id === sess.sessionId);
// //                         const label = apiS?.title || apiS?.preview || sess.title || "Chat";
// //                         return (
// //                           <SideItem key={sess.sessionId} indent={1}
// //                             icon={<Icon d={ICONS.chat} size={13} />}
// //                             label={label}
// //                             muted
// //                             active={activeSession?.sessionId === sess.sessionId}
// //                             onClick={() => openExistingSession(sess.sessionId, proj.id)}
// //                           />
// //                         );
// //                       })}
// //                       <SideItem indent={1} muted
// //                         icon={<Icon d={ICONS.plus} size={13} stroke={C.textMute} />}
// //                         label="New chat"
// //                         onClick={() => openNewChat(proj.id)}
// //                       />
// //                     </div>
// //                   )}
// //                 </div>
// //               );
// //             })}

// //             {/* ── Knowledge base PDFs ── */}
// //             <div style={{ padding: "12px 14px 4px", fontSize: 11, fontWeight: 700, color: C.textMute, letterSpacing: "0.08em" }}>KNOWLEDGE BASE</div>
// //             {[
// //               { label: "PARC Report 2023-24",  file: "PARC Annual Report 2023-24_compressed.pdf" },
// //               { label: "FAO Crop Guidelines",  file: "i5550e.pdf" },
// //               { label: "Punjab Agri Rules",    file: "PbAgriDeptExtenAdapReseWing_SR_2007_20070612.pdf" },
// //             ].map(({ label, file }) => (
// //               <div key={file} onClick={() => window.open(`/api/pdf/${encodeURIComponent(file)}`, "_blank")}
// //                 style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 12px 6px 18px", cursor: "pointer", color: C.textSub, fontSize: 12 }}>
// //                 <Icon d={ICONS.book} size={13} stroke={C.textMute} />
// //                 <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{label}</span>
// //                 <span style={{ color: C.accentDim, fontSize: 10 }}>↗</span>
// //               </div>
// //             ))}
// //           </div>

// //           {/* User footer */}
// //           <div style={{ padding: "10px 14px", borderTop: `1px solid ${C.border}`, display: "flex", alignItems: "center", gap: 8 }}>
// //             <div style={{ width: 30, height: 30, borderRadius: "50%", background: C.accentBg, border: `1px solid ${C.accent}44`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 700, color: C.accent }}>
// //               {username[0].toUpperCase()}
// //             </div>
// //             <span style={{ flex: 1, fontSize: 12, color: C.textSub, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{username}</span>
// //             {onLogout && (
// //               <button onClick={onLogout} title="Sign out" style={{ background: "none", border: "none", cursor: "pointer" }}>
// //                 <Icon d={ICONS.x} size={14} stroke={C.textMute} />
// //               </button>
// //             )}
// //           </div>
// //         </div>

// //         {/* ══════════════════════════════════════════════════════════════════
// //             MAIN CHAT AREA
// //         ══════════════════════════════════════════════════════════════════ */}
// //         <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
// //           {/* Header */}
// //           <div style={{ padding: "0 20px", height: 52, display: "flex", alignItems: "center", gap: 12, background: C.surface, borderBottom: `1px solid ${C.border}`, flexShrink: 0 }}>
// //             <span style={{ fontSize: 16 }}>🌾</span>
// //             <div style={{ flex: 1 }}>
// //               <span style={{ fontSize: 14, fontWeight: 600, color: C.text }}>
// //                 {activeSession ? activeSession.title : "Agricultural Knowledge Base"}
// //               </span>
// //               {activeSession?.projectId && (
// //                 <span style={{ fontSize: 11, color: C.textMute, marginLeft: 8 }}>
// //                   · {projects.find(p => p.id === activeSession.projectId)?.name}
// //                 </span>
// //               )}
// //             </div>
// //             <StatusBadge chunks={chunkCount} />
// //             <button onClick={() => setShowTrace(t => !t)} title={showTrace ? "Hide trace" : "Show trace"}
// //               style={{ background: "none", border: `1px solid ${C.border}`, borderRadius: 6, padding: "4px 8px", cursor: "pointer", color: C.amber, fontSize: 12, display: "flex", alignItems: "center", gap: 5 }}>
// //               <Icon d={ICONS.trace} size={13} stroke={C.amber} />
// //               Trace
// //             </button>
// //             {activeSession && (
// //               <button onClick={() => exportSession(activeSession.sessionId, "markdown")} title="Export as Markdown"
// //                 style={{ background: "none", border: `1px solid ${C.border}`, borderRadius: 6, padding: "4px 8px", cursor: "pointer", color: C.textSub, fontSize: 12, display: "flex", alignItems: "center", gap: 5 }}>
// //                 <Icon d={ICONS.export} size={13} stroke={C.textSub} />
// //                 Export
// //               </button>
// //             )}
// //           </div>

// //           {/* Chat area */}
// //           <div ref={chatRef} style={{ flex: 1, overflowY: "auto", padding: "20px 24px", display: "flex", flexDirection: "column", gap: 16 }}>
// //             {!activeSession ? (
// //               <Welcome onSend={(p) => { openNewChat(null); setTimeout(() => sendMessage(p), 50); }} />
// //             ) : currentMessages.length === 0 ? (
// //               <Welcome onSend={sendMessage} />
// //             ) : (
// //               currentMessages.map((m, i) => (
// //                 <Message key={i} role={m.role} content={m.content} ts={m.ts} usedRag={m.usedRag}
// //                   onRegenerate={m.role === "assistant" ? () => {
// //                     const prev = currentMessages.slice(0, i).reverse().find(x => x.role === "user");
// //                     if (prev) sendMessage(prev.content);
// //                   } : null}
// //                 />
// //               ))
// //             )}
// //             {loading && <TypingDots />}
// //           </div>

// //           {/* Input */}
// //           <div style={{ padding: "12px 20px 16px", borderTop: `1px solid ${C.border}`, background: C.surface }}>
// //             {!activeSession && (
// //               <div style={{ fontSize: 12, color: C.textMute, textAlign: "center", marginBottom: 8 }}>
// //                 Click <strong style={{ color: C.accent }}>+ New chat</strong> or select a conversation to start.
// //               </div>
// //             )}
// //             <div style={{ display: "flex", gap: 10, alignItems: "flex-end" }}>
// //               <div style={{ flex: 1, background: C.surface2, border: `1px solid ${activeSession ? C.borderHi : C.border}`, borderRadius: 10, padding: "10px 14px" }}>
// //                 <textarea ref={textareaRef} rows={2} value={input}
// //                   onChange={e => setInput(e.target.value)}
// //                   onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
// //                   placeholder={activeSession ? "Ask about crops, diseases, PARC activities… (Enter to send)" : "Select or create a chat first"}
// //                   disabled={!activeSession}
// //                   style={{ width: "100%", background: "transparent", border: "none", outline: "none", color: C.text, fontSize: 14, fontFamily: "inherit", resize: "none", lineHeight: 1.5 }} />
// //               </div>
// //               <button onClick={() => sendMessage()} disabled={loading || !input.trim() || !activeSession}
// //                 style={{ width: 42, height: 42, borderRadius: 10, border: "none", background: C.accent, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", alignSelf: "flex-end", flexShrink: 0, opacity: (loading || !input.trim() || !activeSession) ? 0.4 : 1, transition: "opacity 0.15s" }}>
// //                 <Icon d={ICONS.send} size={16} stroke="#fff" />
// //               </button>
// //             </div>
// //           </div>
// //         </div>

// //         {/* ══════════════════════════════════════════════════════════════════
// //             TRACE PANEL (collapsible)
// //         ══════════════════════════════════════════════════════════════════ */}
// //         {showTrace && (
// //           <div style={{ width: 280, background: C.surface, borderLeft: `1px solid ${C.border}`, display: "flex", flexDirection: "column", overflow: "hidden", flexShrink: 0 }}>
// //             <TracePanel trace={trace} />
// //             {/* Pipeline config at bottom */}
// //             <div style={{ padding: "12px 14px", borderTop: `1px solid ${C.border}` }}>
// //               <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: C.textMute, marginBottom: 8 }}>Pipeline</div>
// //               {[
// //                 ["Vector DB",   status?.vector_db || "ChromaDB"],
// //                 ["Retrieval",   status?.retrieval || "BM25 + Embeddings"],
// //                 ["Fusion",      status?.fusion    || "RRF"],
// //                 ["Chunks",      chunkCount.toLocaleString()],
// //               ].map(([k, v]) => (
// //                 <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "4px 8px", background: C.surface2, borderRadius: 6, marginBottom: 4, fontSize: 12 }}>
// //                   <span style={{ color: C.textSub }}>{k}</span>
// //                   <span style={{ color: C.text }}>{v}</span>
// //                 </div>
// //               ))}
// //               {statusError && (
// //                 <div style={{ marginTop: 8, background: C.dangerBg, border: `1px solid ${C.danger}`, borderRadius: 8, padding: "8px 10px", fontSize: 11.5, color: "#e8938a", lineHeight: 1.5 }}>
// //                   {statusError}
// //                 </div>
// //               )}
// //             </div>
// //           </div>
// //         )}
// //       </div>

// //       {/* ── Modals ─────────────────────────────────────────────────────────── */}

// //       {/* New Project */}
// //       <Modal open={showNewProject} onClose={() => setShowNewProject(false)} title="Create new project">
// //         <div style={{ marginBottom: 14 }}>
// //           <label style={{ fontSize: 12, color: C.textSub, display: "block", marginBottom: 6 }}>Icon</label>
// //           <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
// //             {EMOJIS.map(e => (
// //               <button key={e} onClick={() => setNewProjEmoji(e)}
// //                 style={{ fontSize: 20, padding: "4px 8px", borderRadius: 8, cursor: "pointer", border: `1px solid ${newProjEmoji === e ? C.accent : C.border}`, background: newProjEmoji === e ? C.accentBg : C.surface2, fontFamily: "inherit" }}>
// //                 {e}
// //               </button>
// //             ))}
// //           </div>
// //         </div>
// //         <TextInput label="Project name" value={newProjName} onChange={setNewProjName} placeholder="e.g. Wheat Disease Research" />
// //         <TextInput label="Description (optional)" value={newProjDesc} onChange={setNewProjDesc} placeholder="What is this project about?" multiline />
// //         <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", marginTop: 4 }}>
// //           <Btn onClick={() => setShowNewProject(false)}>Cancel</Btn>
// //           <Btn variant="primary" onClick={createProject} disabled={!newProjName.trim()}>Create project</Btn>
// //         </div>
// //       </Modal>

// //       {/* Rename */}
// //       <Modal open={showRename} onClose={() => { setShowRename(false); setRenameTarget(null); }} title={`Rename ${renameTarget?.type || "item"}`} width={400}>
// //         <TextInput label="New name" value={renameName} onChange={setRenameName} placeholder="Enter new name" />
// //         <div style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
// //           <Btn onClick={() => { setShowRename(false); setRenameTarget(null); }}>Cancel</Btn>
// //           <Btn variant="primary" onClick={commitRename} disabled={!renameName.trim()}>Save</Btn>
// //         </div>
// //       </Modal>

// //       {/* Delete confirm */}
// //       <Modal open={showDeleteConfirm} onClose={() => { setShowDeleteConfirm(false); setDeleteTarget(null); }} title="Confirm deletion" width={380}>
// //         <div style={{ fontSize: 13, color: C.textSub, marginBottom: 20, lineHeight: 1.6 }}>
// //           Delete <strong style={{ color: C.text }}>{deleteTarget?.name}</strong>? This will remove all its chats and data.
// //         </div>
// //         <div style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
// //           <Btn onClick={() => { setShowDeleteConfirm(false); setDeleteTarget(null); }}>Cancel</Btn>
// //           <button onClick={() => { if (deleteTarget?.type === "project") deleteProject(deleteTarget.id); }}
// //             style={{ padding: "7px 14px", borderRadius: 8, background: C.danger, color: "#fff", border: "none", cursor: "pointer", fontWeight: 600, fontSize: 13, fontFamily: "inherit" }}>
// //             Delete
// //           </button>
// //         </div>
// //       </Modal>
// //     </>
// //   );
// // }

// /**
//  * ProjectManager.jsx — Enhanced
//  * ==============================
//  * NEW features (over base version):
//  *  1. ◀▶ Sidebar collapse/expand toggle
//  *  2. 🌐 Tavily web search toggle in header — fires tavily_search MCP tool
//  *     and injects live web results into the LLM context before answering
//  *  3. 📄 PDF export of current chat (top-right, beside chunk badge)
//  *  4. ✏️  Rename for BOTH recent chats AND projects in sidebar
//  *  5. ➕ File-upload button ("+") in every query box — uploads doc and
//  *     answers questions grounded in that uploaded document
//  *  6. MCP tool call display in trace panel (weather, crop_calendar, etc.)
//  *
//  * Props: username, token, onLogout  (same as before — no API changes needed)
//  */

// import { useState, useRef, useEffect, useCallback } from "react";

// // ── Palette ───────────────────────────────────────────────────────────────────
// const C = {
//   bg:        "#0c1108",
//   surface:   "#141c0f",
//   surface2:  "#1c2614",
//   surface3:  "#222e18",
//   border:    "#2a3d1e",
//   borderHi:  "#3d5a2a",
//   accent:    "#7ab648",
//   accentDim: "#4a7a1e",
//   accentBg:  "rgba(122,182,72,0.10)",
//   amber:     "#e8a020",
//   amberDim:  "#7a4e00",
//   amberBg:   "rgba(232,160,32,0.10)",
//   teal:      "#2bbfa0",
//   tealDim:   "#0d5a48",
//   tealBg:    "rgba(43,191,160,0.10)",
//   text:      "#dde8cc",
//   textSub:   "#7a9460",
//   textMute:  "#4a6035",
//   userBub:   "#1a2e10",
//   botBub:    "#0f1a08",
//   danger:    "#c0392b",
//   dangerBg:  "rgba(192,57,43,0.12)",
// };

// // ── Icon ──────────────────────────────────────────────────────────────────────
// const Icon = ({ d, size = 16, stroke = C.textSub, fill = "none" }) => (
//   <svg width={size} height={size} viewBox="0 0 24 24" fill={fill}
//     stroke={stroke} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round"
//     style={{ flexShrink: 0 }}>
//     <path d={d} />
//   </svg>
// );

// const ICONS = {
//   leaf:      "M12 2a4 4 0 0 1 4 4v2h2a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2V6a4 4 0 0 1 4-4z",
//   chat:      "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z",
//   folder:    "M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z",
//   file:      "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H8",
//   plus:      "M12 5v14M5 12h14",
//   trash:     "M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6",
//   edit:      "M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z",
//   upload:    "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12",
//   download:  "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3",
//   globe:     "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zM2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z",
//   book:      "M4 19.5A2.5 2.5 0 0 1 6.5 17H20M4 19.5A2.5 2.5 0 0 0 6.5 22H20V2H6.5A2.5 2.5 0 0 0 4 4.5v15z",
//   chevD:     "M6 9l6 6 6-6",
//   chevR:     "M9 18l6-6-6-6",
//   chevL:     "M15 18l-6-6 6-6",
//   panelOpen: "M3 12h18M3 6h18M3 18h18",
//   panelClose:"M3 6h7M3 12h7M3 18h7M17 6l4 6-4 6",
//   x:         "M18 6L6 18M6 6l12 12",
//   search:    "M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z",
//   send:      "M22 2L11 13M22 2L15 22 11 13 2 9l20-7z",
//   check:     "M20 6L9 17 4 12",
//   copy:      "M20 9H11a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2v-9a2 2 0 0 0-2-2zM5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1",
//   thumbUp:   "M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3",
//   thumbDown: "M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zM17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17",
//   share:     "M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8M16 6l-4-4-4 4M12 2v13",
//   trace:     "M3 3h18v18H3zM9 9h6M9 13h6M9 17h4",
//   bot:       "M12 2a4 4 0 0 1 4 4v2h2a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2V6a4 4 0 0 1 4-4zM9 10H7v2h2v-2zm8 0h-2v2h2v-2zm-5 4h-2v2h2v-2z",
//   user:      "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
//   snapshot:  "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H8",
//   reset:     "M1 4v6h6M23 20v-6h-6M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15",
//   sources:   "M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2zM22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z",
//   regen:     "M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15",
//   export:    "M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8M16 6l-4-4-4 4M12 2v13",
//   pdf:       "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M11 13H8M16 13h-2M11 17H8M16 17h-2",
//   tool:      "M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z",
//   attach:    "M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48",
//   weather:   "M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9z",
// };

// // ── Utilities ─────────────────────────────────────────────────────────────────
// const now = () => new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

// // ── Citation parser ───────────────────────────────────────────────────────────
// function parseSources(content) {
//   const sourcesMatch = content.match(/SOURCES:\s*\n([\s\S]+)$/i);
//   const mainText = sourcesMatch
//     ? content.slice(0, content.indexOf(sourcesMatch[0])).trim()
//     : content;
//   const sources = [];
//   if (sourcesMatch) {
//     const lines = sourcesMatch[1].trim().split("\n").filter(Boolean);
//     lines.forEach(line => {
//       const docMatch = line.match(/\[(\d+)\]\s*(.+?)\s*\|\s*[Pp]age\s*(\d+)/);
//       if (docMatch) {
//         sources.push({ num: parseInt(docMatch[1]), filename: docMatch[2].trim(), page: parseInt(docMatch[3]), type: "document" });
//         return;
//       }
//       const webMatch = line.match(/\[Web\s*(\d+)\]\s*(.+?)\s*—\s*(https?:\/\/\S+)/);
//       if (webMatch) {
//         sources.push({ num: parseInt(webMatch[1]), title: webMatch[2].trim(), url: webMatch[3].trim(), type: "web" });
//       }
//     });
//   }
//   return { mainText, sources };
// }

// function renderTextWithCitations(text, sources, onCiteClick) {
//   const parts = text.split(/(\[(?:Web\s*)?\d+\])/g);
//   return parts.map((part, i) => {
//     const match = part.match(/^\[(?:Web\s*)?(\d+)\]$/);
//     if (match) {
//       const num = parseInt(match[1]);
//       const isWeb = part.toLowerCase().includes("web");
//       const src = sources.find(s => s.num === num && (isWeb ? s.type === "web" : s.type === "document"))
//                || sources.find(s => s.num === num);
//       return (
//         <sup key={i} onClick={() => src && onCiteClick(src)}
//           title={src ? (src.type === "document" ? `${src.filename} — Page ${src.page}` : src.title) : ""}
//           style={{
//             cursor: src ? "pointer" : "default",
//             color: src ? (src.type === "web" ? C.amber : C.accent) : C.textMute,
//             fontWeight: 700, fontSize: "0.72em", marginLeft: 1,
//             padding: "1px 4px", borderRadius: 3,
//             background: src ? (src.type === "web" ? "#2a1e00" : "#16301a") : "transparent",
//             border: src ? `1px solid ${src.type === "web" ? C.amberDim : C.accentDim}` : "none",
//             userSelect: "none",
//           }}>
//           {part}
//         </sup>
//       );
//     }
//     return (
//       <span key={i}>
//         {part.split("\n").map((line, j, arr) => (
//           <span key={j}>{line}{j < arr.length - 1 && <br />}</span>
//         ))}
//       </span>
//     );
//   });
// }

// function SourcesList({ sources }) {
//   if (!sources.length) return null;
//   const open = (src) => {
//     if (src.type === "document") window.open(`/api/pdf/${encodeURIComponent(src.filename)}#page=${src.page}`, "_blank");
//     else window.open(src.url, "_blank");
//   };
//   return (
//     <div style={{ marginTop: 12, paddingTop: 10, borderTop: `1px solid ${C.border}` }}>
//       <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: C.textMute, marginBottom: 6 }}>
//         References
//       </div>
//       {sources.map((src, i) => (
//         <div key={i} onClick={() => open(src)}
//           style={{ display: "flex", alignItems: "flex-start", gap: 7, marginBottom: 5, cursor: "pointer", padding: "5px 7px", borderRadius: 7, transition: "background 0.15s" }}
//           onMouseEnter={e => e.currentTarget.style.background = C.surface2}
//           onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
//           <span style={{ minWidth: 20, height: 20, borderRadius: 4, flexShrink: 0, background: src.type === "document" ? C.accentDim : C.amberDim, border: `1px solid ${src.type === "document" ? C.accent : C.amber}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 9, fontWeight: 700, color: src.type === "document" ? C.accent : C.amber }}>
//             {src.num}
//           </span>
//           <div style={{ fontSize: 11.5, color: C.textSub, lineHeight: 1.5 }}>
//             {src.type === "document" ? (
//               <><span style={{ color: C.text, fontWeight: 500 }}>{src.filename}</span><span style={{ color: C.textMute }}> — Page {src.page}</span><span style={{ color: C.accentDim, fontSize: 10, marginLeft: 5 }}>↗ open PDF</span></>
//             ) : (
//               <><span style={{ color: C.text, fontWeight: 500 }}>{src.title}</span><span style={{ color: C.amberDim, fontSize: 10, marginLeft: 5 }}>↗ web</span></>
//             )}
//           </div>
//         </div>
//       ))}
//     </div>
//   );
// }

// // ── Message bubble ────────────────────────────────────────────────────────────
// function Message({ role, content, ts, usedRag, uploadedFile, webSearched, onRegenerate }) {
//   const [copied, setCopied] = useState(false);
//   const [liked, setLiked]   = useState(null);
//   const [showSrc, setShowSrc] = useState(true);
//   const isUser = role === "user";

//   const ActionBtn = ({ icon, title, onClick, active, activeColor }) => (
//     <button onClick={onClick} title={title}
//       style={{ background: "none", border: "none", cursor: "pointer", padding: "4px 5px", borderRadius: 6, display: "flex", alignItems: "center", opacity: 0.55, transition: "opacity 0.15s" }}
//       onMouseEnter={e => { e.currentTarget.style.opacity = "1"; e.currentTarget.style.background = C.surface2; }}
//       onMouseLeave={e => { e.currentTarget.style.opacity = "0.55"; e.currentTarget.style.background = "none"; }}>
//       <Icon d={icon} size={14} stroke={active ? (activeColor || C.accent) : C.textSub} />
//     </button>
//   );

//   const ragBadge = !isUser && usedRag !== null && usedRag !== undefined && (
//     <span style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 9.5, fontWeight: 600, letterSpacing: "0.03em", padding: "2px 7px", borderRadius: 20, background: usedRag ? "#16301a" : "#2a2210", border: `1px solid ${usedRag ? C.accentDim : C.amberDim}`, color: usedRag ? C.accent : C.amber, marginLeft: 6 }}>
//       {usedRag ? "RAG" : "🌐 Web"}
//     </span>
//   );

//   const webBadge = !isUser && webSearched && (
//     <span style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 9.5, fontWeight: 600, padding: "2px 7px", borderRadius: 20, background: C.tealBg, border: `1px solid ${C.tealDim}`, color: C.teal, marginLeft: 6 }}>
//       🌐 Tavily
//     </span>
//   );

//   return (
//     <div style={{ display: "flex", flexDirection: "column", alignItems: isUser ? "flex-end" : "flex-start", gap: 4 }}>
//       <div style={{ display: "flex", alignItems: "center", gap: 6, flexDirection: isUser ? "row-reverse" : "row" }}>
//         <div style={{ width: 26, height: 26, borderRadius: "50%", background: isUser ? C.accentDim : "#1a2610", border: `1px solid ${isUser ? C.accent : C.border}`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
//           <Icon d={isUser ? ICONS.user : ICONS.bot} size={13} stroke={isUser ? C.accent : C.textSub} />
//         </div>
//         <span style={{ fontSize: 11, color: C.textMute, display: "flex", alignItems: "center", flexWrap: "wrap", gap: 2 }}>
//           {isUser ? "You" : "RAG Assistant"} · {ts}{ragBadge}{webBadge}
//         </span>
//       </div>

//       {/* File attachment badge on user message */}
//       {isUser && uploadedFile && (
//         <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "5px 10px", background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 8, fontSize: 11, color: C.textSub, maxWidth: "78%" }}>
//           <Icon d={ICONS.attach} size={12} stroke={C.accent} />
//           <span style={{ color: C.accent, fontWeight: 500 }}>{uploadedFile}</span>
//           <span style={{ color: C.textMute }}>· attached</span>
//         </div>
//       )}

//       <div style={{ maxWidth: "78%", background: isUser ? C.userBub : C.botBub, border: `1px solid ${isUser ? C.accentDim : C.border}`, borderRadius: isUser ? "14px 4px 14px 14px" : "4px 14px 14px 14px", padding: "10px 14px", lineHeight: 1.65, fontSize: 14, color: C.text }}>
//         {isUser ? (
//           <span style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>{content}</span>
//         ) : (() => {
//           const { mainText, sources } = parseSources(content);
//           const onCiteClick = src => {
//             if (src.type === "document") window.open(`/api/pdf/${encodeURIComponent(src.filename)}#page=${src.page}`, "_blank");
//             else window.open(src.url, "_blank");
//           };
//           return (
//             <>
//               <div style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
//                 {renderTextWithCitations(mainText, sources, onCiteClick)}
//               </div>
//               {showSrc && <SourcesList sources={sources} />}
//             </>
//           );
//         })()}
//       </div>

//       {!isUser && (
//         <div style={{ display: "flex", alignItems: "center", gap: 1, paddingLeft: 4, marginTop: -2 }}>
//           <ActionBtn icon={copied ? ICONS.check : ICONS.copy} title="Copy" onClick={() => { navigator.clipboard.writeText(content); setCopied(true); setTimeout(() => setCopied(false), 1500); }} active={copied} activeColor={C.accent} />
//           <ActionBtn icon={ICONS.thumbUp} title="Good response" onClick={() => setLiked(l => l === "up" ? null : "up")} active={liked === "up"} activeColor={C.accent} />
//           <ActionBtn icon={ICONS.thumbDown} title="Bad response" onClick={() => setLiked(l => l === "down" ? null : "down")} active={liked === "down"} activeColor={C.danger} />
//           <ActionBtn icon={ICONS.share} title="Copy to clipboard" onClick={() => navigator.clipboard.writeText(content)} />
//           {onRegenerate && <ActionBtn icon={ICONS.regen} title="Regenerate" onClick={onRegenerate} />}
//           <div style={{ width: 1, height: 14, background: C.border, margin: "0 3px" }} />
//           <ActionBtn icon={ICONS.sources} title={showSrc ? "Hide sources" : "Show sources"} onClick={() => setShowSrc(s => !s)} active={showSrc} activeColor={C.accent} />
//         </div>
//       )}
//     </div>
//   );
// }

// // ── Typing dots ───────────────────────────────────────────────────────────────
// function TypingDots() {
//   return (
//     <div style={{ display: "flex", alignItems: "flex-start", gap: 6 }}>
//       <div style={{ width: 26, height: 26, borderRadius: "50%", background: "#1a2610", border: `1px solid ${C.border}`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
//         <Icon d={ICONS.bot} size={13} stroke={C.textSub} />
//       </div>
//       <div style={{ background: C.botBub, border: `1px solid ${C.border}`, borderRadius: "4px 14px 14px 14px", padding: "12px 16px", display: "flex", gap: 5, alignItems: "center" }}>
//         {[0, 0.18, 0.36].map((delay, i) => (
//           <div key={i} style={{ width: 7, height: 7, borderRadius: "50%", background: C.accentDim, animation: "pulse 1.2s ease-in-out infinite", animationDelay: `${delay}s` }} />
//         ))}
//       </div>
//     </div>
//   );
// }

// // ── Trace panel ───────────────────────────────────────────────────────────────
// function TracePanel({ trace, webSearchResults, mcpCalls, status, statusError }) {
//   const [tab, setTab] = useState("trace");
//   return (
//     <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
//       {/* Tabs */}
//       <div style={{ display: "flex", borderBottom: `1px solid ${C.border}`, flexShrink: 0 }}>
//         {[["trace","Trace",ICONS.trace,C.amber], ["web","Web Search",ICONS.globe,C.teal], ["mcp","MCP Tools",ICONS.tool,C.accent]].map(([id,label,ic,col]) => (
//           <button key={id} onClick={() => setTab(id)} style={{ flex:1, padding:"10px 4px", background:"none", border:"none", borderBottom:`2px solid ${tab===id?col:"transparent"}`, cursor:"pointer", fontSize:11, fontWeight:600, color:tab===id?col:C.textMute, display:"flex", alignItems:"center", justifyContent:"center", gap:4, transition:"all 0.15s" }}>
//             <Icon d={ic} size={12} stroke={tab===id?col:C.textMute} />{label}
//           </button>
//         ))}
//       </div>

//       <div style={{ flex: 1, overflowY: "auto", padding: "12px 14px" }}>
//         {tab === "trace" && (
//           !trace ? (
//             <div style={{ color: C.textMute, fontSize: 12, textAlign: "center", marginTop: 40, lineHeight: 1.7 }}>
//               Pipeline step timings<br />appear here after each query
//             </div>
//           ) : (
//             <pre style={{ fontFamily: "'JetBrains Mono','Fira Code',monospace", fontSize: 11, color: C.textSub, lineHeight: 1.75, whiteSpace: "pre-wrap", wordBreak: "break-word", margin: 0 }}>
//               {trace}
//             </pre>
//           )
//         )}

//         {tab === "web" && (
//           webSearchResults?.length > 0 ? (
//             <div>
//               <div style={{ fontSize: 11, color: C.teal, fontWeight: 600, marginBottom: 10 }}>
//                 {webSearchResults.length} web results retrieved via Tavily
//               </div>
//               {webSearchResults.map((r, i) => (
//                 <div key={i} style={{ marginBottom: 10, padding: "8px 10px", background: C.surface2, borderRadius: 8, border: `1px solid ${C.border}` }}>
//                   <div style={{ fontSize: 11.5, fontWeight: 600, color: C.text, marginBottom: 3 }}>{r.title}</div>
//                   <div style={{ fontSize: 10.5, color: C.textSub, marginBottom: 4, lineHeight: 1.5 }}>{r.content?.slice(0,200)}…</div>
//                   <a href={r.url} target="_blank" rel="noreferrer" style={{ fontSize: 10, color: C.amber }}>{r.url?.slice(0,60)}</a>
//                 </div>
//               ))}
//             </div>
//           ) : (
//             <div style={{ color: C.textMute, fontSize: 12, textAlign: "center", marginTop: 40, lineHeight: 1.7 }}>
//               Enable 🌐 Web Search in the header,<br />then ask a question to see live results.
//             </div>
//           )
//         )}

//         {tab === "mcp" && (
//           mcpCalls?.length > 0 ? (
//             <div>
//               <div style={{ fontSize: 11, color: C.accent, fontWeight: 600, marginBottom: 10 }}>
//                 {mcpCalls.length} MCP tool call{mcpCalls.length !== 1 ? "s" : ""} this session
//               </div>
//               {mcpCalls.map((call, i) => (
//                 <div key={i} style={{ marginBottom: 10, padding: "8px 10px", background: C.surface2, borderRadius: 8, border: `1px solid ${C.border}` }}>
//                   <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
//                     <span style={{ fontSize: 11.5, fontWeight: 700, color: C.accent }}>⚡ {call.tool}</span>
//                     <span style={{ fontSize: 10, color: call.ok ? C.accent : C.danger }}>{call.ok ? "✓ ok" : "✗ error"}</span>
//                   </div>
//                   <pre style={{ fontSize: 10, color: C.textSub, margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
//                     {JSON.stringify(call.params, null, 1).slice(0,200)}
//                   </pre>
//                   {call.preview && <div style={{ fontSize: 10.5, color: C.text, marginTop: 4 }}>{call.preview}</div>}
//                 </div>
//               ))}
//             </div>
//           ) : (
//             <div style={{ color: C.textMute, fontSize: 12, textAlign: "center", marginTop: 40, lineHeight: 1.7 }}>
//               MCP tool calls (weather, crop<br />calendar, unit converter…)<br />appear here after each query.
//             </div>
//           )
//         )}
//       </div>

//       {/* Pipeline config at bottom */}
//       <div style={{ padding: "12px 14px", borderTop: `1px solid ${C.border}` }}>
//         <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: C.textMute, marginBottom: 8 }}>Pipeline</div>
//         {[
//           ["Vector DB",  status?.vector_db || "ChromaDB"],
//           ["Retrieval",  status?.retrieval || "BM25 + Embeddings"],
//           ["Fusion",     status?.fusion    || "RRF"],
//           ["Chunks",     (status?.chunk_count || 0).toLocaleString()],
//         ].map(([k, v]) => (
//           <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "4px 8px", background: C.surface2, borderRadius: 6, marginBottom: 4, fontSize: 12 }}>
//             <span style={{ color: C.textSub }}>{k}</span>
//             <span style={{ color: C.text }}>{v}</span>
//           </div>
//         ))}
//         {statusError && (
//           <div style={{ marginTop: 8, background: C.dangerBg, border: `1px solid ${C.danger}`, borderRadius: 8, padding: "8px 10px", fontSize: 11.5, color: "#e8938a", lineHeight: 1.5 }}>
//             {statusError}
//           </div>
//         )}
//       </div>
//     </div>
//   );
// }

// // ── Welcome screen ────────────────────────────────────────────────────────────
// function Welcome({ onSend }) {
//   const prompts = [
//     "What wheat diseases are monitored in Punjab?",
//     "Is today's weather good for wheat sowing in Lahore?",
//     "Convert 50 acres to hectares",
//     "Which FAO guidelines cover Ug99 rust?",
//     "Summarise PARC's 2023-24 research highlights",
//     "What is the role of the Agriculture Extension Wing?",
//   ];
//   return (
//     <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: 32, gap: 28 }}>
//       <div style={{ textAlign: "center" }}>
//         <div style={{ fontSize: 40, marginBottom: 12 }}>🌾</div>
//         <div style={{ fontSize: 22, fontWeight: 700, color: C.text, letterSpacing: "-0.02em", marginBottom: 6 }}>
//           Agricultural RAG Assistant
//         </div>
//         <div style={{ fontSize: 13, color: C.textSub, maxWidth: 440, lineHeight: 1.6 }}>
//           Grounded in PARC Annual Report, FAO Crop Guidelines, and Punjab Agri Rules.
//           MCP tools: weather, crop calendar, unit converter, Tavily web search.
//         </div>
//       </div>
//       <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, width: "100%", maxWidth: 560 }}>
//         {prompts.map((p, i) => (
//           <button key={i} onClick={() => onSend(p)}
//             style={{ background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 10, padding: "10px 14px", color: C.textSub, fontSize: 12, textAlign: "left", cursor: "pointer", lineHeight: 1.5, transition: "border-color 0.15s, color 0.15s", fontFamily: "inherit" }}
//             onMouseEnter={e => { e.currentTarget.style.borderColor = C.accent; e.currentTarget.style.color = C.text; }}
//             onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.color = C.textSub; }}>
//             {p}
//           </button>
//         ))}
//       </div>
//     </div>
//   );
// }

// // ── Sidebar item ──────────────────────────────────────────────────────────────
// const SideItem = ({ icon, label, active, onClick, indent = 0, muted = false }) => (
//   <div onClick={onClick}
//     style={{ display: "flex", alignItems: "center", gap: 8, padding: `7px 12px 7px ${12 + indent * 16}px`, borderRadius: 8, cursor: "pointer", margin: "1px 6px", background: active ? C.accentBg : "transparent", color: active ? C.accent : muted ? C.textMute : C.textSub, fontSize: 13, fontWeight: active ? 600 : 400, transition: "all 0.12s" }}>
//     {icon}
//     <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{label}</span>
//   </div>
// );

// // ── Modal ─────────────────────────────────────────────────────────────────────
// const Modal = ({ open, onClose, title, children, width = 480 }) => {
//   if (!open) return null;
//   return (
//     <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center" }}
//       onClick={onClose}>
//       <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 14, padding: "24px 28px", width, maxWidth: "90vw", maxHeight: "80vh", overflowY: "auto" }}
//         onClick={e => e.stopPropagation()}>
//         <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
//           <span style={{ fontSize: 16, fontWeight: 700, color: C.text }}>{title}</span>
//           <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer" }}>
//             <Icon d={ICONS.x} stroke={C.textSub} size={18} />
//           </button>
//         </div>
//         {children}
//       </div>
//     </div>
//   );
// };

// const TextInput = ({ label, value, onChange, placeholder, multiline = false, autoFocus = false }) => (
//   <div style={{ marginBottom: 14 }}>
//     {label && <label style={{ fontSize: 12, color: C.textSub, display: "block", marginBottom: 6 }}>{label}</label>}
//     {multiline
//       ? <textarea value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
//           style={{ width: "100%", background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 8, padding: "10px 12px", color: C.text, fontSize: 13, fontFamily: "inherit", outline: "none", resize: "vertical", minHeight: 80, boxSizing: "border-box" }} />
//       : <input value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder} autoFocus={autoFocus}
//           style={{ width: "100%", background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 8, padding: "10px 12px", color: C.text, fontSize: 13, fontFamily: "inherit", outline: "none", boxSizing: "border-box" }} />
//     }
//   </div>
// );

// const Btn = ({ children, onClick, variant = "ghost", danger = false, style: sx = {}, disabled = false }) => {
//   const base = { display: "inline-flex", alignItems: "center", gap: 6, padding: "7px 12px", borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: disabled ? "not-allowed" : "pointer", border: "none", transition: "all 0.15s", opacity: disabled ? 0.5 : 1, fontFamily: "inherit" };
//   const variants = {
//     primary: { background: C.accent, color: C.bg },
//     ghost:   { background: "transparent", color: danger ? C.danger : C.textSub, border: `1px solid ${danger ? C.danger + "55" : C.border}` },
//     surface: { background: C.surface2, color: C.text, border: `1px solid ${C.border}` },
//   };
//   return <button style={{ ...base, ...variants[variant], ...sx }} onClick={onClick} disabled={disabled}>{children}</button>;
// };

// function StatusBadge({ chunks }) {
//   const ok = chunks > 0;
//   return (
//     <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "4px 10px", borderRadius: 20, background: ok ? "#1a3310" : "#3a1010", border: `1px solid ${ok ? C.accentDim : C.danger}`, fontSize: 12, color: ok ? C.accent : "#e74c3c", whiteSpace: "nowrap" }}>
//       <div style={{ width: 7, height: 7, borderRadius: "50%", background: ok ? C.accent : C.danger, boxShadow: ok ? `0 0 6px ${C.accent}` : "none" }} />
//       {ok ? `${chunks.toLocaleString()} chunks` : "Empty"}
//     </div>
//   );
// }

// // ── PDF chat export ───────────────────────────────────────────────────────────
// function exportChatAsPDF(messages, sessionTitle) {
//   if (!messages || messages.length === 0) {
//     alert("No messages to export yet.");
//     return;
//   }
//   const escHtml = s => s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
//   const date = new Date().toLocaleString();
//   const rows = messages.map(m => {
//     const isUser = m.role === "user";
//     const label = isUser ? "You" : "RAG Assistant";
//     const align = isUser ? "right" : "left";
//     const mlAuto = isUser ? "auto" : "0";
//     const bg = isUser ? "#1a2e10" : "#0f1a08";
//     const borderColor = isUser ? "#4a7a1e" : "#2a3d1e";
//     return `
//       <div style="margin-bottom:18px;text-align:${align}">
//         <div style="font-size:11px;color:#7a9460;margin-bottom:4px">${label} · ${m.ts || ""}</div>
//         <div style="display:inline-block;max-width:78%;background:${bg};border:1px solid ${borderColor};border-radius:12px;padding:10px 14px;font-size:13px;line-height:1.7;color:#dde8cc;white-space:pre-wrap;word-break:break-word;margin-left:${mlAuto};text-align:left">${escHtml(m.content)}</div>
//       </div>`;
//   }).join("");

//   const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"/><title>${escHtml(sessionTitle || "RAG Chat")}</title>
//   <style>@page{size:A4;margin:20mm 18mm}body{background:#0c1108;color:#dde8cc;font-family:'Segoe UI',sans-serif;font-size:13px;padding:0}
//   .cover{border-bottom:1px solid #2a3d1e;padding-bottom:16px;margin-bottom:24px}.cover h1{font-size:20px;font-weight:700;color:#dde8cc;margin-bottom:6px}
//   .cover .meta{font-size:11px;color:#7a9460}@media print{body{-webkit-print-color-adjust:exact;print-color-adjust:exact}}</style>
//   </head><body>
//   <div class="cover"><h1>🌾 ${escHtml(sessionTitle || "RAG Conversation")}</h1>
//   <div class="meta">Exported ${date} · ${messages.length} messages</div></div>
//   ${rows}</body></html>`;

//   const iframe = document.createElement("iframe");
//   iframe.style.cssText = "position:fixed;top:-9999px;left:-9999px;width:0;height:0;opacity:0;";
//   document.body.appendChild(iframe);
//   iframe.contentDocument.open();
//   iframe.contentDocument.write(html);
//   iframe.contentDocument.close();
//   setTimeout(() => {
//     iframe.contentWindow.print();
//     setTimeout(() => document.body.removeChild(iframe), 3000);
//   }, 500);
// }

// // ═══════════════════════════════════════════════════════════════════════════════
// //  MAIN COMPONENT
// // ═══════════════════════════════════════════════════════════════════════════════
// const EMOJIS = ["🌱", "🌾", "🪴", "🌽", "🍃", "🌿", "🌻", "🌴", "🫘", "🍀"];

// export default function ProjectManager({ username = "user", token, onLogout }) {
//   // ── Projects / chats ──────────────────────────────────────────────────────
//   const [projects, setProjects]               = useState([]);
//   const [expandedProjects, setExpandedProjects] = useState(new Set());
//   const [selectedProject, setSelectedProject] = useState(null);
//   const [activeSession, setActiveSession]     = useState(null);
//   const [msgCache, setMsgCache]               = useState({});
//   const [loading, setLoading]                 = useState(false);
//   const [trace, setTrace]                     = useState(null);
//   const [input, setInput]                     = useState("");

//   // ── New: sidebar collapsed ────────────────────────────────────────────────
//   const [sidebarOpen, setSidebarOpen]         = useState(true);

//   // ── New: web search (Tavily) ──────────────────────────────────────────────
//   const [webSearch, setWebSearch]             = useState(false);
//   const [webSearchResults, setWebSearchResults] = useState([]);

//   // ── New: MCP call log ─────────────────────────────────────────────────────
//   const [mcpCalls, setMcpCalls]               = useState([]);

//   // ── New: file upload state ────────────────────────────────────────────────
//   const [pendingFile, setPendingFile]         = useState(null); // { name, fileId } after upload
//   const [uploadingFile, setUploadingFile]     = useState(false);
//   const fileInputRef                          = useRef(null);

//   // ── Backend ───────────────────────────────────────────────────────────────
//   const [apiSessions, setApiSessions]         = useState([]);
//   const [status, setStatus]                   = useState(null);
//   const [chunkCount, setChunkCount]           = useState(0);
//   const [statusError, setStatusError]         = useState(null);
//   const [sideSearch, setSideSearch]           = useState("");
//   const [showTrace, setShowTrace]             = useState(true);

//   // ── Modals ────────────────────────────────────────────────────────────────
//   const [showNewProject, setShowNewProject]   = useState(false);
//   const [newProjName, setNewProjName]         = useState("");
//   const [newProjDesc, setNewProjDesc]         = useState("");
//   const [newProjEmoji, setNewProjEmoji]       = useState("🌱");
//   const [showRename, setShowRename]           = useState(false);
//   const [renameTarget, setRenameTarget]       = useState(null);
//   const [renameName, setRenameName]           = useState("");
//   const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
//   const [deleteTarget, setDeleteTarget]       = useState(null);

//   const chatRef     = useRef(null);
//   const textareaRef = useRef(null);

//   const authHeaders = () => token
//     ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` }
//     : { "Content-Type": "application/json" };

//   // ── Scroll ────────────────────────────────────────────────────────────────
//   useEffect(() => {
//     if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
//   }, [msgCache, activeSession, loading]);

//   // ── Poll /api/status ──────────────────────────────────────────────────────
//   useEffect(() => {
//     const fetch_ = () => {
//       fetch("/api/status").then(r => r.json()).then(d => {
//         setStatus(d); setChunkCount(d.chunk_count || 0);
//         setStatusError(d.vector_store_error || d.pipeline_error || null);
//       }).catch(err => { setStatusError(`Cannot reach API: ${err.message}`); setChunkCount(0); });
//     };
//     fetch_(); const id = setInterval(fetch_, 8000); return () => clearInterval(id);
//   }, []);

//   // ── Load sessions ─────────────────────────────────────────────────────────
//   const fetchApiSessions = useCallback(() => {
//     fetch("/api/sessions", { headers: authHeaders() })
//       .then(r => r.json())
//       .then(d => setApiSessions(d.sessions || []))
//       .catch(() => {});
//   }, [token]);

//   useEffect(() => { fetchApiSessions(); }, [fetchApiSessions]);

//   // ── Load projects from localStorage ───────────────────────────────────────
//   useEffect(() => {
//     try {
//       const saved = localStorage.getItem(`rag_projects_${username}`);
//       if (saved) setProjects(JSON.parse(saved));
//     } catch (_) {}
//   }, [username]);

//   const saveProjects = (ps) => {
//     setProjects(ps);
//     try { localStorage.setItem(`rag_projects_${username}`, JSON.stringify(ps)); } catch (_) {}
//   };

//   // ── Open session ──────────────────────────────────────────────────────────
//   const openNewChat = (projectId = null) => {
//     const sessionId = crypto.randomUUID();
//     const proj = projectId ? projects.find(p => p.id === projectId) : null;
//     const session = { sessionId, projectId, title: proj ? `${proj.emoji} New chat` : "New chat" };
//     setActiveSession(session); setTrace(null); setInput("");
//     setPendingFile(null); setWebSearchResults([]); setMcpCalls([]);
//     if (projectId) {
//       const updated = projects.map(p => {
//         if (p.id !== projectId) return p;
//         return { ...p, sessions: [...(p.sessions || []), { sessionId, title: "New chat", date: new Date().toISOString().slice(0, 10) }] };
//       });
//       saveProjects(updated);
//     }
//   };

//   const openExistingSession = (sessionId, projectId = null) => {
//     const proj = projectId ? projects.find(p => p.id === projectId) : null;
//     const apiSess = apiSessions.find(s => s.session_id === sessionId);
//     const title = apiSess?.title || apiSess?.preview || "Chat";
//     setActiveSession({ sessionId, projectId, title: proj ? `${proj.emoji} ${title}` : title });
//     setTrace(null); setInput(""); setPendingFile(null); setWebSearchResults([]); setMcpCalls([]);
//     if (!msgCache[sessionId]) {
//       fetch(`/api/sessions/${sessionId}`, { headers: authHeaders() })
//         .then(r => r.json())
//         .then(d => {
//           const msgs = (d.messages || []).map(m => ({ role: m.role, content: m.content, ts: m.ts || now(), usedRag: m.used_rag }));
//           setMsgCache(prev => ({ ...prev, [sessionId]: msgs }));
//         }).catch(() => {});
//     }
//   };

//   // ── FILE UPLOAD ("+") ─────────────────────────────────────────────────────
//   const handleFileSelect = async (e) => {
//     const file = e.target.files?.[0];
//     if (!file || !activeSession) return;
//     e.target.value = "";

//     setUploadingFile(true);
//     try {
//       const fd = new FormData();
//       fd.append("file", file);
//       const r = await fetch("/api/upload", {
//         method: "POST",
//         headers: token ? { Authorization: `Bearer ${token}` } : {},
//         body: fd,
//       });
//       if (!r.ok) throw new Error(`Upload failed (${r.status})`);
//       const data = await r.json();
//       setPendingFile({ name: file.name, fileId: data.file_id });
//     } catch (err) {
//       alert(`File upload failed: ${err.message}\n\nMake sure the API server is running and /api/upload endpoint exists.`);
//     } finally {
//       setUploadingFile(false);
//     }
//   };

//   // ── SEND MESSAGE ──────────────────────────────────────────────────────────
//   const sendMessage = async (text) => {
//     const q = (text || input).trim();
//     if (!q || loading || !activeSession) return;
//     setInput("");

//     const attachedFile = pendingFile;
//     setPendingFile(null);

//     const userMsg = {
//       role: "user", content: q, ts: now(),
//       uploadedFile: attachedFile?.name || null,
//     };
//     setMsgCache(prev => ({
//       ...prev,
//       [activeSession.sessionId]: [...(prev[activeSession.sessionId] || []), userMsg],
//     }));
//     setLoading(true);
//     setTrace(null);
//     setWebSearchResults([]);

//     try {
//       // ── Step 1: Tavily web search (if enabled) ────────────────────────────
//       let webCtx = "";
//       let webResults = [];
//       if (webSearch) {
//         try {
//           const wr = await fetch("/api/mcp/run", {
//             method: "POST",
//             headers: authHeaders(),
//             body: JSON.stringify({ query: q, session_id: activeSession.sessionId }),
//           });
//           if (wr.ok) {
//             const wd = await wr.json();
//             // Try tavily_search tool result
//             if (wd.results?.tavily_search?.results?.length) {
//               webResults = wd.results.tavily_search.results;
//               setWebSearchResults(webResults);
//               webCtx = webResults.slice(0, 4).map((r, i) => `[Web ${i+1}] ${r.title}\n${r.content}`).join("\n\n");
//               // Log MCP call
//               setMcpCalls(prev => [...prev, {
//                 tool: "tavily_search", ok: true,
//                 params: { query: q },
//                 preview: `${webResults.length} results from Tavily`,
//               }]);
//             }
//             // Also capture any other MCP tool calls (weather, calendar, etc.)
//             if (wd.mcp_calls) {
//               wd.mcp_calls.forEach(c => setMcpCalls(prev => [...prev, c]));
//             }
//           }
//         } catch (e) {
//           console.warn("[Web search] MCP run failed:", e.message);
//         }
//       }

//       // ── Step 2: Build enriched query with web context ─────────────────────
//       let enrichedQuery = q;
//       if (attachedFile?.fileId) {
//         enrichedQuery = `[Referring to uploaded file: ${attachedFile.name} (id:${attachedFile.fileId})]\n${q}`;
//       }
//       if (webCtx) {
//         enrichedQuery = `${enrichedQuery}\n\nLIVE WEB SEARCH RESULTS (use these for current information):\n${webCtx}`;
//       }

//       // ── Step 3: RAG chat ───────────────────────────────────────────────────
//       const res = await fetch("/api/chat", {
//         method: "POST",
//         headers: authHeaders(),
//         body: JSON.stringify({
//           session_id: activeSession.sessionId,
//           query: enrichedQuery,
//           ...(attachedFile?.fileId ? { file_id: attachedFile.fileId } : {}),
//         }),
//       });
//       const data = await res.json();

//       // Capture any MCP calls returned from the pipeline
//       if (data.mcp_calls) {
//         data.mcp_calls.forEach(c => setMcpCalls(prev => [...prev, c]));
//       }

//       const botMsg = {
//         role: "assistant",
//         content: data.response || "No response received.",
//         ts: now(),
//         usedRag: data.used_rag,
//         webSearched: webResults.length > 0,
//       };
//       setMsgCache(prev => ({
//         ...prev,
//         [activeSession.sessionId]: [...(prev[activeSession.sessionId] || []), botMsg],
//       }));
//       if (data.trace) setTrace(data.trace);

//       // Auto-title
//       const currentMsgs = msgCache[activeSession.sessionId] || [];
//       if (currentMsgs.filter(m => m.role === "user").length === 0) {
//         const autoTitle = q.slice(0, 40) + (q.length > 40 ? "…" : "");
//         setActiveSession(prev => ({ ...prev, title: autoTitle }));
//         if (activeSession.projectId) {
//           const updated = projects.map(p => {
//             if (p.id !== activeSession.projectId) return p;
//             return { ...p, sessions: (p.sessions || []).map(s => s.sessionId === activeSession.sessionId ? { ...s, title: autoTitle } : s) };
//           });
//           saveProjects(updated);
//         }
//       }
//     } catch (err) {
//       const errMsg = { role: "assistant", content: `❌ Could not reach the backend.\n\nError: ${err.message}`, ts: now() };
//       setMsgCache(prev => ({ ...prev, [activeSession.sessionId]: [...(prev[activeSession.sessionId] || []), errMsg] }));
//     } finally {
//       setLoading(false);
//       fetchApiSessions();
//     }
//   };

//   // ── Delete session ────────────────────────────────────────────────────────
//   const deleteSession = async (sessionId) => {
//     if (!confirm("Delete this conversation permanently?")) return;
//     await fetch(`/api/sessions/${sessionId}`, { method: "DELETE", headers: authHeaders() }).catch(() => {});
//     setMsgCache(prev => { const n = { ...prev }; delete n[sessionId]; return n; });
//     if (activeSession?.sessionId === sessionId) setActiveSession(null);
//     fetchApiSessions();
//   };

//   // ── Rename ────────────────────────────────────────────────────────────────
//   const openRename = (type, id, currentName, e) => {
//     e?.stopPropagation();
//     setRenameTarget({ type, id });
//     setRenameName(currentName || "");
//     setShowRename(true);
//   };

//   const commitRename = async () => {
//     if (!renameName.trim() || !renameTarget) return;
//     if (renameTarget.type === "session") {
//       await fetch(`/api/sessions/${renameTarget.id}`, {
//         method: "PATCH", headers: authHeaders(),
//         body: JSON.stringify({ title: renameName.trim() }),
//       }).catch(() => {});
//       fetchApiSessions();
//       if (activeSession?.sessionId === renameTarget.id) {
//         setActiveSession(prev => ({ ...prev, title: renameName.trim() }));
//       }
//     } else if (renameTarget.type === "project") {
//       const updated = projects.map(p => p.id === renameTarget.id ? { ...p, name: renameName.trim() } : p);
//       saveProjects(updated);
//       if (selectedProject?.id === renameTarget.id) setSelectedProject(prev => ({ ...prev, name: renameName.trim() }));
//     }
//     setShowRename(false); setRenameTarget(null); setRenameName("");
//   };

//   // ── Project CRUD ──────────────────────────────────────────────────────────
//   const createProject = () => {
//     if (!newProjName.trim()) return;
//     const proj = { id: "p" + Date.now(), name: newProjName.trim(), emoji: newProjEmoji, description: newProjDesc.trim(), createdAt: new Date().toISOString().slice(0, 10), sessions: [] };
//     saveProjects([...projects, proj]);
//     setNewProjName(""); setNewProjDesc(""); setNewProjEmoji("🌱");
//     setShowNewProject(false);
//     setExpandedProjects(prev => new Set([...prev, proj.id]));
//   };

//   const deleteProject = (id) => {
//     saveProjects(projects.filter(p => p.id !== id));
//     if (selectedProject?.id === id) setSelectedProject(null);
//     if (activeSession?.projectId === id) setActiveSession(null);
//     setShowDeleteConfirm(false); setDeleteTarget(null);
//   };

//   // ── Filtered lists ────────────────────────────────────────────────────────
//   const search = sideSearch.toLowerCase();
//   const allProjectSessionIds = new Set(projects.flatMap(p => (p.sessions || []).map(ss => ss.sessionId)));
//   const filteredApiSessions  = apiSessions.filter(s => !allProjectSessionIds.has(s.session_id) && (!search || (s.title || s.preview || "").toLowerCase().includes(search)));
//   const filteredProjects     = projects.filter(p => !search || p.name.toLowerCase().includes(search));
//   const currentMessages      = (activeSession && msgCache[activeSession.sessionId]) || [];

//   // ─────────────────────────────────────────────────────────────────────────
//   return (
//     <>
//       <style>{`
//         * { box-sizing: border-box; margin: 0; padding: 0; }
//         body { background: ${C.bg}; }
//         ::-webkit-scrollbar { width: 5px; }
//         ::-webkit-scrollbar-track { background: transparent; }
//         ::-webkit-scrollbar-thumb { background: ${C.border}; border-radius: 4px; }
//         @keyframes pulse { 0%,100% { opacity:0.3; transform:scale(0.85); } 50% { opacity:1; transform:scale(1.1); } }
//         .sidebar-item-actions { display: none; }
//         .sidebar-row:hover .sidebar-item-actions { display: flex; }
//       `}</style>

//       <div style={{ display: "flex", height: "100vh", fontFamily: "'Inter','Segoe UI',system-ui,sans-serif", color: C.text, overflow: "hidden", background: C.bg }}>

//         {/* ══════════════════════════════════════════════════════════════════
//             SIDEBAR  (Feature 1: collapsible)
//         ══════════════════════════════════════════════════════════════════ */}
//         <div style={{
//           width: sidebarOpen ? 248 : 0,
//           background: C.surface,
//           borderRight: sidebarOpen ? `1px solid ${C.border}` : "none",
//           display: "flex", flexDirection: "column", height: "100vh", flexShrink: 0,
//           overflow: "hidden",
//           transition: "width 0.2s ease",
//         }}>
//           {/* Logo + search */}
//           <div style={{ padding: "14px 12px 10px", borderBottom: `1px solid ${C.border}`, flexShrink: 0 }}>
//             <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
//               <Icon d={ICONS.leaf} size={20} stroke={C.accent} />
//               <span style={{ fontWeight: 700, fontSize: 15, color: C.text }}>Agentic RAG</span>
//             </div>
//             <div style={{ display: "flex", alignItems: "center", gap: 6, background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 8, padding: "6px 10px" }}>
//               <Icon d={ICONS.search} size={14} />
//               <input value={sideSearch} onChange={e => setSideSearch(e.target.value)} placeholder="Search…"
//                 style={{ flex: 1, background: "transparent", border: "none", outline: "none", color: C.text, fontSize: 12, fontFamily: "inherit" }} />
//             </div>
//           </div>

//           <div style={{ flex: 1, overflowY: "auto", padding: "8px 0" }}>
//             {/* New Chat */}
//             <div style={{ padding: "4px 8px 8px" }}>
//               <Btn variant="surface" onClick={() => openNewChat(null)} style={{ width: "100%", justifyContent: "center" }}>
//                 <Icon d={ICONS.plus} size={14} stroke={C.accent} /> New chat
//               </Btn>
//             </div>

//             {/* ── Recent Chats ── */}
//             <div style={{ padding: "8px 14px 4px", fontSize: 11, fontWeight: 700, color: C.textMute, letterSpacing: "0.08em" }}>RECENT CHATS</div>
//             {filteredApiSessions.length === 0 && (
//               <div style={{ fontSize: 12, color: C.textMute, padding: "4px 18px" }}>No chats yet</div>
//             )}
//             {filteredApiSessions.map(s => {
//               const label = s.title || s.preview || "Untitled";
//               return (
//                 <div key={s.session_id} className="sidebar-row"
//                   style={{ position: "relative", display: "flex", alignItems: "center", margin: "1px 6px", borderRadius: 8, background: activeSession?.sessionId === s.session_id ? C.accentBg : "transparent" }}>
//                   <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 8, padding: "7px 36px 7px 12px", color: activeSession?.sessionId === s.session_id ? C.accent : C.textSub, fontSize: 13, fontWeight: activeSession?.sessionId === s.session_id ? 600 : 400, cursor: "pointer", overflow: "hidden" }}
//                     onClick={() => openExistingSession(s.session_id, null)}>
//                     <Icon d={ICONS.chat} size={14} stroke="currentColor" />
//                     <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{label}</span>
//                   </div>
//                   {/* Feature 4: rename + delete for recent chats */}
//                   <div className="sidebar-item-actions" style={{ position: "absolute", right: 6, gap: 2 }}>
//                     <button onClick={e => openRename("session", s.session_id, label, e)} title="Rename"
//                       style={{ background: "none", border: "none", cursor: "pointer", padding: 3, borderRadius: 4, opacity: 0.6 }}>
//                       <Icon d={ICONS.edit} size={11} stroke={C.textSub} />
//                     </button>
//                     <button onClick={e => { e.stopPropagation(); deleteSession(s.session_id); }} title="Delete"
//                       style={{ background: "none", border: "none", cursor: "pointer", padding: 3, borderRadius: 4, opacity: 0.6 }}>
//                       <Icon d={ICONS.trash} size={11} stroke={C.danger} />
//                     </button>
//                   </div>
//                 </div>
//               );
//             })}

//             {/* ── Projects ── */}
//             <div style={{ padding: "12px 14px 4px", fontSize: 11, fontWeight: 700, color: C.textMute, letterSpacing: "0.08em", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
//               <span>PROJECTS</span>
//               <button onClick={() => setShowNewProject(true)} style={{ background: "none", border: "none", cursor: "pointer", padding: 2 }}>
//                 <Icon d={ICONS.plus} size={14} stroke={C.accent} />
//               </button>
//             </div>

//             {filteredProjects.map(proj => {
//               const isExpanded = expandedProjects.has(proj.id);
//               const isSelected = activeSession?.projectId === proj.id;
//               return (
//                 <div key={proj.id}>
//                   <div className="sidebar-row" style={{ display: "flex", alignItems: "center", margin: "1px 6px", borderRadius: 8, background: isSelected ? C.accentBg : "transparent", position: "relative" }}>
//                     <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 8, padding: "7px 8px 7px 12px", color: isSelected ? C.accent : C.textSub, fontSize: 13, fontWeight: isSelected ? 600 : 400, cursor: "pointer", overflow: "hidden" }}
//                       onClick={() => { setSelectedProject(proj); setExpandedProjects(prev => new Set([...prev, proj.id])); }}>
//                       <span style={{ fontSize: 15 }}>{proj.emoji}</span>
//                       <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{proj.name}</span>
//                     </div>
//                     {/* Feature 4: rename + delete for projects */}
//                     <div className="sidebar-item-actions" style={{ gap: 2 }}>
//                       <button onClick={e => openRename("project", proj.id, proj.name, e)} title="Rename project"
//                         style={{ background: "none", border: "none", cursor: "pointer", padding: 3, borderRadius: 4, opacity: 0.6 }}>
//                         <Icon d={ICONS.edit} size={11} stroke={C.textSub} />
//                       </button>
//                       <button onClick={e => { e.stopPropagation(); setDeleteTarget({ type: "project", id: proj.id, name: proj.name }); setShowDeleteConfirm(true); }} title="Delete project"
//                         style={{ background: "none", border: "none", cursor: "pointer", padding: 3, borderRadius: 4, opacity: 0.6 }}>
//                         <Icon d={ICONS.trash} size={11} stroke={C.danger} />
//                       </button>
//                     </div>
//                     <button onClick={e => { e.stopPropagation(); setExpandedProjects(prev => { const s = new Set(prev); s.has(proj.id) ? s.delete(proj.id) : s.add(proj.id); return s; }); }}
//                       style={{ background: "none", border: "none", cursor: "pointer", padding: "7px 8px", color: C.textMute, flexShrink: 0 }}>
//                       <Icon d={isExpanded ? ICONS.chevD : ICONS.chevR} size={13} stroke={C.textMute} />
//                     </button>
//                   </div>
//                   {isExpanded && (
//                     <div>
//                       {(proj.sessions || []).map(sess => {
//                         const apiS = apiSessions.find(a => a.session_id === sess.sessionId);
//                         const label = apiS?.title || apiS?.preview || sess.title || "Chat";
//                         return (
//                           <div key={sess.sessionId} className="sidebar-row" style={{ position: "relative", display: "flex", alignItems: "center" }}>
//                             <SideItem indent={1}
//                               icon={<Icon d={ICONS.chat} size={13} stroke="currentColor" />}
//                               label={label}
//                               muted
//                               active={activeSession?.sessionId === sess.sessionId}
//                               onClick={() => openExistingSession(sess.sessionId, proj.id)}
//                             />
//                             <div className="sidebar-item-actions" style={{ position: "absolute", right: 10, gap: 2 }}>
//                               <button onClick={e => openRename("session", sess.sessionId, label, e)} title="Rename"
//                                 style={{ background: "none", border: "none", cursor: "pointer", padding: 3, borderRadius: 4, opacity: 0.6 }}>
//                                 <Icon d={ICONS.edit} size={11} stroke={C.textSub} />
//                               </button>
//                               <button onClick={e => { e.stopPropagation(); deleteSession(sess.sessionId); }} title="Delete"
//                                 style={{ background: "none", border: "none", cursor: "pointer", padding: 3, borderRadius: 4, opacity: 0.6 }}>
//                                 <Icon d={ICONS.trash} size={11} stroke={C.danger} />
//                               </button>
//                             </div>
//                           </div>
//                         );
//                       })}
//                       <SideItem indent={1} muted
//                         icon={<Icon d={ICONS.plus} size={13} stroke={C.textMute} />}
//                         label="New chat"
//                         onClick={() => openNewChat(proj.id)}
//                       />
//                     </div>
//                   )}
//                 </div>
//               );
//             })}

//             {/* ── Knowledge base PDFs ── */}
//             <div style={{ padding: "12px 14px 4px", fontSize: 11, fontWeight: 700, color: C.textMute, letterSpacing: "0.08em" }}>KNOWLEDGE BASE</div>
//             {[
//               { label: "PARC Report 2023-24",  file: "PARC Annual Report 2023-24_compressed.pdf" },
//               { label: "FAO Crop Guidelines",  file: "i5550e.pdf" },
//               { label: "Punjab Agri Rules",    file: "PbAgriDeptExtenAdapReseWing_SR_2007_20070612.pdf" },
//             ].map(({ label, file }) => (
//               <div key={file} onClick={() => window.open(`/api/pdf/${encodeURIComponent(file)}`, "_blank")}
//                 style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 12px 6px 18px", cursor: "pointer", color: C.textSub, fontSize: 12 }}>
//                 <Icon d={ICONS.book} size={13} stroke={C.textMute} />
//                 <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{label}</span>
//                 <span style={{ color: C.accentDim, fontSize: 10 }}>↗</span>
//               </div>
//             ))}
//           </div>

//           {/* User footer */}
//           <div style={{ padding: "10px 14px", borderTop: `1px solid ${C.border}`, display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
//             <div style={{ width: 30, height: 30, borderRadius: "50%", background: C.accentBg, border: `1px solid ${C.accent}44`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 700, color: C.accent }}>
//               {username[0].toUpperCase()}
//             </div>
//             <span style={{ flex: 1, fontSize: 12, color: C.textSub, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{username}</span>
//             {onLogout && (
//               <button onClick={onLogout} title="Sign out" style={{ background: "none", border: "none", cursor: "pointer" }}>
//                 <Icon d={ICONS.x} size={14} stroke={C.textMute} />
//               </button>
//             )}
//           </div>
//         </div>

//         {/* ══════════════════════════════════════════════════════════════════
//             MAIN CHAT AREA
//         ══════════════════════════════════════════════════════════════════ */}
//         <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", minWidth: 0 }}>
//           {/* Header */}
//           <div style={{ padding: "0 16px", height: 52, display: "flex", alignItems: "center", gap: 10, background: C.surface, borderBottom: `1px solid ${C.border}`, flexShrink: 0 }}>
//             {/* Feature 1: sidebar toggle button */}
//             <button onClick={() => setSidebarOpen(o => !o)} title={sidebarOpen ? "Close sidebar" : "Open sidebar"}
//               style={{ background: "none", border: `1px solid ${C.border}`, borderRadius: 7, padding: "5px 7px", cursor: "pointer", display: "flex", alignItems: "center", flexShrink: 0 }}>
//               <Icon d={sidebarOpen ? ICONS.panelClose : ICONS.panelOpen} size={15} stroke={C.textSub} />
//             </button>

//             <span style={{ fontSize: 16 }}>🌾</span>
//             <div style={{ flex: 1, minWidth: 0 }}>
//               <span style={{ fontSize: 14, fontWeight: 600, color: C.text }}>
//                 {activeSession ? activeSession.title : "Agricultural Knowledge Base"}
//               </span>
//               {activeSession?.projectId && (
//                 <span style={{ fontSize: 11, color: C.textMute, marginLeft: 8 }}>
//                   · {projects.find(p => p.id === activeSession.projectId)?.name}
//                 </span>
//               )}
//             </div>

//             {/* Feature 2: Tavily web search toggle */}
//             <button onClick={() => setWebSearch(w => !w)}
//               title={webSearch ? "Web search ON (Tavily) — click to disable" : "Web search OFF — click to enable Tavily"}
//               style={{
//                 display: "flex", alignItems: "center", gap: 5, padding: "4px 10px", borderRadius: 20,
//                 background: webSearch ? C.tealBg : "transparent",
//                 border: `1px solid ${webSearch ? C.teal : C.border}`,
//                 cursor: "pointer", fontSize: 12, fontWeight: 600,
//                 color: webSearch ? C.teal : C.textMute,
//                 transition: "all 0.15s",
//               }}>
//               <div style={{ width: 7, height: 7, borderRadius: "50%", background: webSearch ? C.teal : C.textMute, boxShadow: webSearch ? `0 0 5px ${C.teal}` : "none", transition: "all 0.15s" }} />
//               Web Search {webSearch ? "ON" : "OFF"}
//             </button>

//             {/* Feature 3: PDF export of current chat */}
//             <StatusBadge chunks={chunkCount} />
//             {activeSession && (
//               <button
//                 onClick={() => exportChatAsPDF(currentMessages, activeSession.title)}
//                 title="Download chat as PDF"
//                 style={{ display: "flex", alignItems: "center", gap: 5, padding: "4px 10px", borderRadius: 8, background: "none", border: `1px solid ${C.border}`, cursor: "pointer", fontSize: 12, color: C.textSub, whiteSpace: "nowrap" }}>
//                 <Icon d={ICONS.pdf} size={13} stroke={C.textSub} />
//                 Save PDF
//               </button>
//             )}
//             <button onClick={() => setShowTrace(t => !t)} title={showTrace ? "Hide trace" : "Show trace"}
//               style={{ background: "none", border: `1px solid ${C.border}`, borderRadius: 6, padding: "4px 8px", cursor: "pointer", color: C.amber, fontSize: 12, display: "flex", alignItems: "center", gap: 5, whiteSpace: "nowrap" }}>
//               <Icon d={ICONS.trace} size={13} stroke={C.amber} />
//               Trace
//             </button>
//           </div>

//           {/* Chat area */}
//           <div ref={chatRef} style={{ flex: 1, overflowY: "auto", padding: "20px 24px", display: "flex", flexDirection: "column", gap: 16 }}>
//             {!activeSession ? (
//               <Welcome onSend={(p) => { openNewChat(null); setTimeout(() => sendMessage(p), 50); }} />
//             ) : currentMessages.length === 0 ? (
//               <Welcome onSend={sendMessage} />
//             ) : (
//               currentMessages.map((m, i) => (
//                 <Message key={i} role={m.role} content={m.content} ts={m.ts} usedRag={m.usedRag}
//                   uploadedFile={m.uploadedFile}
//                   webSearched={m.webSearched}
//                   onRegenerate={m.role === "assistant" ? () => {
//                     const prev = currentMessages.slice(0, i).reverse().find(x => x.role === "user");
//                     if (prev) sendMessage(prev.content);
//                   } : null}
//                 />
//               ))
//             )}
//             {loading && <TypingDots />}
//           </div>

//           {/* Input (Feature 5: "+" file upload button) */}
//           <div style={{ padding: "12px 20px 16px", borderTop: `1px solid ${C.border}`, background: C.surface, flexShrink: 0 }}>
//             {!activeSession && (
//               <div style={{ fontSize: 12, color: C.textMute, textAlign: "center", marginBottom: 8 }}>
//                 Click <strong style={{ color: C.accent }}>+ New chat</strong> or select a conversation to start.
//               </div>
//             )}

//             {/* Pending file badge */}
//             {pendingFile && (
//               <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 8, padding: "5px 10px", background: C.accentBg, border: `1px solid ${C.accentDim}`, borderRadius: 8, width: "fit-content" }}>
//                 <Icon d={ICONS.attach} size={12} stroke={C.accent} />
//                 <span style={{ fontSize: 12, color: C.accent, fontWeight: 500 }}>{pendingFile.name}</span>
//                 <span style={{ fontSize: 11, color: C.textSub }}>will be used in next message</span>
//                 <button onClick={() => setPendingFile(null)} style={{ background: "none", border: "none", cursor: "pointer", padding: 0, marginLeft: 4 }}>
//                   <Icon d={ICONS.x} size={11} stroke={C.textSub} />
//                 </button>
//               </div>
//             )}

//             {uploadingFile && (
//               <div style={{ fontSize: 12, color: C.teal, marginBottom: 8 }}>⏳ Uploading document…</div>
//             )}

//             <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
//               {/* Feature 5: file upload "+" button */}
//               <button
//                 onClick={() => fileInputRef.current?.click()}
//                 disabled={!activeSession || uploadingFile}
//                 title="Attach a document (PDF, TXT, DOCX) to your message"
//                 style={{
//                   width: 38, height: 38, borderRadius: 9, border: `1px solid ${C.border}`,
//                   background: C.surface2, cursor: activeSession ? "pointer" : "not-allowed",
//                   display: "flex", alignItems: "center", justifyContent: "center",
//                   flexShrink: 0, alignSelf: "flex-end",
//                   opacity: activeSession ? 1 : 0.4, transition: "all 0.15s",
//                   color: pendingFile ? C.accent : C.textSub,
//                 }}
//                 onMouseEnter={e => { if (activeSession) e.currentTarget.style.borderColor = C.accent; }}
//                 onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; }}>
//                 <Icon d={ICONS.attach} size={15} stroke={pendingFile ? C.accent : C.textSub} />
//               </button>
//               <input ref={fileInputRef} type="file" accept=".pdf,.txt,.docx,.csv,.md"
//                 style={{ display: "none" }} onChange={handleFileSelect} />

//               <div style={{ flex: 1, background: C.surface2, border: `1px solid ${activeSession ? C.borderHi : C.border}`, borderRadius: 10, padding: "10px 14px" }}>
//                 <textarea ref={textareaRef} rows={2} value={input}
//                   onChange={e => setInput(e.target.value)}
//                   onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
//                   placeholder={
//                     !activeSession ? "Select or create a chat first" :
//                     webSearch ? "Ask anything — web search is ON (Tavily)… (Enter to send)" :
//                     "Ask about crops, diseases, PARC activities… (Enter to send)"
//                   }
//                   disabled={!activeSession}
//                   style={{ width: "100%", background: "transparent", border: "none", outline: "none", color: C.text, fontSize: 14, fontFamily: "inherit", resize: "none", lineHeight: 1.5 }} />
//               </div>
//               <button onClick={() => sendMessage()} disabled={loading || !input.trim() || !activeSession}
//                 style={{ width: 42, height: 42, borderRadius: 10, border: "none", background: C.accent, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", alignSelf: "flex-end", flexShrink: 0, opacity: (loading || !input.trim() || !activeSession) ? 0.4 : 1, transition: "opacity 0.15s" }}>
//                 <Icon d={ICONS.send} size={16} stroke="#fff" />
//               </button>
//             </div>
//           </div>
//         </div>

//         {/* ══════════════════════════════════════════════════════════════════
//             TRACE PANEL (collapsible)
//         ══════════════════════════════════════════════════════════════════ */}
//         {showTrace && (
//           <div style={{ width: 290, background: C.surface, borderLeft: `1px solid ${C.border}`, display: "flex", flexDirection: "column", overflow: "hidden", flexShrink: 0 }}>
//             <TracePanel
//               trace={trace}
//               webSearchResults={webSearchResults}
//               mcpCalls={mcpCalls}
//               status={status}
//               statusError={statusError}
//             />
//           </div>
//         )}
//       </div>

//       {/* ── Modals ───────────────────────────────────────────────────────── */}

//       {/* New Project */}
//       <Modal open={showNewProject} onClose={() => setShowNewProject(false)} title="Create new project">
//         <div style={{ marginBottom: 14 }}>
//           <label style={{ fontSize: 12, color: C.textSub, display: "block", marginBottom: 6 }}>Icon</label>
//           <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
//             {EMOJIS.map(e => (
//               <button key={e} onClick={() => setNewProjEmoji(e)}
//                 style={{ fontSize: 20, padding: "4px 8px", borderRadius: 8, cursor: "pointer", border: `1px solid ${newProjEmoji === e ? C.accent : C.border}`, background: newProjEmoji === e ? C.accentBg : C.surface2, fontFamily: "inherit" }}>
//                 {e}
//               </button>
//             ))}
//           </div>
//         </div>
//         <TextInput label="Project name" value={newProjName} onChange={setNewProjName} placeholder="e.g. Wheat Disease Research" autoFocus />
//         <TextInput label="Description (optional)" value={newProjDesc} onChange={setNewProjDesc} placeholder="What is this project about?" multiline />
//         <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", marginTop: 4 }}>
//           <Btn onClick={() => setShowNewProject(false)}>Cancel</Btn>
//           <Btn variant="primary" onClick={createProject} disabled={!newProjName.trim()}>Create project</Btn>
//         </div>
//       </Modal>

//       {/* Feature 4: Rename modal (sessions + projects) */}
//       <Modal open={showRename} onClose={() => { setShowRename(false); setRenameTarget(null); }}
//         title={`Rename ${renameTarget?.type === "project" ? "project" : "conversation"}`} width={400}>
//         <TextInput label="New name" value={renameName} onChange={setRenameName}
//           placeholder={renameTarget?.type === "project" ? "Project name" : "Conversation title"}
//           autoFocus />
//         <div style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
//           <Btn onClick={() => { setShowRename(false); setRenameTarget(null); }}>Cancel</Btn>
//           <Btn variant="primary" onClick={commitRename} disabled={!renameName.trim()}>Save</Btn>
//         </div>
//       </Modal>

//       {/* Delete confirm */}
//       <Modal open={showDeleteConfirm} onClose={() => { setShowDeleteConfirm(false); setDeleteTarget(null); }} title="Confirm deletion" width={380}>
//         <div style={{ fontSize: 13, color: C.textSub, marginBottom: 20, lineHeight: 1.6 }}>
//           Delete <strong style={{ color: C.text }}>{deleteTarget?.name}</strong>? This will remove all its chats and data.
//         </div>
//         <div style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
//           <Btn onClick={() => { setShowDeleteConfirm(false); setDeleteTarget(null); }}>Cancel</Btn>
//           <button onClick={() => { if (deleteTarget?.type === "project") deleteProject(deleteTarget.id); }}
//             style={{ padding: "7px 14px", borderRadius: 8, background: C.danger, color: "#fff", border: "none", cursor: "pointer", fontWeight: 600, fontSize: 13, fontFamily: "inherit" }}>
//             Delete
//           </button>
//         </div>
//       </Modal>
//     </>
//   );
// }


import { useState, useRef, useEffect, useCallback } from "react";

// ── Palette ───────────────────────────────────────────────────────────────────
const C = {
  bg:        "#0c1108",
  surface:   "#141c0f",
  surface2:  "#1c2614",
  surface3:  "#222e18",
  border:    "#2a3d1e",
  borderHi:  "#3d5a2a",
  accent:    "#7ab648",
  accentDim: "#4a7a1e",
  accentBg:  "rgba(122,182,72,0.10)",
  amber:     "#e8a020",
  amberDim:  "#7a4e00",
  amberBg:   "rgba(232,160,32,0.10)",
  teal:      "#2bbfa0",
  tealDim:   "#0d5a48",
  tealBg:    "rgba(43,191,160,0.10)",
  text:      "#dde8cc",
  textSub:   "#7a9460",
  textMute:  "#4a6035",
  userBub:   "#1a2e10",
  botBub:    "#0f1a08",
  danger:    "#c0392b",
  dangerBg:  "rgba(192,57,43,0.12)",
};

// ── Icon ──────────────────────────────────────────────────────────────────────
const Icon = ({ d, size = 16, stroke = C.textSub, fill = "none" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill={fill}
    stroke={stroke} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round"
    style={{ flexShrink: 0 }}>
    <path d={d} />
  </svg>
);

const ICONS = {
  leaf:      "M12 2a4 4 0 0 1 4 4v2h2a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2V6a4 4 0 0 1 4-4z",
  chat:      "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z",
  folder:    "M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z",
  file:      "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H8",
  plus:      "M12 5v14M5 12h14",
  trash:     "M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6",
  edit:      "M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z",
  upload:    "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12",
  download:  "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3",
  globe:     "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zM2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z",
  book:      "M4 19.5A2.5 2.5 0 0 1 6.5 17H20M4 19.5A2.5 2.5 0 0 0 6.5 22H20V2H6.5A2.5 2.5 0 0 0 4 4.5v15z",
  chevD:     "M6 9l6 6 6-6",
  chevR:     "M9 18l6-6-6-6",
  chevL:     "M15 18l-6-6 6-6",
  panelOpen: "M3 12h18M3 6h18M3 18h18",
  panelClose:"M3 6h7M3 12h7M3 18h7M17 6l4 6-4 6",
  x:         "M18 6L6 18M6 6l12 12",
  search:    "M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z",
  send:      "M22 2L11 13M22 2L15 22 11 13 2 9l20-7z",
  check:     "M20 6L9 17 4 12",
  copy:      "M20 9H11a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2v-9a2 2 0 0 0-2-2zM5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1",
  thumbUp:   "M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3",
  thumbDown: "M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zM17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17",
  share:     "M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8M16 6l-4-4-4 4M12 2v13",
  trace:     "M3 3h18v18H3zM9 9h6M9 13h6M9 17h4",
  bot:       "M12 2a4 4 0 0 1 4 4v2h2a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2V6a4 4 0 0 1 4-4zM9 10H7v2h2v-2zm8 0h-2v2h2v-2zm-5 4h-2v2h2v-2z",
  user:      "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
  snapshot:  "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H8",
  reset:     "M1 4v6h6M23 20v-6h-6M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15",
  sources:   "M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2zM22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z",
  regen:     "M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15",
  export:    "M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8M16 6l-4-4-4 4M12 2v13",
  pdf:       "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M11 13H8M16 13h-2M11 17H8M16 17h-2",
  tool:      "M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z",
  attach:    "M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48",
  weather:   "M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9z",
};

// ── Utilities ─────────────────────────────────────────────────────────────────
const now = () => new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

// ── Citation parser ───────────────────────────────────────────────────────────
function parseSources(content) {
  const sourcesMatch = content.match(/SOURCES:\s*\n([\s\S]+)$/i);
  const mainText = sourcesMatch
    ? content.slice(0, content.indexOf(sourcesMatch[0])).trim()
    : content;
  const sources = [];
  if (sourcesMatch) {
    const lines = sourcesMatch[1].trim().split("\n").filter(Boolean);
    lines.forEach(line => {
      const docMatch = line.match(/\[(\d+)\]\s*(.+?)\s*\|\s*[Pp]age\s*(\d+)/);
      if (docMatch) {
        sources.push({ num: parseInt(docMatch[1]), filename: docMatch[2].trim(), page: parseInt(docMatch[3]), type: "document" });
        return;
      }
      const webMatch = line.match(/\[Web\s*(\d+)\]\s*(.+?)\s*—\s*(https?:\/\/\S+)/);
      if (webMatch) {
        sources.push({ num: parseInt(webMatch[1]), title: webMatch[2].trim(), url: webMatch[3].trim(), type: "web" });
      }
    });
  }
  return { mainText, sources };
}

function renderTextWithCitations(text, sources, onCiteClick) {
  const parts = text.split(/(\[(?:Web\s*)?\d+\])/g);
  return parts.map((part, i) => {
    const match = part.match(/^\[(?:Web\s*)?(\d+)\]$/);
    if (match) {
      const num = parseInt(match[1]);
      const isWeb = part.toLowerCase().includes("web");
      const src = sources.find(s => s.num === num && (isWeb ? s.type === "web" : s.type === "document"))
               || sources.find(s => s.num === num);
      return (
        <sup key={i} onClick={() => src && onCiteClick(src)}
          title={src ? (src.type === "document" ? `${src.filename} — Page ${src.page}` : src.title) : ""}
          style={{
            cursor: src ? "pointer" : "default",
            color: src ? (src.type === "web" ? C.amber : C.accent) : C.textMute,
            fontWeight: 700, fontSize: "0.72em", marginLeft: 1,
            padding: "1px 4px", borderRadius: 3,
            background: src ? (src.type === "web" ? "#2a1e00" : "#16301a") : "transparent",
            border: src ? `1px solid ${src.type === "web" ? C.amberDim : C.accentDim}` : "none",
            userSelect: "none",
          }}>
          {part}
        </sup>
      );
    }
    return (
      <span key={i}>
        {part.split("\n").map((line, j, arr) => (
          <span key={j}>{line}{j < arr.length - 1 && <br />}</span>
        ))}
      </span>
    );
  });
}

function SourcesList({ sources }) {
  if (!sources || !sources.length) return null;
  const open = (src) => {
    if (src.type === "web" && src.url) window.open(src.url, "_blank", "noreferrer");
    else if (src.filename) window.open(`/api/pdf/${encodeURIComponent(src.filename)}#page=${src.page}`, "_blank");
  };
  return (
    <div style={{ marginTop: 12, paddingTop: 10, borderTop: `1px solid ${C.border}` }}>
      <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: C.textMute, marginBottom: 6 }}>
        References
      </div>
      {sources.map((src, i) => (
        <div key={i} onClick={() => open(src)}
          style={{ display: "flex", alignItems: "flex-start", gap: 7, marginBottom: 5, cursor: "pointer", padding: "5px 7px", borderRadius: 7, transition: "background 0.15s" }}
          onMouseEnter={e => e.currentTarget.style.background = C.surface2}
          onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
          <span style={{ minWidth: 20, height: 20, borderRadius: 4, flexShrink: 0, background: src.type === "document" ? C.accentDim : C.amberDim, border: `1px solid ${src.type === "document" ? C.accent : C.amber}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 9, fontWeight: 700, color: src.type === "document" ? C.accent : C.amber }}>
            {src.num}
          </span>
          <div style={{ fontSize: 11.5, color: C.textSub, lineHeight: 1.5 }}>
            {src.type === "document" ? (
              <><span style={{ color: C.text, fontWeight: 500 }}>{src.filename}</span><span style={{ color: C.textMute }}> — Page {src.page}</span><span style={{ color: C.accentDim, fontSize: 10, marginLeft: 5 }}>↗ open PDF</span></>
            ) : (
              <><span style={{ color: C.text, fontWeight: 500 }}>{src.title}</span><span style={{ color: C.amberDim, fontSize: 10, marginLeft: 5 }}>↗ web</span></>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Message bubble ────────────────────────────────────────────────────────────
function Message({ role, content, ts, usedRag, uploadedFile, sourceType, mcpTool, sources, onRegenerate }) {
  const [copied, setCopied] = useState(false);
  const [liked, setLiked]   = useState(null);
  // FIX: default to false — sources stay hidden until the user explicitly
  // clicks the sources toggle button, per the "don't show sources before
  // the user enables it" requirement.
  const [showSrc, setShowSrc] = useState(false);
  const isUser = role === "user";

  const ActionBtn = ({ icon, title, onClick, active, activeColor }) => (
    <button onClick={onClick} title={title}
      style={{ background: "none", border: "none", cursor: "pointer", padding: "4px 5px", borderRadius: 6, display: "flex", alignItems: "center", opacity: 0.55, transition: "opacity 0.15s" }}
      onMouseEnter={e => { e.currentTarget.style.opacity = "1"; e.currentTarget.style.background = C.surface2; }}
      onMouseLeave={e => { e.currentTarget.style.opacity = "0.55"; e.currentTarget.style.background = "none"; }}>
      <Icon d={icon} size={14} stroke={active ? (activeColor || C.accent) : C.textSub} />
    </button>
  );

  // Source badge: reflects exactly what the backend reports via
  // ChatResponse.source_type — "RAG" | "UPLOAD" | "MCP" | "WEB".
  // This is the source of truth (server-side), not a client-side guess.
  const sourceBadge = !isUser && sourceType && (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 9.5, fontWeight: 600, letterSpacing: "0.03em", padding: "2px 7px", borderRadius: 20,
      background: sourceType === "RAG" ? "#16301a" : sourceType === "UPLOAD" ? "#16301a" : sourceType === "MCP" ? "#1a2a3a" : "#2a2210",
      border: `1px solid ${sourceType === "RAG" || sourceType === "UPLOAD" ? C.accentDim : sourceType === "MCP" ? "#3a7ab0" : C.amberDim}`,
      color: sourceType === "RAG" || sourceType === "UPLOAD" ? C.accent : sourceType === "MCP" ? "#5aa0d8" : C.amber, marginLeft: 6 }}>
      {sourceType === "RAG" && "📚 RAG"}
      {sourceType === "UPLOAD" && "📎 Uploaded doc"}
      {sourceType === "MCP" && `⚡ MCP${mcpTool ? `: ${mcpTool}` : ""}`}
      {sourceType === "WEB" && "🌐 Web"}
    </span>
  );

  const ragBadge = !isUser && !sourceType && usedRag !== null && usedRag !== undefined && (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 9.5, fontWeight: 600, letterSpacing: "0.03em", padding: "2px 7px", borderRadius: 20, background: usedRag ? "#16301a" : "#2a2210", border: `1px solid ${usedRag ? C.accentDim : C.amberDim}`, color: usedRag ? C.accent : C.amber, marginLeft: 6 }}>
      {usedRag ? "RAG" : "🌐 Web"}
    </span>
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: isUser ? "flex-end" : "flex-start", gap: 4 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6, flexDirection: isUser ? "row-reverse" : "row" }}>
        <div style={{ width: 26, height: 26, borderRadius: "50%", background: isUser ? C.accentDim : "#1a2610", border: `1px solid ${isUser ? C.accent : C.border}`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <Icon d={isUser ? ICONS.user : ICONS.bot} size={13} stroke={isUser ? C.accent : C.textSub} />
        </div>
        <span style={{ fontSize: 11, color: C.textMute, display: "flex", alignItems: "center", flexWrap: "wrap", gap: 2 }}>
          {isUser ? "You" : "RAG Assistant"} · {ts}{sourceBadge}{ragBadge}
        </span>
      </div>

      {/* File attachment badge on user message */}
      {isUser && uploadedFile && (
        <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "5px 10px", background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 8, fontSize: 11, color: C.textSub, maxWidth: "78%" }}>
          <Icon d={ICONS.attach} size={12} stroke={C.accent} />
          <span style={{ color: C.accent, fontWeight: 500 }}>{uploadedFile}</span>
          <span style={{ color: C.textMute }}>· attached</span>
        </div>
      )}

      <div style={{ maxWidth: "78%", background: isUser ? C.userBub : C.botBub, border: `1px solid ${isUser ? C.accentDim : C.border}`, borderRadius: isUser ? "14px 4px 14px 14px" : "4px 14px 14px 14px", padding: "10px 14px", lineHeight: 1.65, fontSize: 14, color: C.text }}>
        {isUser ? (
          <span style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>{content}</span>
        ) : (() => {
          // FIX: sources now come from the API's structured sources[] field
          // (passed down as the `sources` prop), not scraped from a
          // "SOURCES:\n" text block — the pipeline stopped emitting that
          // block, so parseSources() always found zero sources.
          const apiSources = (sources || []).map(s => ({
            num:      s.num,
            filename: s.source_file || s.label || "",
            page:     s.page || 0,
            title:    s.label || s.source_file || "",
            url:      s.url || "",
            type:     s.url ? "web" : "document",
            is_upload: !!s.is_upload,
          }));
          // Strip any leftover inline SOURCES block from older cached messages
          const cleanContent = content
            .replace(/\n*SOURCES:[\s\S]*$/i, "")
            .replace(/\n*\*\*Web sources.*?\*\*[\s\S]*$/i, "")
            .trim();
          const onCiteClick = src => {
            if (src.type === "web" && src.url) window.open(src.url, "_blank", "noreferrer");
            else if (src.filename) window.open(`/api/pdf/${encodeURIComponent(src.filename)}#page=${src.page}`, "_blank");
          };
          return (
            <>
              <div style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                {renderTextWithCitations(cleanContent, apiSources, onCiteClick)}
              </div>
              {showSrc && <SourcesList sources={apiSources} />}
            </>
          );
        })()}
      </div>

      {!isUser && (
        <div style={{ display: "flex", alignItems: "center", gap: 1, paddingLeft: 4, marginTop: -2 }}>
          <ActionBtn icon={copied ? ICONS.check : ICONS.copy} title="Copy" onClick={() => { navigator.clipboard.writeText(content); setCopied(true); setTimeout(() => setCopied(false), 1500); }} active={copied} activeColor={C.accent} />
          <ActionBtn icon={ICONS.thumbUp} title="Good response" onClick={() => setLiked(l => l === "up" ? null : "up")} active={liked === "up"} activeColor={C.accent} />
          <ActionBtn icon={ICONS.thumbDown} title="Bad response" onClick={() => setLiked(l => l === "down" ? null : "down")} active={liked === "down"} activeColor={C.danger} />
          <ActionBtn icon={ICONS.share} title="Copy to clipboard" onClick={() => navigator.clipboard.writeText(content)} />
          {onRegenerate && <ActionBtn icon={ICONS.regen} title="Regenerate" onClick={onRegenerate} />}
          <div style={{ width: 1, height: 14, background: C.border, margin: "0 3px" }} />
          <ActionBtn icon={ICONS.sources} title={showSrc ? "Hide sources" : "Show sources"} onClick={() => setShowSrc(s => !s)} active={showSrc} activeColor={C.accent} />
        </div>
      )}
    </div>
  );
}

// ── Typing dots ───────────────────────────────────────────────────────────────
function TypingDots() {
  return (
    <div style={{ display: "flex", alignItems: "flex-start", gap: 6 }}>
      <div style={{ width: 26, height: 26, borderRadius: "50%", background: "#1a2610", border: `1px solid ${C.border}`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
        <Icon d={ICONS.bot} size={13} stroke={C.textSub} />
      </div>
      <div style={{ background: C.botBub, border: `1px solid ${C.border}`, borderRadius: "4px 14px 14px 14px", padding: "12px 16px", display: "flex", gap: 5, alignItems: "center" }}>
        {[0, 0.18, 0.36].map((delay, i) => (
          <div key={i} style={{ width: 7, height: 7, borderRadius: "50%", background: C.accentDim, animation: "pulse 1.2s ease-in-out infinite", animationDelay: `${delay}s` }} />
        ))}
      </div>
    </div>
  );
}

// ── Trace panel ───────────────────────────────────────────────────────────────
function TracePanel({ trace, status, statusError }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
      {/* Header — single Trace label, no tabs */}
      <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "10px 14px", borderBottom: `1px solid ${C.border}`, flexShrink: 0 }}>
        <Icon d={ICONS.trace} size={13} stroke={C.amber} />
        <span style={{ fontSize: 12, fontWeight: 700, color: C.amber }}>Trace</span>
      </div>

      <div style={{ flex: 1, overflowY: "auto", padding: "12px 14px" }}>
        {!trace ? (
          <div style={{ color: C.textMute, fontSize: 12, textAlign: "center", marginTop: 40, lineHeight: 1.7 }}>
            Pipeline step timings<br />appear here after each query
          </div>
        ) : (
          <pre style={{ fontFamily: "'JetBrains Mono','Fira Code',monospace", fontSize: 11, color: C.textSub, lineHeight: 1.75, whiteSpace: "pre-wrap", wordBreak: "break-word", margin: 0 }}>
            {trace}
          </pre>
        )}
      </div>

      {/* Pipeline config at bottom */}
      <div style={{ padding: "12px 14px", borderTop: `1px solid ${C.border}` }}>
        <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: C.textMute, marginBottom: 8 }}>Pipeline</div>
        {[
          ["Vector DB",  status?.vector_db || "ChromaDB"],
          ["Retrieval",  status?.retrieval || "BM25 + Embeddings"],
          ["Fusion",     status?.fusion    || "RRF"],
          ["Chunks",     (status?.chunk_count || 0).toLocaleString()],
        ].map(([k, v]) => (
          <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "4px 8px", background: C.surface2, borderRadius: 6, marginBottom: 4, fontSize: 12 }}>
            <span style={{ color: C.textSub }}>{k}</span>
            <span style={{ color: C.text }}>{v}</span>
          </div>
        ))}
        {statusError && (
          <div style={{ marginTop: 8, background: C.dangerBg, border: `1px solid ${C.danger}`, borderRadius: 8, padding: "8px 10px", fontSize: 11.5, color: "#e8938a", lineHeight: 1.5 }}>
            {statusError}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Welcome screen ────────────────────────────────────────────────────────────
function Welcome({ onSend }) {
  const prompts = [
    "What wheat diseases are monitored in Punjab?",
    "Is today's weather good for wheat sowing in Lahore?",
    "Convert 50 acres to hectares",
    "Which FAO guidelines cover Ug99 rust?",
    "Summarise PARC's 2023-24 research highlights",
    "What is the role of the Agriculture Extension Wing?",
  ];
  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: 32, gap: 28 }}>
      <div style={{ textAlign: "center" }}>
        <div style={{ fontSize: 40, marginBottom: 12 }}>🌾</div>
        <div style={{ fontSize: 22, fontWeight: 700, color: C.text, letterSpacing: "-0.02em", marginBottom: 6 }}>
          Agricultural RAG Assistant
        </div>
        <div style={{ fontSize: 13, color: C.textSub, maxWidth: 440, lineHeight: 1.6 }}>
          Grounded in PARC Annual Report, FAO Crop Guidelines, and Punjab Agri Rules.
          MCP tools: weather, crop calendar, unit converter, Tavily web search.
        </div>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, width: "100%", maxWidth: 560 }}>
        {prompts.map((p, i) => (
          <button key={i} onClick={() => onSend(p)}
            style={{ background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 10, padding: "10px 14px", color: C.textSub, fontSize: 12, textAlign: "left", cursor: "pointer", lineHeight: 1.5, transition: "border-color 0.15s, color 0.15s", fontFamily: "inherit" }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = C.accent; e.currentTarget.style.color = C.text; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.color = C.textSub; }}>
            {p}
          </button>
        ))}
      </div>
    </div>
  );
}

// ── Sidebar item ──────────────────────────────────────────────────────────────
const SideItem = ({ icon, label, active, onClick, indent = 0, muted = false }) => (
  <div onClick={onClick}
    style={{ display: "flex", alignItems: "center", gap: 8, padding: `7px 12px 7px ${12 + indent * 16}px`, borderRadius: 8, cursor: "pointer", margin: "1px 6px", background: active ? C.accentBg : "transparent", color: active ? C.accent : muted ? C.textMute : C.textSub, fontSize: 13, fontWeight: active ? 600 : 400, transition: "all 0.12s" }}>
    {icon}
    <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{label}</span>
  </div>
);

// ── Modal ─────────────────────────────────────────────────────────────────────
const Modal = ({ open, onClose, title, children, width = 480 }) => {
  if (!open) return null;
  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center" }}
      onClick={onClose}>
      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 14, padding: "24px 28px", width, maxWidth: "90vw", maxHeight: "80vh", overflowY: "auto" }}
        onClick={e => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <span style={{ fontSize: 16, fontWeight: 700, color: C.text }}>{title}</span>
          <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer" }}>
            <Icon d={ICONS.x} stroke={C.textSub} size={18} />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
};

const TextInput = ({ label, value, onChange, placeholder, multiline = false, autoFocus = false }) => (
  <div style={{ marginBottom: 14 }}>
    {label && <label style={{ fontSize: 12, color: C.textSub, display: "block", marginBottom: 6 }}>{label}</label>}
    {multiline
      ? <textarea value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
          style={{ width: "100%", background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 8, padding: "10px 12px", color: C.text, fontSize: 13, fontFamily: "inherit", outline: "none", resize: "vertical", minHeight: 80, boxSizing: "border-box" }} />
      : <input value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder} autoFocus={autoFocus}
          style={{ width: "100%", background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 8, padding: "10px 12px", color: C.text, fontSize: 13, fontFamily: "inherit", outline: "none", boxSizing: "border-box" }} />
    }
  </div>
);

const Btn = ({ children, onClick, variant = "ghost", danger = false, style: sx = {}, disabled = false }) => {
  const base = { display: "inline-flex", alignItems: "center", gap: 6, padding: "7px 12px", borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: disabled ? "not-allowed" : "pointer", border: "none", transition: "all 0.15s", opacity: disabled ? 0.5 : 1, fontFamily: "inherit" };
  const variants = {
    primary: { background: C.accent, color: C.bg },
    ghost:   { background: "transparent", color: danger ? C.danger : C.textSub, border: `1px solid ${danger ? C.danger + "55" : C.border}` },
    surface: { background: C.surface2, color: C.text, border: `1px solid ${C.border}` },
  };
  return <button style={{ ...base, ...variants[variant], ...sx }} onClick={onClick} disabled={disabled}>{children}</button>;
};

function StatusBadge({ chunks }) {
  const ok = chunks > 0;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "4px 10px", borderRadius: 20, background: ok ? "#1a3310" : "#3a1010", border: `1px solid ${ok ? C.accentDim : C.danger}`, fontSize: 12, color: ok ? C.accent : "#e74c3c", whiteSpace: "nowrap" }}>
      <div style={{ width: 7, height: 7, borderRadius: "50%", background: ok ? C.accent : C.danger, boxShadow: ok ? `0 0 6px ${C.accent}` : "none" }} />
      {ok ? `${chunks.toLocaleString()} chunks` : "Empty"}
    </div>
  );
}

// ── PDF chat export — uses MCP pdf export tool on backend ────────────────────
// Old client-side iframe/print approach replaced with server-side generation:
//   GET /api/sessions/{id}/export/pdf
//   → mcp_pdf_export.py reads SQLite (messages + pipeline steps + sources)
//   → Builds styled A4 HTML report
//   → weasyprint converts to real PDF (falls back to HTML if not installed)
//   → Binary stream downloaded by browser
// The sessionId-based approach means ALL data (traces, cited sources, token
// counts, pipeline timings) is included — not just what the frontend cached.
async function exportChatAsPDF(sessionId, sessionTitle, token) {
  if (!sessionId) {
    alert("No active chat to export.");
    return;
  }
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  try {
    const res = await fetch(`/api/sessions/${sessionId}/export/pdf`, { headers });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
      throw new Error(err.detail || `Export failed (${res.status})`);
    }
    const exportType = res.headers.get("X-Export-Type") || "pdf";
    const blob = await res.blob();
    const disposition = res.headers.get("Content-Disposition") || "";
    const match = disposition.match(/filename="([^"]+)"/);
    const filename = match ? match[1] : `chat.${exportType === "pdf" ? "pdf" : "html"}`;
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
    if (exportType === "html") {
      console.info(
        "[PDF Export] Server returned HTML — install weasyprint on the server for true PDF output:\n" +
        "  pip install weasyprint"
      );
    }
  } catch (err) {
    alert(`PDF export failed: ${err.message}\n\nMake sure the API server is running.`);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
//  MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════════════════════
const EMOJIS = ["🌱", "🌾", "🪴", "🌽", "🍃", "🌿", "🌻", "🌴", "🫘", "🍀"];

export default function ProjectManager({ username = "user", token, onLogout }) {
  // ── Projects / chats ──────────────────────────────────────────────────────
  const [projects, setProjects]               = useState([]);
  const [expandedProjects, setExpandedProjects] = useState(new Set());
  const [selectedProject, setSelectedProject] = useState(null);
  const [activeSession, setActiveSession]     = useState(null);
  const [msgCache, setMsgCache]               = useState({});
  const [loading, setLoading]                 = useState(false);
  const [trace, setTrace]                     = useState(null);
  const [input, setInput]                     = useState("");

  // ── New: sidebar collapsed ────────────────────────────────────────────────
  const [sidebarOpen, setSidebarOpen]         = useState(true);

  // ── New: web search toggle — sent to backend as force_web ──────────────────
  const [webSearch, setWebSearch]             = useState(false);

  // ── New: file upload state ────────────────────────────────────────────────
  const [pendingFile, setPendingFile]         = useState(null); // { name, fileId } after upload
  const [uploadingFile, setUploadingFile]     = useState(false);
  const fileInputRef                          = useRef(null);

  // ── Backend ───────────────────────────────────────────────────────────────
  const [apiSessions, setApiSessions]         = useState([]);
  const [status, setStatus]                   = useState(null);
  const [chunkCount, setChunkCount]           = useState(0);
  const [statusError, setStatusError]         = useState(null);
  const [sideSearch, setSideSearch]           = useState("");
  const [showTrace, setShowTrace]             = useState(true);

  // ── Modals ────────────────────────────────────────────────────────────────
  const [showNewProject, setShowNewProject]   = useState(false);
  const [newProjName, setNewProjName]         = useState("");
  const [newProjDesc, setNewProjDesc]         = useState("");
  const [newProjEmoji, setNewProjEmoji]       = useState("🌱");
  const [showRename, setShowRename]           = useState(false);
  const [renameTarget, setRenameTarget]       = useState(null);
  const [renameName, setRenameName]           = useState("");
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteTarget, setDeleteTarget]       = useState(null);

  const chatRef     = useRef(null);
  const textareaRef = useRef(null);

  const authHeaders = () => token
    ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` }
    : { "Content-Type": "application/json" };

  // ── Scroll ────────────────────────────────────────────────────────────────
  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [msgCache, activeSession, loading]);

  // ── Poll /api/status ──────────────────────────────────────────────────────
  useEffect(() => {
    const fetch_ = () => {
      fetch("/api/status").then(r => r.json()).then(d => {
        setStatus(d); setChunkCount(d.chunk_count || 0);
        setStatusError(d.vector_store_error || d.pipeline_error || null);
      }).catch(err => { setStatusError(`Cannot reach API: ${err.message}`); setChunkCount(0); });
    };
    fetch_(); const id = setInterval(fetch_, 8000); return () => clearInterval(id);
  }, []);

  // ── Load sessions ─────────────────────────────────────────────────────────
  const fetchApiSessions = useCallback(() => {
    fetch("/api/sessions", { headers: authHeaders() })
      .then(r => r.json())
      .then(d => setApiSessions(d.sessions || []))
      .catch(() => {});
  }, [token]);

  useEffect(() => { fetchApiSessions(); }, [fetchApiSessions]);

  // ── Load projects from localStorage ───────────────────────────────────────
  useEffect(() => {
    try {
      const saved = localStorage.getItem(`rag_projects_${username}`);
      if (saved) setProjects(JSON.parse(saved));
    } catch (_) {}
  }, [username]);

  const saveProjects = (ps) => {
    setProjects(ps);
    try { localStorage.setItem(`rag_projects_${username}`, JSON.stringify(ps)); } catch (_) {}
  };

  // ── Open session ──────────────────────────────────────────────────────────
  const openNewChat = (projectId = null) => {
    const sessionId = crypto.randomUUID();
    const proj = projectId ? projects.find(p => p.id === projectId) : null;
    const session = { sessionId, projectId, title: proj ? `${proj.emoji} New chat` : "New chat" };
    setActiveSession(session); setTrace(null); setInput("");
    setPendingFile(null);
    if (projectId) {
      const updated = projects.map(p => {
        if (p.id !== projectId) return p;
        return { ...p, sessions: [...(p.sessions || []), { sessionId, title: "New chat", date: new Date().toISOString().slice(0, 10) }] };
      });
      saveProjects(updated);
    }
  };

  const openExistingSession = (sessionId, projectId = null) => {
    const proj = projectId ? projects.find(p => p.id === projectId) : null;
    const apiSess = apiSessions.find(s => s.session_id === sessionId);
    const title = apiSess?.title || apiSess?.preview || "Chat";
    setActiveSession({ sessionId, projectId, title: proj ? `${proj.emoji} ${title}` : title });
    setTrace(null); setInput(""); setPendingFile(null);
    if (!msgCache[sessionId]) {
      fetch(`/api/sessions/${sessionId}`, { headers: authHeaders() })
        .then(r => r.json())
        .then(d => {
          const msgs = (d.messages || []).map(m => ({ role: m.role, content: m.content, ts: m.ts || now(), usedRag: m.used_rag }));
          setMsgCache(prev => ({ ...prev, [sessionId]: msgs }));
        }).catch(() => {});
    }
  };

  // ── FILE UPLOAD ("+") ─────────────────────────────────────────────────────
  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !activeSession) return;
    e.target.value = "";

    setUploadingFile(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      // CRITICAL: /api/upload requires session_id (or sessionId) as a form
      // field to register the file under SESSION_FILES[session_id] — without
      // this it silently falls back to a "global" bucket that this chat
      // session never looks at, so uploaded docs were never actually used.
      fd.append("session_id", activeSession.sessionId);
      const r = await fetch("/api/upload", {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: fd,
      });
      if (!r.ok) throw new Error(`Upload failed (${r.status})`);
      const data = await r.json();
      setPendingFile({ name: file.name, fileId: data.file_id });
    } catch (err) {
      alert(`File upload failed: ${err.message}\n\nMake sure the API server is running and /api/upload endpoint exists.`);
    } finally {
      setUploadingFile(false);
    }
  };

  // ── SEND MESSAGE ──────────────────────────────────────────────────────────
  const sendMessage = async (text) => {
    const q = (text || input).trim();
    if (!q || loading || !activeSession) return;
    setInput("");

    const attachedFile = pendingFile;
    setPendingFile(null);

    const userMsg = {
      role: "user", content: q, ts: now(),
      uploadedFile: attachedFile?.name || null,
    };
    setMsgCache(prev => ({
      ...prev,
      [activeSession.sessionId]: [...(prev[activeSession.sessionId] || []), userMsg],
    }));
    setLoading(true);
    setTrace(null);

    try {
      // ── Single call to /api/chat ────────────────────────────────────────
      // The backend now owns the whole routing decision:
      //   • force_web=false (default): the pipeline ALWAYS checks the 3
      //     indexed PDFs first (RAG), and only falls back to live Tavily
      //     web search if the relevance evaluator finds nothing useful.
      //   • force_web=true (Web Search toggle ON): skip the knowledge base
      //     and answer straight from the open internet.
      // MCP tools (weather / crop_calendar / unit_converter / tavily_search)
      // are dispatched automatically server-side on every query — no
      // separate pre-fetch call needed (that call used the wrong request
      // shape and was silently failing, which is why "MCP wasn't working").
      // Uploaded files are matched to this chat purely by session_id
      // (sent below during upload), so we don't need to pass a file_id here.
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          session_id: activeSession.sessionId,
          query: q,
          force_web: webSearch,
        }),
      });
      const data = await res.json();

      const botMsg = {
        role: "assistant",
        content: data.response || "No response received.",
        ts: now(),
        usedRag: data.used_rag,
        sourceType: data.source_type,   // "RAG" | "WEB" | "MCP" | "UPLOAD"
        mcpTool: data.mcp_tool || null,
        // FIX: capture structured sources from the API so the Sources panel
        // has data to render. Previously this was dropped entirely, so the
        // panel toggle always showed nothing even though citations [1][2]
        // rendered fine (those come from inline text, not this field).
        sources: data.sources || [],
      };
      setMsgCache(prev => ({
        ...prev,
        [activeSession.sessionId]: [...(prev[activeSession.sessionId] || []), botMsg],
      }));
      if (data.trace) setTrace(data.trace);

      // Auto-title
      const currentMsgs = msgCache[activeSession.sessionId] || [];
      if (currentMsgs.filter(m => m.role === "user").length === 0) {
        const autoTitle = q.slice(0, 40) + (q.length > 40 ? "…" : "");
        setActiveSession(prev => ({ ...prev, title: autoTitle }));
        if (activeSession.projectId) {
          const updated = projects.map(p => {
            if (p.id !== activeSession.projectId) return p;
            return { ...p, sessions: (p.sessions || []).map(s => s.sessionId === activeSession.sessionId ? { ...s, title: autoTitle } : s) };
          });
          saveProjects(updated);
        }
      }
    } catch (err) {
      const errMsg = { role: "assistant", content: `❌ Could not reach the backend.\n\nError: ${err.message}`, ts: now() };
      setMsgCache(prev => ({ ...prev, [activeSession.sessionId]: [...(prev[activeSession.sessionId] || []), errMsg] }));
    } finally {
      setLoading(false);
      fetchApiSessions();
    }
  };

  // ── Delete session ────────────────────────────────────────────────────────
  const deleteSession = async (sessionId) => {
    if (!confirm("Delete this conversation permanently?")) return;
    await fetch(`/api/sessions/${sessionId}`, { method: "DELETE", headers: authHeaders() }).catch(() => {});
    setMsgCache(prev => { const n = { ...prev }; delete n[sessionId]; return n; });
    if (activeSession?.sessionId === sessionId) setActiveSession(null);
    fetchApiSessions();
  };

  // ── Rename ────────────────────────────────────────────────────────────────
  const openRename = (type, id, currentName, e) => {
    e?.stopPropagation();
    setRenameTarget({ type, id });
    setRenameName(currentName || "");
    setShowRename(true);
  };

  const commitRename = async () => {
    if (!renameName.trim() || !renameTarget) return;
    if (renameTarget.type === "session") {
      await fetch(`/api/sessions/${renameTarget.id}`, {
        method: "PATCH", headers: authHeaders(),
        body: JSON.stringify({ title: renameName.trim() }),
      }).catch(() => {});
      fetchApiSessions();
      if (activeSession?.sessionId === renameTarget.id) {
        setActiveSession(prev => ({ ...prev, title: renameName.trim() }));
      }
    } else if (renameTarget.type === "project") {
      const updated = projects.map(p => p.id === renameTarget.id ? { ...p, name: renameName.trim() } : p);
      saveProjects(updated);
      if (selectedProject?.id === renameTarget.id) setSelectedProject(prev => ({ ...prev, name: renameName.trim() }));
    }
    setShowRename(false); setRenameTarget(null); setRenameName("");
  };

  // ── Project CRUD ──────────────────────────────────────────────────────────
  const createProject = () => {
    if (!newProjName.trim()) return;
    const proj = { id: "p" + Date.now(), name: newProjName.trim(), emoji: newProjEmoji, description: newProjDesc.trim(), createdAt: new Date().toISOString().slice(0, 10), sessions: [] };
    saveProjects([...projects, proj]);
    setNewProjName(""); setNewProjDesc(""); setNewProjEmoji("🌱");
    setShowNewProject(false);
    setExpandedProjects(prev => new Set([...prev, proj.id]));
  };

  const deleteProject = (id) => {
    saveProjects(projects.filter(p => p.id !== id));
    if (selectedProject?.id === id) setSelectedProject(null);
    if (activeSession?.projectId === id) setActiveSession(null);
    setShowDeleteConfirm(false); setDeleteTarget(null);
  };

  // ── Filtered lists ────────────────────────────────────────────────────────
  const search = sideSearch.toLowerCase();
  const allProjectSessionIds = new Set(projects.flatMap(p => (p.sessions || []).map(ss => ss.sessionId)));
  const filteredApiSessions  = apiSessions.filter(s => !allProjectSessionIds.has(s.session_id) && (!search || (s.title || s.preview || "").toLowerCase().includes(search)));
  const filteredProjects     = projects.filter(p => !search || p.name.toLowerCase().includes(search));
  const currentMessages      = (activeSession && msgCache[activeSession.sessionId]) || [];

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <>
      <style>{`
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: ${C.bg}; }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: ${C.border}; border-radius: 4px; }
        @keyframes pulse { 0%,100% { opacity:0.3; transform:scale(0.85); } 50% { opacity:1; transform:scale(1.1); } }
        .sidebar-item-actions { display: none; }
        .sidebar-row:hover .sidebar-item-actions { display: flex; }
      `}</style>

      <div style={{ display: "flex", height: "100vh", fontFamily: "'Inter','Segoe UI',system-ui,sans-serif", color: C.text, overflow: "hidden", background: C.bg }}>

        {/* ══════════════════════════════════════════════════════════════════
            SIDEBAR  (Feature 1: collapsible)
        ══════════════════════════════════════════════════════════════════ */}
        <div style={{
          width: sidebarOpen ? 248 : 0,
          background: C.surface,
          borderRight: sidebarOpen ? `1px solid ${C.border}` : "none",
          display: "flex", flexDirection: "column", height: "100vh", flexShrink: 0,
          overflow: "hidden",
          transition: "width 0.2s ease",
        }}>
          {/* Logo + search */}
          <div style={{ padding: "14px 12px 10px", borderBottom: `1px solid ${C.border}`, flexShrink: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
              <Icon d={ICONS.leaf} size={20} stroke={C.accent} />
              <span style={{ fontWeight: 700, fontSize: 15, color: C.text }}>Agentic RAG</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 6, background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 8, padding: "6px 10px" }}>
              <Icon d={ICONS.search} size={14} />
              <input value={sideSearch} onChange={e => setSideSearch(e.target.value)} placeholder="Search…"
                style={{ flex: 1, background: "transparent", border: "none", outline: "none", color: C.text, fontSize: 12, fontFamily: "inherit" }} />
            </div>
          </div>

          <div style={{ flex: 1, overflowY: "auto", padding: "8px 0" }}>
            {/* New Chat */}
            <div style={{ padding: "4px 8px 8px" }}>
              <Btn variant="surface" onClick={() => openNewChat(null)} style={{ width: "100%", justifyContent: "center" }}>
                <Icon d={ICONS.plus} size={14} stroke={C.accent} /> New chat
              </Btn>
            </div>

            {/* ── Recent Chats ── */}
            <div style={{ padding: "8px 14px 4px", fontSize: 11, fontWeight: 700, color: C.textMute, letterSpacing: "0.08em" }}>RECENT CHATS</div>
            {filteredApiSessions.length === 0 && (
              <div style={{ fontSize: 12, color: C.textMute, padding: "4px 18px" }}>No chats yet</div>
            )}
            {filteredApiSessions.map(s => {
              const label = s.title || s.preview || "Untitled";
              return (
                <div key={s.session_id} className="sidebar-row"
                  style={{ position: "relative", display: "flex", alignItems: "center", margin: "1px 6px", borderRadius: 8, background: activeSession?.sessionId === s.session_id ? C.accentBg : "transparent" }}>
                  <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 8, padding: "7px 36px 7px 12px", color: activeSession?.sessionId === s.session_id ? C.accent : C.textSub, fontSize: 13, fontWeight: activeSession?.sessionId === s.session_id ? 600 : 400, cursor: "pointer", overflow: "hidden" }}
                    onClick={() => openExistingSession(s.session_id, null)}>
                    <Icon d={ICONS.chat} size={14} stroke="currentColor" />
                    <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{label}</span>
                  </div>
                  {/* Feature 4: rename + delete for recent chats */}
                  <div className="sidebar-item-actions" style={{ position: "absolute", right: 6, gap: 2 }}>
                    <button onClick={e => openRename("session", s.session_id, label, e)} title="Rename"
                      style={{ background: "none", border: "none", cursor: "pointer", padding: 3, borderRadius: 4, opacity: 0.6 }}>
                      <Icon d={ICONS.edit} size={11} stroke={C.textSub} />
                    </button>
                    <button onClick={e => { e.stopPropagation(); deleteSession(s.session_id); }} title="Delete"
                      style={{ background: "none", border: "none", cursor: "pointer", padding: 3, borderRadius: 4, opacity: 0.6 }}>
                      <Icon d={ICONS.trash} size={11} stroke={C.danger} />
                    </button>
                  </div>
                </div>
              );
            })}

            {/* ── Projects ── */}
            <div style={{ padding: "12px 14px 4px", fontSize: 11, fontWeight: 700, color: C.textMute, letterSpacing: "0.08em", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span>PROJECTS</span>
              <button onClick={() => setShowNewProject(true)} style={{ background: "none", border: "none", cursor: "pointer", padding: 2 }}>
                <Icon d={ICONS.plus} size={14} stroke={C.accent} />
              </button>
            </div>

            {filteredProjects.map(proj => {
              const isExpanded = expandedProjects.has(proj.id);
              const isSelected = activeSession?.projectId === proj.id;
              return (
                <div key={proj.id}>
                  <div className="sidebar-row" style={{ display: "flex", alignItems: "center", margin: "1px 6px", borderRadius: 8, background: isSelected ? C.accentBg : "transparent", position: "relative" }}>
                    <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 8, padding: "7px 8px 7px 12px", color: isSelected ? C.accent : C.textSub, fontSize: 13, fontWeight: isSelected ? 600 : 400, cursor: "pointer", overflow: "hidden" }}
                      onClick={() => { setSelectedProject(proj); setExpandedProjects(prev => new Set([...prev, proj.id])); }}>
                      <span style={{ fontSize: 15 }}>{proj.emoji}</span>
                      <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{proj.name}</span>
                    </div>
                    {/* Feature 4: rename + delete for projects */}
                    <div className="sidebar-item-actions" style={{ gap: 2 }}>
                      <button onClick={e => openRename("project", proj.id, proj.name, e)} title="Rename project"
                        style={{ background: "none", border: "none", cursor: "pointer", padding: 3, borderRadius: 4, opacity: 0.6 }}>
                        <Icon d={ICONS.edit} size={11} stroke={C.textSub} />
                      </button>
                      <button onClick={e => { e.stopPropagation(); setDeleteTarget({ type: "project", id: proj.id, name: proj.name }); setShowDeleteConfirm(true); }} title="Delete project"
                        style={{ background: "none", border: "none", cursor: "pointer", padding: 3, borderRadius: 4, opacity: 0.6 }}>
                        <Icon d={ICONS.trash} size={11} stroke={C.danger} />
                      </button>
                    </div>
                    <button onClick={e => { e.stopPropagation(); setExpandedProjects(prev => { const s = new Set(prev); s.has(proj.id) ? s.delete(proj.id) : s.add(proj.id); return s; }); }}
                      style={{ background: "none", border: "none", cursor: "pointer", padding: "7px 8px", color: C.textMute, flexShrink: 0 }}>
                      <Icon d={isExpanded ? ICONS.chevD : ICONS.chevR} size={13} stroke={C.textMute} />
                    </button>
                  </div>
                  {isExpanded && (
                    <div>
                      {(proj.sessions || []).map(sess => {
                        const apiS = apiSessions.find(a => a.session_id === sess.sessionId);
                        const label = apiS?.title || apiS?.preview || sess.title || "Chat";
                        return (
                          <div key={sess.sessionId} className="sidebar-row" style={{ position: "relative", display: "flex", alignItems: "center" }}>
                            <SideItem indent={1}
                              icon={<Icon d={ICONS.chat} size={13} stroke="currentColor" />}
                              label={label}
                              muted
                              active={activeSession?.sessionId === sess.sessionId}
                              onClick={() => openExistingSession(sess.sessionId, proj.id)}
                            />
                            <div className="sidebar-item-actions" style={{ position: "absolute", right: 10, gap: 2 }}>
                              <button onClick={e => openRename("session", sess.sessionId, label, e)} title="Rename"
                                style={{ background: "none", border: "none", cursor: "pointer", padding: 3, borderRadius: 4, opacity: 0.6 }}>
                                <Icon d={ICONS.edit} size={11} stroke={C.textSub} />
                              </button>
                              <button onClick={e => { e.stopPropagation(); deleteSession(sess.sessionId); }} title="Delete"
                                style={{ background: "none", border: "none", cursor: "pointer", padding: 3, borderRadius: 4, opacity: 0.6 }}>
                                <Icon d={ICONS.trash} size={11} stroke={C.danger} />
                              </button>
                            </div>
                          </div>
                        );
                      })}
                      <SideItem indent={1} muted
                        icon={<Icon d={ICONS.plus} size={13} stroke={C.textMute} />}
                        label="New chat"
                        onClick={() => openNewChat(proj.id)}
                      />
                    </div>
                  )}
                </div>
              );
            })}

            {/* ── Knowledge base PDFs ── */}
            <div style={{ padding: "12px 14px 4px", fontSize: 11, fontWeight: 700, color: C.textMute, letterSpacing: "0.08em" }}>KNOWLEDGE BASE</div>
            {[
              { label: "PARC Report 2023-24",  file: "PARC Annual Report 2023-24_compressed.pdf" },
              { label: "FAO Crop Guidelines",  file: "i5550e.pdf" },
              { label: "Punjab Agri Rules",    file: "PbAgriDeptExtenAdapReseWing_SR_2007_20070612.pdf" },
            ].map(({ label, file }) => (
              <div key={file} onClick={() => window.open(`/api/pdf/${encodeURIComponent(file)}`, "_blank")}
                style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 12px 6px 18px", cursor: "pointer", color: C.textSub, fontSize: 12 }}>
                <Icon d={ICONS.book} size={13} stroke={C.textMute} />
                <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{label}</span>
                <span style={{ color: C.accentDim, fontSize: 10 }}>↗</span>
              </div>
            ))}
          </div>

          {/* User footer */}
          <div style={{ padding: "10px 14px", borderTop: `1px solid ${C.border}`, display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
            <div style={{ width: 30, height: 30, borderRadius: "50%", background: C.accentBg, border: `1px solid ${C.accent}44`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 700, color: C.accent }}>
              {username[0].toUpperCase()}
            </div>
            <span style={{ flex: 1, fontSize: 12, color: C.textSub, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{username}</span>
            {onLogout && (
              <button onClick={onLogout} title="Sign out" style={{ background: "none", border: "none", cursor: "pointer" }}>
                <Icon d={ICONS.x} size={14} stroke={C.textMute} />
              </button>
            )}
          </div>
        </div>

        {/* ══════════════════════════════════════════════════════════════════
            MAIN CHAT AREA
        ══════════════════════════════════════════════════════════════════ */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", minWidth: 0 }}>
          {/* Header */}
          <div style={{ padding: "0 16px", height: 52, display: "flex", alignItems: "center", gap: 10, background: C.surface, borderBottom: `1px solid ${C.border}`, flexShrink: 0 }}>
            {/* Feature 1: sidebar toggle button */}
            <button onClick={() => setSidebarOpen(o => !o)} title={sidebarOpen ? "Close sidebar" : "Open sidebar"}
              style={{ background: "none", border: `1px solid ${C.border}`, borderRadius: 7, padding: "5px 7px", cursor: "pointer", display: "flex", alignItems: "center", flexShrink: 0 }}>
              <Icon d={sidebarOpen ? ICONS.panelClose : ICONS.panelOpen} size={15} stroke={C.textSub} />
            </button>

            <span style={{ fontSize: 16 }}>🌾</span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <span style={{ fontSize: 14, fontWeight: 600, color: C.text }}>
                {activeSession ? activeSession.title : "Agricultural Knowledge Base"}
              </span>
              {activeSession?.projectId && (
                <span style={{ fontSize: 11, color: C.textMute, marginLeft: 8 }}>
                  · {projects.find(p => p.id === activeSession.projectId)?.name}
                </span>
              )}
            </div>

            {/* Feature 2: Tavily web search toggle */}
            <button onClick={() => setWebSearch(w => !w)}
              title={webSearch ? "Web search ON (Tavily) — click to disable" : "Web search OFF — click to enable Tavily"}
              style={{
                display: "flex", alignItems: "center", gap: 5, padding: "4px 10px", borderRadius: 20,
                background: webSearch ? C.tealBg : "transparent",
                border: `1px solid ${webSearch ? C.teal : C.border}`,
                cursor: "pointer", fontSize: 12, fontWeight: 600,
                color: webSearch ? C.teal : C.textMute,
                transition: "all 0.15s",
              }}>
              <div style={{ width: 7, height: 7, borderRadius: "50%", background: webSearch ? C.teal : C.textMute, boxShadow: webSearch ? `0 0 5px ${C.teal}` : "none", transition: "all 0.15s" }} />
              Web Search {webSearch ? "ON" : "OFF"}
            </button>

            {/* Feature 3: PDF export of current chat */}
            <StatusBadge chunks={chunkCount} />
            {activeSession && (
              <button
                onClick={() => exportChatAsPDF(activeSession.sessionId, activeSession.title, token)}
                title="Download professional PDF report with pipeline trace and sources"
                style={{ display: "flex", alignItems: "center", gap: 5, padding: "4px 10px", borderRadius: 8, background: "none", border: `1px solid ${C.border}`, cursor: "pointer", fontSize: 12, color: C.textSub, whiteSpace: "nowrap" }}>
                <Icon d={ICONS.pdf} size={13} stroke={C.textSub} />
                Save PDF
              </button>
            )}
            <button onClick={() => setShowTrace(t => !t)} title={showTrace ? "Hide trace" : "Show trace"}
              style={{ background: "none", border: `1px solid ${C.border}`, borderRadius: 6, padding: "4px 8px", cursor: "pointer", color: C.amber, fontSize: 12, display: "flex", alignItems: "center", gap: 5, whiteSpace: "nowrap" }}>
              <Icon d={ICONS.trace} size={13} stroke={C.amber} />
              Trace
            </button>
          </div>

          {/* Chat area */}
          <div ref={chatRef} style={{ flex: 1, overflowY: "auto", padding: "20px 24px", display: "flex", flexDirection: "column", gap: 16 }}>
            {!activeSession ? (
              <Welcome onSend={(p) => { openNewChat(null); setTimeout(() => sendMessage(p), 50); }} />
            ) : currentMessages.length === 0 ? (
              <Welcome onSend={sendMessage} />
            ) : (
              currentMessages.map((m, i) => (
                <Message key={i} role={m.role} content={m.content} ts={m.ts} usedRag={m.usedRag}
                  uploadedFile={m.uploadedFile}
                  sourceType={m.sourceType}
                  mcpTool={m.mcpTool}
                  sources={m.sources}
                  onRegenerate={m.role === "assistant" ? () => {
                    const prev = currentMessages.slice(0, i).reverse().find(x => x.role === "user");
                    if (prev) sendMessage(prev.content);
                  } : null}
                />
              ))
            )}
            {loading && <TypingDots />}
          </div>

          {/* Input (Feature 5: "+" file upload button) */}
          <div style={{ padding: "12px 20px 16px", borderTop: `1px solid ${C.border}`, background: C.surface, flexShrink: 0 }}>
            {!activeSession && (
              <div style={{ fontSize: 12, color: C.textMute, textAlign: "center", marginBottom: 8 }}>
                Click <strong style={{ color: C.accent }}>+ New chat</strong> or select a conversation to start.
              </div>
            )}

            {/* Pending file badge */}
            {pendingFile && (
              <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 8, padding: "5px 10px", background: C.accentBg, border: `1px solid ${C.accentDim}`, borderRadius: 8, width: "fit-content" }}>
                <Icon d={ICONS.attach} size={12} stroke={C.accent} />
                <span style={{ fontSize: 12, color: C.accent, fontWeight: 500 }}>{pendingFile.name}</span>
                <span style={{ fontSize: 11, color: C.textSub }}>will be used in next message</span>
                <button onClick={() => setPendingFile(null)} style={{ background: "none", border: "none", cursor: "pointer", padding: 0, marginLeft: 4 }}>
                  <Icon d={ICONS.x} size={11} stroke={C.textSub} />
                </button>
              </div>
            )}

            {uploadingFile && (
              <div style={{ fontSize: 12, color: C.teal, marginBottom: 8 }}>⏳ Uploading document…</div>
            )}

            <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
              {/* Feature 5: file upload "+" button */}
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={!activeSession || uploadingFile}
                title="Attach a document (PDF, TXT, DOCX) to your message"
                style={{
                  width: 38, height: 38, borderRadius: 9, border: `1px solid ${C.border}`,
                  background: C.surface2, cursor: activeSession ? "pointer" : "not-allowed",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  flexShrink: 0, alignSelf: "flex-end",
                  opacity: activeSession ? 1 : 0.4, transition: "all 0.15s",
                  color: pendingFile ? C.accent : C.textSub,
                }}
                onMouseEnter={e => { if (activeSession) e.currentTarget.style.borderColor = C.accent; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; }}>
                <Icon d={ICONS.attach} size={15} stroke={pendingFile ? C.accent : C.textSub} />
              </button>
              <input ref={fileInputRef} type="file" accept=".pdf,.txt,.docx,.csv,.md"
                style={{ display: "none" }} onChange={handleFileSelect} />

              <div style={{ flex: 1, background: C.surface2, border: `1px solid ${activeSession ? C.borderHi : C.border}`, borderRadius: 10, padding: "10px 14px" }}>
                <textarea ref={textareaRef} rows={2} value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
                  placeholder={
                    !activeSession ? "Select or create a chat first" :
                    webSearch ? "Ask anything — web search is ON (Tavily)… (Enter to send)" :
                    "Ask about crops, diseases, PARC activities… (Enter to send)"
                  }
                  disabled={!activeSession}
                  style={{ width: "100%", background: "transparent", border: "none", outline: "none", color: C.text, fontSize: 14, fontFamily: "inherit", resize: "none", lineHeight: 1.5 }} />
              </div>
              <button onClick={() => sendMessage()} disabled={loading || !input.trim() || !activeSession}
                style={{ width: 42, height: 42, borderRadius: 10, border: "none", background: C.accent, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", alignSelf: "flex-end", flexShrink: 0, opacity: (loading || !input.trim() || !activeSession) ? 0.4 : 1, transition: "opacity 0.15s" }}>
                <Icon d={ICONS.send} size={16} stroke="#fff" />
              </button>
            </div>
          </div>
        </div>

        {/* ══════════════════════════════════════════════════════════════════
            TRACE PANEL (collapsible)
        ══════════════════════════════════════════════════════════════════ */}
        {showTrace && (
          <div style={{ width: 290, background: C.surface, borderLeft: `1px solid ${C.border}`, display: "flex", flexDirection: "column", overflow: "hidden", flexShrink: 0 }}>
            <TracePanel
              trace={trace}
              status={status}
              statusError={statusError}
            />
          </div>
        )}
      </div>

      {/* ── Modals ───────────────────────────────────────────────────────── */}

      {/* New Project */}
      <Modal open={showNewProject} onClose={() => setShowNewProject(false)} title="Create new project">
        <div style={{ marginBottom: 14 }}>
          <label style={{ fontSize: 12, color: C.textSub, display: "block", marginBottom: 6 }}>Icon</label>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {EMOJIS.map(e => (
              <button key={e} onClick={() => setNewProjEmoji(e)}
                style={{ fontSize: 20, padding: "4px 8px", borderRadius: 8, cursor: "pointer", border: `1px solid ${newProjEmoji === e ? C.accent : C.border}`, background: newProjEmoji === e ? C.accentBg : C.surface2, fontFamily: "inherit" }}>
                {e}
              </button>
            ))}
          </div>
        </div>
        <TextInput label="Project name" value={newProjName} onChange={setNewProjName} placeholder="e.g. Wheat Disease Research" autoFocus />
        <TextInput label="Description (optional)" value={newProjDesc} onChange={setNewProjDesc} placeholder="What is this project about?" multiline />
        <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", marginTop: 4 }}>
          <Btn onClick={() => setShowNewProject(false)}>Cancel</Btn>
          <Btn variant="primary" onClick={createProject} disabled={!newProjName.trim()}>Create project</Btn>
        </div>
      </Modal>

      {/* Feature 4: Rename modal (sessions + projects) */}
      <Modal open={showRename} onClose={() => { setShowRename(false); setRenameTarget(null); }}
        title={`Rename ${renameTarget?.type === "project" ? "project" : "conversation"}`} width={400}>
        <TextInput label="New name" value={renameName} onChange={setRenameName}
          placeholder={renameTarget?.type === "project" ? "Project name" : "Conversation title"}
          autoFocus />
        <div style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
          <Btn onClick={() => { setShowRename(false); setRenameTarget(null); }}>Cancel</Btn>
          <Btn variant="primary" onClick={commitRename} disabled={!renameName.trim()}>Save</Btn>
        </div>
      </Modal>

      {/* Delete confirm */}
      <Modal open={showDeleteConfirm} onClose={() => { setShowDeleteConfirm(false); setDeleteTarget(null); }} title="Confirm deletion" width={380}>
        <div style={{ fontSize: 13, color: C.textSub, marginBottom: 20, lineHeight: 1.6 }}>
          Delete <strong style={{ color: C.text }}>{deleteTarget?.name}</strong>? This will remove all its chats and data.
        </div>
        <div style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
          <Btn onClick={() => { setShowDeleteConfirm(false); setDeleteTarget(null); }}>Cancel</Btn>
          <button onClick={() => { if (deleteTarget?.type === "project") deleteProject(deleteTarget.id); }}
            style={{ padding: "7px 14px", borderRadius: 8, background: C.danger, color: "#fff", border: "none", cursor: "pointer", fontWeight: 600, fontSize: 13, fontFamily: "inherit" }}>
            Delete
          </button>
        </div>
      </Modal>
    </>
  );
}
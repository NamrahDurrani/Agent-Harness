// import { useState, useRef, useEffect } from "react";

// // ── Palette ────────────────────────────────────────────────────────────────────
// const C = {
//   bg:        "#0c1108",
//   surface:   "#141c0f",
//   surface2:  "#1c2614",
//   border:    "#2a3d1e",
//   borderHi:  "#3d5a2a",
//   accent:    "#7ab648",
//   accentDim: "#4a7a1e",
//   amber:     "#e8a020",
//   amberDim:  "#7a4e00",
//   text:      "#dde8cc",
//   textSub:   "#7a9460",
//   textMute:  "#4a6035",
//   userBub:   "#1a2e10",
//   botBub:    "#0f1a08",
//   danger:    "#c0392b",
// };

// // ── Icons ─────────────────────────────────────────────────────────────────────
// const Icon = ({ d, size = 18, stroke = C.textSub }) => (
//   <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
//     stroke={stroke} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
//     <path d={d} />
//   </svg>
// );

// const Icons = {
//   send:       "M22 2L11 13M22 2L15 22l-4-9-9-4 20-7z",
//   reset:      "M1 4v6h6M23 20v-6h-6M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15",
//   trace:      "M3 3h18v18H3zM9 9h6M9 13h6M9 17h4",
//   bot:        "M12 2a4 4 0 0 1 4 4v2h2a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2V6a4 4 0 0 1 4-4zM9 10H7v2h2v-2zm8 0h-2v2h2v-2zm-5 4h-2v2h2v-2z",
//   user:       "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
//   copy:       "M20 9H11a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2v-9a2 2 0 0 0-2-2zM5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1",
//   check:      "M20 6L9 17l-5-5",
//   snapshot:   "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H8",
//   trash:      "M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2",
//   thumbUp:    "M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3",
//   thumbDown:  "M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zM17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17",
//   share:      "M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8M16 6l-4-4-4 4M12 2v13",
//   regenerate: "M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15",
//   sources:    "M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2zM22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z",
//   chevLeft:   "M15 18l-6-6 6-6",
//   chevRight:  "M9 18l6-6-6-6",
// };

// // ── Styles ─────────────────────────────────────────────────────────────────────
// const S = {
//   app: {
//     display: "grid",
//     gridTemplateColumns: "260px 1fr 300px",
//     gridTemplateRows: "56px 1fr",
//     height: "100vh",
//     background: C.bg,
//     color: C.text,
//     fontFamily: "'Inter', 'Segoe UI', system-ui, sans-serif",
//     fontSize: 14,
//     overflow: "hidden",
//   },
//   header: {
//     gridColumn: "1 / -1",
//     display: "flex",
//     alignItems: "center",
//     gap: 12,
//     padding: "0 24px",
//     background: C.surface,
//     borderBottom: `1px solid ${C.border}`,
//   },
//   sidebar: {
//     background: C.surface,
//     borderRight: `1px solid ${C.border}`,
//     display: "flex",
//     flexDirection: "column",
//     padding: 16,
//     gap: 8,
//     overflowY: "auto",
//   },
//   main: { display: "flex", flexDirection: "column", overflow: "hidden" },
//   tracePanel: {
//     background: C.surface,
//     borderLeft: `1px solid ${C.border}`,
//     display: "flex",
//     flexDirection: "column",
//     overflow: "hidden",
//   },
//   chatArea: {
//     flex: 1,
//     overflowY: "auto",
//     padding: "20px 24px",
//     display: "flex",
//     flexDirection: "column",
//     gap: 16,
//   },
//   inputRow: {
//     display: "flex",
//     gap: 10,
//     padding: "12px 20px 16px",
//     borderTop: `1px solid ${C.border}`,
//     background: C.surface,
//   },
//   textarea: {
//     flex: 1,
//     background: C.surface2,
//     border: `1px solid ${C.border}`,
//     borderRadius: 10,
//     color: C.text,
//     padding: "10px 14px",
//     fontSize: 14,
//     resize: "none",
//     outline: "none",
//     fontFamily: "inherit",
//     lineHeight: 1.5,
//     transition: "border-color 0.2s",
//   },
//   sendBtn: {
//     width: 42, height: 42, borderRadius: 10, border: "none",
//     background: C.accent, cursor: "pointer",
//     display: "flex", alignItems: "center", justifyContent: "center",
//     alignSelf: "flex-end", flexShrink: 0,
//     transition: "opacity 0.15s, transform 0.1s",
//   },
//   headerBtn: {
//     background: C.surface2, border: `1px solid ${C.border}`,
//     borderRadius: 8, padding: "5px 10px", color: C.textSub,
//     cursor: "pointer", fontSize: 12, display: "flex",
//     alignItems: "center", gap: 5,
//   },
// };

// // ── PDF snapshot ───────────────────────────────────────────────────────────────
// // Pure browser approach — no library needed.
// // Builds a print-friendly HTML page in a hidden iframe and triggers window.print().
// // The page uses @media print to render cleanly as PDF when the user picks
// // "Save as PDF" in the print dialog (works in Chrome, Edge, Firefox).
// function saveAsPDF(messages, chunkCount) {
//   if (messages.length === 0) {
//     alert("Nothing to save — start a conversation first.");
//     return;
//   }

//   const date = new Date().toLocaleString();

//   // Build message rows HTML
//   const rows = messages.map(m => {
//     const isUser = m.role === "user";
//     const label  = isUser ? "You" : "RAG Assistant";
//     const color  = isUser ? "#2d5a1b" : "#1a3a0a";
//     const border = isUser ? "#4a7a1e" : "#2a3d1e";
//     const align  = isUser ? "right" : "left";
//     const mlAuto = isUser ? "auto" : "0";
//     const mrAuto = isUser ? "0" : "auto";

//     return `
//       <div style="margin-bottom:18px; text-align:${align}">
//         <div style="font-size:11px; color:#7a9460; margin-bottom:4px;">
//           ${label} · ${m.ts}
//         </div>
//         <div style="
//           display:inline-block; max-width:75%;
//           background:${color}; border:1px solid ${border};
//           border-radius:12px; padding:10px 14px;
//           font-size:13px; line-height:1.7; color:#dde8cc;
//           white-space:pre-wrap; word-break:break-word;
//           margin-left:${mlAuto}; margin-right:${mrAuto};
//           text-align:left;
//         ">${escHtml(m.content)}</div>
//       </div>`;
//   }).join("");

//   const html = `<!DOCTYPE html>
// <html lang="en">
// <head>
//   <meta charset="UTF-8"/>
//   <title>RAG Conversation Snapshot</title>
//   <style>
//     @page { size: A4; margin: 20mm 18mm; }
//     * { box-sizing: border-box; margin:0; padding:0; }
//     body {
//       background: #0c1108;
//       color: #dde8cc;
//       font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
//       font-size: 13px;
//       padding: 0;
//     }
//     .cover {
//       border-bottom: 1px solid #2a3d1e;
//       padding-bottom: 16px;
//       margin-bottom: 24px;
//     }
//     .cover h1 {
//       font-size: 20px; font-weight: 700; color: #dde8cc;
//       letter-spacing: -0.02em; margin-bottom: 6px;
//     }
//     .cover .meta {
//       font-size: 11px; color: #7a9460; display:flex; gap: 20px;
//     }
//     .meta span { display:flex; align-items:center; gap:4px; }
//     .messages { padding-top: 4px; }
//     @media print {
//       body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
//     }
//   </style>
// </head>
// <body>
//   <div class="cover">
//     <h1>🌾 Agricultural RAG — Conversation Snapshot</h1>
//     <div class="meta">
//       <span>📅 ${date}</span>
//       <span>💬 ${messages.length} messages</span>
//       <span>📦 ${chunkCount.toLocaleString()} chunks indexed</span>
//     </div>
//   </div>
//   <div class="messages">${rows}</div>
// </body>
// </html>`;

//   // Open in a hidden iframe and trigger print
//   let iframe = document.getElementById("__snapshot_iframe__");
//   if (!iframe) {
//     iframe = document.createElement("iframe");
//     iframe.id = "__snapshot_iframe__";
//     iframe.style.cssText = "position:fixed;width:0;height:0;border:none;top:-9999px;left:-9999px;";
//     document.body.appendChild(iframe);
//   }

//   iframe.srcdoc = html;
//   iframe.onload = () => {
//     setTimeout(() => {
//       iframe.contentWindow.focus();
//       iframe.contentWindow.print();
//     }, 300);
//   };
// }

// function escHtml(str) {
//   return str
//     .replace(/&/g, "&amp;")
//     .replace(/</g, "&lt;")
//     .replace(/>/g, "&gt;")
//     .replace(/"/g, "&quot;");
// }

// // ── Status badge ──────────────────────────────────────────────────────────────
// function StatusBadge({ chunks }) {
//   const ok = chunks > 0;
//   return (
//     <div style={{
//       display:"flex", alignItems:"center", gap:6,
//       padding:"4px 10px", borderRadius:20,
//       background: ok ? "#1a3310" : "#3a1010",
//       border:`1px solid ${ok ? C.accentDim : C.danger}`,
//       fontSize:12, color: ok ? C.accent : "#e74c3c",
//     }}>
//       <div style={{
//         width:7, height:7, borderRadius:"50%",
//         background: ok ? C.accent : C.danger,
//         boxShadow: ok ? `0 0 6px ${C.accent}` : "none",
//       }} />
//       {ok ? `${chunks.toLocaleString()} chunks` : "Empty — index first"}
//     </div>
//   );
// }

// // ── Sidebar helpers ───────────────────────────────────────────────────────────
// function SidebarSection({ title, children }) {
//   return (
//     <div style={{ marginBottom:8 }}>
//       <div style={{ fontSize:11, fontWeight:600, letterSpacing:"0.08em",
//         textTransform:"uppercase", color:C.textMute, marginBottom:8, padding:"0 4px" }}>
//         {title}
//       </div>
//       {children}
//     </div>
//   );
// }
// function SidebarItem({ label, value, accent }) {
//   // Long values (e.g. "BM25 + Sentence Embeddings") wrap to two lines.
//   // A simple row layout with space-between then vertically centers the
//   // short label against the wrapped value and visually overlaps it.
//   // Stack label above value instead whenever the value is long, so both
//   // always have their own line and never collide.
//   const valueStr = String(value ?? "");
//   const isLong = valueStr.length > 14;

//   if (isLong) {
//     return (
//       <div style={{
//         padding:"6px 10px", borderRadius:8, background:C.surface2, marginBottom:4,
//       }}>
//         <div style={{ color:C.textSub, fontSize:11, marginBottom:2 }}>{label}</div>
//         <div style={{ color:accent||C.text, fontSize:12, fontWeight:500, lineHeight:1.4 }}>
//           {value}
//         </div>
//       </div>
//     );
//   }

//   return (
//     <div style={{
//       display:"flex", justifyContent:"space-between", alignItems:"center",
//       padding:"6px 10px", borderRadius:8, background:C.surface2, marginBottom:4,
//     }}>
//       <span style={{ color:C.textSub, fontSize:12 }}>{label}</span>
//       <span style={{ color:accent||C.text, fontSize:12, fontWeight:500 }}>{value}</span>
//     </div>
//   );
// }

// // ── Citation renderer ─────────────────────────────────────────────────────────
// // Parses the LLM's structured output into:
// //   - Inline [N] citation superscripts (clickable, jump to source)
// //   - SOURCES section as numbered clickable links that open the PDF at the page
// //   - Web search sources as amber-coloured external links

// function parseSources(content) {
//   const sourcesMatch = content.match(/SOURCES:\s*\n([\s\S]+)$/i);
//   const mainText = sourcesMatch
//     ? content.slice(0, content.indexOf(sourcesMatch[0])).trim()
//     : content;

//   const sources = [];
//   if (sourcesMatch) {
//     const lines = sourcesMatch[1].trim().split("\n").filter(Boolean);
//     lines.forEach(line => {
//       // Match [N] FILENAME | Page X
//       const docMatch = line.match(/\[(\d+)\]\s*(.+?)\s*\|\s*[Pp]age\s*(\d+)/);
//       if (docMatch) {
//         sources.push({
//           num:      parseInt(docMatch[1]),
//           filename: docMatch[2].trim(),
//           page:     parseInt(docMatch[3]),
//           type:     "document",
//         });
//         return;
//       }
//       // Match [Web N] Title — URL
//       const webMatch = line.match(/\[Web\s*(\d+)\]\s*(.+?)\s*—\s*(https?:\/\/\S+)/);
//       if (webMatch) {
//         sources.push({
//           num:   parseInt(webMatch[1]),
//           title: webMatch[2].trim(),
//           url:   webMatch[3].trim(),
//           type:  "web",
//         });
//       }
//     });
//   }
//   return { mainText, sources };
// }

// function renderTextWithCitations(text, sources, onCiteClick) {
//   // Split on [N] or [Web N] patterns and render superscript badges
//   const parts = text.split(/(\[(?:Web\s*)?\d+\])/g);
//   return parts.map((part, i) => {
//     const match = part.match(/^\[(?:Web\s*)?(\d+)\]$/);
//     if (match) {
//       const num = parseInt(match[1]);
//       const isWeb = part.toLowerCase().includes("web");
//       const src = sources.find(s => s.num === num && (isWeb ? s.type === "web" : s.type === "document"))
//                || sources.find(s => s.num === num);
//       return (
//         <sup key={i}
//           onClick={() => src && onCiteClick(src)}
//           title={src ? (src.type === "document"
//             ? `${src.filename} — Page ${src.page}`
//             : src.title) : ""}
//           style={{
//             cursor: src ? "pointer" : "default",
//             color: src ? (src.type === "web" ? C.amber : C.accent) : C.textMute,
//             fontWeight: 700, fontSize: "0.72em",
//             marginLeft: 1, padding: "1px 4px", borderRadius: 3,
//             background: src ? (src.type === "web" ? "#2a1e00" : "#16301a") : "transparent",
//             border: src ? `1px solid ${src.type === "web" ? C.amberDim : C.accentDim}` : "none",
//             userSelect: "none",
//           }}
//         >
//           {part}
//         </sup>
//       );
//     }
//     // Normal text — preserve newlines
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
//   const openSource = (src) => {
//     if (src.type === "document") {
//       // Opens PDF via FastAPI endpoint — browser PDF viewer honours #page=N
//       window.open(
//         `/api/pdf/${encodeURIComponent(src.filename)}#page=${src.page}`,
//         "_blank"
//       );
//     } else {
//       window.open(src.url, "_blank");
//     }
//   };

//   if (!sources.length) return null;

//   return (
//     <div style={{
//       marginTop: 12, paddingTop: 10,
//       borderTop: `1px solid ${C.border}`,
//     }}>
//       <div style={{
//         fontSize: 10, fontWeight: 700, letterSpacing: "0.08em",
//         textTransform: "uppercase", color: C.textMute, marginBottom: 6,
//       }}>
//         References
//       </div>
//       {sources.map((src, i) => (
//         <div key={i}
//           onClick={() => openSource(src)}
//           style={{
//             display: "flex", alignItems: "flex-start", gap: 7,
//             marginBottom: 5, cursor: "pointer",
//             padding: "5px 7px", borderRadius: 7,
//             transition: "background 0.15s",
//           }}
//           onMouseEnter={e => e.currentTarget.style.background = C.surface2}
//           onMouseLeave={e => e.currentTarget.style.background = "transparent"}
//         >
//           {/* Badge number */}
//           <span style={{
//             minWidth: 20, height: 20, borderRadius: 4, flexShrink: 0,
//             background: src.type === "document" ? C.accentDim : C.amberDim,
//             border: `1px solid ${src.type === "document" ? C.accent : C.amber}`,
//             display: "flex", alignItems: "center", justifyContent: "center",
//             fontSize: 9, fontWeight: 700,
//             color: src.type === "document" ? C.accent : C.amber,
//           }}>
//             {src.num}
//           </span>
//           {/* Label */}
//           <div style={{ fontSize: 11.5, color: C.textSub, lineHeight: 1.5 }}>
//             {src.type === "document" ? (
//               <>
//                 <span style={{ color: C.text, fontWeight: 500 }}>{src.filename}</span>
//                 <span style={{ color: C.textMute }}> — Page {src.page}</span>
//                 <span style={{ color: C.accentDim, fontSize: 10, marginLeft: 5 }}>↗ open PDF</span>
//               </>
//             ) : (
//               <>
//                 <span style={{ color: C.text, fontWeight: 500 }}>{src.title}</span>
//                 <span style={{ color: C.amberDim, fontSize: 10, marginLeft: 5 }}>↗ web</span>
//               </>
//             )}
//           </div>
//         </div>
//       ))}
//     </div>
//   );
// }

// // ── Message bubble ────────────────────────────────────────────────────────────
// function Message({ role, content, ts, usedRag, onRegenerate }) {
//   const [copied, setCopied]         = useState(false);
//   const [liked, setLiked]           = useState(null);   // null | "up" | "down"
//   const [showSources, setShowSources] = useState(true);
//   const isUser = role === "user";

//   const copyText = () => {
//     navigator.clipboard.writeText(content);
//     setCopied(true);
//     setTimeout(() => setCopied(false), 1500);
//   };

//   const ragBadge = !isUser && usedRag !== null && usedRag !== undefined && (
//     <span style={{
//       display:"inline-flex", alignItems:"center", gap:4,
//       fontSize:9.5, fontWeight:600, letterSpacing:"0.03em",
//       padding:"2px 7px", borderRadius:20,
//       background: usedRag ? "#16301a" : "#2a2210",
//       border: `1px solid ${usedRag ? C.accentDim : C.amberDim}`,
//       color: usedRag ? C.accent : C.amber,
//       marginLeft: 6,
//     }}>
//       {usedRag ? "RAG" : "🌐 Web"}
//     </span>
//   );

//   // GPT-style icon button helper
//   const ActionBtn = ({ icon, title, onClick, active, activeColor }) => (
//     <button onClick={onClick} title={title} style={{
//       background: "none", border: "none", cursor: "pointer",
//       padding: "4px 5px", borderRadius: 6, display:"flex", alignItems:"center",
//       opacity: 0.55, transition:"opacity 0.15s, background 0.15s",
//     }}
//       onMouseEnter={e => { e.currentTarget.style.opacity="1"; e.currentTarget.style.background=C.surface2; }}
//       onMouseLeave={e => { e.currentTarget.style.opacity="0.55"; e.currentTarget.style.background="none"; }}
//     >
//       <Icon d={icon} size={14} stroke={active ? (activeColor||C.accent) : C.textSub} />
//     </button>
//   );

//   return (
//     <div style={{ display:"flex", flexDirection:"column",
//       alignItems: isUser ? "flex-end" : "flex-start", gap:4 }}>
//       <div style={{ display:"flex", alignItems:"center", gap:6,
//         flexDirection: isUser ? "row-reverse" : "row" }}>
//         <div style={{
//           width:26, height:26, borderRadius:"50%",
//           background: isUser ? C.accentDim : "#1a2610",
//           border:`1px solid ${isUser ? C.accent : C.border}`,
//           display:"flex", alignItems:"center", justifyContent:"center", flexShrink:0,
//         }}>
//           <Icon d={isUser ? Icons.user : Icons.bot} size={13}
//             stroke={isUser ? C.accent : C.textSub} />
//         </div>
//         <span style={{ fontSize:11, color:C.textMute, display:"flex", alignItems:"center" }}>
//           {isUser ? "You" : "RAG Assistant"} · {ts}
//           {ragBadge}
//         </span>
//       </div>

//       <div style={{
//         maxWidth:"78%",
//         background: isUser ? C.userBub : C.botBub,
//         border:`1px solid ${isUser ? C.accentDim : C.border}`,
//         borderRadius: isUser ? "14px 4px 14px 14px" : "4px 14px 14px 14px",
//         padding:"10px 14px", lineHeight:1.65, fontSize:14, color:C.text,
//       }}>
//         {isUser ? (
//           <span style={{ whiteSpace:"pre-wrap", wordBreak:"break-word" }}>{content}</span>
//         ) : (() => {
//           const { mainText, sources } = parseSources(content);
//           const onCiteClick = (src) => {
//             if (src.type === "document") {
//               window.open(`/api/pdf/${encodeURIComponent(src.filename)}#page=${src.page}`, "_blank");
//             } else {
//               window.open(src.url, "_blank");
//             }
//           };
//           return (
//             <>
//               <div style={{ whiteSpace:"pre-wrap", wordBreak:"break-word" }}>
//                 {renderTextWithCitations(mainText, sources, onCiteClick)}
//               </div>
//               {showSources && <SourcesList sources={sources} />}
//             </>
//           );
//         })()}
//       </div>

//       {/* ── GPT-style action icon bar (assistant messages only) ─────────── */}
//       {!isUser && (
//         <div style={{
//           display:"flex", alignItems:"center", gap:1,
//           paddingLeft:4, marginTop:-2,
//         }}>
//           <ActionBtn icon={copied ? Icons.check : Icons.copy}
//             title="Copy" onClick={copyText}
//             active={copied} activeColor={C.accent} />
//           <ActionBtn icon={Icons.thumbUp}
//             title="Good response" onClick={() => setLiked(l => l==="up" ? null : "up")}
//             active={liked==="up"} activeColor={C.accent} />
//           <ActionBtn icon={Icons.thumbDown}
//             title="Bad response" onClick={() => setLiked(l => l==="down" ? null : "down")}
//             active={liked==="down"} activeColor={C.danger} />
//           <ActionBtn icon={Icons.share}
//             title="Share" onClick={() => {
//               const txt = `Q: ${content.slice(0,120)}…`;
//               navigator.clipboard.writeText(txt);
//             }} />
//           {onRegenerate && (
//             <ActionBtn icon={Icons.regenerate}
//               title="Regenerate response" onClick={onRegenerate} />
//           )}
//           {/* Separator */}
//           <div style={{ width:1, height:14, background:C.border, margin:"0 3px" }} />
//           <ActionBtn icon={Icons.sources}
//             title={showSources ? "Hide sources" : "Show sources"}
//             onClick={() => setShowSources(s => !s)}
//             active={showSources} activeColor={C.accent} />
//         </div>
//       )}
//     </div>
//   );
// }

// // ── Typing indicator ──────────────────────────────────────────────────────────
// function TypingDots() {
//   return (
//     <div style={{ display:"flex", alignItems:"flex-start", gap:6 }}>
//       <div style={{
//         width:26, height:26, borderRadius:"50%",
//         background:"#1a2610", border:`1px solid ${C.border}`,
//         display:"flex", alignItems:"center", justifyContent:"center", flexShrink:0,
//       }}>
//         <Icon d={Icons.bot} size={13} stroke={C.textSub} />
//       </div>
//       <div style={{
//         background:C.botBub, border:`1px solid ${C.border}`,
//         borderRadius:"4px 14px 14px 14px", padding:"12px 16px",
//         display:"flex", gap:5, alignItems:"center",
//       }}>
//         {[0, 0.18, 0.36].map((delay, i) => (
//           <div key={i} style={{
//             width:7, height:7, borderRadius:"50%", background:C.accentDim,
//             animation:"pulse 1.2s ease-in-out infinite",
//             animationDelay:`${delay}s`,
//           }} />
//         ))}
//       </div>
//     </div>
//   );
// }

// // ── Trace panel ───────────────────────────────────────────────────────────────
// function TracePanel({ trace }) {
//   return (
//     <div style={{ display:"flex", flexDirection:"column", height:"100%", overflow:"hidden" }}>
//       <div style={{
//         padding:"14px 16px 10px", borderBottom:`1px solid ${C.border}`,
//         display:"flex", alignItems:"center", gap:8,
//       }}>
//         <Icon d={Icons.trace} size={15} stroke={C.amber} />
//         <span style={{ fontSize:13, fontWeight:600, color:C.amber }}>Pipeline trace</span>
//       </div>
//       <div style={{ flex:1, overflowY:"auto", padding:"12px 14px" }}>
//         {!trace ? (
//           <div style={{ color:C.textMute, fontSize:12, textAlign:"center",
//             marginTop:40, lineHeight:1.7 }}>
//             Pipeline step timings<br/>appear here after each query
//           </div>
//         ) : (
//           <pre style={{
//             fontFamily:"'JetBrains Mono','Fira Code',monospace",
//             fontSize:11, color:C.textSub, lineHeight:1.75,
//             whiteSpace:"pre-wrap", wordBreak:"break-word", margin:0,
//           }}>
//             {trace}
//           </pre>
//         )}
//       </div>
//     </div>
//   );
// }

// // ── Welcome screen ────────────────────────────────────────────────────────────
// function Welcome({ onSend }) {
//   const prompts = [
//     "What wheat diseases are monitored in Punjab?",
//     "Summarise PARC's 2023-24 research highlights",
//     "What is the role of the Agriculture Extension Wing?",
//     "Which FAO guidelines cover Ug99 rust?",
//   ];
//   return (
//     <div style={{ flex:1, display:"flex", flexDirection:"column",
//       alignItems:"center", justifyContent:"center", padding:32, gap:28 }}>
//       <div style={{ textAlign:"center" }}>
//         <div style={{ fontSize:40, marginBottom:12 }}>🌾</div>
//         <div style={{ fontSize:22, fontWeight:700, color:C.text,
//           letterSpacing:"-0.02em", marginBottom:6 }}>
//           Agricultural RAG Assistant
//         </div>
//         <div style={{ fontSize:13, color:C.textSub, maxWidth:380, lineHeight:1.6 }}>
//           Ask about PARC Annual Report 2023-24, FAO Crop Monitoring
//           Guidelines, or Punjab Agriculture Rules.
//         </div>
//       </div>
//       <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr",
//         gap:10, width:"100%", maxWidth:560 }}>
//         {prompts.map((p, i) => (
//           <button key={i} onClick={() => onSend(p)} style={{
//             background:C.surface2, border:`1px solid ${C.border}`,
//             borderRadius:10, padding:"10px 14px", color:C.textSub,
//             fontSize:12, textAlign:"left", cursor:"pointer", lineHeight:1.5,
//             transition:"border-color 0.15s, color 0.15s",
//           }}
//             onMouseEnter={e => { e.currentTarget.style.borderColor=C.accent; e.currentTarget.style.color=C.text; }}
//             onMouseLeave={e => { e.currentTarget.style.borderColor=C.border; e.currentTarget.style.color=C.textSub; }}
//           >
//             {p}
//           </button>
//         ))}
//       </div>
//     </div>
//   );
// }

// // ── Snapshot toast ────────────────────────────────────────────────────────────
// function Toast({ show }) {
//   return (
//     <div style={{
//       position:"fixed", bottom:28, left:"50%", transform:`translateX(-50%) translateY(${show?0:20}px)`,
//       opacity: show ? 1 : 0, transition:"all 0.25s ease",
//       background:C.surface2, border:`1px solid ${C.accent}`,
//       borderRadius:10, padding:"9px 18px",
//       fontSize:13, color:C.accent, fontWeight:500,
//       display:"flex", alignItems:"center", gap:8,
//       pointerEvents:"none", zIndex:9999,
//       boxShadow:`0 4px 20px rgba(0,0,0,0.5)`,
//     }}>
//       <Icon d={Icons.check} size={14} stroke={C.accent} />
//       Print dialog opened — choose "Save as PDF"
//     </div>
//   );
// }

// // ── Backend label normalizer ───────────────────────────────────────────────────
// // The /api/status backend field reflects whatever LLM_BACKEND env var is set
// // in whichever terminal launched api_server.py. If that terminal session
// // forgot to set it, it silently falls back to "GROQ". Since this project
// // only uses Qwen, never surface Groq in the UI — show a clear "not
// // configured" state instead so it's obvious something needs fixing,
// // rather than quietly displaying the wrong provider.
// function normalizeBackendLabel(rawBackend, model) {
//   if (!rawBackend) return { label: "—", isGroqLeak: false };
//   const upper = rawBackend.toUpperCase();
//   if (upper === "GROQ") {
//     return { label: "⚠ Not set to Qwen", isGroqLeak: true };
//   }
//   if (upper.startsWith("QWEN")) {
//     return { label: model || "Qwen", isGroqLeak: false };
//   }
//   return { label: rawBackend, isGroqLeak: false };
// }

// // ── Main app ──────────────────────────────────────────────────────────────────
// export default function App() {
//   const [messages, setMessages]     = useState([]);
//   const [input, setInput]           = useState("");
//   const [loading, setLoading]       = useState(false);
//   const [trace, setTrace]           = useState(null);
//   const [chunkCount, setChunkCount] = useState(0);
//   const [toast, setToast]           = useState(false);
//   const [sessionId]                 = useState(() => crypto.randomUUID());
//   const [status, setStatus]         = useState(null);
//   const [statusError, setStatusError] = useState(null);
//   const [pastSessions, setPastSessions] = useState([]);
//   const [historyLoading, setHistoryLoading] = useState(true);
//   const [editingSessionId, setEditingSessionId] = useState(null);
//   const [editingTitle, setEditingTitle]         = useState("");
//   const [exportMenuFor, setExportMenuFor]       = useState(null);
//   const [leftOpen, setLeftOpen]     = useState(true);   // left sidebar toggle
//   const [rightOpen, setRightOpen]   = useState(true);   // right panel toggle
//   const chatRef     = useRef(null);
//   const textareaRef = useRef(null);

//   const backendInfo = normalizeBackendLabel(status?.backend, status?.model);

//   useEffect(() => {
//     if (chatRef.current)
//       chatRef.current.scrollTop = chatRef.current.scrollHeight;
//   }, [messages, loading]);

//   // Poll /api/status so the sidebar always reflects what the backend is
//   // ACTUALLY doing — never a hardcoded guess. Refreshes every 8s so a
//   // freshly-indexed vector store or backend swap shows up without reload.
//   useEffect(() => {
//     const fetchStatus = () => {
//       fetch("/api/status")
//         .then(r => r.json())
//         .then(d => {
//           setStatus(d);
//           setChunkCount(d.chunk_count || 0);
//           setStatusError(d.vector_store_error || d.pipeline_error || null);
//         })
//         .catch(err => {
//           setStatusError(`Cannot reach API server: ${err.message}`);
//           setChunkCount(0);
//         });
//     };
//     fetchStatus();
//     const id = setInterval(fetchStatus, 8000);
//     return () => clearInterval(id);
//   }, []);

//   // ── Chat history: load list, load one session, delete one session ───────────
//   const fetchSessionList = () => {
//     fetch("/api/sessions")
//       .then(r => r.json())
//       .then(d => setPastSessions(d.sessions || []))
//       .catch(() => {})
//       .finally(() => setHistoryLoading(false));
//   };

//   useEffect(() => {
//     fetchSessionList();
//   }, []);

//   const loadSession = (sid) => {
//     fetch(`/api/sessions/${sid}`)
//       .then(r => r.json())
//       .then(d => {
//         const loaded = (d.messages || []).map(m => ({
//           role: m.role,
//           content: m.content,
//           ts: m.ts ? new Date(m.ts).toLocaleTimeString([], { hour:"2-digit", minute:"2-digit" }) : "",
//           usedRag: m.used_rag,   // backend already returns this per-message for assistant turns
//         }));
//         setMessages(loaded);
//         setTrace(null);
//         // Note: continuing to chat will append to a NEW session id client-side,
//         // since this app generates one session id per page load. The loaded
//         // history is still viewable/exportable, but new replies start a fresh
//         // session row in the DB.
//       })
//       .catch(() => {});
//   };

//   const deleteSession = (sid) => {
//     if (!confirm("Delete this conversation permanently?")) return;
//     fetch(`/api/sessions/${sid}`, { method: "DELETE" })
//       .then(() => fetchSessionList())
//       .catch(() => {});
//   };
  
// const startRename = (s) => {
//   setEditingSessionId(s.session_id);
//   setEditingTitle(s.title || s.preview || "");
// };
 
// const cancelRename = () => {
//   setEditingSessionId(null);
//   setEditingTitle("");
// };
 
// const commitRename = async (sid) => {
//   const newTitle = editingTitle.trim();
//   if (!newTitle) { cancelRename(); return; }
//   try {
//     await fetch(`/api/sessions/${sid}`, {
//       method: "PATCH",
//       headers: { "Content-Type": "application/json" },
//       body: JSON.stringify({ title: newTitle }),
//     });
//     fetchSessionList();
//   } catch (err) {
//     console.error("Rename failed:", err);
//   } finally {
//     cancelRename();
//   }
// };
 
// const exportSession = async (sid, format) => {
//   setExportMenuFor(null);
//   try {
//     const res = await fetch(`/api/sessions/${sid}/export?format=${format}`);
//     if (!res.ok) throw new Error(`Export failed (${res.status})`);
//     const blob = await res.blob();
//     const disposition = res.headers.get("Content-Disposition") || "";
//     const match = disposition.match(/filename="([^"]+)"/);
//     const filename = match ? match[1] : `chat.${format === "json" ? "json" : "md"}`;
 
//     const url = URL.createObjectURL(blob);
//     const a = document.createElement("a");
//     a.href = url;
//     a.download = filename;
//     document.body.appendChild(a);
//     a.click();
//     a.remove();
//     URL.revokeObjectURL(url);
//   } catch (err) {
//     alert(`Could not export chat: ${err.message}`);
//   }
// };
//   const now = () => new Date().toLocaleTimeString([], { hour:"2-digit", minute:"2-digit" });

//   const sendMessage = async (text) => {
//     const q = (text || input).trim();
//     if (!q || loading) return;
//     setInput("");
//     setMessages(prev => [...prev, { role:"user", content:q, ts:now() }]);
//     setLoading(true);
//     setTrace(null);
//     try {
//       const res  = await fetch("/api/chat", {
//         method:"POST", headers:{"Content-Type":"application/json"},
//         body: JSON.stringify({ session_id:sessionId, query:q }),
//       });
//       const data = await res.json();
//       setMessages(prev => [...prev, {
//         role:"assistant",
//         content: data.response || "No response received.",
//         ts: now(),
//         usedRag: data.used_rag,   // true = RAG, false = direct, undefined = unknown
//       }]);
//       if (data.trace) setTrace(data.trace);
//     } catch (err) {
//       setMessages(prev => [...prev, {
//         role:"assistant",
//         content:`❌ Could not reach the backend.\n\nError: ${err.message}`,
//         ts:now(),
//       }]);
//     } finally {
//       setLoading(false);
//       fetchSessionList();   // keep sidebar history fresh as conversation grows
//     }
//   };

//   const resetSession = () => { setMessages([]); setTrace(null); setInput(""); };

//   // ── Snapshot handler ────────────────────────────────────────────────────────
//   const handleSnapshot = () => {
//     saveAsPDF(messages, chunkCount);
//     setToast(true);
//     setTimeout(() => setToast(false), 3000);
//   };

//   const handleKey = (e) => {
//     if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
//   };

//   return (
//     <>
//       <style>{`
//         * { box-sizing:border-box; margin:0; padding:0; }
//         body { background:${C.bg}; }
//         ::-webkit-scrollbar { width:5px; }
//         ::-webkit-scrollbar-track { background:transparent; }
//         ::-webkit-scrollbar-thumb { background:${C.border}; border-radius:4px; }
//         @keyframes pulse {
//           0%,100% { opacity:0.3; transform:scale(0.85); }
//           50%      { opacity:1;   transform:scale(1.1); }
//         }
//       `}</style>

//       <Toast show={toast} />

//       <div style={{
//         ...S.app,
//         gridTemplateColumns: `${leftOpen ? "260px" : "0px"} 1fr ${rightOpen ? "300px" : "0px"}`,
//         transition: "grid-template-columns 0.25s ease",
//       }}>

//         {/* ── Header ─────────────────────────────────────────────────────── */}
//         <div style={S.header}>
//           {/* Left sidebar toggle */}
//           <button onClick={() => setLeftOpen(o => !o)} title={leftOpen ? "Hide sidebar" : "Show sidebar"} style={{
//             background:"none", border:`1px solid ${C.border}`, borderRadius:6,
//             padding:"4px 7px", cursor:"pointer", display:"flex", alignItems:"center",
//             marginRight:4, transition:"border-color 0.15s",
//           }}
//             onMouseEnter={e => e.currentTarget.style.borderColor = C.accent}
//             onMouseLeave={e => e.currentTarget.style.borderColor = C.border}
//           >
//             <Icon d={leftOpen ? Icons.chevLeft : Icons.chevRight} size={14} stroke={C.textSub} />
//           </button>

//           <span style={{ fontSize:18 }}>🌾</span>
//           <span style={{ fontWeight:700, fontSize:15, letterSpacing:"-0.01em" }}>
//             Agentic RAG
//           </span>
//           <span style={{ color:C.textMute, fontSize:13 }}>Agricultural Knowledge Base</span>
//           <div style={{ flex:1 }} />
//           <StatusBadge chunks={chunkCount} />

//           {/* ── Save conversation button ──── */}
//           <button
//             onClick={handleSnapshot}
//             disabled={messages.length === 0}
//             title="Save conversation as PDF"
//             style={{
//               ...S.headerBtn,
//               opacity: messages.length === 0 ? 0.4 : 1,
//               color: C.amber,
//               border: `1px solid ${C.amberDim}`,
//             }}
//           >
//             <Icon d={Icons.snapshot} size={13} stroke={C.amber} />
//             Save PDF
//           </button>

//           <button onClick={resetSession} style={S.headerBtn}>
//             <Icon d={Icons.reset} size={13} stroke={C.textSub} />
//             New session
//           </button>

//           {/* Right panel toggle */}
//           <button onClick={() => setRightOpen(o => !o)} title={rightOpen ? "Hide trace panel" : "Show trace panel"} style={{
//             background:"none", border:`1px solid ${C.border}`, borderRadius:6,
//             padding:"4px 7px", cursor:"pointer", display:"flex", alignItems:"center",
//             marginLeft:4, transition:"border-color 0.15s",
//           }}
//             onMouseEnter={e => e.currentTarget.style.borderColor = C.amber}
//             onMouseLeave={e => e.currentTarget.style.borderColor = C.border}
//           >
//             <Icon d={rightOpen ? Icons.chevRight : Icons.chevLeft} size={14} stroke={C.textSub} />
//           </button>
//         </div>

//         {/* ── Sidebar ────────────────────────────────────────────────────── */}
//         <div style={{ ...S.sidebar, overflow: leftOpen ? "auto" : "hidden",
//           width: leftOpen ? undefined : 0, padding: leftOpen ? 16 : 0,
//           transition:"width 0.25s ease, padding 0.25s ease" }}>

//           {/* ── 1. Chat history (TOP) ──────── */}
//           <SidebarSection title="Chat history">
//             {historyLoading ? (
//               <div style={{ fontSize:11.5, color:C.textMute, padding:"4px 10px" }}>Loading…</div>
//             ) : pastSessions.length === 0 ? (
//               <div style={{ fontSize:11.5, color:C.textMute, padding:"4px 10px", lineHeight:1.5 }}>
//                 Past conversations appear here
//               </div>
//             ) : (
//               <div style={{ display:"flex", flexDirection:"column", gap:4, maxHeight:220, overflowY:"auto" }}>
//                 {pastSessions.map(s => (
//   <div key={s.session_id} style={{
//     display: "flex", alignItems: "center", gap: 4,
//     background: s.session_id === sessionId ? "#22331a" : C.surface2,
//     border: `1px solid ${s.session_id === sessionId ? C.accentDim : C.border}`,
//     borderRadius: 8, padding: "6px 8px", position: "relative",
//   }}>
//     {editingSessionId === s.session_id ? (
//       <input
//         autoFocus
//         value={editingTitle}
//         onChange={(e) => setEditingTitle(e.target.value)}
//         onBlur={() => commitRename(s.session_id)}
//         onKeyDown={(e) => {
//           if (e.key === "Enter") commitRename(s.session_id);
//           if (e.key === "Escape") cancelRename();
//         }}
//         style={{
//           flex: 1, background: C.surface, border: `1px solid ${C.accent}`,
//           borderRadius: 4, color: C.text, fontSize: 11, padding: "3px 6px",
//           outline: "none",
//         }}
//       />
//     ) : (
//       <button
//         onClick={() => loadSession(s.session_id)}
//         title={s.preview}
//         style={{
//           flex: 1, background: "none", border: "none", cursor: "pointer",
//           textAlign: "left", color: C.textSub, fontSize: 11,
//           overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
//         }}
//       >
//         {s.title || s.preview || "(empty)"}
//         <div style={{ fontSize: 9.5, color: C.textMute, marginTop: 1 }}>
//           {s.message_count} msgs · {new Date(s.last_activity || s.created_at).toLocaleDateString()}
//         </div>
//       </button>
//     )}
 
//     {editingSessionId !== s.session_id && (
//       <>
//         <button
//           onClick={() => startRename(s)}
//           title="Rename"
//           style={{ background: "none", border: "none", cursor: "pointer", padding: 2, opacity: 0.5 }}
//         >
//           <Icon d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" size={12} stroke={C.textSub} />
//         </button>
 
//         <div style={{ position: "relative" }}>
//           <button
//             onClick={() => setExportMenuFor(exportMenuFor === s.session_id ? null : s.session_id)}
//             title="Export"
//             style={{ background: "none", border: "none", cursor: "pointer", padding: 2, opacity: 0.5 }}
//           >
//             <Icon d={Icons.share} size={12} stroke={C.textSub} />
//           </button>
//           {exportMenuFor === s.session_id && (
//             <div style={{
//               position: "absolute", right: 0, top: "100%", marginTop: 4, zIndex: 20,
//               background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6,
//               padding: 4, display: "flex", flexDirection: "column", minWidth: 110,
//               boxShadow: "0 6px 20px rgba(0,0,0,0.4)",
//             }}>
//               <button onClick={() => exportSession(s.session_id, "markdown")}
//                 style={{ background: "none", border: "none", color: C.textSub, fontSize: 11,
//                   textAlign: "left", padding: "5px 8px", cursor: "pointer", borderRadius: 4 }}>
//                 Export as Markdown
//               </button>
//               <button onClick={() => exportSession(s.session_id, "json")}
//                 style={{ background: "none", border: "none", color: C.textSub, fontSize: 11,
//                   textAlign: "left", padding: "5px 8px", cursor: "pointer", borderRadius: 4 }}>
//                 Export as JSON
//               </button>
//             </div>
//           )}
//         </div>
//       </>
//     )}
 
//     <button
//       onClick={() => deleteSession(s.session_id)}
//       title="Delete this conversation"
//       style={{ background: "none", border: "none", cursor: "pointer", padding: 2, opacity: 0.5 }}
//     >
//       <Icon d={Icons.trash} size={12} stroke={C.danger} />
//     </button>
//   </div>
// ))}
//               </div>
//             )}
//           </SidebarSection>

//           {/* ── 2. Knowledge base (clickable PDF names) ── */}
//           <SidebarSection title="Knowledge base">
//             {[
//               { label:"PARC Report 2023-24",  file:"PARC Annual Report 2023-24_compressed.pdf" },
//               { label:"FAO Crop Guidelines",  file:"i5550e.pdf" },
//               { label:"Punjab Agri Rules",    file:"PbAgriDeptExtenAdapReseWing_SR_2007_20070612.pdf" },
//             ].map(({ label, file }) => (
//               <button key={file}
//                 onClick={() => window.open(`/api/pdf/${encodeURIComponent(file)}`, "_blank")}
//                 title={`Open ${file}`}
//                 style={{
//                   display:"flex", justifyContent:"space-between", alignItems:"center",
//                   width:"100%", padding:"6px 10px", borderRadius:8,
//                   background:C.surface2, border:`1px solid ${C.border}`,
//                   marginBottom:4, cursor:"pointer", textAlign:"left",
//                   transition:"border-color 0.15s",
//                 }}
//                 onMouseEnter={e => e.currentTarget.style.borderColor = C.accent}
//                 onMouseLeave={e => e.currentTarget.style.borderColor = C.border}
//               >
//                 <span style={{ color:C.textSub, fontSize:12 }}>{label}</span>
//                 <span style={{ color:C.accent, fontSize:11 }}>✓ ↗</span>
//               </button>
//             ))}
//           </SidebarSection>

//           <SidebarSection title="Pipeline config">
//             <SidebarItem label="LLM"        value={backendInfo.label}
//               accent={backendInfo.isGroqLeak ? C.danger : undefined} />
//             <SidebarItem label="Embedding"  value={status?.embedding_model || "—"} />
//             <SidebarItem label="Vector DB"  value={status?.vector_db || "—"} />
//             <SidebarItem label="Retrieval"  value={status?.retrieval || "—"} />
//             <SidebarItem label="Fusion"     value={status?.fusion || "—"} />
//             <SidebarItem label="Max retries" value="2" />
//           </SidebarSection>

//           <SidebarSection title="Session">
//             <SidebarItem label="Messages"       value={messages.length} />
//             <SidebarItem label="Chunks indexed" value={chunkCount.toLocaleString()} accent={C.accent} />
//             <SidebarItem label="Backend"        value={backendInfo.label}
//               accent={backendInfo.isGroqLeak ? C.danger : C.amber} />
//           </SidebarSection>

//           {backendInfo.isGroqLeak && (
//             <SidebarSection title="⚠ Wrong backend">
//               <div style={{
//                 background:"#2a1010", border:`1px solid ${C.danger}`,
//                 borderRadius:8, padding:"10px 12px",
//                 fontSize:11.5, color:"#e8a0a0", lineHeight:1.6,
//               }}>
//                 LLM_BACKEND is defaulting to Groq. Run this in the terminal
//                 running api_server.py, then restart it:
//                 <div style={{
//                   marginTop:6, fontFamily:"monospace", fontSize:10.5,
//                   color:"#f0c0c0", background:"#1a0808", padding:"6px 8px", borderRadius:4,
//                 }}>
//                   $env:LLM_BACKEND = "qwen_remote"
//                 </div>
//               </div>
//             </SidebarSection>
//           )}

//           {statusError && (
//             <SidebarSection title="⚠ Backend issue">
//               <div style={{
//                 background:"#2a1010", border:`1px solid ${C.danger}`,
//                 borderRadius:8, padding:"10px 12px",
//                 fontSize:11.5, color:"#e8a0a0", lineHeight:1.6,
//                 wordBreak:"break-word",
//               }}>
//                 {statusError}
//               </div>
//             </SidebarSection>
//           )}

//           {/* ── Chat history ─────────────────────── */}
//           {/* (moved to top of sidebar — rendered first above) */}

//           {/* ── Snapshot section in sidebar ─────── */}
//           <SidebarSection title="Snapshot">
//             <div style={{
//               background:C.surface2, border:`1px solid ${C.amberDim}`,
//               borderRadius:10, padding:"12px 12px 10px",
//             }}>
//               <div style={{ fontSize:12, color:C.textSub, lineHeight:1.6, marginBottom:10 }}>
//                 Exports the full conversation to a dark-themed PDF — questions,
//                 answers, timestamps, and session metadata.
//               </div>
//               <button
//                 onClick={handleSnapshot}
//                 disabled={messages.length === 0}
//                 style={{
//                   width:"100%", padding:"7px 0",
//                   background: messages.length === 0 ? C.surface : C.amberDim,
//                   border:`1px solid ${messages.length === 0 ? C.border : C.amber}`,
//                   borderRadius:8, color: messages.length === 0 ? C.textMute : C.amber,
//                   fontSize:12, fontWeight:600, cursor: messages.length === 0 ? "default" : "pointer",
//                   display:"flex", alignItems:"center", justifyContent:"center", gap:6,
//                   transition:"background 0.15s",
//                 }}
//               >
//                 <Icon d={Icons.snapshot} size={13}
//                   stroke={messages.length === 0 ? C.textMute : C.amber} />
//                 {messages.length === 0 ? "No messages yet" : `Save ${messages.length} messages as PDF`}
//               </button>
//             </div>
//           </SidebarSection>
//         </div>

//         {/* ── Chat ───────────────────────────────────────────────────────── */}
//         <div style={S.main}>
//           <div ref={chatRef} style={S.chatArea}>
//             {messages.length === 0
//               ? <Welcome onSend={sendMessage} />
//               : messages.map((m, i) => (
//                   <Message key={i} role={m.role} content={m.content} ts={m.ts}
//                     usedRag={m.usedRag}
//                     onRegenerate={!m.role || m.role==="user" ? null : () => {
//                       // Find the user message just before this assistant message
//                       const prevUser = messages.slice(0, i).reverse().find(x => x.role==="user");
//                       if (prevUser) sendMessage(prevUser.content);
//                     }}
//                   />
//                 ))
//             }
//             {loading && <TypingDots />}
//           </div>

//           <div style={S.inputRow}>
//             <textarea
//               ref={textareaRef}
//               rows={2}
//               value={input}
//               onChange={e => setInput(e.target.value)}
//               onKeyDown={handleKey}
//               placeholder="Ask about crops, diseases, PARC activities… (Enter to send)"
//               style={{ ...S.textarea, borderColor: input ? C.borderHi : C.border }}
//             />
//             <button
//               onClick={() => sendMessage()}
//               disabled={loading || !input.trim()}
//               style={{ ...S.sendBtn, opacity: loading || !input.trim() ? 0.4 : 1 }}
//             >
//               <Icon d={Icons.send} size={16} stroke="#fff" />
//             </button>
//           </div>
//         </div>

//         {/* ── Trace panel ────────────────────────────────────────────────── */}
//         <div style={S.tracePanel}>
//           <TracePanel trace={trace} />
//         </div>

//       </div>
//     </>
//   );
// }



import { useState, useRef, useEffect } from "react";

// ── Palette ────────────────────────────────────────────────────────────────────
const C = {
  bg:        "#0c1108",
  surface:   "#141c0f",
  surface2:  "#1c2614",
  border:    "#2a3d1e",
  borderHi:  "#3d5a2a",
  accent:    "#7ab648",
  accentDim: "#4a7a1e",
  amber:     "#e8a020",
  amberDim:  "#7a4e00",
  text:      "#dde8cc",
  textSub:   "#7a9460",
  textMute:  "#4a6035",
  userBub:   "#1a2e10",
  botBub:    "#0f1a08",
  danger:    "#c0392b",
};

// ── Icons ─────────────────────────────────────────────────────────────────────
const Icon = ({ d, size = 18, stroke = C.textSub }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke={stroke} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
    <path d={d} />
  </svg>
);

const Icons = {
  send:       "M22 2L11 13M22 2L15 22l-4-9-9-4 20-7z",
  reset:      "M1 4v6h6M23 20v-6h-6M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15",
  trace:      "M3 3h18v18H3zM9 9h6M9 13h6M9 17h4",
  bot:        "M12 2a4 4 0 0 1 4 4v2h2a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2V6a4 4 0 0 1 4-4zM9 10H7v2h2v-2zm8 0h-2v2h2v-2zm-5 4h-2v2h2v-2z",
  user:       "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
  copy:       "M20 9H11a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2v-9a2 2 0 0 0-2-2zM5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1",
  check:      "M20 6L9 17l-5-5",
  snapshot:   "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H8",
  trash:      "M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2",
  thumbUp:    "M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3",
  thumbDown:  "M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zM17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17",
  share:      "M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8M16 6l-4-4-4 4M12 2v13",
  regenerate: "M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15",
  sources:    "M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2zM22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z",
  chevLeft:   "M15 18l-6-6 6-6",
  chevRight:  "M9 18l6-6-6-6",
  upload:     "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12",
  globe:      "M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10zM2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z",
  edit:       "M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z",
  logout:     "M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9",
  fileUp:     "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M12 18v-6M9 15l3-3 3 3",
};

// ── Styles ─────────────────────────────────────────────────────────────────────
const S = {
  app: {
    display: "grid",
    gridTemplateColumns: "260px 1fr 300px",
    gridTemplateRows: "56px 1fr",
    height: "100vh",
    background: C.bg,
    color: C.text,
    fontFamily: "'Inter', 'Segoe UI', system-ui, sans-serif",
    fontSize: 14,
    overflow: "hidden",
  },
  header: {
    gridColumn: "1 / -1",
    display: "flex",
    alignItems: "center",
    gap: 12,
    padding: "0 24px",
    background: C.surface,
    borderBottom: `1px solid ${C.border}`,
  },
  sidebar: {
    background: C.surface,
    borderRight: `1px solid ${C.border}`,
    display: "flex",
    flexDirection: "column",
    padding: 16,
    gap: 8,
    overflowY: "auto",
  },
  main: { display: "flex", flexDirection: "column", overflow: "hidden" },
  tracePanel: {
    background: C.surface,
    borderLeft: `1px solid ${C.border}`,
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
  },
  chatArea: {
    flex: 1,
    overflowY: "auto",
    padding: "20px 24px",
    display: "flex",
    flexDirection: "column",
    gap: 16,
  },
  inputRow: {
    display: "flex",
    gap: 10,
    padding: "12px 20px 16px",
    borderTop: `1px solid ${C.border}`,
    background: C.surface,
  },
  textarea: {
    flex: 1,
    background: C.surface2,
    border: `1px solid ${C.border}`,
    borderRadius: 10,
    color: C.text,
    padding: "10px 14px",
    fontSize: 14,
    resize: "none",
    outline: "none",
    fontFamily: "inherit",
    lineHeight: 1.5,
    transition: "border-color 0.2s",
  },
  sendBtn: {
    width: 42, height: 42, borderRadius: 10, border: "none",
    background: C.accent, cursor: "pointer",
    display: "flex", alignItems: "center", justifyContent: "center",
    alignSelf: "flex-end", flexShrink: 0,
    transition: "opacity 0.15s, transform 0.1s",
  },
  headerBtn: {
    background: C.surface2, border: `1px solid ${C.border}`,
    borderRadius: 8, padding: "5px 10px", color: C.textSub,
    cursor: "pointer", fontSize: 12, display: "flex",
    alignItems: "center", gap: 5,
  },
};

// ── PDF snapshot ───────────────────────────────────────────────────────────────
// Pure browser approach — no library needed.
// Builds a print-friendly HTML page in a hidden iframe and triggers window.print().
// The page uses @media print to render cleanly as PDF when the user picks
// "Save as PDF" in the print dialog (works in Chrome, Edge, Firefox).
function saveAsPDF(messages, chunkCount) {
  if (messages.length === 0) {
    alert("Nothing to save — start a conversation first.");
    return;
  }

  const date = new Date().toLocaleString();

  // Build message rows HTML
  const rows = messages.map(m => {
    const isUser = m.role === "user";
    const label  = isUser ? "You" : "RAG Assistant";
    const color  = isUser ? "#2d5a1b" : "#1a3a0a";
    const border = isUser ? "#4a7a1e" : "#2a3d1e";
    const align  = isUser ? "right" : "left";
    const mlAuto = isUser ? "auto" : "0";
    const mrAuto = isUser ? "0" : "auto";

    return `
      <div style="margin-bottom:18px; text-align:${align}">
        <div style="font-size:11px; color:#7a9460; margin-bottom:4px;">
          ${label} · ${m.ts}
        </div>
        <div style="
          display:inline-block; max-width:75%;
          background:${color}; border:1px solid ${border};
          border-radius:12px; padding:10px 14px;
          font-size:13px; line-height:1.7; color:#dde8cc;
          white-space:pre-wrap; word-break:break-word;
          margin-left:${mlAuto}; margin-right:${mrAuto};
          text-align:left;
        ">${escHtml(m.content)}</div>
      </div>`;
  }).join("");

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <title>RAG Conversation Snapshot</title>
  <style>
    @page { size: A4; margin: 20mm 18mm; }
    * { box-sizing: border-box; margin:0; padding:0; }
    body {
      background: #0c1108;
      color: #dde8cc;
      font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
      font-size: 13px;
      padding: 0;
    }
    .cover {
      border-bottom: 1px solid #2a3d1e;
      padding-bottom: 16px;
      margin-bottom: 24px;
    }
    .cover h1 {
      font-size: 20px; font-weight: 700; color: #dde8cc;
      letter-spacing: -0.02em; margin-bottom: 6px;
    }
    .cover .meta {
      font-size: 11px; color: #7a9460; display:flex; gap: 20px;
    }
    .meta span { display:flex; align-items:center; gap:4px; }
    .messages { padding-top: 4px; }
    @media print {
      body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    }
  </style>
</head>
<body>
  <div class="cover">
    <h1>🌾 Agricultural RAG — Conversation Snapshot</h1>
    <div class="meta">
      <span>📅 ${date}</span>
      <span>💬 ${messages.length} messages</span>
      <span>📦 ${chunkCount.toLocaleString()} chunks indexed</span>
    </div>
  </div>
  <div class="messages">${rows}</div>
</body>
</html>`;

  // Open in a hidden iframe and trigger print
  let iframe = document.getElementById("__snapshot_iframe__");
  if (!iframe) {
    iframe = document.createElement("iframe");
    iframe.id = "__snapshot_iframe__";
    iframe.style.cssText = "position:fixed;width:0;height:0;border:none;top:-9999px;left:-9999px;";
    document.body.appendChild(iframe);
  }

  iframe.srcdoc = html;
  iframe.onload = () => {
    setTimeout(() => {
      iframe.contentWindow.focus();
      iframe.contentWindow.print();
    }, 300);
  };
}

function escHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ── Status badge ──────────────────────────────────────────────────────────────
function StatusBadge({ chunks }) {
  const ok = chunks > 0;
  return (
    <div style={{
      display:"flex", alignItems:"center", gap:6,
      padding:"4px 10px", borderRadius:20,
      background: ok ? "#1a3310" : "#3a1010",
      border:`1px solid ${ok ? C.accentDim : C.danger}`,
      fontSize:12, color: ok ? C.accent : "#e74c3c",
    }}>
      <div style={{
        width:7, height:7, borderRadius:"50%",
        background: ok ? C.accent : C.danger,
        boxShadow: ok ? `0 0 6px ${C.accent}` : "none",
      }} />
      {ok ? `${chunks.toLocaleString()} chunks` : "Empty — index first"}
    </div>
  );
}

// ── Sidebar helpers ───────────────────────────────────────────────────────────
function SidebarSection({ title, children }) {
  return (
    <div style={{ marginBottom:8 }}>
      <div style={{ fontSize:11, fontWeight:600, letterSpacing:"0.08em",
        textTransform:"uppercase", color:C.textMute, marginBottom:8, padding:"0 4px" }}>
        {title}
      </div>
      {children}
    </div>
  );
}
function SidebarItem({ label, value, accent }) {
  // Long values (e.g. "BM25 + Sentence Embeddings") wrap to two lines.
  // A simple row layout with space-between then vertically centers the
  // short label against the wrapped value and visually overlaps it.
  // Stack label above value instead whenever the value is long, so both
  // always have their own line and never collide.
  const valueStr = String(value ?? "");
  const isLong = valueStr.length > 14;

  if (isLong) {
    return (
      <div style={{
        padding:"6px 10px", borderRadius:8, background:C.surface2, marginBottom:4,
      }}>
        <div style={{ color:C.textSub, fontSize:11, marginBottom:2 }}>{label}</div>
        <div style={{ color:accent||C.text, fontSize:12, fontWeight:500, lineHeight:1.4 }}>
          {value}
        </div>
      </div>
    );
  }

  return (
    <div style={{
      display:"flex", justifyContent:"space-between", alignItems:"center",
      padding:"6px 10px", borderRadius:8, background:C.surface2, marginBottom:4,
    }}>
      <span style={{ color:C.textSub, fontSize:12 }}>{label}</span>
      <span style={{ color:accent||C.text, fontSize:12, fontWeight:500 }}>{value}</span>
    </div>
  );
}

// ── Citation renderer ─────────────────────────────────────────────────────────
// Parses the LLM's structured output into:
//   - Inline [N] citation superscripts (clickable, jump to source)
//   - SOURCES section as numbered clickable links that open the PDF at the page
//   - Web search sources as amber-coloured external links

function parseSources(content) {
  const sourcesMatch = content.match(/SOURCES:\s*\n([\s\S]+)$/i);
  const mainText = sourcesMatch
    ? content.slice(0, content.indexOf(sourcesMatch[0])).trim()
    : content;

  const sources = [];
  if (sourcesMatch) {
    const lines = sourcesMatch[1].trim().split("\n").filter(Boolean);
    lines.forEach(line => {
      // Match [N] FILENAME | Page X
      const docMatch = line.match(/\[(\d+)\]\s*(.+?)\s*\|\s*[Pp]age\s*(\d+)/);
      if (docMatch) {
        sources.push({
          num:      parseInt(docMatch[1]),
          filename: docMatch[2].trim(),
          page:     parseInt(docMatch[3]),
          type:     "document",
        });
        return;
      }
      // Match [Web N] Title — URL
      const webMatch = line.match(/\[Web\s*(\d+)\]\s*(.+?)\s*—\s*(https?:\/\/\S+)/);
      if (webMatch) {
        sources.push({
          num:   parseInt(webMatch[1]),
          title: webMatch[2].trim(),
          url:   webMatch[3].trim(),
          type:  "web",
        });
      }
    });
  }
  return { mainText, sources };
}

function renderTextWithCitations(text, sources, onCiteClick) {
  // Split on [N] or [Web N] patterns and render superscript badges
  const parts = text.split(/(\[(?:Web\s*)?\d+\])/g);
  return parts.map((part, i) => {
    const match = part.match(/^\[(?:Web\s*)?(\d+)\]$/);
    if (match) {
      const num = parseInt(match[1]);
      const isWeb = part.toLowerCase().includes("web");
      const src = sources.find(s => s.num === num && (isWeb ? s.type === "web" : s.type === "document"))
               || sources.find(s => s.num === num);
      return (
        <sup key={i}
          onClick={() => src && onCiteClick(src)}
          title={src ? (src.type === "document"
            ? `${src.filename} — Page ${src.page}`
            : src.title) : ""}
          style={{
            cursor: src ? "pointer" : "default",
            color: src ? (src.type === "web" ? C.amber : C.accent) : C.textMute,
            fontWeight: 700, fontSize: "0.72em",
            marginLeft: 1, padding: "1px 4px", borderRadius: 3,
            background: src ? (src.type === "web" ? "#2a1e00" : "#16301a") : "transparent",
            border: src ? `1px solid ${src.type === "web" ? C.amberDim : C.accentDim}` : "none",
            userSelect: "none",
          }}
        >
          {part}
        </sup>
      );
    }
    // Normal text — preserve newlines
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
  const openSource = (src) => {
    if (src.type === "document") {
      // Opens PDF via FastAPI endpoint — browser PDF viewer honours #page=N
      window.open(
        `/api/pdf/${encodeURIComponent(src.filename)}#page=${src.page}`,
        "_blank"
      );
    } else {
      window.open(src.url, "_blank");
    }
  };

  if (!sources.length) return null;

  return (
    <div style={{
      marginTop: 12, paddingTop: 10,
      borderTop: `1px solid ${C.border}`,
    }}>
      <div style={{
        fontSize: 10, fontWeight: 700, letterSpacing: "0.08em",
        textTransform: "uppercase", color: C.textMute, marginBottom: 6,
      }}>
        References
      </div>
      {sources.map((src, i) => (
        <div key={i}
          onClick={() => openSource(src)}
          style={{
            display: "flex", alignItems: "flex-start", gap: 7,
            marginBottom: 5, cursor: "pointer",
            padding: "5px 7px", borderRadius: 7,
            transition: "background 0.15s",
          }}
          onMouseEnter={e => e.currentTarget.style.background = C.surface2}
          onMouseLeave={e => e.currentTarget.style.background = "transparent"}
        >
          {/* Badge number */}
          <span style={{
            minWidth: 20, height: 20, borderRadius: 4, flexShrink: 0,
            background: src.type === "document" ? C.accentDim : C.amberDim,
            border: `1px solid ${src.type === "document" ? C.accent : C.amber}`,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 9, fontWeight: 700,
            color: src.type === "document" ? C.accent : C.amber,
          }}>
            {src.num}
          </span>
          {/* Label */}
          <div style={{ fontSize: 11.5, color: C.textSub, lineHeight: 1.5 }}>
            {src.type === "document" ? (
              <>
                <span style={{ color: C.text, fontWeight: 500 }}>{src.filename}</span>
                <span style={{ color: C.textMute }}> — Page {src.page}</span>
                <span style={{ color: C.accentDim, fontSize: 10, marginLeft: 5 }}>↗ open PDF</span>
              </>
            ) : (
              <>
                <span style={{ color: C.text, fontWeight: 500 }}>{src.title}</span>
                <span style={{ color: C.amberDim, fontSize: 10, marginLeft: 5 }}>↗ web</span>
              </>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Message bubble ────────────────────────────────────────────────────────────
function Message({ role, content, ts, usedRag, onRegenerate }) {
  const [copied, setCopied]         = useState(false);
  const [liked, setLiked]           = useState(null);   // null | "up" | "down"
  const [showSources, setShowSources] = useState(true);
  const isUser = role === "user";

  const copyText = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const ragBadge = !isUser && usedRag !== null && usedRag !== undefined && (
    <span style={{
      display:"inline-flex", alignItems:"center", gap:4,
      fontSize:9.5, fontWeight:600, letterSpacing:"0.03em",
      padding:"2px 7px", borderRadius:20,
      background: usedRag ? "#16301a" : "#2a2210",
      border: `1px solid ${usedRag ? C.accentDim : C.amberDim}`,
      color: usedRag ? C.accent : C.amber,
      marginLeft: 6,
    }}>
      {usedRag ? "RAG" : "🌐 Web"}
    </span>
  );

  // GPT-style icon button helper
  const ActionBtn = ({ icon, title, onClick, active, activeColor }) => (
    <button onClick={onClick} title={title} style={{
      background: "none", border: "none", cursor: "pointer",
      padding: "4px 5px", borderRadius: 6, display:"flex", alignItems:"center",
      opacity: 0.55, transition:"opacity 0.15s, background 0.15s",
    }}
      onMouseEnter={e => { e.currentTarget.style.opacity="1"; e.currentTarget.style.background=C.surface2; }}
      onMouseLeave={e => { e.currentTarget.style.opacity="0.55"; e.currentTarget.style.background="none"; }}
    >
      <Icon d={icon} size={14} stroke={active ? (activeColor||C.accent) : C.textSub} />
    </button>
  );

  return (
    <div style={{ display:"flex", flexDirection:"column",
      alignItems: isUser ? "flex-end" : "flex-start", gap:4 }}>
      <div style={{ display:"flex", alignItems:"center", gap:6,
        flexDirection: isUser ? "row-reverse" : "row" }}>
        <div style={{
          width:26, height:26, borderRadius:"50%",
          background: isUser ? C.accentDim : "#1a2610",
          border:`1px solid ${isUser ? C.accent : C.border}`,
          display:"flex", alignItems:"center", justifyContent:"center", flexShrink:0,
        }}>
          <Icon d={isUser ? Icons.user : Icons.bot} size={13}
            stroke={isUser ? C.accent : C.textSub} />
        </div>
        <span style={{ fontSize:11, color:C.textMute, display:"flex", alignItems:"center" }}>
          {isUser ? "You" : "RAG Assistant"} · {ts}
          {ragBadge}
        </span>
      </div>

      <div style={{
        maxWidth:"78%",
        background: isUser ? C.userBub : C.botBub,
        border:`1px solid ${isUser ? C.accentDim : C.border}`,
        borderRadius: isUser ? "14px 4px 14px 14px" : "4px 14px 14px 14px",
        padding:"10px 14px", lineHeight:1.65, fontSize:14, color:C.text,
      }}>
        {isUser ? (
          <span style={{ whiteSpace:"pre-wrap", wordBreak:"break-word" }}>{content}</span>
        ) : (() => {
          const { mainText, sources } = parseSources(content);
          const onCiteClick = (src) => {
            if (src.type === "document") {
              window.open(`/api/pdf/${encodeURIComponent(src.filename)}#page=${src.page}`, "_blank");
            } else {
              window.open(src.url, "_blank");
            }
          };
          return (
            <>
              <div style={{ whiteSpace:"pre-wrap", wordBreak:"break-word" }}>
                {renderTextWithCitations(mainText, sources, onCiteClick)}
              </div>
              {showSources && <SourcesList sources={sources} />}
            </>
          );
        })()}
      </div>

      {/* ── GPT-style action icon bar (assistant messages only) ─────────── */}
      {!isUser && (
        <div style={{
          display:"flex", alignItems:"center", gap:1,
          paddingLeft:4, marginTop:-2,
        }}>
          <ActionBtn icon={copied ? Icons.check : Icons.copy}
            title="Copy" onClick={copyText}
            active={copied} activeColor={C.accent} />
          <ActionBtn icon={Icons.thumbUp}
            title="Good response" onClick={() => setLiked(l => l==="up" ? null : "up")}
            active={liked==="up"} activeColor={C.accent} />
          <ActionBtn icon={Icons.thumbDown}
            title="Bad response" onClick={() => setLiked(l => l==="down" ? null : "down")}
            active={liked==="down"} activeColor={C.danger} />
          <ActionBtn icon={Icons.share}
            title="Share" onClick={() => {
              const txt = `Q: ${content.slice(0,120)}…`;
              navigator.clipboard.writeText(txt);
            }} />
          {onRegenerate && (
            <ActionBtn icon={Icons.regenerate}
              title="Regenerate response" onClick={onRegenerate} />
          )}
          {/* Separator */}
          <div style={{ width:1, height:14, background:C.border, margin:"0 3px" }} />
          <ActionBtn icon={Icons.sources}
            title={showSources ? "Hide sources" : "Show sources"}
            onClick={() => setShowSources(s => !s)}
            active={showSources} activeColor={C.accent} />
        </div>
      )}
    </div>
  );
}

// ── Typing indicator ──────────────────────────────────────────────────────────
function TypingDots() {
  return (
    <div style={{ display:"flex", alignItems:"flex-start", gap:6 }}>
      <div style={{
        width:26, height:26, borderRadius:"50%",
        background:"#1a2610", border:`1px solid ${C.border}`,
        display:"flex", alignItems:"center", justifyContent:"center", flexShrink:0,
      }}>
        <Icon d={Icons.bot} size={13} stroke={C.textSub} />
      </div>
      <div style={{
        background:C.botBub, border:`1px solid ${C.border}`,
        borderRadius:"4px 14px 14px 14px", padding:"12px 16px",
        display:"flex", gap:5, alignItems:"center",
      }}>
        {[0, 0.18, 0.36].map((delay, i) => (
          <div key={i} style={{
            width:7, height:7, borderRadius:"50%", background:C.accentDim,
            animation:"pulse 1.2s ease-in-out infinite",
            animationDelay:`${delay}s`,
          }} />
        ))}
      </div>
    </div>
  );
}

// ── Trace panel ───────────────────────────────────────────────────────────────
function TracePanel({ trace }) {
  return (
    <div style={{ display:"flex", flexDirection:"column", height:"100%", overflow:"hidden" }}>
      <div style={{
        padding:"14px 16px 10px", borderBottom:`1px solid ${C.border}`,
        display:"flex", alignItems:"center", gap:8,
      }}>
        <Icon d={Icons.trace} size={15} stroke={C.amber} />
        <span style={{ fontSize:13, fontWeight:600, color:C.amber }}>Pipeline trace</span>
      </div>
      <div style={{ flex:1, overflowY:"auto", padding:"12px 14px" }}>
        {!trace ? (
          <div style={{ color:C.textMute, fontSize:12, textAlign:"center",
            marginTop:40, lineHeight:1.7 }}>
            Pipeline step timings<br/>appear here after each query
          </div>
        ) : (
          <pre style={{
            fontFamily:"'JetBrains Mono','Fira Code',monospace",
            fontSize:11, color:C.textSub, lineHeight:1.75,
            whiteSpace:"pre-wrap", wordBreak:"break-word", margin:0,
          }}>
            {trace}
          </pre>
        )}
      </div>
    </div>
  );
}

// ── Welcome screen ────────────────────────────────────────────────────────────
function Welcome({ onSend }) {
  const prompts = [
    "What wheat diseases are monitored in Punjab?",
    "Summarise PARC's 2023-24 research highlights",
    "What is the role of the Agriculture Extension Wing?",
    "Which FAO guidelines cover Ug99 rust?",
  ];
  return (
    <div style={{ flex:1, display:"flex", flexDirection:"column",
      alignItems:"center", justifyContent:"center", padding:32, gap:28 }}>
      <div style={{ textAlign:"center" }}>
        <div style={{ fontSize:40, marginBottom:12 }}>🌾</div>
        <div style={{ fontSize:22, fontWeight:700, color:C.text,
          letterSpacing:"-0.02em", marginBottom:6 }}>
          Agricultural RAG Assistant
        </div>
        <div style={{ fontSize:13, color:C.textSub, maxWidth:380, lineHeight:1.6 }}>
          Ask about Agriculture of Pakistan
        </div>
      </div>
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr",
        gap:10, width:"100%", maxWidth:560 }}>
        {prompts.map((p, i) => (
          <button key={i} onClick={() => onSend(p)} style={{
            background:C.surface2, border:`1px solid ${C.border}`,
            borderRadius:10, padding:"10px 14px", color:C.textSub,
            fontSize:12, textAlign:"left", cursor:"pointer", lineHeight:1.5,
            transition:"border-color 0.15s, color 0.15s",
          }}
            onMouseEnter={e => { e.currentTarget.style.borderColor=C.accent; e.currentTarget.style.color=C.text; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor=C.border; e.currentTarget.style.color=C.textSub; }}
          >
            {p}
          </button>
        ))}
      </div>
    </div>
  );
}

// ── Snapshot toast ────────────────────────────────────────────────────────────
function Toast({ show }) {
  return (
    <div style={{
      position:"fixed", bottom:28, left:"50%", transform:`translateX(-50%) translateY(${show?0:20}px)`,
      opacity: show ? 1 : 0, transition:"all 0.25s ease",
      background:C.surface2, border:`1px solid ${C.accent}`,
      borderRadius:10, padding:"9px 18px",
      fontSize:13, color:C.accent, fontWeight:500,
      display:"flex", alignItems:"center", gap:8,
      pointerEvents:"none", zIndex:9999,
      boxShadow:`0 4px 20px rgba(0,0,0,0.5)`,
    }}>
      <Icon d={Icons.check} size={14} stroke={C.accent} />
      Print dialog opened — choose "Save as PDF"
    </div>
  );
}

// ── Backend label normalizer ───────────────────────────────────────────────────
// The /api/status backend field reflects whatever LLM_BACKEND env var is set
// in whichever terminal launched api_server.py. If that terminal session
// forgot to set it, it silently falls back to "GROQ". Since this project
// only uses Qwen, never surface Groq in the UI — show a clear "not
// configured" state instead so it's obvious something needs fixing,
// rather than quietly displaying the wrong provider.
function normalizeBackendLabel(rawBackend, model) {
  if (!rawBackend) return { label: "—", isGroqLeak: false };
  const upper = rawBackend.toUpperCase();
  if (upper === "GROQ") {
    return { label: "⚠ Not set to Qwen", isGroqLeak: true };
  }
  if (upper.startsWith("QWEN")) {
    return { label: model || "Qwen", isGroqLeak: false };
  }
  return { label: rawBackend, isGroqLeak: false };
}

// ── Main app ──────────────────────────────────────────────────────────────────
export default function App({ username = "", onLogout = null }) {
  const [messages, setMessages]     = useState([]);
  const [input, setInput]           = useState("");
  const [loading, setLoading]       = useState(false);
  const [trace, setTrace]           = useState(null);
  const [chunkCount, setChunkCount] = useState(0);
  const [toast, setToast]           = useState(false);
  const [sessionId]                 = useState(() => crypto.randomUUID());
  const [status, setStatus]         = useState(null);
  const [statusError, setStatusError] = useState(null);
  const [pastSessions, setPastSessions] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [editingSessionId, setEditingSessionId] = useState(null);
  const [editingTitle, setEditingTitle]         = useState("");
  const [exportMenuFor, setExportMenuFor]       = useState(null);
  const [leftOpen, setLeftOpen]     = useState(true);
  const [rightOpen, setRightOpen]   = useState(true);
  // Upload panel state
  const [showUpload, setShowUpload]   = useState(false);
  const [uploads, setUploads]         = useState([]);
  const [uploading, setUploading]     = useState(false);
  const [uploadError, setUploadError] = useState("");
  // Live web search toggle
  const [webSearchMode, setWebSearchMode] = useState(false);
  // Auth token (read from localStorage, set by main.jsx)
  const authToken = () => localStorage.getItem("agri_rag_token") || "";
  const chatRef     = useRef(null);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  const backendInfo = normalizeBackendLabel(status?.backend, status?.model);

  useEffect(() => {
    if (chatRef.current)
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [messages, loading]);

  // Poll /api/status so the sidebar always reflects what the backend is
  // ACTUALLY doing — never a hardcoded guess. Refreshes every 8s so a
  // freshly-indexed vector store or backend swap shows up without reload.
  useEffect(() => {
    const fetchStatus = () => {
      fetch("/api/status")
        .then(r => r.json())
        .then(d => {
          setStatus(d);
          setChunkCount(d.chunk_count || 0);
          setStatusError(d.vector_store_error || d.pipeline_error || null);
        })
        .catch(err => {
          setStatusError(`Cannot reach API server: ${err.message}`);
          setChunkCount(0);
        });
    };
    fetchStatus();
    const id = setInterval(fetchStatus, 8000);
    return () => clearInterval(id);
  }, []);

  // ── Chat history: load list, load one session, delete one session ───────────
  const fetchSessionList = () => {
    fetch("/api/sessions")
      .then(r => r.json())
      .then(d => setPastSessions(d.sessions || []))
      .catch(() => {})
      .finally(() => setHistoryLoading(false));
  };

  useEffect(() => {
    fetchSessionList();
  }, []);

  const loadSession = (sid) => {
    fetch(`/api/sessions/${sid}`)
      .then(r => r.json())
      .then(d => {
        const loaded = (d.messages || []).map(m => ({
          role: m.role,
          content: m.content,
          ts: m.ts ? new Date(m.ts).toLocaleTimeString([], { hour:"2-digit", minute:"2-digit" }) : "",
          usedRag: m.used_rag,   // backend already returns this per-message for assistant turns
        }));
        setMessages(loaded);
        setTrace(null);
        // Note: continuing to chat will append to a NEW session id client-side,
        // since this app generates one session id per page load. The loaded
        // history is still viewable/exportable, but new replies start a fresh
        // session row in the DB.
      })
      .catch(() => {});
  };

  const deleteSession = (sid) => {
    if (!confirm("Delete this conversation permanently?")) return;
    fetch(`/api/sessions/${sid}`, { method: "DELETE" })
      .then(() => fetchSessionList())
      .catch(() => {});
  };

  // ── File upload handlers ──────────────────────────────────────────────────
  const fetchUploads = () => {
    fetch("/api/uploads", {
      headers: authToken() ? { Authorization: `Bearer ${authToken()}` } : {},
    })
      .then(r => r.json())
      .then(d => setUploads(d.uploads || []))
      .catch(() => {});
  };

  useEffect(() => { fetchUploads(); }, []);

  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (uploads.length >= 3) {
      setUploadError("Maximum 3 files allowed. Delete one to upload another.");
      return;
    }
    const allowedTypes = ["application/pdf", "text/plain"];
    if (!allowedTypes.includes(file.type) && !file.name.endsWith(".pdf") && !file.name.endsWith(".txt")) {
      setUploadError("Only PDF and TXT files are supported.");
      return;
    }
    setUploading(true);
    setUploadError("");
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData,
        headers: authToken() ? { Authorization: `Bearer ${authToken()}` } : {},
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Upload failed");
      fetchUploads();
    } catch (err) {
      setUploadError(err.message || "Upload failed");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const deleteUpload = async (fileId) => {
    if (!confirm("Delete this uploaded file?")) return;
    await fetch(`/api/uploads/${fileId}`, { method: "DELETE" });
    fetchUploads();
  };
  
const startRename = (s) => {
  setEditingSessionId(s.session_id);
  setEditingTitle(s.title || s.preview || "");
};
 
const cancelRename = () => {
  setEditingSessionId(null);
  setEditingTitle("");
};
 
const commitRename = async (sid) => {
  const newTitle = editingTitle.trim();
  if (!newTitle) { cancelRename(); return; }
  try {
    await fetch(`/api/sessions/${sid}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: newTitle }),
    });
    fetchSessionList();
  } catch (err) {
    console.error("Rename failed:", err);
  } finally {
    cancelRename();
  }
};
 
const exportSession = async (sid, format) => {
  setExportMenuFor(null);
  try {
    const res = await fetch(`/api/sessions/${sid}/export?format=${format}`);
    if (!res.ok) throw new Error(`Export failed (${res.status})`);
    const blob = await res.blob();
    const disposition = res.headers.get("Content-Disposition") || "";
    const match = disposition.match(/filename="([^"]+)"/);
    const filename = match ? match[1] : `chat.${format === "json" ? "json" : "md"}`;
 
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  } catch (err) {
    alert(`Could not export chat: ${err.message}`);
  }
};
  const now = () => new Date().toLocaleTimeString([], { hour:"2-digit", minute:"2-digit" });

  const sendMessage = async (text) => {
    const q = (text || input).trim();
    if (!q || loading) return;
    setInput("");
    setMessages(prev => [...prev, { role:"user", content:q, ts:now() }]);
    setLoading(true);
    setTrace(null);
    try {
      // Choose endpoint based on web search mode
      const endpoint = webSearchMode ? "/api/search/live" : "/api/chat";
      const body     = webSearchMode
        ? { query: q, session_id: sessionId }
        : { session_id: sessionId, query: q };

      const res  = await fetch(endpoint, {
        method:"POST",
        headers:{
          "Content-Type":"application/json",
          ...(authToken() ? { Authorization: `Bearer ${authToken()}` } : {}),
        },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      setMessages(prev => [...prev, {
        role:"assistant",
        content: data.response || "No response received.",
        ts: now(),
        usedRag:  data.used_rag,
        usedWeb:  webSearchMode,
      }]);
      if (data.trace) setTrace(data.trace);
    } catch (err) {
      setMessages(prev => [...prev, {
        role:"assistant",
        content:`❌ Could not reach the backend.\n\nError: ${err.message}`,
        ts:now(),
      }]);
    } finally {
      setLoading(false);
      fetchSessionList();
    }
  };

  const resetSession = () => { setMessages([]); setTrace(null); setInput(""); };

  // ── Snapshot handler ────────────────────────────────────────────────────────
  const handleSnapshot = () => {
    saveAsPDF(messages, chunkCount);
    setToast(true);
    setTimeout(() => setToast(false), 3000);
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  return (
    <>
      <style>{`
        * { box-sizing:border-box; margin:0; padding:0; }
        body { background:${C.bg}; }
        ::-webkit-scrollbar { width:5px; }
        ::-webkit-scrollbar-track { background:transparent; }
        ::-webkit-scrollbar-thumb { background:${C.border}; border-radius:4px; }
        @keyframes pulse {
          0%,100% { opacity:0.3; transform:scale(0.85); }
          50%      { opacity:1;   transform:scale(1.1); }
        }
      `}</style>

      <Toast show={toast} />

      <div style={{
        ...S.app,
        gridTemplateColumns: `${leftOpen ? "260px" : "0px"} 1fr ${rightOpen ? "300px" : "0px"}`,
        transition: "grid-template-columns 0.25s ease",
      }}>

        {/* ── Header ─────────────────────────────────────────────────────── */}
        <div style={S.header}>
          {/* Left sidebar toggle */}
          <button onClick={() => setLeftOpen(o => !o)} title={leftOpen ? "Hide sidebar" : "Show sidebar"} style={{
            background:"none", border:`1px solid ${C.border}`, borderRadius:6,
            padding:"4px 7px", cursor:"pointer", display:"flex", alignItems:"center",
            marginRight:4, transition:"border-color 0.15s",
          }}
            onMouseEnter={e => e.currentTarget.style.borderColor = C.accent}
            onMouseLeave={e => e.currentTarget.style.borderColor = C.border}
          >
            <Icon d={leftOpen ? Icons.chevLeft : Icons.chevRight} size={14} stroke={C.textSub} />
          </button>

          <span style={{ fontSize:18 }}>🌾</span>
          <span style={{ fontWeight:700, fontSize:15, letterSpacing:"-0.01em" }}>
            Agriculture-Knowledge Base
          </span>
          <span style={{ color:C.textMute, fontSize:13 }}>Agricultural Knowledge Base</span>
          <div style={{ flex:1 }} />
          <StatusBadge chunks={chunkCount} />

          {/* Web Search toggle */}
          <button
            onClick={() => setWebSearchMode(m => !m)}
            title={webSearchMode ? "Switch to RAG mode" : "Switch to Live Web Search"}
            style={{
              ...S.headerBtn,
              background: webSearchMode ? "#1a2e40" : C.surface2,
              border: `1px solid ${webSearchMode ? "#3a80c0" : C.border}`,
              color: webSearchMode ? "#60b0f0" : C.textSub,
            }}
          >
            <Icon d={Icons.globe} size={13} stroke={webSearchMode ? "#60b0f0" : C.textSub} />
            {webSearchMode ? "Web Search ON" : "Web Search"}
          </button>

          {/* Upload files button */}
          <button
            onClick={() => setShowUpload(u => !u)}
            title="Upload documents (max 3)"
            style={{
              ...S.headerBtn,
              background: showUpload ? C.accentDim : C.surface2,
              border: `1px solid ${showUpload ? C.accent : C.border}`,
              color: showUpload ? C.accent : C.textSub,
            }}
          >
            <Icon d={Icons.upload} size={13} stroke={showUpload ? C.accent : C.textSub} />
            Files {uploads.length > 0 ? `(${uploads.length}/3)` : ""}
          </button>

          {/* Save PDF */}
          <button
            onClick={handleSnapshot}
            disabled={messages.length === 0}
            title="Save conversation as PDF"
            style={{
              ...S.headerBtn,
              opacity: messages.length === 0 ? 0.4 : 1,
              color: C.amber,
              border: `1px solid ${C.amberDim}`,
            }}
          >
            <Icon d={Icons.snapshot} size={13} stroke={C.amber} />
            Save PDF
          </button>

          <button onClick={resetSession} style={S.headerBtn}>
            <Icon d={Icons.reset} size={13} stroke={C.textSub} />
            New session
          </button>

          {/* Username + logout */}
          {username && (
            <div style={{ display:"flex", alignItems:"center", gap:6,
              padding:"4px 10px", borderRadius:8, background:C.surface2,
              border:`1px solid ${C.border}`, fontSize:12, color:C.textSub }}>
              <Icon d={Icons.user} size={13} stroke={C.accent} />
              <span style={{ color:C.text, fontWeight:500 }}>{username}</span>
              {onLogout && (
                <button onClick={onLogout} title="Sign out" style={{
                  background:"none", border:"none", cursor:"pointer",
                  padding:2, display:"flex", alignItems:"center",
                }}>
                  <Icon d={Icons.logout} size={13} stroke={C.danger} />
                </button>
              )}
            </div>
          )}

          {/* Right panel toggle */}
          <button onClick={() => setRightOpen(o => !o)} title={rightOpen ? "Hide trace panel" : "Show trace panel"} style={{
            background:"none", border:`1px solid ${C.border}`, borderRadius:6,
            padding:"4px 7px", cursor:"pointer", display:"flex", alignItems:"center",
            marginLeft:4, transition:"border-color 0.15s",
          }}
            onMouseEnter={e => e.currentTarget.style.borderColor = C.amber}
            onMouseLeave={e => e.currentTarget.style.borderColor = C.border}
          >
            <Icon d={rightOpen ? Icons.chevRight : Icons.chevLeft} size={14} stroke={C.textSub} />
          </button>
        </div>

        {/* ── Upload panel (slides in below header when showUpload=true) ─────── */}
        {showUpload && (
          <div style={{
            gridColumn:"1 / -1",
            background:C.surface, borderBottom:`1px solid ${C.border}`,
            padding:"14px 24px", display:"flex", gap:16, alignItems:"flex-start",
            flexWrap:"wrap",
          }}>
            <div>
              <div style={{ fontSize:12, fontWeight:600, color:C.textSub, marginBottom:6 }}>
                Uploaded documents ({uploads.length}/3 max)
              </div>
              {uploads.length === 0 && (
                <div style={{ fontSize:12, color:C.textMute }}>
                  No documents uploaded yet. Upload PDFs to chat with your own docs.
                </div>
              )}
              <div style={{ display:"flex", flexWrap:"wrap", gap:8 }}>
                {uploads.map(u => (
                  <div key={u.file_id} style={{
                    display:"flex", alignItems:"center", gap:6,
                    background:C.surface2, border:`1px solid ${u.status==="indexed" ? C.accentDim : C.border}`,
                    borderRadius:8, padding:"6px 10px", fontSize:12,
                  }}>
                    <Icon d={Icons.fileUp} size={13} stroke={u.status==="indexed" ? C.accent : C.textSub} />
                    <span style={{ color:C.text, maxWidth:160, overflow:"hidden",
                      textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{u.original_name}</span>
                    <span style={{ fontSize:10, color:u.status==="indexed" ? C.accent : C.amber }}>
                      {u.status === "indexed" ? `✓ ${u.chunks} chunks` : u.status}
                    </span>
                    <button onClick={() => deleteUpload(u.file_id)} style={{
                      background:"none", border:"none", cursor:"pointer", padding:1 }}>
                      <Icon d={Icons.trash} size={12} stroke={C.danger} />
                    </button>
                  </div>
                ))}
              </div>
              {uploadError && (
                <div style={{ fontSize:11.5, color:C.danger, marginTop:6 }}>{uploadError}</div>
              )}
            </div>
            <div>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.txt"
                style={{ display:"none" }}
                onChange={handleFileSelect}
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading || uploads.length >= 3}
                style={{
                  display:"flex", alignItems:"center", gap:6,
                  padding:"8px 14px", borderRadius:8, fontSize:12, fontWeight:600,
                  background: uploads.length >= 3 ? C.surface2 : C.accentDim,
                  border:`1px solid ${uploads.length >= 3 ? C.border : C.accent}`,
                  color: uploads.length >= 3 ? C.textMute : C.accent,
                  cursor: uploads.length >= 3 ? "default" : "pointer",
                  opacity: uploading ? 0.6 : 1,
                }}
              >
                <Icon d={Icons.upload} size={13} stroke={uploads.length >= 3 ? C.textMute : C.accent} />
                {uploading ? "Uploading…" : uploads.length >= 3 ? "Limit reached (3/3)" : "Upload PDF / TXT"}
              </button>
              <div style={{ fontSize:10.5, color:C.textMute, marginTop:5, maxWidth:220 }}>
                Files are indexed into the knowledge base. Chat will search them alongside the default PDFs.
              </div>
            </div>
          </div>
        )}

        {/* ── Sidebar ────────────────────────────────────────────────────── */}
        <div style={{ ...S.sidebar, overflow: leftOpen ? "auto" : "hidden",
          width: leftOpen ? undefined : 0, padding: leftOpen ? 16 : 0,
          transition:"width 0.25s ease, padding 0.25s ease" }}>

          {/* ── 1. Chat history (TOP) ──────── */}
          <SidebarSection title="Chat history">
            {historyLoading ? (
              <div style={{ fontSize:11.5, color:C.textMute, padding:"4px 10px" }}>Loading…</div>
            ) : pastSessions.length === 0 ? (
              <div style={{ fontSize:11.5, color:C.textMute, padding:"4px 10px", lineHeight:1.5 }}>
                Past conversations appear here
              </div>
            ) : (
              <div style={{ display:"flex", flexDirection:"column", gap:4, maxHeight:220, overflowY:"auto" }}>
                {pastSessions.map(s => (
  <div key={s.session_id} style={{
    display: "flex", alignItems: "center", gap: 4,
    background: s.session_id === sessionId ? "#22331a" : C.surface2,
    border: `1px solid ${s.session_id === sessionId ? C.accentDim : C.border}`,
    borderRadius: 8, padding: "6px 8px", position: "relative",
  }}>
    {editingSessionId === s.session_id ? (
      <input
        autoFocus
        value={editingTitle}
        onChange={(e) => setEditingTitle(e.target.value)}
        onBlur={() => commitRename(s.session_id)}
        onKeyDown={(e) => {
          if (e.key === "Enter") commitRename(s.session_id);
          if (e.key === "Escape") cancelRename();
        }}
        style={{
          flex: 1, background: C.surface, border: `1px solid ${C.accent}`,
          borderRadius: 4, color: C.text, fontSize: 11, padding: "3px 6px",
          outline: "none",
        }}
      />
    ) : (
      <button
        onClick={() => loadSession(s.session_id)}
        title={s.preview}
        style={{
          flex: 1, background: "none", border: "none", cursor: "pointer",
          textAlign: "left", color: C.textSub, fontSize: 11,
          overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
        }}
      >
        {s.title || s.preview || "(empty)"}
        <div style={{ fontSize: 9.5, color: C.textMute, marginTop: 1 }}>
          {s.message_count} msgs · {new Date(s.last_activity || s.created_at).toLocaleDateString()}
        </div>
      </button>
    )}
 
    {editingSessionId !== s.session_id && (
      <>
        <button
          onClick={() => startRename(s)}
          title="Rename"
          style={{ background: "none", border: "none", cursor: "pointer", padding: 2, opacity: 0.5 }}
        >
          <Icon d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" size={12} stroke={C.textSub} />
        </button>
 
        <div style={{ position: "relative" }}>
          <button
            onClick={() => setExportMenuFor(exportMenuFor === s.session_id ? null : s.session_id)}
            title="Export"
            style={{ background: "none", border: "none", cursor: "pointer", padding: 2, opacity: 0.5 }}
          >
            <Icon d={Icons.share} size={12} stroke={C.textSub} />
          </button>
          {exportMenuFor === s.session_id && (
            <div style={{
              position: "absolute", right: 0, top: "100%", marginTop: 4, zIndex: 20,
              background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6,
              padding: 4, display: "flex", flexDirection: "column", minWidth: 110,
              boxShadow: "0 6px 20px rgba(0,0,0,0.4)",
            }}>
              <button onClick={() => exportSession(s.session_id, "markdown")}
                style={{ background: "none", border: "none", color: C.textSub, fontSize: 11,
                  textAlign: "left", padding: "5px 8px", cursor: "pointer", borderRadius: 4 }}>
                Export as Markdown
              </button>
              <button onClick={() => exportSession(s.session_id, "json")}
                style={{ background: "none", border: "none", color: C.textSub, fontSize: 11,
                  textAlign: "left", padding: "5px 8px", cursor: "pointer", borderRadius: 4 }}>
                Export as JSON
              </button>
            </div>
          )}
        </div>
      </>
    )}
 
    <button
      onClick={() => deleteSession(s.session_id)}
      title="Delete this conversation"
      style={{ background: "none", border: "none", cursor: "pointer", padding: 2, opacity: 0.5 }}
    >
      <Icon d={Icons.trash} size={12} stroke={C.danger} />
    </button>
  </div>
))}
              </div>
            )}
          </SidebarSection>

          {/* ── 2. Knowledge base (clickable PDF names) ── */}
          <SidebarSection title="Knowledge base">
            {[
              { label:"PARC Report 2023-24",  file:"PARC Annual Report 2023-24_compressed.pdf" },
              { label:"FAO Crop Guidelines",  file:"i5550e.pdf" },
              { label:"Punjab Agri Rules",    file:"PbAgriDeptExtenAdapReseWing_SR_2007_20070612.pdf" },
            ].map(({ label, file }) => (
              <button key={file}
                onClick={() => window.open(`/api/pdf/${encodeURIComponent(file)}`, "_blank")}
                title={`Open ${file}`}
                style={{
                  display:"flex", justifyContent:"space-between", alignItems:"center",
                  width:"100%", padding:"6px 10px", borderRadius:8,
                  background:C.surface2, border:`1px solid ${C.border}`,
                  marginBottom:4, cursor:"pointer", textAlign:"left",
                  transition:"border-color 0.15s",
                }}
                onMouseEnter={e => e.currentTarget.style.borderColor = C.accent}
                onMouseLeave={e => e.currentTarget.style.borderColor = C.border}
              >
                <span style={{ color:C.textSub, fontSize:12 }}>{label}</span>
                <span style={{ color:C.accent, fontSize:11 }}>✓ ↗</span>
              </button>
            ))}
          </SidebarSection>

          <SidebarSection title="Pipeline config">
            <SidebarItem label="LLM"        value={backendInfo.label}
              accent={backendInfo.isGroqLeak ? C.danger : undefined} />
            <SidebarItem label="Embedding"  value={status?.embedding_model || "—"} />
            <SidebarItem label="Vector DB"  value={status?.vector_db || "—"} />
            <SidebarItem label="Retrieval"  value={status?.retrieval || "—"} />
            <SidebarItem label="Fusion"     value={status?.fusion || "—"} />
            <SidebarItem label="Max retries" value="2" />
          </SidebarSection>

          <SidebarSection title="Session">
            <SidebarItem label="Messages"       value={messages.length} />
            <SidebarItem label="Chunks indexed" value={chunkCount.toLocaleString()} accent={C.accent} />
            <SidebarItem label="Backend"        value={backendInfo.label}
              accent={backendInfo.isGroqLeak ? C.danger : C.amber} />
          </SidebarSection>

          {backendInfo.isGroqLeak && (
            <SidebarSection title="⚠ Wrong backend">
              <div style={{
                background:"#2a1010", border:`1px solid ${C.danger}`,
                borderRadius:8, padding:"10px 12px",
                fontSize:11.5, color:"#e8a0a0", lineHeight:1.6,
              }}>
                LLM_BACKEND is defaulting to Groq. Run this in the terminal
                running api_server.py, then restart it:
                <div style={{
                  marginTop:6, fontFamily:"monospace", fontSize:10.5,
                  color:"#f0c0c0", background:"#1a0808", padding:"6px 8px", borderRadius:4,
                }}>
                  $env:LLM_BACKEND = "qwen_remote"
                </div>
              </div>
            </SidebarSection>
          )}

          {statusError && (
            <SidebarSection title="⚠ Backend issue">
              <div style={{
                background:"#2a1010", border:`1px solid ${C.danger}`,
                borderRadius:8, padding:"10px 12px",
                fontSize:11.5, color:"#e8a0a0", lineHeight:1.6,
                wordBreak:"break-word",
              }}>
                {statusError}
              </div>
            </SidebarSection>
          )}

          {/* ── Chat history ─────────────────────── */}
          {/* (moved to top of sidebar — rendered first above) */}

          {/* ── Snapshot section in sidebar ─────── */}
          <SidebarSection title="Snapshot">
            <div style={{
              background:C.surface2, border:`1px solid ${C.amberDim}`,
              borderRadius:10, padding:"12px 12px 10px",
            }}>
              <div style={{ fontSize:12, color:C.textSub, lineHeight:1.6, marginBottom:10 }}>
                Exports the full conversation to a dark-themed PDF — questions,
                answers, timestamps, and session metadata.
              </div>
              <button
                f={handleSnapshot}
                disabled={messages.length === 0}
                style={{
                  width:"100%", padding:"7px 0",
                  background: messages.length === 0 ? C.surface : C.amberDim,
                  border:`1px solid ${messages.length === 0 ? C.border : C.amber}`,
                  borderRadius:8, color: messages.length === 0 ? C.textMute : C.amber,
                  fontSize:12, fontWeight:600, cursor: messages.length === 0 ? "default" : "pointer",
                  display:"flex", alignItems:"center", justifyContent:"center", gap:6,
                  transition:"background 0.15s",
                }}
              >
                <Icon d={Icons.snapshot} size={13}
                  stroke={messages.length === 0 ? C.textMute : C.amber} />
                {messages.length === 0 ? "No messages yet" : `Save ${messages.length} messages as PDF`}
              </button>
            </div>
          </SidebarSection>
        </div>

        {/* ── Chat ───────────────────────────────────────────────────────── */}
        <div style={S.main}>
          <div ref={chatRef} style={S.chatArea}>
            {messages.length === 0
              ? <Welcome onSend={sendMessage} />
              : messages.map((m, i) => (
                  <Message key={i} role={m.role} content={m.content} ts={m.ts}
                    usedRag={m.usedRag}
                    onRegenerate={!m.role || m.role==="user" ? null : () => {
                      // Find the user message just before this assistant message
                      const prevUser = messages.slice(0, i).reverse().find(x => x.role==="user");
                      if (prevUser) sendMessage(prevUser.content);
                    }}
                  />
                ))
            }
            {loading && <TypingDots />}
          </div>

          <div style={S.inputRow}>
            <textarea
              ref={textareaRef}
              rows={2}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Ask about crops, diseases, PARC activities… (Enter to send)"
              style={{ ...S.textarea, borderColor: input ? C.borderHi : C.border }}
            />
            <button
              onClick={() => sendMessage()}
              disabled={loading || !input.trim()}
              style={{ ...S.sendBtn, opacity: loading || !input.trim() ? 0.4 : 1 }}
            >
              <Icon d={Icons.send} size={16} stroke="#fff" />
            </button>
          </div>
        </div>

        {/* ── Trace panel ────────────────────────────────────────────────── */}
        <div style={S.tracePanel}>
          <TracePanel trace={trace} />
        </div>

      </div>
    </>
  );
}
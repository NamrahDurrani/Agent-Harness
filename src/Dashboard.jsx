/**
 * Dashboard.jsx — standalone full-screen home page.
 *
 * Shown after login, before entering the chat app. Deliberately has NONE
 * of the chat app's chrome (no sidebar, no header icons, no composer,
 * no example-prompt suggestions) — just: a welcome greeting, New Chat /
 * New Project actions, and a dynamic status card. The card describes
 * what AgriBot is ready to help with in plain terms — it doesn't name
 * implementation details (Groq, ChromaDB, Tavily, MCP, BM25, etc.),
 * since those are backend choices, not something a user needs to know
 * to use the app.
 *
 * Props:
 *   username, email   — from the auth session
 *   onNewChat()        — go to the chat app and start a new chat
 *   onNewProject()      — go to the chat app and open "new project"
 */
import { useState, useEffect } from "react";
import { getThemeColors } from "./theme";
import agribotIcon from "./assets/agribot-icon.png";

function pickGreeting() {
  const h = new Date().getHours();
  if (h < 5)  return "Working late? Ask away — crops, weather, prices, all of it.";
  if (h < 12) return "Good morning! What can I help you look into today?";
  if (h < 17) return "Good afternoon! What can I help you look into today?";
  if (h < 21) return "Good evening! What can I help you look into today?";
  return "Working late? Ask away — crops, weather, prices, all of it.";
}

function ActionBox({ icon, title, subtitle, onClick, C }) {
  return (
    <button onClick={onClick}
      style={{
        display: "flex", alignItems: "flex-start", gap: 14, textAlign: "left",
        padding: "22px 24px", borderRadius: 16, border: `1px solid ${C.border}`,
        background: C.surface, cursor: "pointer", fontFamily: "inherit",
        transition: "all 0.15s",
      }}
      onMouseEnter={e => { e.currentTarget.style.borderColor = C.accent; e.currentTarget.style.background = C.accentBg; e.currentTarget.style.transform = "translateY(-1px)"; }}
      onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.background = C.surface; e.currentTarget.style.transform = "translateY(0)"; }}>
      <div style={{ width: 44, height: 44, borderRadius: 12, background: C.accentDim, border: `1px solid ${C.accent}`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, fontSize: 20 }}>
        {icon}
      </div>
      <div>
        <div style={{ fontSize: 16, fontWeight: 700, color: C.text, marginBottom: 4 }}>{title}</div>
        <div style={{ fontSize: 13, color: C.textSub, lineHeight: 1.5 }}>{subtitle}</div>
      </div>
    </button>
  );
}

function Stat({ label, value, C }) {
  return (
    <div>
      <div style={{ fontSize: 22, fontWeight: 800, color: C.text }}>{value}</div>
      <div style={{ fontSize: 12, color: C.textMute, marginTop: 3 }}>{label}</div>
    </div>
  );
}

export default function Dashboard({ username = "", email = "", onNewChat, onNewProject }) {
  const [themeMode] = useState(() => localStorage.getItem("agribot_theme") || "dark");
  const C = getThemeColors(themeMode);
  const [greeting] = useState(pickGreeting);
  const [status, setStatus] = useState(null);

  useEffect(() => {
    fetch("/api/status").then(r => r.json()).then(setStatus).catch(() => {});
  }, []);

  const chunkCount = status?.chunk_count || 0;
  const ready = chunkCount > 0;
  const displayName = email || username;

  return (
    <div style={{
      minHeight: "100vh", width: "100%", background: C.bg,
      display: "flex", flexDirection: "column", alignItems: "center",
      justifyContent: "center", padding: "40px 24px", boxSizing: "border-box",
      fontFamily: "'Segoe UI', system-ui, -apple-system, sans-serif",
    }}>
      <div style={{ width: "100%", maxWidth: 760, display: "flex", flexDirection: "column", alignItems: "center", gap: 32 }}>

        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: -8 }}>
          <img src={agribotIcon} alt="AgriBot" style={{ width: 32, height: 32, borderRadius: 8 }} />
          <span style={{ fontSize: 15, fontWeight: 700, color: C.textSub }}>AgriBot</span>
        </div>

        <div style={{ textAlign: "center" }}>
          <h1 style={{ fontSize: 34, fontWeight: 800, color: C.text, letterSpacing: "-0.03em", margin: "0 0 10px", lineHeight: 1.25 }}>
            Welcome back{displayName ? `,` : ""}
            {displayName && <><br />{displayName}</>}
          </h1>
          <p style={{ fontSize: 15.5, color: C.textSub, margin: 0 }}>{greeting}</p>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, width: "100%" }}>
          <ActionBox icon="💬" title="New chat" subtitle="Ask a fresh agriculture question" onClick={onNewChat} C={C} />
          <ActionBox icon="📁" title="New project" subtitle="Group related chats together" onClick={onNewProject} C={C} />
        </div>

        <div style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 16, background: C.surface, padding: "20px 26px" }}>
          <div style={{ fontSize: 13.5, fontWeight: 700, color: C.text, marginBottom: 14 }}>
            Agriculture Knowledge Base
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
            <Stat label="Indexed chunks" value={chunkCount.toLocaleString()} C={C} />
            <Stat label="Status" value={ready ? "Ready" : "Preparing"} C={C} />
          </div>
        </div>

      </div>
    </div>
  );
}

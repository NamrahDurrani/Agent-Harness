// import { useState, useEffect } from "react";

// /**
//  * AuthPage — Sign in / Create account
//  *
//  * FIXES applied vs the previous version:
//  *
//  * 1. Email field added (register only) — matches the screenshot UI and is
//  *    required for the welcome-email MCP tool to have somewhere to send to.
//  *
//  * 2. Theme-aware — reads the shared "agribot-theme" key from localStorage
//  *    (light | dark | system) so the login screen matches whatever the user
//  *    picked last time, instead of always forcing dark green. If no ProjectManager
//  *    Settings/Appearance panel has set this key yet, it defaults to "dark"
//  *    (current look) and falls back to system preference for "system".
//  *
//  * 3. Input-remount audit — the classic cause of "1 click per letter" is a
//  *    component (often a styled wrapper or icon-row) being DEFINED INSIDE
//  *    the parent component's function body. React then treats it as a brand
//  *    new component type on every render, unmounts the old input, and the
//  *    browser drops focus after each keystroke. This file defines every
//  *    sub-piece (Icon, PALETTES, field styles) at MODULE scope, outside the
//  *    component function, so nothing here can cause that bug. If the bug
//  *    persists after replacing this file, the cause is elsewhere (most likely
//  *    the parent component wrapping <AuthPage> is being remounted itself —
//  *    check that App.jsx doesn't recreate AuthPage's key on every render).
//  */

// // ── Palettes — mirrors ProjectManager.jsx exactly (same keys, same values) ────
// const PALETTES = {
//   dark: {
//     bg: "#0c1108", surface: "#141c0f", surface2: "#1c2614",
//     border: "#2a3d1e", borderHi: "#3d5a2a",
//     accent: "#7ab648", accentDim: "#4a7a1e",
//     amber: "#e8a020", amberDim: "#7a4e00",
//     text: "#dde8cc", textSub: "#7a9460", textMute: "#4a6035",
//     danger: "#c0392b",
//   },
//   light: {
//     bg: "#f4f9ef", surface: "#ffffff", surface2: "#eaf3e2",
//     border: "#c8dab8", borderHi: "#a8c890",
//     accent: "#4a8a1e", accentDim: "#6aa838",
//     amber: "#b87800", amberDim: "#e0a838",
//     text: "#1a2e10", textSub: "#4a6035", textMute: "#7a9460",
//     danger: "#c0392b",
//   },
// };

// function resolveTheme(pref) {
//   if (pref === "light" || pref === "dark") return pref;
//   // "system" or unset → follow OS preference
//   if (typeof window !== "undefined" && window.matchMedia) {
//     return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
//   }
//   return "dark";
// }

// const Icon = ({ d, size = 20, stroke }) => (
//   <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
//     stroke={stroke} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
//     <path d={d} />
//   </svg>
// );

// const leafPath  = "M12 2a4 4 0 0 1 4 4v2h2a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2V6a4 4 0 0 1 4-4z";
// const userPath  = "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z";
// const lockPath  = "M19 11H5a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7a2 2 0 0 0-2-2zM7 11V7a5 5 0 0 1 10 0v4";
// const mailPath  = "M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2zM22 6l-10 7L2 6";

// // ── API base ────────────────────────────────────────────────────────────────
// const API_BASE = "";

// export default function AuthPage({ onAuthSuccess }) {
//   // Theme — read once on mount, then subscribe to storage changes so it stays
//   // in sync if the user (already logged in elsewhere) changes it and comes
//   // back to this screen (e.g. after logout).
//   const [themePref, setThemePref] = useState(
//     () => (typeof window !== "undefined" && localStorage.getItem("agribot-theme")) || "dark"
//   );
//   useEffect(() => {
//     const onStorage = (e) => {
//       if (e.key === "agribot-theme") setThemePref(e.newValue || "dark");
//     };
//     window.addEventListener("storage", onStorage);
//     return () => window.removeEventListener("storage", onStorage);
//   }, []);
//   const resolved = resolveTheme(themePref);
//   const C = PALETTES[resolved];

//   const [mode, setMode]         = useState("login"); // "login" | "register"
//   const [username, setUsername] = useState("");
//   const [email, setEmail]       = useState("");
//   const [password, setPassword] = useState("");
//   const [confirm, setConfirm]   = useState("");
//   const [error, setError]       = useState("");
//   const [loading, setLoading]   = useState(false);

//   const submit = async (e) => {
//     e.preventDefault();
//     setError("");

//     if (mode === "register" && password !== confirm) {
//       setError("Passwords don't match.");
//       return;
//     }
//     if (username.trim().length < 3) {
//       setError("Username must be at least 3 characters.");
//       return;
//     }
//     if (password.length < 6) {
//       setError("Password must be at least 6 characters.");
//       return;
//     }
//     if (mode === "register" && email.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
//       setError("Enter a valid email address, or leave it blank.");
//       return;
//     }

//     setLoading(true);
//     try {
//       const endpoint = mode === "login" ? "/api/auth/login" : "/api/auth/register";
//       const payload = mode === "login"
//         ? { username: username.trim(), password }
//         : { username: username.trim(), password, email: email.trim() };

//       const res = await fetch(`${API_BASE}${endpoint}`, {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify(payload),
//       });
//       const data = await res.json();
//       if (!res.ok) {
//         throw new Error(data.detail || "Something went wrong.");
//       }
//       onAuthSuccess(data.token, data.username);
//     } catch (err) {
//       setError(err.message || "Network error — is the API server running?");
//     } finally {
//       setLoading(false);
//     }
//   };

//   const S = {
//     page: {
//       height: "100vh", width: "100vw", display: "flex",
//       alignItems: "center", justifyContent: "center",
//       background: C.bg, fontFamily: "'Inter','Segoe UI',system-ui,sans-serif",
//       color: C.text, transition: "background 0.2s, color 0.2s",
//     },
//     card: {
//       width: 380, background: C.surface, border: `1px solid ${C.border}`,
//       borderRadius: 14, padding: "32px 28px",
//       boxShadow: resolved === "light" ? "0 20px 60px rgba(0,0,0,0.10)" : "0 20px 60px rgba(0,0,0,0.4)",
//     },
//     logoRow: { display: "flex", alignItems: "center", gap: 10, marginBottom: 6, justifyContent: "center" },
//     title: { fontSize: 19, fontWeight: 700, margin: 0, color: C.text },
//     subtitle: { fontSize: 13, color: C.textSub, textAlign: "center", margin: "4px 0 24px" },
//     tabRow: { display: "flex", background: C.surface2, borderRadius: 10, padding: 4, marginBottom: 22 },
//     tab: (active) => ({
//       flex: 1, textAlign: "center", padding: "8px 0", borderRadius: 8,
//       fontSize: 13, fontWeight: 600, cursor: "pointer",
//       color: active ? "#ffffff" : C.textSub,
//       background: active ? C.accent : "transparent",
//       transition: "all 0.15s ease",
//     }),
//     fieldWrap: { marginBottom: 14 },
//     label: { fontSize: 12, color: C.textSub, marginBottom: 6, display: "block" },
//     inputRow: {
//       display: "flex", alignItems: "center", gap: 8,
//       background: C.surface2, border: `1px solid ${C.border}`,
//       borderRadius: 8, padding: "10px 12px",
//     },
//     input: {
//       flex: 1, background: "transparent", border: "none", outline: "none",
//       color: C.text, fontSize: 14, fontFamily: "inherit",
//     },
//     submitBtn: {
//       width: "100%", marginTop: 8, padding: "11px 0", borderRadius: 8,
//       border: "none", background: C.accent, color: "#ffffff",
//       fontWeight: 700, fontSize: 14, cursor: "pointer",
//     },
//     submitBtnDisabled: { opacity: 0.6, cursor: "not-allowed" },
//     error: {
//       background: resolved === "light" ? "rgba(192,57,43,0.08)" : "rgba(192,57,43,0.12)",
//       border: `1px solid ${C.danger}`, color: resolved === "light" ? "#a03020" : "#e8938a",
//       fontSize: 12.5, padding: "8px 10px", borderRadius: 8, marginBottom: 14,
//     },
//     footNote: { fontSize: 11.5, color: C.textMute, textAlign: "center", marginTop: 18 },
//   };

//   return (
//     <div style={S.page}>
//       <div style={S.card}>
//         <div style={S.logoRow}>
//           <Icon d={leafPath} size={26} stroke={C.accent} />
//           <h1 style={S.title}>AgriBot</h1>
//         </div>
//         <p style={S.subtitle}>Agricultural Knowledge Assistant</p>

//         <div style={S.tabRow}>
//           <div style={S.tab(mode === "login")} onClick={() => { setMode("login"); setError(""); }}>
//             Sign in
//           </div>
//           <div style={S.tab(mode === "register")} onClick={() => { setMode("register"); setError(""); }}>
//             Create account
//           </div>
//         </div>

//         {error && <div style={S.error}>{error}</div>}

//         <form onSubmit={submit}>
//           <div style={S.fieldWrap}>
//             <label style={S.label}>Username</label>
//             <div style={S.inputRow}>
//               <Icon d={userPath} size={16} stroke={C.textSub} />
//               <input
//                 style={S.input}
//                 value={username}
//                 onChange={(e) => setUsername(e.target.value)}
//                 placeholder="your_username"
//                 autoComplete="username"
//               />
//             </div>
//           </div>

//           {mode === "register" && (
//             <div style={S.fieldWrap}>
//               <label style={S.label}>Email (optional)</label>
//               <div style={S.inputRow}>
//                 <Icon d={mailPath} size={16} stroke={C.textSub} />
//                 <input
//                   style={S.input}
//                   type="email"
//                   value={email}
//                   onChange={(e) => setEmail(e.target.value)}
//                   placeholder="you@example.com"
//                   autoComplete="email"
//                 />
//               </div>
//             </div>
//           )}

//           <div style={S.fieldWrap}>
//             <label style={S.label}>Password</label>
//             <div style={S.inputRow}>
//               <Icon d={lockPath} size={16} stroke={C.textSub} />
//               <input
//                 style={S.input}
//                 type="password"
//                 value={password}
//                 onChange={(e) => setPassword(e.target.value)}
//                 placeholder="••••••••"
//                 autoComplete={mode === "login" ? "current-password" : "new-password"}
//               />
//             </div>
//           </div>

//           {mode === "register" && (
//             <div style={S.fieldWrap}>
//               <label style={S.label}>Confirm password</label>
//               <div style={S.inputRow}>
//                 <Icon d={lockPath} size={16} stroke={C.textSub} />
//                 <input
//                   style={S.input}
//                   type="password"
//                   value={confirm}
//                   onChange={(e) => setConfirm(e.target.value)}
//                   placeholder="••••••••"
//                   autoComplete="new-password"
//                 />
//               </div>
//             </div>
//           )}

//           <button type="submit" disabled={loading}
//             style={{ ...S.submitBtn, ...(loading ? S.submitBtnDisabled : {}) }}>
//             {loading ? "Please wait…" : mode === "login" ? "Sign in" : "Create account →"}
//           </button>
//         </form>

//         <p style={S.footNote}>
//           {mode === "login" ? "New here?" : "Already have an account?"}{" "}
//           <span
//             style={{ color: C.accent, cursor: "pointer", fontWeight: 600 }}
//             onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}
//           >
//             {mode === "login" ? "Create an account" : "Sign in instead"}
//           </span>
//         </p>
//       </div>
//     </div>
//   );
// }





import { useState, useEffect } from "react";
import agribotIcon from "./assets/agribot-icon.png";

/**
 * AuthPage — Sign in / Create account
 *
 * FIXES applied vs the previous version:
 *
 * 1. Email field added (register only) — matches the screenshot UI and is
 *    required for the welcome-email MCP tool to have somewhere to send to.
 *
 * 2. Theme-aware — reads the shared "agribot_theme" key from localStorage
 *    (light | dark | system) so the login screen matches whatever the user
 *    picked last time, instead of always forcing dark green. If no ProjectManager
 *    Settings/Appearance panel has set this key yet, it defaults to "dark"
 *    (current look) and falls back to system preference for "system".
 *
 * 3. Input-remount audit — the classic cause of "1 click per letter" is a
 *    component (often a styled wrapper or icon-row) being DEFINED INSIDE
 *    the parent component's function body. React then treats it as a brand
 *    new component type on every render, unmounts the old input, and the
 *    browser drops focus after each keystroke. This file defines every
 *    sub-piece (Icon, PALETTES, field styles) at MODULE scope, outside the
 *    component function, so nothing here can cause that bug. If the bug
 *    persists after replacing this file, the cause is elsewhere (most likely
 *    the parent component wrapping <AuthPage> is being remounted itself —
 *    check that App.jsx doesn't recreate AuthPage's key on every render).
 */

// ── Palettes — mirrors ProjectManager.jsx exactly (same keys, same values) ────
const PALETTES = {
  dark: {
    bg: "#0c1108", surface: "#141c0f", surface2: "#1c2614",
    border: "#2a3d1e", borderHi: "#3d5a2a",
    accent: "#7ab648", accentDim: "#4a7a1e",
    amber: "#e8a020", amberDim: "#7a4e00",
    text: "#dde8cc", textSub: "#7a9460", textMute: "#4a6035",
    danger: "#c0392b",
  },
  light: {
    bg: "#f4f9ef", surface: "#ffffff", surface2: "#eaf3e2",
    border: "#c8dab8", borderHi: "#a8c890",
    accent: "#4a8a1e", accentDim: "#6aa838",
    amber: "#b87800", amberDim: "#e0a838",
    text: "#1a2e10", textSub: "#4a6035", textMute: "#7a9460",
    danger: "#c0392b",
  },
};

function resolveTheme(pref) {
  if (pref === "light" || pref === "dark") return pref;
  // "system" or unset → follow OS preference
  if (typeof window !== "undefined" && window.matchMedia) {
    return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
  }
  return "dark";
}

const Icon = ({ d, size = 20, stroke }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke={stroke} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
    <path d={d} />
  </svg>
);

const leafPath  = "M12 2a4 4 0 0 1 4 4v2h2a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2V6a4 4 0 0 1 4-4z";
const userPath  = "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z";
const lockPath  = "M19 11H5a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7a2 2 0 0 0-2-2zM7 11V7a5 5 0 0 1 10 0v4";
const mailPath  = "M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2zM22 6l-10 7L2 6";
const eyePath   = "M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8zM12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z";
const eyeOffPath = "M17.94 17.94A10.94 10.94 0 0 1 12 20c-7 0-11-8-11-8a18.4 18.4 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19M14.12 14.12a3 3 0 1 1-4.24-4.24M1 1l22 22";

// ── API base ────────────────────────────────────────────────────────────────
const API_BASE = "";

export default function AuthPage({ onAuthSuccess }) {
  // Theme — read once on mount, then subscribe to storage changes so it stays
  // in sync if the user (already logged in elsewhere) changes it and comes
  // back to this screen (e.g. after logout).
  const [themePref, setThemePref] = useState(
    () => (typeof window !== "undefined" && localStorage.getItem("agribot_theme")) || "dark"
  );
  useEffect(() => {
    const onStorage = (e) => {
      if (e.key === "agribot_theme") setThemePref(e.newValue || "dark");
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);
  const resolved = resolveTheme(themePref);
  const C = PALETTES[resolved];

  const [mode, setMode]         = useState("login"); // "login" | "register"
  const [username, setUsername] = useState("");
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm]   = useState("");
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);
  const [showPw, setShowPw]         = useState(false);
  const [showConfirmPw, setShowConfirmPw] = useState(false);
  const [focusedField, setFocusedField]   = useState(null); // "username" | "email" | "password" | "confirm" | null

  const submit = async (e) => {
    e.preventDefault();
    setError("");

    if (mode === "register" && password !== confirm) {
      setError("Passwords don't match.");
      return;
    }
    if (username.trim().length < 3) {
      setError("Username must be at least 3 characters.");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }
    if (mode === "register" && email.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      setError("Enter a valid email address, or leave it blank.");
      return;
    }

    setLoading(true);
    try {
      const endpoint = mode === "login" ? "/api/auth/login" : "/api/auth/register";
      const payload = mode === "login"
        ? { username: username.trim(), password }
        : { username: username.trim(), password, email: email.trim() };

      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Something went wrong.");
      }
      onAuthSuccess(data.token, data.username);
    } catch (err) {
      setError(err.message || "Network error — is the API server running?");
    } finally {
      setLoading(false);
    }
  };

  const S = {
    page: {
      minHeight: "100vh", width: "100%", display: "flex",
      alignItems: "center", justifyContent: "center",
      background: C.bg, fontFamily: "'Inter','Segoe UI',system-ui,sans-serif",
      color: C.text, transition: "background 0.2s, color 0.2s",
      padding: "24px 16px", boxSizing: "border-box",
    },
    card: {
      width: "100%", maxWidth: 380, background: C.surface, border: `1px solid ${C.border}`,
      borderRadius: 14, padding: "clamp(24px, 6vw, 32px) clamp(20px, 5vw, 28px)",
      boxShadow: resolved === "light" ? "0 20px 60px rgba(0,0,0,0.10)" : "0 20px 60px rgba(0,0,0,0.4)",
      boxSizing: "border-box",
    },
    logoRow: { display: "flex", alignItems: "center", gap: 10, marginBottom: 6, justifyContent: "center" },
    title: { fontSize: 19, fontWeight: 700, margin: 0, color: C.text },
    subtitle: { fontSize: 13, color: C.textSub, textAlign: "center", margin: "4px 0 24px" },
    tabRow: { display: "flex", background: C.surface2, borderRadius: 10, padding: 4, marginBottom: 22 },
    tab: (active) => ({
      flex: 1, textAlign: "center", padding: "8px 0", borderRadius: 8,
      fontSize: 13, fontWeight: 600, cursor: "pointer",
      color: active ? "#ffffff" : C.textSub,
      background: active ? C.accent : "transparent",
      transition: "all 0.15s ease",
    }),
    fieldWrap: { marginBottom: 14 },
    label: { fontSize: 12, color: C.textSub, marginBottom: 6, display: "block" },
    inputRow: (focused) => ({
      display: "flex", alignItems: "center", gap: 8,
      background: C.surface2, border: `1.5px solid ${focused ? C.accent : C.border}`,
      borderRadius: 8, padding: "10px 12px",
      boxShadow: focused ? `0 0 0 3px ${resolved === "light" ? "rgba(74,138,30,0.12)" : "rgba(122,182,72,0.15)"}` : "none",
      transition: "border-color 0.15s, box-shadow 0.15s",
    }),
    input: {
      flex: 1, background: "transparent", border: "none", outline: "none",
      color: C.text, fontSize: 14, fontFamily: "inherit", minWidth: 0,
    },
    eyeBtn: { background: "none", border: "none", cursor: "pointer", padding: 2, display: "flex", alignItems: "center", flexShrink: 0 },
    submitBtn: {
      width: "100%", marginTop: 8, padding: "12px 0", borderRadius: 8,
      border: "none", background: C.accent, color: "#ffffff",
      fontWeight: 700, fontSize: 14, cursor: "pointer",
      transition: "transform 0.15s, box-shadow 0.15s, filter 0.15s",
      boxShadow: `0 4px 14px ${resolved === "light" ? "rgba(74,138,30,0.25)" : "rgba(122,182,72,0.2)"}`,
    },
    submitBtnDisabled: { opacity: 0.6, cursor: "not-allowed" },
    error: {
      background: resolved === "light" ? "rgba(192,57,43,0.08)" : "rgba(192,57,43,0.12)",
      border: `1px solid ${C.danger}`, color: resolved === "light" ? "#a03020" : "#e8938a",
      fontSize: 12.5, padding: "8px 10px", borderRadius: 8, marginBottom: 14,
    },
    footNote: { fontSize: 11.5, color: C.textMute, textAlign: "center", marginTop: 18 },
  };

  return (
    <div style={S.page}>
      <div style={S.card}>
        <div style={S.logoRow}>
          <img src={agribotIcon} alt="AgriBot" style={{ width: 30, height: 30, borderRadius: 8 }} />
          <h1 style={S.title}>AgriBot</h1>
        </div>
        <p style={S.subtitle}>Agricultural Knowledge Assistant</p>

        <div style={S.tabRow}>
          <div style={S.tab(mode === "login")} onClick={() => { setMode("login"); setError(""); }}>
            Sign in
          </div>
          <div style={S.tab(mode === "register")} onClick={() => { setMode("register"); setError(""); }}>
            Create account
          </div>
        </div>

        {error && <div style={S.error}>{error}</div>}

        <form onSubmit={submit}>
          <div style={S.fieldWrap}>
            <label style={S.label}>Username</label>
            <div style={S.inputRow(focusedField === "username")}>
              <Icon d={userPath} size={16} stroke={focusedField === "username" ? C.accent : C.textSub} />
              <input
                style={S.input}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                onFocus={() => setFocusedField("username")}
                onBlur={() => setFocusedField(null)}
                placeholder="your_username"
                autoComplete="username"
              />
            </div>
          </div>

          {mode === "register" && (
            <div style={S.fieldWrap}>
              <label style={S.label}>Email (optional)</label>
              <div style={S.inputRow(focusedField === "email")}>
                <Icon d={mailPath} size={16} stroke={focusedField === "email" ? C.accent : C.textSub} />
                <input
                  style={S.input}
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onFocus={() => setFocusedField("email")}
                  onBlur={() => setFocusedField(null)}
                  placeholder="you@example.com"
                  autoComplete="email"
                />
              </div>
            </div>
          )}

          <div style={S.fieldWrap}>
            <label style={S.label}>Password</label>
            <div style={S.inputRow(focusedField === "password")}>
              <Icon d={lockPath} size={16} stroke={focusedField === "password" ? C.accent : C.textSub} />
              <input
                style={S.input}
                type={showPw ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onFocus={() => setFocusedField("password")}
                onBlur={() => setFocusedField(null)}
                placeholder="••••••••"
                autoComplete={mode === "login" ? "current-password" : "new-password"}
              />
              <button type="button" style={S.eyeBtn} onClick={() => setShowPw(v => !v)} tabIndex={-1}>
                <Icon d={showPw ? eyeOffPath : eyePath} size={15} stroke={C.textMute} />
              </button>
            </div>
          </div>

          {mode === "register" && (
            <div style={S.fieldWrap}>
              <label style={S.label}>Confirm password</label>
              <div style={S.inputRow(focusedField === "confirm")}>
                <Icon d={lockPath} size={16} stroke={focusedField === "confirm" ? C.accent : C.textSub} />
                <input
                  style={S.input}
                  type={showConfirmPw ? "text" : "password"}
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  onFocus={() => setFocusedField("confirm")}
                  onBlur={() => setFocusedField(null)}
                  placeholder="••••••••"
                  autoComplete="new-password"
                />
                <button type="button" style={S.eyeBtn} onClick={() => setShowConfirmPw(v => !v)} tabIndex={-1}>
                  <Icon d={showConfirmPw ? eyeOffPath : eyePath} size={15} stroke={C.textMute} />
                </button>
              </div>
            </div>
          )}

          <button type="submit" disabled={loading}
            style={{ ...S.submitBtn, ...(loading ? S.submitBtnDisabled : {}) }}
            onMouseEnter={e => { if (!loading) { e.currentTarget.style.transform = "translateY(-1px)"; e.currentTarget.style.filter = "brightness(1.06)"; } }}
            onMouseLeave={e => { e.currentTarget.style.transform = "translateY(0)"; e.currentTarget.style.filter = "brightness(1)"; }}>
            {loading ? "Please wait…" : mode === "login" ? "Sign in" : "Create account →"}
          </button>
        </form>

        <p style={S.footNote}>
          {mode === "login" ? "New here?" : "Already have an account?"}{" "}
          <span
            style={{ color: C.accent, cursor: "pointer", fontWeight: 600 }}
            onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}
          >
            {mode === "login" ? "Create an account" : "Sign in instead"}
          </span>
        </p>
      </div>
    </div>
  );
}
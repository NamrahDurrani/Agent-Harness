/**
 * App.jsx — Root entrypoint for AgriBot
 * Wires AuthPage ↔ AgriBot with localStorage JWT session management.
 */
import { useState } from "react";
import AuthPage  from "./AuthPage";
import AgriBot   from "./AgriBot";

export default function App() {
  const [session, setSession] = useState(() => {
    try {
      const token    = localStorage.getItem("rag_token");
      const username = localStorage.getItem("rag_username");
      const email    = localStorage.getItem("rag_email") || "";
      if (token && username) return { token, username, email };
    } catch (_) {}
    return null;
  });

  const handleAuthSuccess = (token, username, email = "") => {
    localStorage.setItem("rag_token",    token);
    localStorage.setItem("rag_username", username);
    localStorage.setItem("rag_email",    email);
    setSession({ token, username, email });
  };

  const handleLogout = () => {
    localStorage.removeItem("rag_token");
    localStorage.removeItem("rag_username");
    localStorage.removeItem("rag_email");
    setSession(null);
  };

  if (!session) {
    return <AuthPage onAuthSuccess={handleAuthSuccess} />;
  }

  return (
    <AgriBot
      username={session.username}
      email={session.email}
      token={session.token}
      onLogout={handleLogout}
    />
  );
}

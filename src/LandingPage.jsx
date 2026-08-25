/**
 * LandingPage.jsx — Front page shown before the app.
 *
 * Full-bleed hero photo of a field, the AgriBot badge icon, title, and a
 * short description. Clicking "Enter AgriBot" (or anywhere on the card)
 * calls onEnter() — App.jsx then falls through to its existing
 * session-gated logic (AuthPage if not logged in, otherwise AgriBot),
 * completely unchanged. This component doesn't touch auth or session
 * state at all — it's purely a screen shown first.
 */
import heroImage from "./assets/agribot-hero.jpg";
import agribotIcon from "./assets/agribot-icon.png";

export default function LandingPage({ onEnter }) {
  return (
    <div
      style={{
        position: "fixed", inset: 0, width: "100vw", height: "100vh",
        backgroundImage: `linear-gradient(180deg, rgba(10,20,5,0.35) 0%, rgba(10,20,5,0.55) 55%, rgba(8,16,4,0.82) 100%), url(${heroImage})`,
        backgroundSize: "cover", backgroundPosition: "center",
        display: "flex", alignItems: "center", justifyContent: "center",
        fontFamily: "'Segoe UI', system-ui, -apple-system, sans-serif",
      }}
    >
      <div
        onClick={onEnter}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") onEnter(); }}
        style={{
          display: "flex", flexDirection: "column", alignItems: "center",
          textAlign: "center", gap: 18, padding: "48px 40px",
          maxWidth: 440, cursor: "pointer",
        }}
      >
        <img
          src={agribotIcon}
          alt="AgriBot"
          style={{ width: 96, height: 96, borderRadius: 22, boxShadow: "0 8px 30px rgba(0,0,0,0.35)" }}
        />

        <h1 style={{
          fontSize: 42, fontWeight: 800, color: "#fff", margin: 0,
          letterSpacing: "-0.02em", textShadow: "0 2px 12px rgba(0,0,0,0.4)",
        }}>
          AgriBot
        </h1>

        <p style={{
          fontSize: 15.5, lineHeight: 1.65, color: "rgba(255,255,255,0.92)",
          margin: 0, textShadow: "0 1px 6px rgba(0,0,0,0.35)",
        }}>
          An agriculture knowledge assistant for Pakistan — grounded answers on crop
          diseases, sowing schedules, and farming practices from PARC and FAO
          research, live weather advisories, and your own uploaded documents.
        </p>

        <button
          onClick={(e) => { e.stopPropagation(); onEnter(); }}
          style={{
            marginTop: 8, padding: "13px 34px", borderRadius: 999,
            border: "none", background: "#4a7a2e", color: "#fff",
            fontSize: 15, fontWeight: 700, cursor: "pointer",
            boxShadow: "0 6px 20px rgba(74,122,46,0.45)",
            transition: "transform 0.15s, box-shadow 0.15s",
          }}
          onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-1px)"; e.currentTarget.style.boxShadow = "0 8px 24px rgba(74,122,46,0.55)"; }}
          onMouseLeave={e => { e.currentTarget.style.transform = "translateY(0)"; e.currentTarget.style.boxShadow = "0 6px 20px rgba(74,122,46,0.45)"; }}
        >
          Enter AgriBot →
        </button>
      </div>
    </div>
  );
}

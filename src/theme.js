/**
 * theme.js — shared color theme, extracted so AgriBot.jsx and
 * Dashboard.jsx (a separate standalone page) use the identical theme
 * instead of two copies that could silently drift apart.
 */
// Professional neutral-slate dark theme with a muted forest-green accent
// (previous version used a near-black green-tinted background with a
// saturated lime accent, which read as a "green LED panel" rather than
// a professional app). Light theme detuned to match — same structure,
// softer saturation.
export const DARK = {
  bg:        "#0f1115", surface:   "#161920", surface2:  "#1e222b",
  surface3:  "#262b36", border:    "#2a2f3a", borderHi:  "#3a4150",
  accent:    "#4f9d6e", accentDim: "#3a7551", accentBg:  "rgba(79,157,110,0.12)",
  amber:     "#d1a13c", amberDim:  "#8a6b1f", amberBg:   "rgba(209,161,60,0.12)",
  text:      "#e8eaed", textSub:   "#9aa1ad", textMute:  "#5f6672",
  userBub:   "#1d2430", botBub:    "#161920", danger:    "#e5555a",
  dangerBg:  "rgba(229,85,90,0.12)", inputBg:  "#1a1e26", shadow: "0 8px 32px rgba(0,0,0,0.45)",
};

export const LIGHT = {
  bg:        "#f7f8f7", surface:   "#ffffff", surface2:  "#f0f2ef",
  surface3:  "#e4e8e2", border:    "#dde1db", borderHi:  "#4f9d6e",
  accent:    "#3f7d54", accentDim: "#2c5c3c", accentBg:  "rgba(63,125,84,0.08)",
  amber:     "#96731c", amberDim:  "#6b5313", amberBg:   "rgba(150,115,28,0.08)",
  text:      "#1c2024", textSub:   "#5a6169", textMute:  "#8b929b",
  userBub:   "#eef3ee", botBub:    "#ffffff", danger:    "#c0392b",
  dangerBg:  "rgba(192,57,43,0.08)", inputBg:  "#f0f2ef", shadow: "0 8px 32px rgba(20,30,20,0.10)",
};

export function getThemeColors(mode) {
  if (mode === "light") return LIGHT;
  if (mode === "dark")  return DARK;
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? DARK : LIGHT;
}

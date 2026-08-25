/**
 * theme.js — shared color theme, extracted so AgriBot.jsx and
 * Dashboard.jsx (a separate standalone page) use the identical theme
 * instead of two copies that could silently drift apart.
 */
export const DARK = {
  bg:        "#0c1108", surface:   "#141c0f", surface2:  "#1c2614",
  surface3:  "#222e18", border:    "#2a3d1e", borderHi:  "#3d5a2a",
  accent:    "#7ab648", accentDim: "#4a7a1e", accentBg:  "rgba(122,182,72,0.12)",
  amber:     "#e8a020", amberDim:  "#7a4e00", amberBg:   "rgba(232,160,32,0.12)",
  text:      "#dde8cc", textSub:   "#7a9460", textMute:  "#4a6035",
  userBub:   "#1a2e10", botBub:    "#0f1a08", danger:    "#c0392b",
  dangerBg:  "rgba(192,57,43,0.12)", inputBg:  "#1c2614", shadow: "0 8px 32px rgba(0,0,0,0.5)",
};

export const LIGHT = {
  bg:        "#f0f7ec", surface:   "#ffffff", surface2:  "#e8f4e0",
  surface3:  "#d4ecc4", border:    "#b8d9a0", borderHi:  "#7ab648",
  accent:    "#4a8a1e", accentDim: "#2a6a0a", accentBg:  "rgba(74,138,30,0.10)",
  amber:     "#8a5800", amberDim:  "#5a3a00", amberBg:   "rgba(138,88,0,0.10)",
  text:      "#1a2e10", textSub:   "#3a6020", textMute:  "#6a9450",
  userBub:   "#d4ecc4", botBub:    "#eaf5e0", danger:    "#c0392b",
  dangerBg:  "rgba(192,57,43,0.08)", inputBg:  "#e8f4e0", shadow: "0 8px 32px rgba(60,100,30,0.12)",
};

export function getThemeColors(mode) {
  if (mode === "light") return LIGHT;
  if (mode === "dark")  return DARK;
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? DARK : LIGHT;
}

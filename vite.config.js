import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  server: {
    port: 5175,
    proxy: {
      // Every request starting with /api is forwarded to FastAPI
      "/api": {
        target: "http://localhost:8001",
        changeOrigin: true,
        // Uncomment the line below if FastAPI is on HTTPS with a self-signed cert:
        // secure: false,
      },
      // Agent harness SSE stream (/agent/events/{execution_id}) — without
      // this, EventSource('/agent/events/...') connects to Vite's own dev
      // server (no such route there) instead of FastAPI, and the Agent
      // Execution panel sits stuck on RUNNING with zero events forever.
      "/agent": {
        target: "http://localhost:8001",
        changeOrigin: true,
        ws: false, // SSE, not WebSocket — the plain HTTP proxy already
                   // streams it fine, no ws upgrade needed
      },
    },
  },
});
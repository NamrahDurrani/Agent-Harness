import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  server: {
    port: 5173,
    proxy: {
      // Every request starting with /api is forwarded to FastAPI
      "/api": {
        target: "http://localhost:8001",
        changeOrigin: true,
        // Uncomment the line below if FastAPI is on HTTPS with a self-signed cert:
        // secure: false,
      },
    },
  },
});
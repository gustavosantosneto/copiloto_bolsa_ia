import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// /api/* → API Python ([api] em config/parametros.toml)
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": { target: "http://127.0.0.1:8000", rewrite: (p) => p.replace(/^\/api/, "") } },
  },
});

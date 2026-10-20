import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// /api/* → API Python. Portas vêm de config/parametros.toml via `copiloto painel` ([api].porta, [painel].porta_web)
declare const process: { env: Record<string, string | undefined> }; // roda no Node; evita @types/node
const api = process.env.COPILOTO_API ?? "http://127.0.0.1:8000";
export default defineConfig({
  plugins: [react()],
  server: {
    port: Number(process.env.COPILOTO_PORTA_WEB ?? 5173),
    strictPort: true, // porta ocupada → erro, não troca calada
    proxy: { "/api": { target: api, rewrite: (p) => p.replace(/^\/api/, "") } },
  },
});

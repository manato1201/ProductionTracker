/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// 画面と API を同じオリジンにする(セッション + CSRF のクッキーをそのまま使うため)
const target = process.env.VITE_PROXY_TARGET ?? "http://localhost:8000";
const allowedHosts = (process.env.VITE_ALLOWED_HOSTS ?? "").split(",").filter(Boolean);

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    allowedHosts: allowedHosts.length ? allowedHosts : undefined,
    proxy: {
      "/api": { target },
      "/admin": { target },
      "/static": { target },
      "/healthz": { target },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
  },
});

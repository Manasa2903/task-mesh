import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      "/chat": "http://localhost:8000",
      "/tasks": "http://localhost:8000",
      "/notes": "http://localhost:8000",
      "/logs": "http://localhost:8000",
      "/calendar": "http://localhost:8000",
      "/health": "http://localhost:8000",
    },
  },
});

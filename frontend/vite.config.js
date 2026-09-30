import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Reads VITE_API_BASE_URL from .env at build/dev time (see .env.example)
export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
});

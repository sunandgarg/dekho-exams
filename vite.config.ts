import { defineConfig } from "vite";
import { cloudflare } from "@cloudflare/vite-plugin";
import { tanstackStart } from "@tanstack/react-start/plugin/vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { resolve } from "node:path";

export default defineConfig({
  cacheDir: ".vite-ozi",
  server: { port: 3001, strictPort: true },
  plugins: [
    cloudflare({ inspectorPort: 9240, viteEnvironment: { name: "ssr" } }),
    tanstackStart({ server: { entry: "server" } }),
    react(),
    tailwindcss(),
  ],
  resolve: {
    tsconfigPaths: true,
    // The 4,000-entry local preview fixture must not ship alongside the
    // separate WordPress export fallback in Cloudflare's 25 MiB Worker.
    alias: process.env["VITE_PREVIEW_MODE"] === "false"
      ? [{ find: "@/data/fixtures.json", replacement: resolve("src/data/production-empty-fixtures.json") }]
      : [],
  },
});

import { defineConfig } from "vite";
import { cloudflare } from "@cloudflare/vite-plugin";
import { tanstackStart } from "@tanstack/react-start/plugin/vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

const nodeBuild = process.env["DEKHO_RUNTIME"] === "node";

export default defineConfig({
  build: { copyPublicDir: false },
  cacheDir: ".vite-ozi",
  server: { port: 3001, strictPort: true },
  plugins: [
    !nodeBuild && cloudflare({ inspectorPort: 9240, viteEnvironment: { name: "ssr" } }),
    tanstackStart({ server: { entry: "server" } }),
    react(),
    tailwindcss(),
  ],
  resolve: {
    tsconfigPaths: true,
    alias: nodeBuild ? { "cloudflare:workers": new URL("./server/assets.mjs", import.meta.url).pathname } : {},
  },
});

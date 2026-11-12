import { serve } from "srvx/node";
import { serveStatic } from "srvx/static";
import app from "../dist/server/server.js";
import { env } from "./assets.mjs";

const clientFile = serveStatic({ dir: "dist/client/assets" });
await serve({
  manual: true,
  trustProxy: process.env.TRUST_PROXY === "true",
  port: Number(process.env.PORT || 3000),
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname;
    if (path.startsWith("/assets/")) {
      url.pathname = path.slice("/assets".length);
      return clientFile(new Request(url, { method: request.method }), () => new Response(null, { status: 404 }));
    }
    if (path === "/jee-archive/math.svg" || path === "/jee-advanced-archive/math.svg" || /^\/(?:exam-logos|fonts|images|jee-figures|jee-papers|logos)\/|^\/(?:[\w-]+\.(?:svg|png|css|js|webmanifest)|sitemap-jee-[\w-]+\.xml)$/.test(path)) {
      const response = await env.ASSETS.fetch(request);
      if (path.startsWith("/jee-papers/")) response.headers.set("X-Robots-Tag", "noindex, follow");
      return response;
    }
    return app.fetch(request, env, {});
  },
}).serve();

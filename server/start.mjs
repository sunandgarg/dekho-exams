import { serve } from "srvx/node";
import { serveStatic } from "srvx/static";
import app from "../dist/server/server.js";
import { env } from "./assets.mjs";

import { stat } from "node:fs/promises";
import { createReadStream } from "node:fs";
import { Readable } from "node:stream";
const clientFile = serveStatic({ dir: "dist/client/assets" });
await serve({
  manual: true,
  hostname: process.env.HOST || "0.0.0.0",
  trustProxy: process.env.TRUST_PROXY === "true",
  port: Number(process.env.PORT || 3000),
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname;
    if (path.startsWith("/api/platform/v1/")) {
      const { platformResponse } = await import("./student/http.ts");
      return platformResponse(request);
    }
    if (/^\/(?:login|platform-(?:admin(?:\/leads)?|school|student))\/?$/.test(path)) {
      const page = await app.fetch(request, env, {});
      const response = new Response(page.body, page);
      response.headers.set("Cache-Control", "private, no-store");
      response.headers.set("Referrer-Policy", "no-referrer");
      response.headers.set("X-Frame-Options", "DENY");
      return response;
    }
    if (/^\/verified-pdf\/[a-f0-9]{64}\.pdf$/.test(path)) {
      if (!["GET","HEAD"].includes(request.method)) return new Response(null, {status:405});
      const file = "public" + path;
      const size = (await stat(file).catch(() => null))?.size;
      if (!size) return new Response(null, {status:404});
      let start = 0, end = size - 1;
      const range = request.headers.get("range");
      const headers = new Headers({"Accept-Ranges":"bytes", "Content-Type":"application/pdf", ETag:'"' + path.slice(-68,-4) + '"'});
      if (range) {
        const match = /^bytes=(\d*)-(\d*)$/.exec(range);
        if (match) {
          start = match[1] ? Number(match[1]) : Math.max(0, size - Number(match[2]));
          end = match[1] && match[2] ? Math.min(end, Number(match[2])) : end;
        }
        if (!match || start > end || start >= size) return new Response(null,{status:416, headers:{"Content-Range":"bytes */"+size}});
        headers.set("Content-Range", "bytes "+start+"-"+end+"/"+size);
      }
      headers.set("Content-Length", String(end - start + 1));
      const body = request.method === "HEAD" ? null : Readable.toWeb(createReadStream(file, {start,end}));
      return new Response(body, {status:range ? 206 : 200, headers});
    }
    if (path.startsWith("/assets/")) {
      url.pathname = path.slice("/assets".length);
      return clientFile(new Request(url, { method: request.method }), () => new Response(null, { status: 404 }));
    }
    if (path === "/sitemap-pdf-library.xml" || path === "/favicon.ico" || path === "/jee-archive/math.svg" || path === "/jee-advanced-archive/math.svg" || /^\/(?:exam-logos|fonts|images|jee-figures|jee-papers|logos)\/|^\/(?:[\w-]+\.(?:svg|png|css|js|webmanifest)|sitemap-jee-[\w-]+\.xml)$/.test(path)) {
      const response = await env.ASSETS.fetch(request);
      if (path.startsWith("/jee-papers/")) response.headers.set("X-Robots-Tag", "noindex, follow");
      return response;
    }
    return app.fetch(request, env, {});
  },
}).serve();

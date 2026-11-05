import { cp, mkdir, rm } from "node:fs/promises";
import { resolve } from "node:path";
import { build } from "esbuild";

const output = resolve("dist/pages");
await rm(output, { recursive: true, force: true });
await mkdir(output, { recursive: true });
await cp(resolve("dist/client"), output, { recursive: true, force: true });

// Bundle the server into one Pages Function. Its source chunks stay outside
// the upload directory, so visitors cannot request them as static files.
await build({
  stdin: {
    contents: `import app from "../server/index.js";

const staticPath = /^(?:\\/assets\\/|\\/logos\\/|\\/fonts\\/|\\/downloads\\/|\\/(?:aitrove-favicon(?:-v2)?|favicon)\\.png$|\\/(?:java|learning)-coverage\\.html$)/;

export default {
  async fetch(request, env, context) {
    const url = new URL(request.url);
    if (url.pathname.startsWith("/__prerender/")) return new Response("Not found", { status: 404 });
    if (staticPath.test(url.pathname)) {
      return env.ASSETS.fetch(request);
    }
    if ((request.method === "GET" || request.method === "HEAD") &&
        !url.search && !request.headers.has("authorization") && !request.headers.has("cookie") &&
        (url.pathname === "/" || /^\\/[a-z0-9]+(?:[/-][a-z0-9]+)*$/.test(url.pathname) ||
         /^\\/(?:robots\\.txt|sitemap(?:-\\d+)?\\.xml)$/.test(url.pathname))) {
      const assetPath = url.pathname === "/" ? "home" : url.pathname.slice(1);
      const assetUrl = new URL("/__prerender/" + assetPath, url);
      const asset = await env.ASSETS.fetch(new Request(assetUrl, request));
      if (asset.ok) {
        const headers = new Headers(asset.headers);
        headers.set("X-Content-Type-Options", "nosniff");
        headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
        headers.set("X-Frame-Options", "SAMEORIGIN");
        headers.set("X-AITrove-Prerender", "HIT");
        return new Response(asset.body, { status: asset.status, headers });
      }
    }
    return app.fetch(request, env, context);
  },
};
`,
    resolveDir: output,
    sourcefile: "_worker.entry.js",
    loader: "js",
  },
  outfile: resolve(output, "_worker.js"),
  bundle: true,
  splitting: false,
  format: "esm",
  platform: "neutral",
  target: "es2022",
  external: ["node:*", "cloudflare:*"],
});

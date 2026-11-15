import { AwsClient } from "aws4fetch";

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.hostname === "www.dekhoexams.com") {
      url.hostname = "dekhoexams.com";
      return Response.redirect(url.href, 308);
    }
    const path = url.pathname;
    const media = path.startsWith("/jee-papers/") || path.startsWith("/jee-figures/");
    if (media && !/^\/(?:jee-papers\/[a-z0-9-]+\/[a-z0-9-]+\/[a-z0-9-]+\.pdf|jee-figures\/[a-f0-9]+\.png)$/.test(path)) return new Response(null, { status: 404 });
    if (media && !["GET", "HEAD"].includes(request.method)) return new Response(null, { status: 405, headers: { Allow: "GET, HEAD" } });
    const cacheable = request.method === "GET" && !url.search && !request.headers.has("authorization") &&
      !request.headers.has("cookie") && (media || path.startsWith("/assets/") || path.startsWith("/past-years/"));
    if (cacheable) {
      const hit = await caches.default.match(request);
      if (hit) return hit;
    }
    let response;
    if (media) {
      const s3 = new AwsClient({ accessKeyId: env.S3_KEY_ID, secretAccessKey: env.S3_SECRET, region: env.AWS_REGION, service: "s3", retries: 1 });
      const headers = new Headers();
      for (const name of ["Range", "If-None-Match", "If-Modified-Since"]) {
        if (request.headers.has(name)) headers.set(name, request.headers.get(name));
      }
      const upstream = await s3.fetch(`https://${env.MEDIA_BUCKET}.s3.${env.AWS_REGION}.amazonaws.com${path}`, { method: request.method, headers });
      const publicHeaders = new Headers();
      for (const name of ["Content-Length", "Content-Range", "Accept-Ranges", "Last-Modified", "ETag"]) {
        if (upstream.headers.has(name)) publicHeaders.set(name, upstream.headers.get(name));
      }
      if (!upstream.ok && upstream.status !== 304) {
        // S3 returns 403 for missing keys when the reader has no bucket listing permission.
        if (upstream.status === 403) console.warn("S3 denied GET or key is absent", path);
        publicHeaders.delete("Content-Length");
        await upstream.body?.cancel();
        return new Response(null, { status: upstream.status === 403 ? 404 : upstream.status, headers: publicHeaders });
      }
      publicHeaders.set("Content-Type", path.endsWith(".pdf") ? "application/pdf" : "image/png");
      publicHeaders.set("Cache-Control", "public, max-age=300, s-maxage=86400");
      publicHeaders.set("X-Content-Type-Options", "nosniff");
      if (path.endsWith(".pdf")) publicHeaders.set("X-Robots-Tag", "noindex, follow");
      response = new Response(upstream.body, { status: upstream.status, headers: publicHeaders });
    } else {
      const origin = new URL(env.APP_ORIGIN);
      if (origin.protocol !== "https:" || !env.ORIGIN_KEY) throw Error("Invalid origin configuration");
      const headers = new Headers(request.headers);
      headers.set("X-Dekho-Host", url.host);
      headers.set("X-Origin-Key", env.ORIGIN_KEY);
      url.host = origin.host;
      url.protocol = origin.protocol;
      response = await fetch(url, { method: request.method, headers, body: request.body, redirect: "manual" });
    }
    if (cacheable && response.status === 200 && !request.headers.has("range") &&
        !response.headers.has("set-cookie") && !/private|no-store|no-cache/i.test(response.headers.get("cache-control") || "")) {
      const cached = new Response(response.clone().body, response);
      cached.headers.set("Cache-Control", media ? "public, max-age=86400" : "public, max-age=300");
      ctx.waitUntil(caches.default.put(request, cached));
    }
    return response;
  },
};

import figures from "../../src/data/approved-diagrams.json" with { type: "json" };
import pdfs from "./approved-pdfs.json" with { type: "json" };
import { AwsClient } from "aws4fetch";

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.hostname === "www.dekhoexams.com") {
      url.hostname = "dekhoexams.com";
      return Response.redirect(url.href, 308);
    }
    const path = url.pathname;
    // Apply review before cache lookup, including on direct, range and conditional requests.
    let decoded;
    try { decoded = decodeURIComponent(path); } catch { return new Response(null, { status: 400 }); }
    const canonical = new URL(decoded.replaceAll("\\", "/").replace(/\/{2,}/g, "/"), url.origin).pathname;
    if (/^\/(?:jee-(?:figures|papers)|images\/jee-main-reviewed|verified-pdf)(?:\/|$)/i.test(canonical) &&
        (decoded !== path || canonical !== path || canonical.startsWith("/verified-pdf/"))) return new Response(null, { status: 404 });
    const diagram = path.startsWith("/jee-figures/") || path.startsWith("/images/jee-main-reviewed/");
    const pdf = path.startsWith("/jee-papers/");
    if ((diagram && !Object.hasOwn(figures, path)) || (pdf && !Object.hasOwn(pdfs, path))) {
      return new Response(null, { status: 404, headers: { "Cache-Control": "no-store", "X-Robots-Tag": "noindex" } });
    }
    const approved = pdf ? pdfs[path] : null;
    const originDiagram = path.startsWith("/images/jee-main-reviewed/");
    const media = pdf || diagram;
    const collectionPdf = /^\/jee-papers\/collections\/[a-z0-9-]+\/(?:[A-Za-z0-9_-]+\/)+[A-Za-z0-9_-]+\.pdf$/.test(path);
    if (media && !originDiagram && !collectionPdf && !/^\/(?:jee-papers\/[a-z0-9-]+\/[a-z0-9-]+\/[a-z0-9-]+\.pdf|jee-figures\/[a-f0-9]+\.png)$/.test(path)) return new Response(null, { status: 404 });
    if (media && !["GET", "HEAD"].includes(request.method)) return new Response(null, { status: 405, headers: { Allow: "GET, HEAD" } });
    // S3 keys are public editions; query strings and cookies do not select their contents.
    const page = path === "/" || path.startsWith("/past-years/") || path.startsWith("/pyq-pdfs/past-years/") || path === "/pdf-library" || path.startsWith("/pdf-library/");
    const trackingOnly = [...url.searchParams.keys()].every(key => /^utm_|^(gclid|fbclid)$/.test(key));
    const anonymous = !request.headers.has("authorization") &&
      !(request.headers.get("cookie") || "").split(";").some(cookie => cookie.trim() && !/^(_ga(?:_[A-Za-z0-9]+)?|_gid)=/.test(cookie.trim()));
    const html = !request.headers.has("accept") || /text\/html|\*\/\*/.test(request.headers.get("accept"));
    const publicPage = page && html && anonymous && trackingOnly && request.method === "GET" &&
      !request.headers.has("range") && !request.headers.has("x-tsr-serverfn");
    const cacheable = request.method === "GET" && !request.headers.has("if-range") &&
      (media || publicPage || (anonymous && !url.search && path.startsWith("/assets/")));
    const keyUrl = new URL(url);
    // Keep cached HTML aligned with the branded site release.
    if (publicPage || media) keyUrl.pathname = "/__edge/v36" + (media ? "/" + (approved?.sha ?? approved?.etag ?? figures[path]) : "") + path;
    if (media || publicPage) keyUrl.search = "";
    const cacheKey = new Request(keyUrl, { headers: media ? request.headers : undefined });
    // Old cached PDFs also need a download filename, including language editions named en.pdf.
    const pdfFilename = path.endsWith(".pdf") && media
      ? "DekhoExams-" + (collectionPdf ? path.split("/").slice(3).join("-").replace(/DekhoExams_/gi, "") : path.split("/").slice(2).join("-"))
      : null;
    if (cacheable) {
      const hit = await caches.default.match(cacheKey);
      if (hit) {
        const result = new Response(hit.body, hit);
        result.headers.set("X-Dekhoexams-Cache", "HIT");
        if (pdfFilename) result.headers.set("Content-Disposition", 'attachment; filename="' + pdfFilename + '"');
        return result;
      }
    }
    let response;
    if (originDiagram) {
      const upstream = await fetch(new URL(path, env.APP_ORIGIN), {headers:{"X-Origin-Key":env.ORIGIN_KEY, "X-Dekho-Host":url.hostname}, redirect:"manual"});
      if (!upstream.ok) return new Response(null,{status:upstream.status,headers:{"Cache-Control":"no-store"}});
      const bytes = await upstream.arrayBuffer();
      const hash = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",bytes)), b => b.toString(16).padStart(2,"0")).join("");
      if (hash !== figures[path]) return new Response(null,{status:503,headers:{"Cache-Control":"no-store"}});
      response = new Response(request.method === "HEAD" ? null : bytes,{headers:{
        "Content-Type":"image/png","Content-Length":String(bytes.byteLength), "ETag":'"'+hash+'"', "Cache-Control":"public, max-age=300, s-maxage=86400",
      }});
    } else if (media) {
      const s3 = new AwsClient({ accessKeyId: env.S3_KEY_ID, secretAccessKey: env.S3_SECRET, region: env.AWS_REGION, service: "s3", retries: 1 });
      const headers = new Headers();
      for (const name of ["Range"]) {
        if (request.headers.has(name)) headers.set(name, request.headers.get(name));
      }
      const validator = request.headers.get("if-range");
      if (validator && ![approved?.sha, approved?.etag, approved?.multipart, figures[path]].some(v => v && validator === '"' + v + '"')) headers.delete("Range");
      const objectPath = approved?.sha ? "/jee-papers/reviewed/" + approved.sha + ".pdf" : path;
      let upstream;
      let metadataOnly = false;
      if (approved?.sha && env.REVIEWED_PDFS_ON_ORIGIN === "true") {
        headers.set("X-Origin-Key", env.ORIGIN_KEY);
        headers.set("X-Dekho-Host", url.hostname);
        upstream = await fetch(new URL("/verified-pdf/" + approved.sha + ".pdf", env.APP_ORIGIN), { method: request.method, headers, redirect: "manual" });
        if (upstream.ok && upstream.headers.get("etag") !== '"' + approved.sha + '"') {
          await upstream.body?.cancel();
          return new Response(null, {status:503, headers:{"Cache-Control":"no-store"}});
        }
      } else {
        // Some edge locations turn signed HEAD into GET upstream. A one-byte signed GET keeps the signature valid.
        metadataOnly = request.method === "HEAD" && !headers.has("Range");
        if (metadataOnly) headers.set("Range", "bytes=0-0");
        upstream = await s3.fetch(`https://${env.MEDIA_BUCKET}.s3.${env.AWS_REGION}.amazonaws.com${objectPath}`, { method: "GET", headers });
        const etag = (upstream.headers.get("etag") || "").replaceAll('"', "");
        if ((upstream.ok || upstream.status === 304) && etag !== (approved?.etag ?? figures[path]) && (!approved?.multipart || etag !== approved.multipart)) {
          await upstream.body?.cancel();
          return new Response(null, {status: 503, headers: {"Cache-Control": "no-store"}});
        }
      }
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
      if (pdfFilename) {
        publicHeaders.set("X-Robots-Tag", "noindex, follow");
        publicHeaders.set("Content-Disposition", 'attachment; filename="' + pdfFilename + '"');
      }
      if (metadataOnly && upstream.status === 206) {
        const total = /^bytes 0-0\/(\d+)$/.exec(publicHeaders.get("Content-Range") || "")?.[1];
        if (!total) { await upstream.body?.cancel(); return new Response(null,{status:502}); }
        publicHeaders.set("Content-Length", total);
        publicHeaders.delete("Content-Range");
      }
      if (request.method === "HEAD") await upstream.body?.cancel();
      response = new Response(request.method === "HEAD" ? null : upstream.body, { status: metadataOnly && upstream.status === 206 ? 200 : upstream.status, headers: publicHeaders });
    } else {
      const origin = new URL(env.APP_ORIGIN);
      if (origin.protocol !== "https:" || !env.ORIGIN_KEY) throw Error("Invalid origin configuration");
      // Render a single anonymous HTML representation for the shared page key.
      const headers = publicPage ? new Headers({ Accept: "text/html" }) : new Headers(request.headers);
      if (publicPage) url.search = "";
      headers.set("X-Dekho-Host", url.host);
      headers.set("X-Origin-Key", env.ORIGIN_KEY);
      url.host = origin.host;
      url.protocol = origin.protocol;
      response = await fetch(url, { method: request.method, headers, body: request.body, redirect: "manual" });
    }
    if (cacheable && response.status === 200 && !request.headers.has("range") &&
        !response.headers.has("set-cookie") && !/private|no-store|no-cache/i.test(response.headers.get("cache-control") || "")) {
      response = new Response(response.body, response);
      response.headers.set("X-Dekhoexams-Cache", "MISS");
      const cached = response.clone();
      cached.headers.set("Cache-Control", media ? "public, max-age=300, s-maxage=86400" : "public, max-age=0, s-maxage=900");
      ctx.waitUntil(caches.default.put(new Request(keyUrl), cached));
    }
    return response;
  },
};

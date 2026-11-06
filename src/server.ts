import "./lib/error-capture";
import { seoFileResponse } from "./lib/seo.server";
import { IS_PREVIEW, isUtilityPath, normalizedContentPath } from "./lib/seo";
import { EDUCATION_ALIASES, educationPage, educationIndexable } from "./lib/education-catalog";

import { consumeLastCapturedError } from "./lib/error-capture";
import { renderErrorPage } from "./lib/error-page";

type ServerEntry = {
  fetch: (request: Request, env: unknown, ctx: unknown) => Promise<Response> | Response;
};

let serverEntryPromise: Promise<ServerEntry> | undefined;

async function getServerEntry(): Promise<ServerEntry> {
  if (!serverEntryPromise) {
    serverEntryPromise = import("@tanstack/react-start/server-entry").then(
      (m) => (m.default ?? m) as ServerEntry,
    );
  }
  return serverEntryPromise;
}

// h3 swallows in-handler throws into a normal 500 Response with body
// {"unhandled":true,"message":"HTTPError"} — try/catch alone never fires for those.
async function normalizeCatastrophicSsrResponse(response: Response): Promise<Response> {
  if (response.status < 500) return response;
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) return response;

  const body = await response.clone().text();
  if (!isH3SwallowedErrorBody(body)) return response;

  console.error(consumeLastCapturedError() ?? new Error(`h3 swallowed SSR error: ${body}`));
  return new Response(renderErrorPage(), {
    status: 500,
    headers: { "content-type": "text/html; charset=utf-8" },
  });
}

function isH3SwallowedErrorBody(body: string): boolean {
  try {
    const payload = JSON.parse(body) as { unhandled?: unknown; message?: unknown };
    return payload.unhandled === true && payload.message === "HTTPError";
  } catch {
    return false;
  }
}

function withPublicHeaders(response: Response, request: Request): Response {
  const headers = new Headers(response.headers);
  headers.set("X-Content-Type-Options", "nosniff");
  headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
  headers.set("X-Frame-Options", "SAMEORIGIN");
  const path = new URL(request.url).pathname;
  const education = educationPage(path);
  if (
    IS_PREVIEW ||
    (education && !educationIndexable(education)) ||
    isUtilityPath(path) ||
    response.status >= 400 ||
    /^\/(?:downloads|(?:java|learning)-coverage\.html)(?:\/|$)/.test(path)
  )
    headers.set("X-Robots-Tag", "noindex, follow");
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

function contentAliasRedirect(request: Request): Response | null {
  if (request.method !== "GET" && request.method !== "HEAD") return null;
  const url = new URL(request.url);
  const path = url.pathname;
  // Never rewrite assets, encoded paths, framework RPC or application operations.
  if (
    !/^\/[a-zA-Z0-9/-]*$/.test(path) ||
    /^\/(?:src|assets|logos|fonts|downloads|node_modules|_)(?:\/|$)/i.test(path) ||
    isUtilityPath(path)
  )
    return null;
  const normalized = normalizedContentPath(path);
  const normalizedPath = normalized ? `/${normalized}` : "/";
  const alias = EDUCATION_ALIASES[normalizedPath];
  const target = alias ?? normalizedPath;
  if (path === target) return null;
  url.pathname = target;
  return Response.redirect(url.href, alias ? 301 : 308);
}

function cacheablePublicPage(request: Request): boolean {
  // shortcut: preview HTML skips edge caching to keep hashed asset links current; version cache keys before enabling it.
  if (IS_PREVIEW) return false;
  if (request.method !== "GET" || request.headers.has("authorization") || request.headers.has("cookie"))
    return false;
  const url = new URL(request.url);
  return (
    !url.search &&
    /^\/[a-z0-9/-]*$/.test(url.pathname) &&
    !/^\/(?:src|assets|logos|fonts|downloads|node_modules|_)(?:\/|$)/.test(url.pathname) &&
    !isUtilityPath(url.pathname)
  );
}

export default {
  async fetch(request: Request, env: unknown, ctx: unknown) {
    try {
      if (new URL(request.url).hostname === "www.dekhoexams.com") {
        const canonical = new URL(request.url);
        canonical.hostname = "dekhoexams.com";
        return Response.redirect(canonical.href, 308);
      }
      const redirect = contentAliasRedirect(request);
      if (redirect) return withPublicHeaders(redirect, request);
      const seoFile = await seoFileResponse(request);
      if (seoFile) return withPublicHeaders(seoFile, request);
      const path = new URL(request.url).pathname;
      if (path === "/__data/cms-snapshot.txt")
        return withPublicHeaders(new Response("Not found", { status: 404 }), request);
      if (
        ["/java-coverage.html", "/learning-coverage.html"].includes(path) ||
        path.startsWith("/downloads/")
      ) {
        const assets = (env as { ASSETS?: { fetch(request: Request): Promise<Response> } }).ASSETS;
        if (assets) return withPublicHeaders(await assets.fetch(request), request);
      }
      const cache = cacheablePublicPage(request) && typeof caches !== "undefined"
        ? (caches as CacheStorage & { default: Cache }).default
        : null;
      const cached = await cache?.match(request);
      if (cached) {
        const response = withPublicHeaders(cached, request);
        response.headers.set("X-AITrove-Cache", "HIT");
        return response;
      }
      const handler = await getServerEntry();
      const response = await handler.fetch(request, env, ctx);
      const publicResponse = withPublicHeaders(await normalizeCatastrophicSsrResponse(response), request);
      if (
        cache &&
        publicResponse.status === 200 &&
        publicResponse.headers.get("content-type")?.includes("text/html") &&
        !publicResponse.headers.has("set-cookie")
      ) {
        const stored = publicResponse.clone();
        stored.headers.set("Cache-Control", "public, max-age=0, s-maxage=300");
        (ctx as { waitUntil(promise: Promise<unknown>): void }).waitUntil(cache.put(request, stored));
        publicResponse.headers.set("X-AITrove-Cache", "MISS");
      }
      return publicResponse;
    } catch (error) {
      console.error(error);
      return withPublicHeaders(
        new Response(renderErrorPage(), {
          status: 500,
          headers: { "content-type": "text/html; charset=utf-8" },
        }),
        request,
      );
    }
  },
};

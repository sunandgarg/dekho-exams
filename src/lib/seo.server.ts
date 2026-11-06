import type { Entry } from "./content-types";
import { canonicalUrl, IS_PREVIEW, isSeoReady, SITE_ORIGIN } from "./seo";
import {
  EDUCATION_PAGES,
  EDUCATION_ALIASES,
  educationIndexable,
  ownsEducationPath,
} from "./education-catalog";

const PAGE_SIZE = 1000;
const MAX_PAGES = 5000;
type SitemapEntry = Pick<Entry, "path" | "type" | "status" | "data" | "updated_at">;
type MetadataPage = { items: SitemapEntry[]; total: number; page: number; per_page: number };

function xmlEscape(value: string): string {
  return value.replace(
    /[<>&"']/g,
    (char) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;", "'": "&apos;" })[char]!,
  );
}

async function boundedJson(response: Response): Promise<unknown> {
  const reader = response.body?.getReader();
  if (!reader) throw new Error("CMS sitemap metadata response is empty.");
  const chunks: Uint8Array[] = [];
  let length = 0;
  try {
    while (true) {
      const next = await reader.read();
      if (next.done) break;
      length += next.value.length;
      if (length > 2 * 1024 * 1024) {
        await reader.cancel();
        throw new Error("CMS sitemap metadata exceeded 2 MB.");
      }
      chunks.push(next.value);
    }
  } finally {
    reader.releaseLock();
  }
  const bytes = new Uint8Array(length);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.length;
  }
  return JSON.parse(new TextDecoder().decode(bytes));
}

async function metadataPage(page: number): Promise<MetadataPage> {
  if (process.env["AITROVE_STATIC_EXPORT"] === "1") {
    const { snapshotSitemapPage } = await import("./cms-snapshot.server");
    return snapshotSitemapPage(page, PAGE_SIZE);
  }
  const base = process.env["WORDPRESS_URL"]?.trim();
  if (!base) {
    const { snapshotSitemapPage } = await import("./cms-snapshot.server");
    return snapshotSitemapPage(page, PAGE_SIZE);
  }
  const cms = new URL(base);
  if (cms.protocol !== "https:" && cms.hostname !== "localhost" && cms.hostname !== "127.0.0.1")
    throw new Error("WORDPRESS_URL must use HTTPS.");
  const url = new URL(`${cms.href.replace(/\/$/, "")}/wp-json/aitrove/v1/sitemap-entries`);
  url.searchParams.set("page", String(page));
  url.searchParams.set("per_page", String(PAGE_SIZE));
  try {
    const response = await fetch(url, {
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(4000),
    });
    if (!response.ok) throw new Error(`CMS sitemap metadata returned HTTP ${response.status}.`);
    const value = await boundedJson(response);
    if (!value || typeof value !== "object") throw new Error("Invalid CMS sitemap metadata.");
    const parsed = value as Partial<MetadataPage>;
    if (
      !Array.isArray(parsed.items) ||
      !Number.isSafeInteger(parsed.total) ||
      Number(parsed.total) < 0 ||
      parsed.page !== page ||
      parsed.per_page !== PAGE_SIZE ||
      parsed.items.length > PAGE_SIZE ||
      Number(parsed.total) > PAGE_SIZE * MAX_PAGES
    )
      throw new Error("Invalid or oversized CMS sitemap metadata pagination.");
    for (const item of parsed.items) {
      if (
        !item ||
        typeof item.path !== "string" ||
        typeof item.type !== "string" ||
        typeof item.updated_at !== "string" ||
        item.status !== "published"
      )
        throw new Error("Invalid CMS sitemap entry.");
    }
    return parsed as MetadataPage;
  } catch (error) {
    console.error("WordPress sitemap request failed; using published snapshot:", error);
    const { snapshotSitemapPage } = await import("./cms-snapshot.server");
    return snapshotSitemapPage(page, PAGE_SIZE);
  }
}

function urlset(items: SitemapEntry[], includeHome: boolean): string {
  const urls = includeHome
    ? ["", "about", "privacy"].map(
        (path) => `<url><loc>${xmlEscape(canonicalUrl(path))}</loc></url>`,
      )
    : [];
  for (const item of items.filter(
    (item) =>
      isSeoReady(item) &&
      !ownsEducationPath(`/${item.path}`) &&
      !EDUCATION_ALIASES[`/${item.path}`],
  )) {
    const date = Number.isFinite(Date.parse(item.updated_at))
      ? `<lastmod>${xmlEscape(new Date(item.updated_at).toISOString())}</lastmod>`
      : "";
    urls.push(`<url><loc>${xmlEscape(canonicalUrl(item.path))}</loc>${date}</url>`);
  }
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls.join("")}</urlset>`;
}

export async function seoFileResponse(request: Request): Promise<Response | null> {
  const url = new URL(request.url);
  if (request.method !== "GET" && request.method !== "HEAD") return null;
  if (url.pathname === "/robots.txt") {
    return new Response(
      request.method === "HEAD"
        ? null
        : IS_PREVIEW
          ? "User-agent: *\nDisallow: /\n"
          : `User-agent: *\nAllow: /\n\nSitemap: ${SITE_ORIGIN}/sitemap.xml\n`,
      {
        headers: {
          "content-type": "text/plain; charset=utf-8",
          "cache-control": "public, max-age=300",
        },
      },
    );
  }
  const match = url.pathname.match(/^\/sitemap(?:-(\d+|education))?\.xml$/);
  if (!match) return null;
  if (match[1] === "education") {
    const ready = IS_PREVIEW ? [] : EDUCATION_PAGES.filter(educationIndexable);
    const xml = `<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${ready.map((p) => `<url><loc>${xmlEscape(canonicalUrl(p.path))}</loc></url>`).join("")}</urlset>`;
    return new Response(request.method === "HEAD" ? null : xml, {
      headers: {
        "content-type": "application/xml; charset=utf-8",
        "cache-control": "public, max-age=300",
      },
    });
  }
  const page = match[1] ? Number(match[1]) : 1;
  if (!Number.isSafeInteger(page) || page < 1 || page > MAX_PAGES)
    return new Response("Sitemap not found.", { status: 404 });
  if (IS_PREVIEW) {
    if (match[1]) return new Response("Preview sitemap is empty.", { status: 404 });
    return new Response(request.method === "HEAD" ? null : urlset([], false), {
      headers: {
        "content-type": "application/xml; charset=utf-8",
        "x-robots-tag": "noindex",
        "cache-control": "public, max-age=60",
      },
    });
  }
  const result = await metadataPage(page);
  const pages = Math.max(1, Math.ceil(result.total / PAGE_SIZE));
  if (page > pages) return new Response("Sitemap not found.", { status: 404 });
  let xml: string;
  if (!match[1]) {
    const indexes = Array.from(
      { length: pages },
      (_, index) =>
        `<sitemap><loc>${xmlEscape(`${SITE_ORIGIN}/sitemap-${index + 1}.xml`)}</loc></sitemap>`,
    );
    indexes.unshift(
      `<sitemap><loc>${xmlEscape(`${SITE_ORIGIN}/sitemap-education.xml`)}</loc></sitemap>`,
    );
    xml = `<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${indexes.join("")}</sitemapindex>`;
  } else xml = urlset(result.items, page === 1);
  return new Response(request.method === "HEAD" ? null : xml, {
    headers: {
      "content-type": "application/xml; charset=utf-8",
      "cache-control": "public, max-age=300",
    },
  });
}

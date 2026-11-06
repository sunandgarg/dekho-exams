import { FEATURES, isPublicEntryType, isPublicPath, publicCopy } from "./features";
import { createServerFn } from "@tanstack/react-start";
import { decodeHTML } from "entities";
import { z } from "zod";
import { ENTRY_TYPES, type Entry, type EntryListItem } from "./content-types";

const listSchema = z.object({
  type: z.enum(ENTRY_TYPES).optional(),
  category: z.string().max(120).optional(),
  subject: z.string().max(120).optional(),
  difficulty: z.string().max(40).optional(),
  company: z.string().max(120).optional(),
  author: z.string().max(400).optional(),
  q: z.string().max(120).optional(),
  featured: z.boolean().optional(),
  potd: z.boolean().optional(),
  paths: z.array(z.string().max(400)).max(100).optional(),
  limit: z.number().int().min(1).max(100).optional(),
  offset: z.number().int().min(0).max(250000).optional(),
});
export type ListInput = z.infer<typeof listSchema>;

function cmsBaseUrl(): string | null {
  const value = process.env["WORDPRESS_URL"]?.trim();
  if (!value) return null;
  const url = new URL(value);
  if (url.protocol !== "https:" && url.hostname !== "localhost" && url.hostname !== "127.0.0.1") {
    throw new Error("WORDPRESS_URL must use HTTPS.");
  }
  return url.href.replace(/\/$/, "");
}

let cmsRetryAfter = 0;

async function wordpressGet<T>(endpoint: string, params: Record<string, string>): Promise<T> {
  if (Date.now() < cmsRetryAfter) throw new Error("WordPress is in a short retry window.");
  const base = cmsBaseUrl();
  if (!base) throw new Error("WordPress CMS is not configured. Set WORDPRESS_URL on the server.");
  const url = new URL(`${base}/wp-json/aitrove/v1/${endpoint}`);
  for (const [key, value] of Object.entries(params)) url.searchParams.set(key, value);
  // The public CMS endpoints are cached by the zone's narrow GET-only cache
  // rule. Keep this request ordinary so it shares that cache with sitemap reads.
  try {
    const response = await fetch(url, {
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(4000),
    });
    if (response.status === 429 || response.status >= 500) cmsRetryAfter = Date.now() + 120000;
    if (!response.ok) throw new Error(`WordPress returned HTTP ${response.status}.`);
    return (await response.json()) as T;
  } catch (error) {
    if (!(error instanceof Error && error.message === "WordPress returned HTTP 404."))
      cmsRetryAfter = Math.max(cmsRetryAfter, Date.now() + 120000);
    throw error;
  }
}

export const getEntryByPath = createServerFn({ method: "GET" })
  .validator((d) => z.object({ path: z.string().max(400) }).parse(d))
  .handler(async ({ data }): Promise<Entry | null> => {
    const path = data.path.replace(/^\/+|\/+$/g, "").toLowerCase();
    if (!path || !isPublicPath(path)) return null;
    if (process.env["AITROVE_STATIC_EXPORT"] === "1") {
      const { snapshotEntry } = await import("./cms-snapshot.server");
      return snapshotEntry(path);
    }
    if (!cmsBaseUrl()) {
      const { snapshotEntry } = await import("./cms-snapshot.server");
      return snapshotEntry(path);
    }
    try {
      const entry = await wordpressGet<Entry>("entry", { path });
      return isPublicEntryType(entry.type)
        ? { ...entry, title: decodeHTML(entry.title), body: publicCopy(entry.body), summary: publicCopy(entry.summary) }
        : null;
    } catch (error) {
      if (error instanceof Error && error.message === "WordPress returned HTTP 404.") return null;
      console.error("WordPress entry request failed; using published snapshot:", error);
      const { snapshotEntry } = await import("./cms-snapshot.server");
      return snapshotEntry(path);
    }
  });

export const listEntries = createServerFn({ method: "GET" })
  .validator((d) => listSchema.parse(d))
  .handler(
    async ({ data }): Promise<{ items: EntryListItem[]; total: number; error: string | null }> => {
      if (data.type && !isPublicEntryType(data.type)) return { items: [], total: 0, error: null };
      if (process.env["AITROVE_STATIC_EXPORT"] === "1") {
        const { snapshotList } = await import("./cms-snapshot.server");
        return snapshotList(data);
      }
      if (!cmsBaseUrl()) {
        const { snapshotList } = await import("./cms-snapshot.server");
        return snapshotList(data);
      }
      const params: Record<string, string> = {};
      for (const [key, value] of Object.entries(data)) {
        if (value !== undefined)
          params[key] = Array.isArray(value) ? value.join(",") : String(value);
      }
      if (!FEATURES.courses) params["exclude_types"] = "course";
      try {
        const result = await wordpressGet<{ items: EntryListItem[]; total: number; error: null }>(
          "entries",
          params,
        );
        return {
          ...result,
          items: result.items
            .filter((item) => isPublicEntryType(item.type))
            .map((item) => ({ ...item, title: decodeHTML(item.title), summary: publicCopy(item.summary) })),
        };
      } catch (error) {
        console.error("WordPress list request failed; using published snapshot:", error);
        const { snapshotList } = await import("./cms-snapshot.server");
        return snapshotList(data);
      }
    },
  );

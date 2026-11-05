import packedSnapshot from "@/data/cms-snapshot.txt?raw";
import { isPublicEntryType, publicCopy } from "./features";
import type { Entry, EntryListItem } from "./content-types";
import type { ListInput } from "./cms.functions";

type PackedRow = [
  string, string, string, string, string, string, string | null, string | null,
  string | null, string[], Entry["data"], string | null, boolean, number, string, string,
];

let loaded: Promise<Entry[]> | undefined;
function entries(): Promise<Entry[]> {
  loaded ??= (async () => {
    const binary = atob(packedSnapshot);
    const bytes = new Uint8Array(binary.length);
    for (let index = 0; index < binary.length; index++) bytes[index] = binary.charCodeAt(index);
    const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"));
    const rows = JSON.parse(await new Response(stream).text()) as PackedRow[];
    return rows.map((row) => ({
      id: row[0], type: row[1] as Entry["type"], path: row[2], title: row[3],
      summary: row[4], body: row[5], category: row[6], subject: row[7],
      difficulty: row[8], tags: row[9], data: row[10], potd_date: row[11],
      featured: row[12], sort_order: row[13], status: "published" as const,
      published_at: row[14], created_at: row[14], updated_at: row[15],
    }));
  })();
  return loaded;
}

export async function snapshotEntry(path: string): Promise<Entry | null> {
  const row = (await entries()).find((item) => item.path === path && isPublicEntryType(item.type));
  return row ? { ...row, summary: publicCopy(row.summary), body: publicCopy(row.body) } : null;
}

export async function snapshotList(input: ListInput): Promise<{
  items: EntryListItem[]; total: number; error: null;
}> {
  let rows = (await entries()).filter((row) => isPublicEntryType(row.type));
  if (input.type) rows = rows.filter((row) => row.type === input.type);
  if (input.category) rows = rows.filter((row) => row.category?.toLowerCase() === input.category?.toLowerCase());
  if (input.subject) rows = rows.filter((row) => row.subject === input.subject);
  if (input.company) rows = rows.filter((row) => {
    const data = row.data as { company?: string; companies?: string[] };
    return data.company === input.company || data.companies?.includes(input.company!);
  });
  if (input.author) rows = rows.filter((row) => (row.data as { author_path?: string }).author_path === input.author);
  if (input.difficulty) rows = rows.filter((row) => row.difficulty === input.difficulty);
  if (input.featured) rows = rows.filter((row) => row.featured);
  if (input.paths) rows = rows.filter((row) => input.paths?.includes(row.path));
  if (input.q) {
    const term = input.q.toLowerCase();
    rows = rows.filter((row) => `${row.title} ${row.summary}`.toLowerCase().includes(term));
  }
  if (input.potd) rows = rows.filter((row) => row.potd_date).sort((a, b) => (b.potd_date ?? "").localeCompare(a.potd_date ?? ""));
  else rows = rows.sort((a, b) => a.sort_order - b.sort_order || (b.published_at ?? "").localeCompare(a.published_at ?? ""));
  return {
    items: rows.slice(input.offset ?? 0, (input.offset ?? 0) + (input.limit ?? 24))
      .map(({ body: _body, ...item }) => ({ ...item, summary: publicCopy(item.summary) })),
    total: rows.length,
    error: null,
  };
}

export async function snapshotSitemapPage(page: number, size: number) {
  const ready = (await entries()).filter((row) =>
    isPublicEntryType(row.type) &&
    !!row.data && typeof row.data === "object" && !Array.isArray(row.data) &&
    row.data["seo_ready"] === true,
  ).sort((a, b) => a.path.localeCompare(b.path));
  return {
    items: ready.slice((page - 1) * size, page * size).map(({ path, type, status, data, updated_at }) => ({
      path, type, status, data: { seo_ready: true }, updated_at,
    })),
    total: ready.length, page, per_page: size,
  };
}

import { isPublicEntryType, publicCopy } from "./features";
import records from "@/data/fixtures.json";
import type { Entry, EntryListItem } from "./content-types";
import type { ListInput } from "./cms.functions";

const entries = records as Entry[];
export const fixtureEntry = (path: string): Entry | null => {
  const entry = entries.find(
    (row) => row.path === path && row.status === "published" && isPublicEntryType(row.type),
  );
  return entry
    ? { ...entry, body: publicCopy(entry.body), summary: publicCopy(entry.summary) }
    : null;
};

export function fixtureList(input: ListInput): {
  items: EntryListItem[];
  total: number;
  error: null;
} {
  let rows = entries.filter((row) => row.status === "published" && isPublicEntryType(row.type));
  if (input.type) rows = rows.filter((row) => row.type === input.type);
  if (input.category)
    rows = rows.filter((row) => row.category?.toLowerCase() === input.category?.toLowerCase());
  if (input.subject) rows = rows.filter((row) => row.subject === input.subject);
  if (input.company)
    rows = rows.filter((row) => {
      const d = row.data as { company?: string; companies?: string[] };
      return d.company === input.company || d.companies?.includes(input.company!);
    });
  if (input.author)
    rows = rows.filter(
      (row) => (row.data as { author_path?: string }).author_path === input.author,
    );
  if (input.difficulty) rows = rows.filter((row) => row.difficulty === input.difficulty);
  if (input.featured) rows = rows.filter((row) => row.featured);
  if (input.paths) rows = rows.filter((row) => input.paths?.includes(row.path));
  if (input.q) {
    const term = input.q.toLowerCase();
    rows = rows.filter((row) => `${row.title} ${row.summary}`.toLowerCase().includes(term));
  }
  if (input.potd)
    rows = rows
      .filter((row) => row.potd_date)
      .sort((a, b) => (b.potd_date ?? "").localeCompare(a.potd_date ?? ""));
  else
    rows = rows.sort(
      (a, b) =>
        a.sort_order - b.sort_order || (b.published_at ?? "").localeCompare(a.published_at ?? ""),
    );
  const total = rows.length;
  return {
    items: rows
      .slice(input.offset ?? 0, (input.offset ?? 0) + (input.limit ?? 24))
      .map(({ body: _body, ...item }) => ({ ...item, summary: publicCopy(item.summary) })),
    total,
    error: null,
  };
}

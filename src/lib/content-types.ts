export type Json = string | number | boolean | null | { [key: string]: Json | undefined } | Json[];

export const ENTRY_TYPES = [
  "subject",
  "article",
  "category",
  "problem",
  "course",
  "video",
  "event",
  "job",
  "business",
  "page",
  "quiz",
  "path",
  "company",
  "author",
] as const;
export type EntryType = (typeof ENTRY_TYPES)[number];

export type Entry = {
  id: string;
  type: EntryType;
  path: string;
  title: string;
  summary: string;
  body: string;
  category: string | null;
  subject: string | null;
  difficulty: string | null;
  tags: string[];
  data: Json;
  potd_date: string | null;
  featured: boolean;
  sort_order: number;
  status: "draft" | "published";
  published_at: string | null;
  created_at: string;
  updated_at: string;
};

export type EntryListItem = Omit<Entry, "body">;

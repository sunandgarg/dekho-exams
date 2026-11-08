import { createServerFn } from "@tanstack/react-start";
import { env } from "cloudflare:workers";
import type { ArchiveId } from "./jee-catalog";
import { z } from "zod";

export type ArchiveRow = { id: string; teaser: string; group: string; paper: string };
export type ArchiveQuestion = {
  slug: string;
  teaser: string;
  qid?: string;
  paper: string;
  paperTitle?: string;
  subject: string;
  chapter: string;
  body: string;
  kind: string;
  options: string[];
  solution: string;
  complete: boolean;
  numericKey?: number;
  choiceKey?: number;
  choiceKeys?: number[];
  numericRange?: [number, number];
  hi?: { body: string; options: string[]; solution: string };
  canonical?: string;
  prev: string | null;
  next: string | null;
};
const segment = z
  .string()
  .max(220)
  .regex(/^[a-z0-9][a-z0-9-]*$/);
const questionId = z
  .string()
  .max(240)
  .regex(/^[A-Za-z0-9][A-Za-z0-9-]*(?:\.htm)?$/);
const examSchema = z.enum(["jee-main", "jee-advanced"]);
async function asset<T>(exam: ArchiveId, path: string): Promise<T | null> {
  const res = await env.ASSETS.fetch(
    new Request(
      "https://dekhoexams.com/" +
        (exam === "jee-main" ? "jee-archive" : "jee-advanced-archive") +
        "/" +
        path +
        ".bin",
    ),
  );
  if (res.status === 404) return null;
  if (!res.ok || !res.body) throw new Error("Question archive temporarily unavailable.");
  return (await new Response(res.body.pipeThrough(new DecompressionStream("gzip"))).json()) as T;
}
export const archiveList = createServerFn({ method: "GET" })
  .validator((x) =>
    z
      .union([
        z.object({ exam: examSchema, subject: segment, chapter: segment }),
        z.object({ exam: examSchema, paper: segment }),
      ])
      .parse(x),
  )
  .handler(({ data }) =>
    asset<ArchiveRow[]>(
      data.exam,
      "paper" in data ? "paper/" + data.paper : "chapter/" + data.subject + "/" + data.chapter,
    ),
  );
export const archiveQuestion = createServerFn({ method: "GET" })
  .validator((x) => z.object({ id: z.string(), exam: examSchema.optional() }).parse(x))
  .handler(async ({ data }) => {
    if (!questionId.safeParse(data.id).success) return null;
    const digest = new Uint8Array(
      await crypto.subtle.digest("SHA-256", new TextEncoder().encode(data.id)),
    );
    const path = "q/" + digest[0]!.toString(16).padStart(2, "0") + (digest[1]! >> 4).toString(16);
    const owners: ArchiveId[] = data.exam ? [data.exam] : ["jee-main", "jee-advanced"];
    for (const exam of owners) {
      const shard = await asset<Record<string, ArchiveQuestion>>(exam, path);
      if (shard && Object.hasOwn(shard, data.id)) return { ...shard[data.id]!, exam };
    }
    return null;
  });
export type ChapterMeta = { stats: string[][]; pdfs: Record<string, string> };
export const archiveChapterMeta = createServerFn({ method: "GET" })
  .validator((x) => z.object({ exam: examSchema, subject: segment, chapter: segment }).parse(x))
  .handler(({ data }) =>
    asset<ChapterMeta>(data.exam, "meta/" + data.subject + "/" + data.chapter),
  );

import { createServerFn } from "@tanstack/react-start";
import { env } from "cloudflare:workers";
import { z } from "zod";

const lessonSchema = z.object({
  title: z.string().min(1).max(160),
  summary: z.string().min(1).max(600),
  keyIdea: z.string().min(1).max(3000),
  whyItWorks: z.string().min(1).max(3000),
  commonMistake: z.string().min(1).max(3000),
  example: z.string().min(1).max(3000),
  steps: z.array(z.string().min(1).max(1000)).min(1).max(8),
  check: z.string().min(1).max(3000),
});

export const getSchoolLesson = createServerFn({ method: "GET" })
  .validator((data) => z.object({ id: z.string().regex(/^pp-\d{4}$/) }).parse(data))
  .handler(async ({ data }) => {
    const origin = env.SCHOOL_WORDPRESS_URL?.trim();
    if (!origin) return null;
    const base = new URL(origin);
    if (base.protocol !== "https:" && !["localhost", "127.0.0.1"].includes(base.hostname))
      throw new Error("SCHOOL_WORDPRESS_URL must use HTTPS.");
    const url = new URL("/wp-json/dekhoexams/v1/lesson", base);
    url.searchParams.set("id", data.id);
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(4000) });
      if (response.status === 404) return null;
      if (!response.ok) throw new Error(`WordPress returned HTTP ${response.status}.`);
      return lessonSchema.parse(await response.json());
    } catch (error) {
      console.error("School WordPress request failed; using local lesson:", error);
      return null;
    }
  });

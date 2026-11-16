import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";
import { pdfExams, type PdfEntry } from "./pdf-library";

export const getPdfPage = createServerFn({ method: "GET" })
  .validator((value: unknown) => z.string().max(400).parse(value))
  .handler(async ({ data }) => {
    const [exam, ...segments] = data.split("/");
    if (!exam || !Object.hasOwn(pdfExams, exam)) return null;
    const catalog: Record<string, PdfEntry[]> = (
      await import("../data/published-pdf-collections.json")
    ).default;
    const entries = catalog[exam]!;
    const name = pdfExams[exam]!;
    if (!segments.length)
      return {
        exam,
        name,
        entries: entries.map(({ path, title, subject, year, kind }) => ({
          path,
          title,
          subject,
          year,
          kind,
        })),
        entry: null,
      };
    const entry = entries.find((row) => row.path === segments.join("/"));
    return entry ? { exam, name, entries: [], entry } : null;
  });

const browseInput = z.object({
  exam: z.string().max(40),
  kind: z.enum(["paper", "chapter"]),
  subject: z.string().max(60).optional(),
});
export const getPdfBrowse = createServerFn({ method: "GET" })
  .validator((v: unknown) => browseInput.parse(v))
  .handler(async ({ data }) =>
    (await import("./pdf-browse.server")).browsePdfExam(data.exam, data.kind, data.subject),
  );

export const getArchivePdf = createServerFn({ method: "GET" })
  .validator((v: unknown) =>
    z.object({ exam: z.enum(["jee-main", "jee-advanced"]), edition: z.string().max(200) }).parse(v),
  )
  .handler(async ({ data }) => {
    const kind = data.edition.includes("--") ? "chapter" : "paper";
    return (
      (await import("./pdf-browse.server"))
        .browsePdfExam(data.exam, kind)
        ?.entries.find((e) => e.archiveSlug === data.edition)?.file ?? null
    );
  });

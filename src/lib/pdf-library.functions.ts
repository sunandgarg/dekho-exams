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

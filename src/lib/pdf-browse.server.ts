import collections from "@/data/published-pdf-collections.json";
import variants from "@/data/jee-main-pdf-papers.json";
import { archiveCatalog, isArchive } from "./jee-catalog";
import { pdfExams, type PdfEntry, type PdfKind } from "./pdf-library";

const catalogs: Record<string, PdfEntry[]> = collections;
const key = (s: string) =>
  s
    .toLowerCase()
    .replace(/\b(?:online|offline)\b/g, "")
    .replace(/&/g, "and")
    .replace(/[^a-z0-9]/g, "");
type ArchiveInfo = { slug: string; order: number; date?: string; unit?: string };

function archiveInfo(exam: string, kind: PdfKind) {
  const info = new Map<string, ArchiveInfo>();
  if (!isArchive(exam)) return info;
  const c = archiveCatalog(exam);
  if (kind === "paper") {
    c.papers.forEach((p, order) => info.set(key(p.title), { slug: p.slug, date: p.date, order }));
  } else {
    for (const [subject, chapters] of Object.entries(c.chapters)) {
      for (const slug of chapters) {
        const meta = c.meta[subject + "/" + slug];
        if (meta)
          info.set(subject + "/" + key(meta.name), {
            slug: subject + "--" + slug,
            unit: meta.unit,
            order: info.size,
          });
      }
    }
  }
  return info;
}
export function browsePdfExam(exam: string, kind: PdfKind, subject?: string) {
  if (!Object.hasOwn(pdfExams, exam)) return null;
  const info = archiveInfo(exam, kind);
  const entries = (catalogs[exam] ?? [])
    .filter((e) => e.kind === kind && (!subject || e.subject.toLowerCase() === subject))
    .map((e) => {
      const archive = info.get(
        (kind === "chapter" ? e.subject.toLowerCase() + "/" : "") + key(e.title),
      );
      const slug = archive?.slug || "";
      const editions =
        exam === "jee-main" && Object.hasOwn(variants, slug)
          ? variants[slug as keyof typeof variants]
          : null;
      return {
        path: e.path,
        title: e.title,
        file: e.file,
        year: e.year,
        subject: e.subject,
        pages: e.pages,
        questions: e.questions,
        date: archive?.date || e.date,
        unit: archive?.unit || "",
        order: archive?.order ?? 0,
        archiveSlug: slug,
        languages: editions?.languages ?? [],
      };
    });
  entries.sort((a, b) =>
    kind === "paper" ? b.year - a.year || a.order - b.order : a.order - b.order,
  );
  return entries.length ? { exam, name: pdfExams[exam], kind, subject, entries } : null;
}
export type PdfBrowse = NonNullable<ReturnType<typeof browsePdfExam>>;

import { notFound } from "@tanstack/react-router";
import mainChapters from "@/data/jee-main-chapters.json";
import mainMeta from "@/data/jee-main-chapter-meta.json";
import mainCounts from "@/data/jee-main-counts.json";
import mainPapers from "@/data/jee-main-papers.json";
import mainHindi from "@/data/jee-main-hindi-print.json";
import advancedChapters from "@/data/jee-advanced-chapters.json";
import advancedMeta from "@/data/jee-advanced-chapter-meta.json";
import advancedCounts from "@/data/jee-advanced-counts.json";
import advancedPapers from "@/data/jee-advanced-papers.json";
import advancedHindi from "@/data/jee-advanced-hindi-print.json";

export type ArchiveId = "jee-main" | "jee-advanced";
export type ArchivePaper = (typeof mainPapers)[number];
export function isArchive(id: unknown): id is ArchiveId {
  return id === "jee-main" || id === "jee-advanced";
}
export function archiveCatalog(id: string) {
  if (!isArchive(id)) throw notFound();
  const main = id === "jee-main";
  const jeeHub = "/past-years/jee/" + id,
    paperHub = "/past-years/year-wise/jee/" + id;
  return {
    id,
    name: main ? "JEE Main" : "JEE Advanced",
    jeeHub,
    paperHub,
    pdfHub: "/pyq-pdfs" + paperHub,
    chapters: (main ? mainChapters : advancedChapters) as Record<string, string[]>,
    meta: (main ? mainMeta : advancedMeta) as Record<
      string,
      { name: string; unit: string; latest: string }
    >,
    counts: (main ? mainCounts : advancedCounts) as Record<string, number>,
    papers: (main ? mainPapers : advancedPapers) as ArchivePaper[],
    hindiPrint: (main ? mainHindi : advancedHindi) as string[],
    printPrefix: main ? "/pyq-pdfs/print/" : "/pyq-pdfs/print/jee-advanced/",
  };
}
export function archiveUnits(id: ArchiveId, subject: string) {
  const catalog = archiveCatalog(id);
  const groups = new Map<string, [string, string][]>();
  for (const slug of catalog.chapters[subject] ?? []) {
    const entry = catalog.meta[subject + "/" + slug];
    if (!entry) continue;
    if (!groups.has(entry.unit)) groups.set(entry.unit, []);
    groups.get(entry.unit)!.push([slug, entry.name]);
  }
  return [...groups].map(([name, chapters]) => ({ name, chapters }));
}
export function questionKind(kind: string) {
  return (
    (
      {
        mcq: "Single correct",
        mcqm: "Multiple correct",
        integer: "Numerical",
        subjective: "Written response",
        "fill-blanks": "Fill in the blanks",
        tf: "True or false",
        "t/f": "True or false",
      } as Record<string, string>
    )[kind] ?? kind.replaceAll("-", " ")
  );
}

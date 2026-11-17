import figures from "../data/approved-diagrams.json" with { type: "json" };
import type { ArchiveQuestion } from "./jee-archive.functions";

export function reviewedHtml(html: string) {
  return html.replace(/<img\b[^>]*>/gi, tag => {
    const src = /\bsrc="([^"]+)"/.exec(tag)?.[1] ?? "";
    return Object.hasOwn(figures, src) ? tag : '<span class="jee-figure-pending">Diagram pending review</span>';
  });
}
export function reviewedQuestion<T extends ArchiveQuestion>(q: T): T {
  const edition = (e: Pick<ArchiveQuestion, "body" | "options" | "solution">) => ({
    body: reviewedHtml(e.body), options: e.options.map(reviewedHtml), solution: reviewedHtml(e.solution),
  });
  return { ...q, ...edition(q), ...(q.hi && { hi: edition(q.hi) }) };
}

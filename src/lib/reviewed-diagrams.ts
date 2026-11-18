import figures from "../data/approved-diagrams.json" with { type: "json" };
import type { ArchiveQuestion } from "./jee-archive.functions";

export function reviewedHtml(html: string) {
  return html.replace(/<img\b[^>]*>/gi, tag => {
    const src = /\ssrc=(["'])(.*?)\1/i.exec(tag);
    const path = (src?.[2] ?? "").split(/[?#]/)[0] ?? "";
    if (!src || !Object.hasOwn(figures, path)) return '<span class="jee-figure-pending">Diagram pending review</span>';
    // A revised image must not reuse a student's previously cached copy.
    return tag.replace(src[0], ' src="' + path + '?v=' + figures[path as keyof typeof figures] + '"');
  });
}
export function reviewedQuestion<T extends ArchiveQuestion>(q: T): T {
  const edition = (e: Pick<ArchiveQuestion, "body" | "options" | "solution">) => ({
    body: reviewedHtml(e.body), options: e.options.map(reviewedHtml), solution: reviewedHtml(e.solution),
  });
  return { ...q, ...edition(q), ...(q.hi && { hi: edition(q.hi) }) };
}

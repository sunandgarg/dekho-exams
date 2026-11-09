import type { ArchiveQuestion } from "./jee-archive.functions";

export const JEE_SITEMAPS = ["jee-main", "jee-main-questions", "jee-advanced", "jee-advanced-questions"];

export function releasedSearchPath(path: string) {
  return /^\/?$/.test(path) || /^\/?(?:pyq-pdfs\/)?past-years\/(?:year-wise\/)?jee\/(?:jee-main|jee-advanced|question)(?:\/|$)/.test(path);
}

export function readyQuestion(q?: ArchiveQuestion | null) {
  return !!q?.complete && !q.canonical && [q, q.hi].every(ed =>
    ed && ed.body && ed.solution && ![ed.body, ...ed.options, ed.solution].some(s => s.includes("jee-figure-pending"))
  );
}

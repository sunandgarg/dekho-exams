import type { ArchiveQuestion } from "./jee-archive.functions";
export type Item = Pick<
  ArchiveQuestion,
  | "body"
  | "subject"
  | "options"
  | "solution"
  | "kind"
  | "choiceKey"
  | "numericKey"
  | "numericRange"
  | "choiceKeys"
> & { review?: string };
export const validNumber = (s: string) => /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$/.test(s);
export const answerKey = (q: Item) =>
  q.choiceKeys ?? (q.choiceKey === undefined ? [] : [q.choiceKey]);
export const correct = (q: Item, v: string) => {
  if (q.review || !v) return false;
  if (q.options.length) return v === answerKey(q).join(",");
  const n = Number(v);
  return (
    validNumber(v) &&
    (q.numericRange ? n >= q.numericRange[0] && n <= q.numericRange[1] : n === q.numericKey)
  );
};
export const displayKey = (q: Item) =>
  q.options.length
    ? answerKey(q)
        .map((i) => String.fromCharCode(65 + i))
        .join(", ")
    : (q.numericRange?.join(" to ") ?? q.numericKey);

export const selectQuestions = (items: Item[], scoredOnly: boolean) =>
  items.map((q, i) => ({ ...q, number: i + 1 })).filter((q) => !scoredOnly || !q.review);

export function summarize(items: Item[], answers: string[]) {
  const graded = items.filter((q) => !q.review).length;
  const attempted = items.filter((q, i) => !q.review && answers[i]).length;
  const hits = items.filter((q, i) => correct(q, answers[i] ?? "")).length;
  const misses = attempted - hits;
  const score = 4 * hits - misses;
  return {
    graded,
    hits,
    misses,
    score,
    max: 4 * graded,
    skipped: graded - attempted,
    review: items.length - graded,
    readiness: graded ? Math.round((Math.max(0, score) / (4 * graded)) * 100) : null,
  };
}

export function performance(items: Item[], answers: string[]) {
  const s = summarize(items, answers);
  const attempted = s.hits + s.misses;
  return {
    ...s,
    attempted,
    accuracy: attempted ? Math.round((100 * s.hits) / attempted) : null,
    attemptRate: s.graded ? Math.round((100 * attempted) / s.graded) : null,
    earned: 4 * s.hits,
    penalty: s.misses,
  };
}

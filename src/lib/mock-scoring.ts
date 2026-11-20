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
  | "numericKeys"
  | "numericRange"
  | "numericRanges"
  | "textKeys"
  | "choiceKeys"
  | "choiceKeySets"
> & { review?: string };
export const validNumber = (s: string) => /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$/.test(s);
export const normalizeTextAnswer = (s: string) =>
  s
    .normalize("NFKC")
    .trim()
    .toLocaleLowerCase("en")
    .replace(/[−–—]/g, "-")
    .replace(/\s+/g, " ")
    .replace(/\s*([/%°])\s*/g, "$1");
export const answerKey = (q: Item) =>
  q.choiceKeys ?? q.choiceKeySets?.[0] ?? (q.choiceKey === undefined ? [] : [q.choiceKey]);
export const acceptedChoiceIndices = (q: Item) =>
  [...new Set((q.choiceKeySets ?? [answerKey(q)]).flat())];
export const hasAnswerKey = (q: Item) =>
  q.options.length
    ? answerKey(q).length > 0
    : q.numericKey !== undefined ||
      Boolean(q.numericKeys?.length) ||
      Boolean(q.numericRange) ||
      Boolean(q.numericRanges?.length) ||
      Boolean(q.textKeys?.length);
export const correct = (q: Item, v: string) => {
  if (q.review || !v) return false;
  if (q.options.length) {
    const accepted = q.choiceKeySets ?? [answerKey(q)];
    return accepted.some((key) => v === key.join(","));
  }
  const trimmed = v.trim();
  if (q.textKeys?.some((key) => normalizeTextAnswer(key) === normalizeTextAnswer(trimmed))) return true;
  if (!validNumber(trimmed)) return false;
  const n = Number(trimmed);
  if (q.numericKey !== undefined && n === q.numericKey) return true;
  if (q.numericKeys?.includes(n)) return true;
  if (q.numericRange && n >= q.numericRange[0] && n <= q.numericRange[1]) return true;
  return Boolean(q.numericRanges?.some(([min, max]) => n >= min && n <= max));
};
export const displayKey = (q: Item) =>
  q.options.length
    ? (q.choiceKeySets ?? [answerKey(q)])
        .map((key) => key.map((i) => String.fromCharCode(65 + i)).join(", "))
        .join(" or ")
    : (q.textKeys?.join(" or ") ??
      q.numericRanges?.map((range) => range.join(" to ")).join(" or ") ??
      q.numericRange?.join(" to ") ??
      q.numericKeys?.join(" or ") ??
      q.numericKey);

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

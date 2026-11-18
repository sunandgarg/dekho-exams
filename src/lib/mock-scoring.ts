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

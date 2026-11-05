import { expect, test } from "bun:test";
import { EXAMS, QUESTIONS, examBySlug, scoreAttempt } from "../src/lib/question-bank";

test("JEE Main practice marking: +4 correct, -1 wrong option, 0 skipped", () => {
  const m = examBySlug("jee-main")!.marking;
  const [a, b, c] = QUESTIONS.filter((q) => q.exam === "jee-main" && q.type === "mcq");
  const r = scoreAttempt(m, [a!, b!, c!], { [a!.id]: a!.answer, [b!.id]: (b!.answer + 1) % 4, [c!.id]: null });
  expect(r).toEqual({ score: 3, max: 12, correct: 1, wrong: 1, unattempted: 1 });
});

test("wrong numerical answers carry no negative mark", () => {
  const q = QUESTIONS.find((x) => x.exam === "jee-main" && x.type === "numeric")!;
  expect(scoreAttempt(examBySlug("jee-main")!.marking, [q], { [q.id]: q.answer + 5 }).score).toBe(0);
});

test("every question points to a real exam/subject/chapter and has no unverified year", () => {
  for (const q of QUESTIONS) {
    const sub = EXAMS.find((e) => e.slug === q.exam)?.subjects.find((s) => s.slug === q.subject);
    expect(sub?.chapters.some(([c]) => c === q.chapter)).toBe(true);
    expect(q.year).toBeNull();
    if (q.type === "mcq") expect(q.answer).toBeLessThan(q.options!.length);
  }
  expect(new Set(QUESTIONS.map((q) => q.id)).size).toBe(QUESTIONS.length);
});

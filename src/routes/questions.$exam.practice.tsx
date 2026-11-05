import { useEffect, useState } from "react";
import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { seoHead } from "@/lib/seo";
import { examBySlug, isCorrect, questionsFor, scoreAttempt, type Question } from "@/lib/question-bank";
import { useQuestionProgress } from "@/lib/question-progress";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export const Route = createFileRoute("/questions/$exam/practice")({
  loader: ({ params }) => {
    const exam = examBySlug(params.exam);
    if (!exam) throw notFound();
    return { slug: exam.slug, name: exam.name };
  },
  head: ({ loaderData }) => seoHead({
    title: loaderData ? `${loaderData.name} Timed Practice | Pencil2Pen` : "Exam not found | Pencil2Pen",
    description: loaderData ? `Timed ${loaderData.name} practice set with instant scoring.` : "This exam is not in the question bank.",
    path: loaderData ? `questions/${loaderData.slug}/practice` : "questions",
    noindex: true,
  }),
  notFoundComponent: () => <div className="study-home"><h1>Exam not found</h1><Link to="/questions">Back to the question bank</Link></div>,
  component: PracticePage,
});

const fmt = (s: number) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;

function PracticePage() {
  const exam = examBySlug(Route.useLoaderData().slug)!;
  const p = useQuestionProgress();
  const [subject, setSubject] = useState("all");
  const [minutes, setMinutes] = useState(10);
  const [set, setSet] = useState<Question[] | null>(null);
  const [res, setRes] = useState<Record<string, number | null>>({});
  const [left, setLeft] = useState(0);
  const [done, setDone] = useState(false);
  const pool = questionsFor(exam.slug, subject === "all" ? undefined : subject);

  function submit() {
    if (!set || done) return;
    setDone(true);
    for (const q of set) {
      const r = res[q.id];
      if (r !== null && r !== undefined && !Number.isNaN(r)) p.record(q.id, r, isCorrect(q, r));
    }
  }
  useEffect(() => {
    if (!set || done) return;
    if (left <= 0) { submit(); return; }
    const t = setTimeout(() => setLeft((l) => l - 1), 1000);
    return () => clearTimeout(t);
  });

  if (!set) {
    return (
      <div className="study-home study-lesson">
        <p className="text-sm"><Link to="/questions">Question Bank</Link> / <Link to="/questions/$exam" params={{ exam: exam.slug }}>{exam.name}</Link> / Timed practice</p>
        <h1>{exam.name} timed practice</h1>
        <p className="study-intro">
          A short practice set from the questions we have so far. It is not a full mock test. Scoring uses practice marks: +{exam.marking.correct} for correct, {exam.marking.wrong.toFixed(2).replace(/\.00$/, "")} for a wrong option, 0 for a wrong numerical answer or a skipped question.
        </p>
        <div className="my-5 flex flex-wrap items-end gap-4">
          <label className="grid gap-1 text-sm">Subject
            <select className="rounded-lg border bg-background px-3 py-2" value={subject} onChange={(e) => setSubject(e.target.value)}>
              <option value="all">All subjects</option>
              {exam.subjects.map((s) => <option key={s.slug} value={s.slug}>{s.name}</option>)}
            </select>
          </label>
          <label className="grid gap-1 text-sm">Minutes
            <Input type="number" min={1} max={180} value={minutes} onChange={(e) => setMinutes(Math.max(1, Math.min(180, Number(e.target.value) || 1)))} className="w-24" />
          </label>
          <Button disabled={pool.length === 0} onClick={() => {
            setSet([...pool].sort(() => Math.random() - 0.5).slice(0, 20)); setRes({}); setDone(false); setLeft(minutes * 60);
          }}>Start ({Math.min(20, pool.length)} questions)</Button>
        </div>
        {pool.length === 0 && <p>No questions are written for this selection yet.</p>}
      </div>
    );
  }

  const result = scoreAttempt(exam.marking, set, res);
  return (
    <div className="study-home study-lesson">
      <div className="sticky top-0 z-10 mb-4 flex items-center justify-between rounded-lg border bg-background px-4 py-3">
        <b>{done ? "Finished" : `Time left ${fmt(left)}`}</b>
        {!done ? <Button size="sm" onClick={submit}>Submit</Button> : <Button size="sm" variant="outline" onClick={() => setSet(null)}>New set</Button>}
      </div>
      {done && (
        <section className="mb-6 rounded-xl border bg-card p-5">
          <h2>Score: {result.score} / {result.max}</h2>
          <p>Correct {result.correct} · Wrong {result.wrong} · Skipped {result.unattempted}</p>
        </section>
      )}
      <ol className="grid gap-4">
        {set.map((q, i) => {
          const r = res[q.id];
          const ok = isCorrect(q, r);
          return (
            <li key={q.id} className="rounded-xl border bg-card p-5">
              <p className="mb-3 font-medium"><b>Q{i + 1}.</b> {q.text}</p>
              {q.type === "mcq" ? (
                <div className="grid gap-2">
                  {q.options!.map((o, j) => (
                    <button key={j} type="button" disabled={done} aria-pressed={r === j}
                      onClick={() => setRes({ ...res, [q.id]: r === j ? null : j })}
                      className={`rounded-lg border px-4 py-2 text-left text-sm ${r === j ? "border-primary bg-primary/10" : ""} ${done && j === q.answer ? "border-primary font-bold" : ""}`}>
                      {String.fromCharCode(65 + j)}. {o}
                    </button>
                  ))}
                </div>
              ) : (
                <Input inputMode="decimal" disabled={done} aria-label={`Answer for question ${i + 1}`} className="max-w-xs"
                  value={r === null || r === undefined ? "" : String(r)}
                  onChange={(e) => setRes({ ...res, [q.id]: e.target.value.trim() === "" ? null : Number(e.target.value) })} />
              )}
              {done && (
                <div className="mt-3 rounded-lg bg-muted p-3 text-sm">
                  <p className={`font-bold ${ok ? "text-primary" : "text-destructive"}`}>{r === null || r === undefined ? "Skipped" : ok ? "Correct" : "Wrong"} · Answer: {q.type === "mcq" ? String.fromCharCode(65 + q.answer) : q.answer}</p>
                  <p>{q.solution}</p>
                </div>
              )}
            </li>
          );
        })}
      </ol>
    </div>
  );
}

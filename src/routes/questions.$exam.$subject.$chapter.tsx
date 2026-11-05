import { useState } from "react";
import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { seoHead } from "@/lib/seo";
import { chapterName, examBySlug, questionsFor, subjectOf } from "@/lib/question-bank";
import { PracticeNotice, QuestionCard } from "@/components/question-bank";
import { useQuestionProgress } from "@/lib/question-progress";

export const Route = createFileRoute("/questions/$exam/$subject/$chapter")({
  loader: ({ params }) => {
    const exam = examBySlug(params.exam);
    const sub = exam && subjectOf(exam, params.subject);
    const chap = sub && chapterName(sub, params.chapter);
    if (!exam || !sub || !chap) throw notFound();
    return { exam: exam.slug, examName: exam.name, subject: sub.slug, subjectName: sub.name, chapter: params.chapter, chapterName: chap };
  },
  head: ({ loaderData: d }) => seoHead({
    title: d ? `${d.chapterName} — ${d.examName} ${d.subjectName} Questions | Pencil2Pen` : "Chapter not found | Pencil2Pen",
    description: d ? `Practise ${d.chapterName} questions for ${d.examName} ${d.subjectName} with step-by-step solutions.` : "This chapter is not in the question bank.",
    path: d ? `questions/${d.exam}/${d.subject}/${d.chapter}` : "questions",
    noindex: true,
  }),
  notFoundComponent: () => <div className="study-home"><h1>Chapter not found</h1><Link to="/questions">Back to the question bank</Link></div>,
  component: ChapterPage,
});

const sel = "rounded-lg border bg-background px-3 py-2 text-sm";

function ChapterPage() {
  const d = Route.useLoaderData();
  const p = useQuestionProgress();
  const [difficulty, setDifficulty] = useState("all");
  const [type, setType] = useState("all");
  const [status, setStatus] = useState("all");
  const all = questionsFor(d.exam, d.subject, d.chapter);
  const years = [...new Set(all.map((q) => q.year).filter((y): y is number => y !== null))];
  const [year, setYear] = useState("all");
  const list = all.filter((q) => {
    const a = p.state.attempts[q.id];
    return (difficulty === "all" || q.difficulty === difficulty)
      && (type === "all" || q.type === type)
      && (year === "all" || String(q.year) === year)
      && (status === "all"
        || (status === "new" && !a) || (status === "correct" && a?.ok) || (status === "wrong" && a && !a.ok)
        || (status === "bookmarked" && p.state.bookmarks.includes(q.id)));
  });
  return (
    <div className="study-home study-lesson">
      <p className="text-sm">
        <Link to="/questions">Question Bank</Link> / <Link to="/questions/$exam" params={{ exam: d.exam }}>{d.examName}</Link> / {d.subjectName}
      </p>
      <h1>{d.chapterName}</h1>
      <PracticeNotice />
      {all.length === 0 ? (
        <p className="mt-6">No questions have been written for this chapter yet. Try another chapter from <Link to="/questions/$exam" params={{ exam: d.exam }}>{d.examName}</Link>.</p>
      ) : (
        <>
          <div className="my-5 flex flex-wrap gap-3" aria-label="Filters">
            <select aria-label="Year" className={sel} value={year} onChange={(e) => setYear(e.target.value)} disabled={years.length === 0}
              title={years.length === 0 ? "No past-paper questions with a year in this chapter yet" : undefined}>
              <option value="all">{years.length === 0 ? "Year: none yet" : "All years"}</option>
              {years.map((y) => <option key={y} value={y}>{y}</option>)}
            </select>
            <select aria-label="Difficulty" className={sel} value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
              <option value="all">All difficulty</option><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option>
            </select>
            <select aria-label="Question type" className={sel} value={type} onChange={(e) => setType(e.target.value)}>
              <option value="all">All types</option><option value="mcq">Single correct</option><option value="numeric">Numerical</option>
            </select>
            <select aria-label="Status" className={sel} value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="all">All questions</option><option value="new">Not attempted</option><option value="correct">Solved</option><option value="wrong">Got wrong</option><option value="bookmarked">Bookmarked</option>
            </select>
          </div>
          <p className="mb-3 text-sm text-muted-foreground">Showing {list.length} of {all.length}</p>
          <div className="grid gap-4">
            {list.map((q, i) => <QuestionCard key={q.id} q={q} index={i} />)}
            {list.length === 0 && <p>No questions match these filters.</p>}
          </div>
        </>
      )}
    </div>
  );
}

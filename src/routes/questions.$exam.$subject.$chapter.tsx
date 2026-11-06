import { useState } from "react";
import { createFileRoute, Link, notFound, redirect } from "@tanstack/react-router";
import { seoHead } from "@/lib/seo";
import { chapterName, examBySlug, jeeMainPublicChapterSlug, questionsFor, subjectOf } from "@/lib/question-bank";
import { PracticeNotice, QuestionCard } from "@/components/question-bank";
import { useQuestionProgress } from "@/lib/question-progress";
import { Crumbs } from "@/components/exams/exam-ui";

export type ChapterData = { exam: string; examName: string; subject: string; subjectName: string; chapter: string; chapterName: string };

export const Route = createFileRoute("/questions/$exam/$subject/$chapter")({
  loader: ({ params }) => {
    const exam = examBySlug(params.exam);
    const sub = exam && subjectOf(exam, params.subject);
    const chap = sub && chapterName(sub, params.chapter);
    if (!exam || !sub || !chap) throw notFound();
    if (exam.slug === "jee-main") {
      const publicSlug = jeeMainPublicChapterSlug(sub.slug, params.chapter);
      if (publicSlug) throw redirect({ to: "/past-years/jee/jee-main/$subject/$chapter", params: { subject: sub.slug, chapter: publicSlug }, statusCode: 301 });
    }
    return { exam: exam.slug, examName: exam.name, subject: sub.slug, subjectName: sub.name, chapter: params.chapter, chapterName: chap };
  },
  head: ({ loaderData: d }) => seoHead({
    title: d ? `${d.chapterName} — ${d.examName} ${d.subjectName} Questions` : "Chapter not found",
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
  return <ChapterContent d={d} />;
}

export function ChapterContent({ d }: { d: ChapterData }) {
  const p = useQuestionProgress();
  const [difficulty, setDifficulty] = useState("all");
  const [type, setType] = useState("all");
  const [status, setStatus] = useState("all");
  const all = questionsFor(d.exam, d.subject, d.chapter);
  const exam = examBySlug(d.exam)!;
  const subject = subjectOf(exam, d.subject)!;
  const jeeMain = d.exam === "jee-main";
  const mcqCount = all.filter((q) => q.type === "mcq").length;
  const numericCount = all.length - mcqCount;
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
  const chapterLinks = subject.units.map((unit) => <div key={unit.name}>
    <h3 className="mb-1 text-xs font-bold uppercase tracking-wide text-muted-foreground">{unit.name}</h3>
    {unit.chapters.map(([slug, name]) => {
      const publicSlug = jeeMainPublicChapterSlug(d.subject, slug);
      return publicSlug ? <Link key={slug} to="/past-years/jee/jee-main/$subject/$chapter" params={{ subject: d.subject, chapter: publicSlug }} aria-current={slug === d.chapter ? "page" : undefined} className={`block rounded-lg px-2 py-1.5 text-sm hover:bg-accent ${slug === d.chapter ? "bg-primary/10 font-bold text-primary" : ""}`}>{name}</Link>
        : <Link key={slug} to="/questions/$exam/$subject/$chapter" params={{ exam: d.exam, subject: d.subject, chapter: slug }} className="block rounded-lg px-2 py-1.5 text-sm hover:bg-accent">{name}</Link>;
    })}
  </div>);
  return (
    <div className={`exam-wrap${jeeMain ? " exam-jee-page" : ""}`}>
      <div className={`grid gap-7 ${jeeMain ? "lg:grid-cols-[260px_minmax(0,1fr)]" : ""}`}>
      {jeeMain && <aside className="exam-pastel-card self-start rounded-2xl border p-4 lg:sticky lg:top-20" aria-label={`${d.subjectName} chapters`}>
        <p className="text-xs font-bold uppercase tracking-wide text-muted-foreground">{d.examName}</p>
        <h2 className="mt-1 font-bold">{d.subjectName}</h2>
        <details className="mt-3 lg:hidden"><summary className="cursor-pointer text-sm font-semibold">Browse chapters</summary><nav className="mt-3 max-h-72 space-y-4 overflow-y-auto" aria-label="Chapters">{chapterLinks}</nav></details>
        <nav className="mt-4 hidden max-h-[70vh] space-y-4 overflow-y-auto lg:block" aria-label="Chapters">{chapterLinks}</nav>
      </aside>}
      <main className="min-w-0">
      <Crumbs items={[["Home", <Link to="/">Home</Link>], [d.examName, <Link to="/questions/$exam" params={{ exam: d.exam }}>{d.examName}</Link>], [d.subjectName], [d.chapterName]]} />
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">{d.chapterName}</h1>
          <p className="mt-1 text-muted-foreground">Original {d.examName} {d.subjectName} practice questions with solutions.</p>
        </div>
        {all.length > 0 && <a href="#questions" className="rounded-lg border bg-card px-4 py-2 text-sm font-semibold hover:bg-accent">Start practice →</a>}
      </div>
      {jeeMain && <div className="mt-5 grid grid-cols-3 gap-2 sm:gap-3" aria-label="Chapter question summary">
        <div className="exam-pastel-panel rounded-xl border p-3 sm:p-4"><b className="text-xl">{all.length}</b><p className="text-xs text-muted-foreground sm:text-sm">Original questions</p></div>
        <div className="exam-pastel-card rounded-xl border p-3 sm:p-4"><b className="text-xl">{mcqCount}</b><p className="text-xs text-muted-foreground sm:text-sm">Single correct</p></div>
        <div className="exam-pastel-card rounded-xl border p-3 sm:p-4"><b className="text-xl">{numericCount}</b><p className="text-xs text-muted-foreground sm:text-sm">Numerical</p></div>
      </div>}
      <div className="mt-5"><PracticeNotice /></div>
      {all.length === 0 ? (
        <p className="mt-6">No questions have been written for this chapter yet. Try another chapter from <Link to="/questions/$exam" params={{ exam: d.exam }}>{d.examName}</Link>.</p>
      ) : (
        <>
          <h2 id="questions" className="mt-8 scroll-mt-24 text-xl font-bold">Practice questions <span className="text-sm font-normal text-muted-foreground">{all.length}</span></h2>
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
      </main>
      </div>
    </div>
  );
}

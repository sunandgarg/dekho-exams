import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Printer } from "lucide-react";
import { seoHead } from "@/lib/seo";
import { categoryOf, examBySlug, paperById, questionById, type Question } from "@/lib/question-bank";
import { Crumbs } from "@/components/exams/exam-ui";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/questions/$exam/papers/$paper")({
  validateSearch: (s: Record<string, unknown>): { print?: number } => (s.print ? { print: 1 } : {}),
  loader: ({ params }) => {
    const exam = examBySlug(params.exam);
    const paper = exam && paperById(exam.slug, params.paper);
    if (!exam || !paper) throw notFound();
    return { exam: exam.slug, examName: exam.name, paper: paper.id, title: paper.title };
  },
  head: ({ loaderData }) => seoHead({
    title: loaderData ? loaderData.title : "Paper not found",
    description: loaderData ? `${loaderData.title}: every question in order with an answer key at the end. Print or save as PDF.` : "This paper is not available.",
    path: loaderData ? `questions/${loaderData.exam}/papers/${loaderData.paper}` : "questions",
    noindex: true,
  }),
  notFoundComponent: () => <div className="exam-wrap"><h1 className="text-2xl font-bold">Paper not found</h1><Link to="/" className="text-primary">Back to all exams</Link></div>,
  component: PaperPage,
});

const letter = (i: number) => String.fromCharCode(65 + i);
const answerText = (q: Question) => (q.type === "mcq" ? letter(q.answer) : String(q.answer));

function PaperPage() {
  const d = Route.useLoaderData();
  const { print } = Route.useSearch();
  const exam = examBySlug(d.exam)!;
  const cat = categoryOf(exam);
  const paper = paperById(d.exam, d.paper)!;
  const qs = paper.questionIds.map(questionById).filter((q): q is Question => !!q);
  const subjects = exam.subjects.filter((s) => qs.some((q) => q.subject === s.slug));
  const [filter, setFilter] = useState<string>("all");
  const shown = qs.filter((q) => filter === "all" || q.subject === filter);
  useEffect(() => { if (print) window.setTimeout(() => window.print(), 400); }, [print]);
  let n = 0;
  return (
    <div className="exam-wrap max-w-4xl">
      <div className="no-print">
        <Crumbs items={[["Home", <Link to="/">Home</Link>], [cat.short, <a href={`/#${cat.slug}`}>{cat.short}</a>], [exam.name, <Link to="/questions/$exam/papers" params={{ exam: exam.slug }}>{exam.name} papers</Link>], [paper.title]]} />
      </div>
      <article className="paper-sheet rounded-2xl border bg-card p-6 sm:p-10">
        <header className="border-b pb-5">
          <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground">{exam.name} · Original practice set · {qs.length} questions</p>
          <h1 className="mt-2 text-2xl font-extrabold tracking-tight sm:text-3xl">{paper.title}</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Written for Dekhoexams in the {exam.name} style. Not a past paper. Marking: +{exam.marking.correct} correct, {exam.marking.wrong} wrong (MCQ). Answer key at the end.
          </p>
          <div className="no-print mt-4 flex flex-wrap items-center gap-2">
            <Button size="sm" onClick={() => window.print()}><Printer className="size-4" /> Print / Save PDF</Button>
            <Button size="sm" variant="outline" asChild><Link to="/questions/$exam/practice" params={{ exam: exam.slug }}>Attempt as timed practice</Link></Button>
            {subjects.length > 1 && (
              <div className="ml-auto flex flex-wrap gap-1.5" role="group" aria-label="Filter by subject">
                {[["all", "All"], ...subjects.map((s) => [s.slug, s.name])].map(([v, l]) => (
                  <button key={v} type="button" aria-pressed={filter === v} onClick={() => setFilter(v!)}
                    className={`rounded-full border px-3 py-1 text-xs font-semibold ${filter === v ? "border-primary bg-primary text-primary-foreground" : "hover:bg-accent"}`}>{l}</button>
                ))}
              </div>
            )}
          </div>
        </header>
        {subjects.filter((s) => filter === "all" || s.slug === filter).map((s) => (
          <section key={s.slug} className="mt-8">
            <h2 className="mb-4 text-lg font-bold">{s.name}</h2>
            <ol className="grid gap-6">
              {shown.filter((q) => q.subject === s.slug).map((q) => {
                n += 1;
                return (
                  <li key={q.id} className="paper-q">
                    <p className="leading-7"><b className="mr-2">Q{n}.</b>{q.text}</p>
                    {q.type === "mcq" ? (
                      <ol className="mt-2 grid gap-1 pl-7 text-sm sm:grid-cols-2">
                        {q.options!.map((o, i) => <li key={i}><b>({letter(i)})</b> {o}</li>)}
                      </ol>
                    ) : (
                      <p className="mt-2 pl-7 text-sm text-muted-foreground">Numerical answer type</p>
                    )}
                  </li>
                );
              })}
            </ol>
          </section>
        ))}
        <section className="paper-q mt-10 border-t pt-6">
          <h2 className="mb-3 text-lg font-bold">Answer key</h2>
          <ol className="grid grid-cols-3 gap-2 text-sm sm:grid-cols-5">
            {subjects.filter((s) => filter === "all" || s.slug === filter).flatMap((s) => shown.filter((q) => q.subject === s.slug)).map((q, i) => (
              <li key={q.id} className="rounded border px-2 py-1"><b>{i + 1}.</b> {answerText(q)}</li>
            ))}
          </ol>
        </section>
      </article>
    </div>
  );
}

import { createFileRoute, Link, notFound, redirect } from "@tanstack/react-router";
import { ArrowRight, FileText, Printer } from "lucide-react";
import { seoHead } from "@/lib/seo";
import { categoryOf, examBySlug, papersFor } from "@/lib/question-bank";
import { Crumbs, ExamLogo } from "@/components/exams/exam-ui";

export const Route = createFileRoute("/questions/$exam/papers/")({
  loader: ({ params }) => {
    if (params.exam === "jee-main") throw redirect({ to: "/past-years/year-wise/jee/jee-main", statusCode: 301 });
    const exam = examBySlug(params.exam);
    if (!exam) throw notFound();
    return { slug: exam.slug, name: exam.name };
  },
  head: ({ loaderData }) => seoHead({
    title: loaderData ? `${loaderData.name} Question Papers, Paper-wise` : "Exam not found",
    description: loaderData ? `${loaderData.name} original practice sets with answer keys and printable copies. Verified past papers will be listed when available.` : "This exam is not in the question bank.",
    path: loaderData ? `questions/${loaderData.slug}/papers` : "questions",
    noindex: true,
  }),
  notFoundComponent: () => <div className="exam-wrap"><h1 className="text-2xl font-bold">Exam not found</h1><Link to="/" className="text-primary">Back to all exams</Link></div>,
  component: PapersPage,
});

function PapersPage() {
  const exam = examBySlug(Route.useLoaderData().slug)!;
  const cat = categoryOf(exam);
  const papers = papersFor(exam.slug);
  const past = papers.filter((p) => p.kind === "past");
  const practice = papers.filter((p) => p.kind === "practice");
  const firstPractice = practice[0];
  const years = [...new Set(past.map((p) => p.year!))].sort((a, b) => b - a);
  const jeeMain = exam.slug === "jee-main";
  return (
    <div className={`exam-wrap${jeeMain ? " exam-jee-page" : ""}`}>
      <Crumbs items={[["Home", <Link to="/">Home</Link>], [cat.short, <a href={`/#${cat.slug}`}>{cat.short}</a>], [exam.name, <Link to="/questions/$exam" params={{ exam: exam.slug }}>{exam.name}</Link>], ["Paper-wise"]]} />
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex gap-3">
          <ExamLogo exam={exam} />
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight">{exam.name} question papers</h1>
            <p className="mt-1 text-muted-foreground">Browse available practice sets and verified past papers, with answer keys.</p>
          </div>
        </div>
        <Link to="/questions/$exam" params={{ exam: exam.slug }} className="rounded-lg border bg-card px-4 py-2 text-sm font-semibold hover:bg-accent">Chapter-wise</Link>
      </div>

      <section className="exam-pastel-panel mt-7 flex flex-wrap items-center justify-between gap-4 rounded-2xl border p-5 shadow-sm" aria-label="Available papers">
        <div>
          <p className="text-xs font-bold uppercase tracking-wide text-muted-foreground">Paper-wise practice</p>
          <h2 className="mt-1 text-lg font-bold">{practice.length} original {practice.length === 1 ? "set" : "sets"} available</h2>
          <p className="mt-1 text-sm text-muted-foreground">Open a paper to read every question, check the answer key, or print it for offline practice.</p>
        </div>
        {firstPractice && <Link to="/questions/$exam/papers/$paper" params={{ exam: exam.slug, paper: firstPractice.id }} className="inline-flex items-center gap-2 rounded-lg border bg-card px-4 py-2 text-sm font-semibold hover:bg-accent">Open practice set <ArrowRight className="size-4" /></Link>}
      </section>

      {years.map((y) => (
        <section key={y} className="mt-8">
          <h2 className="mb-3 text-xl font-bold">{y} <span className="text-sm font-normal text-muted-foreground">{past.filter((p) => p.year === y).length} papers</span></h2>
        </section>
      ))}
      {past.length === 0 && (
        <p className="mt-8 rounded-xl border border-dashed bg-card p-5 text-sm text-muted-foreground">
          No verified past papers for {exam.name} have been added yet. Year- and shift-wise papers appear here once each one is checked
          and cleared for publishing.
        </p>
      )}

      <section className="mt-10">
        <h2 className="mb-3 flex items-baseline gap-2 text-xl font-bold">Practice sets <span className="text-sm font-normal text-muted-foreground">{practice.length} {practice.length === 1 ? "set" : "sets"}</span></h2>
        {practice.length === 0 ? (
          <p className="text-sm text-muted-foreground">No practice sets for this exam yet.</p>
        ) : (
          <ul className="grid gap-3 md:grid-cols-2">
            {practice.map((p) => (
              <li key={p.id} className="exam-pastel-card rounded-xl border p-5">
                <span className="inline-block rounded-full border bg-card px-2.5 py-1 text-xs font-semibold text-muted-foreground">Original practice</span>
                <h3 className="font-bold">
                  <Link to="/questions/$exam/papers/$paper" params={{ exam: exam.slug, paper: p.id }} className="hover:text-primary">{p.title}</Link>
                </h3>
                <p className="mt-1 text-sm text-muted-foreground">{p.questionIds.length} questions · English · Answer key included</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  <Link to="/questions/$exam/papers/$paper" params={{ exam: exam.slug, paper: p.id }} className="inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm font-semibold hover:bg-accent">
                    <FileText className="size-4" /> View paper
                  </Link>
                  <Link to="/questions/$exam/practice" params={{ exam: exam.slug }} className="inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm font-semibold hover:bg-accent">
                    Practice questions
                  </Link>
                  <Link to="/questions/$exam/papers/$paper" params={{ exam: exam.slug, paper: p.id }} search={{ print: 1 }} className="inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm font-semibold text-primary hover:bg-accent">
                    <Printer className="size-4" /> Print / Save PDF
                  </Link>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

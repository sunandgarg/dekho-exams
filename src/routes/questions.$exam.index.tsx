import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { seoHead } from "@/lib/seo";
import { examBySlug, questionsFor } from "@/lib/question-bank";
import { PracticeNotice } from "@/components/question-bank";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/questions/$exam/")({
  loader: ({ params }) => {
    const exam = examBySlug(params.exam);
    if (!exam) throw notFound();
    return { slug: exam.slug, name: exam.name };
  },
  head: ({ loaderData }) => seoHead({
    title: loaderData ? `${loaderData.name} Chapter-wise Questions | Dekhoexams` : "Exam not found | Dekhoexams",
    description: loaderData ? `Chapter-wise ${loaderData.name} practice questions with solutions and timed practice.` : "This exam is not in the question bank.",
    path: loaderData ? `questions/${loaderData.slug}` : "questions",
    noindex: true,
  }),
  notFoundComponent: () => <div className="study-home"><h1>Exam not found</h1><Link to="/questions">Back to the question bank</Link></div>,
  component: ExamPage,
});

function ExamPage() {
  const exam = examBySlug(Route.useLoaderData().slug)!;
  return (
    <div className="study-home study-lesson">
      <p className="text-sm"><Link to="/questions">Question Bank</Link> / {exam.name}</p>
      <h1>{exam.name} questions</h1>
      <PracticeNotice />
      <div className="my-5">
        <Button asChild><Link to="/questions/$exam/practice" params={{ exam: exam.slug }}>Start timed practice</Link></Button>
      </div>
      {exam.subjects.map((s) => (
        <section key={s.slug} className="mb-8">
          <h2>{s.name}</h2>
          <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {s.chapters.map(([slug, name]) => {
              const n = questionsFor(exam.slug, s.slug, slug).length;
              return (
                <li key={slug}>
                  <Link to="/questions/$exam/$subject/$chapter" params={{ exam: exam.slug, subject: s.slug, chapter: slug }}
                    className="flex justify-between rounded-lg border px-3 py-2 text-sm hover:bg-accent">
                    <span>{name}</span>
                    <span className="text-muted-foreground">{n === 0 ? "Coming soon" : n}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </section>
      ))}
    </div>
  );
}

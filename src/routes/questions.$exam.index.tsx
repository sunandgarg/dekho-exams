import { createFileRoute, Link, notFound, redirect } from "@tanstack/react-router";
import { seoHead } from "@/lib/seo";
import { categoryOf, examBySlug } from "@/lib/question-bank";
import { ArchiveNav } from "@/components/exams/jee-archive";
import {archiveCatalog,archiveUnits,isArchive} from "@/lib/jee-catalog";
import { PracticeNotice } from "@/components/question-bank";
import { ChapterCard, Crumbs, ExamLogo } from "@/components/exams/exam-ui";

export const Route = createFileRoute("/questions/$exam/")({
  loader: ({ params }) => {
    if (isArchive(params.exam)) throw redirect({ to: "/past-years/jee/$archive",params:{archive:params.exam}, statusCode: 301 });
    const exam = examBySlug(params.exam);
    if (!exam) throw notFound();
    return { slug: exam.slug, name: exam.name };
  },
  head: ({ loaderData }) => seoHead({
    title: loaderData ? `${loaderData.name} Chapter-wise Questions with Solutions` : "Exam not found",
    description: loaderData ? `${loaderData.name} chapter-wise questions with solutions, grouped by subject and unit.` : "This exam is not in the question bank.",
    path: loaderData ? `questions/${loaderData.slug}` : "questions",
    noindex: true,
  }),
  notFoundComponent: () => <div className="exam-wrap"><h1 className="text-2xl font-bold">Exam not found</h1><Link to="/" className="text-primary">Back to all exams</Link></div>,
  component: ExamPage,
});

function ExamPage() {
  const exam = examBySlug(Route.useLoaderData().slug)!;
  return <ExamHub exam={exam} />;
}

export function ExamHub({ exam, subject }: { exam: NonNullable<ReturnType<typeof examBySlug>>; subject?: string }) {
  const cat = categoryOf(exam);
  const selected = exam.subjects.find((s) => s.slug === subject);
  const catalog = isArchive(exam.slug) ? archiveCatalog(exam.slug) : null;
  return (
    <div className={`exam-wrap${catalog ? " exam-jee-page" : ""}`}>
      <Crumbs items={[["Home", <Link to="/">Home</Link>], [cat.short, <a href={`/#${cat.slug}`}>{cat.short}</a>], [exam.name]]} />
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex gap-3">
          <ExamLogo exam={exam} />
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight">{exam.name}{selected ? " · " + selected.name : ""}</h1>
            <p className="mt-1 text-muted-foreground">Chapter-wise questions with solutions, by subject.</p>
          </div>
        </div>
        <div className="flex gap-2">
          {!catalog && <Link to="/questions/$exam/papers" params={{ exam: exam.slug }} className="rounded-lg border bg-card px-4 py-2 text-sm font-semibold hover:bg-accent">Paper-wise</Link>}
          {!catalog && <Link to="/questions/$exam/practice" params={{ exam: exam.slug }} className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground">Timed practice</Link>}
        </div>
      </div>
      {catalog && <ArchiveNav/>}
      <div className="mt-4 flex flex-wrap gap-2">
        {exam.subjects.map((s) => (
          <a key={s.slug} href={catalog ? catalog.jeeHub+"/"+s.slug : `#${s.slug}`} className="rounded-full border bg-card px-3 py-1 text-sm font-medium hover:bg-accent">{s.name}</a>
        ))}
      </div>
      {catalog ? (
        <section className="exam-pastel-panel mt-6 flex flex-wrap items-center justify-between gap-4 rounded-2xl border p-5 shadow-sm" aria-label={exam.name+" practice bank"}>
          <div>
            <h2 className="text-base font-bold">Chapter-wise {exam.name} practice</h2>
            <p className="mt-1 text-sm text-muted-foreground">{Object.values(catalog.counts).reduce((a,b)=>a+b,0).toLocaleString("en-IN")} previous-year question listings across Physics, Chemistry and Mathematics.</p>
            <p className="mt-1 text-sm text-muted-foreground">Browse previous papers by year for paper PDFs. Practice solutions have not been academically reviewed.</p>
          </div>
          <Link to="/questions/$exam/practice" params={{ exam: exam.slug }} className="rounded-lg border bg-background px-4 py-2 text-sm font-semibold hover:bg-accent">Practise original set →</Link>
        </section>
      ) : <div className="mt-5"><PracticeNotice /></div>}
      {exam.subjects.filter((s) => !subject || s.slug === subject).map((s) => (
        <section key={s.slug} id={s.slug} className="mt-10 scroll-mt-28">
          <h2 className="mb-2 flex items-center gap-4 text-xl font-bold">{s.name}<span className="h-px flex-1 bg-border" /></h2>
          {(catalog?archiveUnits(catalog.id,s.slug):s.units).map((u) => (
            <div key={u.name} className="mt-5">
              {s.units.length > 1 && <h3 className="mb-3 text-xs font-bold uppercase tracking-wider text-muted-foreground">{u.name}</h3>}
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {u.chapters.map(([slug, name]) => (
                  <ChapterCard key={slug} exam={exam.slug} subject={s.slug} slug={slug} name={name} />
                ))}
              </div>
            </div>
          ))}
        </section>
      ))}
    </div>
  );
}

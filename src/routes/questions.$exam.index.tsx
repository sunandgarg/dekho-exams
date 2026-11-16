import { Atom, BookOpen, ChevronRight, FlaskConical, Radical } from "lucide-react";
import { pdfBrowsePath, pdfExams } from "@/lib/pdf-library";
import { createFileRoute, Link, notFound, redirect } from "@tanstack/react-router";
import { seoHead } from "@/lib/seo";
import { categoryOf, examBySlug, questionsFor } from "@/lib/question-bank";
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
    noindex: !loaderData || !questionsFor(loaderData.slug).length,
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
  const icons = { physics: Atom, chemistry: FlaskConical, mathematics: Radical };
  return (
    <div className={`exam-wrap exam-hub${catalog ? " exam-jee-page" : ""}`}>
      <Crumbs items={[["Home", <Link to="/">Home</Link>], [cat.short, <a href={`/#${cat.slug}`}>{cat.short}</a>], [exam.name]]} />
      <header className="exam-hub-head">
        <div className="exam-hub-intro">
          <ExamLogo exam={exam}/>
          <div>
            <h1>{exam.name}{selected ? " · " + selected.name : ""}</h1>
            <p>Chapter-wise questions with solutions</p>
          </div>
        </div>
        {catalog && <dl className="exam-hub-stats">
          <div><dt>Chapters</dt><dd>{Object.keys(catalog.meta).length}</dd></div>
          <div><dt>Past papers</dt><dd>{catalog.papers.length}</dd></div>
          <div><dt>Question listings</dt><dd>{Object.values(catalog.counts).reduce((a,b)=>a+b,0).toLocaleString("en-IN")}</dd></div>
        </dl>}
      </header>
      {catalog ? <ArchiveNav/> : <nav className="exam-hub-actions" aria-label="Exam resources">
        {Object.hasOwn(pdfExams, exam.slug) && <a className="pdf-download" href={pdfBrowsePath(exam.slug,"chapter")}>Download chapter PDFs</a>}
        <Link to="/questions/$exam/papers" params={{exam: exam.slug}}>Paper-wise</Link>
        <Link to="/questions/$exam/practice" params={{exam: exam.slug}}>Timed practice</Link>
      </nav>}
      <nav className="subject-picker" aria-label="Subjects">
        {exam.subjects.map(s => {
          const Icon = icons[s.slug as keyof typeof icons] ?? BookOpen;
          const total = catalog?.chapters[s.slug]?.length ?? s.chapters.length;
          return <a key={s.slug} data-subject={s.slug} href={catalog ? catalog.jeeHub+"/"+s.slug : "#"+s.slug} aria-current={subject === s.slug ? "page" : undefined}>
            <span className="subject-icon"><Icon size={23} aria-hidden="true"/></span>
            <span><strong>{s.name}</strong><small>{total} {total===1 ? "chapter" : "chapters"}</small></span><ChevronRight size={18} aria-hidden="true"/>
          </a>;
        })}
      </nav>
      {!catalog && <div className="mt-5"><PracticeNotice /></div>}
      {exam.subjects.filter((s) => !subject || s.slug === subject).map((s) => (
        <section key={s.slug} id={s.slug} data-subject={s.slug} className="exam-subject">
          <h2>{s.name}</h2>
          {(catalog?archiveUnits(catalog.id,s.slug):s.units).map((u) => (
            <div key={u.name} className="mt-5">
              {s.units.length > 1 && <h3 className="exam-unit-name">{u.name}</h3>}
              <div className="chapter-grid">
                {u.chapters.map(([slug, name]) => (
                  <ChapterCard key={slug} exam={exam.slug} subject={s.slug} slug={slug} name={name} />
                ))}
              </div>
            </div>
          ))}
        </section>
      ))}
      {catalog && <aside className="exam-hub-practice">
        <Link to="/questions/$exam/practice" params={{ exam: exam.slug }}>Practise an original set →</Link>
        <span>Practice solutions have not been academically reviewed.</span>
      </aside>}
    </div>
  );
}

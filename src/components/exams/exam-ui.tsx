import {archiveCatalog,isArchive} from "@/lib/jee-catalog";
import { Link } from "@tanstack/react-router";
import { ArrowUpRight, ChevronRight, FileText } from "lucide-react";
import type { ReactNode } from "react";
import { CATEGORIES, examsIn, papersFor, questionsFor, type Exam } from "@/lib/question-bank";
import logoSources from "@/data/exam-logo-sources.json";

export function ExamLogo({ exam }: { exam: Exam }) {
  const logo = logoSources[exam.slug as keyof typeof logoSources];
  return (
    <span className="exam-logo" data-cat={exam.category} data-has-logo={!!logo} aria-hidden="true">
      {logo ? <img src={`/exam-logos/${logo.file}`} alt="" width="64" height="52" loading="lazy" decoding="async" /> : exam.short}
    </span>
  );
}

export function Crumbs({ items }: { items: [label: string, to?: ReactNode][] }) {
  return (
    <nav aria-label="Breadcrumb" className="mb-3 flex flex-wrap items-center gap-1.5 text-sm text-muted-foreground">
      {items.map(([label, link], i) => (
        <span key={label} className="flex items-center gap-1.5">
          {i > 0 && <span aria-hidden="true">/</span>}
          {link ?? <span className="font-medium text-foreground">{label}</span>}
        </span>
      ))}
    </nav>
  );
}


function ExamCard({ exam }: { exam: Exam }) {
  const catalog=isArchive(exam.slug)?archiveCatalog(exam.slug):null;
  const n = questionsFor(exam.slug).length;
  const papers = papersFor(exam.slug).length;
  return (
    <article className="exam-card text-card-foreground" data-cat={exam.category}>
      <div className="flex gap-3">
        <ExamLogo exam={exam} />
        <div>
          <h3 className="text-base font-bold leading-6">{exam.name}</h3>
          <p className="text-sm text-muted-foreground">
            {catalog ? Object.keys(catalog.meta).length+" chapters · "+catalog.papers.length+" previous-year papers" : n > 0 ? `${n} practice ${n === 1 ? "question" : "questions"} with solutions` : "Chapters listed · questions coming soon"}
          </p>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-2">
        {catalog ? <a href={catalog.jeeHub} className="exam-btn exam-btn-solid">Chapter-wise</a> : <Link to="/questions/$exam" params={{ exam: exam.slug }} className="exam-btn exam-btn-solid">Chapter-wise</Link>}
        {catalog ? <a href={catalog.paperHub} className="exam-btn">Paper-wise</a> : <Link to="/questions/$exam/papers" params={{ exam: exam.slug }} className="exam-btn">Paper-wise</Link>}
      </div>
      <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 border-t pt-3 text-sm">
        <Link to="/questions/$exam/practice" params={{ exam: exam.slug }} className="inline-flex items-center gap-1 text-muted-foreground hover:text-foreground">
          Timed practice <ArrowUpRight className="size-3.5" />
        </Link>
        {catalog ? <a href={catalog.pdfHub} className="inline-flex items-center gap-1 font-semibold text-primary"><FileText className="size-3.5"/> PYQ PDFs</a> : papers > 0 && (
          <Link to="/questions/$exam/papers" params={{ exam: exam.slug }} className="inline-flex items-center gap-1 font-semibold text-primary">
            <FileText className="size-3.5" /> Printable sets
          </Link>
        )}
      </div>
    </article>
  );
}

export function ExamDirectory() {
  return (
    <div className="exam-wrap">
      <header className="exam-hero">
      <span className="exam-sticker">✦ Dekhoexams Questions</span>
      <h1 className="mt-4 max-w-3xl text-4xl font-black tracking-tight sm:text-6xl">Crack your exam, one chapter at a time.</h1>
      <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground">
        JEE, NEET, GATE, UPSC, NDA, SSC and CBSE, organised chapter-wise and paper-wise. Browse JEE Main and JEE Advanced past papers by year and shift, or choose an original Dekhoexams practice set.
      </p>
      </header>
      <div className="exam-chipbar">
        {CATEGORIES.map((c) => (
          <a key={c.slug} href={`#${c.slug}`} className="exam-chip">
            {c.short} <b>{examsIn(c.slug).length}</b>
          </a>
        ))}
        <Link to="/questions/bookmarks" className="exam-chip">🔖 Bookmarks</Link>
      </div>
      {CATEGORIES.map((c) => (
        <section key={c.slug} id={c.slug} className="mt-10 scroll-mt-28" aria-labelledby={`${c.slug}-h`}>
          <h2 id={`${c.slug}-h`} className="mb-4 flex items-baseline gap-2 text-xl font-bold">
            {c.name} <span className="text-sm font-normal text-muted-foreground">{examsIn(c.slug).length} exams</span>
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {examsIn(c.slug).map((e) => <ExamCard key={e.slug} exam={e} />)}
          </div>
        </section>
      ))}
    </div>
  );
}

export function ChapterCard({ exam, subject, slug, name }: { exam: string; subject: string; slug: string; name: string }) {
  const qs = questionsFor(exam, subject, slug);
  const catalog=isArchive(exam)?archiveCatalog(exam):null;
  const entry=catalog?.meta[subject+"/"+slug];
  const content = <>
    <span className="flex items-start justify-between gap-2 font-semibold leading-6">
      {entry?.name ?? name}
      <ChevronRight className="mt-0.5 size-4 shrink-0 text-muted-foreground group-hover:text-primary" />
    </span>
    <span className="mt-2 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
      {catalog && entry ? <span><b>{catalog.counts["chapter/"+subject+"/"+slug] ?? 0}</b> previous-year questions</span> : qs.length > 0 ? <><span className="rounded bg-muted px-2 py-0.5 text-xs font-semibold">Practice</span><span><b className="text-foreground">{qs.length}</b> {qs.length === 1 ? "question" : "questions"}</span></> : <span className="text-xs">Coming soon</span>}
    </span>
    {entry?.latest && <small className="block text-muted-foreground">{entry.latest}</small>}
  </>;
  const className = "chapter-card group flex min-h-[84px] flex-col justify-between rounded-xl border bg-card p-4 hover:border-primary";
  if (catalog && entry) return <Link to="/past-years/jee/$archive/$subject/$chapter" params={{ archive:catalog.id,subject, chapter:slug }} className={className}>{content}</Link>;
  return (
    <Link
      to="/questions/$exam/$subject/$chapter"
      params={{ exam, subject, chapter: slug }}
      className={className}
    >
      {content}
    </Link>
  );
}

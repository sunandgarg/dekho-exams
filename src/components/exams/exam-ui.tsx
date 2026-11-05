import { Link } from "@tanstack/react-router";
import { ArrowUpRight, ChevronRight, FileText } from "lucide-react";
import type { ReactNode } from "react";
import { CATEGORIES, examsIn, papersFor, questionsFor, type Exam } from "@/lib/question-bank";

export function ExamLogo({ exam }: { exam: Exam }) {
  return (
    <span className="exam-logo" data-cat={exam.category} aria-hidden="true">
      {exam.short}
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

const pill = "inline-flex items-center gap-1.5 rounded-full border bg-card px-3 py-1 text-sm font-medium hover:bg-accent";
const btn = "flex h-10 items-center justify-center rounded-lg border bg-card text-sm font-semibold hover:bg-accent";

function ExamCard({ exam }: { exam: Exam }) {
  const n = questionsFor(exam.slug).length;
  const papers = papersFor(exam.slug).length;
  return (
    <article className="flex flex-col rounded-xl border bg-card p-5 text-card-foreground">
      <div className="flex gap-3">
        <ExamLogo exam={exam} />
        <div>
          <h3 className="text-base font-bold leading-6">{exam.name}</h3>
          <p className="text-sm text-muted-foreground">
            {n > 0 ? `${n} practice ${n === 1 ? "question" : "questions"} with solutions` : "Chapters listed · questions coming soon"}
          </p>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-2">
        <Link to="/questions/$exam" params={{ exam: exam.slug }} className={btn}>Chapter-wise</Link>
        <Link to="/questions/$exam/papers" params={{ exam: exam.slug }} className={btn}>Paper-wise</Link>
      </div>
      <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 border-t pt-3 text-sm">
        <Link to="/questions/$exam/practice" params={{ exam: exam.slug }} className="inline-flex items-center gap-1 text-muted-foreground hover:text-foreground">
          Timed practice <ArrowUpRight className="size-3.5" />
        </Link>
        {papers > 0 && (
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
      <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Dekhoexams Questions</p>
      <h1 className="mt-2 text-3xl font-extrabold tracking-tight sm:text-4xl">Exam questions with solutions</h1>
      <p className="mt-3 max-w-2xl text-base leading-7 text-muted-foreground">
        JEE, NEET, GATE, UPSC, NDA, SSC and CBSE, organised chapter-wise and paper-wise. Questions here are
        original Dekhoexams practice questions; verified past papers will be marked with their year and shift.
      </p>
      <div className="mt-5 flex flex-wrap gap-2">
        {CATEGORIES.map((c) => (
          <a key={c.slug} href={`#${c.slug}`} className={pill}>
            {c.short} <span className="text-muted-foreground">{examsIn(c.slug).length}</span>
          </a>
        ))}
        <Link to="/questions/bookmarks" className={pill}>Bookmarks</Link>
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
  return (
    <Link
      to="/questions/$exam/$subject/$chapter"
      params={{ exam, subject, chapter: slug }}
      className="group flex min-h-[84px] flex-col justify-between rounded-xl border bg-card p-4 hover:border-primary"
    >
      <span className="flex items-start justify-between gap-2 font-semibold leading-6">
        {name}
        <ChevronRight className="mt-0.5 size-4 shrink-0 text-muted-foreground group-hover:text-primary" />
      </span>
      <span className="mt-2 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
        {qs.length > 0 ? (
          <>
            <span className="rounded bg-muted px-2 py-0.5 text-xs font-semibold">Practice</span>
            <span><b className="text-foreground">{qs.length}</b> {qs.length === 1 ? "question" : "questions"}</span>
          </>
        ) : (
          <span className="text-xs">Coming soon</span>
        )}
      </span>
    </Link>
  );
}

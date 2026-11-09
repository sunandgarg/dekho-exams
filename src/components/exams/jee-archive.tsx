import { useState } from "react";
import downloadPapers from "@/data/jee-main-pdf-papers.json";
import { useParams } from "@tanstack/react-router";
import { archiveCatalog, questionKind, type ArchiveId, type ArchivePaper } from "@/lib/jee-catalog";
import { useQuestionProgress } from "@/lib/question-progress";
import type { ArchiveQuestion, ArchiveRow } from "@/lib/jee-archive.functions";
function useCatalog(owner?: ArchiveId) {
  const params = useParams({ strict: false });
  return archiveCatalog(owner ?? params.archive ?? "jee-main");
}
const btn =
  "inline-flex items-center rounded-lg border bg-card px-3 py-2 text-sm font-semibold hover:bg-accent";
const label = questionKind;
const title = (s: string) => s.replaceAll("-", " ").replace(/(^|\s)\w/g, (c) => c.toUpperCase());
export function ArchiveNav({ owner }: { owner?: ArchiveId } = {}) {
  const { jeeHub, paperHub, pdfHub, name } = useCatalog(owner);
  return (
    <nav className="my-4 flex flex-wrap gap-2" aria-label={name + " library"}>
      <a className={btn} href={jeeHub}>
        Chapter-wise
      </a>
      <a className={btn} href={paperHub}>
        Paper-wise
      </a>
      <a className={btn} href={pdfHub}>
        PYQ PDFs
      </a>
    </nav>
  );
}
export function ArchiveRows({
  rows,
  paper,
  filter,
}: {
  rows: ArchiveRow[];
  paper?: string;
  filter?: string;
}) {
  const { paperHub } = useCatalog();
  const [group, setGroup] = useState(filter ?? ""),
    [year, setYear] = useState("");
  const selected = rows.filter(
    (x) => (!group || x.group === group) && (!year || x.paper.includes(year)),
  );
  const years = [
    ...new Set(rows.map((x) => x.paper.match(/\b(?:19|20)\d{2}\b/)?.[0]).filter(Boolean)),
  ];
  return (
    <section className="my-6">
      <h2 className="text-xl font-bold">
        Previous-year questions{" "}
        <small className="text-sm text-muted-foreground">{rows.length}</small>
      </h2>
      <div className="my-3 flex flex-wrap items-center gap-3">
        {!filter && (
          <select
            className={btn}
            value={group}
            aria-label={paper ? "Subject" : "Question type"}
            onChange={(e) => setGroup(e.target.value)}
          >
            <option value="">{paper ? "All subjects" : "All types"}</option>
            {[...new Set(rows.map((x) => x.group))].map((g) => (
              <option key={g} value={g}>
                {title(label(g))}
              </option>
            ))}
          </select>
        )}
        {!paper && (
          <select
            className={btn}
            value={year}
            aria-label="Exam year"
            onChange={(e) => setYear(e.target.value)}
          >
            <option value="">All years</option>
            {years.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
        )}
        <small>{selected.length} shown</small>
      </div>
      <ol className="grid gap-2">
        {selected.map((r, i) => (
          <li key={r.id}>
            <a
              className="exam-pastel-card flex items-start gap-3 rounded-xl border px-4 py-3 hover:border-primary"
              href={
                paper ? paperHub + "/" + paper + "/" + r.id : "/past-years/jee/question/" + r.id
              }
            >
              <span aria-hidden="true" className="mt-0.5 text-xs text-muted-foreground">
                {i + 1}.
              </span>
              <span className="min-w-0">
                <small className="block font-semibold text-primary">
                  {paper ? title(r.group) : r.paper}
                </small>
                <span className="line-clamp-2 break-words">{r.teaser}</span>
              </span>
            </a>
          </li>
        ))}
      </ol>
      {!selected.length && <p>No questions match these filters.</p>}
    </section>
  );
}
export function EditionLinks({ edition }: { edition: string }) {
  const { id, printPrefix, hindiPrint } = useCatalog();
  const paper =
    id === "jee-main"
      ? (downloadPapers as Record<string, { languages: string[]; unlisted: number[] }>)[edition]
      : undefined;
  return (
    <>
      {paper !== undefined && (
        <div className="mt-3">
          <p className="mb-1 text-sm font-semibold">Download paper with answer key</p>
          <div className="flex flex-wrap gap-2">
            {paper.languages.flatMap((lang) =>
              ["", "-dark"].map((theme) => {
                const file = lang + theme + ".pdf";
                return (
                  <a
                    key={file}
                    className={btn}
                    href={"/jee-papers/jee-main/" + edition + "/" + file}
                    download={"DekhoExams-" + edition + "-" + file}
                  >
                    {lang === "en" ? "English" : lang === "hi" ? "Hindi" : "Bengali"} ·{" "}
                    {theme ? "Dark" : "Light"}
                  </a>
                );
              }),
            )}
          </div>
          {paper.unlisted.length > 0 && (
            <p className="mt-1 text-sm text-muted-foreground">
              The PDF answer key does not list a definitive answer for{" "}
              {paper.unlisted.map((n) => "Q" + n).join(", ")}.
            </p>
          )}
        </div>
      )}
      <div className="mt-2 flex flex-wrap gap-2">
        <a className={btn} href={printPrefix + edition + "/en"}>
          English print edition
        </a>
        {hindiPrint.includes(edition) && (
          <a className={btn} href={printPrefix + edition + "/hi"}>
            Hindi print edition
          </a>
        )}
      </div>
    </>
  );
}
export function PaperCatalog({ pdf = false }: { pdf?: boolean }) {
  const { papers, name, jeeHub, paperHub, id } = useCatalog();
  const years = [
    ...new Set(papers.map((p) => p.date.match(/\d{4}/)?.[0] ?? p.title.match(/\d{4}/)![0])),
  ];
  const [year, setYear] = useState(""),
    [query, setQuery] = useState("");
  return (
    <main className="exam-wrap exam-jee-page">
      <ArchiveNav />
      <header className="exam-pastel-panel rounded-2xl border p-5">
        <h1 className="text-3xl font-extrabold">
          {name} {pdf ? "PYQ PDFs" : "previous-year papers"}
        </h1>
        <p className="mt-2 text-muted-foreground">
          {papers.length} papers by year.{" "}
          {pdf
            ? id === "jee-main"
              ? "Download available papers with answer keys in English or Hindi, and Bengali where listed. Choose a light or dark edition. Use the print edition for worked solutions."
              : "Open a Dekhoexams edition, choose whether to include solutions, then print or save as PDF."
            : "Choose a paper to practise its questions in order."}
        </p>
      </header>
      {pdf && (
        <a className={btn + " mt-4"} href={"/pyq-pdfs" + jeeHub}>
          Browse chapter PDFs →
        </a>
      )}
      <div className="my-5 flex flex-wrap gap-3">
        <select
          className={btn}
          aria-label="Exam year"
          value={year}
          onChange={(e) => setYear(e.target.value)}
        >
          <option value="">All years</option>
          {years.map((y) => (
            <option key={y}>{y}</option>
          ))}
        </select>
        <input
          className={btn}
          aria-label="Search papers"
          placeholder={id === "jee-main" ? "Find a date or shift" : "Find a year or paper"}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>
      {(year ? [year] : years).map((y) => {
        const items = papers.filter(
          (p) =>
            (p.date.includes(y) || p.title.includes(y)) &&
            p.title.toLowerCase().includes(query.toLowerCase()),
        );
        return (
          items.length > 0 && (
            <section key={y} className="mb-6">
              <h2 className="mb-3 text-xl font-bold">
                {y} <small className="text-sm text-muted-foreground">{items.length} papers</small>
              </h2>
              <div className="grid gap-3 sm:grid-cols-2">
                {items.map((p) => (
                  <article key={p.slug} className="exam-pastel-card rounded-xl border p-4">
                    <small>{p.date}</small>
                    <h3 className="font-semibold">
                      <a href={paperHub + "/" + p.slug}>{p.title}</a>
                    </h3>
                    {pdf && <EditionLinks edition={p.slug} />}
                  </article>
                ))}
              </div>
            </section>
          )
        );
      })}
      {!papers.some(
        (p) =>
          (!year || p.date.includes(year) || p.title.includes(year)) &&
          p.title.toLowerCase().includes(query.toLowerCase()),
      ) && <p>No papers match this search.</p>}
      {!pdf && (
        <a className={btn} href={"/questions/" + id + "/papers/practice-set-1"}>
          Original printable practice set
        </a>
      )}
    </main>
  );
}
export function PaperPage({ paper, rows }: { paper: ArchivePaper; rows: ArchiveRow[] }) {
  const { paperHub } = useCatalog();
  return (
    <main className="exam-wrap exam-jee-page">
      <ArchiveNav />
      <header className="exam-pastel-panel rounded-2xl border p-5">
        <p className="text-sm text-muted-foreground">
          {paper.date} · {rows.length} questions
        </p>
        <h1 className="my-2 text-3xl font-bold">{paper.title}</h1>
        {rows[0] && (
          <a className={btn} href={paperHub + "/" + paper.slug + "/" + rows[0].id}>
            Start paper practice →
          </a>
        )}
        <EditionLinks edition={paper.slug} />
      </header>
      <ArchiveRows rows={rows} paper={paper.slug} />
    </main>
  );
}
export function QuestionView({
  q,
  owner,
  inPaper = false,
  language = "en",
}: {
  q: ArchiveQuestion;
  owner?: ArchiveId;
  inPaper?: boolean;
  language?: "en" | "hi";
}) {
  const [choices, setChoices] = useState<number[]>([]),
    [revealed, setRevealed] = useState(false),
    [numeric, setNumeric] = useState(""),
    [checked, setChecked] = useState(false);
  const { id, name, jeeHub, paperHub, papers } = useCatalog(owner);
  const paper = papers.find((p) => p.slug === q.paper);
  const keys = q.choiceKeys ?? (q.choiceKey === undefined ? undefined : [q.choiceKey]);
  const bounds =
    q.numericRange ?? (q.numericKey === undefined ? undefined : [q.numericKey, q.numericKey]);
  const content = language === "hi" && q.hi ? q.hi : q;
  const promptFigurePending = [content.body, ...content.options].some((part) =>
    part.includes('class="jee-figure-pending"'),
  );
  const progress = useQuestionProgress();
  const bookmarkHref = q.canonical
    ? "/past-years/jee/question/" + q.canonical
    : q.chapter
      ? "/past-years/jee/question/" + q.slug
      : paperHub + "/" + q.paper + "/" + q.slug;
  const saved = progress.state.pyqs.some((x) => x.href === bookmarkHref);
  const [saveError, setSaveError] = useState(false);
  const suffix = language === "hi" ? "?lang=hi" : "";
  const prefix = inPaper ? paperHub + "/" + q.paper + "/" : "/past-years/jee/question/";
  return (
    <main className="exam-wrap exam-jee-page">
      <ArchiveNav owner={id} />
      <article className="exam-pastel-card mx-auto max-w-4xl rounded-2xl border p-5 sm:p-8">
        <p className="text-sm font-semibold text-primary">
          {paper ? <a href={paperHub + "/" + q.paper}>{paper.title}</a> : q.paperTitle}
        </p>
        <h1 className="mt-2 text-2xl font-extrabold">{title(q.chapter || q.subject)} question</h1>
        <p className="mb-5 text-sm text-muted-foreground">{title(label(q.kind))}</p>
        <div className="mb-4 flex items-center gap-3">
          <button
            className={btn}
            aria-pressed={saved}
            onClick={() =>
              setSaveError(
                !progress.togglePyq({
                  href: bookmarkHref,
                  title:
                    (paper?.title || q.paperTitle || name) + " · " + title(q.chapter || q.subject),
                }),
              )
            }
          >
            {saved ? "Bookmarked" : "Bookmark"}
          </button>
          <a className="text-sm text-primary" href="/questions/bookmarks">
            My bookmarks
          </a>
          {saveError && <small role="status">Your browser could not save this bookmark.</small>}
        </div>
        {q.hi && (
          <nav aria-label="Question language" className="mb-4 flex gap-2">
            <a
              className={btn}
              aria-current={language === "en" ? "page" : undefined}
              href="?lang=en"
            >
              English
            </a>
            <a
              className={btn}
              aria-current={language === "hi" ? "page" : undefined}
              href="?lang=hi"
              lang="hi"
            >
              हिन्दी
            </a>
          </nav>
        )}
        {promptFigurePending && (
          <p className="mb-3 text-sm text-muted-foreground">
            {language === "hi"
              ? "इस प्रश्न में चित्र अभी उपलब्ध नहीं है। आप हल पढ़ सकते हैं।"
              : "A diagram in this question is pending. You can still read the explanation."}
          </p>
        )}
        <div
          className="jee-prose"
          lang={content === q ? "en" : "hi"}
          dangerouslySetInnerHTML={{ __html: content.body }}
        />
        {content.options.length > 0 && (
          <fieldset className="mt-5 grid gap-2">
            <legend className="mb-2 font-semibold">Your answer</legend>
            {content.options.map((opt, i) => (
              <label
                key={i}
                className="flex cursor-pointer items-start gap-3 rounded-lg border px-3 py-2 has-checked:border-primary"
              >
                <input
                  className="mt-2"
                  type={q.kind === "mcqm" ? "checkbox" : "radio"}
                  name="choice"
                  checked={choices.includes(i)}
                  onChange={() => {
                    setChecked(false);
                    setChoices(
                      q.kind === "mcqm"
                        ? choices.includes(i)
                          ? choices.filter((x) => x !== i)
                          : [...choices, i]
                        : [i],
                    );
                  }}
                />
                <b>{String.fromCharCode(65 + i)}</b>
                <span
                  className="jee-prose min-w-0"
                  lang={content === q ? "en" : "hi"}
                  dangerouslySetInnerHTML={{ __html: opt }}
                />
              </label>
            ))}
          </fieldset>
        )}
        {q.complete && ["subjective", "fill-blanks"].includes(q.kind) && (
          <label className="mt-5 block font-semibold">
            Your response
            <textarea
              className="mt-2 block w-full rounded-lg border bg-background p-3 font-normal"
              rows={q.kind === "subjective" ? 4 : 2}
            />
          </label>
        )}
        {q.complete && q.kind === "integer" && (
          <label className="mt-5 block font-semibold">
            Your numerical answer{" "}
            <input
              aria-label="Your numerical answer"
              type="text"
              inputMode="decimal"
              className={btn}
              value={numeric}
              onChange={(e) => {
                setNumeric(e.target.value);
                setChecked(false);
              }}
            />
          </label>
        )}
        {keys && !promptFigurePending && (
          <div className="mt-3 flex items-center gap-3">
            <button className={btn} disabled={!choices.length} onClick={() => setChecked(true)}>
              Check selected answer
            </button>
            {checked && (
              <span role="status">
                {choices.length === keys.length && keys.every((k) => choices.includes(k))
                  ? "Correct."
                  : "Published answer: " + keys.map((k) => String.fromCharCode(65 + k)).join(", ")}
              </span>
            )}
          </div>
        )}
        {bounds && !promptFigurePending && (
          <div className="mt-3 flex items-center gap-3">
            <button
              className={btn}
              disabled={!/^[+-]?(?:\d+\.?\d*|\.\d+)$/.test(numeric.trim())}
              onClick={() => setChecked(true)}
            >
              Check numerical answer
            </button>
            {checked && (
              <span role="status">
                {Number(numeric) >= bounds[0]! && Number(numeric) <= bounds[1]!
                  ? "Correct."
                  : "Published answer: " +
                    (bounds[0] === bounds[1] ? bounds[0] : bounds.join(" to "))}
              </span>
            )}
          </div>
        )}
        {content.solution ? (
          <>
            <button
              className={btn + " mt-5"}
              aria-expanded={revealed}
              onClick={() => setRevealed(!revealed)}
            >
              {revealed ? "Hide explanation" : "Show explanation"}
            </button>
            {revealed && (
              <section className="mt-4 rounded-lg border p-4">
                <h2 className="mb-2 font-bold">Explanation</h2>
                <div className="jee-prose" dangerouslySetInnerHTML={{ __html: content.solution }} />
              </section>
            )}
          </>
        ) : (
          <p className="mt-5 text-sm text-muted-foreground">
            {q.complete
              ? "No published explanation is available for this question."
              : "Question preview. Answer choices and explanation are not yet available here."}
          </p>
        )}
        <nav
          className="mt-6 flex flex-wrap justify-between gap-2 border-t pt-4"
          aria-label="Question navigation"
        >
          {q.prev && (
            <a className={btn} href={prefix + q.prev + suffix}>
              ← Previous
            </a>
          )}
          {q.canonical && (
            <a className={btn} href={"/past-years/jee/question/" + q.canonical + suffix}>
              View in chapter
            </a>
          )}
          {q.chapter && (
            <a className={btn} href={jeeHub + "/" + q.subject + "/" + q.chapter}>
              Chapter
            </a>
          )}
          {q.next && (
            <a className={btn} href={prefix + q.next + suffix}>
              Next →
            </a>
          )}
        </nav>
      </article>
    </main>
  );
}

export function ChapterPdfCatalog({ subject }: { subject?: string }) {
  const { name, jeeHub, chapters: chapterOrder, meta: chapterMeta } = useCatalog();
  return (
    <main className="exam-wrap exam-jee-page">
      <ArchiveNav />
      <header className="exam-pastel-panel rounded-2xl border p-5">
        <h1 className="text-3xl font-extrabold">
          {name} chapter PDFs{subject ? " · " + title(subject) : ""}
        </h1>
        <p className="mt-2 text-muted-foreground">
          Choose a chapter to print or save a Dekhoexams edition with optional solutions.
        </p>
      </header>
      {Object.entries(chapterOrder)
        .filter(([s]) => !subject || s === subject)
        .map(([s, chapters]) => (
          <section key={s} className="my-6">
            <h2 className="mb-3 text-xl font-bold">
              <a href={"/pyq-pdfs" + jeeHub + "/" + s}>{title(s)}</a>
            </h2>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {chapters.map((c) => (
                <a
                  className="exam-pastel-card rounded-xl border p-3"
                  key={c}
                  href={"/pyq-pdfs" + jeeHub + "/" + s + "/" + c}
                >
                  {(chapterMeta as Record<string, { name: string }>)[s + "/" + c]?.name ?? title(c)}
                </a>
              ))}
            </div>
          </section>
        ))}
    </main>
  );
}

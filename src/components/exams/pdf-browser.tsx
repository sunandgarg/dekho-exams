import { ArrowDownToLine, BookOpen, ChevronDown, ChevronRight, Files, Search } from "lucide-react";
import { useState } from "react";
import type { PdfBrowse } from "@/lib/pdf-browse.server";
import { pdfBrowsePath, pdfLanguages, type PdfKind } from "@/lib/pdf-library";

export function PdfTabs({ exam, active }: { exam: string; active?: PdfKind | undefined }) {
  return (
    <nav className="pdf-tabs" aria-label="Browse PDFs">
      <a href={pdfBrowsePath(exam, "paper")} aria-current={active === "paper" ? "page" : undefined}>
        <Files size={16} />
        Question papers
      </a>
      <a
        href={pdfBrowsePath(exam, "chapter")}
        aria-current={active === "chapter" ? "page" : undefined}
      >
        <BookOpen size={16} />
        Chapter wise
      </a>
    </nav>
  );
}
export function DownloadPdf({
  file,
  title,
  compact = false,
}: {
  file: string;
  title: string;
  compact?: boolean;
}) {
  return (
    <a href={file} download className="pdf-download" aria-label={"Download " + title + " PDF"}>
      <ArrowDownToLine size={16} />
      {compact ? "PDF" : "Download PDF"}
    </a>
  );
}
function PaperEditions({ row }: { row: PdfBrowse["entries"][number] }) {
  return (
    <details className="pdf-more">
      <summary>
        Editions <ChevronDown size={14} />
      </summary>
      <div>
        {row.languages.flatMap((lang) =>
          ["", "-dark"].map((theme) => {
            const text = (pdfLanguages[lang] || lang) + (theme ? " · Dark" : " · Light");
            return (
              <a
                key={lang + theme}
                download
                href={"/jee-papers/jee-main/" + row.archiveSlug + "/" + lang + theme + ".pdf"}
                aria-label={"Download " + row.title + " · " + text}
              >
                <ArrowDownToLine size={14} />
                {text}
              </a>
            );
          }),
        )}
      </div>
    </details>
  );
}
const anchor = (group: string) => "group-" + group.toLowerCase().replace(/[^a-z0-9]+/g, "-");
const subjects = ["Physics", "Chemistry", "Mathematics"];
export function PdfBrowser({ data }: { data: PdfBrowse }) {
  const { exam, name, kind, entries, subject } = data;
  const papers = kind === "paper";
  const [search, setSearch] = useState("");
  const groupOf = (e: PdfBrowse["entries"][number]) =>
    papers ? String(e.year || "Other papers") : e.subject;
  const groups = [...new Set(entries.map(groupOf))];
  if (!papers)
    groups.sort(
      (a, b) =>
        (subjects.includes(a) ? subjects.indexOf(a) : 10) -
        (subjects.includes(b) ? subjects.indexOf(b) : 10),
    );
  const term = search.trim().toLowerCase();
  const matching = entries.filter((e) =>
    [e.title, e.subject, e.year || "", e.date, e.unit].join(" ").toLowerCase().includes(term),
  );
  const label = papers ? "papers" : "chapters";
  return (
    <div className="pdf-view">
      <header className="pdf-rule">
        <div className="pdf-container">
          <nav className="pdf-crumb" aria-label="Breadcrumb">
            <a href="/pdf-library#exams">Exams</a>
            <ChevronRight size={13} />
            <a href={"/pdf-library/" + exam}>{name}</a>
            {subject && <> / {entries[0]?.subject}</>}
          </nav>
          <p className="pdf-kicker">
            {name} · {entries.length} {label}
            {papers && groups.length > 1 && " · " + groups.at(-1) + "–" + groups[0]}
          </p>
          <h1>
            {papers
              ? "Previous year question papers"
              : subject
                ? entries[0]?.subject + " chapter-wise questions"
                : "Chapter-wise previous year questions"}
          </h1>
          <p className="pdf-sub">
            {papers
              ? "Choose a year and shift to download the full paper."
              : "Pick a subject and download the questions for one chapter at a time."}
          </p>
          <PdfTabs active={kind} exam={exam} />
        </div>
      </header>
      <div className="pdf-container pdf-content">
        <div className="pdf-tools">
          <nav aria-label={papers ? "Jump to year" : "Jump to subject"} className="pdf-jumps">
            {groups.map((g) => (
              <a key={g} href={"#" + anchor(g)} onClick={() => setSearch("")}>
                {g}
              </a>
            ))}
          </nav>
          <label className="pdf-search">
            <Search size={16} />
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              aria-label={papers ? "Search papers" : "Search chapters"}
              placeholder={papers ? "Find a year or shift" : "Find a chapter"}
            />
          </label>
        </div>
        {!matching.length && (
          <p role="status">
            No {label} match “{search}”.{" "}
            <button type="button" className="underline" onClick={() => setSearch("")}>
              Clear search
            </button>
          </p>
        )}
        {groups.map((g) => {
          const rows = matching.filter((e) => groupOf(e) === g);
          if (!rows.length) return null;
          return (
            <section
              key={g}
              id={anchor(g)}
              className={papers ? "pdf-section pdf-year" : "pdf-section"}
            >
              <header className="pdf-group">
                <h2>{g}</h2>
                <span>
                  {rows.length} {rows.length === 1 ? (papers ? "paper" : "chapter") : label}
                </span>
              </header>
              <div className="pdf-units">
                {[...new Set(rows.map((e) => e.unit))].map((unit) => (
                  <div key={unit}>
                    {unit && <h3 className="pdf-unit">{unit}</h3>}
                    <ul className={"pdf-list" + (papers ? "" : " pdf-chapters")}>
                      {rows
                        .filter((e) => e.unit === unit)
                        .map((e) => (
                          <li key={e.path}>
                            <div className="pdf-row-info">
                              <a href={"/pdf-library/" + exam + "/" + e.path}>{e.title}</a>
                              <small>
                                {[
                                  papers && e.date,
                                  e.questions > 0 && e.questions + " questions",
                                  e.pages > 0 && e.pages + " pages",
                                ]
                                  .filter(Boolean)
                                  .join(" · ")}
                              </small>
                            </div>
                            <div className="pdf-actions">
                              <DownloadPdf file={e.file} title={e.title} compact={!papers} />
                              {e.languages.length > 0 && <PaperEditions row={e} />}
                            </div>
                          </li>
                        ))}
                    </ul>
                  </div>
                ))}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}

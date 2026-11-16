import { PdfTabs, DownloadPdf } from "@/components/exams/pdf-browser";
import { pdfBrowsePath } from "@/lib/pdf-library";
import { createFileRoute, notFound } from "@tanstack/react-router";
import { getPdfPage } from "@/lib/pdf-library.functions";
import { seoHead } from "@/lib/seo";
export const Route = createFileRoute("/pdf-library/$")({
  loader: async ({ params }) => {
    const page = await getPdfPage({ data: params._splat ?? "" });
    if (!page) throw notFound();
    return page;
  },
  head: ({ loaderData: d }) => {
    if (!d) return seoHead({ title: "PDF unavailable", description: "", noindex: true });
    const e = d.entry;
    const title = e
      ? (e.title.toLowerCase().includes(d.name.toLowerCase()) ? e.title : d.name + " " + e.title) +
        " PDF"
      : d.name + " chapter-wise and year-wise PDFs";
    return seoHead({
      title,
      description: e
        ? [
            "Download",
            title,
            e.subject,
            e.year || "",
            e.questions ? "· " + e.questions + " questions" : "",
            e.pages ? "· " + e.pages + " pages" : "",
          ]
            .filter(Boolean)
            .join(" ")
        : "Browse " + d.entries.length + " downloadable chapters and papers for " + d.name + ".",
      path: "pdf-library/" + d.exam + (e ? "/" + e.path : ""),
    });
  },
  component: PdfPage,
});
function PdfPage() {
  const { entry, entries, exam, name } = Route.useLoaderData();
  return (
    <div className="pdf-view">
      <div className="pdf-rule">
        <div className="pdf-container">
          <nav aria-label="Breadcrumb" className="pdf-crumb">
            <a href="/pdf-library#exams">Exams</a> / <a href={"/pdf-library/" + exam}>{name}</a>
          </nav>
          <p className="pdf-kicker">{name} · PDF library</p>
          <h1>{entry ? entry.title : name + " question papers and chapters"}</h1>
          <p className="pdf-sub">
            {entry
              ? [
                  entry.subject,
                  entry.date || entry.year,
                  entry.sourceType,
                  entry.questions && entry.questions + " questions",
                  entry.pages && entry.pages + " pages",
                ]
                  .filter(Boolean)
                  .join(" · ")
              : "Choose a full paper by year or download a chapter by subject."}
          </p>
          <PdfTabs
            exam={exam}
            active={entry?.kind === "chapter" ? "chapter" : entry ? "paper" : undefined}
          />
        </div>
      </div>
      <div className="pdf-container pdf-content">
        {entry ? (
          <article className="pdf-detail">
            <h2>{entry.kind === "chapter" ? "Chapter PDF" : "Question paper PDF"}</h2>
            {entry.years && <p>Question years: {entry.years.split(",").join(", ")}</p>}
            <DownloadPdf file={entry.file} title={entry.title} />
          </article>
        ) : (
          <div className="pdf-choices">
            {(["paper", "chapter"] as const).map((kind) => (
              <a
                href={pdfBrowsePath(exam, kind)}
                id={kind === "paper" ? "papers" : "chapters"}
                key={kind}
              >
                <strong>
                  {kind === "paper" ? "Year-wise question papers" : "Chapter-wise questions"}
                </strong>
                <span>
                  {entries.filter((e) => e.kind === kind).length}{" "}
                  {kind === "paper" ? "papers" : "chapters"} →
                </span>
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

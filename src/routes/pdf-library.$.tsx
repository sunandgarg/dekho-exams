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
  const hub = "/pdf-library/" + exam;
  return (
    <div className="exam-wrap">
      <nav aria-label="Breadcrumb" className="mb-5 flex gap-3 text-sm">
        <a href="/pdf-library" className="text-primary">
          PDF library
        </a>
        {entry && (
          <a href={hub} className="text-primary">
            {name}
          </a>
        )}
      </nav>
      <h1 className="text-3xl font-bold">{entry ? entry.title : name + " PDFs"}</h1>
      {entry ? (
        <article className="mt-5 space-y-4">
          <p>
            {[
              name,
              entry.kind === "chapter" ? "Chapter collection" : "Previous-year paper",
              entry.subject,
              entry.date || entry.year || "",
              entry.shift === "Not specified" ? "" : entry.shift,
            ]
              .filter(Boolean)
              .join(" · ")}
          </p>
          {entry.sourceType && <p>{entry.sourceType}</p>}
          {entry.years && <p>Question years: {entry.years.split(",").join(", ")}</p>}
          <p>
            {[
              entry.questions && entry.questions + " questions",
              entry.pages && entry.pages + " pages",
            ]
              .filter(Boolean)
              .join(" · ")}
          </p>
          <a className="exam-btn exam-btn-solid inline-flex" href={entry.file} download>
            Download PDF
          </a>
        </article>
      ) : (
        (["chapter", "paper"] as const).map((kind) => {
          const list = entries.filter((e) => e.kind === kind);
          const groups = Array.from(
            new Set(list.map((e) => e.subject || String(e.year || "Papers"))),
          );
          return (
            <section key={kind} id={kind === "chapter" ? "chapters" : "papers"} className="mt-8">
              <h2 className="text-2xl font-bold">
                {kind === "chapter" ? "Chapter-wise PDFs" : "Year-wise papers"} ({list.length})
              </h2>
              {groups.map((group) => (
                <section key={group} className="my-5">
                  <h3 className="mb-2 text-lg font-semibold">{group}</h3>
                  <ul className="grid gap-2 sm:grid-cols-2">
                    {list
                      .filter((e) => (e.subject || String(e.year || "Papers")) === group)
                      .map((e) => (
                        <li key={e.path}>
                          <a
                            className="exam-pastel-card block rounded-lg border p-3"
                            href={hub + "/" + e.path}
                          >
                            {e.title}
                          </a>
                        </li>
                      ))}
                  </ul>
                </section>
              ))}
            </section>
          );
        })
      )}
    </div>
  );
}

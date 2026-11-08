import { archiveCatalog } from "@/lib/jee-catalog";
import { createFileRoute, notFound } from "@tanstack/react-router";
import { ArchiveNav, EditionLinks } from "@/components/exams/jee-archive";
import { seoHead } from "@/lib/seo";
export const Route = createFileRoute("/pyq-pdfs/past-years/jee/$archive/$subject/$chapter")({
  loader: ({ params: p }) => {
    if (!Object.hasOwn(archiveCatalog(p.archive).meta, p.subject + "/" + p.chapter))
      throw notFound();
    return p;
  },
  head: ({ loaderData: d }) =>
    seoHead({
      title: d
        ? archiveCatalog(d.archive).name + " " + d.chapter.replaceAll("-", " ") + " chapter PDFs"
        : "Chapter PDFs unavailable",
      description: "Open a chapter PDF by language and edition.",
      path: d
        ? "pyq-pdfs" + archiveCatalog(d.archive).jeeHub + "/" + d.subject + "/" + d.chapter
        : "questions",
      noindex: true,
    }),
  component: () => {
    const d = Route.useLoaderData();
    const { jeeHub } = archiveCatalog(d.archive);
    return (
      <main className="exam-wrap exam-jee-page">
        <ArchiveNav />
        <h1 className="text-3xl font-bold capitalize">{d.chapter.replaceAll("-", " ")} PDFs</h1>
        <p className="my-3 text-muted-foreground">
          Open a Dekhoexams edition, choose whether to include solutions, then print or save as PDF.
        </p>
        <EditionLinks edition={d.subject + "--" + d.chapter} />
        <a
          className="mt-4 inline-block text-primary"
          href={jeeHub + "/" + d.subject + "/" + d.chapter}
        >
          Practise this chapter →
        </a>
      </main>
    );
  },
});

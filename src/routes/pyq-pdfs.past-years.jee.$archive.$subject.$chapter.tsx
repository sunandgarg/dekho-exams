import { getArchivePdf } from "@/lib/pdf-library.functions";
import { PdfTabs } from "@/components/exams/pdf-browser";
import { archiveCatalog } from "@/lib/jee-catalog";
import { createFileRoute, notFound } from "@tanstack/react-router";
import { EditionLinks } from "@/components/exams/jee-archive";
import { seoHead } from "@/lib/seo";
export const Route = createFileRoute("/pyq-pdfs/past-years/jee/$archive/$subject/$chapter")({
  loader: async ({ params: p }) => {
    if (!Object.hasOwn(archiveCatalog(p.archive).meta, p.subject + "/" + p.chapter))
      throw notFound();
    return {
      ...p,
      file: await getArchivePdf({
        data: { exam: archiveCatalog(p.archive).id, edition: p.subject + "--" + p.chapter },
      }),
    };
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
    }),
  component: () => {
    const d = Route.useLoaderData();
    const { jeeHub } = archiveCatalog(d.archive);
    return (
      <div className="pdf-container pdf-content">
        <PdfTabs exam={d.archive} active="chapter" />
        <h1 className="text-3xl font-bold capitalize">{d.chapter.replaceAll("-", " ")} PDFs</h1>
        <p className="my-3 text-muted-foreground">
          {d.file
            ? "Download the chapter or open a print edition with optional solutions."
            : "Open the print edition to print this chapter or save it as a PDF."}
        </p>
        <EditionLinks file={d.file} edition={d.subject + "--" + d.chapter} />
        <a
          className="mt-4 inline-block text-primary"
          href={jeeHub + "/" + d.subject + "/" + d.chapter}
        >
          Practise this chapter →
        </a>
      </div>
    );
  },
});

import { archiveCatalog } from "@/lib/jee-catalog";
import { createFileRoute, notFound } from "@tanstack/react-router";
import { ChapterPdfCatalog } from "@/components/exams/jee-archive";
import { seoHead } from "@/lib/seo";
export const Route = createFileRoute("/pyq-pdfs/past-years/jee/$archive/$subject/")({
  loader: ({ params: p }) => {
    if (!Object.hasOwn(archiveCatalog(p.archive).chapters, p.subject)) throw notFound();
    return p.subject;
  },
  head: ({ params, loaderData: s }) =>
    seoHead({
      title: archiveCatalog(params.archive).name + " " + (s ?? "") + " chapter PDFs",
      description: "Print a Dekhoexams chapter edition with optional solutions.",
      path: "pyq-pdfs" + archiveCatalog(params.archive).jeeHub + "/" + s,
    }),
  component: () => <ChapterPdfCatalog subject={Route.useLoaderData()} />,
});

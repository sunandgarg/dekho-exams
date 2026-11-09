import { archiveCatalog } from "@/lib/jee-catalog";
import { createFileRoute } from "@tanstack/react-router";
import { ChapterPdfCatalog } from "@/components/exams/jee-archive";
import { seoHead } from "@/lib/seo";
export const Route = createFileRoute("/pyq-pdfs/past-years/jee/$archive/")({
  loader: ({ params }) => archiveCatalog(params.archive).id,
  head: ({ params }) =>
    seoHead({
      title: archiveCatalog(params.archive).name + " previous-year chapter PDFs",
      description: "Find chapter PDFs by subject.",
      path: "pyq-pdfs" + archiveCatalog(params.archive).jeeHub,
    }),
  component: () => <ChapterPdfCatalog />,
});

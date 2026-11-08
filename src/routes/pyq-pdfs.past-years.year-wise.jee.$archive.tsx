import { archiveCatalog } from "@/lib/jee-catalog";
import { createFileRoute } from "@tanstack/react-router";
import { PaperCatalog } from "@/components/exams/jee-archive";
import { seoHead } from "@/lib/seo";
export const Route = createFileRoute("/pyq-pdfs/past-years/year-wise/jee/$archive")({
  loader: ({ params }) => archiveCatalog(params.archive).id,
  head: ({ params }) =>
    seoHead({
      title: archiveCatalog(params.archive).name + " previous-year question paper PDFs",
      description: "Choose your year, shift, language and PDF edition.",
      path: archiveCatalog(params.archive).pdfHub.slice(1),
      noindex: true,
    }),
  component: () => <PaperCatalog pdf />,
});

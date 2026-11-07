import { createFileRoute } from "@tanstack/react-router";
import { PaperCatalog, pdfHub } from "@/components/exams/jee-archive";
import { seoHead } from "@/lib/seo";
export const Route = createFileRoute("/pyq-pdfs/past-years/year-wise/jee/jee-main")({
  head: () =>
    seoHead({
      title: "JEE Main previous-year question paper PDFs",
      description: "Choose your year, shift, language and PDF edition.",
      path: pdfHub.slice(1),
      noindex: true,
    }),
  component: () => <PaperCatalog pdf />,
});

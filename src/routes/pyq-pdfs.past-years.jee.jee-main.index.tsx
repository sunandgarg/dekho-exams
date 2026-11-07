import { createFileRoute } from "@tanstack/react-router";
import { ChapterPdfCatalog, jeeHub } from "@/components/exams/jee-archive";
import { seoHead } from "@/lib/seo";
export const Route = createFileRoute("/pyq-pdfs/past-years/jee/jee-main/")({
  head: () =>
    seoHead({
      title: "JEE Main previous-year chapter PDFs",
      description: "Find JEE Main chapter PDFs by subject.",
      path: "pyq-pdfs" + jeeHub,
      noindex: true,
    }),
  component: () => <ChapterPdfCatalog />,
});

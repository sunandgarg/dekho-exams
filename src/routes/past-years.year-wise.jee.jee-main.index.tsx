import { createFileRoute } from "@tanstack/react-router";
import { PaperCatalog, paperHub } from "@/components/exams/jee-archive";
import { seoHead } from "@/lib/seo";
export const Route = createFileRoute("/past-years/year-wise/jee/jee-main/")({
  head: () =>
    seoHead({
      title: "JEE Main previous-year papers by year and shift",
      description: "Practise a JEE Main paper by date, shift and subject.",
      path: paperHub.slice(1),
      noindex: true,
    }),
  component: () => <PaperCatalog />,
});

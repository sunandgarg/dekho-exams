import { archiveCatalog } from "@/lib/jee-catalog";
import { createFileRoute } from "@tanstack/react-router";
import { PaperCatalog } from "@/components/exams/jee-archive";
import { seoHead } from "@/lib/seo";
export const Route = createFileRoute("/past-years/year-wise/jee/$archive/")({
  loader: ({ params }) => archiveCatalog(params.archive).id,
  head: ({ params }) =>
    seoHead({
      title: archiveCatalog(params.archive).name + " previous-year papers by year and shift",
      description: "Practise a JEE paper by date, shift and subject.",
      path: archiveCatalog(params.archive).paperHub.slice(1),
      noindex: true,
    }),
  component: () => <PaperCatalog />,
});

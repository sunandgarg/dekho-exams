import { archiveCatalog } from "@/lib/jee-catalog";
import { createFileRoute, notFound } from "@tanstack/react-router";
import { PaperPage } from "@/components/exams/jee-archive";
import { archiveList } from "@/lib/jee-archive.functions";
import { seoHead } from "@/lib/seo";
export const Route = createFileRoute("/past-years/year-wise/jee/$archive/$paper/")({
  loader: async ({ params }) => {
    const catalog = archiveCatalog(params.archive);
    const paper = catalog.papers.find((p) => p.slug === params.paper);
    if (!paper) throw notFound();
    const rows = await archiveList({ data: { exam: catalog.id, paper: paper.slug } });
    if (!rows) throw notFound();
    return { exam: catalog.id, paper, rows };
  },
  head: ({ loaderData: d }) =>
    seoHead({
      title: d?.paper.title || "Paper not found",
      description: "Read and practise this paper by subject.",
      path: d ? archiveCatalog(d.exam).paperHub.slice(1) + "/" + d.paper.slug : "questions",
    }),
  component: () => <PaperPage {...Route.useLoaderData()} />,
});

import { createFileRoute, notFound } from "@tanstack/react-router";
import { PaperPage, paperHub } from "@/components/exams/jee-archive";
import papers from "@/data/jee-main-papers.json";
import { archiveList } from "@/lib/jee-archive.functions";
import { seoHead } from "@/lib/seo";
export const Route = createFileRoute("/past-years/year-wise/jee/jee-main/$paper/")({
  loader: async ({ params }) => {
    const paper = papers.find((p) => p.slug === params.paper);
    if (!paper) throw notFound();
    const rows = await archiveList({ data: { paper: paper.slug } });
    if (!rows) throw notFound();
    return { paper, rows };
  },
  head: ({ loaderData: d }) =>
    seoHead({
      title: d?.paper.title || "Paper not found",
      description: "Read and practise this paper by subject.",
      path: d ? paperHub.slice(1) + "/" + d.paper.slug : "questions",
      noindex: true,
    }),
  component: () => <PaperPage {...Route.useLoaderData()} />,
});

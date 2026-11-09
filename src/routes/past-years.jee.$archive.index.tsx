import { archiveCatalog } from "@/lib/jee-catalog";
import { createFileRoute } from "@tanstack/react-router";
import { examBySlug } from "@/lib/question-bank";
import { seoHead } from "@/lib/seo";
import { ExamHub } from "./questions.$exam.index";

export const Route = createFileRoute("/past-years/jee/$archive/")({
  loader: ({ params }) => archiveCatalog(params.archive).id,
  head: ({ params }) =>
    seoHead({
      title: archiveCatalog(params.archive).name + " chapter-wise questions",
      description: "Browse Physics, Chemistry and Mathematics by unit and chapter.",
      path: archiveCatalog(params.archive).jeeHub.slice(1),
    }),
  component: () => <ExamHub exam={examBySlug(Route.useLoaderData())!} />,
});

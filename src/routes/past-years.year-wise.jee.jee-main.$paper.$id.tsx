import { createFileRoute, notFound } from "@tanstack/react-router";
import { QuestionView, paperHub } from "@/components/exams/jee-archive";
import { archiveQuestion } from "@/lib/jee-archive.functions";
import { seoHead } from "@/lib/seo";
export const Route = createFileRoute("/past-years/year-wise/jee/jee-main/$paper/$id")({
  validateSearch: (s: Record<string, unknown>): { lang?: "hi" | "en" } =>
    s["lang"] === "hi" ? { lang: "hi" } : s["lang"] === "en" ? { lang: "en" } : {},
  loader: async ({ params }) => {
    const q = await archiveQuestion({ data: params.id });
    if (!q || q.chapter || q.paper !== params.paper) throw notFound();
    return q;
  },
  head: ({ loaderData: q }) =>
    seoHead({
      title: q ? q.teaser.slice(0, 100) + " · JEE Main" : "Question not found",
      description: "Practise a previous-year JEE Main question.",
      path: q
        ? q.canonical
          ? "past-years/jee/question/" + q.canonical
          : paperHub.slice(1) + "/" + q.paper + "/" + q.slug
        : "questions",
      noindex: true,
    }),
  component: () => {
    const q = Route.useLoaderData();
    return (
      <QuestionView
        key={q.slug + Route.useSearch().lang}
        language={Route.useSearch().lang ?? "en"}
        q={q}
        inPaper
      />
    );
  },
});

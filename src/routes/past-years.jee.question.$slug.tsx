import { readyQuestion } from "@/lib/jee-search";
import { createFileRoute, notFound } from "@tanstack/react-router";
import { QuestionView } from "@/components/exams/jee-archive";
import { archiveQuestion } from "@/lib/jee-archive.functions";
import { seoHead } from "@/lib/seo";
export const Route = createFileRoute("/past-years/jee/question/$slug")({
  validateSearch: (s: Record<string, unknown>): { lang?: "hi" | "en" } =>
    s["lang"] === "hi" ? { lang: "hi" } : s["lang"] === "en" ? { lang: "en" } : {},
  loader: async ({ params }) => {
    const q = await archiveQuestion({ data: {id:params.slug} });
    if (!q?.chapter) throw notFound();
    return q;
  },
  head: ({ loaderData: q }) =>
    seoHead({
      title: q ? q.teaser.slice(0, 100) + " · " + q.paperTitle : "Question not found",
      description: "Practise a JEE previous-year question with its explanation.",
      path: q ? "past-years/jee/question/" + q.slug : "questions",
      noindex: !readyQuestion(q),
    }),
  component: () => {
    const q = Route.useLoaderData();
    return (
      <QuestionView
        key={q.slug + Route.useSearch().lang}
        language={Route.useSearch().lang ?? "en"}
        q={q} owner={q.exam}
      />
    );
  },
});

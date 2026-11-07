import { createFileRoute, notFound } from "@tanstack/react-router";
import { examBySlug, subjectOf } from "@/lib/question-bank";
import { seoHead } from "@/lib/seo";
import { ExamHub } from "./questions.$exam.index";

const exam = examBySlug("jee-main")!;
export const Route = createFileRoute("/past-years/jee/jee-main/$subject/")({
  loader: ({ params }) => {
    const subject = subjectOf(exam, params.subject);
    if (!subject) throw notFound();
    return { name: subject.name, slug: subject.slug };
  },
  head: ({ loaderData: d }) =>
    seoHead({
      title: d ? `JEE Main ${d.name} chapters` : "Subject unavailable",
      description: "Choose a chapter to practise.",
      path: `past-years/jee/jee-main/${d?.slug ?? ""}`,
      noindex: true,
    }),
  component: () => <ExamHub exam={exam} subject={Route.useLoaderData().slug} />,
});

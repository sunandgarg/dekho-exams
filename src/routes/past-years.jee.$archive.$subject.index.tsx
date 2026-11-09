import { archiveCatalog } from "@/lib/jee-catalog";
import { createFileRoute, notFound } from "@tanstack/react-router";
import { examBySlug, subjectOf } from "@/lib/question-bank";
import { seoHead } from "@/lib/seo";
import { ExamHub } from "./questions.$exam.index";

export const Route = createFileRoute("/past-years/jee/$archive/$subject/")({
  loader: ({ params }) => {
    const exam = examBySlug(archiveCatalog(params.archive).id)!;
    const subject = subjectOf(exam, params.subject);
    if (!subject) throw notFound();
    return { exam: exam.slug, examName: exam.name, name: subject.name, slug: subject.slug };
  },
  head: ({ loaderData: d }) =>
    seoHead({
      title: d ? `${d.examName} ${d.name} chapters` : "Subject unavailable",
      description: "Choose a chapter to practise.",
      path: `past-years/jee/${d?.exam}/${d?.slug ?? ""}`,
    }),
  component: () => (
    <ExamHub exam={examBySlug(Route.useLoaderData().exam)!} subject={Route.useLoaderData().slug} />
  ),
});

import { createFileRoute } from "@tanstack/react-router";
import { examBySlug } from "@/lib/question-bank";
import { seoHead } from "@/lib/seo";
import { ExamHub } from "./questions.$exam.index";

export const Route = createFileRoute("/past-years/jee/jee-main/")({
  head: () =>
    seoHead({
      title: "JEE Main chapter-wise questions",
      description: "Browse JEE Main Physics, Chemistry and Mathematics by unit and chapter.",
      path: "past-years/jee/jee-main",
      noindex: true,
    }),
  component: () => <ExamHub exam={examBySlug("jee-main")!} />,
});

import { createFileRoute } from "@tanstack/react-router";
import { seoHead } from "@/lib/seo";
import { ExamDirectory } from "@/components/exams/exam-ui";

export const Route = createFileRoute("/questions/")({
  head: () => seoHead({
    title: "All Exams — Chapter-wise and Paper-wise Questions",
    description: "Pick an exam to browse questions chapter-wise or paper-wise, with solutions, bookmarks and timed practice.",
    path: "questions",
    noindex: true,
  }),
  component: ExamDirectory,
});

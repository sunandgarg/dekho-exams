import { createFileRoute } from "@tanstack/react-router";
import { ExamDirectory } from "@/components/exams/exam-ui";
import { seoHead, homeSchema } from "@/lib/seo";

export const Route = createFileRoute("/")({
  head: () =>
    seoHead({
      title: "Exam Questions with Solutions — JEE, NEET, GATE, UPSC, SSC, CBSE",
      description:
        "Chapter-wise and paper-wise questions with solutions for JEE Main, JEE Advanced, NEET, GATE, UPSC, NDA, SSC and CBSE on Dekhoexams.",
      schema: homeSchema(),
    }),
  component: ExamDirectory,
  errorComponent: () => (
    <p className="p-10 text-center">The home page couldn't load. Please refresh.</p>
  ),
});

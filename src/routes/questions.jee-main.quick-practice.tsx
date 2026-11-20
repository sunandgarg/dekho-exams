import { createFileRoute } from "@tanstack/react-router";
import { QuickPractice } from "@/components/student/quick-practice";
import { seoHead } from "@/lib/seo";

export const Route = createFileRoute("/questions/jee-main/quick-practice")({
  head: () =>
    seoHead({
      title: "JEE Main quick practice",
      description: "Practise six JEE Main questions and get a subject breakdown.",
      path: "questions/jee-main/quick-practice",
      noindex: true,
    }),
  component: QuickPractice,
});

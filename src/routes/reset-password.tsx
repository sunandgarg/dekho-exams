import { createFileRoute } from "@tanstack/react-router";
import { seoHead } from "@/lib/seo";
import { LearnerAuth } from "@/components/cms/surfaces";
export const Route = createFileRoute("/reset-password")({
  head: () =>
    seoHead({
      title: "Reset your password",
      description: "AI Trove learner account recovery.",
      path: "reset-password",
      noindex: true,
    }),
  component: () => <LearnerAuth view="reset-password" />,
});

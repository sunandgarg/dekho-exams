import { createFileRoute } from "@tanstack/react-router";
import { seoHead } from "@/lib/seo";
import { LearnerAuth } from "@/components/cms/surfaces";
export const Route = createFileRoute("/auth")({
  head: () =>
    seoHead({
      title: "Sign in",
      description: "AI Trove learner access.",
      path: "auth",
      noindex: true,
    }),
  component: () => <LearnerAuth view="login" />,
});

import { createFileRoute } from "@tanstack/react-router";
import { PlatformWorkspace } from "@/components/student/platform-workspace";
import { seoHead } from "@/lib/seo";

export const Route = createFileRoute("/platform-school")({
  head: () =>
    seoHead({
      title: "School workspace",
      description: "Private DekhoExams workspace.",
      path: "platform-school",
      noindex: true,
    }),
  component: () => <PlatformWorkspace role="school" />,
});

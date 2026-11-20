import { createFileRoute } from "@tanstack/react-router";
import { PlatformWorkspace } from "@/components/student/platform-workspace";
import { seoHead } from "@/lib/seo";

export const Route = createFileRoute("/platform-admin")({
  head: () =>
    seoHead({
      title: "Admin workspace",
      description: "Private DekhoExams workspace.",
      path: "platform-admin",
      noindex: true,
    }),
  component: () => <PlatformWorkspace role="owner" />,
});

import { createFileRoute } from "@tanstack/react-router";
import { PlatformWorkspace } from "@/components/student/platform-workspace";
import { seoHead } from "@/lib/seo";

export const Route = createFileRoute("/platform-student")({
  head: () =>
    seoHead({
      title: "Student workspace",
      description: "Private DekhoExams workspace.",
      path: "platform-student",
      noindex: true,
    }),
  component: () => <PlatformWorkspace role="student" />,
});

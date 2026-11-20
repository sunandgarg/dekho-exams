import { createFileRoute } from "@tanstack/react-router";
import { PlatformWorkspace } from "@/components/student/platform-workspace";
import { seoHead } from "@/lib/seo";

export const Route = createFileRoute("/platform-admin_/leads")({
  head: () =>
    seoHead({
      title: "All leads",
      description: "Private DekhoExams lead management.",
      path: "platform-admin/leads",
      noindex: true,
    }),
  component: () => <PlatformWorkspace role="owner" ownerView="leads" />,
});

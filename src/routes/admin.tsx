import { createFileRoute } from "@tanstack/react-router";
import { seoHead } from "@/lib/seo";
import { AdminPortal } from "@/components/cms/admin-portal";
export const Route = createFileRoute("/admin")({
  head: () =>
    seoHead({
      title: "WordPress editor",
      description: "AI Trove editorial workspace.",
      path: "admin",
      noindex: true,
    }),
  component: AdminPortal,
});

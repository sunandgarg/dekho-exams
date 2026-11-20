import { createFileRoute } from "@tanstack/react-router";
import { PlatformPreview } from "@/components/student/platform-preview";
import { seoHead } from "@/lib/seo";

export const Route = createFileRoute("/platform-preview")({
  head: () =>
    seoHead({
      title: "Student platform design preview",
      description:
        "Preview the DekhoExams student, school coupon and report experience. Sample data only.",
      path: "platform-preview",
      noindex: true,
    }),
  component: PlatformPreview,
});

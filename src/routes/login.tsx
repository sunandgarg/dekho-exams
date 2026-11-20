import { createFileRoute } from "@tanstack/react-router";
import { PlatformEntry } from "@/components/student/platform-entry";
import { seoHead } from "@/lib/seo";

export const Route = createFileRoute("/login")({
  head: () =>
    seoHead({
      title: "Sign in to DekhoExams",
      description: "Open your student or school workspace, or request access.",
      path: "login",
      noindex: true,
    }),
  component: PlatformEntry,
});

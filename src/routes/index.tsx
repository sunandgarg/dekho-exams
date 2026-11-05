import { createFileRoute } from "@tanstack/react-router";
import { Home } from "@/components/cms/home";
import { seoHead, homeSchema } from "@/lib/seo";

export const Route = createFileRoute("/")({
  head: () =>
    seoHead({
      title: "Study Resources and Official Exam Updates for Classes 1–12",
      description:
        "Explore Class 1–12 lessons and NCERT resources, plus official links for CBSE date sheets and results, JEE Main and NEET answer keys on Dekhoexams.",
      schema: homeSchema(),
    }),
  component: Home,
  errorComponent: () => (
    <p className="p-10 text-center">The home page couldn't load. Please refresh.</p>
  ),
});

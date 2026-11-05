import { createFileRoute, notFound, redirect } from "@tanstack/react-router";
import { EDUCATION_ALIASES } from "@/lib/education-catalog";
export const Route = createFileRoute("/study/$")({
  beforeLoad: ({ params }) => {
    const target = EDUCATION_ALIASES[`/study/${params._splat ?? ""}`];
    if (!target) throw notFound();
    throw redirect({ href: target, statusCode: 301 });
  },
});

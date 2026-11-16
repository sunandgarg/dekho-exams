import { createFileRoute } from "@tanstack/react-router";
import { pdfExams } from "@/lib/pdf-library";
import { seoHead } from "@/lib/seo";
export const Route = createFileRoute("/pdf-library/")({
  head: () =>
    seoHead({
      title: "Chapter-wise and year-wise exam PDFs",
      description:
        "Download chapter collections and previous-year papers for eight engineering entrance exams.",
      path: "pdf-library",
    }),
  component: () => (
    <div className="exam-wrap">
      <a href="/" className="text-sm text-primary">
        All exams
      </a>
      <h1 className="mt-4 text-3xl font-bold">Exam PDF library</h1>
      <p className="mt-2 text-muted-foreground">
        Choose an exam to download a chapter or a previous-year paper.
      </p>
      <div className="my-6 grid gap-3 sm:grid-cols-2">
        {Object.entries(pdfExams).map(([slug, name]) => (
          <a
            key={slug}
            href={"/pdf-library/" + slug}
            className="exam-pastel-card rounded-xl border p-5 font-bold"
          >
            {name}
          </a>
        ))}
      </div>
    </div>
  ),
});

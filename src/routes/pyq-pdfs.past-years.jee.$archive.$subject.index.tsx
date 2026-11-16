import { createFileRoute, notFound } from "@tanstack/react-router";
import { PdfBrowser } from "@/components/exams/pdf-browser";
import { getPdfBrowse } from "@/lib/pdf-library.functions";
import { pdfBrowsePath } from "@/lib/pdf-library";
import { seoHead } from "@/lib/seo";
export const Route = createFileRoute("/pyq-pdfs/past-years/jee/$archive/$subject/")({
  loader: async ({ params }) => {
    const data = await getPdfBrowse({
      data: { exam: params.archive, kind: "chapter", subject: params.subject },
    });
    if (!data) throw notFound();
    return data;
  },
  head: ({ loaderData: d }) =>
    d
      ? seoHead({
          title: [d.name, d.subject, "chapter-wise previous year question PDFs"]
            .filter(Boolean)
            .join(" "),
          description:
            "Download " + d.entries.length + " chapter PDFs by subject for " + d.name + ".",
          path: pdfBrowsePath(d.exam, d.kind).slice(1) + (d.subject ? "/" + d.subject : ""),
        })
      : seoHead({ title: "PDF collection unavailable", description: "", noindex: true }),
  component: () => <PdfBrowser data={Route.useLoaderData()} />,
});

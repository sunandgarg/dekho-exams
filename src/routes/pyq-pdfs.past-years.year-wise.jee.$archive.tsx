import { createFileRoute, notFound } from "@tanstack/react-router";
import { PdfBrowser } from "@/components/exams/pdf-browser";
import { getPdfBrowse } from "@/lib/pdf-library.functions";
import { pdfBrowsePath } from "@/lib/pdf-library";
import { seoHead } from "@/lib/seo";
export const Route = createFileRoute("/pyq-pdfs/past-years/year-wise/jee/$archive")({
  loader: async ({ params }) => {
    const data = await getPdfBrowse({ data: { exam: params.archive, kind: "paper" } });
    if (!data) throw notFound();
    return data;
  },
  head: ({ loaderData: d }) =>
    d
      ? seoHead({
          title: [d.name, d.subject, "previous year question paper PDFs"].filter(Boolean).join(" "),
          description:
            "Download " + d.entries.length + " papers by year and shift for " + d.name + ".",
          path: pdfBrowsePath(d.exam, d.kind).slice(1) + (d.subject ? "/" + d.subject : ""),
        })
      : seoHead({ title: "PDF collection unavailable", description: "", noindex: true }),
  component: () => <PdfBrowser data={Route.useLoaderData()} />,
});

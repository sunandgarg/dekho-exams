import { createFileRoute, notFound } from "@tanstack/react-router";
import { ChapterPdfCatalog, jeeHub } from "@/components/exams/jee-archive";
import { seoHead } from "@/lib/seo";
import chapterOrder from "@/data/jee-main-chapters.json";
export const Route = createFileRoute("/pyq-pdfs/past-years/jee/jee-main/$subject/")({
  loader: ({ params: p }) => {
    if (!Object.hasOwn(chapterOrder, p.subject)) throw notFound();
    return p.subject;
  },
  head: ({ loaderData: s }) =>
    seoHead({
      title: "JEE Main " + (s ?? "") + " chapter PDFs",
      description: "Open printable JEE Main chapters.",
      path: "pyq-pdfs" + jeeHub + "/" + s,
      noindex: true,
    }),
  component: () => <ChapterPdfCatalog subject={Route.useLoaderData()} />,
});

import { createFileRoute, notFound } from "@tanstack/react-router";
import { archiveChapterMeta } from "@/lib/jee-archive.functions";
import { ArchiveNav, jeeHub } from "@/components/exams/jee-archive";
import { seoHead } from "@/lib/seo";
import hindiPrint from "@/data/jee-main-hindi-print.json";
import chapters from "@/data/jee-main-chapters.json";
export const Route = createFileRoute("/pyq-pdfs/past-years/jee/jee-main/$subject/$chapter")({
  loader: async ({ params: p }) => {
    if (!(chapters as Record<string, string[]>)[p.subject]?.includes(p.chapter)) throw notFound();
    const m = await archiveChapterMeta({ data: p });
    if (!m) throw notFound();
    return { ...p, pdfs: m.pdfs };
  },
  head: ({ loaderData: d }) =>
    seoHead({
      title: d
        ? "JEE Main " + d.chapter.replaceAll("-", " ") + " chapter PDFs"
        : "Chapter PDFs unavailable",
      description: "Open a chapter PDF by language and edition.",
      path: d ? "pyq-pdfs" + jeeHub + "/" + d.subject + "/" + d.chapter : "questions",
      noindex: true,
    }),
  component: () => {
    const d = Route.useLoaderData();
    return (
      <main className="exam-wrap exam-jee-page">
        <ArchiveNav />
        <h1 className="text-3xl font-bold capitalize">{d.chapter.replaceAll("-", " ")} PDFs</h1>
        <p className="my-3 text-muted-foreground">
          Print a Dekhoexams edition, or open an external PDF by language and theme.
        </p>
        <div className="mb-4 flex flex-wrap gap-3">
          <a
            className="rounded-lg border p-3 font-semibold"
            href={"/pyq-pdfs/print/" + d.subject + "--" + d.chapter + "/en"}
          >
            Print English edition
          </a>
          {hindiPrint.includes(d.subject + "--" + d.chapter) && (
            <a
              className="rounded-lg border p-3 font-semibold"
              href={"/pyq-pdfs/print/" + d.subject + "--" + d.chapter + "/hi"}
            >
              Print Hindi edition
            </a>
          )}
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          {Object.entries(d.pdfs).map(([path, label]) => (
            <a
              className="exam-pastel-card rounded-xl border p-4 font-semibold"
              key={path}
              href={"https://pdf.questions.examgoal.com" + path}
              target="_blank"
              rel="nofollow noreferrer"
            >
              {label} ↗
            </a>
          ))}
        </div>
        <a
          className="mt-4 inline-block text-primary"
          href={jeeHub + "/" + d.subject + "/" + d.chapter}
        >
          Practise this chapter →
        </a>
      </main>
    );
  },
});

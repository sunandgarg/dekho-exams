import { createFileRoute, notFound } from "@tanstack/react-router";
import chapters from "@/data/jee-main-chapters.json";
import { archiveList } from "@/lib/jee-archive.functions";
import { ArchiveNav, ArchiveRows, jeeHub } from "@/components/exams/jee-archive";
import { seoHead } from "@/lib/seo";
export const Route = createFileRoute("/past-years/jee/jee-main/$subject/$chapter/$kind")({
  loader: async ({ params: p }) => {
    if (
      !(chapters as Record<string, string[]>)[p.subject]?.includes(p.chapter) ||
      !["mcq", "integer", "mcqm"].includes(p.kind)
    )
      throw notFound();
    const rows = (await archiveList({ data: { subject: p.subject, chapter: p.chapter } }))?.filter(
      (x) => x.group === p.kind,
    );
    if (!rows?.length) throw notFound();
    return { ...p, rows };
  },
  head: ({ loaderData: d }) =>
    seoHead({
      title: d ? d.chapter.replaceAll("-", " ") + " · JEE Main " + d.kind : "Questions unavailable",
      description: "Practise one question type from this JEE Main chapter.",
      path: d ? jeeHub.slice(1) + "/" + d.subject + "/" + d.chapter + "/" + d.kind : "questions",
      noindex: true,
    }),
  component: () => {
    const d = Route.useLoaderData();
    return (
      <main className="exam-wrap exam-jee-page">
        <ArchiveNav />
        <h1 className="text-3xl font-bold capitalize">{d.chapter.replaceAll("-", " ")}</h1>
        <a className="text-sm text-primary" href={jeeHub + "/" + d.subject + "/" + d.chapter}>
          All question types
        </a>
        <ArchiveRows rows={d.rows} filter={d.kind} />
      </main>
    );
  },
});

import { archiveCatalog } from "@/lib/jee-catalog";
import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { canonicalUrl, seoHead } from "@/lib/seo";
import { chapterName, examBySlug, jeeMainPublicChapterSlug, subjectOf } from "@/lib/question-bank";
import { archiveList, archiveChapterMeta } from "@/lib/jee-archive.functions";
import { ChapterContent } from "./questions.$exam.$subject.$chapter";

export const Route = createFileRoute("/past-years/jee/$archive/$subject/$chapter/")({
  loader: async ({ params }) => {
    const catalog = archiveCatalog(params.archive);
    const exam = examBySlug(catalog.id)!;
    const sub = subjectOf(exam, params.subject);
    const entry = catalog.meta[params.subject + "/" + params.chapter];
    if (!sub || !entry) throw notFound();
    const internal =
      sub.chapters.find(
        ([slug]) =>
          slug === params.chapter || jeeMainPublicChapterSlug(sub.slug, slug) === params.chapter,
      )?.[0] ?? params.chapter;
    const name = entry.name;
    const data = { exam: catalog.id, subject: sub.slug, chapter: params.chapter };
    const [rows, meta] = await Promise.all([archiveList({ data }), archiveChapterMeta({ data })]);
    if (!rows) throw notFound();
    return {
      rows,
      meta,
      exam: exam.slug,
      examName: exam.name,
      subject: sub.slug,
      subjectName: sub.name,
      chapter: internal,
      publicChapter: params.chapter,
      chapterName: name,
    };
  },
  head: ({ loaderData: d }) =>
    seoHead({
      title: d ? `${d.chapterName} — ${d.examName} ${d.subjectName} Practice` : "Chapter not found",
      description: d
        ? `Previous-year ${d.chapterName} questions for ${d.examName} ${d.subjectName}, with solutions.`
        : "This chapter is not in the question bank.",
      path: d ? `past-years/jee/${d.exam}/${d.subject}/${d.publicChapter}` : "questions",
      schema: d
        ? [
            {
              "@context": "https://schema.org",
              "@type": "BreadcrumbList",
              itemListElement: [
                {
                  "@type": "ListItem",
                  position: 1,
                  name: d.examName,
                  item: canonicalUrl("past-years/jee/" + d.exam),
                },
                {
                  "@type": "ListItem",
                  position: 2,
                  name: d.chapterName,
                  item: canonicalUrl(`past-years/jee/${d.exam}/${d.subject}/${d.publicChapter}`),
                },
              ],
            },
          ]
        : [],
    }),
  notFoundComponent: () => (
    <div className="exam-wrap">
      <h1>Chapter not found</h1>
      <Link to="/questions">Back to exams</Link>
    </div>
  ),
  component: () => (
    <ChapterContent
      d={Route.useLoaderData()}
      rows={Route.useLoaderData().rows}
      meta={Route.useLoaderData().meta}
    />
  ),
});

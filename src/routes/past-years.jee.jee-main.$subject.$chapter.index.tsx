import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { canonicalUrl, seoHead } from "@/lib/seo";
import { chapterName, examBySlug, jeeMainPublicChapterSlug, subjectOf } from "@/lib/question-bank";
import { archiveList, archiveChapterMeta } from "@/lib/jee-archive.functions";
import { ChapterContent } from "./questions.$exam.$subject.$chapter";

export const Route = createFileRoute("/past-years/jee/jee-main/$subject/$chapter/")({
  loader: async ({ params }) => {
    const exam = examBySlug("jee-main")!;
    const sub = subjectOf(exam, params.subject);
    const internal = sub?.chapters.find(
      ([slug]) => jeeMainPublicChapterSlug(params.subject, slug) === params.chapter,
    )?.[0];
    const name = sub && internal && chapterName(sub, internal);
    if (!sub || !internal || !name) throw notFound();
    const data = { subject: sub.slug, chapter: params.chapter };
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
      chapterName: name,
    };
  },
  head: ({ loaderData: d }) =>
    seoHead({
      title: d ? `${d.chapterName} — JEE Main ${d.subjectName} Practice` : "Chapter not found",
      description: d
        ? `Previous-year ${d.chapterName} questions for JEE Main ${d.subjectName}, with solutions.`
        : "This chapter is not in the question bank.",
      path: d
        ? `past-years/jee/jee-main/${d.subject}/${jeeMainPublicChapterSlug(d.subject, d.chapter)}`
        : "questions",
      noindex: true,
      schema: d
        ? [
            {
              "@context": "https://schema.org",
              "@type": "BreadcrumbList",
              itemListElement: [
                {
                  "@type": "ListItem",
                  position: 1,
                  name: "JEE Main",
                  item: canonicalUrl("past-years/jee/jee-main"),
                },
                {
                  "@type": "ListItem",
                  position: 2,
                  name: d.chapterName,
                  item: canonicalUrl(
                    `past-years/jee/jee-main/${d.subject}/${jeeMainPublicChapterSlug(d.subject, d.chapter)}`,
                  ),
                },
              ],
            },
          ]
        : [],
    }),
  notFoundComponent: () => (
    <div className="exam-wrap">
      <h1>Chapter not found</h1>
      <Link to="/questions/$exam" params={{ exam: "jee-main" }}>
        Back to JEE Main
      </Link>
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

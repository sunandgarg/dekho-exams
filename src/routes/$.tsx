import { isPublicPath } from "@/lib/features";
import { createFileRoute, notFound } from "@tanstack/react-router";
import { z } from "zod";
import { CmsView, planPath, type SiteSearch } from "@/components/cms/templates";
import { entryQuery, listQuery, obj, str } from "@/lib/cms";
import { seoHead, schemaForEntry, isSeoReady } from "@/lib/seo";
import { EducationPage } from "@/components/education-page";
import {
  educationPage,
  ownsEducationPath,
  educationIndexable,
  educationBreadcrumbs,
  resourceById,
} from "@/lib/education-catalog";
import { canonicalUrl } from "@/lib/seo";
import { getSchoolLesson } from "@/lib/school-cms.functions";

const searchSchema = z.object({
  q: z.preprocess(
    (value) => (typeof value === "number" ? String(value) : value),
    z.string().max(120).optional().catch(undefined),
  ),
  grade: z.coerce
    .string()
    .regex(/^(?:[1-9]|1[0-2])$/)
    .optional()
    .catch(undefined),
  difficulty: z.string().max(20).optional().catch(undefined),
  topic: z.string().max(80).optional().catch(undefined),
  company: z.string().max(80).optional().catch(undefined),
  tab: z.string().max(20).optional().catch(undefined),
  page: z.coerce.number().int().min(1).max(20000).optional().catch(undefined),
});

const LIST_TITLES: Record<string, [string, string]> = {
  subjects: ["Programming Tutorials", "Browse programming and computer science subjects."],
  interview: ["Interview Preparation", "Practice technical interview topics and questions."],
  explore: ["Practice Problems", "Explore coding problems by topic, company and difficulty."],
  potd: ["Problem of the Day", "A hand-picked daily coding problem and its archive."],
  courses: ["Courses", "Live and self-paced programming courses with projects and certificates."],
  videos: ["Videos", "Short video lessons on programming and computer science."],
  events: ["Events & Contests", "Hackathons, coding contests and hiring challenges."],
  jobs: ["Tech Jobs", "Curated software and tech job openings."],
  category: ["Articles", "Browse articles in this category."],
  quizzes: ["Quizzes", "Check your knowledge and review explained answers."],
  paths: ["Learning paths", "Follow ordered learning resources."],
  companies: ["Companies", "Explore employer profiles and open roles."],
  authors: ["Authors", "Meet our contributors."],
  search: ["Search", "Search tutorials, problems, videos and more."],
};

export const Route = createFileRoute("/$")({
  validateSearch: (s): SiteSearch & { grade?: string | undefined } => searchSchema.parse(s),
  loaderDeps: ({ search }) => search,
  loader: async ({ params, deps, context }) => {
    const educationPath = `/${params._splat ?? ""}`;
    const page = educationPage(educationPath);
    if (page)
      return {
        plan: {
          kind: "education" as const,
          path: educationPath,
          lesson: page.resourceId
            ? await getSchoolLesson({ data: { id: page.resourceId } })
            : null,
        },
        entry: null,
      };
    if (ownsEducationPath(educationPath)) throw notFound();
    if (!isPublicPath(params._splat ?? "")) throw notFound();
    const plan = planPath(params._splat ?? "", deps);
    if (plan.kind === "list") {
      const list = await context.queryClient.ensureQueryData(listQuery(plan.input));
      if ((plan.template === "category" || plan.slug) && !list.total && !list.error)
        throw notFound();
      if ((deps.page ?? 1) > 1 && !list.items.length && !list.error) throw notFound();
      const header =
        plan.template === "category" && plan.slug
          ? await context.queryClient.ensureQueryData(entryQuery(`category/${plan.slug}`))
          : null;
      return {
        plan,
        entry: header
          ? {
              path: header.path,
              type: header.type,
              title: header.title,
              summary: header.summary,
              data: header.data,
              status: header.status,
              published_at: header.published_at,
              updated_at: header.updated_at,
            }
          : null,
      };
    }
    if (plan.kind === "screen" && !plan.source) return { plan, entry: null };
    const entry = await context.queryClient.ensureQueryData(
      entryQuery(plan.kind === "screen" ? plan.source! : plan.path),
    );
    if (!entry) throw notFound();
    if (plan.kind === "screen") {
      const expected = (
        {
          "quiz-attempt": "quiz",
          "quiz-result": "quiz",
          checkout: "course",
          lesson: "course",
          assignment: "course",
          contest: "event",
          leaderboard: "event",
          application: "job",
        } as Record<string, string>
      )[plan.screen];
      if (expected && entry.type !== expected) throw notFound();
      if (plan.index !== undefined) {
        const data = entry.data as { lessons?: unknown[]; syllabus?: { items?: unknown[] }[] };
        const count =
          data?.lessons?.length ||
          data?.syllabus?.reduce((n, m) => n + (m.items?.length ?? 0), 0) ||
          0;
        if (plan.index < 1 || plan.index > count) throw notFound();
      }
    }
    const rootPath = str(obj(entry.data).subject_root);
    const root =
      rootPath && rootPath !== entry.path
        ? await context.queryClient.ensureQueryData(entryQuery(rootPath))
        : entry;
    return {
      plan,
      entry: {
        path: entry.path,
        type: entry.type,
        title: entry.title,
        summary: entry.summary,
        data: { ...obj(entry.data), resource_tabs: obj(root?.data).resource_tabs ?? [] },
        status: entry.status,
        published_at: entry.published_at,
        updated_at: entry.updated_at,
      },
    };
  },
  head: ({ params, loaderData, match }) => {
    if (loaderData?.plan.kind === "education") {
      const page = educationPage(loaderData.plan.path)!;
      const resource = page.resourceId ? resourceById(page.resourceId) : undefined;
      const lesson = loaderData.plan.lesson;
      return seoHead({
        title: resource
          ? `Class ${resource.lesson.grade} ${resource.lesson.subject}: ${lesson?.title ?? page.title}`
          : page.title,
        description: lesson?.summary ?? page.description,
        path: page.path,
        noindex:
          !educationIndexable(page) ||
          Object.values(match.search).some((value) => value !== undefined && value !== ""),
        schema: [
          {
            "@context": "https://schema.org",
            "@type": resource ? "LearningResource" : "CollectionPage",
            name: page.title,
            description: page.description,
            url: canonicalUrl(page.path),
            inLanguage: "en",
            ...(resource
              ? {
                  learningResourceType: "Lesson and self-check",
                  educationalLevel: `Class ${resource.lesson.grade}`,
                }
              : {}),
          },
          {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            itemListElement: [{ title: "Home", path: "/" }, ...educationBreadcrumbs(page)].map(
              (p, i) => ({
                "@type": "ListItem",
                position: i + 1,
                name: p.title,
                item: canonicalUrl(p.path),
              }),
            ),
          },
        ],
      });
    }
    const fallback =
      params._splat?.split("/").filter(Boolean).at(-1)?.replace(/[-_]/g, " ") ??
      "Learning resource";
    let title = fallback;
    let description = "Explore this learning resource on Dekhoexams.";
    if (loaderData?.entry) {
      title = loaderData.entry.title;
      description = loaderData.entry.summary || description;
    } else if (loaderData?.plan.kind === "list") {
      const [t, d] = LIST_TITLES[loaderData.plan.template] ?? ["Browse", description];
      title = loaderData.plan.slug ? `${loaderData.plan.slug.replace(/-/g, " ")} ${t}` : t;
      description = d;
    }
    if (loaderData?.plan.kind === "screen")
      title = `${loaderData.plan.title}${loaderData.entry ? `: ${loaderData.entry.title}` : ""}`;
    const search = match.search;
    const filtered = !!(
      search.q ||
      search.difficulty ||
      search.topic ||
      search.company ||
      search.tab
    );
    const entry = loaderData?.entry;
    return seoHead({
      title,
      description,
      path: params._splat ?? "",
      page: search.page,
      noindex: !entry || !isSeoReady(entry) || filtered || loaderData?.plan.kind === "screen",
      schema: entry && loaderData?.plan.kind === "entry" ? schemaForEntry(entry) : [],
    });
  },
  component: CatchAllPage,
  errorComponent: ({ error }) => (
    <div className="mx-auto max-w-lg px-5 py-20 text-center">
      <h1 className="font-display text-2xl font-bold">This page didn't load</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        {(error instanceof Error && error.message) || "Please try again in a moment."}
      </p>
    </div>
  ),
});

function CatchAllPage() {
  const search = Route.useSearch();
  const { plan } = Route.useLoaderData();
  if (plan.kind === "education")
    return (
      <EducationPage
        path={plan.path}
        query={search.q ?? ""}
        grade={search.grade ?? ""}
        topic={search.topic ?? ""}
        lessonOverride={plan.lesson}
      />
    );
  return <CmsView plan={plan} search={search} fallback={null} />;
}

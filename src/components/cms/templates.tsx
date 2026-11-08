import { SafeMedia } from "./privacy-controls";
import { isPublicPath } from "@/lib/features";
import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
  type MouseEventHandler,
  type CSSProperties,
} from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import { useSuspenseQueries, useSuspenseQuery } from "@tanstack/react-query";
import {
  ArrowRight,
  BookOpen,
  BriefcaseBusiness,
  CalendarDays,
  Check,
  ChevronLeft,
  ChevronRight,
  CirclePlay,
  Clock,
  Code2,
  Flame,
  GraduationCap,
  MapPin,
  Play,
  Search,
  Star,
  Users,
} from "lucide-react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  Sheet,
  SheetTrigger,
  SheetContent,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { arr, entryQuery, listQuery, obj, str, type Entry, type EntryData } from "@/lib/cms";
import { TopicMark } from "./topic-mark";
import { JavaConceptGallery } from "./java-concept-gallery";
import { DifficultyBadge, DifficultyFilter } from "./difficulty";
import { LinkedListDemo } from "./linked-list-demo";
import { LinkedListReversal } from "./linked-list-reversal";
import type { ListInput } from "@/lib/cms.functions";
import { Markdown } from "./markdown";
import { surfacePlan, DIRECTORY_PATHS, type ScreenPlan } from "@/lib/surface-routes";
import {
  SurfaceView,
  QuizLanding,
  LearningPath,
  CompanyProfile,
  AuthorProfile,
  BookmarkButton,
  InquiryForm,
} from "./surfaces";

export type SiteSearch = {
  q?: string | undefined;
  difficulty?: string | undefined;
  topic?: string | undefined;
  company?: string | undefined;
  page?: number | undefined;
  tab?: string | undefined;
};
type ListItem = Awaited<
  ReturnType<typeof import("@/lib/cms.functions").listEntries>
>["items"][number];

const PAGE_SIZE = 12;

/* ---------- Path planning (shared by the route loader and the renderer) ---------- */
export type Plan =
  | {
      kind: "list";
      template:
        | "subjects"
        | "interview"
        | "explore"
        | "potd"
        | "courses"
        | "videos"
        | "events"
        | "jobs"
        | "category"
        | "search"
        | "quizzes"
        | "paths"
        | "companies"
        | "authors";
      input: ListInput;
      slug?: string | undefined;
    }
  | { kind: "entry"; path: string }
  | ScreenPlan;

export function planPath(rawPath: string, search: SiteSearch): Plan {
  const path = rawPath.replace(/^\/+|\/+$/g, "").toLowerCase();
  const page = Math.max(1, search.page ?? 1);
  const paging = { limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE };
  const q = search.q?.trim() || undefined;
  const screen = surfacePlan(path);
  if (screen) return screen;
  if (Object.hasOwn(DIRECTORY_PATHS, path))
    return {
      kind: "list",
      template: "subjects",
      input: { type: "subject", category: DIRECTORY_PATHS[path], q, ...paging },
    };
  const extraLists: Record<
    string,
    {
      template: "quizzes" | "paths" | "companies" | "authors";
      type: "quiz" | "path" | "company" | "author";
    }
  > = {
    quizzes: { template: "quizzes", type: "quiz" },
    "learning-paths": { template: "paths", type: "path" },
    companies: { template: "companies", type: "company" },
    authors: { template: "authors", type: "author" },
  };
  if (extraLists[path])
    return {
      kind: "list",
      template: extraLists[path].template,
      input: { type: extraLists[path].type, q, ...paging },
    };
  if (path === "interview-experiences/company-interview-corner")
    return {
      kind: "list",
      template: "interview",
      input: { type: "article", category: "Interview", q, ...paging },
    };
  if (path === "explore")
    return {
      kind: "list",
      template: "explore",
      input: {
        type: "problem",
        q,
        difficulty: search.difficulty,
        category: search.topic,
        company: search.company,
        ...paging,
      },
    };
  if (path === "problem-of-the-day")
    return { kind: "list", template: "potd", input: { type: "problem", potd: true, limit: 30 } };
  if (path === "search")
    return { kind: "list", template: "search", input: { q: q ?? "", ...paging } };
  const m = path.match(/^(courses|videos)(?:\/category\/([a-z0-9-]+))?$/);
  if (m)
    return {
      kind: "list",
      template: m[1] as "courses" | "videos",
      slug: m[2],
      input: { type: m[1] === "courses" ? "course" : "video", category: m[2], q, ...paging },
    };
  if (path === "events")
    return { kind: "list", template: "events", input: { type: "event", q, ...paging } };
  if (path === "jobs")
    return {
      kind: "list",
      template: "jobs",
      input: { type: "job", q, company: search.company, ...paging },
    };
  const c = path.match(/^category\/([a-z0-9-]+)$/);
  if (c)
    return {
      kind: "list",
      template: "category",
      slug: c[1],
      input: { type: "article", category: c[1], q, ...paging },
    };
  return { kind: "entry", path };
}

/* ---------- Shared primitives ---------- */
export function ELink({
  to,
  className,
  children,
  ...rest
}: {
  to: string;
  className?: string;
  children: ReactNode;
  style?: CSSProperties;
  "aria-label"?: string;
  "aria-current"?: "page" | "location" | undefined;
  onClick?: MouseEventHandler<HTMLAnchorElement> | undefined;
}) {
  if (!isPublicPath(to)) return null;
  const clean = to.replace(/^\/+/, "");
  if (!clean)
    return (
      <Link to="/" activeOptions={{ exact: true }} className={className} {...rest}>
        {children}
      </Link>
    );
  return (
    <Link
      to="/$"
      params={{ _splat: clean }}
      activeOptions={{ exact: true }}
      className={className}
      {...rest}
    >
      {children}
    </Link>
  );
}

function Container({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`mx-auto w-full max-w-[1240px] px-4 sm:px-6 ${className}`}>{children}</div>
  );
}

function Crumbs({ items }: { items: [string, string?][] }) {
  return (
    <nav aria-label="Breadcrumb" className="text-xs text-muted-foreground">
      <ol className="flex flex-wrap items-center gap-1">
        <li>
          <Link to="/" className="hover:text-primary">
            Home
          </Link>
        </li>
        {items.map(([label, href]) => (
          <li key={label} className="flex items-center gap-1">
            <ChevronRight className="size-3" aria-hidden />
            {href ? (
              <ELink to={href} className="hover:text-primary">
                {label}
              </ELink>
            ) : (
              <span aria-current="page" className="text-foreground">
                {label}
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}

function PageHeader({
  eyebrow,
  title,
  description,
  crumbs,
  children,
  tone = "hero",
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  crumbs?: [string, string?][];
  children?: ReactNode;
  tone?: "hero" | "course-hero" | "event-hero" | "business-hero";
}) {
  const bg = {
    hero: "bg-hero",
    "course-hero": "bg-course-hero",
    "event-hero": "bg-event-hero",
    "business-hero": "bg-business-hero",
  }[tone];
  return (
    <header className={`ozi-page-heading ${bg} border-b border-border`}>
      <Container className="py-8 md:py-12">
        {crumbs && <Crumbs items={crumbs} />}
        {eyebrow && (
          <p className="mt-4 text-xs font-bold uppercase tracking-wider text-primary">{eyebrow}</p>
        )}
        <h1 className="mt-2 max-w-3xl text-balance font-display text-3xl font-extrabold leading-tight md:text-4xl">
          {title}
        </h1>
        {description && (
          <p className="mt-3 max-w-2xl text-pretty text-muted-foreground md:text-lg">
            {description}
          </p>
        )}
        {children && <div className="mt-6">{children}</div>}
      </Container>
    </header>
  );
}

function SearchBar({
  placeholder,
  defaultValue = "",
}: {
  placeholder: string;
  defaultValue?: string | undefined;
}) {
  const navigate = useNavigate();
  const [value, setValue] = useState(defaultValue);
  return (
    <form
      role="search"
      className="flex max-w-xl gap-2"
      onSubmit={(e) => {
        e.preventDefault();
        navigate({
          to: ".",
          search: (prev: SiteSearch) => ({ ...prev, q: value || undefined, page: undefined }),
        });
      }}
    >
      <label className="relative flex-1">
        <span className="sr-only">{placeholder}</span>
        <Search
          className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
          aria-hidden
        />
        <Input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={placeholder}
          className="h-11 bg-background pl-9"
        />
      </label>
      <Button type="submit" className="h-11">
        Search
      </Button>
    </form>
  );
}

function Chips({
  options,
  active,
  param,
}: {
  options: { label: string; value?: string }[];
  active?: string;
  param: keyof SiteSearch;
}) {
  return (
    <div className="scrollbar-none -mx-1 flex gap-2 overflow-x-auto px-1 py-1" role="list">
      {options.map((o) => {
        const on = (o.value ?? "") === (active ?? "");
        return (
          <Link
            key={o.label}
            to="."
            search={(prev: SiteSearch) => ({ ...prev, [param]: o.value, page: undefined })}
            role="listitem"
            aria-current={on ? "true" : undefined}
            className={`shrink-0 rounded-full border px-4 py-1.5 text-sm font-semibold transition ${on ? "border-primary bg-primary text-primary-foreground" : "border-border bg-card hover:border-primary/50"}`}
          >
            {o.label}
          </Link>
        );
      })}
    </div>
  );
}

function Pager({ total, page }: { total: number; page: number }) {
  const pages = Math.ceil(total / PAGE_SIZE);
  if (pages <= 1) return null;
  return (
    <nav aria-label="Pagination" className="mt-10 flex items-center justify-center gap-2">
      <Button variant="outline" size="sm" asChild disabled={page <= 1}>
        <Link
          to="."
          search={(p: SiteSearch) => ({ ...p, page: page > 2 ? page - 1 : undefined })}
          aria-disabled={page <= 1}
          className={page <= 1 ? "pointer-events-none opacity-50" : ""}
        >
          <ChevronLeft className="size-4" />
          Previous
        </Link>
      </Button>
      <span className="px-3 text-sm text-muted-foreground">
        Page {page} of {pages}
      </span>
      <Button variant="outline" size="sm" asChild>
        <Link
          to="."
          search={(p: SiteSearch) => ({ ...p, page: page + 1 })}
          aria-disabled={page >= pages}
          className={page >= pages ? "pointer-events-none opacity-50" : ""}
        >
          Next
          <ChevronRight className="size-4" />
        </Link>
      </Button>
    </nav>
  );
}

export function EmptyState({
  title,
  text,
  action,
}: {
  title: string;
  text: string;
  action?: ReactNode;
}) {
  return (
    <div className="rounded-lg border border-dashed border-border bg-surface-subtle px-6 py-14 text-center">
      <p className="font-display text-lg font-bold">{title}</p>
      <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">{text}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function EntryCard({
  item,
  icon,
  meta,
}: {
  item: Pick<ListItem, "path" | "title" | "summary" | "category" | "featured">;
  icon?: ReactNode;
  meta?: ReactNode;
}) {
  return (
    <ELink
      to={item.path}
      className="catalog-entry-card group flex h-full flex-col rounded-lg border border-border bg-card p-5 shadow-card transition hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-card-hover focus-visible:outline-2 focus-visible:outline-ring"
    >
      <div className="flex items-center justify-between gap-2">
        {icon && (
          <span className="rounded-md bg-primary-soft p-2 text-primary [&_svg]:size-4">{icon}</span>
        )}
        {item.featured && <Badge variant="secondary">Featured</Badge>}
      </div>
      <h3 className="mt-4 font-display text-lg font-bold leading-snug group-hover:text-primary">
        {item.title}
      </h3>
      <p className="mt-2 line-clamp-3 flex-1 text-sm leading-6 text-muted-foreground">
        {item.summary}
      </p>
      {meta && (
        <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs font-semibold text-muted-foreground">
          {meta}
        </div>
      )}
    </ELink>
  );
}

function Grid({ children, cols = 3 }: { children: ReactNode; cols?: 3 | 4 }) {
  return (
    <div
      className={`grid gap-4 sm:grid-cols-2 ${cols === 4 ? "lg:grid-cols-4" : "lg:grid-cols-3"}`}
    >
      {children}
    </div>
  );
}

function headings(md: string) {
  if (/^\s*</.test(md))
    return Array.from(md.matchAll(/<h2\b[^>]*>([\s\S]*?)<\/h2>/gi), (m) =>
      m[1]!.replace(/<[^>]*>/g, "").trim(),
    );
  return md
    .split("\n")
    .filter((l) => /^##\s/.test(l))
    .map((l) => l.replace(/^##\s+/, "").trim());
}
const slugify = (s: string) =>
  s
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");

/* ---------- Resolver ---------- */
export function CmsView({
  plan,
  search,
  fallback,
}: {
  plan: Plan;
  search: SiteSearch;
  fallback: ReactNode;
}) {
  if (plan.kind === "screen") return <SurfaceView plan={plan} />;
  if (plan.kind === "list") return <ListView plan={plan} search={search} />;
  return <EntryView path={plan.path} search={search} fallback={fallback} />;
}

function EntryView({
  path,
  search,
  fallback,
}: {
  path: string;
  search: SiteSearch;
  fallback: ReactNode;
}) {
  const { data: entry } = useSuspenseQuery(entryQuery(path));
  if (!entry) return <>{fallback}</>;
  const d = obj(entry.data);
  switch (entry.type) {
    case "subject":
      return <SubjectHub entry={entry} d={d} />;
    case "article":
      return <ArticleDetail entry={entry} d={d} />;
    case "category":
      return (
        <CategoryArchive
          slug={entry.category ?? path.split("/").pop() ?? ""}
          header={entry}
          search={search}
        />
      );
    case "problem":
      return <ProblemDetail entry={entry} d={d} tab={search.tab} />;
    case "course":
      return <CourseDetail entry={entry} d={d} />;
    case "video":
      return <VideoDetail entry={entry} d={d} />;
    case "event":
      return <EventDetail entry={entry} d={d} />;
    case "job":
      return <JobDetail entry={entry} d={d} />;
    case "business":
      return <BusinessLanding entry={entry} d={d} />;
    case "page":
      return <StaticPage entry={entry} />;
    case "quiz":
      return <QuizLanding entry={entry} />;
    case "path":
      return <LearningPath entry={entry} tab={search.tab} />;
    case "company":
      return <CompanyProfile entry={entry} />;
    case "author":
      return <AuthorProfile entry={entry} />;
  }
}

function ListView({ plan, search }: { plan: Extract<Plan, { kind: "list" }>; search: SiteSearch }) {
  switch (plan.template) {
    case "subjects":
      return (
        <DirectoryPage
          plan={plan}
          title={
            plan.input.category === "AI & Data"
              ? "AI, machine learning & data science"
              : "Programming tutorials"
          }
          description="Choose a subject and follow its lessons."
          search={search}
        />
      );
    case "interview":
      return (
        <DirectoryPage
          plan={plan}
          title="Interview preparation"
          description="Questions, explanations and preparation resources."
          search={search}
        />
      );
    case "explore":
      return <ExplorePage plan={plan} search={search} />;
    case "potd":
      return <PotdPage plan={plan} />;
    case "courses":
      return <CourseListing plan={plan} search={search} />;
    case "videos":
      return <VideoListing plan={plan} search={search} />;
    case "events":
      return <EventListing plan={plan} search={search} />;
    case "jobs":
      return <JobListing plan={plan} search={search} />;
    case "category":
      return <CategoryArchive slug={plan.slug ?? ""} search={search} />;
    case "quizzes":
      return (
        <DirectoryPage
          plan={plan}
          title="Knowledge quizzes"
          description="Test your understanding and review explained answers."
          search={search}
        />
      );
    case "paths":
      return (
        <DirectoryPage
          plan={plan}
          title="Learning paths"
          description="Follow ordered lessons and practice resources."
          search={search}
        />
      );
    case "companies":
      return (
        <DirectoryPage
          plan={plan}
          title="Companies"
          description="Explore employer profiles and open roles."
          search={search}
        />
      );
    case "authors":
      return (
        <DirectoryPage
          plan={plan}
          title="Authors & contributors"
          description="Meet the people behind the learning resources."
          search={search}
        />
      );
    case "search":
      return <SearchResults plan={plan} search={search} />;
  }
}

function DirectoryPage({
  plan,
  title,
  description,
  search,
}: {
  plan: Extract<Plan, { kind: "list" }>;
  title: string;
  description: string;
  search: SiteSearch;
}) {
  const { data } = useSuspenseQuery(listQuery(plan.input));
  return (
    <>
      <PageHeader title={title} description={description} crumbs={[[title]]} />
      <Container className="py-10">
        <SearchBar placeholder={`Search ${title.toLowerCase()}`} defaultValue={search.q} />
        <div className="mt-8">
          {data.items.length ? (
            <Grid>
              {data.items.map((item) => (
                <EntryCard key={item.path} item={item} />
              ))}
            </Grid>
          ) : (
            <EmptyState
              title="No resources yet"
              text="Publish entries in WordPress to fill this directory."
            />
          )}
        </div>
        <Pager total={data.total} page={search.page ?? 1} />
      </Container>
    </>
  );
}

/* ---------- 2. Subject hub & 3. Article: three-column learning layout ---------- */
function CurriculumLinks({
  hub,
  lessons,
  current,
  onSelect,
  mobile = false,
}: {
  hub?: ListItem | undefined;
  lessons: ListItem[];
  current: string;
  onSelect?: (() => void) | undefined;
  mobile?: boolean;
}) {
  const byPath = new Map(lessons.map((lesson) => [lesson.path, lesson]));
  const modules = hub ? arr<{ title: string; lessons: string[] }>(obj(hub.data).modules) : [];
  const grouped = new Set(modules.flatMap((module) => module.lessons ?? []));
  const renderLink = (lesson: ListItem, index?: number) => (
    <ELink
      to={lesson.path}
      onClick={onSelect}
      aria-current={lesson.path === current ? "page" : undefined}
      className="curriculum-lesson"
    >
      {index !== undefined && (
        <span className="lesson-number">{String(index + 1).padStart(2, "0")}</span>
      )}
      <span>{lesson.title}</span>
      {lesson.path === current && <span className="sr-only">Current lesson</span>}
    </ELink>
  );
  return (
    <nav aria-label="Section lessons" className="curriculum-links">
      {hub && (
        <ELink
          to={hub.path}
          onClick={onSelect}
          aria-current={hub.path === current ? "page" : undefined}
          className="curriculum-overview"
        >
          Section overview
        </ELink>
      )}
      {modules.map((module, i) => (
        <details
          key={i}
          open={!mobile || i === 0}
          name={mobile ? "mobile-curriculum-modules" : undefined}
          className="curriculum-module"
        >
          <summary>
            {module.title}
            <span>{module.lessons.length}</span>
          </summary>
          <ul>
            {module.lessons.map((path, index) => {
              const lesson = byPath.get(path);
              return lesson ? <li key={path}>{renderLink(lesson, index)}</li> : null;
            })}
          </ul>
        </details>
      ))}
      <ul>
        {lessons
          .filter((lesson) => !grouped.has(lesson.path))
          .map((lesson) => (
            <li key={lesson.path}>{renderLink(lesson)}</li>
          ))}
      </ul>
      {!lessons.length && (
        <p className="py-2 text-sm text-muted-foreground">No lessons published yet.</p>
      )}
    </nav>
  );
}

function useSectionLessons(entry: Entry) {
  const sectionPath = str(obj(entry.data).section_path, entry.path);
  const { data: section } = useSuspenseQuery(entryQuery(sectionPath));
  const paths = [
    ...new Set(
      arr<{ lessons?: string[] }>(obj(section?.data).modules).flatMap(
        (module) => module.lessons ?? [],
      ),
    ),
  ];
  const batches: ListInput[] = [];
  for (let start = 0; start < paths.length; start += 100) {
    const batch = paths.slice(start, start + 100);
    batches.push({ paths: batch, limit: batch.length });
  }
  const results = useSuspenseQueries({
    queries: (batches.length
      ? batches
      : [{ subject: entry.subject ?? "__none__", limit: 100 }]
    ).map(listQuery),
  });
  const items = results.flatMap(({ data }) => data.items);
  const lessons = items.filter((item) => item.type === "article" || item.type === "quiz");
  if ((entry.type === "article" || entry.type === "quiz") && !lessons.some((item) => item.path === entry.path)) {
    lessons.push(entry);
  }
  return { hub: section?.type === "subject" ? section : undefined, lessons };
}

function LessonRail({ entry }: { entry: Entry }) {
  const { hub, lessons } = useSectionLessons(entry);
  return (
    <aside
      aria-label="Curriculum"
      className="learning-sidebar hidden border-r bg-surface-subtle lg:block"
    >
      <p className="curriculum-heading">{hub?.title ?? "Curriculum"}</p>
      <CurriculumLinks
        hub={hub}
        lessons={lessons}
        current={entry.path}
      />
    </aside>
  );
}

function headingAnchor(heading: string) {
  if (heading === "See the links change") return "linked-list-demo";
  if (heading === "Reverse one link at a time") return "linked-list-reversal";
  if (heading === "Java, mapped out") return "java-diagrams";
  return slugify(heading);
}

function pageContents(entry: Entry) {
  const toc = headings(entry.body);
  if (entry.path === "java/java") toc.push("Java, mapped out");
  if (entry.type === "subject" && obj(entry.data).modules) toc.push("Curriculum");
  if (obj(entry.data).visual_demo === "linked-list")
    toc.unshift("See the links change", "Reverse one link at a time");
  return toc;
}

function useActiveHeading(path: string) {
  const [active, setActive] = useState("");
  useEffect(() => {
    const nodes = [...document.querySelectorAll<HTMLElement>(".learning-shell article h2[id]")];
    const update = () => {
      const offset =
        document.querySelector("[data-subject-tabs]")?.getBoundingClientRect().bottom ?? 160;
      const passed = nodes.filter((node) => node.getBoundingClientRect().top <= offset + 40);
      setActive((passed.at(-1) ?? nodes[0])?.id ?? "");
    };
    update();
    window.addEventListener("scroll", update, { passive: true });
    return () => window.removeEventListener("scroll", update);
  }, [path]);
  return active;
}

function MobileContents({ entry }: { entry: Entry }) {
  const { hub, lessons } = useSectionLessons(entry);
  const toc = pageContents(entry);
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState("lessons");
  const active = useActiveHeading(entry.path);
  const pendingHeading = useRef<string | null>(null);
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <button className="mobile-contents-trigger lg:hidden" type="button">
          <span aria-hidden="true">☷</span> Contents · {lessons.length}
        </button>
      </SheetTrigger>
      <SheetContent
        side="bottom"
        className="mobile-contents-sheet"
        onCloseAutoFocus={(event) => {
          const id = pendingHeading.current;
          pendingHeading.current = null;
          if (!id) return;
          event.preventDefault();
          // Finish the jump after the sheet releases its scroll lock.
          requestAnimationFrame(() => {
            const heading = document.getElementById(id);
            heading?.setAttribute("tabindex", "-1");
            heading?.focus({ preventScroll: true });
            heading?.scrollIntoView({ block: "start", behavior: "instant" });
          });
        }}
      >
        <SheetTitle>Contents</SheetTitle>
        <SheetDescription>{hub?.title ?? entry.title}</SheetDescription>
        <div className="my-4 flex gap-2" role="group" aria-label="Contents view">
          <button
            type="button"
            aria-pressed={tab === "lessons"}
            className="contents-view"
            onClick={() => setTab("lessons")}
          >
            Lessons · {lessons.length}
          </button>
          <button
            type="button"
            aria-pressed={tab === "page"}
            className="contents-view"
            onClick={() => setTab("page")}
          >
            On this page · {toc.length}
          </button>
        </div>
        <div className="contents-scroll">
          {tab === "lessons" ? (
            <CurriculumLinks
              hub={hub}
              lessons={lessons}
              current={entry.path}
              onSelect={() => setOpen(false)}
              mobile
            />
          ) : (
            <nav aria-label="Page contents">
              <ul>
                {toc.map((heading, index) => (
                  <li key={heading}>
                    <a
                      className="curriculum-lesson"
                      href={`#${headingAnchor(heading)}`}
                      aria-current={active === headingAnchor(heading) ? "location" : undefined}
                      onClick={() => {
                        pendingHeading.current = headingAnchor(heading);
                        setOpen(false);
                      }}
                    >
                      <span className="lesson-number">{String(index + 1).padStart(2, "0")}</span>
                      <span>{heading}</span>
                    </a>
                  </li>
                ))}
              </ul>
            </nav>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

function RightRail({ entry }: { entry: Entry }) {
  const toc = pageContents(entry);
  const active = useActiveHeading(entry.path);
  const { data } = useSuspenseQuery(listQuery({ type: "course", featured: true, limit: 2 }));
  return (
    <aside aria-label="On this page" className="hidden xl:block">
      <div className="sticky top-[92px] grid gap-6 p-5">
        {toc.length > 0 && (
          <nav>
            <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
              On this page
            </p>
            <ul className="mt-3 grid gap-2 border-l border-border">
              {toc.map((h) => (
                <li key={h}>
                  <a
                    href={`#${headingAnchor(h)}`}
                    aria-current={active === headingAnchor(h) ? "location" : undefined}
                    className="-ml-px block border-l-2 border-transparent pl-3 text-sm text-muted-foreground hover:border-primary hover:text-foreground"
                  >
                    {h}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        )}
        {data.items.map((c) => (
          <ELink
            key={c.path}
            to={c.path}
            className="rounded-lg border border-border bg-course-hero p-4 hover:border-primary/40"
          >
            <p className="text-xs font-bold text-primary">Recommended course</p>
            <p className="mt-1 font-display font-bold leading-snug">{c.title}</p>
            <span className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-primary">
              Explore <ArrowRight className="size-3" />
            </span>
          </ELink>
        ))}
      </div>
    </aside>
  );
}

type SubjectTab = { title: string; path: string };
function SubjectResources({ entry }: { entry: Entry }) {
  const rootPath = str(obj(entry.data).subject_root, entry.path);
  const { data: root } = useSuspenseQuery(entryQuery(rootPath));
  const tabs = arr<SubjectTab>(obj(root?.data ?? entry.data).resource_tabs).filter(
    (t) => t.title && isPublicPath(t.path),
  );
  const activePath = str(obj(entry.data).section_path, entry.path);
  useEffect(() => {
    const bar = document.querySelector<HTMLElement>("[data-subject-tabs]");
    const active = bar?.querySelector<HTMLElement>("[aria-current=page]");
    if (bar && active) {
      const offset = active.getBoundingClientRect().left - bar.getBoundingClientRect().left;
      bar.scrollLeft += offset - (bar.clientWidth - active.clientWidth) / 2;
    }
  }, [activePath]);
  if (!tabs.length)
    return (
      <nav aria-label="Subject resources" className="subject-resource-bar">
        <ELink to="explore">Practice</ELink>
        <ELink to="quizzes">Quizzes</ELink>
        <ELink to="learning-paths">Learning paths</ELink>
        <ELink to="videos">Videos</ELink>
      </nav>
    );
  return (
    <nav aria-label="Subject resources" data-subject-tabs className="subject-resource-bar">
      {tabs.map((tab) => (
        <ELink
          key={tab.path}
          to={tab.path}
          aria-current={tab.path === activePath ? "page" : undefined}
        >
          {tab.title}
        </ELink>
      ))}
    </nav>
  );
}
export function LearningLayout({ entry, children }: { entry: Entry; children: ReactNode }) {
  const [readingFocus, setReadingFocus] = useState(false);
  const [largeText, setLargeText] = useState(false);
  return (
    <div
      className="learning-shell mx-auto max-w-[1440px]"
      data-reading-focus={readingFocus ? "true" : undefined}
      data-reading-size={largeText ? "large" : "standard"}
    >
      <SubjectResources entry={entry} />
      <MobileContents entry={entry} />
      <div className="learning-grid grid grid-cols-1 lg:grid-cols-[260px_minmax(0,1fr)] xl:grid-cols-[260px_minmax(0,1fr)_280px]">
        <LessonRail entry={entry} />
        <article className="min-w-0 px-4 py-8 sm:px-8 lg:px-12">
          {(entry.type === "article" || entry.type === "quiz") && (
            <div className="reading-controls" role="group" aria-label="Reading preferences">
              <span>Make this comfortable</span>
              <div>
                <button
                  type="button"
                  aria-pressed={largeText}
                  onClick={() => setLargeText(!largeText)}
                >
                  {largeText ? (
                    <Check className="size-4" aria-hidden="true" />
                  ) : (
                    <span aria-hidden="true">Aa</span>
                  )}{" "}
                  Larger text
                </button>
                <button
                  type="button"
                  aria-pressed={readingFocus}
                  onClick={() => setReadingFocus(!readingFocus)}
                >
                  {readingFocus ? (
                    <Check className="size-4" aria-hidden="true" />
                  ) : (
                    <BookOpen className="size-4" aria-hidden="true" />
                  )}{" "}
                  Focus reading
                </button>
              </div>
            </div>
          )}
          {headings(entry.body).length > 0 && (
            <details className="mb-6 hidden rounded-md border px-4 py-3 lg:block xl:hidden">
              <summary className="cursor-pointer text-sm font-semibold">On this page</summary>
              <nav className="mt-3 grid gap-2">
                {headings(entry.body).map((h) => (
                  <a
                    key={h}
                    href={`#${headingAnchor(h)}`}
                    className="text-sm text-muted-foreground hover:text-primary"
                  >
                    {h}
                  </a>
                ))}
              </nav>
            </details>
          )}
          {children}
          {(entry.type === "article" || entry.type === "quiz") && (
            <LessonNavigation entry={entry} />
          )}
          <ContinueSections entry={entry} />
        </article>
        <RightRail entry={entry} />
      </div>
    </div>
  );
}
function ContinueSections({ entry }: { entry: Entry }) {
  const { data: root } = useSuspenseQuery(
    entryQuery(str(obj(entry.data).subject_root, entry.path)),
  );
  const tabs = arr<SubjectTab>(obj(root?.data ?? entry.data).resource_tabs);
  const active = str(obj(entry.data).section_path, entry.path);
  const next = tabs[tabs.findIndex((t) => t.path === active) + 1];
  if (!tabs.length) return null;
  return (
    <nav aria-label="Continue exploring this subject" className="mt-10 border-t pt-6">
      {next && (
        <ELink to={next.path} className="section-next-link">
          <span className="text-xs text-muted-foreground">Continue to the next section</span>
          <strong className="mt-1 flex items-center justify-between gap-3">
            {next.title}
            <ArrowRight className="size-5" aria-hidden="true" />
          </strong>
        </ELink>
      )}
      <h2 className="mt-6 font-bold">Explore this subject</h2>
      <ul className="mt-3 flex flex-wrap gap-x-5 gap-y-3">
        {tabs
          .filter((t) => t.path !== active)
          .map((t) => (
            <li key={t.path}>
              <ELink to={t.path} className="text-sm text-primary underline">
                {t.title}
              </ELink>
            </li>
          ))}
      </ul>
    </nav>
  );
}

function MarkdownWithAnchors({ body }: { body: string }) {
  // Headings get stable ids for the "On this page" rail.
  const withIds = body.replace(/^##\s+(.+)$/gm, (_, h: string) => `## ${h}`);
  return (
    <div className="[&_h2]:scroll-mt-28">
      <Markdown source={withIds} />
    </div>
  );
}

function SubjectHub({ entry, d }: { entry: Entry; d: EntryData }) {
  const modules = arr<{ title?: string; summary?: string; lessons?: string[] }>(d.modules);
  const openingParagraph = entry.body.match(/^\s*<p>([\s\S]*?)<\/p>/)?.[1]?.trim();
  const showSummary = entry.summary && openingParagraph !== entry.summary.trim();
  const paths = [...new Set(modules.flatMap((m) => m.lessons ?? []))];
  const batches = [];
  for (let start = 0; start < paths.length; start += 100) {
    batches.push(paths.slice(start, start + 100));
  }
  const results = useSuspenseQueries({
    queries: (batches.length ? batches : [["__none__"]]).map((batch) =>
      listQuery({ paths: batch, limit: batch.length }),
    ),
  });
  const byPath = new Map(
    results.flatMap(({ data }) => data.items.map((item) => [item.path, item] as const)),
  );
  return (
    <LearningLayout entry={entry}>
      <Crumbs items={[[entry.category ?? "Tutorials"], [entry.title]]} />
      <h1 className="mt-4 text-balance font-display text-3xl font-extrabold [overflow-wrap:anywhere] md:text-4xl">
        {entry.title}
      </h1>
      {showSummary && <p className="mt-3 text-lg text-muted-foreground">{entry.summary}</p>}
      <div className="mt-6">
        <HeadingIds>
          <Markdown source={entry.body} />
        </HeadingIds>
      </div>
      {entry.path === "java/java" && <JavaConceptGallery />}
      {modules.length > 0 && (
        <section className="mt-10" aria-labelledby="curriculum">
          <h2 id="curriculum" className="font-display text-2xl font-bold">
            Curriculum
          </h2>
          <Accordion
            type="multiple"
            defaultValue={d.content_format === "html" ? modules.map((_, i) => String(i)) : ["0"]}
            className="curriculum-roadmap mt-4 rounded-lg border border-border"
          >
            {modules.map((m, i) => (
              <AccordionItem key={i} value={String(i)} className="px-4 last:border-b-0">
                <AccordionTrigger className="font-display text-base font-bold">
                  {m.title ?? `Module ${i + 1}`}
                  <span className="ml-auto mr-3 text-xs font-normal text-muted-foreground">
                    {m.lessons?.length ?? 0} lessons
                  </span>
                </AccordionTrigger>
                <AccordionContent>
                  {m.summary && <p className="mb-3 text-sm text-muted-foreground">{m.summary}</p>}
                  <ol className="grid gap-1">
                    {(m.lessons ?? []).map((p, j) => {
                      const l = byPath.get(p);
                      return (
                        <li key={p}>
                          {l ? (
                            <ELink
                              to={p}
                              className="roadmap-lesson flex items-center gap-3 rounded-md px-2 py-2.5 text-sm hover:bg-accent"
                            >
                              <span className="grid size-6 place-items-center rounded-full bg-primary-soft text-xs font-bold text-primary">
                                {j + 1}
                              </span>
                              {l.title}
                            </ELink>
                          ) : (
                            <span className="flex items-center gap-3 px-2 py-2.5 text-sm text-muted-foreground">
                              <span className="grid size-6 place-items-center rounded-full border text-xs">
                                {j + 1}
                              </span>
                              {p} · coming soon
                            </span>
                          )}
                        </li>
                      );
                    })}
                  </ol>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </section>
      )}
    </LearningLayout>
  );
}

/** Adds ids to rendered h2 elements so in-page anchors work. */
function HeadingIds({ children }: { children: ReactNode }) {
  return (
    <div
      ref={(el) => {
        el?.querySelectorAll("h2").forEach((h) => {
          if (!h.id) h.id = slugify(h.textContent ?? "");
        });
        el?.querySelectorAll("h3").forEach((h) => {
          if (/common mistakes|edge cases/i.test(h.textContent ?? ""))
            h.classList.add("tutorial-caution-heading");
        });
      }}
    >
      {children}
    </div>
  );
}

function ArticleDetail({ entry, d }: { entry: Entry; d: EntryData }) {
  const relatedLessons = arr<string | { title?: string; path?: string }>(d.related)
    .map((related) => {
      if (typeof related !== "string" && (!related || typeof related !== "object"))
        return null;
      const path = typeof related === "string" ? related : related.path;
      if (!path || !isPublicPath(path)) return null;
      const title = typeof related === "string" ? undefined : related.title;
      return {
        path,
        title: title || path.split("/").at(-1)!.replace(/-/g, " "),
      };
    })
    .filter((related): related is { path: string; title: string } => related !== null);
  const introduction =
    d.content_format === "html" ? entry.body.match(/^<p>[\s\S]*?<\/p>/)?.[0] : undefined;
  const body = introduction ? entry.body.slice(introduction.length) : entry.body;
  const { data: subjectRoot } = useSuspenseQuery(entryQuery(str(d.subject_root, entry.path)));
  const sectionPath = str(d.section_path);
  const sectionTitle =
    arr<SubjectTab>(obj(subjectRoot?.data).resource_tabs).find((tab) => tab.path === sectionPath)
      ?.title ?? "Articles";
  const kit = /^\/downloads\/(?:aitrove|dekhoexams)-(java|spring|python)-source-kit\.zip$/.exec(str(d["download_path"]))?.[1] as "java" | "spring" | "python" | undefined;
  const updated = new Date(entry.updated_at).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "Asia/Kolkata",
  });
  return (
    <LearningLayout entry={entry}>
      <Crumbs items={[sectionPath ? [sectionTitle, sectionPath] : [sectionTitle], [entry.title]]} />
      <h1 className="mt-4 text-balance font-display text-3xl font-extrabold [overflow-wrap:anywhere] md:text-4xl">
        {entry.title}
      </h1>
      <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
        <span>Last updated: {updated}</span>
        {str(d.reading_minutes) && (
          <span className="inline-flex items-center gap-1">
            <Clock className="size-3" />
            {str(d.reading_minutes)} min read
          </span>
        )}
        {str(d.kind) && (
          <Badge variant="outline" className="capitalize">
            {str(d.kind)}
          </Badge>
        )}
        {entry.difficulty && <DifficultyBadge value={entry.difficulty} />}
        <BookmarkButton entry={entry} />
      </div>
      {introduction ? (
        <div className="mt-5 text-lg text-muted-foreground">
          <Markdown source={introduction} />
        </div>
      ) : entry.summary ? (
        <p className="mt-5 text-lg text-muted-foreground">{entry.summary}</p>
      ) : null}
      {kit && (
        <a href={"/downloads/dekhoexams-" + kit + "-source-kit.zip"} download
          className="mt-5 inline-flex min-h-11 items-center rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary">
          Download {{ java: "Java", spring: "Spring", python: "Python" }[kit]} source kit
        </a>
      )}
      {d.visual_demo === "linked-list" && <LinkedListDemo />}
      {d.visual_demo === "linked-list" && <LinkedListReversal />}
      <div className="mt-4">
        <HeadingIds>
          <MarkdownWithAnchors body={body} />
        </HeadingIds>
      </div>
      {relatedLessons.length > 0 && (
        <nav aria-label="Related lessons" className="mt-8 border-t pt-5">
          <h2 className="font-display text-lg font-bold">Keep working</h2>
          <ul className="mt-3 space-y-2">
            {relatedLessons.map((link) => (
              <li key={link.path}>
                <ELink to={link.path} className="text-primary underline">
                  {link.title}
                </ELink>
              </li>
            ))}
          </ul>
        </nav>
      )}
      {entry.tags.length > 0 && (
        <div className="mt-8 flex flex-wrap gap-2">
          {entry.tags.map((t) => (
            <Badge key={t} variant="secondary">
              {t}
            </Badge>
          ))}
        </div>
      )}
    </LearningLayout>
  );
}

function LessonNavigation({ entry }: { entry: Entry }) {
  const { data: section } = useSuspenseQuery(
    entryQuery(str(obj(entry.data).section_path, entry.path)),
  );
  const paths = [
    ...new Set(
      arr<{ lessons?: string[] }>(obj(section?.data).modules).flatMap(
        (module) => module.lessons ?? [],
      ),
    ),
  ];
  const sectionIndex = paths.indexOf(entry.path);
  const adjacentPaths = [paths[sectionIndex - 1], paths[sectionIndex + 1]].filter(
    (path): path is string => !!path,
  );
  const useSectionOrder = sectionIndex >= 0;
  const { data } = useSuspenseQuery(
    listQuery(
      useSectionOrder
        ? {
            paths: adjacentPaths.length ? adjacentPaths : ["__none__"],
            limit: Math.max(1, adjacentPaths.length),
          }
        : { subject: entry.subject ?? "__none__", limit: 100 },
    ),
  );
  const byPath = new Map(data.items.map((item) => [item.path, item]));
  const lessons = data.items.filter(
    (item): item is NonNullable<typeof item> =>
      !!item && (item.type === "article" || item.type === "quiz"),
  );
  const index = lessons.findIndex((item) => item.path === entry.path);
  const prev = useSectionOrder
    ? byPath.get(paths[sectionIndex - 1] ?? "")
    : index > 0
      ? lessons[index - 1]
      : undefined;
  const next = useSectionOrder
    ? byPath.get(paths[sectionIndex + 1] ?? "")
    : index >= 0
      ? lessons[index + 1]
      : undefined;
  if (!prev && !next) return null;
  return (
    <nav
      aria-label="Lesson navigation"
      className="lesson-navigation mt-10 grid gap-3 border-t border-border pt-6 sm:grid-cols-2"
    >
      {prev ? (
        <ELink to={prev.path} className="lesson-step lesson-step-previous">
          <span className="lesson-step-direction">
            <ChevronLeft className="size-5" aria-hidden="true" />
            Previous lesson
          </span>
          <strong className="lesson-step-title">{prev.title}</strong>
        </ELink>
      ) : (
        <span />
      )}
      {next && (
        <ELink to={next.path} className="lesson-step lesson-step-next">
          <span className="lesson-step-direction">
            Next lesson
            <ChevronRight className="size-5" aria-hidden="true" />
          </span>
          <strong className="lesson-step-title">{next.title}</strong>
        </ELink>
      )}
    </nav>
  );
}

/* ---------- 4. Category / archive ---------- */
function CategoryArchive({
  slug,
  header,
  search,
}: {
  slug: string;
  header?: Entry;
  search: SiteSearch;
}) {
  const page = search.page ?? 1;
  const { data: head } = useSuspenseQuery(entryQuery(`category/${slug}`));
  const meta = header ?? head;
  const { data } = useSuspenseQuery(
    listQuery({
      type: "article",
      category: slug,
      q: search.q,
      limit: PAGE_SIZE,
      offset: (page - 1) * PAGE_SIZE,
    }),
  );
  const title = meta?.title ?? slug.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  return (
    <>
      <PageHeader
        crumbs={[["Category"], [title]]}
        eyebrow="Archive"
        title={title}
        description={meta?.summary || `All articles filed under ${title}.`}
      >
        <SearchBar placeholder={`Search in ${title}`} defaultValue={search.q} />
      </PageHeader>
      <Container className="py-10">
        <p className="mb-5 text-sm text-muted-foreground">
          {data.total} article{data.total === 1 ? "" : "s"}
        </p>
        {data.items.length ? (
          <div className="grid gap-4">
            {data.items.map((a) => (
              <ELink
                key={a.path}
                to={a.path}
                className="group grid gap-1 rounded-lg border border-border bg-card p-5 hover:border-primary/40 sm:grid-cols-[1fr_auto] sm:items-center"
              >
                <div>
                  <h2 className="font-display text-lg font-bold group-hover:text-primary">
                    {a.title}
                  </h2>
                  <p className="mt-1 text-sm text-muted-foreground">{a.summary}</p>
                </div>
                <span className="text-xs text-muted-foreground">
                  {a.published_at
                    ? new Date(a.published_at).toLocaleDateString("en-IN", {
                        day: "numeric",
                        month: "short",
                        year: "numeric",
                        timeZone: "Asia/Kolkata",
                      })
                    : ""}
                </span>
              </ELink>
            ))}
          </div>
        ) : (
          <EmptyState
            title="No articles yet"
            text="Articles added to this category in the admin will appear here."
          />
        )}
        <Pager total={data.total} page={page} />
      </Container>
    </>
  );
}

/* ---------- 5. Practice listing ---------- */
function ExplorePage({
  plan,
  search,
}: {
  plan: Extract<Plan, { kind: "list" }>;
  search: SiteSearch;
}) {
  const { data } = useSuspenseQuery(listQuery(plan.input));
  const { data: options } = useSuspenseQuery(listQuery({ type: "problem", limit: 100 }));
  const topics = useMemo(
    () => [...new Set(options.items.map((p) => p.category).filter(Boolean) as string[])].sort(),
    [options.items],
  );
  const companies = useMemo(
    () => [...new Set(options.items.flatMap((p) => arr<string>(obj(p.data).companies)))].sort(),
    [options.items],
  );
  const rows = data.items;
  const navigate = useNavigate();
  const setFilter = (key: keyof SiteSearch, value: string) =>
    navigate({
      to: ".",
      search: (p: SiteSearch) => ({ ...p, [key]: value || undefined, page: undefined }),
    });
  return (
    <>
      <PageHeader
        crumbs={[["Practice"]]}
        eyebrow="Practice"
        title="Explore problems"
        description="Sharpen your skills with curated problems, filtered by topic, company and difficulty."
      >
        <SearchBar placeholder="Search problems" defaultValue={search.q} />
      </PageHeader>
      <Container className="grid gap-8 py-8 lg:grid-cols-[250px_minmax(0,1fr)]">
        <aside aria-label="Filters" className="grid content-start gap-5">
          <DifficultyFilter
            value={search.difficulty}
            onChange={(v) => setFilter("difficulty", v)}
          />
          <FilterSelect
            label="Topic"
            value={search.topic}
            options={topics}
            onChange={(v) => setFilter("topic", v)}
          />
          <FilterSelect
            label="Company"
            value={search.company}
            options={companies}
            onChange={(v) => setFilter("company", v)}
          />
          {(search.difficulty || search.topic || search.company || search.q) && (
            <Button variant="outline" asChild>
              <Link to="." search={{}}>
                Clear filters
              </Link>
            </Button>
          )}
          <ELink
            to="/problem-of-the-day"
            className="rounded-lg border border-border bg-event-hero p-4"
          >
            <Flame className="size-5 text-primary" />
            <p className="mt-2 font-display font-bold">Problem of the Day</p>
            <p className="text-xs text-muted-foreground">Solve daily to keep your streak.</p>
          </ELink>
        </aside>
        <div className="min-w-0">
          <p className="mb-3 text-sm text-muted-foreground" aria-live="polite">
            {data.total} problem{data.total === 1 ? "" : "s"}
          </p>
          {rows.length ? (
            <div className="discovery-problem-grid">
              {rows.map((problem, index) => (
                <div className="catalog-problem-card" key={problem.path}>
                  <ELink
                    to={problem.path}
                    className={`catalog-problem-art tone-${["mint", "lilac", "sky", "peach", "butter"][index % 5]}`}
                    aria-label={problem.title}
                  >
                    <TopicMark path={problem.path} />
                    <span>{problem.category}</span>
                  </ELink>
                  <div className="catalog-problem-copy">
                    <div className="flex items-center justify-between gap-2">
                      <DifficultyBadge value={problem.difficulty} />
                      <BookmarkButton entry={problem} />
                    </div>
                    <ELink to={problem.path}>
                      <h2>{problem.title}</h2>
                    </ELink>
                    <p>{problem.summary}</p>
                    <ELink to={problem.path} className="tool-open">
                      Open problem ↗
                    </ELink>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No problems match"
              text="Try removing a filter or searching a different term."
            />
          )}
          <Pager total={data.total} page={search.page ?? 1} />
        </div>
      </Container>
    </>
  );
}

function FilterSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value?: string | undefined;
  options: string[];
  onChange: (v: string) => void;
}) {
  const id = `f-${label}`;
  return (
    <div>
      <label
        htmlFor={id}
        className="text-xs font-bold uppercase tracking-wider text-muted-foreground"
      >
        {label}
      </label>
      <select
        id={id}
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
        className="mt-2 h-10 w-full rounded-md border border-input bg-background px-3 text-sm focus-visible:outline-2 focus-visible:outline-ring"
      >
        <option value="">All</option>
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </div>
  );
}

/* ---------- 6. Problem detail / editor ---------- */
function ProblemDetail({
  entry,
  d,
  tab,
}: {
  entry: Entry;
  d: EntryData;
  tab?: string | undefined;
}) {
  const [code, setCode] = useState(str(d.starter_code, "# write your solution here\n"));
  const [lang, setLang] = useState("Python 3");
  const [output, setOutput] = useState<string | null>(null);
  const companies = arr<string>(d.companies);
  return (
    <div className="bg-workspace">
      <div className="mx-auto grid max-w-[1600px] gap-3 p-3 lg:h-[calc(100dvh-92px)] lg:grid-cols-2">
        <section className="flex min-h-0 flex-col overflow-hidden rounded-lg border border-border bg-card">
          <Tabs defaultValue={tab ?? "problem"} className="flex min-h-0 flex-1 flex-col">
            <TabsList className="m-2 w-fit">
              <TabsTrigger value="problem">Problem</TabsTrigger>
              <TabsTrigger value="editorial">Editorial</TabsTrigger>
              <TabsTrigger value="submissions">Submissions</TabsTrigger>
              <TabsTrigger value="comments">Comments</TabsTrigger>
              <TabsTrigger value="hints">Hints</TabsTrigger>
            </TabsList>
            <TabsContent value="problem" className="min-h-0 flex-1 overflow-y-auto px-5 pb-6">
              <Crumbs items={[["Practice", "/explore"], [entry.title]]} />
              <h1 className="mt-3 font-display text-2xl font-extrabold">{entry.title}</h1>
              <div className="mt-2 flex flex-wrap gap-3 text-xs">
                <DifficultyBadge value={entry.difficulty} />
                {str(d.accuracy) && (
                  <span className="text-muted-foreground">Accuracy {str(d.accuracy)}</span>
                )}
                {str(d.submissions) && (
                  <span className="text-muted-foreground">Submissions {str(d.submissions)}</span>
                )}
                {str(d.points) && (
                  <span className="text-muted-foreground">Points {str(d.points)}</span>
                )}
              </div>
              <div className="mt-4">
                <Markdown source={entry.body} />
              </div>
              {companies.length > 0 && (
                <div className="mt-6">
                  <p className="text-xs font-bold uppercase text-muted-foreground">Asked in</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {companies.map((c) => (
                      <Badge key={c} variant="secondary">
                        {c}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              {entry.tags.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2">
                  {entry.tags.map((t) => (
                    <Badge key={t} variant="outline">
                      {t}
                    </Badge>
                  ))}
                </div>
              )}
            </TabsContent>
            <TabsContent value="editorial" className="min-h-0 flex-1 overflow-y-auto px-5 pb-6">
              {str(d.editorial) ? (
                <Markdown source={str(d.editorial)} />
              ) : (
                <EmptyState
                  title="Editorial coming soon"
                  text="An explanation will be published here."
                />
              )}
            </TabsContent>
            <TabsContent value="comments" className="px-5 pb-6">
              <EmptyState
                title="No discussion yet"
                text="Discussion and moderation will be enabled with learner services."
              />
              <Button className="mt-4" variant="outline" asChild>
                <ELink to="login">Learner sign-in</ELink>
              </Button>
            </TabsContent>
            <TabsContent value="hints" className="px-5 pb-6">
              <h2 className="font-bold">Hints</h2>
              <p className="mt-3 text-sm text-muted-foreground">
                Start by identifying the input constraints and testing a small example. Review the
                editorial for a complete approach.
              </p>
            </TabsContent>
            <TabsContent value="submissions" className="px-5 pb-6">
              <EmptyState
                title="Sign in to see submissions"
                text="Your submission history will appear here once online judging is available."
              />
            </TabsContent>
          </Tabs>
        </section>
        <section className="flex min-h-[520px] flex-col overflow-hidden rounded-lg border border-editor-border bg-editor text-editor-foreground">
          <div className="flex items-center justify-between gap-2 border-b border-editor-border bg-editor-panel px-3 py-2">
            <label className="sr-only" htmlFor="lang">
              Language
            </label>
            <select
              id="lang"
              value={lang}
              onChange={(e) => setLang(e.target.value)}
              className="h-8 rounded border border-editor-border bg-editor px-2 text-sm"
            >
              {["Python 3", "C++", "Java", "JavaScript"].map((l) => (
                <option key={l}>{l}</option>
              ))}
            </select>
            <span className="text-xs text-editor-muted">Autosave off · demo editor</span>
          </div>
          <label className="sr-only" htmlFor="code">
            Code editor
          </label>
          <Textarea
            id="code"
            spellCheck={false}
            value={code}
            onChange={(e) => setCode(e.target.value)}
            className="min-h-0 flex-1 resize-none rounded-none border-0 bg-editor font-mono text-sm leading-6 text-editor-foreground focus-visible:ring-0"
          />
          <div className="border-t border-editor-border bg-editor-panel p-3">
            <label className="grid gap-2 text-xs text-editor-muted">
              Custom input
              <Textarea
                rows={2}
                placeholder="Enter test input"
                className="border-editor-border bg-editor text-editor-foreground"
              />
            </label>
            {output && (
              <p
                role="status"
                className="mb-3 rounded border border-warning-border bg-warning/10 p-3 text-sm"
              >
                {output}
              </p>
            )}
            <div className="flex justify-end gap-2">
              <Button
                variant="secondary"
                onClick={() =>
                  setOutput("Code execution is not connected yet. Your code was not run.")
                }
              >
                <Play className="size-4" />
                Run
              </Button>
              <Button
                onClick={() =>
                  setOutput(
                    "Submissions are not judged yet — online judging will be added in a later phase.",
                  )
                }
              >
                Submit
              </Button>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

/* ---------- 7. Problem of the day ---------- */
function PotdPage({ plan }: { plan: Extract<Plan, { kind: "list" }> }) {
  const { data } = useSuspenseQuery(listQuery(plan.input));
  const today = new Date().toISOString().slice(0, 10);
  const items = data.items.filter((p) => (p.potd_date ?? "") <= today);
  const [current, ...archive] = items;
  return (
    <>
      <PageHeader
        tone="event-hero"
        crumbs={[["Practice", "/explore"], ["Problem of the Day"]]}
        eyebrow="Daily challenge"
        title="Problem of the Day"
        description="One hand-picked problem every day. Build consistency and keep your streak alive."
      />
      <Container className="grid gap-8 py-10 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div>
          {current ? (
            <div className="rounded-xl border border-border bg-card p-6 shadow-card">
              <p className="inline-flex items-center gap-2 text-sm font-semibold text-primary">
                <Flame className="size-4" />
                Today · {current.potd_date}
              </p>
              <h2 className="mt-3 font-display text-2xl font-extrabold">{current.title}</h2>
              <p className="mt-2 text-muted-foreground">{current.summary}</p>
              <div className="mt-4 flex flex-wrap gap-3 text-sm">
                <DifficultyBadge value={current.difficulty} />
                <span className="text-muted-foreground">{current.category}</span>
              </div>
              <Button className="mt-6" asChild>
                <ELink to={current.path}>
                  Solve problem <ArrowRight className="size-4" />
                </ELink>
              </Button>
            </div>
          ) : (
            <EmptyState
              title="No problem scheduled"
              text="Set a “Problem of the Day date” on a problem in the admin to feature it here."
            />
          )}
        </div>
        <aside aria-labelledby="archive-h">
          <h2 id="archive-h" className="font-display text-lg font-bold">
            Previous problems
          </h2>
          <ol className="mt-3 grid gap-2">
            {archive.map((p) => (
              <li key={p.path}>
                <ELink
                  to={p.path}
                  className="flex items-center justify-between gap-3 rounded-lg border border-border bg-card p-3 hover:border-primary/40"
                >
                  <span>
                    <span className="block text-xs text-muted-foreground">{p.potd_date}</span>
                    <span className="font-semibold">{p.title}</span>
                  </span>
                  <DifficultyBadge value={p.difficulty} />
                </ELink>
              </li>
            ))}
            {!archive.length && (
              <li className="text-sm text-muted-foreground">The archive fills up as days pass.</li>
            )}
          </ol>
        </aside>
      </Container>
    </>
  );
}

/* ---------- 8. Course listing & 9. Course detail ---------- */
function CourseListing({
  plan,
  search,
}: {
  plan: Extract<Plan, { kind: "list" }>;
  search: SiteSearch;
}) {
  const { data } = useSuspenseQuery(listQuery(plan.input));
  const { data: all } = useSuspenseQuery(listQuery({ type: "course", limit: 100 }));
  const cats = [...new Set(all.items.map((c) => c.category).filter(Boolean) as string[])];
  const page = search.page ?? 1;
  const label = (s: string) => s.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  return (
    <>
      <PageHeader
        tone="course-hero"
        crumbs={plan.slug ? [["Courses", "/courses"], [label(plan.slug)]] : [["Courses"]]}
        eyebrow="Courses"
        title={plan.slug ? `${label(plan.slug)} courses` : "Learn from structured courses"}
        description="Live and self-paced programs with projects, mentorship and certificates."
      >
        <SearchBar placeholder="Search courses" defaultValue={search.q} />
      </PageHeader>
      <Container className="py-8">
        <nav
          aria-label="Course categories"
          className="scrollbar-none -mx-1 flex gap-2 overflow-x-auto px-1 py-1"
        >
          <ELink
            to="/courses"
            className={`shrink-0 rounded-full border px-4 py-1.5 text-sm font-semibold ${!plan.slug ? "border-primary bg-primary text-primary-foreground" : "border-border bg-card"}`}
          >
            All
          </ELink>
          {cats.map((c) => (
            <ELink
              key={c}
              to={`/courses/category/${c}`}
              className={`shrink-0 rounded-full border px-4 py-1.5 text-sm font-semibold ${plan.slug === c ? "border-primary bg-primary text-primary-foreground" : "border-border bg-card hover:border-primary/50"}`}
            >
              {label(c)}
            </ELink>
          ))}
        </nav>
        <div className="mt-6">
          {data.items.length ? (
            <Grid>
              {data.items.map((c) => {
                const cd = obj(c.data);
                return (
                  <EntryCard
                    key={c.path}
                    item={c}
                    icon={<GraduationCap />}
                    meta={
                      <>
                        {str(cd.rating) && (
                          <span className="inline-flex items-center gap-1">
                            <Star className="size-3 fill-current text-warning" />
                            {str(cd.rating)}
                          </span>
                        )}
                        {str(cd.learners) && (
                          <span className="inline-flex items-center gap-1">
                            <Users className="size-3" />
                            {str(cd.learners)}
                          </span>
                        )}
                        {str(cd.mode) && <Badge variant="outline">{str(cd.mode)}</Badge>}
                        {str(cd.price) && (
                          <span className="ml-auto text-sm font-bold text-foreground">
                            {str(cd.price)}
                          </span>
                        )}
                      </>
                    }
                  />
                );
              })}
            </Grid>
          ) : (
            <EmptyState title="No courses found" text="Try another category or search term." />
          )}
        </div>
        <Pager total={data.total} page={page} />
      </Container>
    </>
  );
}

function CourseDetail({ entry, d }: { entry: Entry; d: EntryData }) {
  const syllabus = arr<{ title?: string; items?: string[] }>(d.syllabus);
  const outcomes = arr<string>(d.outcomes);
  return (
    <>
      <PageHeader
        tone="course-hero"
        crumbs={[["Courses", "/courses"], [entry.title]]}
        eyebrow={str(d.mode, "Course")}
        title={entry.title}
        description={entry.summary}
      >
        <div className="flex flex-wrap gap-4 text-sm">
          {str(d.rating) && (
            <span className="inline-flex items-center gap-1 font-semibold">
              <Star className="size-4 fill-current text-warning" />
              {str(d.rating)} rating
            </span>
          )}
          {str(d.learners) && (
            <span className="inline-flex items-center gap-1">
              <Users className="size-4" />
              {str(d.learners)} learners
            </span>
          )}
          {str(d.duration) && (
            <span className="inline-flex items-center gap-1">
              <Clock className="size-4" />
              {str(d.duration)}
            </span>
          )}
          {entry.difficulty && <DifficultyBadge value={entry.difficulty} />}
        </div>
      </PageHeader>
      <Container className="grid gap-10 py-10 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div className="min-w-0">
          {outcomes.length > 0 && (
            <section aria-labelledby="learn" className="rounded-xl border border-border p-6">
              <h2 id="learn" className="font-display text-xl font-bold">
                What you'll learn
              </h2>
              <ul className="mt-4 grid gap-3 sm:grid-cols-2">
                {outcomes.map((o) => (
                  <li key={o} className="flex gap-2 text-sm">
                    <Check className="mt-0.5 size-4 shrink-0 text-primary" />
                    {o}
                  </li>
                ))}
              </ul>
            </section>
          )}
          <div className="mt-8">
            <Markdown source={entry.body} />
          </div>
          <section className="mt-8 rounded-xl border p-6">
            <h2 className="font-display text-xl font-bold">Your instructor</h2>
            <ELink
              to={str(d.instructor_path, "authors")}
              className="mt-3 block font-semibold text-primary"
            >
              {str(d.instructor, "Course team")}
            </ELink>
            <p className="mt-2 text-sm text-muted-foreground">
              View expertise and published resources.
            </p>
          </section>
          {arr<string>(d.projects).length > 0 && (
            <section className="mt-8">
              <h2 className="font-display text-xl font-bold">Hands-on projects</h2>
              <ul className="mt-3 grid gap-2">
                {arr<string>(d.projects).map((p) => (
                  <li key={p} className="rounded-lg border p-4 text-sm">
                    {p}
                  </li>
                ))}
              </ul>
            </section>
          )}
          <section className="mt-8">
            <h2 className="font-display text-xl font-bold">Available batches</h2>
            <div className="mt-3 grid gap-3">
              {arr<{ title: string; schedule: string; seats: string }>(d.batches).map((b) => (
                <div key={b.title} className="rounded-lg border p-4">
                  <h3 className="font-semibold">{b.title}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {b.schedule} · {b.seats}
                  </p>
                </div>
              ))}
            </div>
          </section>
          <section className="mt-8">
            <h2 className="font-display text-xl font-bold">Learner reviews</h2>
            <p className="mt-3 text-sm text-muted-foreground">
              No verified reviews published yet.
            </p>
          </section>
          <Button
            className="mt-6"
            variant="outline"
            onClick={() => {
              const text = `${entry.title}\n${entry.summary}\n\n${syllabus.map((m) => `${m.title}\n${(m.items ?? []).join("\n")}`).join("\n\n")}`;
              const url = URL.createObjectURL(new Blob([text], { type: "text/plain" }));
              const a = document.createElement("a");
              a.href = url;
              a.download = "dekhoexams-course-outline.txt";
              a.click();
              URL.revokeObjectURL(url);
            }}
          >
            Download course outline
          </Button>
          {syllabus.length > 0 && (
            <section aria-labelledby="syl" className="mt-10">
              <h2 id="syl" className="font-display text-2xl font-bold">
                Syllabus
              </h2>
              <Accordion
                type="multiple"
                defaultValue={["0"]}
                className="mt-4 rounded-lg border border-border"
              >
                {syllabus.map((m, i) => (
                  <AccordionItem key={i} value={String(i)} className="px-4 last:border-b-0">
                    <AccordionTrigger className="font-display font-bold">
                      {m.title}
                    </AccordionTrigger>
                    <AccordionContent>
                      <ul className="grid gap-2">
                        {(m.items ?? []).map((it) => (
                          <li key={it} className="flex items-center gap-2 text-sm">
                            <BookOpen className="size-4 text-muted-foreground" />
                            {it}
                          </li>
                        ))}
                      </ul>
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </section>
          )}
        </div>
        <aside className="lg:sticky lg:top-[100px] lg:self-start">
          <div className="rounded-xl border border-border bg-card p-6 shadow-card">
            <p className="font-display text-3xl font-extrabold">{str(d.price, "Free")}</p>
            {str(d.original_price) && (
              <p className="text-sm text-muted-foreground line-through">{str(d.original_price)}</p>
            )}
            <Button className="mt-5 h-11 w-full" asChild>
              <ELink to={`checkout/${entry.path.replace(/^courses\//, "")}`}>View enrollment</ELink>
            </Button>
            <Button className="mt-3 h-11 w-full" variant="outline" asChild>
              <ELink to={`learn/${entry.path.replace(/^courses\//, "")}/lesson/1`}>
                Preview curriculum
              </ELink>
            </Button>
            <div className="mt-3">
              <BookmarkButton entry={entry} />
            </div>
            <ul className="mt-5 grid gap-2 text-sm text-muted-foreground">
              {str(d.duration) && (
                <li className="flex gap-2">
                  <Clock className="size-4" />
                  {str(d.duration)}
                </li>
              )}
              {str(d.mode) && (
                <li className="flex gap-2">
                  <CirclePlay className="size-4" />
                  {str(d.mode)} classes
                </li>
              )}
              <li className="flex gap-2">
                <GraduationCap className="size-4" />
                Certificate of completion
              </li>
            </ul>
          </div>
        </aside>
      </Container>
    </>
  );
}

/* ---------- 10. Video listing & 11. Video detail ---------- */
function VideoThumb({ title, duration }: { title: string; duration?: string }) {
  return (
    <div className="relative grid aspect-video place-items-center overflow-hidden rounded-t-lg bg-video">
      <span className="grid size-12 place-items-center rounded-full bg-background/90 text-primary shadow">
        <Play className="size-5 fill-current" />
        <span className="sr-only">Play {title}</span>
      </span>
      {duration && (
        <span className="absolute bottom-2 right-2 rounded bg-foreground/80 px-1.5 py-0.5 text-xs font-semibold text-background">
          {duration}
        </span>
      )}
    </div>
  );
}

function VideoCard({ v }: { v: ListItem }) {
  const vd = obj(v.data);
  return (
    <ELink
      to={v.path}
      className="group overflow-hidden rounded-lg border border-border bg-card shadow-card transition hover:-translate-y-0.5 hover:shadow-card-hover"
    >
      <VideoThumb title={v.title} duration={str(vd.duration)} />
      <div className="p-4">
        <h3 className="font-display font-bold leading-snug group-hover:text-primary">{v.title}</h3>
        <p className="mt-1 text-xs text-muted-foreground">
          {[str(vd.instructor), str(vd.views) && `${str(vd.views)} views`]
            .filter(Boolean)
            .join(" · ")}
        </p>
      </div>
    </ELink>
  );
}

function VideoListing({
  plan,
  search,
}: {
  plan: Extract<Plan, { kind: "list" }>;
  search: SiteSearch;
}) {
  const { data } = useSuspenseQuery(listQuery(plan.input));
  const { data: all } = useSuspenseQuery(listQuery({ type: "video", limit: 100 }));
  const cats = [...new Set(all.items.map((c) => c.category).filter(Boolean) as string[])];
  const label = (s: string) => s.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  return (
    <>
      <PageHeader
        crumbs={plan.slug ? [["Videos", "/videos"], [label(plan.slug)]] : [["Videos"]]}
        eyebrow="Videos"
        title={plan.slug ? `${label(plan.slug)} videos` : "Watch and learn"}
        description="Short, focused lessons explained visually."
      >
        <SearchBar placeholder="Search videos" defaultValue={search.q} />
      </PageHeader>
      <Container className="py-8">
        <nav
          aria-label="Video categories"
          className="scrollbar-none -mx-1 flex gap-2 overflow-x-auto px-1 py-1"
        >
          <ELink
            to="/videos"
            className={`shrink-0 rounded-full border px-4 py-1.5 text-sm font-semibold ${!plan.slug ? "border-primary bg-primary text-primary-foreground" : "border-border bg-card"}`}
          >
            All
          </ELink>
          {cats.map((c) => (
            <ELink
              key={c}
              to={`/videos/category/${c}`}
              className={`shrink-0 rounded-full border px-4 py-1.5 text-sm font-semibold ${plan.slug === c ? "border-primary bg-primary text-primary-foreground" : "border-border bg-card hover:border-primary/50"}`}
            >
              {label(c)}
            </ELink>
          ))}
        </nav>
        <div className="mt-6">
          {data.items.length ? (
            <Grid cols={4}>
              {data.items.map((v) => (
                <VideoCard key={v.path} v={v} />
              ))}
            </Grid>
          ) : (
            <EmptyState title="No videos found" text="Try another category." />
          )}
        </div>
        <Pager total={data.total} page={search.page ?? 1} />
      </Container>
    </>
  );
}

function VideoDetail({ entry, d }: { entry: Entry; d: EntryData }) {
  const { data } = useSuspenseQuery(listQuery({ type: "video", limit: 8 }));
  const url = str(d.video_url);
  const related = data.items.filter((v) => v.path !== entry.path).slice(0, 6);
  return (
    <Container className="grid gap-8 py-6 lg:grid-cols-[minmax(0,1fr)_340px]">
      <div className="min-w-0">
        <div className="overflow-hidden rounded-xl bg-video">
          {url ? (
            <SafeMedia url={url} title={entry.title} />
          ) : (
            <div className="grid aspect-video place-items-center text-center">
              <div>
                <CirclePlay className="mx-auto size-12 text-primary" />
                <p className="mt-2 text-sm text-muted-foreground">Video not uploaded yet</p>
              </div>
            </div>
          )}
        </div>
        <Crumbs items={[["Videos", "/videos"], [entry.title]]} />
        <h1 className="mt-3 font-display text-2xl font-extrabold md:text-3xl">{entry.title}</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          {[str(d.instructor), str(d.views) && `${str(d.views)} views`, str(d.duration)]
            .filter(Boolean)
            .join(" · ")}
        </p>
        <Tabs defaultValue="description" className="mt-5">
          <TabsList>
            <TabsTrigger value="description">Description</TabsTrigger>
            <TabsTrigger value="transcript">Transcript</TabsTrigger>
          </TabsList>
          <TabsContent value="description">
            <div className="rounded-lg bg-surface-subtle p-5">
              <p className="font-semibold">{entry.summary}</p>
              <Markdown source={entry.body} />
            </div>
          </TabsContent>
          <TabsContent value="transcript">
            <div className="rounded-lg border p-5">
              <Markdown source={str(d.transcript, "Transcript not published yet.")} />
            </div>
          </TabsContent>
        </Tabs>
      </div>
      <aside aria-labelledby="rel">
        <h2 id="rel" className="font-display font-bold">
          Up next
        </h2>
        <div className="mt-3 grid gap-3">
          {related.map((v) => (
            <VideoCard key={v.path} v={v} />
          ))}
        </div>
      </aside>
    </Container>
  );
}

/* ---------- 12. Event listing & 13. Event detail ---------- */
const fmtDate = (iso: string) => {
  const t = Date.parse(iso);
  return Number.isNaN(t)
    ? iso
    : new Date(t).toLocaleString("en-IN", {
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "numeric",
        minute: "2-digit",
        timeZone: "Asia/Kolkata",
      });
};

function EventListing({
  plan,
  search,
}: {
  plan: Extract<Plan, { kind: "list" }>;
  search: SiteSearch;
}) {
  const { data } = useSuspenseQuery(listQuery(plan.input));
  const now = Date.now();
  const end = (e: ListItem) =>
    Date.parse(str(obj(e.data).ends_at) || str(obj(e.data).starts_at)) || 0;
  const upcoming = data.items.filter((e) => end(e) >= now);
  const past = data.items.filter((e) => end(e) < now);
  const render = (list: ListItem[], empty: string) =>
    list.length ? (
      <Grid>
        {list.map((e) => {
          const ed = obj(e.data);
          return (
            <EntryCard
              key={e.path}
              item={e}
              icon={<CalendarDays />}
              meta={
                <>
                  {str(ed.starts_at) && <span>{fmtDate(str(ed.starts_at))}</span>}
                  {str(ed.location) && (
                    <span className="inline-flex items-center gap-1">
                      <MapPin className="size-3" />
                      {str(ed.location)}
                    </span>
                  )}
                  {e.category && <Badge variant="outline">{e.category}</Badge>}
                </>
              }
            />
          );
        })}
      </Grid>
    ) : (
      <EmptyState title={empty} text="Check back soon for new events." />
    );
  return (
    <>
      <PageHeader
        tone="event-hero"
        crumbs={[["Events"]]}
        eyebrow="Events & contests"
        title="Compete, learn and connect"
        description="Hackathons, coding contests, hiring challenges and community events."
      />
      <Container className="py-8">
        <Tabs defaultValue={search.tab === "past" ? "past" : "upcoming"}>
          <TabsList>
            <TabsTrigger value="upcoming">Upcoming ({upcoming.length})</TabsTrigger>
            <TabsTrigger value="past">Past ({past.length})</TabsTrigger>
          </TabsList>
          <TabsContent value="upcoming" className="mt-6">
            {render(upcoming, "No upcoming events")}
          </TabsContent>
          <TabsContent value="past" className="mt-6">
            {render(past, "No past events")}
          </TabsContent>
        </Tabs>
        <Pager total={data.total} page={search.page ?? 1} />
      </Container>
    </>
  );
}

function EventDetail({ entry, d }: { entry: Entry; d: EntryData }) {
  const [note, setNote] = useState(false);
  const agenda = arr<{ time?: string; title?: string }>(d.agenda);
  const reg = str(d.register_url);
  const past = (Date.parse(str(d.ends_at) || str(d.starts_at)) || Infinity) < Date.now();
  return (
    <>
      <PageHeader
        tone="event-hero"
        crumbs={[["Events", "/events"], [entry.title]]}
        eyebrow={entry.category ?? "Event"}
        title={entry.title}
        description={entry.summary}
      >
        <div className="flex flex-wrap items-center gap-4 text-sm">
          {str(d.starts_at) && (
            <span className="inline-flex items-center gap-1.5">
              <CalendarDays className="size-4" />
              {fmtDate(str(d.starts_at))}
            </span>
          )}
          {str(d.location) && (
            <span className="inline-flex items-center gap-1.5">
              <MapPin className="size-4" />
              {str(d.location)}
            </span>
          )}
          {past ? (
            <Badge variant="secondary">Ended</Badge>
          ) : reg ? (
            <Button asChild>
              <a href={reg} target="_blank" rel="noopener noreferrer">
                Register now
              </a>
            </Button>
          ) : (
            <Button onClick={() => setNote(true)}>Register now</Button>
          )}
        </div>
        <div className="mt-5 flex flex-wrap gap-3">
          <Button variant="outline" asChild>
            <ELink to={`${entry.path}/participate`}>Practice workspace</ELink>
          </Button>
          <Button variant="outline" asChild>
            <ELink to={`${entry.path}/leaderboard`}>Leaderboard</ELink>
          </Button>
        </div>
        {note && (
          <p
            role="status"
            className="mt-3 max-w-xl rounded-md border border-warning-border bg-warning/10 p-3 text-sm"
          >
            Registration isn't open online yet. Add a registration link in the admin to enable it.
          </p>
        )}
      </PageHeader>
      <Container className="grid gap-10 py-10 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="min-w-0">
          <Markdown source={entry.body} />
        </div>
        {agenda.length > 0 && (
          <aside
            aria-labelledby="agenda-h"
            className="rounded-xl border border-border p-5 lg:self-start"
          >
            <h2 id="agenda-h" className="font-display text-lg font-bold">
              Agenda
            </h2>
            <ol className="mt-4 grid gap-4 border-l-2 border-primary/30 pl-4">
              {agenda.map((a, i) => (
                <li key={i}>
                  <p className="text-xs font-bold text-primary">{a.time}</p>
                  <p className="font-semibold">{a.title}</p>
                </li>
              ))}
            </ol>
          </aside>
        )}
      </Container>
    </>
  );
}

/* ---------- 14. Job listing (+ job detail) ---------- */
function JobListing({
  plan,
  search,
}: {
  plan: Extract<Plan, { kind: "list" }>;
  search: SiteSearch;
}) {
  const { data } = useSuspenseQuery(listQuery(plan.input));
  const { data: all } = useSuspenseQuery(listQuery({ type: "job", limit: 100 }));
  const companies = [...new Set(all.items.map((j) => str(obj(j.data).company)).filter(Boolean))];
  const navigate = useNavigate();
  return (
    <>
      <PageHeader
        tone="business-hero"
        crumbs={[["Jobs"]]}
        eyebrow="Careers"
        title="Find your next tech role"
        description="Curated openings from companies hiring developers."
      >
        <SearchBar placeholder="Search by role or keyword" defaultValue={search.q} />
      </PageHeader>
      <Container className="py-8">
        <div className="mb-6 max-w-xs">
          <FilterSelect
            label="Company"
            value={search.company}
            options={companies}
            onChange={(v) =>
              navigate({
                to: ".",
                search: (p: SiteSearch) => ({ ...p, company: v || undefined, page: undefined }),
              })
            }
          />
        </div>
        <p className="mb-4 text-sm text-muted-foreground" aria-live="polite">
          {data.total} opening{data.total === 1 ? "" : "s"}
        </p>
        {data.items.length ? (
          <div className="grid gap-3">
            {data.items.map((j) => {
              const jd = obj(j.data);
              return (
                <ELink
                  key={j.path}
                  to={j.path}
                  className="group grid gap-3 rounded-lg border border-border bg-card p-5 hover:border-primary/40 sm:grid-cols-[auto_1fr_auto] sm:items-center"
                >
                  <span className="grid size-12 place-items-center rounded-lg bg-primary-soft font-display text-lg font-extrabold text-primary">
                    {str(jd.company, "?").charAt(0)}
                  </span>
                  <div>
                    <h2 className="font-display text-lg font-bold group-hover:text-primary">
                      {j.title}
                    </h2>
                    <p className="text-sm text-muted-foreground">{str(jd.company)}</p>
                    <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
                      {str(jd.location) && (
                        <span className="inline-flex items-center gap-1">
                          <MapPin className="size-3" />
                          {str(jd.location)}
                        </span>
                      )}
                      {str(jd.experience) && (
                        <span className="inline-flex items-center gap-1">
                          <BriefcaseBusiness className="size-3" />
                          {str(jd.experience)}
                        </span>
                      )}
                      {str(jd.salary) && <span>{str(jd.salary)}</span>}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    {j.featured && <Badge>Featured</Badge>}
                    {str(jd.job_type) && <Badge variant="outline">{str(jd.job_type)}</Badge>}
                  </div>
                </ELink>
              );
            })}
          </div>
        ) : (
          <EmptyState title="No openings match" text="Try a different keyword." />
        )}
        <Pager total={data.total} page={search.page ?? 1} />
      </Container>
    </>
  );
}

function JobDetail({ entry, d }: { entry: Entry; d: EntryData }) {
  const apply = str(d.apply_url);
  return (
    <>
      <PageHeader
        tone="business-hero"
        crumbs={[["Jobs", "/jobs"], [entry.title]]}
        eyebrow={str(d.company)}
        title={entry.title}
        description={entry.summary}
      >
        <div className="flex flex-wrap gap-4 text-sm">
          {[str(d.location), str(d.experience), str(d.salary), str(d.job_type)]
            .filter(Boolean)
            .map((x) => (
              <span key={x} className="rounded-full border border-border bg-background px-3 py-1">
                {x}
              </span>
            ))}
        </div>
      </PageHeader>
      <Container className="grid gap-10 py-10 lg:grid-cols-[minmax(0,1fr)_300px]">
        <div className="min-w-0">
          <Markdown source={entry.body} />
        </div>
        <aside className="rounded-xl border border-border p-5 lg:self-start">
          <div className="mb-4">
            <BookmarkButton entry={entry} />
          </div>
          <Button className="mb-4 w-full" variant="outline" asChild>
            <ELink to={`${entry.path}/apply`}>Application preview</ELink>
          </Button>
          {str(d.company_path) && (
            <ELink to={str(d.company_path)} className="mb-4 block text-sm text-primary">
              View company profile
            </ELink>
          )}
          {apply ? (
            <Button asChild className="w-full">
              <a href={apply} target="_blank" rel="noopener noreferrer">
                Apply on company site
              </a>
            </Button>
          ) : (
            <p className="text-sm text-muted-foreground">
              Applications for this role aren't open online yet.
            </p>
          )}
        </aside>
      </Container>
    </>
  );
}

/* ---------- 15. Business landing ---------- */
function BusinessLanding({ entry, d }: { entry: Entry; d: EntryData }) {
  const features = arr<{ title?: string; text?: string }>(d.features);
  const stats = arr<{ label?: string; value?: string }>(d.stats);
  const cta = str(d.cta_url, "/about/contact-us");
  return (
    <>
      <PageHeader
        tone="business-hero"
        crumbs={[[entry.title]]}
        eyebrow="For business"
        title={entry.title}
        description={entry.summary}
      >
        <Button size="lg" asChild>
          <ELink to={cta}>
            {str(d.cta_label, "Contact us")} <ArrowRight className="size-4" />
          </ELink>
        </Button>
      </PageHeader>
      {stats.length > 0 && (
        <Container className="grid gap-4 py-8 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map((s) => (
            <div key={s.label} className="rounded-lg border border-border p-5">
              <p className="font-display text-3xl font-extrabold text-primary">{s.value}</p>
              <p className="text-sm text-muted-foreground">{s.label}</p>
            </div>
          ))}
        </Container>
      )}
      <Container className="py-10">
        <div className="max-w-3xl">
          <Markdown source={entry.body} />
        </div>
        {features.length > 0 && (
          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((f) => (
              <div
                key={f.title}
                className="rounded-xl border border-border bg-card p-6 shadow-card"
              >
                <Code2 className="size-6 text-primary" />
                <h3 className="mt-4 font-display text-lg font-bold">{f.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{f.text}</p>
              </div>
            ))}
          </div>
        )}
        <InquiryForm title={`Discuss ${entry.title.toLowerCase()}`} />
        <div className="mt-12 rounded-2xl bg-primary p-8 text-primary-foreground md:flex md:items-center md:justify-between">
          <p className="font-display text-2xl font-extrabold">Ready to get started?</p>
          <Button variant="secondary" size="lg" className="mt-4 md:mt-0" asChild>
            <ELink to={cta}>{str(d.cta_label, "Contact us")}</ELink>
          </Button>
        </div>
      </Container>
    </>
  );
}

/* ---------- 16. Static information page ---------- */
function StaticPage({ entry }: { entry: Entry }) {
  const { data } = useSuspenseQuery(listQuery({ type: "page", limit: 50 }));
  return (
    <Container className="grid gap-10 py-10 lg:grid-cols-[220px_minmax(0,1fr)]">
      <nav
        aria-label="Information pages"
        className="min-w-0 lg:sticky lg:top-[100px] lg:self-start"
      >
        <ul className="flex gap-2 overflow-x-auto lg:grid lg:gap-1">
          {data.items.map((p) => (
            <li key={p.path} className="shrink-0">
              <ELink
                to={p.path}
                aria-current={p.path === entry.path ? "page" : undefined}
                className={`block rounded-md px-3 py-2 text-sm ${p.path === entry.path ? "bg-primary-soft font-semibold text-primary" : "text-muted-foreground hover:bg-accent"}`}
              >
                {p.title}
              </ELink>
            </li>
          ))}
        </ul>
      </nav>
      <article className="min-w-0 max-w-3xl">
        <Crumbs items={[[entry.title]]} />
        <h1 className="mt-4 font-display text-3xl font-extrabold md:text-4xl">{entry.title}</h1>
        {entry.summary && <p className="mt-3 text-lg text-muted-foreground">{entry.summary}</p>}
        <p className="mt-2 text-xs text-muted-foreground">
          Last updated{" "}
          {new Date(entry.updated_at).toLocaleDateString("en-IN", {
            day: "numeric",
            month: "long",
            year: "numeric",
            timeZone: "Asia/Kolkata",
          })}
        </p>
        <div className="mt-6">
          <Markdown source={entry.body} />
        </div>
        {entry.path === "about/contact-us" && <InquiryForm />}
      </article>
    </Container>
  );
}

/* ---------- Search ---------- */
function SearchResults({
  plan,
  search,
}: {
  plan: Extract<Plan, { kind: "list" }>;
  search: SiteSearch;
}) {
  const { data } = useSuspenseQuery(listQuery(plan.input));
  const q = search.q?.trim();
  return (
    <>
      <PageHeader
        crumbs={[["Search"]]}
        title={q ? `Results for “${q}”` : "Search"}
        description="Search tutorials, problems, videos, events and jobs."
      >
        <SearchBar placeholder="What do you want to learn?" defaultValue={q} />
      </PageHeader>
      <Container className="py-8">
        {!q ? (
          <EmptyState title="Start typing to search" text="Try “python”, “sorting” or “react”." />
        ) : data.items.length ? (
          <ul className="grid gap-3">
            {data.items.map((r) => (
              <li key={r.path}>
                <ELink
                  to={r.path}
                  className="block rounded-lg border border-border bg-card p-4 hover:border-primary/40"
                >
                  <Badge variant="outline" className="capitalize">
                    {r.type}
                  </Badge>
                  <h2 className="mt-2 font-display font-bold">{r.title}</h2>
                  <p className="mt-1 text-sm text-muted-foreground">{r.summary}</p>
                </ELink>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState title="No results" text="Try a broader term or check the spelling." />
        )}
        <Pager total={data.total} page={search.page ?? 1} />
      </Container>
    </>
  );
}

import { useEffect, useState } from "react";
import { ArrowRight, Bookmark, CheckCircle2, ChevronDown, RotateCcw, Search } from "lucide-react";
import { StudyStrategy } from "@/components/study-strategy";
import {
  EDUCATION_PAGES,
  GRADES_FOR_FILTER,
  NCERT_SYLLABUS_SOURCE,
  SUBJECTS,
  educationBreadcrumbs,
  educationPage,
  relatedEducationPages,
  resourceById,
  RESOURCES,
  type EducationPage as Page,
  type LearningResource,
} from "@/lib/education-catalog";
import { updateProgress, useLearningProgress } from "@/lib/learning-progress";
import { directoryGroup, directoryItem } from "@/lib/subject-directory";
import { examGuide } from "@/lib/exam-update-guides";
import type { SchoolLesson } from "@/lib/school-content";

function ownedChildren(page: Page) {
  return page.children
    .map(educationPage)
    .filter((child): child is Page => !!child && child.parent === page.path);
}

function hasStudyPreview(page: Page) {
  return page.family === "school" && page.resourceIds.length > 0 && page.resourceIds.length <= 4;
}

function syllabusGrade(path: string) {
  const classMatch = /^\/ncert\/class-(\d+)$/.exec(path);
  const languageMatch = /^\/ncert\/(?:english|hindi)\/class-(\d+)$/.exec(path);
  return Number(classMatch?.[1] ?? languageMatch?.[1] ?? 0);
}

function SyllabusSpotlight({ grade, pagePath }: { grade: number; pagePath: string }) {
  const language = /^\/ncert\/(english|hindi)\/class-\d+$/.exec(pagePath)?.[1];
  const syllabusPath = language ? `${pagePath}/syllabus` : `/ncert/class-${grade}/syllabus`;
  return (
    <section className="study-syllabus-spotlight" id="syllabus-spotlight" aria-label="Syllabus">
      <div>
        <span className="study-syllabus-eyebrow">Syllabus first</span>
        <p>
          Check what applies before you plan your revision. Our class-specific outline is still
          being reviewed.
        </p>
      </div>
      <div className="study-syllabus-actions">
        <a href={syllabusPath}>
          {language ? `${language === "english" ? "English" : "Hindi"} ` : ""}Class {grade} syllabus{" "}
          <ArrowRight aria-hidden="true" />
        </a>
        <a href={NCERT_SYLLABUS_SOURCE.path} target="_blank" rel="noopener noreferrer">
          Official NCERT source <span aria-label="opens in a new tab">↗</span>
        </a>
      </div>
    </section>
  );
}

function ResourceLinks({ resources }: { resources: LearningResource[] }) {
  return (
    <div className="study-subject-list">
      {resources.map((r) => (
        <a className="study-subject-link" key={r.id} href={r.canonicalPath}>
          <span className="study-subject-label">
            Class {r.lesson.grade} · {r.lesson.subject} · English
          </span>
          <strong>{r.lesson.title}</strong>
          <span>{r.lesson.summary}</span>
        </a>
      ))}
    </div>
  );
}

export function EducationPage({
  path,
  query = "",
  grade = "",
  topic = "",
  lessonOverride = null,
}: {
  path: string;
  query?: string;
  grade?: string;
  topic?: string;
  lessonOverride?: Partial<SchoolLesson> | null;
}) {
  const page = educationPage(path)!;
  const guide = examGuide(page.path);
  const syllabus = syllabusGrade(page.path);
  const classDirectory = /(?:^|\/)class-\d+$/.test(page.path);
  const original = page.resourceId ? resourceById(page.resourceId) : undefined;
  const resource = original && lessonOverride
    ? { ...original, lesson: { ...original.lesson, ...lessonOverride } }
    : original;
  const utility = page.family === "utility";
  const relatedPages = utility ? [] : relatedEducationPages(page);
  const group = directoryGroup(page.path);
  const selected = directoryItem(page.path, topic);
  const parent = educationPage(page.parent);
  const curriculumPage = resource ? (parent ?? page) : page;
  const sectionLinks =
    curriculumPage.sections
      ?.find((section) => section.title === "Subjects")
      ?.paths.map(educationPage)
      .filter((item): item is Page => !!item)
      .map((item) => ({ title: item.title, path: item.path })) ??
    curriculumPage.sections
      ?.find((section) => section.paths.length)
      ?.paths.map(educationPage)
      .filter((item): item is Page => !!item)
      .map((item) => ({ title: item.title, path: item.path }));
  const curriculumLinks = group
    ? group.items.map((item) => ({ title: item.label, path: item.href }))
    : sectionLinks?.length
      ? sectionLinks
      : curriculumPage.children.length
        ? curriculumPage.children
            .map(educationPage)
            .filter((p): p is Page => !!p)
            .map((p) => ({ title: p.title, path: p.path }))
        : curriculumPage.resourceIds
            .map(resourceById)
            .filter((r): r is LearningResource => !!r)
            .map((r) => ({ title: r.lesson.title, path: r.canonicalPath }));
  const fallbackLinks =
    !curriculumLinks.length && parent
      ? parent.children
          .map(educationPage)
          .filter((p): p is Page => !!p)
          .map((p) => ({ title: p.title, path: p.path }))
      : curriculumLinks;
  let tabsPage: Page | undefined = resource ? parent : page;
  while (tabsPage && ownedChildren(tabsPage).length < 2 && tabsPage.parent !== "/") {
    tabsPage = educationPage(tabsPage.parent);
  }
  const tabs =
    !classDirectory && page.path !== "/classes" && tabsPage
      ? [...(tabsPage.path === page.path ? [tabsPage] : []), ...ownedChildren(tabsPage)]
      : [];
  const outline =
    page.path === "/classes"
      ? []
      : resource
        ? [
            { id: "book", title: "Book" },
            { id: "study-strategy", title: "Study strategy" },
            { id: "key-idea", title: "Key idea" },
            { id: "why-it-works", title: "Why it works" },
            { id: "worked-example", title: "Worked example" },
            { id: "common-mistakes", title: "Common mistakes" },
            { id: "practice", title: "Chapter self-check" },
            { id: "continue-learning", title: "Continue learning" },
            ...(relatedPages.length ? [{ id: "related-study", title: "Keep exploring" }] : []),
          ]
        : [
            ...(syllabus ? [{ id: "syllabus-spotlight", title: "Syllabus" }] : []),
            ...(selected ? [{ id: "selected-course", title: "Selected course" }] : []),
            ...(group && !selected ? [{ id: "courses", title: "Courses" }] : []),
            ...(guide
              ? guide.sections.map((section, index) => ({
                  id: `official-guide-${index}`,
                  title: section.heading,
                }))
              : []),
            ...(page.sections
              ? page.sections.map((section, index) => ({
                  id: `collection-section-${index}`,
                  title: section.title,
                }))
              : page.children.length
                ? [
                    {
                      id: "explore-collection",
                      title:
                        page.path === "/classes"
                          ? "Choose your class"
                          : ownedChildren(page).length
                            ? "Explore"
                            : "Related resources",
                    },
                  ]
                : []),
            ...(!page.sections && page.resourceIds.length
              ? [
                  {
                    id: "available-lessons",
                    title: page.children.length ? "Lessons & practice" : "Learning path",
                  },
                ]
              : []),
            ...(!page.sections && hasStudyPreview(page)
              ? [
                  { id: "study-notes", title: "Study notes" },
                  { id: "curriculum", title: "Curriculum" },
                ]
              : []),
            ...(page.sources.length && !guide
              ? [{ id: "official-sources", title: "Official sources" }]
              : []),
            ...(!utility ? [{ id: "study-strategy", title: "Study strategy" }] : []),
            ...(relatedPages.length ? [{ id: "related-study", title: "Keep exploring" }] : []),
          ];
  const breadcrumb = (
    <nav className="study-breadcrumb" aria-label="Breadcrumb">
      <a href="/">Home</a>
      {educationBreadcrumbs(page).map((p) => (
        <span key={p.path}>
          {" "}
          /{" "}
          {p.path === path ? (
            <span aria-current="page">{p.title}</span>
          ) : (
            <a href={p.path}>{p.title}</a>
          )}
        </span>
      ))}
    </nav>
  );
  const content = resource ? (
    <Lesson key={resource.id} resource={resource} />
  ) : (
    <>
      <h1>{page.title}</h1>
      {!!syllabus && <SyllabusSpotlight grade={syllabus} pagePath={page.path} />}
      {utility && <StudyStrategy />}
      {path === "/search" ? (
        <CatalogSearch query={query} grade={grade} />
      ) : path === "/my-study" ? (
        <MyStudy />
      ) : (
        <Collection page={page} topic={topic} showStrategy={!classDirectory} />
      )}
      {classDirectory && <StudyStrategy />}
    </>
  );
  if (utility) {
    return (
      <div className="study-home">
        {breadcrumb}
        {content}
      </div>
    );
  }
  return (
    <div className="study-home study-page-shell">
      {!!tabs.length && (
        <nav className="study-page-tabs" aria-label="Related study sections">
          <div>
            {tabs.map((tab) => (
              <a
                key={tab.path}
                href={tab.path}
                aria-current={
                  path === tab.path || path.startsWith(`${tab.path}/`) ? "page" : undefined
                }
              >
                {tab.title}
              </a>
            ))}
          </div>
        </nav>
      )}
      <div
        className={`study-page-grid${page.path === "/classes" ? " study-page-grid-classes" : outline.length ? "" : " study-page-grid-no-outline"}`}
      >
        {page.path !== "/classes" && (
          <aside className="study-page-curriculum" aria-label="Related sections">
            <StudyCurriculum
              title={curriculumPage.title}
              overview={curriculumPage.path}
              links={fallbackLinks}
              activePath={path}
              selectedHref={selected?.href}
            />
          </aside>
        )}
        <div className="study-page-main">
          {page.path !== "/classes" && fallbackLinks.length > 1 && (
            <details className="study-mobile-outline">
              <summary>
                Browse this section <ChevronDown aria-hidden="true" />
              </summary>
              <StudyCurriculum
                title={curriculumPage.title}
                overview={curriculumPage.path}
                links={fallbackLinks}
                activePath={path}
                selectedHref={selected?.href}
              />
            </details>
          )}
          <div className="study-page-article">
            {breadcrumb}
            {content}
            {!!relatedPages.length && (
              <nav className="study-related" id="related-study" aria-label="Related study paths">
                <h2>Keep exploring</h2>
                <div>
                  {relatedPages.map((related) => (
                    <a key={related.path} href={related.path}>
                      {related.title} <ArrowRight aria-hidden="true" />
                    </a>
                  ))}
                </div>
              </nav>
            )}
          </div>
        </div>
        {!!outline.length && (
          <aside className="study-page-on-this" aria-label="On this page">
            <p>On this page</p>
            <nav aria-label="Page sections">
              {outline.map((item) => (
                <a key={item.id} href={`#${item.id}`}>
                  {item.title}
                </a>
              ))}
            </nav>
          </aside>
        )}
      </div>
    </div>
  );
}

function StudyCurriculum({
  title,
  overview,
  links,
  activePath,
  selectedHref,
}: {
  title: string;
  overview: string;
  links: { title: string; path: string }[];
  activePath: string;
  selectedHref: string | undefined;
}) {
  return (
    <nav aria-label="Section links">
      <p className="study-curriculum-title">{title}</p>
      <a
        className="study-curriculum-overview"
        href={overview}
        aria-current={activePath === overview && !selectedHref ? "page" : undefined}
      >
        Section overview
      </a>
      {!!links.length && (
        <details className="study-curriculum-module" open>
          <summary>
            Explore this section
            <span>
              {links.length}
              <ChevronDown aria-hidden="true" />
            </span>
          </summary>
          <ol>
            {links.map((link, index) => (
              <li key={`${link.path}-${index}`}>
                <a
                  href={link.path}
                  aria-current={link.path === (selectedHref ?? activePath) ? "page" : undefined}
                >
                  <span aria-hidden="true">{String(index + 1).padStart(2, "0")}</span>
                  {link.title}
                </a>
              </li>
            ))}
          </ol>
        </details>
      )}
    </nav>
  );
}

function Collection({
  page,
  topic,
  showStrategy,
}: {
  page: Page;
  topic: string;
  showStrategy: boolean;
}) {
  const resources = page.resourceIds.map(resourceById).filter((r): r is LearningResource => !!r);
  const subject = SUBJECTS.find(
    ([slug]) => page.path === `/${slug}` || page.path.endsWith(`/${slug}`),
  )?.[0];
  const guide = examGuide(page.path);
  const group = directoryGroup(page.path);
  const selected = directoryItem(page.path, topic);
  return (
    <>
      {selected && (
        <section className="directory-selection" id="selected-course">
          <h2>{selected.label}</h2>
          <p>Dekhoexams lessons for this specific course are not published yet.</p>
          <a href={selected.referenceUrl} target="_blank" rel="noopener noreferrer">
            Study on Khan Academy <span aria-label="external site, opens in a new tab">↗</span>
          </a>
          <p className="study-intro">
            External resource. Dekhoexams is independent of Khan Academy.
          </p>
          <a href={page.path}>Back to {group!.title}</a>
        </section>
      )}
      {page.description !== `${page.title} on Dekhoexams.` && (
        <p className="study-intro">{page.description}</p>
      )}
      {page.notice && <p className="study-intro">{page.notice}</p>}
      {guide?.sections.map((section, index) => (
        <section className="study-more" id={`official-guide-${index}`} key={section.heading}>
          <h2>{section.heading}</h2>
          <p className="study-intro">{section.guidance}</p>
          <div className="study-subject-list">
            {section.links.map((link) => (
              <a
                className="study-subject-link"
                href={link.path}
                key={link.path}
                target="_blank"
                rel="noopener noreferrer"
              >
                <strong>{link.title}</strong>
                <span>Open official website ↗</span>
              </a>
            ))}
          </div>
        </section>
      ))}
      {group && !selected && (
        <section className="study-more" id="courses">
          <h2>Courses</h2>
          <ul className="directory-course-list">
            {group.items.map((item, index) => (
              <li key={`${item.id}-${index}`}>
                <a href={item.href}>
                  {item.label}
                  <ArrowRight aria-hidden="true" />
                </a>
              </li>
            ))}
          </ul>
        </section>
      )}
      {!!page.sections &&
        page.sections.map((section, index) => (
          <section
            className={`study-more${section.title === "Subjects" || section.title === "Boards & books" ? " study-more-rail" : ""}`}
            id={`collection-section-${index}`}
            key={`${section.title}-${index}`}
          >
            <h2>{section.title}</h2>
            {section.paths.length ? (
              <>
                <div className="study-subject-list">
                  {section.paths
                    .filter(
                      (path) =>
                        section.title !== "Boards & books" ||
                        !/^\/class-\d+$/.test(page.path) ||
                        !path.startsWith("/state-boards/"),
                    )
                    .map((path) => {
                      const destination = educationPage(path)!;
                      return (
                        <a key={path} href={path} className="study-subject-link">
                          <strong>
                            {section.title === "Subjects"
                              ? (SUBJECTS.find(([slug]) => path.endsWith(`/${slug}`))?.[1] ??
                                destination.title)
                              : destination.title}
                          </strong>
                          {destination.resourceId && <span>{destination.description}</span>}
                          <ArrowRight aria-hidden="true" />
                        </a>
                      );
                    })}
                </div>
                {section.title === "Boards & books" && /^\/class-\d+$/.test(page.path) && (
                  <details className="study-state-boards">
                    <summary>
                      State boards <ChevronDown aria-hidden="true" />
                    </summary>
                    <div className="study-subject-list">
                      {section.paths
                        .filter((path) => path.startsWith("/state-boards/"))
                        .map((path) => (
                          <a key={path} href={path} className="study-subject-link">
                            <strong>{educationPage(path)!.title}</strong>
                            <ArrowRight aria-hidden="true" />
                          </a>
                        ))}
                    </div>
                  </details>
                )}
              </>
            ) : (
              <p className="study-intro">{section.empty ?? "Material is awaiting review."}</p>
            )}
          </section>
        ))}
      {!page.sections && !!page.children.length && (
        <section className="study-more" id="explore-collection">
          <h2>
            {page.path === "/classes"
              ? "Choose your class"
              : ownedChildren(page).length
                ? "Explore"
                : "Related resources"}
          </h2>
          <div
            className={`study-subject-list${page.path === "/classes" ? " study-class-list" : ""}`}
          >
            {page.children.map((path) => {
              const child = educationPage(path)!;
              return (
                <a key={path} href={path} className="study-subject-link">
                  {page.path === "/classes" && (
                    <img
                      src={`/images/discovery/class-${path.slice(7)}.png`}
                      alt=""
                      width={64}
                      height={64}
                      loading="lazy"
                      decoding="async"
                    />
                  )}
                  <strong>{child.title}</strong>
                  {page.path !== "/classes" && (
                    <span>
                      {child.resourceIds.length
                        ? `${child.resourceIds.length} lesson${child.resourceIds.length === 1 ? "" : "s"} to explore`
                        : child.children.length
                          ? `${child.children.length} topics`
                          : "More chapters coming"}
                    </span>
                  )}
                  <ArrowRight aria-hidden="true" />
                </a>
              );
            })}
          </div>
        </section>
      )}
      {!page.sections && !!resources.length && (
        <section className="study-more" id="available-lessons">
          <h2>{page.children.length ? "Lessons & practice" : "Learning path"}</h2>
          <ResourceLinks resources={resources} />
        </section>
      )}
      {!page.sections && hasStudyPreview(page) && (
        <>
          <section className="study-more" id="study-notes">
            <h2>Study notes</h2>
            {resources.map((resource) => (
              <div className="study-note" key={resource.id}>
                {resources.length > 1 && <h3>{resource.lesson.title}</h3>}
                <p>{resource.lesson.whyItWorks}</p>
                <p>
                  <strong>Watch for:</strong> {resource.lesson.commonMistake}
                </p>
              </div>
            ))}
          </section>
          <section className="study-more" id="curriculum">
            <h2>Curriculum</h2>
            <div className="study-curriculum-roadmap">
              {resources.map((resource, index) => (
                <details key={resource.id} open={index === 0}>
                  <summary>
                    {resource.lesson.title}
                    <ChevronDown aria-hidden="true" />
                  </summary>
                  <p>{resource.lesson.summary}</p>
                  <ol>
                    <li>
                      <a href={`${resource.canonicalPath}#key-idea`}>Key idea</a>
                    </li>
                    <li>
                      <a href={`${resource.canonicalPath}#why-it-works`}>Why it works</a>
                    </li>
                    <li>
                      <a href={`${resource.canonicalPath}#worked-example`}>Worked example</a>
                    </li>
                    <li>
                      <a href={`${resource.canonicalPath}#practice`}>Chapter self-check</a>
                    </li>
                  </ol>
                </details>
              ))}
            </div>
          </section>
        </>
      )}
      {!!page.sources.length && !guide && (
        <section className="study-more" id="official-sources">
          <h2>Official sources</h2>
          <ul>
            {page.sources.map((source) => (
              <li key={source.path}>
                <a href={source.path} target="_blank" rel="noopener noreferrer">
                  {source.title} <span aria-label="opens in a new tab">↗</span>
                </a>
              </li>
            ))}
          </ul>
        </section>
      )}
      {showStrategy && <StudyStrategy subject={subject ?? ""} />}
    </>
  );
}

function CatalogSearch({ query, grade }: { query: string; grade: string }) {
  const terms = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
  const results = RESOURCES.filter(
    (r) =>
      (!grade || String(r.lesson.grade) === grade) &&
      terms.every((term) =>
        `${r.lesson.title} ${r.lesson.subject} ${r.lesson.subject === "Mathematics" ? "maths math" : ""} class ${r.lesson.grade} ${r.lesson.summary}`
          .toLowerCase()
          .includes(term),
      ),
  );
  const collections =
    query.trim() && !grade
      ? EDUCATION_PAGES.filter(
          (p) =>
            !p.resourceId &&
            p.family !== "utility" &&
            terms.every((term) => p.title.toLowerCase().includes(term)),
        )
      : [];
  return (
    <>
      <form className="study-search-form" action="/search" role="search">
        <label className="sr-only" htmlFor="catalog-query">
          Search catalog
        </label>
        <Search aria-hidden="true" />
        <input
          id="catalog-query"
          name="q"
          defaultValue={query}
          placeholder="Class, subject, exam or topic"
          maxLength={120}
        />
        <label className="sr-only" htmlFor="catalog-grade">
          Class
        </label>
        <select id="catalog-grade" name="grade" defaultValue={grade}>
          <option value="">All classes</option>
          {GRADES_FOR_FILTER.map((g) => (
            <option key={g} value={g}>
              Class {g}
            </option>
          ))}
        </select>
        <button type="submit" aria-label="Search catalog">
          <Search aria-hidden="true" />
        </button>
      </form>
      <p role="status">
        {results.length} lessons · {collections.length} matching collections
      </p>
      <ResourceLinks resources={results} />
      {!!collections.length && (
        <section className="study-more">
          <h2>Collections</h2>
          <ul>
            {collections.map((p) => (
              <li key={p.path}>
                <a href={p.path}>{p.title}</a>
              </li>
            ))}
          </ul>
        </section>
      )}
      {!results.length && !collections.length && (
        <p className="study-intro">No matches. Try a subject, class or shorter topic name.</p>
      )}
    </>
  );
}

function MyStudy() {
  const progress = useLearningProgress();
  const [view, setView] = useState<"saved" | "recent" | "mistakes">("saved");
  const resources =
    view === "mistakes"
      ? RESOURCES.filter((r) =>
          r.lesson.questions.some((q, i) => {
            const answer = progress.answers[`${r.id}@${r.version}`]?.[i];
            return answer !== undefined && answer !== q.answer;
          }),
        )
      : progress[view].map(resourceById).filter((r): r is LearningResource => !!r);
  return (
    <>
      <p className="study-intro">Saved on this browser only. No account or cross-device sync.</p>
      <div className="education-tabs" role="group" aria-label="Study lists">
        {(["saved", "recent", "mistakes"] as const).map((tab) => (
          <button type="button" aria-pressed={tab === view} key={tab} onClick={() => setView(tab)}>
            {tab === "saved" ? "Saved" : tab === "recent" ? "Recently opened" : "Mistake review"}
          </button>
        ))}
      </div>
      <ResourceLinks resources={resources} />
      {!resources.length && (
        <p className="study-intro">
          {view === "mistakes" ? "No incorrect answers to review." : "Your list is empty."}{" "}
          <a href="/classes">Browse lessons</a>
        </p>
      )}
    </>
  );
}

function Lesson({ resource }: { resource: LearningResource }) {
  const { lesson } = resource;
  const progress = useLearningProgress();
  const key = `${resource.id}@${resource.version}`;
  const answers = progress.answers[key] ?? {};
  const [notice, setNotice] = useState("");
  const [fallbackAnswers, setFallbackAnswers] = useState<Record<number, number> | null>(null);
  const activeAnswers = fallbackAnswers ?? answers;
  const saved = progress.saved.includes(resource.id);
  useEffect(() => {
    updateProgress((p) => ({
      ...p,
      recent: [resource.id, ...p.recent.filter((id) => id !== resource.id)].slice(0, 30),
    }));
  }, [resource.id]);
  function answer(index: number, choice: number) {
    const next = { ...activeAnswers, [index]: choice };
    if (!updateProgress((p) => ({ ...p, answers: { ...p.answers, [key]: next } }))) {
      setFallbackAnswers(next);
      setNotice("Browser storage is unavailable. Answers will last only while this page is open.");
    }
  }
  return (
    <article className="study-lesson">
      <p className="study-subject-label">
        Class {lesson.grade} · {lesson.subject} · English
      </p>
      <h1>{lesson.title}</h1>
      <p className="study-intro">{lesson.summary}</p>
      <section id="book" className="study-book-source">
        <h2>Book</h2>
        <p>
          This lesson is ours, not copied from a textbook. We have not checked which book edition it
          matches yet, so compare it with the chapter your teacher uses.
        </p>
        <p>
          <a href={`/ncert/class-${lesson.grade}/books`}>Browse Class {lesson.grade} NCERT books</a>
          {" · "}
          <a href="https://ncert.nic.in/textbook.php" target="_blank" rel="noopener noreferrer">
            Official NCERT textbook portal <span aria-label="opens in a new tab">↗</span>
          </a>
        </p>
      </section>
      <StudyStrategy lesson />
      <div className="education-actions">
        <button
          type="button"
          className="education-icon"
          aria-label={saved ? "Remove saved lesson" : "Save lesson"}
          title={saved ? "Remove saved lesson" : "Save lesson"}
          aria-pressed={saved}
          onClick={() => {
            const ok = updateProgress((p) => ({
              ...p,
              saved: saved ? p.saved.filter((id) => id !== resource.id) : [...p.saved, resource.id],
            }));
            setNotice(
              ok
                ? saved
                  ? "Lesson removed from My Study."
                  : "Lesson saved to My Study."
                : "Browser storage is unavailable. This lesson could not be saved.",
            );
          }}
        >
          <Bookmark aria-hidden="true" fill={saved ? "currentColor" : "none"} />
        </button>
        <a href="/my-study">My Study</a>
      </div>
      {notice && <p role="status">{notice}</p>}
      <p className="study-intro">
        Original Dekhoexams lesson ·{" "}
        {resource.status === "preview" ? "Academic review pending" : "Reviewed lesson"}
      </p>
      <section id="key-idea">
        <h2>Key idea</h2>
        <p>{lesson.keyIdea}</p>
      </section>
      <section id="why-it-works">
        <h2>Why it works</h2>
        <p>{lesson.whyItWorks}</p>
      </section>
      <section id="worked-example">
        <h2>Worked example</h2>
        <p>
          <strong>{lesson.example}</strong>
        </p>
        <ol>
          {lesson.steps.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>
        <p className="study-check">
          <CheckCircle2 aria-hidden="true" />
          {lesson.check}
        </p>
      </section>
      <section id="common-mistakes">
        <h2>Common mistakes</h2>
        <p>{lesson.commonMistake}</p>
      </section>
      <section id="practice">
        <h2>Chapter self-check</h2>
        {lesson.questions.map((question, index) => (
          <fieldset className="study-question" key={index}>
            <legend>
              {index + 1}. {question.prompt}
            </legend>
            <div className="study-choices">
              {question.choices.map((choice, i) => (
                <label
                  key={i}
                  data-result={
                    activeAnswers[index] === undefined
                      ? undefined
                      : i === question.answer
                        ? "correct"
                        : activeAnswers[index] === i
                          ? "incorrect"
                          : undefined
                  }
                >
                  <input
                    type="radio"
                    name={`${key}-${index}`}
                    checked={activeAnswers[index] === i}
                    onChange={() => answer(index, i)}
                  />
                  {choice}
                </label>
              ))}
            </div>
            {activeAnswers[index] !== undefined && (
              <p className="study-feedback" role="status">
                <strong>
                  {activeAnswers[index] === question.answer ? "Correct. " : "Review: "}
                </strong>
                {question.explanation}
              </p>
            )}
          </fieldset>
        ))}
        <p className="study-score" role="status">
          {Object.keys(activeAnswers).length} of {lesson.questions.length} answered ·{" "}
          {lesson.questions.filter((q, i) => activeAnswers[i] === q.answer).length} correct
        </p>
        <button
          className="education-icon"
          type="button"
          title="Reset self-check"
          aria-label="Reset self-check"
          onClick={() => {
            const ok = updateProgress((p) => ({ ...p, answers: { ...p.answers, [key]: {} } }));
            setFallbackAnswers(ok ? null : {});
          }}
        >
          <RotateCcw aria-hidden="true" />
        </button>
      </section>
      <nav className="study-lesson-next" id="continue-learning" aria-label="Continue learning">
        <a href={`/class-${lesson.grade}`}>Class {lesson.grade}</a>
        <a href="/tests">More self-checks</a>
        <a href="/my-study">Saved lessons & mistakes</a>
      </nav>
    </article>
  );
}

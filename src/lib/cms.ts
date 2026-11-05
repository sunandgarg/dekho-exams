import { queryOptions } from "@tanstack/react-query";
import type { Entry, EntryType, Json } from "./content-types";
import { getEntryByPath, listEntries, type ListInput } from "./cms.functions";

export type { Entry, EntryType } from "./content-types";
export type EntryData = {
  [
    K in
      | "questions"
      | "duration_minutes"
      | "steps"
      | "lessons"
      | "batches"
      | "problems"
      | "industry"
      | "role"
      | "expertise"
      | "author_path"
      | "instructor_path"
      | "projects"
      | "transcript"
      | "company_path"
      | "testimonials"
      | "modules"
      | "subject_root"
      | "section_path"
      | "resource_tabs"
      | "visual_demo"
      | "related"
      | "content_format"
      | "kind"
      | "reading_minutes"
      | "companies"
      | "accuracy"
      | "submissions"
      | "points"
      | "starter_code"
      | "editorial"
      | "price"
      | "original_price"
      | "rating"
      | "learners"
      | "duration"
      | "mode"
      | "outcomes"
      | "syllabus"
      | "video_url"
      | "views"
      | "instructor"
      | "starts_at"
      | "ends_at"
      | "location"
      | "register_url"
      | "agenda"
      | "company"
      | "experience"
      | "salary"
      | "job_type"
      | "apply_url"
      | "features"
      | "stats"
      | "cta_label"
      | "cta_url"
  ]?: Json | undefined;
} & Record<string, Json | undefined>;

export const normalizePath = (path: string) => path.replace(/^\/+|\/+$/g, "").toLowerCase();

export const entryQuery = (path: string) =>
  queryOptions({
    queryKey: ["entry", normalizePath(path)],
    queryFn: () => getEntryByPath({ data: { path: normalizePath(path) } }),
  });

export const listQuery = (input: ListInput) =>
  queryOptions({ queryKey: ["entries", input], queryFn: () => listEntries({ data: input }) });

export const str = (v: Json | undefined, fallback = "") =>
  typeof v === "string" ? v : typeof v === "number" ? String(v) : fallback;
export const arr = <T = Json>(v: Json | undefined): T[] => (Array.isArray(v) ? (v as T[]) : []);
export const obj = (v: Json | undefined): EntryData =>
  v && typeof v === "object" && !Array.isArray(v) ? (v as EntryData) : {};

/** Template families, labels and URL prefixes — used by the public site and the admin. */
export const TYPE_META: Record<
  EntryType,
  { label: string; plural: string; prefix: string; example: string }
> = {
  subject: {
    label: "Subject hub",
    plural: "Subject hubs",
    prefix: "",
    example: "python/python-programming-language-tutorial",
  },
  article: {
    label: "Article / lesson",
    plural: "Articles",
    prefix: "",
    example: "python/python-functions",
  },
  category: {
    label: "Category archive",
    plural: "Categories",
    prefix: "category/",
    example: "category/blogs",
  },
  problem: {
    label: "Practice problem",
    plural: "Problems",
    prefix: "problems/",
    example: "problems/two-sum/1",
  },
  course: {
    label: "Course",
    plural: "Courses",
    prefix: "courses/",
    example: "courses/python-for-beginners",
  },
  video: { label: "Video", plural: "Videos", prefix: "videos/", example: "videos/merge-sort" },
  event: {
    label: "Event / campaign",
    plural: "Events",
    prefix: "event/",
    example: "event/build-with-ai",
  },
  job: { label: "Job", plural: "Jobs", prefix: "jobs/", example: "jobs/company-role" },
  business: {
    label: "Business landing page",
    plural: "Business pages",
    prefix: "",
    example: "advertise-with-us",
  },
  quiz: { label: "Quiz", plural: "Quizzes", prefix: "quizzes/", example: "quizzes/python-basics" },
  path: {
    label: "Learning path",
    plural: "Learning paths",
    prefix: "learning-paths/",
    example: "learning-paths/python-foundations",
  },
  company: {
    label: "Company",
    plural: "Companies",
    prefix: "companies/",
    example: "companies/example",
  },
  author: {
    label: "Author",
    plural: "Authors",
    prefix: "authors/",
    example: "authors/aitrove-editorial",
  },
  page: {
    label: "Static page",
    plural: "Static pages",
    prefix: "",
    example: "legal/privacy-policy",
  },
};

export type FieldDef = {
  key: string;
  label: string;
  kind: "text" | "textarea" | "list" | "json" | "url";
  hint?: string;
};

/** Extra, template-specific fields stored in `entries.data`. */
export const DATA_FIELDS: Record<EntryType, FieldDef[]> = {
  subject: [
    {
      key: "modules",
      label: "Curriculum modules",
      kind: "json",
      hint: 'e.g. [{"title":"Basics","lessons":["python/python-variables"]}]',
    },
  ],
  article: [
    {
      key: "kind",
      label: "Article kind",
      kind: "text",
      hint: "concept, algorithm, comparison, interview, notes, project, blog",
    },
    { key: "reading_minutes", label: "Reading time (minutes)", kind: "text" },
  ],
  category: [],
  problem: [
    { key: "companies", label: "Companies", kind: "list", hint: "One per line" },
    { key: "accuracy", label: "Accuracy", kind: "text" },
    { key: "submissions", label: "Submissions", kind: "text" },
    { key: "points", label: "Points", kind: "text" },
    { key: "starter_code", label: "Starter code", kind: "textarea" },
    { key: "editorial", label: "Editorial", kind: "textarea" },
  ],
  course: [
    { key: "price", label: "Price", kind: "text" },
    { key: "original_price", label: "Original price", kind: "text" },
    { key: "rating", label: "Rating", kind: "text" },
    { key: "learners", label: "Learners", kind: "text" },
    { key: "duration", label: "Duration", kind: "text" },
    { key: "mode", label: "Mode", kind: "text", hint: "Live or Self-paced" },
    { key: "outcomes", label: "Outcomes", kind: "list", hint: "One per line" },
    {
      key: "syllabus",
      label: "Syllabus",
      kind: "json",
      hint: '[{"title":"Module","items":["Lesson"]}]',
    },
  ],
  video: [
    { key: "video_url", label: "Video embed URL", kind: "url", hint: "YouTube embed or MP4 link" },
    { key: "duration", label: "Duration", kind: "text" },
    { key: "views", label: "Views", kind: "text" },
    { key: "instructor", label: "Instructor", kind: "text" },
  ],
  event: [
    {
      key: "starts_at",
      label: "Starts at (ISO date)",
      kind: "text",
      hint: "2026-10-18T10:00:00+05:30",
    },
    { key: "ends_at", label: "Ends at (ISO date)", kind: "text" },
    { key: "location", label: "Location", kind: "text" },
    { key: "register_url", label: "Registration link", kind: "url" },
    { key: "agenda", label: "Agenda", kind: "json", hint: '[{"time":"10:00","title":"Kickoff"}]' },
  ],
  job: [
    { key: "company", label: "Company", kind: "text" },
    { key: "location", label: "Location", kind: "text" },
    { key: "experience", label: "Experience", kind: "text" },
    { key: "salary", label: "Salary", kind: "text" },
    { key: "job_type", label: "Job type", kind: "text" },
    { key: "apply_url", label: "Apply link", kind: "url" },
  ],
  business: [
    { key: "features", label: "Features", kind: "json", hint: '[{"title":"...","text":"..."}]' },
    { key: "stats", label: "Stats", kind: "json", hint: '[{"label":"...","value":"..."}]' },
    { key: "cta_label", label: "Button label", kind: "text" },
    { key: "cta_url", label: "Button link", kind: "text" },
  ],
  quiz: [
    {
      key: "questions",
      label: "Questions",
      kind: "json",
      hint: '[{"prompt":"...","options":["A","B"],"answer":0,"explanation":"..."}]',
    },
    { key: "duration_minutes", label: "Time limit (minutes)", kind: "text" },
  ],
  path: [
    {
      key: "steps",
      label: "Ordered steps",
      kind: "json",
      hint: '[{"title":"Lesson","path":"python/python-functions","kind":"Read"}]',
    },
  ],
  company: [
    { key: "company", label: "Company name", kind: "text" },
    { key: "location", label: "Location", kind: "text" },
  ],
  author: [
    { key: "expertise", label: "Expertise", kind: "list" },
    { key: "role", label: "Role", kind: "text" },
  ],
  page: [],
};

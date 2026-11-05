import { FormPrivacyNotice } from "./privacy-controls";
import { FEATURES, isPublicEntryType, isPublicPath } from "@/lib/features";
import { useEffect, useState, type ReactNode } from "react";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "@tanstack/react-router";
import {
  ArrowRight,
  BookOpen,
  Bookmark,
  Check,
  CheckCircle2,
  Clock,
  GraduationCap,
  LockKeyhole,
  Trophy,
  UserRound,
} from "lucide-react";
import { DifficultyBadge } from "./difficulty";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { arr, entryQuery, listQuery, obj, str, type Entry } from "@/lib/cms";
import { usePreview } from "@/lib/preview-state";
import type { ScreenPlan } from "@/lib/surface-routes";
import { Markdown } from "./markdown";
import { ELink, EntryCard, EmptyState, LearningLayout } from "./templates";

function Wrap({ children }: { children: ReactNode }) {
  return <div className="mx-auto max-w-[1240px] px-4 py-8 sm:px-6 md:py-12">{children}</div>;
}
function Intro({ label, title, text }: { label: string; title: string; text?: string }) {
  return (
    <div className="mb-8">
      <p className="text-xs font-bold uppercase tracking-widest text-primary">{label}</p>
      <h1 className="mt-2 font-display text-3xl font-extrabold md:text-4xl">{title}</h1>
      {text && <p className="mt-3 max-w-2xl text-muted-foreground">{text}</p>}
    </div>
  );
}
export function PreviewNotice({ children }: { children: ReactNode }) {
  return (
    <p className="rounded-lg border border-border bg-surface-subtle px-4 py-3 text-sm text-muted-foreground">
      {children}
    </p>
  );
}
export function BookmarkButton({ entry }: { entry: Pick<Entry, "path" | "title" | "type"> }) {
  const { state, update, ready } = usePreview();
  const saved = state.bookmarks.some((i) => i.path === entry.path);
  return (
    <Button
      variant="outline"
      size="sm"
      disabled={!ready}
      aria-pressed={saved}
      onClick={() =>
        update((p) => ({
          ...p,
          bookmarks: saved
            ? p.bookmarks.filter((i) => i.path !== entry.path)
            : [...p.bookmarks, { path: entry.path, title: entry.title, type: entry.type }],
        }))
      }
    >
      <Bookmark className={`size-4 ${saved ? "fill-current" : ""}`} />
      {saved ? "Saved" : "Save"}
    </Button>
  );
}
export function SurfaceView({ plan }: { plan: ScreenPlan }) {
  if (plan.screen === "account") return <AccountPage view={plan.view ?? "overview"} />;
  if (plan.screen === "auth") return <LearnerAuth view={plan.view ?? "login"} />;
  if (plan.screen === "site-map") return <PageDirectory />;
  return <ResourceScreen plan={plan} />;
}
function ResourceScreen({ plan }: { plan: ScreenPlan }) {
  const { data: entry } = useSuspenseQuery(entryQuery(plan.source ?? ""));
  if (!entry)
    return (
      <Wrap>
        <EmptyState title="Resource not found" text="This resource has not been published." />
      </Wrap>
    );
  switch (plan.screen) {
    case "quiz-attempt":
    case "quiz-result":
      return (
        <QuizWorkspace
          key={plan.screen + entry.path}
          entry={entry}
          result={plan.screen === "quiz-result"}
        />
      );
    case "checkout":
      return <Checkout entry={entry} />;
    case "lesson":
    case "assignment":
      return (
        <CourseWorkspace
          entry={entry}
          index={plan.index ?? 1}
          assignment={plan.screen === "assignment"}
        />
      );
    case "contest":
    case "leaderboard":
      return <ContestWorkspace entry={entry} leaderboard={plan.screen === "leaderboard"} />;
    case "application":
      return <Application entry={entry} />;
    default:
      return null;
  }
}

type Question = { prompt: string; options: string[]; answer: number; explanation: string };
function questions(entry: Entry): Question[] {
  return arr<Question>(obj(entry.data).questions).filter(
    (q) =>
      q &&
      typeof q.prompt === "string" &&
      Array.isArray(q.options) &&
      q.options.every((option) => typeof option === "string") &&
      q.options.length > 1 &&
      Number.isInteger(q.answer) &&
      q.answer >= 0 &&
      q.answer < q.options.length,
  );
}
export function QuizLanding({ entry }: { entry: Entry }) {
  const qs = questions(entry);
  const d = obj(entry.data);
  return (
    <LearningLayout key={entry.path} entry={entry}>
      <nav aria-label="Breadcrumb" className="text-xs text-muted-foreground">
        <ELink to="">Home</ELink>
        {" / "}
        <ELink to={str(d.section_path, "quizzes")}>Quizzes</ELink>
        {" / "}
        <span>{entry.title}</span>
      </nav>
      <h1 className="mt-4 text-balance font-display text-3xl font-extrabold [overflow-wrap:anywhere] md:text-4xl">
        {entry.title}
      </h1>
      <div className="my-5 flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
        <Badge variant="outline">Knowledge check</Badge>
        <span>{qs.length} questions</span>
        <span className="inline-flex items-center gap-1">
          <Clock className="size-4" aria-hidden="true" />
          {str(d.duration_minutes, "10")} minutes
        </span>
        <BookmarkButton entry={entry} />
      </div>
      <Markdown source={entry.body || `<p>${entry.summary}</p>`} />
      <section className="quiz-start-panel mt-8" aria-labelledby="start-quiz">
        <h2 id="start-quiz" className="font-display text-xl font-bold">
          Start this quiz
        </h2>
        <p className="mt-3 text-sm leading-6 text-muted-foreground">
          Choose one answer per question. Finish to see every explanation and the concepts to
          review. Your result stays in this browser.
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          {qs.length > 0 && (
            <Button asChild className="min-h-11">
              <ELink to={`${entry.path}/attempt`}>
                Start quiz
                <ArrowRight className="size-4" aria-hidden="true" />
              </ELink>
            </Button>
          )}
          <Button variant="outline" asChild className="min-h-11">
            <ELink to={`${entry.path}/result`}>Previous result</ELink>
          </Button>
        </div>
      </section>
    </LearningLayout>
  );
}
function QuizWorkspace({ entry, result }: { entry: Entry; result: boolean }) {
  const qs = questions(entry);
  const { state, update, ready } = usePreview();
  const navigate = useNavigate();
  const [answers, setAnswers] = useState<number[]>(() => qs.map(() => -1));
  const [current, setCurrent] = useState(0);
  const totalSeconds = Math.max(
    60,
    Number(str(obj(entry.data).duration_minutes, "10")) * 60 || 600,
  );
  const [seconds, setSeconds] = useState(totalSeconds);
  useEffect(() => {
    if (result) return;
    const timer = window.setInterval(() => setSeconds((p) => Math.max(0, p - 1)), 1000);
    return () => window.clearInterval(timer);
  }, [result]);
  const stored = state.quizzes[entry.path];
  function finish() {
    update((p) => ({
      ...p,
      quizzes: { ...p.quizzes, [entry.path]: { answers, submittedAt: new Date().toISOString() } },
    }));
    navigate({ to: "/$", params: { _splat: entry.path + "/result" }, search: {} });
  }
  if (!qs.length)
    return (
      <Wrap>
        <EmptyState
          title="Quiz not ready"
          text="Publish valid questions in WordPress to enable this quiz."
        />
      </Wrap>
    );
  if (result) {
    if (!ready)
      return (
        <Wrap>
          <p>Loading your local result…</p>
        </Wrap>
      );
    if (!stored)
      return (
        <Wrap>
          <Intro label="Quiz result" title={entry.title} />
          <EmptyState
            title="No attempt yet"
            text="Complete the quiz to see your score and answer review."
            action={
              <Button asChild>
                <ELink to={`${entry.path}/attempt`}>Start quiz</ELink>
              </Button>
            }
          />
        </Wrap>
      );
    const correct = qs.filter((q, i) => q.answer === stored.answers[i]).length;
    return (
      <Wrap>
        <Intro label="Your result" title={entry.title} />
        <div className="mb-8 flex flex-wrap items-center gap-6 rounded-xl border bg-course-hero p-6">
          <Trophy className="size-12 text-primary" />
          <div>
            <p className="font-display text-3xl font-extrabold">
              {correct} / {qs.length}
            </p>
            <p className="text-sm text-muted-foreground">
              {Math.round((correct / qs.length) * 100)}% correct · local practice result
            </p>
          </div>
          <Button variant="outline" asChild>
            <ELink to={`${entry.path}/attempt`}>Try again</ELink>
          </Button>
        </div>
        <h2 className="mb-4 font-display text-xl font-bold">Answer review</h2>
        <div className="grid gap-4">
          {qs.map((q, i) => (
            <section key={i} className="rounded-lg border bg-card p-5">
              <div className="flex gap-3">
                <Badge variant={stored.answers[i] === q.answer ? "default" : "secondary"}>
                  {i + 1}
                </Badge>
                <h3 className="font-bold">{q.prompt}</h3>
              </div>
              <p className="mt-3 text-sm">
                Your answer: {q.options[stored.answers[i] ?? -1] ?? "Not answered"}
              </p>
              <p className="mt-1 text-sm font-semibold text-primary">
                Correct answer: {q.options[q.answer]}
              </p>
              <p className="mt-3 text-sm text-muted-foreground">{q.explanation}</p>
            </section>
          ))}
        </div>
      </Wrap>
    );
  }
  const q = qs[current]!;
  const answered = answers.filter((a) => a >= 0).length;
  return (
    <Wrap>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <Intro label="Quiz attempt" title={entry.title} />
        <Badge variant="outline">
          <Clock className="mr-2 size-4" />
          {Math.floor(seconds / 60)}:{String(seconds % 60).padStart(2, "0")}
        </Badge>
      </div>
      <div className="grid gap-6 lg:grid-cols-[1fr_260px]">
        <section className="rounded-xl border bg-card p-6">
          <p className="text-xs text-muted-foreground">
            Question {current + 1} of {qs.length}
          </p>
          <h2 className="mt-3 font-display text-xl font-bold">{q.prompt}</h2>
          <fieldset className="mt-6 grid gap-3" disabled={seconds === 0}>
            <legend className="sr-only">Choose an answer</legend>
            {q.options.map((option, i) => (
              <label
                key={i}
                className={`flex cursor-pointer items-center gap-3 rounded-lg border p-4 ${answers[current] === i ? "border-primary bg-primary-soft" : "hover:bg-accent"}`}
              >
                <input
                  type="radio"
                  name={"question-" + current}
                  value={i}
                  checked={answers[current] === i}
                  onChange={() => setAnswers((p) => p.map((a, n) => (n === current ? i : a)))}
                  className="accent-primary"
                />
                <span>{option}</span>
              </label>
            ))}
          </fieldset>
          {seconds === 0 && (
            <p role="status" className="mt-4 text-sm">
              Time is up. Submit to review your answers.
            </p>
          )}
          <div className="mt-6 flex justify-between">
            <Button
              variant="outline"
              disabled={current === 0}
              onClick={() => setCurrent((p) => p - 1)}
            >
              Previous
            </Button>
            {current < qs.length - 1 ? (
              <Button onClick={() => setCurrent((p) => p + 1)}>Next</Button>
            ) : (
              <Button onClick={finish}>Finish & review</Button>
            )}
          </div>
        </section>
        <aside className="h-fit rounded-xl border p-5">
          <p className="text-sm font-semibold">
            {answered} of {qs.length} answered
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            {qs.map((_, i) => (
              <Button
                key={i}
                size="icon"
                variant={i === current ? "default" : "outline"}
                aria-label={`Go to question ${i + 1}`}
                onClick={() => setCurrent(i)}
              >
                {answers[i]! >= 0 ? <Check className="size-4" /> : i + 1}
              </Button>
            ))}
          </div>
          <Button className="mt-6 w-full" variant="outline" onClick={finish}>
            Submit attempt
          </Button>
          <p className="mt-3 text-xs text-muted-foreground">
            Unanswered questions count as incorrect.
          </p>
        </aside>
      </div>
    </Wrap>
  );
}

export function LearningPath({ entry, tab }: { entry: Entry; tab?: string | undefined }) {
  const steps = arr<{ title: string; path: string; kind: string }>(obj(entry.data).steps);
  const { state, update, ready } = usePreview();
  const complete = steps.filter((s) => state.completed.includes(s.path)).length;
  return (
    <Wrap>
      <Intro label="Guided learning" title={entry.title} text={entry.summary} />
      <div className="mb-8 flex items-center gap-4 rounded-xl border bg-course-hero p-5">
        <GraduationCap className="size-8 text-primary" />
        <div className="flex-1">
          <p className="text-sm font-semibold">
            {complete} of {steps.length} steps completed
          </p>
          <progress
            value={complete}
            max={steps.length || 1}
            className="mt-2 h-2 w-full accent-primary"
          />
        </div>
        <span className="text-xs text-muted-foreground">Local progress</span>
      </div>
      <Tabs defaultValue={tab?.toLowerCase() === "resources" ? "resources" : "path"}>
        <TabsList>
          <TabsTrigger value="path">Learning path</TabsTrigger>
          <TabsTrigger value="resources">Resources</TabsTrigger>
          <TabsTrigger value="about">About</TabsTrigger>
        </TabsList>
        <TabsContent value="path" className="mt-6">
          <ol className="grid gap-4">
            {steps.map((s, i) => (
              <li
                key={s.path}
                className="flex flex-wrap items-center gap-4 rounded-lg border bg-card p-5"
              >
                <span className="grid size-10 place-items-center rounded-full bg-primary-soft font-bold text-primary">
                  {state.completed.includes(s.path) ? <Check /> : i + 1}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-xs text-muted-foreground">{s.kind}</p>
                  <ELink to={s.path} className="font-semibold hover:text-primary">
                    {s.title}
                  </ELink>
                </div>
                <Button
                  size="sm"
                  disabled={!ready}
                  variant="outline"
                  aria-pressed={state.completed.includes(s.path)}
                  onClick={() =>
                    update((p) => ({
                      ...p,
                      completed: p.completed.includes(s.path)
                        ? p.completed.filter((x) => x !== s.path)
                        : [...p.completed, s.path],
                    }))
                  }
                >
                  {state.completed.includes(s.path) ? "Undo" : "Mark complete"}
                </Button>
              </li>
            ))}
          </ol>
        </TabsContent>
        <TabsContent value="resources" className="mt-6">
          <div className="grid gap-3 sm:grid-cols-2">
            {steps.map((s) => (
              <ELink
                key={s.path}
                to={s.path}
                className="rounded-lg border p-5 hover:border-primary"
              >
                <Badge variant="secondary">{s.kind}</Badge>
                <h2 className="mt-3 font-bold">{s.title}</h2>
              </ELink>
            ))}
          </div>
        </TabsContent>
        <TabsContent value="about" className="mt-6">
          <Markdown source={entry.body} />
        </TabsContent>
      </Tabs>
    </Wrap>
  );
}

type Lesson = { title: string; module: string; body: string };
function courseLessons(entry: Entry): Lesson[] {
  const explicit = arr<Lesson>(obj(entry.data).lessons);
  if (explicit.length) return explicit;
  return arr<{ title: string; items: string[] }>(obj(entry.data).syllabus).flatMap((m) =>
    (m.items ?? []).map((title) => ({
      title,
      module: m.title,
      body: `## ${title}\n\nThis is the lesson preview for ${title}. Publish the full lesson body through this course's lessons field in WordPress.\n\n## Learning exercise\n\nExplain the concept in your own words, create a small example and verify its behavior.`,
    })),
  );
}
function Checkout({ entry }: { entry: Entry }) {
  const d = obj(entry.data);
  const [batch, setBatch] = useState("");
  const [notice, setNotice] = useState("");
  const batches = arr<{ title: string; schedule: string }>(d.batches);
  return (
    <Wrap>
      <Intro
        label="Enrollment"
        title="Course checkout"
        text="Review your course and preferred batch."
      />
      <div className="grid gap-8 lg:grid-cols-[1fr_360px]">
        <form
          className="grid content-start gap-5 rounded-xl border p-6"
          onSubmit={(e) => {
            e.preventDefault();
            setNotice(
              "Checkout is not connected to a payment service. No order was placed and no payment was taken.",
            );
          }}
        >
          <h2 className="font-display text-xl font-bold">Your details</h2>
          <Field label="Full name" autoComplete="name" required />
          <Field label="Email address" type="email" autoComplete="email" required />
          <label className="grid gap-2 text-sm font-semibold">
            Preferred batch
            <select
              required
              value={batch}
              onChange={(e) => setBatch(e.target.value)}
              className="h-11 rounded-md border bg-background px-3"
            >
              <option value="">Choose a batch</option>
              {batches.map((b, i) => (
                <option key={i} value={b.title}>
                  {b.title} · {b.schedule}
                </option>
              ))}
            </select>
          </label>
          <label className="flex items-start gap-3 text-sm">
            <input type="checkbox" required className="mt-1 accent-primary" />
            <span>I understand this is a checkout preview and enrollment is not open.</span>
          </label>
          <Button type="submit">Check enrollment availability</Button>
          {notice && <PreviewNotice>{notice}</PreviewNotice>}
        </form>
        <aside className="h-fit rounded-xl border bg-course-hero p-6">
          <Badge variant="secondary">Order summary</Badge>
          <h2 className="mt-4 font-display text-xl font-bold">{entry.title}</h2>
          <p className="mt-3 text-sm text-muted-foreground">
            {str(d.mode)} · {str(d.duration)}
          </p>
          <p className="mt-6 font-display text-3xl font-extrabold">{str(d.price, "Free")}</p>
          <p className="mt-2 text-xs text-muted-foreground">
            Preview price; final pricing and taxes must be configured before launch.
          </p>
          <Button className="mt-6 w-full" variant="outline" asChild>
            <ELink to={`learn/${entry.path.replace(/^courses\//, "")}/lesson/1`}>
              Preview a lesson
            </ELink>
          </Button>
          <ELink to={entry.path} className="mt-4 block text-center text-sm text-primary">
            Back to course details
          </ELink>
        </aside>
      </div>
    </Wrap>
  );
}
function CourseWorkspace({
  entry,
  index,
  assignment,
}: {
  entry: Entry;
  index: number;
  assignment: boolean;
}) {
  const lessons = courseLessons(entry);
  const lesson = lessons[index - 1];
  const slug = entry.path.replace(/^courses\//, "");
  const { state, update, ready } = usePreview();
  const path = `learn/${slug}/lesson/${index}`;
  const [submission, setSubmission] = useState("");
  const [notice, setNotice] = useState("");
  useEffect(() => setSubmission(state.drafts[path] ?? ""), [state.drafts, path]);
  if (!lesson)
    return (
      <Wrap>
        <EmptyState
          title="Lesson not found"
          text="This lesson has not been added to the course curriculum."
        />
      </Wrap>
    );
  return (
    <div className="mx-auto grid max-w-[1440px] lg:grid-cols-[300px_minmax(0,1fr)]">
      <aside className="border-r bg-surface-subtle p-5">
        <ELink to={entry.path} className="font-display font-bold hover:text-primary">
          {entry.title}
        </ELink>
        <p className="mt-2 text-xs text-muted-foreground">
          Course preview · progress stays in this browser
        </p>
        <ol className="mt-6 grid gap-2">
          {lessons.map((l, i) => (
            <li key={i}>
              <ELink
                to={`learn/${slug}/lesson/${i + 1}`}
                className={`flex gap-3 rounded-md px-3 py-3 text-sm ${i + 1 === index ? "bg-primary-soft font-bold text-primary" : "hover:bg-accent"}`}
              >
                <span>
                  {state.completed.includes(`learn/${slug}/lesson/${i + 1}`) ? (
                    <CheckCircle2 className="size-4" />
                  ) : (
                    i + 1
                  )}
                </span>
                {l.title}
              </ELink>
            </li>
          ))}
        </ol>
        <ELink
          to={`learn/${slug}/assignment/${index}`}
          className="mt-4 block rounded-lg border p-3 text-sm font-semibold"
        >
          Lesson assignment
        </ELink>
        <ELink to="account/courses" className="mt-4 block text-sm text-primary">
          My courses
        </ELink>
      </aside>
      <article className="min-w-0 px-4 py-8 sm:px-8 lg:px-12">
        <Intro
          label={assignment ? "Assignment" : lesson.module}
          title={assignment ? `${lesson.title}: assignment` : lesson.title}
        />
        <PreviewNotice>
          This is an open lesson preview. Enrollment, private course access and grading are not
          connected.
        </PreviewNotice>
        <div className="mt-6">
          <Markdown source={lesson.body} />
        </div>
        {assignment ? (
          <form
            className="mt-8 grid gap-4"
            onSubmit={(e) => {
              e.preventDefault();
              update((p) => ({ ...p, drafts: { ...p.drafts, [path]: submission } }));
              setNotice("Draft saved in this browser. It has not been submitted for grading.");
            }}
          >
            <label className="grid gap-2 text-sm font-semibold">
              Your solution or notes
              <Textarea
                required
                rows={8}
                value={submission}
                onChange={(e) => setSubmission(e.target.value)}
              />
            </label>
            <Button type="submit" disabled={!ready} className="w-fit">
              Save assignment draft
            </Button>
            {notice && (
              <p role="status" className="text-sm text-primary">
                {notice}
              </p>
            )}
          </form>
        ) : (
          <div className="mt-8 flex flex-wrap gap-3">
            <Button
              disabled={!ready}
              onClick={() =>
                update((p) => ({
                  ...p,
                  completed: p.completed.includes(path) ? p.completed : [...p.completed, path],
                }))
              }
            >
              {state.completed.includes(path) ? "Completed" : "Mark lesson complete"}
            </Button>
            <Button variant="outline" asChild>
              <ELink to={`learn/${slug}/assignment/${index}`}>Try assignment</ELink>
            </Button>
          </div>
        )}
        <nav className="mt-12 flex justify-between border-t pt-6">
          {index > 1 ? (
            <ELink to={`learn/${slug}/lesson/${index - 1}`} className="text-sm text-primary">
              ← Previous lesson
            </ELink>
          ) : (
            <span />
          )}
          {index < lessons.length && (
            <ELink to={`learn/${slug}/lesson/${index + 1}`} className="text-sm text-primary">
              Next lesson →
            </ELink>
          )}
        </nav>
      </article>
    </div>
  );
}

function ContestWorkspace({ entry, leaderboard }: { entry: Entry; leaderboard: boolean }) {
  const d = obj(entry.data);
  const paths = arr<string>(d.problems);
  const { data } = useSuspenseQuery(
    listQuery({ type: "problem", ...(paths.length ? { paths } : {}), limit: 12 }),
  );
  return (
    <Wrap>
      <Intro
        label="Events & contests"
        title={leaderboard ? `${entry.title}: leaderboard` : entry.title}
        text={entry.summary}
      />
      <nav className="mb-6 flex flex-wrap gap-3">
        <Button variant="outline" asChild>
          <ELink to={entry.path}>Overview</ELink>
        </Button>
        <Button variant={leaderboard ? "outline" : "default"} asChild>
          <ELink to={`${entry.path}/participate`}>Practice workspace</ELink>
        </Button>
        <Button variant={leaderboard ? "default" : "outline"} asChild>
          <ELink to={`${entry.path}/leaderboard`}>Leaderboard</ELink>
        </Button>
      </nav>
      <PreviewNotice>
        Contest registration and scoring are not connected. These problems are available for
        practice; attempts do not create a contest rank.
      </PreviewNotice>
      {leaderboard ? (
        <div className="mt-8 overflow-x-auto rounded-xl border">
          <table className="w-full text-sm">
            <thead className="bg-surface-subtle text-left">
              <tr>
                {["Rank", "Participant", "Solved", "Score", "Time"].map((h) => (
                  <th key={h} className="p-4">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr>
                <td colSpan={5} className="p-12 text-center text-muted-foreground">
                  No ranked submissions yet.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      ) : (
        <div className="mt-8 grid gap-6 lg:grid-cols-[1fr_300px]">
          <div className="grid gap-3">
            {data.items.map((p, i) => (
              <ELink
                key={p.path}
                to={p.path}
                className="flex items-center justify-between gap-4 rounded-lg border p-5 hover:border-primary"
              >
                <span>
                  <span className="text-xs text-muted-foreground">Problem {i + 1}</span>
                  <span className="mt-1 block font-bold">{p.title}</span>
                </span>
                <DifficultyBadge value={p.difficulty} />
              </ELink>
            ))}
          </div>
          <aside className="h-fit rounded-lg border p-5">
            <h2 className="font-bold">Practice rules</h2>
            <ul className="mt-4 grid gap-3 text-sm text-muted-foreground">
              <li>Read the input and output requirements.</li>
              <li>Write and test your solution locally.</li>
              <li>Review the editorial after your attempt.</li>
            </ul>
            <p className="mt-5 text-xs text-muted-foreground">Online code judging is pending.</p>
          </aside>
        </div>
      )}
    </Wrap>
  );
}
export function CompanyProfile({ entry }: { entry: Entry }) {
  const [page, setPage] = useState(0);
  const d = obj(entry.data);
  const { data } = useSuspenseQuery(
    listQuery({ type: "job", company: str(d.company, entry.title), limit: 12, offset: page * 12 }),
  );
  return (
    <Wrap>
      <Intro label="Company profile" title={entry.title} text={entry.summary} />
      <div className="mb-8 flex gap-3">
        {[str(d.industry), str(d.location)].filter(Boolean).map((x) => (
          <Badge key={x} variant="outline">
            {x}
          </Badge>
        ))}
      </div>
      <Markdown source={entry.body} />
      <h2 className="mt-10 font-display text-2xl font-bold">Open positions</h2>
      <div className="mt-5 grid gap-4 md:grid-cols-2">
        {data.items.map((j) => (
          <EntryCard key={j.path} item={j} />
        ))}
        {!data.items.length && (
          <p className="text-muted-foreground">No open positions published.</p>
        )}
      </div>
      <LocalPager page={page} total={data.total} size={12} onChange={setPage} />
    </Wrap>
  );
}
export function AuthorProfile({ entry }: { entry: Entry }) {
  const [page, setPage] = useState(0);
  const { data } = useSuspenseQuery(
    listQuery({ type: "article", author: entry.path, limit: 24, offset: page * 24 }),
  );
  const d = obj(entry.data);
  return (
    <Wrap>
      <div className="mb-8 flex flex-wrap items-center gap-6">
        <div className="grid size-24 place-items-center rounded-full bg-primary-soft">
          <UserRound className="size-12 text-primary" />
        </div>
        <div>
          <Intro label={str(d.role, "Contributor")} title={entry.title} text={entry.summary} />
          <div className="flex flex-wrap gap-2">
            {arr<string>(d.expertise).map((x) => (
              <Badge key={x} variant="secondary">
                {x}
              </Badge>
            ))}
          </div>
        </div>
      </div>
      <Markdown source={entry.body} />
      <h2 className="mt-10 font-display text-2xl font-bold">Published resources</h2>
      <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {data.items.map((a) => (
          <EntryCard key={a.path} item={a} />
        ))}
      </div>
      <LocalPager page={page} total={data.total} size={24} onChange={setPage} />
    </Wrap>
  );
}
function LocalPager({
  page,
  total,
  size,
  onChange,
}: {
  page: number;
  total: number;
  size: number;
  onChange: (page: number) => void;
}) {
  const count = Math.ceil(total / size);
  if (count <= 1) return null;
  return (
    <nav aria-label="Pagination" className="mt-8 flex items-center justify-center gap-3">
      <Button variant="outline" disabled={page === 0} onClick={() => onChange(page - 1)}>
        Previous
      </Button>
      <span className="text-sm">
        Page {page + 1} of {count}
      </span>
      <Button variant="outline" disabled={page + 1 >= count} onClick={() => onChange(page + 1)}>
        Next
      </Button>
    </nav>
  );
}
function Field({ label, ...props }: { label: string } & React.ComponentProps<typeof Input>) {
  return (
    <label className="grid gap-2 text-sm font-semibold">
      {label}
      <Input {...props} className="h-11" />
    </label>
  );
}
export function InquiryForm({ title = "Send an inquiry" }: { title?: string }) {
  const [notice, setNotice] = useState("");
  return (
    <form
      className="mt-8 grid gap-4 rounded-xl border bg-card p-6"
      onSubmit={(e) => {
        e.preventDefault();
        setNotice(
          "The inquiry service is not connected. Your message has not been sent. You can email aitrove@gmail.com directly.",
        );
      }}
    >
      <h2 className="font-display text-xl font-bold">{title}</h2>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Name" required autoComplete="name" />
        <Field label="Email" required type="email" autoComplete="email" />
      </div>
      <Field label="Organization (optional)" autoComplete="organization" />
      <label className="grid gap-2 text-sm font-semibold">
        Message
        <Textarea required minLength={10} rows={5} />
      </label>
      <FormPrivacyNotice />
      <Button type="submit" className="w-fit">
        Check inquiry availability
      </Button>
      <p className="text-xs text-muted-foreground">
        Contact delivery is pending. This form does not send data.
      </p>
      {notice && (
        <p role="status" className="text-sm text-muted-foreground">
          {notice}
        </p>
      )}
    </form>
  );
}
function Application({ entry }: { entry: Entry }) {
  const [notice, setNotice] = useState("");
  const d = obj(entry.data);
  return (
    <Wrap>
      <Intro label={str(d.company, "Careers")} title={`Apply: ${entry.title}`} />
      <div className="grid gap-8 lg:grid-cols-[1fr_320px]">
        <form
          className="grid gap-5 rounded-xl border p-6"
          onSubmit={(e) => {
            e.preventDefault();
            setNotice(
              "The application service is not connected. Your information and résumé have not been sent or saved.",
            );
          }}
        >
          <Field label="Full name" required autoComplete="name" />
          <Field label="Email" required type="email" autoComplete="email" />
          <Field label="Portfolio or LinkedIn URL" type="url" />
          <label className="grid gap-2 text-sm font-semibold">
            Résumé (PDF)
            <Input type="file" accept="application/pdf" required />
          </label>
          <label className="grid gap-2 text-sm font-semibold">
            Cover letter
            <Textarea rows={5} />
          </label>
          <FormPrivacyNotice />
          <Button type="submit">Check application availability</Button>
          {notice && <PreviewNotice>{notice}</PreviewNotice>}
        </form>
        <aside className="h-fit rounded-xl border p-6">
          <h2 className="font-bold">Role summary</h2>
          <p className="mt-3 text-sm text-muted-foreground">{entry.summary}</p>
          <p className="mt-3 text-sm">
            {str(d.location)} · {str(d.job_type)}
          </p>
          <div className="mt-5">
            <BookmarkButton entry={entry} />
          </div>
          {str(d.apply_url) && (
            <Button className="mt-4 w-full" asChild>
              <a href={str(d.apply_url)} target="_blank" rel="noopener noreferrer">
                Apply on company site
              </a>
            </Button>
          )}
          <ELink to={entry.path} className="mt-4 block text-sm text-primary">
            Back to job details
          </ELink>
        </aside>
      </div>
    </Wrap>
  );
}

export function LearnerAuth({ view = "login" }: { view?: string }) {
  const [notice, setNotice] = useState("");
  const signup = view === "signup";
  const forgot = view === "forgot-password" || view === "reset-password";
  return (
    <Wrap>
      <div className="mx-auto max-w-md rounded-2xl border bg-card p-6 shadow-card sm:p-8">
        <LockKeyhole className="size-8 text-primary" />
        <h1 className="mt-4 font-display text-2xl font-extrabold">
          {forgot
            ? "Reset your password"
            : signup
              ? "Create your AITrove account"
              : "Welcome to AITrove"}
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Learner authentication will be enabled when its service is connected.
        </p>
        <form
          className="mt-6 grid gap-4"
          onSubmit={(e) => {
            e.preventDefault();
            setNotice(
              "Learner authentication is not configured. No account was created, signed in or changed. Use the local dashboard to preview learning features.",
            );
          }}
        >
          {signup && <Field label="Full name" required autoComplete="name" />}
          <Field label="Email address" type="email" required autoComplete="email" />
          {!forgot && (
            <Field
              label="Password"
              type="password"
              minLength={8}
              required
              autoComplete={signup ? "new-password" : "current-password"}
            />
          )}
          <p className="text-sm">
            Read our{" "}
            <a href="/legal/privacy-policy" className="underline">
              privacy policy
            </a>{" "}
            and{" "}
            <a href="/legal/terms-and-conditions" className="underline">
              terms
            </a>
            . Do not enter a real password into this preview.
          </p>
          <Button type="submit">
            {forgot
              ? "Check reset availability"
              : signup
                ? "Check signup availability"
                : "Check sign-in availability"}
          </Button>
          {notice && (
            <p role="status" className="text-sm text-muted-foreground">
              {notice}
            </p>
          )}
        </form>
        <div className="mt-5 flex flex-wrap justify-between gap-3 text-sm">
          <ELink to={signup ? "login" : "signup"} className="text-primary">
            {signup ? "Already have an account?" : "Create an account"}
          </ELink>
          <ELink to="forgot-password" className="text-primary">
            Forgot password?
          </ELink>
        </div>
        <div className="mt-6 border-t pt-5">
          <Button className="w-full" variant="outline" asChild>
            <ELink to="account">Explore local dashboard</ELink>
          </Button>
          <p className="mt-3 text-xs text-muted-foreground">
            Editors use the separate WordPress{" "}
            <a href="/admin" className="text-primary underline">
              administration portal
            </a>
            .
          </p>
        </div>
      </div>
    </Wrap>
  );
}
const accountLinks = [
  ["overview", "Overview"],
  ["courses", "My courses"],
  ["bookmarks", "Bookmarks"],
  ["progress", "Learning progress"],
  ["saved-jobs", "Saved jobs"],
  ["applications", "Applications"],
  ["notifications", "Notifications"],
  ["profile", "Profile"],
  ["settings", "Settings"],
] as const;
function AccountPage({ view }: { view: string }) {
  const { state, update, ready } = usePreview();
  const { data: courses } = useSuspenseQuery(listQuery({ type: "course", limit: 12 }));
  const [notice, setNotice] = useState("");
  if (!ready)
    return (
      <Wrap>
        <h1 className="font-display text-2xl font-bold">My learning</h1>
        <p aria-busy="true" className="mt-3">
          Loading local learning data…
        </p>
      </Wrap>
    );
  const visibleBookmarks = state.bookmarks.filter(
    (i) => isPublicEntryType(i.type) && isPublicPath(i.path),
  );
  const completed = state.completed.filter(isPublicPath);
  const items = visibleBookmarks.filter((i) => (view === "saved-jobs" ? i.type === "job" : true));
  return (
    <Wrap>
      <div className="grid gap-8 lg:grid-cols-[220px_minmax(0,1fr)]">
        <aside className="min-w-0">
          <div className="mb-5 flex items-center gap-3">
            <span className="grid size-10 place-items-center rounded-full bg-primary-soft font-bold text-primary">
              {state.settings.displayName.charAt(0)}
            </span>
            <span className="text-sm font-bold">{state.settings.displayName}</span>
          </div>
          <nav aria-label="Learner dashboard" className="flex gap-1 overflow-x-auto lg:grid">
            {accountLinks
              .filter(([key]) => isPublicPath("account/" + key))
              .map(([key, label]) => (
                <ELink
                  key={key}
                  to={"account" + (key === "overview" ? "" : "/" + key)}
                  className={`shrink-0 rounded-md px-3 py-2.5 text-sm ${view === key ? "bg-primary-soft font-bold text-primary" : "text-muted-foreground hover:bg-accent"}`}
                >
                  {label}
                </ELink>
              ))}
          </nav>
        </aside>
        <section className="min-w-0">
          <Intro
            label="My learning"
            title={accountLinks.find(([key]) => key === view)?.[1] ?? "Overview"}
          />
          <PreviewNotice>
            Local preview dashboard. Bookmarks, quiz results and progress stay in this browser. You
            are not signed in to a learner account.
          </PreviewNotice>
          {view === "overview" && (
            <>
              <div className="mt-6 grid gap-4 sm:grid-cols-3">
                {[
                  ["Saved resources", visibleBookmarks.length],
                  ["Completed steps", completed.length],
                  ["Quizzes attempted", Object.keys(state.quizzes).length],
                ].map(([label, value]) => (
                  <div key={label} className="rounded-xl border p-5">
                    <p className="font-display text-3xl font-extrabold text-primary">{value}</p>
                    <p className="mt-1 text-sm text-muted-foreground">{label}</p>
                  </div>
                ))}
              </div>
              <h2 className="mt-8 font-display text-xl font-bold">Continue exploring</h2>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                {[
                  ["Learning paths", "learning-paths"],
                  ["Practice problems", "explore"],
                  ["Knowledge quizzes", "quizzes"],
                  ["Course previews", "account/courses"],
                ]
                  .filter(([, path]) => isPublicPath(path!))
                  .map(([title, path]) => (
                    <ELink
                      key={path}
                      to={path!}
                      className="rounded-lg border p-5 font-bold hover:border-primary"
                    >
                      {title} <ArrowRight className="mt-3 size-4 text-primary" />
                    </ELink>
                  ))}
              </div>
            </>
          )}
          {FEATURES.courses && view === "courses" && (
            <>
              <p className="mt-6 text-sm text-muted-foreground">
                Course previews · no active enrollments
              </p>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                {courses.items.map((c) => (
                  <div key={c.path} className="rounded-xl border bg-card p-5">
                    <h2 className="font-bold">{c.title}</h2>
                    <p className="mt-2 text-sm text-muted-foreground">{c.summary}</p>
                    <Button className="mt-4" variant="outline" asChild>
                      <ELink to={`learn/${c.path.replace(/^courses\//, "")}/lesson/1`}>
                        Preview curriculum
                      </ELink>
                    </Button>
                  </div>
                ))}
              </div>
            </>
          )}
          {(view === "bookmarks" || view === "saved-jobs") && (
            <div className="mt-6 grid gap-3">
              {items.length ? (
                items.map((i) => (
                  <div
                    key={i.path}
                    className="flex items-center justify-between gap-4 rounded-lg border p-4"
                  >
                    <ELink to={i.path} className="font-semibold hover:text-primary">
                      {i.title}
                    </ELink>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() =>
                        update((p) => ({
                          ...p,
                          bookmarks: p.bookmarks.filter((x) => x.path !== i.path),
                        }))
                      }
                    >
                      Remove
                    </Button>
                  </div>
                ))
              ) : (
                <EmptyState
                  title="Nothing saved yet"
                  text="Use the Save button on articles, videos or jobs to keep them here."
                />
              )}
            </div>
          )}
          {view === "progress" && (
            <div className="mt-6 grid gap-6">
              <section>
                <h2 className="font-display text-xl font-bold">Completed lessons & steps</h2>
                {completed.length ? (
                  <ul className="mt-4 grid gap-2">
                    {completed.map((p) => (
                      <li key={p}>
                        <ELink
                          to={p}
                          className="flex items-center gap-2 rounded-lg border p-3 text-sm hover:text-primary"
                        >
                          <CheckCircle2 className="size-4 text-primary" />
                          {p.replace(/[-/]/g, " ")}
                        </ELink>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-3 text-sm text-muted-foreground">
                    Mark a lesson or learning-path step complete to track it here.
                  </p>
                )}
              </section>
              <section>
                <h2 className="font-display text-xl font-bold">Quiz attempts</h2>
                <div className="mt-3 grid gap-2">
                  {Object.keys(state.quizzes).map((p) => (
                    <ELink key={p} to={p + "/result"} className="rounded-lg border p-3 text-sm">
                      {p.replace("quizzes/", "").replace(/-/g, " ")} → Review result
                    </ELink>
                  ))}
                </div>
              </section>
            </div>
          )}
          {view === "notifications" && (
            <div className="mt-6">
              <EmptyState
                title="You're all caught up"
                text="There are no notifications. Event notifications will appear after learner services are connected."
              />
            </div>
          )}
          {view === "applications" && (
            <div className="mt-6">
              <EmptyState
                title="No applications submitted"
                text="Application delivery is not connected. Browse jobs and use an employer's external application link when provided."
                action={
                  <Button asChild>
                    <ELink to="jobs">Browse jobs</ELink>
                  </Button>
                }
              />
            </div>
          )}
          {(view === "settings" || view === "profile") && (
            <form
              className="mt-6 grid max-w-lg gap-5 rounded-xl border p-6"
              onSubmit={(e) => {
                e.preventDefault();
                const values = new FormData(e.currentTarget);
                update((p) => ({
                  ...p,
                  settings: {
                    displayName: String(values.get("displayName") || "Learner"),
                    dailyGoal: Number(values.get("dailyGoal") || 20),
                  },
                }));
                setNotice("Preferences saved in this browser.");
              }}
            >
              <Field
                name="displayName"
                label="Display name"
                required
                maxLength={60}
                defaultValue={state.settings.displayName}
                key={state.settings.displayName}
              />
              <Field
                name="dailyGoal"
                label="Daily learning goal (minutes)"
                type="number"
                min={5}
                max={240}
                defaultValue={state.settings.dailyGoal}
                key={state.settings.dailyGoal}
              />
              <Button type="submit" className="w-fit">
                Save local preferences
              </Button>
              {notice && (
                <p role="status" className="text-sm text-primary">
                  {notice}
                </p>
              )}
              <Button
                type="button"
                variant="outline"
                className="w-fit"
                onClick={() => {
                  if (
                    window.confirm(
                      "Clear local bookmarks, quiz results, lesson progress and assignment drafts?",
                    )
                  ) {
                    update(() => ({
                      bookmarks: [],
                      completed: [],
                      quizzes: {},
                      settings: { displayName: "Learner", dailyGoal: 20 },
                      drafts: {},
                    }));
                    setNotice("Local preview data cleared.");
                  }
                }}
              >
                Clear local preview data
              </Button>
            </form>
          )}
        </section>
      </div>
    </Wrap>
  );
}

const screenLinks = [
  ["Learner sign-in", "login"],
  ["Create account", "signup"],
  ["Password recovery", "forgot-password"],
  ["Learner dashboard", "account"],
  ["My courses", "account/courses"],
  ["Learning progress", "account/progress"],
  ["Bookmarks", "account/bookmarks"],
  ["Saved jobs", "account/saved-jobs"],
  ["Applications", "account/applications"],
  ["Notifications", "account/notifications"],
  ["Profile", "account/profile"],
  ["Settings", "account/settings"],
  ["WordPress editor", "admin"],
];
export function PageDirectory() {
  const [page, setPage] = useState(0);
  const { data } = useSuspenseQuery(listQuery({ limit: 100, offset: page * 200 }));
  const { data: rest } = useSuspenseQuery(listQuery({ limit: 100, offset: page * 200 + 100 }));
  const entries = [...data.items, ...rest.items];
  const families = [
    "subject",
    "article",
    "category",
    "quiz",
    "path",
    "problem",
    "course",
    "video",
    "event",
    "job",
    "company",
    "author",
    "business",
    "page",
  ];
  return (
    <Wrap>
      <Intro
        label="Content directory"
        title="Explore all published resources"
        text="Browse the full collection. Use the page controls to move through every published resource, or search for a specific topic."
      />
      <div className="mb-8 rounded-xl border bg-course-hero p-5">
        <p className="font-semibold">
          {data.total} published resources · {FEATURES.courses ? 14 : 13} active content types
        </p>
        <p className="mt-2 text-sm text-muted-foreground">
          The directory shows 200 resources per page. Lessons also appear in their subject curricula.
        </p>
      </div>
      <section>
        <h2 className="font-display text-xl font-bold">Catalogs & directories</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[
            ["All tutorials", "tutorials/programming-language-tutorials"],
            ["Computer science", "tutorials/articles-on-computer-science-subjects-gq"],
            ["Practice catalog", "explore"],
            ["Problem of the day", "problem-of-the-day"],
            ["Courses", "courses"],
            ["Videos", "videos"],
            ["Events & contests", "events"],
            ["Jobs", "jobs"],
            ["Quizzes", "quizzes"],
            ["Learning paths", "learning-paths"],
            ["Companies", "companies"],
            ["Authors", "authors"],
            ["Blogs", "category/blogs"],
            ["Interview preparation", "interview-experiences/company-interview-corner"],
          ]
            .filter(([, path]) => isPublicPath(path!))
            .map(([label, path]) => (
              <ELink
                key={path}
                to={path!}
                className="rounded-lg border p-4 text-sm font-semibold hover:border-primary"
              >
                {label}
              </ELink>
            ))}
        </div>
      </section>
      <section className="mt-10">
        <h2 className="font-display text-xl font-bold">Learner & administration screens</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {screenLinks
            .filter(([, path]) => isPublicPath(path!))
            .map(([label, path]) => (
              <a
                key={path}
                href={"/" + path}
                className="rounded-lg border p-4 text-sm font-semibold hover:border-primary"
              >
                {label}
              </a>
            ))}
        </div>
      </section>
      {data.total > 200 && (
        <nav aria-label="Resource directory pagination" className="mt-8 flex items-center gap-4">
          <Button variant="outline" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
            Previous resources
          </Button>
          <span className="text-sm">
            Page {page + 1} of {Math.ceil(data.total / 200)}
          </span>
          <Button
            variant="outline"
            disabled={(page + 1) * 200 >= data.total}
            onClick={() => setPage((p) => p + 1)}
          >
            Next resources
          </Button>
        </nav>
      )}
      {families.filter(isPublicEntryType).map((type) => (
        <section key={type} className="mt-10">
          <h2 className="font-display text-xl font-bold capitalize">
            {type === "path" ? "Learning paths" : type + " pages"}
          </h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {entries
              .filter((e) => e.type === type)
              .map((e) => (
                <div key={e.path} className="rounded-lg border bg-card p-4">
                  <ELink to={e.path} className="font-semibold hover:text-primary">
                    {e.title}
                  </ELink>
                  <p className="mt-1 break-all text-xs text-muted-foreground">/{e.path}</p>
                  <div className="mt-3 flex flex-wrap gap-3 text-xs font-semibold text-primary">
                    {type === "quiz" && (
                      <>
                        <ELink to={e.path + "/attempt"}>Attempt</ELink>
                        <ELink to={e.path + "/result"}>Result</ELink>
                      </>
                    )}
                    {type === "course" && (
                      <>
                        <ELink to={"checkout/" + e.path.replace(/^courses\//, "")}>Checkout</ELink>
                        <ELink to={"learn/" + e.path.replace(/^courses\//, "") + "/lesson/1"}>
                          Lesson
                        </ELink>
                        <ELink to={"learn/" + e.path.replace(/^courses\//, "") + "/assignment/1"}>
                          Assignment
                        </ELink>
                      </>
                    )}
                    {type === "event" && (
                      <>
                        <ELink to={e.path + "/participate"}>Workspace</ELink>
                        <ELink to={e.path + "/leaderboard"}>Leaderboard</ELink>
                      </>
                    )}
                    {type === "job" && <ELink to={e.path + "/apply"}>Application</ELink>}
                  </div>
                </div>
              ))}
          </div>
        </section>
      ))}
    </Wrap>
  );
}

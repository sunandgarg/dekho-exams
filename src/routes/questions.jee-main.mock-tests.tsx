import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { seoHead } from "@/lib/seo";
import { Button } from "@/components/ui/button";
import type { ArchiveQuestion } from "@/lib/jee-archive.functions";

const files = import.meta.glob<string>("../generated/jee-main-mocks/*.json.gz", {
  eager: true,
  query: "?url&no-inline",
  import: "default",
});
const sets = Object.entries(files)
  .map(([path, url]) => {
    const [kind, number, count] = path.split("/").pop()!.split(".")[0]!.split("-");
    const full = kind === "mock";
    const name = full ? "Mock test" : kind![0]!.toUpperCase() + kind!.slice(1) + " practice";
    return {
      id: kind + "-" + number,
      name: name + " " + Number(number),
      full,
      count: Number(count),
      minutes: full ? 180 : Math.ceil(Number(count) * 2.4),
      url,
    };
  })
  .sort((a, b) => Number(b.full) - Number(a.full) || a.id.localeCompare(b.id));
type SetInfo = (typeof sets)[number];
type Item = Pick<
  ArchiveQuestion,
  "body" | "subject" | "options" | "solution" | "kind" | "choiceKey" | "numericKey"
>;
type Attempt = { end: number; index: number; done: boolean; answers: string[] };
const count = sets.reduce((n, s) => n + s.count, 0);
export const Route = createFileRoute("/questions/jee-main/mock-tests")({
  head: () =>
    seoHead({
      title: "JEE Main mock tests with worked solutions | DekhoExams",
      description:
        "Practise JEE Main previous-year questions in timed Physics, Chemistry and Mathematics sets.",
      path: "questions/jee-main/mock-tests",
      noindex: true,
    }),
  component: Library,
});
function Library() {
  const [chosen, select] = useState(sets[0]?.id);
  const [active, start] = useState<SetInfo | null>(null);
  const choice = sets.find((s) => s.id === chosen);
  return (
    <div className="exam-wrap max-w-4xl">
      <a className="text-sm font-semibold text-primary" href="/past-years/jee/jee-main">
        ← JEE Main
      </a>
      <h1 className="mt-3 text-3xl font-extrabold">JEE Main mock tests</h1>
      {active ? (
        <Runner key={active.url} set={active} back={() => start(null)} />
      ) : (
        <>
          <p className="my-4">
            {sets.filter((s) => s.full).length} full mocks built from previous-year questions. Each
            full mock has 75 questions across Physics, Chemistry and Mathematics. Subject sets cover
            the remaining questions in the {count.toLocaleString("en-IN")}-question pool.
          </p>
          <div className="question-panel">
            <label className="grid gap-2 font-semibold">
              Choose a test
              <select
                className="rounded-lg border bg-card p-2"
                value={chosen}
                onChange={(e) => select(e.target.value)}
              >
                {sets.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} · {s.count} questions
                  </option>
                ))}
              </select>
            </label>
            {choice && (
              <>
                <p className="my-4">
                  {choice.minutes} minutes · +4 for correct, −1 for incorrect, 0 for skipped. Review
                  worked solutions after submitting.
                </p>
                <Button onClick={() => start(choice)}>Open test</Button>
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
}
function initial(set: SetInfo): Attempt {
  try {
    const a = JSON.parse(sessionStorage.getItem("de-mock:" + set.url) || "null");
    if (
      a &&
      Number.isFinite(a.end) &&
      typeof a.done === "boolean" &&
      Number.isInteger(a.index) &&
      a.index >= 0 &&
      a.index < set.count &&
      Array.isArray(a.answers) &&
      a.answers.length === set.count &&
      a.answers.every((v: unknown) => typeof v === "string")
    )
      return { ...a, done: a.done || a.end <= Date.now() };
  } catch {
    /* Browser storage is optional. */
  }
  return {
    end: Date.now() + set.minutes * 60000,
    index: 0,
    done: false,
    answers: Array(set.count).fill(""),
  };
}
const validNumber = (s: string) => /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$/.test(s);
const correct = (q: Item, v: string) =>
  validNumber(v) && Number(v) === (q.kind === "mcq" ? q.choiceKey : q.numericKey);
function Runner({ set, back }: { set: SetInfo; back: () => void }) {
  const [items, load] = useState<Item[]>([]);
  const [a, update] = useState<Attempt | null>(null);
  const [now, tick] = useState(Date.now);
  const [error, fail] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    (async () => {
      const r = await fetch(set.url, { signal: controller.signal });
      if (!r.ok || !r.body) throw Error();
      const data: Item[] = await new Response(
        r.body.pipeThrough(new DecompressionStream("gzip")),
      ).json();
      if (data.length !== set.count) throw Error();
      if (!controller.signal.aborted) {
        load(data);
        update(initial(set));
        tick(Date.now());
      }
    })().catch(() => {
      if (!controller.signal.aborted) fail(true);
    });
    return () => controller.abort();
  }, [set]);
  useEffect(() => {
    if (a)
      try {
        sessionStorage.setItem("de-mock:" + set.url, JSON.stringify(a));
      } catch {
        /* Practice still works in memory. */
      }
  }, [a, set.url]);
  const end = a?.end,
    done = a?.done;
  useEffect(() => {
    if (!end || done) return;
    const timer = window.setInterval(() => {
      const t = Date.now();
      tick(t);
      if (t >= end) update((v) => v && { ...v, done: true });
    }, 500);
    return () => clearInterval(timer);
  }, [end, done]);
  if (!a)
    return (
      <div className="my-4">
        <p role="status">
          {error ? "This test could not load. Open it again to retry." : "Loading questions…"}
        </p>
        <Button variant="outline" onClick={back}>
          Test library
        </Button>
      </div>
    );
  const q = items[a.index]!,
    answer = a.answers[a.index]!,
    attempted = a.answers.filter(Boolean).length;
  const hits = a.done ? items.filter((q, i) => correct(q, a.answers[i]!)).length : 0;
  const seconds = Math.max(0, Math.ceil((a.end - now) / 1000));
  const respond = (value: string) =>
    update((v) => {
      if (!v || v.done) return v;
      if (Date.now() >= v.end) return { ...v, done: true };
      const answers = v.answers.slice();
      answers[v.index] = value;
      return { ...v, answers };
    });
  const jump = (index: number) => update((v) => v && { ...v, index });
  return (
    <>
      <h2 className="mt-4 text-xl font-bold">{set.name}</h2>
      <p className="my-2" role="status">
        {a.done
          ? `Score ${4 * hits - (attempted - hits)} / ${4 * items.length} · ${hits} correct · ${attempted - hits} incorrect · ${items.length - attempted} skipped`
          : `${attempted} of ${items.length} answered`}
      </p>
      {!a.done && (
        <p className="mb-3">
          Time left {Math.floor(seconds / 60)}:{String(seconds % 60).padStart(2, "0")}
        </p>
      )}
      <article className="question-panel" data-subject={q.subject}>
        <label className="mb-3 flex flex-wrap items-center gap-2 font-bold">
          Question
          <select
            value={a.index}
            className="rounded-lg border bg-card p-2"
            onChange={(e) => jump(Number(e.target.value))}
          >
            {items.map((_, i) => (
              <option key={i} value={i}>
                {i + 1}
                {a.answers[i] ? " · answered" : ""}
              </option>
            ))}
          </select>
          <span className="capitalize">{q.subject}</span>
        </label>
        <div className="question-prompt jee-prose" dangerouslySetInnerHTML={{ __html: q.body }} />
        {q.kind === "mcq" ? (
          <fieldset className="mt-4 grid min-w-0 gap-2" disabled={a.done}>
            <legend className="sr-only">Your answer</legend>
            {q.options.map((option, i) => (
              <label
                className="answer-choice"
                key={i}
                data-correct={(a.done && i === q.choiceKey) || undefined}
              >
                <input
                  type="radio"
                  name="answer"
                  checked={answer === String(i)}
                  onChange={() => respond(String(i))}
                />
                <b className="choice-letter">{String.fromCharCode(65 + i)}</b>
                <span className="jee-prose" dangerouslySetInnerHTML={{ __html: option }} />
              </label>
            ))}
          </fieldset>
        ) : (
          <label className="mt-4 grid gap-1">
            Numerical answer
            <input
              className="rounded-lg border p-2"
              inputMode="decimal"
              disabled={a.done}
              value={answer}
              onChange={(e) => respond(e.target.value)}
            />
            {answer && !validNumber(answer) && (
              <span role="status">Enter a number to receive credit.</span>
            )}
          </label>
        )}
        {a.done && (
          <section className="question-solution">
            <h3 className="font-bold">
              {!answer ? "Skipped" : correct(q, answer) ? "Correct" : "Incorrect"} · Answer{" "}
              {q.kind === "mcq" ? String.fromCharCode(65 + q.choiceKey!) : q.numericKey}
            </h3>
            <div className="jee-prose" dangerouslySetInnerHTML={{ __html: q.solution }} />
          </section>
        )}
        <nav className="mt-4 flex flex-wrap gap-2" aria-label="Test questions">
          <Button variant="outline" disabled={a.index === 0} onClick={() => jump(a.index - 1)}>
            Previous
          </Button>
          <Button disabled={a.index === items.length - 1} onClick={() => jump(a.index + 1)}>
            Next
          </Button>
          {!a.done && (
            <Button variant="ghost" disabled={!answer} onClick={() => respond("")}>
              Clear answer
            </Button>
          )}
        </nav>
      </article>
      <div className="my-4 flex flex-wrap gap-2">
        <Button variant="outline" onClick={back}>
          Test library
        </Button>
        {a.done ? (
          <Button
            onClick={() => {
              try {
                sessionStorage.removeItem("de-mock:" + set.url);
              } catch {}
              update(initial(set));
              tick(Date.now());
            }}
          >
            Retake test
          </Button>
        ) : (
          <Button
            onClick={() => {
              if (window.confirm(`Submit with ${attempted} of ${items.length} questions answered?`))
                update((v) => v && { ...v, done: true });
            }}
          >
            Submit test
          </Button>
        )}
      </div>
    </>
  );
}

import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  answerKey,
  correct,
  displayKey,
  performance,
  type selectQuestions,
} from "@/lib/mock-scoring";
import { exportMockReport } from "@/lib/mock-report";
import "./mock-results.css";

type Questions = ReturnType<typeof selectQuestions>;
export function MockResults({
  name,
  id,
  items,
  answers,
  total,
}: {
  name: string;
  id: string;
  items: Questions;
  answers: string[];
  total: number;
}) {
  const report = useRef<HTMLDivElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [created] = useState(() => new Date().toLocaleString());
  const s = performance(items, answers);
  const subjects = [...new Set(items.map((q) => q.subject))].map((subject) => {
    const indices = items.flatMap((q, i) => (q.subject === subject ? [i] : []));
    return {
      subject,
      ...performance(
        indices.map((i) => items[i]!),
        indices.map((i) => answers[i] ?? ""),
      ),
    };
  });
  const exportReport = async (print: boolean) => {
    if (!report.current) return;
    setBusy(true);
    setError("");
    try {
      await exportMockReport(report.current, id, print);
    } catch {
      setError("The report could not be prepared. Check your connection and try again.");
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <div className="my-4 flex flex-wrap gap-2">
        <Button disabled={busy} onClick={() => exportReport(false)}>
          {busy ? "Preparing report…" : "Download report"}
        </Button>
        <Button variant="outline" disabled={busy} onClick={() => exportReport(true)}>
          Print / Save PDF
        </Button>
      </div>
      <p className="mb-4 text-sm">
        Download your branded performance report with scores and subject insights. Questions and
        answers stay on this page. Choose Print / Save PDF for a PDF copy.
      </p>
      {error && (
        <p role="alert" className="my-3">
          {error}
        </p>
      )}
      <div className="mock-report">
        <div className="mock-report mock-performance" data-performance-report ref={report}>
          <header className="mock-report-heading">
            <img
              className="mock-brand"
              src="/logos/dekhoexams-wordmark.png"
              width="220"
              height="33"
              alt="DekhoExams"
            />
            <p className="mock-brand-label">DEKHOEXAMS · YOUR PERFORMANCE SNAPSHOT</p>
            <h2>{name}</h2>
            <p>Report generated {created}</p>
          </header>
          <section className="mock-summary" aria-label="Test results">
            <div>
              <h3>Score</h3>
              <p className="mock-score">{s.graded ? `${s.score} / ${s.max}` : "Not graded"}</p>
              <p>
                {s.hits} correct · {s.misses} incorrect · {s.skipped} skipped · {s.review} not
                graded
              </p>
              <p>
                {s.graded} scorable questions out of {total} in the source set.
                {total > items.length &&
                  ` ${total - items.length} awaiting a verified key or diagram were excluded from this attempt.`}
              </p>
              <p>
                Practice marking: +4 correct, −1 incorrect, 0 skipped. Exact answers only; no
                partial credit. Official paper marking may differ.
              </p>
            </div>
            <div className="mock-readiness">
              <h3>Practice score percentage</h3>
              <strong>{s.readiness === null ? "Not available" : `${s.readiness}%`}</strong>
              {s.readiness !== null && (
                <meter
                  min="0"
                  max="100"
                  value={s.readiness}
                  aria-label="Practice score percentage"
                />
              )}
              <p>
                Net score as a percentage of the available practice marks, with a minimum of 0%.
                This measures this attempt, not your probability of selection.
              </p>
            </div>
          </section>
          <dl className="mock-kpis">
            {[
              ["Accuracy", s.accuracy === null ? "—" : `${s.accuracy}%`],
              ["Attempt rate", s.attemptRate === null ? "—" : `${s.attemptRate}%`],
              ["Correct", s.hits],
              ["Incorrect", s.misses],
              ["Skipped", s.skipped],
              ["Scorable attempts", s.attempted],
              ["Marks earned", s.earned],
              ["Negative marks", s.penalty],
            ].map(([label, value]) => (
              <div key={label}>
                <dt>{label}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
          <p className="mock-metric-note">
            Accuracy = correct ÷ scorable attempts. Attempt rate = scorable attempts ÷ scorable
            questions. A dash means there is not enough data.
          </p>
          <section className="mock-subjects" aria-label="Subject performance">
            <h3>Subject breakdown</h3>
            <div className="mock-subject-grid">
              {subjects.map((row) => (
                <article className="mock-subject" key={row.subject}>
                  <h4>{row.subject}</h4>
                  <strong>{row.graded ? `${row.score} / ${row.max}` : "Not graded"}</strong>
                  <p>
                    {row.hits} correct · {row.misses} incorrect · {row.skipped} skipped
                  </p>
                  <p>
                    Accuracy: {row.accuracy === null ? "—" : `${row.accuracy}%`} · Attempted:{" "}
                    {row.attempted}/{row.graded}
                  </p>
                  {!!row.review && <p>{row.review} excluded from scoring</p>}
                </article>
              ))}
            </div>
          </section>
          <section className="mock-next-step">
            <h3>Your next practice step</h3>
            <p>
              {!s.graded
                ? "Choose a test with verified questions to measure your performance."
                : !s.attempted
                  ? "Answer a few questions in each subject to establish your starting point."
                  : s.misses
                    ? "Review the concepts behind your incorrect attempts, then try a focused practice set."
                    : s.skipped
                      ? "Work through the skipped topics next while maintaining your accuracy."
                      : "Build consistency with another timed test covering different topics."}
            </p>
          </section>
          <footer className="mock-report-footer">
            <strong>DekhoExams</strong> · Learn. Practise. Progress.
            <br />
            dekhoexams.com · Personal practice report · No rank or selection prediction
          </footer>
        </div>
        <h3 className="mock-review-heading">All {items.length} questions · Answer review</h3>
        <div className="mock-result-list">
          {items.map((q, i) => {
            const answer = answers[i] ?? "";
            const status = q.review
              ? "Not graded"
              : !answer
                ? "Skipped"
                : correct(q, answer)
                  ? "Correct"
                  : "Incorrect";
            const yours = !answer
              ? "Not answered"
              : q.options.length
                ? answer
                    .split(",")
                    .map((v) =>
                      /^\d+$/.test(v) && Number(v) < q.options.length
                        ? String.fromCharCode(65 + Number(v))
                        : "Invalid option",
                    )
                    .join(", ")
                : answer;
            return (
              <article className="mock-result" key={q.number} data-result={status}>
                <div className="mock-question">
                  <h4>
                    Question {q.number} <span>{q.subject}</span>
                  </h4>
                  <div className="jee-prose" dangerouslySetInnerHTML={{ __html: q.body }} />
                  <ol className="mock-options" aria-label={`Question ${q.number} options`}>
                    {q.options.map((option, j) => (
                      <li
                        key={j}
                        data-correct={(!q.review && answerKey(q).includes(j)) || undefined}
                      >
                        <b>{String.fromCharCode(65 + j)}</b>
                        <div className="jee-prose" dangerouslySetInnerHTML={{ __html: option }} />
                      </li>
                    ))}
                  </ol>
                </div>
                <aside className="mock-answer" aria-label={`Question ${q.number} answer`}>
                  <p className="mock-result-status">{status}</p>
                  <dl>
                    <dt>Your answer</dt>
                    <dd>{yours}</dd>
                    <dt>{q.review ? "Verification status" : "Correct answer"}</dt>
                    <dd className={q.review ? "mock-pending" : undefined}>
                      {q.review || displayKey(q)}
                    </dd>
                  </dl>
                  {q.review && (
                    <p>Excluded from scoring until the key and required diagrams are verified.</p>
                  )}
                  <h4>Solution</h4>
                  {q.solution ? (
                    <div className="jee-prose" dangerouslySetInnerHTML={{ __html: q.solution }} />
                  ) : (
                    <p>A verified solution is not yet available.</p>
                  )}
                </aside>
              </article>
            );
          })}
        </div>
      </div>
    </>
  );
}

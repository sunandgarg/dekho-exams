import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  answerKey,
  correct,
  displayKey,
  summarize,
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
  const s = summarize(items, answers);
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
        Download an offline HTML report with all answers and available solutions, or save a PDF from
        the print dialog.
      </p>
      {error && (
        <p role="alert" className="my-3">
          {error}
        </p>
      )}
      <div className="mock-report" ref={report}>
        <header className="mock-report-heading">
          <img
            className="mock-brand"
            src="/logos/dekhoexams-wordmark.png"
            width="220"
            height="33"
            alt="DekhoExams"
          />
          <h2>{name} · Practice report</h2>
          <p>Report generated {created}</p>
        </header>
        <section className="mock-summary" aria-label="Test results">
          <div>
            <h3>Score</h3>
            <p className="mock-score">{s.graded ? `${s.score} / ${s.max}` : "Not graded"}</p>
            <p>
              {s.hits} correct · {s.misses} incorrect · {s.skipped} skipped · {s.review} not graded
            </p>
            <p>
              {s.graded} scorable questions out of {total} in the source set.
              {total > items.length &&
                ` ${total - items.length} awaiting a verified key or diagram were excluded from this attempt.`}
            </p>
            <p>
              Practice marking: +4 correct, −1 incorrect, 0 skipped. Exact answers only; no partial
              credit. Official paper marking may differ.
            </p>
          </div>
          <div className="mock-readiness">
            <h3>Practice readiness</h3>
            <strong>{s.readiness === null ? "Not available" : `${s.readiness}%`}</strong>
            {s.readiness !== null && (
              <meter min="0" max="100" value={s.readiness} aria-label="Practice readiness" />
            )}
            <p>
              Net score as a percentage of the available practice marks, with a minimum of 0%. This
              measures this attempt, not your probability of selection.
            </p>
          </div>
        </section>
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
        <footer className="mock-report-footer">DekhoExams · Practice report</footer>
      </div>
    </>
  );
}

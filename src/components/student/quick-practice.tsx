import { useEffect, useRef, useState } from "react";
import { ArrowRight, Download } from "lucide-react";
import { PreviewBreakdown, PreviewDiagnostic, PreviewQuestionReview } from "./preview-diagnostic";
import { blankPreviewAnswers, previewQuestions, previewResult } from "./preview-diagnostic-data";
import "./platform-preview.css";

export function QuickPractice() {
  const [answers, setAnswers] = useState<string[] | null>(null);
  const [flags, setFlags] = useState<boolean[]>([]);
  const [index, setIndex] = useState(0);
  const [result, setResult] = useState<ReturnType<typeof previewResult> | null>(null);
  const reportTitle = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    if (result) reportTitle.current?.focus();
  }, [result]);

  function start() {
    setAnswers(blankPreviewAnswers());
    setFlags([]);
    setIndex(0);
    setResult(null);
  }

  return (
    <div className="student-preview">
      <header className="sp-header">
        <a href="/" aria-label="DekhoExams home">
          <img src="/logos/dekhoexams-wordmark.png" alt="DekhoExams" width={178} height={36} />
        </a>
        <a href="/login">Sign in</a>
      </header>
      <main className="sp-main sp-quick">
        {result ? (
          <>
            <section className="sp-report" data-preview-report>
              <div className="sp-report-header">
                <img
                  src="/logos/dekhoexams-wordmark.png"
                  width={170}
                  height={34}
                  alt="DekhoExams"
                />
                <h1 ref={reportTitle} tabIndex={-1}>
                  Your practice report
                </h1>
              </div>
              <dl className="sp-quick-stats">
                <div>
                  <dt>Score</dt>
                  <dd>
                    {result.score} / {result.max}
                  </dd>
                </div>
                <div>
                  <dt>Accuracy</dt>
                  <dd>{result.accuracy === null ? "—" : result.accuracy + "%"}</dd>
                </div>
                <div>
                  <dt>Correct</dt>
                  <dd>
                    {result.hits} / {result.graded}
                  </dd>
                </div>
                <div>
                  <dt>Skipped</dt>
                  <dd>{result.skipped}</dd>
                </div>
              </dl>
              <PreviewBreakdown result={result} />
            </section>
            <div className="sp-report-actions">
              <button className="sp-button" type="button" onClick={() => window.print()}>
                <Download size={17} aria-hidden="true" /> Print or save report
              </button>
              <button className="sp-button sp-secondary" type="button" onClick={start}>
                Practise again
              </button>
            </div>
            <PreviewQuestionReview result={result} />
          </>
        ) : answers ? (
          <>
            <h1 className="sp-quick-heading">JEE Main practice</h1>
            <PreviewDiagnostic
              answers={answers}
              flags={flags}
              index={index}
              onMove={setIndex}
              onAnswer={(answer) =>
                setAnswers(answers.map((value, i) => (i === index ? answer : value)))
              }
              onFlag={() =>
                setFlags(previewQuestions.map((_, i) => (i === index ? !flags[i] : !!flags[i])))
              }
              onSubmit={() => setResult(previewResult(answers))}
            />
          </>
        ) : (
          <section className="sp-quick-intro">
            <h1 className="sp-quick-heading">JEE Main quick practice</h1>
            <p>
              Six questions across Physics, Chemistry and Maths. Take them at your own pace, then
              see what to revise.
            </p>
            <div className="sp-hero-actions">
              <button className="sp-button" type="button" onClick={start}>
                Start practice <ArrowRight size={17} aria-hidden="true" />
              </button>
              <a href="/questions/jee-main/mock-tests">Browse timed mocks</a>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

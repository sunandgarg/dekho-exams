import * as Dialog from "@radix-ui/react-dialog";
import { ArrowLeft, ArrowRight, BookOpen, ChevronRight, Flag, ShieldCheck } from "lucide-react";
import { useEffect, useRef } from "react";
import { PracticeMedal } from "./practice-medal";
import { previewQuestions, previewResult } from "./preview-diagnostic-data";

const subjectName = (subject: string) => subject.charAt(0).toUpperCase() + subject.slice(1);

export function PreviewDiagnostic({
  answers,
  flags,
  index,
  onAnswer,
  onFlag,
  onMove,
  onSubmit,
}: {
  answers: string[];
  flags: boolean[];
  index: number;
  onAnswer: (answer: string) => void;
  onFlag: () => void;
  onMove: (index: number) => void;
  onSubmit: () => void;
}) {
  const question = previewQuestions[index]!;
  const heading = useRef<HTMLHeadingElement>(null);
  const answered = answers.filter(Boolean).length;
  useEffect(() => {
    heading.current?.focus();
  }, [index]);

  return (
    <div className="sp-test-grid">
      <section className="sp-sample-test" aria-labelledby="sample-question">
        <div className="sp-question-meta">
          <span className="sp-subject-tag">{subjectName(question.subject)}</span>
          <span>
            Question {index + 1} of {previewQuestions.length}
          </span>
        </div>
        <h2 id="sample-question" tabIndex={-1} ref={heading}>
          {question.body}
        </h2>
        <fieldset>
          <legend>Choose one answer</legend>
          {question.options.map((option, i) => (
            <label
              className={answers[index] === String(i) ? "sp-option selected" : "sp-option"}
              key={option}
            >
              <input
                type="radio"
                name={`preview-answer-${index}`}
                checked={answers[index] === String(i)}
                onChange={() => onAnswer(String(i))}
              />
              <span aria-hidden="true">{String.fromCharCode(65 + i)}</span>
              {option}
            </label>
          ))}
        </fieldset>
        <div className="sp-question-actions">
          <button
            type="button"
            className="sp-text-button"
            aria-pressed={!!flags[index]}
            onClick={onFlag}
          >
            <Flag size={16} /> {flags[index] ? "Flagged for review" : "Flag for review"}
          </button>
          {answers[index] && (
            <button type="button" className="sp-text-button" onClick={() => onAnswer("")}>
              Clear answer
            </button>
          )}
        </div>
        <div className="sp-question-controls">
          <button
            type="button"
            className="sp-button sp-secondary"
            disabled={index === 0}
            onClick={() => onMove(index - 1)}
          >
            <ArrowLeft size={17} /> Previous
          </button>
          <button
            type="button"
            className="sp-button"
            disabled={index === previewQuestions.length - 1}
            onClick={() => onMove(index + 1)}
          >
            Next <ArrowRight size={17} />
          </button>
        </div>
      </section>
      <aside className="sp-test-navigation" aria-label="Test progress">
        <h2>Your progress</h2>
        <p aria-live="polite">
          <strong>{answered}</strong> of {previewQuestions.length} answered
        </p>
        <progress aria-label="Questions answered" value={answered} max={previewQuestions.length} />
        <nav aria-label="Jump to a question" className="sp-question-grid">
          {previewQuestions.map((_, i) => (
            <button
              type="button"
              key={i}
              aria-current={i === index ? "step" : undefined}
              aria-label={`Question ${i + 1}, ${answers[i] ? "answered" : "unanswered"}${flags[i] ? ", flagged" : ""}`}
              className={answers[i] ? "sp-answered" : ""}
              onClick={() => onMove(i)}
            >
              {i + 1}
              {flags[i] && <Flag aria-hidden="true" size={11} />}
            </button>
          ))}
        </nav>
        <p className="sp-test-key">
          <Flag size={15} /> {flags.filter(Boolean).length} flagged for review
        </p>
        <Dialog.Root>
          <Dialog.Trigger asChild>
            <button type="button" className="sp-button">
              Submit sample test
            </button>
          </Dialog.Trigger>
          <Dialog.Portal>
            <Dialog.Overlay className="sp-dialog-overlay" />
            <Dialog.Content className="student-preview sp-coupon-sheet sp-dialog-position sp-submit-dialog">
              <Dialog.Title>Submit your diagnostic?</Dialog.Title>
              <Dialog.Description>
                {answered === previewQuestions.length
                  ? `You’ve answered all ${previewQuestions.length} questions.`
                  : `${previewQuestions.length - answered} question${previewQuestions.length - answered === 1 ? " is" : "s are"} unanswered and will score zero.`}{" "}
                Your report will be ready after you submit.
              </Dialog.Description>
              <div className="sp-question-controls">
                <Dialog.Close asChild>
                  <button type="button" className="sp-button sp-secondary">
                    Keep reviewing
                  </button>
                </Dialog.Close>
                <Dialog.Close asChild>
                  <button type="button" className="sp-button" onClick={onSubmit}>
                    Submit and see results
                  </button>
                </Dialog.Close>
              </div>
            </Dialog.Content>
          </Dialog.Portal>
        </Dialog.Root>
      </aside>
    </div>
  );
}

export function PreviewBreakdown({ result }: { result: ReturnType<typeof previewResult> }) {
  const next = result.next?.question;
  return (
    <>
      <section className="sp-subject-breakdown" aria-label="Results by subject">
        <h2>Results by subject</h2>
        {result.subjects.map((subject) => (
          <div key={subject.subject} className="sp-subject-row">
            <strong>{subjectName(subject.subject)}</strong>
            <div
              className="sp-subject-bar"
              role="img"
              aria-label={`${subject.hits} correct, ${subject.misses} incorrect, ${subject.skipped} skipped`}
            >
              <span className="sp-subject-correct" style={{ flexGrow: subject.hits }} />
              <span className="sp-subject-wrong" style={{ flexGrow: subject.misses }} />
              <span className="sp-subject-skipped" style={{ flexGrow: subject.skipped }} />
            </div>
            <span>
              {subject.hits}/{subject.graded} correct
            </span>
          </div>
        ))}
        <p className="sp-subject-legend">
          <span>Correct</span>
          <span>Incorrect</span>
          <span>Skipped</span>
        </p>
      </section>
      <div className="sp-next-practice">
        <span className="sp-icon sp-blue">
          <BookOpen size={20} />
        </span>
        <div>
          <h2>
            {next ? `Practise ${next.topic.toLowerCase()} next` : "Try a full timed paper next"}
          </h2>
          <p>
            {next
              ? next.next
              : "You answered all six sample questions correctly. A longer paper will help you check your pace across the full syllabus."}
          </p>
          <a
            href={
              next
                ? `/past-years/jee/jee-main/${next.subject}/${next.chapter}`
                : "/questions/jee-main/mock-tests"
            }
          >
            {next ? "Open chapter practice" : "Browse JEE Main mocks"} <ChevronRight size={16} />
          </a>
        </div>
      </div>
    </>
  );
}

export function PreviewQuestionReview({ result }: { result: ReturnType<typeof previewResult> }) {
  return (
    <section className="sp-test-review" aria-label="Review the six questions">
      <h2>Review your answers</h2>
      {result.rows.map(({ question, answer, outcome, index }) => (
        <details key={question.topic}>
          <summary>
            <span>
              {index + 1}. {question.topic}
            </span>
            <span className={`sp-result-tag sp-result-${outcome.toLowerCase()}`}>{outcome}</span>
          </summary>
          <div>
            <h3>{question.body}</h3>
            <p>
              <strong>Your answer</strong> {answer ? question.options[Number(answer)] : "Skipped"}
            </p>
            <p>
              <strong>Correct answer</strong> {question.options[question.choiceKey!]}
            </p>
            <p>{question.solution}</p>
          </div>
        </details>
      ))}
      <div className="sp-awards-note">
        <PracticeMedal tier="Preview" />
        <div>
          <h3>Medals and certificates</h3>
          <p>
            Medals are earned on the school diagnostic. This practice set shows your score and what
            to revise next.
          </p>
          <a href="/platform-student">
            Open student panel <ShieldCheck size={15} />
          </a>
        </div>
      </div>
    </section>
  );
}

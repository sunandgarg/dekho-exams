import { useCallback, useEffect, useRef, useState } from "react";
import {
  Award,
  BookOpen,
  Check,
  CheckCircle2,
  Clock3,
  Download,
  Flag,
  Timer,
  Trophy,
} from "lucide-react";
import { platformMessage, platformRequest, PlatformError } from "@/lib/platform-client";
import { Block, Notice } from "./platform-controls";

type Answers = Record<string, number>;
type Question = { id: string; subject: string; topic: string; prompt: string; options: string[] };
type Result = {
  score: number;
  max: number;
  hits: number;
  misses: number;
  skipped: number;
  accuracy: number | null;
  subjects: { subject: string; hits: number; total: number }[];
  nextTopic: string | null;
};
type Attempt = {
  id: string;
  status: "active" | "submitted";
  deadline: string | number;
  answers: Answers;
  revision: number;
  result?: Result;
};
type StudentAward = { medal: string; certificateUrl?: string };
type StudentDashboard = {
  name: string;
  schoolName: string;
  attempt: Attempt | null;
  marketing: { eligible?: boolean; optedIn: boolean; email?: string };
  award?: StudentAward;
};
type AttemptUpdate = { attempt: Attempt; award?: StudentAward };

function minutesAndSeconds(ms: number) {
  const total = Math.max(0, Math.ceil(ms / 1000));
  return Math.floor(total / 60) + ":" + String(total % 60).padStart(2, "0");
}

function ProgressReport({ result, award }: { result: Result; award?: StudentAward }) {
  const download =
    award?.certificateUrl === "/api/platform/v1/student/certificate"
      ? award.certificateUrl
      : undefined;
  return (
    <div className="pw-grid">
      <Block title="Your diagnostic report" description="JEE Main school pilot · practice results">
        <div className="pw-stats">
          <div>
            <span>Score</span>
            <strong>
              {result.score} / {result.max}
            </strong>
          </div>
          <div>
            <span>Accuracy</span>
            <strong>{result.accuracy === null ? "—" : result.accuracy + "%"}</strong>
          </div>
          <div>
            <span>Correct</span>
            <strong>{result.hits}</strong>
          </div>
        </div>
        <p className="pw-muted">
          {result.misses} incorrect · {result.skipped} skipped
        </p>
        <ul className="pw-subjects">
          {result.subjects.map((subject) => (
            <li key={subject.subject}>
              <div className="pw-between">
                <strong>{subject.subject}</strong>
                <span>
                  {subject.hits} / {subject.total}
                </span>
              </div>
              <progress
                value={subject.hits}
                max={subject.total}
                aria-label={subject.subject + " correct answers"}
              />
            </li>
          ))}
        </ul>
        <div className="pw-callout">
          <BookOpen size={20} aria-hidden="true" />
          <div>
            <strong>What to practise next</strong>
            <p>
              {result.nextTopic
                ? "Review " +
                  result.nextTopic +
                  ", then work through a few problems without a timer."
                : "Try a longer timed mock to see how your pace holds across subjects."}
            </p>
          </div>
        </div>
        <div className="pw-inline pw-tools">
          <a
            className="pw-button"
            href="/api/platform/v1/student/report"
            download="DekhoExams-JEE-Main-report.html"
          >
            <Download size={17} aria-hidden="true" /> Download report
          </a>
          <a
            className="pw-button pw-secondary"
            href="/api/platform/v1/student/report"
            target="_blank"
            rel="noopener"
          >
            Open printable report
          </a>
        </div>
      </Block>
      <Block
        title="Medals and certificates"
        description="Recognition for completed practice on DekhoExams."
      >
        <div className="pw-award">
          <Award size={42} aria-hidden="true" />
          <div>
            <h3>{award ? award.medal + " medal" : "Your award history"}</h3>
            <p>
              {award
                ? "Earned from your submitted diagnostic."
                : "Awards you earn will appear here."}
            </p>
          </div>
        </div>
        {download && (
          <a className="pw-button" href={download} download="DekhoExams-certificate.html">
            <Download size={17} aria-hidden="true" /> Download certificate
          </a>
        )}
      </Block>
    </div>
  );
}

export function PlatformStudent() {
  const [data, setData] = useState<StudentDashboard | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [draft, setDraft] = useState<Answers>({});
  const [flags, setFlags] = useState<string[]>([]);
  const [position, setPosition] = useState(0);
  const [now, setNow] = useState(Date.now);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState("");
  const [confirmSubmit, setConfirmSubmit] = useState(false);
  const pending = useRef(false);
  const expiryChecked = useRef("");
  const questionHeading = useRef<HTMLHeadingElement>(null);

  async function load() {
    setBusy("load");
    setError("");
    try {
      setData(await platformRequest<StudentDashboard>("/student"));
    } catch (cause) {
      setError(platformMessage(cause));
    } finally {
      setBusy("");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const showAttempt = useCallback(({ attempt, award }: AttemptUpdate) => {
    setData((current) => current && { ...current, attempt, ...(award ? { award } : {}) });
    setDraft(attempt.answers);
    if (attempt.status === "submitted") {
      setQuestions([]);
      setConfirmSubmit(false);
    }
  }, []);

  const startOrResume = useCallback(async () => {
    if (pending.current) return;
    pending.current = true;
    setError("");
    setMessage("");
    setBusy("attempt");
    try {
      const result = await platformRequest<AttemptUpdate & { questions: Question[] }>(
        "/student/attempt",
        {},
      );
      setQuestions(result.questions);
      setPosition(0);
      showAttempt(result);
      setNow(Date.now());
    } catch (cause) {
      setError(platformMessage(cause));
    } finally {
      pending.current = false;
      setBusy("");
    }
  }, [showAttempt]);

  const deadline =
    data?.attempt?.status === "active" ? new Date(data.attempt.deadline).getTime() : 0;
  useEffect(() => {
    if (!deadline) return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [deadline]);

  useEffect(() => {
    if (
      !deadline ||
      deadline > now ||
      busy ||
      !data?.attempt ||
      expiryChecked.current === data.attempt.id
    )
      return;
    expiryChecked.current = data.attempt.id;
    void startOrResume();
  }, [deadline, now, busy, data?.attempt, startOrResume]);

  async function save(submit: boolean, next = position) {
    if (pending.current || !data?.attempt || data.attempt.status !== "active") return;
    pending.current = true;
    setBusy(submit ? "submit" : "save");
    setError("");
    setMessage("");
    try {
      const result = await platformRequest<AttemptUpdate>("/student/answers", {
        revision: data.attempt.revision,
        answers: draft,
        submit,
      });
      showAttempt(result);
      setPosition(next);
      if (!submit) setMessage("Answers saved.");
    } catch (cause) {
      setError(
        cause instanceof PlatformError && cause.status === 409
          ? "This attempt changed in another tab. Reload the saved attempt to continue."
          : platformMessage(cause),
      );
    } finally {
      pending.current = false;
      setBusy("");
    }
  }

  async function marketing(optedIn: boolean) {
    if (!data?.marketing.eligible || pending.current) return;
    pending.current = true;
    setBusy("marketing");
    setError("");
    setMessage("");
    try {
      await platformRequest("/student/marketing", { optedIn });
      setData((current) => current && { ...current, marketing: { ...current.marketing, optedIn } });
      setMessage(optedIn ? "Mock test email updates are on." : "Mock test email updates are off.");
    } catch (cause) {
      setError(platformMessage(cause));
    } finally {
      pending.current = false;
      setBusy("");
    }
  }

  const question = questions[position];
  const running = !!question && data?.attempt?.status === "active";
  const remaining = deadline ? Math.max(0, deadline - now) : 0;
  const dirty = questions.some((item) => draft[item.id] !== data?.attempt?.answers[item.id]);
  const answered = questions.filter((item) => draft[item.id] !== undefined).length;

  function selectQuestion(next: number) {
    setPosition(next);
    questionHeading.current?.focus();
  }

  return (
    <>
      <div className="pw-hero">
        <div>
          <p className="pw-kicker">Student workspace</p>
          <h1>{data ? "Welcome, " + data.name : "Your practice"}</h1>
          <p>
            {data?.schoolName
              ? data.schoolName + " · JEE Main pilot"
              : "Your mock progress, reports and awards."}
          </p>
        </div>
        <Trophy size={42} aria-hidden="true" />
      </div>
      <Notice message={error} error />
      <Notice message={message} />
      {!data ? (
        <div role="status">
          {busy ? (
            "Loading your workspace…"
          ) : (
            <button className="pw-button pw-secondary" onClick={() => void load()}>
              Try again
            </button>
          )}
        </div>
      ) : (
        <>
          {data.attempt?.status === "submitted" && data.attempt.result ? (
            <ProgressReport
              result={data.attempt.result}
              {...(data.award ? { award: data.award } : {})}
            />
          ) : running && question ? (
            <div className="pw-runner">
              <Block title="JEE Main diagnostic">
                <div className="pw-between pw-attempt-meta">
                  <p>
                    {question.subject} · {question.topic}
                  </p>
                  <span className="pw-pill">
                    <Timer size={16} aria-hidden="true" /> {minutesAndSeconds(remaining)} remaining
                  </span>
                </div>
                <h3 className="pw-question" tabIndex={-1} ref={questionHeading}>
                  {question.prompt}
                </h3>
                <fieldset className="pw-choices" disabled={!!busy || !remaining || confirmSubmit}>
                  {question.options.map((option, index) => (
                    <label
                      className={draft[question.id] === index ? "pw-choice chosen" : "pw-choice"}
                      key={index}
                    >
                      <input
                        type="radio"
                        name={question.id}
                        checked={draft[question.id] === index}
                        onChange={() =>
                          setDraft((current) => ({ ...current, [question.id]: index }))
                        }
                      />
                      <span aria-hidden="true">{String.fromCharCode(65 + index)}</span> {option}
                    </label>
                  ))}
                </fieldset>
                <div className="pw-inline pw-tools">
                  <button
                    type="button"
                    className="pw-button pw-secondary"
                    disabled={position <= 0 || !!busy || confirmSubmit}
                    onClick={() => selectQuestion(position - 1)}
                  >
                    Previous
                  </button>
                  <button
                    type="button"
                    className="pw-button pw-secondary"
                    disabled={position >= questions.length - 1 || !!busy || confirmSubmit}
                    onClick={() => selectQuestion(position + 1)}
                  >
                    Next question
                  </button>
                  <button
                    type="button"
                    className="pw-button pw-secondary"
                    aria-pressed={flags.includes(question.id)}
                    disabled={!!busy || confirmSubmit}
                    onClick={() =>
                      setFlags((current) =>
                        current.includes(question.id)
                          ? current.filter((id) => id !== question.id)
                          : [...current, question.id],
                      )
                    }
                  >
                    <Flag size={16} aria-hidden="true" />{" "}
                    {flags.includes(question.id) ? "Unflag" : "Flag for review"}
                  </button>
                  <button
                    type="button"
                    className="pw-button pw-secondary"
                    disabled={
                      draft[question.id] === undefined || !!busy || !remaining || confirmSubmit
                    }
                    onClick={() =>
                      setDraft((current) => {
                        const next = { ...current };
                        delete next[question.id];
                        return next;
                      })
                    }
                  >
                    Clear answer
                  </button>
                </div>
              </Block>
              <Block
                title="Progress"
                description={answered + " of " + questions.length + " answered"}
              >
                <ol className="pw-question-nav">
                  {questions.map((item, index) => (
                    <li key={item.id}>
                      <button
                        aria-current={index === position ? "step" : undefined}
                        className={draft[item.id] !== undefined ? "answered" : ""}
                        disabled={!!busy || confirmSubmit}
                        type="button"
                        aria-label={
                          "Question " +
                          (index + 1) +
                          (draft[item.id] !== undefined ? ", answered" : ", unanswered") +
                          (flags.includes(item.id) ? ", flagged" : "")
                        }
                        onClick={() => selectQuestion(index)}
                      >
                        {index + 1}
                        {flags.includes(item.id) && <Flag size={12} aria-hidden="true" />}
                      </button>
                    </li>
                  ))}
                </ol>
                <p className="pw-muted" role="status">
                  {dirty ? "You have unsaved answers." : "Your answers are saved."}
                </p>
                {remaining ? (
                  <div className="pw-form">
                    <button
                      type="button"
                      className="pw-button pw-secondary"
                      disabled={!!busy || !dirty || confirmSubmit}
                      onClick={() => void save(false)}
                    >
                      <Check size={17} aria-hidden="true" />{" "}
                      {busy === "save" ? "Saving…" : "Save answers"}
                    </button>
                    {!confirmSubmit ? (
                      <button
                        type="button"
                        className="pw-button"
                        disabled={!!busy}
                        onClick={() => setConfirmSubmit(true)}
                      >
                        Review submission
                      </button>
                    ) : (
                      <div className="pw-confirm">
                        <strong>Submit your diagnostic?</strong>
                        <p>
                          {questions.length - answered} unanswered. Your current choices will be
                          saved and scored.
                        </p>
                        <div className="pw-inline">
                          <button
                            type="button"
                            className="pw-button"
                            disabled={!!busy}
                            onClick={() => void save(true)}
                          >
                            {busy === "submit" ? "Submitting…" : "Submit test"}
                          </button>
                          <button
                            type="button"
                            className="pw-button pw-secondary"
                            disabled={!!busy}
                            onClick={() => setConfirmSubmit(false)}
                          >
                            Keep working
                          </button>
                        </div>
                      </div>
                    )}
                    {error && (
                      <button
                        type="button"
                        className="pw-button pw-secondary"
                        disabled={!!busy}
                        onClick={() => void startOrResume()}
                      >
                        Reload saved attempt
                      </button>
                    )}
                  </div>
                ) : (
                  <button
                    type="button"
                    className="pw-button"
                    disabled={!!busy}
                    onClick={() => void startOrResume()}
                  >
                    {busy ? "Checking…" : "Open timed result"}
                  </button>
                )}
              </Block>
            </div>
          ) : (
            <Block
              title="JEE Main diagnostic"
              description="One timed practice test is included with this school invitation."
            >
              <div className="pw-callout">
                <Clock3 size={21} aria-hidden="true" />
                <p>
                  The timer starts when you begin. Save answers during the test so you can resume
                  after an interruption.
                </p>
              </div>
              <button
                type="button"
                className="pw-button"
                disabled={!!busy}
                onClick={() => void startOrResume()}
              >
                {busy === "attempt"
                  ? "Opening…"
                  : data.attempt
                    ? "Resume your diagnostic"
                    : "Start timed diagnostic"}
              </button>
            </Block>
          )}
          <Block
            title="Email preferences"
            description="Choose whether to receive optional DekhoExams mock test updates. Your choice does not affect school access."
          >
            {data.marketing.eligible ? (
              <label className="pw-check">
                <input
                  type="checkbox"
                  checked={data.marketing.optedIn}
                  disabled={!!busy}
                  onChange={(event) => void marketing(event.target.checked)}
                />
                <span>
                  Send me mock test updates by email
                  {data.marketing.email ? " at " + data.marketing.email : ""}.
                </span>
              </label>
            ) : (
              <p className="pw-inline pw-muted">
                <CheckCircle2 size={17} aria-hidden="true" /> Marketing email is off for this school
                account.
              </p>
            )}
          </Block>
        </>
      )}
    </>
  );
}

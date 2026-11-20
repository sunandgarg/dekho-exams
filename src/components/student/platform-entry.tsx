import { useEffect, useState, type FormEvent } from "react";
import { ArrowRight, GraduationCap, School2 } from "lucide-react";
import { platformMessage, platformRequest } from "@/lib/platform-client";
import { Notice } from "./platform-controls";
import { PracticeMedal } from "./practice-medal";
import "./platform-workspace.css";

type Audience = "student" | "parent" | "school";

export function PlatformEntry() {
  const [available, setAvailable] = useState<boolean | null>(null);
  const [audience, setAudience] = useState<Audience>("student");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    void platformRequest<{ available: boolean }>("/status")
      .then((result) => {
        if (active) setAvailable(result.available);
      })
      .catch(() => {
        if (active) setAvailable(false);
      });
    return () => {
      active = false;
    };
  }, []);

  async function requestAccess(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || !available) return;
    const values = new FormData(event.currentTarget);
    setBusy(true);
    setError("");
    try {
      await platformRequest("/inquiry", {
        kind: audience,
        name: values.get("name"),
        email: values.get("email"),
        school: values.get("school") ?? "",
        website: values.get("website") ?? "",
        adult: values.get("adult") === "on",
        contactPermission: values.get("contactPermission") === "on",
      });
      setSent(true);
    } catch (cause) {
      setError(platformMessage(cause));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="pw-workspace pw-entry">
      <a className="pw-skip" href="#access-main">
        Skip to sign in
      </a>
      <header className="pw-top">
        <div className="pw-top-inner">
          <a href="/" className="pw-brand" aria-label="DekhoExams home">
            <img src="/logos/dekhoexams-wordmark.png" alt="DekhoExams" width={162} height={33} />
          </a>
          <a href="/questions">Question bank</a>
        </div>
      </header>
      <main className="pw-main pw-entry-main" id="access-main">
        <div className="pw-entry-heading">
          <h1>Sign in to DekhoExams</h1>
          <p>Use the invitation your school or the DekhoExams team sent you.</p>
        </div>
        <div className="pw-entry-layout">
          <div className="pw-access-options">
            <section className="pw-panel pw-access-card">
              <span className="pw-access-icon">
                <GraduationCap size={23} aria-hidden="true" />
              </span>
              <div>
                <h2>Students</h2>
                <p>Take your school mock and see what to practise next.</p>
              </div>
              <div className="pw-inline pw-tools">
                <a className="pw-button" href="/platform-student">
                  Student sign in <ArrowRight size={16} aria-hidden="true" />
                </a>
                {available && (
                  <a
                    href="#request-access"
                    onClick={() => {
                      setAudience("student");
                      setSent(false);
                    }}
                  >
                    Request student access
                  </a>
                )}
              </div>
            </section>
            <section className="pw-panel pw-access-card" id="schools">
              <span className="pw-access-icon">
                <School2 size={23} aria-hidden="true" />
              </span>
              <div>
                <h2>Schools</h2>
                <p>Upload your class list and track how many students finish the mock.</p>
              </div>
              <div className="pw-inline pw-tools">
                <a className="pw-button" href="/platform-school">
                  School sign in <ArrowRight size={16} aria-hidden="true" />
                </a>
                {available && (
                  <a
                    href="#request-access"
                    onClick={() => {
                      setAudience("school");
                      setSent(false);
                    }}
                  >
                    Request school access
                  </a>
                )}
              </div>
            </section>
            <div className="pw-entry-practice">
              {available === false && <p role="status">School enrollment is currently closed.</p>}
              <a href="/platform-preview">
                Try six JEE Main questions without signing in{" "}
                <ArrowRight size={16} aria-hidden="true" />
              </a>
            </div>
          </div>
          <section className="pw-certificate-preview" aria-labelledby="practice-certificate-title">
            <PracticeMedal />
            <h2 id="practice-certificate-title">Practice certificates</h2>
            <p>
              Earn a DekhoExams medal and printable certificate with at least four correct answers
              on the school diagnostic.
            </p>
            <dl>
              <div>
                <dt>Bronze</dt>
                <dd>4 correct</dd>
              </div>
              <div>
                <dt>Silver</dt>
                <dd>5 correct</dd>
              </div>
              <div>
                <dt>Gold</dt>
                <dd>6 correct</dd>
              </div>
            </dl>
          </section>
        </div>
        {available && (
          <section className="pw-panel" id="request-access">
            <h2>Request access</h2>
            {sent ? (
              <Notice message="Your request was received. The DekhoExams team can follow up by email." />
            ) : (
              <form className="pw-form" method="post" onSubmit={requestAccess}>
                <label className="pw-field">
                  I’m a
                  <select
                    value={audience}
                    onChange={(event) => setAudience(event.target.value as Audience)}
                  >
                    <option value="student">Student aged 18 or older</option>
                    <option value="parent">Parent or guardian</option>
                    <option value="school">School staff member</option>
                  </select>
                </label>
                <div className="pw-form-columns">
                  <label className="pw-field">
                    Your name
                    <input name="name" autoComplete="name" required maxLength={120} />
                  </label>
                  <label className="pw-field">
                    {audience === "school" ? "Work email" : "Your email"}
                    <input
                      name="email"
                      type="email"
                      autoComplete="email"
                      required
                      maxLength={254}
                    />
                  </label>
                </div>
                {audience === "school" && (
                  <label className="pw-field">
                    School name
                    <input name="school" autoComplete="organization" required maxLength={180} />
                  </label>
                )}
                <div hidden>
                  <label>
                    Website
                    <input name="website" autoComplete="off" tabIndex={-1} />
                  </label>
                </div>
                <label className="pw-inline">
                  <input name="adult" type="checkbox" required />
                  I’m 18 or older.
                </label>
                <label className="pw-inline">
                  <input name="contactPermission" type="checkbox" required />
                  DekhoExams can email me about this access request.
                </label>
                <p className="pw-muted">
                  Parents and school staff should enter their own contact details.{" "}
                  <a href="/privacy">Privacy policy</a>
                </p>
                <Notice message={error} error />
                <button className="pw-button" type="submit" disabled={busy}>
                  {busy ? "Sending…" : "Request access"}
                </button>
              </form>
            )}
          </section>
        )}
      </main>
    </div>
  );
}

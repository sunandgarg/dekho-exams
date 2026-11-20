import { useEffect, useState, type FormEvent } from "react";
import { ArrowRight, Award, GraduationCap, School2 } from "lucide-react";
import { platformMessage, platformRequest } from "@/lib/platform-client";
import { Block, Notice } from "./platform-controls";
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
    <div className="pw-workspace">
      <header className="pw-top">
        <div className="pw-top-inner">
          <a href="/" className="pw-brand" aria-label="DekhoExams home">
            <img src="/logos/dekhoexams-wordmark.png" alt="DekhoExams" width={162} height={33} />
          </a>
          <a href="/questions">Question bank</a>
        </div>
      </header>
      <main className="pw-main">
        <div className="pw-hero">
          <div>
            <h1>Sign in to DekhoExams</h1>
            <p>Choose your workspace to get started.</p>
          </div>
        </div>
        {available === false && (
          <Notice message="Workspace enrollment is being set up. You can practise without an account today." />
        )}
        <div className="pw-grid">
          <section className="pw-panel pw-access-card">
            <GraduationCap size={32} aria-hidden="true" />
            <h2>Students</h2>
            <p>
              Use your school invitation to take your mock, view your report and download any
              practice certificate you earn.
            </p>
            <div className="pw-inline pw-tools">
              <a className="pw-button" href="/platform-student">
                Student sign in <ArrowRight size={16} aria-hidden="true" />
              </a>
              <a href="/platform-preview">Try the free diagnostic</a>
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
            <School2 size={32} aria-hidden="true" />
            <h2>Schools</h2>
            <p>
              Use your school workspace to upload a roster, give students their mock access and
              track completion.
            </p>
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
        <Block title="Practice certificates">
          <p className="pw-inline">
            <Award size={21} aria-hidden="true" /> Eligible results from a submitted school
            diagnostic earn a DekhoExams medal and a printable practice certificate.
          </p>
        </Block>
      </main>
    </div>
  );
}

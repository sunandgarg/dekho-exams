import { useState } from "react";
import { CheckCircle2, ExternalLink, KeyRound, LockKeyhole } from "lucide-react";
import { STUDENT_INTEGRATIONS, type IntegrationName } from "@/lib/student-integrations";

export function IntegrationPreview() {
  const [mode, setMode] = useState("test");
  const [saved, setSaved] = useState<string[]>([]);
  const [message, setMessage] = useState("");
  return (
    <section className="sp-integration-section">
      <div className="sp-section-heading">
        <div>
          <h2>Connect once. Manage it here.</h2>
          <p className="sp-muted">
            The integration desk for your live admin. Use sample values in this design preview.
          </p>
        </div>
        <label className="sp-field">
          Environment
          <select value={mode} onChange={(e) => setMode(e.target.value)}>
            <option value="test">Test mode</option>
            <option value="live">Live mode</option>
          </select>
        </label>
      </div>
      <div className="sp-integration-notice">
        <LockKeyhole size={18} />
        <p>
          Do not paste real keys in this public preview. The live owner-only setup will encrypt
          credentials on the server and show only their configured status.
        </p>
      </div>
      {message && (
        <p className="sp-notice" role="status">
          {message}
        </p>
      )}
      <div className="sp-integration-grid">
        {(Object.keys(STUDENT_INTEGRATIONS) as IntegrationName[]).map((id) => {
          const s = STUDENT_INTEGRATIONS[id],
            key = id + ":" + mode;
          return (
            <article className="sp-table-card" key={key}>
              <div className="sp-section-heading">
                <span className="sp-icon sp-blue">
                  <KeyRound size={20} />
                </span>
                <span className="sp-tiny-pill">
                  {saved.includes(key)
                    ? "Sample setup checked"
                    : id === "ses"
                      ? "SES sandbox"
                      : "Not connected"}
                </span>
              </div>
              <h3>{s.name}</h3>
              <p className="sp-muted">{s.note}</p>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  setSaved((v) => [...new Set([...v, key])]);
                  setMessage(
                    s.name +
                      ": sample fields checked. No credentials were saved and no provider request was sent.",
                  );
                  e.currentTarget.reset();
                }}
              >
                {s.fields.map((f) => (
                  <label className="sp-field" key={f.key}>
                    {f.label}
                    <input
                      type={f.secret ? "password" : "text"}
                      name={f.key}
                      placeholder="Sample value only"
                      required
                      autoComplete="off"
                      maxLength={4096}
                    />
                  </label>
                ))}
                <button className="sp-button sp-secondary" type="submit">
                  <CheckCircle2 size={16} />
                  Check sample setup
                </button>
              </form>
              <a href={s.help} target="_blank" rel="noopener noreferrer">
                Provider setup guide <ExternalLink size={14} />
              </a>
            </article>
          );
        })}
      </div>
    </section>
  );
}

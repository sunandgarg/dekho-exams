import { useEffect, useState, type FormEvent } from "react";
import { KeyRound, Plus, School2 } from "lucide-react";
import { STUDENT_INTEGRATIONS, type IntegrationName } from "@/lib/student-integrations";
import {
  formatDate,
  platformMessage,
  platformRequest,
  type Invite,
  type School,
  type SchoolCoupon,
} from "@/lib/platform-client";
import { Block, CopyValue, Invitation, Notice } from "./platform-controls";

type IntegrationMode = "test" | "live";
type IntegrationStatus = {
  provider: IntegrationName;
  mode: IntegrationMode;
  configured: { field: string; present: boolean }[];
  updatedAt?: string;
};
type AdminDashboard = {
  schools: School[];
  nextCursor?: string | null;
  integrations: IntegrationStatus[];
};

function IntegrationEditor({
  provider,
  mode,
  status,
  onSaved,
}: {
  provider: IntegrationName;
  mode: IntegrationMode;
  status?: IntegrationStatus;
  onSaved: (saved: IntegrationStatus) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const spec = STUDENT_INTEGRATIONS[provider];
  const count = status?.configured.filter((field) => field.present).length ?? 0;

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const values = Object.fromEntries(new FormData(form));
    if (!Object.values(values).some((value) => String(value).trim())) {
      setError("Enter at least one setting to save.");
      return;
    }
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const result = await platformRequest<IntegrationStatus>("/integrations", {
        provider,
        mode,
        values,
      });
      onSaved({ ...result, provider, mode });
      form.reset();
      setMessage("Settings saved. Provider activation is separate.");
    } catch (cause) {
      setError(platformMessage(cause));
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className="pw-integration">
      <div className="pw-between">
        <h3>{spec.name}</h3>
        <span className="pw-pill">
          {count} / {spec.fields.length} saved
        </span>
      </div>
      <p className="pw-muted">
        {spec.note}{" "}
        <a href={spec.help} target="_blank" rel="noreferrer">
          Setup guide
        </a>
      </p>
      <form className="pw-form" onSubmit={save} method="post" autoComplete="off">
        {spec.fields.map((field) => {
          const present = status?.configured.some(
            (item) => item.field === field.key && item.present,
          );
          return (
            <label className="pw-field" key={field.key}>
              {field.label}
              <input
                type={field.secret ? "password" : "text"}
                name={field.key}
                autoComplete="off"
                maxLength={4096}
                placeholder={present ? "Saved. Leave blank to keep." : "Enter value"}
                spellCheck={false}
              />
            </label>
          );
        })}
        <Notice message={error} error />
        <Notice message={message} />
        <button className="pw-button pw-secondary" disabled={busy} type="submit">
          <KeyRound size={16} aria-hidden="true" /> {busy ? "Saving…" : "Save settings"}
        </button>
      </form>
    </article>
  );
}

export function PlatformAdmin() {
  const [data, setData] = useState<AdminDashboard | null>(null);
  const [mode, setMode] = useState<IntegrationMode>("test");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const [school, setSchool] = useState<{ school: School; coupon: SchoolCoupon } | null>(null);
  const [invite, setInvite] = useState<{ schoolId: string; value: Invite } | null>(null);

  async function load(after?: string) {
    setBusy("load");
    setError("");
    try {
      const result = await platformRequest<AdminDashboard>(
        "/admin" + (after ? "?after=" + encodeURIComponent(after) : ""),
      );
      setData((current) =>
        after && current ? { ...result, schools: [...current.schools, ...result.schools] } : result,
      );
    } catch (cause) {
      setError(platformMessage(cause));
    } finally {
      setBusy("");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function createSchool(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const values = Object.fromEntries(new FormData(form));
    setBusy("school");
    setError("");
    setSchool(null);
    try {
      const created = await platformRequest<{ school: School; coupon: SchoolCoupon }>("/schools", {
        ...values,
        redemptionLimit: Number(values["redemptionLimit"]),
      });
      setSchool(created);
      setData(
        (current) => current && { ...current, schools: [created.school, ...current.schools] },
      );
      form.reset();
    } catch (cause) {
      setError(platformMessage(cause));
    } finally {
      setBusy("");
    }
  }

  async function inviteSchool(schoolId: string) {
    setBusy(schoolId);
    setError("");
    setInvite(null);
    try {
      const value = await platformRequest<Invite>("/invitations", { schoolId });
      setInvite({ schoolId, value });
    } catch (cause) {
      setError(platformMessage(cause));
    } finally {
      setBusy("");
    }
  }

  return (
    <>
      <div className="pw-hero">
        <div>
          <h1>Platform administration</h1>
          <p>Create school partnerships and manage provider settings for DekhoExams.</p>
        </div>
        <div className="pw-inline">
          <a className="pw-button" href="/platform-admin/leads">
            All leads
          </a>
          <a className="pw-button pw-secondary" href="#integrations">
            Integration settings
          </a>
        </div>
      </div>
      <Notice message={error} error />
      {!data ? (
        <p role="status">
          {busy ? (
            "Loading your workspace…"
          ) : (
            <button className="pw-button pw-secondary" onClick={() => void load()}>
              Try again
            </button>
          )}
        </p>
      ) : (
        <>
          <div className="pw-grid">
            <Block
              title="Add a school"
              description="Each school gets one default coupon. An eligible student can use it for one mock."
            >
              <form className="pw-form" onSubmit={createSchool} method="post">
                <label className="pw-field">
                  School name
                  <input name="name" required maxLength={180} placeholder="School name" />
                </label>
                <div className="pw-form-columns">
                  <label className="pw-field">
                    City
                    <input name="city" required maxLength={100} />
                  </label>
                  <label className="pw-field">
                    State
                    <input name="state" required maxLength={80} />
                  </label>
                </div>
                <div className="pw-form-columns">
                  <label className="pw-field">
                    Exam
                    <select name="exam">
                      <option value="jee-main">JEE Main</option>
                    </select>
                  </label>
                  <label className="pw-field">
                    Coupon limit
                    <input
                      type="number"
                      name="redemptionLimit"
                      min={1}
                      max={10000}
                      required
                      defaultValue={100}
                    />
                  </label>
                </div>
                <label className="pw-field">
                  Valid through (IST)
                  <input type="date" name="expiresAt" required />
                </label>
                <button className="pw-button" type="submit" disabled={!!busy}>
                  <Plus size={16} aria-hidden="true" />{" "}
                  {busy === "school" ? "Creating…" : "Create school and coupon"}
                </button>
              </form>
              {school && (
                <div className="pw-invite">
                  <Notice message={school.school.name + " is ready."} />
                  <CopyValue value={school.coupon.code} label="Default school coupon" />
                  <p>Expires {formatDate(school.coupon.expiresAt)} IST.</p>
                </div>
              )}
            </Block>
            <Block
              title="Partner schools"
              description="Create an invitation for the person who will manage each school workspace."
            >
              {!data.schools.length && (
                <p className="pw-empty">
                  <School2 size={24} aria-hidden="true" /> Your partner schools will appear here.
                </p>
              )}
              <ul className="pw-list">
                {data.schools.map((item) => (
                  <li key={item.id}>
                    <div className="pw-between">
                      <div>
                        <strong>{item.name}</strong>
                        <p className="pw-muted">
                          {item.city}, {item.state}
                        </p>
                      </div>
                      <button
                        className="pw-button pw-secondary"
                        type="button"
                        disabled={!!busy}
                        onClick={() => void inviteSchool(item.id)}
                      >
                        {busy === item.id ? "Creating…" : "Create school invitation"}
                      </button>
                    </div>
                    {invite?.schoolId === item.id && <Invitation invite={invite.value} />}
                  </li>
                ))}
              </ul>
              {data.nextCursor && (
                <button
                  className="pw-button pw-secondary"
                  disabled={!!busy}
                  onClick={() => void load(data.nextCursor ?? undefined)}
                >
                  Load more schools
                </button>
              )}
            </Block>
          </div>
          <div id="integrations" className="pw-panel">
            <div className="pw-between">
              <div>
                <h2>Integration settings</h2>
                <p className="pw-muted">Saved credentials are encrypted and never shown again.</p>
              </div>
              <label className="pw-field">
                Environment
                <select
                  value={mode}
                  onChange={(event) => setMode(event.target.value === "live" ? "live" : "test")}
                >
                  <option value="test">Test</option>
                  <option value="live">Live</option>
                </select>
              </label>
            </div>
            <div className="pw-grid pw-integration-grid">
              {(Object.keys(STUDENT_INTEGRATIONS) as IntegrationName[]).map((provider) => {
                const status = data.integrations.find(
                  (item) => item.provider === provider && item.mode === mode,
                );
                return (
                  <IntegrationEditor
                    key={provider + mode}
                    provider={provider}
                    mode={mode}
                    {...(status ? { status } : {})}
                    onSaved={(saved) =>
                      setData(
                        (current) =>
                          current && {
                            ...current,
                            integrations: [
                              ...current.integrations.filter(
                                (item) => item.provider !== provider || item.mode !== mode,
                              ),
                              saved,
                            ],
                          },
                      )
                    }
                  />
                );
              })}
            </div>
          </div>
        </>
      )}
    </>
  );
}

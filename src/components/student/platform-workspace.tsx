import { useEffect, useState, type FormEvent } from "react";
import { ArrowRight, LockKeyhole, LogOut, ShieldCheck } from "lucide-react";
import {
  extractInvitation,
  platformMessage,
  platformRequest,
  PlatformError,
  platformRoutes,
  type PlatformRole,
  type PlatformSession,
} from "@/lib/platform-client";
import { Notice } from "./platform-controls";
import { PlatformAdmin } from "./platform-admin";
import { PlatformLeads } from "./platform-leads";
import { PlatformSchool } from "./platform-school";
import { PlatformStudent } from "./platform-student";
import "./platform-workspace.css";

const titles: Record<PlatformRole, string> = {
  owner: "Owner workspace",
  school: "School workspace",
  student: "Student workspace",
};
const descriptions: Record<PlatformRole, string> = {
  owner: "Manage school partnerships, coupons and provider settings.",
  school: "Manage your school coupon and give your enrolled students access.",
  student: "Take your school diagnostic and see your private report and awards.",
};

export function PlatformWorkspace({
  role,
  ownerView,
}: {
  role: PlatformRole;
  ownerView?: "leads";
}) {
  const [session, setSession] = useState<PlatformSession | null>(null);
  const [available, setAvailable] = useState<boolean | null>(null);
  const [invite, setInvite] = useState("");
  const [codeSent, setCodeSent] = useState(false);
  const [busy, setBusy] = useState("session");
  const [error, setError] = useState("");

  useEffect(() => {
    const fragment = window.location.hash;
    if (fragment.startsWith("#invite=")) {
      const token = extractInvitation(window.location.href);
      window.history.replaceState(
        window.history.state,
        "",
        window.location.pathname + window.location.search,
      );
      setInvite(token);
      if (!token) setError("This invitation link is malformed.");
    }
    let active = true;
    void platformRequest<{ available: boolean }>("/status")
      .then(({ available }) => {
        if (active) setAvailable(available);
      })
      .catch(() => {
        if (active) setAvailable(null);
      });
    void platformRequest<PlatformSession>("/session")
      .then((result) => {
        if (active) setSession(result);
      })
      .catch((cause) => {
        if (active && !(cause instanceof PlatformError && cause.status === 401))
          setError(platformMessage(cause));
      })
      .finally(() => {
        if (active) setBusy("");
      });
    return () => {
      active = false;
    };
  }, []);

  async function sendCode(token: string) {
    setBusy("code");
    setError("");
    try {
      await platformRequest<{ sent: true }>("/student-code", { token });
      setInvite(token);
      setCodeSent(true);
    } catch (cause) {
      setError(platformMessage(cause));
    } finally {
      setBusy("");
    }
  }

  async function activate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const token = invite || extractInvitation(String(form.get("invite") ?? ""));
    if (!token) {
      setError("Enter a valid DekhoExams invitation link.");
      return;
    }
    if (role === "student" && !codeSent) {
      await sendCode(token);
      return;
    }
    setBusy("activate");
    setError("");
    try {
      const result = await platformRequest<PlatformSession>(
        "/activate",
        role === "student" ? { token, code: String(form.get("code") ?? "") } : { token },
      );
      setInvite("");
      setCodeSent(false);
      setSession(result);
      if (result.role !== role && platformRoutes[result.role])
        window.location.assign(platformRoutes[result.role]);
    } catch (cause) {
      setError(platformMessage(cause));
    } finally {
      setBusy("");
    }
  }

  async function logout() {
    setBusy("logout");
    setError("");
    try {
      await platformRequest("/logout", {});
      setSession(null);
    } catch (cause) {
      setError(platformMessage(cause));
    } finally {
      setBusy("");
    }
  }

  const unlocked = session?.role === role && !invite;

  return (
    <div className="pw-workspace">
      <a className="pw-skip" href="#workspace-main">
        Skip to content
      </a>
      <header className="pw-top">
        <div className="pw-top-inner">
          <a className="pw-brand" href="/" aria-label="DekhoExams home">
            <img src="/logos/dekhoexams-wordmark.png" alt="DekhoExams" width="162" height="33" />
          </a>
          <span className="pw-top-title">{titles[role]}</span>
          {session && (
            <button
              type="button"
              className="pw-button pw-secondary"
              disabled={!!busy}
              onClick={() => void logout()}
            >
              <LogOut size={17} aria-hidden="true" />{" "}
              {busy === "logout" ? "Signing out…" : "Sign out"}
            </button>
          )}
        </div>
      </header>
      <main className="pw-main" id="workspace-main">
        <Notice message={error} error />
        {busy === "session" ? (
          <p className="pw-muted" role="status">
            Checking your session…
          </p>
        ) : unlocked ? (
          role === "owner" ? (
            ownerView === "leads" ? (
              <PlatformLeads />
            ) : (
              <PlatformAdmin />
            )
          ) : role === "school" ? (
            <PlatformSchool />
          ) : (
            <PlatformStudent />
          )
        ) : (
          <div className="pw-unlock">
            <div className="pw-unlock-copy">
              <ShieldCheck aria-hidden="true" size={44} />
              <h1>{titles[role]}</h1>
              <p>{descriptions[role]}</p>
            </div>
            <section className="pw-panel" aria-labelledby="pw-unlock-title">
              <h2 id="pw-unlock-title">
                <LockKeyhole size={20} aria-hidden="true" />{" "}
                {session ? "You’re signed in" : "Open your invitation"}
              </h2>
              {!session && role !== "owner" && (
                <a href="/login">Student and school access options</a>
              )}
              {session ? (
                <>
                  <p className="pw-muted">
                    You’re signed in to the {titles[session.role].toLowerCase()}. Sign out before
                    activating a new invitation.
                  </p>
                  {session.role === role ? (
                    <button className="pw-button" type="button" onClick={() => setInvite("")}>
                      Stay in this workspace <ArrowRight size={16} aria-hidden="true" />
                    </button>
                  ) : (
                    <a className="pw-button" href={platformRoutes[session.role]}>
                      Go to your workspace <ArrowRight size={16} aria-hidden="true" />
                    </a>
                  )}
                </>
              ) : available === false ? (
                <>
                  <Notice message="Workspace enrollment is being set up." />
                  {role !== "owner" && (
                    <a className="pw-button" href="/platform-preview">
                      Try the free diagnostic
                    </a>
                  )}
                </>
              ) : (
                <form className="pw-form" onSubmit={activate} method="post">
                  <p className="pw-muted" role={codeSent ? "status" : undefined}>
                    {codeSent
                      ? "Enter the six-digit code sent to your registered mobile."
                      : role === "student"
                        ? "Use your school’s invitation link to request a code on your registered mobile. SMS must be enabled for this pilot."
                        : invite
                          ? "This single-use link activates your access. Use it only if you were the intended recipient."
                          : "Use the private invitation link from your school or the DekhoExams team."}
                  </p>
                  {!invite && (
                    <label className="pw-field">
                      Invitation link
                      <input
                        type="password"
                        name="invite"
                        required
                        autoComplete="off"
                        spellCheck={false}
                        maxLength={1200}
                      />
                    </label>
                  )}
                  {codeSent && (
                    <label className="pw-field">
                      Verification code
                      <input
                        type="text"
                        name="code"
                        inputMode="numeric"
                        autoComplete="one-time-code"
                        pattern="[0-9]{6}"
                        maxLength={6}
                        required
                      />
                    </label>
                  )}
                  <button className="pw-button" type="submit" disabled={!!busy}>
                    {busy === "activate"
                      ? "Activating…"
                      : busy === "code"
                        ? "Sending code…"
                        : role !== "student"
                          ? "Activate invitation"
                          : codeSent
                            ? "Verify and sign in"
                            : "Send a code"}{" "}
                    <ArrowRight size={16} aria-hidden="true" />
                  </button>
                  {codeSent && (
                    <button
                      className="pw-button pw-secondary"
                      type="button"
                      disabled={!!busy}
                      onClick={() => void sendCode(invite)}
                    >
                      Resend code
                    </button>
                  )}
                </form>
              )}
              <a className="pw-back" href="/platform-preview">
                Explore the platform preview
              </a>
            </section>
          </div>
        )}
      </main>
    </div>
  );
}

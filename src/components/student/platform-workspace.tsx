import { lazy, Suspense, useEffect, useState, type FormEvent } from "react";
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
import "./platform-workspace.css";

const PlatformAdmin = lazy(() =>
  import("./platform-admin").then((module) => ({ default: module.PlatformAdmin })),
);
const PlatformLeads = lazy(() =>
  import("./platform-leads").then((module) => ({ default: module.PlatformLeads })),
);
const PlatformSchool = lazy(() =>
  import("./platform-school").then((module) => ({ default: module.PlatformSchool })),
);
const PlatformStudent = lazy(() =>
  import("./platform-student").then((module) => ({ default: module.PlatformStudent })),
);

const titles: Record<PlatformRole, string> = {
  owner: "Owner workspace",
  school: "School workspace",
  student: "Student workspace",
};
const descriptions: Record<PlatformRole, string> = {
  owner: "Manage school partnerships, coupons and provider settings.",
  school: "Bring your class roster, invite students and track completed mocks.",
  student: "Take your school mock, see what to revise and download any award you earn.",
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
          <Suspense fallback={<p role="status">Opening your workspace…</p>}>
            {role === "owner" ? (
              ownerView === "leads" ? (
                <PlatformLeads />
              ) : (
                <PlatformAdmin />
              )
            ) : role === "school" ? (
              <PlatformSchool />
            ) : (
              <PlatformStudent />
            )}
          </Suspense>
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
                {session ? "You’re signed in" : available ? "Open your invitation" : "Sign in"}
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
              ) : available !== true ? (
                <p className="pw-muted">Sign-in is unavailable right now.</p>
              ) : (
                <form className="pw-form" onSubmit={activate} method="post">
                  <p className="pw-muted" role={codeSent ? "status" : undefined}>
                    {codeSent
                      ? "Enter the six-digit code sent to your registered mobile."
                      : role === "student"
                        ? "Paste the invitation from your school. We’ll send a code to the mobile number your school registered."
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
              <a className="pw-back" href="/questions/jee-main/quick-practice">
                Practise JEE Main
              </a>
            </section>
          </div>
        )}
      </main>
    </div>
  );
}

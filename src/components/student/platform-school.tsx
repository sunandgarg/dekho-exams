import { useEffect, useState, type ChangeEvent, type FormEvent } from "react";
import { Download, School2, Ticket, Upload, Users } from "lucide-react";
import {
  formatDate,
  PlatformError,
  platformMessage,
  platformRequest,
  type Invite,
  type School,
  type SchoolCoupon,
} from "@/lib/platform-client";
import { readRoster, type RosterRow } from "@/lib/platform-roster";
import { Block, CopyValue, Invitation, Notice } from "./platform-controls";

type RosterRecord = {
  id: string;
  name: string;
  mobile: string;
  email?: string;
  level?: string;
  access?: "none" | "invited" | "activated";
};
type SchoolDashboard = {
  school: School;
  coupon: SchoolCoupon | null;
  roster: RosterRecord[];
  nextCursor: string | null;
};
type ImportResult = { added: number; duplicates: number; total: number };
const template = "data:text/csv;charset=utf-8," + encodeURIComponent("name,mobile,email,class\r\n");

export function PlatformSchool() {
  const [data, setData] = useState<SchoolDashboard | null>(null);
  const [file, setFile] = useState<{ name: string; rows: RosterRow[] } | null>(null);
  const [invite, setInvite] = useState<{ rosterId: string; value: Invite } | null>(null);
  const [completed, setCompleted] = useState<ImportResult | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [rowErrors, setRowErrors] = useState<PlatformError["rowErrors"]>([]);

  async function load(after?: string) {
    const result = await platformRequest<SchoolDashboard>(
      "/school" + (after ? "?after=" + encodeURIComponent(after) : ""),
    );
    setData((current) =>
      after && current ? { ...result, roster: [...current.roster, ...result.roster] } : result,
    );
  }

  async function refresh(after?: string) {
    setBusy("load");
    setError("");
    try {
      await load(after);
    } catch (cause) {
      setError(platformMessage(cause));
    } finally {
      setBusy("");
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function chooseFile(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.currentTarget.files?.[0];
    event.currentTarget.value = "";
    setFile(null);
    setCompleted(null);
    setError("");
    setRowErrors([]);
    if (!selected) return;
    setBusy("file");
    try {
      const rows = await readRoster(selected);
      setFile({ name: selected.name, rows });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not read that roster.");
    } finally {
      setBusy("");
    }
  }

  async function importRoster(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file || new FormData(event.currentTarget).get("authorized") !== "on") return;
    setBusy("import");
    setError("");
    setRowErrors([]);
    try {
      const result = await platformRequest<ImportResult>("/roster", {
        rows: file.rows,
        authorized: true,
      });
      setFile(null);
      setCompleted(result);
      await load();
    } catch (cause) {
      setError(platformMessage(cause));
      if (cause instanceof PlatformError) setRowErrors(cause.rowErrors);
    } finally {
      setBusy("");
    }
  }

  async function inviteStudent(rosterId: string) {
    setError("");
    setBusy(rosterId);
    setInvite(null);
    try {
      const value = await platformRequest<Invite>("/invitations", { rosterId });
      setInvite({ rosterId, value });
      setData(
        (current) =>
          current && {
            ...current,
            roster: current.roster.map((row) =>
              row.id === rosterId && row.access !== "activated"
                ? { ...row, access: "invited" }
                : row,
            ),
          },
      );
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
          <p className="pw-kicker">School workspace</p>
          <h1>{data?.school.name ?? "Your school"}</h1>
          <p>
            {data
              ? [data.school.city, data.school.state].join(", ")
              : "Manage your students’ mock access and invitations."}
          </p>
        </div>
        <School2 size={43} aria-hidden="true" />
      </div>
      <Notice message={error} error />
      {!data ? (
        <div role="status">
          {busy ? (
            "Loading your school…"
          ) : (
            <button className="pw-button pw-secondary" onClick={() => void refresh()}>
              Try again
            </button>
          )}
        </div>
      ) : (
        <>
          <div className="pw-grid">
            <Block
              title="Your school coupon"
              description="Each eligible student can redeem this for one mock."
            >
              {data.coupon ? (
                <>
                  <div className="pw-stats">
                    <div>
                      <span>Redeemed</span>
                      <strong>{data.coupon.used}</strong>
                    </div>
                    <div>
                      <span>Limit</span>
                      <strong>{data.coupon.limit}</strong>
                    </div>
                    <div>
                      <span>Remaining</span>
                      <strong>{Math.max(0, data.coupon.limit - data.coupon.used)}</strong>
                    </div>
                  </div>
                  <CopyValue value={data.coupon.code} label="Default school coupon" />
                  <p className="pw-inline pw-muted">
                    <Ticket size={18} aria-hidden="true" />{" "}
                    {data.coupon.exam === "jee-advanced"
                      ? "JEE Advanced"
                      : data.coupon.exam === "jee-main"
                        ? "JEE Main"
                        : data.coupon.exam}{" "}
                    · {data.coupon.active ? "Active" : "Inactive"} · Expires{" "}
                    {formatDate(data.coupon.expiresAt)} IST
                  </p>
                </>
              ) : (
                <p className="pw-empty">
                  <Ticket size={24} aria-hidden="true" /> A school coupon has not been assigned.
                </p>
              )}
            </Block>
            <Block
              title="Import a class roster"
              description="Upload a CSV or the first sheet of an Excel .xlsx workbook. Up to 250 students and 1 MB per file."
            >
              <div className="pw-inline pw-tools">
                <label className="pw-file pw-button">
                  <Upload size={16} aria-hidden="true" />{" "}
                  {busy === "file" ? "Reading…" : "Choose file"}
                  <input
                    type="file"
                    accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    onChange={(event) => void chooseFile(event)}
                    disabled={!!busy}
                  />
                </label>
                <a
                  className="pw-button pw-secondary"
                  href={template}
                  download="dekhoexams-roster-template.csv"
                >
                  <Download size={16} aria-hidden="true" /> CSV template
                </a>
              </div>
              <p className="pw-muted">
                Required columns are name and mobile. Email and class are optional. Rosters are used
                for school test access. Uploading them does not opt students into marketing.
              </p>
              {completed && (
                <Notice
                  message={`${completed.added} added. ${completed.duplicates} duplicate${completed.duplicates === 1 ? "" : "s"} skipped.`}
                />
              )}
              {rowErrors.length > 0 && (
                <ul className="pw-list" aria-label="Roster entries to correct">
                  {rowErrors.map(({ row, fields }) => (
                    <li key={row}>
                      Roster entry {row}. Check {fields.join(", ")}.
                    </li>
                  ))}
                </ul>
              )}
              {file && (
                <form className="pw-form" onSubmit={importRoster} method="post">
                  <p>
                    <strong>{file.rows.length} rows ready</strong> from {file.name}
                  </p>
                  <ul className="pw-preview-list" aria-label="First rows in the roster">
                    {file.rows.slice(0, 5).map((row, index) => (
                      <li key={index}>
                        {row.name} <span>··· {row.mobile.slice(-4)}</span>
                      </li>
                    ))}
                  </ul>
                  <label className="pw-check">
                    <input type="checkbox" name="authorized" required />
                    <span>
                      My school has permission to share this roster for mock access. I will deliver
                      student invitations privately.
                    </span>
                  </label>
                  <div className="pw-inline">
                    <button className="pw-button" type="submit" disabled={!!busy}>
                      {busy === "import" ? "Importing…" : "Confirm and import"}
                    </button>
                    <button
                      className="pw-button pw-secondary"
                      type="button"
                      disabled={!!busy}
                      onClick={() => setFile(null)}
                    >
                      Discard preview
                    </button>
                  </div>
                </form>
              )}
            </Block>
          </div>
          <Block
            title="Student roster"
            description="Only this school’s roster appears here. Contact details are masked."
          >
            {!data.roster.length && (
              <p className="pw-empty">
                <Users size={24} aria-hidden="true" /> Import a roster to create student
                invitations.
              </p>
            )}
            <ul className="pw-list">
              {data.roster.map((row) => (
                <li key={row.id}>
                  <div className="pw-between">
                    <div>
                      <strong>{row.name}</strong>
                      <p className="pw-muted">
                        {[
                          row.mobile,
                          row.email,
                          row.level && /^(10|11|12)$/.test(row.level)
                            ? "Class " + row.level
                            : row.level,
                        ]
                          .filter(Boolean)
                          .join(" · ")}
                      </p>
                    </div>
                    <div className="pw-inline">
                      {row.access === "activated" && <span className="pw-pill">Activated</span>}
                      {row.access === "invited" && <span className="pw-pill">Invited</span>}
                      <button
                        className="pw-button pw-secondary"
                        type="button"
                        disabled={!!busy}
                        onClick={() => void inviteStudent(row.id)}
                      >
                        {busy === row.id
                          ? "Creating…"
                          : row.access === "activated" || row.access === "invited"
                            ? "Create new link"
                            : "Create student invitation"}
                      </button>
                    </div>
                  </div>
                  {invite?.rosterId === row.id && <Invitation invite={invite.value} />}
                </li>
              ))}
            </ul>
            {data.nextCursor && (
              <button
                className="pw-button pw-secondary"
                disabled={!!busy}
                onClick={() => void refresh(data.nextCursor ?? undefined)}
              >
                Load more students
              </button>
            )}
          </Block>
        </>
      )}
    </>
  );
}

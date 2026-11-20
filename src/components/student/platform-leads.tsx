import { useEffect, useState, type FormEvent } from "react";
import { Search } from "lucide-react";
import { formatDate, platformMessage, platformRequest } from "@/lib/platform-client";
import { Notice } from "./platform-controls";

const audiences = {
  student: "Adult student",
  parent: "Parent or guardian",
  school: "School staff",
};
type Status = "new" | "contacted";
type Lead = {
  id: string;
  name: string;
  email: string;
  school: string;
  kind: keyof typeof audiences;
  status: Status;
  createdAt: string;
};
type Page = { leads: Lead[]; nextCursor: string | null };
type Filters = { email?: string; status?: string; kind?: string };

export function PlatformLeads() {
  const [page, setPage] = useState<Page | null>(null);
  const [filters, setFilters] = useState<Filters>({});
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");

  async function load(search: Filters, before?: string) {
    setBusy(true);
    setError("");
    try {
      const next = await platformRequest<Page>("/admin/leads", { ...search, before });
      setPage((previous) =>
        before && previous ? { ...next, leads: [...previous.leads, ...next.leads] } : next,
      );
    } catch (cause) {
      setError(platformMessage(cause));
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    void load({});
  }, []);

  function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const next = Object.fromEntries(
      ["email", "kind", "status"].flatMap((key) => {
        const value = String(data.get(key) ?? "").trim();
        return value ? [[key, value]] : [];
      }),
    );
    setPage(null);
    setFilters(next);
    void load(next);
  }

  async function changeStatus(lead: Lead) {
    const status = lead.status === "new" ? "contacted" : "new";
    setBusy(true);
    setError("");
    try {
      await platformRequest("/admin/leads/status", { id: lead.id, status });
      await load(filters);
    } catch (cause) {
      setError(platformMessage(cause));
      setBusy(false);
    }
  }

  return (
    <>
      <div className="pw-hero">
        <div>
          <h1>All leads</h1>
          <p>Access requests from adult students, parents and schools.</p>
        </div>
        <a className="pw-button pw-secondary" href="/platform-admin">
          Back to admin
        </a>
      </div>
      <section className="pw-panel">
        <form className="pw-lead-filters" onSubmit={search} method="post">
          <label className="pw-field">
            Email
            <input type="email" name="email" maxLength={254} placeholder="Exact email address" />
          </label>
          <label className="pw-field">
            Audience
            <select name="kind">
              <option value="">All audiences</option>
              {Object.entries(audiences).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label className="pw-field">
            Status
            <select name="status">
              <option value="">All statuses</option>
              <option value="new">New</option>
              <option value="contacted">Contacted</option>
            </select>
          </label>
          <button type="submit" className="pw-button" disabled={busy}>
            <Search size={16} aria-hidden="true" /> Apply filters
          </button>
        </form>
        <Notice message={error} error />
        <p className="pw-muted" role="status">
          {busy
            ? "Loading leads…"
            : page
              ? `${page.leads.length} ${page.leads.length === 1 ? "request" : "requests"} shown`
              : ""}
        </p>
        {page &&
          (page.leads.length ? (
            <div className="pw-leads-table" tabIndex={0} aria-label="Access requests" role="region">
              <table>
                <thead>
                  <tr>
                    <th scope="col">Contact</th>
                    <th scope="col">Audience</th>
                    <th scope="col">Received (IST)</th>
                    <th scope="col">Status</th>
                    <th scope="col">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {page.leads.map((lead) => (
                    <tr key={lead.id}>
                      <td>
                        <strong>{lead.name}</strong>
                        <br />
                        <a href={`mailto:${encodeURIComponent(lead.email)}`}>{lead.email}</a>
                        {lead.school && (
                          <>
                            <br />
                            {lead.school}
                          </>
                        )}
                      </td>
                      <td>{audiences[lead.kind]}</td>
                      <td>{formatDate(lead.createdAt)}</td>
                      <td>
                        <span className="pw-pill">
                          {lead.status === "new" ? "New" : "Contacted"}
                        </span>
                      </td>
                      <td>
                        <button
                          className="pw-button pw-secondary"
                          type="button"
                          disabled={busy}
                          onClick={() => void changeStatus(lead)}
                        >
                          {lead.status === "new" ? "Mark contacted" : "Reopen"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="pw-empty">No access requests match these filters.</p>
          ))}
        {page?.nextCursor && (
          <button
            className="pw-button pw-secondary"
            type="button"
            disabled={busy}
            onClick={() => void load(filters, page.nextCursor!)}
          >
            Load more
          </button>
        )}
      </section>
    </>
  );
}

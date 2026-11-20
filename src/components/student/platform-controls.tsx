import { Copy, ShieldCheck } from "lucide-react";
import { useId, useState, type ReactNode } from "react";
import { formatDate, type Invite } from "@/lib/platform-client";

export function Block({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: ReactNode;
}) {
  const id = useId();
  return (
    <section className="pw-panel" aria-labelledby={id}>
      <h2 id={id}>{title}</h2>
      {description && <p className="pw-muted">{description}</p>}
      {children}
    </section>
  );
}

export function Notice({ message, error = false }: { message: string; error?: boolean }) {
  return message ? (
    <p className={error ? "pw-notice pw-error" : "pw-notice"} role={error ? "alert" : "status"}>
      {message}
    </p>
  ) : null;
}

export function CopyValue({ value, label }: { value: string; label: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <div className="pw-copy">
      <label className="pw-field">
        {label}
        <input
          readOnly
          value={value}
          onFocus={(e) => e.currentTarget.select()}
          spellCheck={false}
        />
      </label>
      <button
        type="button"
        className="pw-button pw-secondary"
        onClick={async () => {
          try {
            await navigator.clipboard.writeText(value);
            setCopied(true);
          } catch {
            setCopied(false);
          }
        }}
      >
        <Copy size={16} aria-hidden="true" /> {copied ? "Copied" : "Copy"}
      </button>
    </div>
  );
}

export function Invitation({ invite }: { invite: Invite }) {
  return (
    <div className="pw-invite">
      <CopyValue value={invite.url} label="Single-use invitation link" />
      <p>
        <ShieldCheck size={16} aria-hidden="true" /> Share this link privately. It expires{" "}
        {formatDate(invite.expiresAt)} IST.
      </p>
    </div>
  );
}

export type PlatformRole = "owner" | "school" | "student";
export type PlatformSession = { role: PlatformRole; schoolId?: string; name?: string };
export type School = { id: string; name: string; state: string; city: string };
export type SchoolCoupon = {
  id: string;
  code: string;
  exam: string;
  active: boolean;
  expiresAt: string;
  limit: number;
  used: number;
};
export type Invite = { url: string; expiresAt: string };
export const platformRoutes = {
  owner: "/platform-admin",
  school: "/platform-school",
  student: "/platform-student",
} as const;

export class PlatformError extends Error {
  status: number;
  rowErrors: { row: number; fields: string[] }[];
  constructor(message: string, status: number, rows: unknown = null) {
    super(message);
    this.status = status;
    this.rowErrors = Array.isArray(rows)
      ? rows
          .filter(
            (item) =>
              Number.isInteger(item?.row) &&
              item.row > 0 &&
              item.row <= 250 &&
              Array.isArray(item.fields) &&
              item.fields.every((field: unknown) =>
                ["row", "name", "mobile", "email", "level"].includes(String(field)),
              ),
          )
          .slice(0, 10)
      : [];
  }
}

export async function platformRequest<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch("/api/platform/v1" + path, {
    method: body === undefined ? "GET" : "POST",
    credentials: "same-origin",
    cache: "no-store",
    ...(body === undefined
      ? {}
      : {
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }),
  });
  const data = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok)
    throw new PlatformError(
      typeof data?.error === "string"
        ? data.error
        : "That request could not be completed. Try again.",
      response.status,
      data?.details,
    );
  if (data === null && response.status !== 204)
    throw new PlatformError("The platform sent an unexpected response.", 502);
  return data as T;
}

export function platformMessage(error: unknown) {
  return error instanceof PlatformError
    ? error.message
    : "Could not reach DekhoExams. Check your connection and try again.";
}

export const formatDate = (date: string) =>
  new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Kolkata",
  }).format(new Date(date));

export function extractInvitation(value: string): string {
  const trimmed = value.trim();
  const token = /^[a-zA-Z0-9_-]{43}$/;
  if (token.test(trimmed)) return trimmed;
  try {
    const url = new URL(trimmed, window.location.origin);
    if (url.origin !== window.location.origin) return "";
    const invite = new URLSearchParams(url.hash.slice(1)).get("invite") || "";
    return token.test(invite) ? invite : "";
  } catch {
    return "";
  }
}

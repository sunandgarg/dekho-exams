import type { Pool, RowDataPacket } from "mysql2/promise";
import { z, ZodError } from "zod";
import { STUDENT_INTEGRATIONS, type IntegrationName } from "../../src/lib/student-integrations.ts";
import {
  activate,
  issueInvite,
  platformOrigin,
  resolveMember,
  sessionCookie,
  sessionToken,
  type Role,
} from "./access.ts";
import { tokenDigest, validToken } from "./crypto.ts";
import { diagnostic, PilotError, type scoreDiagnostic } from "./diagnostic.ts";
import { openSettings, saveIntegration, validateSettings } from "./integrations.ts";
import { platformKey, platformPool } from "./pool.ts";
import {
  createSchool,
  getSchool,
  getStudentRosterName,
  importSchoolRoster,
  listSchools,
  ownerSchool,
  SchoolError,
  schoolInvitationContact,
} from "./schools.ts";

import { sendStudentCode } from "./otp.ts";

const pathPrefix = "/api/platform/v1";
const noStore = {
  "Cache-Control": "private, no-store",
  "X-Robots-Tag": "noindex, nofollow",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "no-referrer",
  "X-Frame-Options": "DENY",
};
const respond = (data: unknown, status = 200, headers: Record<string, string> = {}) =>
  Response.json(data, { status, headers: { ...noStore, ...headers } });
const uuid = z.string().uuid();
const settingsSchema = z
  .object({
    provider: z.enum(["google", "sms", "razorpay", "ses"]),
    mode: z.enum(["test", "live"]),
    values: z.record(z.string().max(40), z.string().max(4096)),
  })
  .strict();

async function body(request: Request) {
  if (request.headers.get("origin") !== platformOrigin())
    throw new PilotError(403, "This request must come from the DekhoExams panel.");
  if (request.headers.get("content-type")?.split(";")[0] !== "application/json")
    throw new PilotError(415, "Send JSON for this request.");
  const limit = 128 * 1024;
  if (Number(request.headers.get("content-length")) > limit || !request.body)
    throw new PilotError(413, "This import or request is too large.");
  const reader = request.body.getReader(),
    chunks: Uint8Array[] = [];
  let length = 0;
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    length += value.byteLength;
    if (length > limit) {
      await reader.cancel();
      throw new PilotError(413, "This import or request is too large.");
    }
    chunks.push(value);
  }
  try {
    return JSON.parse(Buffer.concat(chunks).toString());
  } catch {
    throw new PilotError(400, "The request body is not valid JSON.");
  }
}

function html(value: string) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
function printable(title: string, content: string) {
  return new Response(
    `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${html(title)}</title>
<style>body{font:17px/1.55 system-ui;color:#142038;background:#f3f5ff;margin:0;padding:6vw}main{max-width:760px;margin:auto;border:3px solid #3e51d2;background:#fff;padding:clamp(20px,5vw,48px)}header{font-size:28px;font-weight:850}header span{color:#ad4a00}h1{font-size:clamp(26px,4vw,40px);line-height:1.1}p,h2,small{overflow-wrap:anywhere}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(125px,1fr));gap:10px}.stats div{border:1px solid #d7deef;padding:10px}dd{font-weight:750;margin:0}small{display:block}@media print{body{padding:0;background:white}.stats div,header,h1{break-inside:avoid}}</style>
<main><header>Dekho<span>Exams</span></header>${content}</main></html>`,
    {
      headers: {
        ...noStore,
        "Content-Type": "text/html; charset=utf-8",
        "Content-Security-Policy":
          "default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
      },
    },
  );
}

function practiceReport(
  name: string,
  date: string,
  result: ReturnType<typeof scoreDiagnostic>,
  medal?: string,
) {
  const accuracy = result.accuracy === null ? "—" : result.accuracy + "%";
  const metrics = [
    ["Score", `${result.score} / ${result.max}`],
    ["Accuracy", accuracy],
    ["Answered", String(result.hits + result.misses)],
    ["Correct", String(result.hits)],
    ["Incorrect", String(result.misses)],
    ["Skipped", String(result.skipped)],
  ];
  return printable(
    "DekhoExams diagnostic report",
    `<h1>JEE Main diagnostic report</h1><p>${html(name)} · ${html(date)}</p>
<dl class="stats">${metrics.map(([label, value]) => `<div><dt>${label}</dt><dd>${value}</dd></div>`).join("")}</dl>
<h2>By subject</h2><ul>${result.subjects.map((s) => `<li>${html(s.subject)} · ${s.hits} of ${s.total} correct</li>`).join("")}</ul>
${medal ? `<p><strong>Practice medal</strong> · ${html(medal)}</p>` : ""}
<h2>Next practice</h2><p>${result.nextTopic ? html(result.nextTopic) : "Try a longer timed mock to check your pace."}</p>
<small>Practice scoring uses +4 correct, −1 incorrect and 0 skipped.</small>`,
  );
}

export async function platformResponse(
  request: Request,
  poolFactory: () => Pool = platformPool,
  keyFactory: () => string = platformKey,
  sms?: Parameters<typeof sendStudentCode>[3],
): Promise<Response> {
  try {
    const path = new URL(request.url).pathname.slice(pathPrefix.length);
    const { method } = request;
    if (!["GET", "POST"].includes(method)) return respond({ error: "Method unavailable." }, 405);
    if (
      !(method === "POST" && ["/activate", "/student-code"].includes(path)) &&
      !validToken(sessionToken(request))
    )
      return respond({ error: "Sign in with your private access link." }, 401);
    if (method === "POST" && request.headers.get("origin") !== platformOrigin())
      throw new PilotError(403, "This request must come from the DekhoExams panel.");
    const pool = poolFactory();
    if (method === "POST" && path === "/student-code") {
      const { token } = z
        .object({
          token: z.string().max(100),
          code: z
            .string()
            .regex(/^\d{6}$/)
            .optional(),
        })
        .strict()
        .parse(await body(request));
      return respond(await sendStudentCode(pool, token, keyFactory(), sms));
    }
    if (method === "POST" && path === "/activate") {
      const input = z
        .object({
          token: z.string().max(100),
          code: z
            .string()
            .regex(/^\d{6}$/)
            .optional(),
        })
        .strict()
        .parse(await body(request));
      const { member, cookie } = await activate(pool, input.token, input.code, keyFactory());
      return respond({ role: member.role, schoolId: member.schoolId }, 200, {
        "Set-Cookie": cookie,
      });
    }
    const member = await resolveMember(pool, request);
    if (!member) return respond({ error: "Sign in with your private access link." }, 401);
    const requireRole = (role: Role) => {
      if (member.role !== role) throw new PilotError(403, "This account cannot access that panel.");
    };
    const key = keyFactory();
    if (method === "GET" && path === "/session")
      return respond({ role: member.role, schoolId: member.schoolId });
    if (method === "POST" && path === "/logout") {
      await body(request);
      await pool.execute("UPDATE de_sessions SET revoked_at=UTC_TIMESTAMP(3) WHERE token_hash=?", [
        tokenDigest(sessionToken(request)!),
      ]);
      return respond({ signedOut: true }, 200, { "Set-Cookie": sessionCookie("", 0) });
    }
    const cursor = new URL(request.url).searchParams.get("after");
    const after = cursor === null ? undefined : uuid.parse(cursor);
    if (method === "GET" && path === "/admin") {
      requireRole("owner");
      const directory = await listSchools(pool, member.id, after);
      const [rows] = await pool.execute<RowDataPacket[]>(
        "SELECT provider,mode,encrypted_values,updated_at FROM de_integration_settings",
      );
      const integrations = rows.map((r) => {
        const provider = r["provider"] as IntegrationName,
          mode = r["mode"] as "test" | "live";
        const values = openSettings(provider, mode, r["encrypted_values"], key);
        return {
          provider,
          mode,
          configured: STUDENT_INTEGRATIONS[provider].fields.map((f) => ({
            field: f.key,
            present: !!values[f.key],
          })),
          updatedAt: (r["updated_at"] as Date).toISOString(),
        };
      });
      return respond({ ...directory, integrations });
    }
    if (method === "POST" && path === "/integrations") {
      requireRole("owner");
      const { provider, mode, values } = settingsSchema.parse(await body(request));
      if (!Object.values(values).some((v) => v.trim()))
        throw new PilotError(400, "Enter at least one value to save.");
      try {
        validateSettings(provider, values);
      } catch (e) {
        throw new PilotError(400, (e as Error).message);
      }
      if (
        provider === "razorpay" &&
        values["keyId"]?.trim() &&
        !values["keyId"].trim().startsWith("rzp_" + mode + "_")
      )
        throw new PilotError(400, "The Razorpay key ID does not match the selected environment.");
      return respond(await saveIntegration(pool, member.id, provider, mode, values, key));
    }
    if (method === "POST" && path === "/schools") {
      requireRole("owner");
      return respond(await createSchool(pool, member.id, await body(request), key), 201);
    }
    if (method === "POST" && path === "/invitations") {
      if (member.role !== "owner" && member.role !== "school")
        throw new PilotError(403, "This account cannot issue access links.");
      const input = await body(request);
      const target =
        member.role === "owner"
          ? z.object({ schoolId: uuid }).strict().parse(input).schoolId
          : z.object({ rosterId: uuid }).strict().parse(input).rosterId;
      const db = await pool.getConnection();
      try {
        await db.beginTransaction();
        if (member.role === "owner") await ownerSchool(db, member.id, target);
        else await schoolInvitationContact(db, member.id, member.schoolId!, target, key);
        const link = await issueInvite(
          db,
          member.role === "owner" ? "school" : "student",
          target,
          member.id,
        );
        await db.commit();
        return respond(link, 201);
      } catch (e) {
        await db.rollback();
        throw e;
      } finally {
        db.release();
      }
    }
    if (method === "GET" && path === "/school") {
      requireRole("school");
      return respond(await getSchool(pool, member.id, member.schoolId!, key, after));
    }
    if (method === "POST" && path === "/roster") {
      requireRole("school");
      const { rows } = z
        .object({ authorized: z.literal(true), rows: z.array(z.unknown()).min(1).max(250) })
        .strict()
        .parse(await body(request));
      return respond(
        await importSchoolRoster(pool, member.id, member.schoolId!, { rows }, key),
        201,
      );
    }
    if (path.startsWith("/student")) {
      requireRole("student");
      if (method === "GET" && path === "/student") {
        const student = await getStudentRosterName(pool, member.id, key);
        const record = await diagnostic(
          pool,
          Buffer.from(key, "base64"),
          member.id,
          member.schoolId!,
          "read",
        );
        return respond({
          ...student,
          attempt: record.attempt,
          award: record.award,
          marketing: { eligible: false, optedIn: false },
        });
      }
      if (method === "POST" && path === "/student/attempt") {
        z.object({})
          .strict()
          .parse(await body(request));
        return respond(
          await diagnostic(pool, Buffer.from(key, "base64"), member.id, member.schoolId!, "start"),
        );
      }
      if (method === "POST" && path === "/student/answers") {
        const input = z
          .object({
            answers: z.record(z.string().max(10), z.number().int()),
            revision: z.number().int().min(0),
            submit: z.boolean().default(false),
          })
          .strict()
          .parse(await body(request));
        return respond(
          await diagnostic(
            pool,
            Buffer.from(key, "base64"),
            member.id,
            member.schoolId!,
            "save",
            input,
          ),
        );
      }
      if (method === "POST" && path === "/student/marketing") {
        const { optedIn } = z
          .object({ optedIn: z.boolean() })
          .strict()
          .parse(await body(request));
        if (optedIn)
          throw new PilotError(
            403,
            "Marketing signup requires separate adult eligibility and email verification.",
          );
        return respond({ optedIn: false });
      }
      if (method === "GET" && (path === "/student/certificate" || path === "/student/report")) {
        const record = await diagnostic(
          pool,
          Buffer.from(key, "base64"),
          member.id,
          member.schoolId!,
          "read",
        );
        if (
          !record.submittedAt ||
          !record.attempt ||
          !("result" in record.attempt) ||
          !record.attempt.result
        )
          throw new PilotError(404, "Submit your diagnostic to open its report.");
        const student = await getStudentRosterName(pool, member.id, key);
        const date = record.submittedAt.toLocaleDateString("en-IN", {
          timeZone: "Asia/Kolkata",
          dateStyle: "long",
        });
        if (path === "/student/report")
          return practiceReport(student.name, date, record.attempt.result, record.award?.medal);
        if (!record.award)
          throw new PilotError(404, "No certificate has been earned for this diagnostic.");
        return printable(
          "DekhoExams diagnostic certificate",
          `<h1>${html(record.award.medal)} medal</h1><p>Practice achievement awarded to</p><h2>${html(student.name)}</h2>
<p>For scoring <strong>${record.attempt.result.score} / ${record.attempt.result.max}</strong> on the DekhoExams six-question diagnostic.</p>
<p>${html(date)}</p><small>Certificate reference ${html(record.attempt.id)}</small>
<small>Private practice achievement. No exam qualification or accreditation is awarded.</small>`,
        );
      }
    }
    return respond({ error: "Panel route unavailable." }, 404);
  } catch (e) {
    if (e instanceof PilotError || e instanceof SchoolError)
      return respond(
        {
          error: e.message,
          ...(e instanceof SchoolError && e.details ? { details: e.details } : {}),
        },
        e.status,
      );
    if (e instanceof ZodError)
      return respond({ error: "Check the required fields and try again." }, 400);
    // No user input, database error text or secrets in the service log.
    console.error("Platform request failed.");
    return respond({ error: "The panel is temporarily unavailable." }, 503);
  }
}

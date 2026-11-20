import { createHmac } from "node:crypto";
import type { Pool, RowDataPacket } from "mysql2/promise";
import { z } from "zod";
import { decryptRecord, encryptRecord } from "./crypto.ts";
import { PilotError } from "./diagnostic.ts";

const kind = z.enum(["student", "parent", "school"]);
const status = z.enum(["new", "contacted"]);
const id = z.string().regex(/^[1-9]\d{0,14}$/);
const email = z
  .string()
  .trim()
  .max(254)
  .email()
  .transform((value) => value.toLowerCase());
const text = (max: number) =>
  z
    .string()
    .trim()
    .min(1)
    .max(max)
    .refine((value) => !/[\u0000-\u001f\u007f]/u.test(value));
const inquiry = z
  .object({
    kind,
    name: text(120),
    email,
    school: z.string().trim().max(180),
    adult: z.literal(true),
    contactPermission: z.literal(true),
    website: z.string().max(100).default(""),
  })
  .strict()
  .refine((value) => value.kind !== "school" || !!value.school, { path: ["school"] });
type Contact = Pick<z.output<typeof inquiry>, "name" | "email" | "school">;
const consentVersion = "access-inquiry-v1";
const contactHash = (key: Buffer, value: string) =>
  createHmac("sha256", key)
    .update("lead-email:" + value)
    .digest();

export async function saveLead(pool: Pool, key: Buffer, input: unknown) {
  const { name, email: address, school, kind: audience, website } = inquiry.parse(input);
  if (website) return { received: true };
  const hash = contactHash(key, address);
  const db = await pool.getConnection();
  try {
    await db.beginTransaction();
    await db.execute(
      "INSERT INTO de_platform_lead_budget(utc_day) VALUES(UTC_DATE()) ON DUPLICATE KEY UPDATE utc_day=utc_day",
    );
    const [[budget]] = await db.execute<RowDataPacket[]>(
      "SELECT submissions FROM de_platform_lead_budget WHERE utc_day=UTC_DATE() FOR UPDATE",
    );
    // shortcut: bounded pilot intake, add edge bot protection before opening high-volume signup.
    if (Number(budget?.["submissions"] ?? 400) >= 400)
      throw new PilotError(429, "Requests are full today. Please try again tomorrow.");
    const [[existing]] = await db.execute<RowDataPacket[]>(
      "SELECT id FROM de_platform_leads WHERE kind=? AND contact_hash=?",
      [audience, hash],
    );
    if (!existing) {
      await db.execute(
        `INSERT INTO de_platform_leads(kind,contact_hash,encrypted_fields,consent_version)
         VALUES(?,?,?,?)`,
        [
          audience,
          hash,
          encryptRecord<Contact>(key, "lead:" + audience + ":" + hash.toString("hex"), {
            name,
            email: address,
            school: audience === "school" ? school : "",
          }),
          consentVersion,
        ],
      );
      await db.execute(
        "UPDATE de_platform_lead_budget SET submissions=submissions+1 WHERE utc_day=UTC_DATE()",
      );
    }
    await db.commit();
  } catch (error) {
    await db.rollback();
    throw error;
  } finally {
    db.release();
  }
  return { received: true };
}

export async function listLeads(pool: Pool, key: Buffer, input: unknown) {
  const filters = z
    .object({
      kind: kind.optional(),
      status: status.optional(),
      email: email.optional(),
      before: id.optional(),
    })
    .strict()
    .parse(input);
  const where = [];
  const args = [];
  if (filters.kind) {
    where.push("kind=?");
    args.push(filters.kind);
  }
  if (filters.status) {
    where.push("status=?");
    args.push(filters.status);
  }
  if (filters.email) {
    where.push("contact_hash=?");
    args.push(contactHash(key, filters.email));
  }
  if (filters.before) {
    where.push("id<?");
    args.push(filters.before);
  }
  const [rows] = await pool.execute<RowDataPacket[]>(
    `SELECT CAST(id AS CHAR) AS id,kind,status,contact_hash,encrypted_fields,created_at
     FROM de_platform_leads ${where.length ? "WHERE " + where.join(" AND ") : ""}
     ORDER BY de_platform_leads.id DESC LIMIT 51`,
    args,
  );
  const items = rows.slice(0, 50).map((row) => {
    const audience = kind.parse(row["kind"]);
    const hash = (row["contact_hash"] as Buffer).toString("hex");
    return {
      id: id.parse(row["id"]),
      kind: audience,
      status: status.parse(row["status"]),
      createdAt: (row["created_at"] as Date).toISOString(),
      ...decryptRecord<Contact>(key, "lead:" + audience + ":" + hash, row["encrypted_fields"]),
    };
  });
  return { leads: items, nextCursor: rows.length > 50 ? items.at(-1)?.id : null };
}

export async function setLeadStatus(pool: Pool, input: unknown) {
  const value = z.object({ id, status }).strict().parse(input);
  await pool.execute("UPDATE de_platform_leads SET status=? WHERE id=?", [value.status, value.id]);
  return { saved: true };
}

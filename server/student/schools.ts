import { createHash, createHmac, randomBytes, randomUUID } from "node:crypto";
import type { Pool, PoolConnection, ResultSetHeader, RowDataPacket } from "mysql2/promise";
import { z } from "zod";
import { decryptRecord, encryptRecord } from "./crypto.ts";

const PAGE_SIZE = 50;
export const ROSTER_IMPORT_LIMIT = 250;
const UUID = /^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/;
const text = (max: number) =>
  z
    .string()
    .trim()
    .min(1)
    .max(max)
    .refine((value) => !/[\x00-\x1f\x7f]/.test(value), "Enter plain text.");

const schoolInput = z
  .object({
    name: text(180),
    state: text(80),
    city: text(100),
    exam: z.literal("jee-main"),
    redemptionLimit: z.number().int().min(1).max(100_000),
    expiresAt: z.string().regex(/^20\d{2}-\d{2}-\d{2}$/),
  })
  .strict();

const rosterRow = z
  .object({
    name: text(120),
    mobile: z
      .string()
      .min(1)
      .max(32)
      .transform((value) => {
        const compact = value.trim().replace(/[ -]/g, "");
        return /^[6-9]\d{9}$/.test(compact)
          ? `+91${compact}`
          : /^91[6-9]\d{9}$/.test(compact)
            ? `+${compact}`
            : compact;
      })
      .pipe(z.string().regex(/^\+91[6-9]\d{9}$/, "Enter a valid Indian mobile number.")),
    email: z
      .string()
      .trim()
      .max(254)
      .pipe(z.union([z.literal(""), z.string().email("Enter a valid email address.")]))
      .optional(),
    level: z.enum(["", "10", "11", "12", "graduation", "masters"]).optional(),
  })
  .strict();
type RosterContact = z.output<typeof rosterRow>;
type School = { id: string; name: string; state: string; city: string };
interface SchoolRow extends RowDataPacket, School {}
interface CouponRow extends RowDataPacket {
  id: string;
  exam: string | null;
  active: number;
  starts_at: Date;
  expires_at: Date;
  redemption_limit: number;
  used: number;
  encrypted_code: Buffer;
}
interface RosterRow extends RowDataPacket {
  id: string;
  phone_hash: Buffer;
  encrypted_fields: Buffer;
  access: "activated" | "invited" | "none";
}

export class SchoolError extends Error {
  status: number;
  details?: { row: number; fields: string[] }[];
  constructor(status: number, message: string, details?: { row: number; fields: string[] }[]) {
    super(message);
    this.status = status;
    if (details) this.details = details;
  }
}

function keyFrom(encoded: string, purpose: "encrypt" | "lookup") {
  const key = Buffer.from(encoded, "base64");
  if (key.length !== 32 || key.toString("base64") !== encoded)
    throw Error("A 32-byte server encryption key is required.");
  return createHmac("sha256", key).update(`dekhoexams:schools:v1:${purpose}`).digest();
}

function scopeId(id: string) {
  if (typeof id !== "string" || !UUID.test(id))
    throw new SchoolError(404, "School record not found.");
  return id;
}

function cursorId(after?: string) {
  if (!after) return "";
  if (!UUID.test(after)) throw new SchoolError(400, "Invalid page cursor.");
  return after;
}

async function assertOwner(db: Pool | PoolConnection, actorId: string, lock = false) {
  const [rows] = await db.execute<RowDataPacket[]>(
    `SELECT a.student_id FROM de_admin_roles a
    JOIN de_students s ON s.id=a.student_id AND s.status='active'
    WHERE a.student_id=? AND a.role='owner'${lock ? " FOR UPDATE" : ""}`,
    [actorId],
  );
  if (!rows.length) throw new SchoolError(403, "Owner access is required.");
}

async function staffSchool(
  db: Pool | PoolConnection,
  actorId: string,
  schoolId: string,
  lock: "read" | "write",
) {
  const [schools] = await db.execute<SchoolRow[]>(
    `SELECT s.id,s.name,s.state,s.city FROM de_school_staff m
    JOIN de_schools s ON s.id=m.school_id AND s.active=TRUE
    JOIN de_students a ON a.id=m.student_id AND a.status='active'
    WHERE m.student_id=? AND m.school_id=?${lock === "write" ? " FOR UPDATE" : " FOR SHARE"}`,
    [actorId, scopeId(schoolId)],
  );
  // A nonexistent school and one belonging to somebody else are indistinguishable to staff.
  if (!schools[0]) throw new SchoolError(404, "School record not found.");
  return schools[0];
}

export async function ownerSchool(
  db: PoolConnection,
  actorId: string,
  schoolId: string,
): Promise<School> {
  await assertOwner(db, actorId, true);
  const [schools] = await db.execute<SchoolRow[]>(
    "SELECT id,name,state,city FROM de_schools WHERE id=? AND active=TRUE FOR UPDATE",
    [scopeId(schoolId)],
  );
  if (!schools[0]) throw new SchoolError(404, "School record not found.");
  return schools[0];
}

export async function listSchools(pool: Pool, actorId: string, after?: string) {
  await assertOwner(pool, actorId);
  const [records] = await pool.execute<SchoolRow[]>(
    "SELECT id,name,state,city FROM de_schools WHERE id>? ORDER BY id LIMIT 51",
    [cursorId(after)],
  );
  const schools = records.slice(0, PAGE_SIZE);
  return { schools, nextCursor: records.length > PAGE_SIZE ? schools.at(-1)!.id : null };
}

export async function listMySchools(pool: Pool, actorId: string) {
  const [schools] = await pool.execute<SchoolRow[]>(
    `SELECT s.id,s.name,s.state,s.city FROM de_school_staff m
    JOIN de_schools s ON s.id=m.school_id AND s.active=TRUE
    JOIN de_students a ON a.id=m.student_id AND a.status='active'
    WHERE m.student_id=? ORDER BY s.id LIMIT 50`,
    [actorId],
  );
  return { schools };
}

export async function createSchool(
  pool: Pool,
  actorId: string,
  input: unknown,
  encryptionKey: string,
) {
  const result = schoolInput.safeParse(input);
  if (!result.success)
    throw new SchoolError(
      422,
      "Enter the school details, an exam, a valid date and a student limit.",
    );
  const { name, state, city, exam, redemptionLimit, expiresAt } = result.data;
  const day = new Date(`${expiresAt}T00:00:00Z`);
  if (!Number.isFinite(day.getTime()) || day.toISOString().slice(0, 10) !== expiresAt)
    throw new SchoolError(422, "Enter a valid expiry date.");
  // The selected date is inclusive in India. Store the exclusive next-midnight timestamp in UTC.
  const expires = new Date(`${expiresAt}T00:00:00+05:30`);
  expires.setTime(expires.getTime() + 86_400_000);
  if (expires.getTime() <= Date.now())
    throw new SchoolError(422, "Choose an expiry date that has not passed.");
  const schoolId = randomUUID();
  const couponId = randomUUID();
  const code = `SCHOOL-${randomBytes(16).toString("hex").toUpperCase()}`;
  const codeHash = createHash("sha256").update(code).digest();
  const encryptedCode = encryptRecord(
    keyFrom(encryptionKey, "encrypt"),
    `coupon:${schoolId}:${couponId}`,
    code,
  );

  const db = await pool.getConnection();
  try {
    await db.beginTransaction();
    await assertOwner(db, actorId, true);
    await db.execute("INSERT INTO de_schools(id,name,state,city) VALUES(?,?,?,?)", [
      schoolId,
      name,
      state,
      city,
    ]);
    await db.execute(
      `INSERT INTO de_coupons(id,code_hash,kind,school_id,exam,starts_at,expires_at,redemption_limit)
      VALUES(?,?,'school',?,?,UTC_TIMESTAMP(3),?,?)`,
      [couponId, codeHash, schoolId, exam, expires, redemptionLimit],
    );
    await db.execute(
      "INSERT INTO de_school_coupon_defaults(school_id,coupon_id,encrypted_code) VALUES(?,?,?)",
      [schoolId, couponId, encryptedCode],
    );
    await db.execute(
      "INSERT INTO de_audit(actor_id,action,target_id) VALUES(?,'school.created',?)",
      [actorId, schoolId],
    );
    await db.commit();
    return {
      school: { id: schoolId, name, state, city },
      coupon: {
        id: couponId,
        code,
        exam,
        active: true,
        expiresAt: expires.toISOString(),
        limit: redemptionLimit,
        used: 0,
      },
    };
  } catch (error) {
    await db.rollback();
    throw error;
  } finally {
    db.release();
  }
}

function contactFor(row: RosterRow, schoolId: string, key: Buffer): RosterContact {
  return rosterRow.parse(decryptRecord(key, `roster:${schoolId}:${row.id}`, row.encrypted_fields));
}

export async function getSchool(
  pool: Pool,
  actorId: string,
  schoolId: string,
  encryptionKey: string,
  after?: string,
) {
  const key = keyFrom(encryptionKey, "encrypt");
  const db = await pool.getConnection();
  try {
    await db.beginTransaction();
    const school = await staffSchool(db, actorId, schoolId, "read");
    const [codes] = await db.execute<CouponRow[]>(
      `SELECT c.id,c.exam,c.active,c.starts_at,c.expires_at,c.redemption_limit,c.used,d.encrypted_code
      FROM de_school_coupon_defaults d JOIN de_coupons c ON c.id=d.coupon_id AND c.school_id=d.school_id AND c.kind='school'
      WHERE d.school_id=?`,
      [schoolId],
    );
    const current = codes[0];
    const now = Date.now();
    const coupon = current
      ? {
          id: current.id,
          code: decryptRecord<string>(
            key,
            `coupon:${schoolId}:${current.id}`,
            current.encrypted_code,
          ),
          exam: current.exam,
          active:
            Boolean(current.active) &&
            current.starts_at.getTime() <= now &&
            current.expires_at.getTime() > now &&
            current.used < current.redemption_limit,
          expiresAt: current.expires_at.toISOString(),
          limit: current.redemption_limit,
          used: current.used,
        }
      : null;
    const [records] = await db.execute<RosterRow[]>(
      `SELECT r.id,r.encrypted_fields,CASE WHEN a.roster_id IS NOT NULL THEN 'activated'
       WHEN EXISTS(SELECT 1 FROM de_platform_invites i WHERE i.target_kind='student' AND i.target_id=r.id
         AND i.consumed_at IS NULL AND i.expires_at>UTC_TIMESTAMP(3)) THEN 'invited' ELSE 'none' END AS access
       FROM de_school_roster r LEFT JOIN de_platform_roster_accounts a ON a.roster_id=r.id
       WHERE r.school_id=? AND r.id>? ORDER BY r.id LIMIT 51`,
      [schoolId, cursorId(after)],
    );
    const roster = records.slice(0, PAGE_SIZE).map((row) => {
      const contact = contactFor(row, schoolId, key);
      return {
        id: row.id,
        name: contact.name,
        mobile: `••••••${contact.mobile.slice(-4)}`,
        email: contact.email ? `${contact.email[0]}•••@•••` : "",
        level: contact.level ?? "",
        access: row.access,
      };
    });
    const [[progress]] = await db.execute<RowDataPacket[]>(
      `SELECT COUNT(*) AS enrolled, COUNT(a.student_id) AS activated,
              COUNT(d.id) AS started, COUNT(d.submitted_at) AS completed
       FROM de_school_roster r
       LEFT JOIN de_platform_roster_accounts a ON a.roster_id=r.id
       LEFT JOIN de_platform_diagnostics d ON d.student_id=a.student_id
       WHERE r.school_id=?`,
      [schoolId],
    );
    await db.commit();
    return {
      school,
      coupon,
      roster,
      progress: {
        enrolled: Number(progress?.["enrolled"] ?? 0),
        activated: Number(progress?.["activated"] ?? 0),
        started: Number(progress?.["started"] ?? 0),
        completed: Number(progress?.["completed"] ?? 0),
      },
      nextCursor: records.length > PAGE_SIZE ? roster.at(-1)!.id : null,
    };
  } catch (error) {
    await db.rollback();
    throw error;
  } finally {
    db.release();
  }
}

export async function importSchoolRoster(
  pool: Pool,
  actorId: string,
  schoolId: string,
  input: unknown,
  encryptionKey: string,
) {
  const batch = z
    .object({ rows: z.array(z.unknown()).min(1).max(ROSTER_IMPORT_LIMIT) })
    .strict()
    .safeParse(input);
  if (!batch.success)
    throw new SchoolError(422, `Upload between 1 and ${ROSTER_IMPORT_LIMIT} student rows.`);
  const rows = new Map<string, RosterContact>();
  const errors: { row: number; fields: string[] }[] = [];
  batch.data.rows.forEach((row, index) => {
    const parsed = rosterRow.safeParse(row);
    if (!parsed.success) {
      errors.push({
        row: index + 1,
        fields: [...new Set(parsed.error.issues.map((issue) => String(issue.path[0] ?? "row")))],
      });
    } else if (!rows.has(parsed.data.mobile)) {
      rows.set(parsed.data.mobile, parsed.data);
    }
  });
  if (errors.length)
    throw new SchoolError(
      422,
      "Correct the highlighted rows and upload again. No rows were saved.",
      errors,
    );

  const encryptKey = keyFrom(encryptionKey, "encrypt");
  const lookupKey = keyFrom(encryptionKey, "lookup");
  scopeId(schoolId);
  const entries = [...rows.values()].map((contact) => {
    const id = randomUUID();
    const phoneHash = createHmac("sha256", lookupKey)
      .update(`${schoolId}:${contact.mobile}`)
      .digest();
    return {
      id,
      phoneHash,
      data: encryptRecord(encryptKey, `roster:${schoolId}:${id}`, contact),
    };
  });
  const db = await pool.getConnection();
  try {
    await db.beginTransaction();
    // All imports for one school lock its row before checking duplicates, so retries cannot overwrite an invite's roster row.
    await staffSchool(db, actorId, schoolId, "write");
    const [prior] = await db.execute<RosterRow[]>(
      `SELECT phone_hash FROM de_school_roster WHERE school_id=?
      AND phone_hash IN (${entries.map(() => "?").join(",")})`,
      [schoolId, ...entries.map((item) => item.phoneHash)],
    );
    const existing = new Set(prior.map((row) => row.phone_hash.toString("hex")));
    const additions = entries.filter((item) => !existing.has(item.phoneHash.toString("hex")));
    if (additions.length) {
      const [insert] = await db.execute<ResultSetHeader>(
        `INSERT INTO de_school_roster(id,school_id,phone_hash,encrypted_fields) VALUES ${additions.map(() => "(?,?,?,?)").join(",")}`,
        additions.flatMap((item) => [item.id, schoolId, item.phoneHash, item.data]),
      );
      if (insert.affectedRows !== additions.length)
        throw Error("School import did not save every new row.");
      await db.execute(
        "INSERT INTO de_audit(actor_id,action,target_id) VALUES(?,'school.roster.imported',?)",
        [actorId, schoolId],
      );
    }
    await db.commit();
    return {
      added: additions.length,
      duplicates: batch.data.rows.length - additions.length,
      total: batch.data.rows.length,
    };
  } catch (error) {
    await db.rollback();
    throw error;
  } finally {
    db.release();
  }
}

// Call in the invitation write transaction. Unmasked contact fields must stay on the server.
export async function schoolInvitationContact(
  db: PoolConnection,
  actorId: string,
  schoolId: string,
  rosterId: string,
  encryptionKey: string,
) {
  await staffSchool(db, actorId, schoolId, "write");
  const [rows] = await db.execute<RosterRow[]>(
    "SELECT id,encrypted_fields FROM de_school_roster WHERE school_id=? AND id=? FOR UPDATE",
    [schoolId, scopeId(rosterId)],
  );
  if (!rows[0]) throw new SchoolError(404, "School record not found.");
  return contactFor(rows[0], schoolId, keyFrom(encryptionKey, "encrypt"));
}

export async function getStudentRosterName(pool: Pool, studentId: string, encryptionKey: string) {
  const [rows] = await pool.execute<(RosterRow & { school_id: string; school_name: string })[]>(
    `SELECT r.id,r.school_id,r.encrypted_fields,s.name AS school_name
     FROM de_platform_roster_accounts a JOIN de_school_roster r ON r.id=a.roster_id
     JOIN de_schools s ON s.id=r.school_id AND s.active=TRUE
     JOIN de_students student ON student.id=a.student_id AND student.status='active'
     WHERE a.student_id=?`,
    [studentId],
  );
  const row = rows[0];
  if (!row) throw new SchoolError(404, "Student record not found.");
  return {
    name: contactFor(row, row.school_id, keyFrom(encryptionKey, "encrypt")).name,
    schoolName: row.school_name,
  };
}

// Only called after a live student invitation has selected and locked its roster.
export async function studentInvitationMobile(
  db: PoolConnection,
  rosterId: string,
  encryptionKey: string,
) {
  const [[row]] = await db.execute<(RosterRow & { school_id: string })[]>(
    `SELECT r.id,r.school_id,r.encrypted_fields FROM de_school_roster r
    JOIN de_schools s ON s.id=r.school_id AND s.active=TRUE WHERE r.id=? FOR UPDATE`,
    [rosterId],
  );
  if (!row) throw new SchoolError(404, "Student record not found.");
  return contactFor(row, row.school_id, keyFrom(encryptionKey, "encrypt")).mobile;
}

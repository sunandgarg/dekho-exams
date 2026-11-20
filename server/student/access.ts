import { randomUUID } from "node:crypto";
import type { Pool, PoolConnection, RowDataPacket } from "mysql2/promise";
import { newToken, tokenDigest, validToken } from "./crypto.ts";
import { PilotError } from "./diagnostic.ts";
import { checkStudentProof } from "./otp.ts";

export type Role = "owner" | "school" | "student";
export type Member = { id: string; role: Role; schoolId?: string; rosterId?: string };
export const platformOrigin = () => process.env["PLATFORM_ORIGIN"] ?? "https://dekhoexams.com";
const cookieName = "__Secure-de_platform";
const cookiePath = "/api/platform/v1";

export function sessionToken(request: Request) {
  const cookie = (request.headers.get("cookie") ?? "")
    .split(";")
    .map((p) => p.trim())
    .find((p) => p.startsWith(cookieName + "="));
  return cookie?.slice(cookieName.length + 1);
}
export function sessionCookie(token: string, maxAge: number) {
  return `${cookieName}=${token}; Path=${cookiePath}; HttpOnly; Secure; SameSite=Strict; Max-Age=${maxAge}`;
}
export async function resolveMember(pool: Pool, request: Request): Promise<Member | null> {
  const token = sessionToken(request);
  if (!validToken(token)) return null;
  const [[row]] = await pool.execute<RowDataPacket[]>(
    `SELECT st.id,a.role,s.id AS staff_school,r.id AS roster_id,
    r.school_id AS student_school FROM de_sessions t JOIN de_students st ON st.id=t.student_id AND st.status='active'
    LEFT JOIN de_admin_roles a ON a.student_id=st.id AND a.role='owner'
    LEFT JOIN de_school_staff sf ON sf.student_id=st.id
    LEFT JOIN de_schools s ON s.id=sf.school_id AND s.active=TRUE
    LEFT JOIN de_platform_roster_accounts b ON b.student_id=st.id
    LEFT JOIN de_school_roster r ON r.id=b.roster_id
    LEFT JOIN de_schools rs ON rs.id=r.school_id AND rs.active=TRUE
    WHERE token_hash=? AND t.expires_at>UTC_TIMESTAMP(3) AND t.revoked_at IS NULL
      AND (a.role='owner' OR s.id IS NOT NULL OR rs.id IS NOT NULL)`,
    [tokenDigest(token)],
  );
  if (!row) return null;
  if (row["role"] === "owner") return { id: row["id"], role: "owner" };
  if (row["staff_school"]) return { id: row["id"], role: "school", schoolId: row["staff_school"] };
  return {
    id: row["id"],
    role: "student",
    schoolId: row["student_school"],
    rosterId: row["roster_id"],
  };
}
export async function issueInvite(
  db: PoolConnection,
  role: Role,
  targetId: string,
  actorId: string,
) {
  const token = newToken(),
    lifespan = role === "owner" ? 1800 : 86400;
  await db.execute(
    "UPDATE de_platform_invites SET consumed_at=UTC_TIMESTAMP(3) WHERE target_kind=? AND target_id=? AND consumed_at IS NULL",
    [role, targetId],
  );
  const expiresAt = new Date(Date.now() + lifespan * 1000);
  await db.execute(
    "INSERT INTO de_platform_invites(token_hash,target_kind,target_id,expires_at) VALUES(?,?,?,?)",
    [tokenDigest(token), role, targetId, expiresAt],
  );
  await db.execute("INSERT INTO de_audit(actor_id,action,target_id) VALUES(?,?,?)", [
    actorId,
    "invite." + role,
    targetId,
  ]);
  return {
    url: `${platformOrigin()}/platform-${role === "owner" ? "admin" : role}#invite=${token}`,
    expiresAt: expiresAt.toISOString(),
  };
}

export async function activate(pool: Pool, token: unknown, code: unknown, key: string) {
  if (!validToken(token)) throw new PilotError(401, "This access link is invalid or expired.");
  const db = await pool.getConnection();
  try {
    await db.beginTransaction();
    const digest = tokenDigest(token);
    const [[invite]] = await db.execute<RowDataPacket[]>(
      `SELECT target_kind,target_id FROM de_platform_invites
      WHERE token_hash=? AND consumed_at IS NULL AND expires_at>UTC_TIMESTAMP(3)`,
      [digest],
    );
    if (!invite)
      throw new PilotError(401, "This access link was used or expired. Request a fresh link.");
    const role = invite["target_kind"] as Role,
      target = String(invite["target_id"]);
    let member: Member;
    if (role === "owner") {
      const [[owner]] = await db.execute<RowDataPacket[]>(
        `SELECT st.id FROM de_students st JOIN de_admin_roles a
        ON a.student_id=st.id WHERE st.id=? AND st.status='active' AND a.role='owner' FOR UPDATE`,
        [target],
      );
      if (!owner) throw new PilotError(403, "Owner access is inactive.");
      member = { id: target, role };
    } else {
      const targetSql =
        role === "school"
          ? "SELECT id AS school_id FROM de_schools WHERE id=? AND active=TRUE FOR UPDATE"
          : "SELECT s.id AS school_id FROM de_schools s JOIN de_school_roster r ON r.school_id=s.id WHERE r.id=? AND s.active=TRUE FOR UPDATE";
      const [[school]] = await db.execute<RowDataPacket[]>(targetSql, [target]);
      if (!school) throw new PilotError(403, "School access is inactive.");
      if (role === "student") {
        const [[active]] = await db.execute<RowDataPacket[]>(
          "SELECT token_hash FROM de_platform_invites WHERE token_hash=? AND consumed_at IS NULL AND expires_at>UTC_TIMESTAMP(3) FOR UPDATE",
          [digest],
        );
        if (!active || !(await checkStudentProof(db, target, digest, code, key))) {
          await db.commit();
          throw new PilotError(401, "Enter the current code sent to the registered mobile.");
        }
      }
      const lookup =
        role === "school"
          ? "SELECT student_id FROM de_school_staff WHERE school_id=? ORDER BY student_id LIMIT 1 FOR UPDATE"
          : "SELECT student_id FROM de_platform_roster_accounts WHERE roster_id=? FOR UPDATE";
      const [[old]] = await db.execute<RowDataPacket[]>(lookup, [target]);
      const id = old ? String(old["student_id"]) : randomUUID();
      if (!old) {
        await db.execute("INSERT INTO de_students(id,status) VALUES(?,'active')", [id]);
        if (role === "school")
          await db.execute("INSERT INTO de_school_staff(school_id,student_id) VALUES(?,?)", [
            target,
            id,
          ]);
        else
          await db.execute(
            "INSERT INTO de_platform_roster_accounts(roster_id,student_id) VALUES(?,?)",
            [target, id],
          );
      } else {
        const [[student]] = await db.execute<RowDataPacket[]>(
          "SELECT status FROM de_students WHERE id=? FOR UPDATE",
          [id],
        );
        if (student?.["status"] !== "active")
          throw new PilotError(403, "Account access is inactive.");
      }
      member = {
        id,
        role,
        schoolId: school["school_id"],
        ...(role === "student" ? { rosterId: target } : {}),
      };
    }
    const [[current]] = await db.execute<RowDataPacket[]>(
      "SELECT token_hash FROM de_platform_invites WHERE token_hash=? AND consumed_at IS NULL AND expires_at>UTC_TIMESTAMP(3) FOR UPDATE",
      [digest],
    );
    if (!current)
      throw new PilotError(401, "This access link was used or expired. Request a fresh link.");
    const session = newToken(),
      age = role === "student" ? 7 * 86400 : 8 * 3600;
    await db.execute(
      "UPDATE de_platform_invites SET consumed_at=UTC_TIMESTAMP(3) WHERE token_hash=?",
      [digest],
    );
    // A replacement link rotates access, including after a link was delivered to the wrong person.
    await db.execute(
      "UPDATE de_sessions SET revoked_at=UTC_TIMESTAMP(3) WHERE student_id=? AND revoked_at IS NULL",
      [member.id],
    );
    await db.execute(
      "INSERT INTO de_sessions(token_hash,student_id,client,expires_at) VALUES(?,?,'web',?)",
      [tokenDigest(session), member.id, new Date(Date.now() + age * 1000)],
    );
    await db.execute(
      "INSERT INTO de_audit(actor_id,action,target_id) VALUES(?,'invite.activated',?)",
      [member.id, target],
    );
    await db.commit();
    return { member, cookie: sessionCookie(session, age) };
  } catch (e) {
    await db.rollback();
    throw e;
  } finally {
    db.release();
  }
}

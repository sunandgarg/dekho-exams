import { createHmac, randomInt, timingSafeEqual } from "node:crypto";
import type { Pool, PoolConnection, RowDataPacket } from "mysql2/promise";
import { tokenDigest, validToken } from "./crypto.ts";
import { PilotError } from "./diagnostic.ts";
import { openSettings } from "./integrations.ts";
import { studentInvitationMobile } from "./schools.ts";

function otpHash(key: string, invite: Buffer, code: string) {
  return createHmac("sha256", Buffer.from(key, "base64"))
    .update("dekhoexams:student-otp:v1")
    .update(invite)
    .update(code)
    .digest();
}

type Sms = (mobile: string, code: string, settings: Record<string, string>) => Promise<void>;
const msg91Send: Sms = async (mobile, code, settings) => {
  const endpoint = new URL("https://control.msg91.com/api/v5/otp");
  endpoint.search = new URLSearchParams({
    template_id: settings["templateId"]!,
    mobile: mobile.replace(/^\+/, ""),
    otp: code,
    otp_length: "6",
    otp_expiry: "5",
  }).toString();
  try {
    const response = await fetch(endpoint, {
      method: "POST",
      redirect: "error",
      signal: AbortSignal.timeout(8000),
      headers: { authkey: settings["authKey"]!, "Content-Type": "application/json" },
      body: "{}",
    });
    if (!response.ok || (await response.json())?.type !== "success")
      throw Error("Provider rejected message");
  } catch {
    throw new PilotError(503, "The code could not be sent. Please wait a minute and try again.");
  }
};

export async function sendStudentCode(
  pool: Pool,
  token: unknown,
  key: string,
  send: Sms = msg91Send,
) {
  if (!validToken(token)) throw new PilotError(401, "This access link is invalid or expired.");
  const digest = tokenDigest(token);
  const db = await pool.getConnection();
  let mobile: string, settings: Record<string, string>;
  const code = String(randomInt(1_000_000)).padStart(6, "0");
  try {
    await db.beginTransaction();
    const [[target]] = await db.execute<RowDataPacket[]>(
      "SELECT target_id FROM de_platform_invites WHERE token_hash=? AND target_kind='student' AND consumed_at IS NULL AND expires_at>UTC_TIMESTAMP(3)",
      [digest],
    );
    if (!target)
      throw new PilotError(401, "This access link was used or expired. Request a fresh link.");
    const rosterId = String(target["target_id"]);
    mobile = await studentInvitationMobile(db, rosterId, key);
    const [[active]] = await db.execute<RowDataPacket[]>(
      "SELECT token_hash FROM de_platform_invites WHERE token_hash=? AND consumed_at IS NULL AND expires_at>UTC_TIMESTAMP(3) FOR UPDATE",
      [digest],
    );
    if (!active)
      throw new PilotError(401, "This access link was used or expired. Request a fresh link.");
    const [[saved]] = await db.execute<RowDataPacket[]>(
      "SELECT encrypted_values FROM de_integration_settings WHERE provider='sms' AND mode='live'",
    );
    settings = saved ? openSettings("sms", "live", saved["encrypted_values"], key) : {};
    if (!settings["authKey"] || !settings["templateId"])
      throw new PilotError(503, "The school sign-in SMS service is being set up.");
    const [[previous]] = await db.execute<RowDataPacket[]>(
      "SELECT next_send_at FROM de_platform_otp WHERE roster_id=? FOR UPDATE",
      [rosterId],
    );
    if (previous && new Date(previous["next_send_at"]).getTime() > Date.now())
      throw new PilotError(429, "Wait a minute before requesting another code.");
    await db.execute(
      "INSERT INTO de_platform_sms_budget(utc_day,sends) VALUES(UTC_DATE(),0) ON DUPLICATE KEY UPDATE sends=sends",
    );
    const [reserved] = await db.execute<import("mysql2/promise").ResultSetHeader>(
      "UPDATE de_platform_sms_budget SET sends=sends+1 WHERE utc_day=UTC_DATE() AND sends<250",
    );
    if (!reserved.affectedRows)
      throw new PilotError(429, "The daily sign-in code limit has been reached.");
    await db.execute(
      `INSERT INTO de_platform_otp(roster_id,invite_hash,code_hash,expires_at,next_send_at,attempts)
      VALUES(?,?,?,UTC_TIMESTAMP(3)+INTERVAL 5 MINUTE,UTC_TIMESTAMP(3)+INTERVAL 60 SECOND,0)
      ON DUPLICATE KEY UPDATE invite_hash=VALUES(invite_hash),code_hash=VALUES(code_hash),
      expires_at=VALUES(expires_at),next_send_at=VALUES(next_send_at),attempts=0`,
      [rosterId, digest, otpHash(key, digest, code)],
    );
    await db.commit();
  } catch (e) {
    await db.rollback();
    throw e;
  } finally {
    db.release();
  }
  await send(mobile, code, settings);
  return { sent: true };
}

// Call after locking the roster and current invitation. Failed proofs commit only the retry counter.
export async function checkStudentProof(
  db: PoolConnection,
  rosterId: string,
  digest: Buffer,
  code: unknown,
  key: string,
) {
  if (typeof code !== "string" || !/^\d{6}$/.test(code)) return false;
  const [[challenge]] = await db.execute<RowDataPacket[]>(
    "SELECT code_hash FROM de_platform_otp WHERE roster_id=? AND invite_hash=? AND attempts<5 AND expires_at>UTC_TIMESTAMP(3) FOR UPDATE",
    [rosterId, digest],
  );
  if (!challenge) return false;
  await db.execute("UPDATE de_platform_otp SET attempts=attempts+1 WHERE roster_id=?", [rosterId]);
  return timingSafeEqual(challenge["code_hash"], otpHash(key, digest, code));
}

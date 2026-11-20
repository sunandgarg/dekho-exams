import { createHash, randomUUID } from "node:crypto";
import type { Pool, RowDataPacket } from "mysql2/promise";
import {
  couponCode,
  quoteAccess,
  OfferError,
  type OfferStudent,
  type Coupon,
} from "../../src/lib/student-offers.ts";

// Internal service: studentId must come from a verified server session, never the request body.
export async function grantFreeAttempt(
  pool: Pool,
  studentId: string,
  test: { id: string; exam: string },
  code: string,
  retryKey: string,
) {
  if (
    !/^[a-zA-Z0-9_-]{16,80}$/.test(retryKey) ||
    !/^[a-z0-9-]{1,120}$/.test(test.id) ||
    !/^[a-z0-9-]{1,50}$/.test(test.exam)
  )
    throw new OfferError("invalid_request", "This booking request is invalid.");
  const codeHash = createHash("sha256").update(couponCode(code)).digest();
  const db = await pool.getConnection();
  try {
    await db.beginTransaction();
    const [students] = await db.execute<RowDataPacket[]>(
      "SELECT status FROM de_students WHERE id = ? FOR UPDATE",
      [studentId],
    );
    if (students[0]?.["status"] !== "active")
      throw new OfferError("account_required", "A verified active student account is required.");
    const [existing] = await db.execute<RowDataPacket[]>(
      `SELECT o.id,o.test_id,o.coupon_id,e.id AS entitlement FROM de_orders o
      JOIN de_entitlements e ON e.order_id=o.id WHERE o.student_id=? AND o.idempotency_key=?`,
      [studentId, retryKey],
    );
    if (existing[0]) {
      const [sameCode] = await db.execute<RowDataPacket[]>(
        "SELECT id FROM de_coupons WHERE code_hash=?",
        [codeHash],
      );
      if (existing[0]["test_id"] !== test.id || existing[0]["coupon_id"] !== sameCode[0]?.["id"])
        throw new OfferError(
          "retry_conflict",
          "Use a new booking request when changing your test or coupon.",
        );
      await db.commit();
      return {
        orderId: String(existing[0]["id"]),
        entitlementId: String(existing[0]["entitlement"]),
        duePaise: 0,
      };
    }
    const [eligibility] = await db.execute<RowDataPacket[]>(
      `SELECT
      EXISTS(SELECT 1 FROM de_identities i JOIN de_contacts c ON c.student_id=i.student_id AND i.subject=c.mobile WHERE i.student_id=? AND i.provider='phone') AS verified,
      EXISTS(SELECT 1 FROM de_contacts WHERE student_id=?) AND EXISTS(SELECT 1 FROM de_education WHERE student_id=?) AS profileReady,
      EXISTS(SELECT 1 FROM de_consents WHERE student_id=? AND purpose='account' AND revoked_at IS NULL) AS consentReady,
      (SELECT COUNT(*) FROM de_attempts WHERE student_id=? AND state='submitted') AS submittedAttempts`,
      Array(5).fill(studentId),
    );
    const [coupons] = await db.execute<RowDataPacket[]>(
      `SELECT c.*,s.active AS school_active FROM de_coupons c
      LEFT JOIN de_schools s ON s.id=c.school_id WHERE code_hash=? FOR UPDATE`,
      [codeHash],
    );
    const c = coupons[0];
    if (!c || (c["kind"] === "school" && !c["school_active"]))
      throw new OfferError("unavailable", "This coupon isn't available.");
    const [used] = await db.execute<RowDataPacket[]>(
      "SELECT order_id FROM de_redemptions WHERE coupon_id=? AND student_id=?",
      [c["id"], studentId],
    );
    const s = eligibility[0]!;
    const student: OfferStudent = {
      verified: !!s["verified"],
      profileReady: !!s["profileReady"],
      consentReady: !!s["consentReady"],
      submittedAttempts: Number(s["submittedAttempts"]),
    };
    const coupon: Coupon = {
      id: c["id"],
      kind: c["kind"],
      exam: c["exam"],
      active: !!c["active"],
      startsAt: new Date(c["starts_at"]).getTime(),
      expiresAt: new Date(c["expires_at"]).getTime(),
      limit: c["redemption_limit"],
      used: c["used"],
    };
    const quote = quoteAccess(student, test.exam, coupon, used.length > 0);
    const orderId = randomUUID(),
      entitlementId = randomUUID();
    await db.execute(
      `INSERT INTO de_orders(id,student_id,test_id,idempotency_key,coupon_id,price_paise,discount_paise,due_paise,status)
      VALUES(?,?,?,?,?,?,?,?, 'paid')`,
      [orderId, studentId, test.id, retryKey, c["id"], quote.pricePaise, 0, quote.duePaise],
    );
    await db.execute("INSERT INTO de_redemptions(coupon_id,student_id,order_id) VALUES(?,?,?)", [
      c["id"],
      studentId,
      orderId,
    ]);
    await db.execute("UPDATE de_coupons SET used=used+1 WHERE id=?", [c["id"]]);
    await db.execute(
      "INSERT INTO de_entitlements(id,order_id,student_id,test_id) VALUES(?,?,?,?)",
      [entitlementId, orderId, studentId, test.id],
    );
    await db.execute(
      "INSERT INTO de_audit(actor_id,action,target_id) VALUES(?,'coupon.redeemed',?)",
      [studentId, orderId],
    );
    await db.commit();
    return { orderId, entitlementId, duePaise: quote.duePaise };
  } catch (error) {
    await db.rollback();
    throw error;
  } finally {
    db.release();
  }
}

import { createHmac, timingSafeEqual, randomUUID } from "node:crypto";
import type { Pool, RowDataPacket } from "mysql2/promise";

export function monthAfter(start: Date) {
  if (!Number.isFinite(start.getTime())) throw Error("Invalid pass date.");
  const end = new Date(start);
  end.setUTCDate(1);
  end.setUTCMonth(end.getUTCMonth() + 1);
  const last = new Date(Date.UTC(end.getUTCFullYear(), end.getUTCMonth() + 1, 0)).getUTCDate();
  end.setUTCDate(Math.min(start.getUTCDate(), last));
  return end;
}
export function capturedPayment(raw: Buffer, signature: string, secret: string) {
  if (
    !secret ||
    raw.length > 65_536 ||
    !/^[a-f0-9]{64}$/.test(signature) ||
    !timingSafeEqual(
      Buffer.from(signature, "hex"),
      createHmac("sha256", secret).update(raw).digest(),
    )
  )
    throw Error("Invalid payment signature.");
  const event = JSON.parse(raw.toString());
  const p = event?.payload?.payment?.entity;
  if (
    event.event !== "payment.captured" ||
    p?.status !== "captured" ||
    p.captured !== true ||
    !/^[a-zA-Z0-9_]{1,120}$/.test(p.order_id || "") ||
    !/^[a-zA-Z0-9_]{1,120}$/.test(p.id || "") ||
    !Number.isSafeInteger(p.amount) ||
    p.amount < 1 ||
    p.currency !== "INR"
  )
    throw Error("Unexpected payment event.");
  return {
    orderId: String(p.order_id),
    paymentId: String(p.id),
    amount: Number(p.amount),
    currency: "INR",
  };
}
// Internal webhook service: raw bytes are verified before JSON is trusted; no browser success grants access.
export async function captureMonthlyPass(
  pool: Pool,
  raw: Buffer,
  signature: string,
  secret: string,
  now = new Date(),
) {
  const payment = capturedPayment(raw, signature, secret),
    db = await pool.getConnection();
  try {
    const [lookup] = await db.execute<RowDataPacket[]>(
      "SELECT student_id FROM de_orders WHERE gateway_order=?",
      [payment.orderId],
    );
    if (!lookup[0]) throw Error("Payment order not found.");
    await db.beginTransaction();
    await db.execute("SELECT id FROM de_students WHERE id=? FOR UPDATE", [lookup[0]["student_id"]]);
    const [orders] = await db.execute<RowDataPacket[]>(
      "SELECT * FROM de_orders WHERE gateway_order=? FOR UPDATE",
      [payment.orderId],
    );
    const order = orders[0]!;
    if (
      order["product"] !== "monthly" ||
      order["currency"] !== payment.currency ||
      order["due_paise"] !== payment.amount ||
      !["pending", "paid"].includes(order["status"])
    )
      throw Error("Payment does not match the order.");
    if (order["status"] === "paid") {
      if (order["gateway_payment"] !== payment.paymentId)
        throw Error("Duplicate payment mismatch.");
      const [old] = await db.execute<RowDataPacket[]>(
        "SELECT id FROM de_monthly_passes WHERE order_id=?",
        [order["id"]],
      );
      if (!old[0]) throw Error("Paid order requires reconciliation.");
      await db.commit();
      return { passId: String(old[0]["id"]) };
    }
    const [passes] = await db.execute<RowDataPacket[]>(
      "SELECT MAX(expires_at) AS expires FROM de_monthly_passes WHERE student_id=? AND revoked_at IS NULL",
      [order["student_id"]],
    );
    const start = new Date(
      Math.max(
        now.getTime(),
        passes[0]?.["expires"] ? new Date(passes[0]["expires"]).getTime() : 0,
      ),
    );
    const end = monthAfter(start),
      id = randomUUID();
    await db.execute(
      "INSERT INTO de_monthly_passes(id,order_id,student_id,starts_at,expires_at) VALUES(?,?,?,?,?)",
      [id, order["id"], order["student_id"], start, end],
    );
    await db.execute("UPDATE de_orders SET status='paid',gateway_payment=? WHERE id=?", [
      payment.paymentId,
      order["id"],
    ]);
    await db.execute("INSERT INTO de_audit(actor_id,action,target_id) VALUES(?,'pass.paid',?)", [
      order["student_id"],
      order["id"],
    ]);
    await db.commit();
    return { passId: id };
  } catch (e) {
    await db.rollback();
    throw e;
  } finally {
    db.release();
  }
}

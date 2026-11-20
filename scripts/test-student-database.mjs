// Isolated local socket only: this script cannot target the live database.
import { readFile } from "node:fs/promises";
import { randomUUID, createHash, createHmac, randomBytes } from "node:crypto";
import assert from "node:assert/strict";
import mysql from "mysql2/promise";
import { grantFreeAttempt } from "../server/student/checkout.ts";
import { captureMonthlyPass } from "../server/student/payments.ts";
import { saveProfileSlice } from "../server/student/profiles.ts";
import { saveIntegration } from "../server/student/integrations.ts";

const socket = "/tmp/dekhoexams-student-test.sock";
const name = "de_student_test_" + randomBytes(6).toString("hex");
const admin = await mysql.createConnection({ socketPath: socket, user: "root", timezone: "Z" });
await admin.query(`CREATE DATABASE ${name} CHARACTER SET utf8mb4`);
const pool = mysql.createPool({
  socketPath: socket,
  user: "root",
  database: name,
  timezone: "Z",
  connectionLimit: 8,
  queueLimit: 100,
});
const messages = [];
try {
  const schema = await readFile(new URL("../server/student/schema.sql", import.meta.url), "utf8");
  for (const s of schema
    .replace(/--[^\n]*/g, "")
    .split(";")
    .map((s) => s.trim())
    .filter(Boolean))
    await pool.query(s);
  const ids = Array.from({ length: 8 }, () => randomUUID());
  for (const [i, id] of ids.entries()) {
    await pool.execute("INSERT INTO de_students(id,status) VALUES(?,'active')", [id]);
    await pool.execute(
      "INSERT INTO de_identities(provider,subject,student_id,verified_at) VALUES('phone',?,?,NOW(3))",
      ["+91987650000" + i, id],
    );
    await pool.execute(
      "INSERT INTO de_consents(id,student_id,purpose,policy_version,granted_at) VALUES(?,?,'account','test',NOW(3))",
      [randomUUID(), id],
    );
    await saveProfileSlice(pool, id, "contact", {
      name: "Sample Student " + i,
      email: `sample${i}@example.com`,
      mobile: "+91987650000" + i,
    });
    await saveProfileSlice(pool, id, "education", {
      level: "12",
      state: "Delhi",
      city: "New Delhi",
    });
  }
  await saveProfileSlice(pool, ids[0], "preferences", { dob: null });
  await saveProfileSlice(pool, ids[0], "contact", {
    name: "Updated Sample",
    email: "updated@example.com",
    mobile: "+919876500000",
  });
  const [[profile]] = await pool.execute(
    "SELECT c.name,e.level,p.dob,p.birthday_completed FROM de_contacts c JOIN de_education e ON e.student_id=c.student_id JOIN de_preferences p ON p.student_id=c.student_id WHERE c.student_id=?",
    [ids[0]],
  );
  assert.equal(profile.name, "Updated Sample");
  assert.equal(profile.level, "12");
  assert.equal(profile.dob, null);
  assert.equal(profile.birthday_completed, 1);
  const [[identities]] = await pool.query(
    "SELECT COUNT(*) AS n FROM de_identities WHERE provider='phone'",
  );
  assert.equal(identities.n, 8);
  messages.push(
    "Three profile slices persist independently; contact edits do not create verified identities.",
  );
  const couponId = randomUUID();
  await pool.execute(
    `INSERT INTO de_coupons(id,code_hash,kind,exam,starts_at,expires_at,redemption_limit) VALUES(?,?,'welcome','jee-main','2020-01-01','2099-01-01',100)`,
    [couponId, createHash("sha256").update("WELCOME100").digest()],
  );
  const test = { id: "jee-main-test-1", exam: "jee-main" },
    key = "same-retry-key-123456";
  const attempts = await Promise.all(
    Array.from({ length: 20 }, () => grantFreeAttempt(pool, ids[0], test, "WELCOME100", key)),
  );
  assert.equal(new Set(attempts.map((a) => a.orderId)).size, 1);
  await assert.rejects(
    grantFreeAttempt(pool, ids[0], test, "WELCOME100", "different-retry-key-12345"),
  );
  await assert.rejects(
    grantFreeAttempt(pool, ids[0], { ...test, id: "another-test" }, "WELCOME100", key),
  );
  const [[counter]] = await pool.query("SELECT used FROM de_coupons WHERE id=?", [couponId]);
  assert.equal(counter.used, 1);
  const [[one]] = await pool.query("SELECT COUNT(*) AS n FROM de_entitlements WHERE student_id=?", [
    ids[0],
  ]);
  assert.equal(one.n, 1);
  messages.push(
    "20 concurrent retries produce one free order and entitlement; reuse and changed-request retries fail.",
  );
  const school = randomUUID(),
    schoolCoupon = randomUUID();
  await pool.execute(
    "INSERT INTO de_schools(id,name,state,city) VALUES(?,'Sample school','Delhi','Delhi')",
    [school],
  );
  await pool.execute(
    "INSERT INTO de_coupons(id,code_hash,kind,school_id,exam,starts_at,expires_at,redemption_limit) VALUES(?,?,'school',?,'jee-main','2020-01-01','2099-01-01',2)",
    [schoolCoupon, createHash("sha256").update("SCHOOL-TEST").digest(), school],
  );
  const race = await Promise.allSettled(
    ids.slice(1).map((id) => grantFreeAttempt(pool, id, test, "SCHOOL-TEST", "school-key-" + id)),
  );
  assert.equal(race.filter((r) => r.status === "fulfilled").length, 2);
  const [[limit]] = await pool.query("SELECT used FROM de_coupons WHERE id=?", [schoolCoupon]);
  assert.equal(limit.used, 2);
  const [[orders]] = await pool.query("SELECT COUNT(*) AS n FROM de_orders WHERE coupon_id=?", [
    schoolCoupon,
  ]);
  assert.equal(orders.n, 2);
  messages.push(
    "Seven students racing for two school grants cannot oversell; rejected requests leave no partial order.",
  );
  const order = randomUUID();
  await pool.execute(
    "INSERT INTO de_orders(id,student_id,test_id,idempotency_key,product,price_paise,discount_paise,due_paise,status,gateway_order) VALUES(?,?,?,'monthly-123456789','monthly',99900,0,99900,'pending','order_test1')",
    [order, ids[0], test.id],
  );
  const raw = Buffer.from(
    JSON.stringify({
      event: "payment.captured",
      payload: {
        payment: {
          entity: {
            id: "pay_test1",
            order_id: "order_test1",
            status: "captured",
            captured: true,
            amount: 99900,
            currency: "INR",
          },
        },
      },
    }),
  );
  const secret = randomBytes(32).toString("hex"),
    sig = createHmac("sha256", secret).update(raw).digest("hex");
  const paid = await Promise.all(
    Array.from({ length: 12 }, () =>
      captureMonthlyPass(pool, raw, sig, secret, new Date("2026-01-31T12:00:00Z")),
    ),
  );
  assert.equal(new Set(paid.map((p) => p.passId)).size, 1);
  const [[pass]] = await pool.query("SELECT expires_at FROM de_monthly_passes WHERE order_id=?", [
    order,
  ]);
  assert.equal(pass.expires_at.toISOString(), "2026-02-28T12:00:00.000Z");
  await pool.execute("UPDATE de_orders SET status='refunded' WHERE id=?", [order]);
  await assert.rejects(captureMonthlyPass(pool, raw, sig, secret));
  messages.push(
    "12 signed payment replays produce one monthly pass, clamp January month-end and cannot reactivate refunded orders.",
  );
  const encryptionKey = randomBytes(32).toString("base64");
  await assert.rejects(
    saveIntegration(pool, ids[1], "razorpay", "test", { keySecret: "test-secret" }, encryptionKey),
  );
  await pool.execute("INSERT INTO de_admin_roles(student_id,role) VALUES(?,'owner')", [ids[0]]);
  const settings = await saveIntegration(
    pool,
    ids[0],
    "razorpay",
    "test",
    { keyId: "rzp_test_example", keySecret: "test-secret", webhookSecret: "webhook-test" },
    encryptionKey,
  );
  assert(!JSON.stringify(settings).includes("test-secret"));
  assert.equal(settings.connected, false);
  const [[stored]] = await pool.query(
    "SELECT encrypted_values FROM de_integration_settings WHERE provider='razorpay'",
  );
  assert(!stored.encrypted_values.includes(Buffer.from("test-secret")));
  messages.push(
    "Only the explicit owner can save encrypted provider settings; credentials are absent from returned data.",
  );
  console.log(
    JSON.stringify(
      {
        databaseVersion: (await pool.query("SELECT VERSION() AS v"))[0][0].v,
        checks: messages,
        productionTouched: false,
      },
      null,
      2,
    ),
  );
} finally {
  await pool.end();
  await admin.query(`DROP DATABASE ${name}`);
  await admin.end();
}

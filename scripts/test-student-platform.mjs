import test from "node:test";
import assert from "node:assert/strict";
import { randomBytes, createHmac } from "node:crypto";
import { quoteAccess, couponCode } from "../src/lib/student-offers.ts";
import { monthAfter, capturedPayment } from "../server/student/payments.ts";
import { sealSettings, openSettings, validateSettings } from "../server/student/integrations.ts";
import { validateProfileSlice } from "../server/student/profiles.ts";

const student = { verified: true, profileReady: true, consentReady: true, submittedAttempts: 0 };
const coupon = {
  id: "welcome",
  kind: "welcome",
  active: true,
  exam: "jee-main",
  startsAt: 100,
  expiresAt: 1000,
  limit: 10,
  used: 0,
};
test("monthly access is ₹999; a coupon grants one mock and never a free monthly pass", () => {
  assert.deepEqual(quoteAccess(student, "jee-main", null), {
    product: "monthly",
    pricePaise: 99900,
    duePaise: 99900,
  });
  assert.deepEqual(quoteAccess(student, "jee-main", coupon, false, 200), {
    product: "single",
    pricePaise: 0,
    duePaise: 0,
  });
});
test("coupons fail closed at boundaries, limits, identity and repeat conditions", () => {
  for (const change of [
    { active: false },
    { expiresAt: 200 },
    { startsAt: 201 },
    { limit: 0 },
    { used: 10 },
    { used: -1 },
    { used: NaN },
    { exam: "neet" },
    { kind: "anything" },
    { expiresAt: NaN },
  ])
    assert.throws(() => quoteAccess(student, "jee-main", { ...coupon, ...change }, false, 200));
  assert.throws(() => quoteAccess(student, "jee-main", coupon, true, 200));
  for (const flag of ["verified", "profileReady", "consentReady"])
    assert.throws(() => quoteAccess({ ...student, [flag]: false }, "jee-main", coupon, false, 200));
  assert.throws(() =>
    quoteAccess(student, "jee-main", { ...coupon, kind: "comeback" }, false, 200),
  );
  assert.equal(
    quoteAccess(
      { ...student, submittedAttempts: 1 },
      "jee-main",
      { ...coupon, kind: "comeback" },
      false,
      200,
    ).product,
    "single",
  );
  assert.throws(() =>
    quoteAccess({ ...student, submittedAttempts: 1 }, "jee-main", coupon, false, 200),
  );
  assert.equal(quoteAccess(student, "jee-main", coupon, false, 100).duePaise, 0);
  assert.equal(couponCode(" welcome100 "), "WELCOME100");
  for (const bad of ["a", "abc\nfoo", "x".repeat(65), "स्कूल"])
    assert.throws(() => couponCode(bad));
});
test("profile saves are strict independent slices and invalid birthdays cannot pass", () => {
  assert.deepEqual(validateProfileSlice("preferences", { dob: null }), { dob: null });
  assert.throws(() =>
    validateProfileSlice("contact", {
      name: "Riya",
      email: "r@example.com",
      mobile: "+919876500000",
      role: "owner",
    }),
  );
  assert.throws(() => validateProfileSlice("preferences", { dob: "2025-02-29" }));
  assert.throws(() =>
    validateProfileSlice("preferences", { dob: "2027-01-01" }, new Date("2026-11-20")),
  );
  assert.throws(() =>
    validateProfileSlice("education", { level: "13", state: "Delhi", city: "Delhi" }),
  );
  assert.equal(
    validateProfileSlice("education", { level: "12", state: "Delhi", city: "New Delhi" }).level,
    "12",
  );
});
test("one month clamps month end without changing time, including leap years", () => {
  assert.equal(
    monthAfter(new Date("2026-01-31T15:30:10Z")).toISOString(),
    "2026-02-28T15:30:10.000Z",
  );
  assert.equal(
    monthAfter(new Date("2028-01-31T15:30:10Z")).toISOString(),
    "2028-02-29T15:30:10.000Z",
  );
  assert.equal(
    monthAfter(new Date("2026-12-20T15:30:10Z")).toISOString(),
    "2027-01-20T15:30:10.000Z",
  );
});
test("only an authentic raw captured-payment event is accepted", () => {
  const secret = randomBytes(32).toString("hex");
  const raw = Buffer.from(
    JSON.stringify({
      event: "payment.captured",
      payload: {
        payment: {
          entity: {
            id: "pay_abc",
            order_id: "order_abc",
            status: "captured",
            captured: true,
            amount: 99900,
            currency: "INR",
          },
        },
      },
    }),
  );
  const sig = createHmac("sha256", secret).update(raw).digest("hex");
  assert.equal(capturedPayment(raw, sig, secret).amount, 99900);
  assert.throws(() => capturedPayment(Buffer.concat([raw, Buffer.from(" ")]), sig, secret));
  assert.throws(() => capturedPayment(raw, "bad", secret));
  assert.throws(() => capturedPayment(raw, sig, "wrong"));
});
test("integration credentials are encrypted, tamper-evident and bound to provider/mode", () => {
  const key = randomBytes(32).toString("base64"),
    values = { keySecret: "sample-secret" };
  const sealed = sealSettings("razorpay", "test", values, key);
  assert(!sealed.includes(Buffer.from("sample-secret")));
  assert.deepEqual(openSettings("razorpay", "test", sealed, key), values);
  assert.throws(() => openSettings("razorpay", "live", sealed, key));
  assert.throws(() => openSettings("google", "test", sealed, key));
  const changed = Buffer.from(sealed);
  changed[changed.length - 1] ^= 1;
  assert.throws(() => openSettings("razorpay", "test", changed, key));
  assert.throws(() => sealSettings("razorpay", "test", values, ""));
  assert.throws(() => validateSettings("razorpay", { url: "https://elsewhere.invalid" }));
  assert.throws(() => validateSettings("ses", { fromEmail: "x@another.example" }));
});

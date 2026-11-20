// Uses the isolated local MySQL socket exclusively.
import assert from "node:assert/strict";
import { randomBytes, randomUUID } from "node:crypto";
import { readFile } from "node:fs/promises";
import mysql from "mysql2/promise";
import { platformResponse } from "../server/student/http.ts";
import { issueInvite, platformOrigin } from "../server/student/access.ts";

const local = { socketPath: "/tmp/dekhoexams-student-test.sock", user: "root", timezone: "Z" };
const dbName = "de_pilot_test_" + randomBytes(6).toString("hex");
const db = await mysql.createConnection(local);
await db.query("CREATE DATABASE " + dbName);
const pool = mysql.createPool({ ...local, database: dbName, connectionLimit: 8 });
const key = randomBytes(32).toString("base64");
const origin = platformOrigin(),
  base = origin + "/api/platform/v1";
const sent = new Map();
const request = (path, cookie, json, requestOrigin = origin) =>
  platformResponse(
    new Request(base + path, {
      method: json === undefined ? "GET" : "POST",
      headers: {
        ...(cookie ? { cookie } : {}),
        ...(json === undefined
          ? {}
          : { "content-type": "application/json", origin: requestOrigin }),
      },
      ...(json === undefined ? {} : { body: JSON.stringify(json) }),
    }),
    () => pool,
    () => key,
    async (mobile, code) => {
      sent.set(mobile, code);
    },
  );
const response = async (path, cookie, json, status = 200) => {
  const r = await request(path, cookie, json);
  assert.equal(r.status, status, path + " " + (await r.clone().text()));
  assert.match(r.headers.get("cache-control"), /private, no-store/);
  return await r.json();
};
const linkToken = (url) => new URLSearchParams(new URL(url).hash.slice(1)).get("invite");
const login = async (url, mobile) => {
  const token = linkToken(url);
  let code;
  if (mobile) {
    await response("/activate", "", { token }, 401);
    await response("/student-code", "", { token });
    await response("/student-code", "", { token }, 429);
    code = sent.get(mobile);
    const wrong = String((Number(code) + 1) % 1_000_000).padStart(6, "0");
    await response("/activate", "", { token, code: wrong }, 401);
  }
  const r = await request("/activate", "", { token, ...(code ? { code } : {}) });
  assert.equal(r.status, 200, await r.clone().text());
  const cookie = r.headers.get("set-cookie");
  assert.match(cookie, /HttpOnly; Secure; SameSite=Strict/);
  assert.match(cookie, /Path=\/api\/platform\/v1/);
  return cookie.split(";")[0];
};
try {
  for (const f of ["schema.sql", "pilot.sql"]) {
    const sql = await readFile(new URL("../server/student/" + f, import.meta.url), "utf8");
    for (const s of sql
      .replace(/^--[^\n]*/gm, "")
      .split(";")
      .map((x) => x.trim())
      .filter(Boolean))
      await pool.query(s);
  }
  const ownerId = randomUUID();
  await pool.execute("INSERT INTO de_students(id,status) VALUES(?,'active')", [ownerId]);
  await pool.execute("INSERT INTO de_admin_roles(student_id,role) VALUES(?,'owner')", [ownerId]);
  const conn = await pool.getConnection();
  let ownerLink;
  try {
    await conn.beginTransaction();
    ownerLink = await issueInvite(conn, "owner", ownerId, ownerId);
    await conn.commit();
  } finally {
    conn.release();
  }
  const owner = await login(ownerLink.url);
  await response("/activate", "", { token: linkToken(ownerLink.url) }, 401);
  await response("/session", "", undefined, 401);
  const secret = "isolated-only-test-secret";
  assert.equal(
    (
      await request(
        "/integrations",
        owner,
        { provider: "razorpay", mode: "test", values: { keySecret: secret } },
        "https://elsewhere.invalid",
      )
    ).status,
    403,
  );
  const settings = await response("/integrations", owner, {
    provider: "razorpay",
    mode: "test",
    values: { keyId: "rzp_test_demo", keySecret: secret },
  });
  await response("/integrations", owner, {
    provider: "sms",
    mode: "live",
    values: { authKey: "mock-only", templateId: "fake-template" },
  });
  const admin = await response("/admin", owner);
  assert.equal(settings.connected, false);
  assert(!JSON.stringify(admin).includes(secret));
  const create = (name) =>
    response(
      "/schools",
      owner,
      {
        name,
        city: "New Delhi",
        state: "Delhi",
        exam: "jee-main",
        redemptionLimit: 1,
        expiresAt: "2098-03-31",
      },
      201,
    );
  const a = await create("Sample School A"),
    b = await create("Sample School B");
  const firstStaff = await response("/invitations", owner, { schoolId: a.school.id }, 201);
  const secondStaff = await response("/invitations", owner, { schoolId: b.school.id }, 201);
  const staffA = await login(firstStaff.url),
    staffB = await login(secondStaff.url);
  await response("/admin", staffA, undefined, 403);
  await response("/roster", staffA, { rows: [{ name: "Sample", mobile: "9876500001" }] }, 400);
  await response(
    "/roster",
    staffA,
    {
      authorized: true,
      rows: [
        { name: "Test <Student>", mobile: "9876500001" },
        { name: "Seat race", mobile: "9876500002" },
      ],
    },
    201,
  );
  const roster = await response("/school", staffA);
  const other = await response("/school", staffB);
  assert.equal(roster.roster.length, 2);
  assert.equal(other.roster.length, 0);
  assert.deepEqual(roster.progress, { enrolled: 2, activated: 0, started: 0, completed: 0 });
  assert.equal(roster.coupon.code, a.coupon.code);
  assert.equal(other.coupon.code, b.coupon.code);
  const candidate = roster.roster.find((s) => s.name === "Test <Student>");
  const racer = roster.roster.find((s) => s.id !== candidate.id);
  await response("/invitations", staffB, { rosterId: candidate.id }, 404);
  const studentLink = await response("/invitations", staffA, { rosterId: candidate.id }, 201);
  const replaced = await response("/invitations", staffA, { rosterId: candidate.id }, 201);
  await response("/activate", "", { token: linkToken(studentLink.url) }, 401);
  const student = await login(replaced.url, "+919876500001");
  await response("/school", student, undefined, 403);
  await response("/student", staffA, undefined, 403);
  await response("/student/marketing", student, { optedIn: true }, 403);
  await response("/student/report", student, undefined, 404);
  await response("/student/certificate", student, undefined, 404);
  assert.deepEqual((await response("/student", student)).marketing, {
    eligible: false,
    optedIn: false,
  });
  const concurrent = await Promise.all(
    Array.from({ length: 5 }, () => response("/student/attempt", student, {})),
  );
  assert.equal(new Set(concurrent.map((x) => x.attempt.id)).size, 1);
  const secondLink = await response("/invitations", staffA, { rosterId: racer.id }, 201);
  const unused = await login(secondLink.url, "+919876500002");
  await response("/student/attempt", unused, {}, 409);
  const { attempt, questions } = concurrent[0];
  assert.equal(questions.length, 6);
  assert(!questions.some((q) => "key" in q));
  const answers = { "p-1": 0, "p-2": 1, "c-1": 2, "c-2": 3, "m-1": 2, "m-2": 2 };
  await response(
    "/student/answers",
    student,
    { revision: attempt.revision, answers: { nope: 0 } },
    400,
  );
  const saved = await response("/student/answers", student, {
    revision: attempt.revision,
    answers,
  });
  await response(
    "/student/answers",
    student,
    { revision: attempt.revision, answers, submit: true },
    409,
  );
  const result = await response("/student/answers", student, {
    revision: saved.attempt.revision,
    answers,
    submit: true,
  });
  assert.equal(result.attempt.result.score, 24);
  assert.equal(result.award.medal, "Gold");
  assert.deepEqual((await response("/school", staffA)).progress, {
    enrolled: 2,
    activated: 2,
    started: 1,
    completed: 1,
  });
  assert.deepEqual((await response("/school", staffB)).progress, {
    enrolled: 0,
    activated: 0,
    started: 0,
    completed: 0,
  });
  const replay = await response("/student/answers", student, {
    revision: saved.attempt.revision,
    answers: {},
    submit: true,
  });
  assert.equal(replay.attempt.result.score, 24);
  await response("/student/certificate", unused, undefined, 404);
  await response("/student/report", unused, undefined, 404);
  await response("/student/report", staffA, undefined, 403);
  await response("/student/report", "", undefined, 401);
  const report = await request("/student/report", student);
  assert.equal(report.status, 200);
  assert.match(report.headers.get("cache-control"), /no-store/);
  assert.match(report.headers.get("content-security-policy"), /default-src 'none'/);
  const reportBody = await report.text();
  assert.match(reportBody, /Test &lt;Student&gt;/);
  assert.match(reportBody, /24 \/ 24/);
  assert.match(reportBody, /100%/);
  assert.match(reportBody, /Physics/);
  assert(!questions.some((q) => reportBody.includes(q.prompt)));
  const certificate = await request("/student/certificate", student);
  assert.equal(certificate.status, 200);
  assert.match(certificate.headers.get("cache-control"), /no-store/);
  assert.match(await certificate.text(), /Test &lt;Student&gt;/);
  await response("/logout", student, {});
  await response("/session", student, undefined, 401);
  console.log(
    "Pilot API passed: role and tenant isolation, student OTP and resend cooldown, same-origin writes, encrypted settings, invite reissue and replay, single seat, stale saves, private grading, award ownership and logout.",
  );
} finally {
  await pool.end();
  await db.query("DROP DATABASE " + dbName);
  await db.end();
}

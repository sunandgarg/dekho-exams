// This suite only accepts the local test socket and uses a fresh temporary schema.
import { readFile } from "node:fs/promises";
import { randomBytes, randomUUID } from "node:crypto";
import assert from "node:assert/strict";
import mysql from "mysql2/promise";
import {
  createSchool,
  getSchool,
  getStudentRosterName,
  importSchoolRoster,
  listMySchools,
  listSchools,
  ownerSchool,
  schoolInvitationContact,
} from "../server/student/schools.ts";

const connect = { socketPath: "/tmp/dekhoexams-student-test.sock", user: "root", timezone: "Z" };
const database = `de_school_test_${randomBytes(6).toString("hex")}`;
const admin = await mysql.createConnection(connect);
await admin.query(`CREATE DATABASE ${database} CHARACTER SET utf8mb4`);
const pool = mysql.createPool({ ...connect, database, connectionLimit: 4 });
const key = randomBytes(32).toString("base64");
const [owner, staffA, staffB, student, outsider] = Array.from({ length: 5 }, randomUUID);
const expiresAt = new Date(Date.now() + 86_400_000 * 30).toISOString().slice(0, 10);
const input = {
  name: "School A",
  state: "Delhi",
  city: "New Delhi",
  exam: "jee-main",
  redemptionLimit: 150,
  expiresAt,
};
const person = {
  name: "Synthetic Student",
  email: "sample@example.invalid",
  mobile: "9876543210",
  level: "12",
};
const notFound = (error) => error.status === 404;

try {
  for (const file of ["schema.sql", "pilot.sql"]) {
    const sql = await readFile(new URL(`../server/student/${file}`, import.meta.url), "utf8");
    for (const statement of sql
      .replace(/--[^\n]*/g, "")
      .split(";")
      .map((s) => s.trim())
      .filter(Boolean))
      await pool.query(statement);
  }
  for (const id of [owner, staffA, staffB, student, outsider]) {
    await pool.execute("INSERT INTO de_students(id,status) VALUES(?,'active')", [id]);
  }
  await pool.execute("INSERT INTO de_admin_roles(student_id,role) VALUES(?,'owner')", [owner]);
  await assert.rejects(createSchool(pool, staffA, input, key), (error) => error.status === 403);
  await assert.rejects(
    createSchool(pool, owner, { ...input, expiresAt: "2099-02-30" }, key),
    (error) => error.status === 422,
  );
  const a = await createSchool(pool, owner, input, key);
  const b = await createSchool(pool, owner, { ...input, name: "School B" }, key);
  assert.notEqual(a.coupon.code, b.coupon.code);
  assert.equal(a.coupon.expiresAt, `${expiresAt}T18:30:00.000Z`);
  assert.equal(a.coupon.limit, 150);
  assert.equal((await listSchools(pool, owner)).schools.length, 2);
  await assert.rejects(listSchools(pool, staffA), (error) => error.status === 403);
  for (const [actor, id] of [
    [staffA, a.school.id],
    [staffB, b.school.id],
  ])
    await pool.execute("INSERT INTO de_school_staff(school_id,student_id) VALUES(?,?)", [
      id,
      actor,
    ]);
  assert.deepEqual(
    (await listMySchools(pool, staffA)).schools.map((s) => s.id),
    [a.school.id],
  );
  await assert.rejects(getSchool(pool, owner, a.school.id, key), notFound);
  await assert.rejects(getSchool(pool, staffA, b.school.id, key), notFound);
  await assert.rejects(
    importSchoolRoster(pool, staffA, b.school.id, { rows: [person] }, key),
    notFound,
  );
  await assert.rejects(
    importSchoolRoster(
      pool,
      staffA,
      a.school.id,
      { rows: [person, { ...person, mobile: "secret invalid number", marketingConsent: true }] },
      key,
    ),
    (error) =>
      error.status === 422 &&
      error.details.length === 1 &&
      !JSON.stringify(error.details).includes("secret"),
  );
  assert.equal((await getSchool(pool, staffA, a.school.id, key)).roster.length, 0);
  const imports = await Promise.all(
    Array.from({ length: 8 }, () =>
      importSchoolRoster(
        pool,
        staffA,
        a.school.id,
        {
          rows: [person, { ...person, name: "Overwriting attempt", mobile: "+91 98765-43210" }],
        },
        key,
      ),
    ),
  );
  assert.equal(
    imports.reduce((sum, item) => sum + item.added, 0),
    1,
  );
  assert.equal(
    imports.reduce((sum, item) => sum + item.duplicates, 0),
    15,
  );
  await importSchoolRoster(pool, staffB, b.school.id, { rows: [person] }, key);
  const [rows] = await pool.query(
    "SELECT school_id,phone_hash,encrypted_fields FROM de_school_roster",
  );
  assert.equal(rows.length, 2);
  assert.notDeepEqual(rows[0].phone_hash, rows[1].phone_hash);
  for (const row of rows)
    for (const original of [person.name, person.mobile, person.email]) {
      assert(!row.encrypted_fields.includes(Buffer.from(original)));
    }
  const [[{ encrypted_code }]] = await pool.execute(
    "SELECT encrypted_code FROM de_school_coupon_defaults WHERE school_id=?",
    [a.school.id],
  );
  assert(!encrypted_code.includes(Buffer.from(a.coupon.code)));
  const dashboard = await getSchool(pool, staffA, a.school.id, key);
  assert.equal(dashboard.coupon.code, a.coupon.code);
  assert.equal(dashboard.roster[0].access, "none");
  assert.equal(dashboard.roster[0].name, person.name);
  assert.equal(dashboard.roster[0].mobile.slice(-4), "3210");
  assert(!JSON.stringify(dashboard).includes(person.mobile));
  assert(!JSON.stringify(dashboard).includes(person.email));
  await assert.rejects(getSchool(pool, staffA, a.school.id, randomBytes(32).toString("base64")));

  const rosterId = dashboard.roster[0].id;
  const connection = await pool.getConnection();
  try {
    await connection.beginTransaction();
    assert.equal((await ownerSchool(connection, owner, a.school.id)).id, a.school.id);
    await assert.rejects(
      schoolInvitationContact(connection, staffB, b.school.id, rosterId, key),
      notFound,
    );
    assert.equal(
      (await schoolInvitationContact(connection, staffA, a.school.id, rosterId, key)).mobile,
      "+919876543210",
    );
    await connection.execute(
      "INSERT INTO de_platform_invites(token_hash,target_kind,target_id,expires_at) VALUES(?,'student',?,DATE_ADD(UTC_TIMESTAMP(3), INTERVAL 1 DAY))",
      [randomBytes(32), rosterId],
    );
    await connection.commit();
  } finally {
    connection.release();
  }
  assert.equal((await getSchool(pool, staffA, a.school.id, key)).roster[0].access, "invited");
  await pool.execute("INSERT INTO de_platform_roster_accounts(roster_id,student_id) VALUES(?,?)", [
    rosterId,
    student,
  ]);
  assert.equal((await getSchool(pool, staffA, a.school.id, key)).roster[0].access, "activated");
  assert.deepEqual(await getStudentRosterName(pool, student, key), {
    name: person.name,
    schoolName: input.name,
  });
  await assert.rejects(getStudentRosterName(pool, outsider, key), notFound);
  const [[{ count }]] = await pool.query("SELECT COUNT(*) AS count FROM de_consents");
  assert.equal(Number(count), 0);
  console.log(
    "School isolation, encrypted roster and coupons, bounded retry-safe imports, invite scope, own student access and no marketing side effects passed.",
  );
} finally {
  await pool.end();
  await admin.query(`DROP DATABASE ${database}`);
  await admin.end();
}

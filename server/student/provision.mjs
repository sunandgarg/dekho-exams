// Run as root on the existing origin with its usual protected environment file.
import { randomBytes, randomUUID } from "node:crypto";
import { open, readFile, writeFile } from "node:fs/promises";
import assert from "node:assert/strict";
import mysql from "mysql2/promise";
import { issueInvite } from "./access.ts";

const name = "dekhoexams_platform";
const user = "de_platform_app";
const runtimeFile = "/etc/dekhoexams/platform.env";
const ownerLinkFile = "/root/dekhoexams-platform-owner.json";
const { MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_CA_FILE } = process.env;
assert(process.getuid?.() === 0 && MYSQL_HOST && MYSQL_USER && MYSQL_PASSWORD && MYSQL_CA_FILE);
const conn = await mysql.createConnection({
  host: MYSQL_HOST,
  user: MYSQL_USER,
  password: MYSQL_PASSWORD,
  timezone: "Z",
  ssl: { ca: await readFile(MYSQL_CA_FILE), rejectUnauthorized: true, verifyIdentity: true },
});
try {
  await conn.query("CREATE DATABASE IF NOT EXISTS dekhoexams_platform CHARACTER SET utf8mb4");
  await conn.changeUser({ database: name });
  for (const source of ["schema.sql", "pilot.sql"]) {
    const sql = await readFile(new URL(source, import.meta.url), "utf8");
    for (const statement of sql
      .replace(/^--[^\n]*/gm, "")
      .split(";")
      .map((s) => s.trim())
      .filter(Boolean)) {
      assert(/^CREATE TABLE IF NOT EXISTS de_[a-z_]+ /.test(statement));
      await conn.query(statement);
    }
  }
  // Keep the master encryption key and SQL password outside the release and DB backups.
  let password;
  let file;
  try {
    file = await open(runtimeFile, "wx", 0o600);
  } catch (e) {
    if (e.code !== "EEXIST") throw e;
    const existing = await readFile(runtimeFile, "utf8");
    password = /^PLATFORM_DB_PASSWORD=([a-f0-9]{64})$/m.exec(existing)?.[1];
    assert(password && /^PLATFORM_ENCRYPTION_KEY=[A-Za-z0-9+/]{43}=$/m.test(existing));
  }
  if (file) {
    password = randomBytes(32).toString("hex");
    try {
      await file.writeFile(
        [
          "PLATFORM_ENABLED=true",
          "PLATFORM_ORIGIN=https://dekhoexams.com",
          "PLATFORM_DB_USER=" + user,
          "PLATFORM_DB_PASSWORD=" + password,
          "PLATFORM_ENCRYPTION_KEY=" + randomBytes(32).toString("base64"),
          "",
        ].join("\n"),
      );
    } finally {
      await file.close();
    }
  }
  await conn.query("CREATE USER IF NOT EXISTS 'de_platform_app'@'%' IDENTIFIED BY ? REQUIRE SSL", [
    password,
  ]);
  // Provisioning is repeatable and never rotates a running app's password.
  await conn.query(
    "GRANT SELECT, INSERT, UPDATE ON dekhoexams_platform.* TO 'de_platform_app'@'%'",
  );
  const runtime = await mysql.createConnection({
    host: MYSQL_HOST,
    user,
    password,
    database: name,
    timezone: "Z",
    ssl: { ca: await readFile(MYSQL_CA_FILE), rejectUnauthorized: true, verifyIdentity: true },
  });
  try {
    await runtime.query("SELECT 1 FROM de_platform_invites LIMIT 1");
  } finally {
    await runtime.end();
  }
  if (process.argv.includes("--owner-link")) {
    await conn.beginTransaction();
    try {
      const [rows] = await conn.query(
        "SELECT student_id FROM de_admin_roles WHERE role='owner' ORDER BY student_id LIMIT 2 FOR UPDATE",
      );
      if (rows.length > 1) throw Error("Multiple owners require named recovery.");
      const id = rows[0]?.student_id ?? randomUUID();
      if (!rows[0]) {
        await conn.execute("INSERT INTO de_students(id,status) VALUES(?,'active')", [id]);
        await conn.execute("INSERT INTO de_admin_roles(student_id,role) VALUES(?,'owner')", [id]);
      }
      const link = await issueInvite(conn, "owner", id, id);
      await writeFile(ownerLinkFile, JSON.stringify(link), { mode: 0o600 });
      await conn.commit();
    } catch (e) {
      await conn.rollback();
      throw e;
    }
  }
  console.log("Platform schema and restricted SQL account verified.");
} catch (e) {
  // Provider error text can contain SQL and values. Report error class/code only.
  console.error("Platform provisioning failed.", e.code ?? e.name);
  process.exitCode = 1;
} finally {
  await conn.end();
}

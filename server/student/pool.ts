import { readFileSync } from "node:fs";
import mysql, { type Pool } from "mysql2/promise";

let pool: Pool | undefined;
export function platformKey() {
  const key = process.env["PLATFORM_ENCRYPTION_KEY"] ?? "";
  if (!/^[A-Za-z0-9+/]{43}=$/.test(key) || Buffer.from(key, "base64").length !== 32)
    throw Error("Platform encryption is not configured.");
  return key;
}
export function platformPool() {
  if (pool) return pool;
  const host = process.env["MYSQL_HOST"],
    ca = process.env["MYSQL_CA_FILE"];
  const user = process.env["PLATFORM_DB_USER"],
    password = process.env["PLATFORM_DB_PASSWORD"];
  if (process.env["PLATFORM_ENABLED"] !== "true" || !host || !ca || !user || !password)
    throw Error("Student platform is not configured.");
  platformKey();
  pool = mysql.createPool({
    host,
    user,
    password,
    database: "dekhoexams_platform",
    timezone: "Z",
    ssl: { ca: readFileSync(ca), rejectUnauthorized: true, verifyIdentity: true },
    connectionLimit: 3,
    queueLimit: 16,
    connectTimeout: 5000,
  });
  return pool;
}

import { readFileSync } from "node:fs";
import mysql from "mysql2/promise";

let pool;
export function archivePool() {
  if (!pool) {
    const { MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_CA_FILE, MYSQL_SOCKET, ARCHIVE_RELEASE } = process.env;
    if (!MYSQL_USER || (!MYSQL_SOCKET && !(MYSQL_HOST && MYSQL_PASSWORD && MYSQL_CA_FILE)) ||
        !/^[a-zA-Z0-9_-]{1,64}$/.test(ARCHIVE_RELEASE || "")) throw Error("Incomplete archive database configuration.");
    pool = mysql.createPool({
      host: MYSQL_HOST, user: MYSQL_USER, password: MYSQL_PASSWORD,
      database: process.env.MYSQL_DATABASE || "dekhoexams",
      socketPath: MYSQL_SOCKET, connectionLimit: 4, queueLimit: 32, connectTimeout: 5000,
      ssl: MYSQL_SOCKET ? undefined : { ca: readFileSync(MYSQL_CA_FILE), rejectUnauthorized: true, verifyIdentity: true },
    });
  }
  return pool;
}

export async function archiveResponse(path) {
  const [rows] = await archivePool().execute(
    "SELECT body FROM published_assets WHERE release_id = ? AND path = ?",
    [process.env.ARCHIVE_RELEASE, path],
  );
  return rows.length ? new Response(rows[0].body) : new Response(null, { status: 404 });
}

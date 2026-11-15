import { opendir, readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { archivePool } from "../server/archive-db.mjs";

async function* files(path) {
  for await (const file of await opendir("public" + path)) {
    const child = path + "/" + file.name;
    if (file.isDirectory()) yield* files(child);
    else if (file.isFile() && child.endsWith(".bin")) yield child;
  }
}

const pool = archivePool();
const db = await pool.getConnection();
try {
  await db.query(`CREATE TABLE IF NOT EXISTS published_assets (
    release_id VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    path VARCHAR(512) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    body MEDIUMBLOB NOT NULL, PRIMARY KEY(release_id, path)
  ) ENGINE=InnoDB`);
  const paths = ["/__data/cms-snapshot.txt"];
  for (const root of ["/jee-archive", "/jee-advanced-archive"]) {
    for await (const path of files(root)) paths.push(path);
  }
  await db.beginTransaction();
  let bytes = 0;
  for (const path of paths.sort()) {
    const body = await readFile("public" + path);
    const key = [process.env.ARCHIVE_RELEASE, path];
    const [existing] = await db.execute("SELECT SHA2(body, 256) AS digest FROM published_assets WHERE release_id=? AND path=? FOR UPDATE", key);
    if (!existing.length) await db.execute("INSERT INTO published_assets VALUES (?,?,?)", [...key, body]);
    else if (existing[0].digest !== createHash("sha256").update(body).digest("hex")) throw Error("Changed file in existing release: " + path);
    bytes += body.length;
  }
  await db.commit();
  console.log("Published", paths.length, "archive files,", bytes, "bytes.");
} catch (error) {
  await db.rollback();
  throw error;
} finally {
  db.release();
  await pool.end();
}

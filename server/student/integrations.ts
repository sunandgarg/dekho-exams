import { randomBytes, createCipheriv, createDecipheriv } from "node:crypto";
import type { Pool, RowDataPacket } from "mysql2/promise";
import { STUDENT_INTEGRATIONS, type IntegrationName } from "../../src/lib/student-integrations.ts";

function masterKey(encoded: string) {
  const key = Buffer.from(encoded, "base64");
  if (key.length !== 32 || key.toString("base64") !== encoded)
    throw Error("A 32-byte server encryption key is required.");
  return key;
}
export function sealSettings(
  provider: IntegrationName,
  mode: "test" | "live",
  values: Record<string, string>,
  key: string,
) {
  const iv = randomBytes(12),
    cipher = createCipheriv("aes-256-gcm", masterKey(key), iv);
  cipher.setAAD(Buffer.from(`dekhoexams:integration:v1:${provider}:${mode}`));
  const body = Buffer.concat([cipher.update(JSON.stringify(values)), cipher.final()]);
  return Buffer.concat([iv, cipher.getAuthTag(), body]);
}
export function openSettings(
  provider: IntegrationName,
  mode: "test" | "live",
  body: Buffer,
  key: string,
): Record<string, string> {
  if (body.length < 29) throw Error("Invalid encrypted configuration.");
  const decipher = createDecipheriv("aes-256-gcm", masterKey(key), body.subarray(0, 12));
  decipher.setAAD(Buffer.from(`dekhoexams:integration:v1:${provider}:${mode}`));
  decipher.setAuthTag(body.subarray(12, 28));
  return JSON.parse(
    Buffer.concat([decipher.update(body.subarray(28)), decipher.final()]).toString(),
  );
}
export function validateSettings(provider: IntegrationName, values: Record<string, string>) {
  const spec = STUDENT_INTEGRATIONS[provider];
  if (!spec || !values || typeof values !== "object" || Array.isArray(values))
    throw Error("Unknown integration.");
  const allowed: readonly string[] = spec.fields.map((f) => f.key);
  if (Object.keys(values).some((k) => !allowed.includes(k))) throw Error("Unknown setting.");
  for (const value of Object.values(values))
    if (typeof value !== "string" || value.length > 4096 || /[\x00-\x1f\x7f]/.test(value))
      throw Error("Invalid setting.");
  if (provider === "ses" && values["region"] && values["region"] !== "ap-south-1")
    throw Error("This deployment uses Mumbai SES.");
  if (
    provider === "ses" &&
    values["fromEmail"] &&
    !/^[A-Za-z0-9._+-]+@dekhoexams\.com$/.test(values["fromEmail"])
  )
    throw Error("Use a verified DekhoExams sender.");
  return values;
}
// Internal service. actorId is supplied by a verified session, not client JSON.
export async function saveIntegration(
  pool: Pool,
  actorId: string,
  provider: IntegrationName,
  mode: "test" | "live",
  input: Record<string, string>,
  encryptionKey: string,
) {
  if (!["test", "live"].includes(mode)) throw Error("Invalid integration mode.");
  validateSettings(provider, input);
  const db = await pool.getConnection();
  try {
    await db.beginTransaction();
    const [roles] = await db.execute<RowDataPacket[]>(
      "SELECT role FROM de_admin_roles WHERE student_id=? AND role='owner' FOR UPDATE",
      [actorId],
    );
    if (!roles.length) throw Error("Owner permission required.");
    const [rows] = await db.execute<RowDataPacket[]>(
      "SELECT encrypted_values FROM de_integration_settings WHERE provider=? AND mode=? FOR UPDATE",
      [provider, mode],
    );
    const values = rows[0]
      ? openSettings(provider, mode, rows[0]["encrypted_values"], encryptionKey)
      : {};
    // Blank fields preserve existing credentials; key removal uses a distinct explicit operation.
    for (const [k, v] of Object.entries(input)) if (v.trim()) values[k] = v.trim();
    validateSettings(provider, values);
    await db.execute(
      `INSERT INTO de_integration_settings(provider,mode,encrypted_values,updated_by) VALUES(?,?,?,?)
      ON DUPLICATE KEY UPDATE encrypted_values=VALUES(encrypted_values),updated_by=VALUES(updated_by),updated_at=CURRENT_TIMESTAMP(3)`,
      [provider, mode, sealSettings(provider, mode, values, encryptionKey), actorId],
    );
    await db.execute(
      "INSERT INTO de_audit(actor_id,action,target_id) VALUES(?,'integration.updated',?)",
      [actorId, provider + ":" + mode],
    );
    await db.commit();
    // Never return the credentials to the browser, even to an owner.
    return {
      provider,
      mode,
      configured: STUDENT_INTEGRATIONS[provider].fields.map((f) => ({
        field: f.key,
        present: !!values[f.key],
      })),
      connected: false,
    };
  } catch (e) {
    await db.rollback();
    throw e;
  } finally {
    db.release();
  }
}

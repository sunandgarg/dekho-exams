import { createCipheriv, createDecipheriv, createHash, randomBytes } from "node:crypto";

export const tokenDigest = (token: string) => createHash("sha256").update(token).digest();
export const newToken = () => randomBytes(32).toString("base64url");
export const validToken = (token: unknown): token is string =>
  typeof token === "string" && /^[A-Za-z0-9_-]{43}$/.test(token);

export function encryptRecord<T>(key: Buffer, context: string, value: T) {
  const iv = randomBytes(12);
  const cipher = createCipheriv("aes-256-gcm", key, iv);
  cipher.setAAD(Buffer.from("dekhoexams:pilot:v1:" + context));
  const encrypted = Buffer.concat([cipher.update(JSON.stringify(value)), cipher.final()]);
  return Buffer.concat([iv, cipher.getAuthTag(), encrypted]);
}

export function decryptRecord<T>(key: Buffer, context: string, sealed: Buffer): T {
  if (sealed.length < 29) throw Error("Encrypted platform record is invalid.");
  const cipher = createDecipheriv("aes-256-gcm", key, sealed.subarray(0, 12));
  cipher.setAAD(Buffer.from("dekhoexams:pilot:v1:" + context));
  cipher.setAuthTag(sealed.subarray(12, 28));
  return JSON.parse(Buffer.concat([cipher.update(sealed.subarray(28)), cipher.final()]).toString());
}

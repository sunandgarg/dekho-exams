import { z } from "zod";
import type { Pool, RowDataPacket } from "mysql2/promise";

const text = (max: number) =>
  z
    .string()
    .trim()
    .min(1)
    .max(max)
    .refine((s) => !/[\x00-\x1f\x7f]/.test(s));
export const PROFILE_SLICES = {
  contact: z
    .object({
      name: text(120),
      email: z.string().trim().email().max(254),
      mobile: z.string().regex(/^\+91[6-9][0-9]{9}$/),
    })
    .strict(),
  education: z
    .object({
      level: z.enum(["10", "11", "12", "graduation", "masters"]),
      state: text(80),
      city: text(100),
    })
    .strict(),
  preferences: z
    .object({
      dob: z
        .string()
        .regex(/^\d{4}-\d{2}-\d{2}$/)
        .nullable(),
    })
    .strict(),
};
export function validateProfileSlice(
  slice: keyof typeof PROFILE_SLICES,
  input: unknown,
  now = new Date(),
) {
  if (!(slice in PROFILE_SLICES)) throw Error("Unknown profile section.");
  const value = PROFILE_SLICES[slice].parse(input);
  if ("dob" in value && value.dob !== null) {
    const date = new Date(value.dob + "T00:00:00Z");
    if (
      !Number.isFinite(date.getTime()) ||
      date.toISOString().slice(0, 10) !== value.dob ||
      value.dob < "1900-01-01" ||
      value.dob > now.toISOString().slice(0, 10)
    )
      throw Error("Invalid birthday.");
  }
  return value;
}
// Session ownership and guardian consent must be resolved before this internal service is called.
export async function saveProfileSlice(
  pool: Pool,
  studentId: string,
  slice: keyof typeof PROFILE_SLICES,
  input: unknown,
) {
  const v = validateProfileSlice(slice, input);
  const db = await pool.getConnection();
  try {
    await db.beginTransaction();
    const [users] = await db.execute<RowDataPacket[]>(
      "SELECT status FROM de_students WHERE id=? FOR UPDATE",
      [studentId],
    );
    if (users[0]?.["status"] !== "active") throw Error("An active student account is required.");
    if (slice !== "contact") {
      const [prior] = await db.execute<RowDataPacket[]>(
        "SELECT student_id FROM de_contacts WHERE student_id=?",
        [studentId],
      );
      if (!prior.length) throw Error("Save contact details first.");
    }
    if ("name" in v)
      await db.execute(
        `INSERT INTO de_contacts(student_id,name,email,mobile) VALUES(?,?,?,?)
      ON DUPLICATE KEY UPDATE name=VALUES(name),email=VALUES(email),mobile=VALUES(mobile),saved_at=CURRENT_TIMESTAMP(3)`,
        [studentId, v.name, v.email, v.mobile],
      );
    else if ("level" in v)
      await db.execute(
        `INSERT INTO de_education(student_id,level,state,city) VALUES(?,?,?,?)
      ON DUPLICATE KEY UPDATE level=VALUES(level),state=VALUES(state),city=VALUES(city),saved_at=CURRENT_TIMESTAMP(3)`,
        [studentId, v.level, v.state, v.city],
      );
    else if ("dob" in v) {
      const [prior] = await db.execute<RowDataPacket[]>(
        "SELECT student_id FROM de_education WHERE student_id=?",
        [studentId],
      );
      if (!prior.length) throw Error("Save education details first.");
      await db.execute(
        `INSERT INTO de_preferences(student_id,dob,birthday_completed) VALUES(?,?,TRUE)
      ON DUPLICATE KEY UPDATE dob=VALUES(dob),birthday_completed=TRUE,saved_at=CURRENT_TIMESTAMP(3)`,
        [studentId, v.dob],
      );
    } else throw Error("Unknown profile section.");
    await db.execute("INSERT INTO de_audit(actor_id,action,target_id) VALUES(?, ?, ?)", [
      studentId,
      "profile." + slice,
      studentId,
    ]);
    await db.commit();
    return { saved: slice };
  } catch (e) {
    await db.rollback();
    throw e;
  } finally {
    db.release();
  }
}

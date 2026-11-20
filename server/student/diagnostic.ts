import { randomUUID } from "node:crypto";
import type { Pool, RowDataPacket } from "mysql2/promise";
import { encryptRecord, decryptRecord } from "./crypto.ts";

export const DIAGNOSTIC_VERSION = "jee-main-pilot-v1";
export const questions = [
  {
    id: "p-1",
    subject: "Physics",
    topic: "Units and measurements",
    prompt:
      "A plate is 12.4 cm long and 5.1 cm wide. To the correct number of significant figures, what is its area?",
    options: ["63 cm²", "63.24 cm²", "63.2 cm²", "60 cm²"],
    key: 0,
  },
  {
    id: "p-2",
    subject: "Physics",
    topic: "Kinematics",
    prompt:
      "A cart starts from rest and accelerates uniformly at 3 m/s² for 4 seconds. How far does it travel?",
    options: ["12 m", "24 m", "36 m", "48 m"],
    key: 1,
  },
  {
    id: "c-1",
    subject: "Chemistry",
    topic: "Mole concept",
    prompt: "How many moles of oxygen atoms are present in 0.25 mol of carbon dioxide?",
    options: ["0.125 mol", "0.25 mol", "0.50 mol", "1.00 mol"],
    key: 2,
  },
  {
    id: "c-2",
    subject: "Chemistry",
    topic: "Chemical bonding",
    prompt:
      "Which molecule has a bent shape because its central atom has two bonding pairs and two lone pairs?",
    options: ["CO₂", "BF₃", "CH₄", "H₂O"],
    key: 3,
  },
  {
    id: "m-1",
    subject: "Mathematics",
    topic: "Sequences and series",
    prompt:
      "An arithmetic progression has first term 7 and common difference 4. What is the sum of its first six terms?",
    options: ["82", "96", "102", "108"],
    key: 2,
  },
  {
    id: "m-2",
    subject: "Mathematics",
    topic: "Probability",
    prompt: "Two fair coins are tossed. What is the probability that exactly one shows heads?",
    options: ["1/4", "1/3", "1/2", "3/4"],
    key: 2,
  },
] as const;
export const publicQuestions = questions.map(({ key: _key, ...question }) => question);
type Answers = Record<string, number>;
export function checkAnswers(input: Record<string, unknown>): Answers {
  const result: Answers = {};
  for (const [id, choice] of Object.entries(input)) {
    const question = questions.find((q) => q.id === id);
    if (
      !question ||
      typeof choice !== "number" ||
      !Number.isInteger(choice) ||
      choice < 0 ||
      choice >= question.options.length
    )
      throw new PilotError(400, "An answer does not match this test.");
    result[id] = choice;
  }
  return result;
}
export function scoreDiagnostic(answers: Answers) {
  let hits = 0,
    misses = 0;
  const subjects = ["Physics", "Chemistry", "Mathematics"].map((subject) => ({
    subject,
    hits: 0,
    total: 0,
  }));
  let firstMiss: string | null = null;
  let firstSkip: string | null = null;
  for (const q of questions) {
    const subject = subjects.find((s) => s.subject === q.subject)!;
    subject.total++;
    if (answers[q.id] === undefined) firstSkip ??= q.topic;
    else if (answers[q.id] === q.key) {
      hits++;
      subject.hits++;
    } else {
      misses++;
      firstMiss ??= q.topic;
    }
  }
  return {
    score: 4 * hits - misses,
    max: 4 * questions.length,
    hits,
    misses,
    skipped: questions.length - hits - misses,
    accuracy: hits + misses ? Math.round((hits * 100) / (hits + misses)) : null,
    subjects,
    nextTopic: firstMiss ?? firstSkip,
  };
}
type Result = ReturnType<typeof scoreDiagnostic>;
export const medalFor = (result: Result) =>
  result.hits === questions.length
    ? "Gold"
    : result.hits >= 5
      ? "Silver"
      : result.hits >= 4
        ? "Bronze"
        : null;
export class PilotError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}
interface AttemptRow extends RowDataPacket {
  id: string;
  question_set: string;
  deadline_at: Date;
  submitted_at: Date | null;
  answers: Buffer;
  result: Buffer | null;
  revision: number;
}

// All operations start by locking the same student row, including coupon consumption.
export async function diagnostic(
  pool: Pool,
  key: Buffer,
  studentId: string,
  schoolId: string,
  operation: "read" | "start" | "save",
  update?: { revision: number; answers: Answers; submit: boolean },
) {
  const db = await pool.getConnection();
  try {
    await db.beginTransaction();
    if (operation === "start") {
      const [[school]] = await db.execute<RowDataPacket[]>(
        "SELECT id FROM de_schools WHERE id=? AND active=TRUE FOR UPDATE",
        [schoolId],
      );
      if (!school) throw new PilotError(403, "School access is inactive.");
    }
    const [[student]] = await db.execute<RowDataPacket[]>(
      "SELECT status FROM de_students WHERE id=? FOR UPDATE",
      [studentId],
    );
    if (student?.["status"] !== "active") throw new PilotError(403, "Student access is inactive.");
    const [[row]] = await db.execute<AttemptRow[]>(
      "SELECT * FROM de_platform_diagnostics WHERE student_id=? FOR UPDATE",
      [studentId],
    );
    const now = new Date();
    let record = row;
    if (!record && operation === "start") {
      const [[coupon]] = await db.execute<RowDataPacket[]>(
        `SELECT c.id FROM de_school_coupon_defaults d
        JOIN de_coupons c ON c.id=d.coupon_id AND c.school_id=d.school_id JOIN de_schools s ON s.id=d.school_id
        WHERE d.school_id=? AND s.active=TRUE AND c.active=TRUE AND c.kind='school'
        AND (c.exam IS NULL OR c.exam='jee-main') AND c.starts_at<=? AND c.expires_at>? AND c.used<c.redemption_limit FOR UPDATE`,
        [schoolId, now, now],
      );
      if (!coupon)
        throw new PilotError(
          409,
          "The school’s diagnostic places have expired or are full. Contact your school.",
        );
      const id = randomUUID(),
        deadline = new Date(now.getTime() + 10 * 60_000);
      await db.execute(
        "INSERT INTO de_platform_diagnostics (id,student_id,coupon_id,question_set,answers,started_at,deadline_at) VALUES (?,?,?,?,?,?,?)",
        [
          id,
          studentId,
          coupon["id"],
          DIAGNOSTIC_VERSION,
          encryptRecord(key, id + ":answers", {}),
          now,
          deadline,
        ],
      );
      await db.execute("UPDATE de_coupons SET used=used+1 WHERE id=?", [coupon["id"]]);
      const [[created]] = await db.execute<AttemptRow[]>(
        "SELECT * FROM de_platform_diagnostics WHERE id=?",
        [id],
      );
      record = created!;
    }
    if (!record && operation === "save")
      throw new PilotError(409, "Start the test before saving answers.");
    if (!record) {
      await db.commit();
      return { attempt: null, questions: [], award: undefined, submittedAt: null };
    }
    if (record.question_set !== DIAGNOSTIC_VERSION) throw Error("Unsupported diagnostic edition.");
    let answers = decryptRecord<Answers>(key, record.id + ":answers", record.answers);
    let result = record.result
      ? decryptRecord<Result>(key, record.id + ":result", record.result)
      : null;
    let submittedAt = record.submitted_at,
      revision = record.revision;
    if (!submittedAt) {
      const expired = record.deadline_at <= now;
      if (!expired && update && update.revision !== revision)
        throw new PilotError(
          409,
          "This test changed in another tab. Reload the test before saving.",
        );
      if (expired || update) {
        if (!expired && update) answers = checkAnswers(update.answers);
        if (expired || update?.submit) {
          result = scoreDiagnostic(answers);
          submittedAt = now;
        }
        revision++;
        await db.execute(
          "UPDATE de_platform_diagnostics SET answers=?,revision=?,submitted_at=?,result=? WHERE id=?",
          [
            encryptRecord(key, record.id + ":answers", answers),
            revision,
            submittedAt,
            result ? encryptRecord(key, record.id + ":result", result) : null,
            record.id,
          ],
        );
      }
    }
    await db.commit();
    const medal = result && medalFor(result);
    return {
      attempt: {
        id: record.id,
        status: submittedAt ? "submitted" : "active",
        deadline: record.deadline_at.toISOString(),
        answers,
        revision,
        ...(result ? { result } : {}),
      },
      questions: !submittedAt && operation === "start" ? publicQuestions : [],
      ...(medal
        ? { award: { medal, certificateUrl: "/api/platform/v1/student/certificate" } }
        : {}),
      submittedAt,
    };
  } catch (e) {
    await db.rollback();
    throw e;
  } finally {
    db.release();
  }
}

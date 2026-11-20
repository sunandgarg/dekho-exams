// A quoted amount is informational; the server rechecks it inside the redemption transaction.
export const MONTHLY_PRICE_PAISE = 99_900;
export const STUDENT_OFFERS = [
  {
    code: "WELCOME100",
    title: "Your first one's on us",
    detail: "One free mock to find your starting point.",
    kind: "welcome",
  },
  {
    code: "COMEBACK100",
    title: "Keep that momentum",
    detail: "One more free mock after your first submission.",
    kind: "comeback",
  },
] as const;
export type Coupon = {
  id: string;
  kind: "welcome" | "comeback" | "school";
  exam: string | null;
  active: boolean;
  startsAt: number;
  expiresAt: number;
  limit: number;
  used: number;
};
export type OfferStudent = {
  verified: boolean;
  profileReady: boolean;
  consentReady: boolean;
  submittedAttempts: number;
};
export class OfferError extends Error {
  code: string;
  constructor(code: string, message: string) {
    super(message);
    this.code = code;
  }
}
export function couponCode(value: string) {
  const code = value.trim().toUpperCase();
  if (!/^[A-Z0-9-]{4,64}$/.test(code))
    throw new OfferError("invalid_code", "Check that coupon code and try again.");
  return code;
}
export function quoteAccess(
  student: OfferStudent,
  exam: string,
  coupon: Coupon | null,
  alreadyUsed = false,
  now = Date.now(),
) {
  if (!student.verified || !student.profileReady || !student.consentReady)
    throw new OfferError("profile_required", "Finish your verified profile before booking a mock.");
  if (
    !Number.isSafeInteger(student.submittedAttempts) ||
    student.submittedAttempts < 0 ||
    !Number.isFinite(now)
  )
    throw new OfferError("invalid_state", "Your test eligibility could not be checked.");
  if (!coupon)
    return {
      product: "monthly" as const,
      pricePaise: MONTHLY_PRICE_PAISE,
      duePaise: MONTHLY_PRICE_PAISE,
    };
  if (
    !["welcome", "comeback", "school"].includes(coupon.kind) ||
    !coupon.active ||
    !Number.isFinite(coupon.startsAt) ||
    !Number.isFinite(coupon.expiresAt) ||
    now < coupon.startsAt ||
    now >= coupon.expiresAt ||
    !Number.isSafeInteger(coupon.limit) ||
    coupon.limit < 1 ||
    !Number.isSafeInteger(coupon.used) ||
    coupon.used < 0 ||
    coupon.used >= coupon.limit ||
    (coupon.exam !== null && coupon.exam !== exam)
  )
    throw new OfferError("unavailable", "This coupon isn't available for this test.");
  if (alreadyUsed)
    throw new OfferError(
      "used",
      "You've already used this offer. Your booked test is in My tests.",
    );
  if (coupon.kind === "welcome" && student.submittedAttempts !== 0)
    throw new OfferError("first_attempt_only", "This offer is for your first mock.");
  if (coupon.kind === "comeback" && student.submittedAttempts < 1)
    throw new OfferError("submit_first", "Submit your first mock to unlock this offer.");
  return { product: "single" as const, pricePaise: 0, duePaise: 0 };
}

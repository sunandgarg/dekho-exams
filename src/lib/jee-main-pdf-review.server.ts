import main from "../generated/jee-main-mocks/reader.json" with { type: "json" };
import advanced from "../generated/jee-advanced-mocks/reader.json" with { type: "json" };
import type { ArchiveQuestion } from "./jee-archive.functions";

type Update = Partial<
  Pick<
    ArchiveQuestion,
    | "body"
    | "options"
    | "solution"
    | "choiceKey"
    | "choiceKeys"
    | "numericKey"
    | "numericKeys"
    | "numericRange"
    | "numericRanges"
    | "textKeys"
  >
> & { hold?: boolean };

export async function applyPdfReview(
  q: ArchiveQuestion,
  exam: "jee-main" | "jee-advanced" = "jee-main",
): Promise<ArchiveQuestion> {
  // Match the original English stem and option order, including on paper aliases.
  const payload =
    "[" +
    JSON.stringify(q.body) +
    ", [" +
    q.options.map((o) => JSON.stringify(o)).join(", ") +
    "]]";
  const bytes = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(payload));
  const hash = Array.from(new Uint8Array(bytes), (n) => n.toString(16).padStart(2, "0")).join("");
  const patch = ((exam === "jee-main" ? main : advanced) as unknown as Record<string, Update>)[
    hash
  ];
  if (!patch) return q;
  if (patch.hold) {
    const copy = { ...q, keyConflict: true };
    delete copy.choiceKey;
    delete copy.choiceKeys;
    delete copy.numericKey;
    delete copy.numericKeys;
    delete copy.numericRange;
    delete copy.numericRanges;
    delete copy.textKeys;
    return copy;
  }
  const { body = q.body, options = q.options, solution = q.solution, ...englishKey } = patch;
  return { ...q, body, options, solution, englishKey };
}

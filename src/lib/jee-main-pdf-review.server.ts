import review from "../generated/jee-main-mocks/reader.json" with { type: "json" };
import type { ArchiveQuestion } from "./jee-archive.functions";

type Update = Partial<Pick<ArchiveQuestion, "body" | "options" | "choiceKey" | "choiceKeys" | "numericKey" | "numericRange">> & { hold?: boolean };

export async function applyPdfReview(q: ArchiveQuestion): Promise<ArchiveQuestion> {
  // Match the original English stem and option order, including on paper aliases.
  const payload = "[" + JSON.stringify(q.body) + ", [" + q.options.map(o => JSON.stringify(o)).join(", ") + "]]";
  const bytes = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(payload));
  const hash = Array.from(new Uint8Array(bytes), n => n.toString(16).padStart(2, "0")).join("");
  const patch = (review as unknown as Record<string, Update>)[hash];
  if (!patch) return q;
  if (patch.hold) {
    const copy = { ...q, keyConflict: true };
    delete copy.choiceKey; delete copy.choiceKeys; delete copy.numericKey; delete copy.numericRange;
    return copy;
  }
  const { body = q.body, options = q.options, ...englishKey } = patch;
  return { ...q, body, options, englishKey };
}

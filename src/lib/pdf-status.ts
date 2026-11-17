import status from "../data/pdf-review-status.json" with { type: "json" };
export function pdfStatus(path: string) {
  return (status as Record<string, "partial" | "held" | "complete">)[path] ?? "held";
}

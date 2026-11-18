import status from "../data/pdf-review-status.json" with { type: "json" };
import editions from "../../deploy/lightsail/approved-pdfs.json" with { type: "json" };
export function pdfStatus(path: string) {
  return (status as Record<string, "partial" | "held" | "complete">)[path] ?? "held";
}
export function pdfUrl(path: string) {
  const edition = Object.hasOwn(editions, path) ? (editions as Record<string, { etag: string; sha?: string }>)[path] : undefined;
  return edition ? path + "?v=" + (edition.sha ?? edition.etag) : undefined;
}

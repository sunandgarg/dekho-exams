import { env } from "cloudflare:workers";
import { archiveCatalog, type ArchiveId } from "./jee-catalog";

export async function printEdition(exam: ArchiveId, paper: string, language: string) {
  const catalog = archiveCatalog(exam);
  if (
    !["hi", "en"].includes(language) ||
    (!catalog.papers.some((p) => p.slug === paper) &&
      !Object.hasOwn(catalog.meta, paper.replace("--", "/")))
  )
    return new Response("Edition not found", { status: 404 });
  const directory = exam === "jee-main" ? "jee-archive" : "jee-advanced-archive";
  const res = await env.ASSETS.fetch(
    new Request(`https://dekhoexams.com/${directory}/print/${paper}/${language}.bin`),
  );
  if (!res.ok || !res.body)
    return new Response("Edition unavailable", { status: res.status === 404 ? 404 : 503 });
  return new Response(res.body.pipeThrough(new DecompressionStream("gzip")), {
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      "X-Robots-Tag": "noindex, follow",
      "Content-Security-Policy":
        "default-src 'none'; style-src 'self'; script-src 'self'; img-src 'self' https:; base-uri 'none'; frame-ancestors 'self'",
    },
  });
}

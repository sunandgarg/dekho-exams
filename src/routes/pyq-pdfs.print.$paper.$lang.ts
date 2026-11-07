import { createFileRoute } from "@tanstack/react-router";
import { env } from "cloudflare:workers";
import chapterMeta from "@/data/jee-main-chapter-meta.json";
import papers from "@/data/jee-main-papers.json";
export const Route = createFileRoute("/pyq-pdfs/print/$paper/$lang")({
  server: {
    handlers: {
      GET: async ({ params }) => {
        if (
          (!papers.some((p) => p.slug === params.paper) &&
            !Object.hasOwn(chapterMeta, params.paper.replace("--", "/"))) ||
          !["hi", "en"].includes(params.lang)
        )
          return new Response("Paper not found", { status: 404 });
        const res = await env.ASSETS.fetch(
          new Request(
            "https://dekhoexams.com/jee-archive/print/" + params.paper + "/" + params.lang + ".bin",
          ),
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
      },
    },
  },
});

import { createFileRoute } from "@tanstack/react-router";
import { printEdition } from "@/lib/jee-print.server";
export const Route = createFileRoute("/pyq-pdfs/print/jee-advanced/$paper/$lang")({
  server: {
    handlers: { GET: ({ params }) => printEdition("jee-advanced", params.paper, params.lang) },
  },
});

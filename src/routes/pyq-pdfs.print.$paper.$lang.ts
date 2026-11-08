import { createFileRoute } from "@tanstack/react-router";
import { printEdition } from "@/lib/jee-print.server";
export const Route = createFileRoute("/pyq-pdfs/print/$paper/$lang")({
  server: {
    handlers: { GET: ({ params }) => printEdition("jee-main", params.paper, params.lang) },
  },
});

import { createFileRoute, redirect } from "@tanstack/react-router";
export const Route = createFileRoute("/pyq-pdfs/")({
  beforeLoad: () => { throw redirect({ href: "/pdf-library", statusCode: 301 }); },
});

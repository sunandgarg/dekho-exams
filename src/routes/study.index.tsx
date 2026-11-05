import { createFileRoute, redirect } from "@tanstack/react-router";
export const Route = createFileRoute("/study/")({
  beforeLoad: () => {
    throw redirect({ href: "/classes", statusCode: 301 });
  },
});

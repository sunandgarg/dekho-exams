import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/platform-preview")({
  beforeLoad: () => {
    throw redirect({ href: "/questions/jee-main/quick-practice", statusCode: 301 });
  },
});

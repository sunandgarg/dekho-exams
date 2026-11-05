import { createFileRoute, redirect } from "@tanstack/react-router";
export const Route = createFileRoute("/study/search")({
  validateSearch: (s) => ({ q: typeof s["q"] === "string" ? s["q"].slice(0, 120) : "" }),
  beforeLoad: ({ search }) => {
    throw redirect({
      href: `/search${search.q ? `?q=${encodeURIComponent(search.q)}` : ""}`,
      statusCode: 301,
    });
  },
});

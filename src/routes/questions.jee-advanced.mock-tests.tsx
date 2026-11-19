import { createFileRoute } from "@tanstack/react-router";
import papers from "@/data/jee-advanced-papers.json";
import { seoHead } from "@/lib/seo";
import { MockLibrary, type SetInfo } from "@/components/exams/mock-library";

const files = import.meta.glob<string>("../generated/jee-advanced-mocks/*.json.gz", {
  eager: true,
  query: "?url&no-inline",
  import: "default",
});
const sets: SetInfo[] = Object.entries(files).map(([path, url]) => {
  const [id, n] = path.split("/").pop()!.split(".");
  const count = Number(n),
    full = id!.startsWith("mixed-");
  return {
    id: id!,
    count,
    url,
    full,
    minutes: full || !id!.startsWith("extra-") ? 180 : Math.ceil(count * 3),
    name: full
      ? "Mixed mock " + Number(id!.slice(6))
      : (papers.find((p) => p.slug === id)?.title ??
        id!.replace(
          /^extra-(.+)-0?(\d+)$/,
          (_, subject, n) => subject[0].toUpperCase() + subject.slice(1) + " · Set " + n,
        )),
  };
});
const groups = {
  mixed: sets.filter((s) => s.full).sort((a, b) => a.id.localeCompare(b.id)),
  papers: papers.map((p) => sets.find((s) => s.id === p.slug)!),
  extra: sets.filter((s) => s.id.startsWith("extra-")).sort((a, b) => a.id.localeCompare(b.id)),
};
export const Route = createFileRoute("/questions/jee-advanced/mock-tests")({
  validateSearch: (search: Record<string, unknown>) => ({
    paper:
      typeof search["paper"] === "string" && groups.papers.some((p) => p.id === search["paper"])
        ? search["paper"]
        : undefined,
  }),
  head: ({ match }) =>
    seoHead({
      title: "JEE Advanced mock tests and timed papers | DekhoExams",
      description:
        "Practise JEE Advanced Physics, Chemistry and Mathematics with timed papers, mixed tests and available solutions.",
      path: "questions/jee-advanced/mock-tests",
      noindex: !!match.search.paper,
    }),
  component: () => (
    <MockLibrary
      exam="jee-advanced"
      label="JEE Advanced"
      groups={groups}
      paper={Route.useSearch().paper}
    />
  ),
});

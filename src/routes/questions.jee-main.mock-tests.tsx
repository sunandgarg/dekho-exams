import { createFileRoute } from "@tanstack/react-router";
import papers from "@/data/jee-main-papers.json";
import { seoHead } from "@/lib/seo";
import { MockLibrary } from "@/components/exams/mock-library";

const files = import.meta.glob<string>("../generated/jee-main-mocks/*.json.gz", {
  eager: true,
  query: "?url&no-inline",
  import: "default",
});
const sets = Object.entries(files)
  .map(([path, url]) => {
    const [kind, number, count] = path.split("/").pop()!.split(".")[0]!.split("-");
    const full = kind === "mock";
    const name = full ? "Mock test" : kind![0]!.toUpperCase() + kind!.slice(1) + " practice";
    return {
      id: kind + "-" + number,
      name: name + " " + Number(number),
      full,
      count: Number(count),
      minutes: full ? 180 : Math.ceil(Number(count) * 2.4),
      url,
    };
  })
  .sort((a, b) => Number(b.full) - Number(a.full) || a.id.localeCompare(b.id));
const archiveFiles = import.meta.glob<string>("../generated/jee-main-mocks/archive/*.json.gz", {
  eager: true,
  query: "?url&no-inline",
  import: "default",
});
const archiveSets = new Map(
  Object.entries(archiveFiles).map(([path, url]) => {
    const [id, n] = path.split("/").pop()!.split(".");
    const count = Number(n);
    const name = id!.replace(
      /^extra-(.+)-0?(\d+)$/,
      (_, subject, index) => subject[0].toUpperCase() + subject.slice(1) + " · Set " + index,
    );
    return [
      id!,
      {
        id: id!,
        count,
        name,
        url,
        full: false,
        minutes: id!.startsWith("extra-") ? Math.ceil(count * 2.4) : 180,
      },
    ];
  }),
);
const paperSets = papers.map((p) => ({ ...archiveSets.get(p.slug)!, name: p.title }));
const extraSets = [...archiveSets.values()].filter((s) => s.id.startsWith("extra-"));
const moreMocks = [...archiveSets.values()]
  .filter((s) => s.id.startsWith("combined-"))
  .map((s) => ({
    ...s,
    full: true,
    minutes: 180,
    name: "Mock test " + Number(s.id.slice("combined-".length)),
  }));
const groups = {
  mixed: [...sets.filter((s) => s.full), ...moreMocks, ...sets.filter((s) => !s.full)],
  papers: paperSets,
  extra: extraSets,
};
export const Route = createFileRoute("/questions/jee-main/mock-tests")({
  validateSearch: (search: Record<string, unknown>) => ({
    paper:
      typeof search["paper"] === "string" && paperSets.some((p) => p.id === search["paper"])
        ? search["paper"]
        : undefined,
  }),
  head: ({ match }) =>
    seoHead({
      title: "JEE Main mock tests with worked solutions | DekhoExams",
      description:
        "Practise JEE Main previous-year questions in timed Physics, Chemistry and Mathematics sets.",
      path: "questions/jee-main/mock-tests",
      noindex: !!match.search.paper,
    }),
  component: Library,
});
function Library() {
  return (
    <MockLibrary exam="jee-main" label="JEE Main" groups={groups} paper={Route.useSearch().paper} />
  );
}

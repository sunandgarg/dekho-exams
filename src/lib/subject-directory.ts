import reference from "../data/khan-course-reference.json" with { type: "json" };

export type DirectoryIcon =
  "maths" | "science" | "english" | "computing" | "economics" | "boards" | "explore" | "teachers";
export type DirectoryItem = { id: string; label: string; referenceUrl: string; href: string };
export type DirectoryGroup = {
  id: string;
  title: string;
  path: string;
  parent: string;
  icon: DirectoryIcon;
  items: DirectoryItem[];
};

// Explicit mappings preserve our route grammar; reference URLs are never local routes.
const groups: [string, string, string, DirectoryIcon][] = [
  ["NCERT Mathematics", "/ncert/maths", "/ncert", "maths"],
  ["NCERT Science", "/ncert/science", "/ncert", "science"],
  ["Mathematics: Bridge", "/ncert/maths/bridge", "/ncert/maths", "maths"],
  ["Science: Bridge", "/ncert/science/bridge", "/ncert/science", "science"],
  ["Mathematics: Revision", "/ncert/maths/revision", "/ncert/maths", "maths"],
  ["Science: Revision", "/ncert/science/revision", "/ncert/science", "science"],
  ["Karnataka Mathematics", "/state-boards/karnataka/maths", "/state-boards/karnataka", "maths"],
  ["Karnataka Science", "/state-boards/karnataka/science", "/state-boards/karnataka", "science"],
  [
    "Maharashtra Mathematics",
    "/state-boards/maharashtra/maths",
    "/state-boards/maharashtra",
    "maths",
  ],
  [
    "Maharashtra Science",
    "/state-boards/maharashtra/science",
    "/state-boards/maharashtra",
    "science",
  ],
  ["Telangana Mathematics", "/state-boards/telangana/maths", "/state-boards/telangana", "maths"],
  ["Telangana Science", "/state-boards/telangana/science", "/state-boards/telangana", "science"],
  ["English & Grammar", "/english/grammar", "/english", "english"],
  ["Computer Science", "/computer-science", "/subjects", "computing"],
  ["Economics", "/economics", "/subjects", "economics"],
  ["All Boards", "/boards", "/", "boards"],
  ["Beyond the Classroom", "/explore-more", "/resources", "explore"],
  ["For Educators", "/teachers", "/resources", "teachers"],
];

export const SUBJECT_DIRECTORY: DirectoryGroup[] = groups.map(
  ([title, path, parent, icon], index) => {
    const source = reference.groups[index]!;
    const id = path.slice(1).replaceAll("/", "-");
    const items = source.items.map((item, i) => {
      const itemId = new URL(item.url).pathname.split("/").filter(Boolean).at(-1)!;
      let label = item.label
        .replace(/^KA (English|Computer|Information|Economics|Statistics|Macro|Micro)/, "$1")
        .replace(/^KA /, "Karnataka ")
        .replace(/^MH /, "Maharashtra ")
        .replace(/^TG /, "Telangana ");
      if (icon === "teachers")
        label = [
          "Teaching essentials",
          "Advanced teaching",
          "Mentor development",
          "All educator resources",
        ][i]!;
      if (label.startsWith("See ") || i === source.items.length - 1)
        label = icon === "teachers" ? "All educator resources" : `Explore ${title}`;
      return {
        id: itemId,
        label,
        referenceUrl: item.url,
        href: `${path}?topic=${encodeURIComponent(itemId)}`,
      };
    });
    return { id, title, path, parent, icon, items };
  },
);

export function directoryGroup(path: string) {
  return SUBJECT_DIRECTORY.find((group) => group.path === path);
}
export function directoryItem(path: string, id: string) {
  return directoryGroup(path)?.items.find((item) => item.id === id);
}

export const HOME_SHORTCUTS = [
  {
    path: "/ncert",
    title: "NCERT",
    detail: "Books, solutions & notes",
    icon: "books",
    color: "cobalt",
  },
  {
    path: "/boards",
    title: "School Boards",
    detail: "CBSE, CISCE & state boards",
    icon: "boards",
    color: "emerald",
  },
  {
    path: "/exams",
    title: "Entrance & Competitive",
    detail: "JEE, NEET, CUET & more",
    icon: "exams",
    color: "coral",
  },
  {
    path: "/textbook-solutions",
    title: "Books & Solutions",
    detail: "Reference book collections",
    icon: "books",
    color: "charcoal",
  },
  {
    path: "/resources",
    title: "Study & Practice",
    detail: "Self-checks, papers & revision",
    icon: "practice",
    color: "amber",
  },
  {
    path: "/scholarships",
    title: "Scholarships & Awards",
    detail: "Opportunities to go further",
    icon: "awards",
    color: "berry",
  },
] as const;

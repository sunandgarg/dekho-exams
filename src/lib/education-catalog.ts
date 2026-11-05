import { GRADES, SCHOOL_LESSONS, lessonPath, type SchoolLesson } from "./school-content";
import { SUBJECT_DIRECTORY } from "./subject-directory";
import { EXAM_GUIDES } from "./exam-update-guides";
export const GRADES_FOR_FILTER = GRADES;

export type CatalogLink = { title: string; path: string };
export type CatalogSection = { title: string; paths: string[]; empty?: string };
export type EducationPage = {
  path: string;
  title: string;
  description: string;
  parent: string;
  family: "school" | "books" | "boards" | "exams" | "resources" | "languages" | "utility";
  children: string[];
  resourceIds: string[];
  sources: CatalogLink[];
  sections?: CatalogSection[];
  notice?: string | undefined;
  resourceId?: string;
  reviewed: boolean;
};
export type LearningResource = {
  id: string;
  canonicalPath: string;
  version: number;
  language: string;
  type: "lesson";
  status: "preview" | "published";
  rights: "original" | "licensed" | "pending";
  author: string | null;
  reviewer: string | null;
  reviewedAt: string | null;
  syllabusVersion: string | null;
  bookEdition: string | null;
  board: string | null;
  lesson: SchoolLesson;
};

// IDs are persisted by learners. Never rename an ID when changing a title or URL.
const RESOURCE_IDS: Record<string, string> = {
  "counting-to-20": "pp-0001",
  "tens-and-ones": "pp-0002",
  "multiplication-groups": "pp-0003",
  "equivalent-fractions": "pp-0004",
  "decimal-place-value": "pp-0005",
  "adding-fractions": "pp-0006",
  "food-and-nutrients": "pp-0007",
  "integers-on-number-line": "pp-0008",
  "linear-equations": "pp-0009",
  "polynomial-identities": "pp-0010",
  "quadratic-equations": "pp-0011",
  "electric-circuits": "pp-0012",
  "sets-and-intersection": "pp-0013",
  "derivatives-from-first-principles": "pp-0014",
};
export const RESOURCES: LearningResource[] = SCHOOL_LESSONS.map((lesson) => ({
  id: RESOURCE_IDS[lesson.slug]!,
  canonicalPath: lessonPath(lesson),
  version: 1,
  language: "en",
  type: "lesson",
  status: "preview",
  rights: "original",
  author: null,
  reviewer: null,
  reviewedAt: null,
  syllabusVersion: null,
  bookEdition: null,
  board: null,
  lesson,
}));
export const LANGUAGES = [
  ["english", "English", "en"],
  ["hindi", "Hindi", "hi"],
  ["kannada", "Kannada", "kn"],
  ["tamil", "Tamil", "ta"],
  ["telugu", "Telugu", "te"],
  ["marathi", "Marathi", "mr"],
  ["bengali", "Bengali", "bn"],
  ["gujarati", "Gujarati", "gu"],
  ["malayalam", "Malayalam", "ml"],
  ["odia", "Odia", "or"],
  ["punjabi", "Punjabi", "pa"],
  ["assamese", "Assamese", "as"],
  ["urdu", "Urdu", "ur"],
] as const;
export const SUBJECTS = [
  ["maths", "Mathematics"],
  ["science", "Science"],
  ["english", "English"],
  ["hindi", "Hindi"],
  ["environmental-studies", "Environmental Studies"],
  ["social-science", "Social Science"],
  ["physics", "Physics"],
  ["chemistry", "Chemistry"],
  ["biology", "Biology"],
  ["commerce", "Commerce"],
  ["computer-science", "Computer Science"],
] as const;
export const STATES = [
  ["andhra-pradesh", "Andhra Pradesh"],
  ["assam", "Assam"],
  ["bihar", "Bihar"],
  ["chhattisgarh", "Chhattisgarh"],
  ["gujarat", "Gujarat"],
  ["haryana", "Haryana"],
  ["jharkhand", "Jharkhand"],
  ["karnataka", "Karnataka"],
  ["kerala", "Kerala"],
  ["madhya-pradesh", "Madhya Pradesh"],
  ["maharashtra", "Maharashtra"],
  ["mizoram", "Mizoram"],
  ["nagaland", "Nagaland"],
  ["odisha", "Odisha"],
  ["punjab", "Punjab"],
  ["rajasthan", "Rajasthan"],
  ["tamil-nadu", "Tamil Nadu"],
  ["telangana", "Telangana"],
  ["uttar-pradesh", "Uttar Pradesh"],
  ["uttarakhand", "Uttarakhand"],
  ["west-bengal", "West Bengal"],
  ["jammu-and-kashmir", "Jammu & Kashmir"],
] as const;
export const EXAMS = [
  ["jee", "JEE", "Engineering entrance preparation"],
  ["neet", "NEET", "Medical entrance preparation"],
  ["cuet", "CUET", "University entrance preparation"],
  ["cat", "CAT", "Management entrance preparation"],
  ["gate", "GATE", "Graduate engineering and science preparation"],
  ["nda", "NDA", "Defence entrance preparation"],
  ["clat", "CLAT", "Law entrance preparation"],
  ["ca", "CA", "Chartered accountancy preparation"],
  ["upsc", "UPSC", "Civil services preparation"],
] as const;
export const RESOURCE_TYPES = [
  ["ncert-books", "NCERT Books"],
  ["ncert-solutions", "NCERT Solutions"],
  ["ncert-notes", "NCERT Notes"],
  ["ncert-exemplar", "NCERT Exemplar"],
  ["ncert-syllabus", "NCERT Syllabus"],
  ["sample-papers", "Sample Papers"],
  ["previous-year-papers", "Previous Year Papers"],
  ["important-questions", "Important Questions"],
  ["worksheets", "Worksheets"],
  ["tests", "Practice Tests"],
  ["formulas", "Formulas"],
  ["flashcards", "Flashcards"],
] as const;
const NCERT = {
  title: "NCERT official textbook portal",
  path: "https://ncert.nic.in/textbook.php",
};
const NCERT_EXEMPLAR = {
  title: "NCERT exemplar problems",
  path: "https://ncert.nic.in/exemplar-problems.php?ln=en",
};
const NCERT_LAB_MANUAL = {
  title: "NCERT science laboratory manuals",
  path: "https://ncert.nic.in/science-laboratory-manual.php?ln=en",
};
export const NCERT_SYLLABUS_SOURCE = {
  title: "NCERT official syllabus portal",
  path: "https://ncert.nic.in/syllabus.php",
};
const NTA = { title: "National Testing Agency", path: "https://www.nta.ac.in/" };
const CBSE = { title: "CBSE Academic", path: "https://cbseacademic.nic.in/" };
const CBSE_CURRICULUM = {
  title: "CBSE curriculum 2026-27 (check your course variant)",
  path: "https://cbseacademic.nic.in/curriculum_2027.html",
};
const CISCE = { title: "CISCE official website", path: "https://cisce.org/" };
const pending = "No reviewed Dekhoexams material is published in this collection yet.";
const ncertKinds = RESOURCE_TYPES.filter(([slug]) => slug.startsWith("ncert"));
const ncertClassPath = (grade: number) => `/ncert/class-${grade}`;
const ncertMaterialPath = (grade: number, kind: string) =>
  `${ncertClassPath(grade)}/${kind.replace(/^ncert-/, "")}`;
const subjectsForGrade = (grade: number) =>
  SUBJECTS.filter(([slug]) =>
    grade <= 2
      ? ["maths", "english", "hindi"].includes(slug)
      : grade <= 5
        ? ["maths", "english", "hindi", "environmental-studies"].includes(slug)
        : grade <= 10
          ? ["maths", "science", "english", "hindi", "social-science", "computer-science"].includes(slug)
          : ["maths", "english", "hindi", "physics", "chemistry", "biology", "commerce", "computer-science"].includes(slug),
  );
const subjectPaths = (parent: string, grade: number) =>
  subjectsForGrade(grade).map(([slug]) => `${parent}/${slug}`);
const chapterPaths = (grade: number, title: string) =>
  RESOURCES.filter((r) => r.lesson.grade === grade && r.lesson.subject === title).map(
    (r) => r.canonicalPath,
  );
const classPracticePaths = (grade: number) =>
  SUBJECTS.filter(([, title]) =>
    RESOURCES.some((r) => r.lesson.grade === grade && r.lesson.subject === title),
  ).map(([slug]) => `/class-${grade}/${slug}`);
const pages = new Map<string, EducationPage>();
function add(
  path: string,
  title: string,
  family: EducationPage["family"],
  parent = "/",
  extra: Partial<EducationPage> = {},
) {
  if (pages.has(path)) throw new Error(`Duplicate education route: ${path}`);
  pages.set(path, {
    path,
    title,
    family,
    parent,
    description: `${title} on Dekhoexams.`,
    children: [],
    resourceIds: [],
    sources: [],
    reviewed: false,
    ...extra,
  });
}
const resourceIds = (test: (r: LearningResource) => boolean) =>
  RESOURCES.filter(test).map((r) => r.id);
function addSubjectPages(parent: string, grade: number, family: EducationPage["family"], sources: CatalogLink[] = []) {
  for (const [slug, title] of subjectsForGrade(grade)) {
    const chapters = chapterPaths(grade, title);
    add(`${parent}/${slug}`, `Class ${grade} ${title}`, family, parent, {
      description: chapters.length
        ? `Start with a ${title} chapter below. The worked example is there when you need it.`
        : `We're still adding Class ${grade} ${title} chapters. Nothing to read here yet.`,
      sections: [
        { title: "Chapters", paths: chapters, empty: "Use the contents page in your school book for now. We'll add chapters here after checking them." },
        ...(parent.startsWith("/ncert/")
          ? [{ title: "Books and solutions", paths: [ncertMaterialPath(grade, "ncert-books"), ncertMaterialPath(grade, "ncert-solutions")] }]
          : []),
      ],
      notice: chapters.length
        ? "Your school's book may use a different chapter order. These lessons have not been matched to a textbook edition."
        : undefined,
      sources,
    });
  }
}

add("/classes", "Classes 1-12", "school", "/", {
  description: "Choose your class. You can pick a board and subject on the next page.",
  children: GRADES.map((g) => `/class-${g}`),
});
add("/subjects", "Subjects", "school", "/", { children: SUBJECTS.map(([s]) => `/${s}`) });
for (const [slug, title] of SUBJECTS) {
  const ids = resourceIds((r) => r.lesson.subject === title);
  add(`/${slug}`, title, "school", "/subjects", {
    resourceIds: ids,
    notice: ids.length ? undefined : pending,
  });
}
for (const grade of GRADES) {
  const boardPaths = [
    ncertClassPath(grade),
    `/cbse/class-${grade}`,
    grade <= 8 ? `/cisce/class-${grade}` : grade <= 10 ? `/icse/class-${grade}` : `/isc/class-${grade}`,
    ...(grade === 10 || grade === 12 ? [`/nios/class-${grade}`] : []),
    ...STATES.map(([slug]) => `/state-boards/${slug}/class-${grade}`),
  ];
  add(`/class-${grade}`, `Class ${grade}`, "school", "/classes", {
    description: `Pick your board, then open a subject. You can always come back and switch.`,
    children: subjectPaths(`/class-${grade}`, grade),
    resourceIds: resourceIds((r) => r.lesson.grade === grade),
    sections: [
      { title: "Boards & books", paths: boardPaths },
      { title: "Subjects", paths: subjectPaths(`/class-${grade}`, grade) },
    ],
    notice: "Books and chapter order vary by school. Check the title and edition on your own copy.",
  });
  addSubjectPages(`/class-${grade}`, grade, "school");
}
for (const resource of RESOURCES)
  add(
    resource.canonicalPath,
    resource.lesson.title,
    "school",
    resource.canonicalPath.slice(0, resource.canonicalPath.lastIndexOf("/")),
    {
      resourceId: resource.id,
      description: resource.lesson.summary,
    },
  );

add("/ncert", "NCERT Books & Solutions", "books", "/", {
  children: [
    ...GRADES.map(ncertClassPath),
    ...LANGUAGES.map(([slug]) => `/ncert/${slug}`),
    ...ncertKinds.map(([slug]) => `/${slug}`),
  ],
  sections: [
    { title: "Choose a class", paths: GRADES.map(ncertClassPath) },
    { title: "Choose a language", paths: LANGUAGES.map(([slug]) => `/ncert/${slug}`) },
    { title: "NCERT study materials", paths: ncertKinds.map(([slug]) => `/${slug}`) },
  ],
  sources: [NCERT, NCERT_SYLLABUS_SOURCE, NCERT_EXEMPLAR, NCERT_LAB_MANUAL],
});
for (const grade of GRADES) {
  const paths = subjectPaths(ncertClassPath(grade), grade);
  add(ncertClassPath(grade), `NCERT Class ${grade}`, "books", "/ncert", {
    description: `Browse Class ${grade} subjects first, then NCERT books, solutions and practice collections.`,
    children: paths.concat(ncertKinds.map(([slug]) => ncertMaterialPath(grade, slug))),
    sections: [
      {
        title: "Subjects",
        paths,
      },
      {
        title: "Books and solutions",
        paths: ncertKinds
          .filter(([slug]) => slug !== "ncert-syllabus")
          .map(([slug]) => ncertMaterialPath(grade, slug)),
      },
      {
        title: "Papers and practice",
        paths: ["/sample-papers", "/previous-year-papers", "/tests"],
      },
    ],
    notice:
      "Subject links currently lead to original Dekhoexams topics, not verified NCERT chapter mappings. Books, solutions and exam papers are awaiting editorial review.",
    sources: [NCERT],
  });
  addSubjectPages(ncertClassPath(grade), grade, "books", [NCERT]);
}
for (const [slug, title] of RESOURCE_TYPES) {
  const isNcert = slug.startsWith("ncert");
  add(`/${slug}`, title, isNcert ? "books" : "resources", isNcert ? "/ncert" : "/resources", {
    children: isNcert ? GRADES.map((g) => ncertMaterialPath(g, slug)) : [],
    resourceIds: slug === "tests" ? resourceIds(() => true) : [],
    notice:
      slug === "tests"
        ? "Available: two-question chapter self-checks. Full-length mock exams are not available yet."
        : pending,
    sources: isNcert
      ? [NCERT]
      : ["sample-papers", "previous-year-papers"].includes(slug)
        ? [CBSE]
        : [],
  });
  if (isNcert)
    for (const grade of GRADES)
      add(
        ncertMaterialPath(grade, slug),
        `${title}: Class ${grade}`,
        "books",
        ncertClassPath(grade),
        {
          notice:
            slug === "ncert-syllabus"
              ? `A reviewed Class ${grade} syllabus outline is not published yet. Check the current NCERT syllabus and confirm your exam requirements with your school board.`
              : "Book editions, syllabus alignment and chapter material are awaiting review. General lessons below are not NCERT exercise solutions.",
          resourceIds:
            slug === "ncert-syllabus" ? [] : resourceIds((r) => r.lesson.grade === grade),
          sources:
            slug === "ncert-syllabus"
              ? [NCERT_SYLLABUS_SOURCE, ...(grade === 10 || grade === 12 ? [CBSE_CURRICULUM] : [])]
              : [NCERT],
        },
      );
}
add("/languages", "Study Languages", "languages", "/", {
  children: LANGUAGES.map(([s]) => `/ncert/${s}`),
});
for (const [slug, title, code] of LANGUAGES) {
  add(`/ncert/${slug}`, `NCERT ${title}`, "languages", "/ncert", {
    description: `NCERT ${title} resource directory and language availability.`,
    children: GRADES.map((grade) => `/ncert/${slug}/class-${grade}`),
    sections: [
      { title: "Choose a class", paths: GRADES.map((grade) => `/ncert/${slug}/class-${grade}`) },
    ],
    notice:
      code === "en"
        ? "Original English lessons are available below. They are not NCERT textbook solutions."
        : `Dekhoexams ${title} lessons and translations are not published yet. This directory does not claim that NCERT publishes every book in ${title}.`,
    resourceIds: resourceIds((r) => r.language === code),
    sources: [NCERT],
  });
  for (const grade of GRADES)
    add(
      `/ncert/${slug}/class-${grade}`,
      `NCERT ${title} Class ${grade}`,
      "languages",
      `/ncert/${slug}`,
      {
        description: `Class ${grade} ${title} study directory.`,
        children:
          grade === 10 && (slug === "english" || slug === "hindi")
            ? [`/ncert/${slug}/class-10/syllabus`]
            : [],
        notice:
          code === "en"
            ? "Original English lessons are linked below, but they are not verified NCERT textbook chapters or solutions."
            : `No reviewed ${title} chapters, translations or papers are published for this class yet. NCERT language availability must be checked book by book.`,
        sections: [
          {
            title: "Chapters",
            paths: [],
            empty: `Verified ${title} chapter listings are not published yet.`,
          },
          {
            title: "Original Dekhoexams lessons",
            paths: code === "en" ? classPracticePaths(grade) : [],
            empty: `No reviewed ${title} lessons are available yet.`,
          },
          {
            title: "Books and solutions",
            paths:
              code === "en"
                ? ncertKinds
                    .filter(([kind]) => kind !== "ncert-syllabus")
                    .map(([kind]) => ncertMaterialPath(grade, kind))
                : [],
            empty: "Edition-specific books and solutions are awaiting review.",
          },
          {
            title: "Papers and practice",
            paths: code === "en" ? ["/sample-papers", "/previous-year-papers", "/tests"] : [],
            empty: `No ${title} papers or practice sets are published yet.`,
          },
        ],
        sources: [NCERT],
      },
    );
  if (slug === "english" || slug === "hindi")
    add(
      `/ncert/${slug}/class-10/syllabus`,
      `NCERT ${title} Class 10 Syllabus`,
      "languages",
      `/ncert/${slug}/class-10`,
      {
        description: `Class 10 ${title} syllabus links and course-selection guidance.`,
        notice:
          slug === "english"
            ? "A reviewed NCERT English chapter outline is not published yet. For a CBSE exam, confirm whether your school uses English Language and Literature or English Communicative before choosing a syllabus."
            : "A reviewed NCERT Hindi chapter outline is not published yet. For a CBSE exam, confirm whether your school uses Hindi Course A or Course B before choosing a syllabus.",
        sources: [NCERT_SYLLABUS_SOURCE, CBSE_CURRICULUM],
      },
    );
}
add("/boards", "School Boards", "boards", "/", {
  children: ["/cbse", "/cisce", "/nios", "/state-boards"],
});
add("/cisce", "CISCE", "boards", "/boards", {
  children: ["/icse", "/isc", ...GRADES.filter((grade) => grade <= 8).map((grade) => `/cisce/class-${grade}`)],
  sources: [CISCE],
});
for (const [slug, title, grades, sources] of [
  ["cbse", "CBSE", GRADES, [CBSE]],
  ["cisce", "CISCE school", GRADES.filter((grade) => grade <= 8), [CISCE]],
  ["icse", "ICSE", [9, 10], [CISCE]],
  ["isc", "ISC", [11, 12], [CISCE]],
  ["nios", "NIOS", [10, 12], []],
] as const) {
  if (slug !== "cisce")
    add(`/${slug}`, title, "boards", slug === "icse" || slug === "isc" ? "/cisce" : "/boards", {
      children: grades.map((g) => `/${slug}/class-${g}`),
      sources: [...sources],
    });
  for (const grade of grades) {
    const parent = `/${slug}/class-${grade}`;
    add(`/${slug}/class-${grade}`, `${title} Class ${grade}`, "boards", `/${slug}`, {
      notice:
        "Board-specific book editions and chapter mappings are awaiting review. Original Dekhoexams lessons are not a complete board course.",
      children: subjectPaths(parent, grade),
      sections: [
        {
          title: "Subjects",
          paths: subjectPaths(parent, grade),
        },
        {
          title: "Papers and practice",
          paths: ["/sample-papers", "/previous-year-papers", "/tests"],
        },
      ],
      sources: [...sources],
    });
    addSubjectPages(parent, grade, "boards", [...sources]);
  }
}
add("/state-boards", "State Books & Boards", "boards", "/boards", {
  children: STATES.map(([s]) => `/state-boards/${s}`),
});
for (const [slug, title] of STATES)
  add(`/state-boards/${slug}`, `${title} State Books`, "boards", "/state-boards", {
    notice:
      "State-specific textbook editions and language availability are awaiting verification. No state textbooks are hosted here yet.",
    children: GRADES.map((grade) => `/state-boards/${slug}/class-${grade}`),
    sections: [
      {
        title: "Choose a class",
        paths: GRADES.map((grade) => `/state-boards/${slug}/class-${grade}`),
      },
    ],
  });
for (const [slug, title] of STATES)
  for (const grade of GRADES) {
    const parent = `/state-boards/${slug}/class-${grade}`;
    add(
      parent,
      `${title} Class ${grade}`,
      "boards",
      `/state-boards/${slug}`,
      {
        description: `Class ${grade} study directory for the ${title} state board.`,
        notice:
          "State textbook editions, chapters and papers have not yet been verified or published. General Dekhoexams lessons below are not state-board solutions.",
        children: subjectPaths(parent, grade),
        sections: [
          {
            title: "Subjects",
            paths: subjectPaths(parent, grade),
          },
          {
            title: "Papers and practice",
            paths: ["/sample-papers", "/previous-year-papers", "/tests"],
          },
        ],
      },
    );
    addSubjectPages(parent, grade, "boards");
  }
add("/textbook-solutions", "Books & Solutions", "books", "/", {
  children: [
    "/ncert-solutions",
    "/textbook-solutions/rd-sharma",
    "/textbook-solutions/rs-aggarwal",
    "/textbook-solutions/selina",
    "/textbook-solutions/ts-grewal",
    "/textbook-solutions/tr-jain",
    "/textbook-solutions/frank",
  ],
});
for (const [slug, title] of [
  ["rd-sharma", "RD Sharma"],
  ["rs-aggarwal", "RS Aggarwal"],
  ["selina", "Selina"],
  ["ts-grewal", "TS Grewal"],
  ["tr-jain", "TR Jain"],
  ["frank", "Frank"],
])
  add(`/textbook-solutions/${slug}`, `${title} Solutions`, "books", "/textbook-solutions", {
    notice:
      "Edition-specific original solutions are not published yet. Dekhoexams is independent of this publisher; no copyrighted books are reproduced.",
  });
add("/exams", "Entrance & Competitive Exams", "exams", "/", {
  children: EXAMS.map(([s]) => `/${s}`),
});
add("/exam-updates", "Exam Date Sheets, Answer Keys and Results", "exams", "/exams", {
  description:
    "Find official CBSE date sheets and results, NTA answer keys, and CBSE sample papers and marking schemes. Check the publishing authority for the latest release.",
  children: EXAM_GUIDES.map((guide) => guide.path),
  notice: "Dekhoexams is independent of CBSE and NTA. Availability changes by exam year and session; always confirm the newest official notice.",
});
for (const guide of EXAM_GUIDES) {
  add(guide.path, guide.title, "exams", "/exam-updates", {
    description: guide.description,
    sources: [...new Map(guide.sections.flatMap((section) => section.links).map((link) => [link.path, link])).values()],
    notice: "Official portals control release dates and downloads. Dekhoexams does not host exam files or collect exam credentials.",
  });
}
for (const [slug, title, description] of EXAMS)
  add(`/${slug}`, title, "exams", "/exams", {
    description,
    notice:
      "Exam-specific question banks, papers and mock tests are not published yet. Confirm eligibility, dates and the current syllabus with the exam authority.",
    children: ["/classes", "/sample-papers", "/previous-year-papers"],
    sources: ["jee", "neet", "cuet"].includes(slug)
      ? [NTA]
      : slug === "ca"
        ? [{ title: "ICAI", path: "https://www.icai.org/" }]
        : slug === "clat"
          ? [{ title: "Consortium of NLUs", path: "https://consortiumofnlus.ac.in/" }]
          : [],
  });
add("/ug", "Undergraduate (UG)", "exams", "/", {
  children: ["/cuet", "/jee", "/neet", "/clat", "/ca"],
  notice:
    "Degree-specific lessons are not published yet. Entrance preparation directories are listed below.",
});
add("/pg", "Postgraduate (PG)", "exams", "/", {
  children: ["/cuet", "/cat", "/gate"],
  notice:
    "Postgraduate subject courses are not published yet. Verify the UG or PG variant of an entrance exam with its authority.",
});
add("/scholarships", "Scholarships & Awards", "resources", "/", {
  notice:
    "No independently verified scholarship listings are published here yet. Check eligibility and deadlines at the official source.",
  sources: [{ title: "National Scholarship Portal", path: "https://scholarships.gov.in/" }],
});
add("/resources", "Study Resources", "resources", "/", {
  children: [...RESOURCE_TYPES.map(([s]) => `/${s}`), "/scholarships"],
});
add("/search", "Search Dekhoexams", "utility");
add("/my-study", "My Study", "utility");
add("/site-map", "All Collections", "utility", "/", {
  children: [
    "/classes",
    "/subjects",
    "/boards",
    "/ncert",
    "/textbook-solutions",
    "/exams",
    "/ug",
    "/pg",
    "/languages",
    "/resources",
  ],
});

for (const group of SUBJECT_DIRECTORY) {
  if (!pages.has(group.path))
    add(group.path, group.title, "resources", group.parent, {
      notice:
        "Dekhoexams course material for this collection is not published yet. Individual options include a clearly labelled external learning reference.",
    });
  const parent = pages.get(group.parent);
  if (parent && !parent.children.includes(group.path)) parent.children.push(group.path);
}
pages.get("/exams")!.children.push("/ug", "/pg");
pages.get("/exams")!.children.unshift("/exam-updates");
export const EDUCATION_PAGES = [...pages.values()];
export function educationPage(path: string) {
  return pages.get(path);
}
export function relatedEducationPages(page: EducationPage): EducationPage[] {
  const grade = Number(/(?:^|\/)class-(\d+)(?:\/|$)/.exec(page.path)?.[1] ?? 0);
  const subject = SUBJECTS.find(([slug]) => page.path.includes(`/${slug}`));
  const candidates: string[] = [];
  if (grade) {
    candidates.push(`/class-${grade}`, `/ncert/class-${grade}`);
    if (subject) candidates.push(`/ncert/class-${grade}/${subject[0]}`, `/${subject[0]}`);
    if (grade === 10 || grade === 12) candidates.push(`/cbse/class-${grade}`);
    candidates.push(`/ncert/english/class-${grade}`, `/ncert/class-${grade}/syllabus`);
    const peers = RESOURCES.filter((r) => r.lesson.grade === grade && r.id !== page.resourceId);
    candidates.push(...peers.slice(0, 2).map((r) => r.canonicalPath));
  }
  if (page.path.startsWith("/exam-updates/"))
    candidates.push(...EXAM_GUIDES.map((guide) => guide.path));
  if (page.path.startsWith("/ncert/") && page.path.includes("/class-"))
    candidates.push("/ncert-books", "/ncert-solutions");
  if (page.family === "boards") candidates.push("/ncert", "/sample-papers");
  if (page.family === "exams") candidates.push("/exam-updates", "/previous-year-papers");
  if (page.family === "resources") candidates.push("/classes", "/ncert");
  if (page.parent !== "/") candidates.push(page.parent);
  const siblings = EDUCATION_PAGES.filter((candidate) => candidate.parent === page.parent);
  candidates.push(...siblings.slice(0, 3).map((candidate) => candidate.path));
  return [...new Set(candidates)]
    .filter((path) => path !== page.path)
    .map(educationPage)
    .filter((candidate): candidate is EducationPage => !!candidate && candidate.family !== "utility")
    .slice(0, 7);
}
export function resourceById(id: string) {
  return RESOURCES.find((r) => r.id === id);
}
export function educationBreadcrumbs(page: EducationPage): EducationPage[] {
  const chain: EducationPage[] = [page];
  let parent = pages.get(page.parent);
  while (parent) {
    chain.unshift(parent);
    parent = pages.get(parent.parent);
  }
  return chain;
}
export function resourceReady(resource: LearningResource): boolean {
  return (
    resource.status === "published" &&
    resource.rights !== "pending" &&
    !!resource.author?.trim() &&
    !!resource.reviewer?.trim() &&
    !!resource.reviewedAt &&
    Number.isFinite(Date.parse(resource.reviewedAt)) &&
    resource.lesson.questions.length > 0
  );
}
export function educationIndexable(page: EducationPage): boolean {
  if (page.family === "utility") return false;
  if (page.resourceId) {
    const r = resourceById(page.resourceId);
    return !!r && resourceReady(r);
  }
  return (
    page.reviewed &&
    (page.resourceIds.some((id) => {
      const r = resourceById(id);
      return !!r && resourceReady(r);
    }) ||
      page.sources.length > 0)
  );
}
export const EDUCATION_ALIASES: Record<string, string> = {
  "/study": "/classes",
  "/study/search": "/search",
  ...Object.fromEntries(GRADES.map((g) => [`/study/class-${g}`, `/class-${g}`])),
  ...Object.fromEntries(
    RESOURCES.map((r) => [`/study/class-${r.lesson.grade}/${r.lesson.slug}`, r.canonicalPath]),
  ),
  ...Object.fromEntries(
    ncertKinds.flatMap(([kind]) =>
      GRADES.map((grade) => [`/${kind}/class-${grade}`, ncertMaterialPath(grade, kind)]),
    ),
  ),
};
const ownedRoots = new Set(EDUCATION_PAGES.map((p) => p.path.split("/")[1]));
export function ownsEducationPath(path: string) {
  return ownedRoots.has(path.split("/")[1]) || /^\/class-\d+(?:\/|$)/.test(path);
}

export const HOME_CATEGORIES = [
  ["/ncert", "NCERT Books & Solutions"],
  ["/state-boards", "State Books"],
  ["/textbook-solutions", "Books & Solutions"],
  ["/cbse", "CBSE"],
  ["/cisce", "CISCE"],
  ...EXAMS.slice(0, 5).map(([s, t]) => [`/${s}`, t]),
  ["/scholarships", "Scholarships & Awards"],
  ...EXAMS.slice(5).map(([s, t]) => [`/${s}`, t]),
  ["/ug", "UG"],
  ["/pg", "PG"],
] as const;
export const EDUCATION_NAV = [
  {
    label: "Classes",
    path: "classes",
    sections: [{ title: "School", links: GRADES.map((g) => [`Class ${g}`, `class-${g}`]) }],
  },
  {
    label: "Books & Boards",
    path: "boards",
    sections: [
      {
        title: "Collections",
        links: HOME_CATEGORIES.filter(([p]) => !EXAMS.some(([s]) => p === `/${s}`)).map(
          ([p, t]) => [t, p.slice(1)],
        ),
      },
    ],
  },
  {
    label: "Exams",
    path: "exams",
    sections: [{ title: "Prepare", links: EXAMS.map(([s, t]) => [t, s]) }],
  },
  {
    label: "Languages",
    path: "languages",
    sections: [{ title: "Directories", links: LANGUAGES.map(([s, t]) => [t, `ncert/${s}`]) }],
  },
  {
    label: "Resources",
    path: "resources",
    sections: [
      {
        title: "Browse",
        links: [
          ["All subjects", "subjects"],
          ...RESOURCE_TYPES.map(([s, t]) => [t, s]),
          ["My Study", "my-study"],
        ],
      },
    ],
  },
];

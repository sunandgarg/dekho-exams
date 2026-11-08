import { isPublicPath } from "./features";
export const TOPICS = [
  ["ChatGPT / Codex", "ai-tools/chatgpt-codex"],
  ["Claude / Claude Code", "ai-tools/claude-claude-code"],
  ["DSA", "dsa/dsa-tutorial-learn-data-structures-and-algorithms"],
  ["Practice Problems", "explore"],
  ["C", "c/c-programming-language"],
  ["C++", "cpp/c-plus-plus"],
  ["Java", "java/java"],
  ["Spring & Spring Boot", "spring/spring-boot"],
  ["Prompt Engineering", "prompt-engineering/prompt-engineering"],
  ["Python", "python/python-programming-language-tutorial"],
  ["JavaScript", "javascript/javascript-tutorial"],
  ["HTML", "html/html-tutorial"],
  ["Data Science", "data-science/data-science-for-beginners"],
  ["Machine Learning", "machine-learning/machine-learning-tutorial"],
  ["System Design", "system-design/system-design-tutorial"],
  ["Linux", "linux-unix/linux-tutorial"],
  ["DevOps", "devops/devops-tutorial"],
  ["How-to & Shortcuts", "guides/how-to-and-shortcuts"],
] as const;
const ALL_NAV_GROUPS = [
  {
    label: "Study",
    path: "study",
    sections: [
      {
        title: "Guided learning",
        links: [
          ["All classes", "study"],
          ["Class 1", "study/class-1"],
          ["Class 2", "study/class-2"],
          ["Class 3", "study/class-3"],
          ["Class 4", "study/class-4"],
          ["Class 5", "study/class-5"],
          ["Class 6", "study/class-6"],
          ["Class 7", "study/class-7"],
          ["Class 8", "study/class-8"],
          ["Class 9", "study/class-9"],
          ["Class 10", "study/class-10"],
          ["Class 11", "study/class-11"],
          ["Class 12", "study/class-12"],
        ],
      },
    ],
  },
  {
    label: "Courses",
    path: "courses",
    sections: [
      {
        title: "Browse courses",
        links: [
          ["All courses", "courses"],
          ["DSA & placements", "courses/category/dsa-placements"],
          ["Programming", "courses/category/programming-languages"],
          ["Web development", "courses/category/web-development"],
        ],
      },
      {
        title: "Your learning",
        links: [
          ["My course previews", "account/courses"],
          ["Learning paths", "learning-paths"],
          ["Learning progress", "account/progress"],
        ],
      },
    ],
  },
  {
    label: "Tutorials",
    path: "tutorials/programming-language-tutorials",
    sections: [
      {
        title: "Programming",
        links: TOPICS.filter(([label]) =>
          ["C", "C++", "Java", "Python", "JavaScript", "HTML"].includes(label),
        ),
      },
      {
        title: "Backend frameworks",
        links: [["Spring & Spring Boot", "spring/spring-boot"]],
      },
      {
        title: "Computer science",
        links: [
          ["DSA", "dsa/dsa-tutorial-learn-data-structures-and-algorithms"],
          ["DBMS", "dbms/dbms"],
          ["System design", "system-design/system-design-tutorial"],
          ["CS subjects", "tutorials/articles-on-computer-science-subjects-gq"],
        ],
      },
      {
        title: "Explore more",
        links: [
          ["ChatGPT / Codex", "ai-tools/chatgpt-codex"],
          ["Claude / Claude Code", "ai-tools/claude-claude-code"],
          ["Prompt Engineering", "prompt-engineering/prompt-engineering"],
          ["AI & data science", "tutorials/ai-ml-data-science"],
          ["Web technology", "web-tech/web-technology"],
          ["Databases", "sql/guide-to-databases"],
          ["Software & tools", "websites-apps/software-and-tools-a-to-z-list"],
          ["How-to & shortcuts", "guides/how-to-and-shortcuts"],
          ["School resources", "classes"],
          ["All tutorials", "tutorials/programming-language-tutorials"],
        ],
      },
    ],
  },
  {
    label: "Interview Prep",
    path: "interview-experiences/company-interview-corner",
    sections: [
      {
        title: "Prepare",
        links: [
          ["Interview corner", "interview-experiences/company-interview-corner"],
          ["Aptitude", "aptitude/aptitude-questions-and-answers"],
          ["Puzzles", "aptitude/puzzles"],
          ["Python interviews", "python/python-interview-questions"],
          ["System design", "system-design/system-design-tutorial"],
        ],
      },
      {
        title: "Build skills",
        links: [
          ["Guided DSA path", "batch/dsa-step-by-step-learning"],
          ["Knowledge quizzes", "quizzes"],
          ["Revision notes", "dbms/last-minute-notes-dbms"],
          ["Projects", "html/web-development-projects"],
        ],
      },
    ],
  },
  {
    label: "Practice",
    path: "explore",
    sections: [
      {
        title: "Solve & compete",
        links: [
          ["All problems", "explore"],
          ["Problem of the day", "problem-of-the-day"],
          ["Quizzes", "quizzes"],
          ["Events & contests", "events"],
          ["Hiring challenge", "events/rec/job-a-thon"],
        ],
      },
      {
        title: "Resources",
        links: [
          ["Videos", "videos"],
          ["Learning paths", "learning-paths"],
          ["Bookmarks", "account/bookmarks"],
        ],
      },
    ],
  },
  {
    label: "Jobs",
    path: "jobs",
    sections: [
      {
        title: "Careers",
        links: [
          ["Find jobs", "jobs"],
          ["Companies", "companies"],
          ["Saved jobs", "account/saved-jobs"],
          ["Applications", "account/applications"],
        ],
      },
      {
        title: "For organizations",
        links: [
          ["Hiring solutions", "gfg-hiring-solutions-for-recruiters"],
          ["Corporate training", "gfg-corporate-solution"],
          ["Contact us", "about/contact-us"],
        ],
      },
    ],
  },
] as const;

export const NAV_GROUPS = ALL_NAV_GROUPS.filter((g) =>
  ["Study", "Tutorials"].includes(g.label) && isPublicPath(g.path),
).map((g) => ({
  ...g,
  sections: g.sections.map((s) => ({
    ...s,
    links: s.links.filter(([, path]) => isPublicPath(path)),
  })),
}));

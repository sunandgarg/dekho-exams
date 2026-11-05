export const STUDY_TRACKS = [
  {
    title: "Python foundations",
    description: "Learn how names, collections, and functions behave before testing the basics.",
    subject: ["Python tutorial", "python/python-programming-language-tutorial"],
    lessons: [
      ["Variables and objects", "python/python-variables"],
      ["Lists and copies", "python/python-lists"],
      ["Functions and input", "python/python-functions"],
    ],
    quiz: ["Python foundations quiz", "quizzes/python-basics"],
  },
  {
    title: "Java foundations",
    description: "Set up Java, understand primitive values, and practice control flow.",
    subject: ["Java tutorial", "java/java"],
    lessons: [
      ["Set up the JDK", "java/setup"],
      ["Variables and types", "java/variables-types"],
      ["Conditions and loops", "java/control-flow"],
    ],
    quiz: ["Java basics quiz", "quizzes/java-basics"],
  },
  {
    title: "Spring fundamentals",
    description: "Work from application structure to web APIs and testing.",
    subject: ["Spring & Spring Boot", "spring/spring-boot"],
    lessons: [
      ["Spring Core", "spring/spring-core"],
      ["Web APIs", "spring/web-apis"],
      ["Testing", "spring/testing"],
    ],
    quiz: ["Spring Core quiz", "quizzes/spring-core"],
  },
] as const;

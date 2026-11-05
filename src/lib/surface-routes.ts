export type Surface =
  | "quiz-attempt"
  | "quiz-result"
  | "path"
  | "checkout"
  | "lesson"
  | "assignment"
  | "contest"
  | "leaderboard"
  | "application"
  | "account"
  | "auth"
  | "site-map";
export type ScreenPlan = {
  kind: "screen";
  screen: Surface;
  source?: string;
  title: string;
  view?: string;
  index?: number;
};
export function surfacePlan(path: string): ScreenPlan | null {
  if (path === "site-map") return { kind: "screen", screen: "site-map", title: "Page directory" };
  if (/^(login|signup|forgot-password)$/.test(path))
    return {
      kind: "screen",
      screen: "auth",
      title:
        path === "signup"
          ? "Create an account"
          : path === "forgot-password"
            ? "Reset your password"
            : "Sign in",
      view: path,
    };
  const account = path.match(
    /^(?:account|dashboard)(?:\/(courses|bookmarks|progress|notifications|settings|profile|saved-jobs|applications))?$/,
  );
  if (account)
    return {
      kind: "screen",
      screen: "account",
      title: "My learning",
      view: account[1] ?? "overview",
    };
  const quiz = path.match(/^(quizzes\/[a-z0-9-]+)\/(attempt|result)$/);
  if (quiz)
    return {
      kind: "screen",
      screen: quiz[2] === "result" ? "quiz-result" : "quiz-attempt",
      source: quiz[1]!,
      title: quiz[2] === "result" ? "Quiz result" : "Quiz attempt",
    };
  const checkout = path.match(/^checkout\/(.+)$/);
  if (checkout)
    return {
      kind: "screen",
      screen: "checkout",
      source: "courses/" + checkout[1],
      title: "Course checkout",
    };
  const learning = path.match(/^learn\/(.+)\/(lesson|assignment)\/(\d+)$/);
  if (learning)
    return {
      kind: "screen",
      screen: learning[2] === "lesson" ? "lesson" : "assignment",
      source: "courses/" + learning[1],
      index: Number(learning[3]),
      title: learning[2] === "lesson" ? "Course lesson" : "Course assignment",
    };
  const contest = path.match(/^((?:event|events)\/.+)\/(participate|leaderboard)$/);
  if (contest)
    return {
      kind: "screen",
      screen: contest[2] === "leaderboard" ? "leaderboard" : "contest",
      source: contest[1]!,
      title: contest[2] === "leaderboard" ? "Leaderboard" : "Contest workspace",
    };
  const job = path.match(/^(jobs\/.+)\/apply$/);
  if (job)
    return { kind: "screen", screen: "application", source: job[1]!, title: "Job application" };
  return null;
}
export const DIRECTORY_PATHS: Record<string, string | undefined> = {
  "tutorials/programming-language-tutorials": undefined,
  "tutorials/articles-on-computer-science-subjects-gq": "Computer Science",
  "tutorials/ai-ml-data-science": "AI & Data",
};

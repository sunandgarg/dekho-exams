/** Keep archived product code/content; change this flag when courses launch. */
export const FEATURES = { courses: false };
export const isPublicEntryType = (type: string) => FEATURES.courses || type !== "course";
export function isPublicPath(raw: unknown): boolean {
  if (typeof raw !== "string") return false;
  const path = raw
    .split(/[?#]/, 1)[0]!
    .replace(/^\/+|\/+$/g, "")
    .toLowerCase();
  return (
    FEATURES.courses ||
    !/^(?:courses|checkout|learn)(?:\/|$)|^(?:account|dashboard)\/courses(?:\/|$)/.test(path)
  );
}
/** Hide course offers in common overview copy without rewriting stored CMS content. */
export function publicCopy(text: string): string {
  if (FEATURES.courses) return text;
  return text
    .replace(
      /tutorials, practice problems, courses, videos/gi,
      "Tutorials, practice problems, videos",
    )
    .replace(
      /Practice to solve problems, and Courses to find structured programs\./g,
      "Practice to solve problems, and Learning paths to follow structured resources.",
    )
    .replace(
      /tutorials, practice, courses and your local preview/gi,
      "tutorials, practice and your local preview",
    )
    .replace(/Course and event notifications/g, "Event notifications");
}

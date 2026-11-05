const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || "playwright");
import fs from "node:fs/promises";
import path from "node:path";
const base = "http://127.0.0.1:3000";
const out = path.resolve(process.env.PREVIEW_OUTPUT_DIR || "../../outputs/preview-check");
await fs.mkdir(out, { recursive: true });
const entries = JSON.parse(await fs.readFile("src/data/fixtures.json", "utf8"));
const coursesEnabled = process.env.COURSES_ENABLED === "true";
const publicRoute = (route) =>
  coursesEnabled ||
  !/^\/(?:courses|checkout|learn)(?:\/|$)|^\/(?:account|dashboard)\/courses(?:\/|$)/.test(route);

const references = JSON.parse(
  await fs.readFile("../current-reference-route-check.json", "utf8"),
).references.filter((u) => !u.includes("robots.txt") && !u.includes("sitemap_index"));
const routes = new Set([
  "/",
  "/site-map",
  "/quizzes",
  "/learning-paths",
  "/companies",
  "/authors",
  "/login",
  "/signup",
  "/forgot-password",
  "/reset-password",
  "/auth",
  "/admin",
  ...[
    "",
    "courses",
    "bookmarks",
    "progress",
    "notifications",
    "settings",
    "profile",
    "saved-jobs",
    "applications",
  ].map((s) => "/account" + (s ? "/" + s : "")),
  ...references.map((u) => new URL(u).pathname + new URL(u).search),
  ...entries.map((e) => "/" + e.path),
]);
for (const e of entries) {
  if (e.type === "quiz") {
    routes.add("/" + e.path + "/attempt");
    routes.add("/" + e.path + "/result");
  }
  if (e.type === "course") {
    const slug = e.path.replace(/^courses\//, "");
    routes.add("/checkout/" + slug);
    routes.add("/learn/" + slug + "/lesson/1");
    routes.add("/learn/" + slug + "/assignment/1");
  }
  if (e.type === "event") {
    routes.add("/" + e.path + "/participate");
    routes.add("/" + e.path + "/leaderboard");
  }
  if (e.type === "job") routes.add("/" + e.path + "/apply");
}
const results = [];
const links = new Set();
const pending = [...routes];
async function check() {
  for (;;) {
    const route = pending.shift();
    if (!route) return;
    try {
      const response = await fetch(base + route);
      const body = await response.text();
      results.push({ route, status: response.status });
      for (const match of body.matchAll(/href="([^"]+)"/g)) {
        const href = match[1].replaceAll("&amp;", "&");
        if (
          href.startsWith("/") &&
          !href.startsWith("//") &&
          !href.startsWith("/@") &&
          !href.startsWith("/src/") &&
          !href.includes("/node_modules/") &&
          !href.includes(".css") &&
          !href.includes(".png") &&
          !href.startsWith("/assets/")
        )
          links.add(href.split("#")[0]);
      }
    } catch (error) {
      results.push({ route, error: String(error) });
    }
  }
}
await Promise.all(Array.from({ length: 4 }, check));
const extra = [...links].filter((l) => l && !routes.has(l));
pending.push(...extra);
await Promise.all(Array.from({ length: 4 }, check));
const missing = results.filter((r) => r.status !== (publicRoute(r.route) ? 200 : 404));
console.log("HTTP routes checked:", results.length, "failures:", JSON.stringify(missing));
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
const page = await context.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
async function visit(route) {
  await page.goto(base + route);
  await page.locator("h1").first().waitFor();
  if (route !== "/admin") await page.locator('[data-app-ready="true"]').waitFor();
}
const captures = [
  ["home", "/"],
  ["directory", "/site-map"],
  ["article", "/python/python-functions"],
  ["quiz", "/quizzes/python-basics/attempt"],
  ["dashboard", "/account"],
  ["lesson", "/learn/python-for-beginners/lesson/1"],
  ["practice", "/explore"],
  ["checkout", "/checkout/python-for-beginners"],
  ["subject", "/javascript/javascript-tutorial"],
  ["course", "/courses/python-for-beginners"],
  ["author", "/authors/aitrove-editorial"],
  ["company", "/companies/" + entries.find((e) => e.type === "company").path.split("/")[1]],
  ["video", "/" + entries.find((e) => e.type === "video").path],
  ["event", "/events/rec/job-a-thon"],
  ["path", "/batch/dsa-step-by-step-learning?tab=Resources"],
  ["auth", "/login"],
];
const overflow = [];
for (const width of [1440, 390]) {
  await page.setViewportSize({ width, height: 900 });
  for (const [name, route] of captures.filter(([, route]) => publicRoute(route))) {
    await visit(route);
    await page.screenshot({ path: path.join(out, `${name}-${width}.png`), fullPage: true });
    const sizes = await page.evaluate(() => ({
      body: document.documentElement.scrollWidth,
      viewport: innerWidth,
    }));
    if (sizes.body > sizes.viewport + 2) overflow.push({ name, width, ...sizes });
  }
}
await page.setViewportSize({ width: 1440, height: 900 });
await visit("/");
await page.getByText("Tutorials", { exact: true }).first().click();
await page.getByRole("link", { name: "All tutorials", exact: true }).first().click();
await page.waitForURL("**/tutorials/programming-language-tutorials");
await visit("/python/python-functions");
await page.getByRole("button", { name: "Save", exact: true }).click();
await visit("/account/bookmarks");
await page.locator("main").getByRole("link", { name: "Python Functions", exact: true }).waitFor();
await page.reload();
await page.getByRole("button", { name: "Remove", exact: true }).click();
await visit("/quizzes/python-basics/attempt");
await page.getByRole("radio").nth(1).check();
await page.getByRole("button", { name: "Next", exact: true }).click();
await page.getByRole("radio").nth(2).check();
await page.getByRole("button", { name: "Next", exact: true }).click();
await page.getByRole("radio").nth(3).check();
await page.getByRole("button", { name: "Finish & review", exact: true }).click();
await page.waitForURL("**/quizzes/python-basics/result");
await page.getByText("3 / 3", { exact: true }).waitFor();
await page.reload();
await page.getByText("3 / 3", { exact: true }).waitFor();
await page.getByRole("link", { name: "Try again", exact: true }).click();
await page.waitForURL("**/quizzes/python-basics/attempt");
if (await page.getByRole("radio").evaluateAll((rs) => rs.some((r) => r.checked)))
  throw new Error("Retry failed to clear answers");
if (coursesEnabled) {
  await visit("/learn/python-for-beginners/lesson/1");
  await page.getByRole("button", { name: "Mark lesson complete", exact: true }).click();
  await visit("/account/progress");
  await page.getByText("learn python for beginners lesson 1", { exact: true }).waitFor();
} else {
  await visit("/batch/dsa-step-by-step-learning");
  await page.getByRole("button", { name: "Mark complete", exact: true }).first().click();
  await visit("/account/progress");
  await page.getByText("dsa array data structure guide", { exact: true }).waitFor();
}
await visit("/");
await page.getByRole("button", { name: "Toggle theme" }).click();
await page.reload();
await page.locator("html.dark").waitFor();
await page.getByRole("button", { name: "Toggle theme" }).click();
await page.setViewportSize({ width: 390, height: 844 });
await visit("/");
await page.getByRole("button", { name: "Open navigation" }).click();
await page.getByRole("dialog").getByText("Tutorials", { exact: true }).click();
await page.getByRole("dialog").getByRole("link", { name: "All tutorials", exact: true }).click();
await page.waitForURL("**/tutorials/programming-language-tutorials");
await page.getByRole("dialog").waitFor({ state: "hidden" });
const notFound = await page.goto(base + "/this-resource-does-not-exist");
const invalidLesson = await page.goto(base + "/learn/python-for-beginners/lesson/999");
const report = {
  httpChecked: results.length,
  httpFailures: missing,
  overflow,
  consoleErrors: errors,
  unknownStatus: notFound.status(),
  invalidLessonStatus: invalidLesson.status(),
  flows: [
    "Desktop menu",
    "Mobile drawer",
    "Bookmark persistence and removal",
    "Quiz attempt / review / persisted result / fresh retry",
    coursesEnabled ? "Lesson progress" : "Learning-path progress",
    "Persisted theme",
  ],
  results,
};
await fs.writeFile(path.join(out, "report.json"), JSON.stringify(report, null, 2));
await context.close();
await browser.close();
console.log(JSON.stringify({ ...report, results: undefined }, null, 2));
if (
  missing.length ||
  overflow.length ||
  errors.length ||
  notFound.status() !== 404 ||
  invalidLesson.status() !== 404
)
  process.exitCode = 1;

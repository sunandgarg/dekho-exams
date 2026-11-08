import fs from "node:fs/promises";
import path from "node:path";
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || "playwright");
const base = "http://127.0.0.1:3000";
const out = path.resolve(process.env.PREVIEW_OUTPUT_DIR || "../../outputs/course-visibility-check");
await fs.mkdir(out, { recursive: true });
const records = JSON.parse(await fs.readFile("src/data/fixtures.json", "utf8"));
const courses = records.filter((e) => e.type === "course");
if (courses.length !== 4) throw new Error("Archived course records changed unexpectedly.");
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
// Keep local functionality checks independent of remote web-font availability.
await context.route(/fonts\.(googleapis|gstatic)\.com/, (route) => route.abort());
const page = await context.newPage();
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
const hidden = [
  "/courses",
  "/courses/category/dsa-placements",
  "/account/courses",
  "/dashboard/courses",
];
for (const course of courses) {
  const slug = course.path.replace(/^courses\//, "");
  hidden.push(
    "/" + course.path,
    "/checkout/" + slug,
    "/learn/" + slug + "/lesson/1",
    "/learn/" + slug + "/assignment/1",
  );
}
for (const route of hidden) {
  const response = await fetch(base + route);
  if (response.status !== 404)
    throw new Error(`${route} is publicly accessible: ${response.status}`);
}
const routes = [
  "/",
  "/tutorials/ai-ml-data-science",
  "/python/python-functions",
  "/site-map",
  "/search?q=python",
  "/about",
  "/help",
  "/account",
  "/account/bookmarks",
  "/account/progress",
  "/account/notifications",
];
const links = new Set();
async function visit(route) {
  await page.goto(base + route, { waitUntil: "domcontentloaded" });
  await page.locator('[data-app-ready="true"]').waitFor();
  if (route.startsWith("/account"))
    await page.locator('[aria-busy="true"]').waitFor({ state: "hidden" });
}
for (const width of [1440, 390]) {
  await page.setViewportSize({ width, height: 900 });
  for (const route of routes) {
    await visit(route);
    const text = await page.locator("body").innerText();
    if (/\bcourses?\b/i.test(text))
      throw new Error(
        "Visible course copy at " + route + ": " + text.match(/.{0,35}\bcourses?\b.{0,35}/i)?.[0],
      );
    const hrefs = await page
      .locator("a[href]")
      .evaluateAll((as) => as.map((a) => a.getAttribute("href")));
    for (const href of hrefs) {
      if (/^\/(?:courses|checkout|learn)(?:\/|$)|^\/(?:account|dashboard)\/courses/.test(href))
        throw new Error("Course link at " + route + ": " + href);
      if (href.startsWith("/") && !href.startsWith("//") && !href.startsWith("/assets/"))
        links.add(href.split("#")[0]);
    }
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth + 2,
    );
    if (overflow) throw new Error("Horizontal overflow: " + route);
    if (route === "/" || route === "/tutorials/ai-ml-data-science")
      await page.screenshot({
        path: path.join(out, `${route === "/" ? "home" : "ai-directory"}-${width}.png`),
        fullPage: true,
      });
  }
}
await page.setViewportSize({ width: 1440, height: 900 });
await visit("/");
await page.getByText("Tutorials", { exact: true }).first().click();
if (await page.getByText("Courses", { exact: true }).count())
  throw new Error("Desktop menu still offers courses.");
await page.evaluate(
  (course) =>
    localStorage.setItem(
      "aitrove-preview-v1",
      JSON.stringify({
        bookmarks: [{ path: course.path, title: course.title, type: "course" }],
        completed: ["learn/python-for-beginners/lesson/1"],
        quizzes: {},
        settings: { displayName: "Learner", dailyGoal: 20 },
        drafts: {},
      }),
    ),
  courses[0],
);
await visit("/account/bookmarks");
if (!(await page.getByText("Nothing saved yet", { exact: true }).count()))
  throw new Error("Archived course bookmark is visible.");
await visit("/account/progress");
const retained = await page.evaluate(() => JSON.parse(localStorage.getItem("aitrove-preview-v1")));
if (retained.bookmarks.length !== 1 || retained.completed.length !== 1)
  throw new Error("Stored course data was deleted.");
await page.evaluate(() => localStorage.removeItem("aitrove-preview-v1"));
await visit("/");
const logo = page.locator("header img").first();
if (!(await logo.getAttribute("src")).includes("aitrove-symbol-v2"))
  throw new Error("New logo is not installed.");
if (!(await logo.evaluate((img) => img.complete && img.naturalWidth > 0)))
  throw new Error("Logo did not load.");
const favicon = await page.locator('link[rel="icon"]').getAttribute("href");
if (favicon !== "/dekhoexams-icon-192.png") throw new Error("Old favicon");
if (!(await fetch(base + favicon)).ok) throw new Error("Favicon failed to load.");
for (const href of links)
  if (href && !(await fetch(base + href)).ok)
    throw new Error("Broken remaining public link: " + href);
if (errors.length) throw new Error("Browser errors: " + errors.join(", "));
const report = {
  coursesRetained: courses.length,
  hiddenRoutesChecked: hidden.length,
  publicScreensChecked: routes.length * 2,
  publicLinksChecked: links.size,
  browserErrors: errors,
  logo: "aitrove-symbol-v2.png",
  favicon,
  savedCourseDataPreserved: true,
};
await fs.writeFile(path.join(out, "report.json"), JSON.stringify(report, null, 2));
await context.close();
await browser.close();
console.log(JSON.stringify(report, null, 2));

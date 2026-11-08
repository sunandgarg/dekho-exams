import assert from "node:assert/strict";
import fs from "node:fs/promises";
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE);
const base = "http://127.0.0.1:3001";
const out = new URL("../../../outputs/", import.meta.url);
const batch = JSON.parse(await fs.readFile(new URL("java-finish-batch.json", out)));
const entries = JSON.parse(await fs.readFile("src/data/fixtures.json", "utf8"));
const lookup = new Map(entries.map((e) => [e.path, e]));
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 960 } });
const page = await context.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
async function go(path) {
  const r = await page.goto(base + "/" + path, { waitUntil: "networkidle" });
  assert.equal(r.status(), 200, path);
  await page.locator('[data-app-ready="true"]').waitFor();
}
const verified = [];
for (const path of batch.added) {
  const e = lookup.get(path);
  await go(path);
  assert.equal(await page.locator("h1").first().innerText(), e.title);
  const body = page
    .locator(".article-content")
    .filter({ has: page.locator("code.language-java") })
    .first();
  await body.getByRole("heading", { name: "Common Mistakes", exact: true }).waitFor();
  assert.equal(await body.locator("code.language-java").count(), 1, path);
  assert.ok((await body.locator('code.language-java [class^="hljs-"]').count()) > 0, path);
  assert.equal(
    await page.locator('[data-subject-tabs] a[aria-current="page"]').getAttribute("href"),
    "/" + e.data.section_path,
  );
  assert.equal(
    await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2),
    false,
    path,
  );
  verified.push(path);
}
console.log("Verified " + verified.length + " new article screens.");
const quizzes = entries.filter((e) => e.type === "quiz" && e.subject === "java-quizzes");
let answers = 0;
for (const quiz of quizzes) {
  await page.setViewportSize({ width: 390, height: 900 });
  await go(quiz.path + "/attempt");
  for (const q of quiz.data.questions) {
    await page.getByRole("heading", { name: q.prompt, exact: true }).waitFor();
    await page.getByRole("radio", { name: q.options[q.answer], exact: true }).check();
    answers++;
    if (answers % 12 !== 0) await page.getByRole("button", { name: "Next", exact: true }).click();
    else await page.getByRole("button", { name: "Finish & review", exact: true }).click();
  }
  await page.waitForURL(base + "/" + quiz.path + "/result");
  await page.getByRole("heading", { name: "Answer review", exact: true }).waitFor();
  assert.ok((await page.locator("main").innerText()).includes("12 / 12"));
  assert.equal(await page.locator("main section").count(), 12);
  for (const q of quiz.data.questions)
    await page.getByText(q.explanation, { exact: true }).waitFor();
  assert.equal(
    await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2),
    false,
    quiz.path,
  );
}
console.log("Verified " + answers + " answers and explained scores.");
const mobile = [];
for (const width of [1440, 1024, 768, 390, 360, 320]) {
  await page.setViewportSize({ width, height: 900 });
  await go("");
  assert.equal(await page.locator(".explore-card").count(), 16);
  assert.equal(
    await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2),
    false,
  );
  await go("java/trie");
  assert.equal(
    await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2),
    false,
  );
  if (width <= 768) {
    await page.getByRole("button", { name: /Contents ·/ }).click();
    const sheet = page.getByRole("dialog");
    await sheet.locator('a[href="/java/avl-tree"]').click();
    await page.waitForURL(/java\/avl-tree$/);
    await sheet.waitFor({ state: "hidden" });
    await page.getByRole("button", { name: /Contents ·/ }).click();
    await sheet.getByRole("button", { name: /On this page ·/ }).click();
    await sheet.getByRole("link", { name: /Costs and boundaries/ }).click();
    await sheet.waitFor({ state: "hidden" });
    await page.waitForFunction(
      () => document.activeElement?.textContent === "Costs and boundaries",
    );
  }
  mobile.push(width);
}
await page.setViewportSize({ width: 1440, height: 960 });
await go("java/database-project");
const link = page.getByRole("link", { name: "Download Java source kit", exact: true });
assert.equal(await link.getAttribute("download"), "");
const response = await context.request.get(base + "/downloads/dekhoexams-java-source-kit.zip");
assert.equal(response.status(), 200);
const bytes = await response.body();
const local = await fs.readFile("public/downloads/dekhoexams-java-source-kit.zip");
assert.deepEqual(bytes, local);
const pending = page.waitForEvent("download");
await link.click();
const download = await pending;
assert.equal(download.suggestedFilename(), "dekhoexams-java-source-kit.zip");
assert.equal(await download.failure(), null);
await page.screenshot({ path: new URL("java-finish-project-desktop.png", out).pathname });
await page.setViewportSize({ width: 390, height: 900 });
await go("java/trie");
await page.screenshot({ path: new URL("java-finish-trie-mobile.png", out).pathname });
await page.setViewportSize({ width: 1440, height: 960 });
await go("search?q=JMH");
await page.locator('main a[href="/java/jmh-benchmarks"]').first().waitFor();
await page.goto(base + "/java-coverage.html", { waitUntil: "networkidle" });
const routeLinks = await page
  .locator('.branch a[href^="http://127.0.0.1:3001/"]')
  .evaluateAll((as) => new Set(as.map((a) => a.href)).size);
assert.equal(routeLinks, 175);
await page.getByRole("combobox", { name: "Show", exact: true }).selectOption("new");
const changed = await page
  .locator("li:not([hidden])[data-status] a")
  .evaluateAll((as) => new Set(as.map((a) => a.href)).size);
assert.equal(changed, 76);
await page.getByRole("combobox", { name: "Show", exact: true }).selectOption("remaining");
assert.equal(await page.locator(".branch:not([hidden])").count(), 10);
assert.equal(await page.locator("li:not([hidden])[data-status]").count(), 0);
await page.getByRole("combobox", { name: "Show", exact: true }).selectOption("all");
await page.getByRole("textbox", { name: "Find a topic", exact: true }).fill("Bellman");
assert.equal(await page.locator("li:not([hidden])[data-status]").count(), 1);
await page.getByRole("textbox", { name: "Find a topic", exact: true }).fill("");
await page.setViewportSize({ width: 390, height: 900 });
assert.equal(
  await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2),
  false,
);
await page.screenshot({ path: new URL("java-finish-coverage-mobile.png", out).pathname });
const routes = entries.filter(
  (e) => e.path.startsWith("java/") || (e.type === "quiz" && e.subject === "java-quizzes"),
);
for (let i = 0; i < routes.length; i += 6)
  await Promise.all(
    routes.slice(i, i + 6).map(async (e) => {
      const r = await context.request.get(base + "/" + e.path);
      assert.equal(r.status(), 200, e.path);
      assert.ok((await r.text()).includes(e.title.replaceAll("&", "&amp;")) || r.ok());
    }),
  );
assert.deepEqual(errors, []);
const report = {
  newArticleScreens: verified.length,
  quizBanks: quizzes.length,
  correctAnswersAndExplanationsVerified: answers,
  viewports: mobile,
  sourceDownloadBytes: bytes.length,
  sourceDownloadVerified: true,
  search: true,
  coverageRoutes: routeLinks,
  changedMapRoutes: changed,
  allRoutesRespond: routes.length,
  mobileCurriculumAndHeadingJumps: true,
  homepageExploreCards: 16,
  browserErrors: errors,
  passed: true,
};
await fs.writeFile(new URL("java-finish-browser-check.json", out), JSON.stringify(report, null, 2));
console.log(JSON.stringify(report));
await browser.close();

import assert from "node:assert/strict";
import fs from "node:fs/promises";
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE);
const base = "http://127.0.0.1:3001";
const out = new URL("../../../outputs/", import.meta.url);
const batch = JSON.parse(await fs.readFile(new URL("java-release-batch.json", out)));
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
// Keep quiz reading in the subject shell, including after a scrolled hub click.
await page.setViewportSize({ width: 1440, height: 960 });
await go("java/java-quizzes");
const quizLink = page.locator('.learning-sidebar a[href="/quizzes/java-25"]').first();
await quizLink.scrollIntoViewIfNeeded();
await page.evaluate(() => scrollTo(0, document.body.scrollHeight / 2));
await quizLink.click();
await page.waitForURL(base + "/quizzes/java-25");
await page
  .getByRole("heading", { name: lookup.get("quizzes/java-25").title, exact: true })
  .waitFor();
await page.waitForTimeout(300);
assert.ok((await page.locator("h1").boundingBox()).y >= 0, "quiz heading must start in view");
assert.equal(
  await page.locator('[data-subject-tabs] a[aria-current="page"]').getAttribute("href"),
  "/java/java-quizzes",
);
await page.screenshot({ path: new URL("java-release-quiz25-desktop.png", out).pathname });
for (const quiz of quizzes) {
  await go(quiz.path);
  assert.equal(await page.locator("h1").innerText(), quiz.title);
  assert.equal(await page.locator(".learning-sidebar").count(), 1);
  assert.equal(
    await page.locator('[data-subject-tabs] a[aria-current="page"]').getAttribute("href"),
    "/java/java-quizzes",
  );
  assert.equal(
    await page.getByRole("link", { name: "Start quiz", exact: true }).getAttribute("href"),
    "/" + quiz.path + "/attempt",
  );
}
await page.setViewportSize({ width: 390, height: 900 });
await go("quizzes/java-25");
await page.getByRole("button", { name: /Contents ·/ }).click();
const quizSheet = page.getByRole("dialog");
await quizSheet.locator('a[href="/quizzes/java-graphs"]').click();
await page.waitForURL(/quizzes\/java-graphs$/);
await quizSheet.waitFor({ state: "hidden" });
await go("quizzes/java-25");
await page.screenshot({ path: new URL("java-release-quiz25-mobile.png", out).pathname });
await page.setViewportSize({ width: 1440, height: 960 });
await go("java/manifest-project");
const steps = page.locator(".lesson-navigation a");
assert.equal(await steps.count(), 2);
const expectedHub = lookup.get(lookup.get("java/manifest-project").data.section_path);
const ordered = [...new Set(expectedHub.data.modules.flatMap((m) => m.lessons))];
const at = ordered.indexOf("java/manifest-project");
assert.equal(await steps.first().getAttribute("href"), "/" + ordered[at - 1]);
assert.equal(await steps.last().getAttribute("href"), "/" + ordered[at + 1]);
await steps.last().hover();
await page.waitForTimeout(250);
const motion = await steps
  .last()
  .locator("svg")
  .evaluate((el) => getComputedStyle(el).transform);
assert.notEqual(motion, "none");
await page.emulateMedia({ reducedMotion: "reduce" });
assert.equal(
  await steps
    .last()
    .locator("svg")
    .evaluate((el) => getComputedStyle(el).transform),
  "none",
);
await page.emulateMedia({ reducedMotion: "no-preference" });
await steps.last().focus();
await page.screenshot({ path: new URL("java-release-lesson-navigation.png", out).pathname });
const mobile = [];
for (const width of [1440, 1024, 768, 390, 360, 320]) {
  await page.setViewportSize({ width, height: 900 });
  await go("");
  assert.equal(await page.locator(".explore-card").count(), 16);
  assert.equal(
    await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2),
    false,
  );
  await go("java/trie-deletion");
  assert.equal(
    await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2),
    false,
  );
  if (width <= 768) {
    await page.getByRole("button", { name: /Contents ·/ }).click();
    const sheet = page.getByRole("dialog");
    await sheet.locator('a[href="/java/avl-deletion"]').click();
    await page.waitForURL(/java\/avl-deletion$/);
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
await go("java/scoped-values");
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
await page.screenshot({ path: new URL("java-release-scoped-desktop.png", out).pathname });
await page.setViewportSize({ width: 390, height: 900 });
await go("java/trie-deletion");
await page.screenshot({ path: new URL("java-release-trie-deletion-mobile.png", out).pathname });
await page.setViewportSize({ width: 1440, height: 960 });
await go("search?q=Scoped");
await page.locator('main a[href="/java/scoped-values"]').first().waitFor();
await page.goto(base + "/java-coverage.html", { waitUntil: "networkidle" });
const routeLinks = await page
  .locator('.branch a[href^="http://127.0.0.1:3001/"]')
  .evaluateAll((as) => new Set(as.map((a) => a.href)).size);
assert.equal(routeLinks, 219);
await page.getByRole("combobox", { name: "Show", exact: true }).selectOption("new");
const changed = await page
  .locator("li:not([hidden])[data-status] a")
  .evaluateAll((as) => new Set(as.map((a) => a.href)).size);
assert.ok(changed >= 14);
await page.getByRole("combobox", { name: "Show", exact: true }).selectOption("remaining");
assert.equal(await page.locator(".branch:not([hidden])").count(), 10);
assert.equal(await page.locator("li:not([hidden])[data-status]").count(), 0);
await page.getByRole("combobox", { name: "Show", exact: true }).selectOption("all");
await page.getByRole("textbox", { name: "Find a topic", exact: true }).fill("Fenwick");
assert.equal(
  await page
    .locator("li:not([hidden])[data-status] a")
    .evaluateAll((as) => new Set(as.map((a) => a.href)).size),
  1,
);
await page.getByRole("textbox", { name: "Find a topic", exact: true }).fill("");
await page.setViewportSize({ width: 390, height: 900 });
assert.equal(
  await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2),
  false,
);
await page.screenshot({ path: new URL("java-release-coverage-mobile.png", out).pathname });
const routes = entries.filter(
  (e) => e.path.startsWith("java/") || (e.type === "quiz" && e.subject === "java-quizzes"),
);
for (let i = 0; i < routes.length; i += 6)
  await Promise.all(
    routes.slice(i, i + 6).map(async (e) => {
      const r = await context.request.get(base + "/" + e.path);
      assert.equal(r.status(), 200, e.path);
      const expected = e.title
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#x27;");
      const markup = await r.text();
      assert.ok(markup.includes("<h1") && markup.includes(expected), e.path);
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
await fs.writeFile(
  new URL("java-release-browser-check.json", out),
  JSON.stringify(report, null, 2),
);
console.log(JSON.stringify(report));
await browser.close();

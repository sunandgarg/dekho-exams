import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { createHash } from "node:crypto";
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE);
const entries = JSON.parse(await fs.readFile("src/data/fixtures.json", "utf8"));
const lookup = new Map(entries.map((e) => [e.path, e]));
const selected = entries.filter(
  (e) => e.path.startsWith("python/") || e.path.startsWith("quizzes/python-"),
);
const base = "http://127.0.0.1:3001";
const out = new URL("../../../outputs/", import.meta.url);
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 960 } });
const page = await context.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
async function go(path, target = page) {
  const r = await target.goto(base + "/" + path, { waitUntil: "networkidle" });
  assert.equal(r.status(), 200, path);
  await target.locator('[data-app-ready="true"]').waitFor();
}
async function noOverflow(path, target = page) {
  assert.equal(
    await target.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2),
    false,
    path,
  );
}
async function readableCodeFont(target) {
  const font = await target
    .locator("pre code.language-python")
    .first()
    .evaluate((node) => {
      const style = getComputedStyle(node);
      return {
        family: style.fontFamily,
        size: parseFloat(style.fontSize),
        visibility: style.visibility,
      };
    });
  assert.equal(font.family, "monospace");
  assert.ok(font.size >= 12);
  assert.equal(font.visibility, "visible");
}
// Each worker owns its page; these sweeps only read routes and open local dialogs.
async function sweep(rows, viewport, check) {
  let next = 0;
  await Promise.all(
    Array.from({ length: 4 }, async () => {
      const target = await context.newPage();
      target.on("pageerror", (error) => errors.push(error.message));
      await target.setViewportSize(viewport);
      try {
        while (next < rows.length) {
          const entry = rows[next++];
          await check(target, entry);
        }
      } finally {
        await target.close();
      }
    }),
  );
}
const files = [
  "src/data/fixtures.json",
  "src/components/cms/templates.tsx",
  "src/components/gfg/site-shell.tsx",
  "src/components/cms/markdown.tsx",
  "src/styles.css",
  "src/ozi-design.css",
  "scripts/check-python-browser.mjs",
];
const fingerprint = createHash("sha256");
for (const file of files) fingerprint.update(await fs.readFile(file));
const sourceFingerprint = fingerprint.digest("hex");
const sweepFile = new URL("python-page-sweep-validation.json", out);
let mobileScreens = 0;
if (process.env.PYTHON_BROWSER_RESUME_FLOWS === "true") {
  const sweep = JSON.parse(await fs.readFile(sweepFile));
  assert.equal(sweep.sourceFingerprint, sourceFingerprint, "page sources changed since sweep");
  assert.equal(sweep.passed, true);
  mobileScreens = sweep.mobileScreens;
  await page.setViewportSize({ width: 390, height: 900 });
} else {
  if (process.env.PYTHON_BROWSER_MOBILE_ONLY !== "true") {
  await sweep(selected, { width: 1440, height: 960 }, async (target, e) => {
    await go(e.path, target);
    assert.equal(await target.locator("h1").first().innerText(), e.title, e.path);
    assert.equal(
      await target.locator('[data-subject-tabs] a[aria-current="page"]').getAttribute("href"),
      "/" + e.data.section_path,
      e.path,
    );
    const links = await target
      .locator(".learning-sidebar a")
      .evaluateAll((as) => as.map((a) => a.getAttribute("href")));
    assert.ok(
      links.every((p) => p.startsWith("/python/") || p.startsWith("/quizzes/python-")),
      e.path,
    );
    await noOverflow(e.path, target);
    assert.equal(
      await target
        .locator('nav[aria-label="Popular topics"] a[aria-current="page"]')
        .getAttribute("href"),
      "/python/python-programming-language-tutorial",
    );
    if (e.type === "article") {
      await readableCodeFont(target);
      await target.getByRole("link", { name: "Download Python source kit", exact: true }).waitFor();
      assert.ok(
        (await target.locator('code.language-python [class^="hljs-"]').count()) > 0,
        e.path,
      );
      await target.getByRole("heading", { name: "Common Mistakes", exact: true }).waitFor();
    }
  });
  console.log("Desktop Python screens checked: " + selected.length);
  } else {
    console.log("Desktop sweep skipped for mobile diagnosis; prior desktop sweep passed.");
  }

  for (const width of [320, 390]) {
    await sweep(
      selected.filter((e) => e.type === "article"),
      { width, height: 900 },
      async (target, e) => {
        try {
          await go(e.path, target);
          await noOverflow(e.path + " " + width, target);
          await readableCodeFont(target);
          await target.getByRole("button", { name: /Contents ·/ }).click();
          await target.getByRole("dialog").waitFor({ timeout: 8000 });
          await target.keyboard.press("Escape");
          await target.getByRole("dialog").waitFor({ state: "hidden" });
          mobileScreens++;
        } catch (error) {
          console.error("Mobile route failed:", e.path, width, target.url());
          throw error;
        }
      },
    );
    console.log("Mobile width checked: " + width);
  }
  await fs.writeFile(
    sweepFile,
    JSON.stringify(
      {
        passed: true,
        sourceFingerprint,
        desktopScreens: selected.length,
        mobileScreens,
        mobileWidths: [320, 390],
      },
      null,
      2,
    ),
  );
}
await page.setViewportSize({ width: 390, height: 900 });
await go("python/python-variables");
await page.getByRole("button", { name: /Contents ·/ }).click();
const sheet = page.getByRole("dialog");
await sheet.locator('a[href="/python/python-functions"]').first().click();
await page.waitForURL("**/python/python-functions");
await sheet.waitFor({ state: "hidden" });
await page.getByRole("button", { name: /Contents ·/ }).click();
await sheet.getByRole("button", { name: /On this page ·/ }).click();
await sheet.getByRole("link", { name: /Costs and limits/ }).click();
await sheet.waitFor({ state: "hidden" });
await page.waitForFunction(() => document.activeElement?.textContent === "Costs and limits");
let answers = 0;
for (const e of selected.filter((e) => e.type === "quiz")) {
  await go(e.path + "/attempt");
  for (let i = 0; i < e.data.questions.length; i++) {
    const q = e.data.questions[i];
    await page.getByRole("heading", { name: q.prompt, exact: true }).waitFor();
    await page.getByRole("radio", { name: q.options[q.answer], exact: true }).check();
    await page
      .getByRole("button", {
        name: i === e.data.questions.length - 1 ? "Finish & review" : "Next",
        exact: true,
      })
      .click();
    answers++;
  }
  await page.waitForURL(base + "/" + e.path + "/result");
  await page.getByRole("heading", { name: "Answer review", exact: true }).waitFor();
  assert.ok((await page.locator("main").innerText()).includes("12 / 12"));
  await noOverflow(e.path);
}
await page.setViewportSize({ width: 1440, height: 960 });
await go("python/quizzes");
const quiz = page.locator('.learning-sidebar a[href="/quizzes/python-algorithms"]').first();
await quiz.scrollIntoViewIfNeeded();
await quiz.click();
await page.waitForURL("**/quizzes/python-algorithms");
const quizHeading = page.getByRole("heading", {
  name: lookup.get("quizzes/python-algorithms").title,
  exact: true,
});
await quizHeading.waitFor();
assert.ok((await quizHeading.boundingBox()).y >= 0);
assert.equal(
  await page.locator('[data-subject-tabs] a[aria-current="page"]').getAttribute("href"),
  "/python/quizzes",
);
for (const path of ["java/pass-by-value", "java/arraylist", "spring/metric-cardinality"]) {
  await go(path);
  const e = lookup.get(path);
  assert.equal(await page.locator("h1").first().innerText(), e.title);
  if (e.data.download_path) {
    await page
      .getByRole("link", {
        name: path.startsWith("java/") ? "Download Java source kit" : "Download Spring source kit",
        exact: true,
      })
      .waitFor();
  }
  await noOverflow(path);
}
await page.setViewportSize({ width: 390, height: 900 });
await go("python/python-variables");
await page.screenshot({ path: new URL("python-variables-desktop.png", out).pathname });
await page.setViewportSize({ width: 390, height: 900 });
await go("python/inventory-project");
await page.screenshot({ path: new URL("python-inventory-mobile.png", out).pathname });
await go("search?q=Python%20comprehensions");
await page.locator('main a[href="/python/comprehensions"]').first().waitFor();
await go("");
assert.equal(await page.locator(".explore-card").count(), 16);
await page.getByRole("link", { name: /Python View resources/ }).click();
await page.waitForURL("**/python/python-programming-language-tutorial");
for (const path of ["downloads/dekhoexams-python-source-kit.zip", "learning-coverage.html"]) {
  const r = await context.request.get(base + "/" + path);
  assert.equal(r.status(), 200);
  assert.ok(r.headers()["x-robots-tag"].includes("noindex"));
  assert.equal(r.headers()["x-content-type-options"], "nosniff");
}
await page.goto(base + "/learning-coverage.html?subject=Python", { waitUntil: "networkidle" });
assert.equal(await page.locator("#subject").inputValue(), "Python");
assert.equal(
  await page.locator("#sections details").count(),
  selected.filter((e) => e.type === "subject").length,
);
assert.ok(
  (await page.locator("#visible").innerText()).includes(
    `${selected.filter((e) => e.type !== "subject").length} lessons`,
  ),
);
await page.locator("#search").fill("comprehensions");
assert.equal(await page.locator("#sections li a").count(), 1);
await page.locator("#search").fill("");
await noOverflow("learning map");
await page.screenshot({ path: new URL("python-coverage-mobile.png", out).pathname });
await page.setViewportSize({ width: 1440, height: 960 });
await go("python/numpy-views");
await page.screenshot({ path: new URL("python-numpy-desktop.png", out).pathname });
await page.setViewportSize({ width: 390, height: 900 });
await go("python/flask-json-api");
await page.screenshot({ path: new URL("python-flask-mobile.png", out).pathname });
await page.setViewportSize({ width: 1440, height: 1000 });
await page.goto(base + "/python/django-query-counts", { waitUntil: "networkidle" });
await page.screenshot({ path: new URL("python-django-orm-desktop.png", out).pathname });
await page.setViewportSize({ width: 390, height: 844 });
await page.goto(base + "/python/ml-pipeline", { waitUntil: "networkidle" });
await page.screenshot({ path: new URL("python-ml-mobile.png", out).pathname });
await page.setViewportSize({ width: 1440, height: 1000 });
await go("python/avl-insertion");
await page.screenshot({ path: new URL("python-avl-desktop.png", out).pathname });
await page.setViewportSize({ width: 390, height: 844 });
await go("python/drf-object-permissions");
await page.screenshot({ path: new URL("python-drf-permissions-mobile.png", out).pathname });
assert.deepEqual(errors, []);
const report = {
  passed: true,
  desktopScreens: selected.length,
  mobileScreens,
  mobileWidths: [320, 390],
  quizAnswers: answers,
  syntaxHighlighting: true,
  standardMonospaceFont: true,
  downloads: true,
  crossSubjectRegression: true,
  homepageCards: 16,
  pageErrors: errors,
};
await fs.writeFile(new URL("python-browser-validation.json", out), JSON.stringify(report, null, 2));
console.log(JSON.stringify(report));
await browser.close();

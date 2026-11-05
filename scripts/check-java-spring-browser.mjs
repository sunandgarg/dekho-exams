import assert from "node:assert/strict";
import fs from "node:fs/promises";
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE);
const entries = JSON.parse(await fs.readFile("src/data/fixtures.json", "utf8"));
const lookup = new Map(entries.map((e) => [e.path, e]));
const out = new URL("../../../outputs/", import.meta.url);
const java = JSON.parse(await fs.readFile(new URL("java-spring-third-additions.json", out))).java;
const spring = entries.filter(
  (e) => e.path.startsWith("spring/") || e.path.startsWith("quizzes/spring-"),
);
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 960 } });
const page = await context.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
async function go(path) {
  const response = await page.goto("http://127.0.0.1:3001/" + path, { waitUntil: "networkidle" });
  assert.equal(response.status(), 200, path);
  await page.locator('[data-app-ready="true"]').waitFor();
  return response;
}
let checked = 0;
for (const path of [...java, ...spring.map((e) => e.path)]) {
  await go(path);
  assert.equal(await page.locator("h1").first().innerText(), lookup.get(path).title, path);
  assert.equal(
    await page.locator('[data-subject-tabs] a[aria-current="page"]').getAttribute("href"),
    "/" + lookup.get(path).data.section_path,
    path,
  );
  assert.equal(
    await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2),
    false,
    path,
  );
  if (path.startsWith("spring/")) {
    const sidebarLinks = await page
      .locator(".learning-sidebar a")
      .evaluateAll((links) => links.map((a) => a.getAttribute("href")));
    assert.ok(
      sidebarLinks.every((link) => !link.startsWith("/java/")),
      path,
    );
    assert.equal(
      await page
        .locator('nav[aria-label="Popular topics"] a[aria-current="page"]')
        .getAttribute("href"),
      "/spring/spring-boot",
    );
  }
  if (lookup.get(path).type === "article")
    await page
      .getByRole("link", {
        name: path.startsWith("spring/")
          ? "Download Spring source kit"
          : "Download Java source kit",
        exact: true,
      })
      .waitFor();
  checked++;
}
console.log("Checked " + checked + " article, hub and quiz screens.");
for (const width of [320, 390, 768]) {
  await page.setViewportSize({ width, height: 900 });
  for (const path of [
    "spring/spring-boot",
    "spring/application-context",
    "spring/security-filter-chain",
    "spring/transactions",
    "quizzes/spring-core",
    "java/segment-tree",
  ]) {
    await go(path);
    assert.equal(
      await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2),
      false,
      path + " " + width,
    );
    await page
      .getByRole("button", { name: /Contents/ })
      .first()
      .click();
    const dialog = page.getByRole("dialog");
    await dialog.waitFor();
    assert.ok(
      (await dialog.innerText()).includes(lookup.get(path).title) ||
        (await dialog.innerText()).includes("Contents"),
    );
    await page.keyboard.press("Escape");
    await dialog.waitFor({ state: "hidden" });
  }
}
await page.setViewportSize({ width: 390, height: 900 });
let answers = 0;
for (const quiz of spring.filter((e) => e.type === "quiz")) {
  await go(quiz.path + "/attempt");
  for (let index = 0; index < quiz.data.questions.length; index++) {
    const q = quiz.data.questions[index];
    await page.getByRole("heading", { name: q.prompt, exact: true }).waitFor();
    await page.getByRole("radio", { name: q.options[q.answer], exact: true }).check();
    await page
      .getByRole("button", {
        name: index === quiz.data.questions.length - 1 ? "Finish & review" : "Next",
        exact: true,
      })
      .click();
    answers++;
  }
  await page.waitForURL("http://127.0.0.1:3001/" + quiz.path + "/result");
  await page.getByRole("heading", { name: "Answer review", exact: true }).waitFor();
  assert.ok((await page.locator("main").innerText()).includes("12 / 12"));
}
console.log("Checked " + answers + " quiz answers.");
await page.setViewportSize({ width: 1440, height: 960 });
await go("spring/spring-core");
await page.locator('.learning-sidebar a[href="/spring/application-context"]').first().click();
await page.waitForURL("**/spring/application-context");
await page
  .getByRole("heading", { name: lookup.get("spring/application-context").title, exact: true })
  .waitFor();
await page.screenshot({ path: new URL("spring-core-desktop.png", out).pathname, fullPage: false });
await page.setViewportSize({ width: 390, height: 900 });
await go("spring/security-filter-chain");
await page.screenshot({
  path: new URL("spring-security-mobile.png", out).pathname,
  fullPage: false,
});
await go("");
assert.equal(await page.locator(".explore-card").count(), 16);
await page.getByRole("link", { name: /Spring & Spring Boot View resources/ }).click();
await page.waitForURL("**/spring/spring-boot");
for (const path of [
  "downloads/aitrove-spring-source-kit.zip",
  "downloads/aitrove-java-source-kit.zip",
  "learning-coverage.html",
]) {
  const response = await context.request.get("http://127.0.0.1:3001/" + path);
  assert.equal(response.status(), 200, path);
  assert.ok(response.headers()["x-robots-tag"].includes("noindex"), path);
  assert.equal(response.headers()["x-content-type-options"], "nosniff", path);
}
await page.goto("http://127.0.0.1:3001/learning-coverage.html", { waitUntil: "networkidle" });
await page.locator("#subject").selectOption({ label: "Spring & Spring Boot" });
assert.equal(await page.locator("#sections details").count(), 10);
assert.ok(
  (await page.locator("#visible").innerText()).includes(
    `${spring.filter((e) => e.type !== "subject").length} lessons`,
  ),
);
await page.screenshot({
  path: new URL("spring-coverage-mobile.png", out).pathname,
  fullPage: false,
});
assert.deepEqual(errors, []);
const report = {
  passed: true,
  screens: checked,
  mobileWidths: [320, 390, 768],
  quizAnswers: answers,
  approvedHomepageCards: 16,
  separateSpringCurriculum: true,
  downloadHeaders: true,
  pageErrors: errors,
};
await fs.writeFile(new URL("java-spring-browser-check.json", out), JSON.stringify(report, null, 2));
console.log(JSON.stringify(report));
await browser.close();

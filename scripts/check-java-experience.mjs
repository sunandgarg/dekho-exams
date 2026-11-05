import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { fromHtml } from "hast-util-from-html";
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE);
const base = process.env.PREVIEW_BASE || "http://127.0.0.1:3000";
const out = "../../outputs";
const entries = JSON.parse(await fs.readFile("src/data/fixtures.json", "utf8"));
const coreLessonCount = entries
  .find((entry) => entry.path === "java/java")
  .data.modules.flatMap((module) => module.lessons).length;
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
const page = await context.newPage();
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
async function go(path) {
  const response = await page.goto(base + path, { waitUntil: "networkidle" });
  assert.equal(response.status(), 200, path);
  await page.locator('[data-app-ready="true"]').waitFor();
}
function codeValues(body) {
  const values = [];
  const text = (node) =>
    node.type === "text" ? node.value : (node.children || []).map(text).join("");
  const visit = (node) => {
    if (
      node.type === "element" &&
      node.tagName === "code" &&
      node.properties.className?.includes("language-java")
    )
      values.push(text(node));
    for (const child of node.children || []) visit(child);
  };
  visit(fromHtml(body, { fragment: true }));
  return values;
}
for (const width of [1440, 768, 390, 360]) {
  await page.setViewportSize({ width, height: 900 });
  await go("/java/java");
  const trigger = page.getByRole("button", { name: /Contents ·/ });
  assert.equal(await trigger.isVisible(), width < 1024);
  assert.equal(
    await page
      .getByRole("navigation", { name: "Subject resources", exact: true })
      .locator('a[aria-current="page"]')
      .innerText(),
    "Java Tutorial",
  );
  const diagramNext = page.getByRole("button", { name: "Next Java diagram" });
  await diagramNext.click();
  await page.getByRole("heading", { name: "Choose a collection by its operations" }).waitFor();
  await page.getByRole("button", { name: "Previous Java diagram" }).click();
  if (width < 1024) {
    const triggerColour = await trigger.evaluate(
      (element) => getComputedStyle(element).backgroundColor,
    );
    assert.ok(triggerColour.includes("0.94") && triggerColour.includes("190"), triggerColour);
    await page.screenshot({ path: `${out}/java-contents-pastel-${width}.png` });
    await trigger.click();
    const dialog = page.getByRole("dialog");
    await dialog.waitFor();
    assert.equal(
      await dialog
        .getByRole("link", { name: "Section overview", exact: true })
        .getAttribute("aria-current"),
      "page",
    );
    assert.equal(
      await dialog.getByRole("navigation", { name: "Section lessons" }).getByRole("link").count(),
      coreLessonCount + 1,
    );
    await page.waitForFunction(() => {
      const dialog = document.querySelector("[role=dialog]");
      return dialog && dialog.getBoundingClientRect().bottom <= innerHeight + 1;
    });
    await page.screenshot({ path: `${out}/java-mobile-contents-${width}.png` });
    await page.keyboard.press("Escape");
    assert.equal(await trigger.evaluate((element) => element === document.activeElement), true);
    await trigger.click();
    await page
      .getByRole("dialog")
      .getByRole("link", { name: /Java pass-by-value/ })
      .click();
    await page
      .getByRole("heading", { name: "Java pass-by-value: references and mutation", exact: true })
      .waitFor();
    await page.getByRole("dialog").waitFor({ state: "hidden" });
    assert.equal(await page.getByRole("dialog").count(), 0);
    await trigger.click();
    assert.equal(await page.getByRole("dialog").locator('a[aria-current="page"]').count(), 1);
    await page
      .getByRole("dialog")
      .getByRole("button", { name: /On this page/ })
      .click();
    await page
      .getByRole("dialog")
      .getByRole("link", { name: /Cost and design choices/ })
      .click();
    await page.getByRole("dialog").waitFor({ state: "hidden" });
    assert.equal(await page.getByRole("dialog").count(), 0);
    assert.ok((await page.url()).endsWith("#cost-and-design-choices"));
    await page.waitForFunction(() => document.activeElement?.id === "cost-and-design-choices");
    const heading = await page.locator("#cost-and-design-choices").boundingBox();
    const tabs = await page.locator("[data-subject-tabs]").boundingBox();
    assert.ok(heading.y >= tabs.y + tabs.height - 2, JSON.stringify({ heading, tabs }));
    assert.ok(heading.y < 600, JSON.stringify(heading));
    await trigger.click();
    assert.ok(
      await page
        .getByRole("dialog")
        .getByRole("navigation", { name: "Page contents" })
        .locator('a[aria-current="location"]')
        .count(),
    );
    await page.keyboard.press("Escape");
  }
  await go("/java/linkedlist");
  assert.deepEqual(
    await page.locator(".article-content pre > code.language-java").allTextContents(),
    codeValues(entries.find((entry) => entry.path === "java/linkedlist").body),
  );
  assert.ok(await page.locator(".article-content .hljs-keyword").count());
  assert.equal(await page.locator(".article-content pre p").count(), 0);
  await page.getByRole("button", { name: "addLast", exact: true }).click();
  assert.ok((await page.locator(".node-operation").innerText()).includes('addLast("Test")'));
  await page.getByRole("button", { name: "Reset", exact: true }).click();
  await page.locator("#linked-list-demo").scrollIntoViewIfNeeded();
  if (width >= 1280) {
    await page.waitForFunction(() =>
      document.querySelector('[aria-label="On this page"] a[aria-current="location"]'),
    );
  }
  await page.screenshot({ path: `${out}/java-linkedlist-highlighted-${width}.png` });
  assert.equal(
    await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2),
    false,
    String(width),
  );
  await go("/java/hashmap");
  const equalityLink = page.locator('.article-content a[href="/java/equals-hashcode"]').first();
  await equalityLink.click();
  await page
    .getByRole("heading", { name: "Java equals and hashCode: stable value keys", exact: true })
    .waitFor();
  await go("/java/java");
  await page.screenshot({ path: `${out}/java-roadmap-highlighted-${width}.png` });
}
await page.setViewportSize({ width: 390, height: 900 });
await go("/java/java-quizzes");
await page.getByRole("button", { name: "Contents · 7", exact: true }).click();
assert.equal(
  await page
    .getByRole("dialog")
    .getByRole("navigation", { name: "Section lessons" })
    .getByRole("link")
    .count(),
  8,
);
await page
  .getByRole("dialog")
  .getByRole("link", { name: /Java LinkedList quiz/, exact: false })
  .click();
await page.getByRole("heading", { name: "Java LinkedList quiz", exact: true }).waitFor();
await page.getByRole("dialog").waitFor({ state: "hidden" });
const addedQuizzes = entries.filter((entry) =>
  ["quizzes/java-collections", "quizzes/java-advanced", "quizzes/java-modern"].includes(entry.path),
);
for (const quiz of addedQuizzes) {
  await go("/" + quiz.path);
  await page.getByRole("link", { name: "Start quiz", exact: true }).click();
  for (let index = 0; index < quiz.data.questions.length; index++) {
    const question = quiz.data.questions[index];
    await page.getByRole("heading", { name: question.prompt, exact: true }).waitFor();
    await page.getByRole("radio", { name: question.options[question.answer], exact: true }).check();
    await page
      .getByRole("button", {
        name: index === quiz.data.questions.length - 1 ? "Finish & review" : "Next",
        exact: true,
      })
      .click();
  }
  await page.getByRole("heading", { name: "Answer review", exact: true }).waitFor();
  await page.getByText("9 / 9", { exact: true }).waitFor();
  for (const question of quiz.data.questions)
    await page.getByText(question.explanation, { exact: true }).waitFor();
  await page.reload({ waitUntil: "networkidle" });
  await page.getByText("9 / 9", { exact: true }).waitFor();
  assert.equal(
    await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2),
    false,
    quiz.path,
  );
}
const routes = entries.filter(
  (entry) => entry.path.startsWith("java/") || entry.path.startsWith("quizzes/java-"),
);
for (let start = 0; start < routes.length; start += 6) {
  await Promise.all(
    routes.slice(start, start + 6).map(async (entry) => {
      const response = await fetch(base + "/" + entry.path);
      assert.equal(response.status, 200, entry.path);
    }),
  );
}
assert.deepEqual(errors, []);
const report = {
  widths: [1440, 768, 390, 360],
  mobileSheet: true,
  currentLesson: true,
  escapeRestoresFocus: true,
  headingAnchors: true,
  diagramControls: true,
  syntaxColours: true,
  originalCodeTextPreserved: true,
  internalLinkNavigation: true,
  javaRoutesChecked: routes.length,
  newQuizQuestionsAnswered: addedQuizzes.reduce(
    (total, quiz) => total + quiz.data.questions.length,
    0,
  ),
  quizResultsPersistAfterReload: true,
  quizCurriculumIncludesQuizRoutes: true,
  browserErrors: errors,
  passed: true,
};
await fs.writeFile(`${out}/java-browser-check.json`, JSON.stringify(report, null, 2));
console.log(JSON.stringify(report));
await browser.close();

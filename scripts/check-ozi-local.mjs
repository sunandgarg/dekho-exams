import assert from "node:assert/strict";
import fs from "node:fs/promises";
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE);
const base = "http://127.0.0.1:3001";
const entries = JSON.parse(await fs.readFile("src/data/fixtures.json", "utf8"));
const java = entries.filter(
  (entry) =>
    entry.path.startsWith("java/") ||
    [
      "quizzes/java-basics",
      "quizzes/java-linkedlist",
      "quizzes/java-collections",
      "quizzes/java-advanced",
      "quizzes/java-modern",
    ].includes(entry.path),
);
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
const checks = [];
for (const width of [1440, 1024, 768, 390, 360]) {
  await page.setViewportSize({ width, height: 960 });
  await go("/");
  await page.getByRole("heading", { name: "Explore", exact: true, level: 1 }).waitFor();
  assert.equal(
    await page.getByRole("navigation", { name: "Mobile navigation" }).isVisible(),
    width < 768,
  );
  assert.equal(
    await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2),
    false,
  );
  assert.equal(
    await page.evaluate(
      () => getComputedStyle(document.querySelector("[data-site-header]")).backgroundColor,
    ),
    "rgb(255, 255, 255)",
  );
  await page.screenshot({ path: `../../outputs/ozi-local-home-${width}.png`, fullPage: true });
  if (width === 1440 || width === 390)
    await page.screenshot({ path: `../../outputs/ozi-local-first-screen-${width}.png` });
  assert.equal(await page.locator(".hero-lab,.reading-card,.stage-list,.practice-shop").count(), 0);
  assert.equal(await page.locator(".explore-card").count(), 16);
  assert.equal(await page.locator(".explore-card-featured").count(), 4);
  await page.getByRole("link", { name: "Java View resources", exact: true }).click();
  await page.waitForURL(/java\/java$/);
  await page.getByRole("heading", { name: "Java Tutorial", exact: true, level: 1 }).waitFor();
  await go("/");
  await page.getByRole("button", { name: "Open navigation", exact: true }).click();
  await page.getByRole("dialog").waitFor();
  assert.equal(
    await page
      .getByRole("dialog")
      .getByRole("link", { name: "Your saved reading", exact: true })
      .count(),
    1,
  );
  await page.keyboard.press("Escape");
  await page.getByRole("dialog").waitFor({ state: "hidden" });
  const search = page.getByRole("search", { name: "Site search" });
  await search.getByRole("textbox", { name: "Search resources", exact: true }).fill("linkedlist");
  await search.getByRole("button", { name: /Search/ }).click();
  await page.waitForURL(/search\?q=linkedlist/);
  await page.locator('[data-app-ready="true"]').waitFor();
  await page
    .getByRole("heading", { name: "Results for “linkedlist”", exact: true })
    .first()
    .waitFor();
  await go("/java/java");
  const resources = page.getByRole("navigation", { name: "Subject resources", exact: true });
  assert.equal(await resources.locator('a[aria-current="page"]').innerText(), "Java Tutorial");
  await resources.getByRole("link", { name: "Advanced Java", exact: true }).click();
  await page.waitForURL(/java\/advanced-java$/);
  await page.waitForFunction(
    () =>
      document.querySelector("[data-subject-tabs] a[aria-current]")?.textContent ===
      "Advanced Java",
  );
  await go("/java/linkedlist");
  const preferences = page.getByRole("group", { name: "Reading preferences", exact: true });
  await preferences.getByRole("button", { name: "Larger text", exact: true }).click();
  assert.equal(await page.locator(".learning-shell").getAttribute("data-reading-size"), "large");
  assert.equal(
    await page
      .locator(".article-content")
      .first()
      .evaluate((element) => getComputedStyle(element).fontSize),
    width < 768 ? "20px" : "21px",
  );
  await preferences.getByRole("button", { name: "Focus reading", exact: true }).click();
  assert.equal(await page.locator(".learning-shell").getAttribute("data-reading-focus"), "true");
  assert.equal(await page.locator(".learning-sidebar").isVisible(), false);
  if (width < 768) {
    assert.equal(await page.getByRole("navigation", { name: "Popular topics" }).isVisible(), false);
    assert.equal(
      await page.getByRole("navigation", { name: "Subject resources" }).isVisible(),
      false,
    );
  }
  assert.equal(
    await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2),
    false,
  );
  await page.screenshot({ path: `../../outputs/reader-focus-${width}.png` });
  await preferences.getByRole("button", { name: "Focus reading", exact: true }).click();
  await preferences.getByRole("button", { name: "Larger text", exact: true }).click();
  const lab = page.locator(".reversal-lab");
  await lab.getByRole("button", { name: "Next step", exact: true }).click();
  assert.deepEqual(await lab.locator("dd").allTextContents(), ["null", "32", "64"]);
  if (width < 1024) {
    const trigger = page.getByRole("button", { name: /Contents ·/ });
    await trigger.click();
    const dialog = page.getByRole("dialog");
    await dialog.getByRole("button", { name: /On this page ·/ }).click();
    await dialog.getByRole("link", { name: /Reverse one link at a time/ }).click();
    await dialog.waitFor({ state: "hidden" });
    await page.waitForFunction(() => document.activeElement?.id === "linked-list-reversal");
    if (width < 768) {
      const bottom = await page
        .getByRole("navigation", { name: "Mobile navigation" })
        .boundingBox();
      const contents = await trigger.boundingBox();
      assert.ok(contents.y + contents.height < bottom.y);
    }
  }
  assert.equal(
    await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2),
    false,
  );
  await page.screenshot({ path: `../../outputs/ozi-local-lesson-${width}.png` });
  await go("/explore");
  assert.equal(await page.locator(".catalog-problem-card").count(), 5);
  const filter = page.getByRole("group", { name: "Difficulty", exact: true });
  await filter.getByRole("button", { name: "Medium", exact: true }).click();
  await page.waitForURL(/difficulty=Medium/);
  await page.waitForFunction(() => document.querySelectorAll(".catalog-problem-card").length === 2);
  assert.deepEqual(
    await page.locator(".catalog-problem-card [data-difficulty]").allTextContents(),
    ["Medium", "Medium"],
  );
  assert.equal(
    await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2),
    false,
  );
  await page.screenshot({ path: `../../outputs/ozi-local-practice-${width}.png`, fullPage: true });
  await go("/");
  await page.getByRole("button", { name: "Toggle theme", exact: true }).click();
  await page.waitForFunction(() => document.documentElement.classList.contains("dark"));
  assert.equal(
    await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2),
    false,
  );
  await page.screenshot({ path: `../../outputs/ozi-local-dark-${width}.png` });
  await page.getByRole("button", { name: "Toggle theme", exact: true }).click();
  checks.push({
    width,
    noOverflow: true,
    search: true,
    homeExploreCards: true,
    readingPreferences: true,
    navigation: true,
    javaSections: true,
    contents: true,
    reversal: true,
    filters: true,
    darkTheme: true,
  });
}
await page.setViewportSize({ width: 1440, height: 960 });
await go("/java/linkedlist");
const first = page.locator(".learning-shell article").first();
const title = await first.locator("h1").innerText();
await first.getByRole("button", { name: "Save", exact: true }).click();
await page.reload({ waitUntil: "networkidle" });
await first.getByRole("button", { name: "Saved", exact: true }).waitFor();
await page.getByRole("link", { name: "Your reading list", exact: true }).click();
await page.waitForURL(/account\/bookmarks$/);
await page.getByRole("link", { name: title, exact: true }).waitFor();
for (let start = 0; start < java.length; start += 6)
  await Promise.all(
    java.slice(start, start + 6).map(async (entry) => {
      const response = await fetch(base + "/" + entry.path, { signal: AbortSignal.timeout(20000) });
      assert.equal(response.status, 200, entry.path);
    }),
  );
for (const path of ["/courses", "/account/courses", "/checkout/python-programming"])
  assert.equal((await fetch(base + path)).status, 404, path);
assert.deepEqual(errors, []);
await fs.writeFile(
  "../../outputs/ozi-local-check.json",
  JSON.stringify(
    {
      base,
      checks,
      bookmarksPersist: true,
      javaRoutesChecked: java.length,
      coursesHidden: true,
      browserErrors: errors,
      passed: true,
    },
    null,
    2,
  ),
);
console.log(
  JSON.stringify({
    widths: checks.map((c) => c.width),
    javaRoutesChecked: java.length,
    passed: true,
  }),
);
await browser.close();

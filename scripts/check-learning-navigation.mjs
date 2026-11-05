import assert from "node:assert/strict";
import fs from "node:fs/promises";
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE);
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
const out = "../../outputs/learning-navigation-check";
await fs.mkdir(out, { recursive: true });
async function go(p) {
  const r = await page.goto("http://127.0.0.1:3000" + p, { waitUntil: "networkidle" });
  assert.equal(r.status(), 200, p);
  await page.locator('[data-app-ready="true"]').waitFor();
}
const sections = [
  "java/java",
  "java/advanced-java",
  "java/java-interview-questions",
  "java/java-exercises",
  "java/java-examples",
  "java/java-quizzes",
  "java/java-projects",
  "java/java-cheatsheet",
  "java/dsa-in-java",
  "java/java-collections",
];
for (const width of [1440, 390]) {
  await page.setViewportSize({ width, height: 950 });
  await go("/java/java");
  const tabs = page.getByRole("navigation", { name: "Subject resources", exact: true });
  assert.equal(await tabs.locator("a").count(), 10);
  assert.equal(await tabs.locator('[aria-current="page"]').innerText(), "Java Tutorial");
  await tabs.getByRole("link", { name: "Advanced Java", exact: true }).click();
  await page.getByRole("heading", { name: "Advanced Java", exact: true }).waitFor();
  assert.equal(await tabs.locator('[aria-current="page"]').innerText(), "Advanced Java");
  let rail = page.getByRole("complementary", { name: "Curriculum", exact: true });
  if (width === 390) {
    await page.getByRole("button", { name: /Contents ·/ }).click();
    rail = page.getByRole("dialog");
  }
  assert.ok((await rail.innerText()).includes("Types and failures"));
  assert.ok(!(await rail.innerText()).includes("Values and control flow"));
  await rail.getByRole("link", { name: /Java exceptions: recovery boundaries/ }).click();
  await page
    .getByRole("heading", {
      name: "Java exceptions: recovery boundaries and failure context",
      exact: true,
    })
    .waitFor();
  assert.equal(await tabs.locator('[aria-current="page"]').innerText(), "Advanced Java");
  if (width === 390) await page.getByRole("dialog").waitFor({ state: "hidden" });
  await page.screenshot({ path: `${out}/java-lesson-${width}.png`, fullPage: true });
  await page.evaluate(() => scrollTo(0, 500));
  const pos = await tabs.boundingBox();
  const hb = await page.locator("header").boundingBox();
  assert.ok(Math.abs(pos.y - (hb.y + hb.height)) < 3, JSON.stringify({ pos, hb }));
  assert.equal(
    await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2),
    false,
  );
  await go("/java/java");
  assert.ok(
    await page
      .getByRole("navigation", { name: "Continue exploring this subject" })
      .getByRole("link", { name: /Advanced Java/ })
      .count(),
  );
}
const es = JSON.parse(await fs.readFile("src/data/fixtures.json", "utf8"));
const allLinks = new Set();
for (const hub of es.filter((e) => e.type === "subject"))
  for (const tab of hub.data.resource_tabs ?? []) allLinks.add(tab.path);
for (const route of allLinks) {
  const r = await fetch("http://127.0.0.1:3000/" + route);
  assert.equal(r.status, 200, route);
}
for (const route of sections) {
  await go("/" + route);
  assert.equal(await page.locator("h1").count(), 1);
  assert.equal(
    await page
      .getByRole("navigation", { name: "Subject resources", exact: true })
      .locator("a")
      .count(),
    10,
  );
}
await go("/python/python-programming-language-tutorial");
assert.ok(
  await page
    .getByRole("navigation", { name: "Subject resources", exact: true })
    .locator("a")
    .count(),
);
await go("/ai-tools/chatgpt-codex");
assert.ok(
  await page
    .getByRole("navigation", { name: "Subject resources", exact: true })
    .locator("a")
    .count(),
);
assert.deepEqual(errors, []);
const report = {
  javaSections: sections.length,
  subjectTabTargetsChecked: allLinks.size,
  desktopAndMobile: true,
  sidebarChanges: true,
  activeTabOnLessons: true,
  stickyBar: true,
  continuationLinks: true,
  browserErrors: errors,
};
await fs.writeFile(`${out}/report.json`, JSON.stringify(report, null, 2));
console.log(JSON.stringify(report));
await browser.close();

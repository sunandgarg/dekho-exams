import assert from "node:assert/strict";
import fs from "node:fs/promises";
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE);
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 390, height: 900 } });
const file = new URL("../../../outputs/java-coverage-map.html", import.meta.url);
await page.goto(file.href);
const paths = await page
  .locator('a[href^="https://aitrove-frontend.cirkle-world.workers.dev/"]')
  .evaluateAll((anchors) => [...new Set(anchors.map((anchor) => new URL(anchor.href).pathname))]);
assert.equal(paths.length, 100);
assert.equal(
  await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2),
  false,
);
await page.getByLabel("Show", { exact: true }).selectOption("remaining");
assert.equal(await page.locator('.branch[data-status="published"]:visible').count(), 0);
assert.equal(await page.locator("details.remaining:visible").count(), 10);
await page.getByLabel("Show", { exact: true }).selectOption("published");
assert.equal(await page.locator("details.remaining:visible").count(), 0);
await page.getByLabel("Show", { exact: true }).selectOption("all");
await page.getByLabel("Find a topic", { exact: true }).fill("JDBC");
assert.ok((await page.locator(".branch:visible").count()) > 0);
await page.getByLabel("Find a topic", { exact: true }).fill("");
await page.screenshot({ path: "../../outputs/java-coverage-map-mobile.png" });
const report = {
  publishedRouteLinks: 100,
  statusFilters: true,
  search: true,
  mobileOverflow: false,
  passed: true,
};
await fs.writeFile("../../outputs/java-coverage-map-check.json", JSON.stringify(report, null, 2));
console.log(JSON.stringify(report));
await browser.close();

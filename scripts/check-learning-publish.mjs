import assert from "node:assert/strict";
import fs from "node:fs/promises";
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE);
const entries = JSON.parse(await fs.readFile("src/data/fixtures.json", "utf8"));
const ready = entries.filter((e) => e.status === "published" && e.data?.seo_ready === true);
const springCount = entries.filter(
  (e) => e.path.startsWith("spring/") || e.path.startsWith("quizzes/spring-"),
).length;
const base = "http://127.0.0.1:3002";
const origin = "https://aitrove-frontend.cirkle-world.workers.dev";
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 320, height: 900 } });
const request = context.request;
const visited = new Set();
let locations = [];
async function sitemap(path) {
  assert.ok(!visited.has(path), "sitemap loop");
  visited.add(path);
  const r = await request.get(base + path);
  assert.equal(r.status(), 200);
  const xml = await r.text();
  const urls = [...xml.matchAll(/<loc>(.*?)<\/loc>/g)].map((m) => m[1]);
  if (xml.includes("<sitemapindex")) {
    for (const url of urls) await sitemap(new URL(url).pathname);
  } else locations.push(...urls);
}
await sitemap("/sitemap.xml");
assert.equal(new Set(locations).size, ready.length + 1);
assert.ok(locations.includes(origin + "/"));
for (const e of ready) assert.ok(locations.includes(origin + "/" + e.path), e.path);
assert.equal(
  locations.filter(
    (x) =>
      new URL(x).pathname.startsWith("/spring/") ||
      new URL(x).pathname.startsWith("/quizzes/spring-"),
  ).length,
  springCount,
);
const addition = JSON.parse(await fs.readFile("../../outputs/java-spring-third-additions.json"));
const paths = [
  ...addition.java,
  ...entries
    .filter((e) => e.path.startsWith("spring/") || e.path.startsWith("quizzes/spring-"))
    .map((e) => e.path),
];
for (const path of paths) {
  const r = await request.get(base + "/" + path);
  assert.equal(r.status(), 200, path);
  assert.ok(!(r.headers()["x-robots-tag"] ?? "").includes("noindex"), path);
  const html = await r.text();
  assert.ok(html.includes('rel="canonical" href="' + origin + "/" + path + '"'), path);
  assert.ok(html.includes("application/ld+json"), path);
  assert.ok(!html.includes('name="robots" content="noindex'), path);
}
for (const path of [
  "/learning-coverage.html",
  "/java-coverage.html",
  "/downloads/dekhoexams-spring-source-kit.zip",
]) {
  const r = await request.get(base + path);
  assert.equal(r.status(), 200, path);
  assert.ok(r.headers()["x-robots-tag"].includes("noindex"), path);
  assert.equal(r.headers()["x-content-type-options"], "nosniff", path);
}
const page = await context.newPage();
await page.goto(base + "/spring/transactions", { waitUntil: "networkidle" });
await page.locator('[data-app-ready="true"]').waitFor();
const active = page.locator('nav[aria-label="Popular topics"] a[aria-current="page"]');
const box = await active.boundingBox();
assert.ok(box.x >= -1 && box.x + box.width <= 321, JSON.stringify(box));
assert.equal(
  await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2),
  false,
);
await page.screenshot({ path: "../../outputs/spring-transactions-320-final.png", fullPage: false });
const report = {
  passed: true,
  launchSitemapUrls: locations.length,
  eligibleRecords: ready.length,
  springRoutesInSitemap: springCount,
  javaRoutesInSitemap: locations.filter(
    (x) =>
      new URL(x).pathname.startsWith("/java/") || new URL(x).pathname.startsWith("/quizzes/java-"),
  ).length,
  newPagesWithCanonicalAndSchema: paths.length,
  coverageAndDownloadsNoindex: true,
  selectedMobileTopicFullyVisible: true,
};
await fs.writeFile(
  "docs/java-spring-expansion/publish-runtime-check.json",
  JSON.stringify(report, null, 2),
);
console.log(JSON.stringify(report));
await browser.close();

import assert from "node:assert/strict";
import fs from "node:fs/promises";
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE);
const base = process.env.SEO_CHECK_ORIGIN || "http://127.0.0.1:3002";
const preview = process.env.SEO_CHECK_PREVIEW === "true";
const origin = "https://aitrove-frontend.cirkle-world.workers.dev";
const entries = JSON.parse(await fs.readFile("src/data/fixtures.json", "utf8"));
const publicEntries = entries.filter((e) => e.status === "published" && e.type !== "course");
const ready = publicEntries.filter((e) => e.data.seo_ready === true);
const b = await chromium.launch({ headless: true });
const context = await b.newContext();
const checked = [];
const unescape = (s) =>
  s
    .replaceAll("&amp;", "&")
    .replaceAll("&quot;", '"')
    .replaceAll("&#x27;", "'")
    .replaceAll("&lt;", "<")
    .replaceAll("&gt;", ">");
const transportRetries = [];
const get = async (path) => {
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      return await context.request.get(base + "/" + path, { timeout: 30000 });
    } catch (error) {
      if (attempt === 2 || !/ECONNRESET|socket hang up|Timeout/i.test(String(error))) throw error;
      transportRetries.push({ path, attempt: attempt + 1 });
    }
  }
  throw new Error(`Unreachable GET retry state for ${path}`);
};
for (let i = 0; i < publicEntries.length; i += 5) {
  await Promise.all(
    publicEntries.slice(i, i + 5).map(async (e) => {
      const r = await get(e.path);
      assert.equal(r.status(), 200, e.path);
      const text = await r.text();
      assert.equal((text.match(/<h1(?:\s|>)/g) || []).length, 1, e.path);
      const titles = [...text.matchAll(/<title>([\s\S]*?)<\/title>/g)];
      assert.equal(titles.length, 1, e.path);
      assert.ok(unescape(titles[0][1]).includes(e.title), e.path);
      const canonical = [...text.matchAll(/<link[^>]*rel="canonical"[^>]*>/g)];
      assert.equal(canonical.length, 1, e.path);
      assert.ok(canonical[0][0].includes(origin + "/" + e.path), e.path);
      const robots = text.match(/<meta[^>]*name="robots"[^>]*>/)?.[0];
      assert.ok(robots, e.path);
      const shouldIndex = !preview && e.data.seo_ready === true;
      assert.equal(robots.includes("noindex"), !shouldIndex, e.path);
      const schema = [
        ...text.matchAll(/<script[^>]*type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/g),
      ].flatMap((m) => JSON.parse(m[1]));
      if (e.data.seo_ready === true) {
        assert.ok(
          schema.some((s) => s["@type"] === "BreadcrumbList"),
          e.path,
        );
        assert.ok(
          schema.some((s) => s.url === origin + "/" + e.path),
          e.path,
        );
        if (e.type === "article")
          assert.ok(
            schema.some((s) => s["@type"] === "Article" && s.author.name === "AITrove Editorial"),
            e.path,
          );
      }
      checked.push({
        path: e.path,
        status: r.status(),
        indexable: shouldIndex,
        jsonld: schema.length,
      });
    }),
  );
  await new Promise((resolve) => setTimeout(resolve, 1000));
}
const sitemapResponse = await get("sitemap.xml");
assert.equal(sitemapResponse.status(), 200);
const sitemap = await sitemapResponse.text();
const locs = [...sitemap.matchAll(/<loc>([^<]*)<\/loc>/g)].map((m) => unescape(m[1]));
const expected = preview ? [] : [origin + "/", ...ready.map((e) => origin + "/" + e.path)];
assert.deepEqual([...new Set(locs)].sort(), expected.sort());
const robots = await (await get("robots.txt")).text();
assert.ok(robots.includes("Sitemap: " + origin + "/sitemap.xml"));
for (const path of [
  "search?q=missing",
  "account",
  "quizzes/java-25/attempt",
  "quizzes/java-25/result",
  "quizzes/python-basics/attempt",
  "quizzes/python-basics/result",
  "admin",
  "auth",
  "reset-password",
]) {
  const r = await get(path);
  assert.equal(r.status(), 200, path);
  const html = await r.text();
  assert.ok(html.match(/<meta[^>]*name="robots"[^>]*>/)?.[0].includes("noindex"), path);
  assert.ok(r.headers()["x-robots-tag"]?.includes("noindex"), path);
}
for (const path of [
  "category/does-not-exist",
  "video-category/does-not-exist",
  "courses",
  "courses/java",
]) {
  const r = await get(path);
  assert.equal(r.status(), 404, path);
}
const redirect = await context.request.get(base + "/JAVA/HashMap/", { maxRedirects: 0 });
assert.equal(redirect.status(), 308);
assert.equal(new URL(redirect.headers().location).pathname, "/java/hashmap");
const headingPage = await context.newPage();
await headingPage.goto(base + "/quizzes/java-25", { waitUntil: "networkidle" });
assert.equal(
  await headingPage.locator('[data-subject-tabs] a[aria-current="page"]').getAttribute("href"),
  "/java/java-quizzes",
);
for (const path of ["java-coverage.html", "downloads/aitrove-java-source-kit.zip"]) {
  const r = await get(path);
  assert.equal(r.status(), 200, path);
  assert.ok(r.headers()["x-robots-tag"]?.includes("noindex"), path);
}
assert.equal(await headingPage.locator(".local-design-ribbon").count(), preview ? 1 : 0);
assert.ok(
  (await headingPage.getByRole("link", { name: "Start quiz", exact: true }).boundingBox()).height >=
    44,
);

const report = {
  origin: base,
  mode: preview ? "preview" : "production build tested locally",
  publicContentResponses: checked.length,
  readyContent: ready.length,
  sitemapUrls: locs.length,
  utilityNoindexChecks: 9,
  invalidPaths404: 4,
  aliasRedirect: 308,
  passed: true,
  transportRetries,
  pages: checked,
};
await fs.writeFile(
  "../../outputs/seo-publish-runtime-check.json",
  JSON.stringify(report, null, 2) + "\n",
);
console.log(JSON.stringify({ ...report, pages: undefined }));
await b.close();

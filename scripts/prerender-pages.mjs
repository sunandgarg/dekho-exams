import { readFile, mkdir, rm, writeFile } from "node:fs/promises";
import { gunzipSync } from "node:zlib";
import { dirname, resolve } from "node:path";

process.env.AITROVE_STATIC_EXPORT = "1";
const output = resolve("dist/client/__prerender");
const rows = JSON.parse(gunzipSync(Buffer.from(await readFile("src/data/cms-snapshot.txt", "utf8"), "base64")));
const paths = [...new Set(rows
  .filter((row) => row[1] !== "course" && /^[a-z0-9]+(?:[/-][a-z0-9]+)*$/.test(row[2]))
  .map((row) => row[2]))];
const app = (await import("../dist/server/index.js")).default;
const context = { waitUntil() {} };
await rm(output, { recursive: true, force: true });
await mkdir(output, { recursive: true });

async function render(path, destination) {
  const response = await app.fetch(new Request(`https://aitrove.in/${path}`), {}, context);
  if (response.status !== 200) throw new Error(`${path || "/"} rendered HTTP ${response.status}`);
  const body = await response.text();
  if (path && destination.endsWith(".html") && !body.includes(`href="https://aitrove.in/${path}"`))
    throw new Error(`${path} has no matching canonical URL`);
  const target = resolve(output, destination);
  await mkdir(dirname(target), { recursive: true });
  await writeFile(target, body);
}

await render("", "home.html");
let next = 0;
await Promise.all(Array.from({ length: 8 }, async () => {
  while (next < paths.length) {
    const path = paths[next++];
    await render(path, `${path}.html`);
  }
}));

await render("robots.txt", "robots.txt");
await render("sitemap.xml", "sitemap.xml");
const sitemapPages = Math.max(1, Math.ceil(rows.filter((row) => row[1] !== "course" && row[10]?.seo_ready === true).length / 1000));
for (let page = 1; page <= sitemapPages; page++)
  await render(`sitemap-${page}.xml`, `sitemap-${page}.xml`);
await writeFile(resolve("dist/client/404.html"), '<!doctype html><html lang="en"><meta name="robots" content="noindex"><title>Page not found</title><body><h1>Page not found</h1></body></html>');
console.log(`Prerendered ${paths.length + 1} pages, robots.txt, and ${sitemapPages + 1} sitemap files.`);

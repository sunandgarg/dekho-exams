import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE);
const base = 'http://127.0.0.1:3001';
const out = new URL('../../../outputs/', import.meta.url);
const batch = JSON.parse(await fs.readFile(new URL('java-next-content-batch.json', out)));
const entries = JSON.parse(await fs.readFile('src/data/fixtures.json', 'utf8'));
const lookup = new Map(entries.map(e => [e.path, e]));
const browser = await chromium.launch({headless: true});
const page = await browser.newPage({viewport: {width: 1440, height: 960}});
const errors = [];
page.on('pageerror', error => errors.push(error.message));
async function go(path) {
  const response = await page.goto(base + '/' + path, {waitUntil: 'networkidle'});
  assert.equal(response.status(), 200, path);
  await page.locator('[data-app-ready="true"]').waitFor();
}
const verified = [];
for (const path of batch.added) {
  const entry = lookup.get(path);
  await go(path);
  assert.equal(await page.locator('h1').first().innerText(), entry.title);
  const article = page.locator('.article-content').filter({has: page.locator('code.language-java')}).first();
  await article.getByRole('heading', {name: 'Common Mistakes', exact: true}).waitFor();
  assert.equal(await article.locator('code.language-java').count(), 1, path);
  assert.equal(await article.locator('code.language-text').count(), 1, path);
  assert.ok(await article.locator('code.language-java [class^="hljs-"]').count() > 0, path);
  const selected = page.locator('[data-subject-tabs] a[aria-current="page"]');
  assert.equal(await selected.getAttribute('href'), '/' + entry.data.section_path, path);
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2), false, path);
  verified.push(path);
}
await go('java/java');
await page.locator('.curriculum-roadmap').getByRole('button', {name: /Input, encoding and call boundaries/}).waitFor();
await page.locator('main a[href="/java/console-input"]').last().click();
await page.waitForURL(/java\/console-input$/);
await go('java/dijkstra');
await page.screenshot({path: new URL('java-next-dijkstra-desktop.png', out).pathname});
const mobile = [];
for (const width of [768, 390, 360, 320]) {
  await page.setViewportSize({width, height: 900});
  await go('java/console-input');
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2), false);
  await page.getByRole('button', {name: /Contents ·/}).click();
  const sheet = page.getByRole('dialog');
  await sheet.locator('a[href="/java/unicode-encoding"]').click();
  await page.waitForURL(/java\/unicode-encoding$/);
  await sheet.waitFor({state: 'hidden'});
  await page.getByRole('button', {name: /Contents ·/}).click();
  await sheet.getByRole('button', {name: /On this page ·/}).click();
  await sheet.getByRole('link', {name: /Cost and failure boundaries/}).click();
  await sheet.waitFor({state: 'hidden'});
  await page.waitForFunction(() => document.activeElement?.textContent === 'Cost and failure boundaries');
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2), false);
  if (width === 390) {
    await go('java/dijkstra');
    await page.screenshot({path: new URL('java-next-dijkstra-mobile.png', out).pathname});
  }
  mobile.push(width);
}
await page.setViewportSize({width: 1440, height: 960});
await go('search?q=topological');
await page.locator('main a[href="/java/topological-sort"]').first().waitFor();
await page.goto(pathToFileURL(new URL('java-next-coverage.html', out).pathname).href);
const totalLinks = await page.locator('a[href^="http://127.0.0.1:3001/"]').evaluateAll(links => new Set(links.map(a => a.href)).size);
assert.equal(totalLinks, 124);
await page.getByRole('combobox', {name: 'Show', exact: true}).selectOption('new');
const changedPaths = await page.locator('li:not([hidden])[data-status] a').evaluateAll(links => new Set(links.map(a => a.href)).size);
assert.equal(changedPaths, 32);
await page.getByRole('combobox', {name: 'Show', exact: true}).selectOption('remaining');
assert.equal(await page.locator('.branch:not([hidden])').count(), 10);
assert.equal(await page.locator('li:not([hidden])[data-status]').count(), 0);
await page.getByRole('combobox', {name: 'Show', exact: true}).selectOption('all');
await page.getByRole('textbox', {name: 'Find a topic', exact: true}).fill('Dijkstra');
assert.equal(await page.locator('li:not([hidden])').count(), 1);
await page.getByRole('textbox', {name: 'Find a topic', exact: true}).fill('');
await page.setViewportSize({width: 390, height: 900});
assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2), false);
await page.screenshot({path: new URL('java-next-coverage-mobile.png', out).pathname});
assert.deepEqual(errors, []);
const result = {newArticlePagesVerified: verified.length, mobileWidths: mobile, activeSections: true, highlightedCodeAndOutput: true, mobileCurriculumAndHeadingJumps: true, searchFindsNewContent: true, coverageLinks: totalLinks, changedMapLinks: changedPaths, coverageFilters: true, browserErrors: errors, passed: true};
await fs.writeFile(new URL('java-next-browser-check.json', out), JSON.stringify(result, null, 2));
console.log(JSON.stringify(result));
await browser.close();

import assert from "node:assert/strict";
import fs from "node:fs/promises";
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE);
const additions = JSON.parse(await fs.readFile("../../outputs/java-spring-third-additions.json"));
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
let screens = 0;
for (const width of [320, 390]) {
  await page.setViewportSize({ width, height: 900 });
  for (const path of additions.added) {
    const response = await page.goto("http://127.0.0.1:3001/" + path, { waitUntil: "networkidle" });
    assert.equal(response.status(), 200, path);
    await page.locator('[data-app-ready="true"]').waitFor();
    assert.equal(
      await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2),
      false,
      path,
    );
    await page
      .getByRole("button", { name: /Contents/ })
      .first()
      .click();
    await page.getByRole("dialog").waitFor();
    await page.keyboard.press("Escape");
    await page.getByRole("dialog").waitFor({ state: "hidden" });
    screens++;
  }
}
assert.deepEqual(errors, []);
const report = { passed: true, newLessonScreens: screens, widths: [320, 390], pageErrors: errors };
await fs.writeFile(
  "docs/java-spring-expansion/new-mobile-check.json",
  JSON.stringify(report, null, 2),
);
console.log(JSON.stringify(report));
await browser.close();

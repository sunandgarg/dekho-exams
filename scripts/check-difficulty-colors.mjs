import assert from "node:assert/strict";
import fs from "node:fs/promises";
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE);
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
const base = process.env.PREVIEW_BASE || "http://127.0.0.1:3000";
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
const checks = [];
async function contrast(locator) {
  return locator.evaluate((element) => {
    const style = getComputedStyle(element);
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    function lum(color) {
      ctx.fillStyle = color;
      ctx.fillRect(0, 0, 1, 1);
      const channels = [...ctx.getImageData(0, 0, 1, 1).data]
        .slice(0, 3)
        .map((v) => v / 255)
        .map((v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
      return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
    }
    const fg = lum(style.color),
      bg = lum(style.backgroundColor);
    return (Math.max(fg, bg) + 0.05) / (Math.min(fg, bg) + 0.05);
  });
}
for (const width of [1440, 390, 360]) {
  await page.setViewportSize({ width, height: 900 });
  await page.goto(base + "/explore", { waitUntil: "networkidle" });
  await page.locator('[data-app-ready="true"]').waitFor();
  for (const dark of [false, true]) {
    await page.evaluate((dark) => document.documentElement.classList.toggle("dark", dark), dark);
    const filters = page.getByRole("group", { name: "Difficulty", exact: true });
    for (const level of ["Easy", "Medium", "Hard"]) {
      const ratio = await contrast(filters.getByRole("button", { name: level, exact: true }));
      assert.ok(ratio >= 4.5, `${level} ${width} ${dark} ${ratio}`);
      checks.push({ width, dark, level, contrast: Number(ratio.toFixed(2)) });
    }
    const medium = filters.getByRole("button", { name: "Medium", exact: true });
    await medium.click();
    await page.waitForURL(/difficulty=Medium/);
    await page.waitForFunction(() =>
      [...document.querySelectorAll("tbody [data-difficulty]")].every(
        (el) => el.textContent === "Medium",
      ),
    );
    assert.equal(await medium.getAttribute("aria-pressed"), "true");
    assert.equal(await page.locator("tbody [data-difficulty]").count(), 2);
    assert.ok((await contrast(medium)) >= 4.5);
    assert.ok((await contrast(page.locator("tbody [data-difficulty]").first())) >= 4.5);
    await page.screenshot({
      path: `../../outputs/difficulty-${width}-${dark ? "dark" : "light"}.png`,
    });
    await filters.getByRole("button", { name: "All", exact: true }).click();
    await page.waitForURL((url) => !url.searchParams.has("difficulty"));
    await page.waitForFunction(
      () => document.querySelectorAll("tbody [data-difficulty]").length === 5,
    );
    const easy = filters.getByRole("button", { name: "Easy", exact: true });
    await easy.focus();
    await page.keyboard.press("Enter");
    await page.waitForURL(/difficulty=Easy/);
    await page.waitForFunction(() =>
      [...document.querySelectorAll(".difficulty-options button")].some(
        (el) => el.textContent === "Easy" && el.getAttribute("aria-pressed") === "true",
      ),
    );
    assert.equal(await easy.getAttribute("aria-pressed"), "true");
    await filters.getByRole("button", { name: "All", exact: true }).click();
    await page.waitForURL((url) => !url.searchParams.has("difficulty"));
    await page.waitForFunction(
      () => document.querySelectorAll("tbody [data-difficulty]").length === 5,
    );
    assert.equal(
      await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2),
      false,
    );
  }
  await page.goto(base + "/problems/kadanes-algorithm/1", { waitUntil: "networkidle" });
  assert.equal(await page.locator("[data-difficulty]").first().innerText(), "Medium");
  await page.goto(base + "/java/hashmap", { waitUntil: "networkidle" });
  assert.equal(await page.locator("[data-difficulty]").first().innerText(), "Intermediate");
  await page.goto(base + "/java/linkedlist", { waitUntil: "networkidle" });
  const action = page.getByRole("button", { name: "addLast", exact: true });
  assert.ok((await contrast(action)) >= 4.5);
  await action.click();
  assert.ok((await page.locator(".node-operation").innerText()).includes('addLast("Test")'));
}
assert.deepEqual(errors, []);
await fs.writeFile(
  "../../outputs/difficulty-color-check.json",
  JSON.stringify({ base, checks, errors, passed: true }, null, 2),
);
console.log(
  JSON.stringify({
    contrastChecks: checks.length,
    minimum: Math.min(...checks.map((c) => c.contrast)),
    passed: true,
  }),
);
await browser.close();

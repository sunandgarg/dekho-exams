import assert from "node:assert/strict";
import fs from "node:fs/promises";
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE);
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
const results = [];
const selectors = {
  "/": [
    ".directory-eyebrow",
    ".directory-intro h1",
    ".directory-intro > p",
    ".directory-jumps a",
    ".tool-collection h3",
    ".tool-copy p",
    ".shelf-heading h2",
    ".subject-tile h3",
    ".algorithm-topic h3",
    ".implementation-link",
    ".directory-shortcuts a",
    ".shelf-all",
    ".ozi-search button",
    ".ozi-footer .text-footer-muted",
  ],
  "/java/linkedlist": [
    ".learning-shell article > h1",
    ".article-content p",
    ".article-content h2",
    ".article-content h3",
    ".reading-controls button",
    ".reading-controls > span",
    ".difficulty-pill",
    ".curriculum-heading",
    ".curriculum-module > summary",
    ".curriculum-lesson",
    ".mobile-contents-trigger",
  ],
};
function lum(rgb) {
  return rgb
    .map((c) => c / 255)
    .map((c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4))
    .reduce((n, c, i) => n + c * [0.2126, 0.7152, 0.0722][i], 0);
}
for (const mode of ["light", "dark"]) {
  for (const [path, list] of Object.entries(selectors)) {
    await page.goto("http://127.0.0.1:3001" + path, { waitUntil: "networkidle" });
    await page.locator("[data-app-ready=true]").waitFor();
    if (
      ((await page.locator("html").getAttribute("class")) ?? "").includes("dark") !==
      (mode === "dark")
    )
      await page.getByRole("button", { name: "Toggle theme", exact: true }).click();
    await page.waitForFunction(
      (m) => document.documentElement.classList.contains("dark") === (m === "dark"),
      mode,
    );
    const pairs = await page.evaluate(
      (list) =>
        list.flatMap((selector) =>
          [...document.querySelectorAll(selector)]
            .filter(
              (e) =>
                e.getBoundingClientRect().width &&
                e.getBoundingClientRect().height &&
                e.textContent.trim(),
            )
            .map((e) => {
              const style = getComputedStyle(e);
              const canvas = document.createElement("canvas");
              canvas.width = canvas.height = 1;
              const context = canvas.getContext("2d", { willReadFrequently: true });
              const parse = (color) => {
                context.clearRect(0, 0, 1, 1);
                context.fillStyle = color;
                context.fillRect(0, 0, 1, 1);
                return [...context.getImageData(0, 0, 1, 1).data];
              };
              let ancestor = e;
              const layers = [];
              while (ancestor) {
                layers.push({
                  css: getComputedStyle(ancestor).backgroundColor,
                  rgba: parse(getComputedStyle(ancestor).backgroundColor),
                });
                ancestor = ancestor.parentElement;
              }
              let background = [255, 255, 255];
              for (const layer of layers.reverse())
                background = background.map(
                  (channel, i) =>
                    (layer.rgba[i] * layer.rgba[3]) / 255 + channel * (1 - layer.rgba[3] / 255),
                );
              return {
                selector,
                text: e.textContent.trim().slice(0, 65),
                foreground: parse(style.color).slice(0, 3),
                background,
                size: parseFloat(style.fontSize),
                weight: parseInt(style.fontWeight),
                cssColor: style.color,
                cssBackground: layers.filter((l) => l.rgba[3]).map((l) => l.css),
              };
            }),
        ),
      list,
    );
    for (const pair of pairs) {
      assert.ok(pair.foreground && pair.background, JSON.stringify(pair));
      const a = lum(pair.foreground),
        b = lum(pair.background);
      const ratio = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
      const minimum = pair.size >= 24 || (pair.size >= 18.667 && pair.weight >= 700) ? 3 : 4.5;
      results.push({ mode, path, ...pair, ratio: +ratio.toFixed(2), minimum });
      assert.ok(ratio >= minimum, JSON.stringify({ mode, path, ...pair, ratio }));
    }
  }
}
await page.setViewportSize({ width: 390, height: 844 });
await page.goto("http://127.0.0.1:3001/java/linkedlist", { waitUntil: "networkidle" });
await page.getByRole("button", { name: "Larger text", exact: true }).click();
await page.getByRole("button", { name: "Focus reading", exact: true }).click();
await page.getByRole("button", { name: /Contents ·/ }).click();
await page.getByRole("dialog").waitFor();
await page.keyboard.press("Escape");
await page.getByRole("dialog").waitFor({ state: "hidden" });
assert.equal(
  await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2),
  false,
);
await page.goto("http://127.0.0.1:3001/", { waitUntil: "networkidle" });
await page.keyboard.press("Tab");
await page.getByRole("link", { name: "Skip to content", exact: true }).waitFor();
await page.keyboard.press("Enter");
assert.equal(await page.evaluate(() => document.activeElement.id), "main-content");
await fs.writeFile(
  "../../outputs/reader-palette-check.json",
  JSON.stringify(
    {
      passed: true,
      pairs: results.length,
      minimumRatio: Math.min(...results.map((r) => r.ratio)),
      mobileFocusContents: true,
      keyboardSkip: true,
      results,
    },
    null,
    2,
  ),
);
console.log(
  JSON.stringify({
    passed: true,
    pairs: results.length,
    minimumRatio: Math.min(...results.map((r) => r.ratio)),
  }),
);
await browser.close();

import fs from "node:fs/promises";
import assert from "node:assert/strict";
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE);
const out = "../../outputs/privacy-editorial-check";
await fs.mkdir(out, { recursive: true });
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1440, height: 950 },
  permissions: ["clipboard-read", "clipboard-write"],
});
const page = await context.newPage();
const errors = [];
const external = [];
page.on("pageerror", (e) => errors.push(e.message));
context.on("request", (r) => {
  if (!r.url().startsWith("http://127.0.0.1:3000") && !r.url().startsWith("data:"))
    external.push(r.url());
});
const go = async (path) => {
  await page.goto("http://127.0.0.1:3000" + path, { waitUntil: "networkidle" });
  await page.locator('[data-app-ready="true"]').waitFor();
};
await go("/");
assert.equal(await page.locator("main").getAttribute("class"), null);
await page.getByRole("button", { name: "Reject optional media", exact: true }).click();
assert.equal(
  await page.evaluate(() => JSON.parse(localStorage.getItem("aitrove-consent-v1")).externalMedia),
  false,
);
await page.reload({ waitUntil: "networkidle" });
assert.equal(await page.getByRole("heading", { name: "Your privacy choices" }).count(), 0);
const paths = [
  "/legal",
  "/legal/privacy-policy",
  "/legal/terms-and-conditions",
  "/legal/cookie-policy",
  "/legal/refund-policy",
  "/legal/accessibility",
  "/legal/content-policy",
  "/about/contact-us",
  "/tutorials/ai-ml-data-science",
  "/python/python-functions",
];
for (const width of [1440, 390]) {
  await page.setViewportSize({ width, height: 950 });
  for (const path of paths) {
    await go(path);
    assert.equal(await page.locator("h1").count(), 1, path);
    assert.equal(
      await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2),
      false,
      path,
    );
    if (path.includes("privacy-policy") || path.includes("ai-ml-data-science"))
      await page.screenshot({
        path: `${out}/${path.includes("privacy-policy") ? "privacy" : "ai-directory"}-${width}.png`,
        fullPage: true,
      });
  }
}
await page.setViewportSize({ width: 1440, height: 950 });
await go("/about/contact-us");
const form = page.locator("main form");
await form.getByLabel("Name", { exact: true }).fill("Preview Learner");
await form.getByLabel("Email", { exact: true }).fill("learner@example.com");
await form
  .getByLabel("Message", { exact: true })
  .fill("Please explain this example in more detail.");
await form.getByRole("button", { name: "Check inquiry availability" }).click();
assert.equal(
  await form.locator('input[type="checkbox"]').evaluate((el) => el.validity.valueMissing),
  true,
);
await form.getByRole("checkbox").focus();
await page.keyboard.press("Space");
await form.getByRole("button", { name: "Check inquiry availability" }).click();
await form.getByRole("status").filter({ hasText: "has not been sent" }).waitFor();
assert.equal(await page.evaluate(() => localStorage.getItem("aitrove-preview-v1")), null);
// Exercise a supported media URL without adding a third-party video to editorial fixtures.
await page.evaluate(async () => {
  const reactModule = await import("/node_modules/.vite/deps/react.js");
  const React = reactModule.default ?? reactModule;
  const domModule = await import("/node_modules/.vite/deps/react-dom_client.js");
  const { createRoot } = domModule.default ?? domModule;
  const { SafeMedia } = await import("/src/components/cms/privacy-controls.tsx");
  const mount = document.createElement("div");
  mount.id = "test-media";
  document.querySelector("main").append(mount);
  createRoot(mount).render(
    React.createElement(SafeMedia, {
      url: "https://www.youtube.com/embed/test-preview",
      title: "Media privacy test",
    }),
  );
});
await page.getByText("External video is paused", { exact: true }).waitFor();
assert.equal(await page.locator("#test-media iframe").count(), 0);
await context.route(/youtube-nocookie\.com/, (route) => route.abort());
await page.getByRole("button", { name: "Privacy preferences", exact: true }).click();
await page.getByRole("button", { name: "Allow external media", exact: true }).click();
await page.locator("#test-media iframe").waitFor();
assert.match(await page.locator("#test-media iframe").getAttribute("src"), /youtube-nocookie/);
await page.getByRole("button", { name: "Privacy preferences", exact: true }).click();
await page.getByRole("button", { name: "Reject optional media", exact: true }).click();
await page.locator("#test-media iframe").waitFor({ state: "detached" });
await page.evaluate(() => {
  localStorage.setItem(
    "aitrove-preview-v1",
    JSON.stringify({
      bookmarks: [],
      completed: ["x"],
      quizzes: {},
      drafts: {},
      settings: { displayName: "Preview", dailyGoal: 20 },
    }),
  );
});
page.once("dialog", (d) => d.accept());
await page.getByRole("button", { name: "Clear saved learning data", exact: true }).click();
assert.equal(await page.evaluate(() => localStorage.getItem("aitrove-preview-v1")), null);
await go("/python/python-functions");
await page.getByRole("button", { name: "Copy code", exact: true }).first().click();
await page.getByRole("status").filter({ hasText: "Code copied" }).first().waitFor();
assert.ok((await page.evaluate(() => navigator.clipboard.readText())).length > 10);
assert.equal(
  external.filter((u) => !u.includes("youtube-nocookie")).length,
  0,
  external.join("\n"),
);
assert.deepEqual(errors, []);
const report = {
  policyRoutes: paths.length,
  responsiveWidths: [1440, 390],
  homepageBodyPreserved: true,
  externalRequestsBeforePermission: 0,
  mediaAllowAndWithdraw: true,
  formConsentKeyboardChecked: true,
  localDataDeletion: true,
  codeCopy: true,
  browserErrors: errors,
};
await fs.writeFile(`${out}/report.json`, JSON.stringify(report, null, 2));
console.log(JSON.stringify(report));
await browser.close();

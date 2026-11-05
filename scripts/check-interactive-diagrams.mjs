import assert from "node:assert/strict";
import fs from "node:fs/promises";
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE);
const base = process.env.PREVIEW_BASE || "http://127.0.0.1:3000";
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
const checks = [];
for (const width of [1440, 768, 390, 360]) {
  await page.setViewportSize({ width, height: 900 });
  await page.goto(base + "/java/linkedlist", { waitUntil: "networkidle" });
  await page.locator('[data-app-ready="true"]').waitFor();
  const lab = page.locator(".reversal-lab");
  const registers = () => lab.locator("dd").allTextContents();
  assert.deepEqual(await registers(), ["null", "32", "not assigned"]);
  for (let step = 1; step <= 16; step++) {
    await lab.getByRole("button", { name: "Next step", exact: true }).click();
    const processed = Math.floor(step / 4);
    const phase = step % 4;
    const node = (index) => (index < 0 || index > 3 ? "null" : String((index + 1) * 32));
    assert.deepEqual(await registers(), [
      node(processed + (phase >= 3 ? 1 : 0) - 1),
      node(processed),
      node(phase >= 1 ? processed + 1 : processed),
    ]);
    const changed = Math.min(4, processed + (phase >= 2 ? 1 : 0));
    const reversed = [32, 64, 96, 128].slice(0, changed).reverse().join(" to ") || "empty";
    const pending = [32, 64, 96, 128].slice(changed).join(" to ") || "empty";
    assert.equal(
      await lab.getByRole("img").getAttribute("aria-label"),
      `Reversed chain: ${reversed}. Unprocessed chain: ${pending}.`,
    );
  }
  assert.equal(
    await lab.getByRole("button", { name: "Next step", exact: true }).isDisabled(),
    true,
  );
  await lab.getByRole("button", { name: "Previous step", exact: true }).click();
  assert.deepEqual(await registers(), ["128", "128", "null"]);
  await lab.getByRole("button", { name: "One node", exact: true }).click();
  for (let step = 0; step < 4; step++)
    await lab.getByRole("button", { name: "Next step", exact: true }).click();
  assert.deepEqual(await registers(), ["32", "null", "null"]);
  await lab.getByRole("button", { name: "Empty list", exact: true }).click();
  assert.equal(
    await lab.getByRole("button", { name: "Next step", exact: true }).isDisabled(),
    true,
  );
  assert.ok((await lab.getByRole("status").innerText()).includes("loop never runs"));
  await lab
    .getByRole("button", { name: "To allocate a copy of the next node", exact: true })
    .click();
  assert.ok(
    (await lab.getByRole("status").allTextContents()).some((text) => text.includes("Try again.")),
  );
  await lab
    .getByRole("button", { name: "To keep the rest of the list reachable", exact: true })
    .click();
  assert.ok(
    (await lab.getByRole("status").allTextContents()).some((text) => text.includes("Correct.")),
  );
  await lab.getByRole("button", { name: "Four nodes", exact: true }).click();
  await lab.getByRole("button", { name: "Next step", exact: true }).focus();
  await page.keyboard.press("Enter");
  assert.deepEqual(await registers(), ["null", "32", "64"]);
  await lab.getByRole("button", { name: "Next step", exact: true }).click();
  await lab.scrollIntoViewIfNeeded();
  assert.equal(
    await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2),
    false,
  );
  await lab.screenshot({ path: `../../outputs/java-reversal-${width}.png` });
  if (width < 1024) {
    await page.getByRole("button", { name: /Contents ·/ }).click();
    const dialog = page.getByRole("dialog");
    await dialog.getByRole("button", { name: /On this page ·/ }).click();
    await dialog.getByRole("link", { name: /Reverse one link at a time/ }).click();
    await dialog.waitFor({ state: "hidden" });
    await page.waitForFunction(() => document.activeElement?.id === "linked-list-reversal");
  }
  await page.evaluate(() => document.documentElement.classList.add("dark"));
  await lab.screenshot({ path: `../../outputs/java-reversal-dark-${width}.png` });
  await page.evaluate(() => document.documentElement.classList.remove("dark"));
  checks.push({
    width,
    assignments: 16,
    empty: true,
    singleton: true,
    prediction: true,
    keyboard: true,
    noOverflow: true,
  });
}
assert.deepEqual(errors, []);
await fs.writeFile(
  "../../outputs/java-interactive-check.json",
  JSON.stringify({ base, checks, errors }, null, 2),
);
await browser.close();
console.log(JSON.stringify({ checks: checks.length, assignments: 64, errors }));

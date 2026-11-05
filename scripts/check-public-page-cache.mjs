import assert from "node:assert/strict";

const origin = process.argv[2] ?? "https://aitrove.in";
const lesson = `${origin}/java/setup`;
let hit = false;
for (let attempt = 0; attempt < 8; attempt++) {
  const response = await fetch(lesson);
  if (response.ok) {
    const html = await response.text();
    assert.match(html, /<link rel="canonical" href="https:\/\/aitrove\.in\/java\/setup"/);
    hit ||= response.headers.get("x-aitrove-cache") === "HIT";
  }
  if (hit) break;
}
assert.ok(hit, "Public lesson never reached the Worker HTML cache");

for (const path of ["/auth", "/java/setup?q=private"]) {
  const response = await fetch(`${origin}${path}`);
  assert.notEqual(response.headers.get("x-aitrove-cache"), "HIT", `${path} must bypass cache`);
}
console.log("Public HTML cache hit; utility and query requests bypassed.");

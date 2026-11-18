import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import diagrams from "../../src/data/approved-diagrams.json" with { type: "json" };
import downloads from "../../deploy/lightsail/approved-pdfs.json" with { type: "json" };
import states from "../../src/data/pdf-review-status.json" with { type: "json" };
import library from "../../src/data/published-pdf-collections.json" with { type: "json" };
import variants from "../../src/data/jee-main-pdf-papers.json" with { type: "json" };
import faintInkHolds from "../../docs/media-review/faint-ink-holds-2026-11-18.json" with { type: "json" };

const heldHashes = new Set(faintInkHolds.deniedHashes);

const files = new Set(Object.values(library).flat().map(row => row.file));
for (const [paper, editions] of Object.entries(variants)) {
  for (const lang of editions.languages) for (const theme of ["", "-dark"]) {
    files.add("/jee-papers/jee-main/" + paper + "/" + lang + theme + ".pdf");
  }
}
assert.deepEqual(new Set(Object.keys(states)), files);
assert.deepEqual(new Set(Object.keys(downloads)), new Set([...files].filter(path => states[path] !== "held")));
for (const [path, v] of Object.entries(downloads)) {
  assert.match(v.etag, /^[a-f0-9]{32}$/);
  if (v.sha) assert.match(v.sha, /^[a-f0-9]{64}$/);
  assert(["partial", "complete"].includes(states[path]) && (states[path] !== "partial" || v.sha));
}
for (const [path, hash] of Object.entries(diagrams)) {
  assert.match(path, /^\/(jee-figures\/[a-f0-9]{24}|images\/jee-main-reviewed\/[a-f0-9]{64})\.png$/);
  const bytes = readFileSync(new URL("../../public" + path, import.meta.url));
  assert(!heldHashes.has(createHash("sha256").update(bytes).digest("hex")), "Withheld faint-ink figure: " + path);
  assert.equal(createHash(path.startsWith("/images/") ? "sha256" : "md5").update(bytes).digest("hex"), hash, path);
}
console.log("Approved diagrams:", Object.keys(diagrams).length, "PDFs available:", Object.keys(downloads).length, "catalogued editions:", files.size);

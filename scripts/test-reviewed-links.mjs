import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { gunzipSync } from "node:zlib";
import { reviewedHtml } from "../src/lib/reviewed-diagrams.ts";
import { pdfStatus, pdfUrl } from "../src/lib/pdf-status.ts";
import figures from "../src/data/approved-diagrams.json" with { type: "json" };
import pdfs from "../deploy/lightsail/approved-pdfs.json" with { type: "json" };
import status from "../src/data/pdf-review-status.json" with { type: "json" };

for (const [path, hash] of Object.entries(figures)) {
  const html = reviewedHtml(`<img src='${path}?v=old' alt="Figure" />`);
  assert(html.includes(`src="${path}?v=${hash}"`));
  assert.equal(reviewedHtml(html), html);
}
for (const src of ["/jee-figures/unreviewed.png", "https://example.com/figure.png"]) {
  assert.equal(reviewedHtml(`<img src="${src}"/>`), '<span class="jee-figure-pending">Diagram pending review</span>');
}
assert(!reviewedHtml('<img data-src="/other.png">').includes('<img'));
for (const [path, edition] of Object.entries(pdfs)) {
  assert.notEqual(pdfStatus(path), "held");
  assert.equal(pdfUrl(path), path + "?v=" + (edition.sha ?? edition.etag));
}
for (const [path, state] of Object.entries(status)) if (state === "held") assert.equal(pdfUrl(path), undefined);
assert.equal(pdfUrl("constructor"), undefined);
let mockImages = 0;
for (const folder of ["", "archive/"]) {
  const dir = new URL("../src/generated/jee-main-mocks/" + folder, import.meta.url);
  for (const file of readdirSync(dir).filter(name => name.endsWith(".json.gz"))) {
    for (const q of JSON.parse(gunzipSync(readFileSync(new URL(file, dir))))) {
      for (const html of [q.body, ...q.options, q.solution]) {
        for (const [, src] of html.matchAll(/<img\b[^>]*\ssrc="([^"]+)"/g)) {
          const [path, version] = src.split("?v=");
          assert(Object.hasOwn(figures, path));
          assert.equal(version, figures[path]);
          mockImages++;
        }
      }
    }
  }
}
assert(mockImages > 0);
console.log("Reviewed figure and PDF links use current versions; held media has no download link.");

import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { gunzipSync } from "node:zlib";
import {
  correct,
  displayKey,
  selectQuestions,
  summarize,
  performance,
} from "../src/lib/mock-scoring.ts";
import { applyPdfReview } from "../src/lib/jee-main-pdf-review.server.ts";
import { createHash } from "node:crypto";
import figures from "../src/data/approved-diagrams.json" with { type: "json" };
import papers from "../src/data/jee-advanced-papers.json" with { type: "json" };
import ledger from "./jee/advanced-pdf-review.json" with { type: "json" };
const root = new URL("../src/generated/jee-advanced-mocks/", import.meta.url);
let full = 0,
  count = 0,
  images = 0;
const emitted = new Set();
for (const file of readdirSync(root).filter((n) => n.endsWith(".json.gz"))) {
  const [id, n] = file.split(".");
  emitted.add(id);
  const rows = JSON.parse(gunzipSync(readFileSync(new URL(file, root))));
  assert.equal(rows.length, Number(n));
  if (id.startsWith("mixed-")) {
    full++;
    for (const s of ["physics", "chemistry", "mathematics"])
      assert.equal(rows.filter((q) => q.subject === s).length, 20);
    assert(
      rows.every((q) => !q.review && q.solution && !q.solution.includes("jee-figure-pending")),
    );
  } else count += rows.length;
  for (const q of rows) {
    for (const html of [q.body, ...q.options, q.solution]) {
      for (const [, src] of html.matchAll(/<img\b[^>]*\ssrc="([^"]+)"/g)) {
        const [path, version] = src.split("?v=");
        assert.equal(version, figures[path]);
        assert(version);
        images++;
      }
    }
    if (q.review) assert.equal(correct(q, "0"), false);
    else {
      const key = q.options.length
        ? (q.choiceKeys ?? [q.choiceKey]).join(",")
        : String(q.numericRange?.[0] ?? q.numericKey);
      assert.equal(correct(q, key), true);
      assert.equal(correct(q, ""), false);
    }
  }
}
for (const p of papers) assert(emitted.has(p.slug));
assert.equal(count, 3962);
assert(full >= 1 && images >= 16);
const multi = { options: ["A", "B", "C", "D"], choiceKeys: [0, 3] };
assert(correct(multi, "0,3"));
assert(!correct(multi, "0"));
assert(!correct(multi, "0,1,3"));
assert.equal(displayKey(multi), "A, D");
const numeric = { options: [], numericRange: [1.38, 1.39] };
assert(correct(numeric, "1.385"));
assert(!correct(numeric, "1.4"));
assert(!correct(numeric, "1.38garbage"));
assert(!correct({ ...numeric, review: "Answer key conflict" }, "1.385"));
// Reports and scored-only attempts must use the same grading and original numbering.
const sample = [
  { options: ["A", "B"], choiceKey: 0 },
  { options: ["A", "B"], review: "Answer key unavailable" },
  multi,
  numeric,
];
assert.deepEqual(
  selectQuestions(sample, true).map((q) => q.number),
  [1, 3, 4],
);
assert.equal(selectQuestions(sample, false).length, 4);
assert.deepEqual(summarize(sample, ["0", "0", "0", ""]), {
  graded: 3,
  hits: 1,
  misses: 1,
  score: 3,
  max: 12,
  skipped: 1,
  review: 1,
  readiness: 25,
});
assert.deepEqual(summarize([sample[1]], ["0"]), {
  graded: 0,
  hits: 0,
  misses: 0,
  score: 0,
  max: 0,
  skipped: 0,
  review: 1,
  readiness: null,
});
assert.equal(summarize([sample[0]], ["1"]).score, -1);
assert.equal(summarize([sample[0]], ["1"]).readiness, 0);
assert.equal(summarize([sample[0]], [""]).readiness, 0);
assert.equal(summarize([multi, numeric], ["0,3", "1.385"]).readiness, 100);
let checked = 0;
for (const f of readdirSync(new URL("../public/jee-advanced-archive/q/", import.meta.url))) {
  const rows = JSON.parse(
    gunzipSync(readFileSync(new URL("../public/jee-advanced-archive/q/" + f, import.meta.url))),
  );
  for (const q of Object.values(rows)) {
    // Python's evidence hash includes spaces between array elements.
    const payload =
      "[" +
      JSON.stringify(q.body) +
      ", [" +
      q.options.map((o) => JSON.stringify(o)).join(", ") +
      "]]";
    const evidence = ledger[createHash("sha256").update(payload).digest("hex")];
    if (!evidence) continue;
    const patched = await applyPdfReview(q, "jee-advanced");
    if (evidence.hold) {
      assert(patched.keyConflict);
      for (const k of ["choiceKey", "choiceKeys", "numericKey", "numericRange"])
        assert.equal(patched[k], undefined);
    } else {
      if (evidence.key)
        for (const [k, v] of Object.entries(evidence.key))
          assert.deepEqual(patched.englishKey[k], v);
      if (evidence.contentCorrection) {
        assert.equal(patched.solution, "");
        assert.deepEqual(patched.options, evidence.contentCorrection.replacement.options);
        assert.equal(patched.body, evidence.contentCorrection.replacement.body);
        assert.equal(q.body, evidence.contentCorrection.originalBody);
      }
      for (const fig of evidence.figures ?? [])
        assert([patched.body, ...patched.options].join("").includes(fig.path));
    }
    assert.deepEqual(patched.hi, q.hi);
    checked++;
  }
}
assert(checked >= Object.keys(ledger).length);
console.log(
  `Advanced: ${count} archive questions, ${full} mixed mocks, ${checked} canonical/alias patches, reviewed media and grading passed.`,
);

const metrics = performance(sample, ["0", "0", "0", ""]);
assert.equal(metrics.accuracy, 50);
assert.equal(metrics.attemptRate, 67);
assert.equal(metrics.earned, 4);
assert.equal(metrics.penalty, 1);
assert.equal(metrics.attempted, 2);
assert.equal(performance([sample[1]], ["0"]).accuracy, null);
assert.equal(performance([sample[1]], ["0"]).attemptRate, null);
assert.equal(performance([sample[0]], [""]).accuracy, null);
assert.equal(performance([sample[0]], [""]).attemptRate, 0);

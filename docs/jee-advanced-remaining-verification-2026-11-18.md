# JEE Advanced PDF recovery verification — 2026-11-18

The second recovery adds 325 printed keys and 81 clean prompt diagrams. It makes 331 more questions scorable: **2,145 / 3,962**. All 79 paper attempts remain available, and the balanced mixed library grows from 12 to 14 mocks.

The application applies the evidence ledger to original database/archive questions at read time. S3 holds the images and recovery backups; the compiled reader and mock assets ship with the Node app. Source IDs and raw answer semantics are retained. Rebuilt mock assets receive new content hashes so saved attempts against an older edition are not silently regraded.

## Validation

- TypeScript, 19 education checks, seven Cloudflare media/cache checks, approved-media/link checks and full archive grading checks pass.
- Every recovered key is tied to a PDF hash, question number, original content hash and printed key. All canonical/alias patches are checked, including unchanged Hindi content and held conflicts.
- The MathJax paint-order helper has self-checks for simple/indexed/nested roots, nested SVG fences, invisible function application and malformed markup. Six printed question/key pairs were visually inspected.
- All 81 new diagram renders passed paired visual review, native-resolution OCR and contrast inspection. Eleven candidates failed publication review.
- All 181 uploaded S3 objects were checked against the upload ETag. Objects include 81 diagrams, 97 mock/set files and reader/stats/evidence backups.
- Full production build, TypeScript and both JEE archive verifiers passed.
- Application commit `59d01118` deployed with a health-checked Lightsail cutover. Caddy and Node services are active. Cloudflare production version: `648c67b3-eb40-447d-9c96-e2bae22bc112`; preview version: `dca7dc1d-2598-4d4e-b351-464174dffd9d`.
- Preview and production each passed 104 HTTP checks: 20 pages, all 81 new diagram bytes, and three concurrent complete PDFs (6,940,046 bytes total, reviewed-edition hashes matched). S3-only papers are checked through Cloudflare, not the local disk-only preview.
- All 97 live mock/paper/extra assets downloaded and matched the production build byte-for-byte (8,507,535 bytes).
- At 390px mobile width, the restored 2018 circuit question accepted B + D, loaded the clean 845px diagram at 363px display width, and had no horizontal overflow.
- Live Mixed mock 14 accepted D on its first question and reported 4 / 240, one correct, 59 skipped and zero ungraded. The downloaded 1,609,464-byte HTML report contains all 60 questions, four embedded images, inline math glyphs and no competitor text.
- Published sitemap: 11 child maps, 23,766 unique URLs, 35 canonical/indexability samples passed. Private attempt URLs and excluded paper views remain outside the index.
- The temporary deployment SSH rule was removed; the original single-IP allowlist is retained. No plan upgrades.
- Live machine-readable evidence: `docs/media-review/jee-advanced-remaining-live-2026-11-18.json`.

## Remaining

| Reason | Questions |
| --- | ---: |
| Usable key needed | 1,157 |
| Prompt/option diagram needed | 463 |
| Both needed | 191 |
| Conflicting keys | 6 |
| Total | 1,817 |

Separately, solution diagrams remain pending for 1,051 questions (496 otherwise scorable). Printed written-response keys and disjoint numerical values are not forced into a single-answer/range grader. A key match verifies transcription against the supplied PDF, not independent academic correctness. No claim of exhaustive manual review of every pixel in every supplied PDF is made.

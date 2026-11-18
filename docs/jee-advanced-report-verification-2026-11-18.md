# Advanced recovery and performance-report release

Implemented November 18; live verification completed November 19, 2026 (IST).
Application commit: `14edb5fe`.

## Recovery

Baseline: 2,295 scorable of 3,962; 1,667 pending.
Result: **2,337 scorable**, **1,625 pending**. Recovered 14 missing keys and
28 questions' prompt diagrams (27 unique images). All 42 became scorable.
The builder now produces 16 balanced mixed mocks (960 positions), 79 paper
sets and four extra chapter sets: 99 downloadable mock assets in total.

| Remaining reason | Questions |
|---|---:|
| Key only | 1,056 |
| Required diagram only | 372 |
| Both key and required diagram | 191 |
| Conflicting or unsupported alternative key sets | 6 |

Full official questions and all options were compared manually before approval.
PDF URL, SHA-256, page, printed number, key mapping or crop coordinates are in
[the evidence ledger](media-review/jee-advanced-report-2026-11-18.json).
The [official archive](https://jeeadv.ac.in/archive.html) supplies the source papers.
OCR locates candidates; it does not decide answers. Crops preserve the official
PDF pixels. Every new image was inspected normally and with 24x faint-ink
amplification, then checked using local full-resolution OCR. No competitor
branding was found in the new crops; no watermark was erased or covered.

Two already-unscored questions were explicitly held: 2013 Paper 2 Q3 accepts
ABCD OR BCD, and 2011 Paper 2 Q32 accepts A OR AC. The current single-set
grader cannot represent these alternatives fairly. Their archived keys were
not replaced with a guess. Raw archive records and Hindi remain unchanged.

The user-supplied PDFs were rechecked against current hashes and keys. Remaining
candidates included 116 image-option cases needing option mapping, 49 text-option
mismatches, 29 stem-math mismatches, seven option-math mismatches, and seven
otherwise matching text cases with unresolved mathematical/order ambiguity.
No new key was approved solely from those automatic matches. This is a verified
additional batch, not a claim that all 1,625 cases have been exhausted.

## Reports

The shared JEE Main/Advanced result component exports only its performance card.
The website retains the complete question and solution review. The download
embeds the DekhoExams wordmark and includes score, score percentage, accuracy,
attempt rate, correct/incorrect/skipped counts, scorable attempts, earned marks,
deducted marks, subject breakdowns and a data-based next practice step.
It does not estimate rank, admission or selection probability.

Both Download report (offline HTML) and Print / Save PDF use the same restricted
card. The export only accepts the same-origin brand logo; it no longer fetches
question images or math sprites. Report content has no external dependencies.
The printed sample was rendered and visually inspected as one A4 page with the
footer intact. Longer test names or browser print settings can affect pagination.

## Validation and deployment

- Production build, TypeScript, grading/KPI assertions, official correction
  guards, archive verification, 19 education checks and seven edge tests passed.
- `scripts/test-mock-report.browser.js` exercised the actual download on live
  JEE Advanced and Main results: eight KPI tiles, one embedded logo and no
  question, answer, option or solution elements. A zero-attempt Main result
  correctly displays unavailable accuracy and 0% attempt rate.
- Advanced live attempt: 4/240; 60 question reviews remained online. At a
  390px mobile viewport the report had no horizontal page overflow.
- Mumbai public-URL verification passed 176 checks: 99 mock assets, 27 unique
  diagrams, 47 pages and three complete PDFs. Binary files matched expected
  hashes. The three concurrent PDFs were 1,949,674, 2,723,410 and 2,266,962 bytes.
- Local command-line checks encountered intermittent resets/timeouts; an initial
  default Python request from Mumbai received 403. Repeating from Mumbai with
  the release-verification user agent passed all 176 checks. This is functional
  release verification, not a global availability or load-test guarantee.
- All 11 sitemap children passed, covering 23,767 unique URLs; sampled
  canonicals/indexability and excluded duplicate paper views were verified.
- Existing S3 bucket: 138 uploaded objects, 21,082,398 bytes, with ETag verification.
  Diagrams use their existing public media prefix. Recovery evidence, mock data
  and source PDFs are backed up under `content/jee-advanced/recovery/2026-11-18-report/`.
- Lightsail app and Caddy were active after health-checked cutover. No instance,
  database or hosting-plan upgrade. Origin check: HTTP 200; temporary deployment
  SSH access was removed afterward.
- Cloudflare production: `3a5325c7-0502-4216-8305-1efd32882211`.
  Preview: `0fbc6ff8-78d4-4435-a8f1-ced326a3e28c`; edge cache version `v21`.

Detailed successful checks: [live verification JSON](media-review/jee-advanced-report-live-2026-11-18.json).

Live: [Advanced mocks](https://dekhoexams.com/questions/jee-advanced/mock-tests),
[Main mocks](https://dekhoexams.com/questions/jee-main/mock-tests).

# JEE Advanced PDF recovery verification — 2026-11-18

The second recovery adds 325 printed keys and 81 clean prompt diagrams. It makes 331 more questions scorable: **2,145 / 3,962**. All 79 paper attempts remain available, and the balanced mixed library grows from 12 to 14 mocks.

The application applies the evidence ledger to original database/archive questions at read time. S3 holds the images and recovery backups; the compiled reader and mock assets ship with the Node app. Source IDs and raw answer semantics are retained. Rebuilt mock assets receive new content hashes so saved attempts against an older edition are not silently regraded.

## Validation

- TypeScript, 19 education checks, seven Cloudflare media/cache checks, approved-media/link checks and full archive grading checks pass.
- Every recovered key is tied to a PDF hash, question number, original content hash and printed key. All canonical/alias patches are checked, including unchanged Hindi content and held conflicts.
- The MathJax paint-order helper has self-checks for simple/indexed/nested roots, nested SVG fences, invisible function application and malformed markup. Six printed question/key pairs were visually inspected.
- All 81 new diagram renders passed paired visual review, native-resolution OCR and contrast inspection. Eleven candidates failed publication review.
- All 181 uploaded S3 objects were checked against the upload ETag. Objects include 81 diagrams, 97 mock/set files and reader/stats/evidence backups.
- Production build and live checks: pending at the time of this implementation commit; appended after deployment.

## Remaining

| Reason | Questions |
| --- | ---: |
| Usable key needed | 1,157 |
| Prompt/option diagram needed | 463 |
| Both needed | 191 |
| Conflicting keys | 6 |
| Total | 1,817 |

Separately, solution diagrams remain pending for 1,051 questions (496 otherwise scorable). Printed written-response keys and disjoint numerical values are not forced into a single-answer/range grader. A key match verifies transcription against the supplied PDF, not independent academic correctness. No claim of exhaustive manual review of every pixel in every supplied PDF is made.

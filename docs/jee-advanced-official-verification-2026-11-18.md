# JEE Advanced official-paper recovery verification — 2026-11-18

Published application commit `02c0ac2d` to main, the existing Lightsail Node app and Cloudflare version `c6fd945d-97ad-4de4-a5ab-38b227f4fad2` (edge cache v19).

## Recovery

65 more distinct questions are scorable: **2,214 / 3,962**. This pass adds 26 missing keys, resolves four previous conflicts and restores 37 clean diagrams. One newly discovered alternative-answer conflict remains held. Evidence and official source hashes are in `media-review/jee-advanced-official-2026-11-18.json`.

The official archive supplied 38 PDFs (2007–2025). Native-text searches covered 16 PDFs; OCR covered 85 scanned pages in three older papers. Every accepted key was checked against question text, mathematical expressions, option order and the printed official key. Exact old-key assertions and official evidence are required to supersede archived English keys. Raw records and Hindi keys remain unchanged.

All 37 published diagrams passed normal visual inspection, contrast diagnostics and full-resolution local OCR. They preserve official PDF pixels; no watermark erasure or diagram invention.

## Verification

- Production build, TypeScript, 19 education checks, seven edge checks, archive/mock grading, approved media and the new official correction guards passed.
- 110 live HTTP checks passed, including changed question pages, all 37 new diagram hashes, and three simultaneous complete paper PDF downloads with expected hashes.
- All 97 live mock/set files matched the build byte-for-byte: 8,517,684 bytes. The library has 14 mixed mocks, 79 papers and four extra sets.
- At 390px mobile width, restored probability key A was accepted. The corrected neutron answer 4 was accepted and old 3 rejected. Rope-wave AD was accepted and old ABD rejected; its clean diagram loaded without overflow.
- Live 2025 Paper 1 offered 40 scorable questions, excluding eight awaiting verification. Submitting A for its first question produced 4 / 160, one correct and 39 skipped. All 40 question review headings were present; all 15 diagram images decoded successfully, 1,301 inline SVGs were present and there was no horizontal overflow. Download/print controls were present; the report file was not downloaded again during this pass.
- The sitemap index and all 11 child maps passed unique URL and sampled canonical/indexability checks: 23,767 unique URLs.
- 176 private S3 uploads were verified against their ETags: 138,081,457 bytes including diagrams, mock assets, reader/stats/evidence, audit and official PDF sources. Recovery backup prefix: `content/jee-advanced/recovery/2026-11-18-official/`; images: `jee-figures/`.
- Node and Caddy services were active after the health-checked deployment. Temporary deployment SSH access was removed. Existing 1 GB app and MySQL plans retained.
- Machine-readable live evidence: `media-review/jee-advanced-official-live-2026-11-18.json`.

## Remaining

| Reason | Questions |
| --- | ---: |
| Usable answer key needed | 1,129 |
| Prompt or option diagram needed | 424 |
| Both needed | 191 |
| Conflicting keys | 4 |
| Total | 1,748 |

Remaining records have not all received exhaustive manual official-PDF review. Unclear matches, incomplete formulas, unsupported written answers, disjoint numerical values and alternative answer sets were not guessed or forced into the current grader. Pending solution diagrams are separate from prompt/option eligibility. Visual/OCR checks cover this release's 37 images, not a fresh whole-site watermark certification. Official-source matching verifies transcription, not independent re-solving of each question.

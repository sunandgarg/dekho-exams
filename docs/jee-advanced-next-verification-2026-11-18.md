# JEE Advanced older official-paper recovery — 2026-11-18

## Recovery

81 more distinct questions can be scored: **2,295 / 3,962**, up from 2,214. Added 59 missing answer keys and 22 diagram patches using 20 distinct official-paper crops. There are now 15 mixed mocks with 900 questions, 79 paper sets and four extra sets.

The official archive supplied the source papers. This pass extends OCR to 568 pages in 21 PDFs, locating 335 candidate matches. Supplied branded-PDF candidates were reclassified too. Neither text similarity nor OCR alone approves a record: complete official questions, formulae, options and printed keys were compared before making explicit hash-bound corrections. One official option permutation was preserved. Raw archive and Hindi records remain unchanged.

Each accepted image was inspected normally, with amplified faint ink, and with full-resolution local OCR. Crops retain original official PDF pixels. No watermark erasure, invented diagrams, inferred keys or independent answer solving was used. Source URLs, page/question references, PDF SHA-256 values, option mappings and crop coordinates are in `media-review/jee-advanced-next-2026-11-18.json`.

## Remaining

| Reason | Questions |
| --- | ---: |
| Answer key needed | 1,070 |
| Prompt/option diagram needed | 402 |
| Both needed | 191 |
| Conflicting keys | 4 |
| Total | 1,667 |

Unresolved items include picture-only option mappings, formula/paragraph discrepancies and unsupported alternative answer sets. For example, an archived 2011 option uses CoCl2 where the official paper uses CoCl4. These are held rather than scored by a nearby prose match. The remaining questions have not all received exhaustive manual review. Pending solution illustrations are separate from prompt/option eligibility. Watermark screening covers this release's new images, not a fresh certification of every image on the website.

## Verification

- Production Node build, TypeScript, 19 education checks, seven edge tests, archive/mock checks, approved media, official-correction guards and 81 new hash-bound patch checks passed.
- S3 upload verification passed for 136 writes (39,130,048 bytes), including the 20 unique images, rebuilt mock assets, reader/stats, review ledger, audit and 12 official source PDFs. Recovery prefix: `content/jee-advanced/recovery/2026-11-18-next/`.
- Live deployment checks are pending at this commit.

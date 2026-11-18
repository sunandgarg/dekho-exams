# JEE Advanced recovery release · 19 November 2026

The 94 verified recoveries are published on dekhoexams.com from commit `9226b288a312c1e345dae3a001afad1a0d4c80bb`. The existing Mumbai 1 GB Lightsail app and 1 GB managed MySQL plans are unchanged; approved media continues to come from private S3 through Cloudflare.

## Published content

- 2,875 of 3,962 distinct questions are scorable, up 94.
- Recovered 67 printed answer keys and published 94 clean official diagram crops for 46 questions. Complete questions, formulas, passages and option mappings were checked. Images passed normal visual inspection, amplified-contrast inspection and OCR. No inferred answers or watermark removal.
- 22 mixed mocks (1,320 questions), 79 paper attempts and four extra sets.
- Remaining 1,087: 984 need keys, 47 need prompt/option diagrams, 48 need both, and eight have conflicting keys. The missing-key categories include 616 written-response and 161 fill-in records without supported automatic scoring keys.
- Raw archive records, stable URLs, Hindi keys and practice marking rules are unchanged.

## Verification

Production build, TypeScript, archive grading/correction guards, 19 education tests, seven edge tests and reviewed-media checks passed. All 232 S3 recovery objects were verified. The preview passed 11 checks before the public Worker was updated.

All 297 production checks passed: 94 affected question pages, 94 new image files, 105 mock/paper payloads, three complete PDF downloads and the mock library. Asset checks compared bytes with local hashes. Requests used a maximum concurrency of three.

At a 390px mobile viewport, the restored ray-diagram question loaded all four options, graded option C correctly and displayed its solution without horizontal overflow. Mixed mock 22 submitted with 60 answer-review cards; one verified A,D answer scored +4. Its report download contained eight KPIs and one embedded DekhoExams logo, with no question or answer content. Eleven sitemap files contained 23,772 unique URLs; sampled canonicals and indexability exclusions passed.

The app and Caddy remained active after testing; 311 MiB of memory was available. Temporary deployment SSH access was removed. These checks do not certify production capacity or independently re-solve the printed answer keys.

## Live pages and evidence

- [JEE Advanced mock library](https://dekhoexams.com/questions/jee-advanced/mock-tests)
- [Recovered ray-diagram question](https://dekhoexams.com/past-years/jee/question/pfor-light-incident-from-air-on-a-meta-material-the-appro-jee-advanced-physics-units-and-measurements-6ydfrsoellybedhv)
- [Recovery evidence](media-review/jee-advanced-next-2026-11-19.json)
- [Full live verification, versions and hashes](media-review/jee-advanced-next-live-2026-11-19.json)

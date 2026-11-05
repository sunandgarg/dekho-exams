# Pencil2Pen Implementation Status

Updated 2026-10-17. The frontend is serving from Cloudflare at https://pencil2pen.com/ as a noindex preview. This is not a full SelfStudys/Khan Academy content library or a traffic-ready production launch. No GitHub push, bulk textbook import or automatic traffic-generation service was performed.

## Hosting Preview

- Public preview: https://pencil2pen.com/ (`pencil2pen-frontend` Worker in the Javapaathshala Cloudflare account). `www.pencil2pen.com` is also bound to the Worker. Hostinger registrar nameservers are `marjory.ns.cloudflare.com` and `skip.ns.cloudflare.com`; Cloudflare reports the zone active. On October 17, direct HTTPS checks returned 200 for the homepage, Class 1, subject and chapter routes with the new content. `robots.txt` disallows crawling, pages emit `noindex`, and preview sitemaps have no URLs.
- Separate Hostinger Premium WordPress install: https://cms.pencil2pen.com/wp-admin/ (`Pencil2Pen CMS`). HTTPS and the standard WordPress REST API respond; the editorial site emits `noindex, nofollow`. The existing AITrove WordPress site was not modified.
- WordPress is **not connected to the student frontend yet**. The frontend's existing CMS client expects an AITrove-specific API plugin, while the new install has only standard WordPress REST. Do not point `WORDPRESS_URL` at the new CMS until a Pencil2Pen content contract and publishing workflow are implemented and tested.
- The account has a 25 GB Hostinger Premium allocation; Cloudflare Workers remains on Free for preview only. Neither 1 million daily visits nor launch capacity has been load-tested or approved. Production requires a paid-capacity decision, reviewed content, cache/load testing, a safe CMS integration, analytics/monitoring, and a controlled change from noindex to indexable pages.

Content inventory, state-grade planning matrix and phased publishing plan: `PENPENCIL-CONTENT-ROADMAP.md`.

## Implemented In This Pass

- Original local book-badge PNG artwork for Classes 1-12 and all 13 languages, with native-script labels. Source generator and provenance notes are included; images use fixed dimensions and lazy loading. These are navigation artwork, not new lessons or translations.

- Existing shell, typography and mobile navigation retained. User-requested visual refresh replaces pastels with cobalt, emerald, amber, coral, berry and charcoal accents in light/dark themes. Six broader top shortcuts replace 17 tiles without removing category routes.
- Three-row horizontally scrolling subject directory between Explore Pencil2Pen and Classes 1-12: 16 homepage dropdowns and 281 course choices, consistent-size original icons, keyboard controls, inert collapsed panels, responsive layout, accordion/hover animations and reduced-motion CSS. The two removed homepage groups remain as registered routes. Course selections disclose missing local lessons and offer labelled external Khan Academy links; no course content was copied.
- All requested categories: NCERT Books & Solutions, State Books, Books & Solutions, CBSE, CISCE (ICSE/ISC), JEE, NEET, CUET, CAT, GATE (once), Scholarships & Awards, NDA, CLAT, UG, PG, CA and UPSC. NIOS and subject/resource directories are also included.
- Classes 1-12, actual subject/chapter paths, 22 state/territory directories and 13 NCERT language availability directories: English, Hindi, Kannada, Tamil, Telugu, Marathi, Bengali, Gujarati, Malayalam, Odia, Punjabi, Assamese and Urdu. This does not cover every Indian state and union territory.
- 2,338 registered catalog routes, 14 original English starter lessons and 88 one-hop aliases for legacy links. Class pages now show board/book choices and subjects first; board/class and subject pages expose chapters where original lessons exist. Lessons show a Book panel with an official NCERT source link and an explicit warning where textbook/edition mapping is unverified. Route count is NOT a count of published educational resources; no school resource is reviewed or indexable yet.
- Internal-page copy now uses short, subject-aware study habits and realistic slips rather than a repeated three-step checklist. Class choices lead before advice, empty chapter lists offer a useful next action, lesson counts use correct singular/plural, and the redundant class-index tab strip is removed. No fake student activity or invented curriculum was added.
- Central resource IDs, canonical ownership, navigational parents, breadcrumbs, SSR metadata/JSON-LD, real unknown-route 404s, sitemap exclusions and build-time catalog checks. Future route policy and editorial requirements documented in SITE-ARCHITECTURE.md and AGENTS.md.
- Catalog search across lessons and collections; class filter for available lessons; clear no-result state. No fake translated results.
- Browser-only saved lessons, recently opened lessons, persisted self-check answers, explained feedback, reset and mistake-review list. Invalid storage is rejected; storage failures are reported rather than silently claiming a save.
- Official-source links where verified. No competitor content or textbook PDF mirrored. Empty collections disclose the gap and remain noindex, including when global preview is disabled.

## Explicitly Remaining

| Blueprint workstream | Current limit / next required work |
| --- | --- |
| Complete Classes 1-12 curriculum | Only 14 starter lessons and 28 questions exist. Commission/author and academically review all subject/chapter coverage. General lessons are not asserted to match a board's current syllabus. |
| NCERT books, notes, solutions, exemplar, syllabus | Collection/class routing exists. Book inventories, edition/chapter/exercise mapping, reviewed original solutions and approved files are not populated. |
| State books and reference-book solutions | State/publisher directories exist; verified textbook editions, rights, language records and original solutions must be supplied. |
| Regional-language education | Availability directories exist, not translated curricula. Recruit reviewers and publish genuine language equivalents before hreflang or multilingual search. |
| CBSE/CISCE/NIOS coverage | Board/class discovery exists. Session-specific syllabi, competency questions, marking schemes, practical/lab resources and board alignment remain. |
| JEE/NEET/CUET/CAT/GATE/NDA/CLAT/CA/UPSC | Directories exist. No exam-specific course, paper bank, subject/chapter tree, mock test, score predictor, eligibility calendar or coaching claims are represented as complete. |
| UG/PG | Entrance discovery exists. Degree/course/university-specific content and separate CUET UG/PG material remain. |
| Scholarships and awards | Official portal link exists. Verify each individual opportunity, eligibility, deadline and update cadence before publishing listings. |
| Downloads and document readers | No school PDFs hosted. Need licence clearance, file ingestion/storage/CDN, accessible reader, integrity checks, versioning and download events. |
| Assessment engine | Current 2-question self-checks are not formal tests. Need question bank, stable question versions, test blueprints, timer/recovery, marking/negative-marking rules, server-scored attempts and result/mistake history. |
| Student accounts | No authenticated school accounts or cross-device progress. Need identity, secure persistence, authorization, recovery/deletion, child-appropriate consent and retention controls. |
| Retention | Saved/recent/current wrong-answer review works locally. Goals, revision schedules, streaks, mastery, spaced repetition, reminders and offline/PWA support remain. |
| School CMS and editorial roles | Legacy WordPress code is preserved, but the school catalog is not connected to it. Need relational entities, migration, validators, permissions, academic/language reviews, correction queue, audits and publication controls. |
| Trust and legal | Need real responsible publisher/contact, verified author/reviewer profiles, content/correction policy, licence register, accessibility statement, and jurisdiction-specific legal review. Current privacy page describes preview behavior only. |
| Teacher distribution | Worksheet builder, printable/shareable packs, teacher dashboards, classroom assignments and properly attributed partner distribution remain. |
| Extra resource types | Worksheets, sample/PYQ papers, important questions, formulas and flashcard collections are not populated. Chapter tabs must not advertise nonexistent notes/solutions/videos/downloads. |
| Tools, guidance and news | Study planner, calculators, dictionaries, career/study guides, current affairs and updates are not built. Add only with useful original content and a maintenance owner. |
| AI help/community | Not built. Need bounded sources, quality evaluation, child safety, privacy, abuse controls and moderation before exposing chat or user publishing. |
| Conversion and monetization | No analytics, lead collection, email subscriptions, payments, ads or affiliate offers enabled. Define conversion events (lesson start, completion, return, save) and consent/measurement before optimizing. No fake counters or forced signup. |
| Search at scale | Current catalog is a small in-process search. Need indexed CMS search with class/board/subject/language/resource filters, ranking, typo tolerance and pagination for a large library. |
| Production hosting | The Cloudflare Worker is live on root/www, and the separate Hostinger CMS remains reachable. Need content integration, cache strategy, deploy/rollback, secrets and capacity plan. Do not reuse AITrove production accidentally. |
| Scale and reliability | No million-visitor load validation. Need CDN/cache testing, search/DB indexes, queues, rate limits, WAF, monitoring, error budgets, backup/restore and load tests. Inherited CMS template client chunk remains large. |
| SEO launch and measurement | Verify domain in Search Console, approve indexed content, submit sitemap, measure indexing/CWV/engagement and audit live crawl behavior. Live production CMS sitemap pagination and CDN behavior still need staging tests. |
| Growth | One million visits per day is not guaranteed by these changes. Requires a large trusted content library, strong repeat use, earned distribution and measured demand. No ranking or traffic results are claimed. |

## Next Practical Batch

1. Choose one complete launch cohort, such as Class 10 Maths in English and Hindi, and confirm curriculum/session/book editions and rights.
2. Build the school CMS publishing workflow and publish reviewed chapter resources through the route contract, including source/reviewer evidence.
3. Populate a quality-checked question bank and formal assessment service if full tests are wanted.
4. Set up separate staging/production hosting, privacy-aware measurement and Search Console; load-test before expanding.

## Verification Record

Homepage directory update: 16 groups appear in a three-row horizontal carousel; Beyond the Classroom and For Educators are absent from homepage SSR and browser DOM. The old group routes remain registered. The detailed content inventory and phased plan are in `PENPENCIL-CONTENT-ROADMAP.md`.

Artwork update: 11 catalog/HTTP tests pass, including coverage and 192px PNG dimension checks for all 25 badges. The homepage includes all image references and all 25 asset URLs return image/png successfully. Production build, TypeScript and homepage ESLint pass. The long-running dev server was restarted after stalled requests; it remains available at http://127.0.0.1:3001/. Saved artwork was visually inspected for correct numeral/script rendering, and the browser verified all 25 images loaded and no badge-container overflow at a 375px CSS viewport.

The latest local HTTP suite passed 20 tests across all 2,338 catalog routes, checking 200 responses, headings, pencil2pen.com canonicals, preview noindex, 88 aliases, 404s, empty preview sitemaps and the new internal-page copy. Class index, Class 1 board/subject rails and English subject copy were checked in the browser at mobile width; the chapter Book panel was checked in the browser in the previous pass. The three-row homepage carousel was previously checked on mobile. Academic accuracy, copyright permissions, live production capacity and real-world Core Web Vitals have NOT been certified by these software tests.

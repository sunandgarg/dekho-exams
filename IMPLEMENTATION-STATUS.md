# Dekhoexams Implementation Status

## JEE Advanced archive (2026-11-08)

- The chapter directory covers 81 chapters and 3,959 questions in Physics, Chemistry and Mathematics. The 79-paper directory spans 1978–2026 and contains 3,920 paper positions. 3,919 link to their matching chapter question. One IIT-JEE 1987 question is available only through its paper.
- All 3,960 distinct questions have English and Hindi editions and an explanation. The reader and print editions retain the common passage for all 284 passage questions. The archive includes single and multiple correct, numerical, written-response, fill-in-the-blank and true/false questions.
- Every chapter and paper has printable English and Hindi Dekhoexams editions with optional solutions. PDF catalogs, practice links, print assets and approved figures stay on Dekhoexams. Unverified figures are marked in place. Paper identifiers are unchanged; the 32 JEE Main question URLs that contained a vendor name redirect to their new canonical URLs. Across both exams, 2,943 distinct questions have a pending diagram in a prompt or option in at least one language; another 3,302 have a pending diagram only in a solution. Full coverage reports are stored in `docs/jee-main/coverage.json` and `docs/jee-advanced/coverage.json`.

## JEE Main archive (2026-11-09)

- The chapter directory has Physics, Chemistry and Mathematics, 95 chapters and 18,006 question listings. Chapter pages preserve question types, historical counts and annual weightages. The year-wise archive contains 202 papers and 15,282 paper positions, ordered by subject. Chapter and paper totals overlap.
- All 18,006 questions have English detail and explanation records; all 18,006 also have Hindi editions, including two questions whose prompts, choices and solutions are notation-only. Automatic grading supports explicit single and multiple choice keys, numerical keys and published numerical ranges. Question readers retain the canonical chapter slug, the paper-specific ID, options, mathematical notation, available English/Hindi editions and published explanations. Grading uses the published keys. Bookmarks are local to the browser.
- The PDF catalog offers 152 static Dekhoexams paper PDFs from the supplied 2025/2026 batch (38 shifts × 2 languages × 2 themes, 75 questions per shift). The six unlisted answer-key entries are identified in the menu and release manifest. Five paper positions have a pending figure in the affected downloads. Matching the reviewed diagrams to the question archive resolved all pending prompt and option figures for 452 additional JEE Main questions; 2,199 still have at least one pending prompt figure across the full Main archive. The catalog also contains 594 printable Dekhoexams editions: 297 English and 297 Hindi. It does not offer third-party downloads. The print verifier checks every chapter and paper for external image URLs and competing publisher names. The JEE dataset is versioned on GitHub and served by Cloudflare; it is separate from the Hostinger WordPress lesson editor. The public search release includes the homepage, JEE directories and complete canonical questions. Duplicate paper views, print editions, unverified questions and noncanonical hosts remain excluded.
- Coverage checks: `npm run test:education` checks the chapter order against the directory; `python3 scripts/jee/verify.py` checks every question, neighbor, paper association and mathematical glyph.

## Dekhoexams migration (2026-11-06)

- Removed the Supabase client, auth middleware, Lovable project metadata and build packages. The public frontend still uses local browser progress; student login remains unavailable.
- Created a separate Hostinger WordPress install at `https://cms.dekhoexams.com`, activated the School content plugin and published `pp-0001` through its public API. The frontend fetches published lesson text with validated local fallback; the other 13 lessons remain in code. The existing `cms.pencil2pen.com` remains untouched.
- Added local exam logo assets for 27 of 29 exams, with source URLs in `src/data/exam-logo-sources.json`. IAT and ICSE Class 10 still use text badges because no verified source image was found.
- `dekhoexams.com` was purchased at Hostinger and delegated to Cloudflare (`adam.ns.cloudflare.com`, `chin.ns.cloudflare.com`). The existing `dekhoexams-frontend` Worker is bound to the apex and www; www redirects to the apex. Cloudflare's DNS-only `cms` A record points to the separate Hostinger WordPress install. Keep preview `noindex` until the user approves an indexed launch.

Updated 2026-10-17. The frontend is serving from Cloudflare at https://pencil2pen.com/ as a noindex preview. This is not a full SelfStudys/Khan Academy content library or a traffic-ready production launch. No GitHub push, bulk textbook import or automatic traffic-generation service was performed.

## Hosting Preview

- Public preview: https://pencil2pen.com/ (`pencil2pen-frontend` Worker in the Javapaathshala Cloudflare account). `www.pencil2pen.com` is also bound to the Worker. Hostinger registrar nameservers are `marjory.ns.cloudflare.com` and `skip.ns.cloudflare.com`; Cloudflare reports the zone active. On October 17, direct HTTPS checks returned 200 for the homepage, Class 1, subject and chapter routes with the new content. `robots.txt` disallows crawling, pages emit `noindex`, and preview sitemaps have no URLs.
- Separate Hostinger Premium WordPress install: https://cms.pencil2pen.com/wp-admin/ (`Dekhoexams CMS`). HTTPS and the standard WordPress REST API respond; the editorial site emits `noindex, nofollow`. The existing AITrove WordPress site was not modified.
- WordPress is **not connected to the student frontend yet**. The frontend's existing CMS client expects an AITrove-specific API plugin, while the new install has only standard WordPress REST. Do not point `WORDPRESS_URL` at the new CMS until a Dekhoexams content contract and publishing workflow are implemented and tested.
- The account has a 25 GB Hostinger Premium allocation; Cloudflare Workers remains on Free for preview only. Neither 1 million daily visits nor launch capacity has been load-tested or approved. Production requires a paid-capacity decision, reviewed content, cache/load testing, a safe CMS integration, analytics/monitoring, and a controlled change from noindex to indexable pages.

Content inventory, state-grade planning matrix and phased publishing plan: `PENPENCIL-CONTENT-ROADMAP.md`.

## Implemented In This Pass

- Original local book-badge PNG artwork for Classes 1-12 and all 13 languages, with native-script labels. Source generator and provenance notes are included; images use fixed dimensions and lazy loading. These are navigation artwork, not new lessons or translations.

- Existing shell, typography and mobile navigation retained. User-requested visual refresh replaces pastels with cobalt, emerald, amber, coral, berry and charcoal accents in light/dark themes. Six broader top shortcuts replace 17 tiles without removing category routes.
- Three-row horizontally scrolling subject directory between Explore Dekhoexams and Classes 1-12: 16 homepage dropdowns and 281 course choices, consistent-size original icons, keyboard controls, inert collapsed panels, responsive layout, accordion/hover animations and reduced-motion CSS. The two removed homepage groups remain as registered routes. Course selections disclose missing local lessons and offer labelled external Khan Academy links; no course content was copied.
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

## Question Bank (added 2026-11-05)

- `/questions` original practice bank uses an exam → subject → chapter layout. 19 exams (JEE Main/Advanced, BITSAT, WB JEE, MHT CET, KCET, COMEDK, VITEEE, NEET, GATE CSE/ECE/EE/ME/CE, CBSE 10/12, ICSE 10, NDA) with syllabus-style chapter lists.
- Only 29 original practice questions exist (single-correct and numerical, with solutions). None are past-paper questions, so year/shift are null and the year filter stays disabled. Solutions are not academically reviewed. Every page is noindex.
- Chapter filters (year, difficulty, type, status), show/hide solutions, bookmarks and attempt progress (this browser only), and a short timed practice set with practice marking. This is not a full mock test and nothing is saved server-side.
- Remaining: rights-cleared past papers with year/shift, many more questions per chapter, academic review, account-synced progress, and exams ExamSide lists that are not added here yet.

## Exam directory (2026-11-05)
- Home page `/` and `/questions` now show the ExamSide-style exam directory: 7 groups (JEE, Medical, GATE, Civil Services, Defence, SSC, CBSE), 29 exams, Chapter-wise / Paper-wise per exam.
- Chapter-wise (`/questions/$exam`) groups chapters by subject and unit. JEE Main uses the chapter and year-wise archive paths above. The other exam directories list their available original practice sets; each original set has a printable view with an answer key.
- JEE Main now opens the archive described above. Earlier practice links still resolve; original practice questions retain their existing IDs and separate labels.
- Exam cards use local logos where sourced; IAT and ICSE Class 10 use initials. 106 original practice questions across all 29 exams (each has a printable practice set); no past papers yet. Dekhoexams eye-and-tick icon and share image added.

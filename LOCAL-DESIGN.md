# Current Java and Spring expansion

Java has 226 articles, 10 hubs and 14 quizzes. Spring & Spring Boot is a separate subject with 45 articles, 10 hubs and 3 quizzes (36 questions). New source-kit programs and tests are recorded in docs/java-spring-expansion. The current map is http://127.0.0.1:3001/learning-coverage.html. Earlier counts below are historical release snapshots.

# AI Trove local design review

This separate checkout started as `design/ozi-local`. The user authorized a GitHub review-branch push on29September; current release information is in docs/release-2026-09-29. Production and the original checkout remain separate.

- Preview: http://127.0.0.1:3001/
- Original local version: http://127.0.0.1:3000/

The homepage now follows the user's 29 September Explore screenshot: 16 colored topic cards in the same order, with the first four spanning two columns on desktop and twelve smaller cards below. On phones, all cards use a compact two-column layout. Cards include topic logos/diagrams and direct resource links. Java explanations remain on Java pages.

The previous separate AI tools, language shelves, main-topic shelves, DSA directory and resource shortcuts were replaced by this single Explore grid. Tutorial pages retain their existing content, interactive diagrams and reading controls. The shared larger logo and homepage header remain intact. No lesson content or archived courses were removed.

The homepage production build, changed-component lint and whitespace checks passed. Current layout verification is `../../outputs/explore-reference-check.json`, covering six widths from 320 to 1440 pixels, all sixteen resource links, loaded logos, white-text contrast and Java navigation. Screenshots use `explore-reference-`. Earlier homepage artifacts show earlier revisions.

Start with `npm run dev -- --host 127.0.0.1 --port 3001`. The dependency directory is a symlink to the original checkout's installed dependencies. Courses stay hidden and WordPress is still pending; the preview uses sample CMS content.

Earlier artifacts such as `directory-layout-check.json` and `reader-palette-check.json` record the previous directory design. The Explore reference check supersedes them for homepage layout and card contrast. `scripts/check-ozi-local.mjs` now expects the sixteen Explore cards and Java hub navigation; its earlier result file predates this homepage change.

The user has now authorized pushing all work. Push the tested review branch; deployment and merging remain separate.

## Current release — 29 September 2026

219 Java routes:195 articles,10 hubs,14 quizzes and168 questions. This pass adds ten original lessons and195 useful body links, expands four lessons, restores all quiz landings to the shared learning layout and gives previous/next links curriculum order and reduced-motion-aware animation. The16-card homepage is unchanged.

See docs/release-2026-09-29 for current Java handoff, stack configuration, SEO audit and action plan. The current map is public/java-coverage.html (http://127.0.0.1:3001/java-coverage.html). Production sitemap eligibility is220 reviewed records plus homepage; preview remains noindex with an empty sitemap. WordPress import and live deployment remain pending. Earlier reports below are historical.

## Earlier Java depth pass — 29 September 2026

The current local preview has 185 Java articles, 10 hubs and 14 quizzes: 209 content routes and 168 questions. Quiz attempt/review URLs use shared templates and are checked separately. This pass adds 31 original articles, expands three articles and adds three twelve-question banks. The new bodies contain 9,360 prose words, or 11,081 words including programs/output. The sixteen-card Explore homepage is unchanged.

New material closes several earlier gaps: cross-package access fixtures, grapheme segmentation and collation, selected Java 25 features, AVL/trie deletion, graph and DP algorithms, multi-index ownership, H2 isolation, a Hikari pool and a bounded migration ledger, own-process heap capture, JFR outcomes, local HTTP/TLS failures and a concurrent import project. Each lesson names its release and bounds; these are learning fixtures, not production guarantees.

Current clickable map: `../../outputs/java-depth-coverage.html`, served at http://127.0.0.1:3001/java-coverage.html. All 209 routes are represented, with 37 new/expanded routes and remaining work for ten sections. `../../outputs/java-depth-editorial-handoff.md` records research and limits. The changed 47-entry export is `aitrove-java-depth-content.json`; the full export is `aitrove-java-full-content.json` with 209 entries. WordPress import remains pending. No push or deployment occurred.

The source archive contains 193 source/build/documentation files, including 159 full standalone JDK units and Maven, module, Gradle, JMH, package-access and owned-process diagnostic fixtures. It contains no binaries, heap dumps, credentials or bundled JDK. Source downloads appear on the new lessons. Release 25 examples need JDK 25; third-party examples need their listed dependencies.

Validation: 174 compiled units, 163 executions and 148 declared output checks across releases 8, 11, 17, 21 and 25; 22 Maven tests with no failures/errors/skips; Hikari source compiled separately for release 17; 5,085,835 property/boundary checks over twelve topics. Three invalid package accesses failed compilation as required. The synthetic JVM histogram and heap capture passed and its temporary dump was removed. System Java was not changed; the checked Corretto 25 runtime is task-local and ignored. Reports: `java-program-check.json`, `java-depth-properties.json`, `java-depth-dependency-check.json`, `java-depth-boundaries-check.json`. Earlier unchanged module/Gradle/JMH fixtures retain their previous-pass checks.

The current browser suite passed all 31 new article screens, all 168 quiz answers/explanations, all 209 response titles, six viewport widths, search, map filters, mobile curriculum/heading jumps and exact source download equality. No browser errors occurred. See `java-depth-browser-check.json`; current screenshots use the `java-depth-` prefix.

The map explicitly retains broader Java/library topics, real database/HTTP/TLS fault and load tests, heap-reference analysis, full benchmark experiments, WordPress publishing, server judging and authenticated quiz storage. Exhaustive Java coverage and a complete internet crawl are not claimed.

## Earlier Java completion pass — 29 September 2026

The isolated preview now contains 154 Java articles, 10 section hubs and 11 quizzes: 175 routes and 132 quiz questions. This pass adds 45 original articles, expands 20 existing articles, adds six quiz banks and expands all five earlier banks. The new article text contains about 12,900 prose words, or 16,022 words including code and output. Every new lesson is linked from a section curriculum and related lessons; search includes the new titles. The approved Explore homepage remains unchanged.

New material includes casts, normalization and regular expressions; immutable/sequenced, copy-on-write and concurrent sorted collections; class loaders, modules, conditions, permits, scheduling, cancellation, channels, sockets and JFR; AVL trees, tries, a binary heap, KMP, spanning forests, Bellman–Ford, tabulation and interval scheduling; interview/exercise/reference sets; persisted reading lists, deque commands, a local HTTP project and a transactional database project; test doubles, parameterized tests, Gradle and JMH.

That earlier clickable skeleton is `../../outputs/java-finish-coverage.html`, (superseded by the depth map). It included all 175 routes, 76 new/expanded article and quiz routes, and remaining scope for all ten sections. `../../outputs/java-finish-editorial-handoff.md` records the research sources and limits. The original prose/programs were written from verified contracts and topic coverage, not copied examples with changed names.

`../../outputs/aitrove-java-finish-content.json` contains this batch’s later WordPress import payload; `../../outputs/aitrove-java-full-content.json` includes all 175 current Java entries. `../../outputs/aitrove-java-source-kit.zip` (also in public/downloads) contains 131 complete JDK source units plus Maven, named-module, Gradle and JMH source/build fixtures. Download buttons are shown on the relevant project/build pages. No CMS import or deployment occurred.

Validation: 144 compiled JDK programs/fragments, 135 executed programs and 120 exact output checks across release targets 8, 11, 17 and 21. The dependency suite passed 19 JUnit/H2 cases; two named modules compiled/launched; Gradle 8.10.2 ran the app/billing project; both JMH 1.37 benchmarks executed in a short smoke check. The new algorithm/concurrency suite passed 2,385,569 checks. See `../../outputs/java-program-check.json`, `java-finish-build-fixtures.json`, `java-finish-modules-check.json` and `java-finish-properties.json`. The website production build passed; changed-component lint has no errors and one existing fast-refresh warning.

Remaining scope is explicit in the current map: Java beyond 21; deeper Unicode/access exercises; AVL/trie deletion and broader problem sets; application-level concurrent workflows; production DB/HTTP fault/load tests, pools and migrations; longer JVM incident/benchmark work; authenticated quiz storage and server judging. Current project fixtures are learning applications with stated boundaries, not production services. JMH smoke scores are not a performance ranking. The Gradle kit requires an installed tool and does not include a wrapper.

The browser suite passed all 45 new article screens, all 132 quiz answers/explanations, all 175 route responses, source-kit download equality, search, coverage filters and mobile reading controls at six widths (320–1440). See `../../outputs/java-finish-browser-check.json`. Visual review confirmed readable desktop and mobile layouts.

Earlier java-next reports document the previous 24-new/8-expanded batch and its 124 routes. They are historical; use the java-depth coverage map for current counts.

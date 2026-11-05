# Pencil2Pen Content and Publishing Roadmap

Updated 2026-10-01. Canonical domain: `https://pencil2pen.com`. This is an execution plan for filling the education site, not a claim that the listed curricula, textbooks, languages or courses are published. `SITE-ARCHITECTURE.md` remains the route and SEO contract; `IMPLEMENTATION-STATUS.md` records current implementation limits.

## 1. Where We Stand

The code catalog contains **672 education routes**, including class-first NCERT, language and state-board directory hubs. These are navigable destinations, not 672 completed learning pages. There are **14 original English draft lessons**, distributed across Classes 1-12, with 28 short self-check questions. All 14 are preview resources; **zero are marked published**, **zero collection pages are reviewed**, and the preview education sitemap is empty. Legacy computing CMS material is separate and is not school curriculum.

The homepage now has **6 broad discovery tiles** and **16 subject dropdowns with 281 reference choices**. The two removed homepage groups, Beyond the Classroom and For Educators, still have registered URLs and are absent only from homepage discovery. The 281 choices are external-reference selections, not Pencil2Pen-authored courses. The underlying reference inventory has 18 groups and 302 choices because those two historical groups remain in the catalog.

| Surface already present | Quantity | Data still needed before a credible launch |
| --- | ---: | --- |
| Classes | 12 grade hubs | Approved grade/subject/chapter inventories, original lessons, practice and reviews. |
| General subjects | 10 subject hubs | Grade-specific coverage and chapter links; the current 14 lessons only touch a small subset. |
| NCERT class and material directories | 12 class hubs and 5 material families x 12 classes | Books, editions, chapters and exercise mapping; original solutions, notes, exemplar and verified syllabus records. Old resource-first class URLs redirect. |
| NCERT language directories | 13 language hubs x 12 class hubs | Actual resource-language availability; translated original lessons and language review where appropriate. English has the 14 general draft lessons, not verified NCERT solutions. |
| State/UT directories in current catalog | 22 state hubs x 12 class hubs | Source authority, board naming, grade/subject coverage, language, book editions and rights. No state textbooks or verified state chapters exist yet. |
| Other board/class routes | CBSE 12; ICSE 2; ISC 2; NIOS 2 | Session-specific syllabi, exam patterns, approved chapters, papers and reviewer evidence. |
| Reference-book publishers | 6 | Book and edition catalog, permission assessment and original worked solutions. |
| Entrance/competitive exams | 9; plus UG and PG hubs | Exam versions, syllabi, subject taxonomy, original questions, past-paper rights and practice products. |
| Additional resource families | 7 | Sample papers, previous papers, important questions, worksheets, tests, formulas and flashcards. Only short lesson self-checks exist today. |
| Scholarships | 1 hub | Individual source-verified opportunities with eligibility, deadline, geography and review dates. |

**The state scope is a planning matrix of 22 current directories x 12 grades = 264 state-grade slots.** These are now live navigation directories, but all are noindex and none imply that an authority publishes every subject or book in every grade/language. Register deeper subject/chapter routes only after source, curriculum and useful original content are verified. The present catalog includes Andhra Pradesh, Assam, Bihar, Chhattisgarh, Gujarat, Haryana, Jharkhand, Karnataka, Kerala, Madhya Pradesh, Maharashtra, Mizoram, Nagaland, Odisha, Punjab, Rajasthan, Tamil Nadu, Telangana, Uttar Pradesh, Uttarakhand, West Bengal and Jammu & Kashmir. Audit missing jurisdictions and current administrative/board naming before calling coverage complete.

## 2. Data Model to Build

The inherited CMS is not wired to the school catalog. A school publishing system needs structured records rather than manually adding hundreds of routes:

| Record | Required fields | What it powers |
| --- | --- | --- |
| Curriculum | authority/board, session, grade, subject, language, official source URL, verified date | Which class and subject combinations actually exist. |
| Book edition | publisher, title, ISBN or official ID if available, edition/year, language, rights decision, source URL | Book inventory and edition-correct links. |
| Chapter and exercise | stable ID, parent book, chapter order/title, exercise/question references | Chapter navigation and exact solution alignment. |
| Learning resource | immutable ID, canonical URL, type, locale, body, source relations, licence, status, author/reviewer, review date, revision | Original lessons, notes, worked solutions and guide pages. |
| Question | stable ID/version, prompt, answer, explanation, difficulty, curriculum alignment, rights and reviewer | Chapter self-checks, worksheets and future tests. |
| Paper/test | exam/board, session/year, subject, variant, question set, marking rules, source and permission | Past papers, sample papers and scored assessments. |
| Language variant | source resource, target locale, translator, academic/language reviewers, equivalence status | Genuine multilingual pages and future reciprocal hreflang. |
| Scholarship | official URL, eligibility, amount, geography, opening/closing dates, last verified, status | Useful time-sensitive listings. |
| Editorial event | actor, action, before/after version, timestamp, approval decision | Corrections, audit trail and publication control. |

Workflow: ingest a verified source -> record rights and edition -> author original material -> academic review -> language review where relevant -> accessibility and SEO review -> publish -> monitor corrections -> archive or update obsolete editions. Separate author, reviewer and publisher permissions. Publishing must trigger route registration, navigation, sitemap inclusion and search indexing from the same approved record.

## 3. What to Fill in Each Area

### A. NCERT, Classes 1-12

Create an edition inventory for each verified grade, subject and language. Record the official book link, chapter order, syllabus/session mapping and whether Pencil2Pen may host any file. Link to the official source where hosting rights are not established. For each chapter, author an original concept lesson, worked examples, common mistakes and explained practice. For an NCERT solution, map the exact book edition, chapter, exercise and question; a general maths lesson cannot be relabelled as a textbook solution. Books, solutions, notes, exemplar and syllabus are five different product types with different review checks.

The current English, Hindi, Kannada and other language directories are availability pages. Populate only the languages for which an actual official edition or independently authored translation has been verified. Do not create 13 copies of every resource by swapping language labels.

### B. State Boards, Classes 1-12

Use the 264-slot matrix as an editorial tracker with statuses: `not researched`, `official source found`, `edition mapped`, `drafting`, `academic review`, `language review`, `published`, `update due`. Per slot, record the authority, current session, grade, subjects, medium of instruction, textbooks and permission position. A slot may have multiple books, fewer subjects than another board, or no supported book at all. Create page records per real grade/subject/book/chapter, not a Cartesian product of states x classes x subjects x languages.

Start with the three states currently prominent in the subject directory: Karnataka, Maharashtra and Telangana. Pick the first state-grade-subject cohorts using verified demand and available academic reviewers. Expand to the other 19 current directories in measured waves; review whether additional jurisdictions belong in the catalog before promising all-India coverage.

### C. CBSE, CISCE and NIOS

CBSE has 12 grade hubs in this codebase; ICSE, ISC and NIOS have 2 grade hubs each. Attach the correct authority, session, subject and assessment pattern. Distinguish general concept lessons from board-aligned lessons. Publish specimen/sample papers, marking schemes and practical materials only when source and distribution rights are clear; build original explanations of solutions.

### D. Reference Books

The six publisher directories need precise book editions and class/subject mappings. Create original worked answers tied to the edition's chapter and exercise. Permission to reference a book is not permission to reproduce its pages, images or answer keys. Keep publisher attribution and a correction path.

### E. Exams and Higher Education

JEE, NEET, CUET, CAT, GATE, NDA, CLAT, CA and UPSC need individual syllabus/version records and question banks; UG and PG need actual degree or entrance pathways. Do not merge CUET UG and PG, or similarly named exam variants, under an ambiguous content record. Add timed mock tests only after the question bank, marking logic, recovery and server-side attempts exist. Maintain dates and eligibility from the issuing authority with an update owner.

### F. Practice and Utility Content

Populate worksheets, formulas, flashcards, important questions, sample papers and previous papers as distinct original/authorized records. Make each chapter page useful on its own; show related practice, revision and next-lesson links only when those resources exist. The existing reading list and mistake review are local-browser conveniences, not student accounts or synchronized scores.

### G. Scholarships

Each listing needs eligibility, location, stage of study, amount, official application URL, opening/closing date, source, last verification and a stale/closed state. Time-sensitive pages need scheduled review and removal from discovery when no longer actionable.

## 4. Rollout Order and Acceptance Gates

Time ranges below are planning windows, contingent on staffing, approved sources and review throughput. They are not traffic forecasts.

| Phase | Indicative window | Ship | Exit gate |
| --- | --- | --- | --- |
| 0. Content foundation | Weeks 1-4 | School CMS schema, editorial roles, source/licence register, correction history, import templates, analytics baseline and staging. | An editor can draft, review, publish, update and unpublish a resource without code edits; preview pages stay out of the sitemap. |
| 1. Complete pilot | Weeks 5-12 | One complete verified cohort, e.g. Class 10 Maths in English, with chapters, worked examples, original solutions where edition-mapped and explained practice. Review the 14 existing drafts. | Full selected syllabus coverage, 100% required source/rights/reviewer fields, route and sitemap checks, real student usability testing. |
| 2. Core school expansion | Months 4-6 | Adjacent grades/subjects and a first reviewed Hindi cohort; CBSE mapping where verified. Build subject landing pages from real resources. | No published empty collections; every translated page reviewed by a native-language subject reviewer; search finds resources by grade, subject and language. |
| 3. State and exam pilots | Months 7-9 | First three state cohorts (Karnataka, Maharashtra, Telangana), one focused entrance-exam bank, papers/worksheets where rights permit. | Authority/edition mapping verified for each published page, question versioning and meaningful practice quality checks. |
| 4. Broader coverage | Months 10-18+ | Roll through remaining state-grade slots, NCERT families, languages and exams in demand-led batches. Add formal tests and accounts only when their backend is ready. | Publish only completed cohorts; measured return use, indexing and content quality guide each next wave. |

Suggested minimum responsibilities: one product/editorial owner, an academic lead for each active subject, independent academic reviewers, native-language reviewers for translations, engineers for CMS/search/assessment, a rights/source owner and an SEO/analytics owner. One person can cover multiple roles in a small pilot, but an author should not be their own sole academic reviewer.

## 5. Search and Growth Plan

The existing route grammar, SSR titles, canonicals, breadcrumbs, 404 behavior and preview noindex gate are useful foundations. Publish a URL only when its actual lesson or curated hub is useful and approved; include it in the sitemap only after publication. Keep `?topic=` reference selections, search/filter URLs and empty hubs out of the index. Give each chapter a clear path from class -> subject -> chapter, with backlinks to parent and real related learning resources. Check mobile readability, load speed, broken links, accessibility and server responses during each batch.

Google advises publishing helpful, original content for learners rather than generating many pages just to capture searches. Its course markup guidance applies to real courses with lessons/modules; do not attach `Course` markup to menu placeholders. See [Google's people-first content guidance](https://developers.google.com/search/docs/fundamentals/creating-helpful-content), [course structured-data guidance](https://developers.google.com/search/docs/appearance/structured-data/course), and [Google's guidance on generated content](https://developers.google.com/search/docs/fundamentals/using-gen-ai-content). NCERT has issued [a copyright warning on unauthorized textbook reproduction](https://www.ncert.nic.in/pdf/announcement/notices/Press_Release_Copyright_Infringement-NCERT.pdf); track permission before mirroring textbooks.

Before public launch: configure separate hosting and TLS for `pencil2pen.com`, verify the property in Search Console, submit the production sitemap, establish privacy-aware analytics and test cache behavior. Track: reviewed published resources, curriculum coverage by cohort, indexing status, non-brand organic entries, lesson starts, practice completions, saves/returns, repeat visitors, correction turnaround, broken links and mobile performance. Record the first live baseline before setting numeric traffic targets. A million visits per day requires content demand, distribution and capacity testing; route count alone cannot produce it.

## 6. Immediate Content Backlog

1. Build the 22 x 12 state-grade tracker and record official source/edition/medium per candidate slot; mark unknowns explicitly.
2. Choose a complete first cohort and collect its current official syllabus, book edition and usage rights.
3. Review or replace the existing 14 English drafts; name the academic reviewer and session/edition alignment where applicable.
4. Implement the school CMS data model and import validator before bulk creation.
5. Produce and review the first cohort's chapter inventory, lessons and question explanations; publish it end to end.
6. Turn on production indexing only for approved resources, then measure search and learner behavior before the next cohort.

This roadmap is a living operating plan. Each wave should update the matrix and `IMPLEMENTATION-STATUS.md` with actual published counts, not just newly created URLs.

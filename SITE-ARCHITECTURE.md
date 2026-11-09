# Dekhoexams Architecture Contract

Canonical origin: https://pencil2pen.com. Public name: Dekhoexams. This contract governs subsequent education additions. The inherited shell and typography remain. The user-approved October 1 visual refresh replaces pastel colors with saturated accents, condenses discovery into six shortcuts and adds an 18-group subject directory. Content changes must not become an unsolicited redesign.

Current map (October 17, 2026): 2,338 registered education routes, 88 legacy aliases and 14 original English lesson drafts. Class pages lead to board/book choices and subjects; board/class and subject pages lead to available chapters. These are mostly route shells, not a complete published curriculum. No education page is reviewed or indexable. The state-board list has 22 entries (including Jammu & Kashmir) and is not all Indian states and union territories. The 13 language hubs do not contain translated lessons.

## Subject Directory

`src/lib/subject-directory.ts` maps the 18 reference groups to explicit registered collection routes. `src/data/khan-course-reference.json` records 302 public menu names and reference URLs captured from Khan Academy on October 1, 2026, not course content. Course choices use a `?topic=` filter under the owning collection, remain noindex and canonicalize to that collection. The selection page discloses missing Dekhoexams lessons and labels the external reference. It must never imply these are 302 locally published courses. Preserve source provenance and verify references before a public release. Icons and headings use independent Dekhoexams branding.

The homepage renders 16 of these groups and 281 options. `/explore-more` and `/teachers` are intentionally absent from homepage discovery, while their previously registered routes remain available to existing links.

## One resource, multiple discovery paths

`education-catalog.ts` owns registered pages, immutable resource IDs, parent relationships, discovery references, aliases and publication gates. `school-content.ts` contains the current original lesson bodies. A class, subject, board, language or resource-type hub references a resource ID, not a cloned body. Only its canonical URL serves the resource. The catch-all resolves education first and reserves education prefixes; unknown combinations return 404. Legacy computing URLs remain separate, not misrepresented as school content.

Current resources record canonical path, version, language, type, status, rights, author/reviewer/review date, syllabus version, board and book edition. Null values mean unverified, not silently assumed. The ID map is explicit and must survive reordered arrays and title/URL changes. New records need new IDs. Material answer changes require a new version so old saved answers are not reinterpreted.

## Permanent URL Grammar

| Intent | URL contract |
| --- | --- |
| Classes and subjects | `/classes`, `/class-10`, `/class-10/maths` |
| General original chapter | `/class-10/maths/quadratic-equations` |
| Subjects across classes | `/subjects`, `/maths`, `/science`, `/physics`, etc. |
| Boards | `/boards`, `/cbse/class-10`, `/cisce`, `/icse/class-10`, `/isc/class-12`, `/nios/class-10` |
| States | `/state-boards/karnataka/class-10`; all states have class 1-12 directory hubs, with subject/chapter descendants only when verified content is registered |
| NCERT class-first directories | `/ncert/class-10`, `/ncert/class-10/maths`, `/ncert/class-10/books`, `/ncert/class-10/solutions`, `/ncert/class-10/notes`, `/ncert/class-10/exemplar`, `/ncert/class-10/syllabus` |
| Real future NCERT chapter solution | `/ncert/class-10/maths/{chapter}/solutions`; requires verified edition/exercise alignment and an original solution, not a rename of a general lesson |
| Language discovery | `/languages`, `/ncert/english/class-10`, `/ncert/hindi/class-10`, `/ncert/kannada/class-10`, etc. Language class directories are noindex until translated content exists. |
| Syllabus guides | `/ncert/class-12/syllabus`, `/ncert/english/class-10/syllabus`, `/ncert/hindi/class-10/syllabus`; the English/Hindi guides distinguish CBSE course variants and link official sources but have no reviewed local chapter outline yet. |
| Future translated resource | `/ncert/hindi/class-10/maths/{chapter}`; register only a real reviewed Hindi resource and its reciprocal translation relationships |
| Reference books | `/textbook-solutions/{book}`; future `/{class}/{subject}/{chapter}` descendants need verified book edition |
| Exams | `/exams`, `/jee`, `/neet`, `/cuet`, `/cat`, `/gate`, `/nda`, `/clat`, `/ca`, `/upsc` |
| Official exam updates | `/exam-updates`, `/exam-updates/date-sheets`, `/exam-updates/answer-keys`, `/exam-updates/results`, `/exam-updates/marking-schemes` |
| Future exam subject/chapter | `/{exam}/{subject}/{chapter}` for exam-specific original material |
| Paper collections | `/sample-papers`, `/previous-year-papers`; future `/{board}/{class}/{subject}/{year}/{paper}` only for an actual distinct paper |
| Practice collections | `/tests`, `/worksheets`, `/important-questions`, `/formulas`, `/flashcards` |
| Future formal attempts | `/tests/{test-id}/attempt`, `/tests/{test-id}/result`; private, noindex, server-authorized |
| Higher education | `/ug`, `/pg`; future subject/course descendants need actual content |
| Funding | `/scholarships`; specific listings require source, eligibility, deadline and review date |
| Utility | `/search?q=...&grade=10`, `/my-study`, `/site-map`; always noindex |

The class directory hubs and NCERT material-type hubs above are live but noindex placeholders until edited. The chapter examples are NOT live. Do not generate every theoretical board x class x subject x chapter combination; add subject and chapter nodes only with verified curriculum data and reviewed original content. Old `/ncert-books/class-10`-style links redirect in one hop to their class-first equivalents. The current resource renderer supports lessons/self-checks, not book/PDF/test-engine records.

Use lowercase ASCII hyphenated paths, no trailing slash, no file extension for a learning page. Keep academic sessions and book editions in metadata unless versions genuinely need separately accessible archives. A permanent move gets a one-hop 301 alias with query preserved. Case/trailing-slash normalization is 308. Never redirect missing resources to an unrelated home or category page.

## SEO Publication Gate

- SSR supplies heading, content, title, description, one canonical and matching breadcrumb JSON-LD. Lesson schema describes actual lessons; no invented Course, FAQ, rating or review markup.
- A resource can be indexed only when published, rights cleared, author and reviewer recorded, review date valid, and actual practice present. Directory review also needs useful reviewed resources or a curated official source. The current 14 starter lessons remain preview and academically unreviewed.
- `VITE_PREVIEW_MODE` defaults true. Only a reviewed production launch sets it false. Removing global preview does not override per-resource gates.
- `/sitemap.xml` is empty in preview. At production it becomes an index containing `/sitemap-education.xml` and paged legacy CMS sitemaps. Only canonical indexable education pages appear in the education sitemap. Split it before exceeding 50,000 URLs or 50 MB; current catalog is well below both.
- CMS sitemap entries cannot overlap owned education prefixes or aliases. Utility/filter URLs are noindex; search filters canonicalize to the clean page. Robots permits crawling so noindex can be read.
- Language directories are English-language availability pages, not translations. Do not add hreflang until genuine equivalent resources exist. Do not claim the 13 languages are ranked by student volume; no enrolment study has been supplied.

## Publishing Workflow To Implement

The school catalog is currently code-backed. Before CMS launch, extend the inherited CMS with normalized board/exam, grade, subject, language, syllabus, book/edition/chapter/exercise, resource and question relations. Do not repurpose arbitrary CMS paths to bypass the registry.

Required workflow: source and licence verification -> original authoring -> academic review -> language review -> accessibility/SEO review -> scheduled publication -> corrections/version history -> archival. Require permission-separated author/reviewer/publisher roles and an audit log. Protect mutation routes, uploads and all private attempts server-side. Uploaded documents need malware/type/size checks, a private original plus authorized public derivative, and explicit redistribution permission.

Resources copied from competitor sites are not a content supply chain. Use original explanations, licensed material and approved official sources. External portal links do not mean permission to mirror textbooks or reproduce their solutions.

The exam-update guides link to CBSE and NTA publishers and must never fabricate a release date, result, answer key, or downloadable file. Sample-paper marking schemes are distinct from live exam answer keys. NCERT discovery links to the official textbook, syllabus, exemplar and lab-manual portals; it does not host their PDFs. Before indexing these guides, an editor must verify current-year notices, attribution, wording and ongoing link health. An exam-alert signup would additionally require consent, safe handling of minors' data, storage and delivery infrastructure; no signup form is live.

## Learning State

`penpencil-learning-v1` stores saved IDs, 30 recent lessons and version-keyed question answers. Malformed/unknown/outdated records are ignored. Changes synchronize between tabs; Clear saved learning data removes the records. There is no account, server attempt, formal grade, mastery model or device sync. Client answer keys are appropriate only for these low-stakes self-checks.

## Verification

`npm run test:education` validates destinations, parents, breadcrumb cycles, IDs, grade/language/category coverage, alias targets, publication gates and hostile/malformed storage. It runs automatically before `npm run build`. Set `PENPENCIL_TEST_URL` to the local preview to also crawl every catalog page for SSR, canonical/robots metadata and route status, plus redirects and sitemap behavior. Keep TypeScript and browser flow checks alongside these tests.

## Google sitemap

The canonical site advertises `https://dekhoexams.com/sitemap.xml` in its robots file. Four child maps separate Main and Advanced directories from their individual question pages. The build regenerates the lists from the checked-in archives; only complete canonical questions with both languages and no pending figure qualify. The rest of the site retains its preview gates. No synthetic modification dates are published.

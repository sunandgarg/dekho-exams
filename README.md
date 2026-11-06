# Dekhoexams learning platform

Dekhoexams is a new Class 1–12 student experience built on this TanStack Start codebase. The local starter has 14 original lessons, plus board, book, exam and language directories. The inherited computing library is preserved. [SITE-ARCHITECTURE.md](SITE-ARCHITECTURE.md) is the routing/content contract; [IMPLEMENTATION-STATUS.md](IMPLEMENTATION-STATUS.md) records what is complete and every remaining production workstream.

## Local preview

```sh
npm install
npm run dev -- --host 127.0.0.1
```

Open the URL reported by Vite (currently `http://127.0.0.1:3001/`). Leave legacy `WORDPRESS_URL` unset to use the bundled computing snapshot. The school lessons are in `src/lib/school-content.ts`; `/classes` is the class hub and `/study` redirects permanently. All new education routes are registered in `src/lib/education-catalog.ts`. Preview mode stays `noindex` until the content, domain and legal pages are reviewed for launch. Canonicals target `https://dekhoexams.com` for the future domain; preview remains noindex until it is purchased and connected.

## Hostinger WordPress and Cloudflare

The student frontend is deployed as the separate `dekhoexams-frontend` Cloudflare Worker at `https://dekhoexams-frontend.bevory-main.workers.dev`. The separate Hostinger WordPress backend is at `https://linen-mandrill-402101.hostingersite.com`; the existing `cms.pencil2pen.com` site remains untouched. The `wordpress/dekhoexams-school-content` plugin is active and the first published School lesson, `pp-0001`, is available at `/wp-json/dekhoexams/v1/lesson?id=pp-0001`. `SCHOOL_WORDPRESS_URL` and build-time `VITE_WORDPRESS_URL` point to this temporary address. The frontend validates the WordPress response and falls back to the local lesson if the CMS is unavailable. The other 13 lessons, practice questions, progress and route ownership stay in code/browser storage. Update both URLs when the purchased domain is connected.

This checkout has no Supabase or Lovable runtime or build dependency. Its school content API uses WordPress; learner accounts and server-saved attempts are not implemented. Do not enable signup or claim cross-device progress until those services are built. Keep `VITE_PREVIEW_MODE=true` and the site `noindex` while content is under review.

Exam logos are checked into `public/exam-logos` and mapped to stable exam slugs in `src/data/exam-logo-sources.json`, including their source URLs. Twenty-five exams use images from DekhoCampus and the two CBSE exams use the CBSE site logo. IAT and ICSE Class 10 retain text badges until a verified source image is available. To replace a logo, update the local file and mapping together; the frontend does not request images from DekhoCampus at runtime.

The legacy computing content has a separate `wordpress/aitrove-cms` plugin and `WORDPRESS_URL` setting. Leave `WORDPRESS_URL` unset unless that plugin and its reviewed content are installed on the target CMS. The current Hostinger site does not yet serve that endpoint.

Use Node 22.18+ (or a current Node LTS). `npm run test:education` runs before every production build. With the preview running, `PENPENCIL_TEST_URL=http://127.0.0.1:3001 npm run test:education` also checks every catalog URL over HTTP, all legacy redirects, preview sitemaps and unknown-route 404s. Never deploy to the inherited AITrove Cloudflare project for a Dekhoexams launch.

## Legacy AITrove integration

The sections below document the inherited computing CMS and deployment configuration. They are not a Dekhoexams production launch guide. Review the WordPress plugin, content, legal copy and Cloudflare project settings before migrating them to the new site.

## Cloudflare Pages preview

The `aitrove` Pages project serves the same TanStack Start routes as the Worker build. Package it with:

```sh
VITE_SITE_URL=https://aitrove.pages.dev VITE_PREVIEW_MODE=true npm run build:pages
```

This writes static assets and a bundled server entry to `dist/pages` for the inherited AITrove project only. Do not use it for Dekhoexams.

Bookmarks, lesson/path completion, quiz scores, assignment drafts, display name and learning goals stay in browser local storage. They are not an authenticated account or an enrollment. Quiz attempts and result reviews work locally. Code judging, payments, authentication, application delivery, contest scores, contact delivery and notifications are not connected. Forms validate inputs and clearly report that nothing was sent. Editors use `/admin`; learners use `/login` and `/account`.

## Connect WordPress

1. After purchasing your domain, install WordPress on a PHP/MySQL host, planned at `cms.aitrove.in`. WordPress does not run inside Cloudflare Workers.
2. Copy `wordpress/aitrove-cms` into `wp-content/plugins/` and activate **AITrove Content API**.
3. Add content under **Learning Content**. Choose its template and unique public path, then fill its title, summary, Markdown body and structured data. The template data guide explains all new families. WordPress handles editorial login, roles, drafts and publishing.
4. Import example entries with `wp aitrove import /absolute/path/to/src/data/fixtures.json`. Import is idempotent by path. **Review all sample lessons, prices, metrics, companies, events and legal/contact copy before publishing a public site.** These are preview examples.
5. Set server-side `WORDPRESS_URL` to your CMS origin and build-time `VITE_WORDPRESS_URL` to the same origin so `/admin` opens WordPress administration. Use HTTPS.
6. Deploy only after checking the WordPress API and DNS. The inherited AITrove Pages deploy command has been removed to prevent publishing Dekhoexams changes to the wrong project.

The frontend reads published entries through `/wp-json/aitrove/v1/entry?path=...` and `/entries`. Server functions perform the API reads, so browser CORS is unnecessary. Company, author and problem-company filters have matching WordPress metadata indexes. Save existing entries again or reimport to populate new indexes when upgrading the plugin.

## Editorial structure

Every entry has `type`, `path`, `title`, `summary`, `body`, `category`, `subject`, `difficulty`, `tags`, `featured`, `sort_order` and optional `potd_date`. Structured `data` fields:

- Subject: `modules: [{title, lessons: [publishedPath]}]`.
- Article: `kind` (concept, reference, project, notes, comparison, interview), `reading_minutes`, `author_path`.
- Quiz: `questions: [{prompt, options: [string], answer: zeroBasedIndex, explanation}]`, `duration_minutes`.
- Path: `steps: [{title, path, kind}]`, `duration`.
- Course: `syllabus: [{title, items: [string]}]`, `lessons: [{title, module, body}]`, `batches: [{title, schedule, seats}]`, `projects`, `instructor`, `instructor_path`, `price`, `mode`, `duration`.
- Company: `company`, `industry`, `location`. Job: `company`, `company_path`, `location`, `experience`, `job_type`, `salary`, `apply_url`.
- Author: `role`, `expertise: [string]`.
- Event: `starts_at`, `ends_at`, `register_url`, `location`, `agenda`, `problems: [publishedPath]`.
- Video: `video_url`, `transcript`, `duration`, `instructor`.
- Business: `features`, `cta_label`, `cta_url`. The inquiry UI requires a delivery service before launch.

Use the fixtures as complete import examples. Unknown resources and invalid lesson numbers return 404. Adding original topic content creates new URLs through these templates; it does not require a new React file per article.

## Verification

```sh
npx tsc --noEmit
npm run lint
npm run build
php -l wordpress/aitrove-cms/aitrove-cms.php
php -l wordpress/dekhoexams-school-content/dekhoexams-school-content.php
```

`scripts/check-preview.mjs` crawls seeded/reference/application routes, checks internal page links, captures 1440px and 390px screenshots and tests menus, bookmarks, quiz retries/results, lesson progress, themes and 404 behavior. It requires a running server and Playwright. Set `PLAYWRIGHT_MODULE` to a Playwright module path when using a bundled runtime. Its report and screenshots are written to the task's outputs directory by default. The script is local verification tooling, not a production dependency.

## Still needed for production

Real CMS installation and import verification; original reviewed content and media; learner authentication and private APIs; judging; payments/enrollment; event registration/scoring; job/inquiry delivery; real author/company/legal information; production sitemaps, canonical/redirect policy and accessibility/performance review. Full screenshot parity with the reference site has not been established. Historical SQL and legacy environment settings are retained for audit and are not used by the public frontend.

## Current product availability

Courses are hidden site-wide via `FEATURES.courses = false` in `src/lib/features.ts`. Course records and all templates are retained. Public menus, home sections, recommendations, search results, learner links and the page directory exclude courses; course, checkout and enrolled-learning URLs return 404 while disabled. Switch the flag to true and restart/rebuild to restore them. Update the WordPress plugin before connecting the CMS so `exclude_types` filtering keeps list pagination/counts correct. Stored course bookmarks/progress remain in browser storage but are hidden.

Brand assets now use `aitrove-symbol-v2.png` and `aitrove-favicon-v2.png`; the original assets are retained.

For the current availability settings, use `scripts/check-course-visibility.mjs` to verify course hiding, retained records/state and the new logo. The general preview check expects courses to be hidden by default; set `COURSES_ENABLED=true` when running it after launching courses.

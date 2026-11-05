# AITrove technical SEO review

Read-only initial snapshot, 29 September 2026. Checkout: `work/aitrove-ozi-local`. Local origin: http://127.0.0.1:3001. Parent edits made after this snapshot require revalidation. No numerical SEO score or ranking guarantee is assigned.

## Verified initial state

- 353 fixture records: 349 published public entries and 4 hidden course entries. All 349 public fixture URLs returned HTTP200 with one H1 and a title.
- Critical content is server-rendered: LinkedList raw response included title, description, headings and tutorial text. This is TanStack Start SSR rather than a blank client-only app.
- Zero canonicals and zero JSON-LD blocks across 349 raw page responses.
- /sitemap.xml, /sitemap_index.xml and /wp-sitemap.xml each404. robots.txt200 allows all, has no Sitemap directive.
- Missing lesson and course routes correctly404. Unknown category/video categories incorrectly return empty200 archives. Case and trailing-slash aliases200 duplicate canonical content.
- All static body/module lesson references resolve to a known published or directory path. This does not establish no rendered orphans: contextual body links appeared on129 of349 entries;220 had none, though sidebar/hub links can still reach them.
- No shared .seo-cache was present. No app files were changed by this agent.

## Concrete issues and recommendations

### high: canonical

All 349 audited public fixture pages lacked a canonical URL; uppercase and trailing-slash aliases returned 200.

Set one configured public SITE_URL shared by canonical, og:url, JSON-LD and sitemap; permanently redirect case/trailing-slash aliases. Preserve true pagination pages instead of canonicalizing them all to page1.

Evidence: `src/routes/$.tsx:73`.

### high: sitemap

/sitemap.xml, /sitemap_index.xml and /wp-sitemap.xml all returned404. robots.txt has no Sitemap directive.

Serve escaped UTF-8 XML with canonical eligible published entries plus real directory pages; use genuine updated_at; exclude archived courses, drafts, utilities, thin fixtures, error pages, redirects and attempt/results. Paginate CMS API rather than first100 only.

Evidence: `public/robots.txt:1; src/server.ts:47`.

### high: utility indexing

search, account, quiz attempt/results, admin/auth/password-reset screens have no noindex rule. admin/auth/reset also lack titles.

Serve noindex,follow and useful titles in initial HTML. Use X-Robots-Tag on coverage/source-kit/internal diagnostics artifacts; do not use robots Disallow as substitute for noindex discovery.

Evidence: `src/routes/$.tsx:90; src/routes/admin.tsx; src/routes/auth.tsx; src/routes/reset-password.tsx`.

### high: soft404

Unknown category and video-category URLs return200 with empty results.

Reject invalid category slugs or unknown empty category archives with404; search intentionally accepts no results but must be noindex. Out-of-range pagination should404 or canonicalize appropriately, without infinite empty200 archives.

Evidence: `src/routes/$.tsx:39; src/components/cms/templates.tsx:planPath`.

### medium: structured data

No JSON-LD was present in any of349 initial server responses.

Use WebSite/Organization for site, TechArticle or Article only on authored lessons, BreadcrumbList for visible breadcrumb hierarchy, CollectionPage on real hubs, WebPage on quizzes. Include actual dates, canonical absolute URLs, truthful organization-author name. No fabricated image/review/rating/course/job claims.

Evidence: `src/routes/$.tsx:90; src/routes/index.tsx:5`.

### high: eligibility

Published local fixtures include short sample articles and topic hubs outside Java (for example python/python-lists body13words). Published alone does not mean editorially ready.

Track explicit seo_indexable or editorial-ready flag; sitemap and meta robots must share this policy. Do not infer readiness solely from word count because functional quiz/hub data can be valuable without long body prose.

Evidence: `src/data/fixtures.json`.

### medium: duplicate title

Three pairs of OpenAI/Claude tutorial titles are identical and generic.

Qualify tool name and task in titles: ChatGPT/Codex getting started versus Claude/Claude Code getting started, distinct prompting/review tasks.

Evidence: `src/data/fixtures.json`.

### medium: security

Local dev sample responses show none of CSP, HSTS, X-Frame-Options, nosniff, Referrer-Policy. This is not proof of deployed edge header state.

Add nosniff, Referrer-Policy and frame protection to public response path; evaluate nonce-based CSP with framework scripts and permitted media, avoid untested restrictive CSP. HSTS only on HTTPS production responses.

Evidence: `src/server.ts:47`.

### launch check: public crawl

Public Workers lesson/robots/sitemap returned403 Cloudflare1010 to this audit client. Web tool also could not access them.

Check bot/security policies and Search Console live URL tests using actual verified Googlebot, not spoofed user-agent strings. Do not claim public site accessible or indexed until checked.

Evidence: `Cloudflare edge configuration outside checkout`.

### launch check: public domain

No purchased AITrove domain is confirmed by user; local preview cannot be indexed publicly.

Use current Workers public origin when publishing now, switch SITE_URL and redirects once purchased domain is connected. Never hardcode an unowned domain as canonical.

## Headless WordPress sitemap boundary

The CMS plugin registers aitrove_entry as public:false in wordpress/aitrove-cms/aitrove-cms.php:17. Do not assume the WordPress core sitemap includes these frontend lessons. Generate the frontend sitemap from published AITrove API records and canonical frontend origin; never submit CMS admin URLs as lesson URLs. API list limit is100, so paginate all records with an explicit failure path rather than silently truncating. For >50,000 eligible URLs or50MB uncompressed, split files and use a sitemap index. Use actual modification dates rather than build time.

## Structured data validation policy

Use Organization author when the page visibly credits AITrove Editorial; do not invent a person or credential. Article dates must use the same visible publication/update records. Images should represent the actual lesson where provided, not pretend the site logo is a subject diagram. BreadcrumbList URLs must match real breadcrumb links, not merely the uppercase subject slug. Quizzes can be WebPage without claiming Google quiz rich results. Course code is archived; omit course offers, prices and ratings.

## Launch verification still required

This audit client received403 Cloudflare1010 on public Workers lesson, robots and sitemap URLs. That proves this client's access failure; it does not prove Googlebot is blocked. Inspect edge bot/security settings and Search Console live URL tests. The public origin/domain, indexing, CWV field data, search-query alignment, rank/traffic and rich-result eligibility remain unverified here. Localhost is not publicly crawlable.

Recheck raw HTML for canonical/robots/JSON-LD, verify all sitemap URLs return200 and are canonical/indexable, exclude utility/archived/sample entries, parse XML/JSON-LD, test pagination and CMS100-entry boundary, and test404/alias redirects after fixes.

## Primary documentation reviewed

- [Google sitemap guidance](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap): use absolute preferred URLs, accurate lastmod, proper size limits and discovery; submission is a hint, not an indexing guarantee.
- [Google canonical guidance](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls): align canonical and redirect signals.
- [Google Article markup](https://developers.google.com/search/docs/appearance/structured-data/article): truthful relevant article fields.
- [Google JavaScript SEO](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics): initial status and metadata matter.

## Repairs implemented after initial audit

Added shared frontend SEO configuration/readiness helpers and metadata-only sitemap handling. Public origin validates as an HTTPS origin and defaults to the existing Workers host. Unset preview mode defaults to true; preview remains globally noindex with an intentionally empty valid sitemap. Only published, public, explicitly reviewed data.seo_ready:true entries can be indexed after production mode is enabled. Utility/filter/unready pages stay noindex.

Ready lessons emit Article and BreadcrumbList JSON-LD; hubs emit CollectionPage; quizzes emit LearningResource. Author is the visible editorial Organization. Canonical/OG URLs and logo references are absolute. Unknown empty category archives now404; safe content aliases308 to normalized case/slash. Dynamic robots.txt references the configured frontend sitemap. The old static asset was removed to avoid static-asset bypass of configuration.

Sitemaps use1000-entry chunks with an index when needed, actual lastmod timestamps, and metadata-only CMS responses. CMS page bounds are explicit and over-capacity/error cases fail instead of silently omitting pages. WordPress plugin0.3.2 indexes readiness on save/import and exposes only published ready metadata; draft/private and archived course content stays excluded.

Validation:22 production helper/pagination assertions passed on1005 eligible synthetic entries (first chunk1000+home, second5); readiness/mode/origin/draft/course/utility checks passed. PHP syntax, targeted ESLint and diff whitespace checks passed. Raw local HTTP confirms canonical/noindex, utility titles,404 empty category, normalized alias, configured robots and empty preview sitemap. No production build or deployment was performed by the specialist. Parent-owned templates.tsx has an existing download_path typecheck error at this snapshot; SEO-owned files are typecheck-clean.

Parent still must mark reviewed fixture readiness, align visible section breadcrumbs with schema, build after stopping dev, update/reimport CMS plugin data, then explicitly launch mode on the correct public origin. Public Cloudflare bot access, Search Console indexing and field Core Web Vitals remain unverified. No guaranteed ranking claim follows these fixes.

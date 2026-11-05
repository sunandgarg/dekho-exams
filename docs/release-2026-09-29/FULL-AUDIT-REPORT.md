> Release snapshot at 4c7db6b. Current Java/Spring counts, exports, checks and remaining scope are in [the expansion handoff](../java-spring-expansion/EDITORIAL-HANDOFF.md).

# AI Trove SEO audit — 29 September 2026

Verification passed:184 compiled code units,173 executions and158 exact outputs; all168 quiz answers/explanations; six viewport widths;359 built content responses;221 eligible sitemap URLs; seven noindex utilities; four404 boundaries;308 content aliases; static download/map headers.

Scope: current isolated checkout, all 359 published public content records, 219 Java routes, shared templates, responsive screens and built Cloudflare runtime. Four archived course records remain hidden. Local implementation evidence does not establish the currently deployed website state. This release is a GitHub review branch, not a deployment.

## Result

The populated Java curriculum now has 195 articles, 10 hubs and 14 quiz banks with 168 explained questions. Every Java route is reachable from a hub, and the final graph has zero broken body, related, module or tab targets and zero Java orphans. Titles and descriptions are unique across Java. The graph contains 617 body links, 424 related links, 225 module links and 100 tab links; these are different edge sets and should not be summed as unique links.

All reviewed Java records plus the truthful editorial profile have explicit readiness metadata: 220 content URLs. Production sitemap eligibility adds the homepage, giving 221 URLs. The remaining 139 public records are not launch-ready and stay noindex, including thin starter content outside Java. Public search-result pages, accounts, login/editor tools, attempt/results, archived courses, diagnostic downloads and error pages do not belong in the search sitemap.

Preview is intentionally globally noindex with an empty sitemap. It will not rank in this mode. For launch, import reviewed content into WordPress, set the real frontend/CMS origins, explicitly disable preview mode, rebuild and verify the public site. A sitemap aids discovery; it neither guarantees indexing nor rankings. Google documents that distinction: https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview.

A credible overall SEO Health Score is not issued: live indexation, query impressions, backlinks and field Core Web Vitals were not available. A made-up aggregate would hide these limits. Automated local checks and scoped findings are reported instead.

## Technical repairs

Initial responses had no canonicals or structured data, sitemap routes returned404, utilities lacked noindex rules and unknown category archives returned empty200s. The current implementation adds one configured canonical origin, real pagination canonicals, permanent case/trailing-slash redirects, sitemap/robots endpoints, proper invalid-path404 responses, useful utility titles and matching noindex rules.

The frontend sitemap reads only published ready public records, excludes courses/utilities and uses actual valid modified dates. WordPress metadata pagination is separate from the normal content API's100-record limit. More than1,000 eligible URLs produce sitemap index/chunk files. A synthetic1,005-entry test verified two chunks. Preview sitemap is deliberately empty. Existing WordPress records need reimport/save to populate the new indexed readiness meta field.

Structured data reflects the page: Article and visible breadcrumbs for lessons, CollectionPage for hubs, LearningResource for quizzes, and WebSite/Organization on the homepage. There are no fabricated reviews, credentials, ratings or course claims. The article author is the editorial organization rather than a fictional person. The visible article breadcrumb uses the actual section name.

Workers adds nosniff, frame protection and Referrer-Policy. Error, utility and preview responses carry X-Robots-Tag. Static assets can bypass Worker response headers; downloads and the coverage map now use explicit Worker-first asset routing plus `_headers`, with noindex verified on the built runtime. Private credentials never belong in Vite public variables.

## Search intent and content

Java LinkedList, HashMap internals, API failure cases and version-specific topics use canonical individual lessons. The Java hub is a roadmap, not a copy of every article. Quiz banks have distinct preparation and explanatory review; examples, exercises and projects retain their own task-oriented intent. The four expanded lessons address HashMap internals, enum collection copy/null boundaries, annotation consumer/processing differences and BigDecimal equality/scale.

The five requested websites were inspected for coverage; technical contracts were verified against primary API/source documentation. Original programs and fresh explanations were written rather than modifying copied tutorial examples. Sources are in the editorial handoff. Java facts/API syntax, third-party logos and open-source dependency code are not exclusive AI Trove property. Generated writing is not claimed to be human-authored or detector-proof.

There is no evidence that every topic matches a high-volume query, outranks competitors or will rank. Search Console data after launch is needed to measure impressions, intended query groups, CTR and landing-page performance. Do not create duplicate near-identical pages solely for keyword variants. Google prioritizes useful people-first content: https://developers.google.com/search/docs/fundamentals/creating-helpful-content.

57 non-Java thin article candidates and39 repeated starter bodies were identified before repairs. They remain unready; bulk publishing them would lower content quality. Paired ChatGPT/Claude starter titles were qualified, but changing titles alone does not make their bodies publishable.

## Performance, images and accessibility

The unchanged header artwork now uses a21,274-byte WebP instead of a492,178-byte PNG (95.7% smaller). Seven local font files have lossless WOFF packaging; their combined bytes fell55.5%. The homepage's four loaded font weights fell55.9%. Original fonts and licences are preserved. The original large artwork is retained as source material.

Desktop/mobile checks include1440,1024,768,390,360 and320 pixels. The sixteen approved homepage cards remain unchanged. Quiz landings retain active Java tabs, curriculum, Contents controls and reading preferences. Quiz attempts/results intentionally use the focused question/review workspace. Previous/next controls follow actual curriculum order, move subtly on hover/focus and disable motion when reduced motion is requested.

No Lighthouse audit or field LCP/INP/CLS data was available. Unthrottled development paint observations are not field CWV. The large shared JavaScript/template payload still deserves route splitting and a throttled production audit. An accessible layout does not establish a complete WCAG certification; keyboard/focus, viewport overflow and the specified controls were checked.

## AI search and external evidence limits

Definitions, bounded examples, version labels, costs and failure cases make Java passages easier to cite. No llms.txt or special markup guarantees AI citations, and that file is not a Google indexing requirement. The sitemap/crawl/structured-data rules are shared with normal search readiness.

A separate client's request to the existing public workers.dev deployment received Cloudflare403/1010. This does not prove Googlebot is blocked. After deployment, verify public response headers and use Search Console URL Inspection; domain/DNS setup and bot policy checks remain. No live GSC, GA4, CrUX, backlinks or search-volume data was supplied, and no traffic/ranking estimates are invented.

## Evidence

See `java-program-check.json`, `java-release-browser-check.json`, `seo-publish-runtime-check.json`, `seo-content-review.json`, `seo-technical-review.json`, `seo-visual-performance.json`, `seo-review-asset-optimization.json` and the editorial handoff. Current checks are distinct from earlier unchanged Maven/property/JMH checks.

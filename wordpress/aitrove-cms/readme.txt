=== AITrove Content API ===
Contributors: aitrove
Tags: headless, content, education
Requires at least: 6.4
Requires PHP: 8.0
Stable tag: 0.3.2
License: GPLv2 or later

Editorial content and read-only public API for the AITrove.in frontend.

== Installation ==
1. Upload the aitrove-cms folder to wp-content/plugins/ or upload the plugin ZIP through Plugins > Add New.
2. Activate AITrove Content API.
3. Add entries in Learning Content. Draft entries remain private; published entries become available through /wp-json/aitrove/v1/entry?path=... and /wp-json/aitrove/v1/entries.
4. Set the Cloudflare frontend WORDPRESS_URL and VITE_WORDPRESS_URL to this WordPress origin.
5. To import the prototype data with WP-CLI: wp aitrove import /absolute/path/to/aitrove-preview-content.json

The post title is the page title. Choose a template type and set a unique public path without leading slash. New AI Trove tutorials use semantic HTML (p, h2, h3, ul, li, strong, pre/code with language classes, and internal a links). Legacy Markdown remains supported. The frontend removes unsupported HTML and unsafe attributes. Tutorial links only point to published internal resources; external URLs and archived course links are removed. Template data is JSON; use visual_demo: "linked-list" for the linked-list teaching model and related: [{title, path}] for internal lesson links. WordPress roles control editing and publishing. Review content before publishing.

== Templates ==
Fourteen types: subject, article, category, problem, course, video, event, job, business, page, quiz, path, company, author. The editing screen includes a structured-data guide. Saving or importing entries builds the company and author filter indexes. When upgrading, reimport or save existing entries to populate these indexes.

Learner authentication, payments, code judging and submissions are separate from WordPress editorial accounts and are not implemented by this plugin.

Version 0.2.1 adds exclude_types to the public entries endpoint so disabled frontend features are filtered before pagination. It does not delete or unpublish course entries.

Version 0.3.1 documents subject families, resource tabs and separate section curricula. AITrove Content > Import content uploads the preview JSON without WP-CLI. Import is administrator-only and protected by a nonce. Publishing is an explicit checkbox.


== Search readiness and frontend sitemaps ==
Set template data seo_ready:true only after reviewing a published entry. Unset/false entries remain visible in the preview, but the frontend sends noindex and omits them from its sitemap. Saving or reimporting entries updates the _aitrove_seo_ready metadata index; existing records must be saved or reimported after this plugin update.

Version 0.3.2 adds GET /wp-json/aitrove/v1/sitemap-entries?page=1&per_page=1000. The response contains only path, type, status, seo_ready and actual modification timestamps, total, page and per_page. Draft/private entries and courses are excluded. Page is bounded1..5000 and per_page1..1000; over-capacity datasets fail explicitly rather than silently truncate. Frontend sitemap pages use1000 entries each and a sitemap index as needed.

This private custom post type is intentionally absent from WordPress core public sitemaps. Submit the frontend /sitemap.xml, not a WordPress admin-domain sitemap. VITE_SITE_URL must be the active owned HTTPS frontend origin. It currently defaults to the existing Workers preview origin until the AITrove domain is purchased and connected. Keep VITE_PREVIEW_MODE=true (the default) until launch: all preview HTML is noindex and /sitemap.xml is intentionally empty. To launch, review content, configure the correct public origin, set VITE_PREVIEW_MODE=false and rebuild. robots.txt allows crawling so noindex can be read. The frontend generates it per build configuration; no static robots file overrides it.

SEO metadata and sitemaps support discovery, not guaranteed indexing or ranking. Verify public crawlability in Search Console, including Cloudflare bot/security policies. Authentication, saved-state, quiz attempts/results, filtered search and coverage/source download utilities stay noindex.

> Release snapshot at 4c7db6b. Current Java/Spring counts, exports, checks and remaining scope are in [the expansion handoff](../java-spring-expansion/EDITORIAL-HANDOFF.md).

# AI Trove stack and configuration

The frontend is React 19 + TypeScript, TanStack Start/Router for server rendering and routes, TanStack Query for content loading, Vite 8 with the Cloudflare plugin, Tailwind CSS 4 and Radix UI. Tutorial HTML is sanitized before rendering; highlight.js colors code. Reading controls, diagrams and local self-checks run in the browser.

Cloudflare Workers runs `src/server.ts` and serves the Vite-built assets. The ASSETS binding serves source downloads and coverage through Worker-first routes so noindex headers are retained; ordinary assets keep asset-first routing. Worker name: `aitrove-frontend`; compatibility date: 2026-09-27, nodejs_compat enabled. The development preview runs on port 3001. The homepage retains the approved 16 Explore cards. Courses remain archived behind a disabled feature flag.

WordPress is the editorial CMS through the custom PHP AITrove Content API plugin (0.3.2), intended for Hostinger. It owns editorial login, entries, drafts and publishing. The frontend reads published entries via `/wp-json/aitrove/v1/entry` and `/entries`; sitemap metadata uses `/sitemap-entries` in pages of 1,000. The reviewed content export contains 220 records, including the editorial profile. Install/update the plugin and import/save records to backfill readiness metadata before connecting it.

The verified local preview currently reads `src/data/fixtures.json`, because its server has no connected WordPress origin. This pass did not install the plugin, import records or change the Hostinger website. Lovable is the connected project/editor and GitHub repository; the frontend does not use the former Lovable Cloud database. SQL/Drizzle packages still listed in package.json are retained migration dependencies, not evidence of an active content database.

Browser-local storage holds reading-list bookmarks, learning progress and quiz results. Quiz questions/answers are public learning data. There is no authenticated cross-device progress, private answer bank, production submission judge, payment processor or jobs application backend in this configuration.

## Environment

- WORDPRESS_URL: server-only HTTPS CMS origin. Unset uses the preview fixtures; configured requests fail visibly on CMS errors rather than silently falling back to stale sample content.
- VITE_WORDPRESS_URL: public WordPress Editor link only. No admin credential belongs here.
- VITE_SITE_URL: canonical HTTPS frontend origin; currently the temporary workers.dev origin. Set the purchased domain after DNS/domain setup and redirects are verified, then rebuild.
- VITE_PREVIEW_MODE: defaults to true. Preview sends noindex and an empty sitemap. Launch requires explicit false and reviewed entries with data.seo_ready=true.

Build: npm run build. Local preview: npm run dev -- --host 127.0.0.1 --port 3001. Built-runtime verification: npm run preview. Deployment is a separate action; this pass pushes a review branch and does not merge or deploy it. The Cloudflare plugin runs built previews inside the Workers runtime: https://developers.cloudflare.com/workers/vite-plugin/tutorial/.

No private environment files or credentials are included in Git or the downloadable Java source kit.

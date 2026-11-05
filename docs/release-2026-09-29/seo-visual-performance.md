# AITrove visual, image and performance audit

Checked 29 September 2026 on the local Vite development preview, `http://127.0.0.1:3001`. This is a baseline audit before the current UI fixes. Four routes were loaded in new browser contexts at 1440, 390 and 320 pixels: homepage, Java overview, LinkedList article, Java 25 quiz landing. All 12 responses were HTTP 200, all pages had exactly one visible H1, no page produced a browser error, and none had document horizontal overflow. Screenshots are named `seo-review-*` in this output directory.

## Asset fixes completed after the baseline

The header now loads a 256 × 256 lossless WebP copy, 21,274 bytes instead of 492,178 bytes: a 95.7% reduction. The artwork and original source file remain intact, and CSS still renders the mobile logo at 50 pixels with fixed square dimensions. Seven fonts were packaged in WOFF1 without changing or subsetting any font tables. Total compressed font bytes are 536,084 instead of 1,205,972: a 55.5% reduction. The four weights used by the homepage now total 366,020 bytes instead of 829,444: a 55.9% reduction. TTF fallback URLs and OFL licences remain.

Every WOFF table was decompressed and compared byte-for-byte with its source. All seven WOFF files loaded in Chromium; no font decoding or console errors appeared. The optimized homepage screenshot preserves the previous appearance. This follows the [standard WOFF lossless packaging format](https://www.w3.org/TR/WOFF/). WOFF2 conversion is still deferred because no installed fontTools/Brotli or woff2 converter was available; no packages were installed.

The follow-up Java layout and navigation review is in `java-release-visual-review.md/json`. It confirms the Java 25 landing now uses the shared learning layout and that keyboard focus/reduced-motion behavior work. Quiz attempt/result still use the standalone practice wrapper.

## Initial findings (before fixes)

1. **Header image download is oversized.** The brand PNG is 1254 × 1254, 492,178 bytes (480.6 KiB), displayed at 50 × 50 CSS pixels on mobile. An image with the same appearance at 100–150 pixels should reduce the repeated first-page download. Preserve explicit dimensions and the decorative empty alt text because the adjacent text identifies AITrove.
2. **Font downloads are larger than needed.** Seven local TTF files total roughly 1.15 MiB. The homepage fetched four fonts totaling 829,444 decoded bytes: Source Sans 3 weights 400/600/700 plus Nunito 800. Local delivery and `font-display: swap` are good. WOFF2 conversion, careful glyph subsetting, and checking whether variable fonts replace repeated files are the next steps. Retain the included OFL licences and verify code symbols, punctuation and non-Latin content. The font-loading recommendation follows [Chrome web.dev font guidance](https://web.dev/articles/optimize-webfont-loading).
3. **Production JavaScript deserves a mobile lab pass.** The existing production main bundle is 1,097,572 bytes raw, 323,276 gzip. The tutorial renderer eagerly imports six language grammars. Route wrappers are split, but the largest client bundle holds much of the application. Split infrequently used templates/visualizers and consider loading only the active grammar. Preserve server-rendered article text, links and code. These file sizes do not by themselves establish a failing CWV result.
4. **Java quizzes break the reading context.** The Java 25 quiz landing has a generic knowledge-check page and no Java tabs, lesson list or mobile contents control. Its screenshot confirms the user's complaint. The quiz attempt itself is usable at 320 pixels: options wrap within the page; labels are 238 pixels wide and 58–82 pixels tall; keyboard Space selects a radio option, and Next changes the question. Put Java quiz landing, attempts and results inside the Java learning wrapper, while retaining explicit stage URLs.
5. **Public performance status is unverified.** No Lighthouse executable or bundled package was available, and no PSI/CrUX real-user data was obtained. Run production mobile/desktop Lighthouse and check field data after publishing to the final canonical host. Do not promise that every page will rank or that local speed proves good real-user CWV.

## What works

- Homepage cards have coherent alignment at 390 and 320 pixels, readable headings, identifiable subjects and large full-card links. The topic SVGs range from about 0.2–9 KiB. Their empty alt attributes are appropriate because they are decorative under `aria-hidden` and text labels identify the links.
- Sample article text starts within the mobile viewport. LinkedList's long heading wraps instead of creating overflow. Code is syntax highlighted and remains inside a horizontally scrollable code container.
- Native forms have labels. Mobile quiz option labels provide large touch areas. The contents sheet opens, Escape dismisses it after the close animation, and keyboard focus returns to its trigger.
- The mobile navigation bar remains below the article and the contents control remains above it in the captured views. No blocking cookie modal appeared.
- Images loaded on these four routes have explicit width and height. There is no separate raster hero illustration. Above-fold logos load eagerly; they are not delayed by lazy loading. This is consistent with [Chrome’s LCP loading guidance](https://web.dev/articles/optimize-lcp).
- Local fonts avoid third-party font requests. Existing styles have reduced-motion rules for transitions and scrolling. Any new previous/next animation should retain these rules and show equivalent keyboard focus feedback.

## Lab observations and limits

Unthrottled local development FCP values ranged from 104–736 ms. Browser-observed layout-shift values without recent input summed from 0.0011–0.0343 across the first loaded view. The final recorded LCP entry appeared in the same 104–736 ms range. These are diagnostic observations from one run per route/width, without CPU/network throttling, using a Vite server and a fast local machine. Raw shift sums are **not** a formally calculated CLS session-window score; see the [official CLS definition](https://web.dev/articles/cls). INP, field LCP/CLS, TBT, Lighthouse performance and accessibility scores remain unavailable.

Development resource bodies total approximately 17–18 MB because modules and HMR sources are unbundled. Do not report this as the production transfer size. The production bundle file sizes above were measured separately from `dist/client/assets`.

Small breadcrumb, author and local design ribbon links exist, but automated small-target checks include inline text and the visually hidden skip link, which have exceptions or separate focus behavior. No blanket WCAG failure is claimed. The local comparison ribbon points to port 3000; remove preview-only controls before public publishing.

## Evidence files

- `seo-visual-performance.json`: complete route/viewport records, browser metrics, resource inventory, images, production asset weights and prioritized issues.
- `seo-review-interactions.json`: quiz keyboard and mobile contents checks.
- `seo-review-home-390.png`, `seo-review-java-linkedlist-320.png`, `seo-review-quizzes-java-25-320.png`, `seo-review-quiz-attempt-320.png`: selected visual evidence. Further screenshots cover every route at every width.
- Shared audit caches were written to `.seo-cache/pages/{route}/visual.json`, `performance.json` and `images.json`. Keep `.seo-cache/` out of source control.

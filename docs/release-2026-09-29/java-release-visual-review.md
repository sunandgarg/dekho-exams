# Java quiz and lesson-navigation release visual review

Reviewed the current integrated local preview on 29 September 2026 at desktop 1440 pixels and mobile 390/320 pixels. The browser sessions were isolated from the user's session. This review changed no application files or server processes and makes no Lighthouse or field Core Web Vitals claim.

## Confirmed fixes

The Java 25 quiz landing now matches the reading layout requested in the screenshots. All three widths show Java section tabs with **Quizzes** active, reading preferences, the Java 25 quiz title, local quiz metadata, and original prerequisite links. The desktop lesson rail includes the selected quiz. On mobile, Contents opens the same grouped quiz curriculum, including a single link to the current Java 25 quiz; lesson and page-content views remain separate. The modal's close button and active lesson presentation are visible. The 320-pixel screenshot shows a readable layout rather than a squeezed desktop sidebar.

The previous/next lesson cards now have purposeful movement and visible color separation. Tested on the manifest project, both links resolve to published Java lessons. Desktop uses side-by-side cards; 390 and 320 pixels stack them without overflow. Keyboard focus produces a visible 3-pixel outline. The focused card lifts 2 pixels; next and previous arrows move 4 pixels in their respective directions. Transitions last 180 milliseconds. With reduced motion enabled, transforms and transitions are removed. There is no continuous animation while reading.

All tested quiz landing, attempt, result and lesson-navigation views stayed within their viewport widths. No browser page errors appeared. Native radio controls on the attempt page remain present, and submitting an isolated practice answer reaches a result page with an answer-review heading. Results remain local practice, not a server-side judge or credential.

## Remaining presentation decisions

Quiz **attempt and result** pages still use the standalone practice wrapper: they omit Java section tabs, curriculum rail and mobile Contents. The screenshot complaint about opening a quiz from the Java curriculum is fixed on the landing page. If retaining curriculum context throughout every quiz stage is intended, these two stages remain to be wrapped.

The Start quiz button is 36 CSS pixels tall; it is usable, but increasing it to 44 pixels would provide a larger mobile touch target. No accessibility conformance failure is asserted from this measurement alone.

The preview-only ribbon remains visible at the top of the local pages. It should not be shipped as a public production feature. The homepage's approved 16-card design was preserved; this follow-up changed no homepage or asset files.

## Evidence

- `java-release-visual-review.json`: exact route/viewport assertions, link rectangles, computed motion/focus styles and browser errors.
- `seo-review-release-quiz25-1440.png`, `seo-review-release-quiz25-390.png`, `seo-review-release-quiz25-320.png`: shared Java quiz layout.
- `seo-review-release-quiz25-contents-390.png` and `seo-review-release-quiz25-contents-320.png`: modal curriculum after the opening animation completes.
- `seo-review-release-navigation-{1440,390,320}.png`: previous/next cards in desktop/mobile layouts.
- `seo-review-release-navigation-focus-{1440,390,320}.png`: keyboard-focus presentation.

The baseline performance/image audit and verified asset-delivery reductions remain documented separately in `seo-visual-performance.md/json`. Production performance and field CWV still need measurements on the published canonical host.

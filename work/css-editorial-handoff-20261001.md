# CSS curriculum editorial handoff — 2026-10-01

The local fixture now has 182 CSS articles: three original starter lessons and 179 new lessons across fifteen content passes. Nine added hubs organize foundations, selectors, layout, type and media, responsive rules, interaction and accessibility, projects, quizzes, and property decisions. The CSS root and added hubs make ten hubs in total. Fifteen quiz banks have 12 explained questions each. The CSS bodies contain 1248 verified internal links. Each new lesson has one original worked sample, an explicit cost or verification discussion, and a Common Mistakes section. The public lesson bodies contain no external source links.

## Scope and review

The material covers stylesheet loading, cascade layers, custom properties and registration, inheritance, native nesting, scoped rules, sizing units, box sizing, margin collapse, spacing shorthands, size constraints, containment, borders and outlines, combinators, attribute and structural selectors, specificity, relational selectors, pseudo-elements, flow, flexbox, grid and subgrid, grid areas and auto-placement, floats, positioning, isolation, pointer targeting, selection, intrinsic sizing, overflow, scroll snapping and boundaries, scroll target offsets, content visibility, multi-column layout, stacking, media and container queries, logical properties, viewport units, fluid type, text wrapping, hyphenation, writing modes, link decoration, table and form styling, feature queries, cascade reset keywords, fonts, images, background sizing, filters, clipping, backdrop filters, color, focus, reduced motion, transitions, themes, print fragmentation, cursor cues, scrollbar gutters, touch gestures, measured rendering hints, transform pivots, blending, masks, shaped text flow, color mixing, active color schemes, numeric glyph alignment, page margins, smooth scrolling, form sizing and interaction states, font loading and fallback metrics, balanced headings, tab width, scrollbar accessibility, forced-color exceptions, contrast preferences, print, keyframes, and three applied page exercises. Seven modern-behavior lessons cover container query units, style queries, entry and discrete transitions, intrinsic-size interpolation, anchor positioning, and view timelines. Eight type, color, and asset lessons cover variable font ranges, optical sizing, synthetic weight, finite counter styles, image candidate sets, wide-gamut output, oklch, and clipped headline decoration. A scroll-and-state set covers scroll anchoring exclusions, display contents, snap stops, focus-within, fragment targets, focal cropping, scrollbar color, and underline ink skipping. A type-and-overlay set covers Unicode font ranges, literal identifier glyphs, language selectors, visual case, wrapped decoration, modal backdrops, popover-open state, and local background attachment. The preceding eight cover native file buttons, read-only controls, mixed checkboxes, default submitters, required and optional controls, placeholder contrast, filtered sibling counting, and WebVTT cue styling. The preceding eight cover semantic direction selectors, vertical glyph posture, text-emphasis marks, pixel-art interpolation, verified variable-font axes, background layer blending, full-screen media layout, and print widow/orphan controls. The next eight distinguish sparse grid tracks, clipped and hidden overflow, native open and user-valid states, reduced transparency, additive animation, printed color requests, and editorial line wrapping. The preceding eight cover shadow host variants, exposed parts, assigned slot styling, custom text highlights, unique view-transition names, transition snapshots, selector-support gates, and baseline alignment. The latest eight cover custom-element definition and internal states, disclosure content, text-fragment highlighting, cross-document transition opt-in, script availability, modal state, and picture-in-picture presentation. These features have functional fallbacks and require browser checks in the target support matrix. The examples are editorial teaching samples, not a working receipt backend or an official incident archival workflow. Nine illustrative asset paths across the CSS lessons must be mapped to real deployment files before reuse in an application: `/assets/receipt-view.css`, `/assets/case-header-texture.webp`, `/assets/receipt-header.woff2`, `/assets/ledger-variable.woff2`, `/assets/case-map-1x.webp`, `/assets/case-map-2x.webp`, `/assets/registry-latin.woff2`, and `/assets/registry-greek.woff2`, and `/assets/annotation-axis.woff2`. The two registry fonts are hypothetical subsets; an editor must verify glyph coverage, licensing, byte size, and range declarations against real files. The annotation font is also hypothetical: confirm the GRAD axis, its supported range, licensing, and actual glyph output before publication.

## Research checked

The preferred tutorial starting points were checked first:

- https://www.geeksforgeeks.org/css/css-tutorial/
- https://www.w3schools.com/css/
- https://codingnomads.com/js-101-basic-css
- https://www.geeksforgeeks.org/css/css-complete-guide/
- https://www.w3schools.com/cssref/css_functions.php

No dedicated CSS tutorial was confirmed at the guessed BeginnersBook path. CodingNomads has a basic CSS lesson, while technical points were cross-checked against primary references:

- https://www.w3.org/TR/css-cascade-5/
- https://www.w3.org/TR/selectors-4/
- https://www.w3.org/TR/css-flexbox-1/
- https://www.w3.org/TR/css-grid-1/
- https://www.w3.org/TR/css-contain-3/
- https://www.w3.org/TR/mediaqueries-5/
- https://www.w3.org/TR/css-transitions-1/
- https://www.w3.org/TR/css-animations-1/
- https://www.w3.org/TR/css-color-adjust-1/
- https://www.w3.org/TR/css-nesting-1/
- https://www.w3.org/TR/css-scroll-snap-1/
- https://www.w3.org/TR/css-overscroll-1/
- https://www.w3.org/TR/css-values-4/
- https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Styling_basics
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40scope
- https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Grid_layout/Subgrid
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/content-visibility
- https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Box_model/Margin_collapsing
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/box-sizing
- https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Grid_layout/Auto-placement
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/background-size
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/appearance
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/aspect-ratio
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/contain
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/isolation
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/pointer-events
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/user-select
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/scroll-margin-top
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/scroll-padding-top
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/hyphens
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/writing-mode
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/break-inside
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/all
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/clip-path
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/backdrop-filter
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/cursor
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/scrollbar-gutter
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/touch-action
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/will-change
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/transform-origin
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/mix-blend-mode
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/mask-image
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/shape-outside
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/font-variant-numeric
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/scroll-behavior
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/color_value/color-mix
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/color_value/light-dark
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40page
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/field-sizing
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/caret-color
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/font-size-adjust
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/text-wrap
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/tab-size
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/scrollbar-width
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/forced-color-adjust
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3Aplaceholder-shown
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3Auser-invalid
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3Aautofill
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40font-face/font-display
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40media/prefers-contrast
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/length
- https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Containment/Container_size_and_style_queries
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40starting-style
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/transition-behavior
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/interpolate-size
- https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Anchor_positioning/Using
- https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Scroll-driven_animations/Timelines
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/animation-timeline
- https://www.geeksforgeeks.org/css/how-to-use-font-optical-sizing-property-in-css/
- https://www.w3schools.com/cssref/atrule_counter-style.php
- https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Fonts/Variable_fonts
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/font-optical-sizing
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/font-synthesis-weight
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40counter-style
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40counter-style/fallback
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/image/image-set
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40media/color-gamut
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/color_value/oklch
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/background-clip
- https://www.geeksforgeeks.org/css/css-scroll-snap-stop/
- https://www.w3schools.com/cssref/css_pr_scroll-snap-stop.php
- https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Scroll_anchoring/Overview
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/display
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/scroll-snap-stop
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3Afocus-within
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3Atarget
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/object-position
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/scrollbar-color
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/text-decoration-skip-ink

Latest reference checks for the type and overlay batch:

- https://www.w3schools.com/Cssref/css3_pr_box-decoration-break.php
- https://www.w3schools.com/cssref/sel_popover-open.php
- https://www.w3schools.com/cssref/sel_backdrop.php
- https://www.w3schools.com/cssref/sel_lang.php
- https://www.geeksforgeeks.org/css/css-complete-guide/
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40font-face/unicode-range
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/font-variant-ligatures
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3Alang
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/text-transform
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/box-decoration-break
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3A%3Abackdrop
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3Apopover-open
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/background-attachment

Latest reference checks for native states and cues:

- https://www.w3schools.com/cssref/sel_file-selector-button.php
- https://www.w3schools.com/cssref/css_ref_pseudo_classes.php
- https://www.geeksforgeeks.org/css/css-complete-guide/
- https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Forms/Advanced_form_styling
- https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/readonly
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3Aindeterminate
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3Adefault
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3Arequired
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3A%3Aplaceholder
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3Anth-child
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3A%3Acue

The lesson prose and scenarios were written fresh. This research record does not make the underlying CSS language or syntax proprietary, and no AI-detection score is claimed.

Latest reference checks for direction, typography, and media paint:

- https://www.geeksforgeeks.org/css/css-dir-selector/
- https://www.w3schools.com/cssref/css3_pr_image-rendering.php
- https://www.w3schools.com/cssref/pr_background-blend-mode.php
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3Adir
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/text-orientation
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/text-emphasis
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/image-rendering
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/font-variation-settings
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/background-blend-mode
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3Afullscreen
- https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Paged_media

Latest reference checks for rendering contracts and output choices:

- https://www.geeksforgeeks.org/css/auto-fit-vs-auto-fill-property-in-css-grid/
- https://www.w3schools.com/cssref/css_ref_pseudo_classes.php
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/overflow
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40media/prefers-reduced-transparency
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3Aopen
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3Auser-valid
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/animation-composition
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/print-color-adjust
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/text-wrap

Latest reference checks for component boundaries and view transitions:

- https://www.geeksforgeeks.org/css/css-align-items-property/
- https://www.w3schools.com/cssref/css3_pr_align-items.php
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3Ahost_function
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3A%3Apart
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3A%3Aslotted
- https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Custom_highlight_API
- https://developer.mozilla.org/en-US/docs/Web/API/CSS_Custom_Highlight_API
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/view-transition-name
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3A%3Aview-transition-old
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3A%3Aview-transition-new
- https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API/Using
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40supports
- https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Box_alignment/Overview
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/align-items

Latest reference checks for native states and navigation:

- https://www.geeksforgeeks.org/css/css-selectors/
- https://www.w3schools.com/cssref/css_ref_pseudo_classes.php
- https://www.w3schools.com/cssref/sel_modal.php
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3Adefined
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3Astate
- https://developer.mozilla.org/en-US/docs/Web/API/CustomStateSet
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3A%3Adetails-content
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3A%3Atarget-text
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40view-transition
- https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API/Using
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40media/scripting
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3Amodal
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/%3Apicture-in-picture

## Checks and delivery

- `python3 scripts/check-css-content.py`: 182 articles, 10 hubs, 15 quiz banks, 180 questions, 1248 internal body links, zero curriculum orphans.
- `node scripts/check-css-samples.mjs`: 182 snippets parsed successfully.
- `python3 scripts/check-html-content.py`: 156 HTML articles, 1080 resolved HTML body links, and zero orphans. Forty-nine HTML articles contain 109 CSS body links.
- `npx tsc --noEmit`: pass.
- `npx eslint src`: 0 errors, 7 pre-existing fast-refresh warnings.
- `VITE_SITE_URL=https://aitrove.in VITE_PREVIEW_MODE=false npm run build:pages`: exit 0, with existing large-chunk warnings and a Wrangler log-write EPERM diagnostic in the restricted environment.
- `git diff --check`: pass.

`scripts/export-css-for-wordpress.py` produced `work/aitrove-css-import-drafts.json` with 208 records: 207 CSS pages/quizzes plus the editorial author entry. The export forces draft status and `seo_ready=false` for review. It has not been uploaded to WordPress.

## Remaining

The current workspace has no verified WordPress endpoint or credentials for this site. Cloudflare deployment authentication was unavailable in a preceding content pass, and no live CSS route was verified in this pass. An editor must review the draft payload, resolve the nine illustrative asset paths, import and publish the approved records in WordPress, and check the rendered pages on the live site. Further CSS coverage, including exhaustive property documentation and browser compatibility matrices, remains open; “fully” is not a finite claim over all CSS features and future specifications.

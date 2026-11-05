"""Create original CSS lessons, linked sections, and review-ready quizzes."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path


root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
ROOT = "css/css-tutorial"
sections = {
    "foundations": ("CSS Foundations", "Write stable declarations, then trace why a value wins."),
    "selectors": ("CSS Selectors", "Match elements by their role and state without brittle document paths."),
    "layout": ("CSS Layout", "Allocate space, align components, and contain long content."),
    "type-media": ("CSS Type and Media", "Keep type and images readable while assets load."),
    "responsive": ("Responsive CSS", "Adapt to containers, writing modes, and available space."),
    "interaction": ("CSS Interaction and Accessibility", "Preserve visible focus, user preferences, and print output."),
    "projects": ("CSS Projects", "Combine layout and visual rules in bounded page tasks."),
    "quizzes": ("CSS Quizzes", "Check applied CSS decisions and failure modes."),
}
specs = []


def add(slug, section, title, summary, intro, mechanics, sample, cost, mistakes, related):
    path = "css/" + slug
    assert path not in by_path and all(key in by_path or key.startswith("css/") for key in related)
    specs.append(dict(path=path, section=section, title=title, summary=summary,
                      intro=intro, mechanics=mechanics, sample=sample, cost=cost,
                      mistakes=mistakes, related=related))


# Individual lesson definitions follow. Finalization is at the end of this file.

add("authoring-and-loading", "foundations", "CSS files and rules: keep presentation out of the document structure",
    "Attach a stylesheet once, scope its rules, and keep a usable document when it fails.",
    "A CSS rule pairs a selector with declarations. A linked stylesheet applies those rules to matching document elements without changing their meaning.",
    "A receipt page needs the same header and status colors on several routes. Put shared rules in one stylesheet rather than repeating style attributes on every element. The HTML remains the source of titles, labels, and actions; CSS supplies paint and spacing. The sample assumes the receipt stylesheet is served from a stable local asset path. If it fails to load, the heading and status text still exist. Keep critical content in markup and use a network trace to confirm the CSS file is not missing or needlessly duplicated.",
    '''<link rel="stylesheet" href="/assets/receipt-view.css">
<style>
  .receipt-status { color: #175b44; font-weight: 700; }
</style>''',
    "A linked file adds a request on first load, then can be cached across routes. Inline CSS avoids that request but repeats bytes and complicates cache invalidation when copied across pages. The snippet shows the attachment and a small local override; move that override into the shared file if several pages need it. CSS does not sanitize data or create an accessible name. Confirm the page remains understandable with styling disabled and the final asset path exists in the deployment.",
    ["Do not use CSS-generated text as the sole source of a status.", "Do not copy the same large style block into every page.", "Do not assume a linked stylesheet loaded merely because the page still renders."],
    ["css/selectors-and-cascade", "css/cascade-layers", "html/document-skeleton"])

add("cascade-layers", "foundations", "CSS cascade layers: set precedence before selectors grow",
    "Order component layers explicitly so normal declarations have a predictable owner.",
    "A cascade layer groups rules at a defined precedence level. For ordinary author declarations, later declared layers win over earlier layers before selector specificity is compared.",
    "A case-review interface loads a base skin and route-specific components. A component rule should beat a base rule without requiring an ID selector or repeated important flags. Declare layer order at the top, then assign each rule to the layer that owns it. Unlayered normal rules beat normal layered rules, so keep accidental unlayered overrides out of the file. Important declarations reverse layer order; use them only for a reviewed exception. When a declaration seems ignored, inspect its origin, importance, layer, and specificity in that order instead of adding another selector segment.",
    '''@layer base, components;
@layer base {
  .case-status { color: #31445a; }
}
@layer components {
  .case-status { color: #175b44; }
}''',
    "The computed color is #175b44 for a matching element. Layers do not add a network request or measurable layout work by themselves; their cost is organizational. A layer order changed by an early import can alter many components at once, so keep that order deliberate and test representative routes. The rule remains a color declaration, not a promise that the color has enough contrast against every background. Check theme variants and the computed style in the browser.",
    ["Do not expect a more specific selector in an earlier normal layer to win.", "Do not leave emergency unlayered rules hidden below organized layers.", "Do not assume important declarations follow the same layer order as normal ones."],
    ["css/selectors-and-cascade", "css/specificity-is-where", "css/custom-properties"])

add("custom-properties", "foundations", "CSS custom properties: share tokens without losing fallbacks",
    "Define visual tokens at an owned scope and provide a valid fallback where needed.",
    "Custom properties hold token sequences and normally inherit. The var() function substitutes a property value when the declaration is computed.",
    "A receipt surface has one border color across summary cards and form fields. Scope the token to that surface so another product section can use a different palette without a global collision. The fallback keeps the border visible if the token is absent, but it does not rescue a value that is present yet invalid for the destination property. A token that changes color may affect contrast in every component that reads it. Keep state colors paired with their backgrounds, document what owns each token, and check the computed value when a component looks unexpectedly transparent.",
    '''.receipt-surface { --receipt-border: #b7c4d1; }
.receipt-surface .receipt-card {
  border: 1px solid var(--receipt-border, #8b9bad);
  padding: 1.25rem;
}''',
    "The browser substitutes the token during style calculation; no script is required. Shared tokens reduce duplicated literals, though a large unscoped token system can make simple changes harder to trace. The fallback in this sample is an alternate border color, not a full theme. Test a card inside and outside the token scope, then inspect dark and forced-color environments. A custom property does not automatically type-check like a standard property unless explicitly registered.",
    ["Do not assume var() fallback applies after an invalid substituted value.", "Do not put every token on the document root without an owner.", "Do not change foreground colors without reviewing their paired surfaces."],
    ["css/cascade-layers", "css/colors-and-contrast", "css/dark-mode-and-forced-colors"])

add("inheritance-and-defaults", "foundations", "CSS inheritance and defaults: reset only the property you mean",
    "Distinguish inherited text properties from noninherited box properties.",
    "Inheritance passes some computed values from a parent to its children. Other properties use their own initial value unless the cascade supplies a declaration.",
    "A case note inherits its text color from the page, while its border does not appear merely because the parent has one. Use inherit when a control should take the current text color; use initial when the specification's initial value is intended. The unset keyword inherits on inherited properties and uses the initial value otherwise. Revert and revert-layer ask the cascade to step back through different boundaries, so they are not generic synonyms for zero. A global reset can remove useful browser defaults such as focus outlines or list markers. Inspect the actual computed style before applying one.",
    '''.case-record { color: #21374d; }
.case-record button { color: inherit; }
.case-record .note { border: 1px solid #b7c4d1; }
.case-record .note--plain { border: initial; }''',
    "These keywords add negligible transfer and rendering cost. The maintenance risk comes from broad reset rules: a rule that changes every control may silently erase affordances on unrelated routes. In the sample, border: initial removes the border from the plain note, but it does not change the inherited text color. Verify interactive controls with keyboard focus and without custom styles. Where a component needs its own state, declare that state directly rather than relying on a distant ancestor.",
    ["Do not assume borders and margins inherit with color.", "Do not use all: unset on a control without rebuilding its visible affordance.", "Do not call initial and inherit interchangeable."],
    ["css/selectors-and-cascade", "css/custom-properties", "css/focus-visible"])

add("units-and-functions", "foundations", "CSS units and functions: size against the right reference",
    "Use rem for scalable type, percentages for available width, and clamp for bounded fluid values.",
    "CSS lengths resolve against different references. A rem is tied to the root font size; percentages depend on the property and containing block; viewport units use the viewport.",
    "An intake form needs readable text and a panel that can fill a narrow screen without becoming enormous on a wide one. Give the panel a maximum inline size and allow its actual width to be smaller. Clamp the title between two readable bounds; do not use a viewport-only font size that shrinks the title below a usable level. A percentage height often fails to behave as expected when the containing block's height is indefinite. Identify the reference dimension first. Logical inline sizing also keeps the rule useful when the writing mode changes.",
    '''.intake-panel { inline-size: min(100%, 42rem); margin-inline: auto; }
.intake-panel h1 { font-size: clamp(1.6rem, 2vw + 1rem, 2.4rem); }
.intake-panel p { max-inline-size: 68ch; line-height: 1.55; }''',
    "These calculations are cheap compared with fetching fonts or images. The real cost is a layout that only looks right at one root font size. Test at narrow viewports, 200% browser zoom, and larger user text. The ch unit is an approximate text measure based on font metrics, not an exact character count. If a fixed rem maximum clips translated words, allow wrapping and inspect the actual content rather than raising every cap blindly.",
    ["Do not assume every percentage resolves against the viewport.", "Do not make type depend only on vw.", "Do not use a fixed height for content that can grow."],
    ["css/responsive-layout", "css/fluid-type-clamp", "css/logical-properties"])

add("combinators", "selectors", "CSS combinators: select relationships without encoding every wrapper",
    "Use child and sibling relationships only when the document relationship matters.",
    "A combinator relates selector matches in the element tree. A space matches descendants; a greater-than sign matches direct children; a plus sign matches the next sibling.",
    "A review panel contains a direct status row and several nested notes. Styling only its immediate status row avoids coloring a status inside an embedded audit note. The adjacent-sibling rule gives a heading's following paragraph a tighter top margin. Neither selector creates the relationship; the HTML structure does. Use a stable class for the component root and keep relational depth short. If the DOM changes because a wrapper is added, a direct-child rule may stop matching. That may be correct, or it may reveal an overly fragile contract.",
    '''.review-panel > .status-row { border-block-start: 2px solid #175b44; }
.review-panel h2 + p { margin-block-start: .35rem; }
.review-panel .audit-note p { max-inline-size: 68ch; }''',
    "Simple selectors are rarely a bottleneck on their own. Deep chains raise maintenance cost because markup edits can silently change matching. Verify the selector against a nested audit note and a panel with multiple paragraphs. The second rule matches only the paragraph immediately after a heading, not every paragraph in the panel. If the design depends on a semantic state such as invalid input, prefer a state selector over inferring state from wrapper position.",
    ["Do not confuse direct children with all descendants.", "Do not make a selector mirror every wrapper in the current template.", "Do not use structural position as a substitute for an explicit state."],
    ["css/selectors-and-cascade", "css/pseudo-classes", "css/structural-selectors"])

add("pseudo-classes", "selectors", "CSS pseudo-classes: style interaction states without hiding them",
    "Use native focus, hover, and invalid states as additions to a stable base style.",
    "Pseudo-classes match an element's current state or relationship. They do not add a label, validate on the server, or make a noninteractive element operable.",
    "A receipt lookup field needs a clear default border and visible feedback when the browser considers its input invalid. Keep a base rule that works before interaction, then add a focus outline and an invalid border. Focus must remain visible for keyboard users even if pointer hover uses a subtler treatment. A required field may match :invalid before the person submits; choose whether that timing is helpful rather than making every blank field appear broken at page load. Server errors still need visible text and an accessible association to the control.",
    '''.receipt-lookup input { border: 1px solid #71869a; padding: .7rem; }
.receipt-lookup input:focus-visible { outline: 3px solid #205c8a; outline-offset: 2px; }
.receipt-lookup input:invalid { border-color: #9b3030; }''',
    "State selectors avoid extra script for paint changes. Their cost is testing across keyboard, touch, and validation timing; hover alone does not work on every device. Inspect color contrast on the actual background and confirm the outline is not clipped by a parent with overflow hidden. Do not communicate failure by border color alone. A real server response should return a text error and preserve the submitted value.",
    ["Do not remove outlines without a replacement focus indicator.", "Do not equate :invalid with a trusted server decision.", "Do not make hover the only way to reveal an action."],
    ["css/focus-visible", "html/form-help-and-errors", "css/selectors-and-cascade"])

add("specificity-is-where", "selectors", "CSS :is and :where: group selectors without accidental weight",
    "Choose :where for low-weight defaults and :is when grouped alternatives should retain weight.",
    "The :is() pseudo-class takes the highest specificity of its selector arguments. The :where() pseudo-class matches in a similar way but contributes zero specificity.",
    "A status component appears as either a section or an aside. Its default border should be easy for a product surface to override, so a :where() group is appropriate. A separate rule scopes the actual warning state to the component class. Do not place an ID inside :is() casually: even a branch that does not match the current element can raise the functional selector's specificity through the argument list. Calculate the competing weights and check the computed style instead of using a long selector as a guess.",
    ''':where(section, aside).status-panel { border: 1px solid #b7c4d1; }
.status-panel[data-state="held"] { border-color: #9b3030; }
.case-page .status-panel { padding: 1rem; }''',
    "A :where() default is cheap to override and adds no script. The maintenance cost is understanding that matching and specificity are separate questions. The held-state border changes only when the data-state attribute is set; CSS does not decide whether a case is held. For a production status, render that state in text as well. Test both section and aside variants and ensure a theme override can change the border without important flags.",
    ["Do not assume :is() always has the specificity of the branch that matched.", "Do not expect :where() to make the whole selector zero-weight when other selectors remain.", "Do not encode business state only in a border color."],
    ["css/cascade-layers", "css/combinators", "html/hidden-vs-aria-hidden"])

add("has-relationships", "selectors", "CSS :has: style a parent from a meaningful child state",
    "Use :has to respond to descendant state without adding a presentational class in script.",
    "The :has() relational pseudo-class matches an element when a selector relative to it matches. It can express a parent-child state relationship in CSS.",
    "A receipt field wrapper needs a stronger border when the input inside it is invalid. The wrapper rule can look for that native state, while the input remains the element that owns validation. Scope the search to a small component instead of writing a document-wide rule that relates distant content. The wrapper should not become the only error message; include visible error text after a rejected submission. A blank required input may match :invalid before the person has tried to submit, so decide whether the timing matches the product's feedback policy.",
    '''.receipt-field { border: 1px solid #71869a; padding: .75rem; }
.receipt-field:has(> input:invalid) { border-color: #9b3030; }
.receipt-field:has(> input:focus-visible) { outline: 2px solid #205c8a; }''',
    "The selector adds no JavaScript or network transfer. It can still cause more style matching than a simple class when used broadly, so profile an actual large page before making a performance claim. Test supported browsers and an unsupported-browser fallback: the base border remains usable even when :has is ignored. Keep the native input's own focus indicator as well, since the parent outline may not be close enough to identify the focused control.",
    ["Do not use :has as the only source of validation text.", "Do not apply a broad relational selector to every element on a large page without measurement.", "Do not remove the input focus indicator because its wrapper now changes."],
    ["css/pseudo-classes", "css/focus-visible", "html/aria-invalid-errors"])

add("display-and-flow", "layout", "CSS display and normal flow: choose a formatting context deliberately",
    "Understand what block, inline, and flow-root change before reaching for positioning.",
    "The display property controls how an element participates in layout. A block starts a new line, inline content follows text flow, and flow-root establishes an independent block formatting context.",
    "An audit note should follow the receipt summary in source order and contain its floated thumbnail if one is used. A flow-root wrapper can contain that float without a clearfix utility or a fixed height. This does not make the note a grid or flex container; its children still follow ordinary block flow. Use display: none only when content truly should leave layout and the accessibility tree. A hidden warning cannot help a reader. For a simple vertical article, normal flow is often already correct, with less CSS to maintain than absolute positioning.",
    '''.receipt-summary { display: block; }
.audit-note { display: flow-root; padding: 1rem; border: 1px solid #b7c4d1; }
.audit-note img { float: inline-start; margin-inline-end: 1rem; }''',
    "Flow-root adds a formatting context, not a network or script cost. The image still needs dimensions and alternate text in HTML, and floated media can make very narrow text columns hard to read. Test the note at large text sizes and remove the float below the point where it crowds prose. Do not add flow-root to every wrapper by habit; containment can change margin behavior and other layout relationships.",
    ["Do not use absolute positioning for ordinary article flow.", "Do not set a fixed height just to contain a float.", "Do not use display:none for information required to complete the task."],
    ["css/box-model-and-layout", "css/overflow-and-scroll", "html/image-alt"])

add("flexbox-sizing", "layout", "CSS flexbox sizing: make control rows wrap without clipping",
    "Use flex for one-dimensional groups and set a shrink boundary for long content.",
    "Flexbox distributes space along a main axis and aligns items across a cross axis. Flex items may retain a content-based automatic minimum that prevents expected shrinking.",
    "A case toolbar contains a title and two actions. The title can be long after translation, so the row wraps and the title is allowed to shrink. The actions keep their readable labels and do not disappear behind an overflow mask. The sample uses a flexible title group and natural button widths; it does not reorder items visually. At high zoom, wrapping is preferable to squeezing labels into unreadable controls. If the toolbar becomes a two-dimensional dashboard, grid may express the track relationships more clearly.",
    '''.case-toolbar { display: flex; align-items: center; flex-wrap: wrap; gap: .75rem; }
.case-toolbar__title { flex: 1 1 18rem; min-inline-size: 0; }
.case-toolbar__actions { display: flex; flex-wrap: wrap; gap: .5rem; }
.case-toolbar button { min-block-size: 2.75rem; }''',
    "Flex layout itself is generally cheap, but deeply nested flex containers can complicate debugging and cause unnecessary recalculation when many items change. Test an extremely long case title and 200% zoom. A min-inline-size of zero permits the title to shrink, but unbreakable tokens still need wrapping or overflow rules. Keep the source order aligned with keyboard order; order and row-reverse only change paint, not the underlying sequence.",
    ["Do not hide overflowing buttons when wrapping would preserve access.", "Do not use visual order to repair a wrong DOM order.", "Do not assume flex:1 alone defeats the item's automatic minimum."],
    ["css/grid-tracks", "css/overflow-and-scroll", "css/responsive-layout"])

add("grid-tracks", "layout", "CSS grid tracks: reserve a sidebar without letting content widen the page",
    "Use minmax(0, 1fr) for a shrinkable main track beside a bounded sidebar.",
    "Grid lays out items against rows and columns. Fractional tracks share remaining space, but intrinsic minimums can still force a track wider than its container.",
    "A receipt record has a main narrative and a metadata sidebar. The narrative can contain a long code, so its track must be allowed to shrink. The sidebar has a controlled width, and the layout becomes one column once both tracks no longer fit. Keep the main narrative first in the DOM even if a mockup places the sidebar visually elsewhere. A grid cell with a long preformatted block may also need min-inline-size: 0 and a local scroll container; one rule cannot solve every overflowing child.",
    '''.receipt-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(14rem, 18rem);
  gap: 1.25rem;
}
.receipt-layout > * { min-inline-size: 0; }
@media (max-width: 50rem) {
  .receipt-layout { grid-template-columns: minmax(0, 1fr); }
}''',
    "The browser computes track sizes on layout; the practical cost is usually a too-rigid design, not the grid algorithm. Check long identifiers, translated headings, and zoom before settling on the breakpoint. The 50rem threshold is a content-driven starting point for this example, not a device category. If the sidebar is optional, ensure it follows the narrative in reading order when the grid collapses.",
    ["Do not assume 1fr means a track can always shrink to zero.", "Do not move the sidebar in CSS while leaving an incoherent reading order.", "Do not hide overflow on the whole page to conceal one wide child."],
    ["css/box-model-and-layout", "css/flexbox-sizing", "css/responsive-layout"])

add("positioning-and-sticky", "layout", "CSS positioning: keep sticky controls inside their scroll boundary",
    "Use sticky for contextual controls, not as a substitute for document flow.",
    "A sticky-positioned element stays in normal flow until a scroll threshold is crossed, then sticks within its scrolling boundary. Absolute positioning removes an element from normal flow.",
    "A long incident record keeps a compact section navigation available while the article scrolls. Its sticky top offset clears the fixed site header. This works only if the element's scroll container and available space permit it; an ancestor with overflow behavior can change where it sticks. On a narrow viewport, the navigation returns to ordinary flow so it does not consume most of the visible page. The links remain ordinary anchors either way. Do not position an error message over form fields or rely on visual overlap to convey priority.",
    '''.incident-index { position: sticky; top: 4.5rem; align-self: start; }
@media (max-width: 50rem) {
  .incident-index { position: static; }
}''',
    "Sticky positioning adds no extra asset, though moving layers may increase paint work on a complex page. Test the actual containing block, short viewports, browser zoom, and focus navigation through the index. A fixed header can obscure fragment targets; scroll-margin-block-start on targets may be needed. Keep the top offset synchronized with the real header height rather than guessing from a screenshot.",
    ["Do not expect sticky to work against every ancestor overflow setting.", "Do not cover focused content with a fixed or sticky bar.", "Do not use absolute positioning to reorder a logical article."],
    ["css/stacking-contexts", "css/responsive-layout", "html/skip-link"])

add("overflow-and-scroll", "layout", "CSS overflow: contain long data without losing controls",
    "Give a wide code or table region its own scroll path while leaving the page usable.",
    "Overflow controls how content outside a box is clipped or scrolled. It does not repair a bad information structure or create alternate text for hidden content.",
    "An audit report includes a long machine identifier and a wide data table. Both may need local horizontal scrolling on a phone. Wrap only the region that genuinely exceeds the available inline size, keep focusable controls visible, and make the scroll region discoverable. Setting overflow: hidden on the body to suppress a horizontal scrollbar can hide the actual error and trap a keyboard user's focus. When a string has safe break points, overflow-wrap may be better than a scroller. Avoid clipping a box shadow or focus ring just to make a screenshot look clean.",
    '''.audit-code { max-inline-size: 100%; overflow-x: auto; }
.audit-code code { white-space: pre; }
.case-identifier { overflow-wrap: anywhere; }
.audit-table-wrap { max-inline-size: 100%; overflow-x: auto; }''',
    "A local scroll container adds no network bytes, but nested scrolling costs attention and may be awkward on touch devices. Test keyboard reachability, focus visibility, and a 320-pixel viewport. The table still needs semantic headers in HTML; horizontal scrolling does not supply relationships. If long content is generated, check that the wrapper can shrink inside grid or flex layouts, often with min-inline-size: 0.",
    ["Do not hide page overflow to conceal an oversized child.", "Do not break a code sample in a way that changes the value a reader copies.", "Do not treat scrolling as a replacement for table headers."],
    ["css/grid-tracks", "css/box-model-and-layout", "html/complex-table-headers"])

add("stacking-contexts", "layout", "CSS stacking contexts: debug overlays without arbitrary z-index inflation",
    "Identify the stacking context before raising an overlay's z-index.",
    "A stacking context groups descendants for paint order. A child cannot escape its ancestor's stacking order merely by receiving a very large z-index.",
    "A receipt help panel appears below a fixed header even after its own z-index is raised. The header and panel may belong to different stacking contexts; inspect their ancestors before changing numbers. Positioning with z-index is one cause, and opacity, transforms, and other properties can create contexts too. Use a small documented layer scale for application-owned overlays, and let browser-managed top-layer UI handle modal dialogs where appropriate. A CSS overlay does not trap focus or make the background inert. For a blocking task, use the native dialog behavior instead of painting a high-z box over the page.",
    '''.site-header { position: sticky; top: 0; z-index: 20; }
.receipt-help-layer { position: relative; z-index: 30; }
.receipt-help-layer .note { position: absolute; inset-block-start: 100%; }''',
    "Z-index values do not affect transfer size. The cost is debugging and visual overlap across routes, especially when a transformed ancestor changes the containing or stacking context. Inspect computed styles and the element tree, then test zoom and keyboard focus beneath the overlay. The sample's numbers are a local scale, not a universal layering system. If a native popover fits, it may remove some custom stacking work.",
    ["Do not use z-index: 999999 as the first diagnostic step.", "Do not assume a high-z child can outrank an ancestor's context.", "Do not confuse paint order with focus or modal behavior."],
    ["css/positioning-and-sticky", "html/native-popover", "html/dialog-and-details"])

add("media-queries", "responsive", "CSS media queries: change layout at a content failure point",
    "Set a breakpoint when the content cannot fit, not because a device name appears in a plan.",
    "A media query conditionally applies CSS according to the rendering environment. Width queries commonly adjust layout; preference queries respond to user settings.",
    "A two-column review screen stops fitting once the record panel and action rail together exceed the available width. Begin with the compact one-column arrangement, then add the second track only when there is enough room. Keeping the narrow layout as the base means unsupported media queries still leave a usable reading flow. The chosen breakpoint should be measured with real labels, large text, and translated values. Do not infer the user's input method from viewport width; a narrow desktop window still has a keyboard and a wide tablet may still use touch.",
    '''.review-screen { display: grid; gap: 1rem; }
@media (min-width: 56rem) {
  .review-screen { grid-template-columns: minmax(0, 1fr) 17rem; }
}''',
    "A width query adds negligible runtime work compared with the layout it selects. More breakpoints can increase testing and maintenance, so use the fewest that reflect actual content changes. Check both sides of the threshold, not just one phone and one monitor. CSS cannot change DOM reading order; keep the record before the rail in markup if that is the intended reading sequence.",
    ["Do not treat 56rem as a named device category.", "Do not use viewport width to decide whether a user has a mouse.", "Do not repair a wrong source order with visual reordering."],
    ["css/responsive-layout", "css/container-queries", "css/grid-tracks"])

add("container-queries", "responsive", "CSS container queries: adapt a component to its own space",
    "Use an inline-size query when the same card appears in different page regions.",
    "A size container query tests an ancestor's size rather than the viewport. The ancestor needs container-type: inline-size for inline-axis size queries.",
    "A case summary card appears in a wide dashboard column and a narrow sidebar. A viewport breakpoint cannot describe both positions at once. Declare the card's wrapper as a query container, use a stacked base layout, then arrange the card's children in two columns when that wrapper is wide enough. The queried container cannot style itself based on its own size through the query; the rule targets descendants. Inline-size containment can affect intrinsic sizing, so set up the wrapper intentionally and test it inside its actual grid track. The base layout remains useful on browsers that ignore the query.",
    '''.case-card-slot { container-type: inline-size; }
.case-card { display: grid; gap: .75rem; }
@container (min-width: 32rem) {
  .case-card { grid-template-columns: minmax(0, 1fr) auto; align-items: start; }
}''',
    "Container queries avoid duplicating viewport exceptions for every placement. They still require style calculation and layout; measure a large list of cards before claiming a performance improvement. Test the component in both wide and narrow slots, with long labels and user zoom. If a nested child overflows, give it a shrink rule or wrapping behavior rather than increasing the query threshold blindly.",
    ["Do not forget to establish a size query container.", "Do not expect a container query to style its queried element itself.", "Do not use a viewport breakpoint for a component whose width depends on placement."],
    ["css/media-queries", "css/grid-tracks", "css/responsive-layout"])

add("logical-properties", "responsive", "CSS logical properties: space content by reading direction",
    "Use inline and block axes when spacing should follow writing mode.",
    "Logical properties express sides and dimensions relative to the writing mode. Inline-start is the start of a line, which is not always the physical left side.",
    "A bilingual case record has a small status badge next to its heading. Margin-inline-start keeps the gap on the correct side as the direction changes, while padding-block controls vertical space independently. The markup must still declare the content language and direction accurately; CSS cannot infer a person's script. If a layout truly depends on a physical device edge, a physical property may be correct, but choose that deliberately. Review icons and arrows too, since changing spacing alone does not make a directional symbol correct.",
    '''.case-heading { padding-block: .75rem; padding-inline: 1rem; }
.case-heading__badge { margin-inline-start: .5rem; }
.case-record { max-inline-size: 70rem; margin-inline: auto; }''',
    "Logical properties add no dependency and little runtime cost. Their value is lower duplication across left-to-right and right-to-left variants. Test actual localized copy and bidirectional identifiers, not merely a mirrored screenshot. Some third-party components may still use physical margins; inspect those overrides before adding a second direction-specific rule. Keep focus and reading order aligned with the DOM in both directions.",
    ["Do not assume inline-start always means left.", "Do not substitute CSS direction for correct HTML language metadata.", "Do not mirror numbers or brand marks without reviewing their meaning."],
    ["html/language-and-direction", "css/media-queries", "css/units-and-functions"])

add("fluid-type-clamp", "responsive", "CSS clamp for type: grow headings within readable bounds",
    "Combine a relative minimum, a fluid middle value, and a relative maximum.",
    "The clamp() function chooses a preferred value while respecting minimum and maximum bounds. It does not know whether the words actually fit.",
    "A review title should feel balanced on wide and narrow screens without shrinking below a readable size. Use rem at both ends so a larger root font size still influences the result; the middle term can respond to viewport width. Body copy should retain a comfortable line height and measure, not inherit the heading's fluid scale. The rule is a starting point. Test a long translated title, 200% zoom, and a narrow split-screen window. If a word does not wrap, fix the word behavior or container width rather than lowering the minimum font size until the problem disappears.",
    '''.review-title { font-size: clamp(1.75rem, 1.2rem + 2vw, 2.75rem); line-height: 1.15; }
.review-body { font-size: 1rem; line-height: 1.55; max-inline-size: 68ch; }''',
    "The calculation has negligible runtime cost. Readability is the boundary: a bounded heading can still be too large in a narrow card or too small for a user who changed default text settings. Compare real content, not placeholder text, and do not assume a viewport formula substitutes for a container query when the same component appears in different widths.",
    ["Do not use viewport units alone for essential text.", "Do not set a fixed block height around a fluid heading.", "Do not treat clamp values as proof the translated title fits."],
    ["css/units-and-functions", "css/container-queries", "css/readable-type"])

add("font-loading", "type-media", "CSS font loading: keep content readable while a font arrives",
    "Use a local font face with a fallback family and test layout shifts.",
    "The @font-face rule names a downloadable font resource. font-display controls the browser's display strategy while that resource loads.",
    "A case portal uses a house typeface for headings, but the incident text must remain readable during a slow font request. Declare the local file and a system fallback, then inspect whether swapping fonts changes line breaks or button widths. The source path in the sample must be shipped with the site and licensed for the intended use. A font face can cover only part of a character set; missing glyphs still need a fallback. Do not preload every weight or language subset merely because a design file lists them. Measure the bytes and identify which faces the first screen actually uses.",
    '''@font-face {
  font-family: "Case Sans";
  src: url("/fonts/font-0.woff") format("woff");
  font-display: swap;
}
.case-portal { font-family: "Case Sans", system-ui, sans-serif; }''',
    "The font request and decoding cost more than the CSS declaration. A fallback avoids invisible text, though a later swap can move content. Check the shipped file, its licence, glyph coverage, and final line wrapping. The sample points at an existing local asset, but its family name is an editorial alias; assess its actual metrics before using it on a production design. Keep controls wide enough for both fonts.",
    ["Do not assume a local path works after deployment without checking the asset.", "Do not omit a fallback family.", "Do not load unused weights on the first screen."],
    ["css/readable-type", "css/units-and-functions", "html/language-and-direction"])

add("readable-type", "type-media", "CSS readable type: set measure and rhythm before decorative details",
    "Use line height and a bounded measure that survive zoom and long words.",
    "Typography in CSS controls how text occupies space. Line height, font size, measure, and wrapping affect reading more than a decorative font choice alone.",
    "An investigation report contains long paragraphs and case IDs. The paragraph column uses a moderate maximum line length and generous line height. IDs may need controlled wrapping, but ordinary prose should keep natural word breaks. Avoid fixed-height cards: larger text, localization, and browser zoom will extend the content. A bold title is not a substitute for the correct HTML heading. Test with actual paragraph copy and a screen reader's reading order separately; CSS can make text easier to see but cannot repair a missing semantic structure.",
    '''.investigation-report { max-inline-size: 70ch; font-size: 1rem; line-height: 1.6; }
.investigation-report p { margin-block: 0 1rem; }
.investigation-report .case-id { overflow-wrap: anywhere; font-variant-numeric: tabular-nums; }''',
    "The rules add no network request unless a custom font is also loaded. Tabular numerals can make columns of numbers easier to scan only when the font supports them. Check the report at 200% zoom and with user font overrides. A 70ch cap is approximate and may need adjustment for the chosen font and script; do not equate it to exactly seventy visible characters.",
    ["Do not rely on CSS font size to create a document heading.", "Do not force prose into fixed-height boxes.", "Do not break every word merely to prevent one long identifier from overflowing."],
    ["css/font-loading", "css/fluid-type-clamp", "html/headings-and-paragraphs"])

add("image-fit-and-aspect", "type-media", "CSS object-fit and aspect ratio: crop a preview without distorting it",
    "Reserve a predictable image box and keep the original asset's meaning available.",
    "The aspect-ratio property can reserve a box's proportions. object-fit controls how a replaced image or video fits into that box.",
    "A case index displays small receipt scans with inconsistent source dimensions. A fixed ratio and cover fit keep the card grid stable, but the crop can hide a signature or amount. Use the crop only for a navigational thumbnail; the detail page must expose the full evidence. If every pixel matters on the card, contain is safer and may leave letterboxing. Supply width and height attributes in HTML when known, and write alternate text from the image's function. CSS changes the crop, not the bytes transferred or the accessibility text.",
    '''.receipt-card__thumb { inline-size: 100%; aspect-ratio: 4 / 3; object-fit: cover; }
.receipt-detail__scan { max-inline-size: 100%; block-size: auto; object-fit: contain; }''',
    "Cropping does not reduce download size. Serve an appropriately sized thumbnail asset or responsive source set when the original scan is large. Test cards with portrait, landscape, and unexpectedly small images, and confirm the full record remains reachable. An aspect-ratio placeholder can reduce layout movement while data loads, but it cannot fix a source file with the wrong orientation.",
    ["Do not use cover on evidence when the cropped part may change the decision.", "Do not treat object-fit as image compression.", "Do not remove meaningful alternate text because the crop looks clear."],
    ["css/grid-tracks", "html/responsive-images", "html/image-alt"])

add("backgrounds-and-decorative-images", "type-media", "CSS backgrounds: reserve background images for decoration",
    "Keep evidence and instructional images in HTML; use CSS backgrounds for nonessential paint.",
    "A CSS background is part of an element's visual presentation. It does not have an alt attribute or create meaningful document content.",
    "A receipt callout uses a subtle gradient behind text. The underlying status and explanation remain in HTML, so the callout is understandable when CSS is disabled or colors are changed by the user. Avoid putting a scanned document, barcode, or safety instruction in a background-image; those need a content image with a text alternative and access to the full asset. The sample uses a solid color as a base before a gradient. Verify text contrast over every point of the gradient, especially after theme overrides. A decorative image may still cost bandwidth even if it adds no information.",
    '''.receipt-callout {
  color: #183047;
  background-color: #e8f1f4;
  background-image: linear-gradient(120deg, #e8f1f4, #f5f7e9);
  border-inline-start: .3rem solid #175b44;
  padding: 1rem;
}''',
    "A CSS gradient is generated without an image request; a URL background would add one. A gradient can still cost paint work over large surfaces, so avoid animating it across the whole page without a need. Check a forced-colors mode and print preview, where decorative backgrounds may disappear. The border gives the callout some structure, but the status must remain explicit in text.",
    ["Do not put a receipt scan in background-image and call it accessible evidence.", "Do not rely on a background color as the sole signal of status.", "Do not assume a decorative background survives printing or forced colors."],
    ["css/colors-and-contrast", "css/dark-mode-and-forced-colors", "html/image-alt"])

add("colors-and-contrast", "interaction", "CSS color and contrast: pair text with its real surface",
    "Set foreground and background together, then test every state.",
    "The color property paints text; background-color paints its surface. Readability depends on their pair and on the rendered state, not on either value alone.",
    "A case status banner has a readable dark foreground on a pale background, plus a border for structure. The words say what happened; color reinforces them. Hover, focus, disabled, and dark theme states need separate review because an override can change one half of the pair. Do not claim an exact contrast ratio from a snippet without computing it against the final rendered colors. Images, transparency, and overlays can alter the effective background. Test with actual browser settings and content, including a high-contrast environment that may replace author colors.",
    '''.case-status--held {
  color: #4d1e1e;
  background-color: #fff1ed;
  border: 1px solid #a84235;
  padding: .75rem 1rem;
}''',
    "Color declarations add negligible transfer cost. The real maintenance cost is keeping pairs consistent across themes and states. Use shared tokens only when ownership is clear, and run automated contrast checks on final color pairs as a first screen, followed by visual review. The status text must still identify the case state when the banner is printed without its background or viewed without color.",
    ["Do not use red alone to mean held.", "Do not change only the foreground in a dark theme.", "Do not quote a contrast result without testing the final layered surface."],
    ["css/custom-properties", "css/dark-mode-and-forced-colors", "html/live-status"])

add("focus-visible", "interaction", "CSS focus-visible: keep keyboard location unmistakable",
    "Use :focus-visible for a clear focus indicator that is not clipped.",
    "The :focus-visible pseudo-class matches focus when the browser decides a visible indicator is appropriate. It helps distinguish keyboard-oriented focus styling from every pointer click.",
    "A reviewer tabs through receipt links and action buttons. Each needs an obvious outline that remains visible against the page and does not move the layout. Outline offset separates the indicator from a dark button edge. Do not rely on a shadow alone, since forced colors may remove shadows. A scroll container or overflow-hidden wrapper can clip the indicator even when the rule is correct. Test the first and last focusable controls, keyboard navigation into dialogs, and return focus after closure. CSS does not make a div keyboard-operable; use native interactive elements first.",
    '''.receipt-action:focus-visible,
.receipt-link:focus-visible { outline: 3px solid #205c8a; outline-offset: 3px; }
@media (forced-colors: active) {
  .receipt-action:focus-visible,
  .receipt-link:focus-visible { outline-color: Highlight; }
}''',
    "The outline is inexpensive to paint and does not affect box size. The failure cost is high when focus disappears inside a dense form. Test with Tab and Shift+Tab, not only a mouse click. If a component library removes outlines globally, restore them at the shared control layer rather than patching one route at a time. Keep the control's label visible as focus moves.",
    ["Do not write outline: none without an equally visible replacement.", "Do not assume :hover covers keyboard use.", "Do not style a nonfocusable element and expect it to enter the tab order."],
    ["css/pseudo-classes", "css/overflow-and-scroll", "html/focus-and-native-controls"])

add("reduced-motion", "interaction", "CSS reduced motion: remove nonessential movement at the source",
    "Respect a reduce preference while keeping state changes understandable.",
    "The prefers-reduced-motion media feature can match a user preference for less movement. It does not tell the application to remove content or feedback.",
    "A case panel fades into view after a filter changes. The filter result must be perceivable even with no fade, so its status text and position remain stable. Apply a short transition by default, then remove it for users who request reduced motion. Do not replace a long, disorienting slide with a barely shorter slide and claim the preference was honored. If animation communicates progress, provide a text or static indicator. Test the operating-system preference and the browser emulation, and verify that the panel does not flash through a hidden intermediate state.",
    '''.case-panel { transition: opacity 180ms ease-out; }
.case-panel[data-state="loading"] { opacity: .65; }
@media (prefers-reduced-motion: reduce) {
  .case-panel { transition: none; }
}''',
    "Opacity transitions can be cheaper than animating layout, but they still add paint and may obscure text during the transition. A media query costs little; maintaining two coherent motion paths is the real work. The loading state should also be communicated in text because opacity alone is ambiguous. Avoid a blanket rule that turns every duration into nearly zero without reviewing each interaction's timing and cleanup.",
    ["Do not make movement the only signal of a new result.", "Do not force all transitions to zero without checking state handoff.", "Do not ignore a reduce preference for decorative motion."],
    ["css/transitions-and-transforms", "css/keyframe-animation", "html/live-status"])

add("transitions-and-transforms", "interaction", "CSS transitions and transforms: animate a specific visual property",
    "Name the property that changes and keep the control stable under motion.",
    "A transition interpolates supported property values when they change. A transform changes visual geometry without changing the element's normal-flow allocation.",
    "A receipt action can shift a few pixels on hover, but its focus state must remain equally clear for keyboard users. Transition only transform rather than all properties, so later color or outline changes do not start unexpected motion. A transform can create a stacking context and move painted content over neighbors; test the full toolbar when buttons are close together. Motion should not become the only indication that an action is available. If a press state matters, express it with a visible label or state as well.",
    '''.receipt-action { transform: translateY(0); transition: transform 140ms ease-out; }
.receipt-action:hover { transform: translateY(-2px); }
.receipt-action:focus-visible { outline: 3px solid #205c8a; outline-offset: 2px; }
@media (prefers-reduced-motion: reduce) {
  .receipt-action { transition: none; transform: none; }
}''',
    "Transform animation often avoids layout recalculation, but it can still use compositor memory and trigger paint depending on the element. Measure a real page with many actions before calling the effect free. Test reduced motion, touch input, keyboard focus, and overlap at high zoom. The sample's two-pixel movement is decorative; removing it does not change access to the action.",
    ["Do not transition all properties without reviewing future state changes.", "Do not assume transforms change surrounding layout space.", "Do not hide a focus outline behind motion styling."],
    ["css/reduced-motion", "css/stacking-contexts", "css/focus-visible"])

add("dark-mode-and-forced-colors", "interaction", "CSS dark mode and forced colors: honor distinct user settings",
    "Treat a color-scheme preference and a forced palette as different contracts.",
    "The prefers-color-scheme feature detects a light or dark preference. Forced colors lets the browser apply a user-selected palette that may replace author colors.",
    "A case card starts with an explicit light foreground and surface, then supplies a dark pair when the user prefers dark mode. In forced colors, rely on system colors for the border and let the browser adjust text and backgrounds. Do not opt out of forced adjustment merely to preserve branding. Decorative shadows may disappear, so borders and words must retain the card's structure. A color-scheme declaration can also affect built-in controls; review native inputs as part of the page, not just your custom cards.",
    '''.case-card { color: #183047; background: #f4f7fa; border: 1px solid #9fb0c0; }
@media (prefers-color-scheme: dark) {
  .case-card { color: #edf3f8; background: #172a3b; border-color: #60788d; }
}
@media (forced-colors: active) {
  .case-card { border-color: CanvasText; box-shadow: none; }
}''',
    "Media queries themselves add little cost. Maintaining paired colors, icons, controls, and illustrations across modes is the real work. Test actual system settings, not only a browser screenshot with one class toggled. Do not treat forced colors as a dark-mode variant: the user's chosen palette may be light, dark, or another combination. The status text must remain explicit if color distinctions vanish.",
    ["Do not replace text with a color-coded dot.", "Do not force brand colors over a user-selected forced palette by default.", "Do not review only the card while native inputs use a different scheme."],
    ["css/colors-and-contrast", "css/focus-visible", "html/color-scheme-metadata"])

add("print-styles", "interaction", "CSS print styles: preserve the record and remove screen-only controls",
    "Use print media rules for document output without hiding the evidence itself.",
    "A print stylesheet applies rules when the document is printed or previewed for print. It changes presentation; it does not validate the record or create a PDF archive policy.",
    "An incident report should print with its case number, finding, and source links in readable order. Navigation controls and floating action bars can be hidden, while the article stays visible and breaks across pages sensibly. A link's destination may not be obvious on paper, so important references need readable text in the document itself. Background colors may be omitted by the printer; use black text and borders where needed. Test print preview with long tables and more than one page, not just the first sheet.",
    '''@media print {
  .site-navigation, .report-actions { display: none; }
  .incident-report { color: #000; background: #fff; max-inline-size: none; }
  .incident-report h2 { break-after: avoid; }
  .incident-report table { break-inside: auto; }
}''',
    "Print rules add CSS bytes but no extra request when kept in the main stylesheet. The bigger cost is maintaining a second rendering context and testing page breaks. Do not hide a link list if it is the only record of supporting documents. Print preview is not proof that a later printer or PDF pipeline preserves colors and margins; check the final output when the report is operationally important.",
    ["Do not hide evidence merely because it is awkward to print.", "Do not depend on background color to mark a held case on paper.", "Do not assume one-page preview proves multi-page tables are readable."],
    ["html/print-stylesheet-media", "css/readable-type", "html/incident-evidence-project"])

add("structural-selectors", "selectors", "CSS structural selectors: style repeated items without hard-coded positions",
    "Use nth-child only when sequence or grouping is part of the component contract.",
    "Structural pseudo-classes match elements by their position among siblings. They do not change source order or add an accessible label.",
    "A case timeline alternates a subtle separator between entries. A structural selector can mark every item after the first without adding a class to each generated row. The rule depends on the list's direct-child structure, so adding a wrapper changes which elements it matches. If the design wants a special urgent item, use a data state or class instead; urgency is not determined by its position. Keep the CSS decoration separate from the ordered sequence conveyed by the list markup. Test empty, single-item, and many-item timelines to confirm the first and last boundaries.",
    '''.case-timeline > li + li { border-block-start: 1px solid #b7c4d1; }
.case-timeline > li:nth-child(2n) { background-color: #f4f7fa; }
.case-timeline > li { padding-block: .75rem; }''',
    "The rules are cheap for a short list. Long lists cost more through DOM size and layout than through these selectors; use pagination or virtualization only when measurement warrants it. Background striping may vanish in forced colors, so the list must remain readable without it. The adjacent-sibling border communicates separation without relying on a specific number of rows.",
    ["Do not use nth-child to encode a business status.", "Do not assume a wrapper can be inserted without changing direct-child matching.", "Do not use alternating color as the only way to identify a row."],
    ["css/combinators", "css/pseudo-classes", "html/lists-and-definitions"])

add("keyframe-animation", "interaction", "CSS keyframes: keep repeating motion bounded and optional",
    "Reserve repeated animation for a state that remains understandable when still.",
    "A keyframes rule names points in an animation cycle. The animation properties select that cycle, its duration, and how many times it runs.",
    "A small loading marker on a report card may rotate while an authorized request is pending. The text beside it must say that the report is loading, because motion alone is not a status message. Keep the animation on a small element, not an entire panel of text, and stop it when the request completes or fails. A reduced-motion preference removes the rotation while leaving the marker and status text visible. Avoid an infinite animation on content that is already complete; it wastes attention and can make the interface appear stuck.",
    '''@keyframes report-wait { to { transform: rotate(1turn); } }
.report-loading__mark { inline-size: 1.25rem; aspect-ratio: 1; border: 2px solid currentColor; border-inline-start-color: transparent; border-radius: 50%; animation: report-wait 900ms linear infinite; }
@media (prefers-reduced-motion: reduce) {
  .report-loading__mark { animation: none; border-inline-start-color: currentColor; }
}''',
    "A small transform animation is usually less expensive than animating layout dimensions, but a screen full of perpetual markers still consumes resources. Profile the actual page if many requests can run together. The rule does not start or stop the loading state; application logic must update the element and its text. Check that the marker remains visible in forced colors and that the completed state does not retain the animation class.",
    ["Do not use infinite motion as the only progress announcement.", "Do not leave a spinner running after a failed request.", "Do not ignore reduced-motion settings for repeated decoration."],
    ["css/reduced-motion", "css/transitions-and-transforms", "html/live-status"])

add("supports-feature-query", "responsive", "CSS @supports: layer a feature over a usable base",
    "Use a feature query when an optional enhancement has a safe fallback.",
    "The @supports rule applies CSS only when the browser recognizes a tested declaration or condition. Recognition is not proof that every surrounding design decision works.",
    "A compact case card starts as a simple block so its content remains in normal flow. Where grid is supported, it can align the status beside the summary. The feature query is not permission to hide the base content; it should only add presentation. Test the fallback in a browser without the feature or by removing the enhanced rule, then check long labels at zoom. Some modern CSS features are widely supported enough that a query adds noise; use it where the fallback is materially different or the supported browser set demands it.",
    '''.case-card { display: block; padding: 1rem; }
@supports (display: grid) {
  .case-card { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: .75rem; }
}''',
    "The query adds little runtime cost but another path to test. If a browser understands display:grid while missing some other property inside the block, this condition does not protect that property. Test the exact feature whose absence would break the design. Keep the DOM sequence meaningful in both paths, and avoid writing two unrelated layouts that drift apart as content changes.",
    ["Do not treat @supports as a full browser compatibility test.", "Do not hide important content in the base style.", "Do not add a query around every mature property without a reason."],
    ["css/grid-tracks", "css/media-queries", "css/container-queries"])

add("receipt-dashboard-project", "projects", "CSS receipt dashboard project: one layout across cards, rails, and zoom",
    "Combine a shrinkable grid, wrapped controls, and a card container query.",
    "This project styles a receipt dashboard whose HTML keeps the record list before the action rail. CSS allocates space without changing that order.",
    "The outer dashboard begins as one column and grows to two when the rail fits. Each card's slot is its own query container, so a card placed in the main grid or a narrower rail can choose its layout from the space it actually receives. The controls wrap instead of clipping. Keep status words in the HTML, and provide a visible focus indicator through the shared control styles. The sample is the core stylesheet, not an entire application: data fetching, record authorization, and the action endpoints must be implemented separately. Test one empty record, a very long identifier, and a card with a translated title before presenting it as ready.",
    '''.receipt-dashboard { display: grid; gap: 1.25rem; }
@media (min-width: 58rem) {
  .receipt-dashboard { grid-template-columns: minmax(0, 1fr) 17rem; }
}
.receipt-card-slot { container-type: inline-size; min-inline-size: 0; }
.receipt-card { display: grid; gap: .75rem; padding: 1rem; border: 1px solid #b7c4d1; }
@container (min-width: 32rem) {
  .receipt-card { grid-template-columns: minmax(0, 1fr) auto; }
}
.receipt-actions { display: flex; flex-wrap: wrap; gap: .5rem; }''',
    "The stylesheet adds no image or script request. Layout work grows with the number of cards, so paginate or otherwise bound very large result sets based on actual measurement. Check 320-pixel width, 200% zoom, a long status phrase, and keyboard traversal through the actions. Do not treat a CSS project as proof that the record service exists; the HTML project supplies structure, and a backend must own state changes.",
    ["Do not use grid order to move a rail ahead of the record in paint while leaving focus order behind.", "Do not assume a card in the sidebar has the same width as a card in the main region.", "Do not present action buttons as functional without handlers and authorization."],
    ["css/grid-tracks", "css/container-queries", "html/receipt-dashboard-project"])

add("printable-incident-project", "projects", "CSS incident report project: readable on screen and on paper",
    "Pair a bounded screen measure with a print layout that keeps the record intact.",
    "This project styles an incident report for two rendering contexts. The article's HTML owns the facts and headings; CSS adjusts measure, controls, and page breaks.",
    "On screen, keep the main report at a readable line length and allow evidence thumbnails to fit their container. In print, remove only the navigation and editing actions, not the finding or provenance. Headings should not be stranded at the bottom of a page, though exact pagination depends on the printer and final font metrics. The sample avoids color-dependent status because many print settings omit backgrounds. Pair it with the HTML report project, which supplies the case number, evidence descriptions, and links. A generated PDF is still a separate output that must be checked from the final rendering pipeline.",
    '''.incident-report { max-inline-size: 70ch; margin-inline: auto; line-height: 1.55; }
.incident-report img { max-inline-size: 100%; block-size: auto; }
@media print {
  .site-navigation, .incident-actions { display: none; }
  .incident-report { max-inline-size: none; margin: 0; color: #000; }
  .incident-report h2 { break-after: avoid; }
  .incident-report figure { break-inside: avoid; }
}''',
    "Screen rules are cheap; print review is the maintenance cost. Test an incident with several pages, a tall figure, and a long table. A break-inside hint may not be honored in every pagination context, so inspect the result rather than relying on the declaration alone. Keep the report's status explicit in text and verify that evidence URLs or identifiers remain usable from the paper copy.",
    ["Do not hide source references merely because they complicate print layout.", "Do not assume break-inside guarantees one-page figures.", "Do not turn an unverified CSS print preview into an official archived record."],
    ["css/print-styles", "css/readable-type", "html/incident-evidence-project"])


assert len(specs) == 34 and len({spec["path"] for spec in specs}) == len(specs)
titles = {path: row["title"] for path, row in by_path.items()}
titles.update({spec["path"]: spec["title"] for spec in specs})
titles.update({f"{ROOT}/{section}": title for section, (title, _) in sections.items() if section != "quizzes"})
titles.update({"css/quizzes": "CSS Quizzes", "quizzes/css-foundations": "CSS cascade and selectors quiz",
               "quizzes/css-layout-accessibility": "CSS layout and accessibility quiz"})


def linked_list(paths):
    assert all(path in titles for path in paths), [path for path in paths if path not in titles]
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in paths
    ) + "</ul>"


def common_mistakes(items):
    return "<h3>Common Mistakes</h3><ul>" + "".join(
        f"<li>{html.escape(item)}</li>" for item in items
    ) + "</ul>"


def fresh(template, path, title, summary, subject, sort_order):
    row = copy.deepcopy(template)
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
               title=title, summary=summary, subject=subject, sort_order=sort_order,
               status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"]["subject_root"] = ROOT
    row["data"]["section_path"] = path if row["type"] == "subject" else ROOT
    row["data"]["content_format"] = "html"
    row["data"]["seo_ready"] = True
    row["data"]["author_path"] = "authors/aitrove-editorial"
    return row


root_hub = by_path[ROOT]
root_hub["summary"] = "A connected CSS curriculum covering the cascade, selectors, layouts, responsive rules, type, accessibility, and projects."
root_hub["updated_at"] = stamp
root_hub["data"]["resource_tabs"] = [
    {"title": root_hub["title"], "path": ROOT},
    *({"title": title, "path": f"{ROOT}/{section}"}
      for section, (title, _) in sections.items() if section != "quizzes"),
    {"title": "CSS Quizzes", "path": "css/quizzes"},
]
root_hub["body"] = (
    "<p>CSS decides how an HTML document is presented. Start by tracing the cascade, sizing one box, and testing a layout at narrow width and high zoom; then move to the section that matches the failure you need to solve.</p>"
    "<h2>Start with the existing lessons</h2>"
    + linked_list(["css/selectors-and-cascade", "css/box-model-and-layout", "css/responsive-layout"])
    + "<h2>CSS learning paths</h2>"
    + linked_list([f"{ROOT}/{section}" for section in sections if section != "quizzes"] + ["css/quizzes"])
    + "<h2>Build on the document</h2>"
    + linked_list(["html/html-tutorial", "html/html-tutorial/forms", "html/html-tutorial/accessibility"])
    + common_mistakes(["Do not use CSS to supply the only copy of a status or label.",
                       "Do not judge a layout only at one viewport width or default zoom.",
                       "Do not add specificity until the winning cascade rule is understood."])
)

for index, (section, (title, summary)) in enumerate(sections.items()):
    if section == "quizzes":
        continue
    hub_path = f"{ROOT}/{section}"
    lesson_paths = [spec["path"] for spec in specs if spec["section"] == section]
    assert lesson_paths
    hub = fresh(root_hub, hub_path, title, summary, f"css-{section}", 18500 + index)
    hub["data"]["modules"] = [{"title": title, "summary": summary, "lessons": lesson_paths}]
    hub["data"].pop("resource_tabs", None)
    hub["body"] = (
        f"<p>{html.escape(summary)} Each lesson makes one concrete CSS decision and names its verification cost.</p>"
        "<h2>Lessons</h2>" + linked_list(lesson_paths)
        + "<h2>Continue</h2>" + linked_list([ROOT, "css/quizzes", "html/html-tutorial"])
        + common_mistakes(["Do not carry a sample rule into production without checking its containing markup.",
                           "Do not skip keyboard, zoom, or long-content checks when a visual result looks correct."])
    )
    rows.append(hub)

for index, spec in enumerate(specs):
    path = spec["path"]
    section = spec["section"]
    assert all(related in titles for related in spec["related"]), path
    row = fresh(by_path["css/selectors-and-cascade"], path, spec["title"], spec["summary"],
                f"css-{section}", 21000 + index)
    row["tags"] = ["css", section, "web"]
    row["data"]["section_path"] = f"{ROOT}/{section}"
    row["data"]["reading_minutes"] = 5
    row["data"]["related"] = [
        {"path": related, "title": titles[related]} for related in spec["related"]
    ]
    language = "html" if path == "css/authoring-and-loading" else "css"
    row["body"] = (
        f"<p>{html.escape(spec['intro'])}</p><h2>How the rule works</h2>"
        f"<p>{html.escape(spec['mechanics'])}</p>"
        f'<pre><code class="language-{language}">{html.escape(spec["sample"])}</code></pre>'
        "<h2>Cost and verification</h2>"
        f"<p>{html.escape(spec['cost'])}</p>"
        + common_mistakes(spec["mistakes"])
        + "<h2>Connected lessons</h2>"
        + linked_list([f"{ROOT}/{section}", *spec["related"]])
    )
    rows.append(row)

for path, related in {
    "css/selectors-and-cascade": ["css/cascade-layers", "css/specificity-is-where"],
    "css/box-model-and-layout": ["css/flexbox-sizing", "css/grid-tracks", "css/overflow-and-scroll"],
    "css/responsive-layout": ["css/media-queries", "css/container-queries", "css/logical-properties"],
}.items():
    row = by_path[path]
    row["updated_at"] = stamp
    row["data"]["related"].extend({"path": target, "title": titles[target]} for target in related)
    row["body"] += "<h2>Continue this topic</h2>" + linked_list(related)


quiz_specs = [
    ("quizzes/css-foundations", "CSS cascade and selectors quiz", [
        ("Which normal author declaration wins across ordered layers?", ["The declaration in the later layer", "The declaration with the longest selector in an earlier layer", "The first declaration in source order"], 0, "For normal declarations, later author layers outrank earlier layers before specificity is compared."),
        ("What does a direct-child combinator require?", ["Any descendant", "An immediate child", "The next sibling"], 1, "The greater-than combinator matches a child one level below the parent."),
        ("Which rule can preserve a border when a custom property is absent?", ["border: var(--case-border, 1px solid #456);", "border: --case-border;", "border: inherit always;"], 0, "The var() fallback is used if the custom property is missing or invalid as a custom property."),
        ("What changes when :where() wraps a selector?", ["Its matching set becomes empty", "Its specificity contribution becomes zero", "It wins over inline style"], 1, ":where() contributes zero specificity while its arguments still determine matches."),
        ("Which state is best for a visible keyboard focus ring?", [":hover", ":focus-visible", ":empty"], 1, ":focus-visible targets focus when a visible indicator is appropriate."),
        ("What does rem use as its length reference?", ["The root element's font size", "The nearest parent's width", "The viewport height"], 0, "One rem resolves against the root element's font size."),
        ("A percentage height behaves unexpectedly. What should be checked first?", ["The containing block's height", "The sibling count", "The border color"], 0, "Percentage sizing depends on the relevant containing block and whether its size is definite."),
        ("Which selector matches the paragraph immediately after a heading?", ["h2 p", "h2 + p", "h2 > p"], 1, "The adjacent-sibling combinator matches the next sibling."),
        ("What does :has() select in a rule on a parent?", ["A parent matching a relative descendant or sibling condition", "Only a text node", "Every descendant regardless of condition"], 0, ":has() allows the subject to match based on a relative selector."),
        ("Why can an unlayered normal author rule beat a layered normal rule?", ["Unlayered normal rules take precedence over layered normal rules", "Its file is always larger", "It is parsed after JavaScript"], 0, "Normal unlayered author declarations rank above normal layered author declarations."),
        ("Which keyword asks a property to inherit where inheritance applies and use its initial value otherwise?", ["unset", "revert-layer", "currentColor"], 0, "Unset follows inheritance for inherited properties and the initial value for other properties."),
        ("What is a sound response to an unexpected winning declaration?", ["Add !important everywhere", "Inspect origin, importance, layer, and specificity", "Duplicate the selector three times"], 1, "Trace the cascade before raising specificity or importance."),
    ], ["css/cascade-layers", "css/custom-properties", "css/combinators", "css/focus-visible"]),
    ("quizzes/css-layout-accessibility", "CSS layout and accessibility quiz", [
        ("What is the likely fix for a grid child that refuses to shrink around long text?", ["Give the track minmax(0, 1fr) and allow the child min-inline-size: 0", "Add more viewport units", "Move the text with transform"], 0, "Grid tracks and the child minimum size can both preserve unwanted intrinsic width."),
        ("When should a container query be preferred to a viewport query?", ["When a component must adapt to its own allocated width", "Whenever the page has only one column", "Only for print"], 0, "Container queries respond to a query container, not the full viewport."),
        ("Which layout model is usually suitable for one-dimensional action alignment?", ["Flexbox", "Absolute positioning", "A background image"], 0, "Flexbox distributes items along a primary axis while letting them wrap."),
        ("What should be preserved when CSS visually reorders controls?", ["Logical reading and focus order", "Only the paint order", "The original border radius"], 0, "Visual order does not rewrite DOM or keyboard order."),
        ("What does overflow: auto do when content exceeds the box?", ["Creates scroll access as needed", "Deletes excess content", "Makes every child fixed"], 0, "Automatic overflow exposes scrolling when content does not fit."),
        ("What is a reasonable reduced-motion treatment for an entrance animation?", ["Remove nonessential movement while keeping content visible", "Hide the content", "Force a slower looping animation"], 0, "Reduced-motion preferences call for an equivalent usable state with less motion."),
        ("What must a color-only status design add?", ["A text or other noncolor status cue", "Another similar shade", "A transition"], 0, "Color should not be the sole carrier of status information."),
        ("Which rule helps an image keep its proportions inside a bounded box?", ["max-inline-size: 100%; block-size: auto;", "block-size: 100%; inline-size: 100%;", "position: fixed;"], 0, "An automatic block size preserves intrinsic aspect ratio as inline size changes."),
        ("Why can position: sticky appear to fail?", ["An ancestor's scroll or overflow context may change its behavior", "Sticky requires JavaScript", "Sticky only works on images"], 0, "Sticky positioning depends on its scroll container and containing block."),
        ("Which physical property is best replaced by a logical equivalent for varied writing modes?", ["margin-left", "font-weight", "opacity"], 0, "Margin-inline-start maps to the start of the inline axis."),
        ("What should be checked after styling a print report?", ["The actual multipage printed output", "Only a wide-screen screenshot", "The hover transition"], 0, "Pagination and printer settings can change breaks and colors."),
        ("What does @supports test?", ["Whether the user agent supports a CSS feature condition", "Whether the server is online", "Whether the image has alternative text"], 0, "A supports condition selects rules based on feature support."),
    ], ["css/grid-tracks", "css/container-queries", "css/reduced-motion", "css/print-styles"]),
]

quiz_paths = [item[0] for item in quiz_specs]
quiz_hub = fresh(root_hub, "css/quizzes", "CSS Quizzes",
                 "Test cascade decisions, component layouts, and accessibility boundaries.",
                 "css-quizzes", 18590)
quiz_hub["data"]["modules"] = [{"title": "CSS checks", "summary": "Two applied twelve-question quizzes.",
                                "lessons": quiz_paths}]
quiz_hub["data"].pop("resource_tabs", None)
quiz_hub["body"] = ("<p>Answer from the rendered behavior and the cascade, then review the linked rule where an answer fails.</p>"
                    "<h2>Quizzes</h2>" + linked_list(quiz_paths) + "<h2>Review paths</h2>"
                    + linked_list([ROOT, f"{ROOT}/foundations", f"{ROOT}/layout", f"{ROOT}/interaction"])
                    + common_mistakes(["Do not memorize a declaration without checking its containing layout.",
                                       "Do not treat a correct visual answer as an accessibility check."]))
rows.append(quiz_hub)

quiz_template = next(row for row in by_path.values() if row["type"] == "quiz" and row["path"].startswith("quizzes/html-"))
for index, (path, title, questions, related) in enumerate(quiz_specs):
    assert len(questions) == 12
    quiz = fresh(quiz_template, path, title,
                 "Twelve explained checks on CSS behavior and failure boundaries.",
                 "css-quizzes", 3100 + index)
    quiz["tags"] = ["css", "quiz"]
    quiz["data"]["section_path"] = "css/quizzes"
    quiz["data"]["questions"] = [
        {"prompt": prompt, "options": options, "answer": answer, "explanation": explanation}
        for prompt, options, answer, explanation in questions
    ]
    quiz["data"]["related"] = [{"path": target, "title": titles[target]} for target in related]
    quiz["body"] = ("<p>Use each explanation to trace the winning CSS behavior, then inspect the related lesson before changing an application rule.</p>"
                    "<h2>Review the lessons</h2>" + linked_list(related)
                    + "<h2>Other checks</h2>" + linked_list(["css/quizzes", quiz_paths[1 - index]])
                    + common_mistakes(["Do not assume an answer holds when the containing markup changes.",
                                       "Do not skip keyboard and zoom review after a quiz passes."]))
    rows.append(quiz)

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "section_hubs": len(sections),
                  "quizzes": len(quiz_specs), "total_records": len(rows)}))

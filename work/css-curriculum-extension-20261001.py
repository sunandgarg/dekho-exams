"""Extend the CSS fixture curriculum with second-pass applied lessons."""

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
specs = []


def add(slug, section, title, summary, intro, mechanics, sample, cost, mistakes, related):
    path = "css/" + slug
    assert path not in by_path and section in {
        "foundations", "selectors", "layout", "type-media", "responsive", "interaction", "projects"
    }
    specs.append(dict(path=path, section=section, title=title, summary=summary,
                      intro=intro, mechanics=mechanics, sample=sample, cost=cost,
                      mistakes=mistakes, related=related))


add("native-nesting", "foundations", "Native CSS nesting: group states without raising specificity by accident",
    "Use nested rules for component relationships and keep the expanded selector readable.",
    "Native CSS nesting writes a rule inside another rule. The nested selector is resolved relative to the outer selector, so its final match still depends on document structure and the cascade.",
    "A review card has a stable base style, an invalid state, and a heading. Keep those rules close without encoding the whole page wrapper. The ampersand marks where the outer selector participates; it is useful when the state class sits on the same element. A nested descendant selector can omit the ampersand, but a short explicit relationship often reads better during review. Nesting does not create a new component boundary, and a selector list in the parent can affect the expanded specificity. If a rule starts winning unexpectedly, inspect the expanded selector in developer tools rather than adding another layer of nesting. Prefer a flat rule when a nested block becomes harder to scan than the relationship it expresses.",
    '''.review-card {
  padding: 1.25rem;
  border: 1px solid #a9b9c9;
  &.review-card--invalid { border-color: #a92d3b; }
  > h2 { margin-block: 0 .75rem; }
}''',
    "Nesting removes repeated selector text, not CSS matching work. Its real cost is debugging selector expansion when a file mixes long parent lists, states, and conditional rules. The sample has one state and one direct child; inspect both with the invalid class on the card. Test an older browser only if your audience requires it, and provide a build transform or flat fallback for that support target. Do not assume a CSS preprocessor's nesting syntax and native CSS nesting have identical parsing in every case.",
    ["Do not nest six wrapper levels to mirror one template.", "Do not expect nesting to lower specificity automatically.", "Do not place a state class on a child when the selector expects it on the card."],
    ["css/selectors-and-cascade", "css/specificity-is-where", "css/cascade-layers"])

add("scoped-rules", "foundations", "CSS @scope: bound a component rule to a subtree",
    "Constrain a rule to the owning region, then verify it does not bleed into nested components.",
    "The @scope rule gives selectors a root and, optionally, a limit. It can target a subtree without repeating its root in every selector.",
    "A case review panel contains a nested audit panel that reuses a heading class. The outer panel may style its own section headings while leaving the nested audit panel alone. Define the review root and the audit limit, then write the scoped rule against headings within that boundary. Scope is a cascade input, not a substitute for naming states or maintaining a sensible layer order. When origin, importance, layer, and specificity tie, proximity to the scope root can determine which scoped declaration wins. Since compatibility depends on the user's browser set, supply a basic class-based style first so older clients retain a readable panel. Inspect both the outer and nested headings after the change.",
    '''.review-panel :where(.section-title) { color: #254760; }
@scope (.review-panel) to (.audit-panel) {
  .section-title { color: #175b44; }
}''',
    "The fallback still styles headings in the review panel, including nested ones; the scoped enhancement changes the intended outer headings where the feature is supported. If isolation of the nested audit heading is required for older browsers too, use explicit component classes in the fallback. Scope adds no asset request. Its maintenance cost is the need to reason about where nested boundaries begin and end, especially when a component moves in the DOM. Verify actual supported clients rather than using a single desktop browser as the compatibility policy.",
    ["Do not confuse @scope with Shadow DOM isolation.", "Do not assume a limit selector removes styles already supplied by the fallback.", "Do not treat scoping proximity as a replacement for cascade layers."],
    ["css/cascade-layers", "css/native-nesting", "css/combinators"])

add("registered-custom-properties", "foundations", "CSS @property: type a custom value and control inheritance",
    "Register a token when type checking or interpolation has a concrete use.",
    "An @property rule declares a custom property's syntax, inheritance behavior, and initial value. That lets the browser reject a value that does not match the declared type.",
    "A progress rail uses a percentage to size its filled track. Register the percentage so an accidental color token cannot silently become the rail length. Keep the property name private to this component family and choose an initial value that leaves the rail in a usable state before data arrives. The registered value can interpolate when a supported transition uses it, but the UI still needs a text progress value for readers who cannot perceive the fill. Registration is not data validation: the backend owns the real completion state, and CSS only presents it. Check zero and full completion, a malformed value, and a reduced-motion preference. Use an ordinary custom property when typing and interpolation bring no practical benefit.",
    '''@property --review-progress {
  syntax: "<percentage>";
  inherits: false;
  initial-value: 0%;
}
.review-progress { --review-progress: 38%; }
.review-progress__fill { inline-size: var(--review-progress); }''',
    "The browser has a typed value to compute; this does not add a network request. The risk is a registration name reused with incompatible syntax elsewhere in a large stylesheet. Keep one declaration owner and inspect computed values after imports and layering. A percentage still needs a meaningful containing width, so the track must have an actual inline size. Avoid animating the fill without considering motion settings and whether frequent updates are necessary. The code is presentation-only; the numerical state belongs in text or accessible markup as well.",
    ["Do not register the same property name with competing contracts.", "Do not read a CSS progress width as the source of truth.", "Do not assume a typed token fixes an incorrectly sized container."],
    ["css/custom-properties", "css/reduced-motion", "css/transitions-and-transforms"])

add("attribute-selectors", "selectors", "CSS attribute selectors: target explicit document state",
    "Style a stable attribute contract without guessing from DOM position.",
    "An attribute selector matches an element using the presence or value of an attribute. It is useful when the attribute already represents a meaningful state or document contract.",
    "An incident table marks rows with a data-severity value and a form exposes its disabled inputs. A scoped selector can style the severity row without requiring the third row to stay third forever. Treat the data attribute as presentation metadata, not as authorization or a replacement for status text. Attribute values and selector comparisons have specific case behavior; if casing varies in a feed, normalize data before rendering rather than relying on a CSS workaround. The disabled pseudo-class follows actual control state, while a data attribute does nothing functional by itself. Inspect both visual styling and the HTML state that produced it. A selector should describe the state you intend to show, not invent it.",
    '''.incident-list [data-severity="high"] {
  border-inline-start: .3rem solid #a92d3b;
  padding-inline-start: .75rem;
}
.incident-form :disabled { opacity: .72; }''',
    "Two short attribute selectors are cheap in ordinary documents. The expensive part is maintaining multiple state representations if a class, a data attribute, and a backend value can disagree. Verify high and ordinary incidents, missing attributes, and disabled controls with keyboard access. The border must accompany a text severity label, since color and shape alone can be missed. Opacity should not reduce control text below a readable contrast; adjust the entire disabled style against its real background.",
    ["Do not use a data attribute as access control.", "Do not hide a severity word because the border is red.", "Do not assume a disabled-looking control is actually disabled."],
    ["css/pseudo-classes", "css/colors-and-contrast", "html/form-help-and-errors"])

add("pseudo-elements-and-generated-content", "selectors", "CSS pseudo-elements: decorate without relocating meaning",
    "Use generated boxes for ornament; keep required words in HTML.",
    "A pseudo-element such as ::before or ::after creates a stylable box associated with a selected element. The box can carry decoration without adding a markup wrapper.",
    "A case timeline needs a small line and dot before each entry. The entry's date, event text, and status belong in the document; the dot is an optional visual cue. Draw it with a pseudo-element so the layout stays compact. Generated content is not a reliable place for required instructions, identifiers, or status wording, and the accessibility treatment of generated text can vary. The ornament should disappear without losing meaning when CSS is disabled or forced colors replace its paint. Scope the rule to the timeline component, set a containing position, and avoid absolute coordinates tied to one font size. Check a long translated event and a zoomed page before declaring the offset stable.",
    '''.case-timeline__entry { position: relative; padding-inline-start: 1.5rem; }
.case-timeline__entry::before {
  content: "";
  position: absolute;
  inset-inline-start: .15rem;
  inset-block-start: .45em;
  inline-size: .55rem;
  block-size: .55rem;
  border-radius: 50%;
  background: currentColor;
}''',
    "The extra generated box has negligible cost for a short timeline. Thousands of ornamented items can add paint work, so virtualize or paginate based on measured use rather than assuming every item must be present. The inherited currentColor keeps the dot aligned with the entry's text color, but the text must still communicate status. Test with high contrast and print settings; a lost dot should never make the sequence unreadable. If the dot needs its own interactive behavior, it must be real markup, not generated content.",
    ["Do not put an incident number in content: and omit it from the document.", "Do not make decorative pseudo-elements capture pointer interactions.", "Do not position a marker against a fixed text height."],
    ["css/colors-and-contrast", "css/logical-properties", "html/ordered-list-numbering"])

add("subgrid-alignment", "layout", "CSS subgrid: align nested card content to shared tracks",
    "Share a parent grid's row tracks where cards must align, and keep a simpler fallback.",
    "Subgrid lets a nested grid use the track sizing of its parent in one or both dimensions. It solves alignment across nested card content that ordinary independent grids cannot guarantee.",
    "A receipt comparison shows several cards, each with a title, detail, and action. Titles wrap at different lengths, yet the actions should align across a row. Make the outer group a grid with repeated rows, and let each card span and adopt those row tracks. The cards remain separate HTML records; CSS only lines up their visual tracks. The sample uses a three-row subgrid and should be applied to a known row of cards. In a larger responsive grid, row spans and implicit rows need careful review. Do not use subgrid to force semantic order or to hide missing content. Check a card with a two-line title, a missing optional note, and large type.",
    '''.receipt-comparison {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 16rem), 1fr));
  grid-template-rows: repeat(3, auto);
  gap: 1rem;
}
.receipt-comparison__card {
  display: grid;
  grid-row: span 3;
  grid-template-rows: subgrid;
  border: 1px solid #b7c4d1;
  padding: 1rem;
}''',
    "Track sizing may depend on the longest content in the set, so a single unbroken token can make the shared row too tall or wide. Bound and wrap user-supplied content. A fallback can use independent card grids with actions pushed to the end; exact cross-card alignment is a progressive enhancement. Subgrid adds layout relationships, not new bytes or requests. It is useful only when the shared tracks are a real design requirement, since it adds a coupling between parent and child layout definitions.",
    ["Do not expect subgrid to align cards that are in different parent grids.", "Do not leave the card's row span inconsistent with the parent track plan.", "Do not reorder content merely to align action buttons."],
    ["css/grid-tracks", "css/alignment-and-gap", "css/receipt-dashboard-project"])

add("alignment-and-gap", "layout", "CSS alignment and gap: distribute space inside the correct box",
    "Separate item alignment from track distribution and use gap for repeated spacing.",
    "CSS box alignment properties answer different questions. Align-items controls items within their areas; justify-content distributes the layout's tracks or items when free space exists on the inline axis in the relevant layout mode.",
    "A triage toolbar has a title, status, and actions. The actions need consistent spacing even when they wrap, so use flex-wrap and gap rather than right margins on every button. Align-items centers the toolbar's direct children along its cross axis; it does not change their document order. When the title grows, allow it to shrink and wrap, or the actions may overflow. A grid container could be appropriate if fixed columns must align with another region, but flexbox is enough for this one-dimensional row. Inspect actual free space before expecting justify-content to move anything. A child stretched to fill the line leaves no free space for distribution.",
    '''.triage-toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: .75rem 1rem; }
.triage-toolbar__title { flex: 1 1 18rem; min-inline-size: 0; }
.triage-toolbar__actions { display: flex; flex-wrap: wrap; gap: .5rem; }
.triage-toolbar__actions button { max-inline-size: 100%; }''',
    "Gap avoids trailing-margin cleanup and works across wrapped lines. Its layout cost is ordinary flex layout; the notable maintenance cost is knowing which container owns each gap. Nesting one action group inside the toolbar keeps action spacing separate from the title-to-actions spacing. Check long button labels, 320-pixel width, and 200% zoom. A row that looks centered at desktop width may wrap into an unexpected visual order at narrow width, so read it with a keyboard and screen reader as well.",
    ["Do not use justify-content when the children already consume all available width.", "Do not add both gap and equivalent margins to the same item set.", "Do not use CSS order to fix a wrong document sequence."],
    ["css/flexbox-sizing", "css/grid-tracks", "css/subgrid-alignment"])

add("intrinsic-sizing", "layout", "CSS intrinsic sizing: let content set limits without forcing overflow",
    "Choose min-content, max-content, and fit-content against real content constraints.",
    "Intrinsic sizing measures a box from its content. Min-content is the smallest size allowed by the content's breaking opportunities; max-content is the size without optional wrapping; fit-content respects available space within those bounds.",
    "A shipment table has a compact status badge beside a description. Let the badge use its content width, but cap the description against the region's available width. A long tracking token has few break opportunities, so its min-content width may still be wide enough to overflow; add an explicit wrapping rule for data that can safely break. Intrinsic sizing is not an automatic solution to every narrow layout. It is a way to express how much the content asks for before external constraints apply. Verify the rendered values with real identifiers, translated labels, and a small viewport. An ellipsis can hide a critical identifier, so prefer wrapping for records that must be read in full.",
    '''.shipment-row { display: grid; grid-template-columns: fit-content(9rem) minmax(0, 1fr); gap: 1rem; }
.shipment-row__status { inline-size: max-content; max-inline-size: 9rem; }
.shipment-row__description { min-inline-size: 0; overflow-wrap: anywhere; }''',
    "The browser must measure content to determine intrinsic sizes, so large, frequently changing tables can make layout more expensive than fixed tracks. For a modest record list this is usually a reasonable trade for readable content. The fit-content cap does not guarantee that every badge fits without wrapping; the max-inline-size and available track size still matter. Test the longest expected status label rather than a two-word placeholder. If the table is huge, paginate and measure before seeking a CSS micro-optimization.",
    ["Do not equate min-content with zero width.", "Do not clip a legally significant identifier to preserve a neat column.", "Do not add max-content to user text without a width limit."],
    ["css/grid-tracks", "css/overflow-and-scroll", "css/text-wrapping-and-truncation"])

add("scroll-snap", "layout", "CSS scroll snap: align cards without trapping the reader",
    "Use proximity snapping for a horizontal card rail and keep native scrolling available.",
    "Scroll snap proposes positions where a scroll container settles. The container sets an axis and strictness; its children declare alignment points.",
    "A review queue has a short horizontal rail of case previews. Proximity snapping can help a swiped card settle near the start without forcing every small scroll to jump. Give the container overflow access and preserve keyboard navigation to links inside each card. The card's scroll-snap-align defines its target; it does not change its source order. Avoid mandatory snapping on long or variable-size content where a user might struggle to reach intervening text. If controls overlay the rail, account for them with scroll-padding and check the visible result. A browser may choose the exact snap behavior within specification constraints, so test touch, wheel, and keyboard scrolling.",
    '''.review-rail {
  display: flex;
  gap: 1rem;
  overflow-x: auto;
  scroll-snap-type: x proximity;
  scroll-padding-inline: 1rem;
}
.review-rail__card { flex: 0 0 min(18rem, 80vw); scroll-snap-align: start; }''',
    "The rail needs no script or extra asset. Smoothness depends on the number and complexity of cards; expensive shadows and large images can make scrolling feel slow. Limit the data set and load images appropriately. Snapping is an enhancement to scroll access, not a carousel service: the code provides no next-button behavior, pagination, or announcement of the current item. Check that focus remains visible when a link is reached by Tab and that the rail does not obscure the card's content at high zoom.",
    ["Do not hide the scrollbar unless another clear scrolling affordance exists.", "Do not use mandatory snapping for very tall cards.", "Do not assume scroll snapping changes keyboard focus order."],
    ["css/overflow-and-scroll", "css/reduced-motion", "html/link-vs-button"])

add("content-visibility", "layout", "CSS content-visibility: skip offscreen rendering carefully",
    "Reduce rendering work for independent sections while reserving credible space.",
    "Content-visibility: auto lets a browser skip some layout and paint work for offscreen content. Contain-intrinsic-size supplies a placeholder size while that work is skipped.",
    "A long archive page may contain dozens of independent case summaries. Applying the rule to each summary can reduce initial rendering work without deleting the summaries from the document. Choose a placeholder block size close to the observed section height; an unreasonable estimate can shift the page when the section becomes visible. The feature does not replace pagination, server filtering, or image delivery strategy. Keep the headings and content in markup and test fragment navigation into an offscreen section. Do not apply it indiscriminately to a hero, a currently focused region, or content whose height changes wildly. Measure the page with and without the rule before keeping it.",
    '''.archive-summary {
  content-visibility: auto;
  contain-intrinsic-size: auto 24rem;
  border-block-end: 1px solid #c6d0da;
}''',
    "The potential win is less offscreen render work, especially for a large document. The cost is the placeholder estimate and a new source of scroll-position shifts if the estimate is poor. It may also change how layout-dependent scripts observe offscreen content, so test application integrations rather than assuming computed geometry is immediately available. Browser support and actual gains depend on the page. Collect a performance profile and a layout-shift check with realistic archive lengths; do not use this as a substitute for reducing unnecessary DOM and payload size.",
    ["Do not treat content-visibility as a security boundary.", "Do not set a placeholder size from one short sample section.", "Do not claim a performance gain without measuring the actual page."],
    ["css/overflow-and-scroll", "css/intrinsic-sizing", "css/receipt-dashboard-project"])

add("multicolumn-reading", "layout", "CSS multi-column layout: fragment long text without breaking meaning",
    "Use columns for continuous reading material, not unrelated cards.",
    "Multi-column CSS splits one content flow into successive column boxes. Content continues from one column into the next, so the visual order follows the source order.",
    "A compact policy appendix may read well in two columns on a wide print page. Give the column a minimum useful width and allow the browser to choose the count; then prevent a short heading from being left alone at a column end. Keep the appendix's paragraphs and headings in their original document order. Independent case cards should use grid instead: multicolumn would make their contents fragment and reorder reading visually in ways readers do not expect. Column balancing and fragmentation depend on actual content, page size, and font metrics. Inspect a short appendix, a long appendix, and one with a large figure. When content must stay together, break-inside is a hint to test, not a guarantee for every printer.",
    '''.policy-appendix { columns: 18rem 2; column-gap: 2rem; }
.policy-appendix h2 { break-after: avoid; }
.policy-appendix figure { break-inside: avoid; }
@media (max-width: 42rem) {
  .policy-appendix { columns: 1; }
}''',
    "Column layout performs fragmentation work, which can be more expensive than a single text block when content changes frequently. For a static appendix, readability is the deciding factor. The code collapses to one column on a narrow screen, but a print stylesheet should still be checked separately because paper width and margins differ from a screen viewport. Do not hide overflow to force a clean edge: a missing sentence is worse than a ragged column. The browser may balance columns, so compare the resulting order with the source text before shipping.",
    ["Do not use columns for unrelated interactive cards.", "Do not assume break-inside is honored in every print context.", "Do not clip overflowing text to make column heights match."],
    ["css/print-styles", "css/readable-type", "css/grid-tracks"])

add("text-wrapping-and-truncation", "type-media", "CSS text wrapping and truncation: keep records readable",
    "Break long tokens where allowed and reserve ellipses for nonessential previews.",
    "White-space controls collapse and wrapping, overflow-wrap introduces break opportunities in long tokens, and text-overflow signals clipped inline content when overflow and no-wrap conditions are present.",
    "A case card may contain a long external reference and a short preview title. The reference is evidence; it must remain readable, so permit breaks anywhere when ordinary word boundaries are absent. A preview title may be clipped in a narrow list if its full text is available in the detail view and an accessible label still exposes it. Do not put an ellipsis on the only copy of a transaction identifier. The sample uses separate classes because the two content contracts differ. A single global white-space rule would be hard to reason about, and hiding overflow on the entire card can also cut off focus indicators. Check mixed scripts, long URLs, and user zoom before declaring the layout safe.",
    '''.case-reference { overflow-wrap: anywhere; }
.case-preview__title {
  min-inline-size: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.case-preview:focus-within { outline: 2px solid #175b44; outline-offset: 2px; }''',
    "Line breaking can increase block height, so a list that assumes equal card heights may need to grow. Ellipsis saves space but creates an information cost: the hidden text cannot be scanned, copied, or compared from that view. The rule does not add network requests. If a title is routinely too long, redesign the row rather than adding more clipping. The focus outline belongs outside the clipped title, on a container that remains visible. Check that full values are available in the destination and accessible to assistive technology.",
    ["Do not apply white-space: nowrap to user-generated paragraphs.", "Do not treat an ellipsis as a substitute for a full identifier.", "Do not clip the focus ring with overflow: hidden on the whole card."],
    ["css/intrinsic-sizing", "css/overflow-and-scroll", "css/focus-visible"])

add("list-markers-and-counters", "type-media", "CSS list markers and counters: change appearance without changing order",
    "Style ordered steps while keeping their structure in the document.",
    "List markers are part of a list item's presentation. Counters can derive display numbers from position, but the list element still supplies the ordered relationship to readers and software.",
    "An intake workflow has several numbered review steps. Use an ordered list in HTML, then style its marker to match the product's typography. The CSS may reset and increment a counter for a more elaborate visual treatment, but it should not be the only place the sequence exists. If items are added by the server, the visible sequence should update without hard-coded numbers in every item. A counter's scope follows the element tree, so a nested list may need its own reset to prevent unexpected numbering. Test skipped steps, nested notes, print output, and styling disabled. For ordinary decimal numbering, prefer the native marker before writing counter rules.",
    '''.intake-steps { list-style: decimal; padding-inline-start: 2rem; }
.intake-steps li { padding-inline-start: .35rem; margin-block-end: .75rem; }
.intake-steps li::marker { color: #175b44; font-weight: 700; }''',
    "The marker style costs little and leaves the list's semantic order intact. A custom counter system costs more editorial attention because resets, nested levels, and skipped items can yield misleading numbers. The sample stays with native decimal markers for that reason. Check marker contrast and alignment with a two-digit step count and a right-to-left locale. If the list uses a start value or reversed order, keep that instruction in HTML; CSS must not invent the logical sequence.",
    ["Do not build a procedural sequence from plain paragraphs and generated numbers.", "Do not hide markers without a replacement that remains understandable.", "Do not assume every nested list shares one counter scope."],
    ["css/pseudo-elements-and-generated-content", "css/logical-properties", "html/lists-and-definitions"])

add("data-table-layout", "type-media", "CSS data tables: preserve headers when columns get narrow",
    "Keep a real table and provide horizontal access before removing columns.",
    "The table layout algorithm allocates column space from its cells, widths, and layout mode. CSS can change spacing and overflow, but it should not erase header-to-cell relationships.",
    "An audit table shows case ID, owner, state, and last action. Keep the table in semantic markup with headers and a caption. Place it in a scrolling wrapper when the available width cannot show every column legibly. A minimum table width makes the overflow deliberate; the wrapper exposes the horizontal scroll. Table-layout: fixed can make column calculation predictable when widths are specified, yet long names still require wrapping or a detail view. Do not convert every cell to a block merely to avoid scrolling: that can make cross-row comparisons and header associations harder to follow. Check keyboard scrolling, focus inside the wrapper, long identifiers, and print output with all columns present.",
    '''.audit-table-scroll { overflow-x: auto; max-inline-size: 100%; }
.audit-table { inline-size: 100%; min-inline-size: 44rem; border-collapse: collapse; }
.audit-table th, .audit-table td {
  padding: .65rem .8rem;
  border-block-end: 1px solid #c6d0da;
  text-align: start;
}
.audit-table td { overflow-wrap: anywhere; }''',
    "A wide table can impose layout and paint work proportional to its row and cell count. Paginate large data sets instead of assuming overflow is the only cost. The wrapper's scrollbar needs to remain discoverable, and focus should not land in an offscreen cell without moving the scroll position. On paper, remove the narrow-screen minimum if it causes clipping; inspect the printed result rather than extrapolating from screen styling. CSS does not provide sorting or data export, so the UI must not promise those features without working controls.",
    ["Do not hide required columns solely to fit a phone width.", "Do not use CSS order to change the relation between headers and cells.", "Do not treat a scrollable table as an excuse to render thousands of rows."],
    ["css/overflow-and-scroll", "css/print-styles", "html/data-tables"])

add("form-control-states", "interaction", "CSS form states: make errors and disabled fields explicit",
    "Style native control states and keep instructions in the form markup.",
    "CSS pseudo-classes such as :focus-visible, :invalid, and :disabled respond to browser control states. They change presentation; they do not validate the server submission.",
    "A refund form contains a required amount and an optional note. A visible focus ring lets keyboard users locate the active field, while an invalid border provides one visual signal after validation has run. The error message must be real text associated with the input, and the server must still reject invalid amounts. A disabled submit button must use the actual disabled attribute, not just a muted class, if activation is unavailable. Beware of showing an error before the user has had a chance to enter anything: browser constraint validity can exist before a form has been submitted, so coordinate error visibility with the form's interaction policy. Test keyboard, touch, autofill, zoom, and high contrast.",
    '''.refund-form :focus-visible { outline: 3px solid #175b44; outline-offset: 2px; }
.refund-form [aria-invalid="true"] { border-color: #a92d3b; }
.refund-form :disabled { cursor: not-allowed; opacity: .75; }
.refund-form .field-error { color: #8a1725; }''',
    "These state selectors add negligible rendering cost. The maintenance cost lies in keeping aria-invalid, the visible message, and server validation synchronized. The sample uses an explicit aria-invalid attribute rather than styling every empty required field as an error. Color contrast must be checked against actual surfaces, and opacity may make disabled text too faint. A CSS class is not a security boundary; the backend must enforce the same field rules regardless of the button's appearance.",
    ["Do not show an error only through border color.", "Do not make a button look disabled while leaving it active.", "Do not rely on client-side CSS for validation or authorization."],
    ["css/focus-visible", "css/colors-and-contrast", "html/form-help-and-errors"])

add("background-gradients-and-shadows", "type-media", "CSS gradients and shadows: decorate without hiding content",
    "Use paint effects for depth and grouping, with a readable base color.",
    "Gradients are generated images; shadows are painted effects outside or inside a box. Neither changes the document's meaning or its layout dimensions in the same way padding and borders do.",
    "A payment summary card can use a soft gradient to separate it from the page and a restrained shadow to signal its boundary. Start with an opaque background color, then layer the gradient; if it does not render, the text still has a known surface. A strong shadow is not a substitute for a border when forced colors remove decorative paint. Avoid putting required numbers into background images, since backgrounds can be disabled and have no text alternative. The sample uses a border as the primary edge and a small shadow as optional depth. Check the actual foreground contrast at both ends of the gradient, and review printing where backgrounds may be suppressed.",
    '''.payment-summary {
  color: #173148;
  background-color: #f2f6f8;
  background-image: linear-gradient(135deg, #f2f6f8, #e3edf2);
  border: 1px solid #aebfcb;
  border-radius: .75rem;
  box-shadow: 0 .4rem 1rem rgb(20 49 71 / .12);
}''',
    "A CSS gradient avoids a separate image request, but large shadows or many overlapping effects can add paint work during scrolling. Profile a dense dashboard before using the same elevation on hundreds of cards. The gradient increases the contrast-check surface area: a foreground that passes on one end can fail on the other. The border supplies a boundary when the shadow is absent. Keep the visual effect subtle enough that focus indicators and status colors remain distinct from decoration.",
    ["Do not place a monetary amount only in a background image.", "Do not use a shadow as the sole card boundary in forced colors.", "Do not check text contrast against only one gradient stop."],
    ["css/backgrounds-and-decorative-images", "css/colors-and-contrast", "css/dark-mode-and-forced-colors"])

add("viewport-units-and-safe-area", "responsive", "CSS viewport units and safe areas: size panels around real browser chrome",
    "Use small or changing viewport units where fixed viewport assumptions cause clipping.",
    "Viewport-relative units size against a viewport reference. The newer small and changing viewport units distinguish conservative available space from space that changes as browser controls appear and disappear.",
    "A mobile case sheet needs to fit between the top and bottom of the usable viewport. A plain 100vh minimum can extend behind browser controls on some mobile browsers, so use a small-viewport baseline and a dvh unit when supported. Reserve safe-area padding where the device exposes an inset. Content may still grow beyond the viewport; min-block-size is safer than block-size for a form with validation messages or a keyboard. The sample is a layout guard, not a promise that the on-screen keyboard never covers a field. Test real mobile browser chrome, orientation changes, zoom, and a long error message. Keep the form scrollable if it grows past the available height.",
    '''.case-sheet {
  min-block-size: 100vh;
  min-block-size: 100svh;
  padding-block-end: 1rem;
  padding-block-end: max(1rem, env(safe-area-inset-bottom));
  overflow-y: auto;
}
@supports (min-block-size: 100dvh) {
  .case-sheet { min-block-size: 100dvh; }
}''',
    "Changing viewport sizing may trigger relayout while browser chrome changes, so avoid coupling it to expensive animations or constantly measured script geometry. The small-viewport baseline is steadier but may leave unused space when controls retract. Choose based on the panel's task, then measure and test on devices your users actually have. The first padding declaration covers clients without env() support; max() keeps at least one rem where the inset is zero. Do not use a fixed height that clips focusable controls when translation or validation increases content height.",
    ["Do not assume 100vh always equals visible mobile space.", "Do not set a fixed height on a form that can grow.", "Do not rely on safe-area padding to solve keyboard occlusion by itself."],
    ["css/media-queries", "css/overflow-and-scroll", "css/responsive-layout"])

add("pointer-hover-preferences", "responsive", "CSS pointer and hover queries: keep touch targets usable",
    "Use capability queries to add hover polish without requiring hover for access.",
    "The hover and pointer media features describe input capabilities. They can adapt affordances, but one device may have multiple inputs and the primary input can change.",
    "An investigation card reveals an action row. The action must be available by default or on keyboard focus; a hover effect may add emphasis when the primary pointer supports it. Do not hide a destructive action until hover on a touch device, since the user may never discover it. A coarse-pointer rule can increase spacing around controls, but target size still needs review on actual hardware. Capability queries describe the environment, not a particular user's intent or disability. Keep focus-visible styling independent of hover and test hybrid devices such as a tablet with a mouse. If the content needs a disclosure state, use a real button and state rather than a CSS-only hover reveal.",
    '''.investigation-card__actions { display: flex; flex-wrap: wrap; gap: .75rem; }
.investigation-card:focus-within { outline: 2px solid #175b44; }
@media (hover: hover) and (pointer: fine) {
  .investigation-card:hover { border-color: #175b44; }
}
@media (pointer: coarse) {
  .investigation-card__actions button { min-block-size: 2.75rem; }
}''',
    "A border-color change costs little compared with moving a whole card on hover. The coarse-pointer rule changes target height, which can increase wrapping and page length; test that the action row still fits. A hybrid device can report one primary pointer while another is attached, so the base action layout must remain usable under every query result. Check keyboard focus, touch, stylus, and mouse. The CSS cannot prevent accidental destructive actions; confirmation and authorization belong to application behavior.",
    ["Do not make hover the only way to find an action.", "Do not treat pointer: fine as proof that touch is absent.", "Do not make tap targets larger by overlapping adjacent controls."],
    ["css/focus-visible", "css/media-queries", "html/link-vs-button"])

add("audit-table-project", "projects", "CSS audit table project: responsive records without dropped columns",
    "Combine semantic table styling, scrolling, and print treatment for an incident log.",
    "This project styles an audit log whose HTML already defines a caption, headers, body rows, and a scrolling wrapper. The stylesheet preserves those relationships while allocating readable space.",
    "Start with cell padding and a visible row boundary. The table's minimum inline size keeps four columns legible on a desktop; its wrapper provides access on a narrow display. A state badge may have color, but the state word remains in the cell. At print time, remove the narrow minimum so the table can fit the page, then inspect a multipage record with long text. CSS cannot create server-side pagination or CSV export; those require real features. Keep the source order of columns stable so a reader can compare rows without decoding a card transformation. Test a long case identifier, translated owner name, empty cell, keyboard traversal, and 200% zoom before treating the layout as complete.",
    '''.audit-log__scroll { max-inline-size: 100%; overflow-x: auto; }
.audit-log { inline-size: 100%; min-inline-size: 46rem; border-collapse: collapse; }
.audit-log th, .audit-log td {
  padding: .7rem .9rem;
  border-block-end: 1px solid #c6d0da;
  text-align: start;
  vertical-align: top;
}
.audit-log td { overflow-wrap: anywhere; }
@media print { .audit-log { min-inline-size: 0; } }''',
    "The cost grows with row count and with long text that changes column measurement. Paginate large logs; do not render thousands of rows and then blame the scrollbar for slow interaction. The rule set adds no request, but a real product still needs data transport, caching, and authorization. Print treatment can produce awkward page breaks, so inspect the actual PDF or paper output with representative data. The table's HTML header associations remain the source of meaning; CSS only changes the spatial arrangement.",
    ["Do not hide an evidence column because a phone is narrow.", "Do not imply that a styled table has working sort or export controls.", "Do not assume a screen screenshot verifies the print layout."],
    ["css/data-table-layout", "css/print-styles", "html/data-tables"])

add("overscroll-boundaries", "layout", "CSS overscroll behavior: stop unwanted scroll chaining",
    "Contain a nested scroller only where crossing its boundary would disrupt the task.",
    "Overscroll behavior controls what happens when a scroll container reaches an edge. The contain value can prevent the scroll gesture from chaining to an ancestor scroller.",
    "A case detail drawer contains a long evidence list while the page behind it also scrolls. When a reader reaches the evidence list's end, moving the background page can lose context. Give the evidence region an actual scrolling box and use overscroll-behavior on that box. The property does not create scrolling by itself; overflow and a size constraint must already make the region scrollable. Keep the region reachable with a keyboard and allow the full evidence list to be read without pointer gestures. On mobile, containment can affect browser navigation gestures, so test the actual clients before applying it to the entire document. Use it on the smallest appropriate region, not as a blanket page rule.",
    '''.case-drawer__evidence {
  max-block-size: min(30rem, 60vh);
  overflow-y: auto;
  overscroll-behavior-y: contain;
  padding-inline-end: .5rem;
}''',
    "The rule adds no network request and little layout work beyond the nested scroller itself. The UX cost is more serious: a user may expect a gesture at the edge to continue scrolling the page, and a nested scroll area can be hard to discover. Check wheel, touch, trackpad, keyboard, and screen reader navigation. If the drawer is modal, focus management and background scroll locking are application concerns beyond this CSS rule. Browser support should be verified for the intended audience, with normal scroll chaining as a usable fallback.",
    ["Do not expect overscroll-behavior to create a scroll container.", "Do not disable document-level navigation gestures without a task reason.", "Do not treat nested scrolling as a replacement for focus management."],
    ["css/overflow-and-scroll", "css/scroll-snap", "css/positioning-and-sticky"])


assert len(specs) == 20 and len({spec["path"] for spec in specs}) == len(specs)
quiz_path = "quizzes/css-advanced"
titles = {path: row["title"] for path, row in by_path.items()}
titles.update({spec["path"]: spec["title"] for spec in specs})
titles[quiz_path] = "CSS applied decisions quiz"


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


for section in {spec["section"] for spec in specs}:
    hub = by_path[f"{ROOT}/{section}"]
    section_paths = [spec["path"] for spec in specs if spec["section"] == section]
    hub["data"]["modules"][0]["lessons"].extend(section_paths)
    hub["body"] += "<h2>More applied lessons</h2>" + linked_list(section_paths)
    hub["updated_at"] = stamp

for index, spec in enumerate(specs):
    path = spec["path"]
    section = spec["section"]
    assert all(target in titles for target in spec["related"]), path
    row = copy.deepcopy(by_path["css/selectors-and-cascade"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
               title=spec["title"], summary=spec["summary"], subject=f"css-{section}",
               sort_order=23000 + index, status="published", published_at=stamp,
               created_at=stamp, updated_at=stamp)
    row["tags"] = ["css", section, "web"]
    row["data"] = {
        "kind": "tutorial", "reading_minutes": 5,
        "author_path": "authors/aitrove-editorial", "subject_root": ROOT,
        "section_path": f"{ROOT}/{section}", "content_format": "html", "seo_ready": True,
        "related": [{"path": target, "title": titles[target]} for target in spec["related"]],
    }
    row["body"] = (
        f"<p>{html.escape(spec['intro'])}</p><h2>How the rule works</h2>"
        f"<p>{html.escape(spec['mechanics'])}</p>"
        f'<pre><code class="language-css">{html.escape(spec["sample"])}</code></pre>'
        "<h2>Cost and verification</h2>"
        f"<p>{html.escape(spec['cost'])}</p>"
        + common_mistakes(spec["mistakes"])
        + "<h2>Connected lessons</h2>"
        + linked_list([f"{ROOT}/{section}", *spec["related"]])
    )
    rows.append(row)

for path, related in {
    "css/custom-properties": ["css/registered-custom-properties"],
    "css/selectors-and-cascade": ["css/native-nesting", "css/scoped-rules"],
    "css/grid-tracks": ["css/subgrid-alignment", "css/intrinsic-sizing"],
    "css/overflow-and-scroll": ["css/scroll-snap", "css/overscroll-boundaries", "css/content-visibility"],
    "css/print-styles": ["css/multicolumn-reading", "css/audit-table-project"],
    "css/readable-type": ["css/text-wrapping-and-truncation", "css/list-markers-and-counters"],
    "css/media-queries": ["css/viewport-units-and-safe-area", "css/pointer-hover-preferences"],
    "css/focus-visible": ["css/form-control-states"],
}.items():
    row = by_path[path]
    row["data"].setdefault("related", []).extend(
        {"path": target, "title": titles[target]} for target in related
    )
    row["body"] += "<h2>Extend this decision</h2>" + linked_list(related)
    row["updated_at"] = stamp

root_hub = by_path[ROOT]
root_hub["body"] += (
    "<h2>Applied CSS decisions</h2>"
    + linked_list(["css/native-nesting", "css/subgrid-alignment", "css/data-table-layout",
                   "css/form-control-states", "css/audit-table-project"])
)
root_hub["updated_at"] = stamp

questions = [
    ("What does native nesting change?", ["The way related selectors are authored", "The HTML reading order", "The origin of every CSS rule"], 0, "Nesting resolves selectors relative to a parent rule; it does not change document order or origin."),
    ("What does a CSS @scope limit define?", ["Where scoped rules stop matching", "A server authorization boundary", "A new stylesheet request"], 0, "A scope limit bounds selector reach inside the document tree."),
    ("Why register a custom property with @property?", ["To declare its type, initial value, and inheritance behavior", "To make it global JavaScript state", "To make every declaration important"], 0, "Registration gives a custom property a typed contract and controlled inheritance."),
    ("When can subgrid help a set of cards?", ["When nested rows must share parent track sizing", "When cards need separate unrelated columns", "When source order must be reversed"], 0, "Subgrid uses the parent grid's tracks in the selected dimension."),
    ("What must exist before overscroll-behavior can affect a nested list?", ["A scroll container", "A transform", "A print stylesheet"], 0, "Overscroll behavior applies at a scrolling boundary; it does not create scrolling."),
    ("Which value is safer for a short horizontal card rail than strict mandatory snapping?", ["proximity", "none on every card", "fixed"], 0, "Proximity snapping can assist alignment without forcing every scroll end to a snap point."),
    ("What is the risk of a poor contain-intrinsic-size estimate?", ["Scroll-position or layout shifts when content renders", "A change to server-side sorting", "Loss of the HTML heading element"], 0, "The estimated size reserves space before offscreen content is rendered."),
    ("Where should an incident identifier remain readable?", ["In document text, with wrapping if needed", "Only in a CSS pseudo-element", "Only in a gradient"], 0, "Required identifiers belong in real content; wrapping keeps them inspectable."),
    ("What does text-overflow: ellipsis need in a single-line preview?", ["Clipping overflow and a no-wrap condition", "A grid container only", "A custom font file"], 0, "The property signals overflow already hidden in the inline direction."),
    ("How should a narrow audit table retain four important columns?", ["Expose horizontal scrolling while keeping table semantics", "Delete two columns from the DOM", "Convert every cell into a pseudo-element"], 0, "A scroll wrapper preserves cells and their header relationships."),
    ("Which state should the server still verify when CSS marks a form invalid?", ["The submitted field values", "The border color", "The user's hover capability"], 0, "CSS state presentation cannot validate or authorize a submission."),
    ("What should be available without hover on a touch device?", ["The card's required actions", "Only the decorative border", "A hidden confirmation dialog"], 0, "Required actions must remain discoverable and operable without hover."),
]
assert len(questions) == 12
quiz_template = by_path["quizzes/css-layout-accessibility"]
quiz = copy.deepcopy(quiz_template)
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
            path=quiz_path, title=titles[quiz_path],
            summary="Twelve applied checks on modern CSS layout, scoping, text, and input behavior.",
            sort_order=3102, status="published", published_at=stamp,
            created_at=stamp, updated_at=stamp)
quiz["data"] = {
    "subject_root": ROOT, "section_path": "css/quizzes", "content_format": "html",
    "author_path": "authors/aitrove-editorial", "seo_ready": True,
    "duration_minutes": 12,
    "related": [{"path": target, "title": titles[target]} for target in [
        "css/native-nesting", "css/subgrid-alignment", "css/text-wrapping-and-truncation",
        "css/data-table-layout", "css/form-control-states"]],
    "questions": [dict(prompt=prompt, options=options, answer=answer, explanation=explanation)
                  for prompt, options, answer, explanation in questions],
}
quiz["body"] = (
    "<p>Choose the rule that preserves the document contract, then inspect the linked lesson when a failure case is unclear.</p>"
    "<h2>Review the lessons</h2>" + linked_list([item["path"] for item in quiz["data"]["related"]])
    + "<h2>Other checks</h2>" + linked_list(["css/quizzes", "quizzes/css-foundations", "quizzes/css-layout-accessibility"])
    + common_mistakes(["Do not confuse visual order with document order.",
                       "Do not treat a CSS state as server validation."])
)
rows.append(quiz)
quiz_hub = by_path["css/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Applied check</h2>" + linked_list([quiz_path])
quiz_hub["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_quizzes": 1, "total_records": len(rows)}))

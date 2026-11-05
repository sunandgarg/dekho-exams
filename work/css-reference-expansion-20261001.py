"""Add a practical CSS property reference to the local curriculum fixture."""

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
HUB = ROOT + "/reference"
specs = []


def add(slug, title, summary, definition, decision, sample, cost, mistakes, related, group):
    path = "css/" + slug
    assert path not in by_path
    specs.append(dict(path=path, title=title, summary=summary, definition=definition,
                      decision=decision, sample=sample, cost=cost,
                      mistakes=mistakes, related=related, group=group))


add("box-sizing-border-box", "CSS box-sizing: include padding and borders in a declared size",
    "Set a predictable width contract for bordered components.",
    "Box-sizing controls which parts of a box are included in its specified width and height. Content-box sizes the content alone; border-box includes padding and border within the declared dimension.",
    "A case summary card must fit a 24-rem slot even after a one-pixel border and internal padding are added. Border-box makes that width contract easier to maintain. It does not include margins, and it does not solve a long unbroken identifier that refuses to wrap. Apply the rule to the component or establish it in a deliberate reset, then inspect a real card at narrow width. The sample keeps the maximum width within the containing region. Changing box-sizing on an existing site can shift layouts that were calculated under content-box, so audit fixed-width fields and older components before making it global. Check the actual rendered box in developer tools rather than guessing from the declared inline size.",
    '''.case-summary { box-sizing: border-box; inline-size: 24rem; max-inline-size: 100%; padding: 1.25rem; border: 1px solid #aebfcb; }
.case-summary__id { overflow-wrap: anywhere; }''',
    "Box-sizing has negligible runtime cost; the migration cost is in assumptions embedded in existing widths. A card that previously occupied 24 rem plus padding becomes narrower internally when switched to border-box. Verify labels, buttons, and long IDs at 200% zoom. Keep margin outside the declared width calculation and avoid adding a width of 100% to a child that also has external margins. Use one sizing model per component family so later edits do not require mental arithmetic across mixed models.",
    ["Do not assume border-box includes margins.", "Do not change a site-wide reset without checking old fixed-width components.", "Do not use box-sizing to hide content overflow."],
    ["css/box-model-and-layout", "css/intrinsic-sizing", "css/text-wrapping-and-truncation"], "size")

add("margin-collapsing", "CSS margin collapse: explain vertical gaps before changing them",
    "Inspect block margins that combine across siblings and parents.",
    "In normal block flow, adjoining vertical margins can collapse into one gap. This applies to some sibling and parent-child relationships, not to flex or grid items.",
    "An incident report has a heading followed by a paragraph, but the measured gap is smaller than the sum of both margins. Before adding a larger number, inspect whether the margins collapsed. A border or padding between a parent and first child can separate their margins, and a grid or flex container changes the formatting context so its item margins do not collapse in the same way. None of those should be added solely to defeat a mystery; choose the layout model for the actual component. The sample gives the report section its own padding and uses one explicit heading-to-body gap. Check the first section, two adjacent sections, and the printed report where page breaks can change spacing.",
    '''.incident-section { padding-block: 1rem; }
.incident-section h2 { margin-block: 0 .75rem; }
.incident-section p { margin-block: 0 1rem; }
.incident-section p:last-child { margin-block-end: 0; }''',
    "Margin collapse itself is ordinary browser layout, not a performance defect. The cost comes from compensating with unrelated padding or negative margins across many templates. A direct local rule is easier to reason about than a series of overrides whose values depend on source order. Inspect computed margins and the box model in developer tools when a gap changes. Negative margins can make the collapsed result more surprising, so avoid using them as a first fix. At high zoom, preserve enough separation to distinguish sections without relying on a fixed card height.",
    ["Do not add both sibling margins and expect their sum in block flow.", "Do not assume flex and grid item margins collapse.", "Do not patch a gap with a negative margin before finding its owner."],
    ["css/box-model-and-layout", "css/display-and-flow", "css/multicolumn-reading"], "size")

add("spacing-shorthands", "CSS margin and padding shorthands: know which edge a value reaches",
    "Use logical longhands where direction matters and shorthands where all edges share a contract.",
    "The margin and padding shorthands assign values to multiple edges. With two values, the first covers block top and bottom in a horizontal writing mode, while the second covers inline left and right physically.",
    "A payment panel needs one amount of internal padding and a larger gap before the next section. Use padding for space inside its border and margin-block for space outside it. A physical four-value shorthand may be concise on a fixed English-only mockup, but logical properties make ownership clearer when text direction or writing mode can change. Shorthands also reset longhands they include. If a later rule sets padding-inline-start and an even later padding shorthand runs, the logical start value may be replaced. Trace source order and computed values before increasing specificity. The sample leaves the panel's horizontal margin to the layout container and applies only the external block gap it owns.",
    '''.payment-panel { padding: 1rem 1.25rem; margin-block: 0 1.75rem; border: 1px solid #aebfcb; }
.payment-panel__actions { padding-block-start: .75rem; }''',
    "These declarations have negligible runtime cost. The maintenance cost is accidental edge resets when a shorthand is introduced far from a more specific longhand. Group related declarations by component and avoid scattering overrides across files. Test right-to-left labels and a narrow form where extra inline padding can reduce available control width. Padding enlarges the painted box; margin separates it from neighbors. Neither should be used to make an interactive target appear larger if the clickable element itself stays small.",
    ["Do not confuse inner padding with outer margin.", "Do not assume a later shorthand preserves earlier edge longhands.", "Do not hard-code left and right when the design means inline start and end."],
    ["css/logical-properties", "css/box-sizing-border-box", "css/alignment-and-gap"], "size")

add("size-constraints", "CSS min and max sizes: let content grow without breaking the layout",
    "Use minimum and maximum constraints before assigning fixed heights.",
    "Width and height properties set preferred dimensions, while min and max constraints bound the used size. When content grows beyond a fixed block size, overflow behavior decides whether it clips or scrolls.",
    "A case note should remain readable whether it has one sentence or a long translated explanation. Give it a minimum block size for visual balance, but let its natural block size expand. Limit its inline measure so long lines do not stretch across the whole dashboard. The sample keeps the note within its parent and allows a long token to wrap. A height of 8 rem would look neat in a screenshot but can cut off text after zoom or validation. If a bounded scrolling area is truly required, label it and verify keyboard access. Prefer content-driven growth for the main document. Check a short note, a long note, and a missing optional note before locking any maximum.",
    '''.case-note { min-block-size: 7rem; max-inline-size: 68ch; inline-size: 100%; box-sizing: border-box; padding: 1rem; overflow-wrap: anywhere; }
.case-note p { margin-block: 0 .75rem; }''',
    "A min-size constraint does not add meaningful processing work. Its cost is the space it reserves in every repeated item, which can make a dense list far longer than necessary. Use it only where consistency helps scanning. A max-inline-size based on ch approximates a text measure rather than guaranteeing a fixed character count; different fonts change the result. Check the page with the actual production font and fallback font. Do not use max-block-size with overflow hidden on required copy, because hidden material cannot be recovered from that view.",
    ["Do not set a fixed height on user-authored text.", "Do not mistake max-inline-size for a character limit.", "Do not clip evidence to keep cards equal."],
    ["css/units-and-functions", "css/intrinsic-sizing", "css/overflow-and-scroll"], "size")

add("borders-vs-outlines", "CSS border, radius, and outline: separate box edges from focus indication",
    "Use borders to define surfaces and outlines to show focus without shifting layout.",
    "A border occupies space in the box model; an outline is painted outside the border edge and does not take layout space. Border-radius rounds the border box's corners.",
    "A refund action has a quiet border at rest and a strong outline when keyboard focus reaches it. The border makes the control legible against the panel; the outline is a state indicator that should remain visible after a theme changes. Do not remove the browser's outline and replace it with only a subtle shadow. Outline-offset can move the indicator away from the border, but a clipped ancestor may still cut it off. The sample pairs the outline with a color that needs contrast review against the actual page surface. Border-radius affects appearance, not the control's accessible name or click target. Inspect a button near the edge of a scrollable container and one inside a dialog.",
    '''.refund-action { border: 1px solid #41637c; border-radius: .5rem; padding: .7rem 1rem; background: #fff; color: #173148; }
.refund-action:focus-visible { outline: 3px solid #175b44; outline-offset: 3px; }''',
    "The outline adds negligible paint work. Borders can alter the space available to content under content-box sizing, so keep the component's box-sizing explicit when dimensions are tight. A 3-pixel focus ring can be clipped if its ancestor has overflow hidden; test the whole container, not just the button. In forced colors, browser-provided focus colors may differ, so verify that an indicator remains. A decorative radius does not reduce the need for enough padding around the action's text and a usable pointer target.",
    ["Do not remove focus outlines without an equally visible replacement.", "Do not use a shadow as the only focus state.", "Do not assume border-radius changes hit testing or semantics."],
    ["css/focus-visible", "css/box-sizing-border-box", "css/dark-mode-and-forced-colors"], "size")

add("display-visibility-hidden", "CSS display and visibility: choose the intended hidden state",
    "Decide whether a region should leave layout and the accessibility tree.",
    "Display: none removes an element's box from layout and generally removes its subtree from the accessibility tree. Visibility: hidden keeps the box's space while hiding its content and interaction.",
    "A case filter panel can be closed while the user reads the result list. If closed content should take no space and cannot be interacted with, hide the region through an application state that also updates the disclosure button. The CSS rule can render that state with display: none, but it cannot maintain aria-expanded or focus placement by itself. Visibility: hidden is useful when preserving a slot matters; it is not a way to keep hidden controls usable. Do not conflate visually hidden text for assistive technology with these hidden states. A description referenced by accessible-name attributes is a special case with browser and accessibility behavior worth testing, not a general reason to hide important instructions. Verify keyboard focus when the panel closes.",
    '''.case-filter[hidden] { display: none; }
.case-filter--reserved { visibility: hidden; }
.case-filter--open { visibility: visible; }''',
    "Removing a large subtree from rendering can reduce work, but toggling it repeatedly may cause layout shifts. Reserving space avoids movement but wastes room and may confuse users if the empty slot remains. Choose based on the interaction contract, not on animation convenience. The hidden attribute should be controlled by application state, and the trigger must convey whether the panel is expanded. Test that focus is moved or retained appropriately when a currently focused control is hidden, especially in dialogs and responsive navigation.",
    ["Do not hide an active focused control without managing focus.", "Do not treat visibility: hidden as a screen-reader-only technique.", "Do not assume CSS updates aria-expanded automatically."],
    ["css/display-and-flow", "css/focus-visible", "html/dialog-and-details"], "size")

add("grid-template-areas", "CSS grid template areas: name regions without rewriting document order",
    "Describe a page layout with named regions while keeping the HTML sequence meaningful.",
    "Grid-template-areas maps named cells to positions in an explicit grid. A grid item chooses an area with grid-area; the naming affects visual placement, not source order.",
    "A review page has a primary record and a secondary tools rail. At a narrow width, the record comes first. At a wide width, the rail can sit beside it, yet keyboard and screen-reader order still follow the HTML. Name the regions to make the stylesheet easy to inspect, and keep the area map rectangular. The sample gives the main region the flexible track and the rail a bounded width. If the rail contains a required approval action that logically belongs before the record, moving it visually will not fix the document; change the markup contract instead. Inspect the visual and focus sequences at both breakpoints, and test long tool names that might exceed the rail width.",
    '''.review-layout { display: grid; grid-template-areas: "record" "tools"; gap: 1.5rem; }
.review-layout__record { grid-area: record; min-inline-size: 0; }
.review-layout__tools { grid-area: tools; }
@media (min-width: 60rem) {
  .review-layout { grid-template-columns: minmax(0, 1fr) 16rem; grid-template-areas: "record tools"; }
}''',
    "The extra area names are a maintenance aid, not a performance feature. Grid layout work grows with the number of tracks and items, but a two-region page has little overhead. The real risk is a visually convenient area map that contradicts logical reading order. Check keyboard traversal after changing the map. An unused named area or misspelled grid-area can leave an item auto-placed, so inspect every breakpoint rather than trusting the source text. Keep essential content in the record region and bound the rail's content so it can wrap without horizontal overflow.",
    ["Do not use an area map to conceal a wrong HTML sequence.", "Do not leave a grid-area name absent from a breakpoint map.", "Do not give the main track a fixed width that breaks at zoom."],
    ["css/grid-tracks", "css/responsive-layout", "css/receipt-dashboard-project"], "layout")

add("grid-auto-placement", "CSS grid auto-placement: let repeated records fill available tracks",
    "Use automatic placement for repeated cards and preserve source order.",
    "Grid auto-placement positions items that have no explicit grid line or area. By default it follows the grid's flow as it creates implicit rows or columns.",
    "A shipment overview shows a variable number of independent cards. Define responsive columns and let the browser place each card in document order. Avoid manually assigning a line to every record because pagination and filtering will change the item count. The minmax expression gives each card a useful minimum when there is room and permits one full-width track when there is not. Dense packing can backfill gaps but may produce a visual order different from source order; skip it for an interactive record list. A tall card should simply make its row taller. Test one card, an odd count, and a card with long status text. If all cards must align internal details, use a subgrid only where the parent track relationship is real.",
    '''.shipment-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr)); gap: 1rem; }
.shipment-grid__card { min-inline-size: 0; padding: 1rem; border: 1px solid #aebfcb; }''',
    "Automatic placement avoids per-item CSS and makes changes to the record set cheap editorially. Layout still processes every rendered card, so paginate a very large collection. The sample creates as many tracks as fit; a parent with an indefinite or tiny width needs real testing. Do not confuse grid's visual placement with data sort order. If server results are ordered by severity, the DOM should carry that order. Inspect keyboard traversal after any responsive or dense placement change, and allow cards to grow with their text instead of fixing a height.",
    ["Do not use grid-auto-flow: dense on an interactive list without checking reading order.", "Do not assign explicit lines to every data-driven card.", "Do not render thousands of cards merely because auto-placement is concise."],
    ["css/grid-tracks", "css/subgrid-alignment", "css/intrinsic-sizing"], "layout")

add("flex-shorthand-and-order", "CSS flex shorthand and order: distribute space without changing meaning",
    "Set growth, shrinkage, and basis deliberately; leave logical order in HTML.",
    "The flex shorthand combines flex-grow, flex-shrink, and flex-basis. The order property changes visual order of flex items but does not change document or keyboard order.",
    "A case toolbar has a title that should absorb spare width and an action group that should retain its content width. Give the title a flexible basis and allow it to shrink to zero minimum inline size when a long title is present. Keep actions later in the markup if they are read later. Do not use order to move a destructive action to the beginning on mobile while keyboard focus stays at the end. If the toolbar wraps, test the visual grouping rather than relying on one wide screenshot. The sample uses the flex shorthand as a concise contract: the title can grow and shrink from an 18-rem basis, while actions use their natural width.",
    '''.case-toolbar { display: flex; flex-wrap: wrap; gap: .75rem; align-items: center; }
.case-toolbar__title { flex: 1 1 18rem; min-inline-size: 0; }
.case-toolbar__actions { flex: 0 1 auto; display: flex; flex-wrap: wrap; gap: .5rem; }''',
    "Flex layout cost is usually small for a toolbar. Complexity arrives when several children have implicit minimum sizes and cannot shrink as expected. Inspect flex-basis, content width, and the item's min-inline-size before adding overflow hidden. The action group may wrap at high zoom; it should remain reachable. A visual order change can create an accessibility defect even though the CSS parses and paints correctly, so read through the controls with a keyboard after any order declaration is introduced.",
    ["Do not use order to repair the document sequence.", "Do not assume flex: 1 means the same thing as flex: 1 1 auto.", "Do not clip the title before testing its minimum size."],
    ["css/flexbox-sizing", "css/alignment-and-gap", "css/responsive-layout"], "layout")

add("float-and-flow-root", "CSS float and flow-root: contain legacy text wraps",
    "Use float for text wrapping and flow-root to contain it.",
    "A floated box moves to one side of its containing block so inline content can wrap around it. Display: flow-root establishes a block formatting context that can contain floats.",
    "An archived incident report places a small evidence thumbnail next to its first paragraph. A float can produce the intended text wrap, while the report's local flow-root prevents the thumbnail from protruding into the next section. This is a narrow use for float; a page header or dashboard columns belong in grid or flexbox. The image still needs a meaningful alternative text in HTML if it conveys evidence. Give it a bounded inline size and an external margin so text does not touch it. Test a paragraph shorter than the image, a tall image, and a narrow viewport where the text may have too little room. If the wrap becomes awkward, switch to a stacked layout through a media query rather than forcing a smaller unreadable text column.",
    '''.evidence-intro { display: flow-root; }
.evidence-intro__thumb { float: inline-start; inline-size: min(10rem, 38%); margin-inline-end: 1rem; margin-block-end: .5rem; }
@media (max-width: 34rem) { .evidence-intro__thumb { float: none; display: block; inline-size: min(100%, 18rem); } }''',
    "Text wrapping around a single small image is cheap. The maintenance cost is less obvious flow behavior: a float is removed from normal flow and can protrude if the parent does not establish an appropriate context. Flow-root contains it without a clearing pseudo-element. The logical inline-start value follows writing direction where supported; test right-to-left copy. A floating image should not be used to reorder the meaning of a report. Keep the figure and caption in the correct source position, and inspect print pages for awkward breaks.",
    ["Do not build whole-page columns with floats.", "Do not forget that a float can extend beyond a short parent.", "Do not shrink evidence text merely to preserve a decorative wrap."],
    ["css/display-and-flow", "css/grid-template-areas", "css/logical-properties"], "layout")

add("background-size-position", "CSS background size and position: crop decoration deliberately",
    "Keep a real fallback color and choose whether a decorative image may crop.",
    "Background-size determines how a background image is scaled; background-position chooses its placement in the paint area. Cover fills the box and may crop the image, while contain fits the whole image and may leave empty space.",
    "A case dashboard header uses an abstract texture that carries no information. Give the header an opaque base color, prevent repetition, and use cover only because cropping cannot remove required meaning. Center positioning may be wrong if the visual focal point sits off-center, so inspect both wide and narrow headers. If the image were a photograph of evidence, it should be an HTML image with text alternative and sizing appropriate to that evidence, not a CSS background. Avoid fetching a large asset merely to fill a narrow strip; compress and size it for actual display. Test with the image blocked and in forced colors to ensure the heading remains readable.",
    '''.case-header { color: #f7fafc; background-color: #173148; background-image: url("/assets/case-header-texture.webp"); background-size: cover; background-position: 62% center; background-repeat: no-repeat; padding: 2rem 1.5rem; }''',
    "The image request and decoding usually cost far more than the CSS declarations. The path is illustrative and must be replaced by a real optimized asset before deployment. Cover can crop different portions as the box's aspect ratio changes; if the focal point matters, the art direction may need separate assets. A background can be omitted by print settings, so maintain contrast on the base color. Do not use contain and assume the image covers the whole header; any uncovered region shows the background color. Profile the delivered bytes before adding layered effects.",
    ["Do not use a background image as the only carrier of evidence.", "Do not assume cover shows the entire image.", "Do not ship the illustrative asset path without a file."],
    ["css/backgrounds-and-decorative-images", "css/image-fit-and-aspect", "css/colors-and-contrast"], "paint")

add("link-decoration-states", "CSS link decoration and states: preserve a visible navigation cue",
    "Keep links identifiable at rest, focus, and hover.",
    "Text-decoration paints marks such as underlines on text. Link state pseudo-classes let a stylesheet change a link's presentation according to interaction and visit state.",
    "A payment history page contains case links inside ordinary paragraphs. Underline them at rest so they remain recognizable without hover or color discrimination. Give keyboard focus a separate outline and increase underline thickness on hover only as an enhancement. A visited color can help orientation, but browsers restrict what visited-state styling can reveal for privacy, so do not build behavior around detecting it. Buttons and links must retain their distinct jobs: a link navigates, a button acts. The sample scopes styles to the history region so global navigation components can have their own reviewed treatment. Check contrast on every background, especially when the same link appears inside a highlighted status card.",
    '''.payment-history a { color: #145078; text-decoration-line: underline; text-decoration-thickness: .08em; text-underline-offset: .18em; }
.payment-history a:hover { text-decoration-thickness: .14em; }
.payment-history a:focus-visible { outline: 2px solid currentColor; outline-offset: 3px; }''',
    "Decoration changes are inexpensive to paint. The maintenance cost is visual consistency across ordinary, visited, hover, and focus states, each of which may be shown on several surfaces. Avoid removing the underline in a dense paragraph without an equally clear noncolor cue. A focus outline can be cut off by a clipped ancestor, so inspect the container too. The text-decoration shorthand can reset color, style, or thickness choices from other rules; longhands make the contract explicit here. Test keyboard focus before and after a long page scroll.",
    ["Do not make a link visible only on hover.", "Do not rely on visited styling for application logic.", "Do not replace a navigation link with a button solely for styling."],
    ["css/pseudo-classes", "css/focus-visible", "html/link-vs-button"], "type")

add("font-shorthand-stack", "CSS font shorthand and fallback stack: keep type stable during loading",
    "Specify the required font pieces and keep a readable system fallback.",
    "The font shorthand sets several font properties in one declaration and requires a size and family. It can also set line height with a slash after the size.",
    "An operations console uses a compact sans-serif face for its toolbar. The named face may arrive after the first render or fail to load, so keep a system fallback that fits the available widths reasonably well. A shorthand resets constituent font properties not included in the declaration; this can undo an earlier weight or style unexpectedly. Scope it to the toolbar rather than applying a new font contract to every control in the app. The sample sets a readable size, line height, and family together. Test long labels under both the intended face and the fallback, and inspect weight changes if variable font files are involved. A stylesheet declaration does not prove the font asset was fetched successfully.",
    '''.operations-toolbar { font: 500 1rem/1.4 "Case Sans", system-ui, sans-serif; }
.operations-toolbar__count { font-variant-numeric: tabular-nums; }''',
    "A custom font adds transfer and decoding cost; the CSS shorthand alone is cheap. The actual font resource belongs to a separately reviewed @font-face definition and loading policy. If the fallback has much wider glyphs, controls can wrap or shift when the face loads. Keep enough flexible space and test with font loading blocked. Tabular numerals help counts align in a changing status display, but they do not change the meaning of the count. Prefer a stable platform font when the branded face adds little value to the task.",
    ["Do not omit the required size and family from font shorthand.", "Do not assume omitted font properties retain earlier values.", "Do not ship a named family without reviewing its fallback rendering."],
    ["css/font-loading", "css/readable-type", "css/text-wrapping-and-truncation"], "type")

add("line-height-and-measure", "CSS line height and measure: protect long-form reading",
    "Set a unitless line height and cap the line measure for report prose.",
    "Line-height controls the height of line boxes. A unitless value scales with the element's own font size when inherited, which is often useful in mixed-size content.",
    "A compliance report contains paragraphs, subheadings, and short code references. Set the report's prose to a readable measure rather than letting one line stretch across a wide monitor. A unitless line height follows larger text without requiring a separate pixel value for every heading. Do not treat a ch maximum as an exact character count; glyph widths differ across fonts and languages. The sample gives ordinary paragraphs a 66-ch cap and keeps their width within the parent. Tables and code blocks need separate overflow rules because prose line-length guidance does not make a wide table fit. Check body copy with a fallback font, 200% zoom, and long terms. The final measure should be evaluated against real text, not a repeated placeholder sentence.",
    '''.compliance-report { line-height: 1.55; }
.compliance-report p { max-inline-size: min(100%, 66ch); margin-block: 0 1rem; }
.compliance-report h2 { line-height: 1.25; margin-block: 1.75rem .75rem; }''',
    "These properties add little rendering cost. Their maintenance cost is separate treatment for headings, code, and dense data, which naturally have different line-height needs. Excessive line height can separate words from the line they belong to; too little can make multi-line text hard to track. Use the font's actual metrics in visual review. Do not lock paragraph height to a fixed number of lines, since translation and user font scaling can produce more lines. Keep the report's source order and headings meaningful without CSS.",
    ["Do not set one pixel line height for all font sizes.", "Do not assume ch is an exact word or character count.", "Do not cap block height to enforce a preferred paragraph length."],
    ["css/readable-type", "css/font-shorthand-stack", "css/multicolumn-reading"], "type")

add("form-appearance-accent", "CSS form appearance and accent color: retain native behavior",
    "Prefer light native control styling before replacing an entire widget.",
    "Appearance controls how a form widget uses native operating-system styling. Accent-color can color supported controls while retaining much of their native rendering and behavior.",
    "A case intake form has checkboxes for optional notifications. Give the controls an accent color and leave their native checked mark, focus behavior, and keyboard support intact. Setting appearance: none would require reconstructing every visible state and verifying platform behavior; that is rarely justified for a routine preference field. The sample sizes the controls modestly without hiding their labels. Check checked, unchecked, disabled, and high-contrast states, as well as touch target size created by the label area. Accent color alone does not establish text contrast or a validation message. The form's HTML still owns the label and submission value, and the server must persist the preference. Styling should not suggest the option is saved before confirmation.",
    '''.case-preference { display: flex; align-items: start; gap: .65rem; }
.case-preference input[type="checkbox"] { accent-color: #175b44; inline-size: 1.15rem; block-size: 1.15rem; margin-block-start: .15rem; }
.case-preference label { line-height: 1.4; }''',
    "The native control incurs no custom image or script request. The main cost of appearance: none would be state reconstruction and cross-platform QA; avoid that unless the product has a compelling need. Different browsers may render the accent slightly differently, so verify the intended support set rather than demanding identical pixels. Do not use a CSS pseudo-element as the only checked indicator. The actual checkbox state and associated label should remain usable when the stylesheet fails.",
    ["Do not remove native appearance without rebuilding every visible state.", "Do not color a checkbox without checking its label and focus state.", "Do not mistake the checked paint for a saved server preference."],
    ["css/form-control-states", "css/focus-visible", "html/form-help-and-errors"], "type")

add("css-errors-and-fallbacks", "CSS invalid declarations and fallbacks: fail locally, not silently",
    "Place a dependable value before an optional enhancement and inspect the computed result.",
    "CSS parsers generally discard an invalid declaration while continuing with the rest of the stylesheet. A later valid declaration can replace an earlier fallback when the browser understands it.",
    "A report panel uses a basic solid border and a newer color function for a softer theme. Keep the plain color first, then add the enhanced value in a later declaration. An older browser ignores a declaration it cannot parse and retains the preceding valid one. A syntactically valid custom property can still produce an invalid value when substituted at computed-value time, which is a different failure path; inspect the actual computed style. Do not assume that a successful stylesheet download means every declaration applied. Test the component with a known unsupported value in a local sandbox, not in production, to see how the fallback behaves. Comments can document a compatibility decision, but they should not hide a copied pile of unexplained overrides.",
    '''.report-panel { border: 1px solid #aebfcb; background-color: #f2f6f8; }
@supports (color: color-mix(in srgb, black, white)) {
  .report-panel { background-color: color-mix(in srgb, #f2f6f8 85%, #d4e3ec); }
}''',
    "A fallback can increase CSS bytes slightly, but it avoids a broken surface on unsupported clients. The real cost is maintaining two paths and testing both. @supports checks parsing support for the feature condition, not color contrast or the meaning of a whole component. Verify the final surface against its text in each path. Avoid placing a fallback after the enhanced declaration, where it would override the enhancement by source order. Keep related declarations near each other so reviewers can see the intended progression.",
    ["Do not read a successful network response as proof every rule applied.", "Do not put the fallback after the enhancement in the same cascade position.", "Do not expect @supports to verify accessibility or business behavior."],
    ["css/supports-feature-query", "css/custom-properties", "css/cascade-layers"], "paint")

add("filter-effects", "CSS filter effects: use image treatment without obscuring evidence",
    "Apply filters to decorative previews, not to the only copy of an evidentiary image.",
    "The filter property processes an element's rendered pixels through operations such as grayscale or blur. It changes appearance after layout; it does not change the element's intrinsic content.",
    "A gallery of closed cases uses desaturated thumbnails to distinguish archived records from active ones. Keep a visible text state beside each thumbnail, since grayscale alone cannot communicate archival status. Do not apply blur to evidence that a reviewer must inspect; provide the original image through a proper detail view. The sample uses grayscale only on a decorative preview class and returns full color on keyboard focus within the card. A visual effect can create a new stacking context, so inspect overlays and positioned badges after adding it. Check the card with images disabled and in print. CSS filtering cannot redact sensitive information, because the underlying asset remains available and must be protected at the server boundary.",
    '''.case-card--archived .case-card__preview { filter: grayscale(80%); }
.case-card--archived:focus-within .case-card__preview { filter: none; }
.case-card__status { font-weight: 700; }''',
    "Filters may require extra painting or compositing, especially across many large images. Measure a gallery with realistic thumbnails before applying blur or stacked effects to every item. A simple grayscale filter on a small preview may be acceptable, but the benchmark must come from the target devices. The status text remains the primary information channel. Do not confuse a visual mask with a security control, and do not let an effect reduce the legibility of captions or focus indicators. If print output is official, inspect it without relying on color treatment.",
    ["Do not use blur as data redaction.", "Do not convey archived status only through grayscale.", "Do not apply expensive filters to hundreds of full-resolution images without measurement."],
    ["css/image-fit-and-aspect", "css/colors-and-contrast", "css/stacking-contexts"], "paint")

add("aspect-ratio-boxes", "CSS aspect-ratio: reserve a stable box without fixing both dimensions",
    "Give previews a preferred shape while allowing at least one dimension to remain automatic.",
    "Aspect-ratio expresses a preferred inline-to-block size relationship for a box. It influences automatic sizing; when both dimensions are fixed, those explicit sizes take precedence.",
    "A case attachment list includes image previews of different original shapes. Give each preview frame a 4-to-3 box so the list remains stable while assets load, then use object-fit to control whether the image content crops inside that frame. The HTML image should still include its own width and height when known, since those dimensions help the browser reserve space even if CSS fails. Keep the full evidence image available through the record view; a cropped thumbnail is only a preview. The frame's ratio does not guarantee content fits if captions are placed inside it, so keep captions outside the cropped media box. Test a portrait, a panorama, and a failed image request. At narrow width, let the frame's inline size shrink with its container.",
    '''.attachment-preview { inline-size: min(100%, 18rem); aspect-ratio: 4 / 3; overflow: hidden; background: #e7edf1; }
.attachment-preview img { inline-size: 100%; block-size: 100%; object-fit: cover; object-position: center; }''',
    "The ratio can reduce layout shifts by reserving a predictable preview box, but it cannot reduce image download bytes. Serve appropriately sized files and measure the actual layout shift if this is a performance goal. Cropping with object-fit is a visual decision; it must not make the preview the only way to inspect evidence. Aspect-ratio has little calculation cost for a simple box. Do not set both inline and block sizes to fixed values and expect the ratio to override them. Keep captions, controls, and status outside the clipping frame so they remain readable.",
    ["Do not mistake a cropped preview for the complete evidence image.", "Do not fix both dimensions and expect aspect-ratio to choose a size.", "Do not hide captions inside an overflow-clipped media frame."],
    ["css/image-fit-and-aspect", "css/size-constraints", "css/receipt-dashboard-project"], "size")


assert len(specs) == 18 and len({spec["path"] for spec in specs}) == len(specs)
quiz_path = "quizzes/css-property-decisions"
titles = {path: row["title"] for path, row in by_path.items()}
titles.update({spec["path"]: spec["title"] for spec in specs})
titles.update({HUB: "CSS Property Decisions", quiz_path: "CSS property decisions quiz"})


def linked_list(paths):
    assert all(path in titles for path in paths), [path for path in paths if path not in titles]
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in paths
    ) + "</ul>"


def mistakes_list(items):
    return "<h3>Common Mistakes</h3><ul>" + "".join(
        f"<li>{html.escape(item)}</li>" for item in items
    ) + "</ul>"


group_titles = {
    "size": ("Boxes and dimensions", "Size components without clipping their content."),
    "layout": ("Placement and flow", "Place repeated content while preserving its source sequence."),
    "type": ("Type and controls", "Keep text, links, and native controls readable."),
    "paint": ("Paint and fallbacks", "Use effects without carrying required meaning in decoration."),
}
hub = copy.deepcopy(by_path[ROOT])
hub.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + HUB)),
           path=HUB, title=titles[HUB],
           summary="Property-level CSS decisions for boxes, placement, text, controls, and paint.",
           subject="css-reference", sort_order=18580, status="published",
           published_at=stamp, created_at=stamp, updated_at=stamp)
hub["data"] = {
    "modules": [
        {"title": title, "summary": summary,
         "lessons": [spec["path"] for spec in specs if spec["group"] == group]}
        for group, (title, summary) in group_titles.items()
    ],
    "subject_root": ROOT, "section_path": HUB, "content_format": "html",
    "seo_ready": True, "author_path": "authors/aitrove-editorial",
}
assert all(module["lessons"] for module in hub["data"]["modules"])
hub["body"] = (
    "<p>Choose a CSS property by the layout or presentation contract it must preserve. The pages below use small component examples and state what each declaration costs to maintain or render.</p>"
    + "".join(
        f"<h2>{html.escape(title)}</h2><p>{html.escape(summary)}</p>"
        + linked_list([spec["path"] for spec in specs if spec["group"] == group])
        for group, (title, summary) in group_titles.items()
    )
    + "<h2>Connected paths</h2>" + linked_list([ROOT, "css/css-tutorial/layout", "css/css-tutorial/type-media", "css/quizzes"])
    + mistakes_list(["Do not pick a property by name before inspecting the containing layout.",
                     "Do not use paint effects to replace labels, values, or interaction state."])
)
rows.append(hub)

for index, spec in enumerate(specs):
    path = spec["path"]
    assert all(target in titles for target in spec["related"]), path
    row = copy.deepcopy(by_path["css/selectors-and-cascade"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)),
               path=path, title=spec["title"], summary=spec["summary"],
               subject="css-reference", sort_order=24000 + index,
               status="published", published_at=stamp, created_at=stamp,
               updated_at=stamp)
    row["tags"] = ["css", "reference", "web"]
    row["data"] = {
        "kind": "tutorial", "reading_minutes": 5,
        "author_path": "authors/aitrove-editorial", "subject_root": ROOT,
        "section_path": HUB, "content_format": "html", "seo_ready": True,
        "related": [{"path": target, "title": titles[target]} for target in spec["related"]],
    }
    row["body"] = (
        f"<p>{html.escape(spec['definition'])}</p><h2>When to use it</h2>"
        f"<p>{html.escape(spec['decision'])}</p>"
        f'<pre><code class="language-css">{html.escape(spec["sample"])}</code></pre>'
        "<h2>Cost and verification</h2>"
        f"<p>{html.escape(spec['cost'])}</p>"
        + mistakes_list(spec["mistakes"])
        + "<h2>Connected lessons</h2>" + linked_list([HUB, *spec["related"]])
    )
    rows.append(row)

root_hub = by_path[ROOT]
root_hub["data"]["resource_tabs"].insert(-1, {"title": titles[HUB], "path": HUB})
root_hub["body"] += "<h2>Property reference</h2>" + linked_list([HUB])
root_hub["updated_at"] = stamp
for path, related in {
    "css/box-model-and-layout": ["css/box-sizing-border-box", "css/margin-collapsing", "css/size-constraints"],
    "css/grid-tracks": ["css/grid-template-areas", "css/grid-auto-placement"],
    "css/flexbox-sizing": ["css/flex-shorthand-and-order"],
    "css/display-and-flow": ["css/display-visibility-hidden", "css/float-and-flow-root"],
    "css/backgrounds-and-decorative-images": ["css/background-size-position", "css/filter-effects"],
    "css/focus-visible": ["css/borders-vs-outlines", "css/link-decoration-states"],
    "css/font-loading": ["css/font-shorthand-stack"],
    "css/readable-type": ["css/line-height-and-measure"],
    "css/form-control-states": ["css/form-appearance-accent"],
    "css/image-fit-and-aspect": ["css/aspect-ratio-boxes"],
}.items():
    row = by_path[path]
    row["data"].setdefault("related", []).extend(
        {"path": target, "title": titles[target]} for target in related
    )
    row["body"] += "<h2>Property decisions</h2>" + linked_list(related)
    row["updated_at"] = stamp

questions = [
    ("What does border-box include in a declared width?", ["Content, padding, and border", "Content and margin only", "Margin, outline, and shadow"], 0, "Border-box includes padding and border, while margin remains outside."),
    ("Where can adjacent vertical margins collapse?", ["Between ordinary block-flow siblings", "Between flex items", "Between grid tracks"], 0, "Certain adjacent margins in normal block flow collapse; flex and grid item margins do not."),
    ("Which property adds space inside a panel's border?", ["padding", "margin", "outline-offset"], 0, "Padding separates content from the border inside the box."),
    ("Why might aspect-ratio have no sizing effect?", ["Both relevant dimensions are fixed", "The box has a border", "The element has a class"], 0, "A preferred ratio influences sizing only when at least one dimension is automatic."),
    ("What is a common use for outline on a button?", ["A focus indicator without changing layout size", "A replacement for the button's label", "A server validation rule"], 0, "Outlines are painted outside the border and do not occupy layout space."),
    ("What remains when visibility: hidden is applied?", ["The element's layout space", "A usable keyboard action", "The element's painted text"], 0, "Visibility hides paint while preserving the box's space."),
    ("What does grid-template-areas change?", ["Visual placement of named grid items", "Document and keyboard order", "Backend sort order"], 0, "Named areas place items visually but do not rewrite the DOM sequence."),
    ("When is grid auto-placement useful?", ["For a variable set of repeated cards", "Only for a single fixed item", "To change the data sort order"], 0, "Automatic placement handles items without per-item line assignments."),
    ("Which tool contains a text-wrapped float within its parent?", ["display: flow-root", "text-decoration: none", "opacity: 0"], 0, "A flow-root formatting context contains the float."),
    ("What can background-size: cover do?", ["Crop a decorative image to fill a box", "Reveal every pixel without empty space", "Provide image alternative text"], 0, "Cover fills the area and may crop an edge."),
    ("What must remain visible for an inline navigation link?", ["A recognizable link cue at rest and focus", "Only a hover color", "A CSS-generated href"], 0, "A link needs a visible cue before hover and a keyboard focus indicator."),
    ("What does appearance: none require on a checkbox?", ["Rebuilding and testing its visual states", "No further work", "Only changing its server value"], 0, "Removing native appearance keeps functionality but removes much built-in visual treatment."),
]
assert len(questions) == 12
quiz = copy.deepcopy(by_path["quizzes/css-advanced"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
            path=quiz_path, title=titles[quiz_path],
            summary="Twelve applied questions on CSS sizing, placement, type, and controls.",
            sort_order=3103, status="published", published_at=stamp,
            created_at=stamp, updated_at=stamp)
quiz["data"] = {
    "subject_root": ROOT, "section_path": "css/quizzes", "content_format": "html",
    "author_path": "authors/aitrove-editorial", "seo_ready": True,
    "duration_minutes": 12,
    "related": [{"path": target, "title": titles[target]} for target in [
        "css/box-sizing-border-box", "css/margin-collapsing", "css/grid-template-areas",
        "css/background-size-position", "css/form-appearance-accent"]],
    "questions": [dict(prompt=prompt, options=options, answer=answer, explanation=explanation)
                  for prompt, options, answer, explanation in questions],
}
quiz["body"] = (
    "<p>Choose the property that preserves the component's content and interaction contract, then inspect the linked lesson for the boundary case.</p>"
    "<h2>Review the lessons</h2>" + linked_list([item["path"] for item in quiz["data"]["related"]])
    + "<h2>Other checks</h2>" + linked_list(["css/quizzes", "quizzes/css-advanced"])
    + mistakes_list(["Do not use a visual fix to hide a document-order defect.",
                     "Do not treat a parsed declaration as proof it is appropriate for the content."])
)
rows.append(quiz)
quiz_hub = by_path["css/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Property check</h2>" + linked_list([quiz_path])
quiz_hub["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_hubs": 1, "new_quizzes": 1,
                  "total_records": len(rows)}))

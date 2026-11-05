"""Add CSS behavior lessons and connect them to existing curriculum paths."""

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
hub_path = "css/css-tutorial/reference"
specs = []


def add(slug, title, summary, definition, decision, sample, cost, mistakes, related, group):
    path = "css/" + slug
    assert path not in by_path
    specs.append(dict(path=path, title=title, summary=summary, definition=definition,
                      decision=decision, sample=sample, cost=cost, mistakes=mistakes,
                      related=related, group=group))


add("containment-boundaries", "CSS contain: isolate work without cutting off content",
    "Choose layout or paint containment only after checking what escapes the component.",
    "The contain property marks aspects of an element's subtree as independent from the surrounding page. Layout containment limits layout interactions; paint containment also clips painting beyond the element's bounds.",
    "A case-list row updates its status several times while neighboring rows stay still. Layout containment can give the browser a clearer boundary for those changes, but the row must be a real independent unit. Do not add paint containment if a focus ring, popover, or error message needs to extend beyond the row. Size containment is stronger: the children's sizes no longer determine the container's size, so a row may collapse unless dimensions are supplied. In the sample, only layout containment is requested. Test a long translated status, an expanded details area, and a keyboard-focused action before measuring whether the boundary helps. The declaration can also change containing-block and stacking behavior for positioned descendants; inspect badges that formerly aligned against an outer panel.",
    ".case-list__row { contain: layout; padding: 1rem; border-block-end: 1px solid #b7c7d0; }\n.case-list__row:focus-within { outline: 2px solid #175b44; outline-offset: 2px; }",
    "Containment is a performance hint with layout consequences, not a free speed switch. Profile the real list before and after; a small static page may show no useful gain. Paint containment clips overflow, while size containment needs a deliberate sizing contract. Layout containment itself creates a new formatting and stacking context and can alter absolute positioning. Keep the boundary on the smallest independent region and review overlays, print output, and high zoom. If the row's content must affect surrounding layout in a particular way, preserve that behavior instead of forcing isolation.",
    ["Do not use paint containment around a focus ring or escaping menu.", "Do not apply size containment without a size plan.", "Do not claim a performance gain without measuring the real page."],
    ["css/content-visibility", "css/stacking-contexts", "css/size-constraints"], "size")

add("isolation-stacking", "CSS isolation: give a component a stacking boundary",
    "Keep local overlays and blending inside the component that owns them.",
    "Isolation set to isolate forces an element to form a new stacking context. Descendants can then be ordered within that context without competing directly with elements outside it.",
    "A receipt card has a local status badge layered over its header. Isolate the card so a large badge z-index cannot unexpectedly climb above a neighboring dialog. The card still sits in the page's own stacking order; isolation does not make it a modal layer, and a child cannot escape above a sibling context whose whole box is painted later. The sample uses a modest local z-index and a named component class rather than a site-wide number scale. Check the card beside sticky navigation and inside a scroller. If a popover must cross the card boundary, place that popover in an appropriate top layer or layout owner instead of escalating its descendant z-index.",
    ".receipt-card { position: relative; isolation: isolate; }\n.receipt-card__status { position: absolute; inset-block-start: .75rem; inset-inline-end: .75rem; z-index: 1; }",
    "A stacking boundary is cheap by itself, but it can change paint order in ways that surprise a page assembled from independent components. Inspect shadows, tooltips, and focused controls that overlap the edge. Avoid treating z-index as a global priority number: its comparisons are local to a stacking context. Keep ordinary content in document order so the badge's visual placement does not become the only way to understand the status. If blending is involved, test the result against both the card surface and neighboring surfaces before keeping the effect.",
    ["Do not expect a descendant z-index to escape its parent's stacking context.", "Do not use isolation to make an ordinary card behave like a dialog.", "Do not place required status text solely in an overlaid badge."],
    ["css/stacking-contexts", "css/positioning-and-sticky", "css/borders-vs-outlines"], "layout")

add("pointer-events-targeting", "CSS pointer-events: remove decorative hit targets carefully",
    "Let a noninteractive overlay pass pointer input through without disabling the control beneath.",
    "Pointer-events controls whether an element can be selected as the target of pointer input. The value none removes that element from ordinary pointer hit testing; it is not a disabled-state mechanism.",
    "A search field contains a decorative magnifier drawn over its leading edge. The icon has no action, so pointer-events none lets a click in that region reach the input. Keep the input itself interactive and retain its visible label. Applying none to a button to simulate disabled behavior is unsafe: keyboard focus may still reach it, event listeners and descendants can behave differently, and the form's actual disabled contract remains unchanged. The sample scopes the rule to the decoration only. Test touch selection, mouse clicks near the icon, and keyboard tab order. If a real clear-search control is added later, it needs its own button and hit target; do not inherit this decorative rule.",
    ".search-field { position: relative; }\n.search-field__decoration { position: absolute; inset-inline-start: .8rem; top: 50%; transform: translateY(-50%); pointer-events: none; }",
    "Hit testing itself is inexpensive. The cost is the interaction mismatch when visual affordances and actual targets diverge. A parent set to none may still receive events during capture or bubbling from a targetable descendant, so do not use this CSS as an authorization or event-suppression boundary. Native disabled attributes and application state decide whether an action is allowed. Inspect the target with browser hit-testing tools if clicks are lost. Keep decorative overlays small enough that they do not obscure entered text or the focus outline.",
    ["Do not use pointer-events none to implement authorization or disabled state.", "Do not put the rule on the input or its real action button.", "Do not assume event listeners on an ancestor stop running."],
    ["css/form-control-states", "css/positioning-and-sticky", "html/form-help-and-errors"], "layout")

add("text-selection-controls", "CSS user-select: keep copyable data copyable",
    "Restrict accidental selection on a small decorative handle, not on the evidence around it.",
    "User-select controls whether text can be selected. It affects a browser interaction, not the document's content, permissions, or whether scripts can read that content.",
    "An audit timeline has a drag handle beside each entry. Suppressing selection on that handle can prevent accidental highlighting during a drag, while case IDs and notes remain selectable for copying into a report. Do not apply user-select none to the whole card: reviewers may need an exact reference number, and touch users often rely on selection controls. The sample scopes the rule to the handle and explicitly keeps the record text selectable. Browser behavior and inheritance details vary, so test the actual control in the supported browsers. A drag interaction also needs pointer and keyboard behavior in the application; CSS alone does not create an accessible rearrangement workflow.",
    ".audit-entry__drag-handle { user-select: none; cursor: grab; }\n.audit-entry__reference { user-select: text; }",
    "The declaration has negligible rendering cost. Its product cost can be high when a blanket rule blocks copy, lookup, or assistive workflows. Test selecting a partial reference with a mouse, selecting on touch, and copying the entire entry with a keyboard. User-select all is useful only where atomic selection matches the task; it can prevent partial extraction of long text. This property is not a content-protection feature. If a value is sensitive, enforce access at the data and service layer rather than hiding selection affordances.",
    ["Do not disable text selection across a report or article.", "Do not treat user-select as a security control.", "Do not assume a drag handle is keyboard usable because it has a grab cursor."],
    ["css/pointer-events-targeting", "css/form-control-states", "html/data-tables"], "type")

add("scroll-target-offsets", "CSS scroll offsets: reveal anchors below a persistent header",
    "Reserve room for a fixed toolbar when fragment navigation moves a heading into view.",
    "Scroll-padding changes the scrollport's preferred viewing area; scroll-margin adds space around a target when it is scrolled into view. They affect scrolling placement, not the element's ordinary layout box.",
    "An incident report links from a table of contents to section headings. A persistent toolbar can cover the heading after a fragment jump even though the link worked. Put scroll-padding-block-start on the scrolling root or container that owns that toolbar, and use scroll-margin-block-start on a target when one section needs extra room. The sample chooses the document scrollport and a modest heading offset; nested scrollers require their own treatment. Confirm browser back navigation, keyboard focus, and direct loading of a fragment URL. Do not add a large top margin to every heading just to repair scrolling, since that changes the printed report and all normal page gaps.",
    "html { scroll-padding-block-start: 5rem; }\n.incident-report h2[id] { scroll-margin-block-start: 1rem; }",
    "These offsets are inexpensive, but stale values can hide content again when the toolbar changes height at narrow widths or high zoom. Prefer a sizing token tied to the actual toolbar design and test with wrapped navigation. A nested overflow container may have a different scrollport from the document. Smooth scrolling is optional and must respect reduced-motion preferences if enabled elsewhere. Keep target headings visible and focusable by the navigation behavior; a visually correct offset does not repair a missing fragment ID or misleading link label.",
    ["Do not place the offset on the wrong scroll container.", "Do not use ordinary margins to fix only fragment scrolling.", "Do not assume the header height is fixed under zoom or translation."],
    ["css/scroll-snap", "css/positioning-and-sticky", "html/anchors-and-paths"], "layout")

add("hyphenation-and-language", "CSS hyphens: wrap prose with a declared language",
    "Allow long words to break in narrow reading columns without damaging identifiers.",
    "Hyphens controls whether words may break with a hyphen at line ends. Automatic hyphenation depends on language information and browser resources, so its results are not a fixed string transformation.",
    "A translated policy note sits in a narrow sidebar. Enable automatic hyphenation on the prose only after the HTML language is set correctly; then check languages the site actually serves. Keep invoice codes, URLs, and copyable identifiers outside that treatment, since splitting them may make transcription harder. The sample pairs auto hyphenation with overflow wrapping for an exceptionally long token, but the latter can break at points that are not linguistic syllables. Test a short English note, a long translated note, and a compound identifier. If a browser lacks an appropriate dictionary, the text may wrap differently. The paragraph must remain readable without relying on a specific hyphen position.",
    ".policy-note { max-inline-size: 32ch; hyphens: auto; overflow-wrap: break-word; }\n.policy-note__reference { hyphens: none; overflow-wrap: anywhere; }",
    "Hyphenation can change line count and therefore card height. That is a layout cost, not a defect: avoid fixed heights around legal or procedural copy. Browser dictionaries and language tags affect results, so screenshot tests should not assert an exact line break across engines. The CSS is cheap compared with font loading and layout of a long document. If an identifier must be copied exactly, keep its underlying text intact and make the visual break a presentation detail. Review print output, where narrower columns can amplify hyphenation.",
    ["Do not enable automatic hyphenation without the correct document language.", "Do not insert hard hyphens into identifiers to force a visual break.", "Do not lock the paragraph to a fixed height after enabling wrapping."],
    ["css/text-wrapping-and-truncation", "css/line-height-and-measure", "html/language-and-direction"], "type")

add("writing-mode-layout", "CSS writing-mode: test layout axes rather than rotating text",
    "Use a writing mode for genuine vertical text, then review logical spacing and controls.",
    "Writing-mode establishes the direction in which text lines are laid out. It also changes the relationship between inline and block axes, so logical sizing and spacing follow the writing mode.",
    "A bilingual archive has a narrow vertical title strip for a genuinely vertical label. Writing-mode vertical-rl gives the strip a vertical line flow without rotating its entire box with a transform. Keep the surrounding document in its ordinary writing mode and inspect how inline-size, block-size, padding-inline, and alignment behave at the boundary. Do not turn a full form vertical for decoration: keyboard order, reading expectations, and control rendering need a separate review. The sample scopes the mode to one label. Test a short label, a longer translated label, and high zoom. If the content is actually horizontal text displayed sideways, a transform might be a distinct visual choice, but it does not change layout axes.",
    ".archive-spine__label { writing-mode: vertical-rl; inline-size: max-content; max-block-size: 4rem; padding-inline: .5rem; }",
    "Changing the writing mode changes line layout and can alter the space a component requests from its parent. That can be more significant than the paint cost of the declaration. Use logical properties consistently; a physical width may still be useful for a fixed design, but it has a different meaning from inline-size under vertical flow. Check the selected font and fallback because glyph orientation and spacing can differ. Preserve an ordinary readable label in the DOM rather than baking letters into an image. Print and narrow mobile layouts deserve separate inspection.",
    ["Do not assume inline-size always means physical width.", "Do not rotate an entire form merely to fit a visual strip.", "Do not replace selectable text with an image of vertical lettering."],
    ["css/logical-properties", "css/line-height-and-measure", "html/language-and-direction"], "type")

add("fragmentation-break-inside", "CSS break-inside: keep small report units together in print",
    "Prevent an evidence card from splitting across pages when it can fit on one page.",
    "Break-inside controls permitted fragmentation within an element when content is distributed across pages or columns. Avoid requests are preferences; a unit larger than the available page may still have to break.",
    "A printable incident report groups a timestamp, source, and short note in one evidence card. Asking the print formatter to avoid a break inside that card can keep its label beside the data. Keep the card reasonably small and let long narratives flow as ordinary paragraphs; one giant unbreakable report section can leave empty pages or overflow. The sample scopes the rule to each card under print media and keeps screen layout untouched. Test the first card near a page boundary, a long note, and a report with an image. Browser print engines can paginate differently, so verify the output rather than assuming a single screenshot proves every paper size.",
    "@media print { .evidence-card { break-inside: avoid; margin-block-end: .75rem; } }",
    "Print pagination takes layout work, but the main cost here is wasted page space when too many large blocks refuse to split. A browser may override an impossible avoidance request. Do not hide overflowing text or shrink it until unreadable to force a single-page card. If the report is a formal artifact, inspect A4 and Letter, headers, footers, and grayscale output. In multi-column reading views the same property has a related fragmentation role, but its results still depend on content height and available column space.",
    ["Do not treat avoid as a guarantee for an oversized block.", "Do not apply it to an entire long report.", "Do not validate only the on-screen layout when the rule targets print."],
    ["css/print-styles", "css/printable-incident-project", "css/multicolumn-reading"], "layout")

add("cascade-reset-keywords", "CSS all and revert-layer: reset with a named boundary",
    "Choose a reset keyword according to the cascade boundary you intend to cross.",
    "The all shorthand resets nearly every CSS property on an element except direction, unicode-bidi, and custom properties. Revert-layer rolls a property back to the preceding cascade layer's result rather than to a universal default.",
    "An embedded receipt preview inherits a third-party theme that changes button text and border styling. A blanket all reset can be tempting, but it also removes useful typography, spacing, and form appearance. Start by identifying which layer owns the bad declaration. In a layered stylesheet, revert-layer on the specific property can expose the result from an earlier layer without discarding every other setting. The sample keeps a base button color and resets only the theme layer's color choice for a specialized action. Test the result with the theme layer absent, with user styles, and in forced colors. The reset keyword is a cascade tool, not a shortcut around understanding origin, importance, specificity, and order.",
    "@layer base, theme;\n@layer base { .receipt-action { color: #173148; } }\n@layer theme { .receipt-action { color: #fff; } .receipt-action--plain { color: revert-layer; } }",
    "The CSS bytes are small, but the maintenance cost is high if a broad reset silently strips inherited readability or native control cues. Revert-layer depends on a meaningful layer structure; without that structure it cannot express the intended boundary. All also does not reset custom properties, which may continue feeding later declarations. Inspect computed styles for color, font, line height, focus ring, and form appearance after any reset. Prefer a narrow property override when it states the decision clearly. Do not use a reset to paper over an unknown theme collision.",
    ["Do not assume all clears custom properties.", "Do not use revert-layer without understanding the layer order.", "Do not strip control styles and forget focus or forced-color states."],
    ["css/cascade-layers", "css/specificity-is-where", "css/css-errors-and-fallbacks"], "paint")

add("clip-path-decoration", "CSS clip-path: clip decoration without hiding required content",
    "Shape a decorative surface while leaving text and controls outside its clipping region.",
    "Clip-path defines the region of an element that remains visible. Content outside the region is clipped from painting; the property's shape does not rewrite the element's ordinary layout dimensions.",
    "A case header has a diagonal decorative accent. Put that accent in its own element and clip it, rather than clipping the entire header and losing the title, status, or focus outline. A polygon can express the edge without a separate image request. The sample uses a color block behind the real content. Check narrow widths, longer translated titles, and high zoom, where an accent that occupies too much of the header can obscure text even if the text itself is not clipped. A clipping shape is presentation only; the DOM must still contain the actual information. If an action sits near the shaped edge, verify its full pointer target and focus indicator remain visible.",
    ".case-header { position: relative; isolation: isolate; }\n.case-header__accent { position: absolute; inset: 0; z-index: -1; background: #dceaf0; clip-path: polygon(0 0, 100% 0, 88% 100%, 0 100%); pointer-events: none; }",
    "A simple polygon may be cheap, but animating a complex clipping path across many large surfaces can add paint work. Measure on target devices before making it a motion effect. The shape changes visible pixels and pointer hit regions, not the space reserved in layout, so neighboring boxes may still follow the rectangular dimensions. Keep enough contrast when the decorative region fails to render. Do not use clipping for redaction: underlying data and assets remain available. Review print and forced-color output, where decorative regions may disappear or change.",
    ["Do not clip the element containing the only visible title or action.", "Do not treat clipping as data redaction.", "Do not assume a shaped surface occupies shaped layout space."],
    ["css/backgrounds-and-decorative-images", "css/isolation-stacking", "css/pointer-events-targeting"], "paint")

add("backdrop-filter-legibility", "CSS backdrop-filter: preserve contrast beneath translucent panels",
    "Blur a changing backdrop only when the panel remains readable without the effect.",
    "Backdrop-filter applies graphical effects to the pixels behind an element. A visible result normally needs a background that is at least partly transparent; it does not blur the element's own text in the same way as filter.",
    "A floating case summary sits over a changing dashboard image. A light translucent surface with backdrop blur can separate the summary from the image, but the label and amount still need sufficient contrast when the effect is unsupported or the image changes. Start with a mostly opaque fallback color, then add the blur as decoration. The sample keeps the same readable foreground in both states. Avoid using the blur to hide sensitive information behind the panel: the underlying pixels still exist. Test the worst background crop, reduced transparency settings where available, print, and high zoom. If the summary is a dialog, its focus and semantics come from the HTML and interaction layer, not from the frosted appearance.",
    ".case-summary-overlay { color: #173148; background: rgb(247 250 252 / 94%); }\n@supports (backdrop-filter: blur(8px)) { .case-summary-overlay { background: rgb(247 250 252 / 80%); backdrop-filter: blur(8px); } }",
    "Blurring a large moving backdrop can require extra compositing and paint work. Measure scrolling and animation on the devices that actually use the interface; a narrow panel may be fine while a full-screen blur may not be. The fallback must carry the readability contract because feature support alone does not establish contrast. Avoid stacking multiple filters and translucency layers without a reason. Do not infer privacy from the visual effect. A plain opaque panel is often a better fit for dense financial or evidentiary data.",
    ["Do not rely on blur as a privacy boundary.", "Do not make text contrast depend on one background crop.", "Do not apply a full-screen blur without measuring scrolling cost."],
    ["css/filter-effects", "css/colors-and-contrast", "css/css-errors-and-fallbacks"], "paint")

add("cursor-affordances", "CSS cursor: match the pointer cue to a real action",
    "Use cursor changes as a minor cue while preserving native control behavior.",
    "Cursor selects a pointer image or keyword when a pointing device is over an element. It describes an affordance; it does not turn a static element into a button or make a disabled action safe.",
    "A draggable column-width handle in an audit table may use col-resize because that matches its actual pointer interaction. The resize operation must exist, the handle needs a usable hit area, and a keyboard route should be considered if resizing is part of the task. Do not put cursor pointer on every decorative card just to suggest interactivity. Links and buttons already have semantic behavior that survives touch and keyboard use; a cursor cannot supply it. The sample targets only the real resize grip and leaves ordinary table cells untouched. Test the hit area at high zoom and near a horizontal scroll edge, where pointer precision becomes harder.",
    ".audit-table__resize-grip { cursor: col-resize; inline-size: .75rem; touch-action: none; }\n.audit-table__resize-grip:focus-visible { outline: 2px solid #175b44; }",
    "Changing a cursor is almost free to render, but misleading cues waste user time and can conceal missing behavior. Touch devices may never show the cursor, so the visual design and accessible name must explain the control without it. Touch-action none can change gesture behavior, so scope it tightly and verify the surrounding table still scrolls. For a genuinely disabled native button, use the disabled attribute and a readable visual state; a not-allowed cursor alone does not block activation. Keep any custom cursor asset small if one is necessary.",
    ["Do not assign pointer to a static card with no action.", "Do not simulate disabled state with a cursor keyword.", "Do not suppress touch scrolling across the entire table to support one handle."],
    ["css/pointer-events-targeting", "css/data-table-layout", "css/focus-visible"], "type")


assert len(specs) == 12 and len({spec["path"] for spec in specs}) == len(specs)
titles = {path: row["title"] for path, row in by_path.items()}
titles.update({spec["path"]: spec["title"] for spec in specs})
hub = by_path[hub_path]
group_indices = {"size": 0, "layout": 1, "type": 2, "paint": 3}


def links(paths):
    assert all(path in titles for path in paths)
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in paths
    ) + "</ul>"


for index, spec in enumerate(specs):
    path = spec["path"]
    assert all(target in titles for target in spec["related"]), path
    row = copy.deepcopy(by_path["css/selectors-and-cascade"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)),
               path=path, title=spec["title"], summary=spec["summary"],
               subject="css-reference", sort_order=24018 + index,
               status="published", published_at=stamp, created_at=stamp,
               updated_at=stamp)
    row["tags"] = ["css", "reference", "web"]
    row["data"] = {
        "kind": "tutorial", "reading_minutes": 5,
        "author_path": "authors/aitrove-editorial", "subject_root": "css/css-tutorial",
        "section_path": hub_path, "content_format": "html", "seo_ready": True,
        "related": [{"path": target, "title": titles[target]} for target in spec["related"]],
    }
    row["body"] = (
        f"<p>{html.escape(spec['definition'])}</p><h2>When to use it</h2>"
        f"<p>{html.escape(spec['decision'])}</p>"
        f'<pre><code class="language-css">{html.escape(spec["sample"])}</code></pre>'
        f"<h2>Cost and verification</h2><p>{html.escape(spec['cost'])}</p>"
        + "<h3>Common Mistakes</h3><ul>"
        + "".join(f"<li>{html.escape(item)}</li>" for item in spec["mistakes"])
        + "</ul><h2>Connected lessons</h2>" + links([hub_path, *spec["related"]])
    )
    rows.append(row)
    hub["data"]["modules"][group_indices[spec["group"]]]["lessons"].append(path)

for group, heading in [
    ("size", "Containment boundaries"),
    ("layout", "Interaction and flow boundaries"),
    ("type", "Selection and text axes"),
    ("paint", "Resets and visual effects"),
]:
    hub["body"] += f"<h2>{heading}</h2>" + links(
        [spec["path"] for spec in specs if spec["group"] == group]
    )
hub["updated_at"] = stamp

for source, targets in {
    "css/content-visibility": ["css/containment-boundaries"],
    "css/stacking-contexts": ["css/isolation-stacking"],
    "css/form-control-states": ["css/pointer-events-targeting"],
    "css/scroll-snap": ["css/scroll-target-offsets"],
    "css/text-wrapping-and-truncation": ["css/hyphenation-and-language"],
    "css/logical-properties": ["css/writing-mode-layout"],
    "css/print-styles": ["css/fragmentation-break-inside"],
    "css/cascade-layers": ["css/cascade-reset-keywords"],
    "css/backgrounds-and-decorative-images": ["css/clip-path-decoration"],
    "css/filter-effects": ["css/backdrop-filter-legibility"],
    "css/data-table-layout": ["css/cursor-affordances"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Related behavior</h2>" + links(targets)
    row["data"].setdefault("related", []).extend(
        {"path": target, "title": titles[target]} for target in targets
    )
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "total_records": len(rows)}))

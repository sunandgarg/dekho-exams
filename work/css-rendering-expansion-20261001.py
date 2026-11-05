"""Add rendering and input lessons plus a decision quiz to the CSS reference."""

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
quiz_path = "quizzes/css-rendering-decisions"
specs = []


def add(slug, title, summary, definition, decision, sample, cost, mistakes, related):
    path = "css/" + slug
    assert path not in by_path
    specs.append(dict(path=path, title=title, summary=summary, definition=definition,
                      decision=decision, sample=sample, cost=cost, mistakes=mistakes,
                      related=related))


add("scrollbar-gutter-stability", "CSS scrollbar-gutter: reserve space when a panel starts scrolling",
    "Keep a changing record list from shifting horizontally as its scrollbar appears.",
    "Scrollbar-gutter reserves space for a classic scrollbar on a scrolling box. Overlay scrollbars do not consume that gutter, so the visual result depends on the platform's scrollbar model.",
    "A case list receives records while an operator is reviewing it. Before the list overflows, its rows fill the panel; after overflow, a classic scrollbar steals inline space and can make values wrap. A stable gutter avoids that late width change without forcing a scrollbar to appear when there is nothing to scroll. Apply it to the actual scrolling panel, not to every ancestor. The sample pairs an overflow limit with a stable gutter and leaves the list's height bounded by the available viewport. Test a short list, a long list, overlay scrollbars, and high zoom. The rule will not fix a layout that was too narrow before the scrollbar appeared, and it cannot guarantee identical screenshots across operating systems.",
    ".case-list { max-block-size: min(70vh, 38rem); overflow-y: auto; scrollbar-gutter: stable; }",
    "Reserving a gutter can reduce layout shifts in classic-scrollbar environments, but it also leaves less content width while the list is short. Overlay-scrollbar systems may show no reserved space at all. The declaration is inexpensive; the real cost is a design that assumes a fixed number of columns at every width. Use flexible cell sizing and verify long IDs still wrap. If the panel is part of a dialog, keyboard focus and scrolling must remain usable. Do not hide the scrollbar to make the panel look cleaner; users need to discover that more records exist.",
    ["Do not expect a reserved gutter with overlay scrollbars.", "Do not apply the rule to a non-scrolling ancestor and expect the panel to stabilize.", "Do not hide overflow merely to avoid a width shift."],
    ["css/overflow-and-scroll", "css/data-table-layout", "css/size-constraints"])

add("touch-action-gestures", "CSS touch-action: scope gesture control to the interactive surface",
    "Keep page scrolling available while a touch-operated canvas or handle consumes a specific gesture.",
    "Touch-action tells the browser which default touch gestures may begin on an element. It is considered before event handlers run, so it cannot be repaired by changing the property after a gesture starts.",
    "A signature pad in a case intake form needs drawing strokes, while the rest of the form still needs normal vertical scrolling. Set touch-action none on the drawing surface only and give that surface a clear boundary and keyboard alternative for the task. A resize handle might instead need a narrower gesture policy, but never blanket the whole page with none. The sample leaves its form wrapper untouched. Test drawing with a finger, two-finger zoom, page scrolling from outside the pad, and touch selection in nearby fields. CSS does not implement the drawing logic; pointer handling, storage, undo, and accessibility belong to the application. If the signature is legally significant, the service must validate and retain the submitted data independently of the visual canvas.",
    ".intake-signature__surface { touch-action: none; inline-size: 100%; min-block-size: 12rem; border: 2px solid #41637c; }",
    "Touch-action itself has little paint cost. Its failure cost is severe when it blocks panning or zooming over a large region. Keep the restricted surface as small as the actual gesture area and test on physical touch devices. Browser zoom is an accessibility route; do not disable it across the document. A gesture may already be claimed by the browser when application code receives a pointer cancellation, so handle cancellation as an ordinary input path. Preserve a non-touch way to complete the underlying task rather than equating a canvas gesture with universal access.",
    ["Do not disable touch gestures on the whole page for one pad.", "Do not assume CSS creates the signature workflow.", "Do not omit a usable alternative to a drag-only action."],
    ["css/pointer-events-targeting", "css/cursor-affordances", "css/form-control-states"])

add("will-change-budget", "CSS will-change: reserve a rendering hint for measured trouble",
    "Use a short-lived rendering hint only after profiling an actual transition.",
    "Will-change tells the browser that specified properties are likely to change. It is a hint, not an instruction to make an animation fast or a promise that a new layer will be created.",
    "An operations drawer slides into view during case review. Its transform transition might already run smoothly; measure it before adding a persistent hint. If tracing shows a real rendering issue, scope will-change to the drawer's imminent transition state and remove that state after the motion completes. The sample uses a state class applied by the interaction layer, which must also clean it up on cancellation. Do not put will-change transform on every card in a large list. A browser can allocate extra resources for hinted elements and keep them around longer than the animation, especially if the class never clears. Test an open, close, interrupted close, and reduced-motion path.",
    ".review-drawer.is-preparing-motion { will-change: transform; }\n.review-drawer { transition: transform 180ms ease-out; }\n@media (prefers-reduced-motion: reduce) { .review-drawer { transition: none; } }",
    "The intended benefit is avoiding work at the moment of motion, but extra layers and memory can outweigh it. Measure frame timing and memory on a realistic device; a desktop screenshot cannot prove the optimization. Adding the hint early enough may help, yet leaving it active indefinitely turns a temporary expense into a standing one. Test focus and reading order when the drawer moves; compositing speed does not establish interaction quality. Prefer a simple transform transition without a hint until evidence says otherwise. Do not use will-change as a general-purpose performance reset.",
    ["Do not apply will-change to every repeated card.", "Do not leave a temporary hint active forever.", "Do not claim improved motion without before-and-after measurement."],
    ["css/transitions-and-transforms", "css/reduced-motion", "css/content-visibility"])

add("transform-origin-pivots", "CSS transform-origin: move a visual pivot without moving the layout box",
    "Pivot a small disclosure icon around the point its motion should communicate.",
    "Transform-origin sets the point around which a transform is applied. The transformed pixels can move, but the element's original layout box continues to occupy its normal space.",
    "A disclosure control rotates a small chevron when its details open. Centering the pivot inside the icon avoids a lopsided sweep; it does not change the button's label or accessible expanded state. Keep the icon decorative and let the HTML control carry the interaction. The sample uses a data state on the component, which an application must keep in sync with the disclosure's real state. Test the open and closed state at high zoom and with motion reduction enabled. Do not rotate the full text label merely to make the chevron appear animated. If the icon's hit area feels too small, enlarge the button's padding; transform-origin cannot enlarge a target or alter layout spacing.",
    ".case-disclosure__chevron { display: inline-block; transform-origin: center; transition: transform 160ms ease; }\n.case-disclosure[aria-expanded=\"true\"] .case-disclosure__chevron { transform: rotate(90deg); }\n@media (prefers-reduced-motion: reduce) { .case-disclosure__chevron { transition: none; } }",
    "A small transform is usually cheap to animate, but large transformed surfaces may trigger compositing and repaint costs that need measurement. The declaration has no ability to fix a broken disclosure implementation. Because transforms do not reflow neighboring content, a wide rotation can overlap nearby labels; leave adequate space. Keep a static state cue when animation is removed. A change of writing direction or icon artwork can make the chosen rotation misleading, so inspect the complete control rather than the isolated icon. Preserve the browser's focus indicator around the button.",
    ["Do not use a rotating icon as the only expanded-state signal.", "Do not expect a transform to reserve extra layout space.", "Do not animate the full text control when only its icon needs motion."],
    ["css/transitions-and-transforms", "css/reduced-motion", "html/dialog-and-details"])

add("mix-blend-mode-boundary", "CSS mix-blend-mode: confine decorative blending to one surface",
    "Blend a decorative mark without allowing neighboring content to change its color.",
    "Mix-blend-mode chooses how an element's pixels combine with the rendered backdrop in its stacking context. It is distinct from background-blend-mode, which blends an element's own background layers.",
    "A case-card watermark may blend softly into a colored card background. Isolate the card first so the watermark does not interact with unrelated content behind it, and keep the actual case status as plain text above the decorative layer. The sample uses multiply on the watermark only. Test the card on light and dark surfaces, in print, and with the watermark hidden. If the card includes a link, ensure its underline and focus outline remain clear against every blended result. Do not use blending to create the sole readable copy of a label: changing backdrops can invert or erase contrast. An isolated component still needs a reviewed foreground/background pair for all required information.",
    ".case-card { position: relative; isolation: isolate; background: #e8f0f3; }\n.case-card__watermark { mix-blend-mode: multiply; opacity: .25; pointer-events: none; }",
    "Blend operations can increase paint or compositing work, especially across many large, scrolling cards. Profile a realistic list before keeping the effect. The cheaper design may be a static background color or a precomposed decorative asset. Isolation changes stacking behavior, so inspect popovers and positioned badges after adding it. Contrast must be tested on the final composited pixels, not the source colors alone. Blending cannot protect data or substitute for an accessible status. If print settings omit background colors, the content must remain understandable.",
    ["Do not blend required text with an unpredictable backdrop.", "Do not confuse mix-blend-mode with background-blend-mode.", "Do not skip stacking and performance checks on a repeated component."],
    ["css/isolation-stacking", "css/colors-and-contrast", "css/background-gradients-and-shadows"])

add("mask-image-decoration", "CSS mask-image: fade decoration without fading data",
    "Mask a decorative stripe while preserving unmasked labels and actions.",
    "Mask-image supplies an image used to hide or reveal portions of an element. A gradient can act as the mask, with transparent regions hiding pixels and opaque regions retaining them.",
    "An archive header has a colored stripe that fades toward its trailing edge. Apply the mask to a separate decoration element, not to the header containing the archive title, account number, or actions. The sample has a base header background so losing the masked stripe does not remove contrast or meaning. Do not use a mask to conceal confidential text: the underlying content remains in the document and may still be available to scripts or copied data. Test browser support, high contrast modes, print, and a narrow translated title. If a mask is unsupported, the stripe may show in full, so its unmasked form must also be harmless. Keep any pointer input on the real controls, not on the decoration.",
    ".archive-header { position: relative; background: #173148; color: #fff; }\n.archive-header__stripe { position: absolute; inset: auto 0 0; block-size: .5rem; background: #7fc6d2; mask-image: linear-gradient(90deg, #000, transparent); pointer-events: none; }",
    "A simple gradient mask is usually modest, but masks over many large animated surfaces can add compositing work. Measure before treating it as an inexpensive universal effect. Keep fallback colors and contrast stable when the mask is absent. Masking changes visible pixels, not document semantics or the original box size. A decorative layer should not capture clicks or cover the focus ring; inspect stacking and clipping around the header. If the design can use a plain gradient background instead, compare the simpler rendering path before adding a mask.",
    ["Do not mask required text or controls.", "Do not treat a mask as redaction.", "Do not assume the unmasked fallback remains visually harmless without checking it."],
    ["css/clip-path-decoration", "css/filter-effects", "css/backgrounds-and-decorative-images"])

add("shape-outside-flow", "CSS shape-outside: let prose wrap around a floated decoration",
    "Use shape-outside only when the visual figure and text flow share a deliberate reading order.",
    "Shape-outside defines the contour around which inline content flows beside a floated element. It does not clip the element's own pixels; the float and its dimensions still participate in layout.",
    "A long incident narrative begins beside a circular decorative case marker. Float the marker and give it a circular wrap contour so the text does not leave a rectangular gap. Keep the marker's content nonessential; the report must read correctly when CSS is removed or the float drops above the paragraph on a narrow screen. The sample sets an explicit size, float, and shape margin. Test short and long paragraphs, right-to-left text, and high zoom. Do not use a shaped float to position a key action or evidence image: text wrapping around it may make the sequence harder to follow. For ordinary two-column layout, grid is clearer and less sensitive to changing copy length.",
    ".incident-note__marker { float: inline-start; inline-size: 4.5rem; aspect-ratio: 1; border-radius: 50%; shape-outside: circle(50%); shape-margin: .75rem; margin-inline-end: .5rem; }",
    "The shape calculation is generally small, but repeated complex shapes can make layout and maintenance harder. The larger cost is readability: narrow lines around a large float can produce awkward word breaks. Check the actual production font and localized copy. Shape-outside is not a substitute for semantic figure markup or a caption. The floated box still affects layout and may need containment by its parent; inspect the next section to ensure it clears the float. A circle shaped marker is optional decoration, so the narrative must not rely on it to explain the incident.",
    ["Do not expect shape-outside to clip the marker itself.", "Do not wrap core data or controls around an arbitrary contour.", "Do not omit an explicit float and size when defining the shape."],
    ["css/float-and-flow-root", "css/multicolumn-reading", "css/writing-mode-layout"])

add("color-mix-surfaces", "CSS color-mix: derive a surface without assuming contrast",
    "Mix design tokens for decoration, then verify the final text contrast.",
    "Color-mix computes a color from input colors in a named color space and chosen proportions. Its result depends on the color space as well as the weights, so the same inputs can look different in different spaces.",
    "A reconciliation panel uses a mild highlight based on its brand accent. Define a solid fallback first, then mix the accent with white for the panel background in supporting browsers. Keep the text color explicit. The sample uses sRGB for a predictable compatibility choice; a perceptual space can produce a different visual result and needs its own review. Do not infer that a 15-percent accent automatically passes contrast with dark text. Test the final computed color against the real font size and weight, in dark mode, and in forced colors. If a custom property supplies the accent, inspect its fallback too. A missing token can invalidate the computed declaration even when color-mix itself is supported.",
    ".reconciliation-panel { color: #173148; background: #e9f1f3; }\n@supports (color: color-mix(in srgb, #24778a, white)) { .reconciliation-panel { background: color-mix(in srgb, #24778a 15%, white); } }",
    "Color calculation is cheap relative to image transfer or animation. The real cost is theme testing across every combination that can feed the mix. Alpha, color space, and percentages all influence the final pixel color. Use an automated contrast check on the computed result and confirm it visually under real rendering. A fallback belongs before the enhanced declaration in the same cascade position. Do not use a mixed warning background as the only signal of an error; keep the status in text and preserve a distinct border or icon where appropriate.",
    ["Do not assume a percentage guarantees accessible contrast.", "Do not omit a solid fallback for older clients.", "Do not let an undefined custom property silently remove the background declaration."],
    ["css/colors-and-contrast", "css/css-errors-and-fallbacks", "css/custom-properties"])

add("light-dark-color-scheme", "CSS light-dark: bind component colors to the active scheme",
    "Pair foreground and background values when a component supports light and dark presentation.",
    "The light-dark function selects one of two color values according to the element's active color scheme. The color-scheme property tells the browser which schemes a region supports and also affects native controls.",
    "A case detail panel appears in light and dark dashboard themes. Give the region permission to use both schemes, then select matching foreground and background colors. The sample includes a readable light fallback before the enhanced rules. Do not apply color-scheme light dark to a section whose icons, borders, or embedded images are still designed only for light mode. The function follows the active scheme, which can come from user preference or an ancestor's scheme choice; it is not a JavaScript theme switch. Check native inputs, links, focus rings, images, and print in both modes. A card that looks fine in isolation can fail against a dark page edge or a transparent overlay.",
    ".case-detail { color: #173148; background: #f7fafc; }\n@supports (color: light-dark(black, white)) { .case-detail { color-scheme: light dark; color: light-dark(#173148, #f2f7fa); background: light-dark(#f7fafc, #142a38); } }",
    "The function's runtime cost is small; the testing matrix is not. Every interactive state needs paired colors, and images with fixed light backgrounds may need special treatment. Color-scheme can change browser-rendered form controls and scrollbars, so review them rather than assuming only your CSS values change. Fallback declarations should preserve a complete light presentation if the function is unavailable. Do not state that dark mode is complete after switching only text and panel background. Verify contrast on the final composite, including disabled and error states.",
    ["Do not opt into dark controls without styling the rest of the region.", "Do not switch the background without a matching foreground.", "Do not treat light-dark as a replacement for testing both schemes."],
    ["css/dark-mode-and-forced-colors", "css/colors-and-contrast", "css/form-control-states"])

add("numeric-glyph-alignment", "CSS font-variant-numeric: keep changing values aligned",
    "Use tabular digits for columns and counters without altering their underlying numbers.",
    "Font-variant-numeric requests numeric glyph features from the chosen font. Tabular-nums gives digits equal advance widths when the font provides that feature, making changing values line up more steadily.",
    "A payment dashboard updates several amounts while operators compare rows. Apply tabular numerals to the amount column and any changing count, then align the cells at the appropriate edge. The sample keeps the underlying values as real text; CSS does not format currency, choose a locale, or add separators. Test the chosen font and its fallback because one may not supply the expected glyph feature. A label beside the number may still move if its container is sized by the whole changing string. Use a data table when the relationship among rows and columns matters, and keep each amount's meaning in a header. Do not convert numbers into images or pseudo-element content to get alignment.",
    ".payment-table__amount { font-variant-numeric: tabular-nums; text-align: end; white-space: nowrap; }\n.payment-summary__count { font-variant-numeric: tabular-nums; }",
    "The glyph feature adds negligible rendering cost. The more important cost is ensuring the font files and fallbacks produce a stable table under real data. A wider tabular digit can make a dense column overflow, so test the largest expected amount, negative values, and a translated currency label. White-space nowrap should be limited to the amount itself; it can cause horizontal scrolling in a narrow table. Numeric alignment supports scanning but cannot replace server-side validation or locale-aware formatting of the underlying value.",
    ["Do not assume every font supports tabular numeral glyphs.", "Do not use CSS to generate the only copy of an amount.", "Do not apply nowrap to the whole table to protect one value."],
    ["css/data-table-layout", "css/font-shorthand-stack", "html/data-tables"])

add("page-rule-print-contract", "CSS @page: set a print sheet contract without hiding overflow",
    "Choose page margins for an exported report, then inspect actual pagination.",
    "The @page at-rule describes aspects of a paged output such as page size and page margins. It applies to printed pages, while ordinary selectors still style the document's content.",
    "An incident report is exported for review on standard office paper. A modest page margin keeps evidence away from printer edges; body content must still flow and may occupy several pages. The sample uses a print rule for page margins and a separate print selector for the report's text. Do not use @page to force a long record onto one sheet by shrinking the entire document. Printer dialogs, browser headers, and paper settings can affect the final result. Test A4 and Letter, a one-page case, a long case, and a page containing a large image. Confirm the identifying title and page content remain readable in grayscale.",
    "@page { margin: 18mm; }\n@media print { .incident-report { color: #111; background: #fff; max-inline-size: none; } }",
    "Pagination is a real layout pass and may differ among browsers. The cost of extra paper is less important than a missing timestamp or clipped evidence, so preserve complete content first. Print styles cannot guarantee printer hardware supports borderless output or a particular color mode. A page margin is not the same as a margin on the report element; the two can combine. Pair this rule with small-unit break controls where needed, and inspect a generated PDF or print preview before treating the report as an official artifact.",
    ["Do not promise identical pagination across browsers and paper settings.", "Do not shrink legal or evidentiary text solely to hit one page.", "Do not confuse page margins with margins on the report element."],
    ["css/print-styles", "css/fragmentation-break-inside", "css/printable-incident-project"])

add("smooth-scroll-preferences", "CSS scroll-behavior: make smooth jumps optional",
    "Use motion for document navigation only when it does not obscure orientation.",
    "Scroll-behavior controls whether scrolling initiated by navigation or scrolling APIs moves instantly or smoothly within a scroll container. It does not govern every user scroll action.",
    "A long case report has links to numbered sections. Smooth fragment jumps can help some readers track the move, but others prefer immediate positioning or reduced motion. Apply the rule to the document scrollport and override it under the reduced-motion preference. The sample also reserves room for a persistent toolbar. Test direct fragment URLs, back navigation, a click from the bottom of the report, and keyboard focus after the jump. Do not make the animation so slow that the target feels unresponsive. The document's heading IDs and link labels must work when CSS is off; smoothness is presentation, not navigation logic. Nested scrolling panels may need their own behavior and offset rules.",
    "html { scroll-behavior: smooth; scroll-padding-block-start: 5rem; }\n@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }",
    "A long animated scroll can require repeated rendering frames and may disorient readers when the distance is large. Measure responsiveness on realistic reports, and keep the default jump if smooth motion adds no value. Browser behavior and user settings can override the request. Scroll-padding must match the actual toolbar height across zoom and responsive layouts; a smooth move to a hidden target is still a broken result. Do not use JavaScript animation just to replace this small CSS behavior unless the task requires a control CSS cannot express.",
    ["Do not force motion on users who request less of it.", "Do not assume scroll-behavior changes manual wheel or touch scrolling.", "Do not animate to a heading that remains hidden behind a toolbar."],
    ["css/scroll-target-offsets", "css/reduced-motion", "html/anchors-and-paths"])


assert len(specs) == 12 and len({spec["path"] for spec in specs}) == len(specs)
titles = {path: row["title"] for path, row in by_path.items()}
titles.update({spec["path"]: spec["title"] for spec in specs})
titles[quiz_path] = "CSS rendering and input decisions quiz"


def links(paths):
    assert all(path in titles for path in paths), paths
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in paths
    ) + "</ul>"


hub = by_path[hub_path]
hub["data"]["modules"].append({
    "title": "Rendering and input",
    "summary": "Reserve space, scope gestures, choose paint effects, and preserve motion preferences.",
    "lessons": [spec["path"] for spec in specs],
})
hub["body"] += "<h2>Rendering and input</h2>" + links([spec["path"] for spec in specs])
hub["updated_at"] = stamp

for index, spec in enumerate(specs):
    path = spec["path"]
    assert all(target in titles for target in spec["related"]), path
    row = copy.deepcopy(by_path["css/selectors-and-cascade"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)),
               path=path, title=spec["title"], summary=spec["summary"],
               subject="css-reference", sort_order=24030 + index,
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

for source, targets in {
    "css/overflow-and-scroll": ["css/scrollbar-gutter-stability"],
    "css/pointer-events-targeting": ["css/touch-action-gestures"],
    "css/transitions-and-transforms": ["css/will-change-budget", "css/transform-origin-pivots"],
    "css/isolation-stacking": ["css/mix-blend-mode-boundary"],
    "css/clip-path-decoration": ["css/mask-image-decoration"],
    "css/float-and-flow-root": ["css/shape-outside-flow"],
    "css/colors-and-contrast": ["css/color-mix-surfaces", "css/light-dark-color-scheme"],
    "css/data-table-layout": ["css/numeric-glyph-alignment"],
    "css/print-styles": ["css/page-rule-print-contract"],
    "css/scroll-target-offsets": ["css/smooth-scroll-preferences"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Further rendering decisions</h2>" + links(targets)
    row["data"].setdefault("related", []).extend(
        {"path": target, "title": titles[target]} for target in targets
    )
    row["updated_at"] = stamp

questions = [
    ("When does scrollbar-gutter stable reserve space?", ["With classic scrollbars on a suitable scrolling box", "For every overlay scrollbar", "Only after hiding overflow"], 0, "Classic scrollbar systems can reserve a gutter before overflow; overlay scrollbars do not consume one."),
    ("Where should touch-action none be applied for a signature pad?", ["On the drawing surface", "On the entire page", "Only on the submit button"], 0, "Scope gesture restriction to the surface that handles drawing."),
    ("When is will-change justified?", ["After measurement identifies a rendering problem", "On every card by default", "Whenever a stylesheet has a transition"], 0, "Hints can consume resources and should address measured trouble."),
    ("What does transform-origin change?", ["The pivot for a transform", "The document order", "The element's original layout space"], 0, "The pivot changes transformed pixels, not the original box allocation."),
    ("Which property blends an element with pixels behind it?", ["mix-blend-mode", "background-blend-mode", "border-style"], 0, "Mix-blend-mode uses the backdrop; background-blend-mode combines the element's own background layers."),
    ("What should a mask be applied to in an information header?", ["A separate decorative layer", "The only title text", "The only action button"], 0, "Masking required content can make it disappear."),
    ("What is required for shape-outside to affect nearby prose?", ["A floated, sized element", "A grid container alone", "A hidden element"], 0, "Shape-outside describes the contour around a float."),
    ("What does a color-mix percentage establish by itself?", ["A mixing proportion", "Accessible text contrast", "A dark-mode preference"], 0, "Contrast depends on the computed result and its text."),
    ("What else changes when color-scheme is set on a region?", ["Browser-rendered controls may change", "The server's stored records change", "HTML language changes"], 0, "Color-scheme informs native control rendering as well as light-dark selection."),
    ("What does tabular-nums do when the font supports it?", ["Give digits equal advance widths", "Format currency for a locale", "Validate an amount"], 0, "It affects glyph widths, not data formatting or validation."),
    ("What can @page define for a printed report?", ["Page margins", "A guaranteed one-page output", "An accessible label for every figure"], 0, "Page margins are part of paged output; pagination still depends on content and printer settings."),
    ("How should smooth fragment scrolling handle reduced motion?", ["Switch to auto under the reduced-motion preference", "Force a longer animation", "Remove heading IDs"], 0, "The navigation target remains, while the motion request is removed."),
]
assert len(questions) == 12
quiz = copy.deepcopy(by_path["quizzes/css-advanced"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
            path=quiz_path, title=titles[quiz_path],
            summary="Twelve practical checks on rendering, gestures, colors, and print.",
            sort_order=3104, status="published", published_at=stamp,
            created_at=stamp, updated_at=stamp)
quiz["data"] = {
    "subject_root": "css/css-tutorial", "section_path": "css/quizzes",
    "content_format": "html", "author_path": "authors/aitrove-editorial",
    "seo_ready": True, "duration_minutes": 12,
    "related": [{"path": target, "title": titles[target]} for target in [
        "css/scrollbar-gutter-stability", "css/touch-action-gestures",
        "css/color-mix-surfaces", "css/page-rule-print-contract"]],
    "questions": [dict(prompt=prompt, options=options, answer=answer, explanation=explanation)
                  for prompt, options, answer, explanation in questions],
}
quiz["body"] = (
    "<p>Choose the CSS behavior that preserves the component's interaction and rendering contract. Each question has one answer and an explanation.</p>"
    "<h2>Review the decisions</h2>" + links([item["path"] for item in quiz["data"]["related"]])
    + "<h2>Other checks</h2>" + links(["css/quizzes", "quizzes/css-property-decisions"])
    + "<h3>Common Mistakes</h3><ul><li>Do not confuse a paint effect with data protection.</li>"
    "<li>Do not claim performance gains without measuring the target device.</li></ul>"
)
rows.append(quiz)
quiz_hub = by_path["css/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Rendering check</h2>" + links([quiz_path])
quiz_hub["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_quizzes": 1,
                  "total_records": len(rows)}))

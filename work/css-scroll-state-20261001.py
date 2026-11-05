"""Add CSS lessons for scroll behavior, focus state, and box presentation."""

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
quiz_path = "quizzes/css-scroll-state"
specs = []


def add(slug, title, summary, definition, decision, sample, cost, mistakes, related):
    path = "css/" + slug
    assert path not in by_path
    specs.append(dict(path=path, title=title, summary=summary, definition=definition,
                      decision=decision, sample=sample, cost=cost, mistakes=mistakes,
                      related=related))


add("overflow-anchor-exclusions", "CSS overflow-anchor: exclude a volatile child, not the whole feed",
    "Keep late-loading decoration from becoming the scroll anchor in an activity feed.",
    "Scroll anchoring attempts to preserve the reader's position when content above the viewport changes size. The overflow-anchor property can exclude an element or subtree from consideration. It does not implement a chat application's explicit stick-to-bottom policy.",
    "An audit activity feed receives older entries above the current reading position while a small loading indicator at the top changes height. Leave anchoring available on the feed, but exclude the volatile indicator as an anchor candidate. Give the feed a bounded scroll area and keep each record in source order. Test a reader midway through a long feed while older entries arrive, a reader at the bottom while new entries arrive, images that finish loading above the viewport, and keyboard scrolling. The behavior of automatic anchoring is browser-controlled and can be suppressed by certain layout changes; do not promise an exact pixel location after every update. If the product needs to follow new messages only while the reader is already near the bottom, application code must measure that state and perform the scroll deliberately. The CSS rule should never hide an entry or move focus.",
    ".activity-feed { max-block-size: 34rem; overflow-y: auto; }\n.activity-feed__loading { overflow-anchor: none; min-block-size: 2rem; }",
    "The property has little direct rendering cost. The dominant cost in a live feed is the number of records, images, and layout updates. Reserve media dimensions and avoid replacing entire record trees on each poll; either can create jumps that a single exclusion cannot repair. An opt-out applied to the feed itself disables anchoring for all descendants, and a descendant cannot opt back in under that excluded subtree. Compare behavior on supported browsers with the rule removed before deciding it improves reading position. Do not use a screenshot of a static feed as proof: the failure appears only while content is inserted or resized above a scrolled reader.",
    ["Do not disable anchoring on the entire feed by default.", "Do not treat overflow-anchor as a stick-to-bottom API.", "Do not ignore image dimensions and repeated DOM replacement."],
    ["css/overflow-and-scroll", "css/scrollbar-gutter-stability", "css/content-visibility"])

add("display-contents-wrapper", "CSS display contents: remove a layout box with care",
    "Let children join a parent grid without removing a meaningful semantic container.",
    "Display contents suppresses an element's own layout box while its children continue to participate in layout. It is not equivalent to display none. Some browser and assistive-technology combinations have removed the wrapper itself from the accessibility tree, so semantic wrappers require special caution.",
    "A case dashboard's rendering layer adds a plain div around two visual cards. On wide screens, those cards should occupy adjacent grid tracks with their neighboring cards. Applying display contents to that presentation-only div lets its children become grid items. The fallback remains readable if the declaration is ignored: the wrapper occupies one grid cell and its children stack inside it. Do not apply the same technique to a list, table, labeled region, or interactive control just to simplify track placement. The removed box cannot paint its own border, padding, or background, so keep those visual treatments on the children or on a real parent. Test keyboard order, screen-reader grouping, forced colors, and responsive stacking. The DOM order stays the same even when the grid makes the children appear beside unrelated cards; preserve a logical reading sequence in HTML.",
    ".case-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }\n.case-grid__presentation { display: contents; }\n.case-grid__card { min-inline-size: 0; border: 1px solid #8ea6b4; padding: 1rem; }",
    "Removing a box can simplify grid placement, but it may also change sizing, backgrounds, stacking, and accessibility exposure. A visually empty wrapper can still be meaningful in the document if it carries a role, label, or list relationship. Keep this rule on a neutral wrapper whose loss has been reviewed, and verify the accessibility tree rather than assuming the specification's intended behavior matches every deployed browser. The performance difference is unlikely to justify an architectural rewrite by itself. If a component needs its own padding, clipping, or containing block for positioned children, display contents is the wrong tool. A small markup change or nested grid may be clearer.",
    ["Do not apply display contents to a semantic list or labeled region without accessibility testing.", "Do not expect the removed wrapper to paint a border or supply padding.", "Do not confuse a removed layout box with removed DOM content."],
    ["css/display-and-flow", "css/grid-auto-placement", "html/lists-and-definitions"])

add("scroll-snap-stop-gates", "CSS scroll-snap-stop: require a stop only for short, uniform cards",
    "Prevent one fast swipe from skipping a required review card in a controlled rail.",
    "Scroll-snap-stop decides whether scrolling may pass over a snap position. The always value asks the scroll container to stop at that position; it does not create a snap point without scroll-snap-align and a snapping container.",
    "A short horizontal onboarding rail asks a reviewer to inspect three uniform case summaries in order. Mandatory snapping and an always stop on each card can make each swipe land on a card rather than jump from first to last. Keep real next and previous controls if the workflow depends on progression; CSS cannot record that someone read a card. Test touch, a high-resolution trackpad, keyboard Tab navigation, wheel scrolling, zoom, and the final card. Never use this pattern for long paragraphs or cards taller than the scrollport: mandatory stops can make intervening content hard to reach. If summaries can grow through localization or user-entered text, choose proximity snapping or ordinary scrolling instead. A reviewer still needs a direct route to every card, and source order should match the visual sequence. The rail must remain scrollable when snapping is unsupported.",
    ".review-rail { display: flex; gap: 1rem; overflow-x: auto; scroll-snap-type: x mandatory; scroll-padding-inline: 1rem; }\n.review-rail__card { flex: 0 0 min(18rem, 82vw); scroll-snap-align: start; scroll-snap-stop: always; }",
    "Scroll snapping does not download resources, but it can increase interaction cost when users must cross several stops to reach the desired item. Measure task completion and test varied input devices rather than assuming strict snapping is helpful. A single oversized card can trap the viewport at an awkward position. When support is absent, native scrolling should still expose every card. Keep controls and focus management in HTML and application code; CSS does not satisfy a read acknowledgement or advance workflow state. Use the rule only where the small fixed sequence has been tested with real copy and at high zoom.",
    ["Do not set always without a defined snap container and alignment.", "Do not force mandatory stops on long or variable-height content.", "Do not count a CSS snap as proof a card was reviewed."],
    ["css/scroll-snap", "css/overscroll-boundaries", "css/reduced-motion"])

add("focus-within-group", "CSS :focus-within: mark the active field group",
    "Highlight a field wrapper when any of its controls receives focus while preserving the control's own indicator.",
    "The :focus-within pseudo-class matches an element when it or a descendant has focus. It can style a surrounding group without script. It does not move focus, create a label, or replace the visible focus indicator on the actual control.",
    "A payment search form groups an amount field with a currency selector. When either control receives focus, a modest wrapper border shows which group is active. The input and select keep their own focus-visible outline so a keyboard user can identify the precise control, not just the group. The base wrapper border remains present when no control is focused. Test mouse clicks, Tab movement between the two controls, an error state, forced colors, and a browser that does not apply the enhancement. Do not rely on focus-within to style a server error: a failed submission needs error text and an accessible association even after focus moves elsewhere. Nested dialogs and popovers can change where focus resides; verify the group does not remain visually active after an overlay takes focus. A wrapper highlight is optional context, not the sole focus signal.",
    ".payment-filter { border: 2px solid #8aa2b1; padding: .75rem; }\n.payment-filter:focus-within { border-color: #1c5e87; }\n.payment-filter :focus-visible { outline: 3px solid #1c5e87; outline-offset: 2px; }",
    "Selector matching and a border-color change are inexpensive. The main maintenance cost is reconciling focus, invalid, disabled, and error styles so the wrapper does not imply success when a control is invalid. Avoid a border-width change on focus because it can shift the form layout. Check contrast of both wrapper and control indicators against the actual background. The descendant focus ring remains essential, especially in a group with more than one field. CSS cannot tell whether the form value passed server validation. Keep label text, hint text, and error text in the document where they remain available without this visual enhancement.",
    ["Do not remove the focused control's own indicator.", "Do not treat focus-within as validation feedback.", "Do not change border width and shift the form on every Tab move."],
    ["css/focus-visible", "css/form-control-states", "html/form-labels"])

add("target-fragment-highlight", "CSS :target: confirm the section reached by a fragment",
    "Add a restrained highlight to the current report section after a fragment jump.",
    "The :target pseudo-class matches the element identified by the document URL fragment. It responds to fragment navigation without application state, provided the target has a matching ID in the document.",
    "A long incident report links from its contents list to individual sections. A short-lived visual highlight would require extra state code, but a persistent modest border on the current target can help readers verify arrival. Keep the heading readable and reserve space for a fixed toolbar with scroll-margin. The link and target ID must work without CSS. Test direct URLs, browser back and forward, duplicate or missing IDs, keyboard focus, high zoom, and print. :target shows which fragment is in the URL, not which section is currently centered in the viewport after manual scrolling. Do not use it as a full scrollspy or as the only confirmation for an important action. A fragment may target a heading rather than its containing section; choose the selector and HTML IDs accordingly. Avoid a dramatic animation that repeats when history navigation revisits the section.",
    ".incident-report section[id] { border-inline-start: .25rem solid transparent; scroll-margin-block-start: 5rem; }\n.incident-report section[id]:target { border-inline-start-color: #1c5e87; background: #edf5f8; }\n@media print { .incident-report section[id]:target { background: transparent; border-inline-start-color: transparent; } }",
    "The static style adds negligible rendering cost. The practical cost is keeping fragment IDs stable when content is edited or translated; broken deep links cannot be repaired by :target. If the report supports forced colors, check that the target cue remains perceptible or allow system colors to take over. A persistent highlighted section may be long, so avoid filling its entire background with a low-contrast tint that makes tables or links harder to read. Scroll-margin changes the preferred landing position but does not alter normal layout. Do not confuse the target with keyboard focus: a fragment jump may not put focus where an interactive workflow expects it.",
    ["Do not use :target as a live viewport observer.", "Do not rely on a highlight when the fragment ID is missing or duplicated.", "Do not replace keyboard focus handling with fragment styling."],
    ["css/scroll-target-offsets", "css/link-decoration-states", "html/anchors-and-paths"])

add("object-position-focal-crop", "CSS object-position: move a thumbnail crop without changing the evidence",
    "Bias a cover crop toward the useful part of an image while retaining an uncropped detail view.",
    "Object-position aligns the content of a replaced element inside its box. With object-fit cover, it changes which portion is clipped. It does not edit the image file, reduce transfer size, or recover pixels absent from the source.",
    "A case index displays a landscape photo with the relevant equipment near the right edge. The default centered crop may cut that equipment away in a square thumbnail, so move the cover crop toward the right. The detail page still needs the full image when the entire scene matters as evidence. Test portrait and landscape sources, localized cards with different dimensions, high-density screens, and zoom. A fixed 70 percent horizontal position should be verified against every image in that content class; per-image focal metadata may be needed if subjects move around. If the image is only decoration, a background may be appropriate, but meaningful evidence belongs in HTML with alternate text. Do not use the thumbnail crop as a privacy redaction: the original bytes remain available. Dimensions in HTML should reserve layout space where possible.",
    ".case-photo__thumb { inline-size: 100%; aspect-ratio: 1; object-fit: cover; object-position: 70% center; }\n.case-photo__detail { max-inline-size: 100%; block-size: auto; object-fit: contain; }",
    "The crop operation does not shrink the downloaded file. Generate an appropriately sized thumbnail or responsive image source for a busy index, then keep the full-resolution evidence where it is needed. Rendering many oversized originals as tiny covers wastes bandwidth and decode memory. Check actual focal positions after responsive layout changes; a square crop at one width may be a taller rectangle elsewhere. The rule is a presentational choice, so it must not remove information required to understand or audit the case. A failed image still needs a meaningful text alternative, and the card layout should survive without the bitmap.",
    ["Do not treat object-position as image editing or redaction.", "Do not assume one focal percentage fits every source image.", "Do not use a CSS crop to avoid serving a smaller thumbnail file."],
    ["css/image-fit-and-aspect", "css/background-size-position", "html/responsive-images"])

add("scrollbar-color-contrast", "CSS scrollbar-color: keep the scroll affordance visible",
    "Tint a local scroller only when the thumb remains distinct from its track.",
    "Scrollbar-color requests a thumb color and a track color for a scrolling box. Browser and platform settings affect the final scrollbar, and forced-colors mode can reset authored colors. It does not change whether a box can scroll.",
    "An audit side panel has a long record list and already uses overflow auto. A local scrollbar tint can align with the panel while still showing where more content exists. Choose a thumb that is visibly different from the track and test it in both the light and dark page themes. Keep scrollbar-width auto unless a narrower control has been justified separately. The sample returns control to the system under forced colors, although user agents may do this automatically. Test classic and overlay scrollbar platforms, high zoom, pointer dragging, keyboard scrolling, and a short list that does not overflow. Do not rely on the scrollbar's color as the only signal that a panel scrolls; a clipped row and surrounding layout can still be confusing. Avoid applying a global scrollbar theme to every nested scroller without reviewing each background.",
    ".audit-side-panel { max-block-size: 32rem; overflow-y: auto; scrollbar-color: #4d6577 #e6edf1; }\n@media (forced-colors: active) { .audit-side-panel { scrollbar-color: auto; } }",
    "The color rule is cheap. The cost is cross-platform testing because overlay scrollbars may appear only during interaction and may not look like the classic control used in a desktop mockup. Check contrast of the actual thumb and track rather than treating the chosen hex values as proof. A very dark track can make the panel feel disabled; a faint thumb can conceal the scroll affordance. Keep the native input path and avoid hiding the scrollbar merely to gain a few pixels. The browser may override authored colors for accessibility, and that override should be welcomed rather than counteracted with platform-specific pseudo-elements.",
    ["Do not use an indistinct thumb and track pair.", "Do not assume authored colors override system accessibility settings.", "Do not hide a second scroll region's affordance for visual tidiness."],
    ["css/scrollbar-width-access", "css/overflow-and-scroll", "css/dark-mode-and-forced-colors"])

add("text-decoration-skip-ink", "CSS text-decoration-skip-ink: keep underlined copy legible",
    "Let an underline avoid descenders while retaining a visible link cue.",
    "Text-decoration-skip-ink controls whether text decoration lines skip areas where glyph ink crosses them. The auto value lets the browser interrupt an underline around descenders; none draws a continuous line through them. Font and browser rendering influence the result.",
    "A case report embeds evidence links in dense paragraphs. Keep the underline visible at rest and let the browser skip descenders where that makes the words easier to scan. Set an explicit underline thickness and offset only after checking the real font; too much offset can make the line look detached, while too little can cross glyphs even when skipping is enabled. Test lower-case words with descenders, mixed scripts, high zoom, a light and a dark surface, and forced colors. The effect is typographic polish, not the link's meaning. A link still needs a real href and a focus indicator. Do not remove the underline and depend on color alone. Underline behavior for CJK text and different writing modes may warrant a separate design review rather than applying one global rule to every language.",
    ".case-report a { text-decoration-line: underline; text-decoration-thickness: .1em; text-underline-offset: .16em; text-decoration-skip-ink: auto; }\n.case-report a:focus-visible { outline: 3px solid #1c5e87; outline-offset: 2px; }",
    "Decoration drawing has negligible cost relative to font loading or layout. The maintenance cost is visual testing with the actual typeface, weight, and language mix. Skipping ink changes pixels, not link hit targets or text selection. If an underline becomes too fragmented with a particular display font, review its offset and thickness before forcing a continuous line through every descender. The browser may render skip behavior differently; the link should remain recognizable in each result. Keep contrast between the decoration and the surrounding surface, and verify the focus outline does not merge with the underline on tightly spaced lines.",
    ["Do not remove the resting underline and rely only on color.", "Do not assume skip-ink fixes an underline placed too close to glyphs.", "Do not treat typographic decoration as a keyboard focus indicator."],
    ["css/link-decoration-states", "css/readable-type", "css/writing-mode-layout"])


assert len(specs) == 8
titles = {path: row["title"] for path, row in by_path.items()}
titles.update({item["path"]: item["title"] for item in specs})
titles[quiz_path] = "CSS scroll and state decisions quiz"


def links(paths):
    assert all(path in titles for path in paths), paths
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in paths
    ) + "</ul>"


hub = by_path[hub_path]
hub["data"]["modules"].append({
    "title": "Scroll and state contracts",
    "summary": "Preserve reading position, focus clarity, source order, crop meaning, and scrolling affordances.",
    "lessons": [item["path"] for item in specs],
})
hub["body"] += "<h2>Scroll and state contracts</h2>" + links([item["path"] for item in specs])
hub["updated_at"] = stamp

for index, item in enumerate(specs):
    row = copy.deepcopy(by_path["css/selectors-and-cascade"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + item["path"])),
               path=item["path"], title=item["title"], summary=item["summary"],
               subject="css-reference", sort_order=24080 + index,
               status="published", published_at=stamp, created_at=stamp,
               updated_at=stamp)
    row["tags"] = ["css", "reference", "web"]
    row["data"] = {
        "kind": "tutorial", "reading_minutes": 5,
        "author_path": "authors/aitrove-editorial", "subject_root": "css/css-tutorial",
        "section_path": hub_path, "content_format": "html", "seo_ready": True,
        "related": [{"path": target, "title": titles[target]} for target in item["related"]],
    }
    row["body"] = (
        f"<p>{html.escape(item['definition'])}</p><h2>When to use it</h2>"
        f"<p>{html.escape(item['decision'])}</p>"
        f'<pre><code class="language-css">{html.escape(item["sample"])}</code></pre>'
        f"<h2>Cost and verification</h2><p>{html.escape(item['cost'])}</p>"
        + "<h3>Common Mistakes</h3><ul>"
        + "".join(f"<li>{html.escape(mistake)}</li>" for mistake in item["mistakes"])
        + "</ul><h2>Connected lessons</h2>" + links([hub_path, *item["related"]])
    )
    rows.append(row)

for source, targets in {
    "css/overflow-and-scroll": ["css/overflow-anchor-exclusions", "css/scrollbar-color-contrast"],
    "css/display-and-flow": ["css/display-contents-wrapper"],
    "css/scroll-snap": ["css/scroll-snap-stop-gates"],
    "css/focus-visible": ["css/focus-within-group"],
    "css/scroll-target-offsets": ["css/target-fragment-highlight"],
    "css/image-fit-and-aspect": ["css/object-position-focal-crop"],
    "css/link-decoration-states": ["css/text-decoration-skip-ink"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Further interaction details</h2>" + links(targets)
    row["data"].setdefault("related", []).extend(
        {"path": target, "title": titles[target]} for target in targets
    )
    row["updated_at"] = stamp

questions = [
    ("What does overflow-anchor none on a loading indicator do?", ["Excludes that subtree from anchor selection", "Pins the feed to its bottom", "Hides older records"], 0, "The indicator is excluded; explicit follow-to-bottom behavior needs application logic."),
    ("What happens if scroll anchoring is disabled on the entire feed?", ["Descendants cannot opt back in there", "Every child becomes a scroll anchor", "The browser must scroll to the bottom"], 0, "An opted-out subtree cannot be re-enabled by a descendant."),
    ("What does display contents remove?", ["The element's own layout box", "Its descendants from the DOM", "Every child's accessibility text"], 0, "The wrapper box disappears, while descendants continue in layout."),
    ("Where is display contents especially risky?", ["On a semantic list or labeled region", "On a neutral presentation-only wrapper", "On an unused decorative span"], 0, "Some implementations can remove the wrapper itself from the accessibility tree."),
    ("What else is needed for scroll-snap-stop always to matter?", ["A snapping container and a snap alignment", "A network request", "A hidden scrollbar"], 0, "The stop controls passing over an existing snap position."),
    ("Why avoid mandatory snap stops on long cards?", ["Content can become hard to reach", "All text becomes bold", "The cards leave source order"], 0, "Strict snapping may trap or skip a readable region."),
    ("What does :focus-within style?", ["An element with focus inside its subtree", "Only the clicked mouse pointer", "Every invalid field"], 0, "It matches the focused element or an ancestor of it."),
    ("What does :target follow?", ["The document URL fragment", "The current viewport center", "The most recently hovered card"], 0, "It marks the element identified by the current fragment."),
    ("What does object-position change with object-fit cover?", ["Which part of the image is cropped into view", "The downloaded byte count", "The image's alt text"], 0, "It aligns the replaced content within its box."),
    ("What does scrollbar-color need besides valid syntax?", ["A visible thumb-track contrast on target platforms", "A hidden scrollbar", "A global override for every scroller"], 0, "A scrollbar remains useful only when its parts can be distinguished."),
    ("What does text-decoration-skip-ink affect?", ["Underline painting around glyph ink", "The link destination", "Keyboard focus order"], 0, "It alters decoration drawing, not link behavior."),
    ("Which cue must remain on an underlined report link?", ["A visible focus indicator for keyboard use", "Only hover color", "A pseudo-element URL"], 0, "The underline does not replace a keyboard focus indicator."),
]
assert len(questions) == 12
quiz = copy.deepcopy(by_path["quizzes/css-advanced"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
            path=quiz_path, title=titles[quiz_path],
            summary="Twelve checks on scrolling, focus, fragment state, image crops, and decoration.",
            sort_order=3108, status="published", published_at=stamp,
            created_at=stamp, updated_at=stamp)
quiz["data"] = {
    "subject_root": "css/css-tutorial", "section_path": "css/quizzes",
    "content_format": "html", "author_path": "authors/aitrove-editorial",
    "seo_ready": True, "duration_minutes": 12,
    "related": [{"path": target, "title": titles[target]} for target in [
        "css/overflow-anchor-exclusions", "css/display-contents-wrapper",
        "css/focus-within-group", "css/object-position-focal-crop"]],
    "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                       answer=(answer - index % 3) % 3, explanation=explanation)
                  for index, (prompt, options, answer, explanation) in enumerate(questions)],
}
quiz["body"] = (
    "<p>Check the CSS behavior behind reading position, focus, cropping, and visible scrolling. Each question has one answer and an explanation.</p>"
    "<h2>Review the decisions</h2>" + links([item["path"] for item in quiz["data"]["related"]])
    + "<h2>Other checks</h2>" + links(["css/quizzes", "quizzes/css-type-color-assets"])
    + "<h3>Common Mistakes</h3><ul><li>Do not confuse a CSS position cue with focus management.</li>"
    "<li>Do not let a crop hide the only meaningful evidence.</li></ul>"
)
rows.append(quiz)
quiz_hub = by_path["css/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Scroll and state check</h2>" + links([quiz_path])
quiz_hub["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_quizzes": 1,
                  "total_records": len(rows)}))

"""Add eight CSS rendering contracts with reciprocal navigation and a quiz."""

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
quiz_path = "quizzes/css-rendering-contracts"
specs = []


def add(slug, title, summary, definition, decision, sample, cost, mistakes, related):
    path = "css/" + slug
    assert path not in by_path
    specs.append(dict(path=path, title=title, summary=summary, definition=definition,
                      decision=decision, sample=sample, cost=cost, mistakes=mistakes,
                      related=related))


add(
    "grid-auto-fit-vs-auto-fill",
    "CSS auto-fit vs auto-fill: decide what empty grid tracks should do",
    "Make a sparse card row stretch or reserve empty columns on purpose.",
    "Both auto-fit and auto-fill create as many repeated grid tracks as fit in the available inline size. Their difference appears when there are fewer items than tracks: auto-fit collapses empty repeated tracks, while auto-fill keeps them. Neither keyword loads records, decides the card order, or eliminates a minimum track width that cannot fit a narrow container.",
    "A review dashboard may show one urgent case or many. Its cards should expand across the row when the result set is sparse, so auto-fit is suitable. A separate calendar-like shelf may need fixed empty slots to keep columns aligned with another row; auto-fill expresses that different requirement. Test one, two, and seven records at a wide viewport, then resize until a single card must occupy a whole row. The minimum in the sample uses min(100%, 19rem) so a very narrow parent does not force the track wider than itself. Put records in meaningful DOM order and avoid dense auto-placement when keyboard focus follows them. The precise card width is a design input, not a device breakpoint. A container query can still be useful when inner card content changes shape, but it is unnecessary just to count columns. Empty tracks are layout space, not a sign that data is missing; the UI needs a separate empty-state message when there are no records.",
    '.review-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 19rem), 1fr)); gap: 1rem; }\n.review-grid > article { min-inline-size: 0; }\n.review-grid--reserved { grid-template-columns: repeat(auto-fill, minmax(min(100%, 19rem), 1fr)); }',
    "Grid lays out the items already in the DOM; this rule does not reduce their render or network cost. A large record set still needs paging or another data strategy. The maintenance risk is choosing auto-fill because its name sounds more expansive, then wondering why a single card stays narrow beside unused tracks. Inspect sparse and full states in the same parent width. Content with a long unbreakable identifier may overflow inside a correctly sized track, so give the child a local wrapping or scrolling policy. The sample lets grid items shrink, but it does not authorize clipping buttons or hiding case identifiers.",
    ["Do not treat auto-fit and auto-fill as interchangeable when the row is sparse.", "Do not assume repeat() chooses a meaningful source order.", "Do not use a fixed minimum wider than the narrowest parent."],
    ["css/grid-tracks", "css/grid-auto-placement", "css/intrinsic-sizing", "css/container-queries"],
)

add(
    "overflow-clip-vs-hidden",
    "CSS overflow: clip vs hidden: avoid an accidental scroll container",
    "Clip purely decorative overflow without hiding focusable content.",
    "overflow: hidden clips painted content but creates a scroll container when content overflows; script or keyboard focus can move that hidden scroll position. overflow: clip clips without creating a scroll container and cannot be scrolled programmatically. Both can conceal content, so neither repairs a box that is too small for essential text or controls.",
    "A status tile draws a decorative light streak that may extend beyond its rounded edge. The streak contains no text, links, or controls. Clipping that decoration with overflow: clip prevents it from becoming an unwanted scroll ancestor for nearby sticky or scroll-driven behavior. A transcript pane is a different case: its content must be reachable, so use overflow: auto and a bounded size rather than clip. Test keyboard traversal through every descendant, high zoom, long translations, and a focus outline near the edge. If a focusable link lies outside a clipped box, it can receive focus while remaining invisible. That is a layout defect to fix in the markup or sizing, not a reason to switch blindly to hidden. Mixing clip on one axis with a scrolling value on the other can compute differently than expected; inspect the two-axis rule in the browser. Do not put clip on the document root to conceal horizontal overflow from an oversized child.",
    '.status-tile { overflow: clip; border-radius: .55rem; }\n.status-tile__content { position: relative; z-index: 1; }\n.transcript-pane { max-block-size: 21rem; overflow: auto; }',
    "The property itself is cheap. The meaningful cost is the risk of inaccessible content or altered scroll ancestry. An accidental hidden scroll container can affect sticky positioning and which ancestor a scroll timeline observes; clip avoids that only when the overflow is genuinely decorative. The transcript pane uses auto to preserve access and may need a visible label and keyboard testing. Check whether focus rings are cut off by the status tile and add space or move the outline if they are. Do not infer correctness from the absence of a scrollbar. A no-CSS view and a 200% zoom view often reveal content that the fixed box was concealing.",
    ["Do not clip interactive descendants that can receive keyboard focus.", "Do not assume hidden and clip create the same scroll behavior.", "Do not hide page overflow to cover a sizing bug."],
    ["css/overflow-and-scroll", "css/scroll-driven-view-timelines", "css/positioning-and-sticky", "css/focus-visible"],
)

add(
    "open-state-selector",
    "CSS :open: style the native open state without inventing one",
    "Enhance details and picker controls while preserving their built-in behavior.",
    "The :open pseudo-class matches supported elements with a native open state, including expanded details and dialog elements and certain picker controls while their picker is shown. It is not a generic class for any visible panel. A showing popover has its own :popover-open state, and older browsers may not match :open at all.",
    "An audit help panel is a details element. Its summary has a permanent border and focus style; opening the disclosure adds a background cue and a border beneath the summary. The native summary remains the control, so keyboard activation and expanded state come from HTML. The sample includes details[open] as a fallback for engines that do not recognize :open. Test Enter and Space on the summary, a long help paragraph, nested links, and a second disclosure in the same group. A select picker can also match :open, but browser chrome around a native picker is not fully controlled by this selector; do not promise to style the option popup itself. If the panel is a dialog, closing and focus restoration require correct dialog behavior, not merely a color rule. Avoid styling every :open element globally, since a dialog, details, select, and input picker need different treatments. The state cue is secondary to visible content and the native expanded relationship.",
    '.audit-help > summary { border-block-end: 1px solid #78909c; padding: .6rem; }\n.audit-help[open] > summary { background: #e9f2f6; }\n.audit-help:open > summary { border-block-end-color: #1c5e87; }\n.audit-help > summary:focus-visible { outline: 3px solid #1c5e87; outline-offset: 2px; }',
    "The matching cost is negligible. The compatibility cost matters because :open became broadly available later than the open attribute on details. A usable base rule and the details[open] fallback carry the interaction if the pseudo-class is ignored. Test the actual target browsers before applying :open to picker controls. A CSS state cannot persist a disclosure choice across navigation or decide whether opening one closes another; those are document or application contracts. Never remove the summary marker without providing an equally clear disclosure affordance, and do not hide the focus outline to keep the panel visually quiet.",
    ["Do not use :open as a synonym for :popover-open.", "Do not expect :open to create the open state.", "Do not replace the native summary with a noninteractive painted heading."],
    ["css/popover-open-state", "css/focus-visible", "css/form-control-states", "html/dialog-and-details"],
)

add(
    "user-valid-positive-feedback",
    "CSS :user-valid: confirm a checked field without premature praise",
    "Wait for user interaction before adding positive form feedback.",
    "The :user-valid pseudo-class matches a form control that passes native constraints after the user has interacted with it or attempted submission. That differs from :valid, which may match an untouched optional field immediately. A green border is only presentation; it does not mean the server accepted the value or that a workflow has finished.",
    "A reference lookup form requires a case identifier with a constrained pattern. The field starts neutral. Once the browser exposes user-valid, the border shifts to a positive tone; after user-invalid, a separate error style applies. Keep the visible format hint and a real error message after submission, because a border cannot say why a value failed. Test typing part of the identifier, blur, correction, paste, autofill, and resubmission after a server rejection. Browser timing for interaction states can vary, so do not make the positive border the only proof that a field was accepted. The server may reject a syntactically valid identifier because the case does not exist or the viewer lacks access. Keep that result in application text, not in a native validity pseudo-class. A read-only or disabled control follows different validation rules; scope the selector to editable controls in the form. Color must not be the sole state cue, especially in forced colors.",
    '.case-lookup input { border: 2px solid #5e7480; }\n.case-lookup input:user-valid { border-color: #1f6b4b; }\n.case-lookup input:user-invalid { border-color: #a33b42; }\n.case-lookup input:focus-visible { outline: 3px solid #1c5e87; outline-offset: 2px; }',
    "Selector matching is cheap. The hard part is coordinating native constraints, application messages, and server responses so they do not contradict one another. A browser may expose the state after a committed change or attempted submission, and the visual cue can update while a user edits again. Test that sequence rather than assuming a single fixed blur event. Native constraints validate syntax and required values, not business authorization. Do not paint a valid field as an approved case; the form must report the server's actual result. Keep focus styling distinct from success styling so keyboard users can still locate the active field.",
    ["Do not treat :user-valid as server approval.", "Do not use :valid when untouched optional fields should remain neutral.", "Do not rely on green color alone to communicate a result."],
    ["css/user-invalid-feedback", "css/required-optional-control-state", "css/form-control-states", "html/form-validation"],
)

add(
    "reduced-transparency-fallback",
    "CSS prefers-reduced-transparency: keep overlays readable by default",
    "Offer a solid surface when the user asks for fewer translucent effects.",
    "The prefers-reduced-transparency media feature can reflect a device preference to reduce translucent surfaces. Support is not universal, so the default component must already be readable. The query can improve a decorative overlay; it cannot replace contrast testing, and it does not imply that the user also requested reduced motion.",
    "A document comparison panel floats above a scanned page. Its normal surface is a mostly opaque light color, with a mild backdrop blur added only as decoration when supported. When a reduced-transparency preference is reported, the panel becomes fully opaque and drops the blur. The text and buttons remain legible in the base state even if the media feature is unknown, the scan is unusually dark, or the browser turns the effect off. Test against several background pages, at high zoom, with system contrast settings, and in forced colors. Avoid a transparent panel whose readability depends on a single preference query; unsupported browsers would keep the weak default. Also avoid applying opacity to the whole panel, since that fades the text and controls along with the background. A solid background-color on the panel gives the browser a direct surface to paint. The feature is a progressive enhancement for user preference, not a reliable device classification.",
    '.comparison-panel { color: #173441; background: #f5f8f9; border: 1px solid #7b929d; }\n@supports (backdrop-filter: blur(1px)) { .comparison-panel { background: rgb(245 248 249 / 94%); backdrop-filter: blur(6px); } }\n@media (prefers-reduced-transparency: reduce) { .comparison-panel { background: #f5f8f9; backdrop-filter: none; } }',
    "Backdrop blur can add compositing work over a large moving surface; measure it on representative devices if the panel covers much of the viewport. A solid panel avoids that work. The media query has limited availability, so the base color and border must do the accessibility work. Check the final foreground-to-background contrast over the most demanding page image rather than averaging the scan. Forced-colors mode may substitute system colors; leave the underlying text and controls functional when authored backgrounds disappear. Keep any separate reduced-motion handling independent, since transparency and motion preferences express different needs.",
    ["Do not make a low-contrast default depend on this limited-support query.", "Do not lower opacity on a whole panel containing text.", "Do not assume reduced transparency also means reduced motion."],
    ["css/backdrop-filter-legibility", "css/prefers-contrast-boundaries", "css/dark-mode-and-forced-colors", "css/reduced-motion"],
)

add(
    "animation-composition-add",
    "CSS animation-composition: preserve a base transform during an effect",
    "Add a small motion cue without replacing the element's positioned state.",
    "animation-composition decides how an animation effect combines with the underlying property value. The default replace can override a base transform while keyframes run. add composes the effect with that underlying value. If multiple animations target one property, their composition list follows animation order, so an unreviewed extra animation can change the result.",
    "A review marker is translated into place by a layout rule. A brief attention cue should move it slightly upward and back without dropping its base translation. The sample supplies a base transform and uses animation-composition: add for the temporary nudge. Keep the animation finite, trigger it only when a new item arrives, and leave a textual status in the interface; motion alone cannot explain the item. Test the initial frame, the peak, and the end, plus the case where the base transform changes at a responsive breakpoint. If a target browser ignores add, the animation may temporarily replace the base transform, so the effect is optional and must not carry essential spatial meaning. A reduced-motion preference removes the animation while preserving the marker's position and text. If several transforms are deeply coupled, a wrapper with one transform per element may be easier to reason about than multiple simultaneous effects on one property. Do not animate dozens of markers indefinitely.",
    '@keyframes review-nudge { 50% { transform: translateY(-.35rem); } }\n.review-marker { transform: translateX(.65rem); }\n@supports (animation-composition: add) { .review-marker { animation: review-nudge 520ms ease-out 1; animation-composition: add; } }\n@media (prefers-reduced-motion: reduce) { .review-marker { animation: none; } }',
    "A short transform animation on one small marker is usually inexpensive, but frequent or simultaneous effects still cost frame work. Profile the real screen if arrival events are common. The fallback matters more than the micro-optimization: if add is unsupported, the base translation may be replaced during the cue. Keep the marker usable in that moment and test target browsers. Composition is not a way to fix a wrong layout position; establish the resting transform first. When changing animation-name or adding another keyframe set, review the parallel composition values and the final computed transform. Motion must remain optional under the user's reduced-motion setting.",
    ["Do not assume the default replace preserves a base transform.", "Do not let an unsupported composition alter essential position.", "Do not make motion the only notice that a new item arrived."],
    ["css/keyframe-animation", "css/transitions-and-transforms", "css/reduced-motion", "css/transform-origin-pivots"],
)

add(
    "print-color-adjust-boundary",
    "CSS print-color-adjust: request fidelity without trusting printer color",
    "Preserve a small print cue while keeping a text fallback.",
    "print-color-adjust: exact asks the browser to preserve authored colors and images for an element when it prepares output. It is a request, not a guarantee: browser behavior and user print settings take priority. The default economy allows adjustments that save ink or improve legibility. Printed meaning must survive without an exact color match.",
    "A laboratory chain-of-custody sheet uses pale alternating rows to help readers follow a long item table. The print stylesheet asks for exact color on that table only, while each row still has clear borders and a textual item identifier. This limits the ink request to a region where row alignment benefits from the tint. Test a color print preview, a grayscale preview, background graphics switched off, and an exported PDF from the actual target browser. Do not set exact on the entire report to preserve a decorative dark page theme; it may waste ink and reduce contrast. A red hold label must also say HOLD in text, since an office printer or user preference can remove the red. Keep evidence links and signatures visible in ordinary black text. If the organization needs legally reliable archival color, a controlled PDF generation pipeline and output review are separate requirements. CSS cannot certify that a physical printer reproduced a shade faithfully.",
    '@media print { .custody-table { print-color-adjust: exact; } .custody-table :is(th, td) { border-block-end: 1px solid #66747a; } .custody-table tr:nth-child(even) { background: #eef2f3; } .custody-table .hold-label { color: #111; font-weight: 700; } }',
    "The property adds negligible page runtime cost. If backgrounds actually print, ink and toner use can rise; scope exact to the smallest useful region. Browser print settings may still suppress backgrounds, so the borders and labels must carry row boundaries and status. Check PDF and paper outputs when the document is operationally important, not only the screen stylesheet. The rule does not change pagination, page margins, or whether fonts are embedded in a PDF. A narrow table can still break badly across pages; pair print color choices with the report's existing fragmentation and table rules. Treat exact as a preference to the renderer, not a binding output contract.",
    ["Do not depend on an exact printed hue to carry status.", "Do not put print-color-adjust: exact on the whole site by default.", "Do not assume browser preview proves a physical printer's output."],
    ["css/print-styles", "css/print-widows-orphans", "css/page-rule-print-contract", "html/print-stylesheet-media"],
)

add(
    "text-wrap-pretty-editorial",
    "CSS text-wrap: pretty: spend line-breaking work where copy merits it",
    "Improve a short editorial paragraph without making all body text costly to lay out.",
    "text-wrap: pretty asks the browser to spend more work on soft line breaks to avoid awkward endings in longer text. balance aims for more even short lines and is often used for headings; stable favors lines that do not shift above an edit point in editable text. None of these values inserts editorial line breaks or rewrites the copy.",
    "A case-study introduction has a narrow measure and a final line that repeatedly contains one stranded word. The introduction is short and static, so the page applies pretty there while leaving a long activity feed on ordinary wrap. Its title uses an existing balance rule, and an editable note field is not given pretty because reflow during typing would be distracting. Test the introduction with several localized lengths, the fallback font, and the widths around the page's responsive changes. Browser algorithms can differ; the result is an optional typography improvement rather than a guaranteed exact line arrangement. If a legally significant phrase must stay together, edit the content or markup deliberately instead of assuming pretty will preserve it. Avoid hard-coded break elements purely to match a desktop screenshot; they can create poor lines on a phone. The sample keeps an ordinary wrap declaration first so engines that do not recognize pretty still render readable text.",
    '.case-study__intro { max-inline-size: 62ch; text-wrap: wrap; text-wrap: pretty; }\n.case-study__activity { text-wrap: wrap; }\n.case-study__editable-note { text-wrap: stable; }',
    "Better line breaking can require more layout work than default wrapping. Scope pretty to a small static region where the improvement is visible, and measure if repeated across a long feed or many cards. The browser remains free to choose its algorithm, so snapshots may differ across engines and fonts. The 62ch measure is a starting point for this article, not a universal reading width; test translations and user font enlargement. Text-wrap controls soft breaks, not overflow from an unbreakable code token. Such tokens still need an appropriate wrapping or scrolling policy. In editable text, stable may reduce distracting reflow, but it also needs browser checks and must not hide content.",
    ["Do not apply pretty to every paragraph solely for visual polish.", "Do not expect identical line breaks across browsers and fonts.", "Do not use pretty as a fix for long unbreakable identifiers."],
    ["css/balanced-heading-wrap", "css/line-height-and-measure", "css/text-wrapping-and-truncation", "html/contenteditable-vs-textarea"],
)


assert len(specs) == 8
titles = {path: row["title"] for path, row in by_path.items()}
titles.update({item["path"]: item["title"] for item in specs})
titles[quiz_path] = "CSS rendering contracts quiz"


def links(paths):
    assert all(path in titles for path in paths), paths
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in paths
    ) + "</ul>"


hub = by_path[hub_path]
hub["data"]["modules"].append({
    "title": "Rendering contracts and output choices",
    "summary": "Distinguish grid tracks, clipping, native states, preference queries, motion, print color, and line breaking.",
    "lessons": [item["path"] for item in specs],
})
hub["body"] += "<h2>Rendering contracts and output choices</h2>" + links([item["path"] for item in specs])
hub["updated_at"] = stamp

for index, item in enumerate(specs):
    row = copy.deepcopy(by_path["css/selectors-and-cascade"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + item["path"])),
               path=item["path"], title=item["title"], summary=item["summary"],
               subject="css-reference", sort_order=24300 + index,
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
    "css/grid-auto-placement": ["css/grid-auto-fit-vs-auto-fill"],
    "css/overflow-and-scroll": ["css/overflow-clip-vs-hidden"],
    "css/popover-open-state": ["css/open-state-selector"],
    "css/user-invalid-feedback": ["css/user-valid-positive-feedback"],
    "css/backdrop-filter-legibility": ["css/reduced-transparency-fallback"],
    "css/keyframe-animation": ["css/animation-composition-add"],
    "css/print-styles": ["css/print-color-adjust-boundary"],
    "css/balanced-heading-wrap": ["css/text-wrap-pretty-editorial"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Further rendering decisions</h2>" + links(targets)
    row["data"].setdefault("related", []).extend(
        {"path": target, "title": titles[target]} for target in targets
    )
    row["updated_at"] = stamp

questions = [
    ("Which repeated grid keyword collapses unused tracks?", ["auto-fit", "auto-fill", "min-content"], 0, "auto-fit collapses empty repeated tracks after fitting."),
    ("Which keyword retains empty repeated grid tracks?", ["auto-fill", "auto-fit", "max-content"], 0, "auto-fill keeps the empty track space."),
    ("What distinguishes overflow: clip from hidden?", ["clip does not create a scroll container", "clip adds scrollbars", "hidden always shows clipped content"], 0, "Hidden can still scroll to overflow; clip cannot."),
    ("What is unsafe inside a clipped box?", ["Focusable content outside the visible edge", "A decorative streak", "A solid background"], 0, "Hidden keyboard focus can become unreachable visually."),
    ("Which native control can :open match when expanded?", ["A details element", "Every visible div", "Every popover by definition"], 0, "The selector follows supported native open states."),
    ("When can :user-valid match?", ["After relevant user interaction and native validity", "Only after a server approves", "Before any form constraint exists"], 0, "It follows user-facing native validation state."),
    ("How should a transparency preference be handled in an unsupported browser?", ["The default surface should remain readable", "Hide the panel", "Lower all text opacity"], 0, "The media feature has limited availability."),
    ("What is the default animation composition?", ["replace", "add", "accumulate"], 0, "Replace can override an underlying animated property value."),
    ("What does animation-composition: add do?", ["Combines an effect with its underlying property value", "Starts a request", "Forces hardware acceleration"], 0, "Add composes the effect rather than replacing the base value."),
    ("Can print-color-adjust: exact force a printer to reproduce a status color?", ["No, user and browser output choices can override it", "Yes, always", "Only if the DOM has no table"], 0, "The value requests fidelity but cannot guarantee output."),
    ("Where is text-wrap: pretty most defensible?", ["A small static paragraph where line quality matters", "Every live activity row", "An unbreakable case code"], 0, "The line-breaking work should be scoped to a visible editorial benefit."),
    ("What remains necessary if a soft-wrap hint is ignored?", ["Readable content and a sane fallback layout", "A hidden overflow mask", "A fixed screenshot width"], 0, "Presentation hints must not carry the only readable form of the text."),
]
assert len(questions) == 12
quiz = copy.deepcopy(by_path["quizzes/css-advanced"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
            path=quiz_path, title=titles[quiz_path],
            summary="Twelve checks on CSS track, scroll, state, preference, animation, print, and text contracts.",
            sort_order=3130, status="published", published_at=stamp,
            created_at=stamp, updated_at=stamp)
quiz["data"] = {
    "subject_root": "css/css-tutorial", "section_path": "css/quizzes",
    "content_format": "html", "author_path": "authors/aitrove-editorial",
    "seo_ready": True, "duration_minutes": 12,
    "related": [{"path": target, "title": titles[target]} for target in [
        "css/grid-auto-fit-vs-auto-fill", "css/overflow-clip-vs-hidden",
        "css/open-state-selector", "css/print-color-adjust-boundary"]],
    "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                       answer=(answer - index % 3) % 3, explanation=explanation)
                  for index, (prompt, options, answer, explanation) in enumerate(questions)],
}
quiz["body"] = (
    "<p>Check the difference between rendering hints, native state, output preferences, and behavior that the application must supply.</p>"
    "<h2>Review the decisions</h2>" + links([item["path"] for item in quiz["data"]["related"]])
    + "<h2>Other checks</h2>" + links(["css/quizzes", "quizzes/css-direction-media"])
    + "<h3>Common Mistakes</h3><ul><li>Do not treat a browser presentation hint as a guarantee.</li>"
    "<li>Do not clip, color, or animate away essential information.</li></ul>"
)
rows.append(quiz)
quiz_hub = by_path["css/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Rendering contracts check</h2>" + links([quiz_path])
quiz_hub["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_quizzes": 1,
                  "total_records": len(rows)}))

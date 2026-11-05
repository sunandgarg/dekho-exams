"""Extend the CSS reference with modern layout and motion decisions."""

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
quiz_path = "quizzes/css-modern-behavior"
specs = []


def add(slug, title, summary, definition, decision, sample, cost, mistakes, related):
    path = "css/" + slug
    assert path not in by_path
    specs.append(dict(path=path, title=title, summary=summary, definition=definition,
                      decision=decision, sample=sample, cost=cost, mistakes=mistakes,
                      related=related))


add("container-query-units", "CSS container query units: size type to its component",
    "Use cqi and related units against a query container, with a readable fixed-size fallback.",
    "Container query length units measure a percentage of an eligible query container rather than the viewport. The logical inline unit cqi follows writing direction; cqb follows block size. An absent eligible container makes the unit fall back to the small viewport for that axis.",
    "A case summary card is used in both a narrow queue and a wide dashboard. The title can grow with the card's inline size while staying inside a reviewed range. Give the outer wrapper container-type inline-size, and apply cqi only to descendants; a container cannot use its own size to determine its own font. The first declaration supplies a stable size when the later one is unsupported. The clamp bounds still matter when the card becomes unusually wide. Test the component in both placements, at 200 percent zoom, with a long translated title, and in a vertical writing mode if that mode is supported. Avoid cqb here: an inline-size query container does not necessarily expose a useful block size for this calculation. Container units are a sizing input, not a breakpoint or a guarantee that text will fit.",
    ".case-summary { container-type: inline-size; }\n.case-summary__title { font-size: 1.25rem; font-size: clamp(1.25rem, 3cqi, 1.8rem); overflow-wrap: anywhere; }",
    "The unit adds no network cost. The main cost is maintaining predictable results across embedded contexts: missing containment, nested query containers, zoom, and localization can change the computed value. Check the actual nearest eligible container in developer tools rather than assuming the viewport or a visually obvious parent is the reference. A bounded font size can still overflow if an unbroken identifier sits beside it, so permit wrapping where the content allows it. Container-type can change sizing behavior of the wrapper; validate the card's intrinsic width after adding containment. When support is absent, the fixed rem value remains readable rather than leaving the heading unstyled.",
    ["Do not apply cqi to a component before defining the intended query container.", "Do not assume cqb measures a useful height on an inline-size-only container.", "Do not omit a stable size and long-text test."],
    ["css/container-queries", "css/units-and-functions", "css/writing-mode-layout"])

add("container-style-queries", "CSS container style queries: branch on a local token",
    "Change a child component from an ancestor's custom property without tying it to viewport width.",
    "A container style query tests a computed style on an eligible ancestor. The currently practical target is a custom property, queried with style() inside @container. A style query styles descendants; it does not restyle the queried element itself.",
    "A review queue marks compact rows with a local density token. A badge inside each row can reduce its padding when the ancestor's token is compact, even if the queue and dashboard share the same viewport. The base badge spacing appears first and remains usable in browsers that do not evaluate the query. Use an exact token value, and put the token on the row wrapper rather than the badge. Inspect computed custom properties if the result seems surprising: an inherited token from a higher ancestor can become the nearest matching style container. Keep density a presentation choice; do not hide case IDs, status, or actions in compact mode. Test both token values, an unset token, a nested panel with a different token, and forced colors. A size query is the better tool when the decision really depends on available width.",
    ".review-row { --row-density: comfortable; }\n.review-row[data-density=\"compact\"] { --row-density: compact; }\n.review-row__badge { padding: .35rem .7rem; }\n@container style(--row-density: compact) { .review-row__badge { padding: .2rem .45rem; } }",
    "The query avoids application code that copies a styling state into every child, but it adds a dependency on the ancestor's computed token. Repeated components should be tested with nested and inherited values, because a token set at the document root may affect far more descendants than intended. Unlike registered custom properties with a declared syntax, unregistered values should be treated as exact token matches; do not assume a different spelling or equivalent color notation will compare equal. The rule does not alter layout until its declarations do, so performance depends on the properties changed and the number of affected elements. A simple padding adjustment is cheap; hiding or reordering critical content is not a sound density policy.",
    ["Do not expect a style query to style its own container.", "Do not assume arbitrary standard properties are reliably queryable through style().", "Do not place a broad inherited token at the root without checking nested components."],
    ["css/container-queries", "css/custom-properties", "css/scoped-rules"])

add("starting-style-entry-transitions", "CSS @starting-style: define an element's entry state",
    "Animate an appearing panel from a declared starting state while keeping instant appearance as the fallback.",
    "Transitions normally need a previous rendered style. An element that first appears, or returns from display none, may not have one. @starting-style provides the before-change values used for that entry transition; it does not define a general exit animation.",
    "A case notice is inserted after a save. It should appear immediately in older browsers, while supporting browsers may fade it in. The normal rule defines the final state and transition; the starting rule comes later at the same specificity. Keep the notice's message present as ordinary text and send the appropriate announcement through the application's accessibility behavior. Removing the notice still needs its own lifecycle decision: @starting-style alone will not delay removal or create an exit state. Test first insertion, repeated insertion, reduced motion, and a page restored from browser history. If the notice is already in the DOM but hidden with display none, inspect its display transition separately. Motion cannot replace a visible success state, and a save failure must never be painted as success just because the same component class was reused.",
    ".save-notice { opacity: 1; transition: opacity 180ms ease-out; }\n@starting-style { .save-notice { opacity: 0; } }\n@media (prefers-reduced-motion: reduce) { .save-notice { transition: none; } }",
    "Opacity animation is generally cheaper than repeatedly changing geometry, but a large translucent surface may still cause extra paint or compositing work. Check the actual notice on a low-power device if many notices can appear together. When @starting-style is unsupported, the final opacity remains one, so the message appears without a fade. The order and specificity of the starting rule matter; a later ordinary declaration can defeat it. Keep a stable layout slot or accept the document reflow when the notice is inserted. Reduced-motion handling should remove the transition without hiding or delaying the message. Do not infer that a fade establishes a screen reader announcement or a valid server response.",
    ["Do not use @starting-style as the exit state.", "Do not omit the normal visible rule that serves as fallback.", "Do not rely on motion to announce a completed action."],
    ["css/transitions-and-transforms", "css/reduced-motion", "css/css-errors-and-fallbacks"])

add("discrete-display-transitions", "CSS discrete transitions: keep a closing panel visible long enough to fade",
    "Combine opacity with a discrete display transition, then verify both open and close behavior.",
    "Display does not interpolate through intermediate values. With allow-discrete, its switch can be coordinated with interpolating properties so an element stays visible during an exit transition. Entry from display none also needs a starting state for the opacity change.",
    "A case details region opens and closes from a control that updates the hidden state. The closed rule sets display none and opacity zero; the open rule sets block and opacity one. The transition names display explicitly with allow-discrete, while @starting-style supplies the opening opacity. In a browser without the discrete transition, the panel should still open and close instantly. Test rapid repeated toggles, a keyboard-triggered close, reduced motion, and focus inside the panel at the moment it closes. Application state must move focus to a valid control before a hidden focused child becomes unavailable. CSS cannot decide when a data fetch is complete or whether dismissing the panel loses edits. If the panel uses the top layer, overlay timing may also need its own transition declaration.",
    ".case-detail-panel { display: none; opacity: 0; transition: opacity 200ms ease, display 200ms allow-discrete; }\n.case-detail-panel.is-open { display: block; opacity: 1; }\n@starting-style { .case-detail-panel.is-open { opacity: 0; } }\n@media (prefers-reduced-motion: reduce) { .case-detail-panel { transition: none; } }",
    "The transition can improve visual continuity but does not reduce the work required to lay out the panel. Changing display still affects layout at its switch point, so neighboring content may move; reserve space or use an overlay if that motion is unacceptable. Opacity can briefly create a visible but partly transparent region; verify contrast and focus timing during the transition. A browser that ignores allow-discrete skips the exit fade, which is an acceptable functional fallback. Avoid transition all on a large panel because later property additions can accidentally animate geometry or colors. Profile repeated panels if motion stutters, and do not sacrifice keyboard behavior for a fade.",
    ["Do not expect display to interpolate numerically.", "Do not forget @starting-style when entry begins at display none.", "Do not leave focus inside a panel after it becomes hidden."],
    ["css/starting-style-entry-transitions", "css/transitions-and-transforms", "css/reduced-motion"])

add("interpolate-intrinsic-size", "CSS interpolate-size: animate toward content height carefully",
    "Opt a local disclosure into intrinsic-size interpolation without imposing a guessed pixel height.",
    "Intrinsic sizing keywords such as auto normally do not interpolate with numeric lengths. The inherited interpolate-size property can opt a subtree into transitions between a length and an intrinsic value. It does not enable a transition between two intrinsic keywords.",
    "A compact case synopsis expands when its controlling button changes an expanded state. The closed state has a fixed block size, while the open state takes the content's natural height. Set interpolate-size on the component wrapper so the opt-in does not unexpectedly affect unrelated disclosures across the page. The content must remain reachable when the closed clipping is intentional: use a real control with an accessible expanded state, and avoid clipping focused links. In older browsers the height may jump directly to auto, which keeps the content available. Test a single paragraph, a long localized paragraph, loading content that arrives mid-transition, zoom, and reduced motion. The rule is for presentation; it does not know whether data was authorized or loaded, and it cannot replace semantic disclosure markup or application state.",
    ".case-synopsis { interpolate-size: allow-keywords; }\n.case-synopsis__body { block-size: 4rem; overflow: clip; transition: block-size 220ms ease; }\n.case-synopsis[aria-expanded=\"true\"] .case-synopsis__body { block-size: auto; }\n@media (prefers-reduced-motion: reduce) { .case-synopsis__body { transition: none; } }",
    "Animating block size can cause layout work on each frame because later content moves as the panel grows. Measure on a page with a realistic number of cards; a one-card demo can hide the cost. The feature is an opt-in precisely because changing how intrinsic values animate can affect existing designs. Scope it narrowly and keep a snap-open fallback. Avoid a max-height approximation with an arbitrary huge value: the perceived timing changes with actual content height and overflow can be misleading. A natural-height target can change during image load, so size media explicitly or test that update. Motion reduction should keep the expanded state available immediately.",
    ["Do not expect two intrinsic keywords to interpolate.", "Do not set the opt-in on the document root without auditing every size transition.", "Do not clip a focused control inside the collapsed body."],
    ["css/intrinsic-sizing", "css/reduced-motion", "html/dialog-and-details"])

add("anchor-positioning-overlays", "CSS anchor positioning: place a hint beside its control",
    "Attach a lightweight hint to a trigger while keeping a usable ordinary layout fallback.",
    "Anchor positioning links a positioned element to a named anchor. The trigger declares anchor-name; an absolutely or fixed positioned hint declares position-anchor and uses anchor() or position-area to locate itself relative to the trigger.",
    "A case-status button opens a short explanatory hint. The base layout keeps the hint in normal flow below the control, so unsupported browsers still show the text. An @supports block activates absolute positioning and tethers it to the named trigger. The component has a positioning context and enough room in the design for the hint; real overlays near viewport edges need collision handling and may need a top-layer primitive. Test the first and last row, narrow screens, zoom, scrolling ancestors, and repeated rows. Anchor names can collide across repeated components, so do not assume the nearest visual button is always selected when names are reused. Scope names or give each instance a distinct name where the browser and component model allow it. The button must still control visibility and focus access; CSS anchoring only chooses coordinates.",
    ".status-help { position: relative; }\n.status-help__hint { margin-block-start: .5rem; }\n@supports (top: anchor(bottom)) { .status-help__trigger { anchor-name: --status-trigger; } .status-help__hint:not([hidden]) { position: absolute; position-anchor: --status-trigger; top: anchor(bottom); left: anchor(left); margin-block-start: .4rem; } }",
    "An anchored element can avoid manual coordinate calculations, but it still needs space, stacking, overflow, and collision review. An absolutely positioned hint does not reserve space in the surrounding flow, so a low row may overlap later content. Repeated anchors with the same name can bind unexpectedly; test several instances together rather than one isolated example. If support is missing, the in-flow hint remains readable. Do not make a critical error message depend on a hover-only overlay or on anchor support. Profile and simplify if dozens of live overlays are open; the user usually needs one contextual hint at a time.",
    ["Do not treat anchor positioning as a visibility or focus manager.", "Do not reuse an unscoped anchor name across repeated rows without testing binding.", "Do not assume an absolutely positioned hint reserves layout space."],
    ["css/positioning-and-sticky", "css/css-errors-and-fallbacks", "html/dialog-and-details"])

add("scroll-driven-view-timelines", "CSS view timelines: tie optional motion to visible progress",
    "Add a nonessential reading cue that follows a card entering the scrollport.",
    "A view timeline maps the position of a subject inside its nearest ancestor scrollport to animation progress. animation-timeline: view() attaches that progress to the animated element, while animation-range can limit the portion of the view interval used.",
    "An archive card receives a subtle decorative rule as it enters the reading area. Its ordinary border and text are already complete; the animation only adds a small opacity cue. Put the animation shorthand before animation-timeline, because the shorthand resets the timeline to auto. Guard the enhancement with @supports so unsupported browsers keep a static rule rather than accidentally running a time-based animation. The sample removes the animation under reduced motion. Test a short page with no scrolling, a long page, a nested scroller, keyboard navigation, and a large card that is taller than the viewport. The nearest scroller matters: a card inside an overflow panel does not necessarily follow page scrolling. Never tie the only display of case status or completion to scroll progress; readers can stop scrolling before the timeline reaches its end.",
    ".archive-card__rule { opacity: 1; }\n@supports (animation-timeline: view()) { .archive-card__rule { animation: rule-reveal 1ms linear both; animation-timeline: view(); animation-range: entry 0% entry 100%; } @keyframes rule-reveal { from { opacity: .35; } to { opacity: 1; } } }\n@media (prefers-reduced-motion: reduce) { .archive-card__rule { animation: none; opacity: 1; } }",
    "Opacity is a modest effect, yet scroll-linked animation still needs a real-device check when many cards participate. Keep the animated surface small and avoid layout-changing properties such as width or block size on each scroll frame. Browser support for scroll timelines is uneven, so the static fallback is the primary design. The 1ms duration is a placeholder for the animation declaration; the view timeline, not elapsed time, controls progress. Do not reverse the order of animation and animation-timeline, because a later shorthand silently restores the ordinary document timeline. Verify the chosen range on both small and tall cards; a mathematically valid range can yield an effect that is barely visible.",
    ["Do not place animation-timeline before a later animation shorthand.", "Do not make required content depend on scroll progress.", "Do not omit the static fallback and reduced-motion path."],
    ["css/keyframe-animation", "css/reduced-motion", "css/overflow-and-scroll"])


assert len(specs) == 7
titles = {path: row["title"] for path, row in by_path.items()}
titles.update({item["path"]: item["title"] for item in specs})
titles[quiz_path] = "CSS modern behavior decisions quiz"


def links(paths):
    assert all(path in titles for path in paths), paths
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in paths
    ) + "</ul>"


hub = by_path[hub_path]
hub["data"]["modules"].append({
    "title": "Modern layout and motion",
    "summary": "Container-relative sizing, local style queries, entry and discrete transitions, anchors, and view timelines.",
    "lessons": [item["path"] for item in specs],
})
hub["body"] += "<h2>Modern layout and motion</h2>" + links([item["path"] for item in specs])
hub["updated_at"] = stamp

for index, item in enumerate(specs):
    row = copy.deepcopy(by_path["css/selectors-and-cascade"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + item["path"])),
               path=item["path"], title=item["title"], summary=item["summary"],
               subject="css-reference", sort_order=24060 + index,
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
    "css/container-queries": ["css/container-query-units", "css/container-style-queries"],
    "css/transitions-and-transforms": ["css/starting-style-entry-transitions", "css/discrete-display-transitions"],
    "css/intrinsic-sizing": ["css/interpolate-intrinsic-size"],
    "css/positioning-and-sticky": ["css/anchor-positioning-overlays"],
    "css/keyframe-animation": ["css/scroll-driven-view-timelines"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Related behavior decisions</h2>" + links(targets)
    row["data"].setdefault("related", []).extend(
        {"path": target, "title": titles[target]} for target in targets
    )
    row["updated_at"] = stamp

questions = [
    ("What does 1cqi measure?", ["One percent of an eligible query container's inline size", "One percent of viewport width", "One pixel after zoom"], 0, "cqi tracks the eligible query container's inline dimension."),
    ("What should precede a cqi font size?", ["A readable fallback declaration", "A hidden heading", "A fixed viewport height"], 0, "The fallback keeps the heading readable when container units are unavailable."),
    ("Which value is a practical style-query target?", ["A computed custom property", "Every standard CSS property in every browser", "The element's server response"], 0, "Current style-query use should target computed custom properties."),
    ("Where does a container style query apply its declarations?", ["To matching descendants", "Only to the queried container itself", "Only to the document root"], 0, "The query inspects an ancestor and styles descendants within its rule."),
    ("What problem does @starting-style address?", ["An entry without a previous rendered style", "Printer page margins", "The exit state of every transition"], 0, "It supplies before-change values for an entry transition."),
    ("Why include display with allow-discrete in a closing transition?", ["To coordinate its visibility switch with a fade", "To interpolate display as a number", "To remove focus automatically"], 0, "Display switches discretely while opacity can interpolate."),
    ("What can interpolate-size allow?", ["A length to an intrinsic size keyword", "Any two intrinsic keywords", "A URL to a length"], 0, "The opt-in allows a numeric length and an intrinsic endpoint."),
    ("What is a likely cost of animating block size?", ["Repeated layout work as later content moves", "A mandatory network request", "No possible rendering cost"], 0, "Changing block size can move following content each frame."),
    ("What must an anchor-positioned hint also have?", ["Absolute or fixed positioning", "Only a background color", "A media query at every width"], 0, "The positioned element must participate in an anchor positioning scheme."),
    ("What can repeated unscoped anchor names cause?", ["Binding to an unintended anchor", "Automatic unique names", "Removal of all overlays"], 0, "Repeated names can resolve to a different anchor than the nearby trigger."),
    ("Where should animation-timeline be written relative to animation shorthand?", ["After it", "Before it", "Inside @keyframes only"], 0, "The shorthand resets a previously declared timeline to auto."),
    ("What should a scroll-driven cue preserve without feature support?", ["The complete static content and state", "A permanently transparent label", "Only an animated progress value"], 0, "Motion is optional; the underlying information must remain available."),
]
assert len(questions) == 12
quiz = copy.deepcopy(by_path["quizzes/css-advanced"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
            path=quiz_path, title=titles[quiz_path],
            summary="Twelve decisions about container sizing, transitions, anchors, and view timelines.",
            sort_order=3106, status="published", published_at=stamp,
            created_at=stamp, updated_at=stamp)
quiz["data"] = {
    "subject_root": "css/css-tutorial", "section_path": "css/quizzes",
    "content_format": "html", "author_path": "authors/aitrove-editorial",
    "seo_ready": True, "duration_minutes": 12,
    "related": [{"path": target, "title": titles[target]} for target in [
        "css/container-query-units", "css/starting-style-entry-transitions",
        "css/anchor-positioning-overlays", "css/scroll-driven-view-timelines"]],
    "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                       answer=(answer - index % 3) % 3, explanation=explanation)
                  for index, (prompt, options, answer, explanation) in enumerate(questions)],
}
quiz["body"] = (
    "<p>Check the fallback, scope, and interaction consequences of newer CSS behavior. Each question has one answer and an explanation.</p>"
    "<h2>Review the decisions</h2>" + links([item["path"] for item in quiz["data"]["related"]])
    + "<h2>Other checks</h2>" + links(["css/quizzes", "quizzes/css-rendering-decisions"])
    + "<h3>Common Mistakes</h3><ul><li>Do not treat optional animation as required information.</li>"
    "<li>Do not assume unsupported features make the fallback disappear.</li></ul>"
)
rows.append(quiz)
quiz_hub = by_path["css/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Modern behavior check</h2>" + links([quiz_path])
quiz_hub["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_quizzes": 1,
                  "total_records": len(rows)}))

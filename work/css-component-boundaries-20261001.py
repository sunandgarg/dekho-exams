"""Add focused CSS component and transition decisions to the local fixture."""

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
quiz_path = "quizzes/css-component-boundaries"
specs = []


def add(slug, title, summary, definition, decision, sample, cost, mistakes, related):
    path = "css/" + slug
    assert path not in by_path
    specs.append(dict(path=path, title=title, summary=summary, definition=definition,
                      decision=decision, sample=sample, cost=cost,
                      mistakes=mistakes, related=related))


add(
    "shadow-host-variants",
    "CSS :host: make a component variant an explicit host contract",
    "Style a shadow host from its own stylesheet and keep a stable outside token.",
    "The :host selector matches the shadow root's host from a stylesheet inside that shadow tree. :host() adds a condition on the host, such as an attribute. Neither selector gives the shadow stylesheet control of arbitrary ancestors or makes every internal element available to the page stylesheet.",
    "A shipment-status element has a regular and a compact density. Its owner sets a density attribute on the host; the component stylesheet adjusts padding and spacing only for that declared variant. The page can supply an accent through a documented custom property, but the component retains a fallback value. Keep the attribute vocabulary small and test missing or unexpected values as the regular state. A host with display: inline may not accept the width behavior expected of a card, so define its outer display deliberately. Do not query the page's DOM from inside this stylesheet to infer density from a surrounding layout. If the host contains an interactive control, resizing it must preserve a usable target and visible focus ring. Document which settings are public and which internal class names may change.",
    ':host { display: block; color: #173441; border: 1px solid var(--shipment-accent, #315f75); padding: 1rem; }\n:host([density="compact"]) { padding: .65rem; }\n.status-row { display: flex; flex-wrap: wrap; gap: .75rem; }\n:host([density="compact"]) .status-row { gap: .4rem; }',
    "Selector matching is small compared with rendering the component's actual contents. The maintenance cost is treating private shadow classes as an external API; callers cannot reliably reach them, and changing them should not break themes. A custom property crosses the shadow boundary by inheritance, so its name and fallback become a contract. Inspect regular, compact, unknown-value, high-zoom, and forced-colors states. :host rules belong in shadow CSS; pasting them into a page stylesheet does not style the host. Check the resulting host box in the real layout rather than assuming the custom element's initial inline display is suitable.",
    ["Do not place :host rules in an ordinary document stylesheet.", "Do not expose an unbounded list of density values without defined behavior.", "Do not shrink a control until its target or focus cue becomes unusable."],
    ["css/custom-properties", "css/scoped-rules", "html/declarative-shadow-dom", "html/custom-elements"],
)

add(
    "shadow-part-theming",
    "CSS ::part(): expose a narrow styling surface across Shadow DOM",
    "Let consumers theme a named internal element without relying on private selectors.",
    "The ::part() pseudo-element selects a shadow-tree element whose part attribute exposes the named part on its host. The component author chooses that public name. It does not reveal the entire shadow tree, and a part inside another shadow root must be forwarded through exportparts before an outer consumer can target it.",
    "A document-review badge exposes its visible label as part=\"label\". A consuming application adjusts its weight and underline treatment to suit a dense review list. The badge still supplies a readable default when no outside rule exists. Treat the part name as a versioned styling contract: renaming it can break an integrator even when the visual markup still appears correct. Keep state semantics in the component's HTML and application logic; coloring a label does not make a rejected document accessible to a screen reader. Test the outside rule against default, hover, focus, disabled, and forced-color states. If the badge wraps a second custom element with its own shadow root, explicitly forward the needed part rather than promising that the outer selector crosses both boundaries.",
    'review-badge::part(label) { font-weight: 700; text-decoration-thickness: .12em; text-underline-offset: .16em; }\nreview-badge[status="held"]::part(label) { text-decoration-line: underline; }',
    "The rule adds little runtime work; public API stability is the larger cost. A theme that relies solely on color can erase the distinction between held and accepted states under forced colors or print. The sample adds an underline, but the component should also show the state in text. A public part is less brittle than reaching into a private class that an implementation may rename. Do not assume every pseudo-class or structural selector can be appended after ::part(); check the exact selector you need in target browsers. If the public name is forwarded through a nested host, verify that the exportparts mapping is correct in the actual markup.",
    ["Do not assume ::part() exposes arbitrary shadow descendants.", "Do not forget exportparts across a nested shadow root.", "Do not make color the only status signal."],
    ["css/shadow-host-variants", "css/focus-visible", "html/declarative-shadow-dom", "html/custom-elements"],
)

add(
    "slotted-content-boundary",
    "CSS ::slotted(): style only the assigned element",
    "Set a safe title treatment for content assigned to a component slot.",
    "The ::slotted() pseudo-element is available in a shadow-tree stylesheet. It matches elements directly assigned to a slot, including assigned elements described by the selector argument. It does not reach into descendants of an assigned element, and a plain text node is not an element that the selector can style.",
    "A case-panel component accepts a named title slot. The component styles an assigned heading and preserves normal wrapping for a long case name. It also gives its internal slot a readable fallback style for the case where no title is supplied. A consumer might pass a heading containing a strong element; ::slotted(h2) reaches the heading box, not that nested strong element. Put any descendant typography in the light DOM stylesheet or expose a stable part if the component owns the inner markup. Test an assigned heading, a plain text assignment, no assignment, and a title long enough to wrap at 200% zoom. Do not turn the slot into a visual-only label for a panel that requires a programmatic name; the component's accessibility relationship needs a separate review.",
    'slot[name="title"] { color: #173441; }\n::slotted([slot="title"]) { display: block; margin: 0; font: 700 1.2rem/1.35 system-ui; overflow-wrap: anywhere; }',
    "The selector itself is cheap. The integration cost appears when callers supply a different node shape from the one the stylesheet anticipated. Because text nodes do not match ::slotted(), a consumer that passes bare text may display it with inherited styles instead of the assigned-element rule. Prefer an explicit element contract for consistent typography. Do not write a descendant selector after ::slotted() and expect it to penetrate light DOM children. Slot assignment is an HTML behavior; CSS only paints the resulting boxes. Verify that fallback content is acceptable when the assigned slot is absent.",
    ["Do not expect ::slotted() to style grandchildren of an assigned element.", "Do not expect bare text to match an element selector.", "Do not use visual slot styling as a substitute for an accessible name."],
    ["css/shadow-host-variants", "css/shadow-part-theming", "html/slots-and-fallback", "html/declarative-shadow-dom"],
)

add(
    "custom-highlight-ranges",
    "CSS ::highlight(): paint searched text without changing its markup",
    "Keep a transient search overlay separate from semantic document highlights.",
    "The ::highlight() pseudo-element styles a named set of text ranges registered through the CSS Custom Highlight API. CSS does not find the ranges: JavaScript creates Range objects, constructs a Highlight, and registers its name. The paint is limited to supported highlight properties and does not insert a mark element or create semantic emphasis.",
    "A policy viewer marks current search matches as the user edits a query. The application updates the registered ranges; CSS gives them a pale background and dark foreground so the text remains legible. Provide a separate result count and keyboard path to each match. If a passage is important editorially even when search is idle, use semantic markup rather than a transient highlight registry. Test overlapping ranges, selection across a match, a query with no results, and a browser without the API. The search result list should still work when the paint is unavailable. Do not attach actions or tooltips to a highlight as though it were a DOM element. Keep its color distinct from text selection, and check that forced colors or user themes do not remove the only visible indication of the active match.",
    '::highlight(policy-search-match) { color: #163441; background-color: #ffe28a; }\n@media (forced-colors: active) { ::highlight(policy-search-match) { color: HighlightText; background-color: Highlight; } }',
    "Highlighting a very large number of ranges can increase style and paint work; update only the needed ranges when a query changes and measure a long document. The API setup and search algorithm are separate from the CSS sample. A range can become stale after the text nodes change, so the application must rebuild it after content replacement. The registry name in CSS must match the JavaScript registration name. A fallback result list is necessary because this paint has no semantics and may be unsupported. Avoid promising that the effect can decorate an arbitrary box: it paints text ranges under the API's property restrictions.",
    ["Do not expect CSS to discover or register search ranges.", "Do not treat a custom highlight as semantic mark text.", "Do not make the highlight color the only way to locate a result."],
    ["css/pseudo-elements-and-generated-content", "css/text-selection-controls", "html/mark-relevant-text", "html/inline-text-meaning"],
)

add(
    "view-transition-name-unique",
    "CSS view-transition-name: give one live element one transition identity",
    "Move a case card into its detail view without duplicate snapshot names.",
    "view-transition-name identifies a rendered element for a view transition. During a single transition, a custom name must be unique among the participating elements. Duplicate names cause the transition's ready promise to reject and the transition animation to be skipped. CSS alone does not start a same-document transition; application code calls document.startViewTransition around the DOM update.",
    "A review queue expands one selected case into a detail panel. The application applies a named class only to that selected card and the corresponding detail element at the appropriate stages of the update. It removes the class from other cards, including virtualized items that may briefly coexist. Test rapid reselection, an interrupted update, a hidden element, and a queue that renders two copies of the same case during a filter change. Keep the case identifier visible in text; the animated movement is optional. If the API is absent, update the DOM directly. The name is a transition identity, not a database key, and it need not encode private case data. match-element can assign browser-generated identities in supported same-document transitions, but it does not solve every cross-document mapping problem.",
    '.review-card.is-transition-source { view-transition-name: selected-case; }\n.case-detail.is-transition-target { view-transition-name: selected-case; }\n@media (prefers-reduced-motion: reduce) { ::view-transition-old(selected-case), ::view-transition-new(selected-case) { animation-duration: .01ms; } }',
    "A view transition captures visual snapshots, so a large card with images or filters can increase memory and painting work. Measure the real screen before animating several elements. The old and new elements may exist at different moments, but duplicate matching names in the same captured state break the transition. Keep the ordinary DOM update independent of transition success; the API is an enhancement. Review focus placement after the detail view appears, since a moving snapshot has no interactive semantics. The CSS sample supplies the identity and a reduced-motion treatment, while the application owns lifecycle, errors, and focus.",
    ["Do not assign one custom name to every card in a list.", "Do not expect view-transition-name to start a transition.", "Do not use a moving snapshot in place of focus management."],
    ["css/view-transition-snapshot-motion", "css/reduced-motion", "css/discrete-display-transitions", "html/custom-elements"],
)

add(
    "view-transition-snapshot-motion",
    "CSS view-transition snapshots: animate presentation, then restore interaction",
    "Scope old and new snapshot motion to one selected case.",
    "During a named view transition, ::view-transition-old(name) and ::view-transition-new(name) represent visual snapshots of the matching old and new states. Animation on those pseudo-elements changes the temporary image, not the underlying document semantics. The application still owns the DOM update, focus, and the state shown after the transition finishes.",
    "A selected case moves from an overview tile into a detail sheet. The old snapshot fades while the new snapshot arrives; a reduced-motion query removes those animations. The detail sheet must be fully usable immediately if the transition API is unsupported or the transition is skipped because names collide. Avoid a long crossfade over live controls: a visual copy of a button can appear clickable while the actual focus target is elsewhere. Test keyboard focus before and after the update, rapid back navigation, interrupted transitions, and the reduced-motion setting. A pure opacity change is appropriate only when the content remains understandable in both states. If the view change also replaces an error message, announce that message through the application's ordinary accessible status pattern, not through motion.",
    '::view-transition-old(selected-case) { animation: case-exit 180ms ease-in both; }\n::view-transition-new(selected-case) { animation: case-enter 180ms ease-out both; }\n@keyframes case-exit { to { opacity: 0; } }\n@keyframes case-enter { from { opacity: 0; } }\n@media (prefers-reduced-motion: reduce) { ::view-transition-old(selected-case), ::view-transition-new(selected-case) { animation: none; } }',
    "Snapshots can require extra image memory and paint work, especially when the chosen element includes large media or expensive effects. Keep the scope narrow and profile a real device. Animation does not repair an invalid element-name mapping, a missing DOM update, or lost focus. The reduced-motion rule removes the authored fades; verify the target browser's default transition treatment as well. A brief visual transition is useful only when it helps maintain place without delaying the new content. Do not hide the detail sheet until animation end just to make the effect look complete.",
    ["Do not confuse visual snapshots with interactive DOM elements.", "Do not animate every case card when only one changes.", "Do not leave focus on a removed overview control."],
    ["css/view-transition-name-unique", "css/reduced-motion", "css/keyframe-animation", "css/focus-visible"],
)

add(
    "supports-selector-gate",
    "CSS @supports selector(): gate a relational selector safely",
    "Keep the base component useful when a newer selector cannot parse.",
    "The @supports selector() condition asks whether a browser recognizes a selector's syntax. It can guard a rule containing :has() so an unsupported engine keeps the base styling. The condition does not verify that the selector matches the intended markup, that the interaction works, or that every user can perceive the resulting state.",
    "A dispatch card has a permanent border and a visible text label for its held state. If :has() is supported, the card adds a thicker edge when it contains a checked hold control. The plain border and text remain meaningful without that selector. A script may still need to update an external summary; this CSS relationship cannot persist a review decision or submit it. Test checked, unchecked, disabled, and dynamically replaced controls. Do not write the checked-state emphasis before the feature gate with the unsupported selector in a comma-separated group, since the entire rule can be discarded when parsing fails. If the relationship becomes expensive across a huge changing tree, scope the selector to a short component rather than a page-wide ancestor. The conditional rule should only improve an already working control.",
    '.dispatch-card { border: 1px solid #597581; padding: 1rem; }\n@supports selector(:has(input:checked)) { .dispatch-card:has(> .hold-control input:checked) { border-inline-start: .35rem solid #7a382e; } }\n.dispatch-card:focus-within { outline: 2px solid #205d78; outline-offset: 2px; }',
    "The feature check is cheap. The relationship selector can cost more when broad ancestors must be reconsidered after frequent DOM changes; keep the subject narrow and benchmark a large repeated list if necessary. More significant is the compatibility risk: a browser that fails the condition never sees the enhancement, so the visible label and usable checkbox must stand on their own. @supports validates selector syntax, not accessible state wording or server persistence. Confirm the checked control remains operable with keyboard and assistive technology. The card's focus-within outline makes the current group easier to locate but does not replace the input's own focus cue.",
    ["Do not assume a syntax check proves the state relationship is correct.", "Do not hide the only held-state cue inside a feature gate.", "Do not use an unscoped :has() rule across a large changing page."],
    ["css/supports-feature-query", "css/has-relationships", "css/focus-within-group", "html/form-validation"],
)

add(
    "baseline-alignment-mixed-type",
    "CSS baseline alignment: line up mixed text by its reading edge",
    "Align a count and label without pretending equal box centers mean equal text alignment.",
    "align-items: baseline aligns participating flex or grid items using their first baselines where the layout can establish a shared baseline. This differs from center, which aligns box centers. Font metrics, line wrapping, and writing modes affect the resulting position, so a baseline rule should be checked with the actual text and fonts.",
    "An incident header places a large numeric count beside a smaller status label. Center alignment makes the characters appear to sit at different reading levels even though their boxes are centered; first-baseline alignment keeps their primary text lines together. The gap remains explicit, and wrapping is allowed rather than forcing a long translated label off screen. Test a one-line label, a two-line translation, an alternate font, and 200% zoom. If the label wraps, only its first line shares the intended baseline; decide whether that still reads correctly. A badge icon has no natural text baseline in the same sense, and may need its own alignment decision. Avoid absolute offsets tuned to one font file. For vertical writing or mixed scripts, verify the chosen writing mode before assuming the western horizontal baseline is the desired visual reference.",
    '.incident-heading { display: flex; flex-wrap: wrap; align-items: baseline; column-gap: .55rem; row-gap: .25rem; }\n.incident-heading__count { font: 700 2.2rem/1 system-ui; }\n.incident-heading__label { font: 600 1rem/1.4 system-ui; max-inline-size: 24ch; }',
    "Baseline alignment adds negligible work relative to ordinary layout. The real cost is maintaining visual accuracy across fonts, translations, and wrapping. A fallback font with different ascent or descent metrics can shift the perceived result, so test the actual loading path rather than only a design mockup. Flex wrapping creates multiple lines; alignment happens within each line, not across an entire multi-line header as one unit. If the numeric count is spoken without context, give it a meaningful nearby label in the HTML. CSS cannot create that relationship. Avoid using transform or relative positioning to compensate for a mismatch that baseline alignment solves more clearly.",
    ["Do not assume box centering aligns glyph baselines.", "Do not expect one baseline rule to align every wrapped line together.", "Do not use a positional nudge tied to one font's metrics."],
    ["css/alignment-and-gap", "css/font-size-adjust-fallback", "css/writing-mode-layout", "html/headings-and-paragraphs"],
)

titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
titles[quiz_path] = "CSS component boundaries and transitions: twelve decisions"
for item in specs:
    assert all(target in titles for target in item["related"]), item["path"]


def links(paths):
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in paths
    ) + "</ul>"


hub = by_path[hub_path]
hub["data"]["modules"].append({
    "title": "Component boundaries and transition identity",
    "summary": "Public shadow styling contracts, text highlights, view snapshots, selector gating, and baseline alignment.",
    "lessons": [item["path"] for item in specs],
})
hub["body"] += "<h2>Component boundaries and transition identity</h2>" + links([item["path"] for item in specs])
hub["updated_at"] = stamp

for index, item in enumerate(specs):
    row = copy.deepcopy(by_path["css/selectors-and-cascade"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + item["path"])),
               path=item["path"], title=item["title"], summary=item["summary"],
               subject="css-reference", sort_order=24400 + index,
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
    "css/scoped-rules": ["css/shadow-host-variants"],
    "css/custom-properties": ["css/shadow-host-variants"],
    "css/pseudo-elements-and-generated-content": ["css/shadow-part-theming", "css/custom-highlight-ranges"],
    "css/has-relationships": ["css/supports-selector-gate"],
    "css/supports-feature-query": ["css/supports-selector-gate"],
    "css/alignment-and-gap": ["css/baseline-alignment-mixed-type"],
    "css/transitions-and-transforms": ["css/view-transition-name-unique", "css/view-transition-snapshot-motion"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Related component decisions</h2>" + links(targets)
    row["data"].setdefault("related", []).extend(
        {"path": target, "title": titles[target]} for target in targets
    )
    row["updated_at"] = stamp

questions = [
    ("Where does :host select its host?", ["Inside the host's shadow stylesheet", "In every document stylesheet", "Only inside a media query"], 0, "The selector is meaningful inside a shadow root."),
    ("What provides an outside styling token through a shadow boundary?", ["A documented custom property", "A private inner class", "An undocumented DOM index"], 0, "Inherited custom properties can cross the boundary."),
    ("Who decides which internal node ::part() exposes?", ["The component author through a part name", "The browser's global stylesheet", "Any descendant selector"], 0, "The component owns its public part contract."),
    ("What is needed for a part inside a nested shadow root?", ["A suitable exportparts forwarding path", "A larger z-index", "A page-wide universal selector"], 0, "Nested shadow boundaries require explicit forwarding."),
    ("What can ::slotted() directly match?", ["An assigned element", "Every descendant of an assigned element", "A plain text node"], 0, "It matches assigned elements, not their descendants or bare text."),
    ("What creates the ranges painted by ::highlight()?", ["Application code using Range and Highlight", "The CSS declaration itself", "The focus ring"], 0, "CSS styles ranges registered through the API."),
    ("Does a custom highlight create semantic mark text?", ["No", "Yes, always", "Only during print"], 0, "It paints ranges without changing document semantics."),
    ("What happens when participating elements share one custom view-transition-name?", ["The transition can be skipped after ready rejects", "They merge into one semantic control", "The browser creates unique names"], 0, "Custom names must be unique in a captured state."),
    ("What begins a same-document view transition?", ["Application code calling startViewTransition", "Only a CSS name", "A hover selector"], 0, "CSS naming does not start the update."),
    ("What does a view-transition snapshot provide?", ["Temporary visual presentation", "Persistent focus management", "A server response"], 0, "The application still owns interaction and DOM state."),
    ("What does @supports selector() check?", ["Selector syntax support", "Accessible behavior", "Server persistence"], 0, "It cannot prove the full component is correct."),
    ("What aligns mixed-size text by its reading line?", ["Baseline alignment", "Box centering", "A fixed transform offset"], 0, "A shared baseline aligns text rather than box centers."),
]
quiz = copy.deepcopy(by_path["quizzes/css-advanced"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
            path=quiz_path, title=titles[quiz_path],
            summary="Twelve checks on component styling boundaries and transition behavior.",
            sort_order=3140, status="published", published_at=stamp,
            created_at=stamp, updated_at=stamp)
quiz["data"] = {
    "subject_root": "css/css-tutorial", "section_path": "css/quizzes",
    "content_format": "html", "author_path": "authors/aitrove-editorial",
    "seo_ready": True, "duration_minutes": 12,
    "related": [{"path": target, "title": titles[target]} for target in [
        "css/shadow-host-variants", "css/slotted-content-boundary",
        "css/view-transition-name-unique", "css/supports-selector-gate"]],
    "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                       answer=(answer - index % 3) % 3, explanation=explanation)
                  for index, (prompt, options, answer, explanation) in enumerate(questions)],
}
quiz["body"] = (
    "<p>Check which styling surfaces are public and which behavior an application must supply.</p>"
    "<h2>Review the decisions</h2>" + links([item["path"] for item in quiz["data"]["related"]])
    + "<h2>Other checks</h2>" + links(["css/quizzes", "quizzes/css-rendering-contracts"])
    + "<h3>Common Mistakes</h3><ul><li>Do not confuse paint with semantics.</li>"
    "<li>Do not expect CSS to start or manage an application transition.</li></ul>"
)
rows.append(quiz)
quiz_hub = by_path["css/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Component boundaries check</h2>" + links([quiz_path])
quiz_hub["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_quizzes": 1,
                  "total_records": len(rows)}))

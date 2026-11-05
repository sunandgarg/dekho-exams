"""Add eight CSS native-state and navigation lessons with one linked quiz."""

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
quiz_path = "quizzes/css-native-states-navigation"
specs = []


def add(slug, title, summary, definition, decision, sample, cost, mistakes, related):
    path = "css/" + slug
    assert path not in by_path
    specs.append(dict(path=path, title=title, summary=summary, definition=definition,
                      decision=decision, sample=sample, cost=cost,
                      mistakes=mistakes, related=related))


add(
    "defined-custom-element-boundary",
    "CSS :defined: preserve content while a custom element upgrades",
    "Distinguish a registered component from an unknown tag without hiding useful fallback text.",
    "The :defined pseudo-class matches built-in elements and custom elements whose definitions have been registered. A named custom element can exist in the DOM before its JavaScript class loads; it matches :not(:defined) during that interval. Registration does not prove that its data request completed or that every child control is ready.",
    "An audit-summary custom element contains a short server-rendered status line before its behavior loads. Give the host a stable block box and border immediately so the page does not jump. After definition, a class added by the component can enhance its internal layout. The CSS below marks the pre-upgrade host with a quieter border, while its text stays visible and readable. Test slow script loading, script failure, and a disabled-script browser. Do not set display: none on the undefined host if it contains the only case status. If a custom element replaces light DOM content during upgrade, that replacement needs its own accessibility and loading review; :defined cannot keep the old content present. Check that a defined component with a pending network request still reports loading in words rather than using this selector as a fake data-ready state. A system font and stable minimum size can reduce visual movement without concealing the fallback.",
    'audit-summary { display: block; min-block-size: 4rem; padding: .8rem; border: 1px solid #6e8792; color: #173441; }\n audit-summary:not(:defined) { border-style: dashed; background: #f4f7f8; }\n audit-summary:defined { border-color: #315f75; }',
    "Matching this state is inexpensive. The risk is a hidden or misleading pre-upgrade page: if the JavaScript bundle fails, an invisible custom element never becomes useful. Keep the fallback content in the markup and verify it with throttled or blocked scripts. A completed definition only means the browser has registered the element; application state, data, and event listeners may settle later. Avoid a global :not(:defined) rule that catches unrelated future custom tags. Scope the selector to the component you own. Inspect layout shift when the real template replaces the fallback and keep the same broad dimensions where practical.",
    ["Do not equate :defined with data loaded.", "Do not hide the only meaningful fallback inside an undefined component.", "Do not style every undefined tag with a page-wide selector."],
    ["css/shadow-host-variants", "css/content-visibility", "html/custom-elements", "html/noscript-fallback"],
)

add(
    "custom-element-state-selector",
    "CSS :state(): expose one internal custom-element state to styling",
    "Paint a component-owned state without leaking its internal attributes.",
    "The :state() pseudo-class matches a custom state in an autonomous custom element's ElementInternals.states set. Component JavaScript adds or removes the state identifier; CSS reads it. The selector does not invent the state, persist a decision, or give the element an accessible role by itself.",
    "A review-gate element tracks whether a case is awaiting a second reviewer. The component adds the pending-review state through ElementInternals after its domain state changes. An outside stylesheet uses :state(pending-review) to strengthen the border while the component shows the words Pending review in its rendered content. The base border remains clear if the selector is unsupported. Do not encode a server authorization result solely as an internal style token; users and assistive technology need the actual status. Decide whether the state name is a public contract before other teams depend on it. Test state addition, removal, a failed save, a component upgrade after HTML arrives, and a browser without this selector. If the state is reflected to an attribute for compatibility, update that attribute from the same component logic so the two representations cannot disagree. The state should describe the component, not the user's hover or focus, which already have native selectors.",
    'review-gate { display: block; padding: .85rem; color: #173441; border: 1px solid #62808c; }\n@supports selector(:state(pending-review)) { review-gate:state(pending-review) { border-inline-start: .4rem solid #915a22; background: #fff4df; } }',
    "The selector adds little rendering cost; the state model and compatibility path cost more. State changes must follow the real workflow, including rollback after a rejected save. A CSS feature gate prevents an unsupported selector from breaking neighboring rules, but it does not create an alternative visible status; the component's text does that work. Custom states are supported on autonomous custom elements, so test the actual element type rather than assuming a customized built-in follows the same pattern. A private state that other applications begin styling becomes an accidental API. Record which identifiers may be used externally and version them with care.",
    ["Do not treat :state() as a substitute for status text.", "Do not add a state token before the underlying decision is known.", "Do not assume an unsupported selector leaves the component semantically complete."],
    ["css/defined-custom-element-boundary", "css/supports-selector-gate", "css/shadow-part-theming", "html/custom-elements"],
)

add(
    "details-content-surface",
    "CSS ::details-content: style the disclosure body while keeping native behavior",
    "Separate an expanded explanation from its summary without adding a script-controlled panel.",
    "The ::details-content pseudo-element represents the expandable content of a details element, separate from its always-visible summary. It provides a styling target in supporting browsers. The browser still owns the open state and disclosure interaction; this pseudo-element does not create a details element or supply a summary.",
    "An incident policy note places the rule name in summary and the explanation below it. Give the details element a border and padding that work in every target browser; enhance the expanded body with a top rule and spacing through ::details-content. The same information remains readable if that pseudo-element is ignored. Test closed and open states, keyboard activation, a long linked paragraph, 200% zoom, and printing. Avoid animating height without checking the collapsed content visibility behavior and reduced-motion preference. The sample uses no animation because the policy text must be available immediately. If the disclosure is critical to completing a form, do not hide a required instruction in it and assume every user will open it. Keep the summary text descriptive. A custom content surface is cosmetic; the HTML owns the relationship between summary and explanation.",
    '.policy-note { border: 1px solid #708891; border-radius: .35rem; padding: .75rem; color: #173441; }\n.policy-note > summary { font-weight: 700; cursor: pointer; }\n.policy-note::details-content { margin-block-start: .65rem; padding-block-start: .65rem; border-block-start: 1px solid #a8b7bd; }',
    "The rule is inexpensive, though an animated expansion could trigger repeated layout work. Here the main cost is compatibility: older browsers may ignore ::details-content, so the outer details border and ordinary text spacing must still work. Inspect the real summary marker; removing it without an equivalent cue weakens the control. A printed copy should not omit essential closed content, so review print behavior independently of screen appearance. Styling the pseudo-element does not change native focus behavior or make content outside the details part of its accessible name. Check the target browser matrix before relying on the added divider.",
    ["Do not assume ::details-content works in older browsers.", "Do not remove the summary marker without a clear replacement cue.", "Do not hide required instructions in a disclosure by default."],
    ["css/open-state-selector", "css/discrete-display-transitions", "html/dialog-and-details", "html/exclusive-details-groups"],
)

add(
    "target-text-fragment-cue",
    "CSS ::target-text: preserve the reader's place after a text-fragment link",
    "Make a browser-selected passage legible without confusing it with a section anchor.",
    "The ::target-text pseudo-element styles text selected by a supported text-fragment navigation. It is distinct from :target, which matches an element addressed by an ordinary fragment identifier. The browser finds the passage; CSS only paints the resulting text highlight. If the quoted words change or the browser lacks text-fragment support, the passage may not be targeted.",
    "An investigator shares a paragraph from a lengthy incident report. A restrained highlight gives the recipient a visible landing cue while the paragraph text remains selectable and readable. Use contrasting foreground and background colors and check them under forced colors. The page must still have useful headings and stable section links; a text fragment is a convenience, not the only route to the evidence. Test a fragment that matches one passage, a repeated phrase, a stale quotation, a dark theme, and high zoom. Avoid making the target yellow without considering the text color; inherited pale text can disappear on a bright highlight. This selector cannot identify an arbitrary search result produced by the application, which belongs to a different highlight mechanism. Nor does it mark the passage as semantically important for every reader. If the quotation is part of the report's authored emphasis, preserve that meaning in the document markup.",
    '::target-text { color: #173441; background-color: #ffe29a; }\n@media (forced-colors: active) { ::target-text { color: HighlightText; background-color: Highlight; } }',
    "Painting a selected text range is usually modest work; the reliability cost is the fragile match to changing prose. Rewriting a sentence can invalidate old shared links. Keep stable heading anchors for long-lived references and review links that external systems have stored. The stylesheet cannot detect which text directive failed to match. Test the navigation itself, not only a screenshot of the CSS rule. Do not confuse this with :target: one works on targeted text and the other on a fragment-identified element. A text-fragment highlight also does not create focus or an accessible announcement by itself.",
    ["Do not rely on a text fragment as the only permanent citation path.", "Do not use :target when the browser targeted text instead of an element.", "Do not assume the highlight creates semantic emphasis."],
    ["css/target-fragment-highlight", "css/custom-highlight-ranges", "html/mark-relevant-text", "html/headings-and-paragraphs"],
)

add(
    "cross-document-view-transition-opt-in",
    "CSS @view-transition: opt in only the pages that can tolerate a cross-page animation",
    "Treat same-origin navigation motion as an enhancement to normal links.",
    "The @view-transition rule can opt a document into cross-document view transitions with navigation: auto. Both the departing and arriving documents must opt in, and the navigation must satisfy the browser's same-origin and navigation rules. A normal link and a fully rendered destination remain necessary; CSS does not replace navigation or provide a router.",
    "An incident index and case detail page share a site shell. Their common stylesheet opts both pages in, then keeps the transition short. The ordinary link works when the feature is unavailable, when one page does not opt in, or when a navigation does not qualify. Test a direct page load, a same-origin link, back navigation, a redirect, and an external link. Do not promise the same animation across a cross-origin redirect. The default transition may capture the whole root; review whether sensitive on-screen information can remain visible in a snapshot during navigation. If a named element is added later, ensure each captured document has one matching identity. Keep headings and focus behavior correct after navigation. A reduced-motion preference removes the authored root animation, while the destination content and link behavior remain unchanged. The page should never delay rendering to wait for a decorative transition.",
    '@view-transition { navigation: auto; }\n::view-transition-old(root), ::view-transition-new(root) { animation-duration: 140ms; }\n@media (prefers-reduced-motion: reduce) { ::view-transition-old(root), ::view-transition-new(root) { animation: none; } }',
    "A full-page snapshot can consume more memory and paint time than a narrow named element. Profile navigation on a realistic page before keeping the effect. Cross-document support is still limited, so a site must behave cleanly when the at-rule is ignored. Both documents need the opt-in; a shared stylesheet makes that easier but can also opt in an unsuitable page by accident. Check the route set rather than applying it globally without review. The transition does not transfer application state, stop a network request, or manage focus in an application shell. Keep those contracts independent of the animation.",
    ["Do not assume an opt-in on one page is sufficient.", "Do not expect cross-origin navigation to use this transition.", "Do not let a page-wide snapshot delay or obscure the destination content."],
    ["css/view-transition-name-unique", "css/view-transition-snapshot-motion", "css/reduced-motion", "html/aria-current-navigation"],
)

add(
    "scripting-media-fallback",
    "CSS scripting media feature: reveal a fallback when scripts cannot run",
    "Keep the core document usable before treating script availability as a styling condition.",
    "The scripting media feature reports whether scripting is enabled, unavailable, or limited to the initial load. Its values include enabled, none, and initial-only. It reflects browser settings, not whether a particular bundle loaded successfully, a component initialized, or an API request finished.",
    "A live dispatch board includes a static list of urgent cases in the HTML and adds a live filter when its script initializes. The static list remains the default. When scripting is unavailable, a short note explains that filtering is unavailable while leaving the cases readable. If the browser does not support this media feature, the default list still works. An enabled result is not proof that the filter loaded: a blocked module or runtime exception can leave scripts allowed but the feature broken. The application should reveal the filter only after initialization, not merely through this media query. Test script disabled, bundle blocked, an exception during setup, and the initial-only setting where it exists. Do not make an enabled-only CSS rule hide the static cases. The fallback text should describe an actual limitation, not tell users that their browser is obsolete. CSS can present a hint; the HTML and application own the real workflow.",
    '.dispatch-list { display: block; }\n.script-unavailable-note { display: none; }\n@media (scripting: none) { .script-unavailable-note { display: block; color: #173441; background: #eef4f6; padding: .75rem; } }',
    "The query is cheap; the main cost is false confidence in what it measures. A browser extension may block a script while the media feature still reports enabled. Keep all essential data in the default markup or supply a server-rendered path, and toggle an enhanced control only after successful setup. The note can be absent in older browsers that ignore the query, so the page must remain comprehensible without it. Do not use scripting: none as a security check or authorization boundary. It is a presentation hint about the environment, not a guarantee about individual requests or application health.",
    ["Do not equate scripting: enabled with a successful app initialization.", "Do not hide essential content behind a media feature.", "Do not use this query to decide authorization or data access."],
    ["css/media-queries", "css/defined-custom-element-boundary", "html/noscript-fallback", "html/script-loading"],
)

add(
    "modal-state-selector",
    "CSS :modal: style the active modal state without faking modality",
    "Give a native modal dialog a readable surface and focus boundary.",
    "The :modal pseudo-class matches an element in a modal state that excludes interaction outside it. A dialog opened with showModal() is a common case; a dialog merely opened with the open attribute is not equivalent. CSS cannot turn a normal panel into a modal dialog or implement the browser's focus and top-layer behavior.",
    "A document-rejection form opens as a native dialog when a reviewer chooses Reject. The base dialog rule gives its content a solid surface and bounded width; the modal state adds a distinct border. Keep the reason field's label, the Cancel and Confirm controls, and an obvious focus indicator in the markup. Test Tab and Shift+Tab, Escape or the configured close policy, a long error message, mobile viewport height, and forced colors. Do not style every :modal element globally: fullscreen content may also match and needs a different treatment. The border cannot communicate whether rejection has succeeded; wait for the server result and show that result in text. Avoid a transparent surface whose legibility depends on a blurred backdrop. If JavaScript never calls showModal(), the underlying page should still provide a route to complete or cancel the action rather than presenting a dead button.",
    '.reject-dialog { box-sizing: border-box; max-inline-size: min(34rem, calc(100vw - 2rem)); max-block-size: calc(100dvh - 2rem); overflow: auto; color: #173441; background: #f7fafb; }\n.reject-dialog:modal { border: 3px solid #325f73; }\n.reject-dialog :focus-visible { outline: 3px solid #1b657f; outline-offset: 2px; }',
    "The selector itself is inexpensive. The important work is checking focus, close behavior, and form state under the real dialog interaction. A CSS border cannot enforce modality, trap focus, or restore focus after close. The browser's showModal() path supplies much of that behavior, but the application still has to handle cancellation and submit results correctly. The max-block-size avoids content disappearing beneath a short viewport; test the viewport-unit fallback in older browsers if those are supported. Scope the rule to this dialog so a fullscreen element is not accidentally styled as a rejection form.",
    ["Do not treat an open attribute as proof of modal behavior.", "Do not use :modal as a page-wide theme selector.", "Do not rely on border color to report the server result."],
    ["css/modal-backdrop-boundary", "css/focus-visible", "html/dialog-and-details", "html/dialog-closedby"],
)

add(
    "picture-in-picture-state",
    "CSS :picture-in-picture: reflect detached video state without losing the page transcript",
    "Style the originating video when it enters a floating player.",
    "The :picture-in-picture pseudo-class matches an element currently in picture-in-picture mode where that selector is supported. For ordinary video picture-in-picture, it can alter CSS on the source video element. It does not create the floating player, inject custom controls into its browser chrome, or make a transcript available there.",
    "A training video about evidence review can play in a floating window while the learner reads a checklist. On the page, a status line still says how to return to the full player; script updates that line from the actual picture-in-picture events. CSS adds a subdued border to the video element while it is detached, which is an optional cue rather than the only explanation. Keep the caption and transcript links in the page UI, since not every floating player shows the same controls. Test entry, exit, failed request, browser denial, mobile behavior, and keyboard access to the original controls. Do not hide the original player or transcript when the pseudo-class matches: users may need to return to it. A permission policy or browser setting can prevent picture-in-picture even if this CSS parses. Video playback and detached-window behavior belong to browser and application code, not to the selector.",
    '.training-video { display: block; max-inline-size: 100%; border: 2px solid #6b8490; }\n@supports selector(:picture-in-picture) { .training-video:picture-in-picture { border-color: #235d77; outline: 2px solid #235d77; } }',
    "The styling cost is minor, but media playback and a second viewing surface have their own resource costs. Measure the video experience on target devices instead of assuming the selector changes decoding or bandwidth. Browser support for :picture-in-picture is limited, so the status line and transcript must work without it. The CSS rule cannot know whether a picture-in-picture request failed before entering the mode; event handling must report that result. Do not treat a visual border as evidence that the video is currently accessible in the separate window. Review captions in the floating player and keep the page transcript independently reachable.",
    ["Do not expect CSS to start picture-in-picture mode.", "Do not place the only caption or transcript path in the floating window.", "Do not assume selector support means a request will succeed."],
    ["css/fullscreen-media-state", "css/supports-selector-gate", "html/video-captions", "html/video-descriptive-transcript"],
)

titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
titles[quiz_path] = "CSS native states and navigation: twelve decisions"
for item in specs:
    assert all(target in titles for target in item["related"]), item["path"]


def links(paths):
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in paths
    ) + "</ul>"


hub = by_path[hub_path]
hub["data"]["modules"].append({
    "title": "Native states and navigation surfaces",
    "summary": "Separate CSS state cues from component setup, document navigation, disclosure, and media behavior.",
    "lessons": [item["path"] for item in specs],
})
hub["body"] += "<h2>Native states and navigation surfaces</h2>" + links([item["path"] for item in specs])
hub["updated_at"] = stamp

for index, item in enumerate(specs):
    row = copy.deepcopy(by_path["css/selectors-and-cascade"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + item["path"])),
               path=item["path"], title=item["title"], summary=item["summary"],
               subject="css-reference", sort_order=24500 + index,
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
    "css/shadow-host-variants": ["css/defined-custom-element-boundary", "css/custom-element-state-selector"],
    "css/open-state-selector": ["css/details-content-surface"],
    "css/target-fragment-highlight": ["css/target-text-fragment-cue"],
    "css/view-transition-name-unique": ["css/cross-document-view-transition-opt-in"],
    "css/media-queries": ["css/scripting-media-fallback"],
    "css/modal-backdrop-boundary": ["css/modal-state-selector"],
    "css/fullscreen-media-state": ["css/picture-in-picture-state"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Related native states</h2>" + links(targets)
    row["data"].setdefault("related", []).extend(
        {"path": target, "title": titles[target]} for target in targets
    )
    row["updated_at"] = stamp

questions = [
    ("What does :defined confirm for a custom element?", ["Its definition was registered", "Its data request succeeded", "Its server action committed"], 0, "Definition is separate from application readiness."),
    ("What should remain visible before an audit component upgrades?", ["Meaningful fallback status text", "Only a hidden empty host", "A CSS-generated case number"], 0, "Fallback content should survive script failure."),
    ("Where does :state() read a custom state?", ["ElementInternals.states", "The CSS stylesheet itself", "The browser history entry"], 0, "Component code updates the CustomStateSet."),
    ("What can ::details-content target?", ["The expandable details body", "Only the summary marker", "Every dialog backdrop"], 0, "It is distinct from the always-visible summary."),
    ("How does ::target-text differ from :target?", ["It paints targeted text rather than an identified element", "It starts a search request", "It adds a heading ID"], 0, "Text fragments and element fragments have different targets."),
    ("What happens to an old text-fragment link after its words change?", ["It may stop matching", "It always repairs itself", "It becomes a custom highlight"], 0, "Text-fragment targeting depends on matching text."),
    ("What is required for cross-document view transitions?", ["Opt-in on both same-origin documents", "A CSS class on one link only", "A cross-origin redirect"], 0, "Both documents must opt in and navigation must qualify."),
    ("Does scripting: enabled prove the feature bundle initialized?", ["No", "Yes", "Only in print"], 0, "The query reports scripting availability, not app health."),
    ("What is a usable default under an unknown scripting media feature?", ["Readable core HTML content", "Hidden cases", "An empty client shell"], 0, "The base document must work without the query."),
    ("Which action opens a dialog modally?", ["Calling showModal()", "Setting a border", "Adding open alone"], 0, "CSS and the open attribute do not create modal behavior."),
    ("What can :modal match besides a modal dialog?", ["A fullscreen element", "Every focused button", "Every details element"], 0, "Scope a dialog rule to its own element."),
    ("What starts picture-in-picture mode?", ["Browser or application media behavior", "The :picture-in-picture selector", "A border declaration"], 0, "The selector only reflects a state that already exists."),
]
quiz = copy.deepcopy(by_path["quizzes/css-advanced"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
            path=quiz_path, title=titles[quiz_path],
            summary="Twelve checks on custom state, disclosure, text targets, navigation, and media.",
            sort_order=3150, status="published", published_at=stamp,
            created_at=stamp, updated_at=stamp)
quiz["data"] = {
    "subject_root": "css/css-tutorial", "section_path": "css/quizzes",
    "content_format": "html", "author_path": "authors/aitrove-editorial",
    "seo_ready": True, "duration_minutes": 12,
    "related": [{"path": target, "title": titles[target]} for target in [
        "css/defined-custom-element-boundary", "css/details-content-surface",
        "css/cross-document-view-transition-opt-in", "css/modal-state-selector"]],
    "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                       answer=(answer - index % 3) % 3, explanation=explanation)
                  for index, (prompt, options, answer, explanation) in enumerate(questions)],
}
quiz["body"] = (
    "<p>Check which states CSS can paint and which interactions the browser or application must own.</p>"
    "<h2>Review the decisions</h2>" + links([item["path"] for item in quiz["data"]["related"]])
    + "<h2>Other checks</h2>" + links(["css/quizzes", "quizzes/css-component-boundaries"])
    + "<h3>Common Mistakes</h3><ul><li>Do not confuse styling a state with creating it.</li>"
    "<li>Do not hide essential content behind optional animation or script behavior.</li></ul>"
)
rows.append(quiz)
quiz_hub = by_path["css/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Native states check</h2>" + links([quiz_path])
quiz_hub["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_quizzes": 1,
                  "total_records": len(rows)}))

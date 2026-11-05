"""Extend the CSS reference with form, type, and contrast decisions."""

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
quiz_path = "quizzes/css-forms-type-decisions"
specs = []


def add(slug, title, summary, definition, decision, sample, cost, mistakes, related):
    path = "css/" + slug
    assert path not in by_path
    specs.append(dict(path=path, title=title, summary=summary, definition=definition,
                      decision=decision, sample=sample, cost=cost, mistakes=mistakes,
                      related=related))


add("field-sizing-controls", "CSS field-sizing: let a note grow within firm limits",
    "Grow a case note with entered text without letting it consume the whole form.",
    "Field-sizing changes how supported controls choose their preferred size. The content value lets a text input or textarea size to its contents, subject to constraints supplied by the containing layout and CSS min or max sizes.",
    "A reviewer writes a short exception note beside other form fields. A rigid two-line box becomes awkward when the note grows, but an unbounded box can push the submit action far below the screen. Give the textarea a useful minimum, an upper bound, and a width that fits the form; then opt into content sizing where supported. The sample retains a usable block size if the new property is ignored. Test an empty note, a long pasted paragraph, high zoom, and the case where the field reaches its maximum and starts scrolling. The HTML label and any length rule remain separate. Do not set a fixed height after requesting content sizing and expect the control to keep growing. If the note is required, validate that requirement in the form and service.",
    ".exception-note { box-sizing: border-box; inline-size: 100%; min-block-size: 7rem; max-block-size: 18rem; resize: vertical; }\n@supports (field-sizing: content) { .exception-note { field-sizing: content; } }",
    "Growing a control changes layout as text is entered, which is expected but can move nearby controls. Keep the label and error message associated with the field, and test keyboard scrolling after the maximum size is reached. The declaration itself is inexpensive. Unsupported browsers keep the minimum-sized textarea and a resize handle. A content-sized input without a minimum can shrink to a cursor-width sliver, so do not apply the rule to every form control. Measure form completion on small screens before deciding that automatic growth improves the task.",
    ["Do not use field-sizing without minimum and maximum limits.", "Do not expect a fixed height to coexist with content growth.", "Do not substitute visual growth for validation or a visible label."],
    ["css/form-control-states", "css/size-constraints", "html/textarea-wrap-submission"])

add("caret-color-visibility", "CSS caret-color: keep the insertion point visible",
    "Set a readable caret for a themed input without hiding the browser's focus cue.",
    "Caret-color sets the color of the text insertion caret in editable content. It is independent of the text selection highlight and the control's focus outline.",
    "A dark search field uses pale text. If the caret inherits a color that blends into its surface, users can lose track of the insertion point even while the field is focused. Give the field a caret color with visible contrast and keep a separate focus outline around the control. The sample scopes both to the search input, rather than changing every editable surface in the app. Test when the field is empty, after browser autofill, in forced colors, and with an invalid state that changes the border. A caret color cannot make a disabled field editable or identify the input to a screen reader. Preserve the HTML label and a stable text color in every state.",
    ".case-search { color: #f7fafc; background: #173148; caret-color: #f6d77a; }\n.case-search:focus-visible { outline: 3px solid #f6d77a; outline-offset: 2px; }",
    "Changing a caret color has negligible performance cost. The cost is reviewing the complete state palette: a bright caret against one background may disappear after autofill or an error theme changes the surface. In forced colors, allow system colors to take priority where the browser adjusts them. Do not remove the focus outline because the caret is visible; a user may focus an empty control without an insertion point showing yet. Test keyboard entry and text selection separately, since the caret and selection are different feedback channels.",
    ["Do not make the caret and background the same color.", "Do not treat the caret as a replacement for focus indication.", "Do not use caret-color to imply a control is editable when it is disabled."],
    ["css/focus-visible", "css/form-control-states", "css/light-dark-color-scheme"])

add("placeholder-shown-state", "CSS placeholder-shown: style empty state without replacing a label",
    "Distinguish an empty field while leaving its persistent name in the document.",
    "The placeholder-shown pseudo-class matches a control while its placeholder text is currently displayed. It tests that display state, not whether a submitted value is valid or whether the field has been touched.",
    "A payment-reference input can have a format hint such as an example code, but the visible label must remain outside the control so it does not vanish after entry. Use placeholder-shown to soften an optional helper border before the user types, while keeping the focus outline and error treatment independent. The sample does not move the label or use placeholder text as the only instruction. Test browser autofill, pasted values, whitespace-only input, and an empty required field after failed submission. A placeholder disappears when a value is entered; it is poor storage for a format rule users may need while editing. If validation fails, show a specific visible error and connect it to the control in HTML.",
    ".payment-reference { border: 2px solid #41637c; }\n.payment-reference:placeholder-shown { border-color: #8fa7b8; }\n.payment-reference:focus-visible { outline: 3px solid #175b44; outline-offset: 2px; }",
    "Matching this state is cheap. The failure cost is a form that appears labeled only until the first keystroke. Placeholder text can also have lower contrast and may not be announced consistently as instructions. Keep a persistent label, visible help where needed, and a real error message. Do not infer that an empty-looking field has no value merely from its border color; autofill and programmatic values can change the state. Verify both browser-managed and application-managed form updates with actual interaction tests.",
    ["Do not use placeholder text as the only label.", "Do not treat placeholder-shown as a validation result.", "Do not hide formatting instructions once the user starts typing."],
    ["css/form-control-states", "css/pseudo-classes", "html/form-help-and-errors"])

add("user-invalid-feedback", "CSS user-invalid: delay visual errors until interaction warrants them",
    "Show an invalid border after user interaction while keeping error text authoritative.",
    "The user-invalid pseudo-class matches an invalid form control after the browser determines the user has interacted with it sufficiently to show a validation state. The exact timing depends on browser behavior.",
    "An email field may be technically invalid while the user has typed only the first few characters. Styling every intermediate keystroke as an error can distract from completing the address. Use user-invalid for a border after the browser exposes the state, but keep actual submission feedback in visible text associated with the field. The sample does not suppress the native validity model and does not make the border the sole message. Test typing, blur, correcting the value, browser autofill, and a failed server response. Server rules can reject an address that passes client constraints, so application errors need their own state and message rather than relying on a CSS pseudo-class alone.",
    ".billing-email { border: 2px solid #41637c; }\n.billing-email:user-invalid { border-color: #a12632; }\n.billing-email:focus-visible { outline: 3px solid #175b44; outline-offset: 2px; }",
    "Selector matching is inexpensive. The maintenance cost is coordinating native validity, application state, and server decisions without contradictory cues. The border color must be paired with a visible explanation or status, because color alone does not identify the problem. Do not assume all browsers reveal user-invalid at the same moment. If a control is optional or disabled, check its actual validity contract before styling it. Keep the submit path usable with a keyboard and test that the error remains discoverable after focus moves.",
    ["Do not use an invalid border as the only error message.", "Do not assume browser and server validation rules are identical.", "Do not expect the state to appear at one fixed keystroke across browsers."],
    ["css/form-control-states", "css/attribute-selectors", "html/aria-invalid-errors"])

add("autofill-state-styling", "CSS autofill state: retain contrast when the browser fills a control",
    "Test browser-filled values as a distinct form state instead of trying to erase them.",
    "The autofill pseudo-class matches an input whose value was filled by the browser, subject to browser rules. User editing can end that state, and user agents may restrict which autofill styles authors can override.",
    "A billing form can look correct during manual typing but unreadable when a browser fills saved details over a themed input. Keep a safe baseline of text, background, border, and focus styles. Use autofill only for a modest border cue rather than fighting the browser's protected foreground or background rendering. The sample preserves the normal border as fallback. Test saved data in more than one browser, both color schemes, and a focused autofilled field. Do not disable autofill just to avoid styling work; it saves time and supports many users. The form still needs labels, correct autocomplete tokens, and server validation of submitted values.",
    ".billing-field { border: 2px solid #41637c; color: #173148; background: #fff; }\n.billing-field:autofill { border-color: #175b44; }\n.billing-field:focus-visible { outline: 3px solid #175b44; outline-offset: 2px; }",
    "Autofill styling has negligible layout cost, but browser restrictions make screenshot-only review unreliable. Some user-agent styles cannot be overwritten with an ordinary declaration. Verify the actual filled text contrast and caret, not just the computed border color. A filled value is not automatically valid: dates, addresses, and account identifiers can be stale. Keep the validation path intact. Avoid overly specific hacks that depend on one browser's internal stylesheet; they can break when the browser updates or when forced colors are active.",
    ["Do not disable browser autofill to avoid a color mismatch.", "Do not assume an autofilled value is valid or current.", "Do not depend on overriding every user-agent autofill color."],
    ["css/caret-color-visibility", "css/form-control-states", "html/password-autocomplete-tokens"])

add("font-size-adjust-fallback", "CSS font-size-adjust: steady readable fallback text",
    "Match perceived lowercase size when a custom face is unavailable.",
    "Font-size-adjust influences the apparent size of fallback glyphs using a font metric such as x-height. It does not download a font or change the declared font-size by itself.",
    "An operations toolbar names a custom face first and a system fallback second. If the custom file is delayed, the fallback's lowercase letters may look much smaller at the same nominal size. Set an adjustment value only after measuring the chosen font pair and inspecting both renders. The sample uses a design-specific ratio that must be reviewed against the actual font asset; it is not a universal number. Test long action labels, narrow widths, zoom, and a blocked font request. A larger fallback may wrap more text, so leave flexible space in the toolbar. Font loading strategy and the fallback stack remain separate decisions.",
    ".operations-toolbar { font-family: 'Ledger Sans', system-ui, sans-serif; font-size: 1rem; font-size-adjust: 0.55; }",
    "The property has little ongoing runtime cost; the cost is choosing and validating an appropriate metric. A guessed value can make fallback text too large and increase layout movement rather than reducing it. Record the target font, fallback font, and measurement conditions in the design system. The browser may use different fallback fonts across platforms, so test common environments. Do not use font-size-adjust to force a branded face to load faster. Keep the interface readable when that face never loads, including buttons with two-line labels.",
    ["Do not copy a font-size-adjust ratio without measuring the font pair.", "Do not use it as a font-loading policy.", "Do not fix toolbar heights before testing larger fallback glyphs."],
    ["css/font-loading", "css/font-shorthand-stack", "css/line-height-and-measure"])

add("font-display-policy", "CSS font-display: choose what readers see while a font loads",
    "Declare a fallback-first behavior for a nonessential interface font.",
    "Font-display is a descriptor inside @font-face that influences the browser's font loading and swap periods. It controls presentation timing, not the file's size or whether the request succeeds.",
    "A receipt archive uses a custom heading face, but its titles must remain readable if the asset is slow or absent. Set a system fallback in the heading stack and choose an appropriate display policy for the face. The sample uses swap, which may show fallback text first and then replace it; that can cause a visible change in line breaks. The font URL is illustrative and must be replaced with a licensed, optimized asset before reuse. Test a slow connection, a blocked request, and a narrow title. Preloading every font file can waste bandwidth, so measure the few assets that matter to the first screen. Body copy may be better served by a stable system face.",
    "@font-face { font-family: 'Receipt Header'; src: url('/assets/receipt-header.woff2') format('woff2'); font-display: swap; }\n.receipt-archive__title { font-family: 'Receipt Header', system-ui, sans-serif; }",
    "The expensive part is the font transfer and any layout shift when the face replaces fallback glyphs. Font-display does not eliminate those costs. Check the file's subset, compression, cache behavior, and actual use before loading it site-wide. Licensing must permit web embedding. A fallback stack should produce sensible weight and line breaks, and critical text must not remain invisible just to preserve a visual brand. Compare several display policies under realistic network conditions instead of assuming one value is correct for every font role.",
    ["Do not ship the illustrative font path or an unlicensed asset.", "Do not assume swap prevents layout shifts.", "Do not load a custom face for every small icon or number."],
    ["css/font-loading", "css/font-size-adjust-fallback", "css/readable-type"])

add("balanced-heading-wrap", "CSS text-wrap balance: improve short headings without truncation",
    "Balance a short title's lines while preserving its full text at every width.",
    "Text-wrap balance asks the browser to distribute text more evenly across lines. It is intended for short text, such as headings, rather than long passages with many possible line breaks.",
    "A case summary heading can leave a single short word on its last line at medium width. Balance its wrapping so the lines read as a deliberate title, but retain the full string and let the container grow vertically. The sample applies the property only to the heading and limits the measure; unsupported browsers keep ordinary wrapping. Test a one-line title, a long translated title, and zoom above the default. Do not combine balance with a fixed height or hidden overflow, since that can cut off the title. If an exact wording must fit one line in a compact control, edit the label or layout rather than relying on a balancing algorithm to rescue it.",
    ".case-summary__heading { max-inline-size: 28ch; text-wrap: balance; }",
    "Balancing can require the browser to evaluate alternate line breaks, so scope it to short strings rather than every paragraph in a large feed. The layout can change when fonts load; inspect the intended and fallback faces. A balanced heading may occupy more vertical space than a tightly packed one, which is preferable to clipping but must be accommodated by the card. Test the title in source order and with assistive technology as ordinary text. Text-wrap does not change the underlying words or provide a shorter accessible name.",
    ["Do not apply balance to every long paragraph.", "Do not pair it with fixed height and hidden overflow.", "Do not use it to avoid writing a clear short control label."],
    ["css/text-wrapping-and-truncation", "css/line-height-and-measure", "css/font-size-adjust-fallback"])

add("tab-size-code-blocks", "CSS tab-size: render source indentation without rewriting code",
    "Keep pasted tabs readable in a preformatted diagnostic excerpt.",
    "Tab-size controls the rendered width of tab characters in preserved whitespace. It does not convert tabs to spaces in the source text or change what a user copies.",
    "An incident report includes a short diagnostic excerpt supplied by an engineer. If the excerpt contains tab characters, the browser's default width can push a line off-screen. Set a smaller tab size on the preformatted code region and allow horizontal scrolling rather than wrapping tokens unpredictably. The sample leaves surrounding prose untouched. Test actual tab characters, spaces, a very long line, and mobile width. Do not assume the displayed indentation proves the pasted source was formatted consistently; mixed spaces and tabs can still align badly. If the code is executable, syntax and security checks belong elsewhere. The lesson body should label the excerpt clearly and avoid using indentation as the only cue for meaning.",
    ".diagnostic-excerpt { tab-size: 3; white-space: pre; overflow-x: auto; max-inline-size: 100%; }",
    "Rendering a different tab width is cheap. The maintenance cost is mismatch between what readers see and what they paste into an editor with another tab setting. State the source convention when it matters, and preserve the raw text for copying. Horizontal scrolling can hide a line's end, so keep a visible scroll affordance and inspect keyboard access. Do not use CSS to disguise malformed indentation in an official record. A code viewer with line numbers may need separate semantics and controls, not a larger tab-size value.",
    ["Do not assume tab-size changes copied source text.", "Do not hide the end of a long line without a scroll route.", "Do not use visual indentation to conceal mixed tabs and spaces."],
    ["css/overflow-and-scroll", "css/readable-type", "html/preformatted-code-and-output"])

add("scrollbar-width-access", "CSS scrollbar-width: keep scrolling discoverable",
    "Use thinner scrollbars sparingly and preserve an obvious path to hidden content.",
    "Scrollbar-width requests an automatic, thin, or hidden scrollbar on a scrolling box. The browser retains control over the actual appearance, and a hidden scrollbar does not remove the box's scrolling behavior.",
    "A narrow audit side panel has many records. A thin scrollbar can save a little inline space, but the control must remain visible enough to suggest more content, especially for mouse users who do not know the panel scrolls. The sample keeps overflow auto and applies thin only to that panel. Test classic and overlay scrollbar systems, touch, keyboard page scrolling, and forced colors. Do not set scrollbar-width none merely for a clean screenshot; it can make a second scroll region difficult to discover. If the panel needs more space, first inspect whether a better layout or wider container would solve the problem without altering a system affordance.",
    ".audit-side-panel { max-block-size: 32rem; overflow-y: auto; scrollbar-width: thin; }",
    "The style is inexpensive, but smaller targets can be harder to use. Browser and operating-system settings may override appearance, so never rely on an exact pixel width in a layout calculation. A thin scrollbar does not provide a focus cue for items inside the panel. Keep the region keyboard reachable and make clipped content discoverable with visible structure or an explicit label. Validate at zoom and with long localized row names. If user testing finds the thin affordance difficult, return to auto rather than forcing a custom scrollbar design.",
    ["Do not hide a scrollbar merely to improve a screenshot.", "Do not assume a fixed physical width across browsers.", "Do not trade away a usable pointer target to gain a few pixels."],
    ["css/scrollbar-gutter-stability", "css/overflow-and-scroll", "css/data-table-layout"])

add("forced-color-adjust-exceptions", "CSS forced-color-adjust: preserve a color only for a narrow reason",
    "Allow system colors to govern controls while keeping an optional swatch identifiable.",
    "Forced-color-adjust controls whether the browser may replace an element's colors in forced-colors mode. The default auto lets the system palette take effect; none opts an element out of that adjustment.",
    "A status legend has a small color swatch followed by a text label. In forced colors, keep the label and control surfaces under the system palette. If the exact swatch hue is useful for a secondary comparison, an opt-out may be appropriate only on that tiny swatch, with a visible border and text that still names the status. The sample scopes none to the decorative square. Test every forced-color theme available to the team; the chosen hue may have poor contrast against a system background. Never opt the whole card or form out just to protect brand colors. Forced colors are an access setting, not a theme defect to override.",
    "@media (forced-colors: active) { .status-key__swatch { forced-color-adjust: none; border: 2px solid CanvasText; } }",
    "A narrow opt-out has negligible rendering cost, but it creates a manual contrast responsibility. The browser will not repair a preserved swatch that disappears into its surroundings. Keep the status name in adjacent text and avoid relying on hue alone. Test focus rings, links, error states, and disabled controls with the default auto behavior. If the color comparison has no essential value, remove the opt-out and let the system palette handle the entire component. Do not assume one high-contrast screenshot covers all user palettes.",
    ["Do not set forced-color-adjust none on whole forms or dialogs.", "Do not convey status solely through a preserved swatch.", "Do not skip contrast review in multiple system palettes."],
    ["css/dark-mode-and-forced-colors", "css/colors-and-contrast", "css/form-control-states"])

add("prefers-contrast-boundaries", "CSS prefers-contrast: strengthen an already readable interface",
    "Increase separation when a user asks for more contrast without making the base state weak.",
    "The prefers-contrast media feature reports a user's contrast preference when the platform exposes one. The more value can select stronger borders or other adjustments, while forced-colors is a related but separate environment.",
    "A case review card already has readable text and a visible border. Under a higher-contrast preference, increase the border weight and remove a faint decorative shadow that adds noise. The sample changes only that card; links and focus rings need their own review. Do not make the default contrast poor and expect the media query to rescue users. Some platforms may not expose the preference as expected, so the baseline must stand on its own. Test more contrast, no preference, dark mode, forced colors, and high zoom. A media query cannot tell you whether a particular text/background pair actually passes a measured contrast threshold.",
    ".case-review-card { border: 1px solid #41637c; box-shadow: 0 2px 8px rgb(23 49 72 / 12%); }\n@media (prefers-contrast: more) { .case-review-card { border-width: 3px; box-shadow: none; } }",
    "The extra border has little rendering cost but may reduce inner space in a fixed-width card, so use border-box sizing if dimensions are tight. Review every state of an interactive component rather than only its resting screenshot. Preference matching varies by user environment and does not guarantee the same outcome as forced colors. Keep semantic status labels in text and avoid using contrast changes to indicate a new business state. Verify the computed colors and borders on the actual surfaces, including disabled and selected cards.",
    ["Do not let the default presentation fail contrast checks.", "Do not equate prefers-contrast with every forced-color setting.", "Do not use border strength as the only status indicator."],
    ["css/colors-and-contrast", "css/dark-mode-and-forced-colors", "css/borders-vs-outlines"])


assert len(specs) == 12 and len({spec["path"] for spec in specs}) == len(specs)
titles = {path: row["title"] for path, row in by_path.items()}
titles.update({spec["path"]: spec["title"] for spec in specs})
titles[quiz_path] = "CSS forms, type, and contrast decisions quiz"


def links(paths):
    assert all(path in titles for path in paths), paths
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in paths
    ) + "</ul>"


hub = by_path[hub_path]
hub["data"]["modules"].append({
    "title": "Forms, type, and contrast",
    "summary": "Keep controls readable, text stable, and user preference overrides narrow.",
    "lessons": [spec["path"] for spec in specs],
})
hub["body"] += "<h2>Forms, type, and contrast</h2>" + links([spec["path"] for spec in specs])
hub["updated_at"] = stamp

for index, spec in enumerate(specs):
    path = spec["path"]
    assert all(target in titles for target in spec["related"]), path
    row = copy.deepcopy(by_path["css/selectors-and-cascade"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)),
               path=path, title=spec["title"], summary=spec["summary"],
               subject="css-reference", sort_order=24042 + index,
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
    "css/form-control-states": ["css/field-sizing-controls", "css/placeholder-shown-state", "css/user-invalid-feedback", "css/autofill-state-styling"],
    "css/focus-visible": ["css/caret-color-visibility"],
    "css/font-loading": ["css/font-size-adjust-fallback", "css/font-display-policy"],
    "css/text-wrapping-and-truncation": ["css/balanced-heading-wrap"],
    "css/readable-type": ["css/tab-size-code-blocks"],
    "css/overflow-and-scroll": ["css/scrollbar-width-access"],
    "css/dark-mode-and-forced-colors": ["css/forced-color-adjust-exceptions", "css/prefers-contrast-boundaries"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Further form and type decisions</h2>" + links(targets)
    row["data"].setdefault("related", []).extend(
        {"path": target, "title": titles[target]} for target in targets
    )
    row["updated_at"] = stamp

questions = [
    ("What limits a content-sized textarea?", ["Minimum and maximum size constraints", "Only the placeholder", "The caret color"], 0, "Bounds keep the field useful when empty and prevent unlimited growth."),
    ("What does caret-color change?", ["The insertion caret", "The selection highlight", "The accessible label"], 0, "Caret color does not replace the focus ring or selection styling."),
    ("What does placeholder-shown indicate?", ["Placeholder text is currently displayed", "The field was validated", "The server accepted the value"], 0, "The selector describes a display state, not validation."),
    ("Why use user-invalid rather than invalid for a typing state?", ["To avoid showing an error during every intermediate keystroke", "To skip server validation", "To hide the error text"], 0, "User-invalid waits for browser-defined user interaction before matching."),
    ("What should an autofill style preserve?", ["Readable text and focus states", "A ban on saved values", "Only a browser-specific color hack"], 0, "Autofill helps users, and its filled state still needs readable controls."),
    ("What should determine a font-size-adjust value?", ["Measurement of the intended and fallback fonts", "A copied universal ratio", "The number of toolbar buttons"], 0, "The useful ratio depends on font metrics and the target layout."),
    ("What does font-display control?", ["Font loading presentation periods", "The downloaded font file size", "The font license"], 0, "It changes how text is displayed while a face loads, not the bytes or rights."),
    ("Where is text-wrap balance usually appropriate?", ["A short heading", "Every long report paragraph", "A hidden fixed-height label"], 0, "Balancing short text can improve line distribution without clipping it."),
    ("What does tab-size change?", ["Rendered width of tab characters", "Copied tabs into spaces", "Syntax validation"], 0, "Source characters remain unchanged."),
    ("What is a risk of scrollbar-width none?", ["The scroll region becomes hard to discover", "The content is deleted", "The page gains a label"], 0, "Scrolling may remain possible while its visual affordance disappears."),
    ("Where might forced-color-adjust none be justified?", ["A narrow optional swatch with text beside it", "The entire payment form", "All focus rings"], 0, "Keep opt-outs narrow and preserve system colors for controls."),
    ("What must the baseline do before a prefers-contrast rule applies?", ["Remain readable on its own", "Hide errors until preference is known", "Remove borders from all controls"], 0, "Preference rules strengthen a usable base rather than repairing an unusable one."),
]
assert len(questions) == 12
quiz = copy.deepcopy(by_path["quizzes/css-advanced"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
            path=quiz_path, title=titles[quiz_path],
            summary="Twelve applied checks on form states, font fallback, text, and contrast.",
            sort_order=3105, status="published", published_at=stamp,
            created_at=stamp, updated_at=stamp)
quiz["data"] = {
    "subject_root": "css/css-tutorial", "section_path": "css/quizzes",
    "content_format": "html", "author_path": "authors/aitrove-editorial",
    "seo_ready": True, "duration_minutes": 12,
    "related": [{"path": target, "title": titles[target]} for target in [
        "css/field-sizing-controls", "css/user-invalid-feedback",
        "css/font-size-adjust-fallback", "css/forced-color-adjust-exceptions"]],
    "questions": [dict(prompt=prompt, options=options, answer=answer, explanation=explanation)
                  for prompt, options, answer, explanation in questions],
}
quiz["body"] = (
    "<p>Decide which styling choice preserves a form or reading task, then compare the result with a real browser state.</p>"
    "<h2>Review the lessons</h2>" + links([item["path"] for item in quiz["data"]["related"]])
    + "<h2>Other checks</h2>" + links(["css/quizzes", "quizzes/css-rendering-decisions"])
    + "<h3>Common Mistakes</h3><ul><li>Do not treat a border color as a complete error message.</li>"
    "<li>Do not assume a font metric or contrast preference behaves identically across browsers.</li></ul>"
)
rows.append(quiz)
quiz_hub = by_path["css/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Forms and type check</h2>" + links([quiz_path])
quiz_hub["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_quizzes": 1,
                  "total_records": len(rows)}))

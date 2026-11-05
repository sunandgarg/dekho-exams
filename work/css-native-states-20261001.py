"""Add CSS lessons about native controls, filtered siblings, and caption paint."""

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
quiz_path = "quizzes/css-native-states"
specs = []


def add(slug, title, summary, definition, decision, sample, cost, mistakes, related):
    path = "css/" + slug
    assert path not in by_path
    specs.append(dict(path=path, title=title, summary=summary, definition=definition,
                      decision=decision, sample=sample, cost=cost, mistakes=mistakes,
                      related=related))


add(
    "file-selector-button-native",
    "CSS ::file-selector-button: style the picker without replacing it",
    "Keep the native file input and its selected-file text while styling the picker control.",
    "The ::file-selector-button pseudo-element addresses the button inside a file input. It can style that button without removing the input, its keyboard behavior, or the platform file picker. It does not style the adjacent filename text, validate the file, or upload bytes.",
    "A claims desk accepts a supporting document. The file input has a visible label and stays in the form, while the picker button gets a modest border, padding, and color that fit the surrounding controls. Keep the control's own filename display so the reviewer can see what was chosen. Test a long filename, no file chosen, multiple selected files, keyboard focus, touch selection, high zoom, and forced colors. The button text can vary by browser and locale, so do not size the button for one English phrase. The input's focus-visible outline belongs on the input as a whole; a hover color on the internal button is only an extra pointer cue. Accept is only a picker hint. The server must check type, size, and content before storing evidence. If a custom upload workflow is needed, implement it deliberately in application code instead of hiding the native input and pretending a painted span is a form control.",
    '.evidence-upload { font: inherit; color: #173441; max-inline-size: 100%; }\n.evidence-upload::file-selector-button { font: inherit; padding: .55rem .8rem; margin-inline-end: .7rem; border: 1px solid #426375; border-radius: .3rem; background: #edf4f7; color: #173441; }\n.evidence-upload:focus-visible { outline: 3px solid #1c5e87; outline-offset: 3px; }',
    "The style rule is cheap. The practical cost is platform testing: browser chrome around the filename and the button may differ, and file pickers remain system UI. Avoid a fixed inline width that truncates a localized button label or hides the selected filename. A native input can expose its label and chosen file without extra JavaScript; removing it often creates more work and more accessibility failures. Test the no-CSS state and verify that a file can still be selected and submitted. CSS cannot scan content, show upload progress, or recover from a rejected server response; those behaviors require a real backend and visible messages.",
    ["Do not hide the input just to draw a button-shaped replacement.", "Do not treat accept or the button color as file validation.", "Do not clip long chosen filenames without another way to inspect them."],
    ["css/form-control-states", "css/focus-visible", "css/form-appearance-accent", "html/file-upload-form"],
)

add(
    "read-only-control-state",
    "CSS :read-only: distinguish fixed values from disabled controls",
    "Style an immutable field while preserving its actual form and focus behavior.",
    "The :read-only pseudo-class matches elements whose contents cannot be changed by the user. It is broader than an input carrying readonly; ordinary noneditable elements can match too. Scope a form rule to the intended input or textarea. CSS cannot make a value authoritative merely by painting it as fixed.",
    "A shipment audit form shows a registered parcel code that the reviewer may inspect and copy but cannot edit in that request. The HTML field uses readonly, and CSS gives it a restrained surface distinct from an editable note. The browser can still focus a read-only text control and can submit its value, unlike a disabled control. Keep a proper label and an explanation of why the field is fixed. Test Tab order, text selection, copy, forced colors, server submission, and a programmatic change attempted outside the UI. Server code must read the authoritative parcel record rather than trust any submitted value. Do not apply a broad :read-only selector to every div and paragraph, since those are usually noneditable and could all receive the field treatment. If a control truly should not participate in a submission, choose the right HTML state before styling it.",
    '.shipment-review input:read-only, .shipment-review textarea:read-only { background: #edf3f5; border: 1px solid #6b818c; color: #173441; }\n.shipment-review input:read-write, .shipment-review textarea:read-write { background: #fff; border: 1px solid #426375; }\n.shipment-review :focus-visible { outline: 3px solid #1c5e87; outline-offset: 2px; }',
    "The selectors have trivial cost. Maintenance risk comes from confusing state, semantics, and security. Readonly is supported only by certain controls; setting the attribute on a select does not create an equivalent fixed selection. A muted background can look disabled, so verify that users still understand the field can be focused and copied. Avoid reducing contrast with opacity. Read-only fields are not validated like ordinary editable required fields, and a client can still modify requests. CSS neither enforces the state nor protects the server. Test the actual rendered control across browsers and keep the visual difference secondary to the text label and native behavior.",
    ["Do not use an unscoped :read-only rule across the document.", "Do not confuse readonly submission with disabled omission.", "Do not treat CSS or a readonly attribute as server authorization."],
    ["css/form-control-states", "css/focus-visible", "html/readonly-vs-disabled"],
)

add(
    "indeterminate-checkbox-state",
    "CSS :indeterminate: show a mixed selection without inventing its meaning",
    "Style the native mixed checkbox state after application code has set it.",
    "The :indeterminate pseudo-class can match a checkbox whose indeterminate property is true. That property is set through application code, not an HTML attribute. The mixed visual state is independent of checked; it does not submit a third checkbox value or decide which child records are selected.",
    "A batch review panel offers a parent checkbox for 27 claims. Some claims are selected, so application code sets the parent's indeterminate property and updates a nearby text count. CSS emphasizes the native checkbox and its adjacent label without replacing the checkbox glyph. When every claim is selected, the code sets checked and clears indeterminate; when none are selected, it clears both. Test pointer and keyboard toggles, a selection changed elsewhere in the UI, a rerender that replaces the input node, and form submission. The native checkbox may leave the mixed state when activated, so the application must recompute it from its children. A screen reader needs a meaningful name and the current mixed state from the control; a border color cannot explain which records are selected. Keep the count as real text, not generated content. Never assume that an indeterminate parent means the backend has approved a partial batch.",
    '.batch-review input[type="checkbox"]:indeterminate { accent-color: #175f84; }\n.batch-review input[type="checkbox"]:indeterminate + label { font-weight: 700; color: #173f56; }\n.batch-review input[type="checkbox"]:focus-visible { outline: 3px solid #1c5e87; outline-offset: 3px; }',
    "The paint cost is negligible. The larger cost is keeping the DOM property synchronized with actual selection state after every update. CSS cannot compute the number of selected children or change a checkbox's submitted value. Some high-contrast systems override accent-color; the native mixed mark and the text count must remain usable. Avoid drawing a custom dash with a pseudo-element unless the entire control replacement has been tested across input methods and assistive technology. If the batch contains no eligible items, disable or explain the parent control through HTML and logic rather than styling it as merely pale.",
    ["Do not expect an indeterminate HTML attribute to set the state.", "Do not treat mixed appearance as a third submitted value.", "Do not omit the textual selection count and real state synchronization."],
    ["css/form-appearance-accent", "css/form-control-states", "html/radio-checkbox"],
)

add(
    "default-submit-selector",
    "CSS :default: mark the form's default action, not the last clicked button",
    "Use the default-state selector only after the form's submit order is intentional.",
    "The :default pseudo-class matches a default element in a related group. For a form, a submit button can match as its default submitter; checked-by-default radio buttons and options can match too. It is not the same as :checked or :focus, and clicking another button does not turn that button into the default.",
    "A review form has Save draft and Send for approval actions. The first associated submit button is the form's default action, so the product team must decide whether pressing Enter from a text field should save or send. Put the safer Save draft action first in document order, give both controls explicit type and name values, and style only the default submitter inside this form. Test Enter from each text field, pointer activation of each button, disabled states, a button associated through form ID outside the form subtree, and the server's handling of each submitted name-value pair. CSS cannot change which action Enter triggers. If order is wrong, fix the HTML and request handling; a visual border on Send for approval would only mislead. Also verify that a button of another type placed first does not create an accidental assumption about default submission.",
    '.review-actions button[type="submit"] { border: 2px solid #6b818c; background: #fff; color: #173441; }\n.review-actions button[type="submit"]:default { border-color: #1c5e87; background: #e6f2f8; }\n.review-actions button:focus-visible { outline: 3px solid #1c5e87; outline-offset: 2px; }',
    "The selector is inexpensive, but the action has a high correctness cost if the form order and server contract are unclear. Do not rely on color alone to explain what a button does: the visible text must name the action. A default button can still be disabled, and the styling must not suggest it is available when it is not. A broad :default rule may also catch radio inputs or options, so scope the selector to submit buttons in the intended component. Test real keyboard submission rather than inferring behavior from a screenshot. Server authorization and validation remain mandatory regardless of which submitter was used.",
    ["Do not use :default as a synonym for the last clicked control.", "Do not paint a different action as default while HTML order says otherwise.", "Do not forget explicit button types and server-side action checks."],
    ["css/form-control-states", "css/focus-visible", "html/button-type-default", "html/submitter-name-value"],
)

add(
    "required-optional-control-state",
    "CSS :required and :optional: reinforce a real form requirement",
    "Use native requirement state for a secondary cue while keeping visible instructions.",
    "The :required pseudo-class matches controls with a native required state, and :optional matches supported controls without that requirement. They describe form constraints; neither selector supplies a label, a validation error, or a server rule. ARIA-only required wording does not create native :required matching.",
    "An evidence intake form requires a case code and leaves a reviewer note optional. The labels say which fields are required in words, and the CSS adds a narrow border accent to the required controls. The accent is supplementary because color can disappear in forced colors and a border alone does not explain the requirement. Test an empty submission, a partially filled form, an invalid code, a server rejection, and a no-CSS rendering. Required status differs from validity: an untouched required field can be invalid before a user has acted, so do not show an alarming error border merely because :required matches. The form needs associated error text after validation and an authoritative server check. A disabled control and a readonly text field have different validation behavior; avoid mixing them into a generic required rule without reviewing the actual HTML. Keep optional wording visible when omitting a value has a practical consequence.",
    '.evidence-intake :is(input, select, textarea):required { border-inline-start: .25rem solid #1c5e87; }\n.evidence-intake :is(input, select, textarea):optional { border-inline-start: .25rem solid #9aaeb8; }\n@media (forced-colors: active) { .evidence-intake :is(input, select, textarea):required { border-inline-start-color: CanvasText; } }',
    "Matching requirement state adds little rendering cost. The maintenance cost is keeping visible labels, native attributes, validation messaging, and server rules consistent as a form changes. Do not generate a required asterisk solely through ::after: generated content is not a reliable replacement for a clear label. Use a neutral base border so a control remains visible when the accent is absent. The optional selector does not mean a value is unimportant; it only means native constraint validation does not require one. Test each input type because required has no useful effect on some controls.",
    ["Do not confuse :required with :invalid or a submitted error.", "Do not use CSS-generated symbols as the only requirement instruction.", "Do not assume aria-required activates native validation."],
    ["css/form-control-states", "css/user-invalid-feedback", "html/required-vs-aria-required"],
)

add(
    "placeholder-text-contrast",
    "CSS ::placeholder: keep example text readable and disposable",
    "Style a short input example without turning it into a hidden label.",
    "The ::placeholder pseudo-element styles placeholder text inside an input or textarea. It is different from :placeholder-shown, which matches the control while that text is displayed. Placeholder text disappears as the user enters a value, so it cannot carry the only label or a required instruction.",
    "A case lookup field has a permanent visible label and a nearby format hint. Its placeholder offers one short sample code, shown in a color that remains legible on the field background and distinguishable from entered text. Set an explicit opacity because browser defaults vary. Test empty, focused, typed, autofilled, and error states; also test dark mode, forced colors, and high zoom. The example must not look like a saved value. Use real hint text outside the control for rules such as allowed characters or where to find the code, and associate that hint in HTML. Do not use placeholder text as a substitute for a label: once input begins, the user should still know the field's purpose. If a screen reader repeats the placeholder, the instruction should remain understandable without relying on its color or timing. A styling selector does not validate the sample format or parse submitted text.",
    '.case-lookup input { background: #fff; color: #173441; border: 1px solid #58707d; }\n.case-lookup input::placeholder { color: #506572; opacity: 1; }\n.case-lookup input:focus-visible { outline: 3px solid #1c5e87; outline-offset: 2px; }',
    "The paint cost is negligible. The design cost is contrast testing on the real input background and ensuring placeholder text is not mistaken for an existing value. A translucent default placeholder can fall below a readable contrast threshold even when the authored color looks strong in a code review. Do not solve that by making it identical to entered text without another clear distinction. Check system forced-color handling and keep label and hint text in the DOM. Placeholder content may be truncated on narrow fields, which is another reason to keep essential guidance outside. Server-side format checks and useful error messages remain separate from this presentation rule.",
    ["Do not use ::placeholder as the field label.", "Do not assume a default browser opacity is readable.", "Do not put the only format instruction inside vanishing text."],
    ["css/placeholder-shown-state", "css/colors-and-contrast", "css/form-control-states", "html/placeholder-vs-label"],
)

add(
    "nth-child-filtered-siblings",
    "CSS :nth-child(of selector): count only the rows that match",
    "Stripe visible list items after filtering without counting hidden siblings.",
    "The of selector form of :nth-child() filters the sibling list before applying its position formula. A plain :nth-child(even) counts all siblings, including elements hidden with the HTML hidden attribute. The selector only changes styling; it does not reorder or filter records.",
    "A claims queue marks withdrawn records with hidden while keeping them in the DOM for a temporary review filter. Alternating backgrounds should apply to the remaining visible list items in their current source order. The sample counts direct li children that are not hidden. If the of selector syntax is unsupported, the list stays readable without striping. Test zero, one, and many visible records; hide the first row and a middle row to confirm the parity shifts as expected. If the application instead hides rows through a class or CSS display none, this selector will still count them unless the filter matches that state; choose one source-of-truth convention. Do not use stripes to convey approval or urgency. Screen readers need meaningful row text and headings, and keyboard focus must not land on rows a filter claims are unavailable. Repeated DOM moves can cause layout and focus changes unrelated to this CSS rule.",
    '.claim-queue > li { background: #fff; }\n.claim-queue > li:nth-child(even of :not([hidden])) { background: #edf4f7; }\n.claim-queue > li:focus-within { outline: 2px solid #1c5e87; outline-offset: 2px; }',
    "Selector matching is cheap on an ordinary list. The main cost is reasoning about which siblings are counted after filtering and whether the hidden attribute is applied consistently. Avoid loading thousands of DOM rows merely because CSS can stripe them; paging or virtualization is an application decision, with its own accessibility work. Test target browsers for the of syntax, since older engines may ignore that rule and show a plain list. A fallback base background preserves readability. Do not substitute row parity for data state or rely on alternating color as the only separator when printed or viewed in forced colors.",
    ["Do not confuse li:nth-child(even of .active) with li.active:nth-child(even).", "Do not count a CSS-hidden class unless the filter selector accounts for it.", "Do not let a missed stripe change the meaning of a record."],
    ["css/structural-selectors", "css/attribute-selectors", "css/focus-within-group", "html/lists-and-definitions"],
)

add(
    "caption-cue-presentation",
    "CSS ::cue: improve caption contrast without editing the transcript",
    "Style displayed WebVTT cues conservatively while keeping their words and timing intact.",
    "The ::cue pseudo-element targets rendered WebVTT caption or subtitle cues for a media element. Only a restricted set of CSS properties applies to cue text. It does not create captions, correct timing, identify speakers, or guarantee that a third-party player will honor the stylesheet.",
    "A training clip includes an English captions track with speech and relevant sounds. The default cue rendering is hard to read over bright frames, so the player scope requests light text on a dark translucent background. Keep the underlying VTT content complete and provide a transcript route for someone who cannot use the video. Test captions over bright and dark footage, with native controls visible, at high zoom, in full screen, and on platforms with user caption preferences. The browser may prioritize a viewer's system settings, which is appropriate. Do not force an ornate typeface or tiny line-height to match branding. A caption should not obscure the only visual instruction in the frame; production work may need track positioning and video editing, beyond CSS. Verify the correct track language and that captions can be enabled by keyboard. If the track fails to load, paint cannot compensate for missing timed text.",
    '.training-clip::cue { color: #fff; background-color: rgb(12 30 42 / 88%); font-family: sans-serif; }\n@media (forced-colors: active) { .training-clip::cue { color: CanvasText; background-color: Canvas; } }',
    "The cue paint itself is small, but caption accessibility depends on the VTT file, language labels, sync, player support, and viewer settings. Test the actual target browsers instead of assuming every CSS declaration inside ::cue will apply; layout properties outside the allowed cue set may be ignored. A dark rectangle can improve contrast but may cover content if a cue is too long. Edit the caption text or cue breaks at the source when readability fails; do not shrink the font until the full sentence fits. CSS cannot add missing sound descriptions or replace a separate transcript. Keep user preferences in control of caption appearance where the platform exposes them.",
    ["Do not expect ::cue to generate captions or a transcript.", "Do not assume every ordinary CSS property applies to cue text.", "Do not override viewer preferences to preserve a brand treatment."],
    ["css/colors-and-contrast", "css/readable-type", "html/video-captions", "html/video-track-languages"],
)


assert len(specs) == 8
titles = {path: row["title"] for path, row in by_path.items()}
titles.update({item["path"]: item["title"] for item in specs})
titles[quiz_path] = "CSS native states and cue decisions quiz"


def links(paths):
    assert all(path in titles for path in paths), paths
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in paths
    ) + "</ul>"


hub = by_path[hub_path]
hub["data"]["modules"].append({
    "title": "Native controls and cue paint",
    "summary": "Style browser control states, filtered siblings, and timed-text paint without inventing behavior.",
    "lessons": [item["path"] for item in specs],
})
hub["body"] += "<h2>Native controls and cue paint</h2>" + links([item["path"] for item in specs])
hub["updated_at"] = stamp

for index, item in enumerate(specs):
    row = copy.deepcopy(by_path["css/selectors-and-cascade"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + item["path"])),
               path=item["path"], title=item["title"], summary=item["summary"],
               subject="css-reference", sort_order=24100 + index,
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
    "css/form-control-states": ["css/file-selector-button-native", "css/read-only-control-state", "css/required-optional-control-state"],
    "css/form-appearance-accent": ["css/indeterminate-checkbox-state"],
    "css/focus-visible": ["css/default-submit-selector"],
    "css/placeholder-shown-state": ["css/placeholder-text-contrast"],
    "css/structural-selectors": ["css/nth-child-filtered-siblings"],
    "css/readable-type": ["css/caption-cue-presentation"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Further native-state decisions</h2>" + links(targets)
    row["data"].setdefault("related", []).extend(
        {"path": target, "title": titles[target]} for target in targets
    )
    row["updated_at"] = stamp

questions = [
    ("What does ::file-selector-button style?", ["The file input's picker button", "The selected filename text", "The uploaded file bytes"], 0, "The native control and its filename presentation remain in place."),
    ("Which check cannot be delegated to CSS or accept?", ["Server file validation", "Button border painting", "Input focus outline"], 0, "The server must inspect the received file."),
    ("Why scope :read-only to form controls?", ["Many ordinary noneditable elements can match it", "It only matches disabled buttons", "It changes the server record"], 0, "The pseudo-class is broader than a readonly input attribute."),
    ("How is a checkbox's mixed state set?", ["Application code sets its indeterminate property", "A CSS color declaration sets it", "An HTML indeterminate attribute sets it"], 0, "The mixed state is a DOM property."),
    ("What does :default mean for a submit button?", ["It is the form's default submitter", "It was last clicked", "It is currently focused"], 0, "Default submission is a form behavior, not pointer history."),
    ("What does :required identify?", ["A control with native required state", "A field rejected by the server", "Any control with aria-required only"], 0, "The selector follows native constraint state."),
    ("What disappears after typing in a field?", ["Placeholder text", "Its persistent label", "The submitted value"], 0, "Placeholder text cannot hold the only instruction."),
    ("What does :nth-child(even of :not([hidden])) count?", ["Only siblings without the hidden attribute", "All siblings regardless of hidden", "Only currently focused siblings"], 0, "The of selector filters the sibling list before counting."),
    ("What happens if older CSS ignores the filtered nth-child syntax?", ["The base readable list remains unstriped", "The records are deleted", "The list order reverses"], 0, "Striping is optional presentation."),
    ("What does ::cue require before it can show useful text?", ["A real timed-text track", "Only a box shadow", "A border on the video"], 0, "CSS cannot create missing captions."),
    ("What should be checked when styling cues?", ["Actual video frames and viewer caption preferences", "Only a static blank player", "Only the CSS parser"], 0, "Caption contrast and placement depend on footage and platform rendering."),
    ("What remains authoritative for a read-only field?", ["The server's stored record and checks", "The field background color", "The submitted string alone"], 0, "Client requests can be modified outside the UI."),
]
assert len(questions) == 12
quiz = copy.deepcopy(by_path["quizzes/css-advanced"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
            path=quiz_path, title=titles[quiz_path],
            summary="Twelve checks on native controls, filtered selectors, and caption presentation.",
            sort_order=3110, status="published", published_at=stamp,
            created_at=stamp, updated_at=stamp)
quiz["data"] = {
    "subject_root": "css/css-tutorial", "section_path": "css/quizzes",
    "content_format": "html", "author_path": "authors/aitrove-editorial",
    "seo_ready": True, "duration_minutes": 12,
    "related": [{"path": target, "title": titles[target]} for target in [
        "css/file-selector-button-native", "css/indeterminate-checkbox-state",
        "css/nth-child-filtered-siblings", "css/caption-cue-presentation"]],
    "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                       answer=(answer - index % 3) % 3, explanation=explanation)
                  for index, (prompt, options, answer, explanation) in enumerate(questions)],
}
quiz["body"] = (
    "<p>Check what CSS can style around native control state, filtered sibling positions, and WebVTT cues. Each question has one answer and an explanation.</p>"
    "<h2>Review the decisions</h2>" + links([item["path"] for item in quiz["data"]["related"]])
    + "<h2>Other checks</h2>" + links(["css/quizzes", "quizzes/css-type-overlay"])
    + "<h3>Common Mistakes</h3><ul><li>Do not mistake paint for validation or submitted state.</li>"
    "<li>Do not omit a caption track because a cue style exists.</li></ul>"
)
rows.append(quiz)
quiz_hub = by_path["css/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Native-state check</h2>" + links([quiz_path])
quiz_hub["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_quizzes": 1,
                  "total_records": len(rows)}))

"""Add high-value HTML contracts and complete-page exercises to preview content."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path


root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
rows = json.loads(fixture.read_text())
by_path = {entry["path"]: entry for entry in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
lessons = []


def add(slug, section, title, definition, case, sample, boundary, cost, mistakes, links):
    lessons.append((slug, section, title, definition, case, sample, boundary, cost, mistakes, links))


add("fieldset-and-legend", "forms", "HTML fieldset and legend: name a group before its choices",
    "Fieldset groups related controls, and its first legend gives the group a name.",
    "A dispatch form asks how a damaged parcel should be handled. The three radio labels identify individual actions; the legend asks the shared question they answer. Without that group name, a reader moving control by control can hear an action without its context. A fieldset is also useful for repeated address fields where the same label appears in two groups. Keep legends short enough to be understood when repeated alongside each control label.",
    '''<form action="/parcels/P-47/handling" method="post">
  <fieldset>
    <legend>How should parcel P-47 be handled?</legend>
    <label><input type="radio" name="handling" value="inspect" required> Inspect at depot</label>
    <label><input type="radio" name="handling" value="return"> Return to sender</label>
    <label><input type="radio" name="handling" value="hold"> Hold for review</label>
  </fieldset>
  <button type="submit">Save handling decision</button>
</form>''',
    "The browser submits one selected handling value. The server must check that the value is allowed for this parcel and the current user's role; the fieldset does not enforce business permission or persistence.",
    "The native group adds little markup and no script. Its main maintenance cost is keeping the question, options, and server's allowed values aligned when operational policy changes.",
    ["Do not rely on three standalone radio labels to explain the shared question.", "Do not use fieldset only for a visual border.", "Do not treat required as server-side authorization."],
    ["html/radio-checkbox", "html/form-labels", "html/form-validation", "html/disabled-fieldset"])

add("number-input-or-text", "forms", "HTML number or text input: choose by the value, not its digits",
    "Number input is suited to numeric quantities; digit-only identifiers are still text.",
    "A stock intake screen has a count and a parcel code. The count can be incremented, compared, and bounded. The code may begin with zero and must retain every character exactly, so text with a numeric keyboard hint is a better fit. A browser may present number controls using the user's locale while submitting a normalized value, but it does not know the warehouse's maximum safe quantity. Keep the server's quantity rule separate from the UI control.",
    '''<form action="/stock/intake" method="post">
  <label for="received-units">Units received</label>
  <input id="received-units" name="units" type="number" min="1" max="47" step="1" required>
  <label for="parcel-code">Six-digit parcel code</label>
  <input id="parcel-code" name="parcel_code" type="text" inputmode="numeric" pattern="[0-9]{6}" required>
  <button type="submit">Record intake</button>
</form>''',
    "The parcel code remains a string even when all six characters are digits. The server must reject missing, fractional, or out-of-range quantities and verify the code against its own records.",
    "Native controls avoid a custom widget. Validation and conversion cost little for two fields, but bad type selection can corrupt leading zeroes or produce confusing mobile input and error handling.",
    ["Do not use type=number for postal codes or identifiers.", "Do not assume inputmode validates a text field.", "Do not accept a quantity solely because the browser allowed it."],
    ["html/input-types", "html/input-pattern", "html/autocomplete-and-inputmode", "html/form-validation"])

add("focus-order-tabindex", "accessibility", "HTML tabindex: keep focus order aligned with reading order",
    "Tabindex can make an element focusable or affect its place in sequential keyboard navigation.",
    "An inspection page includes a short in-page link to its findings. The link and form controls already receive keyboard focus in document order. The findings heading can use tabindex=-1 as a programmatic focus target after a navigation action, without becoming another routine Tab stop. Positive tabindex values would pull controls ahead of nearby text and make the page hard to understand. Arrange the DOM in a useful order before considering any focus override.",
    '''<main>
  <h1>Inspection I-47</h1>
  <p><a href="#findings">Skip to findings</a></p>
  <section aria-labelledby="findings">
    <h2 id="findings" tabindex="-1">Findings</h2>
    <p>The seal code matches the intake record.</p>
    <a href="/inspections/I-47/evidence">Open evidence list</a>
  </section>
</main>''',
    "The fragment target already supports navigation. Tabindex=-1 makes a heading focusable by script without adding it to ordinary sequential focus; browser fragment behavior may vary and should be tested on the target devices.",
    "The attribute costs no network bytes worth measuring. The expensive failure is a positive-tabindex sequence that must be maintained every time controls are added, removed, or rearranged.",
    ["Do not assign positive tabindex to repair a poor DOM order.", "Do not make every heading a Tab stop.", "Do not assume visual order matches keyboard order after CSS rearrangement."],
    ["html/focus-and-native-controls", "html/skip-link", "html/anchors-and-paths"])

add("form-help-and-errors", "accessibility", "HTML form help: connect visible instructions and errors to a control",
    "Aria-describedby connects a control to descriptive text in the same document while its label still names the field.",
    "A technician enters a calibrated sensor code. The instruction defines its format, and a server rejection appears below the field when the code is not in the registry. Both messages have IDs referenced by the input, so they stay attached when someone moves focus directly to the control. The sample shows the rejected state intentionally; after a correction, the application must update the visible error, the aria-invalid state, and the description references together.",
    '''<form action="/sensors/register" method="post">
  <label for="sensor-code">Sensor code</label>
  <p id="sensor-help">Use the eight-character code printed on the housing.</p>
  <input id="sensor-code" name="sensor_code" aria-describedby="sensor-help sensor-error" aria-invalid="true" value="SR-47" required>
  <p id="sensor-error">That code is not in the calibrated sensor registry.</p>
  <button type="submit">Check sensor</button>
</form>''',
    "The description does not validate the code or make the error visible automatically. A server must decide whether the code exists; a client-rendered state must ensure both referenced IDs remain present while the error is announced.",
    "Two short text nodes have little load cost. The difficult work is state synchronization: stale errors and dangling ID references create misleading feedback after edits or asynchronous validation.",
    ["Do not replace the field label with only a help paragraph.", "Do not leave aria-invalid=true after a corrected value is accepted.", "Do not reference an ID absent from the rendered document."],
    ["html/form-labels", "html/form-validation", "html/live-status", "html/global-attributes"])

add("anchor-referrer-policy", "core", "HTML link referrer policy: control what a navigation reveals",
    "An anchor referrerpolicy value influences the Referer information sent when that link is followed.",
    "A support page links to a public claim glossary. The route is within the same application, yet the page may be reused when linking to another service that should not learn the current case URL. A no-referrer policy on the sensitive navigation is explicit and local to that link. It does not remove query parameters from the destination URL, hide the current page from scripts, or prevent the browser from recording history.",
    '''<p>Read the terminology before you submit a claim.</p>
<a href="/help/claim-terms" referrerpolicy="no-referrer">Open the claim terms</a>''',
    "The local route must exist. A destination can still infer information from the URL being requested and from its own logs, so avoid encoding secrets in either source or destination paths.",
    "The attribute adds no separate request. The cost is policy complexity: differing link-level, document-level, and response-header rules become hard to reason about unless the application has a clear privacy policy.",
    ["Do not assume no-referrer anonymizes the user.", "Do not put private tokens in the href and expect referrerpolicy to erase them.", "Do not use link-level policy inconsistently across sensitive pages."],
    ["html/anchors-and-paths", "html/new-tab-links", "html/metadata-title"])

add("alternate-language-links", "core", "HTML alternate language links: identify equivalent page versions",
    "A link element with rel=alternate and hreflang can identify a version of the current page for another language.",
    "A public safety notice exists in English and Hindi. Each document identifies the equivalent versions in head, and each page also needs an obvious language switch that a visitor can use. These links should point to translated pages with equivalent meaning, not a generic language homepage. Set the actual document language on each version and keep both notices synchronized when a regulation or safety step changes.",
    '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Depot safety notice</title>
  <link rel="alternate" hreflang="en" href="/safety/depot-notice/en">
  <link rel="alternate" hreflang="hi" href="/safety/depot-notice/hi">
</head>
<body><main><h1>Depot safety notice</h1>
  <p><a href="/safety/depot-notice/hi" hreflang="hi">हिन्दी में पढ़ें</a></p>
</main></body>
</html>''',
    "The two same-site routes must exist and contain genuinely equivalent notices. Head metadata does not translate content or provide a visible switch on its own; the body link serves that human task.",
    "Two metadata links are cheap. The real cost is maintaining translation parity and testing every language route after a notice changes, including links, dates, and emergency instructions.",
    ["Do not point every translated article at one generic language homepage.", "Do not mark an untranslated page with another language code.", "Do not forget a visible language switch."],
    ["html/language-and-direction", "html/metadata-title", "html/anchors-and-paths"])

add("table-column-groups", "semantics", "HTML colgroup: assign column structure without replacing headers",
    "Colgroup describes groups of columns in a table and can provide styling hooks for those columns.",
    "An equipment log has one identifying column and two measurement columns. Grouping them can support consistent styling across all rows, but the table's meaning still comes from its caption and header cells. Column groups do not tell a screen reader that 47 is a temperature or a pressure reading; header text and associations do that. Keep the grid simple enough to verify after a new measurement field is added.",
    '''<table>
  <caption>Depot west sensor readings</caption>
  <colgroup><col span="1"><col span="2"></colgroup>
  <thead><tr><th scope="col">Sensor</th><th scope="col">Temperature °C</th><th scope="col">Pressure kPa</th></tr></thead>
  <tbody><tr><th scope="row">SR-47</th><td>23</td><td>101</td></tr></tbody>
</table>''',
    "The two groups describe one plus two columns. They are not a substitute for scope, caption, or row labels. Any CSS applied to col elements must also be checked in the browsers that display the report.",
    "Column metadata adds little DOM weight. Tables with thousands of rows still require pagination or a bounded dataset; colgroup does nothing to reduce row count or query cost.",
    ["Do not use colgroup to imitate a page layout grid.", "Do not omit table headers because columns have groups.", "Do not let span counts drift from the actual columns."],
    ["html/data-tables", "html/table-spans", "html/complex-table-headers"])

add("hidden-csrf-fields", "forms", "HTML hidden inputs: carry a token without treating it as secret",
    "A hidden input submits a named value with a form but does not display an interactive control.",
    "A parcel release form carries a server-issued request token beside the decision. That token may help the backend distinguish an authorized form submission from a forged one, but only when the server issues, binds, checks, and expires it correctly. The hidden field is visible in page source and can be altered by the client. Never use it as the sole record of the parcel's owner, price, or approval state.",
    '''<form action="/parcels/P-47/release" method="post">
  <input type="hidden" name="request_token" value="SERVER_ISSUED_PER_RESPONSE_TOKEN">
  <p>Release parcel P-47 after the seal check.</p>
  <button type="submit" name="decision" value="release">Confirm release</button>
</form>''',
    "The token value shown is a placeholder, not a usable security token. A production response must replace it with a cryptographically unpredictable value and verify the submitted value on the server along with the user's session and parcel permissions.",
    "The extra field is cheap. Token generation, storage or stateless verification, expiry, and replay rules add server work; correctness there matters far more than the HTML bytes.",
    ["Do not hard-code a token into a real page.", "Do not assume hidden means confidential or immutable.", "Do not trust a submitted parcel ID or decision without server checks."],
    ["html/forms-get-post", "html/form-names-disabled", "html/submit-button-overrides"])

add("multilingual-case-project", "project", "HTML multilingual case page project: preserve names and a clear reading order",
    "A multilingual case page must mark its document language, isolate variable-direction names, and keep navigation understandable.",
    "This static page lists a case summary in English while preserving a customer name in Arabic script and a support route with a Hindi-language alternative. The reference stays visible beside the name so reviewers do not have to infer identity from script or pronunciation. The sample deliberately avoids a language toggle that pretends to translate content; a real application must provide a separate equivalent page and keep its decision text in sync.",
    '''<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Case C-47 — review summary</title>
  <link rel="alternate" hreflang="hi" href="/cases/C-47/hi">
</head>
<body>
  <header><nav aria-label="Case navigation"><a href="/cases">Case index</a></nav></header>
  <main>
    <h1>Case C-47</h1>
    <p>Customer: <bdi>ليلى</bdi>. Review state: awaiting evidence.</p>
    <section aria-labelledby="next-step"><h2 id="next-step">Next step</h2>
      <p>Check the seal record before a decision is recorded.</p></section>
    <p><a href="/cases/C-47/hi" hreflang="hi">हिन्दी में पढ़ें</a></p>
  </main>
</body>
</html>''',
    "Both case routes and the index must be implemented. The static text is an example record, not a live case state. A backend owns authorization, the current review state, and translation equivalence.",
    "The page has no script requirement and only a small amount of HTML. Maintaining two language versions and checking bidirectional text in exports and notifications takes more work than rendering this document.",
    ["Do not use a visible language link that points to an untranslated page.", "Do not force a customer's name into the document direction.", "Do not expose private case data through an unchecked route."],
    ["html/language-and-direction", "html/bidi-isolation", "html/alternate-language-links", "html/landmarks"])

add("inspection-intake-project", "project", "HTML inspection intake project: one bounded, reviewable form",
    "An inspection intake form should name each control, group the decision, and state which facts the server must check.",
    "A depot worker records a parcel code, a measured count, and a short note before placing the parcel on hold or clearing it. The sample uses native controls so it works without JavaScript and remains legible in source order. The request token is represented as a server-generated placeholder; a real response must replace it. After submission, the server must validate the parcel, numeric range, note length, user role, and current state before writing a decision.",
    '''<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Inspection intake for parcel P-47</title></head>
<body><main><h1>Inspect parcel P-47</h1>
  <form action="/inspections/P-47" method="post">
    <input type="hidden" name="request_token" value="SERVER_ISSUED_PER_RESPONSE_TOKEN">
    <label for="intake-code">Six-digit parcel code</label>
    <input id="intake-code" name="parcel_code" inputmode="numeric" pattern="[0-9]{6}" required>
    <label for="seal-count">Seals counted</label>
    <input id="seal-count" name="seal_count" type="number" min="1" max="47" step="1" required>
    <label for="intake-note">Inspection note, 12 to 160 characters</label>
    <textarea id="intake-note" name="note" minlength="12" maxlength="160" required></textarea>
    <fieldset><legend>Decision</legend>
      <label><input type="radio" name="decision" value="hold" required> Hold for review</label>
      <label><input type="radio" name="decision" value="clear"> Clear for dispatch</label>
    </fieldset>
    <button type="submit">Record inspection</button>
  </form>
</main></body>
</html>''',
    "The action route, token, permissions, and persistence are absent from a static snippet. In production, display the authoritative parcel status returned after the server commits the decision, and reject a second conflicting submission.",
    "The markup requires no client bundle. The expensive operations are secure token handling, database state transitions, and audit logging; a successful browser validation is no proof those operations are correct.",
    ["Do not deploy the literal placeholder token.", "Do not accept a changed hidden value as proof of authority.", "Do not treat a browser-valid decision as an authorized state transition."],
    ["html/fieldset-and-legend", "html/number-input-or-text", "html/input-length-limits", "html/hidden-csrf-fields"])


new_paths = {"html/" + lesson[0] for lesson in lessons}
assert len(lessons) == 10 and not new_paths.intersection(by_path)
assert all(set(lesson[-1]) <= set(by_path) | new_paths for lesson in lessons)
titles = {path: row["title"] for path, row in by_path.items()}
titles.update({"html/" + lesson[0]: lesson[2] for lesson in lessons})


def body_for(lesson):
    _, _, _, definition, case, sample, boundary, cost, mistakes, links = lesson
    return (
        "<p>" + html.escape(definition) + "</p>"
        "<h2>Implementation choice</h2><p>" + html.escape(case) + "</p>"
        '<pre><code class="language-html">' + html.escape(sample, quote=False) + "</code></pre>"
        "<h2>What remains outside the markup</h2><p>" + html.escape(boundary) + "</p>"
        "<h2>Cost and limits</h2><p>" + html.escape(cost) + "</p>"
        "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in mistakes) + "</ul>"
        "<h2>Connected lessons</h2><ul>" + "".join(
            '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>" for path in links
        ) + "</ul>"
    )


by_section = {}
for index, lesson in enumerate(lessons):
    slug, section, title, definition, _, _, _, _, _, links = lesson
    path = "html/" + slug
    hub_path = "html/html-tutorial" if section == "core" else "html/html-tutorial/" + section
    hub = by_path[hub_path]
    row = copy.deepcopy(by_path["html/document-skeleton"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)), path=path,
               title=title, summary=definition, body=body_for(lesson), subject=hub["subject"],
               tags=["html", section], sort_order=2000 + index,
               created_at=stamp, updated_at=stamp, published_at=stamp)
    row["data"] = {"subject_root": "html/html-tutorial", "section_path": hub_path,
                   "content_format": "html", "kind": "project" if section == "project" else "tutorial",
                   "reading_minutes": 8, "author_path": "authors/aitrove-editorial", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in links]}
    rows.append(row)
    by_path[path] = row
    by_section.setdefault(section, []).append(path)

for section, paths in by_section.items():
    hub_path = "html/html-tutorial" if section == "core" else "html/html-tutorial/" + section
    hub = by_path[hub_path]
    hub["data"]["modules"].append({"title": "Applied " + section + " decisions",
                                    "summary": "Original examples with explicit browser and server contracts.",
                                    "lessons": paths})
    additions = "<h2>Applied decisions</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>" for path in paths
    ) + "</ul>"
    hub["body"] = hub["body"].replace("<h3>Common Mistakes</h3>", additions + "<h3>Common Mistakes</h3>", 1)
    hub["updated_at"] = stamp

for lesson in lessons:
    path = "html/" + lesson[0]
    target = by_path[lesson[-1][0]]
    link = '<p><a href="/' + path + '">Related: ' + html.escape(titles[path]) + "</a>.</p>"
    if link not in target["body"]:
        target["body"] += link
        target["data"].setdefault("related", []).append({"path": path, "title": titles[path]})
        target["updated_at"] = stamp

root_hub = by_path["html/html-tutorial"]
root_hub["body"] += (
    '<p><a href="/html/multilingual-case-project">Read a multilingual case page</a> and '
    '<a href="/html/inspection-intake-project">build an inspection intake form</a> after the core lessons.</p>'
)

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "articles and two full-page projects")

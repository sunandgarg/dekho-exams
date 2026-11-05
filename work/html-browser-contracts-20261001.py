"""Add distinct HTML browser contracts and make the core/form paths readable."""

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


def links(paths):
    return "".join(
        '<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>"
        for path in paths
    )


def lesson(path, title, summary, section, prose, sample, closing, mistakes, related):
    assert path not in by_path
    body = (
        "<p>" + prose[0] + "</p><h2>Use the contract</h2><p>" + prose[1] + "</p>"
        '<pre><code class="language-html">' + html.escape(sample, quote=False) + "</code></pre>"
        "<h2>Behavior and cost</h2><p>" + closing + "</p>"
        "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + item + "</li>" for item in mistakes) + "</ul>"
        "<h2>Connected lessons</h2><ul>" + links(related) + "</ul>"
    )
    template = by_path["html/number-input-or-text"]
    entry = copy.deepcopy(template)
    entry.update(
        id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
        path=path, title=title, summary=summary, body=body,
        subject=by_path[section]["subject"], tags=["html"], sort_order=2600 + len(rows),
        created_at=stamp, updated_at=stamp, published_at=stamp,
    )
    entry["data"] = {
        "subject_root": "html/html-tutorial", "section_path": section,
        "content_format": "html", "kind": "tutorial", "reading_minutes": 6,
        "author_path": "authors/aitrove-editorial", "seo_ready": True,
        "related": [{"path": key, "title": by_path[key]["title"]} for key in related],
    }
    rows.append(entry)
    by_path[path] = entry
    for key in related:
        target = by_path[key]
        target["body"] += '<p><a href="/' + path + '">Continue with ' + html.escape(title) + "</a>.</p>"
        target["data"].setdefault("related", []).append({"path": path, "title": title})
        target["updated_at"] = stamp


lesson(
    "html/number-step-boundaries",
    "HTML number boundaries: align min, max, and step with the real unit",
    "Use number input constraints for quantities with a clear unit and permitted increment.",
    "html/html-tutorial/forms",
    [
        "A number input accepts a quantity; min, max, and step describe its allowed range and increment. They are browser constraints, not a database rule.",
        "An inspection scale records parcel weight in quarter-kilogram increments from 0.25 through 12 kilograms. State the unit in the label. With min set to 0.25 and step set to 0.25, 2.75 is valid while 2.85 has a step mismatch. The minimum also becomes the step base. An empty field still needs required if the value is mandatory. If weight must be more precise than the scale can report, change the business rule first; a smaller step does not create measurement accuracy. This control is for a numeric quantity, unlike a parcel identifier that merely contains digits.",
    ],
    '''<form action="/parcels/measure" method="post">
  <label for="parcel-weight">Measured weight in kilograms</label>
  <input id="parcel-weight" name="weight_kg" type="number"
         min="0.25" max="12" step="0.25" value="2.75" required>
  <button type="submit">Record weight</button>
</form>''',
    "The browser can reject a value before submission, but a crafted request can bypass every attribute. Recheck the range and increment on the server using decimal arithmetic suited to the stored unit. Do not rely on binary floating-point equality for money or measured increments. Native validation has negligible download cost; the maintenance cost is keeping the HTML, server rule, and equipment calibration in agreement. Test the lower edge, upper edge, one step outside each edge, an empty value, and a value such as 2.85 that sits inside the range but off the increment grid.",
    ["Do not use type=number for codes, telephone numbers, or values with significant leading zeroes.", "Do not assume max or step makes the server safe from altered requests.", "Do not forget that min changes where the step grid starts."],
    ["html/number-input-or-text", "html/form-validation", "html/date-and-time-inputs"],
)

lesson(
    "html/multiple-file-selection",
    "HTML multiple file input: accept several files without inventing a limit",
    "Let the browser select several files while enforcing count and content on the server.",
    "html/html-tutorial/forms",
    [
        "A file input with multiple lets a person select more than one file under one field name. It does not set a maximum count, total byte limit, or safe content type.",
        "A damage report may need up to three photographs. The label states that policy, and the picker hints at JPEG and PNG files. The form uses multipart encoding so file bodies can be sent. Each selected file remains an individual item associated with the field; the server must iterate over them rather than expect one filename string. Required means that the selection cannot be empty for native constraint validation. It does not mean exactly three files. If the reviewer selects four, the server must return a clear error and preserve the other entered fields where policy permits.",
    ],
    '''<form action="/damage-reports/47/photos" method="post" enctype="multipart/form-data">
  <label for="damage-photos">Damage photographs (up to three)</label>
  <input id="damage-photos" name="damage_photos" type="file"
         accept="image/jpeg,image/png" multiple required>
  <button type="submit">Attach photographs</button>
</form>''',
    "The picker may filter files according to accept, but the selected bytes still need inspection. Limit individual and aggregate size before decoding, verify actual format, assign server-owned storage names, and authorize attachment to the report. File transfer and image processing dominate the cost; the HTML attribute itself is cheap. On mobile devices, selection behavior varies, so test one file, several files, cancellation, and an over-limit submission. The shown action path is illustrative until an authenticated upload service exists.",
    ["Do not treat multiple as a three-file cap.", "Do not trust a filename, extension, or client-supplied media type as proof of image content.", "Do not omit multipart encoding when the form submits file bodies."],
    ["html/file-upload-form", "html/file-accept-hint", "html/inspection-intake-project"],
)

lesson(
    "html/color-scheme-metadata",
    "HTML color-scheme metadata: declare supported UI schemes separately from browser chrome",
    "Distinguish color-scheme support from theme-color and from actual page styling.",
    "html/html-tutorial",
    [
        "Color-scheme metadata tells the browser which light and dark color schemes a document can handle. Theme-color is a separate hint for browser interface areas around the page.",
        "An incident console offers both light and dark presentation. Declare that support in the head, then supply actual CSS colors for the document and controls. A matching theme-color may tint parts of the browser interface where the browser supports it; it does not paint the page or guarantee exact chrome colors. The dark and light theme-color entries use different media conditions, so one can match each scheme. Keep text, controls, focus indicators, and images readable in both. If the site only styles one scheme, claiming both support can produce an awkward mix of browser controls and page colors.",
    ],
    '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="color-scheme" content="light dark">
  <meta name="theme-color" content="#f4f1e8" media="(prefers-color-scheme: light)">
  <meta name="theme-color" content="#18232a" media="(prefers-color-scheme: dark)">
  <title>Incident queue</title>
  <style>
    body { background: #f4f1e8; color: #18232a; }
    @media (prefers-color-scheme: dark) {
      body { background: #18232a; color: #f4f1e8; }
    }
  </style>
</head>
<body><main><h1>Incident queue</h1><p>47 records await review.</p></main></body>
</html>''',
    "These declarations are tiny; the cost is testing two complete visual states. A browser may adjust or ignore theme-color when painting its own interface. Test native inputs, system contrast settings, images with transparent backgrounds, and the first paint before CSS finishes loading. Color-scheme metadata can help the browser choose an appropriate early rendering mode, but a correct page still depends on a complete stylesheet. If a future design removes dark support, update the metadata as well as the CSS rather than leaving a false promise in head.",
    ["Do not confuse theme-color with a CSS background declaration.", "Do not claim dark support until every meaningful surface has been checked.", "Do not assume all browsers render browser chrome from the hint identically."],
    ["html/viewport-metadata", "html/metadata-title", "html/print-stylesheet-media"],
)

lesson(
    "html/translate-boundaries",
    "HTML translate attribute: protect identifiers while localizing the surrounding text",
    "Mark fixed tokens as nontranslatable without freezing an entire sentence.",
    "html/html-tutorial/semantics",
    [
        "The translate attribute marks whether an element's text and translatable attributes should change during localization. A no value is appropriate for a fixed identifier, not for the instructions around it.",
        "A dispatch dashboard gives human instructions next to a stable service code. The sentence must be localized; the code must remain the same token that appears in logs and support calls. Wrap only that token. Inherited translation mode means a broad no on the main container would also protect ordinary help text, labels, and headings from translation. The language attribute remains a separate concern: it identifies the language of content for pronunciation and processing. A protected code does not give the rest of the document a language, and a language tag does not prevent an identifier from being translated by a localization workflow.",
    ],
    '''<main>
  <h1>Dispatch review</h1>
  <p>Quote service code <code translate="no">DS-47Q</code> when reporting a failed transfer.</p>
  <p>Describe the failure in the language used by the support team.</p>
</main>''',
    "The attribute adds no runtime bundle. Its cost appears in the translation pipeline: translators need clear context for protected tokens and a review of visible strings after localization. Automated browser translation may not behave exactly like a managed translation system, so test the actual workflow. If a token has several display forms, decide centrally which form is stable rather than scattering no-translate spans through generated copy. Check that accessible names and image alternatives still read naturally in each language.",
    ["Do not set translate=no on a whole article to protect one code.", "Do not use the attribute as a substitute for lang or dir.", "Do not assume a translation tool will preserve every token without review."],
    ["html/language-and-direction", "html/bidi-isolation", "html/multilingual-case-project"],
)

lesson(
    "html/preformatted-code-and-output",
    "HTML pre and code: preserve source layout without hiding the meaning",
    "Use preformatted text for source whose spacing matters and identify code as code.",
    "html/html-tutorial",
    [
        "A pre element preserves preformatted text; code marks computer code. Together they retain line breaks and indentation when those characters help a reader understand a command or snippet.",
        "An operations note records a small SQL query used to inspect delayed parcels. Put it in pre and code so the line breaks are stable when copied. Nearby prose explains the query's purpose and the account boundary; the snippet is not an instruction to run it against production without review. The HTML parser still processes markup characters inside code, so an embedded less-than sign must be escaped in the source document. A pre block also keeps long lines, which can overflow a narrow screen. Break a line deliberately where the language permits, or provide a readable scroll treatment in CSS.",
    ],
    '''<main>
  <h1>Delayed parcel query</h1>
  <p>Read-only query for records awaiting a handoff after the cutoff.</p>
  <pre><code class="language-sql">SELECT parcel_id, depot_code
FROM dispatch_queue
WHERE handoff_hour &lt; 17
ORDER BY parcel_id;</code></pre>
  <p>Review query permissions before running it against live data.</p>
</main>''',
    "The elements add no script or network request. Syntax highlighting is optional and often costs more than the markup, so keep the plain source readable first. A language class can help a highlighter or editor, but HTML itself does not highlight code. For command output, use the element whose semantics represent sample output rather than labeling it as a program. Test copy and paste, horizontal overflow at narrow widths, and screen-reader reading order. Keep credentials, private queries, and operational secrets out of examples; pre preserves text, it does not redact it.",
    ["Do not paste raw markup delimiters into a code sample without escaping them.", "Do not force every note into pre when normal prose is clearer.", "Do not depend on highlighting to communicate the only difference between two code paths."],
    ["html/inline-text-meaning", "html/character-references", "html/word-break-opportunities"],
)

lesson(
    "html/search-form-contract",
    "HTML search form: pair a search landmark with a real GET result route",
    "Give a site search a named text field, a submit control, and a retrievable result URL.",
    "html/html-tutorial/forms",
    [
        "The search element marks a search interface, while an input of type search collects a query. A GET form places the query in the result URL so the search can be revisited or shared.",
        "A reviewer searches a public incident archive by a case reference. The search element identifies the area, the label supplies the field name, and the submit button makes the action clear on physical and virtual keyboards. The server route performs the search and returns an actual results page; neither the element nor the input type implements indexing. Keep the query name stable because saved links and analytics may depend on it. If the archive contains private records, a GET query in the URL can leak through history, logs, or sharing. In that case, design a different retrieval contract with authorization rather than merely changing the markup.",
    ],
    '''<search>
  <form action="/public-incidents/search" method="get">
    <label for="incident-query">Search public incidents</label>
    <input id="incident-query" name="query" type="search" required>
    <button type="submit">Search records</button>
  </form>
</search>''',
    "The static form is small and works without a client bundle, but the result route needs an index, safe query handling, useful empty-state copy, and pagination once results grow. Search latency depends on that service, not on the HTML input. Test an empty query, punctuation, a case reference with spaces, zero results, and direct navigation to a result URL. An accessible landmark does not compensate for a dead endpoint; the shown path is illustrative until the archive search exists.",
    ["Do not use the search element as if it executes a search.", "Do not hide a sensitive query in a shareable GET URL.", "Do not replace the visible submit button with a keyboard hint alone."],
    ["html/search-element", "html/forms-get-post", "html/form-labels"],
)


def set_modules(hub_path, groups):
    hub = by_path[hub_path]
    old = [path for module in hub["data"]["modules"] for path in module["lessons"]]
    fresh = [path for _, _, paths in groups for path in paths]
    assert len(fresh) == len(set(fresh)), hub_path
    assert set(fresh) == set(old) | {path for path in fresh if path not in old and by_path[path]["data"]["section_path"] == hub_path}, hub_path
    hub["data"]["modules"] = [
        {"title": title, "summary": summary, "lessons": paths} for title, summary, paths in groups
    ]
    hub["body"] = (
        "<p>" + hub["summary"] + "</p>"
        + "".join("<h2>" + title + "</h2><p>" + summary + "</p><ul>" + links(paths) + "</ul>" for title, summary, paths in groups)
        + '<p><a href="/html/html-tutorial">Return to the HTML tutorial</a>.</p>'
        + "<h3>Common Mistakes</h3><p>A listed lesson describes a browser contract; its illustrative endpoint or asset is not a working service.</p>"
    )
    hub["updated_at"] = stamp


set_modules("html/html-tutorial", [
    ("Document identity", "Start with parsing mode, encoding, titles, and the viewport.", ["html/html-tags-a-to-z-list", "html/document-skeleton", "html/doctype-and-quirks-mode", "html/parser-and-void-elements", "html/metadata-title", "html/meta-description", "html/viewport-metadata", "html/site-icon-metadata", "html/color-scheme-metadata"]),
    ("Readable text and code", "Choose text structures that retain their meaning without visual treatment.", ["html/headings-and-paragraphs", "html/lists-and-definitions", "html/inline-text-meaning", "html/preformatted-code-and-output", "html/character-references", "html/global-attributes"]),
    ("Links and resource boundaries", "Understand navigation, download behavior, URL resolution, and resource hints.", ["html/anchors-and-paths", "html/new-tab-links", "html/download-links", "html/base-element-paths", "html/anchor-referrer-policy", "html/alternate-language-links", "html/resource-hints", "html/print-stylesheet-media"]),
])

set_modules("html/html-tutorial/forms", [
    ("Submission and server rules", "Choose a request method, name each value, and make every action explicit.", ["html/forms-get-post", "html/form-names-disabled", "html/form-validation", "html/form-ownership", "html/submit-button-overrides", "html/button-type-default", "html/reset-button", "html/draft-formnovalidate", "html/submitter-name-value", "html/hidden-csrf-fields", "html/search-form-contract"]),
    ("Labels and choices", "Keep controls named and group values according to the decision.", ["html/form-labels", "html/input-types", "html/radio-checkbox", "html/select-and-textarea", "html/fieldset-and-legend", "html/disabled-fieldset", "html/select-groups-and-multiple", "html/required-select-placeholder"]),
    ("Text and numeric inputs", "Match identifiers, quantities, and editing hints to their actual data model.", ["html/autocomplete-and-inputmode", "html/datalist-suggestions", "html/input-pattern", "html/input-length-limits", "html/form-dirname", "html/number-input-or-text", "html/number-step-boundaries", "html/text-input-assistance", "html/multiple-email-input", "html/telephone-input", "html/password-autocomplete-tokens", "html/textarea-wrap-submission", "html/contenteditable-vs-textarea"]),
    ("Dates, ranges, and measured values", "Separate display controls from the units and server decisions behind them.", ["html/date-and-time-inputs", "html/range-input-and-output", "html/color-input", "html/progress-meter-output"]),
    ("Files and image submissions", "Budget bytes, count, content, and the activated submitter.", ["html/file-upload-form", "html/file-accept-hint", "html/multiple-file-selection", "html/image-submit-button"]),
])

for hub_path, group_title, group_summary, paths in [
    ("html/html-tutorial/semantics", "Localization boundaries", "Keep identifiers stable while translating the document around them.", ["html/translate-boundaries"]),
]:
    hub = by_path[hub_path]
    hub["data"]["modules"].append({"title": group_title, "summary": group_summary, "lessons": paths})
    hub["body"] += "<h2>" + group_title + "</h2><ul>" + links(paths) + "</ul>"
    hub["updated_at"] = stamp

review_paths = ["html/number-step-boundaries", "html/multiple-file-selection", "html/color-scheme-metadata", "html/translate-boundaries", "html/preformatted-code-and-output", "html/search-form-contract"]
quiz_path = "quizzes/html-browser-contracts"
assert quiz_path not in by_path
questions = [
    ("A weight field has min=0.25 and step=0.25. Which value matches the grid?", ["2.85", "2.75", "2.80"], 1, "2.75 is 0.25 plus ten increments of 0.25."),
    ("Which layer must enforce a weight increment after a crafted request?", ["Only the input attribute", "Only the stylesheet", "The server"], 2, "Browser constraints can be bypassed; the server owns stored data rules."),
    ("A file input has multiple. What limit does that set?", ["No fixed maximum count", "Exactly three files", "One file per form"], 0, "Multiple permits several selections but does not impose a count cap."),
    ("Which form encoding sends selected file bodies?", ["text/plain", "multipart/form-data", "application/json"], 1, "A native file form uses multipart form data to submit file parts."),
    ("What does color-scheme metadata declare?", ["Supported light and dark schemes", "The page's search title", "A guaranteed toolbar color"], 0, "It describes supported color schemes; page styling still needs CSS."),
    ("What is theme-color allowed to affect?", ["Stored form values", "The document's DOM order", "Supported browser interface areas"], 2, "It is a browser UI hint, not the page background declaration."),
    ("Which content should translate=no usually protect?", ["The whole help article", "A fixed service code", "Every form label"], 1, "A stable token can stay fixed while surrounding guidance is translated."),
    ("Does translate=no replace the lang attribute?", ["Yes", "Only on code elements", "No"], 2, "Language identification and translation mode are separate contracts."),
    ("Why pair pre with code for a source snippet?", ["To preserve formatting and mark code", "To execute the snippet", "To encrypt copied text"], 0, "Pre retains preformatted text; code identifies a computer-code fragment."),
    ("What must happen to a less-than sign inside an HTML code sample?", ["It must be escaped in source markup", "It becomes a URL", "It is removed by pre"], 0, "Pre does not disable HTML parsing; markup delimiters need character references."),
    ("What does a GET search form make possible?", ["Automatic indexing", "A retrievable query URL", "Private storage"], 1, "The query becomes part of the result URL; the server still implements search."),
    ("Which part of a search interface performs the actual lookup?", ["The search element", "The type=search input", "The result route"], 2, "Markup identifies the interface; a working result service performs retrieval."),
]
template = by_path["quizzes/html-production-review"]
quiz = copy.deepcopy(template)
quiz.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + quiz_path)),
    path=quiz_path, title="HTML browser contracts quiz",
    summary="Twelve applied checks on quantities, files, metadata, localization, code, and search.",
    body=("<p>Choose the layer that owns each browser behavior, and separate HTML hints from server decisions.</p>"
          "<h2>Review the lessons</h2><ul>" + links(review_paths) + "</ul>"
          "<h3>Common Mistakes</h3><p>A correct quiz answer does not prove that an illustrative route or uploaded asset is deployed.</p>"),
    sort_order=3006, created_at=stamp, updated_at=stamp, published_at=stamp,
)
quiz["data"] = {
    "subject_root": "html/html-tutorial", "section_path": "html/quizzes", "content_format": "html",
    "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
    "related": [{"path": path, "title": by_path[path]["title"]} for path in review_paths],
    "questions": [{"prompt": prompt, "options": options, "answer": answer, "explanation": explanation}
                  for prompt, options, answer, explanation in questions],
}
rows.append(quiz)
by_path[quiz_path] = quiz
hub = by_path["html/quizzes"]
hub["data"]["modules"].append({"title": quiz["title"], "summary": quiz["summary"], "lessons": [quiz_path]})
hub["body"] += "<h2>Browser contracts</h2><ul>" + links([quiz_path]) + "</ul>"
hub["updated_at"] = stamp

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added 6 HTML lessons and 1 quiz; regrouped core and forms.")
